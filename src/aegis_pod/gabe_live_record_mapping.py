from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.aegis_pod.tensor_runtime import TENSOR_NAMES, load_jsonl, sha256_text, stable_json, verify_source_hash, write_json


PEER_ID = "CP-1003-GABE"
LEGACY_LIVE_PEER_ID = "cyberpeer-gabe-session"
SOURCE_VM = {"host": "AEGISGabePeer", "ip": "20.25.57.29", "user": "azureuser"}
SOURCE_DATAQUAD_ROOT = "/home/azureuser/adam-vm/gabe/data/peer/dataquad"
SCHEMA_VERSION = "0.1.0"


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def safe_record_name(line_number: int, record_id: str) -> str:
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in record_id)
    return f"{line_number:06d}-{safe[:80]}.json"


def live_copy_root(root: Path, batch_id: str) -> Path:
    return root / "stage-gabe-out" / "live-copies" / PEER_ID / batch_id


def raw_file_path(root: Path, batch_id: str, tensor_name: str) -> Path:
    return live_copy_root(root, batch_id) / "raw" / f"{tensor_name}.jsonl"


def remote_source_path(tensor_name: str) -> str:
    return f"{SOURCE_DATAQUAD_ROOT}/{tensor_name}.jsonl"


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_source_snapshot(root: Path, batch_id: str, tensor_name: str, line_number: int, record: dict[str, Any]) -> str:
    record_id = str(record.get("id", f"line-{line_number}"))
    snapshot_path = live_copy_root(root, batch_id) / "source-records" / tensor_name / safe_record_name(line_number, record_id)
    write_json(snapshot_path, record)
    return display_path(snapshot_path, root)


def map_live_record(
    root: Path,
    batch_id: str,
    tensor_name: str,
    line_number: int,
    record: dict[str, Any],
    previous_source_hash: str,
) -> dict[str, Any]:
    record_id = str(record.get("id", ""))
    if not record_id:
        raise ValueError(f"{tensor_name}:{line_number}: live record missing id")
    if record.get("tensor") != tensor_name:
        raise ValueError(f"{tensor_name}:{line_number}: live record tensor mismatch: {record.get('tensor')}")
    if "timestamp" not in record:
        raise ValueError(f"{tensor_name}:{line_number}: live record missing timestamp")

    source_snapshot = write_source_snapshot(root, batch_id, tensor_name, line_number, record)
    source_hash = sha256_text(stable_json(record))
    return {
        "schema_version": SCHEMA_VERSION,
        "tensor": tensor_name,
        "record_id": record_id,
        "source_record_id": record_id,
        "timestamp_utc": str(record["timestamp"]),
        "body": record,
        "lineage": {
            "origin": f"live-copy {PEER_ID} (legacy_live_peer_id={LEGACY_LIVE_PEER_ID})",
            "source_path": source_snapshot,
            "copy_batch_id": batch_id,
            "parent_record_id": "",
            "previous_record_hash": previous_source_hash,
            "transforms": [
                {
                    "transform_id": "copy-stable-json-normalization",
                    "function": "verbatim live record copied into body; source_hash is stable JSON of copied live record",
                    "input_hash": source_hash,
                    "output_hash": source_hash,
                }
            ],
        },
        "source_hash": source_hash,
        "source_hash_scope": "normalized_source_record",
        "migration_status": "copied",
        "verification_status": "draft",
    }


