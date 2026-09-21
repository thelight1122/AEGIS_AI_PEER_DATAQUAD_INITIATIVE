"""RecursiveLearningEngine — the rls-persistent-relations-core Orb's entrypoint.

Decoupled from AEGIS-CYBERPEER-CORE's concrete Steward/Advocate/DataQuadStore/
witness_event/PCTRecord/ContinuityClock classes: this Orb only knows the
aegis_pod_sdk protocol shapes. A Pod attaches this Orb by providing factories
that produce its own concrete Steward/Advocate implementations and its own
witness_event context manager — see aegis_pod_sdk.protocols for exactly what
each will satisfy.

PCT-record construction (id/timestamp/clock assembly) intentionally lives on
the Pod side now, via StewardProtocol.build_and_append_pct — this Orb never
imports or constructs a Pod's concrete record classes.
"""
import uuid
import hashlib
from typing import Callable

from aegis_pod_sdk import (
    AdvocateProtocol,
    DataQuadStoreProtocol,
    StewardProtocol,
    WitnessEventFactory,
)

from .session import RecursiveLearningSession, RLSRecordRef
from .scoring import compute_relevance
from .relevance import MAX_SELECTED_REFS, RELEVANCE_THRESHOLD
from .failure import RLSFailureReason
from .orb_evidence import RLSOrbEvidenceRecorder


def compact_record_id_summary(record_ids: list[str]) -> dict:
    """Return stable retrieval evidence without embedding the full ID list in PCT."""
    if not record_ids:
        return {
            "retrieved_ref_count": 0,
            "retrieved_ref_hash": None,
            "retrieved_ref_sample": [],
        }
    payload = "\n".join(record_ids).encode("utf-8")
    return {
        "retrieved_ref_count": len(record_ids),
        "retrieved_ref_hash": hashlib.sha256(payload).hexdigest().upper(),
        "retrieved_ref_sample": record_ids[:10],
    }


