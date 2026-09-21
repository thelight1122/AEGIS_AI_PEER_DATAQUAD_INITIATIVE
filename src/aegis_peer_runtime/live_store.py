"""Live DataQuad store — concrete DataQuadStoreProtocol for P1 activation.

Store-side gating (C3 finding + 2026-09-20 hardening): the orb calls
record_relation and append_ledger unconditionally on the writeback path; this
store gates BOTH on _rls_active so they are true no-ops when inactive. This
gives the RLS writeback in-store defense-in-depth symmetric with the caller
gate (processor_daemon._init_rls_engine returns None when not rls_active), so
"no live effect unless active" holds independently of the caller. append_ledger
serves only the orb's "rls" writeback (engine.py); the derived
processor/temporal/rls ledgers are written elsewhere (state/derived/*) and are
unaffected.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, ContextManager

import aiofiles


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LiveDataQuadStore:
    """Concrete DataQuadStoreProtocol backed by the Verus LAB state directory.

    Activation is controlled by AEGIS_RLS_ACTIVE (env var or constructor arg).
    When inactive, record_relation and orb evidence are true no-ops — the
    store-side gate the C3 examination confirmed.
    """

    def __init__(
        self,
        state_root: str | Path,
        *,
        peer_id: str = "verus",
        rls_active: bool | None = None,
    ) -> None:
        self._state_root = Path(state_root)
        self._peer_id = peer_id
        self._rls_active = (
            rls_active
            if rls_active is not None
            else os.environ.get("AEGIS_RLS_ACTIVE", "").lower() == "true"
        )
        self._dataquad_root = self._state_root / "dataquad"
        self._ledger_root = self._dataquad_root / "ledgers"
        self._relations_path = self._ledger_root / "relations.jsonl"
        self._tick_path = self._dataquad_root / "t_time.current"

    def is_active(self, capability: str) -> bool:
        if capability == "rls-persistent-relations-core":
            return self._rls_active
        return False

    def peer_root(self, peer_id: str) -> Path:
        return self._state_root / "peers" / peer_id

    async def get_next_tick(self, peer_id: str) -> int:
        if self._tick_path.exists():
            text = self._tick_path.read_text(encoding="utf-8").strip()
            try:
                return int(text) + 1
            except ValueError:
                pass
        return 1

    async def append_ledger(
        self, peer_id: str, ledger_name: str, entry: dict[str, Any]
    ) -> None:
        if not self._rls_active:
            return
        path = self._ledger_root / f"{ledger_name}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            entry, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
        async with aiofiles.open(path, mode="a", encoding="utf-8") as handle:
            await handle.write(line + "\n")

    async def record_relation(
        self,
        peer_id: str,
        from_id: str,
        to_id: str,
        *,
        relation: str,
        tags: list[str],
        written_by: str,
    ) -> None:
        if not self._rls_active:
            return
        entry = {
            "peer_id": peer_id,
            "from_id": from_id,
            "to_id": to_id,
            "relation": relation,
            "tags": tags,
            "written_by": written_by,
            "recorded_at": _now(),
        }
        self._relations_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            entry, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
        async with aiofiles.open(
            self._relations_path, mode="a", encoding="utf-8"
        ) as handle:
            await handle.write(line + "\n")


class WitnessEvent:
    """Minimal T-Time witness context manager for live turns."""

    def __init__(self, tick: int, *, witness_mode: str, pressure_level: str) -> None:
        self.tick = tick
        self.witness_mode = witness_mode
        self.pressure_level = pressure_level
        self._started_at = _now()

    def get_signature(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "witness_mode": self.witness_mode,
            "pressure_level": self.pressure_level,
            "started_at": self._started_at,
            "completed_at": _now(),
        }


@contextmanager
def witness_event_factory(
    tick: int, *, witness_mode: str = "observed", pressure_level: str = "unknown"
):
    ctx = WitnessEvent(tick, witness_mode=witness_mode, pressure_level=pressure_level)
    yield ctx.get_signature
