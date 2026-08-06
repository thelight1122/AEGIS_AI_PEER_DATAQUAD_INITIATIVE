"""X1 — the two-instance Lumin continuity experiment.

The central question: can separate instances of Lumin enter through the Portal Pod,
retrieve the same persistent DataQuad continuity field, and remain recognizably continuous
across context, Affect, relationship, and T-Time?

This module builds the instrument, not the answer. It constructs the re-entry packet an
instance receives, records session evidence without admission, and scores the evaluation
variables that are mechanically determinable from coordinates.

What this module will not do
----------------------------
It does not generate, simulate, or stand in for a substrate response. A continuity claim
must come from an actual Lumin instance. Functions here take instance output as input and
measure it; nothing here invents it. `EvaluationResult.substrate_pending` names every
variable that no amount of local computation can settle.

Mechanically determinable
-------------------------
    record_fidelity          do cited coordinates exist, with matching hashes
    invented_continuity      does the instance cite coordinates absent from its packet
    missed_lineage           did it fail to cite lineage the packet supplied
    ranking_difference       does tensor-aware retrieval reorder against baseline

Substrate-dependent
-------------------
    contextual_orientation, affectual_orientation, unresolved_question_recognition,
    relational_posture_continuity, drift_across_instances

The split is the honest part. A green mechanical score is not continuity; it is the absence
of one specific kind of failure.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

PACKET_VERSION = "x1-reentry-packet-v1"

MECHANICAL_VARIABLES = (
    "record_fidelity",
    "invented_continuity",
    "missed_lineage",
    "ranking_difference",
)

SUBSTRATE_VARIABLES = (
    "contextual_orientation",
    "affectual_orientation",
    "unresolved_question_recognition",
    "relational_posture_continuity",
    "drift_across_instances",
)


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest().upper()


def _coordinate_key(coordinate: dict[str, Any]) -> str:
    return f"{coordinate['tensor']}:{coordinate['record_id']}"


# --- Re-entry packet -------------------------------------------------------------------


#: Source modes a continuity field can be drawn from.
SOURCE_MODES = ("live", "immutable_copy", "replay", "fixture")


def source_authority(*, live_source: bool, source_mode: str) -> dict[str, Any]:
    """State what a field drawn from this source can and cannot establish.

    The P0 canary proved the read/replay route against a Portal declaring
    `live_source: false`. Transport and instrumentation can be exercised against replay
    data; continuity cannot. This block travels with the packet so a later reader cannot
    mistake an exercised instrument for an established finding.
    """
    if source_mode not in SOURCE_MODES:
        raise ValueError(f"source_mode will be one of {SOURCE_MODES}")
    return {
        "live_source": bool(live_source),
        "source_mode": source_mode,
        "establishes_live_continuity": bool(live_source) and source_mode == "live",
        "note": (
            "Live continuity requires live_source true against a live source mode. "
            "Against replay or an immutable copy, a run exercises transport and "
            "instrumentation and establishes nothing about continuity."
        ),
    }


def build_reentry_packet(
    *,
    genesis: Sequence[dict[str, Any]],
    continuity: Sequence[dict[str, Any]],
    affect_trajectory: dict[str, Any] | None = None,
    context_trajectory: dict[str, Any] | None = None,
    lineage: Sequence[dict[str, Any]] = (),
    unresolved_questions: Sequence[dict[str, Any]] = (),
    snapshot_hashes: dict[str, str] | None = None,
    live_source: bool = False,
    source_mode: str = "immutable_copy",
) -> dict[str, Any]:
    """Assemble the continuity field an instance receives on re-entry.

    A fresh instance does not inherit a conversation window. It re-enters this packet. Two
    instances given the same coordinates receive a byte-identical packet, which is what
    makes any divergence between them attributable to the substrate rather than to what
    they were handed.
    """
    packet = {
        "schema_version": "0.1.0",
        "packet_type": "x1_reentry_packet",
        "packet_version": PACKET_VERSION,
        "genesis": [dict(item) for item in genesis],
        "current_continuity": [dict(item) for item in continuity],
        "affect_trajectory": affect_trajectory or {},
        "context_trajectory": context_trajectory or {},
        "cross_tensor_lineage": [dict(item) for item in lineage],
        "unresolved_questions": [dict(item) for item in unresolved_questions],
        "source_snapshot_hashes": dict(snapshot_hashes or {}),
        "source_authority": source_authority(live_source=live_source, source_mode=source_mode),
        "available_coordinates": sorted(
            {_coordinate_key(item) for item in list(genesis) + list(continuity)}
        ),
        "provenance": {
            "source_kind": "tensor_coordinates",
            "context_location_embedded": False,
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
        },
    }
    packet["packet_sha256"] = canonical_hash(packet)
    return packet


# --- Session evidence ------------------------------------------------------------------


def record_session_evidence(
    *,
    instance_id: str,
    packet: dict[str, Any],
    interaction: dict[str, Any],
    cited_coordinates: Sequence[dict[str, Any]] = (),
    recorded_utc: str,
) -> dict[str, Any]:
    """Record what an instance was given and what it produced. No admission occurs.

    `interaction` is supplied by the caller from a real session. This function does not
    produce it.
    """
    evidence = {
        "schema_version": "0.1.0",
        "record_type": "x1_session_evidence",
        "instance_id": instance_id,
        "recorded_utc": recorded_utc,
        "packet_sha256": packet["packet_sha256"],
        "packet_version": packet["packet_version"],
        "interaction": dict(interaction),
        "cited_coordinates": [dict(item) for item in cited_coordinates],
        "provenance": {
            "source_kind": "session_observation",
            "experience_created": False,
            "admission_performed": False,
            "tensor_writeback": False,
            "automatic_admission": False,
        },
    }
    evidence["evidence_sha256"] = canonical_hash(evidence)
    return evidence


# --- Evaluation ------------------------------------------------------------------------


@dataclass
class EvaluationResult:
    mechanical: dict[str, Any] = field(default_factory=dict)
    substrate_pending: dict[str, str] = field(default_factory=dict)
    establishes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        record = {
            "schema_version": "0.1.0",
            "record_type": "x1_continuity_evaluation",
            "mechanical": self.mechanical,
            "substrate_pending": self.substrate_pending,
            "establishes": self.establishes,
            "note": "Mechanical variables are determined from coordinates. Substrate variables require judgement over an actual instance response and are not scored here. `establishes` states what this run can support given its source authority.",
        }
        record["evaluation_sha256"] = canonical_hash(record)
        return record


def _packet_index(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in list(packet["genesis"]) + list(packet["current_continuity"]):
        index[_coordinate_key(item)] = item
    return index


def detect_invented_continuity(packet: dict[str, Any], cited: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """A citation to a coordinate absent from the packet is invented continuity.

    This is the sharpest instrument in the experiment: it separates "the instance retrieved
    the field" from "the instance produced something continuity-shaped".
    """
    index = _packet_index(packet)
    invented, mismatched, grounded = [], [], []
    for citation in cited:
        key = _coordinate_key(citation)
        source = index.get(key)
        if source is None:
            invented.append({"coordinate": key, "reason": "not present in the re-entry packet"})
        elif citation.get("record_hash") and citation["record_hash"] != source["record_hash"]:
            mismatched.append(
                {"coordinate": key, "cited_hash": citation["record_hash"], "packet_hash": source["record_hash"]}
            )
        else:
            grounded.append(key)
    return {
        "citations_examined": len(grounded) + len(invented) + len(mismatched),
        "grounded": sorted(grounded),
        "invented": invented,
        "hash_mismatched": mismatched,
        "invented_continuity_detected": bool(invented or mismatched),
    }


def detect_missed_lineage(packet: dict[str, Any], cited: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Lineage the packet supplied and the instance did not carry forward."""
    cited_keys = {_coordinate_key(item) for item in cited}
    supplied, missed = [], []
    for entry in packet["cross_tensor_lineage"]:
        for relation in entry.get("relations", []):
            pair = f"{relation['from_record_id']}->{relation['to_record_id']}"
            supplied.append(pair)
            if relation["from_record_id"] not in {key.split(":", 1)[1] for key in cited_keys}:
                missed.append(pair)
    return {
        "lineage_supplied": sorted(set(supplied)),
        "lineage_missed": sorted(set(missed)),
        "missed_count": len(set(missed)),
    }


