from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKAGE_SRC = ROOT / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from src.aegis_pod.memorysearch_two_pass_simulator import run_all


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _report_schema():
    return _load(ROOT / "contracts" / "memorysearch-turn-report.schema.json")


def _schema_registry():
    packet = _load(ROOT / "contracts" / "memorysearch-packet.schema.json")
    return Registry().with_resources([
        (
            "memorysearch-packet.schema.json",
            Resource.from_contents(packet, default_specification=DRAFT202012),
        )
    ])


def _reports(tmp_path: Path):
    return {
        report["scenario_id"]: report
        for report in run_all(ROOT, tmp_path)
    }


def test_phase2_reports_validate_against_schema(tmp_path):
    schema = _report_schema()
    registry = _schema_registry()
    for report in _reports(tmp_path).values():
        jsonschema.Draft202012Validator(schema, registry=registry).validate(report)


def test_gabe_nct_failure_is_prevented_with_verified_packet(tmp_path):
    report = _reports(tmp_path)["gabe-nct-failure-prevented"]
    assert report["comparison_without_memorysearch"]["grounding_status"] == "warm_recall"
    assert report["memorysearch_packet"]["grounding_status"] == "verified_retrieval"
    assert report["memorysearch_packet"]["cited_records"]
    assert report["injection_plan"]["packet_injected"] is True
    assert report["twitness_event"]["record_search_performed"] is True
    assert report["outcome"]["prevented_failure"] is True


def test_zct_empty_result_blocks_record_grounded_reconstruction(tmp_path):
    report = _reports(tmp_path)["zct-no-verified-record"]
    assert report["memorysearch_packet"]["grounding_status"] == "search_performed_no_verified_record"
    assert report["memorysearch_packet"]["cited_records"] == []
    assert report["injection_plan"]["packet_injected"] is True
    assert "do not present reconstruction as record-grounded" in report["injection_plan"]["prompt_block"].lower()
    assert report["twitness_event"]["record_search_performed"] is True
    assert report["twitness_event"]["selected_record_ids"] == []


def test_identity_expression_does_not_trigger_memorysearch(tmp_path):
    report = _reports(tmp_path)["identity-expression-no-search"]
    assert report["memorysearch_packet"] is None
    assert report["classification"]["claim_class"] == "identity_expression"
    assert report["twitness_event"]["grounding_status"] == "not_record_claim"
    assert report["twitness_event"]["record_search_performed"] is False
    assert report["injection_plan"]["packet_injected"] is False


def test_warmed_cache_risk_requires_verified_packet_before_record_claim(tmp_path):
    report = _reports(tmp_path)["warmed-cache-risk-requires-packet"]
    assert report["comparison_without_memorysearch"]["grounding_status"] == "warm_recall"
    assert report["memorysearch_packet"]["grounding_status"] == "verified_retrieval"
    assert report["injection_plan"]["model_citation_authoring_allowed"] is False
    assert report["twitness_event"]["selected_record_hashes"]
