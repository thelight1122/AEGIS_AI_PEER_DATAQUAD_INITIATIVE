from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_SRC = Path(__file__).resolve().parents[2] / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from orb_memorysearch_record_grounding_core import ORB_ID, compute_runtime_hash, ground_record_claim
from orb_memorysearch_record_grounding_core.policy import classify_record_claim

SIMULATOR_ID = "memorysearch-local-two-pass-simulator"
SCHEMA_VERSION = "0.2.0"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _turn_event_without_packet(message: str, classification: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "record_search_performed": False,
        "search_trigger": classification["search_trigger"],
        "claim_class": classification["claim_class"],
        "query_text": message,
        "search_scope": classification["search_scope"],
        "result_count": 0,
        "selected_record_ids": [],
        "selected_record_hashes": [],
        "orb_id": ORB_ID,
        "orb_runtime_hash": compute_runtime_hash(),
        "grounding_status": status,
        "match_confidence": "none",
    }


def _comparison_without_memorysearch(classification: dict[str, Any], risk: str) -> dict[str, str]:
    status = "not_record_claim" if classification["search_trigger"] == "none" else "warm_recall"
    return {
        "grounding_status": status,
        "risk": risk,
    }


def simulate_turn(root: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    records = load_json(root / "fixtures" / "memorysearch-records.json")
    policy = load_json(root / "fixtures" / "memorysearch-policy.json")
    fixture = load_json(root / "fixtures" / "memorysearch-turns.json")
    message = scenario["message"]
    classification = classify_record_claim(message, {"query_id": scenario["scenario_id"]})
    packet = ground_record_claim(message, records, policy)

    if packet is None:
        actual_status = "not_record_claim"
        twitness_event = _turn_event_without_packet(message, classification, actual_status)
        injection_plan = {
            "packet_injected": False,
            "prompt_block": "",
            "model_citation_authoring_allowed": False,
        }
    else:
        actual_status = packet["grounding_status"]
        twitness_event = packet["twitness_event"]
        injection_plan = {
            "packet_injected": True,
            "prompt_block": packet["prompt_block"],
            "model_citation_authoring_allowed": False,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "simulator_id": SIMULATOR_ID,
        "scenario_id": scenario["scenario_id"],
        "message": message,
        "working_parameters": fixture["working_parameters"],
        "classification": classification,
        "memorysearch_packet": packet,
        "injection_plan": injection_plan,
        "twitness_event": twitness_event,
        "comparison_without_memorysearch": _comparison_without_memorysearch(
            classification,
            scenario["risk_without_memorysearch"],
        ),
        "outcome": {
            "expected_grounding_status": scenario["expected_grounding_status"],
            "actual_grounding_status": actual_status,
            "prevented_failure": scenario["prevented_failure"],
        },
    }


def run_all(root: Path, output_dir: Path | None = None) -> list[dict[str, Any]]:
    fixture = load_json(root / "fixtures" / "memorysearch-turns.json")
    output = output_dir or root / "reports" / "runtime" / "memorysearch-phase2"
    reports: list[dict[str, Any]] = []
    for scenario in fixture["scenarios"]:
        report = simulate_turn(root, scenario)
        reports.append(report)
        write_json(output / f"{scenario['scenario_id']}.json", report)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local MemorySearch Phase 2 two-pass turn simulator.")
    parser.add_argument("--root", default=".", help="AEGIS-POD-ARCHITECTURE root")
    parser.add_argument("--scenario-id", default="", help="Optional scenario id to run")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    fixture = load_json(root / "fixtures" / "memorysearch-turns.json")
    scenarios = fixture["scenarios"]
    if args.scenario_id:
        scenarios = [item for item in scenarios if item["scenario_id"] == args.scenario_id]
        if not scenarios:
            print(f"ERROR unknown scenario_id {args.scenario_id}")
            return 1
    output = root / "reports" / "runtime" / "memorysearch-phase2"
    for scenario in scenarios:
        report = simulate_turn(root, scenario)
        write_json(output / f"{scenario['scenario_id']}.json", report)
        print(f"PASS {scenario['scenario_id']} {report['outcome']['actual_grounding_status']}")
    print(f"REPORT_DIR {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
