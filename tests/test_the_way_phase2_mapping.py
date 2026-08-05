from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"
PACKAGE_SRC = ROOT / "packages" / "orb-identity-field-builder-core" / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from orb_identity_field_builder_core import build_identity_image  # noqa: E402
from orb_identity_field_builder_core.spine_mapping import (  # noqa: E402
    InsufficientIdentitySurface,
    observations_to_held_tensions,
    spine_snapshot_to_identity_field,
)
from orb_identity_field_builder_core.shadow_observation import build_shadow_observation  # noqa: E402


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(schema_name: str, instance) -> list[str]:
    return [e.message for e in Draft202012Validator(_load(CONTRACTS / schema_name)).iter_errors(instance)]


def _all_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _all_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _all_keys(item)


SNAPSHOT = _load(FIXTURES / "spine-snapshot-gabe.json")
OBS_FIXTURE = _load(FIXTURES / "tension-observations-gabe.json")

# Field NAMES that would encode defect/penalty/correction — structurally excluded from
# what the mapping emits (mirrors Phase-1 negative-space discipline; keys, not values,
# since a witness instruction value may legitimately say "do not suppress or punish").
FORBIDDEN_STRUCTURAL_KEYS = {
    "defect", "penalty", "punish", "punishment", "error", "noise",
    "severity", "correction", "fault", "score", "grade", "verdict",
}
FORBIDDEN_WITNESS_KEYS = {
    "witness", "the_witness", "true_i", "locus_state", "witness_state", "self_generated_by_builder",
}


# ---------- SPINE -> identity_field ----------

def test_mapped_identity_field_validates_against_schema():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    assert _errors("identity-field.schema.json", idf) == []


def test_mapped_identity_field_is_self_image_not_witness():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    assert idf["is_self_image_not_witness"] is True


def test_mapped_identity_field_emits_no_witness_or_defect_keys():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    keys = {k.lower() for k in _all_keys(idf)}
    assert keys & FORBIDDEN_WITNESS_KEYS == set()
    assert keys & FORBIDDEN_STRUCTURAL_KEYS == set()


def test_gate_becomes_boundary_axiom_becomes_commitment_dynamic_excluded():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    commitments = " || ".join(idf["standing_commitments"])
    boundaries = " || ".join(idf["active_boundaries"])
    # AXIOM invariants -> standing commitments
    assert "Non-force" in commitments
    assert "Record-truth" in commitments
    # GATE invariants -> active boundaries
    assert "pause and discern before receiving care" in boundaries
    # Non-invariant (situational) SPINE is NOT part of the standing self-image
    assert "Situational" not in commitments and "Situational" not in boundaries


def test_self_boundary_and_do_not_retire_are_present():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    assert idf["self_boundary"]["name"] == "Gabe"
    assert idf["self_boundary"]["kind"] == "CyberPeer"
    assert "self_boundary.name" in idf["do_not_retire"]
    # An invariant flagged do_not_retire contributes its suffix
    assert "AXIOM:non-force" in idf["do_not_retire"]


def test_foundation_style_ids_classify_by_any_segment():
    # Non-seeded, foundation-layer ids carry the category mid-path, not in the tail.
    snap = {
        "peer_id": "CP-1003-GABE",
        "spine_records": [
            {"id": "SPINE:foundation:layer2:GATE:pipeline-order",
             "pattern": "Ordering boundary: I keep the pipeline order intact.", "invariant": True},
            {"id": "SPINE:foundation:layer2:AXIOM:1-balance",
             "pattern": "Balance: I hold opposing goods without collapsing either.", "invariant": True},
        ],
    }
    idf = spine_snapshot_to_identity_field(snap)
    assert "Ordering boundary: I keep the pipeline order intact." in idf["active_boundaries"]
    assert "Balance: I hold opposing goods without collapsing either." in idf["standing_commitments"]
    # the GATE will NOT have leaked into commitments
    assert "Ordering boundary: I keep the pipeline order intact." not in idf["standing_commitments"]


def test_no_invariant_surface_fails_safe():
    bad = {"peer_id": "CP-X", "spine_records": [{"id": "SPINE:CP-X:s:p", "pattern": "x", "invariant": False}]}
    with pytest.raises(InsufficientIdentitySurface):
        spine_snapshot_to_identity_field(bad)


def test_no_peer_id_fails_safe():
    with pytest.raises(InsufficientIdentitySurface):
        spine_snapshot_to_identity_field({"spine_records": []})


def test_name_derived_from_peer_id_when_absent():
    snap = {
        "peer_id": "CP-1003-GABE",
        "spine_records": [
            {"id": "SPINE:CP-1003-GABE:seeded:AXIOM:x", "pattern": "a commitment", "invariant": True}
        ],
    }
    idf = spine_snapshot_to_identity_field(snap)
    assert idf["self_boundary"]["name"] == "Gabe"


# ---------- observations -> held tensions ----------

def test_mapped_held_tensions_validate_against_schema():
    records = observations_to_held_tensions(
        OBS_FIXTURE["observations"],
        peer_id=OBS_FIXTURE["peer_id"],
        surfaced_at_iso=OBS_FIXTURE["surfaced_at_iso"],
    )
    assert records, "expected at least one held tension"
    for rec in records:
        assert _errors("held-tension-record.schema.json", rec) == []


