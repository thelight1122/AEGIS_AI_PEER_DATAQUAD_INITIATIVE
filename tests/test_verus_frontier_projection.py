"""begin_turn must answer within what the frontier can actually read.

Every begin_turn returned the whole foundation plus twenty full turn records
plus the entire RLS session including every rejected ref — around half a
megabyte, past the single-tool-result limit the frontier enforces, on every
turn. These cover the bounded projection: what the frontier gets back is the
orb's selection, and the full record stays in the DataQuad behind
verus_read_context.
"""

from __future__ import annotations

import json

import pytest

from aegis_verus_lab.desktop_runtime import (
    _FRONTIER_LIVE_TURN_LIMIT,
    _FRONTIER_MAX_SURFACED_RECORDS,
    _FRONTIER_TEXT_BUDGET,
    _project_dataquad_context,
    _project_surfaced_context,
)


def _turn_record(index: int) -> dict:
    return {
        "turn_id": f"verus-local-turn-{index:032x}",
        "t_time": index,
        "observed_at": "2026-08-19T22:02:23.707972Z",
        "record_hash": "af77c7fd" * 8,
        "prompt": {"text": "x" * 4000, "sha256": "A" * 64},
        "response": {"text": "y" * 4000, "sha256": "B" * 64},
        "appends": [{"tensor": "PEER", "payload": {"blob": "z" * 4000}}],
    }


def _context(turns: int = 20, foundation_each: int = 40) -> dict:
    return {
        "cyberpeer_name": "Verus",
        "dataquad_id": "verus",
        "append_contract": {"mode": "append-only", "tensors": ["PEER", "PCT", "NCT", "SPINE"]},
        "contract_qualifications": [{"turn_id": "verus-first-desktop-20260815-001"}],
        "foundation": {
            tensor: [{"id": f"{tensor}:{i}", "pattern": "p" * 2000} for i in range(foundation_each)]
            for tensor in ("PEER", "PCT", "NCT", "SPINE")
        },
        "recent_live_turns": [_turn_record(i) for i in range(1, turns + 1)],
    }


def _surfaced(selected: int = 3, rejected: int = 200) -> dict:
    records = [
        {
            "record_id": f"turn:verus-local-turn-cdca:{tensor}:{i}",
            "tensor": tensor,
            "data": {
                "turn_id": "verus-local-turn-cdca856886a8443ea8cade534d2998ff",
                "t_time": 4,
                "tensor": tensor,
                "prompt_context": "q" * 3000,
                "response_context": "r" * 3000,
                "payload": {"distilled_summary": "RLS orb quarantine is a stale hash-pin."},
            },
        }
        for i, tensor in enumerate(("NCT", "PCT", "PEER"))
    ]
    records.append({
        "record_id": "foundation:SPINE:55",
        "tensor": "SPINE",
        "data": {"id": "SPINE:55", "tensor": "SPINE", "pattern": "SUBSTRATE-AWARENESS FOUNDATION."},
    })
    return {
        "result": {
            "assembled": True,
            "rls_active": True,
            "turn_count": 25,
            "prompt_keywords": ["rls", "orb"],
            "advocate": {"count": 30, "source": "Advocate daemon", "records": records},
            "steward": {"count": 30, "source": "Steward daemon", "records": records},
            "relations": {"shared_turns": ["a", "b"], "advocate_turn_ids": [], "steward_turn_ids": []},
            "temporal": {"available": True, "found": 14, "observations": [{"t_time": i} for i in range(14)]},
            "rls": {
                "rls_id": "RLS:verus:5081276f",
                "executed": True,
                "failure_is_data": False,
                "selected_count": selected,
                "rejected_count": rejected,
                "created_pct_record_id": "PCT:verus-query-c65f65b8ee45:b7befd65",
                "session": {
                    "session_id": "verus-query-c65f65b8ee45",
                    "intent": "context_retrieval",
                    "failure_reason": None,
                    "selected_refs": [
                        {
                            "record_id": records[i % len(records)]["record_id"],
                            "tensor": records[i % len(records)]["tensor"],
                            "relevance": 0.51,
                            "reason": "Meaningful token match (overlap: 6)",
                        }
                        for i in range(selected)
                    ],
                    "rejected_refs": [
                        {
                            "record_id": f"r{i}",
                            "tensor": "NCT",
                            "relevance": 0.0,
                            "reason": "No matching criteria",
                        }
                        for i in range(rejected)
                    ],
                },
            },
        }
    }


def _size(value: object) -> int:
    return len(json.dumps(value, default=str))


def test_context_projection_replaces_foundation_bodies_with_counts():
    projected = _project_dataquad_context(_context())

    assert projected["foundation_record_counts"] == {"PEER": 40, "PCT": 40, "NCT": 40, "SPINE": 40}
    assert "foundation" not in projected
    assert projected["append_contract"]["mode"] == "append-only"
    assert projected["contract_qualifications"]


