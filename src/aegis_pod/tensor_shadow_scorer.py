"""R0 shadow scoring for 384x8 DataQuad record tensors.

This module is deliberately additive. It does not replace tensor_runtime.py,
does not write authoritative tensors, and does not infer experience. It builds
record tensors from supplied vectors, scores semantic and affective alignment
separately, and emits coordinate-based derived evidence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
except ImportError:  # Coordinate-only RLS deployment does not require NumPy.
    np = None  # type: ignore[assignment]


SEMANTIC_DIMENSION = 384
AFFECTIVE_DIMENSION = 8
SCORER_VERSION = "r0-shadow-frobenius-v1"


@dataclass(frozen=True)
class Coordinate:
    tensor: str
    record_id: str
    ordinal: int
    t_time: int
    record_hash: str
    tensor_snapshot_hash: str
    semantic_model: str
    semantic_dimension: int
    affective_values: tuple[float, ...]
    affective_provenance: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "tensor": self.tensor,
            "record_id": self.record_id,
            "ordinal": self.ordinal,
            "t_time": self.t_time,
            "record_hash": self.record_hash,
            "tensor_snapshot_hash": self.tensor_snapshot_hash,
            "semantic_coordinate": {"embedding_model": self.semantic_model, "dimension": self.semantic_dimension},
            "affective_coordinate": {
                "values": list(self.affective_values),
                "provenance": list(self.affective_provenance),
            },
        }


@dataclass(frozen=True)
class ShadowRecord:
    coordinate: Coordinate
    semantic_vector: np.ndarray
    affective_vector: np.ndarray
    tensor: np.ndarray


def _unit(vector: np.ndarray) -> np.ndarray:
    if np is None:
        raise RuntimeError("NumPy is required for tensor scoring")
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("zero-length vector cannot be scored")
    return vector / norm


def _sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def deterministic_vector(seed: str, dimension: int = SEMANTIC_DIMENSION) -> np.ndarray:
    """Create a reproducible non-semantic fixture vector; never label it a model embedding."""
    if np is None:
        raise RuntimeError("NumPy is required for deterministic tensor vectors")
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        digest = hashlib.sha256(f"{seed}:{counter}".encode("utf-8")).digest()
        values.extend(((byte / 127.5) - 1.0) for byte in digest)
        counter += 1
    return _unit(np.asarray(values[:dimension], dtype=np.float32))


def build_coordinate(*, tensor: str, record_id: str, ordinal: int, t_time: int, record_hash: str, tensor_snapshot_hash: str, affective_values: Iterable[float], affective_provenance: Iterable[str], semantic_model: str = "deterministic-fixture-hash-v1") -> Coordinate:
    values = tuple(float(value) for value in affective_values)
    provenance = tuple(affective_provenance)
    if len(values) != AFFECTIVE_DIMENSION or len(provenance) != AFFECTIVE_DIMENSION:
        raise ValueError("coordinate affective values and provenance will each have eight dimensions")
    return Coordinate(tensor, record_id, ordinal, t_time, record_hash, tensor_snapshot_hash, semantic_model, SEMANTIC_DIMENSION, values, provenance)


def build_shadow_record(
    *,
    tensor: str,
    record_id: str,
    ordinal: int,
    t_time: int,
    record_hash: str,
    tensor_snapshot_hash: str,
    affective_values: Iterable[float],
    affective_provenance: Iterable[str],
    semantic_vector: Iterable[float] | None = None,
    semantic_model: str = "deterministic-fixture-hash-v1",
) -> ShadowRecord:
    affect = np.asarray(tuple(affective_values), dtype=np.float32)
    provenance = tuple(affective_provenance)
    if affect.shape != (AFFECTIVE_DIMENSION,):
        raise ValueError(f"affective vector will have {AFFECTIVE_DIMENSION} dimensions")
    if len(provenance) != AFFECTIVE_DIMENSION:
        raise ValueError("each affective coordinate will have provenance")
    semantic = deterministic_vector(record_id) if semantic_vector is None else _unit(np.asarray(tuple(semantic_vector), dtype=np.float32))
    if semantic.shape != (SEMANTIC_DIMENSION,):
        raise ValueError(f"semantic vector will have {SEMANTIC_DIMENSION} dimensions")
    coordinate = Coordinate(
        tensor=tensor,
        record_id=record_id,
        ordinal=ordinal,
        t_time=t_time,
        record_hash=record_hash,
        tensor_snapshot_hash=tensor_snapshot_hash,
        semantic_model=semantic_model,
        semantic_dimension=SEMANTIC_DIMENSION,
        affective_values=tuple(float(value) for value in affect),
        affective_provenance=provenance,
    )
    return ShadowRecord(coordinate, semantic, affect, np.einsum("i,j->ij", semantic, affect))


def score_record(record: ShadowRecord, query_semantic: Iterable[float], query_affective: Iterable[float]) -> dict[str, Any]:
    query_s = _unit(np.asarray(tuple(query_semantic), dtype=np.float32))
    query_a = _unit(np.asarray(tuple(query_affective), dtype=np.float32))
    semantic_cosine = float(np.dot(record.semantic_vector, query_s))
    affective_cosine = float(np.dot(_unit(record.affective_vector), query_a))
    frobenius_score = float(np.sum(record.tensor * np.outer(query_s, query_a)) / (np.linalg.norm(record.tensor) * np.linalg.norm(np.outer(query_s, query_a))))
    return {
        "coordinate": record.coordinate.as_dict(),
        "semantic_cosine": round(semantic_cosine, 8),
        "affective_cosine": round(affective_cosine, 8),
        "shadow_score": round(frobenius_score, 8),
        "scoring_policy": SCORER_VERSION,
    }


def rank_records(records: Iterable[ShadowRecord], query_semantic: Iterable[float], query_affective: Iterable[float]) -> list[dict[str, Any]]:
    ranked = [score_record(record, query_semantic, query_affective) for record in records]
    return sorted(ranked, key=lambda item: (-item["shadow_score"], item["coordinate"]["record_id"]))


def build_derived_ledger_record(*, observation_type: str, source_coordinates: list[dict[str, Any]], tensor_snapshot_hashes: dict[str, str], details: dict[str, Any]) -> dict[str, Any]:
    record = {
        "schema_version": "0.1.0",
        "record_type": "rls_derived_coordinate_observation",
        "observation_type": observation_type,
        "algorithm": {"name": "R0 tensor shadow scorer", "version": SCORER_VERSION},
        "source_coordinates": source_coordinates,
        "tensor_snapshot_hashes": tensor_snapshot_hashes,
        "details": details,
        "provenance": {
            "source_kind": "tensor_coordinates",
            "context_location_embedded": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
        },
    }
    record["derived_record_sha256"] = _sha256(record)
    return record


def append_derived_ledger(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
