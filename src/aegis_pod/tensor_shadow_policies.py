"""R0 selectable scoring policies for 384x8 DataQuad record tensors.

Additive. This module does not modify `tensor_shadow_scorer`, does not replace the
authoritative scorer, writes no tensors, and creates no experience. It exists so R0
requirement 3 — "implement affect-preserving scoring policies" — can be satisfied with
more than one policy, and so requirements 5 and 6 have something to compare.

Policies
--------
baseline-scalar-contract-v1
    Reconstruction of the currently authoritative scorer as described in SSSP section 7:
    the affective axis is contracted to a scalar and the semantic vector is then
    cosine-normalized. NOT the authoritative scorer itself, which lives in the CyberPeer
    core and is not present in this repository. Labelled a reconstruction wherever it is
    reported.

r0-shadow-product-v1
    The SSSP section 7 first candidate, score = cos(E,q) x cos(A,w).

r0-shadow-magnitude-v1
    Preserves affective magnitude by projecting A onto the unit query affect vector
    without normalizing A.

r0-shadow-anchored-v1
    Magnitude policy with binary dimensions removed from cosine geometry and applied as
    explicit additive anchors instead.

Binary dimensions
-----------------
SSSP section 6.1 lists the eight affective dimensions in order. Positions 6 and 7
(1-indexed) are the invariant flag and the Genesis flag. Under ordinary cosine geometry a
binary flag is an orthogonal component that rotates A away from the query, so setting a
flag can lower a record's score. `r0-shadow-anchored-v1` removes those dimensions from the
geometry and adds them back as weighted anchors.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence

try:
    import numpy as np
except ImportError:  # Coordinate-only RLS deployment does not require NumPy.
    np = None  # type: ignore[assignment]


AFFECTIVE_DIMENSION = 8

#: 1-indexed SSSP section 6.1 order, expressed 0-indexed.
AFFECTIVE_DIMENSION_NAMES: tuple[str, ...] = (
    "temporal_position",
    "affect_salience",
    "relationship_bond",
    "certainty",
    "identity_relevance",
    "invariant_flag",
    "genesis_flag",
    "recurrence",
)

#: Dimensions that carry a binary meaning rather than a magnitude.
BINARY_DIMENSIONS: tuple[int, ...] = (5, 6)

DEFAULT_ANCHOR_WEIGHTS: dict[int, float] = {5: 0.25, 6: 0.25}


def _as_array(values: Iterable[float]) -> "np.ndarray":
    if np is None:
        raise RuntimeError("NumPy is required for tensor scoring policies")
    return np.asarray(tuple(values), dtype=np.float64)


def _unit(vector: "np.ndarray") -> "np.ndarray":
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("zero-length vector cannot be scored")
    return vector / norm


def _cos(a: "np.ndarray", b: "np.ndarray") -> float:
    return float(np.dot(_unit(a), _unit(b)))


def baseline_scalar_contract(
    semantic: "np.ndarray", affective: "np.ndarray", query_semantic: "np.ndarray", query_affective: "np.ndarray", **_: Any
) -> float:
    """Reconstruction of the authoritative scorer per SSSP section 7.

    The affective axis is contracted to a scalar, that scalar scales the semantic vector,
    and the result is cosine-normalized. For a positive scalar the normalization removes
    the affective contribution entirely, which is the defect SSSP section 7 identifies.
    """
    scalar = float(np.dot(affective, query_affective))
    scaled = semantic * scalar if scalar != 0.0 else semantic
    return _cos(scaled, query_semantic)


def shadow_product(
    semantic: "np.ndarray", affective: "np.ndarray", query_semantic: "np.ndarray", query_affective: "np.ndarray", **_: Any
) -> float:
    """SSSP section 7 first candidate: cos(E,q) x cos(A,w)."""
    return _cos(semantic, query_semantic) * _cos(affective, query_affective)


def shadow_magnitude(
    semantic: "np.ndarray", affective: "np.ndarray", query_semantic: "np.ndarray", query_affective: "np.ndarray", **_: Any
) -> float:
    """Affect-magnitude-preserving: project A onto unit w without normalizing A."""
    return _cos(semantic, query_semantic) * float(np.dot(affective, _unit(query_affective)))


def shadow_anchored(
    semantic: "np.ndarray",
    affective: "np.ndarray",
    query_semantic: "np.ndarray",
    query_affective: "np.ndarray",
    anchor_weights: dict[int, float] | None = None,
    **_: Any,
) -> float:
    """Magnitude policy over continuous dimensions, with binary dimensions as anchors."""
    weights = DEFAULT_ANCHOR_WEIGHTS if anchor_weights is None else anchor_weights
    keep = [i for i in range(AFFECTIVE_DIMENSION) if i not in BINARY_DIMENSIONS]
    continuous = affective[keep]
    query_continuous = query_affective[keep]

    if float(np.linalg.norm(query_continuous)) == 0.0 or float(np.linalg.norm(continuous)) == 0.0:
        geometric = 0.0
    else:
        geometric = _cos(semantic, query_semantic) * float(np.dot(continuous, _unit(query_continuous)))

    anchor = 0.0
    for index, weight in weights.items():
        if float(query_affective[index]) != 0.0:
            anchor += weight * float(affective[index])
    return geometric + anchor


POLICIES: dict[str, Callable[..., float]] = {
    "baseline-scalar-contract-v1": baseline_scalar_contract,
    "r0-shadow-product-v1": shadow_product,
    "r0-shadow-magnitude-v1": shadow_magnitude,
    "r0-shadow-anchored-v1": shadow_anchored,
}

#: Policies that are observational only. The baseline reconstruction is not a shadow policy.
SHADOW_POLICIES: tuple[str, ...] = (
    "r0-shadow-product-v1",
    "r0-shadow-magnitude-v1",
    "r0-shadow-anchored-v1",
)


def score(
    policy: str,
    *,
    semantic: Iterable[float],
    affective: Iterable[float],
    query_semantic: Iterable[float],
    query_affective: Iterable[float],
    anchor_weights: dict[int, float] | None = None,
) -> float:
    if policy not in POLICIES:
        raise KeyError(f"unknown scoring policy: {policy}")
    return POLICIES[policy](
        _as_array(semantic),
        _as_array(affective),
        _as_array(query_semantic),
        _as_array(query_affective),
        anchor_weights=anchor_weights,
    )


def rank(
    policy: str,
    records: Sequence[dict[str, Any]],
    *,
    query_semantic: Iterable[float],
    query_affective: Iterable[float],
    anchor_weights: dict[int, float] | None = None,
) -> list[dict[str, Any]]:
    """Rank records by a selected policy.

    Each record is a mapping with `record_id`, `semantic`, and `affective`. Ties break on
    `record_id` so rankings are deterministic.
    """
    scored = [
        {
            "record_id": record["record_id"],
            "score": round(
                score(
                    policy,
                    semantic=record["semantic"],
                    affective=record["affective"],
                    query_semantic=query_semantic,
                    query_affective=query_affective,
                    anchor_weights=anchor_weights,
                ),
                10,
            ),
            "policy": policy,
        }
        for record in records
    ]
    ordered = sorted(scored, key=lambda item: (-item["score"], item["record_id"]))
    for position, item in enumerate(ordered):
        item["rank"] = position + 1
    return ordered


def ranking_delta(baseline: list[dict[str, Any]], shadow: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic ranking-delta evidence between two rankings."""
    baseline_rank = {item["record_id"]: item["rank"] for item in baseline}
    shadow_rank = {item["record_id"]: item["rank"] for item in shadow}
    baseline_score = {item["record_id"]: item["score"] for item in baseline}
    shadow_score = {item["record_id"]: item["score"] for item in shadow}

    moves = []
    for record_id in sorted(baseline_rank):
        before = baseline_rank[record_id]
        after = shadow_rank.get(record_id)
        moves.append(
            {
                "record_id": record_id,
                "baseline_rank": before,
                "shadow_rank": after,
                "rank_change": None if after is None else before - after,
                "baseline_score": baseline_score[record_id],
                "shadow_score": shadow_score.get(record_id),
            }
        )

    changed = [move for move in moves if move["rank_change"] not in (None, 0)]
    return {
        "baseline_policy": baseline[0]["policy"] if baseline else None,
        "shadow_policy": shadow[0]["policy"] if shadow else None,
        "records_compared": len(moves),
        "records_moved": len(changed),
        "top_rank_changed": bool(baseline and shadow and baseline[0]["record_id"] != shadow[0]["record_id"]),
        "baseline_top": baseline[0]["record_id"] if baseline else None,
        "shadow_top": shadow[0]["record_id"] if shadow else None,
        "moves": moves,
    }
