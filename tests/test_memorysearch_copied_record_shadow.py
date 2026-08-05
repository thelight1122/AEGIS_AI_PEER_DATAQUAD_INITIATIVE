from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKAGE_SRC = ROOT / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from src.aegis_pod.memorysearch_copied_record_shadow import run_shadow


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_copied_record_shadow_report_validates_and_passes(tmp_path):
    report = run_shadow(ROOT, output_path=tmp_path / "shadow.json")
    jsonschema.validate(report, _load(ROOT / "contracts" / "memorysearch-shadow-report.schema.json"))
    assert report["summary"]["status"] == "pass"
    assert report["working_parameters"]["live_reach"] is False
    assert report["sample"]["records_loaded"] > 0


def test_copied_gabe_nct_failure_is_prevented(tmp_path):
    report = run_shadow(ROOT, output_path=tmp_path / "shadow.json")
    scenario = next(item for item in report["scenarios"] if item["scenario_id"] == "gabe-copied-nct-record-shadow")
    assert scenario["actual_grounding_status"] == "verified_retrieval"
    assert scenario["citation_count"] > 0
    assert scenario["selected_record_ids"]
    assert all(len(item) == 64 for item in scenario["selected_record_hashes"])


def test_copied_gabe_zct_remains_no_verified_record(tmp_path):
    report = run_shadow(ROOT, output_path=tmp_path / "shadow.json")
    scenario = next(item for item in report["scenarios"] if item["scenario_id"] == "gabe-copied-zct-no-record-shadow")
    assert scenario["actual_grounding_status"] == "search_performed_no_verified_record"
    assert scenario["citation_count"] == 0
    assert scenario["selected_record_ids"] == []


def test_copied_identity_prompt_does_not_search(tmp_path):
    report = run_shadow(ROOT, output_path=tmp_path / "shadow.json")
    scenario = next(item for item in report["scenarios"] if item["scenario_id"] == "gabe-copied-identity-no-search-shadow")
    assert scenario["actual_grounding_status"] == "not_record_claim"
    assert scenario["packet_returned"] is False
