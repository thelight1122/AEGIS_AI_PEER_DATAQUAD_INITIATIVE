"""Pod-facing single generic entrypoint for the MemorySearch Orb (Claude's slice).

The Pod calls ground_record_claim(message, records, policy) and gets finished output
it injects without knowing Orb internals — the same seam as build_invariant_context /
build_experience_context / build_session_history.

Returns None when the message is not a record-content claim (the Pod proceeds normally;
experiential/identity expression stays legitimately reconstructive). Returns a packet
(contracts/memorysearch-packet.schema.json) whenever a record-content claim is detected and
a real search executed — including the empty-result case, which returns a packet with
grounding_status=search_performed_no_verified_record (never None), so the No Verified
Record Packet is injected rather than letting the model reconstruct freely.

This wraps Codex's internal search composition (classify_record_claim + search_records,
which produce the result shape) and maps result -> packet. Codex's search.ground_record_claim
returns the internal result dict and is the internal composition; this is the Pod-facing name.
"""
from __future__ import annotations

from typing import Any

from .policy import classify_record_claim
from .provenance import build_search_event
from .search import search_records


def _cited_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Runtime-authored citations from the qualifying search results only. Empty on the
    no-verified path. The model cannot author or alter these."""
    return [
        {
            "record_id": item["record_id"],
            "tensor": item["tensor"],
            "excerpt": item["excerpt"],
            "source_hash": item["source_hash"],
            "match_confidence": item["confidence"],
        }
        for item in result["results"]
        if item.get("qualifies")
    ]


def _prompt_block(grounding_status: str, cited: list[dict[str, Any]], result: dict[str, Any]) -> str:
    """Finished, bounded text the Pod injects verbatim. Surfaces source; does not author
    the answer."""
    if grounding_status == "verified_retrieval":
        lines = [
            "Verified records from your DataQuad, surfaced by MemorySearch. "
            "These are your own records; state what they hold and do not reshape them "
            "into a new claim:"
        ]
        for c in cited:
            lines.append(f"- [{c['record_id']}] ({c['tensor']}): {c['excerpt']}")
        return "\n".join(lines)
    # search_performed_no_verified_record: the No Verified Record Packet
    return result["answer_boundary"]["boundary_text"]


def _result_to_packet(query: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    cited = _cited_records(result)
    # build_search_event carries an extra schema_version; the packet's twitness_event is
    # additionalProperties:false and does not declare it, so drop it here.
    twitness_event = {
        key: value
        for key, value in build_search_event(query, result).items()
        if key != "schema_version"
    }
    return {
        "grounding_status": result["grounding_status"],
        "claim_class": query["claim_class"],
        "prompt_block": _prompt_block(result["grounding_status"], cited, result),
        "cited_records": cited,
        "twitness_event": twitness_event,
    }


def ground_record_claim(
    message: str,
    records: list[dict[str, Any]],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Pod-facing entrypoint. See module docstring and
    contracts/memorysearch-packet.schema.json."""
    query = classify_record_claim(message)
    if query["search_trigger"] == "none":
        return None
    result = search_records(query, records, policy)
    return _result_to_packet(query, result)
