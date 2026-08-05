from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.aegis_pod.tensor_runtime import TENSOR_NAMES, load_jsonl, sha256_text, stable_json, verify_source_hash, write_json


PEER_ID = "CP-1004-ORION"
SOURCE_VM = {"host": "AEGISOrionPeer", "ip": "20.119.37.133", "user": "azureuser"}
SOURCE_DATAQUAD_ROOT = "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad"
EXCLUDED_SOURCE_SURFACES = [
    "/home/azureuser/orion-bridge/data/dataquad",
    "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad.backup-before-chamber-backfill-20260708T193819Z",
    "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad.backup-before-chamber-backfill-",
]
SCHEMA_VERSION = "0.1.0"


def utc_now_compact() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def safe_record_name(line_number: int, record_id: str) -> str:
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in record_id)
    return f"{line_number:06d}-{safe[:80]}.json"


def read_text_hash(path: Path) -> str:
    return sha256_text(path.read_text(encoding="utf-8"))


def live_copy_root(root: Path, batch_id: str, peer_id: str = PEER_ID) -> Path:
    return root / "live-copies" / peer_id / batch_id


def raw_file_path(root: Path, batch_id: str, tensor_name: str, peer_id: str = PEER_ID) -> Path:
    return live_copy_root(root, batch_id, peer_id) / "raw" / f"{tensor_name}.jsonl"


def remote_source_path(tensor_name: str) -> str:
    return f"{SOURCE_DATAQUAD_ROOT}/{tensor_name}.jsonl"


def run_checked(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def remote_sha256(remote_path: str) -> str:
    output = run_checked(["ssh", f"{SOURCE_VM['user']}@{SOURCE_VM['ip']}", "sha256sum", remote_path])
    return output.split()[0].upper()


def copy_authoritative_live_files(root: Path, batch_id: str) -> dict[str, str]:
    remote_hashes: dict[str, str] = {}
    raw_root = live_copy_root(root, batch_id) / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)
    for tensor_name in TENSOR_NAMES:
        remote_path = remote_source_path(tensor_name)
        remote_hashes[tensor_name] = remote_sha256(remote_path)
        run_checked([
            "scp",
            "-q",
            f"{SOURCE_VM['user']}@{SOURCE_VM['ip']}:{remote_path}",
            str(raw_file_path(root, batch_id, tensor_name)),
        ])
    return remote_hashes


def load_remote_hashes(root: Path, batch_id: str) -> dict[str, str]:
    hash_path = live_copy_root(root, batch_id) / "remote-sha256.json"
    if not hash_path.exists():
        return {}
    with hash_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value).upper() for key, value in data.items()}


def existing_copied_at_utc(root: Path, batch_id: str) -> str:
    manifest_path = live_copy_root(root, batch_id) / "copy-manifest.json"
    if not manifest_path.exists():
        return ""
    with manifest_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return ""
    return str(data.get("copied_at_utc", ""))


