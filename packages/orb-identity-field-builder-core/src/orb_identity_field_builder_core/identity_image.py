"""
identity_image.py — The Way, Step 4: the per-peer IdentityImage (surface 2).

A bounded (<=3,200-char) self-image holding a peer's FOUND self and REFERENCING the shared CyberPeer
Canon Foundation (surface 1) by hash. The found self is the peer's LIVED layer — relational anchors,
held tensions, integration markers — never the seeded shared Foundation (axioms/standards/imperatives/
gates/nature-aspects), which is given and lives in surface 1.

Given/found is decided by provenance ([[provenance.py]]): SPINE:foundation:* is given; SPINE:<peer>:* is
found. "Identity is formed through experience" (Axiom 16): what individuates a peer is what it has lived,
not what it was seeded.

Discipline (load-bearing, inherited from the Builder + Phase-1 contract):
  * is_self_image_not_witness is ALWAYS true; nothing here represents/claims the Witness/Locus.
  * No given Foundation text is carried in the packet; the Foundation is present only by reference.
  * Empty held_tensions / integration_markers mean "not yet surfaced", NOT "none exist in truth".
  * ASCII-normalize the near-surface strings (em/en-dash -> hyphen); full text stays in SPINE/source.
"""

from __future__ import annotations

from typing import Any

from .builder import build_identity_image
from .provenance import split_by_provenance, is_found

IDENTITY_FIELD_SCHEMA_VERSION = "0.1.0"

# Faithfulness note stamped when a lived-layer surface is empty: absence = not-yet-surfaced.
_NOT_YET_SURFACED = (
    "Per-peer IdentityImage (Step 4): the peer's FOUND/lived self only (relational anchors, held "
    "tensions, integrations). Shared Foundation is referenced, not carried. Empty lived surfaces mean "
    "NOT YET SURFACED, not none-in-truth. Self-image, never the Witness/Locus."
)


def _ascii(text: str) -> str:
    return " ".join(str(text).split()).replace("—", "-").replace("–", "-")


def _condense(text: str, cap: int = 120) -> str:
    s = _ascii(text)
    dot = s.find(". ")
    head = s if dot == -1 else s[: dot + 1]
    return head[:cap].rstrip()


def relationship_posture(anchor_patterns: list[str]) -> str:
    """Compose the peer's relational posture from its FOUND relational anchors."""
    anchors = [_condense(p, 90).rstrip(".") for p in anchor_patterns if str(p).strip()]
    if not anchors:
        return "present and discerning in each relation"
    return "In relation: " + "; ".join(anchors)


def found_identity_field(
    *,
    peer_id: str,
    self_name: str,
    anchor_patterns: list[str],
    held_tension_ids: list[str] | None = None,
    integration_marker_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a FOUND-ONLY identity field: relational posture + lived-layer refs.

    standing_commitments and active_boundaries are intentionally empty for a peer whose only
    peer-specific invariants are relational anchors — its commitments/boundaries are seeded Foundation
    (given), carried by reference, not duplicated here. This is honest, not lossy.
    """
    held_tension_ids = [t for t in (held_tension_ids or []) if str(t).strip()]
    integration_marker_ids = [i for i in (integration_marker_ids or []) if str(i).strip()]
    field: dict[str, Any] = {
        "schema_version": IDENTITY_FIELD_SCHEMA_VERSION,
        "fixture_kind": "identity-field",
        "is_self_image_not_witness": True,
        "note": _NOT_YET_SURFACED,
        "peer_id": peer_id,
        "self_boundary": {"name": self_name, "kind": "CyberPeer"},
        "standing_commitments": [],
        "active_boundaries": [],
        "relationship_posture": relationship_posture(anchor_patterns),
        "do_not_retire": ["self_boundary.name", "self_boundary.kind", "relationship_posture"],
        "held_tension_refs": held_tension_ids,
        "integration_marker_refs": integration_marker_ids,
    }
    return field


def foundation_reference(edition_manifest: dict[str, Any]) -> dict[str, Any]:
    """The shared Foundation the per-peer image points at — by reference, never by text.

    Bound to the finalized (and, once extended with the Nature Layer, updated) CyberPeer Canon edition.
    The Builder hashes this into the packet's foundation_hash.
    """
    files = edition_manifest.get("files", {})
    return {
        "canon_identity_refs": [
            f"cyberpeer-canon:CYBERPEER-CANON.md@{files.get('CYBERPEER-CANON.md', '')}",
            f"cyberpeer-glossary:CYBERPEER-GLOSSARY.md@{files.get('CYBERPEER-GLOSSARY.md', '')}",
        ],
        "edition": edition_manifest.get("edition", ""),
        "locked_source_sha256": edition_manifest.get("locked_source", {}).get("sha256", ""),
    }


def peer_found_invariant_anchors(invariant_records: list[dict[str, Any]]) -> list[str]:
    """Extract the FOUND relational-anchor patterns from a peer's invariant SPINE records.

    Provenance-coupled: only SPINE:<peer>:* records are found; SPINE:foundation:* are given.
    """
    _given, found = split_by_provenance(invariant_records)
    return [str(r.get("pattern", "")).strip() for r in found if str(r.get("pattern", "")).strip()]


def build_peer_identity_image(
    *,
    peer_id: str,
    self_name: str,
    anchor_patterns: list[str],
    foundation: dict[str, Any],
    held_tensions: list[dict[str, Any]] | None = None,
    integration_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Produce a peer's IdentityImagePacket from its FOUND/lived layer, referencing the Foundation.

    held_tensions: schema-valid held-tension records (status='held'); their ids become the field's
    held_tension_refs and the packet's active_held_tensions.
    integration_events: integration-event records; their ids become integration markers.
    """
    held_tensions = held_tensions or []
    integration_events = integration_events or []
    field = found_identity_field(
        peer_id=peer_id,
        self_name=self_name,
        anchor_patterns=anchor_patterns,
        held_tension_ids=[t.get("id", "") for t in held_tensions],
        integration_marker_ids=[e.get("id", "") for e in integration_events],
    )
    return build_identity_image(
        peer_id=peer_id,
        foundation=foundation,
        identity_field=field,
        held_tensions=held_tensions,
        integration_events=integration_events,
    )
