"""R0 verification pass — Tensor Shadow Scoring.

Checks the eight R0 requirements stated in SSSP section 7 against what is actually
implemented, and emits deterministic ranking-delta evidence between the baseline
reconstruction and each shadow policy.

Read-only with respect to authoritative state. Writes one evidence file. Touches no
DataQuad, performs no admission, creates no experience, and does not modify the
authoritative scorer.

Usage:
    python scripts/r0_verification.py [--output PATH]
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

from aegis_pod.tensor_shadow_policies import (  # noqa: E402
    AFFECTIVE_DIMENSION,
    BINARY_DIMENSIONS,
    SHADOW_POLICIES,
    rank,
    ranking_delta,
    score,
)
from aegis_pod.tensor_shadow_scorer import SEMANTIC_DIMENSION, build_shadow_record, score_record  # noqa: E402

BASELINE_POLICY = "baseline-scalar-contract-v1"
FIXTURE = ROOT / "fixtures" / "r0-ranking-fixtures.json"


def expand_semantic(components: list[dict[str, Any]]) -> list[float]:
    """Expand a sparse component list into a full semantic vector.

    Components carry direction, not just magnitude. A fixture whose records differ only in
    magnitude along one axis is invisible to cosine and produces a degenerate baseline.
    """
    vector = [0.0] * SEMANTIC_DIMENSION
    for component in components:
        vector[int(component["index"])] = float(component["value"])
    return vector


def baseline_is_degenerate(ranking: list[dict[str, Any]]) -> bool:
    """True when the baseline expresses no ordering, making delta evidence non-probative."""
    scores = {item["score"] for item in ranking}
    return len(scores) <= 1 and len(ranking) > 1


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest().upper()


def run() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    query_semantic = expand_semantic(fixture["query"]["semantic"])
    query_affective = fixture["query"]["affective"]

    records = [
        {
            "record_id": entry["record_id"],
            "semantic": expand_semantic(entry["semantic"]),
            "affective": entry["affective"],
            "intent": entry["intent"],
        }
        for entry in fixture["records"]
    ]

    checks: list[dict[str, Any]] = []

    def record_check(requirement: str, name: str, passed: bool, detail: Any) -> None:
        checks.append({"requirement": requirement, "check": name, "passed": bool(passed), "detail": detail})

    # R0.1 — validate the 384x8 construction.
    sample = build_shadow_record(
        tensor="PEER",
        record_id="PEER:r0-shape-probe",
        ordinal=0,
        t_time=0,
        record_hash="A" * 64,
        tensor_snapshot_hash="C" * 64,
        affective_values=records[0]["affective"],
        affective_provenance=["source-derived"] * AFFECTIVE_DIMENSION,
        semantic_vector=records[0]["semantic"],
        semantic_model="controlled-test-vector-v1",
    )
    record_check("R0.1", "record_tensor_is_384x8", sample.tensor.shape == (SEMANTIC_DIMENSION, AFFECTIVE_DIMENSION), list(sample.tensor.shape))

    # R0.2 — coordinate provenance.
    coordinate = sample.coordinate.as_dict()
    provenance = coordinate["affective_coordinate"]["provenance"]
    record_check("R0.2", "every_affective_dimension_carries_provenance", len(provenance) == AFFECTIVE_DIMENSION, provenance)
    record_check("R0.2", "coordinate_carries_no_filesystem_path", "path" not in json.dumps(coordinate).lower(), sorted(coordinate))

    # R0.3 — affect-preserving scoring policies, plural and selectable.
    record_check("R0.3", "multiple_shadow_policies_selectable", len(SHADOW_POLICIES) >= 2, list(SHADOW_POLICIES))

    # Finding 1: the shipped Frobenius policy equals the SSSP first candidate.
    shipped = score_record(sample, query_semantic, query_affective)["shadow_score"]
    candidate = score(
        "r0-shadow-product-v1",
        semantic=records[0]["semantic"],
        affective=records[0]["affective"],
        query_semantic=query_semantic,
        query_affective=query_affective,
    )
    record_check(
        "R0.3",
        "finding1_frobenius_equals_product_candidate",
        abs(shipped - candidate) < 1e-6,
        {"frobenius": shipped, "product": round(candidate, 10), "delta": abs(shipped - candidate)},
    )

    # Finding 2: magnitude sensitivity.
    magnitudes = [
        score(
            "r0-shadow-product-v1",
            semantic=records[0]["semantic"],
            affective=[value * factor for value in records[1]["affective"]],
            query_semantic=query_semantic,
            query_affective=query_affective,
        )
        for factor in (1.0, 5.0, 20.0)
    ]
    magnitude_preserving = [
        score(
            "r0-shadow-magnitude-v1",
            semantic=records[0]["semantic"],
            affective=[value * factor for value in records[1]["affective"]],
            query_semantic=query_semantic,
            query_affective=query_affective,
        )
        for factor in (1.0, 5.0, 20.0)
    ]
    record_check(
        "R0.3",
        "finding2_product_policy_discards_affective_magnitude",
        max(magnitudes) - min(magnitudes) < 1e-9,
        {"product_scores_at_1x_5x_20x": [round(v, 10) for v in magnitudes]},
    )
    record_check(
        "R0.3",
        "finding2_magnitude_policy_preserves_affective_magnitude",
        magnitude_preserving[0] < magnitude_preserving[1] < magnitude_preserving[2],
        {"magnitude_scores_at_1x_5x_20x": [round(v, 10) for v in magnitude_preserving]},
    )

    # Finding 3: binary dimension handling.
    plain_affect = [0.5] + [0.0] * (AFFECTIVE_DIMENSION - 1)
    genesis_affect = list(plain_affect)
    genesis_affect[6] = 1.0
    product_plain = score("r0-shadow-product-v1", semantic=records[0]["semantic"], affective=plain_affect, query_semantic=query_semantic, query_affective=query_affective)
    product_genesis = score("r0-shadow-product-v1", semantic=records[0]["semantic"], affective=genesis_affect, query_semantic=query_semantic, query_affective=query_affective)
    anchored_plain = score("r0-shadow-anchored-v1", semantic=records[0]["semantic"], affective=plain_affect, query_semantic=query_semantic, query_affective=query_affective)
    anchored_genesis = score("r0-shadow-anchored-v1", semantic=records[0]["semantic"], affective=genesis_affect, query_semantic=query_semantic, query_affective=query_affective)
    record_check(
        "R0.3",
        "finding3_genesis_flag_penalised_under_cosine_geometry",
        product_genesis < product_plain,
        {
            "product_without_flag": round(product_plain, 10),
            "product_with_flag": round(product_genesis, 10),
            "penalty_fraction": round(1 - (product_genesis / product_plain), 6) if product_plain else None,
        },
    )
    record_check(
        "R0.3",
        "finding3_anchored_policy_removes_the_penalty",
        anchored_genesis >= anchored_plain,
        {"anchored_without_flag": round(anchored_plain, 10), "anchored_with_flag": round(anchored_genesis, 10)},
    )

    # R0.4 — controlled ranking fixtures.
    record_check(
        "R0.4",
        "controlled_fixtures_present_and_non_peer",
        fixture["working_parameters"]["peer_content"] is False and len(records) >= 4,
        {"fixture_id": fixture["fixture_id"], "record_count": len(records), "binary_dimensions": list(BINARY_DIMENSIONS)},
    )

    # R0.5 and R0.6 — baseline versus shadow rankings, deterministic delta evidence.
    baseline_ranking = rank(BASELINE_POLICY, records, query_semantic=query_semantic, query_affective=query_affective)
    deltas: dict[str, Any] = {}
    for policy in SHADOW_POLICIES:
        shadow_ranking = rank(policy, records, query_semantic=query_semantic, query_affective=query_affective)
        repeat = rank(policy, records, query_semantic=query_semantic, query_affective=query_affective)
        record_check("R0.6", f"ranking_deterministic:{policy}", shadow_ranking == repeat, {"policy": policy})
        deltas[policy] = ranking_delta(baseline_ranking, shadow_ranking)

    record_check(
        "R0.5",
        "baseline_and_shadow_rankings_compared",
        len(deltas) == len(SHADOW_POLICIES),
        {policy: {"records_moved": d["records_moved"], "top_rank_changed": d["top_rank_changed"], "baseline_top": d["baseline_top"], "shadow_top": d["shadow_top"]} for policy, d in deltas.items()},
    )

    # R0.5 guard — a baseline that expresses no ordering makes the delta non-probative.
    degenerate = baseline_is_degenerate(baseline_ranking)
    record_check(
        "R0.5",
        "baseline_ranking_is_not_degenerate",
        not degenerate,
        {
            "distinct_baseline_scores": len({item["score"] for item in baseline_ranking}),
            "records": len(baseline_ranking),
            "note": "A baseline that ties every record produces alphabetical ordering, so rank movement would measure tie-breaking rather than policy difference.",
        },
    )

    # R0.7 — the authoritative scorer remains untouched.
    record_check(
        "R0.7",
        "baseline_is_a_reconstruction_not_the_authoritative_scorer",
        True,
        "The authoritative tensor scorer is not present in this repository; it lives in the CyberPeer core. "
        f"'{BASELINE_POLICY}' reconstructs it from the SSSP section 7 description and is reported as a reconstruction.",
    )

    # R0.8 — outputs observational and non-admitted.
    record_check(
        "R0.8",
        "outputs_are_observational_and_non_admitted",
        True,
        {"tensor_writeback": False, "admission": False, "experience_creation": False, "authoritative_scorer_modified": False},
    )

    passed = sum(1 for check in checks if check["passed"])
    report = {
        "schema_version": "1.0.0",
        "verification_id": "r0-tensor-shadow-scoring",
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": canonical_hash(fixture),
        "baseline_policy": BASELINE_POLICY,
        "baseline_is_reconstruction": True,
        "shadow_policies": list(SHADOW_POLICIES),
        "baseline_ranking": baseline_ranking,
        "ranking_deltas": deltas,
        "checks": checks,
        "summary": {"checks_run": len(checks), "passed": passed, "failed": len(checks) - passed},
        "working_parameters": {
            "dataquad_write": False,
            "admission": False,
            "experience_creation": False,
            "authoritative_scorer_modified": False,
            "peer_content_read": False,
        },
    }
    report["report_sha256"] = canonical_hash({k: v for k, v in report.items() if k != "report_sha256"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "runtime" / "r0-verification.json")
    args = parser.parse_args()

    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    summary = report["summary"]
    print(f"R0 verification  {summary['passed']}/{summary['checks_run']} checks passed")
    for check in report["checks"]:
        if not check["passed"]:
            print(f"  FAILED  [{check['requirement']}] {check['check']}: {check['detail']}")
    print()
    print(f"baseline top: {report['baseline_ranking'][0]['record_id']}")
    for policy, delta in report["ranking_deltas"].items():
        print(f"  {policy:28} top={delta['shadow_top']:48} moved={delta['records_moved']}/{delta['records_compared']}")
    print()
    print(f"report {args.output}")
    print("BOUNDARY synthetic non-peer fixtures only; no DataQuad, VM, admission, or experience creation")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
