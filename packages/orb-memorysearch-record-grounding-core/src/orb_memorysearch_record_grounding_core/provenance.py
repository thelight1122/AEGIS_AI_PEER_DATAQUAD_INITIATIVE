from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .orb_evidence import ORB_ID, compute_runtime_hash


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_search_event(query: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "record_search_performed": bool(result["record_search_performed"]),
        "search_trigger": query["search_trigger"],
        "claim_class": query["claim_class"],
        "query_text": query["message"],
        "search_scope": query["search_scope"],
        "result_count": len(result["results"]),
        "selected_record_ids": result["selected_record_ids"],
        "selected_record_hashes": result["selected_record_hashes"],
        "orb_id": ORB_ID,
        "orb_runtime_hash": compute_runtime_hash(),
        "grounding_status": result["grounding_status"],
        "match_confidence": result["match_confidence"],
    }
