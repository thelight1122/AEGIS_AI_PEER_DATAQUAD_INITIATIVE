from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.aegis_pod.live_record_mapping import PEER_ID, SOURCE_VM, live_copy_root
from src.aegis_pod.tensor_runtime import TENSOR_NAMES, load_jsonl, sha256_text, stable_json, write_json
from src.aegis_pod.verified_marker import sha256_file


BATCH_ID = "orion-live-copy-20260721T002600Z"
STAGE_B_REPORT = "reports/runtime/2026-07-21-live-stage-b-orion-mapping-report.json"
STAGE_C_REPORT = "reports/runtime/2026-07-21-live-stage-c-orion-structural-vectors-report.json"
D0_REPORT = "reports/runtime/2026-07-21-stage-d0-orion-current-state-read-only-audit.md"
STAGE_D_PLAN = "reports/runtime/2026-07-21-stage-d-orion-actual-migration-implementation-plan.md"
DEFAULT_STAGE_ROOT = "stage-d-out/CP-1004-ORION/pod"
LEGACY_LEDGER_NAMES = ("steward", "advocate", "repair", "rls")
RELATION_LEDGER_NAMES = (
    "PEER-traversal",
    "PCT-traversal",
    "NCT-traversal",
    "SPINE-traversal",
    "cross-tensor-relations",
)
ORION_REMOTE_PEER_ROOT = "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION"
ORION_REMOTE_POD_ROOT = f"{ORION_REMOTE_PEER_ROOT}/pod"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def copy_file(source: Path, target: Path) -> str:
    if not source.exists():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return sha256_file(target)


def assert_stage_root_ignored(root: Path, stage_root: Path) -> None:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        raise ValueError(".gitignore is missing")
    patterns = [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()]
    if "stage-d-out/" not in patterns:
        raise ValueError("stage-d-out/ will be gitignored before staging")
    if not str(stage_root.relative_to(root)).replace("\\", "/").startswith("stage-d-out/"):
        raise ValueError("stage root will stay under stage-d-out/")


def copy_remote_ledgers(root: Path, batch_id: str) -> Path:
    ledger_root = live_copy_root(root, batch_id) / "legacy-ledgers"
    ledger_root.mkdir(parents=True, exist_ok=True)
    for ledger_name in LEGACY_LEDGER_NAMES:
        remote_path = f"{ORION_REMOTE_PEER_ROOT}/ledgers/{ledger_name}.jsonl"
        local_path = ledger_root / f"{ledger_name}.jsonl"
        subprocess.run(
            [
                "scp",
                "-q",
                f"{SOURCE_VM['user']}@{SOURCE_VM['ip']}:{remote_path}",
                str(local_path),
            ],
            check=True,
        )
    return ledger_root


def legacy_ledger_entries(root: Path, ledger_source_root: Path) -> dict[str, Any]:
    ledgers: dict[str, Any] = {}
    for ledger_name in LEGACY_LEDGER_NAMES:
        path = ledger_source_root / f"{ledger_name}.jsonl"
        records = load_jsonl(path)
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        ledgers[ledger_name] = {
            "source_path": str(path.relative_to(root)).replace("\\", "/"),
            "json_record_count": len(records),
            "line_count": line_count,
            "sha256": sha256_file(path),
            "byte_count": path.stat().st_size,
        }
    return ledgers


