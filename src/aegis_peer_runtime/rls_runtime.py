"""Derived-only RLS observations with authoritative tensor immutability proof."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping

from .models import DATAQUAD_NAMES
from .temporal import require_live_seated
from .storage import StorageError, process_lock


def tensor_hashes(tensors: Mapping[str, object]) -> dict[str, str]:
    return {
        name: hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        for name, value in sorted(tensors.items())
    }


@dataclass(frozen=True)
class DerivedRelation:
    peer_id: str
    relation_id: str
    observed_at: str
    derivation: dict[str, object]
    tensor_hashes_before: dict[str, str]
    tensor_hashes_after: dict[str, str]
    authoritative_tensor_mutation: bool = False


class RLSRuntime:
    def __init__(self, peer_id: str, ledger_path: str | Path) -> None:
        if peer_id not in DATAQUAD_NAMES:
            raise ValueError(f"unknown peer_id: {peer_id}")
        self.peer_id = peer_id
        self.ledger_path = Path(ledger_path)

    def _relations_unlocked(self) -> dict[str, DerivedRelation]:
        result: dict[str, DerivedRelation] = {}
        if not self.ledger_path.exists():
            return result
        if self.ledger_path.is_symlink():
            raise StorageError(f"RLS ledger must not be a symlink: {self.ledger_path}")
        with self.ledger_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                relation = DerivedRelation(**json.loads(line))
                if relation.peer_id != self.peer_id:
                    raise ValueError(f"cross-peer RLS record at line {line_number}")
                if relation.relation_id in result:
                    raise ValueError(f"duplicate RLS relation_id at line {line_number}")
                if relation.authoritative_tensor_mutation is not False:
                    raise ValueError(f"RLS mutation claim at line {line_number}")
                if relation.tensor_hashes_before != relation.tensor_hashes_after:
                    raise ValueError(f"RLS tensor immutability mismatch at line {line_number}")
                result[relation.relation_id] = relation
        return result

    def relations(self) -> dict[str, DerivedRelation]:
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            return self._relations_unlocked()

    def append_relation(
        self,
        *,
        relation_id: str,
        derivation: Mapping[str, object],
        tensors: Mapping[str, object],
        seated: bool,
        live_source: bool,
        source_mode: str,
    ) -> DerivedRelation:
        require_live_seated(
            seated=seated, live_source=live_source, source_mode=source_mode
        )
        before = tensor_hashes(tensors)
        after = tensor_hashes(tensors)
        if before != after:
            raise RuntimeError("RLS mutated authoritative tensors")
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with process_lock(self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")):
            existing = self._relations_unlocked().get(relation_id)
            if existing is not None:
                if (existing.derivation != dict(derivation)
                        or existing.tensor_hashes_before != before
                        or existing.tensor_hashes_after != after):
                    raise ValueError("relation_id already names different RLS evidence")
                return existing
            relation = DerivedRelation(
                peer_id=self.peer_id,
                relation_id=relation_id,
                observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                derivation=dict(derivation),
                tensor_hashes_before=before,
                tensor_hashes_after=after,
            )
            if self.ledger_path.is_symlink():
                raise StorageError(f"RLS ledger must not be a symlink: {self.ledger_path}")
            with self.ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(asdict(relation), sort_keys=True, separators=(",", ":")))
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
        return relation
