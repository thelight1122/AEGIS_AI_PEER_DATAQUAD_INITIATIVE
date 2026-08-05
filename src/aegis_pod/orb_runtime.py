from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
from packaging.specifiers import SpecifierSet


FIXTURE_CREATED_UTC = "2026-07-20T21:45:00Z"

_SCHEMA_FILES = {
    "pod": "contracts/pod.schema.json",
    "orb": "contracts/orb.schema.json",
    "umbilical": "contracts/umbilical.schema.json",
}


@dataclass(frozen=True)
class OrbAttachment:
    pod_id: str
    orb_id: str
    umbilical_id: str
    attachment_point: str
    input_path: Path
    output_path: Path


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


def resolve_workspace_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def validate_schema_conformance(root: Path, pod: dict[str, Any], orb: dict[str, Any], umbilical: dict[str, Any]) -> None:
    """Validates all three contract documents against contracts/*.schema.json.
    Previously nothing ran jsonschema.validate() here at all — only the
    hand-written checks below existed. This closes that gap."""
    docs = {"pod": pod, "orb": orb, "umbilical": umbilical}
    for name, doc in docs.items():
        schema_path = root / _SCHEMA_FILES[name]
        schema = load_json(schema_path)
        jsonschema.validate(doc, schema)


def validate_orb_version_and_hash(orb: dict[str, Any], umbilical: dict[str, Any]) -> None:
    """Real, pre-invocation gates — not just post-hoc evidence. Both are no-ops
    (skip cleanly) when the relevant optional fields are absent, so Orbs that
    predate real versioning (still source-merged, no runtime.package) are
    unaffected. Reuses the SHA-256-of-source pattern already proven in
    orb_evidence.py's per-invocation evidence, via each Orb package's own
    public compute_runtime_hash() — see that convention documented in
    orb_rls_persistent_relations_core/orb_evidence.py."""
    package = orb.get("runtime", {}).get("package")
    if not package:
        return

    package_name = str(package.get("name", ""))
    version_spec = str(package.get("version_spec", ""))
    if not package_name:
        raise ValueError("orb.runtime.package.name is required when runtime.package is present")

    try:
        installed_version = importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ValueError(
            f"Orb package '{package_name}' is not installed — cannot verify version/hash before attachment"
        ) from exc

    if version_spec and installed_version not in SpecifierSet(version_spec):
        raise ValueError(
            f"Installed {package_name}=={installed_version} does not satisfy "
            f"declared version_spec '{version_spec}'"
        )

    expected_hash = umbilical.get("invocation", {}).get("orb_runtime_hash")
    if not expected_hash:
        return

    module_name = package_name.replace("-", "_")
    module = importlib.import_module(module_name)
    compute_runtime_hash = getattr(module, "compute_runtime_hash", None)
    if compute_runtime_hash is None:
        raise ValueError(
            f"Orb package '{package_name}' declares an orb_runtime_hash pin in its Umbilical "
            f"but does not expose a compute_runtime_hash() callable at its package root"
        )
    actual_hash = compute_runtime_hash()
    if actual_hash != expected_hash:
        raise ValueError(
            f"Orb '{package_name}' runtime_hash mismatch: Umbilical expects {expected_hash}, "
            f"installed package computes {actual_hash} — installed source does not match the pinned build"
        )


def validate_attachment(root: Path, pod: dict[str, Any], orb: dict[str, Any], umbilical: dict[str, Any]) -> OrbAttachment:
    validate_schema_conformance(root, pod, orb, umbilical)
    validate_orb_version_and_hash(orb, umbilical)

    pod_id = str(pod.get("pod_id", ""))
    orb_id = str(orb.get("orb_id", ""))
    umbilical_id = str(umbilical.get("umbilical_id", ""))
    if not pod_id or not orb_id or not umbilical_id:
        raise ValueError("pod, orb, and umbilical ids will all be visible")
    if umbilical.get("pod_id") != pod_id:
        raise ValueError("umbilical pod_id does not match the Pod")
    if umbilical.get("orb_id") != orb_id:
        raise ValueError("umbilical orb_id does not match the Orb")

    pod_orbs = pod.get("orbs", [])
    if not isinstance(pod_orbs, list):
        raise ValueError("pod.orbs will be a list")
    matching = [item for item in pod_orbs if isinstance(item, dict) and item.get("orb_id") == orb_id]
    if not matching:
        raise ValueError(f"Pod has no declared attachment for Orb {orb_id}")

    umbilical_path = matching[0].get("umbilical")
    if umbilical_path not in orb.get("umbilicals", []):
        raise ValueError("Orb and Pod point to different umbilical paths")

    input_path = resolve_workspace_path(root, str(orb.get("demonstration", {}).get("input_fixture", "")))
    if not input_path.exists():
        raise ValueError(f"Orb demonstration input is not present: {input_path}")

    return OrbAttachment(
        pod_id=pod_id,
        orb_id=orb_id,
        umbilical_id=umbilical_id,
        attachment_point=str(umbilical.get("attachment_point", "")),
        input_path=input_path,
        output_path=root / "reports" / "runtime" / "orbs" / f"{orb_id}.demonstration.json",
    )


