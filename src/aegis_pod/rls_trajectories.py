"""R1 deterministic trajectory and provenance records for the RLS Orb.

Additive. Every function here is a pure transformation over Tensor Coordinates. Nothing in
this module reads or writes PEER, PCT, NCT, or SPINE, performs admission, creates
experience, or converts inference into source fact.

Determinism
-----------
No wall-clock reads, no randomness, no set iteration order dependence. Timestamps are
supplied by the caller so a record can be reproduced exactly. Given the same coordinates,
these functions return byte-identical output.

Provenance
----------
`build_coordinate_provenance` emits records conforming to
`contracts/coordinate-provenance.schema.json`. It enforces the SSSP section 8 rule
structurally rather than by convention: only a source-derived dimension may set
`asserted_as_source_fact`, and the builder raises if a caller tries otherwise.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Sequence

AFFECTIVE_DIMENSION = 8

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

ORIGINS = ("source-derived", "tensorization-policy-assigned", "rls-derived", "steward-declared")

TRAJECTORY_VERSION = "r1-deterministic-trajectory-v1"

#: Rounding used to form a recurrence signature. Fixed so signatures are reproducible.
RECURRENCE_PRECISION = 3


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest().upper()


# --- Provenance -----------------------------------------------------------------------


def build_dimension_provenance(
    *,
    dimension: int,
    value: float,
    origin: str,
    source_field: str | None = None,
    policy: str | None = None,
    policy_version: str | None = None,
    derivation: str | None = None,
    derived_from_coordinates: Sequence[dict[str, Any]] | None = None,
    declared_by: str | None = None,
    declared_utc: str | None = None,
) -> dict[str, Any]:
    if origin not in ORIGINS:
        raise ValueError(f"unknown coordinate origin: {origin}")
    if not 0 <= dimension < AFFECTIVE_DIMENSION:
        raise ValueError(f"dimension will be 0..{AFFECTIVE_DIMENSION - 1}")

    entry: dict[str, Any] = {
        "dimension": dimension,
        "name": AFFECTIVE_DIMENSION_NAMES[dimension],
        "value": float(value),
        "origin": origin,
        # SSSP section 8: only a source-derived dimension is a source-record fact.
        "asserted_as_source_fact": origin == "source-derived",
    }

    if origin == "source-derived":
        if not source_field:
            raise ValueError("a source-derived dimension will name its source field")
        entry["source_field"] = source_field
    elif origin == "tensorization-policy-assigned":
        if not policy or not policy_version:
            raise ValueError("a policy-assigned dimension will name its policy and version")
        entry["policy"] = policy
        entry["policy_version"] = policy_version
    elif origin == "rls-derived":
        if not derivation or not derived_from_coordinates:
            raise ValueError("an RLS-derived dimension will name its derivation and source coordinates")
        entry["derivation"] = derivation
        entry["derived_from_coordinates"] = [dict(item) for item in derived_from_coordinates]
    elif origin == "steward-declared":
        if not declared_by or not declared_utc:
            raise ValueError("a Steward-declared dimension will name the declaring party and when")
        entry["declared_by"] = declared_by
        entry["declared_utc"] = declared_utc

    return entry


def build_coordinate_provenance(
    *,
    tensor: str,
    record_id: str,
    record_hash: str,
    tensor_snapshot_hash: str,
    dimensions: Sequence[dict[str, Any]],
    locator: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a coordinate provenance record.

    The locator is optional and explicitly replaceable. Identity lives in `coordinate_ref`,
    never in the locator.
    """
    if len(dimensions) != AFFECTIVE_DIMENSION:
        raise ValueError(f"coordinate provenance will carry {AFFECTIVE_DIMENSION} dimensions")
    for position, entry in enumerate(dimensions):
        if entry["dimension"] != position:
            raise ValueError("dimensions will be supplied in SSSP section 6.1 order")

    record: dict[str, Any] = {
        "schema_version": "0.1.0",
        "coordinate_ref": {
            "tensor": tensor,
            "record_id": record_id,
            "record_hash": record_hash,
            "tensor_snapshot_hash": tensor_snapshot_hash,
        },
        "dimensions": [dict(entry) for entry in dimensions],
    }
    if locator is not None:
        record["locator"] = dict(locator)
    return record


# --- Trajectories ---------------------------------------------------------------------


def _affect_values(coordinate: dict[str, Any]) -> list[float]:
    return [float(value) for value in coordinate["affective_coordinate"]["values"]]