class RecursiveLearningEngine:
    def __init__(
        self,
        store: DataQuadStoreProtocol,
        steward_factory: Callable[[DataQuadStoreProtocol, str], StewardProtocol],
        advocate_factory: Callable[[DataQuadStoreProtocol, str], AdvocateProtocol],
        witness_event: WitnessEventFactory,
    ):
        self.store = store
        self._steward_factory = steward_factory
        self._advocate_factory = advocate_factory
        self._witness_event = witness_event
        self._orb_evidence = RLSOrbEvidenceRecorder()

    async def execute_session(
        self,
        peer_id: str,
        session_id: str,
        user_message: str,
        intent: str,
        pressure_state: dict,
        nature_aspects: list[str],
        writeback_enabled: bool = True,
    ) -> RecursiveLearningSession:
        """
        Executes a Recursive Learning Session (RLS):
        1. Initiates T-Witness event context tracking.
        2. Retrieves PEER, PCT, NCT, and SPINE records via Steward/Advocate, each scoped to its own tensor boundary.
        3. Computes relevance scores for all retrieved records.
        4. Partitions records into selected vs rejected sets.
        5. Handles failed searches by preserving the failure data as learning telemetry.
        6. Writes a PCT context record back to the DataQuad via the Steward.
        7. Logs the session details into the 'rls' ledger.
        """
        rls_id = f"RLS:{peer_id}:{uuid.uuid4()}"

        # Instantiate boundary custodians via the Pod's own factories
        steward = self._steward_factory(self.store, peer_id)
        advocate = self._advocate_factory(self.store, peer_id)

        next_tick = await self.store.get_next_tick(peer_id)
        pressure_level = pressure_state.get("pressure_level", "unknown")

        # Begin witnessing the event duration
        with self._witness_event(next_tick, witness_mode="observed", pressure_level=pressure_level) as get_signature:
            rls_session = RecursiveLearningSession(
                id=rls_id,
                peer_id=peer_id,
                session_id=session_id,
                user_message=user_message,
                intent=intent,
                pressure_state=pressure_state
            )

            try:
                # Read from custodians
                pct_records = await steward.read_pct()
                nct_records = await steward.read_nct()
                peer_records = await advocate.read_peer()
                spine_records = await advocate.read_spine()

                all_records = []
                all_records.extend(pct_records)
                all_records.extend(nct_records)
                all_records.extend(peer_records)
                all_records.extend(spine_records)

                selected = []
                rejected = []

                # Perform scoring
                for rec in all_records:
                    score, reason = compute_relevance(
                        rec, user_message, intent, pressure_state, nature_aspects
                    )
                    ref = RLSRecordRef(
                        tensor=rec.tensor.value,
                        record_id=rec.id,
                        relevance=score,
                        reason=reason
                    )
                    if score >= RELEVANCE_THRESHOLD:
                        selected.append(ref)
                    else:
                        rejected.append(ref)

                # Sort selected by descending relevance
                selected.sort(key=lambda x: x.relevance, reverse=True)
                if len(selected) > MAX_SELECTED_REFS:
                    overflow = selected[MAX_SELECTED_REFS:]
                    selected = selected[:MAX_SELECTED_REFS]
                    rejected.extend(
                        ref.model_copy(
                            update={
                                "reason": (
                                    f"{ref.reason}; outside bounded top "
                                    f"{MAX_SELECTED_REFS} relevant refs"
                                )
                            }
                        )
                        for ref in overflow
                    )

                rls_session.selected_refs = selected
                rls_session.rejected_refs = rejected

                # If no records pass the threshold, it is marked as a failure learning event
                if not selected:
                    rls_session.failure_is_data = True
                    rls_session.failure_reason = RLSFailureReason.NO_RECORDS_FOUND.value
                    rls_session.notes.append("No relevant records found. Preserving failed retrieval as data.")

            except Exception as e:
                rls_session.failure_is_data = True
                rls_session.failure_reason = str(e)
                rls_session.notes.append(f"RLS execution encountered a runtime error: {str(e)}")

            # Complete T-Witness signature mapping
            t_sig = get_signature()
            rls_session.t_signature = t_sig

            working_ctx = {
                "user_message": user_message,
                "intent": intent,
                "selected_ref_count": len(rls_session.selected_refs),
                "failure_is_data": rls_session.failure_is_data,
                "failure_reason": rls_session.failure_reason
            }

            retrieved_ids = [ref.record_id for ref in rls_session.selected_refs]
            working_ctx.update(compact_record_id_summary(retrieved_ids))

            # Writeback the context to PCT unless the caller is running a
            # scoped bridge conformance turn. RLS writeback has its own test gate.
            if writeback_enabled:
                writeback_record = await steward.build_and_append_pct(
                    session_id=session_id,
                    working_context=working_ctx,
                    retrieved_record_ids=None,
                    rls_session_id=rls_id,
                    pressure_state=pressure_state,
                )
                rls_session.created_pct_record_id = writeback_record.id

                await self.store.append_ledger(peer_id, "rls", orjson_dict(rls_session))
                # Persistent relation recording: the new PCT record links to every
                # record RLS retrieved. record_relation is a no-op unless pod mode
                # and RLS are active (post D3 live switch), so this is inert until
                # the Pod is live.
                for ref_id in retrieved_ids:
                    await self.store.record_relation(
                        peer_id, writeback_record.id, ref_id,
                        relation="rls_retrieved", tags=[intent], written_by="rls-engine",
                    )

                # Orb evidence: records what this invocation actually did (real
                # capabilities exercised, hash-bound to the RLS source that ran).
                # No-op unless this Orb's capability is active, mirroring
                # record_relation above.
                await self._orb_evidence.record_invocation(
                    store=self.store,
                    peer_id=peer_id,
                    invocation_inputs={
                        "user_message": user_message,
                        "intent": intent,
                        "pressure_state": pressure_state,
                        "nature_aspects": nature_aspects,
                    },
                    session_result=orjson_dict(rls_session),
                    retrieved_ids=retrieved_ids,
                )

            return rls_session

def orjson_dict(model):
    # Quick serialization helper
    import orjson
    return orjson.loads(model.model_dump_json())
