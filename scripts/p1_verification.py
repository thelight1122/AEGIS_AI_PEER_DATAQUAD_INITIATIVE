"""P1 verification pass — Lumin GPT Action Orb.

Establishes that the refitted Action Orb is read and replay only, that the prior write
endpoint is retired rather than merely undocumented, and that every operation reaches the
DataQuad through the Portal Pod with all boundaries false.

Opens no listener and performs no network operation. Serving the Action schema from
lumin.adamone.bond is a separate authorized deployment and is reported as pending.

Usage:
    python scripts/p1_verification.py [--output PATH]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import jsonschema  # noqa: E402

from aegis_pod.lumin_action_orb import (  # noqa: E402
    OPERATION_TO_CAPABILITY,
    OPERATION_TO_SCOPE,
    PROHIBITED_SCOPES,
    RETIRED_OPERATIONS,
    ActionOrbError,
    LuminActionOrb,
)
from aegis_pod.portal_pod.runtime import PortalPod, PortalPodError  # noqa: E402
from aegis_pod.rls_orb import RLSOrb  # noqa: E402

ACTION_CONTRACT = ROOT / "contracts" / "p1-lumin-gpt-action.openapi.json"
RETIRED_PATH = "/api/live-bridge/events"
RETIRED_OPERATION = "appendEvent"

EXPECTED_PATHS = {
    "/api/pod/status",
    "/api/pod/context",
    "/api/pod/canon",
    "/api/pod/continuity",
    "/api/pod/reflection",
}


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_portal() -> tuple[PortalPod, RLSOrb, dict[str, Any]]:
    orb = RLSOrb(ROOT, source_root=ROOT / "fixtures" / "tensor-records")
    orb.build_index()
    pod_contract = load(ROOT / "fixtures" / "p0-portal-pod.json")
    portal = PortalPod(pod_contract)
    portal.register_capability("retrieve_context", lambda p: {"records": orb.coordinates[: int(p.get("limit", 10))]}, required_scope="pod.context.read")
    portal.register_capability("retrieve_canon", lambda p: {"records": []}, required_scope="pod.canon.read")
    portal.register_capability("query_continuity", lambda p: orb.timeline(tensor=p.get("tensor"), t_from=int(p.get("t_from", 0))), required_scope="pod.continuity.observed.read")
    portal.register_capability("request_reflection", lambda p: orb.reflection_packet(tensor=p.get("tensor")), required_scope="pod.reflection.replay")
    portal.register_capability("pod_get_status", lambda p: orb.status(), required_scope="pod.status.read")
    return portal, orb, pod_contract


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record_check(area: str, name: str, passed: bool, detail: Any) -> None:
        checks.append({"area": area, "check": name, "passed": bool(passed), "detail": detail})

    contract = load(ACTION_CONTRACT)
    contract_text = json.dumps(contract)

    # --- The Action schema itself ----------------------------------------------------
    record_check(
        "schema",
        "exposes_exactly_the_five_read_replay_paths",
        set(contract["paths"]) == EXPECTED_PATHS,
        {"declared": sorted(contract["paths"]), "expected": sorted(EXPECTED_PATHS)},
    )

    methods = {path: sorted(spec) for path, spec in contract["paths"].items()}
    record_check(
        "schema",
        "no_path_exposes_put_patch_or_delete",
        all(set(verbs) <= {"get", "post"} for verbs in methods.values()),
        methods,
    )

    # --- Retirement of the write endpoint --------------------------------------------
    record_check(
        "retirement",
        "retired_path_absent_from_paths",
        RETIRED_PATH not in contract["paths"],
        {"retired_path": RETIRED_PATH},
    )

    declared_operations = {spec["operationId"] for verbs in contract["paths"].values() for spec in verbs.values()}
    record_check(
        "retirement",
        "retired_operation_absent_from_operations",
        RETIRED_OPERATION not in declared_operations,
        {"declared_operations": sorted(declared_operations)},
    )

    retired_block = contract.get("x-aegis-retired", {}).get("retired_operations", [])
    record_check(
        "retirement",
        "retirement_is_recorded_not_merely_omitted",
        any(entry["operationId"] == RETIRED_OPERATION and entry["path"] == RETIRED_PATH for entry in retired_block),
        {"retired_block": retired_block},
    )
    record_check(
        "retirement",
        "retired_operation_has_no_replacement",
        all(entry.get("replacement") is None for entry in retired_block),
        "Experience admission is a separate authorized process and is not reachable from an Action Orb.",
    )
    record_check(
        "retirement",
        "prohibited_operations_declared_in_contract",
        RETIRED_OPERATION in contract.get("x-aegis-prohibited-operations", []),
        contract.get("x-aegis-prohibited-operations"),
    )

    # --- Orb manifest and Umbilical ----------------------------------------------------
    orb_manifest = load(ROOT / "fixtures" / "p1-gpt-action-orb.json")
    umbilical = load(ROOT / "fixtures" / "p1-gpt-action-umbilical.json")
    for schema_name, document, label in (
        ("protocol-orb.schema.json", orb_manifest, "action_orb_manifest"),
        ("portal-umbilical.schema.json", umbilical, "action_umbilical"),
    ):
        try:
            jsonschema.validate(document, load(ROOT / "contracts" / schema_name))
            record_check("contract", f"{label}_validates", True, schema_name)
        except jsonschema.ValidationError as exc:
            record_check("contract", f"{label}_validates", False, exc.message)

    record_check(
        "contract",
        "umbilical_carries_no_mutation_admission_or_experience_authority",
        umbilical["mutation_authority"] is False
        and umbilical["admission_authority"] is False
        and umbilical["experience_authority"] is False,
        {k: umbilical[k] for k in ("mutation_authority", "admission_authority", "experience_authority")},
    )
    record_check(
        "contract",
        "action_orb_starts_disabled",
        orb_manifest["enabled"] is False,
        {"enabled": orb_manifest["enabled"]},
    )

    # --- Operation mapping -------------------------------------------------------------
    contract_scopes = contract["x-aegis-operation-scopes"]
    record_check(
        "mapping",
        "runtime_operations_match_the_published_schema",
        set(OPERATION_TO_CAPABILITY) == declared_operations,
        {"runtime": sorted(OPERATION_TO_CAPABILITY), "schema": sorted(declared_operations)},
    )
    record_check(
        "mapping",
        "runtime_scopes_match_the_published_schema",
        OPERATION_TO_SCOPE == contract_scopes,
        {"runtime": OPERATION_TO_SCOPE, "schema": contract_scopes},
    )
    record_check(
        "mapping",
        "no_operation_maps_to_a_prohibited_scope",
        not (set(OPERATION_TO_SCOPE.values()) & PROHIBITED_SCOPES),
        {"mapped_scopes": sorted(set(OPERATION_TO_SCOPE.values())), "prohibited": sorted(PROHIBITED_SCOPES)},
    )
    record_check(
        "mapping",
        "every_umbilical_scope_is_reachable_and_no_others",
        set(OPERATION_TO_SCOPE.values()) == set(umbilical["allowed_scopes"]),
        {"reachable": sorted(set(OPERATION_TO_SCOPE.values())), "umbilical": sorted(umbilical["allowed_scopes"])},
    )

    # --- Live behaviour through the Portal Pod ----------------------------------------
    portal, orb, pod_contract = build_portal()
    action = LuminActionOrb(portal)
    attachment = portal.attach(orb_manifest, umbilical)
    record_check("runtime", "attach_starts_disabled", attachment["attached"] is False, attachment["attached"])
    portal.enable(orb_manifest["orb_id"])

    results: dict[str, Any] = {}
    for operation in sorted(OPERATION_TO_CAPABILITY):
        payload = {"limit": 2} if operation in {"retrieveContext", "retrieveCanon"} else {}
        dispatch = action.call(operation, payload)
        results[operation] = {
            "boundaries": dispatch["boundaries"],
            "result_hash": canonical_hash(dispatch["result"]),
        }
    record_check(
        "runtime",
        "every_operation_dispatches_with_all_boundaries_false",
        all(all(value is False for value in item["boundaries"].values()) for item in results.values()),
        {operation: item["boundaries"] for operation, item in results.items()},
    )
    record_check(
        "runtime",
        "operation_results_are_deterministic",
        all(canonical_hash(action.call(operation, {"limit": 2} if operation in {"retrieveContext", "retrieveCanon"} else {})["result"]) == results[operation]["result_hash"] for operation in sorted(OPERATION_TO_CAPABILITY)),
        {operation: item["result_hash"] for operation, item in results.items()},
    )

    # --- Refusals ----------------------------------------------------------------------
    try:
        action.call(RETIRED_OPERATION, {"event": "anything"})
        record_check("refusal", "retired_operation_is_refused_at_runtime", False, "call succeeded")
    except ActionOrbError as exc:
        record_check("refusal", "retired_operation_is_refused_at_runtime", True, str(exc))

    try:
        action.call("recordExperience", {})
        record_check("refusal", "unknown_operation_is_refused", False, "call succeeded")
    except ActionOrbError as exc:
        record_check("refusal", "unknown_operation_is_refused", True, str(exc))

    # A caller cannot smuggle a write scope through: the Orb presents only its own scope.
    try:
        portal.dispatch(
            {
                "caller": "lumin-gpt",
                "orb_id": orb_manifest["orb_id"],
                "capability": "record_experience",
                "parameters": {},
                "authority": {"scopes": ["pod.experience.write"]},
            }
        )
        record_check("refusal", "write_capability_refused_through_action_orb", False, "dispatch succeeded")
    except PortalPodError as exc:
        record_check("refusal", "write_capability_refused_through_action_orb", True, str(exc))

    record_check(
        "refusal",
        "pod_contract_keeps_record_experience_disabled",
        any(entry["name"] == "record_experience" and entry["enabled"] is False for entry in pod_contract["capability_orbs"]),
        [entry for entry in pod_contract["capability_orbs"] if entry["name"] == "record_experience"],
    )

    # --- Boundary declarations ----------------------------------------------------------
    boundary = contract["x-aegis-boundary"]
    record_check(
        "boundary",
        "contract_declares_every_boundary_false",
        all(value is False for value in boundary.values()),
        boundary,
    )
    record_check(
        "boundary",
        "contract_text_contains_no_write_verb_operation",
        "appendEvent" not in {op for op in declared_operations} and "live-bridge" not in json.dumps(contract["paths"]),
        {"scanned": "paths and operationIds"},
    )

    passed = sum(1 for check in checks if check["passed"])
    report = {
        "schema_version": "1.0.0",
        "verification_id": "p1-lumin-gpt-action-orb",
        "action_contract": str(ACTION_CONTRACT.relative_to(ROOT)),
        "action_contract_sha256": canonical_hash(contract),
        "target_origin": contract["servers"][0]["url"],
        "operations": OPERATION_TO_CAPABILITY,
        "operation_scopes": OPERATION_TO_SCOPE,
        "retired_operations": {name: dict(detail) for name, detail in RETIRED_OPERATIONS.items()},
        "operation_result_hashes": {operation: item["result_hash"] for operation, item in results.items()},
        "checks": checks,
        "summary": {"checks_run": len(checks), "passed": passed, "failed": len(checks) - passed},
        "deployment_pending": {
            "target": contract["servers"][0]["url"],
            "status": "NOT DEPLOYED",
            "note": "This pass verifies the contract and runtime locally. Publishing the Action schema to the live origin, and removing the prior bridge write endpoint from that origin, is a separate authorized deployment. Nothing in this run reached the network.",
        },
        "working_parameters": {
            "listener_opened": False,
            "network_reached": False,
            "authoritative_tensor_write": False,
            "admission": False,
            "experience_creation": False,
            "live_rls_invoked": False,
        },
    }
    report["report_sha256"] = canonical_hash({k: v for k, v in report.items() if k != "report_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "p1-verification.json")
    args = parser.parse_args()

    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = report["summary"]
    print(f"P1 verification  {summary['passed']}/{summary['checks_run']} checks passed")
    for check in report["checks"]:
        if not check["passed"]:
            print(f"  FAILED  [{check['area']}] {check['check']}: {check['detail']}")
    print()
    print(f"operations exposed   {', '.join(sorted(report['operations']))}")
    print(f"retired              {', '.join(report['retired_operations'])} (no replacement)")
    print(f"deployment           {report['deployment_pending']['status']} -> {report['deployment_pending']['target']}")
    print(f"report               {args.output}")
    print("BOUNDARY contract and local runtime only; no listener opened, no network reached")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
