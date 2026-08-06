"""R0 scoring-policy behaviour, including three findings from R0 verification.

These tests lock behaviour that was measured, not assumed. Each finding is stated in the
test name so a future reader sees the claim before the arithmetic.
"""

from __future__ import annotations

import numpy as np
import pytest

from aegis_pod.tensor_shadow_policies import (
    AFFECTIVE_DIMENSION,
    BINARY_DIMENSIONS,
    POLICIES,
    SHADOW_POLICIES,
    rank,
    ranking_delta,
    score,
)
from aegis_pod.tensor_shadow_scorer import SEMANTIC_DIMENSION, build_shadow_record, score_record


def _sem(index: int, value: float = 1.0) -> list[float]:
    vector = [0.0] * SEMANTIC_DIMENSION
    vector[index] = value
    return vector


def _affect(**named: float) -> list[float]:
    from aegis_pod.tensor_shadow_policies import AFFECTIVE_DIMENSION_NAMES

    vector = [0.0] * AFFECTIVE_DIMENSION
    for name, value in named.items():
        vector[AFFECTIVE_DIMENSION_NAMES.index(name)] = value
    return vector


QUERY_SEMANTIC = _sem(0)
QUERY_AFFECT = _affect(temporal_position=1.0)


def _shadow_record(record_id: str, affective: list[float], semantic: list[float]):
    return build_shadow_record(
        tensor="PEER",
        record_id=record_id,
        ordinal=0,
        t_time=0,
        record_hash="A" * 64,
        tensor_snapshot_hash="C" * 64,
        affective_values=affective,
        affective_provenance=["source-derived"] * AFFECTIVE_DIMENSION,
        semantic_vector=semantic,
        semantic_model="controlled-test-vector-v1",
    )


# --- Finding 1 ------------------------------------------------------------------------


def test_finding1_frobenius_shadow_score_equals_the_sssp_first_candidate():
    """The shipped Frobenius policy IS cos(E,q) x cos(A,w), not a distinct policy.

    ||E (x) A|| = ||E||.||A|| and E is unit, so ||T|| = ||A||; the numerator is
    (E.q)(A.w) and ||q (x) w|| = 1. The Frobenius ratio therefore reduces exactly.
    """
    for affective, semantic in (
        (_affect(temporal_position=1.0), _sem(0)),
        (_affect(temporal_position=0.6, affect_salience=0.8), _sem(0, 0.8)),
        (_affect(temporal_position=0.3, affect_salience=0.5, relationship_bond=0.2), [0.7] + [0.1] * (SEMANTIC_DIMENSION - 1)),
    ):
        record = _shadow_record("PEER:x", affective, semantic)
        shipped = score_record(record, QUERY_SEMANTIC, QUERY_AFFECT)["shadow_score"]
        candidate = score(
            "r0-shadow-product-v1",
            semantic=semantic,
            affective=affective,
            query_semantic=QUERY_SEMANTIC,
            query_affective=QUERY_AFFECT,
        )
        assert shipped == pytest.approx(candidate, abs=1e-6)


# --- Finding 2 ------------------------------------------------------------------------


