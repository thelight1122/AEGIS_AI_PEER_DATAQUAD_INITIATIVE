"""Advocate daemon — PEER/SPINE data retrieval operator.

The Advocate knows how to find and reveal data from its tensors (PEER and SPINE).
It does not make decisions about what is important. It searches, filters,
and serves records on demand. The Processor determines what to ask for.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .daemon import BaseDaemon
from .retrieval import IndexedRecord, RetrievalIndex, extract_text, tokenize


class AdvocateDaemon(BaseDaemon):
    """Long-running retrieval operator for PEER (Present Experiential Record)
    and SPINE (Sovereign Identity Continuity) tensors."""

    TENSORS = ("PEER", "SPINE")

    def __init__(
        self,
        socket_path: str | Path,
        release_root: str | Path,
        state_root: str | Path,
    ) -> None:
        super().__init__("Advocate", socket_path)
        self._release_root = Path(release_root)
        self._state_root = Path(state_root)
        self._index = RetrievalIndex()
        self._foundation_loaded = False

        self.add_watcher(
            "live_turns",
            self._state_root / "dataquad" / "ring4-turns.jsonl",
        )

    def on_start(self) -> None:
        self._load_foundation()

    def _load_foundation(self) -> None:
        if self._foundation_loaded:
            return
        foundation_root = self._release_root / "dataquad"
        for tensor in self.TENSORS:
            path = foundation_root / f"{tensor}.jsonl"
            if not path.exists():
                continue
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                record = json.loads(line)
                record_id = f"foundation:{tensor}:{i}"
                text = extract_text(record)
                self._index.add(IndexedRecord(
                    record_id=record_id,
                    record=record,
                    tokens=tokenize(text),
                    source="foundation",
                    tensor=tensor,
                ))
        self._foundation_loaded = True

    def on_new_records(self, watcher_name: str, records: list[dict[str, Any]]) -> None:
        if watcher_name != "live_turns":
            return
        for turn in records:
            turn_id = turn.get("turn_id", "")
            t_time = turn.get("t_time")
            prompt_text = turn.get("prompt", {}).get("text", "")
            response_text = turn.get("response", {}).get("text", "")
            for i, append in enumerate(turn.get("appends", [])):
                tensor = append.get("tensor", "")
                if tensor not in self.TENSORS:
                    continue
                record_id = f"turn:{turn_id}:{tensor}:{i}"
                record_with_context = {
                    "tensor": tensor,
                    "turn_id": turn_id,
                    "t_time": t_time,
                    "custodian": append.get("custodian", ""),
                    "payload": append.get("payload", {}),
                    "prompt_context": prompt_text,
                    "response_context": response_text,
                    "record_hash": turn.get("record_hash", ""),
                    "observed_at": turn.get("observed_at", ""),
                }
                text = extract_text(record_with_context)
                self._index.add(IndexedRecord(
                    record_id=record_id,
                    record=record_with_context,
                    tokens=tokenize(text),
                    source="live",
                    tensor=tensor,
                    turn_id=turn_id,
                    t_time=t_time,
                ))

    def op_search(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Search PEER/SPINE records by keywords."""
        keywords = params.get("keywords", [])
        tensor = params.get("tensor")
        limit = min(params.get("limit", 50), 200)
        if tensor and tensor not in self.TENSORS:
            raise ValueError(f"Advocate does not own tensor: {tensor}")
        return self._index.search(keywords, tensor=tensor, limit=limit)

    def op_get_all(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Get all PEER/SPINE records, optionally filtered by tensor."""
        tensor = params.get("tensor")
        source = params.get("source")
        limit = min(params.get("limit", 200), 500)
        if tensor and tensor not in self.TENSORS:
            raise ValueError(f"Advocate does not own tensor: {tensor}")
        return self._index.get_all(tensor=tensor, source=source, limit=limit)

    def op_get_turn(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Get PEER/SPINE records from a specific turn."""
        turn_id = params.get("turn_id", "")
        if not turn_id:
            raise ValueError("turn_id is required")
        return self._index.get_by_turn(turn_id)

    def op_get_time_range(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Get PEER/SPINE records within a T-Time range."""
        start = params.get("start", 1)
        end = params.get("end", 999999)
        return self._index.get_by_time_range(start, end)

    def op_count(self, params: dict[str, Any]) -> dict[str, Any]:
        """Count indexed PEER/SPINE records."""
        return {
            "total": self._index.record_count,
            "by_tensor": self._index.tensor_counts(),
        }

    def op_health(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "daemon": self.name,
            "status": "ok",
            "running": self._running,
            "tensors": list(self.TENSORS),
            "indexed_records": self._index.record_count,
            "foundation_loaded": self._foundation_loaded,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Advocate daemon — PEER/SPINE retrieval operator")
    parser.add_argument("--socket", type=Path, default=Path("/var/lib/aegis-verus-lab/daemons/advocate.sock"))
    parser.add_argument("--release-root", type=Path, default=Path("/opt/aegis/verus/lab/current/foundation"))
    parser.add_argument("--state-root", type=Path, default=Path("/var/lib/aegis-verus-lab"))
    args = parser.parse_args()

    daemon = AdvocateDaemon(args.socket, args.release_root, args.state_root)
    daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
