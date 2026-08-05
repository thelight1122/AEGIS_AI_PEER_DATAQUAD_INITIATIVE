from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PACKAGE_SRC = Path(__file__).resolve().parents[2] / "packages" / "orb-memorysearch-record-grounding-core" / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from orb_memorysearch_record_grounding_core.policy import classify_record_claim
from orb_memorysearch_record_grounding_core.provenance import build_search_event
from orb_memorysearch_record_grounding_core.search import search_records


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def run_memorysearch_demo(root: Path, message: str, query_id: str) -> dict[str, Any]:
    records = load_json(root / "fixtures" / "memorysearch-records.json")
    policy = load_json(root / "fixtures" / "memorysearch-policy.json")
    query = classify_record_claim(message, {"query_id": query_id})
    result = search_records(query, records, policy)
    search_event = build_search_event(query, result)
    report = {
        "schema_version": "0.1.0",
        "demo_id": query_id,
        "working_parameters": {
            "live_reach": False,
            "pod_state_effect": "unchanged",
            "dataquad_write": False,
        },
        "query": query,
        "result": result,
        "twitness_search_event": search_event,
    }
    write_json(root / "reports" / "runtime" / "memorysearch" / f"{query_id}.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local MemorySearch Orb Phase-1 fixture demo.")
    parser.add_argument("--root", default=".", help="AEGIS-POD-ARCHITECTURE root")
    parser.add_argument("--message", default="What is NCT according to the Canon in your DataQuad?")
    parser.add_argument("--query-id", default="memorysearch-demo-canon-nct")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = run_memorysearch_demo(root, args.message, args.query_id)
    print(f"PASS MemorySearch demo {report['result']['grounding_status']}")
    print(f"REPORT reports/runtime/memorysearch/{args.query_id}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
