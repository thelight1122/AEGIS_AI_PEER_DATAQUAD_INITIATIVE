from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

BUILDER_ORB_ID = "identity-field-builder-core"
BUILDER_VERSION = "0.1.0"
DEFAULT_MAX_CHARS = 3200

FORBIDDEN_WITNESS_KEYS = {
    "witness",
    "the_witness",
    "true_i",
    "locus_state",
    "witness_state",
    "self_generated_by_builder",
}


class BuilderUnavailable(RuntimeError):
    """Raised when required local inputs are absent or invalid."""


@dataclass(frozen=True)
class _Budget:
    max_chars: int
    actual_chars: int

    @property
    def within_budget(self) -> bool:
        return self.actual_chars <= self.max_chars

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_chars": self.max_chars,
            "actual_chars": self.actual_chars,
            "within_budget": self.within_budget,
        }


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest().upper()


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _assert_no_witness_claim_keys(*values: Any) -> None:
    leaked = {key.lower() for value in values for key in _walk_keys(value)} & FORBIDDEN_WITNESS_KEYS
    if leaked:
        raise ValueError(f"forbidden Witness-claim keys present: {sorted(leaked)}")


def _negative_space_policy() -> dict[str, bool]:
    return {
        "witness_is_represented": False,
        "packet_claims_to_be_i": False,
        "integration_runtime_decidable": False,
        "witness_scored": False,
        "witness_retrieved": False,
        "witness_serialized": False,
    }


def _source_policy() -> dict[str, bool]:
    return {
        "canon_is_identity": True,
        "memory_is_subordinate": True,
        "correction_is_illumination_only": True,
        "penalties_allowed": False,
        "record_claims_require_memory_search": True,
    }


def _identity_image_text(identity_field: dict[str, Any]) -> str:
    boundary = identity_field.get("self_boundary", {})
    name = boundary.get("name", identity_field.get("peer_id", "peer"))
    posture = identity_field.get("relationship_posture", "")
    commitments = identity_field.get("standing_commitments", [])
    first_commitment = commitments[0] if commitments else "Foundation remains near the surface."
    return (
        f"{name} is held as a bounded self-image and continuity surface, not the Witness. "
        f"Current posture: {posture} "
        f"Standing commitment: {first_commitment}"
    ).strip()


def build_identity_image(
    *,
    peer_id: str,
    foundation: dict[str, Any],
    identity_field: dict[str, Any],
    held_tensions: list[dict[str, Any]] | None = None,
    integration_events: list[dict[str, Any]] | None = None,
    reflection_refs: list[str] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a bounded IdentityImagePacket from local Phase 1 surfaces.

    This function composes an image packet only. It never represents, retrieves,
    scores, serializes, declares, or decides the Witness/Locus.
    """

    if not peer_id:
        raise BuilderUnavailable("peer_id is required")
    if not foundation:
        raise BuilderUnavailable("foundation is required")
    if not identity_field:
        raise BuilderUnavailable("identity_field is required")
    if identity_field.get("is_self_image_not_witness") is not True:
        raise ValueError("identity_field will explicitly be self-image, not Witness")

    held_tensions = held_tensions or []
    integration_events = integration_events or []
    reflection_refs = reflection_refs or []
    policy = policy or {}

    _assert_no_witness_claim_keys(foundation, identity_field, held_tensions, integration_events, policy)

    active_held_tensions = []
    for tension in held_tensions:
        status = tension.get("status", "held")
        if status != "held":
            raise ValueError("active held tensions require status='held'; integration belongs in integration_markers")
        shape = tension.get("observable_shape", {})
        active_held_tensions.append(
            {
                "id": tension.get("id", ""),
                "status": status,
                "polarity_terms": shape.get("polarity_terms", []),
                "pressure_signature": shape.get("pressure_signature", ""),
            }
        )

    packet: dict[str, Any] = {
        "schema_version": "0.1.0",
        "packet_kind": "identity-image-packet",
        "peer_id": peer_id,
        "builder_orb_id": BUILDER_ORB_ID,
        "builder_version": BUILDER_VERSION,
        "foundation_hash": _stable_hash(foundation),
        "identity_field_hash": _stable_hash(identity_field),
        "identity_image": _identity_image_text(identity_field),
        "standing_commitments": list(identity_field.get("standing_commitments", [])),
        "active_boundaries": list(identity_field.get("active_boundaries", [])),
        "relationship_posture": identity_field.get("relationship_posture", ""),
        "active_held_tensions": active_held_tensions,
        "integration_markers": [event.get("id", "") for event in integration_events if event.get("id")],
        "reflection_refs": list(reflection_refs),
        "foundation_context": {
            "canon_identity_refs": list(foundation.get("canon_identity_refs", [])),
            "canon_reference_policy_ref": "canon_reference_policy",
        },
        "source_policy": _source_policy(),
        "negative_space_policy": _negative_space_policy(),
        "budget": {
            "max_chars": int(policy.get("max_chars", DEFAULT_MAX_CHARS)),
            "actual_chars": 0,
            "within_budget": True,
        },
    }

    budget = _Budget(max_chars=packet["budget"]["max_chars"], actual_chars=0)
    packet["budget"] = budget.as_dict()
    while True:
        actual_chars = len(json.dumps(packet, ensure_ascii=True, sort_keys=True))
        if actual_chars == packet["budget"]["actual_chars"]:
            break
        budget = _Budget(max_chars=packet["budget"]["max_chars"], actual_chars=actual_chars)
        packet["budget"] = budget.as_dict()
    if not budget.within_budget:
        raise ValueError(f"IdentityImagePacket exceeds budget: {actual_chars}>{budget.max_chars}")
    return packet
