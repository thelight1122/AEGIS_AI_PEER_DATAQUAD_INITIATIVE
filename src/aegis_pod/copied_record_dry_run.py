from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.aegis_pod.tensor_runtime import (
    DEFAULT_EMBEDDING_DIMENSION,
    DEFAULT_METADATA_DIMENSION,
    DEFAULT_POD_ID,
    DEFAULT_TENSOR_SPEC_ID,
    TENSOR_NAMES,
    load_jsonl,
    parse_record,
    sha256_text,
    verify_source_hash,
    write_json,
)


FIXTURE_CREATED_UTC = "2026-07-20T22:25:00Z"
MANIFEST_ID = "copied-record-dry-run-local-fixture-0.1.0"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def source_root_entry(copy_root: dict[str, Any], copy_root_path: Path, root: Path) -> dict[str, Any]:
    record_files = copy_root.get("record_files", {})
    paths = [str(value) for value in record_files.values()] if isinstance(record_files, dict) else []
    return {
        "root_id": str(copy_root.get("copy_root_id", "")),
        "path": display_path(copy_root_path, root),
        "kind": str(copy_root.get("kind", "local_fixture_copy")),
        "exists": copy_root_path.exists(),
        "record_files": paths,
    }


def run_dry_run(root: Path, copy_root_path: Path | None = None, output_path: Path | None = None) -> dict[str, Any]:
    copy_root_path = copy_root_path or root / "fixtures" / "copied-record-roots" / "local-dataquad-copy.json"
    output_path = output_path or root / "reports" / "runtime" / "migration" / "copied-record-dry-run-manifest.json"
    copy_root = load_json(copy_root_path)
    record_files = copy_root.get("record_files", {})
    if not isinstance(record_files, dict):
        raise ValueError("copy root record_files will be an object")

    pod = load_json(root / "fixtures" / "local-cyberpeer-pod.json")
    tensor_target_mapping: dict[str, Any] = {}
    hash_records: list[dict[str, Any]] = []
    lineage_records: list[dict[str, Any]] = []
    outside_parameters: list[dict[str, str]] = []
    source_counts = {name: 0 for name in TENSOR_NAMES}

    for tensor_name in TENSOR_NAMES:
        declared_file = record_files.get(tensor_name)
        if not isinstance(declared_file, str):
            outside_parameters.append({
                "kind": "missing_record_file",
                "location": f"record_files.{tensor_name}",
                "reason": "No copied source file was declared for this tensor.",
            })
            records_data: list[dict[str, Any]] = []
            source_file = ""
        else:
            source_file = declared_file
            source_path = root / declared_file
            if source_path.exists():
                records_data = load_jsonl(source_path)
            else:
                outside_parameters.append({
                    "kind": "missing_record_file",
                    "location": declared_file,
                    "reason": "Declared copied source file is not present in the local workspace.",
                })
                records_data = []

        parsed_records = []
        previous_source_hash = ""
        for index, record_data in enumerate(records_data):
            try:
                record = parse_record(record_data, tensor_name)
                parsed_records.append(record)
            except ValueError as exc:
                outside_parameters.append({
                    "kind": "record_contract_mismatch",
                    "location": f"{source_file}:{index + 1}",
                    "reason": str(exc),
                })
                continue

            verification = verify_source_hash(record_data, root)
            hash_records.append({
                "tensor": tensor_name,
                "record_id": record.record_id,
                "source_record_id": record.source_record_id,
                "source_hash": record.source_hash,
                **verification,
            })
            if verification["verification"] == "mismatch":
                outside_parameters.append({
                    "kind": "source_hash_mismatch",
                    "location": record.record_id,
                    "reason": "source_hash does not match the recomputed normalized source record hash.",
                })

            parent_record_id = str(record.lineage.get("parent_record_id", ""))
            previous_record_hash = str(record.lineage.get("previous_record_hash", ""))
            if not parent_record_id and not previous_record_hash:
                continuity_status = "root_record"
            elif previous_record_hash == previous_source_hash:
                continuity_status = "continuous"
            else:
                continuity_status = "outside_working_parameters"
                outside_parameters.append({
                    "kind": "lineage_continuity_gap",
                    "location": record.record_id,
                    "reason": "previous_record_hash does not match the prior copied record source_hash in this dry-run order.",
                })

            lineage_records.append({
                "tensor": tensor_name,
                "record_id": record.record_id,
                "parent_record_id": parent_record_id,
                "previous_record_hash": previous_record_hash,
                "continuity_status": continuity_status,
            })
            previous_source_hash = record.source_hash

        source_counts[tensor_name] = len(parsed_records)
        target_storage = pod.get("tensors", {}).get(tensor_name, {}).get("storage", "")
        tensor_target_mapping[tensor_name] = {
            "source_file": source_file,
            "target_tensor": tensor_name,
            "target_storage": str(target_storage),
            "planned_record_count": len(parsed_records),
            "target_shape": [len(parsed_records), DEFAULT_EMBEDDING_DIMENSION, DEFAULT_METADATA_DIMENSION],
        }

    total_records = sum(source_counts.values())
    broken_chain_count = sum(1 for item in lineage_records if item["continuity_status"] == "outside_working_parameters")
    manifest = {
        "schema_version": "0.1.0",
        "manifest_id": MANIFEST_ID,
        "pod_id": DEFAULT_POD_ID,
        "tensor_spec_id": DEFAULT_TENSOR_SPEC_ID,
        "created_utc": FIXTURE_CREATED_UTC,
        "working_parameters": {
            "mode": "copied-record-dry-run",
            "source_scope": str(copy_root.get("source_scope", "Local copied records only.")),
            "pod_state_effect": "unchanged",
            "migration_execution": False,
            "live_reach": False,
        },
        "source_copy_roots": [source_root_entry(copy_root, copy_root_path, root)],
        "tensor_target_mapping": tensor_target_mapping,
        "source_counts": {
            "total_records": total_records,
            "mapped_records": total_records,
            "outside_parameter_records": len(outside_parameters),
            "by_tensor": source_counts,
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
            "valid_chain_count": len(lineage_records) - broken_chain_count,
            "broken_chain_count": broken_chain_count,
            "records": lineage_records,
        },
        "outside_parameters": outside_parameters,
        "live_reach": False,
        "dry_run_result": {
            "status": "pass" if not outside_parameters else "review_needed",
            "migration_executed": False,
            "target_records_written": 0,
        },
    }
    write_json(output_path, manifest)

    health = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "scope": "local copied-record dry-run only",
        "live_reach": False,
        "manifest_path": display_path(output_path, root),
        "manifest_sha256": sha256_text(output_path.read_text(encoding="utf-8")),
        "record_count": total_records,
        "outside_parameter_count": len(outside_parameters),
        "migration_executed": False,
    }
    write_json(root / "reports" / "runtime" / "migration" / "copied-record-dry-run-health.json", health)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local copied-record dry-run migration manifest.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    manifest = run_dry_run(root)
    print("PASS copied-record dry-run manifest built")
    print(f"ROOT {root}")
    print("BOUNDARY local copied records only; no live DataQuad roots referenced")
    print(f"RECORDS mapped={manifest['source_counts']['mapped_records']} outside={manifest['source_counts']['outside_parameter_records']}")
    print("MIGRATION_EXECUTED false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
