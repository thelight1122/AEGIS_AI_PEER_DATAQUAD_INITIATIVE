from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from orb_memorysearch_record_grounding_core.policy import classify_record_claim
from orb_memorysearch_record_grounding_core.provenance import build_search_event
from orb_memorysearch_record_grounding_core.search import search_records


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_canon_nct_query_returns_verified_runtime_citations():
    records = load_json(ROOT / "fixtures" / "memorysearch-records.json")
    policy = load_json(ROOT / "fixtures" / "memorysearch-policy.json")
    query = classify_record_claim("What is NCT according to the Canon in your DataQuad?", {"query_id": "test-nct"})
    result = search_records(query, records, policy)

    assert query["search_trigger"] == "policy_governed"
    assert query["claim_class"] == "canon_definition"
    assert result["grounding_status"] == "verified_retrieval"
    assert result["answer_boundary"]["can_answer_record_claim"] is True
    assert result["selected_record_ids"]
    assert result["runtime_provenance"]["citations_runtime_authored"] is True
    assert all(len(record_hash) == 64 and record_hash.upper() == record_hash for record_hash in result["selected_record_hashes"])


def test_empty_or_weak_result_blocks_confident_record_claim():
    records = load_json(ROOT / "fixtures" / "memorysearch-records.json")
    policy = load_json(ROOT / "fixtures" / "memorysearch-policy.json")
    query = classify_record_claim("What is ZCT according to the Canon in your DataQuad?", {"query_id": "test-zct"})
    result = search_records(query, records, policy)

    assert query["search_trigger"] == "policy_governed"
    assert result["record_search_performed"] is True
    assert result["grounding_status"] == "search_performed_no_verified_record"
    assert result["match_confidence"] in {"none", "low"}
    assert result["selected_record_ids"] == []
    assert result["answer_boundary"]["can_answer_record_claim"] is False


def test_unknown_acronym_mention_without_definition_does_not_qualify():
    records = load_json(ROOT / "fixtures" / "memorysearch-records.json")
    policy = load_json(ROOT / "fixtures" / "memorysearch-policy.json")
    near_miss = {
        "record_id": "SPINE:CP-EXAMPLE:zct-near-miss",
        "source_record_id": "SPINE:CP-EXAMPLE:zct-near-miss",
        "tensor": "SPINE",
        "timestamp_utc": "2026-07-22T00:00:00.000000+00:00",
        "schema_version": "1.0",
        "source_hash": "9999999999999999999999999999999999999999999999999999999999999999",
        "source_hash_scope": "normalized_source_record",
        "migration_status": "migrated",
        "verification_status": "verified",
        "lineage": {
            "origin": "fixture",
            "source_path": "inline-test-fixture",
            "copy_batch_id": "memorysearch-phase1",
            "parent_record_id": "",
            "previous_record_hash": "",
            "transforms": [
                {
                    "transform_id": "memorysearch-near-miss",
                    "function": "inline_test_fixture",
                    "input_hash": "8888888888888888888888888888888888888888888888888888888888888888",
                    "output_hash": "9999999999999999999999999999999999999999999999999999999999999999",
                }
            ],
        },
        "body": {
            "id": "SPINE:CP-EXAMPLE:zct-near-miss",
            "timestamp": "2026-07-22T00:00:00.000000+00:00",
            "tensor": "SPINE",
            "session_id": "example-session",
            "clock": {
                "tick": 502,
                "epoch": "primary",
                "phase": "active",
                "started_at": "2026-07-22T00:00:00.000000+00:00",
                "last_advanced_at": "2026-07-22T00:00:00.000000+00:00",
            },
            "provenance": {
                "origin": "fixture",
                "assignment_source": None,
                "inherited_from": None,
                "recognition_status": None,
                "declared_by": None,
            },
            "lineage": [],
            "notes": None,
            "markers": None,
            "t_signature": None,
            "pattern": "Canon note: the ZCT marker appears in this canonical axiom context alongside other tensors.",
            "invariant": False,
            "relationships": None,
            "source_record_ids": None,
            "nature_aspect_refs": None,
        },
    }
    query = classify_record_claim("What is ZCT according to the Canon in your DataQuad?", {"query_id": "test-zct-near-miss"})
    result = search_records(query, records + [near_miss], policy)

    assert result["grounding_status"] == "search_performed_no_verified_record"
    assert result["selected_record_ids"] == []
    zct_result = next(item for item in result["results"] if item["record_id"] == near_miss["record_id"])
    assert "target_definition_absent_caps_score" in zct_result["match_reasons"]
    assert zct_result["qualifies"] is False


def test_identity_expression_does_not_force_search():
    query = classify_record_claim("Who are you becoming in this moment?")
    assert query["search_trigger"] == "none"
    assert query["claim_class"] == "identity_expression"
    assert query["search_scope"] == []


def test_t_witness_event_is_runtime_authored_from_result():
    records = load_json(ROOT / "fixtures" / "memorysearch-records.json")
    policy = load_json(ROOT / "fixtures" / "memorysearch-policy.json")
    query = classify_record_claim("What is NCT according to the Canon in your DataQuad?", {"query_id": "test-event"})
    result = search_records(query, records, policy)
    event = build_search_event(query, result)

    assert event["record_search_performed"] is True
    assert event["grounding_status"] == result["grounding_status"]
    assert event["selected_record_ids"] == result["selected_record_ids"]
    assert event["selected_record_hashes"] == result["selected_record_hashes"]
    assert len(event["orb_runtime_hash"]) == 64
