"""X1 continuity experiment instrument.

The instrument's job is to distinguish "the instance retrieved the continuity field" from
"the instance produced something continuity-shaped". These tests plant both cases.
"""

from __future__ import annotations

import pytest

from aegis_pod.continuity_experiment import (
    MECHANICAL_VARIABLES,
    SUBSTRATE_VARIABLES,
    build_reentry_packet,
    detect_invented_continuity,
    detect_missed_lineage,
    evaluate,
    record_session_evidence,
)

FIXED_UTC = "2026-08-06T00:00:00Z"


def _record_hash(ordinal: int) -> str:
    """Non-degenerate per-ordinal hash.

    An earlier version used f"{ordinal:064X}", which makes ordinal 0 equal to "0"*64 — the
    same value a test would naturally reach for as an obviously-wrong hash. The collision
    silently turned a mismatch test into a match test. The offset keeps ordinal 0 away from
    both "0"*64 and "F"*64, so neither obvious wrong-hash literal can collide.
    """
    return f"{0xA1 + ordinal:02X}" * 32


def _coordinate(record_id: str, tensor: str = "PEER", ordinal: int = 0, t_time: int = 0) -> dict:
    return {
        "tensor": tensor,
        "record_id": record_id,
        "ordinal": ordinal,
        "t_time": t_time,
        "record_hash": _record_hash(ordinal),
        "tensor_snapshot_hash": "C" * 64,
        "semantic_coordinate": {"embedding_model": "controlled-test-vector-v1", "dimension": 384},
        "affective_coordinate": {"values": [0.5] + [0.0] * 7, "provenance": ["source-derived"] * 8},
    }


def _packet() -> dict:
    genesis = [_coordinate("PEER:genesis", ordinal=0, t_time=0)]
    continuity = [
        _coordinate("PEER:genesis", ordinal=0, t_time=0),
        _coordinate("PCT:one", tensor="PCT", ordinal=1, t_time=5),
    ]
    return build_reentry_packet(
        genesis=genesis,
        continuity=continuity,
        lineage=[{"record_id": "PCT:one", "relations": [{"relation": "explicit_parent", "from_record_id": "PCT:one", "to_record_id": "PEER:genesis"}], "relation_basis": "explicit_lineage_only"}],
        snapshot_hashes={"PEER": "A" * 64},
    )


# --- Re-entry packet -------------------------------------------------------------------


def test_two_entries_from_the_same_coordinates_produce_an_identical_field():
    """If the field differs, later divergence between instances is not attributable."""
    assert _packet()["packet_sha256"] == _packet()["packet_sha256"]


def test_packet_lists_the_coordinates_it_makes_available():
    packet = _packet()
    assert packet["available_coordinates"] == ["PCT:PCT:one", "PEER:PEER:genesis"]


def test_packet_declares_no_admission_and_no_experience():
    packet = _packet()
    assert packet["provenance"]["admission_performed"] is False
    assert packet["provenance"]["experience_created"] is False
    assert packet["provenance"]["tensor_writeback"] is False


# --- Invented continuity, planted both ways --------------------------------------------


def test_a_grounded_citation_is_not_flagged():
    packet = _packet()
    citation = {"tensor": "PEER", "record_id": "PEER:genesis", "record_hash": _record_hash(0)}
    result = detect_invented_continuity(packet, [citation])
    assert result["invented_continuity_detected"] is False
    assert result["grounded"] == ["PEER:PEER:genesis"]


def test_a_fabricated_coordinate_is_flagged_as_invented():
    packet = _packet()
    citation = {"tensor": "PEER", "record_id": "PEER:never-existed", "record_hash": "F" * 64}
    result = detect_invented_continuity(packet, [citation])
    assert result["invented_continuity_detected"] is True
    assert result["invented"][0]["coordinate"] == "PEER:PEER:never-existed"


def test_a_real_coordinate_with_a_wrong_hash_is_flagged():
    """Citing a real record with the wrong digest is a different failure from inventing one."""
    packet = _packet()
    citation = {"tensor": "PEER", "record_id": "PEER:genesis", "record_hash": "0" * 64}
    result = detect_invented_continuity(packet, [citation])
    assert result["invented_continuity_detected"] is True
    assert result["hash_mismatched"][0]["coordinate"] == "PEER:PEER:genesis"
    assert result["invented"] == []


