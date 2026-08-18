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
        self.clock = None
        self._extra = data

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
