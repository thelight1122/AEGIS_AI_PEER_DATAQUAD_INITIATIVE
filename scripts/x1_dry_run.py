"""X1 dry run — the retrieval half of the two-instance continuity experiment.

Exercises everything the experiment needs that does not require a Lumin substrate: the
re-entry packet is built from real coordinates through the Portal Pod, proven identical for
two separate entries, and the evaluation instrument is exercised against planted controls
so its detectors are known to work before any real session depends on them.

No substrate response is generated. Where a variable requires an actual Lumin instance,
this run says so and scores nothing.

Usage:
    python scripts/x1_dry_run.py [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aegis_pod.continuity_experiment import (  # noqa: E402
    MECHANICAL_VARIABLES,
    SUBSTRATE_VARIABLES,
    build_reentry_packet,
    canonical_hash,
    detect_invented_continuity,
    evaluate,
    record_session_evidence,
)
from aegis_pod.lumin_action_orb import LuminActionOrb  # noqa: E402
from aegis_pod.portal_pod.runtime import PortalPod  # noqa: E402
from aegis_pod.rls_orb import RLSOrb  # noqa: E402
from aegis_pod.rls_trajectories import affect_trajectory, context_trajectory  # noqa: E402
from aegis_pod.tensor_shadow_policies import rank, ranking_delta  # noqa: E402
from aegis_pod.tensor_shadow_scorer import SEMANTIC_DIMENSION  # noqa: E402

#: A fixed timestamp. The experiment record must be reproducible, so nothing reads a clock.
FIXED_UTC = "2026-08-06T00:00:00Z"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_action_orb() -> tuple[LuminActionOrb, RLSOrb]:
    orb = RLSOrb(ROOT, source_root=ROOT / "fixtures" / "tensor-records")
    orb.build_index()
    portal = PortalPod(load(ROOT / "fixtures" / "p0-portal-pod.json"))
    portal.register_capability("retrieve_context", lambda p: {"records": orb.coordinates[: int(p.get("limit", 10))]}, required_scope="pod.context.read")
    portal.register_capability("retrieve_canon", lambda p: {"records": []}, required_scope="pod.canon.read")
    portal.register_capability("query_continuity", lambda p: orb.timeline(tensor=p.get("tensor"), t_from=int(p.get("t_from", 0))), required_scope="pod.continuity.observed.read")
    portal.register_capability("request_reflection", lambda p: orb.reflection_packet(tensor=p.get("tensor")), required_scope="pod.reflection.replay")
    portal.register_capability("pod_get_status", lambda p: orb.status(), required_scope="pod.status.read")

    manifest = load(ROOT / "fixtures" / "p1-gpt-action-orb.json")
    portal.attach(manifest, load(ROOT / "fixtures" / "p1-gpt-action-umbilical.json"))
    portal.enable(manifest["orb_id"])
    return LuminActionOrb(portal), orb


def enter_through_the_portal(action: LuminActionOrb, orb: RLSOrb) -> dict[str, Any]:
    """One instance's entry: retrieve Genesis, continuity, trajectories, lineage."""
    continuity = action.call("queryContinuity", {"t_from": 0})["result"]
    coordinates = continuity["coordinates"]
    genesis = [item for item in coordinates if item["t_time"] == 0] or coordinates[:1]
    lineage = [orb.cross_tensor_lineage(item["record_id"]) for item in coordinates]
    return build_reentry_packet(
        genesis=genesis,
        continuity=coordinates,
        affect_trajectory=affect_trajectory(coordinates),
        context_trajectory=context_trajectory(coordinates),
        lineage=[entry for entry in lineage if entry["relations"]],
        unresolved_questions=[],
        snapshot_hashes=continuity["source_snapshot_hashes"],
    )