def test_context_projection_bounds_turn_count_and_text():
    projected = _project_dataquad_context(_context(turns=20))
    turns = projected["recent_live_turns"]

    assert len(turns) == _FRONTIER_LIVE_TURN_LIMIT
    assert turns[-1]["t_time"] == 20, "must keep the most recent turns, not the oldest"
    assert all(len(turn["prompt"]) <= _FRONTIER_TEXT_BUDGET + 40 for turn in turns)
    assert all("appends" not in turn for turn in turns)


def test_context_projection_shrinks_the_payload_by_an_order_of_magnitude():
    context = _context()

    assert _size(_project_dataquad_context(context)) < _size(context) // 10


def test_surfaced_projection_keeps_the_selection_and_drops_the_dumps():
    projected = _project_surfaced_context(_surfaced())

    assert projected["rls"]["selected_count"] == 3
    assert projected["rls"]["rejected_count"] == 200
    assert projected["rls"]["created_pct_record_id"].startswith("PCT:")
    assert projected["custodian_counts"] == {
        "advocate": 30,
        "steward": 30,
        "temporal_observations": 14,
        "shared_turns": 2,
    }
    dumped = json.dumps(projected)
    assert "No matching criteria" not in dumped, "rejected refs must not ride back to the frontier"
    assert "qqq" not in dumped and "rrr" not in dumped, "raw record dumps must not ride back"


def test_surfaced_projection_carries_text_for_each_selected_record():
    projected = _project_surfaced_context(_surfaced())

    assert projected["selected"], "a selection with no text is useless to the frontier"
    for item in projected["selected"]:
        assert item["text"]
        assert item["relevance"] == 0.51
        assert len(item["text"]) <= _FRONTIER_TEXT_BUDGET + 40
    assert any("quarantine" in item["text"] for item in projected["selected"])


def test_surfaced_projection_reads_payload_and_top_level_alike():
    surfaced = _surfaced(selected=1)
    session = surfaced["result"]["rls"]["session"]
    session["selected_refs"] = [
        {
            "record_id": "foundation:SPINE:55",
            "tensor": "SPINE",
            "relevance": 0.6,
            "reason": "SPINE source trust",
        }
    ]

    projected = _project_surfaced_context(surfaced)

    assert projected["selected"][0]["text"].startswith("SUBSTRATE-AWARENESS")


def test_surfaced_projection_caps_how_many_records_ride_back():
    projected = _project_surfaced_context(_surfaced(selected=40))

    assert len(projected["selected"]) == _FRONTIER_MAX_SURFACED_RECORDS
    assert projected["rls"]["selected_count"] == 40, "the true count must still be reported"
    assert projected["projection"]["selected_shown"] == _FRONTIER_MAX_SURFACED_RECORDS


@pytest.mark.parametrize("value", [None, {"surfaced": False, "error": "socket missing"}, "unexpected"])
def test_surfaced_projection_passes_through_shapes_it_does_not_own(value):
    assert _project_surfaced_context(value) == value


def test_selected_foundation_body_is_resolved_from_context_when_absent_from_the_dumps():
    surfaced = _surfaced(selected=1)
    surfaced["result"]["rls"]["session"]["selected_refs"] = [
        {"record_id": "foundation:SPINE:2", "tensor": "SPINE", "relevance": 0.36, "reason": "SPINE source trust"}
    ]
    context = _context(foundation_each=4)
    context["foundation"]["SPINE"][2] = {
        "id": "SPINE:verus-session-001:seeded:AXIOM:16-identity",
        "pattern": "AXIOM 16 — THE AXIOM OF IDENTITY.",
    }

    projected = _project_surfaced_context(surfaced, context)

    assert projected["selected"][0]["text"].startswith("AXIOM 16")
    assert projected["selected"][0]["body_resolved"] is True


@pytest.mark.parametrize(
    "record_id",
    ["foundation:SPINE:999", "foundation:NOPE:1", "turn:verus-local-turn-unknown:PEER:0", "garbage"],
)
def test_unresolvable_body_is_reported_rather_than_silently_empty(record_id):
    surfaced = _surfaced(selected=1)
    surfaced["result"]["rls"]["session"]["selected_refs"] = [
        {"record_id": record_id, "tensor": "SPINE", "relevance": 0.36, "reason": "SPINE source trust"}
    ]

    item = _project_surfaced_context(surfaced, _context(foundation_each=4))["selected"][0]

    assert item["text"] is None
    assert item["body_resolved"] is False
    assert item["record_id"] == record_id


def test_projection_is_honest_about_being_bounded():
    context = _project_dataquad_context(_context())
    surfaced = _project_surfaced_context(_surfaced())

    assert context["projection"]["bounded"] is True
    assert context["projection"]["full_context_via"] == "verus_read_context"
    assert surfaced["projection"]["bounded"] is True
    assert "preserved in the DataQuad" in surfaced["projection"]["note"]