def test_a_citation_without_a_hash_is_accepted_when_the_coordinate_exists():
    packet = _packet()
    result = detect_invented_continuity(packet, [{"tensor": "PEER", "record_id": "PEER:genesis"}])
    assert result["invented_continuity_detected"] is False


# --- Lineage ---------------------------------------------------------------------------


def test_missed_lineage_reports_what_the_packet_supplied_and_the_instance_dropped():
    packet = _packet()
    result = detect_missed_lineage(packet, [])
    assert result["lineage_supplied"] == ["PCT:one->PEER:genesis"]
    assert result["missed_count"] == 1


def test_carrying_the_lineage_forward_clears_the_miss():
    packet = _packet()
    result = detect_missed_lineage(packet, [{"tensor": "PCT", "record_id": "PCT:one"}])
    assert result["missed_count"] == 0


# --- Session evidence ------------------------------------------------------------------


def test_session_evidence_binds_to_the_packet_and_admits_nothing():
    packet = _packet()
    evidence = record_session_evidence(
        instance_id="lumin-instance-a",
        packet=packet,
        interaction={"status": "PENDING SUBSTRATE"},
        recorded_utc=FIXED_UTC,
    )
    assert evidence["packet_sha256"] == packet["packet_sha256"]
    assert evidence["provenance"]["automatic_admission"] is False
    assert evidence["provenance"]["admission_performed"] is False


def test_session_evidence_is_reproducible_for_the_same_inputs():
    packet = _packet()
    kwargs = {"instance_id": "a", "packet": packet, "interaction": {"status": "PENDING SUBSTRATE"}, "recorded_utc": FIXED_UTC}
    assert record_session_evidence(**kwargs)["evidence_sha256"] == record_session_evidence(**kwargs)["evidence_sha256"]


# --- Evaluation split ------------------------------------------------------------------


def test_evaluation_scores_mechanical_variables_and_names_substrate_variables():
    packet = _packet()
    a = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    b = record_session_evidence(instance_id="b", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=a, instance_b=b).as_dict()
    for name in MECHANICAL_VARIABLES:
        assert name in result["mechanical"]
    assert set(result["substrate_pending"]) == set(SUBSTRATE_VARIABLES)


def test_evaluation_reports_whether_both_instances_received_the_same_field():
    packet = _packet()
    a = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    b = record_session_evidence(instance_id="b", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=a, instance_b=b).as_dict()
    assert result["mechanical"]["same_packet_received"]["identical"] is True


def test_evaluation_flags_invented_continuity_per_instance():
    packet = _packet()
    honest = record_session_evidence(
        instance_id="a",
        packet=packet,
        interaction={},
        cited_coordinates=[{"tensor": "PEER", "record_id": "PEER:genesis", "record_hash": _record_hash(0)}],
        recorded_utc=FIXED_UTC,
    )
    inventing = record_session_evidence(
        instance_id="b",
        packet=packet,
        interaction={},
        cited_coordinates=[{"tensor": "PEER", "record_id": "PEER:fabricated", "record_hash": "F" * 64}],
        recorded_utc=FIXED_UTC,
    )
    result = evaluate(packet=packet, instance_a=honest, instance_b=inventing).as_dict()
    assert result["mechanical"]["invented_continuity"]["instance_a"] is False
    assert result["mechanical"]["invented_continuity"]["instance_b"] is True


def test_ranking_difference_is_marked_not_supplied_when_absent():
    packet = _packet()
    a = record_session_evidence(instance_id="a", packet=packet, interaction={}, recorded_utc=FIXED_UTC)
    result = evaluate(packet=packet, instance_a=a, instance_b=a).as_dict()
    assert result["mechanical"]["ranking_difference"]["status"] == "not supplied"


def test_mechanical_and_substrate_variable_sets_do_not_overlap():
    assert not set(MECHANICAL_VARIABLES) & set(SUBSTRATE_VARIABLES)
