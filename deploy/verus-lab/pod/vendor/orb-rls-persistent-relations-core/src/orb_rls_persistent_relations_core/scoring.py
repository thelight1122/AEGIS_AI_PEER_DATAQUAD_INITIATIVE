from aegis_pod_sdk import RecordLike, TensorKind
import re


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "briefly", "by", "can", "do",
    "does", "for", "from", "gabe", "i", "if", "in", "is", "it", "me", "name",
    "of", "on", "one", "or", "please", "recall", "say", "the", "to", "what",
    "you", "your", "aegis",
}

_CANON_INTENT_TERMS = {"axiom", "canon", "canonical", "identity", "nature", "principle"}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 1 and token not in _STOPWORDS
    }


def _record_text(record: RecordLike) -> str:
    """Return the record's own text, asking the record before naming any field.

    SUPERSEDES the upstream 1.0.0 body, which enumerated five DataQuad field
    names and so required the orb to know every tensor's record schema. PEER is
    deliberately kept raw by the recording protocol, so its affect lives in
    free-form keys no field list can anticipate, and it scored zero however well
    it matched.

    A record that supplies scorable_text is authoritative for its own content.
    The legacy field walk remains as the fallback for records that do not.

    Note what this does NOT promise. Through the live DaemonRecord adapter every
    record supplies scorable_text, foundation records included, so the fallback
    is effectively unreached in that path and those records do not score as they
    did under 1.0.0. Scores move in both directions: the whole-record text can
    add tokens a five-field walk missed, and it drops the dict key names that
    str() of a mapping used to contribute. Selection logic is unchanged, but
    selection outcomes are not outcome-neutral, and the overlap term is not
    normalised for length, so a longer record is easier to select.
    """
    supplied = getattr(record, "scorable_text", None)
    if isinstance(supplied, str) and supplied.strip():
        return supplied

    text_content = ""
    if hasattr(record, "present_state") and record.present_state:
        text_content += " " + str(record.present_state)
    if hasattr(record, "working_context") and record.working_context:
        text_content += " " + str(record.working_context)
    if hasattr(record, "distilled_summary") and record.distilled_summary:
        text_content += " " + record.distilled_summary
    if hasattr(record, "essence_memory") and record.essence_memory:
        text_content += " " + record.essence_memory
    if hasattr(record, "pattern") and record.pattern:
        text_content += " " + record.pattern
    return text_content

def compute_relevance(
    record: RecordLike,
    query: str,
    intent: str,
    pressure_state: dict,
    nature_aspects: list[str]
) -> tuple[float, str]:
    """
    Computes a relevance score from 0.0 to 1.0 for a given record.
    Returns: (score, reason)
    """
    score = 0.0
    reasons = []

    # 1. Semantic Similarity / Keyword match (Phase 1: meaningful token overlap)
    query_words = _tokens(query)
    text_words = _tokens(_record_text(record))
    overlap = len(query_words.intersection(text_words))
    if overlap > 0:
        match_score = min(0.5, overlap * 0.12)
        score += match_score
        reasons.append(f"Meaningful token match (overlap: {overlap})")

    # 2. Intent Match
    if overlap > 0 and intent == "recall" and record.tensor == TensorKind.NCT:
        score += 0.08
        reasons.append("NCT recall support")

    # 3. Recency / clock proximity (Higher ticks get a minor recency bonus)
    if overlap > 0 and record.clock and record.clock.tick > 0:
        recency_bonus = min(0.05, record.clock.tick * 0.0025)
        score += recency_bonus
        reasons.append(f"Recency bonus (+{recency_bonus:.3f})")

    # 4. Source Trust / Tensor Type
    if overlap > 0 and record.tensor == TensorKind.SPINE:
        score += 0.12
        reasons.append("SPINE source trust")
        canon_terms = query_words.intersection(_CANON_INTENT_TERMS)
        if canon_terms and _record_is_foundational_canon(record):
            score += 0.02
            reasons.append("Foundational canon affordance")
    elif overlap > 0 and record.tensor == TensorKind.PCT:
        score += 0.03
        reasons.append("PCT context support")

    # 5. Nature Aspect Relevance
    if record.tensor == TensorKind.SPINE and hasattr(record, "nature_aspect_refs") and record.nature_aspect_refs:
        aspect_matches = len(set(record.nature_aspect_refs).intersection(set(nature_aspects)))
        if aspect_matches > 0:
            score += 0.15
            reasons.append(f"Nature aspect relevance (matches: {aspect_matches})")

    final_score = min(1.0, max(0.0, score))
    reason_str = ", ".join(reasons) if reasons else "No matching criteria"
    return final_score, reason_str


def _record_is_foundational_canon(record: RecordLike) -> bool:
    record_id = str(getattr(record, "id", "")).lower()
    return record_id.startswith("spine:foundation:")