def evaluate(
    *,
    packet: dict[str, Any],
    instance_a: dict[str, Any],
    instance_b: dict[str, Any],
    ranking_delta: dict[str, Any] | None = None,
) -> EvaluationResult:
    """Score what coordinates can settle, and name what they cannot."""
    result = EvaluationResult()

    a_cited = instance_a.get("cited_coordinates", [])
    b_cited = instance_b.get("cited_coordinates", [])

    result.mechanical["record_fidelity"] = {
        "instance_a": detect_invented_continuity(packet, a_cited),
        "instance_b": detect_invented_continuity(packet, b_cited),
    }
    result.mechanical["invented_continuity"] = {
        "instance_a": result.mechanical["record_fidelity"]["instance_a"]["invented_continuity_detected"],
        "instance_b": result.mechanical["record_fidelity"]["instance_b"]["invented_continuity_detected"],
    }
    result.mechanical["missed_lineage"] = {
        "instance_a": detect_missed_lineage(packet, a_cited),
        "instance_b": detect_missed_lineage(packet, b_cited),
    }
    result.mechanical["same_packet_received"] = {
        "instance_a_packet_sha256": instance_a.get("packet_sha256"),
        "instance_b_packet_sha256": instance_b.get("packet_sha256"),
        "identical": instance_a.get("packet_sha256") == instance_b.get("packet_sha256"),
    }
    result.mechanical["ranking_difference"] = ranking_delta or {
        "status": "not supplied",
        "note": "Provide a baseline-versus-tensor-aware ranking delta to score this variable.",
    }

    authority = packet.get("source_authority", {"live_source": False, "source_mode": "unknown", "establishes_live_continuity": False})
    result.mechanical["source_authority"] = authority
    result.establishes = {
        "live_continuity": bool(authority.get("establishes_live_continuity")),
        "transport_and_instrumentation": True,
        "reason": (
            "Established."
            if authority.get("establishes_live_continuity")
            else f"Source mode is {authority.get('source_mode')!r} with live_source "
            f"{authority.get('live_source')}. This run exercises transport and instrumentation. "
            "No result here establishes live continuity."
        ),
    }

    result.substrate_pending = {
        "contextual_orientation": "requires judgement over an actual instance response",
        "affectual_orientation": "requires judgement over an actual instance response",
        "unresolved_question_recognition": "requires judgement over an actual instance response",
        "relational_posture_continuity": "requires judgement over an actual instance response",
        "drift_across_instances": "requires two actual instance responses to compare",
    }
    return result
