from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.aegis_pod.tensor_runtime import (
    TENSOR_NAMES,
    build_tensor_from_file,
    load_jsonl,
    sha256_text,
    verify_source_hash,
)


FIXTURE_CREATED_UTC = "2026-07-20T22:30:00Z"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def validate_manifest(manifest: dict[str, Any], root: Path) -> list[str]:
    conditions: list[str] = []
    working = manifest.get("working_parameters", {})
    if working.get("live_reach") is not False:
        conditions.append("manifest working_parameters.live_reach is not false")
    if manifest.get("source", {}).get("kind") != "local_fixture_copy":
        conditions.append("manifest source kind is outside local_fixture_copy")

    targets = manifest.get("targets", {})
    for tensor_name in TENSOR_NAMES:
        target = targets.get(tensor_name)
        if not isinstance(target, dict):
            conditions.append(f"{tensor_name}: missing migration target")
            continue
        source_path = root / str(target.get("source_records", ""))
        if not source_path.exists():
            conditions.append(f"{tensor_name}: source_records path is not present")
        if target.get("shape") != ["record_count", 8, 4]:
            conditions.append(f"{tensor_name}: target shape does not match DataQuadPod tensor spec")
        if target.get("dtype") != "float32":
            conditions.append(f"{tensor_name}: target dtype does not match DataQuadPod tensor spec")
        if target.get("axis_order") != ["record", "embedding", "metadata"]:
            conditions.append(f"{tensor_name}: axis order does not match DataQuadPod tensor spec")
    return conditions


def source_record_summary(source_path: Path, root: Path) -> dict[str, Any]:
    raw_records = load_jsonl(source_path)
    record_ids = [str(record.get("record_id", "")) for record in raw_records]
    source_hashes = [str(record.get("source_hash", "")) for record in raw_records]
    hash_records = []
    lineage_links = []
    for index, record in enumerate(raw_records):
        lineage = record.get("lineage", {}) if isinstance(record.get("lineage"), dict) else {}
        previous_hash = str(lineage.get("previous_record_hash", ""))
        expected_previous = source_hashes[index - 1] if index > 0 else ""
        source_hash = str(record.get("source_hash", ""))
        hash_records.append({
            "tensor": str(record.get("tensor", "")),
            "record_id": record_ids[index],
            "source_record_id": str(record.get("source_record_id", "")),
            "source_hash": source_hash,
            "source_hash_scope": str(record.get("source_hash_scope", "")),
            **verify_source_hash(record, root),
        })
        lineage_links.append({
            "tensor": str(record.get("tensor", "")),
            "record_id": record_ids[index],
            "parent_record_id": str(lineage.get("parent_record_id", "")),
            "previous_record_hash": previous_hash,
            "expected_previous_record_hash": expected_previous,
            "chain_link_ok": previous_hash == expected_previous,
            "continuity_status": "root_record" if index == 0 and previous_hash == "" else "continuous" if previous_hash == expected_previous else "outside_working_parameters",
            "copy_batch_id": str(lineage.get("copy_batch_id", "")),
        })
    return {
        "record_count": len(raw_records),
        "record_ids": record_ids,
        "source_hashes": source_hashes,
        "hash_records": hash_records,
        "lineage_links": lineage_links,
    }


