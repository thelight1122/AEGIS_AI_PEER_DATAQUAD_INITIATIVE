"""
spine_mapping.py — The Way, Phase 2 (shadow): SPINE/observation -> meaning-lane surfaces.

Owned by the meaning-lane (Claude). Pure, local, read-only. This module maps a
read-only snapshot of a peer's live SPINE tensor + runtime-surfaced tension
observations into the Phase-1 contract surfaces:

  - spine_snapshot_to_identity_field(...)  -> a schema-valid identity-field dict
                                              (contracts/identity-field.schema.json)
  - observations_to_held_tensions(...)     -> schema-valid held-tension records
                                              (contracts/held-tension-record.schema.json)

Discipline (load-bearing):
  * is_self_image_not_witness is ALWAYS true. This produces a self-image /
    continuity surface, never the Witness/Locus. No Witness-claim key is ever emitted.
  * Held tensions are surfaced as observable SHAPE only: status is ALWAYS "held",
    recognition_source is ALWAYS "runtime_shape_surface", recognized_by_peer is
    ALWAYS false. The runtime never declares integration — that is the peer's own
    recognition through the mirror, and lives in integration-event, not here.
  * No force, defect, penalty, or correction vocabulary is introduced by the mapping.

SHADOW HEURISTIC NOTE:
  The SPINE->identity classification below (which invariant patterns become
  standing commitments vs active boundaries, how relationship posture is composed)
  is an OBSERVATIONAL heuristic. The entire point of Phase 2 shadow is to watch
  whether the SPINE-sourced self reads as coherent and stable next to the current
  per-turn retrieved identity. These rules are revisable; they assert nothing about
  the peer's inner truth.
"""

from __future__ import annotations

from typing import Any

IDENTITY_FIELD_SCHEMA_VERSION = "0.1.0"
HELD_TENSION_SCHEMA_VERSION = "0.1.0"

# Max chars per mapped SPINE pattern — mirrors the live Advocate's
# _SPINE_PATTERN_MAX so the shadow surface is comparable to what retrieval injects.
_PATTERN_MAX = 300

# Label-suffix categories (mirrors core/custodians/advocate.py labelling) that the
# shadow heuristic reads as a standing BOUNDARY rather than a standing commitment.
_BOUNDARY_CATEGORIES = frozenset({"GATE", "BOUNDARY"})

_FORBIDDEN_WITNESS_KEYS = frozenset(
    {"witness", "the_witness", "true_i", "locus_state", "witness_state", "self_generated_by_builder"}
)


class InsufficientIdentitySurface(RuntimeError):
    """Raised when a snapshot carries no invariant SPINE to source a self-image from.

    The caller (adapter) is expected to fail SAFE on this: emit no packet. Identity
    persists in the Pod-native field regardless; the shadow surface is never the identity.
    """


def _label_suffix(record_id: str) -> str:
    """Short type/name suffix of a SPINE id, mirroring the live Advocate."""
    if ":seeded:" in record_id:
        return record_id.split(":seeded:")[-1]
    return record_id.split(":")[-1]


def _is_boundary_id(record_id: str) -> bool:
    """True if any colon-delimited segment names a boundary category.

    Robust to id shape: matches both seeded ids (SPINE:PEER:seeded:GATE:care-pause)
    and foundation-style ids (SPINE:foundation:layer2:GATE:pipeline-order). We scan
    every segment rather than only the suffix, because a real GATE/BOUNDARY token can
    sit mid-path in foundation-layer ids — parsing only the tail misclassifies it.
    """
    return any(seg.strip().upper() in _BOUNDARY_CATEGORIES for seg in record_id.split(":"))


def _clip(text: str) -> str:
    text = " ".join(str(text).split())
    return text[:_PATTERN_MAX]