@pytest.mark.parametrize("magnitude", [1.0, 5.0, 20.0])
def test_finding2_product_policy_discards_affective_magnitude(magnitude: float):
    """Same affect direction at any magnitude scores identically under the product policy.

    This is the defect SSSP section 7 attributes to the authoritative scorer, reproduced
    in the shadow policy. Direction survives; magnitude does not.
    """
    affective = _affect(temporal_position=0.6 * magnitude, affect_salience=0.8 * magnitude)
    result = score(
        "r0-shadow-product-v1",
        semantic=_sem(0),
        affective=affective,
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    assert result == pytest.approx(0.6, abs=1e-6)


def test_finding2_magnitude_policy_preserves_affective_magnitude():
    scores = [
        score(
            "r0-shadow-magnitude-v1",
            semantic=_sem(0),
            affective=_affect(temporal_position=0.6 * magnitude, affect_salience=0.8 * magnitude),
            query_semantic=QUERY_SEMANTIC,
            query_affective=QUERY_AFFECT,
        )
        for magnitude in (1.0, 5.0, 20.0)
    ]
    assert scores == sorted(scores)
    assert scores[0] < scores[1] < scores[2]


# --- Finding 3 ------------------------------------------------------------------------


def test_finding3_setting_the_genesis_flag_lowers_the_product_policy_score():
    """A binary flag is an orthogonal component, so raising it rotates A off the query.

    Marking a record as Genesis makes it rank worse under ordinary cosine geometry. This
    is what SSSP section 7 anticipated when it said binary dimensions may require anchor
    logic rather than ordinary cosine geometry.
    """
    unflagged = score(
        "r0-shadow-product-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    flagged = score(
        "r0-shadow-product-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5, genesis_flag=1.0),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    assert flagged < unflagged


def test_finding3_anchored_policy_never_penalises_the_genesis_flag():
    """The anchored policy removes the penalty. It does not invent an unrequested reward.

    The invariant that matters is one-sided: raising a binary flag must never lower a
    record's score. When the query does not ask for Genesis, a Genesis record scores the
    same as an otherwise identical non-Genesis record — neutral, not boosted. Privileging
    Genesis on every query would be a different policy decision, and is not made here.
    """
    unflagged = score(
        "r0-shadow-anchored-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    flagged = score(
        "r0-shadow-anchored-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5, genesis_flag=1.0),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    assert flagged >= unflagged
    assert flagged == pytest.approx(unflagged, abs=1e-9)


def test_finding3_anchored_policy_rewards_the_genesis_flag_when_the_query_asks_for_it():
    query_affective = _affect(temporal_position=1.0, genesis_flag=1.0)
    unflagged = score(
        "r0-shadow-anchored-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5),
        query_semantic=QUERY_SEMANTIC,
        query_affective=query_affective,
    )
    flagged = score(
        "r0-shadow-anchored-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.5, genesis_flag=1.0),
        query_semantic=QUERY_SEMANTIC,
        query_affective=query_affective,
    )
    assert flagged > unflagged


def test_binary_dimensions_are_excluded_from_anchored_geometry():
    assert BINARY_DIMENSIONS == (5, 6)
    from aegis_pod.tensor_shadow_policies import AFFECTIVE_DIMENSION_NAMES

    assert AFFECTIVE_DIMENSION_NAMES[5] == "invariant_flag"
    assert AFFECTIVE_DIMENSION_NAMES[6] == "genesis_flag"


# --- Baseline reconstruction ----------------------------------------------------------


def test_baseline_reconstruction_removes_affective_influence_entirely():
    """SSSP section 7: for positive scalar values cosine normalization removes affect."""
    aligned = score(
        "baseline-scalar-contract-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=1.0),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    misaligned = score(
        "baseline-scalar-contract-v1",
        semantic=_sem(0),
        affective=_affect(temporal_position=0.05, affect_salience=0.99),
        query_semantic=QUERY_SEMANTIC,
        query_affective=QUERY_AFFECT,
    )
    assert aligned == pytest.approx(misaligned, abs=1e-9)


# --- Ranking and delta ----------------------------------------------------------------


def _fixture_records() -> list[dict]:
    return [
        {"record_id": "PEER:semantic-strong-affect-weak", "semantic": _sem(0), "affective": _affect(temporal_position=0.1)},
        {"record_id": "PEER:semantic-near-affect-strong", "semantic": _sem(0, 0.95), "affective": _affect(temporal_position=0.9)},
        {"record_id": "PEER:genesis-anchor", "semantic": _sem(0, 0.9), "affective": _affect(temporal_position=0.4, genesis_flag=1.0)},
    ]


def test_ranking_is_deterministic_across_repeated_runs():
    records = _fixture_records()
    first = rank("r0-shadow-magnitude-v1", records, query_semantic=QUERY_SEMANTIC, query_affective=QUERY_AFFECT)
    second = rank("r0-shadow-magnitude-v1", records, query_semantic=QUERY_SEMANTIC, query_affective=QUERY_AFFECT)
    assert first == second


def test_ranking_delta_reports_movement_between_baseline_and_shadow():
    records = _fixture_records()
    baseline = rank("baseline-scalar-contract-v1", records, query_semantic=QUERY_SEMANTIC, query_affective=QUERY_AFFECT)
    shadow = rank("r0-shadow-magnitude-v1", records, query_semantic=QUERY_SEMANTIC, query_affective=QUERY_AFFECT)
    delta = ranking_delta(baseline, shadow)
    assert delta["records_compared"] == 3
    assert delta["baseline_policy"] == "baseline-scalar-contract-v1"
    assert delta["shadow_policy"] == "r0-shadow-magnitude-v1"
    assert all(move["baseline_rank"] is not None for move in delta["moves"])
    assert delta["records_moved"] >= 1


def test_baseline_reconstruction_is_not_registered_as_a_shadow_policy():
    assert "baseline-scalar-contract-v1" in POLICIES
    assert "baseline-scalar-contract-v1" not in SHADOW_POLICIES