def build_copy_manifest(
    root: Path,
    batch_id: str,
    copied_at_utc: str | None = None,
    remote_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    copied_at_utc = copied_at_utc or existing_copied_at_utc(root, batch_id) or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    remote_hashes = remote_hashes or load_remote_hashes(root, batch_id)
    files: dict[str, Any] = {}
    missing: list[str] = []
    for tensor_name in TENSOR_NAMES:
        raw_path = raw_file_path(root, batch_id, tensor_name)
        if not raw_path.exists():
            missing.append(display_path(raw_path, root))
            continue
        records = load_jsonl(raw_path)
        local_hash = read_text_hash(raw_path)
        remote_hash = str(remote_hashes.get(tensor_name, "")).upper()
        files[tensor_name] = {
            "tensor": tensor_name,
            "source_path": remote_source_path(tensor_name),
            "remote_path_used": remote_source_path(tensor_name),
            "local_raw_path": display_path(raw_path, root),
            "sha256": local_hash,
            "remote_sha256": remote_hash,
            "local_sha256": local_hash,
            "copy_verified": bool(remote_hash and remote_hash == local_hash),
            "record_count": len(records),
            "byte_count": raw_path.stat().st_size,
        }
    if missing:
        raise FileNotFoundError("missing live copy raw files: " + ", ".join(missing))
    return {
        "schema_version": SCHEMA_VERSION,
        "copy_batch_id": batch_id,
        "peer_id": PEER_ID,
        "source_vm": SOURCE_VM,
        "copied_at_utc": copied_at_utc,
        "working_parameters": {
            "source_live_reach": True,
            "source_write_performed": False,
            "target_records_written": 0,
            "live_read_only": True,
        },
        "excluded_source_surfaces": EXCLUDED_SOURCE_SURFACES,
        "files": files,
    }


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
            "origin": f"live-copy {PEER_ID}",
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


def live_readiness_path_gate(report: dict[str, Any]) -> dict[str, Any]:
    allowed_prefixes = tuple(report["test_scaffolding_boundary"]["live_readiness_evidence_may_reference"])
    excluded_prefixes = tuple(report["test_scaffolding_boundary"]["test_only_paths_excluded"])
    referenced_paths: list[str] = [report["mapped_output_root"], report["source_snapshot_root"]]
    for file_entry in report["copy_manifest"]["files"].values():
        referenced_paths.append(str(file_entry["local_raw_path"]))
    blocked_paths = [
        path for path in referenced_paths
        if path.startswith(excluded_prefixes) or not path.startswith(allowed_prefixes)
    ]
    return {
        "status": "pass" if not blocked_paths else "review_needed",
        "allowed_prefixes": list(allowed_prefixes),
        "excluded_prefixes": list(excluded_prefixes),
        "referenced_paths_checked": len(referenced_paths),
        "blocked_paths": blocked_paths,
    }


def copy_fidelity_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    files = manifest.get("files", {})
    results = []
    for tensor_name in TENSOR_NAMES:
        entry = files.get(tensor_name, {})
        results.append({
            "tensor": tensor_name,
            "remote_path_used": entry.get("remote_path_used", ""),
            "remote_sha256": entry.get("remote_sha256", ""),
            "local_sha256": entry.get("local_sha256", ""),
            "copy_verified": entry.get("copy_verified") is True,
            "authoritative_path_used": entry.get("remote_path_used") == remote_source_path(tensor_name),
        })
    return {
        "status": "pass" if all(item["copy_verified"] and item["authoritative_path_used"] for item in results) else "review_needed",
        "results": results,
    }


def map_live_copy(
    root: Path,
    batch_id: str,
    copied_at_utc: str | None = None,
    remote_hashes: dict[str, str] | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    manifest = build_copy_manifest(root, batch_id, copied_at_utc, remote_hashes)
    mapped_counts: dict[str, int] = {}
    hash_records: list[dict[str, Any]] = []
    lineage_records: list[dict[str, Any]] = []
    outside_parameters: list[dict[str, str]] = []

    for tensor_name in TENSOR_NAMES:
        raw_records = load_jsonl(raw_file_path(root, batch_id, tensor_name))
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

    total_records = sum(mapped_counts.values())
    report = {
        "schema_version": SCHEMA_VERSION,
        "stage": "Stage B Orion live-record mapping",
        "status": "pass" if not outside_parameters else "review_needed",
        "copy_manifest": manifest,
        "mapped_output_root": display_path(live_copy_root(root, batch_id) / "mapped", root),
        "source_snapshot_root": display_path(live_copy_root(root, batch_id) / "source-records", root),
        "working_parameters": {
            "source_live_reach": True,
            "source_write_performed": False,
            "target_records_written": 0,
            "tensor_generation": False,
            "live_population": False,
            "placeholder_data_used": False,
            "mock_data_used": False,
            "demo_data_used": False,
            "raw_live_copies_git_tracked": False,
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
        "test_scaffolding_boundary": {
            "live_readiness_evidence_may_reference": ["live-copies/", "reports/runtime/2026-07-21-live-stage-b-orion-mapping-report.json"],
            "test_only_paths_excluded": [
                "fixtures/tensor-records/",
                "fixtures/copied-record-roots/",
                "fixtures/migration-dry-run.json",
                "reports/runtime/tensors/",
                "reports/runtime/migration-dry-run/",
            ],
            "stage_c_d_gate": "no placeholder, mock, or demo data may be referenced by live-readiness evidence",
        },
        "outside_parameters": outside_parameters,
    }
    report["copy_fidelity_gate"] = copy_fidelity_gate(manifest)
    report["live_readiness_path_gate"] = live_readiness_path_gate(report)
    if report["copy_fidelity_gate"]["status"] != "pass":
        report["outside_parameters"].append({
            "kind": "copy_fidelity_not_verified",
            "location": batch_id,
            "reason": "One or more copied files lacks matching remote/local SHA256 evidence from the authoritative source path.",
        })
    if report["live_readiness_path_gate"]["status"] != "pass":
        report["outside_parameters"].append({
            "kind": "live_readiness_path_gate_failed",
            "location": batch_id,
            "reason": "Live-readiness evidence references a test-only or unapproved path.",
        })
    report["status"] = "pass" if not report["outside_parameters"] else "review_needed"
    write_json(report_path or root / "reports" / "runtime" / "2026-07-21-live-stage-b-orion-mapping-report.json", report)
    write_json(live_copy_root(root, batch_id) / "copy-manifest.json", manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Map copied Orion live DataQuad records into the DataQuadPod tensor-record contract.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--batch-id", default="", help="Existing live copy batch id under live-copies/CP-1004-ORION/")
    parser.add_argument("--copy-from-orion", action="store_true", help="Copy authoritative Orion files with remote SHA256 evidence before mapping")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    batch_id = args.batch_id or f"orion-live-copy-{utc_now_compact()}"
    remote_hashes = copy_authoritative_live_files(root, batch_id) if args.copy_from_orion else None
    if remote_hashes:
        write_json(live_copy_root(root, batch_id) / "remote-sha256.json", remote_hashes)
    report = map_live_copy(root, batch_id, remote_hashes=remote_hashes)
    print("PASS Stage B live-record mapping built" if report["status"] == "pass" else "REVIEW_NEEDED Stage B live-record mapping")
    print(f"BATCH {batch_id}")
    print("BOUNDARY read copied live Orion records; zero writes to Orion; no tensor generation; no live population")
    print(f"RECORDS total={report['source_counts']['total_records']} verified={report['hash_preservation']['verification_counts']['verified']}")
    print(f"OUTSIDE_PARAMETERS {len(report['outside_parameters'])}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
