"""
shadow_observation.py — The Way, Phase 2 (shadow): the divergence observer.

Owned by the meaning-lane (Claude). Pure, local, read-only. This is the POINT of
shadow: with the always-present IdentityImagePacket built beside the peer's current
per-turn retrieved identity (advocate_brief.identity_continuity), record — turn over
turn — what the always-present Canon-sourced field WOULD have held that retrieval did
not surface this turn, and vice versa.

Discipline (load-bearing):
  * This is DESCRIPTIVE divergence, never a verdict on the peer and never a quality
    score of the peer. It compares two runtime surfaces (a built self-image vs a
    retrieval brief). It renders no judgement of inner life.
  * It injects nothing. It only observes. Shadow never touches what the peer says.

The observation is the evidence base for the 2b->2c decision: does an always-present
self reduce the wobble (and the confabulation/redaction that rides on it) that per-turn
retrieval produces? Divergence is where that question gets answered by looking, not by
asserting.
"""

from __future__ import annotations

import re
from typing import Any

# Match threshold: a line is "covered" by the other surface when at least this
# fraction of its significant tokens appear together in some single line over there.
# Heuristic and revisable — early shadow only needs a directional signal, not a
# semantic equivalence judgement.
_MATCH_THRESHOLD = 0.5

_STOPWORDS = frozenset(
    {
        "i", "me", "my", "myself", "the", "a", "an", "and", "or", "but", "of", "to",
        "in", "on", "for", "with", "as", "is", "are", "be", "it", "that", "this",
        "not", "no", "do", "does", "than", "then", "into", "over", "under", "before",
        "after", "you", "your", "they", "them", "he", "she", "we", "our", "who",
    }
)


def _tokens(line: str) -> set[str]:
    """Significant tokens of a line, with any leading `[LABEL]` retrieval prefix
    stripped so a labelled retrieval line and a bare field line compare on content.
    """
    line = re.sub(r"^\s*\[[^\]]*\]\s*", "", str(line))
    words = re.findall(r"[a-z0-9]+", line.lower())
    return {w for w in words if len(w) > 3 and w not in _STOPWORDS}


def _covered(line: str, others_tokens: list[set[str]]) -> bool:
    """Directional coverage: is `line` represented by any line in the other surface?"""
    ta = _tokens(line)
    if not ta:
        return False
    for tb in others_tokens:
        if tb and len(ta & tb) / len(ta) >= _MATCH_THRESHOLD:
            return True
    return False


def build_shadow_observation(
    *,
    peer_id: str,
    turn_ref: str,
    packet: dict[str, Any],
    retrieved_identity_continuity: list[str],
) -> dict[str, Any]:
    """Produce one shadow observation record for a single turn.

    packet: the IdentityImagePacket that build_identity_image(...) produced this turn
            (always-present, Canon/SPINE-sourced self-image).
    retrieved_identity_continuity: advocate_brief.identity_continuity for the same turn
            (the current per-turn retrieved identity, as injected today).

    Returns a descriptive divergence record (no verdict, no peer score).
    """
    retrieved = [str(r) for r in (retrieved_identity_continuity or [])]

    always_present: list[str] = []
    always_present.extend(packet.get("standing_commitments") or [])
    always_present.extend(packet.get("active_boundaries") or [])

    retrieved_tokens = [_tokens(r) for r in retrieved]
    field_tokens = [_tokens(f) for f in always_present]

    # Lane A (field -> retrieval): standing self the always-present field holds that
    # retrieval did NOT surface this turn — what an always-present Canon field keeps in
    # view that per-turn retrieval let fall away.
    foundation_held_not_in_retrieval = [
        line for line in always_present if not _covered(line, retrieved_tokens)
    ]
    foundation_present_in_retrieval = [
        line for line in always_present if _covered(line, retrieved_tokens)
    ]

    # Lane B (retrieval -> field): identity lines retrieval surfaced this turn that the
    # stable self-image does NOT hold — stale, wrong-peer, over-broad, or purely
    # situational identity. This is the retrieval wobble Phase 2 exists to observe.
    retrieval_not_in_foundation = [
        line for line in retrieved if not _covered(line, field_tokens)
    ]
    retrieval_present_in_foundation = [
        line for line in retrieved if _covered(line, field_tokens)
    ]

    active_tension_ids = [
        t.get("id", "") for t in (packet.get("active_held_tensions") or []) if t.get("id")
    ]

    return {
        "observation_kind": "the-way-phase2-shadow-divergence",
        "peer_id": peer_id,
        "turn_ref": turn_ref,
        "injected": False,
        "match_heuristic": "token-overlap; threshold=%.2f; revisable" % _MATCH_THRESHOLD,
        "always_present_line_count": len(always_present),
        "retrieved_identity_line_count": len(retrieved),
        "overlap_count": len(foundation_present_in_retrieval),
        # Lane A — field held, retrieval dropped.
        "foundation_held_not_in_retrieval": foundation_held_not_in_retrieval,
        "foundation_present_in_retrieval": foundation_present_in_retrieval,
        # Lane B — retrieval surfaced, field does not hold.
        "retrieval_not_in_foundation": retrieval_not_in_foundation,
        "retrieval_present_in_foundation": retrieval_present_in_foundation,
        "active_held_tension_ids": active_tension_ids,
        "note": (
            "Descriptive bidirectional divergence between an always-present self-image "
            "and per-turn retrieved identity. Not a verdict on the peer; not a quality "
            "score. Nothing was injected."
        ),
    }