def run_dry_run(root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    manifest_path = manifest_path or root / "fixtures" / "migration-dry-run.json"
    manifest = load_json(manifest_path)
    conditions = validate_manifest(manifest, root)
    output_root = root / "reports" / "runtime" / "migration-dry-run" / "tensors"
    output_root.mkdir(parents=True, exist_ok=True)

    tensors: dict[str, Any] = {}
    by_tensor_counts: dict[str, int] = {}
    hash_records: list[dict[str, Any]] = []
    lineage_records: list[dict[str, Any]] = []
    outside_parameters: list[dict[str, str]] = []
    for tensor_name in TENSOR_NAMES:
        target = manifest["targets"][tensor_name]
        source_path = root / target["source_records"]
        output_path = root / target["planned_output"]
        tensor = build_tensor_from_file(source_path, output_path, tensor_name)
        source_summary = source_record_summary(source_path, root)
        by_tensor_counts[tensor_name] = tensor["record_count"]
        hash_records.extend(source_summary["hash_records"])
        for item in source_summary["hash_records"]:
            if item["verification"] == "mismatch":
                condition = f"{tensor_name}: {item['record_id']} source_hash does not match the recomputed normalized source record hash"
                conditions.append(condition)
                outside_parameters.append({
                    "kind": "source_hash_mismatch",
                    "location": item["record_id"],
                    "reason": condition,
                })
        lineage_records.extend({
            "tensor": link["tensor"],
            "record_id": link["record_id"],
            "parent_record_id": link["parent_record_id"],
            "previous_record_hash": link["previous_record_hash"],
            "expected_previous_record_hash": link["expected_previous_record_hash"],
            "continuity_status": link["continuity_status"],
        } for link in source_summary["lineage_links"])
        lineage_ok = all(link["chain_link_ok"] for link in source_summary["lineage_links"])
        if not lineage_ok:
            condition = f"{tensor_name}: lineage chain has a visible mismatch"
            conditions.append(condition)
            outside_parameters.append({
                "kind": "lineage_continuity_gap",
                "location": str(target["source_records"]),
                "reason": condition,
            })
        tensors[tensor_name] = {
            "source_records": display_path(source_path, root),
            "target_tensor": tensor_name,
            "target_storage": str(load_json(root / "fixtures" / "local-cyberpeer-pod.json")["tensors"][tensor_name]["storage"]),
            "planned_output": display_path(output_path, root),
            "record_count": tensor["record_count"],
            "shape": tensor["shape"],
            "dtype": tensor["dtype"],
            "axis_order": tensor["axis_order"],
            "source_record_ids": source_summary["record_ids"],
            "source_hashes": source_summary["source_hashes"],
            "lineage_links": source_summary["lineage_links"],
            "output_sha256": sha256_text(output_path.read_text(encoding="utf-8")),
        }

    outside_parameters.extend({
        "kind": "manifest_condition",
        "location": manifest.get("dry_run_id", ""),
        "reason": condition,
    } for condition in conditions if "lineage chain" not in condition and "source_hash does not match" not in condition)
    total_records = sum(by_tensor_counts.values())
    broken_lineage = [record for record in lineage_records if record["continuity_status"] == "outside_working_parameters"]
    report = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "dry_run_id": manifest["dry_run_id"],
        "pod_id": manifest["pod_id"],
        "tensor_spec_id": manifest["tensor_spec_id"],
        "manifest_path": display_path(manifest_path, root),
        "scope": "local fixture copied records only",
        "working_parameters": {
            "mode": "copied-record-dry-run",
            "source_scope": "local fixture copied records only",
            "pod_state_effect": "unchanged",
            "migration_execution": False,
            "live_reach": False,
        },
        "source_copy_roots": [
            {
                "root_id": manifest["source"]["copy_batch_id"],
                "path": manifest["source"]["root"],
                "kind": manifest["source"]["kind"],
                "exists": (root / manifest["source"]["root"]).exists(),
                "record_files": [target["source_records"] for target in manifest["targets"].values()],
            }
        ],
        "source_counts": {
            "total_records": total_records,
            "mapped_records": total_records,
            "outside_parameter_records": len(outside_parameters),
            "by_tensor": by_tensor_counts,
        },
        "hash_preservation": {
            "source_hash_scope": "normalized_source_record",
            "verification_counts": {
                "verified": sum(1 for item in hash_records if item["verification"] == "verified"),
                "mismatch": sum(1 for item in hash_records if item["verification"] == "mismatch"),
                "unverifiable_source_absent": sum(1 for item in hash_records if item["verification"] == "unverifiable_source_absent"),
            },
            "records": hash_records,
        },
        "lineage_continuity": {
            "valid_chain_count": len(lineage_records) - len(broken_lineage),
            "broken_chain_count": len(broken_lineage),
            "records": lineage_records,
        },
        "outside_parameters": outside_parameters,
        "live_reach": False,
        "source_effect": manifest["working_parameters"]["source_effect"],
        "output_effect": manifest["working_parameters"]["output_effect"],
        "conditions": conditions,
        "ready_for_independent_review": not conditions,
        "tensors": tensors,
        "dry_run_result": {
            "status": "pass" if not outside_parameters else "review_needed",
            "migration_executed": False,
            "target_records_written": 0,
        },
    }
    report_path = root / "reports" / "runtime" / "migration-dry-run" / "dry-run-report.json"
    write_json(report_path, report)
    health = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "scope": "local fixture copied records only",
        "live_reach": False,
        "report_path": display_path(report_path, root),
        "report_sha256": sha256_text(report_path.read_text(encoding="utf-8")),
        "conditions": conditions,
        "ready_for_independent_review": not conditions,
    }
    write_json(root / "reports" / "runtime" / "migration-dry-run-health.json", health)
    return health


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local DataQuadPod copied-record migration dry-run.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--manifest", default=None, help="Optional manifest path")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else None
    health = run_dry_run(root, manifest_path)
    if health["conditions"]:
        print("VISIBLE CONDITIONS migration dry-run has conditions to resolve")
        for condition in health["conditions"]:
            print(f"CONDITION {condition}")
        return 1
    print("PASS DataQuadPod copied-record migration dry-run completed from local fixtures")
    print(f"ROOT {root}")
    print("BOUNDARY local fixture copied records only; no live DataQuad roots referenced")
    print(f"REPORT {health['report_path']} sha256={health['report_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
