from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CORE_REPO_ROOT = Path(r"I:\AEGIS-CYBERPEER-CORE")
if str(CORE_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_REPO_ROOT))

from core.dataquad.records import PEERRecord, PCTRecord, NCTRecord, SPINERecord  # noqa: E402
from core.dataquad import pod as _pod  # noqa: E402

from src.aegis_pod.tensor_runtime import TENSOR_NAMES, load_jsonl, sha256_text, stable_json, write_json  # noqa: E402


LEGACY_LIVE_PEER_ID = "cyberpeer-gabe-session"
MODEL_BY_TENSOR = {
    "PEER": PEERRecord,
    "PCT": PCTRecord,
    "NCT": NCTRecord,
    "SPINE": SPINERecord,
}
# Fields consumed explicitly by the normalizer per tensor; anything else in the
# raw record is preserved verbatim in `legacy_extra_fields` rather than dropped.
CONSUMED_COMMON = {"id", "timestamp", "tensor", "sessionId", "clock", "provenance", "markers", "notes"}
CONSUMED_BY_TENSOR = {
    "PEER": CONSUMED_COMMON | {"presentState"},
    "PCT": CONSUMED_COMMON | {"workingContext"},
    "NCT": CONSUMED_COMMON | {"distilledSummary"},
    "SPINE": CONSUMED_COMMON | {"pattern", "invariant"},
}


def normalize_clock(raw_clock: dict[str, Any] | None, timestamp: str) -> dict[str, Any]:
    raw_clock = raw_clock or {}
    return {
        "tick": int(raw_clock.get("tick", 0)),
        "epoch": "primary",
        "phase": str(raw_clock.get("phase", "active" if raw_clock else "genesis")),
        "started_at": timestamp,
        "last_advanced_at": timestamp,
    }


def normalize_provenance(raw_provenance: dict[str, Any] | None) -> dict[str, Any]:
    raw_provenance = raw_provenance or {}
    origin = str(raw_provenance.get("origin", "gabe-legacy-unspecified"))
    return {"origin": origin}


def legacy_extra_fields(raw: dict[str, Any], tensor: str) -> dict[str, Any]:
    consumed = CONSUMED_BY_TENSOR[tensor]
    return {key: value for key, value in raw.items() if key not in consumed}


def normalize_record(raw: dict[str, Any], tensor: str) -> dict[str, Any]:
    timestamp = str(raw["timestamp"])
    normalized: dict[str, Any] = {
        "id": str(raw["id"]),
        "timestamp": timestamp,
        "tensor": tensor,
        "session_id": str(raw.get("sessionId") or LEGACY_LIVE_PEER_ID),
        "clock": normalize_clock(raw.get("clock"), timestamp),
        "provenance": normalize_provenance(raw.get("provenance")),
        "lineage": [],
        "markers": raw.get("markers"),
        "notes": raw.get("notes"),
    }

    extra = legacy_extra_fields(raw, tensor)
    if extra:
        extra_note = "legacy_extra_fields=" + stable_json(extra)
        notes = normalized["notes"] if isinstance(normalized["notes"], list) else []
        normalized["notes"] = [*notes, extra_note]

    if tensor == "PEER":
        normalized["present_state"] = raw.get("presentState") or {}
        normalized["image_refs"] = []
    elif tensor == "PCT":
        normalized["working_context"] = raw.get("workingContext") or {}
        normalized["retrieved_record_ids"] = None
        normalized["rls_session_id"] = None
        normalized["pressure_state"] = None
    elif tensor == "NCT":
        normalized["distilled_summary"] = str(raw.get("distilledSummary") or "")
        normalized["essence_memory"] = None
        normalized["pivots"] = None
        normalized["source_record_ids"] = []
    elif tensor == "SPINE":
        normalized["pattern"] = str(raw.get("pattern") or "")
        normalized["invariant"] = raw.get("invariant")
        normalized["relationships"] = None
        normalized["source_record_ids"] = None
        normalized["nature_aspect_refs"] = None

    return normalized


