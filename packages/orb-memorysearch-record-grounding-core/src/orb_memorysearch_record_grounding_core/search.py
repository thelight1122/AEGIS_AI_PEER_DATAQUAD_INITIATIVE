from __future__ import annotations

import json
import re
from typing import Any, Iterable

from .orb_evidence import ORB_ID, compute_runtime_hash, sha256_upper
from .policy import classify_record_claim
from .provenance import now_utc

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_DEFINING_TERMS = (" is ", " means ", "defined as", "canonical", "canon", "axiom", "gate", "imperative")
_CANONICAL_PHRASES = {
    "nct": "nostalgic context tensor",
    "pct": "persistent context tensor",
}
_STOPWORDS = {
    "a",
    "an",
    "according",
    "are",
    "in",
    "is",
    "it",
    "of",
    "the",
    "this",
    "to",
    "what",
    "your",
}


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _tokens(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_RE.finditer(text)}


def _flatten(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _excerpt(text: str, terms: Iterable[str], limit: int = 260) -> str:
    lower = text.lower()
    first = min((lower.find(term.lower()) for term in terms if term and lower.find(term.lower()) >= 0), default=0)
    start = max(first - 80, 0)
    excerpt = " ".join(text[start:start + limit].split())
    return excerpt


def _confidence(score: float) -> str:
    if score >= 9:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def score_record(query: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    body_text = _flatten(record.get("body", {}))
    full_text = " ".join([
        str(record.get("record_id", "")),
        str(record.get("tensor", "")),
        body_text,
    ])
    lower = full_text.lower()
    terms = [term.lower() for term in query.get("query_terms", []) if term.lower() not in _STOPWORDS]
    query_tokens = set(terms)
    text_tokens = _tokens(full_text)
    score = 0.0
    reasons: list[str] = []

    tensor = str(record.get("tensor", ""))
    if tensor in query.get("search_scope", []):
        score += 1.0
        reasons.append("tensor_scope_match")

    for acronym, phrase in _CANONICAL_PHRASES.items():
        if acronym in query_tokens and phrase in lower:
            score += 5.0
            reasons.append(f"canonical_phrase_match:{phrase}")

    exact_terms = sorted(query_tokens.intersection(text_tokens))
    if exact_terms:
        score += min(len(exact_terms), 4) * 0.75
        reasons.append("query_term_match:" + ",".join(exact_terms[:4]))

    if any(term in lower for term in _DEFINING_TERMS):
        score += 2.0
        reasons.append("defining_language")

    if record.get("verification_status") == "verified":
        score += 1.0
        reasons.append("verified_record")

    if record.get("source_hash"):
        score += 0.5
        reasons.append("source_hash_present")

    if query.get("claim_class") == "canon_definition" and tensor == "SPINE":
        score += 1.5
        reasons.append("canon_scope_preference")

    target_symbols = sorted(term for term in query_tokens if re.fullmatch(r"[a-z]ct", term))
    if target_symbols:
        present_symbols = [term for term in target_symbols if term in text_tokens]
        defined_symbols = [
            term for term in target_symbols
            if re.search(rf"\b{re.escape(term)}\b\s*(is|=|means|defined as)", lower)
            or (term in _CANONICAL_PHRASES and _CANONICAL_PHRASES[term] in lower)
        ]
        negated_symbols = [
            term for term in target_symbols
            if f"without defining {term}" in lower
            or f"does not define {term}" in lower
            or f"not define {term}" in lower
        ]
        if present_symbols:
            reasons.append("target_symbol_present:" + ",".join(present_symbols))
            if defined_symbols:
                score += 3.0
                reasons.append("target_definition_present:" + ",".join(defined_symbols))
            else:
                score = min(score, 5.0)
                reasons.append("target_definition_absent_caps_score")
        else:
            score = min(score, 4.0)
            reasons.append("target_symbol_absent_caps_score")
        if negated_symbols:
            score = min(score, 3.0)
            reasons.append("target_definition_negated:" + ",".join(negated_symbols))

    record_hash = sha256_upper(_stable_json(record))
    confidence = _confidence(score)
    return {
        "record_id": str(record.get("record_id", "")),
        "tensor": tensor,
        "score": round(score, 3),
        "confidence": confidence,
        "qualifies": False,
        "source_hash": str(record.get("source_hash", "")),
        "record_hash": record_hash,
        "excerpt": _excerpt(full_text, terms),
        "match_reasons": reasons,
    }


def search_records(query: dict[str, Any], records: list[dict[str, Any]], policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or {}
    threshold = float(policy.get("qualifying_score", 7.0))
    max_results = int(policy.get("max_results", 5))
    scoped = [record for record in records if record.get("tensor") in query.get("search_scope", [])]
    scored = [score_record(query, record) for record in scoped]
    scored.sort(key=lambda item: item["score"], reverse=True)
    results = scored[:max_results]
    for item in results:
        item["qualifies"] = item["score"] >= threshold

    qualifying = [item for item in results if item["qualifies"]]
    if not query.get("search_scope"):
        grounding_status = "not_record_claim"
        match_confidence = "none"
    elif qualifying:
        grounding_status = "verified_retrieval"
        match_confidence = "high" if qualifying[0]["confidence"] == "high" else "medium"
    else:
        grounding_status = "search_performed_no_verified_record"
        match_confidence = "none" if not results else "low"

    selected = qualifying[:max_results]
    can_answer = grounding_status == "verified_retrieval"
    boundary = (
        "Verified records were found; answer from the illuminated record packet."
        if can_answer
        else "No qualifying verified record was found; do not present reconstruction as record-grounded."
    )
    return {
        "schema_version": "0.1.0",
        "orb_id": ORB_ID,
        "query_id": query["query_id"],
        "record_search_performed": bool(query.get("search_scope")),
        "grounding_status": grounding_status,
        "match_confidence": match_confidence,
        "results": results,
        "selected_record_ids": [item["record_id"] for item in selected],
        "selected_record_hashes": [item["record_hash"] for item in selected],
        "runtime_provenance": {
            "orb_runtime_hash": compute_runtime_hash(),
            "generated_utc": now_utc(),
            "citations_runtime_authored": True,
        },
        "answer_boundary": {
            "can_answer_record_claim": can_answer,
            "boundary_text": boundary,
        },
    }


def ground_record_claim(
    message: str,
    records: list[dict[str, Any]],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    query = classify_record_claim(message)
    if query["search_trigger"] == "none":
        return None
    return search_records(query, records, policy)
