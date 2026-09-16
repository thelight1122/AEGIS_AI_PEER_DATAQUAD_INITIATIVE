"""Processor daemon — relation mapping, context assembly, and RLS orchestration.

The Processor determines the relations between data across all four tensors.
It queries the Steward (PCT/NCT), Advocate (PEER/SPINE), and Temporal daemons
to find relevant records, maps their relations, and assembles focused context
to send to the Frontier model for processing.

At P1, the Processor also orchestrates the RLS orb engine: when a turn begins,
it wires the live store and daemon-backed protocol adapters into the verified
RecursiveLearningEngine and runs execute_session against live DataQuad data.

This is the orchestrator — when begin_turn needs context, the Processor:
1. Receives the prompt
2. Extracts query terms
3. Queries Steward for relevant PCT/NCT data
4. Queries Advocate for relevant PEER/SPINE data
5. Queries Temporal for time context on the matched records
6. Maps relations across the results
7. (P1) Runs the RLS orb engine to score, select, and persist relations
8. Returns assembled, focused context
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from .daemon import BaseDaemon, DaemonClient
from .retrieval import (
    IndexedRecord, RetrievalIndex, extract_text, tokenize,
)


class ProcessorDaemon(BaseDaemon):
    """Long-running daemon that determines data relations and assembles context.

    At P1, also orchestrates the RLS orb engine when rls_active is True.
    """

    def __init__(
        self,
        socket_path: str | Path,
        release_root: str | Path,
        state_root: str | Path,
        *,
        steward_socket: str | Path | None = None,
        advocate_socket: str | Path | None = None,
        temporal_socket: str | Path | None = None,
        rls_active: bool | None = None,
        peer_id: str | None = None,
    ) -> None:
        super().__init__("Processor", socket_path)
        self._release_root = Path(release_root)
        self._state_root = Path(state_root)
        # Preserve the historical Verus default for existing deployments;
        # instance-specific services must pass an explicit peer id.
        self._peer_id = peer_id or os.environ.get("AEGIS_PEER_ID", "verus")
        daemon_dir = self._state_root / "daemons"
        self._steward = DaemonClient(steward_socket or daemon_dir / "steward.sock")
        self._advocate = DaemonClient(advocate_socket or daemon_dir / "advocate.sock")
        self._temporal = DaemonClient(temporal_socket or daemon_dir / "temporal.sock")

        self._all_index = RetrievalIndex()
        self._turn_map: dict[str, dict[str, Any]] = {}
        self._relation_graph: dict[str, set[str]] = defaultdict(set)

        self._rls_active = (
            rls_active
            if rls_active is not None
            else os.environ.get("AEGIS_RLS_ACTIVE", "").lower() == "true"
        )
        self._rls_engine = None

        self.add_watcher(
            "live_turns",
            self._state_root / "dataquad" / "ring4-turns.jsonl",
        )
        self.add_watcher(
            "processor_ledger",
            self._state_root / "derived" / "processor.jsonl",
        )

    def _init_rls_engine(self) -> Any:
        if self._rls_engine is not None:
            return self._rls_engine
        if not self._rls_active:
            return None
        try:
            from orb_rls_persistent_relations_core.engine import RecursiveLearningEngine
            from .live_store import LiveDataQuadStore, witness_event_factory
            from .protocol_adapters import LiveSteward, LiveAdvocate

            store = LiveDataQuadStore(
                self._state_root, peer_id=self._peer_id, rls_active=True,
            )
            self._rls_engine = RecursiveLearningEngine(
                store=store,
                steward_factory=lambda _store, _pid: LiveSteward(self._steward),
                advocate_factory=lambda _store, _pid: LiveAdvocate(self._advocate),
                witness_event=witness_event_factory,
            )
            return self._rls_engine
        except ImportError:
            return None

    def on_new_records(self, watcher_name: str, records: list[dict[str, Any]]) -> None:
        if watcher_name == "live_turns":
            self._index_turns(records)
        elif watcher_name == "processor_ledger":
            self._build_relations(records)

    def _index_turns(self, turns: list[dict[str, Any]]) -> None:
        for turn in turns:
            turn_id = turn.get("turn_id", "")
            t_time = turn.get("t_time")
            self._turn_map[turn_id] = {
                "turn_id": turn_id,
                "t_time": t_time,
                "observed_at": turn.get("observed_at"),
                "prompt_sha256": turn.get("prompt", {}).get("sha256"),
                "response_sha256": turn.get("response", {}).get("sha256"),
                "record_hash": turn.get("record_hash"),
                "append_count": len(turn.get("appends", [])),
                "tensors_touched": list({
                    a.get("tensor") for a in turn.get("appends", [])
                }),
            }
            text = extract_text(turn)
            record_id = f"turn:{turn_id}"
            self._all_index.add(IndexedRecord(
                record_id=record_id,
                record=turn,
                tokens=tokenize(text),
                source="live",
                tensor="ALL",
                turn_id=turn_id,
                t_time=t_time,
            ))

    def _build_relations(self, admissions: list[dict[str, Any]]) -> None:
        for admission in admissions:
            turn_id = admission.get("turn_id", "")
            steward_tensors = set(admission.get("steward_changes", {}).keys())
            advocate_tensors = set(admission.get("advocate_changes", {}).keys())
            all_tensors = steward_tensors | advocate_tensors
            for tensor in all_tensors:
                self._relation_graph[turn_id].add(tensor)
                self._relation_graph[f"tensor:{tensor}"].add(turn_id)

    def op_context(self, params: dict[str, Any]) -> dict[str, Any]:
        """Assemble focused context for a prompt by querying all three daemons.

        This is the primary operation called during begin_turn.
        """
        prompt = params.get("prompt", "")
        limit = min(params.get("limit", 30), 100)
        keywords = tokenize(prompt)

        steward_results = self._query_steward(keywords, limit)
        advocate_results = self._query_advocate(keywords, limit)

        t_times = set()
        for record in steward_results + advocate_results:
            t = record.get("t_time")
            if t is not None:
                t_times.add(t)

        temporal_context = self._query_temporal(sorted(t_times))

        local_matches = self._all_index.search(keywords, limit=limit)

        relations = self._map_relations(steward_results, advocate_results, local_matches)

        context = {
            "assembled": True,
            "prompt_keywords": keywords[:20],
            "steward": {
                "source": "Steward daemon",
                "tensors": ["PCT", "NCT"],
                "records": steward_results,
                "count": len(steward_results),
            },
            "advocate": {
                "source": "Advocate daemon",
                "tensors": ["PEER", "SPINE"],
                "records": advocate_results,
                "count": len(advocate_results),
            },
            "temporal": temporal_context,
            "relations": relations,
            "turn_count": len(self._turn_map),
            "rls_active": self._rls_active,
        }

        if self._rls_active:
            session_id = params.get("session_id", "")
            if session_id and prompt:
                try:
                    rls_result = self.op_rls_session({
                        "peer_id": params.get("peer_id", self._peer_id),
                        "session_id": session_id,
                        "prompt": prompt,
                        "intent": params.get("intent", "context_retrieval"),
                        "pressure_state": params.get("pressure_state", {}),
                        "nature_aspects": params.get("nature_aspects", []),
                    })
                    context["rls"] = rls_result
                except Exception as exc:
                    context["rls"] = {"executed": False, "error": str(exc)[:512]}

        return context

    def _query_steward(self, keywords: list[str], limit: int) -> list[dict[str, Any]]:
        if not self._steward.available:
            return []
        try:
            response = self._steward.query("search", {
                "keywords": keywords, "limit": limit,
            })
            return response.get("result", [])
        except Exception:
            return []

    def _query_advocate(self, keywords: list[str], limit: int) -> list[dict[str, Any]]:
        if not self._advocate.available:
            return []
        try:
            response = self._advocate.query("search", {
                "keywords": keywords, "limit": limit,
            })
            return response.get("result", [])
        except Exception:
            return []

    def _query_temporal(self, t_times: list[int]) -> dict[str, Any]:
        if not self._temporal.available or not t_times:
            return {"available": False, "observations": []}
        try:
            response = self._temporal.query("time_context", {"t_times": t_times})
            result = response.get("result", {})
            result["available"] = True
            return result
        except Exception:
            return {"available": False, "observations": []}

    def _map_relations(
        self,
        steward_records: list[dict[str, Any]],
        advocate_records: list[dict[str, Any]],
        local_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Map relations across results from all sources."""
        turn_ids_steward = {
            r.get("turn_id") for r in steward_records if r.get("turn_id")
        }
        turn_ids_advocate = {
            r.get("turn_id") for r in advocate_records if r.get("turn_id")
        }
        shared_turns = turn_ids_steward & turn_ids_advocate

        tensor_co_occurrence: dict[str, list[str]] = defaultdict(list)
        for turn_id in shared_turns:
            tensors = self._relation_graph.get(turn_id, set())
            for tensor in tensors:
                tensor_co_occurrence[tensor].append(turn_id)

        return {
            "steward_turn_ids": sorted(turn_ids_steward),
            "advocate_turn_ids": sorted(turn_ids_advocate),
            "shared_turns": sorted(shared_turns),
            "tensor_co_occurrence": {
                k: v for k, v in tensor_co_occurrence.items()
            },
        }

    def op_rls_session(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an RLS session through the verified orb engine.

        This is the P1 live path: the Processor wires the daemon-backed
        protocol adapters and live store into the orb, runs execute_session,
        and returns the scored/partitioned result with persistent relations.
        """
        engine = self._init_rls_engine()
        if engine is None:
            return {
                "executed": False,
                "reason": "RLS engine not active (AEGIS_RLS_ACTIVE != true or orb not installed)",
            }
        peer_id = params.get("peer_id", self._peer_id)
        session_id = params.get("session_id", "")
        prompt = params.get("prompt", "")
        intent = params.get("intent", "context_retrieval")
        pressure_state = params.get("pressure_state", {})
        nature_aspects = params.get("nature_aspects", [])
        if not session_id or not prompt:
            raise ValueError("session_id and prompt are required")

        loop = asyncio.new_event_loop()
        try:
            session = loop.run_until_complete(engine.execute_session(
                peer_id=peer_id,
                session_id=session_id,
                user_message=prompt,
                intent=intent,
                pressure_state=pressure_state,
                nature_aspects=nature_aspects,
                writeback_enabled=True,
            ))
            import orjson
            result = orjson.loads(session.model_dump_json())
            return {
                "executed": True,
                "rls_id": session.id,
                "selected_count": len(session.selected_refs),
                "rejected_count": len(session.rejected_refs),
                "shortfall_is_data": session.shortfall_is_data,
                "shortfall_reason": session.shortfall_reason,
                "failure_is_data": session.failure_is_data,
                "created_pct_record_id": session.created_pct_record_id,
                "session": result,
            }
        finally:
            loop.close()

    def op_relations(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get relations for a specific turn."""
        turn_id = params.get("turn_id", "")
        if not turn_id:
            raise ValueError("turn_id is required")
        related_tensors = sorted(self._relation_graph.get(turn_id, set()))
        related_turns: set[str] = set()
        for tensor in related_tensors:
            related_turns.update(self._relation_graph.get(f"tensor:{tensor}", set()))
        related_turns.discard(turn_id)
        turn_info = self._turn_map.get(turn_id)
        return {
            "turn_id": turn_id,
            "turn_info": turn_info,
            "related_tensors": related_tensors,
            "related_turns": sorted(related_turns),
        }

    def op_turn_map(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get the full turn map."""
        return {
            "total_turns": len(self._turn_map),
            "turns": list(self._turn_map.values()),
        }

    def op_count(self, params: dict[str, Any]) -> dict[str, Any]:
        """Count indexed records and relations."""
        return {
            "turns": len(self._turn_map),
            "indexed_records": self._all_index.record_count,
            "relation_nodes": len(self._relation_graph),
        }

    def op_health(self, params: dict[str, Any]) -> dict[str, Any]:
        steward_ok = self._steward.available
        advocate_ok = self._advocate.available
        temporal_ok = self._temporal.available
        all_ok = steward_ok and advocate_ok and temporal_ok
        rls_engine_loaded = self._rls_engine is not None
        return {
            "daemon": self.name,
            "status": "ok" if all_ok else "degraded",
            "running": self._running,
            "turns_indexed": len(self._turn_map),
            "relation_nodes": len(self._relation_graph),
            "steward_available": steward_ok,
            "advocate_available": advocate_ok,
            "temporal_available": temporal_ok,
            "rls_active": self._rls_active,
            "rls_engine_loaded": rls_engine_loaded,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Processor daemon — relation mapping and context assembly")
    parser.add_argument("--socket", type=Path, default=Path("/var/lib/aegis-verus-lab/daemons/processor.sock"))
    parser.add_argument("--release-root", type=Path, default=Path("/opt/aegis/verus/lab/current/foundation"))
    parser.add_argument("--state-root", type=Path, default=Path("/var/lib/aegis-verus-lab"))
    parser.add_argument("--rls-active", action="store_true", default=None,
                        help="Activate the RLS orb engine (P1). Also reads AEGIS_RLS_ACTIVE env var.")
    parser.add_argument("--peer-id", default=None,
                        help="Bound peer/DataQuad id (defaults to AEGIS_PEER_ID or verus).")
    args = parser.parse_args()

    daemon = ProcessorDaemon(
        args.socket, args.release_root, args.state_root,
        rls_active=args.rls_active, peer_id=args.peer_id,
    )
    daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