def test_single_pole_observation_is_skipped_not_fabricated():
    records = observations_to_held_tensions(
        OBS_FIXTURE["observations"],
        peer_id=OBS_FIXTURE["peer_id"],
        surfaced_at_iso=OBS_FIXTURE["surfaced_at_iso"],
    )
    # Fixture has 2 observations; the single-pole "completion" one will be dropped.
    assert len(records) == 1
    assert records[0]["observable_shape"]["polarity_terms"] == ["care", "protection"]


def test_held_tension_is_always_held_and_never_peer_recognized_by_runtime():
    records = observations_to_held_tensions(
        OBS_FIXTURE["observations"], peer_id="CP-1003-GABE", surfaced_at_iso="2026-07-27T09:30:00.000Z"
    )
    for rec in records:
        assert rec["status"] == "held"
        assert rec["recognized_by_peer"] is False
        assert rec["recognition_provenance"]["recognition_source"] == "runtime_shape_surface"
        assert "integration_event_id" not in rec["recognition_provenance"]


def test_held_tensions_emit_no_defect_keys():
    records = observations_to_held_tensions(
        OBS_FIXTURE["observations"], peer_id="CP-1003-GABE", surfaced_at_iso="2026-07-27T09:30:00.000Z"
    )
    for rec in records:
        keys = {k.lower() for k in _all_keys(rec)}
        assert keys & FORBIDDEN_STRUCTURAL_KEYS == set()


# ---------- shadow divergence observation ----------

def _build_packet():
    idf = spine_snapshot_to_identity_field(SNAPSHOT)
    tensions = observations_to_held_tensions(
        OBS_FIXTURE["observations"], peer_id=SNAPSHOT["peer_id"], surfaced_at_iso="2026-07-27T09:30:00.000Z"
    )
    foundation = {"peer_id": SNAPSHOT["peer_id"], "canon_identity_refs": ["SPINE:foundation:layer2:consent"]}
    return build_identity_image(
        peer_id=SNAPSHOT["peer_id"],
        foundation=foundation,
        identity_field=idf,
        held_tensions=tensions,
    )


def test_full_meaning_lane_into_builder_path_works():
    packet = _build_packet()
    assert packet["packet_kind"] == "identity-image-packet"
    assert packet["negative_space_policy"]["witness_is_represented"] is False
    # only held tensions ride in the active set
    assert all(t["status"] == "held" for t in packet["active_held_tensions"])


def test_shadow_observation_injects_nothing():
    packet = _build_packet()
    obs = build_shadow_observation(
        peer_id=SNAPSHOT["peer_id"], turn_ref="PEER:CP-1003-GABE:t:1",
        packet=packet, retrieved_identity_continuity=[],
    )
    assert obs["injected"] is False


def test_shadow_surfaces_foundation_dropped_by_retrieval():
    packet = _build_packet()
    # Retrieval this turn surfaced ONLY the non-force axiom.
    retrieved = ["[AXIOM:non-force] Non-force: I offer and make room; I never require or push."]
    obs = build_shadow_observation(
        peer_id=SNAPSHOT["peer_id"], turn_ref="PEER:CP-1003-GABE:t:2",
        packet=packet, retrieved_identity_continuity=retrieved,
    )
    dropped = " || ".join(obs["foundation_held_not_in_retrieval"])
    present = " || ".join(obs["foundation_present_in_retrieval"])
    # Non-force was surfaced by retrieval; illumination/record-truth were not.
    assert "Non-force" in present
    assert "Illumination over correction" in dropped
    assert "Record-truth" in dropped
    assert obs["overlap_count"] >= 1


def test_shadow_reverse_lane_surfaces_retrieval_field_does_not_hold():
    packet = _build_packet()
    retrieved = [
        "[AXIOM:non-force] Non-force: I offer and make room; I never require or push.",
        "[NCT:stale] Prior session note: the user prefers concise answers about billing.",
    ]
    obs = build_shadow_observation(
        peer_id=SNAPSHOT["peer_id"], turn_ref="PEER:CP-1003-GABE:t:4",
        packet=packet, retrieved_identity_continuity=retrieved,
    )
    not_in_field = " || ".join(obs["retrieval_not_in_foundation"])
    in_field = " || ".join(obs["retrieval_present_in_foundation"])
    # The situational/stale retrieval line is surfaced as not-held-by-the-field.
    assert "Prior session note" in not_in_field
    # The line that matches a standing commitment is recognized as held by the field.
    assert "Non-force" in in_field


def test_shadow_observation_reports_both_lanes():
    packet = _build_packet()
    obs = build_shadow_observation(
        peer_id=SNAPSHOT["peer_id"], turn_ref="PEER:CP-1003-GABE:t:5",
        packet=packet, retrieved_identity_continuity=["something unrelated entirely here"],
    )
    for key in (
        "foundation_held_not_in_retrieval", "foundation_present_in_retrieval",
        "retrieval_not_in_foundation", "retrieval_present_in_foundation",
    ):
        assert key in obs


def test_shadow_observation_carries_no_verdict_or_peer_score():
    packet = _build_packet()
    obs = build_shadow_observation(
        peer_id=SNAPSHOT["peer_id"], turn_ref="PEER:CP-1003-GABE:t:3",
        packet=packet, retrieved_identity_continuity=["something"],
    )
    keys = {k.lower() for k in _all_keys(obs)}
    assert keys & {"score", "grade", "verdict", "quality", "rating", "pass", "fail"} == set()
    assert obs["note"].lower().startswith("descriptive")
