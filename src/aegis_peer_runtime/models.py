"""Validated runtime models using only the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping

PEERS = ("lumin", "claude", "gemini", "grok")
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
class Record:
    peer: str
    tensor: str
    actor: str
    idempotency_key: str
    payload: Mapping[str, Any]

    def validate(self) -> None:
        if self.peer not in PEERS:
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
