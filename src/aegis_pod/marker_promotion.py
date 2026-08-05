from __future__ import annotations

import argparse
from glob import glob
from pathlib import Path
from typing import Any

from src.aegis_pod.verified_marker import load_json, sha256_file, write_json


def target_hash_paths(marker: dict[str, Any]) -> dict[str, str]:
    target = marker.get("target", {})
    target_kind = target.get("kind")
    target_id = target.get("id")
    if target_kind == "tensor_runtime" and target_id == "local-deterministic-fixture-tensor-runtime":
        return {
            "schema_hash": "contracts/mathematical-tensor.schema.json",
            "implementation_hash": "src/aegis_pod/tensor_runtime.py",
            "demo_hash": "reports/runtime/tensor-health.json",
            "test_result_hash": "reports/runtime/2026-07-20-step-3-tensor-runtime-evidence.md",
        }
    if target_kind == "tensor_runtime" and target_id == "orion-live-structural-non-semantic-vector-runtime":
        return {
            "schema_hash": "contracts/mathematical-tensor.schema.json",
            "implementation_hash": "src/aegis_pod/live_structural_vectors.py",
            "demo_hash": "reports/runtime/2026-07-21-live-stage-c-orion-structural-vectors-report.json",
            "test_result_hash": "reports/runtime/2026-07-21-stage-c-structural-vector-evidence.md",
        }
    if target_kind == "orb" and target_id == "rls-orb-fixture":
        return {
            "schema_hash": "contracts/orb.schema.json",
            "implementation_hash": "src/aegis_pod/orb_runtime.py",
            "demo_hash": "reports/runtime/orbs/rls-orb-fixture.demonstration.json",
            "test_result_hash": "reports/runtime/2026-07-20-step-4-rls-orb-attachment-evidence.md",
        }
    return {}


