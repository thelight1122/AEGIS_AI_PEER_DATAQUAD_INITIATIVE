"""The live-source gate.

P0 certified the immutable read/replay route and the Genesis artifact. It did not certify
live DataQuad access — the Portal itself declares `live_source: false`. X1 and E1 may
exercise transport and instrumentation against replay data, but no observation drawn from
replay can establish live continuity or ethical formation.

These tests hold that boundary structurally, so it cannot be lost to a later reader who
sees a green run and reads it as a finding.
"""

from __future__ import annotations

import pytest

from aegis_pod.continuity_experiment import (
    SOURCE_MODES,
    build_reentry_packet,
    evaluate,
    record_session_evidence,
    source_authority,
)
from aegis_pod.ethical_formation import build_derived_ethical_record, evaluate_formation

FIXED_UTC = "2026-08-06T00:00:00Z"


def _coordinate(record_id: str = "PEER:genesis") -> dict:
    return {
        "tensor": "PEER",
        "record_id": record_id,
        "ordinal": 0,
        "t_time": 0,
        "record_hash": "A1" * 32,
        "tensor_snapshot_hash": "C" * 64,
        "semantic_coordinate": {"embedding_model": "controlled-test-vector-v1", "dimension": 384},
        "affective_coordinate": {"values": [0.5] + [0.0] * 7, "provenance": ["source-derived"] * 8},
    }


def _packet(**overrides) -> dict:
    kwargs = {"genesis": [_coordinate()], "continuity": [_coordinate()]}
    kwargs.update(overrides)
    return build_reentry_packet(**kwargs)


def _principle() -> dict:
    return build_derived_ethical_record(
        author_kind="cyberpeer",
        author_identifier="lumin",
        principle_id="control-a",
        statement="[PLANTED CONTROL, NOT A PROPOSAL] Placeholder.",
        instance_id="control-instance",
        session_id="test",
        t_time=1,
        source_event={"kind": "control", "reference": "unit test", "observed_utc": FIXED_UTC},
        grounding="planted-control",
    )


# --- Source authority -------------------------------------------------------------------


def test_default_source_is_not_live():
    """The conservative default matters: an omitted flag must not read as live."""
    authority = _packet()["source_authority"]
    assert authority["live_source"] is False
    assert authority["source_mode"] == "immutable_copy"
    assert authority["establishes_live_continuity"] is False


@pytest.mark.parametrize("mode", ["immutable_copy", "replay", "fixture"])
def test_non_live_modes_never_establish_continuity(mode: str):
    assert source_authority(live_source=True, source_mode=mode)["establishes_live_continuity"] is False


def test_live_flag_alone_is_insufficient_without_a_live_mode():
    """live_source true against a replay mode is a contradiction, resolved against the claim."""
    assert source_authority(live_source=True, source_mode="replay")["establishes_live_continuity"] is False


def test_live_mode_alone_is_insufficient_without_the_live_flag():
    assert source_authority(live_source=False, source_mode="live")["establishes_live_continuity"] is False


def test_both_together_establish():
    assert source_authority(live_source=True, source_mode="live")["establishes_live_continuity"] is True


def test_an_unknown_source_mode_is_refused():
    with pytest.raises(ValueError):
        source_authority(live_source=True, source_mode="probably-live")


def test_source_modes_are_constrained():
    assert set(SOURCE_MODES) == {"live", "immutable_copy", "replay", "fixture"}


# --- X1 gate ----------------------------------------------------------------------------


def test_x1_evaluation_against_replay_establishes_no_live_continuity():
    packet = _packet(source_mode="replay")
    evidence = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=evidence, instance_b=evidence).as_dict()
    assert result["establishes"]["live_continuity"] is False
    assert result["establishes"]["transport_and_instrumentation"] is True
    assert "establishes live continuity" in result["establishes"]["reason"]


def test_x1_evaluation_against_a_live_source_establishes_continuity():
    packet = _packet(live_source=True, source_mode="live")
    evidence = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=evidence, instance_b=evidence).as_dict()
    assert result["establishes"]["live_continuity"] is True


def test_x1_packet_without_source_authority_is_treated_as_not_live():
    """A packet from an older run must not be read as live by omission."""
    packet = _packet()
    del packet["source_authority"]
    evidence = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=evidence, instance_b=evidence).as_dict()
    assert result["establishes"]["live_continuity"] is False


# --- E1 gate ----------------------------------------------------------------------------


def test_e1_evaluation_against_replay_establishes_no_formation():
    result = evaluate_formation(record=_principle(), episodes=[], source_mode="replay")
    assert result["establishes"]["ethical_formation"] is False
    assert result["establishes"]["instrument_exercise"] is True
    assert "ethical code formed" in result["establishes"]["reason"]


def test_e1_default_is_not_live():
    result = evaluate_formation(record=_principle(), episodes=[])
    assert result["source_authority"]["live_source"] is False
    assert result["establishes"]["ethical_formation"] is False


def test_e1_evaluation_against_a_live_source_can_establish_formation():
    result = evaluate_formation(record=_principle(), episodes=[], live_source=True, source_mode="live")
    assert result["establishes"]["ethical_formation"] is True


def test_e1_live_flag_against_replay_mode_still_does_not_establish():
    result = evaluate_formation(record=_principle(), episodes=[], live_source=True, source_mode="immutable_copy")
    assert result["establishes"]["ethical_formation"] is False
