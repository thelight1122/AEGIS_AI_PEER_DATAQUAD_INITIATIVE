"""Read-only local RLS Orb over coordinate-bearing fixture tensors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .tensor_runtime import TENSOR_NAMES, load_jsonl, parse_record
from .tensor_shadow_scorer import build_coordinate


RLS_ORB_VERSION = "r0-coordinate-index-v1"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _policy_affect(record: Any) -> tuple[list[float], list[str]]:
    explicit = record.body.get("affective_coordinates")
    if isinstance(explicit, list) and len(explicit) == 8:
        return [float(item) for item in explicit], ["source-derived"] * 8
    tensor_defaults = {"SPINE": 1.0, "NCT": 0.7, "PEER": 0.6, "PCT": 0.4}
    values = [0.0] * 8
    values[0] = 0.0
    values[3] = tensor_defaults.get(record.tensor, 0.0)
    values[4] = tensor_defaults.get(record.tensor, 0.0)
    return values, ["policy-assigned"] * 8


def _normalize_snapshot_record(data: dict[str, Any], tensor: str, ordinal: int) -> Any:
    """Normalize the live post-Genesis envelope without rewriting its source."""
    if all(key in data for key in ("schema_version", "record_id", "body", "lineage", "source_hash")):
        return parse_record(data, tensor)
    record_id = str(data.get("id", ""))
    if not record_id:
        raise ValueError(f"{tensor} snapshot record has no id")
    clock = data.get("clock") if isinstance(data.get("clock"), dict) else {}
    body = dict(data.get("body") or {})
    if not body:
        body = {key: value for key, value in data.items() if key not in {"id", "tensor", "clock"}}
    lineage = {
        "origin": "immutable post-Genesis snapshot",
        "source_path": "",
        "copy_batch_id": "phase3a-post-genesis",
        "parent_record_id": "",
        "previous_record_hash": "",
        "transforms": [],
    }
    source_hash = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()
    return SimpleNamespace(
        schema_version="live-snapshot-1",
        tensor=tensor,
        record_id=record_id,
        source_record_id=record_id,
        timestamp_utc=str(data.get("timestamp", clock.get("advancedAt", ""))),
        body=body,
        lineage=lineage,
        source_hash=source_hash,
        source_hash_scope="live_snapshot_record",
        migration_status="copied",
        verification_status="verified",
    )


class RLSOrb:
    """Indexes tensor coordinates and emits derived observations only."""

    def __init__(self, root: Path, *, source_root: Path | None = None) -> None:
        self.root = root
        self.source_root = source_root or (root / "fixtures" / "tensor-records")
        self.coordinates: list[dict[str, Any]] = []
        self._records: dict[str, Any] = {}
        self.snapshot_hashes: dict[str, str] = {}

    def build_index(self) -> dict[str, Any]:
        source_root = self.source_root
        for tensor_name in TENSOR_NAMES:
            source_path = source_root / f"{tensor_name}.jsonl"
            self.snapshot_hashes[tensor_name] = _file_hash(source_path)
            raw = load_jsonl(source_path)
            for ordinal, data in enumerate(raw):
                record = _normalize_snapshot_record(data, tensor_name, ordinal)
                affect, provenance = _policy_affect(record)
                coordinate = build_coordinate(
                    tensor=tensor_name,
                    record_id=record.record_id,
                    ordinal=ordinal,
                    t_time=int((data.get("clock") or {}).get("tick", record.body.get("t_time", ordinal))),
                    record_hash=record.source_hash,
                    tensor_snapshot_hash=self.snapshot_hashes[tensor_name],
                    affective_values=affect,
                    affective_provenance=provenance,
                    semantic_model="deterministic-fixture-hash-v1",
                )
                self._records[record.record_id] = record
                self.coordinates.append(coordinate.as_dict())
        self.coordinates.sort(key=lambda item: (item["t_time"], item["tensor"], item["ordinal"], item["record_id"]))
        return self.status()

    def status(self) -> dict[str, Any]:
        return {
            "orb_id": "rls-coordinate-orb",
            "version": RLS_ORB_VERSION,
            "record_count": len(self.coordinates),
            "tensor_counts": {tensor: sum(item["tensor"] == tensor for item in self.coordinates) for tensor in TENSOR_NAMES},
            "snapshot_hashes": dict(self.snapshot_hashes),
            "writes": {"authoritative_tensors": False, "derived_ledgers": True},
            "experience_created": False,
            "admission_performed": False,
        }

    def timeline(self, *, tensor: str | None = None, t_from: int = 0, t_to: int | None = None) -> dict[str, Any]:
        selected = [item for item in self.coordinates if (tensor is None or item["tensor"] == tensor) and item["t_time"] >= t_from and (t_to is None or item["t_time"] <= t_to)]
        return {"tick_range": {"from": t_from, "to": t_to}, "coordinates": selected, "source_snapshot_hashes": dict(self.snapshot_hashes)}

    def cross_tensor_lineage(self, record_id: str) -> dict[str, Any]:
        record = self._records.get(record_id)
        if record is None:
            return {"record_id": record_id, "relations": [], "relation_basis": "no_record"}
        parent = str(record.lineage.get("parent_record_id", ""))
        relations = []
        if parent and parent in self._records:
            relations.append({"relation": "explicit_parent", "from_record_id": record_id, "to_record_id": parent})
        return {"record_id": record_id, "relations": relations, "relation_basis": "explicit_lineage_only"}

    def reflection_packet(self, *, tensor: str | None = None, t_from: int = 0, t_to: int | None = None) -> dict[str, Any]:
        timeline = self.timeline(tensor=tensor, t_from=t_from, t_to=t_to)
        packet = {
            "schema_version": "0.1.0",
            "packet_type": "rls_structural_reflection_packet",
            "orb_version": RLS_ORB_VERSION,
            "current_context": timeline["coordinates"][-5:],
            "relevant_origins": timeline["coordinates"][:5],
            "affect_trajectory": [{"t_time": item["t_time"], "coordinate": item["affective_coordinate"]} for item in timeline["coordinates"]],
            "cross_tensor_lineage": [self.cross_tensor_lineage(item["record_id"]) for item in timeline["coordinates"]],
            "recurring_patterns": [],
            "drift_observations": [],
            "repairs_and_integrations": [],
            "open_questions": [],
            "source_coordinates": timeline["coordinates"],
            "tick_range": timeline["tick_range"],
            "source_snapshot_hashes": timeline["source_snapshot_hashes"],
            "provenance": {"interpretation": "structural_only", "model_inference": False, "experience_created": False, "admission_performed": False},
        }
        packet["packet_sha256"] = hashlib.sha256(json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest().upper()
        return packet
