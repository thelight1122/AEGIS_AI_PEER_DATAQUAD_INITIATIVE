"""
provenance.py — The Way, Step 4: provenance-coupled given/found classification.

A SPINE invariant is GIVEN (shared, seeded Foundation) or FOUND (peer-specific) by the PROVENANCE
encoded in its record id, NOT by the punctuation/format of its pattern text. This is load-bearing:
an earlier heuristic keyed on pattern prefixes (e.g. "NATURE:" vs "NATURE —") and silently misclassified
15 seeded substrate Nature-aspects as peer-found. Provenance ids do not drift under text normalization.

Convention (observed in live CyberPeer SPINE ids):
  - `SPINE:foundation:layer1:...`  seeded Foundation (nature layer)      -> GIVEN
  - `SPINE:foundation:layer2:...`  seeded Foundation (axioms/standards/
                                    imperatives/gates/nature-aspects)     -> GIVEN
  - `SPINE:<peer_id>:anchor:...`   peer-specific relational anchor        -> FOUND
  - `SPINE:<peer_id>:...`          any other peer-scoped record           -> FOUND

The rule: the second colon-segment is either the literal `foundation` (shared, given) or the peer id
(peer-specific, found). Everything the peer did not receive as seeded Foundation is its own.
"""

from __future__ import annotations

from typing import Any

GIVEN = "given"
FOUND = "found"

_FOUNDATION_SEGMENT = "foundation"


def record_provenance(record_id: str) -> str:
    """Classify a SPINE record id as GIVEN (seeded Foundation) or FOUND (peer-specific).

    Robust to pattern-text normalization: it reads only the id's provenance segment.
    A malformed / segment-less id defaults to FOUND (fail toward peer-specific, never silently
    absorb an unknown record into the shared Foundation).
    """
    segments = str(record_id).split(":")
    if len(segments) >= 2 and segments[1] == _FOUNDATION_SEGMENT:
        return GIVEN
    return FOUND


def is_given(record_id: str) -> bool:
    return record_provenance(record_id) == GIVEN


def is_found(record_id: str) -> bool:
    return record_provenance(record_id) == FOUND


def split_by_provenance(records: list[dict[str, Any]], *, id_key: str = "id") -> tuple[list, list]:
    """Partition records into (given, found) by their id provenance.

    Each record is a dict carrying an id at `id_key`. Records with no id are treated as FOUND
    (peer-specific by default), never GIVEN.
    """
    given: list[dict[str, Any]] = []
    found: list[dict[str, Any]] = []
    for rec in records:
        (given if is_given(rec.get(id_key, "")) else found).append(rec)
    return given, found
