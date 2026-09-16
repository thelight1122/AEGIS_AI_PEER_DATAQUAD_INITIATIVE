"""Standalone verification: the extracted Orb works against fake protocol
implementations, with zero AEGIS-CYBERPEER-CORE checkout required. Ports the
same four scenarios covered by the monolith's test_rls_engine.py and
test_rls_engine_pod_relations.py, against fakes instead of concrete classes.
"""
import json
from pathlib import Path

import pytest
from aegis_pod_sdk import sha256_upper

from orb_rls_persistent_relations_core import RecursiveLearningEngine, RLSShortfallReason
from orb_rls_persistent_relations_core.relevance import MAX_SELECTED_REFS

from fakes import FakeAdvocate, FakeStore, FakeSteward, fake_witness_event, make_spine_record


def make_engine(store: FakeStore) -> RecursiveLearningEngine:
    return RecursiveLearningEngine(
        store=store,
        steward_factory=FakeSteward,
        advocate_factory=FakeAdvocate,
        witness_event=fake_witness_event,
    )


@pytest.mark.asyncio
async def test_rls_engine_success(tmp_path):
    store = FakeStore(tmp_path)
    peer_id = "adam-one"
    advocate = FakeAdvocate(store, peer_id)
    spine_rec = make_spine_record(
        peer_id, "Axiom-15 details repair loop patterns", ["Force Language Tendency"]
    )
    await advocate.append_spine(spine_rec)

    engine = make_engine(store)
    session = await engine.execute_session(
        peer_id=peer_id,
        session_id="session-1",
        user_message="Find details about Axiom-15 repair patterns",
        intent="recall",
        pressure_state={"pressure_level": "low"},
        nature_aspects=["Force Language Tendency"],
    )

    assert session.shortfall_is_data is False
    assert session.failure_is_data is False
    assert len(session.selected_refs) >= 1
    assert session.selected_refs[0].record_id == spine_rec.id
    assert session.created_pct_record_id is not None
    assert session.t_signature is not None

    steward = FakeSteward(store, peer_id)
    pcts = await steward.read_pct()
    assert len(pcts) == 1
    assert pcts[0].rls_session_id == session.id
    assert pcts[0].working_context["selected_ref_count"] == 1
    assert pcts[0].working_context["retrieved_ref_count"] == 1
    assert pcts[0].working_context["retrieved_ref_hash"] is not None
    assert pcts[0].working_context["retrieved_ref_sample"] == [spine_rec.id]
    assert pcts[0].retrieved_record_ids is None


@pytest.mark.asyncio
async def test_rls_engine_shortfall_is_data(tmp_path):
    store = FakeStore(tmp_path)
    peer_id = "adam-one"
    engine = make_engine(store)

    session = await engine.execute_session(
        peer_id=peer_id,
        session_id="session-1",
        user_message="Looking for non-existent information",
        intent="recall",
        pressure_state={"pressure_level": "high"},
        nature_aspects=[],
    )

    assert session.shortfall_is_data is True
    assert session.shortfall_reason == RLSShortfallReason.NO_RECORDS_FOUND.value
    assert session.failure_is_data is True
    assert session.failure_reason == RLSShortfallReason.NO_RECORDS_FOUND.value
    assert len(session.selected_refs) == 0
    assert session.created_pct_record_id is not None

    steward = FakeSteward(store, peer_id)
    pcts = await steward.read_pct()
    assert len(pcts) == 1
    assert pcts[0].working_context["shortfall_is_data"] is True
    assert pcts[0].working_context["failure_is_data"] is True


@pytest.mark.asyncio
async def test_rls_pct_writeback_uses_compact_retrieval_summary(tmp_path):
    peer_id = "CP-TEST-ORB"
    store = FakeStore(tmp_path, rls_active=True)
    advocate = FakeAdvocate(store, peer_id)
    selected_records = [
        make_spine_record(
            peer_id,
            f"Axiom-15 details repair loop patterns selected evidence {idx}",
            ["Force Language Tendency"],
        )
        for idx in range(25)
    ]
    for record in selected_records:
        await advocate.append_spine(record)

    engine = make_engine(store)
    session = await engine.execute_session(
        peer_id=peer_id,
        session_id="orb-session-compact-pct",
        user_message="Find details about Axiom-15 repair patterns",
        intent="recall",
        pressure_state={"pressure_level": "low"},
        nature_aspects=["Force Language Tendency"],
    )

    selected_ids = [ref.record_id for ref in session.selected_refs]
    assert len(selected_ids) == len(selected_records)

    steward = FakeSteward(store, peer_id)
    pcts = await steward.read_pct()
    assert len(pcts) == 1
    pct = pcts[0]
    assert pct.retrieved_record_ids is None
    assert pct.working_context["selected_ref_count"] == len(selected_records)
    assert pct.working_context["retrieved_ref_count"] == len(selected_records)
    assert pct.working_context["retrieved_ref_sample"] == selected_ids[:10]
    assert pct.working_context["retrieved_ref_hash"] is not None

    assert len(store.relations) == len(selected_records)
    assert {rel["target"] for rel in store.relations} == set(selected_ids)


