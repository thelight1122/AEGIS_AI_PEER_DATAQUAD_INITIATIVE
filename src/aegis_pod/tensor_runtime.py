from __future__ import annotations

import argparse
import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TENSOR_NAMES = ("PEER", "PCT", "NCT", "SPINE")
DEFAULT_EMBEDDING_DIMENSION = 8
DEFAULT_METADATA_DIMENSION = 4
FIXTURE_CREATED_UTC = "2026-07-20T21:25:00Z"
DEFAULT_POD_ID = "local-cyberpeer-pod-fixture"
DEFAULT_TENSOR_SPEC_ID = "dataquadpod-core-tensor-spec-0.1.0"
AXIS_DEFINITIONS = [
    {
        "axis": 0,
        "name": "record",
        "function": "Append-only source record position.",
    },
    {
        "axis": 1,
        "name": "embedding",
        "function": "Deterministic numeric vector position.",
    },
    {
        "axis": 2,
        "name": "metadata",
        "function": "Per-vector metadata slot position.",
    },
]
METADATA_SLOTS = [
    {
        "index": 0,
        "name": "embedding_value",
        "function": "Numeric vector value for the embedding axis position.",
    },
    {
        "index": 1,
        "name": "body_length_signal",
        "function": "Normalized size signal derived from stable source body JSON.",
    },
    {
        "index": 2,
        "name": "timestamp_position_signal",
        "function": "Deterministic numeric position signal derived from timestamp hash.",
    },
    {
        "index": 3,
        "name": "verification_signal",
        "function": "Numeric visibility of source record verification state.",
    },
]


@dataclass(frozen=True)
class TensorRecord:
    schema_version: str
    tensor: str
    record_id: str
    source_record_id: str
    timestamp_utc: str
    body: dict[str, Any]
    lineage: dict[str, Any]
    source_hash: str
    source_hash_scope: str
    migration_status: str
    verification_status: str


def stable_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL record") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: record will be a JSON object")
            records.append(value)
    return records


def parse_record(data: dict[str, Any], expected_tensor: str) -> TensorRecord:
    required = [
        "schema_version",
        "tensor",
        "record_id",
        "source_record_id",
        "timestamp_utc",
        "body",
        "lineage",
        "source_hash",
        "source_hash_scope",
        "migration_status",
        "verification_status",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"record missing required fields: {', '.join(missing)}")
    if data["tensor"] != expected_tensor:
        raise ValueError(f"record {data['record_id']} belongs to {data['tensor']}, expected {expected_tensor}")
    if not isinstance(data["body"], dict):
        raise ValueError(f"record {data['record_id']} body will be an object")
    if not isinstance(data["lineage"], dict):
        raise ValueError(f"record {data['record_id']} lineage will be an object")
    lineage_required = ["origin", "source_path", "copy_batch_id", "parent_record_id", "previous_record_hash", "transforms"]
    lineage_missing = [key for key in lineage_required if key not in data["lineage"]]
    if lineage_missing:
        raise ValueError(f"record {data['record_id']} lineage missing required fields: {', '.join(lineage_missing)}")

    return TensorRecord(
        schema_version=str(data["schema_version"]),
        tensor=str(data["tensor"]),
        record_id=str(data["record_id"]),
        source_record_id=str(data["source_record_id"]),
        timestamp_utc=str(data["timestamp_utc"]),
        body=data["body"],
        lineage=data["lineage"],
        source_hash=str(data["source_hash"]),
        source_hash_scope=str(data["source_hash_scope"]),
        migration_status=str(data["migration_status"]),
        verification_status=str(data["verification_status"]),
    )


def verify_source_hash(record_data: dict[str, Any], root: Path) -> dict[str, Any]:
    """Verify a record's declared source_hash against the actual normalized source record.

    The declared scope is normalized_source_record: the hash of the stable JSON of the
    original record at lineage.source_path. When that file is absent from the local
    workspace the hash cannot be verified here - that state is reported as
    unverifiable_source_absent, never as preserved.
    """
    lineage = record_data.get("lineage", {}) if isinstance(record_data.get("lineage"), dict) else {}
    declared = str(record_data.get("source_hash", ""))
    source_path_text = str(lineage.get("source_path", ""))
    source_path = (root / source_path_text) if source_path_text else None
    if source_path is None or not source_path.exists():
        return {
            "source_path": source_path_text,
            "computed_source_hash": "",
            "verification": "unverifiable_source_absent",
            "preserved": None,
        }
    with source_path.open("r", encoding="utf-8") as handle:
        source_data = json.load(handle)
    computed = sha256_text(stable_json(source_data))
    return {
        "source_path": source_path_text,
        "computed_source_hash": computed,
        "verification": "verified" if computed == declared else "mismatch",
        "preserved": computed == declared,
    }


