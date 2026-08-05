from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURE_CREATED_UTC = "2026-07-20T21:55:00Z"
CLAUDE_REVIEW_UTC = "2026-07-20T21:55:27Z"
CURRENT_STANDARD_HASH = "C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5"
CLAUDE_REVIEW_MESSAGE_HASHES = [
    "853E3461B3E46063A184385B36A1D1009C8741016E669F01F93E8921891B4B62",
    "91C4C59AD97C04F2259F5CA772FEB809F29951A05BE3559F9405242743224722",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def marker_base(target_kind: str, target_id: str, version_identity: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "marker_id": f"{target_kind}:{target_id}:0.1.0",
        "target": {
            "kind": target_kind,
            "id": target_id,
        },
        "version_identity": f"{version_identity}; uncommitted workspace hash identity",
        "standard_hash": CURRENT_STANDARD_HASH,
        "reviews": [
            {
                "reviewer": "codex-local-runtime",
                "timestamp_utc": FIXTURE_CREATED_UTC,
                "result": "no_blocking_objection",
                "notes": "Local fixture verification passed and produced hash-bound evidence.",
                "evidence": {
                    "kind": "builder-local-run",
                    "message_hashes": [],
                },
            },
            {
                "reviewer": "claude-independent-review",
                "timestamp_utc": CLAUDE_REVIEW_UTC,
                "result": "no_blocking_objection",
                "notes": "Independent read/run/hash verification confirmed the provisional marker mechanism, while noting that two reviewers is still below a full redundancy threshold.",
                "evidence": {
                    "kind": "peer-bridge-independent-review",
                    "message_hashes": CLAUDE_REVIEW_MESSAGE_HASHES,
                },
            }
        ],
        "working_parameters": {
            "scope": "local fixture records only",
            "pod_state_effect": "unchanged",
            "outside_parameters_behavior": "report visible condition and leave Pod state unchanged",
        },
        "trust_state": "provisional",
    }


def build_tensor_marker(root: Path) -> dict[str, Any]:
    marker = marker_base("tensor_runtime", "local-deterministic-fixture-tensor-runtime", "step-3-local-fixture-runtime")
    marker["hashes"] = {
        "schema_hash": sha256_file(root / "contracts" / "mathematical-tensor.schema.json"),
        "implementation_hash": sha256_file(root / "src" / "aegis_pod" / "tensor_runtime.py"),
        "demo_hash": sha256_file(root / "reports" / "runtime" / "tensor-health.json"),
        "test_result_hash": sha256_file(root / "reports" / "runtime" / "2026-07-20-step-3-tensor-runtime-evidence.md"),
    }
    marker["verification"] = {
        "commands": [
            {"command": "python scripts\\validate_contracts.py", "result": "pass"},
            {"command": "python -m unittest discover -s tests -v", "result": "pass"},
            {"command": "python -m src.aegis_pod.tensor_runtime --root .", "result": "pass"},
        ],
        "evidence_paths": [
            "reports/runtime/2026-07-20-step-3-tensor-runtime-evidence.md",
            "reports/runtime/tensor-health.json",
            "reports/runtime/tensors/PEER.tensor.json",
            "reports/runtime/tensors/PCT.tensor.json",
            "reports/runtime/tensors/NCT.tensor.json",
            "reports/runtime/tensors/SPINE.tensor.json",
        ],
        "live_reach": False,
    }
    marker["claim_boundary"] = {
        "demonstrates": [
            "Local deterministic numeric tensor computation from fixture tensor records.",
            "Stable shape, dtype, record index, and source-hash sensitivity for fixture records.",
        ],
        "outside_current_verified_surface": [
            "Semantic embedding inference.",
            "Live DataQuad tensorization.",
            "Migration execution.",
        ],
    }
    return marker


def build_orb_marker(root: Path) -> dict[str, Any]:
    marker = marker_base("orb", "rls-orb-fixture", "step-4-local-rls-orb-attachment-runtime")
    marker["hashes"] = {
        "schema_hash": sha256_file(root / "contracts" / "orb.schema.json"),
        "implementation_hash": sha256_file(root / "src" / "aegis_pod" / "orb_runtime.py"),
        "demo_hash": sha256_file(root / "reports" / "runtime" / "orbs" / "rls-orb-fixture.demonstration.json"),
        "test_result_hash": sha256_file(root / "reports" / "runtime" / "2026-07-20-step-4-rls-orb-attachment-evidence.md"),
    }
    marker["verification"] = {
        "commands": [
            {"command": "python scripts\\validate_contracts.py", "result": "pass"},
            {"command": "python -m unittest discover -s tests -v", "result": "pass"},
            {"command": "python -m src.aegis_pod.orb_runtime --root .", "result": "pass"},
        ],
        "evidence_paths": [
            "reports/runtime/2026-07-20-step-4-rls-orb-attachment-evidence.md",
            "reports/runtime/orb-attachment-health.json",
            "reports/runtime/orbs/rls-orb-fixture.demonstration.json",
        ],
        "live_reach": False,
    }
    marker["claim_boundary"] = {
        "demonstrates": [
            "Pod, Orb, and Umbilical cross-reference validation.",
            "Local RLS Orb attachment orchestration and visible demonstration output.",
        ],
        "outside_current_verified_surface": [
            "Reflective-learning logic.",
            "Live CyberPeer runtime attachment.",
            "DataQuad mutation or migration execution.",
        ],
    }
    return marker


def marker_output_path(root: Path, marker: dict[str, Any]) -> Path:
    target = marker["target"]
    target_id = str(target["id"]).replace(":", "-")
    return root / "reports" / "runtime" / "verified-markers" / f"{target['kind']}-{target_id}.verified-code-marker.json"


def run_marker_build(root: Path) -> dict[str, Any]:
    markers = [build_tensor_marker(root), build_orb_marker(root)]
    marker_summaries: list[dict[str, Any]] = []
    for marker in markers:
        path = marker_output_path(root, marker)
        write_json(path, marker)
        marker_summaries.append({
            "marker_id": marker["marker_id"],
            "target": marker["target"],
            "trust_state": marker["trust_state"],
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
        })

    health = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "scope": "local fixture records only",
        "live_reach": False,
        "markers": marker_summaries,
    }
    write_json(root / "reports" / "runtime" / "verified-code-marker-health.json", health)
    return health


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local Verified Code Marker artifacts.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    health = run_marker_build(root)
    print("PASS Verified Code Markers built for local fixture runtimes")
    print(f"ROOT {root}")
    print("BOUNDARY local fixture records only; no live DataQuad roots referenced")
    for marker in health["markers"]:
        print(f"MARKER {marker['marker_id']} state={marker['trust_state']} path={marker['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
