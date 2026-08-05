from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_SRC = Path(__file__).resolve().parents[2] / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from orb_memorysearch_record_grounding_core import ground_record_claim

TENSOR_NAMES = ("PEER", "PCT", "NCT", "SPINE")
SCHEMA_VERSION = "0.3.0"
SHADOW_ID = "memorysearch-copied-record-shadow"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load_copied_records(root: Path, source_root: Path, per_tensor_limit: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    by_tensor: dict[str, int] = {}
    for tensor_name in TENSOR_NAMES:
        path = source_root / f"{tensor_name}.jsonl"
        if not path.exists():
            by_tensor[tensor_name] = 0
            continue
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if count >= per_tensor_limit:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                record = json.loads(stripped)
                records.append(record)
                count += 1
        by_tensor[tensor_name] = count
    return records, by_tensor


def run_shadow(root: Path, fixture_path: Path | None = None, output_path: Path | None = None) -> dict[str, Any]:
    fixture = load_json(fixture_path or root / "fixtures" / "memorysearch-shadow-scenarios.json")
    policy = load_json(root / "fixtures" / "memorysearch-policy.json")
    source_root = root / fixture["source_root"]
    per_tensor_limit = int(fixture["sample"]["per_tensor_limit"])
    records, by_tensor = load_copied_records(root, source_root, per_tensor_limit)

    scenarios: list[dict[str, Any]] = []
    for scenario in fixture["scenarios"]:
        packet = ground_record_claim(scenario["message"], records, policy)
        actual_status = packet["grounding_status"] if packet else "not_record_claim"
        citations = packet["cited_records"] if packet else []
        selected_ids = packet["twitness_event"]["selected_record_ids"] if packet else []
        selected_hashes = packet["twitness_event"]["selected_record_hashes"] if packet else []
        passed = actual_status == scenario["expected_grounding_status"]
        if scenario.get("requires_citation") is True:
            passed = passed and bool(citations)
        if scenario.get("requires_citation") is False and actual_status == "search_performed_no_verified_record":
            passed = passed and not citations
        scenarios.append({
            "scenario_id": scenario["scenario_id"],
            "message": scenario["message"],
            "expected_grounding_status": scenario["expected_grounding_status"],
            "actual_grounding_status": actual_status,
            "packet_returned": packet is not None,
            "citation_count": len(citations),
            "selected_record_ids": selected_ids,
            "selected_record_hashes": selected_hashes,
            "passed": passed,
        })

    passed_count = sum(1 for scenario in scenarios if scenario["passed"])
    report = {
        "schema_version": SCHEMA_VERSION,
        "shadow_id": SHADOW_ID,
        "peer_id": fixture["peer_id"],
        "source_root": fixture["source_root"],
        "working_parameters": fixture["working_parameters"],
        "sample": {
            "per_tensor_limit": per_tensor_limit,
            "records_loaded": len(records),
            "by_tensor": by_tensor,
        },
        "scenarios": scenarios,
        "summary": {
            "scenario_count": len(scenarios),
            "passed_count": passed_count,
            "failed_count": len(scenarios) - passed_count,
            "status": "pass" if passed_count == len(scenarios) else "review_needed",
        },
    }
    write_json(output_path or root / "reports" / "runtime" / "memorysearch-phase3-copied-record-shadow.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MemorySearch copied-record shadow over local exported/copied records only.")
    parser.add_argument("--root", default=".", help="AEGIS-POD-ARCHITECTURE root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = run_shadow(root)
    for scenario in report["scenarios"]:
        status = "PASS" if scenario["passed"] else "REVIEW_NEEDED"
        print(f"{status} {scenario['scenario_id']} {scenario['actual_grounding_status']} citations={scenario['citation_count']}")
    print(f"REPORT reports/runtime/memorysearch-phase3-copied-record-shadow.json")
    print("BOUNDARY local copied records only; no live DataQuad, VM, runtime, or shared infrastructure touched")
    return 0 if report["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