def duplicate_record_ids(records: list[TensorRecord]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        if record.record_id in seen:
            duplicates.add(record.record_id)
        seen.add(record.record_id)
    return sorted(duplicates)


def record_embedding(record: TensorRecord, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> list[float]:
    seed = stable_json({
        "body": record.body,
        "record_id": record.record_id,
        "source_hash": record.source_hash,
        "tensor": record.tensor,
    })
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(dimension):
        raw = digest[index] / 255
        values.append(round(raw, 6))
    return values


def record_metadata(record: TensorRecord) -> list[float]:
    body_text = stable_json(record.body)
    timestamp_hash = int(hashlib.sha256(record.timestamp_utc.encode("utf-8")).hexdigest()[:8], 16)
    status_signal = 1.0 if record.verification_status == "verified" else 0.5 if record.verification_status == "provisional" else 0.0
    migration_signal = 1.0 if record.migration_status in {"fixture", "copied", "mapped", "migrated"} else 0.0
    return [
        round(min(len(body_text) / 1000, 1), 6),
        round((timestamp_hash % 1000) / 1000, 6),
        status_signal,
        migration_signal,
    ]


def compute_tensor(records: list[TensorRecord], tensor_name: str) -> dict[str, Any]:
    values: list[list[list[float]]] = []
    record_index: list[dict[str, Any]] = []

    for record_axis, record in enumerate(records):
        embedding = record_embedding(record)
        metadata = record_metadata(record)
        values.append([[embedding_value, *metadata[: DEFAULT_METADATA_DIMENSION - 1]] for embedding_value in embedding])
        record_index.append({
            "record_axis": record_axis,
            "record_id": record.record_id,
            "source_record_id": record.source_record_id,
            "source_hash": record.source_hash,
            "source_hash_scope": record.source_hash_scope,
            "lineage_origin": str(record.lineage.get("origin", "")),
            "copy_batch_id": str(record.lineage.get("copy_batch_id", "")),
            "previous_record_hash": str(record.lineage.get("previous_record_hash", "")),
        })

    return {
        "schema_version": "0.1.0",
        "pod_id": DEFAULT_POD_ID,
        "tensor_name": tensor_name,
        "tensor_spec_id": DEFAULT_TENSOR_SPEC_ID,
        "source_contract": "tensor-record.schema.json",
        "shape": [len(records), DEFAULT_EMBEDDING_DIMENSION, DEFAULT_METADATA_DIMENSION],
        "dtype": "float32",
        "axis_order": ["record", "embedding", "metadata"],
        "axis_definitions": copy.deepcopy(AXIS_DEFINITIONS),
        "record_count": len(records),
        "embedding_dimension": DEFAULT_EMBEDDING_DIMENSION,
        "metadata_dimension": DEFAULT_METADATA_DIMENSION,
        "metadata_slots": copy.deepcopy(METADATA_SLOTS),
        "values": values,
        "record_index": record_index,
        "evidence": {
            "created_utc": FIXTURE_CREATED_UTC,
            "generator": "src/aegis_pod/tensor_runtime.py",
            "trust_state": "draft",
        },
    }


def add_structural_non_semantic_evidence(tensor: dict[str, Any], batch_id: str, created_utc: str) -> dict[str, Any]:
    tensor["vector_label"] = "structural_vector"
    tensor["embedding_kind"] = "structural-non-semantic"
    tensor["semantic_embedding"] = False
    for axis_definition in tensor.get("axis_definitions", []):
        if axis_definition.get("axis") == 1:
            axis_definition["name"] = "structural-non-semantic-vector"
            axis_definition["function"] = "Deterministic structural vector position; embedding_kind=structural-non-semantic."
    tensor["evidence"] = {
        **tensor["evidence"],
        "created_utc": created_utc,
        "generator": "src/aegis_pod/live_structural_vectors.py",
        "source_batch_id": batch_id,
        "vector_label": "structural_vector",
        "embedding_kind": "structural-non-semantic",
        "semantic_embedding": False,
        "label_guard": "Deterministic structural vectors; embedding_kind=structural-non-semantic.",
    }
    return tensor


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_tensor_from_file(source_path: Path, output_path: Path, tensor_name: str) -> dict[str, Any]:
    raw_records = load_jsonl(source_path)
    records = [parse_record(data, tensor_name) for data in raw_records]
    duplicates = duplicate_record_ids(records)
    if duplicates:
        raise ValueError(f"{tensor_name}: duplicate record ids detected: {', '.join(duplicates)}")
    tensor = compute_tensor(records, tensor_name)
    write_json(output_path, tensor)
    return tensor


def run_fixture_build(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    source_root = root / "fixtures" / "tensor-records"
    output_root = output_root or root / "reports" / "runtime" / "tensors"
    output_root.mkdir(parents=True, exist_ok=True)

    tensors: dict[str, Any] = {}
    health_tensors: dict[str, Any] = {}

    for tensor_name in TENSOR_NAMES:
        source_path = source_root / f"{tensor_name}.jsonl"
        output_path = output_root / f"{tensor_name}.tensor.json"
        tensor = build_tensor_from_file(source_path, output_path, tensor_name)
        output_hash = sha256_text(output_path.read_text(encoding="utf-8"))
        tensors[tensor_name] = tensor
        health_tensors[tensor_name] = {
            "source_path": display_path(source_path, root),
            "output_path": display_path(output_path, root),
            "record_count": tensor["record_count"],
            "shape": tensor["shape"],
            "dtype": tensor["dtype"],
            "output_sha256": output_hash,
        }

    health_report = {
        "schema_version": "0.1.0",
        "created_utc": FIXTURE_CREATED_UTC,
        "runtime": "src/aegis_pod/tensor_runtime.py",
        "scope": "local fixture records only",
        "live_reach": False,
        "tensors": health_tensors,
    }
    health_path = output_root.parent / "tensor-health.json"
    write_json(health_path, health_report)
    return health_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local fixture mathematical tensors.")
    parser.add_argument("--root", default=".", help="Workspace root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    health_report = run_fixture_build(root)
    print("PASS mathematical tensors computed from local fixture source records")
    print(f"ROOT {root}")
    print("BOUNDARY local fixture records only; no live DataQuad roots referenced")
    for tensor_name, tensor in health_report["tensors"].items():
        print(f"TENSOR {tensor_name} shape={tensor['shape']} dtype={tensor['dtype']} records={tensor['record_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
