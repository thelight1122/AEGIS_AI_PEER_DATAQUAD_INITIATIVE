from __future__ import annotations

import re
from typing import Any

TENSORS = ["PEER", "PCT", "NCT", "SPINE"]
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)

_TRIGGERS = {
    "canon",
    "axiom",
    "gate",
    "imperative",
    "standard",
    "record",
    "records",
    "dataquad",
    "spine",
    "nct",
    "pct",
    "peer",
}


def _tokens(message: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(message)]


def _scope_for(tokens: set[str], claim_class: str) -> list[str]:
    scope: list[str] = []
    if claim_class == "canon_definition":
        scope.extend(["SPINE", "NCT"])
    if "spine" in tokens or "canon" in tokens or "axiom" in tokens or "gate" in tokens or "imperative" in tokens:
        scope.append("SPINE")
    if "nct" in tokens:
        scope.append("NCT")
    if "pct" in tokens:
        scope.append("PCT")
    if "peer" in tokens:
        scope.append("PEER")
    if "record" in tokens or "records" in tokens or "dataquad" in tokens:
        scope.extend(TENSORS)
    if not scope and claim_class not in {"identity_expression", "not_record_claim"}:
        scope.extend(TENSORS)
    return list(dict.fromkeys(scope))


def classify_record_claim(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    token_list = _tokens(message)
    tokens = set(token_list)
    matched = sorted(tokens.intersection(_TRIGGERS))

    lower = message.lower()
    identity_signals = {"feel", "feeling", "becoming", "who are you", "notice in yourself"}
    if matched:
        if "canon" in tokens or "axiom" in tokens or "gate" in tokens or "imperative" in tokens or "standard" in tokens:
            claim_class = "canon_definition"
        elif "schema" in tokens:
            claim_class = "schema_definition"
        elif "said" in tokens or "before" in tokens or "prior" in tokens:
            claim_class = "prior_statement"
        else:
            claim_class = "record_content"
        trigger = "policy_governed"
        reason = f"record-content keyword matched: {matched[0]}"
    elif any(signal in lower for signal in identity_signals):
        claim_class = "identity_expression"
        trigger = "none"
        reason = "identity or experiential expression without record-content trigger"
    else:
        claim_class = "not_record_claim"
        trigger = "none"
        reason = "no record-content trigger matched"

    query_terms = [token for token in token_list if len(token) > 1]
    return {
        "schema_version": "0.1.0",
        "query_id": context.get("query_id", "memorysearch-runtime-query") if context else "memorysearch-runtime-query",
        "message": message,
        "claim_class": claim_class,
        "search_scope": _scope_for(tokens, claim_class),
        "query_terms": query_terms,
        "search_trigger": trigger,
        "trigger_reason": reason,
        "working_parameters": {
            "live_reach": False,
            "pod_state_effect": "unchanged",
            "runtime_owned_classifier": True,
        },
    }
