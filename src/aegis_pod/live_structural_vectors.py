from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.aegis_pod.live_record_mapping import PEER_ID, live_copy_root
from src.aegis_pod.tensor_runtime import (
    TENSOR_NAMES,
    add_structural_non_semantic_evidence,
    build_tensor_from_file,
    display_path,
    write_json,
)
from src.aegis_pod.verified_marker import sha256_file


REPORT_PATH = "reports/runtime/2026-07-21-live-stage-c-orion-structural-vectors-report.json"
MAPPING_REPORT = "reports/runtime/2026-07-21-live-stage-b-orion-mapping-report.json"
EMBEDDING_KIND = "structural-non-semantic"
TEST_ONLY_PATHS = [
    "fixtures/tensor-records/",
    "fixtures/copied-record-roots/",
    "fixtures/migration-dry-run.json",
    "reports/runtime/tensors/",
    "reports/runtime/migration-dry-run/",
]


def load_json(path: Path) -> dict[str, Any]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def require_pass_gate(report: dict[str, Any], gate_name: str) -> None:
    gate = report.get(gate_name, {})
    if not isinstance(gate, dict) or gate.get("status") != "pass":
        raise ValueError(f"{gate_name} is not passing")


def structural_output_root(root: Path, batch_id: str) -> Path:
    return live_copy_root(root, batch_id) / "tensors" / "structural-non-semantic"


def stage_c_path_gate(report: dict[str, Any]) -> dict[str, Any]:
    allowed_prefixes = ["live-copies/", REPORT_PATH]
    referenced_paths = [REPORT_PATH]
    referenced_paths.extend(str(item["output_path"]) for item in report["tensors"].values())
    blocked_paths = [
        path for path in referenced_paths
        if any(path.startswith(prefix) for prefix in TEST_ONLY_PATHS)
        or not any(path.startswith(prefix) for prefix in allowed_prefixes)
    ]
    return {
        "status": "pass" if not blocked_paths else "fail",
        "allowed_prefixes": allowed_prefixes,
        "excluded_prefixes": TEST_ONLY_PATHS,
        "referenced_paths_checked": len(referenced_paths),
        "blocked_paths": blocked_paths,
    }


def build_live_structural_vectors(root: Path, batch_id: str) -> dict[str, Any]:
    mapping_report_path = root / MAPPING_REPORT
    mapping_report = load_json(mapping_report_path)
    if mapping_report.get("status") != "pass":
        raise ValueError("Stage B mapping report is not passing")
    require_pass_gate(mapping_report, "copy_fidelity_gate")
    require_pass_gate(mapping_report, "live_readiness_path_gate")
    if mapping_report.get("copy_manifest", {}).get("copy_batch_id") != batch_id:
        raise ValueError("Stage B mapping report batch does not match requested batch")

    copied_at_utc = str(mapping_report.get("copy_manifest", {}).get("copied_at_utc", ""))
    output_root = structural_output_root(root, batch_id)
    output_root.mkdir(parents=True, exist_ok=True)
    tensor_summaries: dict[str, Any] = {}

    for tensor_name in TENSOR_NAMES:
        mapped_path = live_copy_root(root, batch_id) / "mapped" / f"{tensor_name}.jsonl"
        tensor_path = output_root / f"{tensor_name}.structural-vector-tensor.json"
        tensor = build_tensor_from_file(mapped_path, tensor_path, tensor_name)
        add_structural_non_semantic_evidence(tensor, batch_id, copied_at_utc)
        write_json(tensor_path, tensor)
        tensor_summaries[tensor_name] = {
            "source_records": display_path(mapped_path, root).replace("\\", "/"),
            "output_path": display_path(tensor_path, root).replace("\\", "/"),
            "output_sha256": sha256_file(tensor_path),
            "record_count": tensor["record_count"],
            "shape": tensor["shape"],
            "vector_label": tensor["vector_label"],
            "embedding_kind": tensor["embedding_kind"],
            "semantic_embedding": tensor["semantic_embedding"],
            "committed_to_git": False,
        }

    report = {
        "schema_version": "0.1.0",
        "stage": "Stage C Orion structural non-semantic vectors",
        "status": "pass",
        "peer_id": PEER_ID,
        "copy_batch_id": batch_id,
        "created_utc": copied_at_utc,
        "source_mapping_report": MAPPING_REPORT,
        "source_mapping_report_sha256": sha256_file(mapping_report_path),
        "working_parameters": {
            "source_live_reach": False,
            "source_write_performed": False,
            "target_records_written": 0,
            "tensor_generation": True,
            "live_population": False,
            "placeholder_data_used": False,
            "mock_data_used": False,
            "demo_data_used": False,
            "semantic_embedding_used": False,
            "structural_non_semantic_vectors": True,
        },
        "label_contract": {
            "vector_label": "structural_vector",
            "embedding_kind": EMBEDDING_KIND,
            "semantic_embedding": False,
            "required_language": "Generated vectors are deterministic structural vectors; embedding_kind=structural-non-semantic.",
        },
        "source_counts": mapping_report["source_counts"],
        "copy_fidelity_gate": mapping_report["copy_fidelity_gate"],
        "stage_b_live_readiness_path_gate": mapping_report["live_readiness_path_gate"],
        "git_boundary": {
            "live_derived_tensor_artifacts_gitignored": True,
            "tensor_output_root": display_path(output_root, root).replace("\\", "/"),
            "committed_artifact": REPORT_PATH,
        },
        "tensors": tensor_summaries,
        "outside_parameters": [],
    }
    report["stage_c_live_readiness_path_gate"] = stage_c_path_gate(report)
    if report["stage_c_live_readiness_path_gate"]["status"] != "pass":
        report["outside_parameters"].append({
            "kind": "stage_c_live_readiness_path_gate_failed",
            "reason": "Stage C evidence references a test-only or unapproved path.",
        })
    report["status"] = "pass" if not report["outside_parameters"] else "review_needed"
    write_json(root / REPORT_PATH, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Stage C Orion structural-non-semantic vector tensors from copied live records.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--batch-id", required=True, help="Verified Orion live-copy batch id")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = build_live_structural_vectors(root, args.batch_id)
    print("PASS Stage C structural-non-semantic vectors built" if report["status"] == "pass" else "FAIL Stage C structural-non-semantic vectors")
    print(f"BATCH {args.batch_id}")
    print("BOUNDARY copied live records only; no Orion writes; no live population; embedding_kind=structural-non-semantic")
    print(f"RECORDS total={report['source_counts']['total_records']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