def hash_evidence(marker: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    paths = target_hash_paths(marker)
    declared_hashes = marker.get("hashes", {})
    evidence: list[dict[str, Any]] = []
    for name, declared in declared_hashes.items():
        relative_path = paths.get(name, "")
        item = {
            "name": name,
            "path": relative_path,
            "declared_hash": declared,
            "computed_hash": "",
            "current": False,
        }
        if relative_path:
            path = root / relative_path
            if path.exists():
                computed = sha256_file(path)
                item["computed_hash"] = computed
                item["current"] = computed == declared
        evidence.append(item)
    return evidence


def evidence_path_results(marker: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for relative_path in marker.get("verification", {}).get("evidence_paths", []):
        path = root / str(relative_path)
        try:
            inside_root = path.resolve().is_relative_to(root.resolve())
        except OSError:
            inside_root = False
        results.append({
            "path": str(relative_path),
            "exists": path.exists(),
            "inside_root": inside_root,
        })
    return results


def review_evidence(marker: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    builder_reviewers = set(policy.get("reviewer_model", {}).get("builder_reviewers", []))
    reviews = marker.get("reviews", [])
    reviewers = sorted({
        review.get("reviewer")
        for review in reviews
        if isinstance(review, dict) and review.get("reviewer")
    })
    independent_reviewers = sorted(reviewer for reviewer in reviewers if reviewer not in builder_reviewers)
    nonblocking = [
        review
        for review in reviews
        if isinstance(review, dict) and review.get("result") == "no_blocking_objection"
    ]
    peer_reviews_with_hashes = [
        review
        for review in reviews
        if isinstance(review, dict)
        and review.get("reviewer") != "codex-local-runtime"
        and review.get("evidence", {}).get("message_hashes")
    ]
    return {
        "distinct_reviewers": reviewers,
        "distinct_reviewer_count": len(reviewers),
        "builder_reviewers": sorted(builder_reviewers.intersection(reviewers)),
        "independent_reviewers": independent_reviewers,
        "independent_reviewer_count": len(independent_reviewers),
        "nonblocking_review_count": len(nonblocking),
        "peer_reviews_with_message_hashes": len(peer_reviews_with_hashes),
    }


def threshold_blockers(
    marker: dict[str, Any],
    threshold: dict[str, Any],
    hashes: list[dict[str, Any]],
    evidence_paths: list[dict[str, Any]],
    reviews: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    min_reviewers = threshold.get("min_independent_reviewers", 0)
    if reviews["independent_reviewer_count"] < min_reviewers:
        blockers.append(f"requires at least {min_reviewers} independent reviewers")

    allowed_results = set(threshold.get("required_review_results", []))
    for review in marker.get("reviews", []):
        result = review.get("result") if isinstance(review, dict) else None
        if result not in allowed_results:
            blockers.append(f"review result outside threshold: {result}")

    if threshold.get("required_reviewer_evidence", {}).get("peer_review_message_hashes"):
        if reviews["peer_reviews_with_message_hashes"] < 1:
            blockers.append("requires peer review evidence with bridge message hashes")

    commands = marker.get("verification", {}).get("commands", [])
    if threshold.get("require_all_commands_pass") and any(command.get("result") != "pass" for command in commands):
        blockers.append("all verification commands will pass")
    if threshold.get("require_all_commands_pass") and not commands:
        blockers.append("verification command evidence is required")

    if threshold.get("require_current_hashes"):
        if not hashes:
            blockers.append("declared hash evidence is required")
        stale = [item["name"] for item in hashes if not item["current"]]
        if stale:
            blockers.append(f"declared hashes are not current: {', '.join(stale)}")
            blockers.append("target hash drift requires reset to provisional")
        if not evidence_paths:
            blockers.append("evidence paths are required")
        missing_evidence = [item["path"] for item in evidence_paths if not item["exists"] or not item["inside_root"]]
        if missing_evidence:
            blockers.append(f"evidence paths are missing or outside root: {', '.join(missing_evidence)}")

    boundary = marker.get("claim_boundary", {})
    if threshold.get("require_claim_boundary"):
        if not boundary.get("demonstrates") or not boundary.get("outside_current_verified_surface"):
            blockers.append("claim boundary will include demonstrates and outside_current_verified_surface")

    live_reach = marker.get("verification", {}).get("live_reach")
    if live_reach is True and threshold.get("live_reach_allowed") is False:
        blockers.append("live_reach is outside this local promotion policy")

    if marker.get("working_parameters", {}).get("pod_state_effect") != "unchanged":
        blockers.append("local marker promotion requires pod_state_effect unchanged")

    return blockers


def evaluate_marker(marker: dict[str, Any], policy: dict[str, Any], root: Path, marker_path: str) -> dict[str, Any]:
    hashes = hash_evidence(marker, root)
    evidence_paths = evidence_path_results(marker, root)
    reviews = review_evidence(marker, policy)
    state_results: dict[str, Any] = {}
    for state_name in ["reviewed", "verified"]:
        blockers = threshold_blockers(marker, policy["states"][state_name], hashes, evidence_paths, reviews)
        state_results[state_name] = {
            "eligible": not blockers,
            "blockers": blockers,
        }

    drift_detected = any(not item["current"] for item in hashes) or not hashes
    if drift_detected:
        recommended_state = "provisional"
        recommendation_reason = "reset_to_provisional_required"
    elif state_results["verified"]["eligible"]:
        recommended_state = "verified"
        recommendation_reason = "verified_threshold_met"
    elif state_results["reviewed"]["eligible"]:
        recommended_state = "reviewed"
        recommendation_reason = "reviewed_threshold_met"
    else:
        recommended_state = "provisional" if marker.get("trust_state") in {"provisional", "reviewed", "verified"} else marker.get("trust_state", "draft")
        recommendation_reason = "threshold_not_met"

    return {
        "marker_id": marker.get("marker_id", ""),
        "path": marker_path,
        "current_trust_state": marker.get("trust_state", ""),
        "recommended_trust_state": recommended_state,
        "recommendation_reason": recommendation_reason,
        "promotion_applied": False,
        "reviews": reviews,
        "hashes": hashes,
        "evidence_paths": evidence_paths,
        "thresholds": state_results,
    }


def run_promotion_evaluation(
    root: Path,
    policy_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    policy_relative = "fixtures/marker-promotion-policy.json"
    policy_file = policy_path if policy_path is not None else root / policy_relative
    policy = load_json(policy_file)
    marker_glob = policy.get("applies_to", {}).get("marker_glob", "")
    root_resolved = root.resolve()
    marker_paths = [
        str(Path(path).resolve().relative_to(root_resolved))
        for path in sorted(glob(str(root / marker_glob)))
    ] if marker_glob else []
    marker_results = []
    for marker_relative in marker_paths:
        marker = load_json(root / marker_relative)
        marker_results.append(evaluate_marker(marker, policy, root, marker_relative))

    report = {
        "schema_version": "0.1.0",
        "policy_id": policy["policy_id"],
        "policy_path": str(policy_file.relative_to(root)) if policy_file.is_relative_to(root) else str(policy_file),
        "working_parameters": {
            "scope": "local marker reports only",
            "pod_state_effect": "unchanged",
            "live_reach": False,
            "promotion_applied": False,
        },
        "summary": {
            "markers_evaluated": len(marker_results),
            "reviewed_recommendations": sum(1 for item in marker_results if item["recommended_trust_state"] == "reviewed"),
            "verified_recommendations": sum(1 for item in marker_results if item["recommended_trust_state"] == "verified"),
        },
        "markers": marker_results,
    }
    target = output_path if output_path is not None else root / "reports" / "runtime" / "marker-promotion-report.json"
    write_json(target, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local Verified Code Marker promotion thresholds.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    report = run_promotion_evaluation(root)
    print("PASS marker promotion thresholds evaluated")
    print(f"ROOT {root}")
    print("BOUNDARY local marker reports only; no marker state changed and no live DataQuad roots referenced")
    for marker in report["markers"]:
        print(
            f"MARKER {marker['marker_id']} current={marker['current_trust_state']} "
            f"recommended={marker['recommended_trust_state']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
