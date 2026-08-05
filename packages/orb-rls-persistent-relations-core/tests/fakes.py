"""Fake implementations of the aegis_pod_sdk protocols — used ONLY by this
package's own test suite to prove the extracted Orb works correctly against
*any* conforming Pod, without needing AEGIS-CYBERPEER-CORE checked out.

These are intentionally not the monolith's real Steward/Advocate/DataQuadStore —
that would defeat the point of Stage 1. A real Pod's own concrete classes are
verified against these same protocols separately (Stage 3/5 integration work).
"""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aegis_pod_sdk import TensorKind


@dataclass
class FakeClock:
    tick: int
    epoch: str = "primary"
    phase: str = "active"
    started_at: str = "t0"
    last_advanced_at: str = "t0"


@dataclass
class FakeRecord:
    id: str
    tensor: TensorKind
    clock: FakeClock
    pattern: str | None = None
    present_state: dict | None = None
    working_context: dict | None = None
    distilled_summary: str | None = None
    essence_memory: str | None = None
    nature_aspect_refs: list[str] | None = None
    rls_session_id: str | None = None
    retrieved_record_ids: list[str] | None = None
    pressure_state: dict | None = None


@dataclass
class FakeTSignature:
    t_witness_ms: float = 0.0


class FakeStore:
    """Minimal DataQuadStoreProtocol conformance: in-memory records, real temp
    filesystem for peer_root (orb_evidence needs to actually write a file to
    verify against)."""

    def __init__(self, tmp_path: Path, rls_active: bool = True):
        self._tmp_path = tmp_path
        self._records: dict[str, list[FakeRecord]] = {}
        self._ticks: dict[str, int] = {}
        self.ledger_entries: list[tuple[str, str, dict]] = []
        self.relations: list[dict] = []
        self._rls_active = rls_active

    def records_for(self, peer_id: str, tensor: TensorKind) -> list[FakeRecord]:
        return [r for r in self._records.get(peer_id, []) if r.tensor == tensor]

    def _append(self, peer_id: str, record: FakeRecord) -> None:
        self._records.setdefault(peer_id, []).append(record)

    async def get_next_tick(self, peer_id: str) -> int:
        self._ticks[peer_id] = self._ticks.get(peer_id, 0) + 1
        return self._ticks[peer_id]

    async def append_ledger(self, peer_id: str, ledger_name: str, entry: dict) -> None:
        self.ledger_entries.append((peer_id, ledger_name, entry))

    async def record_relation(self, peer_id, from_id, to_id, *, relation, tags, written_by) -> None:
        self.relations.append({
            "peer_id": peer_id, "source": from_id, "target": to_id,
            "relation": relation, "tags": tags, "written_by": written_by,
        })

    def is_active(self, capability: str) -> bool:
        return self._rls_active

    def peer_root(self, peer_id: str) -> Path:
        return self._tmp_path / "peers" / peer_id


class FakeSteward:
    def __init__(self, store: FakeStore, peer_id: str):
        self.store = store
        self.peer_id = peer_id

    async def read_pct(self) -> list[FakeRecord]:
        return self.store.records_for(self.peer_id, TensorKind.PCT)

    async def read_nct(self) -> list[FakeRecord]:
        return self.store.records_for(self.peer_id, TensorKind.NCT)

    async def build_and_append_pct(
        self, *, session_id, working_context, retrieved_record_ids, rls_session_id, pressure_state
    ) -> FakeRecord:
        tick = await self.store.get_next_tick(self.peer_id)
        timestamp = datetime.now(timezone.utc).isoformat()
        record = FakeRecord(
            id=f"PCT:{self.peer_id}:{timestamp}:{tick}",
            tensor=TensorKind.PCT,
            clock=FakeClock(tick=tick),
            working_context=working_context,
            rls_session_id=rls_session_id,
            retrieved_record_ids=retrieved_record_ids,
            pressure_state=pressure_state,
        )
        self.store._append(self.peer_id, record)
        return record


class FakeAdvocate:
    def __init__(self, store: FakeStore, peer_id: str):
        self.store = store
        self.peer_id = peer_id

    async def read_peer(self) -> list[FakeRecord]:
        return self.store.records_for(self.peer_id, TensorKind.PEER)

    async def read_spine(self) -> list[FakeRecord]:
        return self.store.records_for(self.peer_id, TensorKind.SPINE)

    async def append_spine(self, record: FakeRecord) -> None:
        self.store._append(self.peer_id, record)


@contextmanager
def fake_witness_event(tick: int, *, witness_mode: str, pressure_level: str):
    def get_signature() -> FakeTSignature:
        return FakeTSignature(t_witness_ms=0.0)
    yield get_signature


def make_spine_record(peer_id: str, pattern: str, nature_aspect_refs: list[str] | None = None) -> FakeRecord:
    return FakeRecord(
        id=f"SPINE:{peer_id}:{uuid.uuid4()}",
        tensor=TensorKind.SPINE,
        clock=FakeClock(tick=0),
        pattern=pattern,
        nature_aspect_refs=nature_aspect_refs or [],
    )