def _ordered(coordinates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(coordinates, key=lambda item: (item["t_time"], item["tensor"], item["ordinal"], item["record_id"]))


def affect_trajectory(coordinates: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic affect movement between consecutive coordinates in T-Time order.

    Reports the step vector, its magnitude, and which dimension moved most. Makes no claim
    about why affect moved and creates no experience.
    """
    ordered = _ordered(coordinates)
    steps: list[dict[str, Any]] = []

    for previous, current in zip(ordered, ordered[1:]):
        before = _affect_values(previous)
        after = _affect_values(current)
        delta = [round(b - a, 10) for a, b in zip(before, after)]
        magnitude = round(sum(component * component for component in delta) ** 0.5, 10)
        largest = max(range(AFFECTIVE_DIMENSION), key=lambda i: (abs(delta[i]), -i))
        steps.append(
            {
                "from_coordinate": {"tensor": previous["tensor"], "record_id": previous["record_id"], "record_hash": previous["record_hash"]},
                "to_coordinate": {"tensor": current["tensor"], "record_id": current["record_id"], "record_hash": current["record_hash"]},
                "t_time_from": previous["t_time"],
                "t_time_to": current["t_time"],
                "delta": delta,
                "magnitude": magnitude,
                "largest_movement_dimension": AFFECTIVE_DIMENSION_NAMES[largest],
                "largest_movement_value": delta[largest],
            }
        )

    record = {
        "schema_version": "0.1.0",
        "record_type": "rls_affect_trajectory",
        "algorithm": {"name": "R1 deterministic affect trajectory", "version": TRAJECTORY_VERSION},
        "coordinates_observed": len(ordered),
        "steps": steps,
        "total_path_length": round(sum(step["magnitude"] for step in steps), 10),
        "provenance": {
            "source_kind": "tensor_coordinates",
            "context_location_embedded": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
            "inference_converted_to_source_fact": False,
        },
    }
    record["derived_record_sha256"] = canonical_hash(record)
    return record


def context_trajectory(coordinates: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic per-tensor context movement across T-Time."""
    ordered = _ordered(coordinates)
    by_tensor: dict[str, list[dict[str, Any]]] = {}
    for coordinate in ordered:
        by_tensor.setdefault(coordinate["tensor"], []).append(coordinate)

    segments = []
    for tensor in sorted(by_tensor):
        items = by_tensor[tensor]
        ticks = [item["t_time"] for item in items]
        segments.append(
            {
                "tensor": tensor,
                "coordinate_count": len(items),
                "t_time_first": ticks[0],
                "t_time_last": ticks[-1],
                "t_time_span": ticks[-1] - ticks[0],
                "first_record_id": items[0]["record_id"],
                "last_record_id": items[-1]["record_id"],
            }
        )

    record = {
        "schema_version": "0.1.0",
        "record_type": "rls_context_trajectory",
        "algorithm": {"name": "R1 deterministic context trajectory", "version": TRAJECTORY_VERSION},
        "segments": segments,
        "tensors_observed": sorted(by_tensor),
        "provenance": {
            "source_kind": "tensor_coordinates",
            "context_location_embedded": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
            "inference_converted_to_source_fact": False,
        },
    }
    record["derived_record_sha256"] = canonical_hash(record)
    return record


def recurrence_observations(coordinates: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic recurrence: coordinates sharing a rounded affective signature.

    This observes repetition of an affective shape. It does not claim the records mean the
    same thing, and it does not create a pattern record in any authoritative tensor.
    """
    ordered = _ordered(coordinates)
    groups: dict[str, list[dict[str, Any]]] = {}
    for coordinate in ordered:
        signature = json.dumps([round(value, RECURRENCE_PRECISION) for value in _affect_values(coordinate)], separators=(",", ":"))
        groups.setdefault(signature, []).append(coordinate)

    recurrences = []
    for signature in sorted(groups):
        members = groups[signature]
        if len(members) < 2:
            continue
        recurrences.append(
            {
                "affective_signature": json.loads(signature),
                "occurrence_count": len(members),
                "coordinates": [
                    {"tensor": item["tensor"], "record_id": item["record_id"], "record_hash": item["record_hash"], "t_time": item["t_time"]}
                    for item in members
                ],
                "t_time_first": members[0]["t_time"],
                "t_time_last": members[-1]["t_time"],
            }
        )

    record = {
        "schema_version": "0.1.0",
        "record_type": "rls_recurrence_observation",
        "algorithm": {
            "name": "R1 deterministic recurrence",
            "version": TRAJECTORY_VERSION,
            "signature_precision": RECURRENCE_PRECISION,
        },
        "coordinates_observed": len(ordered),
        "distinct_signatures": len(groups),
        "recurrences": recurrences,
        "provenance": {
            "source_kind": "tensor_coordinates",
            "context_location_embedded": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
            "inference_converted_to_source_fact": False,
        },
    }
    record["derived_record_sha256"] = canonical_hash(record)
    return record
