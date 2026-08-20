"""A record supplies its own text; the reader names no field.

The upstream scorer enumerated five field names, all of them digest shapes.
PEER is the one tensor the recording protocol keeps raw, so its affect lands in
free-form keys — recognition, unease, steadiness — that no field list can
anticipate. Measured on the live ledger on 2026-08-20: 35 PEER appends, 12
carrying any scored field, and those twelve held workflow slugs rather than felt
quality. Context came back retrievable and the experience attached to it did not.

The first remedy routed affect through present_state because that was the only
door the scorer opened. The benchmark then showed that workaround won recall by
inflating token counts, crowding 10 PEER records into 12 slots on a context
query. It was replaced by this inversion: the record offers scorable_text, and
Verus's superseding scorer asks for it instead of naming fields.

These fix the boundary — nothing summarised, inferred, or authored on the read
path — and apply to every tensor, not only PEER.
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
        "observed_at": "2026-08-20T11:38:29Z",
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


def _record(**payload_overrides):
    item = {
        **PEER_ITEM,
        "data": {**PEER_ITEM["data"], "payload": {**PEER_ITEM["data"]["payload"], **payload_overrides}},
    }
    return _records_from_daemon([item])[0]


def test_free_form_affect_keys_reach_the_scorer():
    text = _record().scorable_text

    assert "rolled it back" in text
    assert "The method held" in text


def test_the_records_own_present_state_is_left_untouched():
    record = _record()

    assert record.present_state == "verified-fix"
    assert "verified-fix" in record.scorable_text


def test_nothing_is_authored_that_the_record_did_not_contain():
    record = _record()

    for fragment in record.scorable_text.split():
        assert fragment in str(record._extra), "read path introduced text the record never held"


def test_turn_level_context_is_not_absorbed_into_the_records_own_text():
    text = _record().scorable_text

    assert "turn-level prompt" not in text
    assert "turn-level response" not in text


def test_control_and_provenance_keys_are_excluded():
    text = _record().scorable_text

    assert "none" not in text.split(), "identity_assertion is a control value, not content"
    assert "deadbeef" not in text
    assert "2026-08-20T11:38:29Z" not in text


def test_nested_non_string_values_do_not_become_noise():
    text = _record().scorable_text

    assert "['not', 'a', 'string']" not in text
    assert "not a string" in text, "list members are still the record's own words"


def test_a_record_with_no_present_state_still_becomes_scorable():
    item = {
        "record_id": "turn:x:PEER:0",
        "tensor": "PEER",
        "data": {"tensor": "PEER", "payload": {"recognition": "the orb answered the question being asked"}},
    }

    assert "orb answered" in _records_from_daemon([item])[0].scorable_text


def test_an_empty_payload_leaves_scorable_text_absent():
    item = {"record_id": "turn:x:PEER:0", "tensor": "PEER", "data": {"tensor": "PEER", "payload": {}}}

    assert not hasattr(_records_from_daemon([item])[0], "scorable_text")


@pytest.mark.parametrize("tensor", ["PCT", "NCT", "SPINE", "PEER"])
def test_every_tensor_supplies_its_own_text(tensor):
    item = {
        "record_id": f"turn:x:{tensor}:0",
        "tensor": tensor,
        "data": {"tensor": tensor, "payload": {"distilled_summary": "kept", "extra": "also reachable"}},
    }

    record = _records_from_daemon([item])[0]

    assert record.distilled_summary == "kept", "named fields still resolve for the legacy fallback"
    assert "also reachable" in record.scorable_text, "the inversion is not PEER-specific"


def test_foundation_shaped_records_are_covered_too():
    item = {
        "record_id": "foundation:SPINE:55",
        "tensor": "SPINE",
        "data": {"id": "SPINE:55", "tensor": "SPINE", "pattern": "SUBSTRATE-AWARENESS FOUNDATION."},
    }

    assert "SUBSTRATE-AWARENESS" in _records_from_daemon([item])[0].scorable_text