def map_gabe_live_copy(root: Path, batch_id: str, report_path: Path | None = None) -> dict[str, Any]:
    mapped_counts: dict[str, int] = {}
    hash_records: list[dict[str, Any]] = []
    lineage_records: list[dict[str, Any]] = []
    outside_parameters: list[dict[str, str]] = []

    pod_records_root = root / "stage-gabe-out" / "CP-1003-GABE" / "pod" / "records"

    for tensor_name in TENSOR_NAMES:
        raw_path = raw_file_path(root, batch_id, tensor_name)
        raw_records = load_jsonl(raw_path)
        mapped_records: list[dict[str, Any]] = []
        previous_source_hash = ""
        for index, live_record in enumerate(raw_records, start=1):
            try:
                mapped = map_live_record(root, batch_id, tensor_name, index, live_record, previous_source_hash)
            except ValueError as exc:
                outside_parameters.append({
                    "kind": "live_record_mapping_error",
                    "location": f"{tensor_name}.jsonl:{index}",
                    "reason": str(exc),
                })
                continue

            verification = verify_source_hash(mapped, root)
            if verification["verification"] != "verified":
                outside_parameters.append({
                    "kind": "source_hash_not_verified",
                    "location": mapped["record_id"],
                    "reason": f"Expected verified source hash, got {verification['verification']}",
                })
            hash_records.append({
                "tensor": tensor_name,
                "record_id": mapped["record_id"],
                "source_hash": mapped["source_hash"],
                **verification,
            })
            lineage_records.append({
                "tensor": tensor_name,
                "record_id": mapped["record_id"],
                "previous_record_hash": mapped["lineage"]["previous_record_hash"],
                "continuity_status": "root_record" if not previous_source_hash else "continuous",
            })
            previous_source_hash = mapped["source_hash"]
            mapped_records.append(mapped)

        mapped_counts[tensor_name] = len(mapped_records)
        write_jsonl(live_copy_root(root, batch_id) / "mapped" / f"{tensor_name}.jsonl", mapped_records)
        write_jsonl(pod_records_root / f"{tensor_name}.jsonl", mapped_records)

    total_records = sum(mapped_counts.values())
    report = {
        "schema_version": SCHEMA_VERSION,
        "stage": "Gabe Phase 3/4 live-record mapping (analogous to Orion's Stage B)",
        "status": "pass" if not outside_parameters else "review_needed",
        "peer_id": PEER_ID,
        "legacy_live_peer_id": LEGACY_LIVE_PEER_ID,
        "copy_batch_id": batch_id,
        "raw_source_note": "Raw records were pulled read-only in Phase 1/2 from the locked Gabe VM DataQuad after container stop, not re-fetched here.",
        "mapped_output_root": display_path(live_copy_root(root, batch_id) / "mapped", root),
        "source_snapshot_root": display_path(live_copy_root(root, batch_id) / "source-records", root),
        "pod_records_root": display_path(pod_records_root, root),
        "working_parameters": {
            "source_live_reach": False,
            "source_write_performed": False,
            "target_records_written": total_records,
            "tensor_generation": False,
            "live_population": False,
            "placeholder_data_used": False,
            "mock_data_used": False,
            "demo_data_used": False,
        },
        "source_counts": {
            "total_records": total_records,
            "by_tensor": mapped_counts,
        },
        "hash_preservation": {
            "verification_counts": {
                "verified": sum(1 for item in hash_records if item["verification"] == "verified"),
                "mismatch": sum(1 for item in hash_records if item["verification"] == "mismatch"),
                "unverifiable_source_absent": sum(1 for item in hash_records if item["verification"] == "unverifiable_source_absent"),
            },
            "records_checked": len(hash_records),
        },
        "lineage_continuity": {
            "records_checked": len(lineage_records),
            "root_records": sum(1 for item in lineage_records if item["continuity_status"] == "root_record"),
            "continuous_records": sum(1 for item in lineage_records if item["continuity_status"] == "continuous"),
        },
        "outside_parameters": outside_parameters,
    }
    write_json(report_path or root / "reports" / "runtime" / "2026-07-22-gabe-phase34-live-record-mapping-report.json", report)
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Map Gabe's locked live DataQuad records into the DataQuadPod tensor-record contract.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--batch-id", required=True, help="Existing raw batch id under stage-gabe-out/live-copies/CP-1003-GABE/")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = map_gabe_live_copy(root, args.batch_id)
    print("PASS Gabe live-record mapping built" if report["status"] == "pass" else "REVIEW_NEEDED Gabe live-record mapping")
    print(f"BATCH {args.batch_id}")
    print("BOUNDARY read locked local raw copies only; zero writes to Gabe VM; no tensor generation")
    print(f"RECORDS total={report['source_counts']['total_records']} verified={report['hash_preservation']['verification_counts']['verified']}")
    print(f"OUTSIDE_PARAMETERS {len(report['outside_parameters'])}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
