"""Validated runtime models using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import hashlib
from typing import Any, Mapping

PEERS = ("lumin", "claude", "gemini", "grok")
DATAQUAD_NAMES = (*PEERS, "verus")
TENSORS = ("PEER", "PCT", "NCT", "SPINE")
WRITE_SCOPES = {
    "steward": frozenset(("PCT", "NCT")),
    "advocate": frozenset(("PEER", "SPINE")),
}


class PeerState(StrEnum):
    UNSEATED = "UNSEATED"
    SEATED = "SEATED"


class ValidationError(ValueError):
    """The request violates a peer-runtime invariant."""


@dataclass(frozen=True, slots=True)
class ExperienceAdmission:
    """Provenance required before an identity-bearing experience is recorded."""

    source_event_id: str
    substrate: str
    instance_id: str
    observed_at: str
    statement_digest: str

    def validate(self) -> None:
        for name in ("source_event_id", "substrate", "instance_id", "observed_at"):
            if not getattr(self, name).strip():
                raise ValidationError(f"admission.{name} must not be empty")
        digest = self.statement_digest.lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValidationError("admission.statement_digest must be a SHA-256 hex digest")
        try:
            observed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValidationError("admission.observed_at must be ISO-8601") from error
        if observed.tzinfo is None:
            raise ValidationError("admission.observed_at must include a timezone")

    def as_dict(self) -> dict[str, str]:
        return {
            "source_event_id": self.source_event_id,
            "substrate": self.substrate,
            "instance_id": self.instance_id,
            "observed_at": self.observed_at,
            "statement_digest": self.statement_digest.lower(),
        }


@dataclass(frozen=True, slots=True)
class Record:
    peer: str
    tensor: str
    actor: str
    idempotency_key: str
    payload: Mapping[str, Any]
    identity_bearing: bool = False
    admission: ExperienceAdmission | None = None

    def validate(self) -> None:
        if self.peer not in DATAQUAD_NAMES:
            raise ValidationError(f"unknown peer: {self.peer}")
        if self.tensor not in TENSORS:
            raise ValidationError(f"unknown tensor: {self.tensor}")
        if self.actor not in WRITE_SCOPES:
            raise ValidationError(f"unknown write actor: {self.actor}")
        if self.tensor not in WRITE_SCOPES[self.actor]:
            raise ValidationError(f"{self.actor} cannot write {self.tensor}")
        if not self.idempotency_key.strip():
            raise ValidationError("idempotency_key must not be empty")
        if not isinstance(self.payload, Mapping):
            raise ValidationError("payload must be an object")
        if not isinstance(self.identity_bearing, bool):
            raise ValidationError("identity_bearing must be boolean")
        if self.identity_bearing:
            if self.admission is None:
                raise ValidationError("identity-bearing experience requires provenance admission")
            self.admission.validate()
            statement = self.payload.get("statement")
            if not isinstance(statement, str) or not statement:
                raise ValidationError("identity-bearing payload requires a statement")
            actual = hashlib.sha256(statement.encode("utf-8")).hexdigest()
            if actual != self.admission.statement_digest.lower():
                raise ValidationError("admission.statement_digest does not bind payload statement")
        elif self.admission is not None:
            raise ValidationError("admission is allowed only for identity-bearing experience")
