"""R1 verification pass — RLS Orb Formation.

Checks the ten R1 items in SSSP section 15 against what is implemented, exercises the RLS
Orb end to end over controlled fixtures, writes deterministic derived-ledger records to
`rls/derived-ledgers/`, and proves no authoritative tensor was mutated by hashing all four
tensors before and after every operation.

Derived-ledger writes are not tensor writes. They are append-only structural observations
that reference Tensor Coordinates.

Usage:
    python scripts/r1_verification.py [--output PATH] [--ledger-dir PATH]
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

from aegis_pod.portal_pod.runtime import NormalizedInvocation, PortalPod  # noqa: E402
from aegis_pod.rls_orb import RLSOrb  # noqa: E402
from aegis_pod.rls_trajectories import (  # noqa: E402
    AFFECTIVE_DIMENSION,
    affect_trajectory,
    build_coordinate_provenance,
    build_dimension_provenance,
    canonical_hash,
    context_trajectory,
    recurrence_observations,
)

TENSORS = ("PEER", "PCT", "NCT", "SPINE")
SOURCE_ROOT = ROOT / "fixtures" / "tensor-records"
LEDGER_DIR_DEFAULT = ROOT / "rls" / "derived-ledgers"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tensor_hashes() -> dict[str, str]:
    return {tensor: file_hash(SOURCE_ROOT / f"{tensor}.jsonl") for tensor in TENSORS}


def load_contract(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))


def append_ledger(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def run(ledger_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record_check(item: str, name: str, passed: bool, detail: Any) -> None:
        checks.append({"item": item, "check": name, "passed": bool(passed), "detail": detail})

    # Tensor state before anything runs. R1.10 depends on this.
    before = tensor_hashes()

    # R1.1 / R1.2 — RLS Orb manifest and Umbilical contract exist and validate.
    orb_manifest = json.loads((ROOT / "fixtures" / "r0-rls-capability-orb.json").read_text(encoding="utf-8"))
    umbilical = json.loads((ROOT / "fixtures" / "r0-rls-umbilical.json").read_text(encoding="utf-8"))
    for schema_name, document, item, label in (
        ("capability-orb.schema.json", orb_manifest, "R1.1", "rls_orb_manifest"),
        ("portal-umbilical.schema.json", umbilical, "R1.2", "rls_umbilical_contract"),
    ):
        try:
            jsonschema.validate(document, load_contract(schema_name))
            record_check(item, f"{label}_validates", True, schema_name)
        except jsonschema.ValidationError as exc:
            record_check(item, f"{label}_validates", False, exc.message)

    # R1.3 — Tensor Coordinate schema, exercised by the Orb's own output.
    orb = RLSOrb(ROOT, source_root=SOURCE_ROOT)
    status = orb.build_index()
    coordinate_schema = load_contract("tensor-coordinate.schema.json")
    coordinate_failures = []
    for coordinate in orb.coordinates:
        try:
            jsonschema.validate(coordinate, coordinate_schema)
        except jsonschema.ValidationError as exc:
            coordinate_failures.append({"record_id": coordinate.get("record_id"), "error": exc.message})
    record_check(
        "R1.3",
        "every_emitted_coordinate_validates",
        not coordinate_failures,
        {"coordinates": len(orb.coordinates), "failures": coordinate_failures[:3]},
    )
    record_check(
        "R1.3",
        "coordinates_carry_no_filesystem_path",
        "source_path" not in json.dumps(orb.coordinates),
        "Tensor Coordinates are canonical; filesystem paths are implementation details.",
    )

    # R1.4 — coordinate provenance schema, including the SSSP section 8 rule.
    provenance_schema = load_contract("coordinate-provenance.schema.json")
    sample = orb.coordinates[0]
    dimensions = [
        build_dimension_provenance(
            dimension=0,
            value=sample["affective_coordinate"]["values"][0],
            origin="source-derived",
            source_field="clock.tick",
        )
    ] + [
        build_dimension_provenance(
            dimension=index,
            value=sample["affective_coordinate"]["values"][index],
            origin="tensorization-policy-assigned",
            policy="r1-fixture-affect-policy",
            policy_version="v1",
        )
        for index in range(1, AFFECTIVE_DIMENSION)
    ]
    provenance = build_coordinate_provenance(
        tensor=sample["tensor"],
        record_id=sample["record_id"],
        record_hash=sample["record_hash"],
        tensor_snapshot_hash=sample["tensor_snapshot_hash"],
        dimensions=dimensions,
        locator={"kind": "filesystem", "value": "fixtures/tensor-records/PEER.jsonl", "observed_utc": "2026-08-06T00:00:00Z", "digest_confirmed": False},
    )
    try:
        jsonschema.validate(provenance, provenance_schema)
        record_check("R1.4", "coordinate_provenance_validates", True, {"dimensions": len(provenance["dimensions"])})
    except jsonschema.ValidationError as exc:
        record_check("R1.4", "coordinate_provenance_validates", False, exc.message)

    record_check(
        "R1.4",
        "only_source_derived_dimensions_assert_source_fact",
        all(
            entry["asserted_as_source_fact"] is (entry["origin"] == "source-derived")
            for entry in provenance["dimensions"]
        ),
        {entry["name"]: {"origin": entry["origin"], "asserted_as_source_fact": entry["asserted_as_source_fact"]} for entry in provenance["dimensions"]},
    )

    # The schema, not just the builder, refuses a policy-assigned dimension claimed as fact.
    forged = json.loads(json.dumps(provenance))
    forged["dimensions"][1]["asserted_as_source_fact"] = True
    try:
        jsonschema.validate(forged, provenance_schema)
        record_check("R1.4", "schema_rejects_policy_assigned_claimed_as_source_fact", False, "schema accepted a forged source-fact claim")
    except jsonschema.ValidationError:
        record_check("R1.4", "schema_rejects_policy_assigned_claimed_as_source_fact", True, "rejected as required by SSSP section 8")

    record_check(
        "R1.4",
        "locator_is_separable_from_identity",
        "locator" in provenance and "value" not in provenance["coordinate_ref"],
        "ADR-0006: Coordinate is identity, Digest is integrity, Path is a replaceable locator.",
    )

    # R1.6 / R1.7 — temporal and cross-tensor indexes.
    timeline = orb.timeline()
    ticks = [item["t_time"] for item in timeline["coordinates"]]
    record_check("R1.6", "temporal_index_is_monotonic", ticks == sorted(ticks), {"coordinates": len(ticks), "tick_range": [ticks[0], ticks[-1]] if ticks else None})
    lineage = [orb.cross_tensor_lineage(item["record_id"]) for item in orb.coordinates]
    record_check(
        "R1.7",
        "cross_tensor_index_reports_explicit_lineage_only",
        all(entry["relation_basis"] in {"explicit_lineage_only", "no_record"} for entry in lineage),
        {"records": len(lineage), "with_relations": sum(1 for entry in lineage if entry["relations"])},
    )

    # R1.8 — deterministic trajectory records.
    affect = affect_trajectory(orb.coordinates)
    affect_repeat = affect_trajectory(orb.coordinates)
    context = context_trajectory(orb.coordinates)
    recurrence = recurrence_observations(orb.coordinates)
    record_check(
        "R1.8",
        "affect_trajectory_is_deterministic",
        affect["derived_record_sha256"] == affect_repeat["derived_record_sha256"],
        {"sha256": affect["derived_record_sha256"], "steps": len(affect["steps"])},
    )
    record_check("R1.8", "context_trajectory_produced", bool(context["segments"]), {"tensors": context["tensors_observed"]})

    # A recurrence detector run over coordinates that contain no recurrence proves nothing.
    # Exercise the detector against a planted control before reporting on real coordinates.
    planted_signature = [0.5, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    planted = [
        dict(sample, record_id="CONTROL:a", tensor="PEER", ordinal=0, t_time=1, affective_coordinate={"values": list(planted_signature), "provenance": ["source-derived"] * AFFECTIVE_DIMENSION}),
        dict(sample, record_id="CONTROL:b", tensor="PEER", ordinal=1, t_time=2, affective_coordinate={"values": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "provenance": ["source-derived"] * AFFECTIVE_DIMENSION}),
        dict(sample, record_id="CONTROL:c", tensor="PEER", ordinal=2, t_time=3, affective_coordinate={"values": list(planted_signature), "provenance": ["source-derived"] * AFFECTIVE_DIMENSION}),
    ]
    control = recurrence_observations(planted)
    record_check(
        "R1.8",
        "recurrence_detector_finds_a_planted_recurrence",
        len(control["recurrences"]) == 1 and control["recurrences"][0]["occurrence_count"] == 2,
        {"planted_recurrences_found": len(control["recurrences"]), "control_only": True},
    )
    record_check(
        "R1.8",
        "trajectories_declare_no_inference_as_source_fact",
        all(rec["provenance"]["inference_converted_to_source_fact"] is False for rec in (affect, context, recurrence)),
        "SSSP section 9.2: the RLS Orb does not silently convert inference into source fact.",
    )

    # R1.5 — dedicated derived ledgers, append-only, referencing coordinates.
    ledger_path = ledger_dir / "rls-derived-observations.jsonl"
    for derived in (affect, context, recurrence):
        append_ledger(ledger_path, derived)
    ledger_text = ledger_path.read_text(encoding="utf-8")
    record_check(
        "R1.5",
        "derived_ledger_written_and_coordinate_referenced",
        ledger_path.exists() and "record_hash" in ledger_text,
        {"ledger": str(ledger_path.relative_to(ROOT)), "lines": len(ledger_text.strip().splitlines())},
    )
    record_check(
        "R1.5",
        "derived_ledger_embeds_no_filesystem_path",
        "source_path" not in ledger_text,
        "RLS ledgers point to Tensor Coordinates, not filesystem locations.",
    )

    # R1.9 — attach the RLS Orb to the Portal Pod and dispatch through it.
    pod = json.loads((ROOT / "fixtures" / "p0-portal-pod.json").read_text(encoding="utf-8"))
    portal = PortalPod(pod)
    portal.register_capability(
        "query_continuity",
        lambda params: orb.timeline(tensor=params.get("tensor"), t_from=int(params.get("t_from", 0))),
        required_scope="pod.continuity.observed.read",
    )
    protocol_orb = json.loads((ROOT / "fixtures" / "p0-mcp-protocol-orb.json").read_text(encoding="utf-8"))
    protocol_umbilical = json.loads((ROOT / "fixtures" / "p0-mcp-umbilical.json").read_text(encoding="utf-8"))
    attachment = portal.attach(protocol_orb, protocol_umbilical)
    portal.enable(protocol_orb["orb_id"])
    dispatch = portal.dispatch(
        NormalizedInvocation.from_dict(
            {
                "caller": "r1-verification",
                "orb_id": protocol_orb["orb_id"],
                "capability": "query_continuity",
                "parameters": {"t_from": 0},
                "authority": {"scopes": ["pod.continuity.observed.read"]},
                "session_id": "r1-verification",
            }
        )
    )
    record_check(
        "R1.9",
        "rls_orb_reachable_through_portal_pod",
        bool(dispatch["result"]["coordinates"]),
        {"attached_disabled_first": attachment["attached"] is False, "coordinates_returned": len(dispatch["result"]["coordinates"])},
    )
    record_check(
        "R1.9",
        "portal_dispatch_reports_all_boundaries_false",
        all(value is False for value in dispatch["boundaries"].values()),
        dispatch["boundaries"],
    )

    # R1.10 — prove no tensor mutation across everything above.
    after = tensor_hashes()
    unchanged = before == after
    record_check(
        "R1.10",
        "no_authoritative_tensor_mutated",
        unchanged,
        {"before": before, "after": after, "identical": unchanged},
    )
    record_check(
        "R1.10",
        "orb_status_declares_no_tensor_writeback",
        status["writes"]["authoritative_tensors"] is False
        and status["experience_created"] is False
        and status["admission_performed"] is False,
        status["writes"] | {"experience_created": status["experience_created"], "admission_performed": status["admission_performed"]},
    )

    passed = sum(1 for check in checks if check["passed"])
    report = {
        "schema_version": "1.0.0",
        "verification_id": "r1-rls-orb-formation",
        "orb_status": status,
        "tensor_hashes_before": before,
        "tensor_hashes_after": after,
        "tensors_unchanged": unchanged,
        "derived_ledger": str(ledger_path.relative_to(ROOT)),
        "derived_record_hashes": {
            "affect_trajectory": affect["derived_record_sha256"],
            "context_trajectory": context["derived_record_sha256"],
            "recurrence_observation": recurrence["derived_record_sha256"],
        },
        "checks": checks,
        "summary": {"checks_run": len(checks), "passed": passed, "failed": len(checks) - passed},
        "coverage": {
            "note": "A passing check states the code behaved correctly on what it was given. This block states what the fixture set actually contained, so coverage is not overstated by a green summary.",
            "coordinates_indexed": len(orb.coordinates),
            "tensors_represented": sorted({item["tensor"] for item in orb.coordinates}),
            "recurrences_present_in_real_coordinates": len(recurrence["recurrences"]),
            "recurrence_exercised_by_real_coordinates": bool(recurrence["recurrences"]),
            "recurrence_exercised_by_planted_control": True,
            "cross_tensor_relations_found": sum(1 for entry in lineage if entry["relations"]),
            "cross_tensor_lineage_exercised": any(entry["relations"] for entry in lineage),
            "limitation": "The controlled fixture set is small. Where a detector was not exercised by real coordinates, it was exercised by a planted control and that is stated rather than implied.",
        },
        "working_parameters": {
            "authoritative_tensor_write": False,
            "derived_ledger_append": True,
            "admission": False,
            "experience_creation": False,
            "live_rls_model_loop": False,
            "listener_opened": False,
            "peer_content_read": False,
        },
    }
    report["report_sha256"] = canonical_hash({k: v for k, v in report.items() if k != "report_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "r1-verification.json")
    parser.add_argument("--ledger-dir", type=Path, default=LEDGER_DIR_DEFAULT)
    args = parser.parse_args()

    report = run(args.ledger_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = report["summary"]
    print(f"R1 verification  {summary['passed']}/{summary['checks_run']} checks passed")
    for check in report["checks"]:
        if not check["passed"]:
            print(f"  FAILED  [{check['item']}] {check['check']}: {check['detail']}")
    print()
    print(f"coordinates indexed      {report['orb_status']['record_count']}")
    print(f"authoritative tensors    {'UNCHANGED' if report['tensors_unchanged'] else 'MUTATED'}")
    print(f"derived ledger           {report['derived_ledger']}")
    print(f"report                   {args.output}")
    print("BOUNDARY controlled fixtures only; derived-ledger append is not a tensor write")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
