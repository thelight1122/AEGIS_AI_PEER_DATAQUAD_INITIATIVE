import hashlib
import json
from pathlib import Path

import jsonschema
import numpy as np

from aegis_pod.tensor_shadow_scorer import (
    AFFECTIVE_DIMENSION,
    SEMANTIC_DIMENSION,
    append_derived_ledger,
    build_derived_ledger_record,
    build_shadow_record,
    rank_records,
)


ROOT = Path(__file__).resolve().parents[1]


def _vector(index: int, value: float = 1.0) -> list[float]:
    result = [0.0] * SEMANTIC_DIMENSION
    result[index] = value
    return result


def _combined(first: tuple[int, float], second: tuple[int, float]) -> list[float]:
    result = [0.0] * SEMANTIC_DIMENSION
    result[first[0]] = first[1]
    result[second[0]] = second[1]
    return result


def _coordinate(record_id: str, ordinal: int) -> dict:
    return build_shadow_record(
        tensor="PEER",
        record_id=record_id,
        ordinal=ordinal,
        t_time=ordinal,
        record_hash=("A" if ordinal == 0 else "B") * 64,
        tensor_snapshot_hash="C" * 64,
        affective_values=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        affective_provenance=["source-derived"] * AFFECTIVE_DIMENSION,
        semantic_vector=_vector(0),
        semantic_model="controlled-test-vector-v1",
    )


def test_shadow_score_preserves_affective_axis_and_changes_ranking():
    semantic_query = _vector(0)
    affective_query = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    semantic_aligned_affect_misaligned = build_shadow_record(
        tensor="PEER", record_id="PEER:A", ordinal=0, t_time=10,
        record_hash="A" * 64, tensor_snapshot_hash="C" * 64,
        affective_values=[0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        affective_provenance=["source-derived"] * 8,
        semantic_vector=_vector(0), semantic_model="controlled-test-vector-v1",
    )
    semantic_near_affect_aligned = build_shadow_record(
        tensor="PEER", record_id="PEER:B", ordinal=1, t_time=11,
        record_hash="B" * 64, tensor_snapshot_hash="C" * 64,
        affective_values=affective_query,
        affective_provenance=["policy-assigned"] * 8,
        semantic_vector=_combined((0, 0.95), (1, 0.3122499)), semantic_model="controlled-test-vector-v1",
    )
    ranked = rank_records([semantic_aligned_affect_misaligned, semantic_near_affect_aligned], semantic_query, affective_query)
    assert ranked[0]["coordinate"]["record_id"] == "PEER:B"
    assert ranked[0]["affective_cosine"] > ranked[1]["affective_cosine"]
    assert ranked[0]["shadow_score"] > ranked[1]["shadow_score"]


def test_coordinate_and_derived_ledger_contracts_validate(tmp_path: Path):
    record = _coordinate("PEER:fixture", 0)
    ledger = build_derived_ledger_record(
        observation_type="shadow_rank",
        source_coordinates=[record.coordinate.as_dict()],
        tensor_snapshot_hashes={"PEER": "C" * 64},
        details={"score": 0.5},
    )
    coordinate_schema = json.loads((ROOT / "contracts" / "tensor-coordinate.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(record.coordinate.as_dict(), coordinate_schema)
    ledger_schema = json.loads((ROOT / "contracts" / "rls-derived-ledger-record.schema.json").read_text(encoding="utf-8"))
    resolver = jsonschema.RefResolver("https://aegis.local/schemas/rls-derived-ledger-record.schema.json", ledger_schema, store={"https://aegis.local/schemas/tensor-coordinate.schema.json": coordinate_schema})
    jsonschema.validate(ledger, ledger_schema, resolver=resolver)
    append_derived_ledger(tmp_path / "rls-derived.jsonl", ledger)
    text = (tmp_path / "rls-derived.jsonl").read_text(encoding="utf-8")
    assert "source_path" not in text
    assert '"context_location_embedded":false' in text


def test_record_tensor_shape():
    record = _coordinate("PEER:fixture", 0)
    assert record.tensor.shape == (SEMANTIC_DIMENSION, AFFECTIVE_DIMENSION)
