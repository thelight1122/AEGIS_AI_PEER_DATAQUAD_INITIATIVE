"""Protocol adapters — wrap live daemon clients into aegis_pod_sdk protocols.

The Steward/Advocate daemons are long-running retrieval operators that own
tensor data. These adapters present their daemon-client interfaces as the
StewardProtocol and AdvocateProtocol the RLS orb engine expects.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .daemon import DaemonClient


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecordClock:
    """Minimal ClockLike exposing the tick the orb scorer reads.

    The orb reads only .tick (recency bonus). Nothing else is promised.
    """

    __slots__ = ("tick",)

    def __init__(self, tick: int) -> None:
        self.tick = tick


def _flatten_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Lift a turn record's payload to the top level.

    Foundation records carry their scored text (pattern, distilled_summary,
    essence_memory, present_state, working_context) at the top level of data.
    Turn-derived records nest the same fields one level down under "payload".
    scoring.py reads them by attribute name, so without this lift every
    turn-derived record presents as empty text and scores exactly 0.0 —
    the whole lived history is unreachable and only the seed is selectable.
    """
    payload = data.get("payload")
    if isinstance(payload, dict):
        return {**data, **payload}
    return data


def _clock_from(data: dict[str, Any]) -> RecordClock | None:
    """Derive the scorer's tick from whichever counter the record carries.

    Foundation records carry a clock mapping with a tick. Turn-derived records
    carry t_time, the peer's own monotonic turn counter — the same quantity the
    recency bonus is reaching for.
    """
    clock = data.get("clock")
    tick = clock.get("tick") if isinstance(clock, dict) else data.get("t_time")
    if isinstance(tick, bool) or not isinstance(tick, int) or tick <= 0:
        return None
    return RecordClock(tick)


# Turn-level and provenance keys: real, but not the record's experiential content.
_PEER_NON_AFFECT_KEYS = frozenset({
    "identity_assertion", "tensor", "turn_id", "record_hash", "custodian",
    "observed_at", "t_time", "prompt_context", "response_context",
})


def _peer_scorable_text(data: dict[str, Any]) -> str | None:
    """Present a PEER record's own words where the orb scorer can read them.

    scoring.py reads five fields and all five are digest shapes. PEER is the one
    tensor the recording protocol deliberately keeps raw, so its affect lands in
    free-form keys the scorer never opens — recognition, unease, steadiness — and
    scores zero however well it matches. Context becomes retrievable and the
    experience attached to it does not.

    This concatenates the record's existing string values verbatim. It does not
    summarise, infer, rank, or author: no text appears here that the record did
    not already contain, so nothing interpretive is introduced on the read path.
    The record's own present_state stays first when it has one.
    """
    present = data.get("present_state")
    parts = [str(present)] if isinstance(present, str) and present else []
    for key, value in data.items():
        if key == "present_state" or key in _PEER_NON_AFFECT_KEYS:
            continue
        if isinstance(value, str) and value.strip():
            parts.append(value)
    text = " ".join(parts).strip()
    return text or None


class DaemonRecord:
    """Minimal RecordLike wrapping a daemon search result.

    Satisfies the aegis_pod_sdk RecordLike protocol: .id, .tensor, .clock.
    Additional fields (present_state, working_context, etc.) are surfaced
    via __getattr__ for scoring.py's defensive hasattr/getattr access.
    """

    __slots__ = ("id", "_tensor_str", "clock", "_extra")

    def __init__(self, record_id: str, tensor: str, data: dict[str, Any]) -> None:
        self.id = record_id
        self._tensor_str = tensor
        self.clock = _clock_from(data)
        extra = _flatten_payload(data)
        if tensor == "PEER":
            scorable = _peer_scorable_text(extra)
            if scorable:
                extra = {**extra, "present_state": scorable}
        self._extra = extra

    @property
    def tensor(self) -> Any:
        try:
            from aegis_pod_sdk import TensorKind
            return TensorKind(self._tensor_str)
        except (ImportError, ValueError):
            return self._tensor_str

    def __getattr__(self, name: str) -> Any:
        try:
            return self._extra[name]
        except KeyError:
            raise AttributeError(name)


def _records_from_daemon(results: list[dict[str, Any]]) -> list[DaemonRecord]:
    records = []
    for item in results:
        record_id = item.get("record_id", "")
        tensor = item.get("tensor", "")
        data = item.get("data", item)
        rec = DaemonRecord(record_id, tensor, data if isinstance(data, dict) else {})
        records.append(rec)
    return records


class LiveSteward:
    """StewardProtocol adapter over the Steward daemon client."""

    def __init__(self, client: DaemonClient) -> None:
        self._client = client

    async def read_pct(self) -> list[DaemonRecord]:
        if not self._client.available:
            return []
        response = self._client.query("get_all", {"tensor": "PCT", "limit": 200})
        return _records_from_daemon(response.get("result", []))

    async def read_nct(self) -> list[DaemonRecord]:
        if not self._client.available:
            return []
        response = self._client.query("get_all", {"tensor": "NCT", "limit": 200})
        return _records_from_daemon(response.get("result", []))

    async def build_and_append_pct(
        self,
        *,
        session_id: str,
        working_context: dict[str, Any],
        retrieved_record_ids: list[str] | None,
        rls_session_id: str,
        pressure_state: dict[str, Any],
    ) -> DaemonRecord:
        record_id = f"PCT:{session_id}:{uuid.uuid4()}"
        record_data = {
            "type": "PCT",
            "session_id": session_id,
            "rls_session_id": rls_session_id,
            "working_context": working_context,
            "retrieved_record_ids": retrieved_record_ids,
            "pressure_state": pressure_state,
            "created_at": _now(),
        }
        return DaemonRecord(record_id, "PCT", record_data)


class LiveAdvocate:
    """AdvocateProtocol adapter over the Advocate daemon client."""

    def __init__(self, client: DaemonClient) -> None:
        self._client = client

    async def read_peer(self) -> list[DaemonRecord]:
        if not self._client.available:
            return []
        response = self._client.query("get_all", {"tensor": "PEER", "limit": 200})
        return _records_from_daemon(response.get("result", []))

    async def read_spine(self) -> list[DaemonRecord]:
        if not self._client.available:
            return []
        response = self._client.query("get_all", {"tensor": "SPINE", "limit": 200})
        return _records_from_daemon(response.get("result", []))