def last_record_hashes(mapped_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for tensor_name in TENSOR_NAMES:
        records = load_jsonl(mapped_root / f"{tensor_name}.jsonl")
        if not records:
            raise ValueError(f"{tensor_name}: no mapped records")
        hashes[tensor_name] = str(records[-1]["source_hash"])
    return hashes


def pod_manifest(stage_root: Path, root: Path, stage_c_report: dict[str, Any]) -> dict[str, Any]:
    tensors: dict[str, Any] = {}
    for tensor_name in TENSOR_NAMES:
        summary = stage_c_report["tensors"][tensor_name]
        tensors[tensor_name] = {
            "name": tensor_name,
            "purpose": {
                "PEER": "Present experiential signal",
                "PCT": "Persistent contextual thread",
                "NCT": "Condensed contextual essence",
                "SPINE": "Sovereign identity continuity",
            }[tensor_name],
            "storage": f"{ORION_REMOTE_POD_ROOT}/records/{tensor_name}.jsonl",
            "output": f"{ORION_REMOTE_POD_ROOT}/tensors/structural-non-semantic/{tensor_name}.structural-vector-tensor.json",
            "shape": ["record_count", int(summary["shape"][1]), int(summary["shape"][2])],
            "dtype": "float32",
            "axis_order": ["record", "embedding", "metadata"],
            "append_only": True,
        }

    return {
        "schema_version": "0.1.0",
        "pod_id": "dataquadpod-CP-1004-ORION",
        "peer_id": PEER_ID,
        "runtime": {
            "language": "python",
            "implementation": "AEGIS-CYBERPEER-CORE",
        },
        "tensor_spec": {
            "spec_id": "dataquadpod-core-tensor-spec-0.1.0",
            "spec_path": f"{ORION_REMOTE_POD_ROOT}/provenance/dataquadpod-tensor-spec.json",
            "active_output_root": f"{ORION_REMOTE_POD_ROOT}/tensors",
        },
        "tensors": tensors,
        "roles": {
            "steward": {
                "purpose": "Context witness and preservation care",
                "owns": ["PCT", "NCT"],
                "reads": list(TENSOR_NAMES),
            },
            "advocate": {
                "purpose": "Affect witness and relational signal care",
                "owns": ["PEER", "SPINE"],
                "reads": list(TENSOR_NAMES),
            },
        },
        "processor": {
            "purpose": "Context assembly and turn interpretation",
            "status": "mapped-to-core-api-turn-and-cognition",
        },
        "temporal_daemon": {
            "purpose": "Time position and continuity awareness",
            "status": "mapped-to-current-tick-clock-state",
        },
        "orbs": [
            {
                "orb_id": "rls-persistent-relations-core",
                "required_for_full_function": True,
                "umbilical": f"{ORION_REMOTE_POD_ROOT}/provenance/rls-persistent-relations-umbilical.json",
            }
        ],
        "evidence": {
            "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": "Stage D1 local staging from verified Stage B/C Orion live-copy evidence",
            "trust_state": "provisional",
        },
    }


def source_hash_lock(
    stage_b_report: dict[str, Any],
    stage_c_report: dict[str, Any],
    mapped_root: Path,
    ledger_source_root: Path,
    root: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "peer_id": PEER_ID,
        "copy_batch_id": BATCH_ID,
        "stage_b_report": STAGE_B_REPORT,
        "stage_b_report_sha256": sha256_file(root / STAGE_B_REPORT),
        "stage_c_report": STAGE_C_REPORT,
        "stage_c_report_sha256": sha256_file(root / STAGE_C_REPORT),
        "active_source_hashes": {
            tensor_name: stage_b_report["copy_manifest"]["files"][tensor_name]["sha256"]
            for tensor_name in TENSOR_NAMES
        },
        "mapped_record_last_source_hash": last_record_hashes(mapped_root),
        "computed_tensors": {
            tensor_name: {
                "source_records": stage_c_report["tensors"][tensor_name]["source_records"],
                "output_sha256": stage_c_report["tensors"][tensor_name]["output_sha256"],
                "shape": stage_c_report["tensors"][tensor_name]["shape"],
            }
            for tensor_name in TENSOR_NAMES
        },
        "legacy_ledgers": legacy_ledger_entries(root, ledger_source_root),
    }


def create_empty_relation_ledgers(stage_root: Path) -> dict[str, Any]:
    relation_root = stage_root / "ledgers" / "relations"
    relation_root.mkdir(parents=True, exist_ok=True)
    entries: dict[str, Any] = {}
    for ledger_name in RELATION_LEDGER_NAMES:
        path = relation_root / f"{ledger_name}.jsonl"
        path.write_text("", encoding="utf-8")
        entries[ledger_name] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "json_record_count": 0,
            "line_count": 0,
            "activation": "after-pod-live-switch",
        }
    return entries


