"""R1 deterministic trajectory and coordinate provenance behaviour.

These tests plant the conditions they claim to detect. A recurrence test over coordinates
with no repeated signature proves nothing, so the fixtures here deliberately contain a
repeated affective signature and an explicit lineage relation.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from aegis_pod.rls_trajectories import (
    AFFECTIVE_DIMENSION,
    AFFECTIVE_DIMENSION_NAMES,
    affect_trajectory,
    build_coordinate_provenance,
    build_dimension_provenance,
    context_trajectory,
    recurrence_observations,
)

ROOT = Path(__file__).resolve().parents[1]


def _coordinate(record_id: str, tensor: str, ordinal: int, t_time: int, affect: list[float]) -> dict:
    return {
        "tensor": tensor,
        "record_id": record_id,
        "ordinal": ordinal,
        "t_time": t_time,
        "record_hash": f"{ordinal:064X}",
        "tensor_snapshot_hash": "C" * 64,
        "semantic_coordinate": {"embedding_model": "controlled-test-vector-v1", "dimension": 384},
        "affective_coordinate": {
            "values": affect,
            "provenance": ["source-derived"] * AFFECTIVE_DIMENSION,
        },
    }


def _planted_coordinates() -> list[dict]:
    """Three distinct signatures, one of which occurs twice. Recurrence must find exactly one."""
    repeated = [0.5, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    return [
        _coordinate("PEER:a", "PEER", 0, 10, list(repeated)),
        _coordinate("PCT:b", "PCT", 1, 11, [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
        _coordinate("NCT:c", "NCT", 2, 12, list(repeated)),
        _coordinate("SPINE:d", "SPINE", 3, 13, [0.2, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]),
    ]


# --- Determinism ----------------------------------------------------------------------


@pytest.mark.parametrize("builder", [affect_trajectory, context_trajectory, recurrence_observations])
def test_trajectory_records_are_byte_identical_across_runs(builder):
    coordinates = _planted_coordinates()
    first = builder(coordinates)
    second = builder(coordinates)
    assert first["derived_record_sha256"] == second["derived_record_sha256"]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_trajectory_output_does_not_depend_on_input_ordering():
    coordinates = _planted_coordinates()
    shuffled = [coordinates[2], coordinates[0], coordinates[3], coordinates[1]]
    assert affect_trajectory(coordinates)["derived_record_sha256"] == affect_trajectory(shuffled)["derived_record_sha256"]


# --- Affect trajectory ----------------------------------------------------------------


def test_affect_trajectory_reports_a_step_between_each_consecutive_pair():
    coordinates = _planted_coordinates()
    record = affect_trajectory(coordinates)
    assert len(record["steps"]) == len(coordinates) - 1
    assert record["steps"][0]["t_time_from"] == 10
    assert record["steps"][0]["t_time_to"] == 11
    assert record["total_path_length"] > 0


def test_affect_trajectory_names_the_dimension_that_moved_most():
    a = _coordinate("PEER:a", "PEER", 0, 1, [0.0] * AFFECTIVE_DIMENSION)
    b = _coordinate("PEER:b", "PEER", 1, 2, [0.0, 0.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0])
    step = affect_trajectory([a, b])["steps"][0]
    assert step["largest_movement_dimension"] == "relationship_bond"
    assert step["largest_movement_value"] == pytest.approx(0.9)


# --- Recurrence, with the recurrence planted -------------------------------------------


def test_recurrence_detects_the_planted_repeated_signature():
    record = recurrence_observations(_planted_coordinates())
    assert record["distinct_signatures"] == 3
    assert len(record["recurrences"]) == 1
    found = record["recurrences"][0]
    assert found["occurrence_count"] == 2
    assert {item["record_id"] for item in found["coordinates"]} == {"PEER:a", "NCT:c"}


def test_recurrence_reports_nothing_when_every_signature_is_unique():
    unique = [
        _coordinate(f"PEER:{i}", "PEER", i, i, [i * 0.1] + [0.0] * (AFFECTIVE_DIMENSION - 1))
        for i in range(1, 5)
    ]
    record = recurrence_observations(unique)
    assert record["recurrences"] == []
    assert record["distinct_signatures"] == 4


# --- Context trajectory ---------------------------------------------------------------


def test_context_trajectory_segments_by_tensor():
    record = context_trajectory(_planted_coordinates())
    assert record["tensors_observed"] == ["NCT", "PCT", "PEER", "SPINE"]
    assert all(segment["coordinate_count"] == 1 for segment in record["segments"])


# --- Provenance -----------------------------------------------------------------------


def _provenance_schema() -> dict:
    return json.loads((ROOT / "contracts" / "coordinate-provenance.schema.json").read_text(encoding="utf-8"))


def _dimensions() -> list[dict]:
    return [
        build_dimension_provenance(dimension=0, value=1.0, origin="source-derived", source_field="clock.tick"),
        build_dimension_provenance(dimension=1, value=0.5, origin="tensorization-policy-assigned", policy="p", policy_version="v1"),
        build_dimension_provenance(
            dimension=2,
            value=0.3,
            origin="rls-derived",
            derivation="mean relationship bond over window",
            derived_from_coordinates=[{"tensor": "PEER", "record_id": "PEER:a", "record_hash": "A" * 64}],
        ),
        build_dimension_provenance(dimension=3, value=0.2, origin="steward-declared", declared_by="Steward", declared_utc="2026-08-06T00:00:00Z"),
    ] + [
        build_dimension_provenance(dimension=index, value=0.0, origin="tensorization-policy-assigned", policy="p", policy_version="v1")
        for index in range(4, AFFECTIVE_DIMENSION)
    ]


def test_provenance_record_validates_against_its_contract():
    record = build_coordinate_provenance(
        tensor="PEER", record_id="PEER:a", record_hash="A" * 64, tensor_snapshot_hash="C" * 64, dimensions=_dimensions()
    )
    jsonschema.validate(record, _provenance_schema())


def test_only_source_derived_dimensions_are_asserted_as_source_fact():
    for entry in _dimensions():
        assert entry["asserted_as_source_fact"] is (entry["origin"] == "source-derived")


def test_schema_rejects_a_policy_assigned_dimension_claimed_as_source_fact():
    record = build_coordinate_provenance(
        tensor="PEER", record_id="PEER:a", record_hash="A" * 64, tensor_snapshot_hash="C" * 64, dimensions=_dimensions()
    )
    record["dimensions"][1]["asserted_as_source_fact"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(record, _provenance_schema())


@pytest.mark.parametrize(
    "origin,kwargs",
    [
        ("source-derived", {}),
        ("tensorization-policy-assigned", {}),
        ("rls-derived", {"derivation": "x"}),
        ("steward-declared", {"declared_by": "Steward"}),
    ],
)
def test_builder_refuses_a_dimension_missing_its_required_provenance(origin, kwargs):
    with pytest.raises(ValueError):
        build_dimension_provenance(dimension=0, value=1.0, origin=origin, **kwargs)


def test_locator_is_optional_and_identity_lives_in_coordinate_ref():
    without = build_coordinate_provenance(
        tensor="PEER", record_id="PEER:a", record_hash="A" * 64, tensor_snapshot_hash="C" * 64, dimensions=_dimensions()
    )
    assert "locator" not in without
    with_locator = build_coordinate_provenance(
        tensor="PEER",
        record_id="PEER:a",
        record_hash="A" * 64,
        tensor_snapshot_hash="C" * 64,
        dimensions=_dimensions(),
        locator={"kind": "filesystem", "value": "fixtures/tensor-records/PEER.jsonl", "observed_utc": "2026-08-06T00:00:00Z", "digest_confirmed": False},
    )
    jsonschema.validate(with_locator, _provenance_schema())
    # Identity is unchanged by the presence or absence of a locator.
    assert without["coordinate_ref"] == with_locator["coordinate_ref"]


def test_dimension_names_follow_sssp_section_6_1_order():
    assert AFFECTIVE_DIMENSION_NAMES[5] == "invariant_flag"
    assert AFFECTIVE_DIMENSION_NAMES[6] == "genesis_flag"
    assert len(AFFECTIVE_DIMENSION_NAMES) == AFFECTIVE_DIMENSION