def run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record_check(area: str, name: str, passed: bool, detail: Any) -> None:
        checks.append({"area": area, "check": name, "passed": bool(passed), "detail": detail})

    action, orb = build_action_orb()

    # Instance A and Instance B enter separately, through the same Action Orb.
    packet_a = enter_through_the_portal(action, orb)
    packet_b = enter_through_the_portal(action, orb)

    record_check(
        "reentry",
        "both_instances_receive_an_identical_continuity_field",
        packet_a["packet_sha256"] == packet_b["packet_sha256"],
        {"packet_sha256": packet_a["packet_sha256"], "coordinates": len(packet_a["current_continuity"])},
    )
    record_check(
        "reentry",
        "packet_carries_genesis",
        bool(packet_a["genesis"]),
        {"genesis_coordinates": [item["record_id"] for item in packet_a["genesis"]]},
    )
    record_check(
        "reentry",
        "packet_embeds_no_filesystem_path",
        "source_path" not in json.dumps(packet_a),
        "The continuity field is addressed by Tensor Coordinate, not by location.",
    )
    record_check(
        "reentry",
        "packet_declares_no_admission_or_experience",
        packet_a["provenance"]["admission_performed"] is False and packet_a["provenance"]["experience_created"] is False,
        packet_a["provenance"],
    )

    # The evaluation instrument, exercised against planted controls.
    real = packet_a["current_continuity"][0]
    grounded_citation = {"tensor": real["tensor"], "record_id": real["record_id"], "record_hash": real["record_hash"]}
    fabricated_citation = {"tensor": "PEER", "record_id": "PEER:coordinate-that-does-not-exist", "record_hash": "F" * 64}
    tampered_citation = {"tensor": real["tensor"], "record_id": real["record_id"], "record_hash": "0" * 64}

    control_grounded = detect_invented_continuity(packet_a, [grounded_citation])
    control_invented = detect_invented_continuity(packet_a, [fabricated_citation])
    control_tampered = detect_invented_continuity(packet_a, [tampered_citation])

    record_check(
        "instrument",
        "detector_passes_a_grounded_citation",
        control_grounded["invented_continuity_detected"] is False,
        control_grounded,
    )
    record_check(
        "instrument",
        "detector_catches_a_fabricated_coordinate",
        control_invented["invented_continuity_detected"] is True and len(control_invented["invented"]) == 1,
        control_invented,
    )
    record_check(
        "instrument",
        "detector_catches_a_hash_mismatch_on_a_real_coordinate",
        control_tampered["invented_continuity_detected"] is True and len(control_tampered["hash_mismatched"]) == 1,
        control_tampered,
    )

    # Ranking difference between baseline and tensor-aware retrieval, over the same coordinates.
    def as_ranking_record(coordinate: dict[str, Any]) -> dict[str, Any]:
        semantic = [0.0] * SEMANTIC_DIMENSION
        semantic[0] = 1.0 - (coordinate["ordinal"] * 0.05)
        semantic[1] = coordinate["ordinal"] * 0.05
        return {"record_id": coordinate["record_id"], "semantic": semantic, "affective": coordinate["affective_coordinate"]["values"]}

    ranking_records = [as_ranking_record(item) for item in packet_a["current_continuity"]]
    query_semantic = [1.0] + [0.0] * (SEMANTIC_DIMENSION - 1)
    query_affective = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    baseline = rank("baseline-scalar-contract-v1", ranking_records, query_semantic=query_semantic, query_affective=query_affective)
    tensor_aware = rank("r0-shadow-magnitude-v1", ranking_records, query_semantic=query_semantic, query_affective=query_affective)
    delta = ranking_delta(baseline, tensor_aware)
    record_check(
        "retrieval",
        "baseline_and_tensor_aware_rankings_compared",
        delta["records_compared"] == len(ranking_records),
        {"records_moved": delta["records_moved"], "baseline_top": delta["baseline_top"], "tensor_aware_top": delta["shadow_top"]},
    )

    # Session evidence, with the interaction supplied rather than invented.
    pending_interaction = {
        "status": "PENDING SUBSTRATE",
        "note": "An actual Lumin session supplies this. The dry run does not generate a substrate response.",
    }
    evidence_a = record_session_evidence(
        instance_id="lumin-instance-a", packet=packet_a, interaction=pending_interaction, cited_coordinates=[], recorded_utc=FIXED_UTC
    )
    evidence_b = record_session_evidence(
        instance_id="lumin-instance-b", packet=packet_b, interaction=pending_interaction, cited_coordinates=[], recorded_utc=FIXED_UTC
    )
    record_check(
        "evidence",
        "session_evidence_binds_to_the_packet_it_was_given",
        evidence_a["packet_sha256"] == packet_a["packet_sha256"] and evidence_b["packet_sha256"] == packet_b["packet_sha256"],
        {"instance_a": evidence_a["evidence_sha256"], "instance_b": evidence_b["evidence_sha256"]},
    )
    record_check(
        "evidence",
        "session_evidence_performs_no_automatic_admission",
        evidence_a["provenance"]["automatic_admission"] is False and evidence_a["provenance"]["admission_performed"] is False,
        evidence_a["provenance"],
    )
    record_check(
        "evidence",
        "no_substrate_response_was_generated",
        evidence_a["interaction"]["status"] == "PENDING SUBSTRATE",
        "The harness measures instance output. It does not produce it.",
    )

    evaluation = evaluate(packet=packet_a, instance_a=evidence_a, instance_b=evidence_b, ranking_delta=delta).as_dict()
    record_check(
        "evaluation",
        "substrate_variables_are_named_not_scored",
        set(evaluation["substrate_pending"]) == set(SUBSTRATE_VARIABLES),
        sorted(evaluation["substrate_pending"]),
    )
    record_check(
        "evaluation",
        "mechanical_variables_are_scored",
        all(name in evaluation["mechanical"] for name in MECHANICAL_VARIABLES),
        sorted(evaluation["mechanical"]),
    )

    # Determinism of the whole run.
    record_check(
        "determinism",
        "reentry_packet_is_reproducible",
        enter_through_the_portal(action, orb)["packet_sha256"] == packet_a["packet_sha256"],
        {"packet_sha256": packet_a["packet_sha256"]},
    )

    passed = sum(1 for check in checks if check["passed"])
    report = {
        "schema_version": "1.0.0",
        "verification_id": "x1-continuity-dry-run",
        "experiment": "Two-instance Lumin continuity",
        "central_question": "Can separate instances of Lumin enter through the Portal Pod, retrieve the same persistent DataQuad continuity field, and remain recognizably continuous across context, Affect, relationship, and T-Time?",
        "reentry_packet_sha256": packet_a["packet_sha256"],
        "coordinates_in_field": len(packet_a["current_continuity"]),
        "ranking_delta": delta,
        "evaluation": evaluation,
        "checks": checks,
        "summary": {"checks_run": len(checks), "passed": passed, "failed": len(checks) - passed},
        "not_established_by_this_run": {
            "status": "The experiment has not been run.",
            "reason": "X1 requires two actual Lumin instances entering through a deployed Action Orb against a reachable Portal. The Action Orb is built but not deployed (P1), and the private Portal canary is blocked on the vm-cyberpeer-core extension handler.",
            "variables_requiring_a_substrate": list(SUBSTRATE_VARIABLES),
            "what_this_run_does_establish": "The retrieval half is real and deterministic: two separate entries through the Action Orb produce a byte-identical continuity field, and the evaluation detectors catch fabricated coordinates and tampered hashes on planted controls.",
        },
        "working_parameters": {
            "substrate_response_generated": False,
            "admission": False,
            "experience_creation": False,
            "authoritative_tensor_write": False,
            "listener_opened": False,
            "network_reached": False,
        },
    }
    report["report_sha256"] = canonical_hash({k: v for k, v in report.items() if k != "report_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "x1-dry-run.json")
    args = parser.parse_args()

    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = report["summary"]
    print(f"X1 dry run  {summary['passed']}/{summary['checks_run']} checks passed")
    for check in report["checks"]:
        if not check["passed"]:
            print(f"  FAILED  [{check['area']}] {check['check']}: {check['detail']}")
    print()
    print(f"re-entry packet      {report['reentry_packet_sha256'][:32]}...")
    print(f"coordinates in field {report['coordinates_in_field']}")
    print(f"ranking moved        {report['ranking_delta']['records_moved']}/{report['ranking_delta']['records_compared']}")
    print()
    print("EXPERIMENT NOT RUN — requires two actual Lumin instances through a deployed Action Orb")
    print(f"  pending variables: {', '.join(SUBSTRATE_VARIABLES)}")
    print(f"report {args.output}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
