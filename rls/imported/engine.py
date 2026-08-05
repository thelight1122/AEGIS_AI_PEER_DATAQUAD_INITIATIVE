import uuid
from datetime import datetime, timezone
from core.dataquad.ledgers import DataQuadStore
from core.custodians.steward import Steward
from core.custodians.advocate import Advocate
from core.dataquad.twitness import witness_event
from core.dataquad.records import PCTRecord, ContinuityClock
from core.rls.session import RecursiveLearningSession, RLSRecordRef
from core.rls.scoring import compute_relevance
from core.rls.relevance import RELEVANCE_THRESHOLD
from core.rls.failure import RLSFailureReason

class RecursiveLearningEngine:
    def __init__(self, store: DataQuadStore):
        self.store = store

    async def execute_session(
        self,
        peer_id: str,
        session_id: str,
        user_message: str,
        intent: str,
        pressure_state: dict,
        nature_aspects: list[str]
    ) -> RecursiveLearningSession:
        """
        Executes a Recursive Learning Session (RLS):
        1. Initiates T-Witness event context tracking.
        2. Retrieves PEER, PCT, NCT, and SPINE records via boundary-enforcing Steward/Advocate.
        3. Computes relevance scores for all retrieved records.
        4. Partitions records into selected vs rejected sets.
        5. Handles failed searches by preserving the failure data as learning telemetry.
        6. Writes a PCT context record back to the DataQuad via the Steward.
        7. Logs the session details into the 'rls' ledger.
        """
        rls_id = f"RLS:{peer_id}:{uuid.uuid4()}"
        
        # Instantiate boundaries custodians
        steward = Steward(self.store, peer_id)
        advocate = Advocate(self.store, peer_id)

        next_tick = await self.store.get_next_tick(peer_id)
        pressure_level = pressure_state.get("pressure_level", "unknown")
        
        # Begin witnessing the event duration
        with witness_event(next_tick, witness_mode="observed", pressure_level=pressure_level) as get_signature:
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

            # Construct working context details for the PCT writeback
            timestamp = datetime.now(timezone.utc).isoformat()
            clock = ContinuityClock(
                tick=next_tick,
                epoch="primary",
                phase="active",
                started_at=timestamp,
                last_advanced_at=timestamp
            )

            working_ctx = {
                "user_message": user_message,
                "intent": intent,
                "selected_ref_count": len(rls_session.selected_refs),
                "failure_is_data": rls_session.failure_is_data,
                "failure_reason": rls_session.failure_reason
            }

            retrieved_ids = [ref.record_id for ref in rls_session.selected_refs]
            
            writeback_record = PCTRecord(
                id=f"PCT:{peer_id}:{timestamp}:{next_tick}",
                timestamp=timestamp,
                session_id=session_id,
                clock=clock,
                working_context=working_ctx,
                retrieved_record_ids=retrieved_ids if retrieved_ids else None,
                rls_session_id=rls_id,
                pressure_state=pressure_state
            )

            # Writeback the context to PCT
            await steward.append_pct(writeback_record)
            rls_session.created_pct_record_id = writeback_record.id

            # Save the session in the rls ledger using serialized model
            await self.store.append_ledger(peer_id, "rls", orjson_dict(rls_session))

            return rls_session

def orjson_dict(model):
    # Quick serialization helper
    import orjson
    return orjson.loads(model.model_dump_json())