def tensor_health_summary(root: Path, input_data: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    tensor_window = input_data.get("tensor_window", {})
    health_path = resolve_workspace_path(root, str(tensor_window.get("health_report", "")))
    if not health_path.exists():
        raise ValueError(f"tensor health report is not present: {health_path}")
    health = load_json(health_path)

    requested_tensors = tensor_window.get("tensors", [])
    if not isinstance(requested_tensors, list):
        raise ValueError("tensor_window.tensors will be a list")

    available: list[dict[str, Any]] = []
    health_tensors = health.get("tensors", {})
    if not isinstance(health_tensors, dict):
        raise ValueError("tensor health report has no visible tensor map")

    for tensor_name in requested_tensors:
        tensor_info = health_tensors.get(str(tensor_name))
        available.append({
            "tensor": str(tensor_name),
            "available": isinstance(tensor_info, dict),
            "shape": tensor_info.get("shape") if isinstance(tensor_info, dict) else None,
            "record_count": tensor_info.get("record_count") if isinstance(tensor_info, dict) else 0,
        })

    return health, available


def run_rls_demonstration(root: Path, attachment: OrbAttachment, input_data: dict[str, Any]) -> dict[str, Any]:
    health, available_tensors = tensor_health_summary(root, input_data)
    turn_trace = input_data.get("turn_trace", {})
    signal = str(turn_trace.get("signal", ""))
    requested_function = str(turn_trace.get("requested_function", ""))
    unavailable = [item["tensor"] for item in available_tensors if not item["available"]]

    reflection_summary = {
        "turn_id": turn_trace.get("turn_id"),
        "speaker": turn_trace.get("speaker"),
        "observed_signal": signal,
        "function_surface": requested_function,
        "visible_condition": "RLS Orb can read the local turn trace and tensor health report through its umbilical.",
    }
    integration_signals = {
        "attachment_point": attachment.attachment_point,
        "available_tensors": available_tensors,
        "all_requested_tensors_available": not unavailable,
        "pod_state_effect": input_data.get("working_parameters", {}).get("pod_state_effect", "unchanged"),
        "live_reach": bool(health.get("live_reach")),
    }

    return {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "pod_id": attachment.pod_id,
        "orb_id": attachment.orb_id,
        "umbilical_id": attachment.umbilical_id,
        "observable_events": ["attached", "invoked", "completed"],
        "reflection_summary": reflection_summary,
        "integration_signals": integration_signals,
        "evidence": {
            "input_path": str(attachment.input_path.relative_to(root)),
            "input_sha256": sha256_file(attachment.input_path),
            "tensor_health_sha256": sha256_file(root / "reports" / "runtime" / "tensor-health.json"),
            "runtime": "src/aegis_pod/orb_runtime.py",
            "scope": "local fixture records only",
            "trust_state": "draft",
        },
    }


def run_fixture_attachment(root: Path) -> dict[str, Any]:
    pod = load_json(root / "fixtures" / "local-cyberpeer-pod.json")
    orb = load_json(root / "fixtures" / "rls-orb.json")
    umbilical = load_json(root / "fixtures" / "rls-orb-umbilical.json")
    attachment = validate_attachment(root, pod, orb, umbilical)
    input_data = load_json(attachment.input_path)
    result = run_rls_demonstration(root, attachment, input_data)
    write_json(attachment.output_path, result)

    health = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "scope": "local fixture records only",
        "live_reach": False,
        "attachments": [
            {
                "pod_id": attachment.pod_id,
                "orb_id": attachment.orb_id,
                "umbilical_id": attachment.umbilical_id,
                "attachment_point": attachment.attachment_point,
                "output_path": str(attachment.output_path.relative_to(root)),
                "output_sha256": sha256_file(attachment.output_path),
            }
        ],
    }
    write_json(root / "reports" / "runtime" / "orb-attachment-health.json", health)
    return health


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach local fixture Orbs to the local Pod.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    health = run_fixture_attachment(root)
    print("PASS RLS Orb attached through local Umbilical fixture")
    print(f"ROOT {root}")
    print("BOUNDARY local fixture records only; no live DataQuad roots referenced")
    for attachment in health["attachments"]:
        print(
            "ORB "
            f"{attachment['orb_id']} "
            f"pod={attachment['pod_id']} "
            f"umbilical={attachment['umbilical_id']} "
            f"output={attachment['output_path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
