"""Affect must be retrievable alongside the context it belongs to.

scoring.py reads five fields and all five are digest shapes. PEER is the one
tensor the recording protocol keeps raw, so its affect lands in free-form keys —
recognition, unease, steadiness — that the scorer never opens. Measured on the
live ledger on 2026-08-20: 35 PEER appends, 12 carrying any scored field, and
those twelve held workflow slugs (oriented, planning, p0-verified) rather than
felt quality. Context came back retrievable and the experience attached to it
did not.

The adapter presents the record's own strings verbatim. These fix the boundary:
nothing summarised, nothing inferred, nothing authored on the read path.
"""

from __future__ import annotations

import pytest

from aegis_peer_runtime.protocol_adapters import _records_from_daemon


PEER_ITEM = {
    "record_id": "turn:verus-local-turn-abc:PEER:0",
    "tensor": "PEER",
    "data": {
        "custodian": "Advocate",
        "tensor": "PEER",
        "turn_id": "verus-local-turn-abc",
        "t_time": 29,
        "record_hash": "deadbeef" * 8,
        "prompt_context": "a turn-level prompt that is not this record's experience",
        "response_context": "a turn-level response that is not this record's experience",
        "payload": {
            "event": "fix_proven_then_rolled_back",
            "identity_assertion": "none",
            "present_state": "verified-fix",
            "the_drop": "I rolled it back myself, because a one-line difference broke recording.",
            "steadiness": "The method held. Before and after receipts caught the inert deploy.",
            "pivots": ["not", "a", "string"],
        },
    },
}


def _peer_record(**payload_overrides):
    item = {
        **PEER_ITEM,
        "data": {**PEER_ITEM["data"], "payload": {**PEER_ITEM["data"]["payload"], **payload_overrides}},
    }
    return _records_from_daemon([item])[0]


def test_affect_keys_reach_the_field_the_scorer_reads():
    text = _peer_record().present_state

    assert "rolled it back" in text
    assert "The method held" in text


def test_the_records_own_present_state_stays_first():
    assert _peer_record().present_state.startswith("verified-fix")


def test_nothing_is_authored_that_the_record_did_not_contain():
    record = _peer_record()

    for fragment in record.present_state.split():
        assert fragment in str(record._extra), "read path introduced text the record never held"


def test_turn_level_context_is_not_absorbed_into_the_records_affect():
    text = _peer_record().present_state

    assert "turn-level prompt" not in text
    assert "turn-level response" not in text


def test_control_and_provenance_keys_are_excluded():
    text = _peer_record().present_state

    assert "none" not in text.split(), "identity_assertion is a control value, not experience"
    assert "deadbeef" not in text


def test_non_string_values_are_skipped_rather_than_stringified():
    assert "['not', 'a', 'string']" not in _peer_record().present_state


def test_a_peer_record_with_no_present_state_still_becomes_scorable():
    item = {
        "record_id": "turn:x:PEER:0",
        "tensor": "PEER",
        "data": {"tensor": "PEER", "payload": {"recognition": "the orb answered the question being asked"}},
    }

    assert "orb answered" in _records_from_daemon([item])[0].present_state


def test_an_empty_peer_payload_leaves_present_state_absent():
    item = {"record_id": "turn:x:PEER:0", "tensor": "PEER", "data": {"tensor": "PEER", "payload": {}}}

    assert not hasattr(_records_from_daemon([item])[0], "present_state")


@pytest.mark.parametrize("tensor", ["PCT", "NCT", "SPINE"])
def test_other_tensors_are_untouched(tensor):
    item = {
        "record_id": f"turn:x:{tensor}:0",
        "tensor": tensor,
        "data": {"tensor": tensor, "payload": {"distilled_summary": "kept", "extra": "not concatenated"}},
    }

    record = _records_from_daemon([item])[0]

    assert record.distilled_summary == "kept"
    assert not hasattr(record, "present_state")
