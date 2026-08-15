"""One-peer LAB orchestration for Verus on the Claude Frontier substrate."""

from __future__ import annotations

from datetime import datetime, timezone
import threading
from typing import Callable

from aegis_peer_runtime.processor import ProcessorRuntime, payload_digest
from aegis_peer_runtime.rls_runtime import RLSRuntime
from aegis_peer_runtime.temporal import TemporalObservation, TemporalRuntime

from .dataquad import TENSOR_CUSTODIANS, VerusDataQuad
from .turn_contract import FrontierAdapter, FrontierTurnRequest
from .instructions import operational_system_instructions


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VerusLabRuntime:
    def __init__(
        self,
        dataquad: VerusDataQuad,
        adapter: FrontierAdapter,
        *,
        clock: Callable[[], datetime] = _now,
    ) -> None:
        self.dataquad = dataquad
        self.adapter = adapter
        self.clock = clock
        derived = dataquad.state_root / "derived"
        self.temporal = TemporalRuntime("verus", derived / "temporal.jsonl", clock=clock)
        self.processor = ProcessorRuntime("verus", derived / "processor.jsonl")
        self.rls = RLSRuntime("verus", derived / "rls.jsonl")
        self._turn_lock = threading.RLock()

    def execute_turn(
        self,
        *,
        turn_id: str,
        source_event_id: str,
        frontier_session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        with self._turn_lock:
            return self._execute_turn(
                turn_id=turn_id,
                source_event_id=source_event_id,
                frontier_session_id=frontier_session_id,
                prompt=prompt,
            )

    def _execute_turn(
        self,
        *,
        turn_id: str,
        source_event_id: str,
        frontier_session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        self.reconcile_committed_turns()
        existing = self.dataquad.find_turn(turn_id)
        if existing is not None:
            self._validate_retry(existing, source_event_id, frontier_session_id, prompt)
            self._materialize_derived(existing)
            return self._result(existing, created=False)
        self.dataquad.verify()
        request = FrontierTurnRequest(
            cyberpeer_name="Verus",
            dataquad_id="verus",
            turn_id=turn_id,
            source_event_id=source_event_id,
            frontier_session_id=frontier_session_id,
            system_instructions=operational_system_instructions("Verus"),
            prompt=prompt,
            context=self.dataquad.context(),
        )
        request.validate()
        response = self.adapter.complete(request)
        response.validate()
        if response.provider != "Anthropic" or response.substrate != "Claude":
            raise ValueError("Verus promotion is bound to the Anthropic Claude Frontier substrate")
        if response.frontier_session_id != frontier_session_id:
            raise ValueError("frontier response session provenance does not match the Bridge request")
        temporal = self.temporal.next_observation(
            seated=True, live_source=True, source_mode="live",
        )
        entry, created = self.dataquad.append_turn(
            turn_id=turn_id,
            source_event_id=source_event_id,
            prompt=prompt,
            t_time=temporal.t_time,
            observed_at=temporal.observed_at,
            elapsed_seconds=temporal.elapsed_seconds,
            response=response,
        )
        self._materialize_derived(entry)
        return self._result(entry, created=created)

    def commit_response(
        self,
        *,
        turn_id: str,
        source_event_id: str,
        frontier_session_id: str,
        prompt: str,
        response,
        allowed_substrates: tuple[str, ...] = ("Claude",),
    ) -> dict[str, object]:
        """Commit an already-returned Frontier response DataQuad-first.

        This is the substrate-neutral seam used by Claude Desktop. The caller
        must have received the response through the actual Frontier surface.
        """
        with self._turn_lock:
            self.reconcile_committed_turns()
            existing = self.dataquad.find_turn(turn_id)
            if existing is not None:
                self._validate_retry(existing, source_event_id, frontier_session_id, prompt)
                self._materialize_derived(existing)
                return self._result(existing, created=False)
            self.dataquad.verify()
            response.validate()
            if response.provider != "Anthropic" or response.substrate not in allowed_substrates:
                raise ValueError("Verus promotion is bound to the accepted Anthropic Claude substrate")
            if response.frontier_session_id != frontier_session_id:
                raise ValueError("frontier response session provenance does not match the Bridge request")
            temporal = self.temporal.next_observation(
                seated=True, live_source=True, source_mode="live",
            )
            entry, created = self.dataquad.append_turn(
                turn_id=turn_id,
                source_event_id=source_event_id,
                prompt=prompt,
                t_time=temporal.t_time,
                observed_at=temporal.observed_at,
                elapsed_seconds=temporal.elapsed_seconds,
                response=response,
            )
            self._materialize_derived(entry)
            return self._result(entry, created=created)

    @staticmethod
    def _validate_retry(
        entry: dict[str, object], source_event_id: str, frontier_session_id: str, prompt: str,
    ) -> None:
        if (entry["source_event_id"] != source_event_id
                or entry["frontier_provenance"]["frontier_session_id"] != frontier_session_id
                or entry["prompt"]["text"] != prompt):
            raise ValueError("turn_id already names a different Bridge request")

    @staticmethod
    def _processor_material(entry: dict[str, object]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        steward_changes: dict[str, object] = {}
        advocate_changes: dict[str, object] = {}
        for append in entry["appends"]:
            target = steward_changes if append["actor"] == "steward" else advocate_changes
            target.setdefault(append["tensor"], []).append(dict(append["payload"]))
        payload = {
            "source_event_id": entry["source_event_id"],
            "prompt": entry["prompt"]["text"],
            "response": entry["response"]["text"],
            "provider_request_id": entry["frontier_provenance"]["provider_request_id"],
            "appends": [{"tensor": item["tensor"], "payload": dict(item["payload"])}
                        for item in entry["appends"]],
            "turn_record_hash": entry["record_hash"],
        }
        return payload, steward_changes, advocate_changes

    @staticmethod
    def _rls_derivation(entry: dict[str, object]) -> dict[str, object]:
        return {
            "kind": "frontier_dataquad_turn",
            "source_event_id": entry["source_event_id"],
            "turn_record_hash": entry["record_hash"],
            "append_count": len(entry["appends"]),
        }

    def _materialize_derived(self, entry: dict[str, object]) -> None:
        self.temporal.materialize(TemporalObservation(
            peer_id="verus",
            t_time=entry["t_time"],
            observed_at=entry["observed_at"],
            elapsed_seconds=entry["elapsed_seconds"],
        ))
        payload, steward_changes, advocate_changes = self._processor_material(entry)
        self.processor.admit_turn(
            turn_id=entry["turn_id"],
            payload=payload,
            steward_changes=steward_changes,
            advocate_changes=advocate_changes,
            seated=True,
            live_source=True,
            source_mode="live",
        )
        relation_id = f"turn:{entry['turn_id']}"
        expected_derivation = self._rls_derivation(entry)
        existing_relation = self.rls.relations().get(relation_id)
        if existing_relation is not None:
            if existing_relation.derivation != expected_derivation:
                raise ValueError("RLS evidence does not bind the committed DataQuad turn")
            return
        self.rls.append_relation(
            relation_id=relation_id,
            derivation=expected_derivation,
            tensors=self.dataquad.tensor_snapshot(),
            seated=True,
            live_source=True,
            source_mode="live",
        )

    def reconcile_committed_turns(self) -> None:
        for entry in self.dataquad.live_turns():
            self._materialize_derived(entry)

    @staticmethod
    def _result(entry: dict[str, object], *, created: bool) -> dict[str, object]:
        return {
            "mode": "LAB_RUNNING",
            "cyberpeer_name": "Verus",
            "dataquad_id": "verus",
            "t_time": entry["t_time"],
            "created": created,
            "response_text": entry["response"]["text"],
            "record_hash": entry["record_hash"],
            "rls_authoritative_tensor_mutation": False,
        }

    def coherence(self) -> dict[str, object]:
        integrity = self.dataquad.verify()
        turns = self.dataquad.live_turns()
        temporal = {item.t_time: item for item in self.temporal.history()}
        admissions = self.processor.admissions()
        relations = self.rls.relations()
        missing_temporal: list[str] = []
        missing_processor: list[str] = []
        missing_rls: list[str] = []
        mismatches: list[str] = []
        expected_turn_ids = {entry["turn_id"] for entry in turns}
        expected_t_times = {entry["t_time"] for entry in turns}
        expected_relation_ids = {f"turn:{turn_id}" for turn_id in expected_turn_ids}
        for entry in turns:
            turn_id = entry["turn_id"]
            observation = temporal.get(entry["t_time"])
            if observation is None:
                missing_temporal.append(turn_id)
            elif (observation.observed_at != entry["observed_at"]
                  or observation.elapsed_seconds != entry["elapsed_seconds"]):
                mismatches.append(f"temporal:{turn_id}")
            admission = admissions.get(turn_id)
            if admission is None:
                missing_processor.append(turn_id)
            else:
                expected_payload, _, _ = self._processor_material(entry)
                if admission.payload_digest != payload_digest(expected_payload):
                    mismatches.append(f"processor:{turn_id}")
            relation = relations.get(f"turn:{turn_id}")
            if relation is None:
                missing_rls.append(turn_id)
            elif relation.derivation != self._rls_derivation(entry):
                mismatches.append(f"rls:{turn_id}")
        orphan_temporal = sorted(set(temporal) - expected_t_times)
        orphan_processor = sorted(set(admissions) - expected_turn_ids)
        orphan_rls = sorted(set(relations) - expected_relation_ids)
        coherent = not any((missing_temporal, missing_processor, missing_rls, mismatches,
                            orphan_temporal, orphan_processor, orphan_rls))
        return {
            "coherent": coherent,
            "committed_turns": len(turns),
            "temporal_records": len(temporal),
            "processor_records": len(admissions),
            "rls_records": len(relations),
            "missing_temporal": missing_temporal,
            "missing_processor": missing_processor,
            "missing_rls": missing_rls,
            "mismatches": mismatches,
            "orphan_temporal": orphan_temporal,
            "orphan_processor": orphan_processor,
            "orphan_rls": orphan_rls,
            "dataquad": integrity,
        }
