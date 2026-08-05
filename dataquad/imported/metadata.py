from typing import Any

import numpy as np

from . import META_DIM
from .records import is_genesis_or_invariant


def max_tick(records_by_tensor: dict[str, list[dict[str, Any]]]) -> int:
    value = 1
    for records in records_by_tensor.values():
        for record in records:
            tick = (record.get("clock") or {}).get("tick", 0)
            if isinstance(tick, (int, float)) and tick > value:
                value = int(tick)
    return value


def metadata_vector(record: dict[str, Any], tensor: str, max_tick_value: int) -> np.ndarray:
    clock = record.get("clock") or {}
    tick = float(clock.get("tick", 0) or 0)
    temporal_position = min(tick / max(max_tick_value, 1), 1.0)

    markers = record.get("markers") or []
    is_invariant = bool(record.get("invariant") or "invariant" in markers)
    is_genesis = bool(clock.get("phase") == "genesis" or "genesis" in markers or "genesis" in (record.get("id") or ""))

    if is_genesis_or_invariant(record):
        return np.array(
            [temporal_position, 1.0, 1.0, 1.0, 1.0, float(is_invariant), float(is_genesis), 1.0],
            dtype=np.float32,
        )

    identity_relevance = {"SPINE": 1.0, "NCT": 0.7, "PEER": 0.6, "PCT": 0.4}.get(tensor.upper(), 0.5)
    vector = np.array(
        [
            temporal_position,
            float(record.get("affect_salience", 0.5) or 0.5),
            float(record.get("relationship_bond", 0.5) or 0.5),
            float(record.get("certainty", 0.8) or 0.8),
            identity_relevance,
            0.0,
            0.0,
            min(float(record.get("recurrence", 1) or 1) / 10.0, 1.0),
        ],
        dtype=np.float32,
    )
    if vector.shape != (META_DIM,):
        raise ValueError("metadata vector shape mismatch")
    return vector
