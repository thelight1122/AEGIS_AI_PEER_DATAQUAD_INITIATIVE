"""The RLS orb must be able to reach a lived turn, not only the seed.

Regression cover for the retrieval blindness found on 2026-08-20: every
turn-derived record scored exactly 0.0 in the live orb (70 of 70 refs, max
relevance 0.0) while foundation records scored normally, because DaemonRecord
exposed data as-is and turn records keep their scored text under "payload".

The record shapes below are the real shapes returned by the Steward/Advocate
daemons for Verus, trimmed. The scored-field list and the access sequence in
_orb_record_text mirror scoring.py::_record_text in
orb-rls-persistent-relations-core v1.0.0 as deployed at
/opt/aegis/verus/venv/.../orb_rls_persistent_relations_core/scoring.py.
"""

from __future__ import annotations

import re

import pytest

from aegis_peer_runtime.protocol_adapters import DaemonRecord, _records_from_daemon

# scoring.py reads exactly these, in this order, via hasattr/getattr.
SCORED_FIELDS = (
    "present_state",
    "working_context",
    "distilled_summary",
    "essence_memory",
    "pattern",
)

RELEVANCE_THRESHOLD = 0.25  # orb_rls_persistent_relations_core.relevance


TURN_NCT = {
    "record_id": "turn:verus-local-turn-cdca856886a8443ea8cade534d2998ff:NCT:2",
    "tensor": "NCT",
    "data": {
        "custodian": "Steward",
        "observed_at": "2026-08-17T21:41:24.656602Z",
        "t_time": 4,
        "tensor": "NCT",
        "turn_id": "verus-local-turn-cdca856886a8443ea8cade534d2998ff",
        "record_hash": "de65315030f72313e3057383564e334fea95c84601d46ccb4e9dd47b387fa27f",
        "prompt_context": "Record two findings about the RLS Orb and the transport.",
        "response_context": "Two findings recorded.",
        "payload": {
            "distilled_summary": (
                "RLS Orb needs supersede-and-verify + Pod activation, not a rebuild "
                "(code is sound; quarantine is a stale hash-pin; relations are inert "
                "until the Pod is live)."
            ),
            "essence_memory": (
                "Surface the real error before diagnosing; the transport was hiding "
                "a validation mismatch."
            ),
            "pivots": [],
            "source_record_ids": [],
        },
    },
}

TURN_PEER = {
    "record_id": "turn:verus-local-turn-cdca856886a8443ea8cade534d2998ff:PEER:0",
    "tensor": "PEER",
    "data": {
        "custodian": "Advocate",
        "t_time": 4,
        "tensor": "PEER",
        "payload": {
            "identity_assertion": "none",
            "present_state": "verified-fix",
            "observation": "The quarantine is a provenance drift, not a defect.",
        },
    },
}

FOUNDATION_NCT = {
    "record_id": "foundation:NCT:11",
    "tensor": "NCT",
    "data": {
        "id": "NCT:verus-session-001:seeded:11",
        "tensor": "NCT",
        "clock": {"epoch": "seeded", "phase": "genesis", "tick": 54},
        "distilled_summary": "Formation proceeds through evidence, not assertion.",
        "essence_memory": "Evidence over assertion.",
        "markers": ["foundation"],
    },
}


def _orb_record_text(record: object) -> str:
    """Reproduce scoring.py::_record_text's attribute access sequence."""
    text = ""
    for field in SCORED_FIELDS:
        if hasattr(record, field) and getattr(record, field):
            text += " " + str(getattr(record, field))
    return text


def _tokens(value: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", value.lower()) if len(t) > 1}


def test_turn_record_text_is_reachable_by_the_orb_scorer():
    record = _records_from_daemon([TURN_NCT])[0]

    text = _orb_record_text(record)

    assert text.strip(), "turn record presented no text to the scorer"
    assert _tokens("rls orb quarantine pod activation") & _tokens(text)


def test_turn_record_scores_above_threshold_on_a_matching_query():
    record = _records_from_daemon([TURN_NCT])[0]
    query = "What does the RLS orb surface about the quarantine and Pod activation?"

    overlap = len(_tokens(query) & _tokens(_orb_record_text(record)))
    # scoring.py stage 1: min(0.5, overlap * 0.12)
    score = min(0.5, overlap * 0.12)

    assert overlap > 0, "turn record scored zero overlap — retrieval blindness"
    assert score >= RELEVANCE_THRESHOLD


def test_peer_payload_fields_survive_the_lift():
    record = _records_from_daemon([TURN_PEER])[0]

    # present_state now leads with the record's own value and carries the rest of
    # its affect text after it, so the scorer can reach experience as well as
    # context. See tests/test_peer_affect_retrievable.py for that contract.
    assert record.present_state.startswith("verified-fix")
    assert "provenance drift" in record.present_state
    assert record.identity_assertion == "none"
    assert record.t_time == 4


def test_foundation_record_keeps_its_top_level_text():
    record = _records_from_daemon([FOUNDATION_NCT])[0]

    assert record.distilled_summary.startswith("Formation proceeds")
    assert _orb_record_text(record).strip()


def test_clock_tick_is_exposed_so_the_recency_bonus_can_fire():
    foundation = _records_from_daemon([FOUNDATION_NCT])[0]
    turn = _records_from_daemon([TURN_NCT])[0]

    assert foundation.clock is not None and foundation.clock.tick == 54
    assert turn.clock is not None and turn.clock.tick == 4


@pytest.mark.parametrize(
    "data",
    [
        {"tensor": "PCT"},
        {"tensor": "PCT", "t_time": 0},
        {"tensor": "PCT", "clock": {"tick": 0}},
        {"tensor": "PCT", "clock": "genesis"},
        {"tensor": "PCT", "t_time": True},
    ],
)
def test_clock_is_none_when_no_usable_tick_is_carried(data):
    assert DaemonRecord("r", "PCT", data).clock is None


def test_missing_field_still_raises_attribute_error():
    record = _records_from_daemon([TURN_NCT])[0]

    assert not hasattr(record, "pattern")
    with pytest.raises(AttributeError):
        record.no_such_field


@pytest.mark.parametrize("item", [TURN_NCT, TURN_PEER, FOUNDATION_NCT])
def test_identity_and_tensor_are_not_shadowed_by_lifted_payload(item):
    record = _records_from_daemon([item])[0]

    assert record.id == item["record_id"]
    assert getattr(record.tensor, "value", record.tensor) == item["tensor"]


def test_real_orb_scorer_selects_a_turn_record_when_the_pod_is_installed():
    scoring = pytest.importorskip(
        "orb_rls_persistent_relations_core.scoring",
        reason="orb package is installed in the Pod venv, not the repo env",
    )
    record = _records_from_daemon([TURN_NCT])[0]

    score, reason = scoring.compute_relevance(
        record,
        "What does the RLS orb surface about the quarantine and Pod activation?",
        "context_retrieval",
        {},
        [],
    )

    assert score >= RELEVANCE_THRESHOLD, reason