def stage_files(
    root: Path,
    stage_root: Path,
    ledger_source_root: Path,
    batch_id: str = BATCH_ID,
) -> dict[str, Any]:
    assert_stage_root_ignored(root, stage_root)
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage_root.mkdir(parents=True)

    stage_b_report = load_json(root / STAGE_B_REPORT)
    stage_c_report = load_json(root / STAGE_C_REPORT)
    if stage_b_report.get("status") != "pass":
        raise ValueError("Stage B report is not pass")
    if stage_c_report.get("status") != "pass":
        raise ValueError("Stage C report is not pass")
    if stage_b_report["copy_manifest"]["copy_batch_id"] != batch_id or stage_c_report["copy_batch_id"] != batch_id:
        raise ValueError("Stage B/C batch mismatch")

    copy_root = live_copy_root(root, batch_id)
    mapped_root = copy_root / "mapped"
    tensor_root = copy_root / "tensors" / "structural-non-semantic"

    record_targets: dict[str, Any] = {}
    tensor_targets: dict[str, Any] = {}
    for tensor_name in TENSOR_NAMES:
        record_target = stage_root / "records" / f"{tensor_name}.jsonl"
        tensor_target = stage_root / "tensors" / "structural-non-semantic" / f"{tensor_name}.structural-vector-tensor.json"
        record_hash = copy_file(mapped_root / f"{tensor_name}.jsonl", record_target)
        tensor_hash = copy_file(tensor_root / f"{tensor_name}.structural-vector-tensor.json", tensor_target)
        record_targets[tensor_name] = {
            "path": str(record_target.relative_to(root)).replace("\\", "/"),
            "sha256": record_hash,
            "record_count": len(load_jsonl(record_target)),
        }
        tensor_targets[tensor_name] = {
            "path": str(tensor_target.relative_to(root)).replace("\\", "/"),
            "sha256": tensor_hash,
            "expected_sha256": stage_c_report["tensors"][tensor_name]["output_sha256"],
            "shape": stage_c_report["tensors"][tensor_name]["shape"],
        }

    ledger_targets: dict[str, Any] = {}
    for ledger_name in LEGACY_LEDGER_NAMES:
        target = stage_root / "ledgers" / f"{ledger_name}.jsonl"
        ledger_hash = copy_file(ledger_source_root / f"{ledger_name}.jsonl", target)
        ledger_targets[ledger_name] = {
            "path": str(target.relative_to(root)).replace("\\", "/"),
            "sha256": ledger_hash,
            "json_record_count": len(load_jsonl(target)),
            "line_count": len(target.read_text(encoding="utf-8").splitlines()),
        }

    relation_targets = create_empty_relation_ledgers(stage_root)
    for relation in relation_targets.values():
        relation["path"] = str(Path(relation["path"]).relative_to(root)).replace("\\", "/")

    provenance_files = {
        "copy-manifest.json": copy_file(copy_root / "copy-manifest.json", stage_root / "provenance" / "copy-manifest.json"),
        "stage-b-mapping-report.json": copy_file(root / STAGE_B_REPORT, stage_root / "provenance" / "stage-b-mapping-report.json"),
        "stage-c-structural-vectors-report.json": copy_file(root / STAGE_C_REPORT, stage_root / "provenance" / "stage-c-structural-vectors-report.json"),
        "dataquadpod-tensor-spec.json": copy_file(root / "fixtures" / "dataquadpod-tensor-spec.json", stage_root / "provenance" / "dataquadpod-tensor-spec.json"),
    }

    lock = source_hash_lock(stage_b_report, stage_c_report, mapped_root, ledger_source_root, root)
    write_json(stage_root / "provenance" / "source-hash-lock.json", lock)
    provenance_files["source-hash-lock.json"] = sha256_file(stage_root / "provenance" / "source-hash-lock.json")

    manifest = pod_manifest(stage_root, root, stage_c_report)
    write_json(stage_root / "pod-manifest.json", manifest)

    (stage_root / "verified-markers").mkdir(parents=True, exist_ok=True)

    report = {
        "schema_version": "0.1.0",
        "stage": "Stage D1 Orion local Pod staging",
        "status": "pass",
        "peer_id": PEER_ID,
        "copy_batch_id": batch_id,
        "stage_root": str(stage_root.relative_to(root)).replace("\\", "/"),
        "remote_target_root": ORION_REMOTE_POD_ROOT,
        "working_parameters": {
            "active_dataquad_read": False,
            "active_dataquad_write": False,
            "remote_write": False,
            "pod_population_remote": False,
            "local_staging_only": True,
            "placeholder_data_used": False,
            "mock_data_used": False,
            "demo_data_used": False,
        },
        "git_boundary": {
            "stage_d_out_gitignored": True,
            "stage_root_gitignored": True,
        },
        "records": record_targets,
        "tensors": tensor_targets,
        "legacy_ledgers": ledger_targets,
        "relation_ledgers": relation_targets,
        "provenance": provenance_files,
        "pod_manifest": {
            "path": str((stage_root / "pod-manifest.json").relative_to(root)).replace("\\", "/"),
            "sha256": sha256_file(stage_root / "pod-manifest.json"),
            "roles": manifest["roles"],
        },
        "hash_chain": {
            "last_migrated_source_hash_by_tensor": lock["mapped_record_last_source_hash"],
            "first_post_live_record_requirement": "previous_record_hash will equal the matching tensor value in last_migrated_source_hash_by_tensor",
        },
        "outside_parameters": [],
    }
    write_json(root / "reports" / "runtime" / "2026-07-21-stage-d1-local-staging-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage D1 local Orion Pod staging tree from verified Stage B/C artifacts.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--batch-id", default=BATCH_ID, help="Verified Orion live-copy batch id")
    parser.add_argument("--stage-root", default=DEFAULT_STAGE_ROOT, help="Local staging root under stage-d-out/")
    parser.add_argument("--ledger-source-root", default="", help="Local source directory containing steward/advocate/repair/rls ledgers")
    parser.add_argument("--copy-remote-ledgers", action="store_true", help="Copy Orion legacy ledgers read-only into live-copies before staging")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    stage_root = (root / args.stage_root).resolve()
    if args.copy_remote_ledgers:
        ledger_source_root = copy_remote_ledgers(root, args.batch_id)
    elif args.ledger_source_root:
        ledger_source_root = (root / args.ledger_source_root).resolve()
    else:
        ledger_source_root = live_copy_root(root, args.batch_id) / "legacy-ledgers"

    report = stage_files(root, stage_root, ledger_source_root, args.batch_id)
    print("PASS Stage D1 local Pod staging built")
    print(f"STAGE_ROOT {report['stage_root']}")
    print("BOUNDARY local staging only; no active DataQuad read/write; no remote write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