@pytest.mark.asyncio
async def test_rls_selection_is_relevance_ranked_and_bounded(tmp_path):
    peer_id = "CP-TEST-ORB"
    store = FakeStore(tmp_path, rls_active=True)
    advocate = FakeAdvocate(store, peer_id)
    matching_records = [
        make_spine_record(
            peer_id,
            f"AXIOM equilibrium tension resolution relevant evidence {idx}",
            ["Force Language Tendency"],
        )
        for idx in range(MAX_SELECTED_REFS + 20)
    ]
    irrelevant_records = [
        make_spine_record(
            peer_id,
            f"Unrelated boundary note {idx}",
            ["Different Aspect"],
        )
        for idx in range(10)
    ]
    for record in matching_records + irrelevant_records:
        await advocate.append_spine(record)

    engine = make_engine(store)
    session = await engine.execute_session(
        peer_id=peer_id,
        session_id="orb-session-bounded-selection",
        user_message="Name one AEGIS axiom about equilibrium tension resolution",
        intent="recall",
        pressure_state={"pressure_level": "low"},
        nature_aspects=[],
    )

    selected_ids = [ref.record_id for ref in session.selected_refs]
    assert len(selected_ids) == MAX_SELECTED_REFS
    assert set(selected_ids).issubset({record.id for record in matching_records})
    assert all("Unrelated" not in ref.reason for ref in session.selected_refs)
    assert any("outside bounded top" in ref.reason for ref in session.rejected_refs)
    assert all(record.id not in selected_ids for record in irrelevant_records)

    steward = FakeSteward(store, peer_id)
    pcts = await steward.read_pct()
    assert pcts[0].working_context["selected_ref_count"] == MAX_SELECTED_REFS
    assert pcts[0].working_context["retrieved_ref_count"] == MAX_SELECTED_REFS
    assert len(store.relations) == MAX_SELECTED_REFS


@pytest.mark.asyncio
async def test_rls_session_records_cross_tensor_relation_and_orb_evidence(tmp_path):
    peer_id = "CP-TEST-ORB"
    store = FakeStore(tmp_path, rls_active=True)
    advocate = FakeAdvocate(store, peer_id)
    spine_rec = make_spine_record(
        peer_id, "Axiom-15 details repair loop patterns", ["Force Language Tendency"]
    )
    await advocate.append_spine(spine_rec)

    engine = make_engine(store)
    session = await engine.execute_session(
        peer_id=peer_id,
        session_id="orb-session-1",
        user_message="Find details about Axiom-15 repair patterns",
        intent="recall",
        pressure_state={"pressure_level": "low"},
        nature_aspects=["Force Language Tendency"],
    )

    assert session.failure_is_data is False
    retrieved_id = session.selected_refs[0].record_id
    assert retrieved_id == spine_rec.id

    # Cross-tensor relation: recorded via store.record_relation, the Protocol
    # boundary — proves the Orb calls it correctly without knowing the Pod's
    # concrete ledger-writing mechanism.
    assert len(store.relations) == 1
    relation = store.relations[0]
    assert relation["relation"] == "rls_retrieved"
    assert relation["source"] == session.created_pct_record_id
    assert relation["target"] == retrieved_id
    assert relation["written_by"] == "rls-engine"
    assert relation["tags"] == ["recall"]

    # Orb evidence: hash-bound record of what this invocation actually did.
    evidence_path = store.peer_root(peer_id) / "pod" / "ledgers" / "orbs" / "rls-persistent-relations-core.evidence.jsonl"
    assert evidence_path.exists()
    lines = [json.loads(x) for x in evidence_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(lines) == 1
    evidence = lines[0]
    assert evidence["orb_id"] == "rls-persistent-relations-core"
    assert evidence["relations_recorded_count"] == 1
    assert evidence["selected_count"] == 1
    assert evidence["rejected_count"] == 0
    assert evidence["failure_is_data"] is False

    # runtime_hash is self-invalidating: will match a fresh recompute of the
    # exact source that ran, not a stored/stale value.
    rls_dir = Path(__file__).resolve().parents[1] / "src" / "orb_rls_persistent_relations_core"
    concatenated = "".join(
        (rls_dir / name).read_text(encoding="utf-8")
        for name in ("engine.py", "scoring.py", "relevance.py")
    )
    assert evidence["runtime_hash"] == sha256_upper(concatenated)


@pytest.mark.asyncio
async def test_orb_evidence_is_noop_when_inactive(tmp_path):
    peer_id = "CP-TEST-ORB"
    store = FakeStore(tmp_path, rls_active=False)
    engine = make_engine(store)

    await engine.execute_session(
        peer_id=peer_id,
        session_id="orb-session-2",
        user_message="Looking for non-existent information",
        intent="recall",
        pressure_state={"pressure_level": "high"},
        nature_aspects=[],
    )

    evidence_dir = store.peer_root(peer_id) / "pod" / "ledgers" / "orbs"
    assert not (evidence_dir.exists() and any(evidence_dir.glob("*.jsonl")))