def wrap_normalized(
    normalized_body: dict[str, Any],
    tensor: str,
    record_id: str,
    raw_source_hash: str,
    raw_source_path: str,
    previous_normalized_hash: str,
    batch_id: str,
) -> dict[str, Any]:
    normalized_hash = sha256_text(stable_json(normalized_body)).upper()
    return {
        "schema_version": _pod.POD_SCHEMA_VERSION,
        "tensor": tensor,
        "record_id": record_id,
        "source_record_id": record_id,
        "timestamp_utc": str(normalized_body["timestamp"]),
        "body": normalized_body,
        "lineage": {
            "origin": "gabe-legacy-to-core-normalize",
            "source_path": raw_source_path,
            "copy_batch_id": batch_id,
            "parent_record_id": "",
            "previous_record_hash": previous_normalized_hash,
            "transforms": [
                {
                    "transform_id": "gabe-legacy-to-core-field-normalize",
                    "function": (
                        "camelCase legacy field mapping (sessionId->session_id, presentState->present_state, "
                        "workingContext->working_context, distilledSummary->distilled_summary) plus synthesized "
                        "ContinuityClock (started_at/last_advanced_at derived from record timestamp) and "
                        "Provenance.origin extraction, for Core Pydantic schema compatibility. Unmapped legacy "
                        "fields preserved verbatim in body.notes as a JSON note, not dropped."
                    ),
                    "input_hash": raw_source_hash,
                    "output_hash": normalized_hash,
                }
            ],
        },
        "source_hash": normalized_hash,
        "source_hash_scope": "normalized_source_record",
        "migration_status": "migrated",
        "verification_status": "draft",
    }


def normalize_tensor(
    root: Path,
    mapped_path: Path,
    output_path: Path,
    tensor: str,
    batch_id: str,
) -> dict[str, Any]:
    model = MODEL_BY_TENSOR[tensor]
    mapped_records = load_jsonl(mapped_path)
    normalized_records: list[dict[str, Any]] = []
    validation_errors: list[dict[str, str]] = []
    previous_normalized_hash = ""

    for mapped in mapped_records:
        raw = mapped["body"]
        record_id = mapped["record_id"]
        raw_source_hash = mapped["source_hash"]
        raw_source_path = mapped["lineage"]["source_path"]

        normalized_body = normalize_record(raw, tensor)
        try:
            model.model_validate(normalized_body)
        except Exception as exc:  # noqa: BLE001
            validation_errors.append({"record_id": record_id, "reason": str(exc)})
            continue

        wrapped = wrap_normalized(
            normalized_body, tensor, record_id, raw_source_hash, raw_source_path,
            previous_normalized_hash, batch_id,
        )
        previous_normalized_hash = wrapped["source_hash"]
        normalized_records.append(wrapped)

    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for r in normalized_records]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    return {
        "tensor": tensor,
        "mapped_input_count": len(mapped_records),
        "normalized_output_count": len(normalized_records),
        "validation_errors": validation_errors,
        "output_path": str(output_path),
    }


def run(root: Path, batch_id: str) -> dict[str, Any]:
    pod_root = root / "stage-gabe-out" / "CP-1003-GABE" / "pod"
    mapped_root = pod_root / "records"
    normalized_root = pod_root / "records-core-normalized"

    results: dict[str, Any] = {}
    for tensor in TENSOR_NAMES:
        result = normalize_tensor(
            root,
            mapped_root / f"{tensor}.jsonl",
            normalized_root / f"{tensor}.jsonl",
            tensor,
            batch_id,
        )
        results[tensor] = result

    report = {
        "stage": "Gabe Phase 5 corrective substep: legacy-to-Core field normalization",
        "batch_id": batch_id,
        "raw_evidence_preserved_at": str(root / "stage-gabe-out" / "live-copies" / "CP-1003-GABE" / batch_id / "raw"),
        "mapped_evidence_preserved_at": str(mapped_root),
        "normalized_output_root": str(normalized_root),
        "per_tensor": results,
        "total_mapped": sum(r["mapped_input_count"] for r in results.values()),
        "total_normalized": sum(r["normalized_output_count"] for r in results.values()),
        "total_validation_errors": sum(len(r["validation_errors"]) for r in results.values()),
    }
    write_json(root / "reports" / "runtime" / "2026-07-22-gabe-phase5-core-normalization-report.json", report)
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize Gabe's legacy-shaped mapped records into Core-Pydantic-valid records.")
    parser.add_argument("--root", default=".", help="Workspace root")
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    report = run(Path(args.root).resolve(), args.batch_id)
    print(f"total_mapped={report['total_mapped']} total_normalized={report['total_normalized']} total_validation_errors={report['total_validation_errors']}")
    for tensor, result in report["per_tensor"].items():
        print(f"{tensor}: mapped={result['mapped_input_count']} normalized={result['normalized_output_count']} errors={len(result['validation_errors'])}")