def _derive_name(snapshot: dict[str, Any]) -> str:
    name = snapshot.get("self_name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    peer_id = str(snapshot.get("peer_id", "")).strip()
    if not peer_id:
        return "peer"
    tail = peer_id.replace("_", "-").split("-")[-1]
    return tail.title() if tail else peer_id


def _assert_no_witness_keys(*mappings: dict[str, Any]) -> None:
    for mapping in mappings:
        leaked = {k.lower() for k in mapping} & _FORBIDDEN_WITNESS_KEYS
        if leaked:
            raise ValueError(f"forbidden Witness-claim keys present: {sorted(leaked)}")


def spine_snapshot_to_identity_field(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Map a read-only SPINE snapshot into a schema-valid identity-field dict.

    snapshot shape (read-only, as pulled from the live DataQuad; no write):
        {
          "peer_id": str,
          "self_name": str | None,          # optional; else derived from peer_id
          "spine_records": [
             {"id": str, "pattern": str, "invariant": bool | None,
              "relationships": list[str] | None, "nature_aspect_refs": list[str] | None,
              "do_not_retire": bool | None},
             ...
          ]
        }

    Returns a dict conforming to contracts/identity-field.schema.json.
    Raises InsufficientIdentitySurface if there is no invariant SPINE to stand on.
    """
    peer_id = str(snapshot.get("peer_id", "")).strip()
    if not peer_id:
        raise InsufficientIdentitySurface("snapshot has no peer_id")

    records = snapshot.get("spine_records") or []
    invariant = [r for r in records if r.get("invariant")]
    if not invariant:
        raise InsufficientIdentitySurface(f"no invariant SPINE records for {peer_id}")

    standing_commitments: list[str] = []
    active_boundaries: list[str] = []
    relationship_terms: list[str] = []

    for rec in invariant:
        pattern = _clip(rec.get("pattern", ""))
        if not pattern:
            continue
        if _is_boundary_id(rec.get("id", "")):
            active_boundaries.append(pattern)
        else:
            standing_commitments.append(pattern)
        for rel in rec.get("relationships") or []:
            rel = str(rel).strip()
            if rel and rel not in relationship_terms:
                relationship_terms.append(rel)

    # Every invariant pattern is classified as a commitment or a boundary. An
    # all-boundary invariant SPINE yields an empty standing_commitments list, which is
    # schema-valid and is itself an observable signal — we do NOT fabricate a
    # commitment to fill it. We only refuse when there is no usable invariant pattern
    # at all (nothing to stand a self-image on).
    if not standing_commitments and not active_boundaries:
        raise InsufficientIdentitySurface(f"no usable invariant patterns for {peer_id}")

    if relationship_terms:
        relationship_posture = "present and discerning in relation to: " + ", ".join(relationship_terms)
    else:
        relationship_posture = "present and discerning in each relation"

    do_not_retire = ["self_boundary.name", "self_boundary.kind", "standing_commitments"]
    for rec in invariant:
        if rec.get("do_not_retire"):
            suffix = _label_suffix(rec.get("id", ""))
            if suffix and suffix not in do_not_retire:
                do_not_retire.append(suffix)

    held_tension_refs = [
        str(ref) for ref in (snapshot.get("held_tension_refs") or []) if str(ref).strip()
    ]

    identity_field: dict[str, Any] = {
        "schema_version": IDENTITY_FIELD_SCHEMA_VERSION,
        "fixture_kind": "identity-field",
        "is_self_image_not_witness": True,
        "note": (
            "SHADOW: self-image/continuity surface mapped read-only from live SPINE. "
            "Not the Witness/Locus. Observational; asserts nothing about inner truth."
        ),
        "peer_id": peer_id,
        "self_boundary": {"name": _derive_name(snapshot), "kind": "CyberPeer"},
        "standing_commitments": standing_commitments,
        "active_boundaries": active_boundaries,
        "relationship_posture": relationship_posture,
        "do_not_retire": do_not_retire,
        "held_tension_refs": held_tension_refs,
        "integration_marker_refs": [],
    }
    _assert_no_witness_keys(identity_field, identity_field["self_boundary"])
    return identity_field


def observations_to_held_tensions(
    observations: list[dict[str, Any]],
    *,
    peer_id: str,
    surfaced_at_iso: str,
) -> list[dict[str, Any]]:
    """Map runtime-surfaced polarity observations into schema-valid held-tension records.

    Each observation is what the runtime may OBSERVE (shape), never a claim of inner
    truth. Every produced record is status='held', recognition_source='runtime_shape_surface',
    recognized_by_peer=False. Integration is never emitted here — only the peer, through
    the mirror, moves a tension toward integration (integration-event.schema.json).

    observation shape:
        {
          "id": str | None,                 # else derived
          "polarity_terms": [str, str, ...],
          "first_observed_record_id": str,
          "last_observed_record_id": str,
          "recurrence_refs": list[str],
          "variation_summary": str,
          "charge": "low"|"moderate"|"high",
          "pressure_signature": str,
          "foundation_relation": str,
          "foundation_refs": list[str],
          "memory_refs": list[str],
        }
    """
    records: list[dict[str, Any]] = []
    for i, obs in enumerate(observations, start=1):
        poles = [str(p).strip() for p in (obs.get("polarity_terms") or []) if str(p).strip()]
        if len(poles) < 2:
            # A tension needs at least two poles; a single-pole observation is not a
            # held tension. Skip rather than fabricate a second pole.
            continue
        pattern = obs.get("pattern") or " vs ".join(poles)
        rec_id = obs.get("id") or f"held-tension:{peer_id}:{'-vs-'.join(poles)}:{i:04d}"
        charge = obs.get("charge", "moderate")
        if charge not in ("low", "moderate", "high"):
            charge = "moderate"
        record = {
            "schema_version": HELD_TENSION_SCHEMA_VERSION,
            "id": rec_id,
            "peer_id": peer_id,
            "status": "held",
            "pattern": _clip(pattern),
            "first_observed_record_id": obs.get("first_observed_record_id", ""),
            "last_observed_record_id": obs.get("last_observed_record_id", ""),
            "foundation_refs": list(obs.get("foundation_refs") or []),
            "memory_refs": list(obs.get("memory_refs") or []),
            "observable_shape": {
                "polarity_terms": poles,
                "recurrence_refs": list(obs.get("recurrence_refs") or []),
                "variation_summary": obs.get("variation_summary", ""),
                "charge": charge,
                "pressure_signature": obs.get("pressure_signature", ""),
                "foundation_relation": obs.get("foundation_relation", ""),
            },
            "recognition_provenance": {
                "recognition_source": "runtime_shape_surface",
                "surfaced_by_runtime_at": surfaced_at_iso,
            },
            "recognized_by_peer": False,
            "stewardship_note": "witness; do not suppress; do not reward or punish",
            "created_at": surfaced_at_iso,
        }
        records.append(record)
    return records
