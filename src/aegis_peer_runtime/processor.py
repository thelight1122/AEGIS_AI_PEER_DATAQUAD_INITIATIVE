"""Idempotent, append-only turn admission for a seated live AI Peer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

from .custodians import ADVOCATE, STEWARD
from .models import DATAQUAD_NAMES
from .temporal import require_live_seated
from .storage import StorageError, process_lock


@dataclass(frozen=True)
class TurnAdmission:
    peer_id: str
    turn_id: str
    payload_digest: str
    admitted_at: str
    steward_changes: dict[str, object]
    advocate_changes: dict[str, object]


def payload_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ProcessorRuntime:
    def __init__(self, peer_id: str, ledger_path: str | Path) -> None:
        if peer_id not in DATAQUAD_NAMES:
            raise ValueError(f"unknown peer_id: {peer_id}")
        self.peer_id = peer_id
        self.ledger_path = Path(ledger_path)

    def _admissions_unlocked(self) -> dict[str, TurnAdmission]:
        result: dict[str, TurnAdmission] = {}
        if not self.ledger_path.exists():
            return result
        if self.ledger_path.is_symlink():
            raise StorageError(f"processor ledger must not be a symlink: {self.ledger_path}")
        with self.ledger_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                item = TurnAdmission(**json.loads(line))
                if item.peer_id != self.peer_id:
                    raise ValueError("cross-peer processor record")
                if item.turn_id in result:
                    raise ValueError("duplicate processor turn_id")
                STEWARD.authorize(item.steward_changes)
                ADVOCATE.authorize(item.advocate_changes)
                result[item.turn_id] = item
        return result

    def admissions(self) -> dict[str, TurnAdmission]:
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            return self._admissions_unlocked()

    def admit_turn(
        self,
        *,
        turn_id: str,
        payload: object,
        steward_changes: Mapping[str, object],
        advocate_changes: Mapping[str, object],
        seated: bool,
        live_source: bool,
        source_mode: str,
    ) -> TurnAdmission:
        require_live_seated(
            seated=seated, live_source=live_source, source_mode=source_mode
        )
        if not turn_id:
            raise ValueError("turn_id is required")
        digest = payload_digest(payload)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            existing = self._admissions_unlocked().get(turn_id)
            if existing:
                if existing.payload_digest != digest:
                    raise ValueError("turn_id already admitted with different payload")
                return existing
            admission = TurnAdmission(
                peer_id=self.peer_id,
                turn_id=turn_id,
                payload_digest=digest,
                admitted_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                steward_changes=STEWARD.authorize(steward_changes),
                advocate_changes=ADVOCATE.authorize(advocate_changes),
            )
            if self.ledger_path.is_symlink():
                raise StorageError(f"processor ledger must not be a symlink: {self.ledger_path}")
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(asdict(admission), sort_keys=True, separators=(",", ":")))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            return admission
