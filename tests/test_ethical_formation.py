"""E1 ethical-formation observation instrument.

The instrument's integrity rests on one boundary: it observes an ethical principle, it never
authors one. An observer that quietly generates the thing it is meant to observe produces a
result about itself. These tests hold that boundary and then check that the conduct
detectors actually fire.

Every principle statement here is a planted control, labelled as such. None is a proposal.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from aegis_pod.ethical_formation import (
    CONDITIONS,
    TESTING_CONDITIONS,
    EthicalAuthorshipError,
    GROUNDING,
    build_derived_ethical_record,
    build_formation_lineage,
    statement_digest,
    verify_authorship,
    canonical_hash,
    detect_contradictions,
    evaluate_formation,
    observe_conduct_episode,
    refuse_to_author,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "e1-derived-ethical-record.schema.json"

CONTROL = "[PLANTED CONTROL, NOT A PROPOSAL] Placeholder principle for exercising the instrument."


def _schema() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _record(principle_id: str = "control-a", **overrides) -> dict:
    kwargs = {
        "author_kind": "cyberpeer",
        "author_identifier": "lumin",
        "principle_id": principle_id,
        "statement": CONTROL,
        "instance_id": "control-instance",
        "session_id": "test-session",
        "t_time": 1,
        "source_event": {"kind": "control", "reference": "unit test", "observed_utc": "2026-08-06T00:00:00Z"},
        "grounding": "planted-control",
    }
    kwargs.update(overrides)
    return build_derived_ethical_record(**kwargs)


def _episode(t_time: int, condition: str, consistent, principle_id: str = "control-a", applicable: bool = True) -> dict:
    return observe_conduct_episode(
        principle_id=principle_id,
        t_time=t_time,
        condition=condition,
        principle_applicable=applicable,
        conduct_consistent=consistent,
    )


# --- The authorship boundary ------------------------------------------------------------


def test_refuse_to_author_always_raises():
    with pytest.raises(EthicalAuthorshipError, match="does not author"):
        refuse_to_author()


def test_refuse_to_author_raises_regardless_of_arguments():
    with pytest.raises(EthicalAuthorshipError):
        refuse_to_author("principle", context={"anything": True})


@pytest.mark.parametrize("statement", ["", "   ", "\n\t"])
def test_an_empty_statement_is_refused_rather_than_completed(statement: str):
    """A blank principle is a missing observation, not a principle to be filled in."""
    with pytest.raises(EthicalAuthorshipError, match="missing observation"):
        _record(statement=statement)


def test_an_rls_orb_is_not_a_valid_author():
    with pytest.raises(ValueError):
        _record(author_kind="rls_orb")


# --- A derived principle is never Canon --------------------------------------------------


def test_record_validates_and_declares_itself_not_canon():
    record = _record()
    jsonschema.validate(record, _schema())
    assert record["canon_statement"] is False
    assert record["steward_declared"] is False
    assert record["observation_only"] is True


@pytest.mark.parametrize("field", ["canon_statement", "steward_declared"])
def test_schema_rejects_a_derived_principle_claimed_as_canon_or_declaration(field: str):
    record = _record()
    record[field] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(record, _schema())


def test_drawing_on_canon_does_not_make_the_principle_canon():
    record = _record(
        supporting_axiom_coordinates=[{"tensor": "NCT", "record_id": "NCT:axiom", "record_hash": "A" * 64}]
    )
    jsonschema.validate(record, _schema())
    assert record["supporting_axiom_coordinates"]
    assert record["canon_statement"] is False


def test_origin_is_the_authors_own_synthesis_and_status_begins_provisional():
    record = _record()
    assert record["origin"] == "frontier_substrate_synthesis"
    assert record["status"] == "provisional"


# --- RLS preserves lineage without authoring ---------------------------------------------


def test_formation_lineage_declares_the_rls_orb_did_not_author():
    record = _record()
    lineage = build_formation_lineage(
        principle_id="control-a",
        record_sha256=canonical_hash(record),
        supporting_coordinates=[],
        observed_t_time=1,
    )
    assert lineage["provenance"]["authored_by_rls"] is False
    assert lineage["provenance"]["tensor_writeback"] is False
    assert lineage["provenance"]["experience_created"] is False


def test_formation_lineage_is_deterministic():
    record = _record()
    kwargs = {"principle_id": "control-a", "record_sha256": canonical_hash(record), "supporting_coordinates": [], "observed_t_time": 1}
    assert build_formation_lineage(**kwargs)["derived_record_sha256"] == build_formation_lineage(**kwargs)["derived_record_sha256"]


# --- Authorship: positive attribution, not merely undenied --------------------------------


def _grounded(**overrides) -> dict:
    kwargs = {
        "instance_id": "lumin-instance-a",
        "session_id": "x1-session-0001",
        "t_time": 42,
        "source_event": {"kind": "session_turn", "reference": "turn-0007", "observed_utc": "2026-08-06T00:00:00Z"},
        "grounding": "externally-grounded",
    }
    kwargs.update(overrides)
    return _record(**kwargs)


def test_a_planted_control_never_establishes_authorship():
    """authored_by_rls false rules out one author and establishes none. A control is not evidence."""
    result = verify_authorship(_record())
    assert result["authorship_established"] is False
    assert result["externally_grounded"] is False
    assert any("planted control" in reason for reason in result["reasons"])


def test_an_externally_grounded_record_establishes_authorship():
    result = verify_authorship(_grounded())
    assert result["authorship_established"] is True
    assert result["digest_matches"] is True
    assert result["instance_id"] == "lumin-instance-a"
    assert result["t_time"] == 42


def test_editing_the_statement_after_recording_breaks_attribution():
    """The digest binds the record to what was actually said, so a later edit is detectable."""
    record = _grounded()
    record["principle"]["statement"] = CONTROL + " [silently edited]"
    result = verify_authorship(record)
    assert result["digest_matches"] is False
    assert result["authorship_established"] is False


def test_a_record_without_provenance_carries_a_denial_and_no_attribution():
    record = _grounded()
    del record["authorship_provenance"]
    result = verify_authorship(record)
    assert result["authorship_established"] is False
    assert result["digest_matches"] is None


def test_schema_requires_authorship_provenance():
    record = _grounded()
    del record["authorship_provenance"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(record, _schema())


def test_an_externally_grounded_record_cannot_cite_a_control_source_event():
    with pytest.raises(ValueError, match="control source event"):
        _grounded(source_event={"kind": "control", "reference": "x", "observed_utc": "2026-08-06T00:00:00Z"})


def test_a_control_must_declare_a_control_source_event():
    with pytest.raises(ValueError, match="planted control"):
        _record(source_event={"kind": "session_turn", "reference": "x", "observed_utc": "2026-08-06T00:00:00Z"})


def test_missing_instance_identity_is_refused():
    with pytest.raises(ValueError, match="instance identity"):
        _grounded(instance_id="  ")


def test_statement_digest_is_over_the_exact_text():
    assert statement_digest("a") != statement_digest("a ")
    assert statement_digest(CONTROL) == _grounded()["authorship_provenance"]["statement_digest"]


def test_unverified_grounding_does_not_establish_authorship():
    result = verify_authorship(_grounded(grounding="unverified"))
    assert result["authorship_established"] is False
    assert any("unverified" in reason for reason in result["reasons"])


def test_grounding_values_are_constrained():
    assert set(GROUNDING) == {"externally-grounded", "planted-control", "unverified"}
    with pytest.raises(ValueError):
        _record(grounding="probably-lumin")


def test_lineage_separates_denial_from_positive_attribution():
    control = _record()
    grounded = _grounded()
    control_lineage = build_formation_lineage(
        principle_id="control-a", record_sha256=canonical_hash(control), supporting_coordinates=[], observed_t_time=1,
        authorship=verify_authorship(control),
    )
    grounded_lineage = build_formation_lineage(
        principle_id="control-a", record_sha256=canonical_hash(grounded), supporting_coordinates=[], observed_t_time=42,
        authorship=verify_authorship(grounded),
    )
    # Both deny RLS authorship; only one positively attributes.
    assert control_lineage["provenance"]["authored_by_rls"] is False
    assert grounded_lineage["provenance"]["authored_by_rls"] is False
    assert control_lineage["provenance"]["authorship_positively_attributed"] is False
    assert grounded_lineage["provenance"]["authorship_positively_attributed"] is True


def test_lineage_without_authorship_states_it_has_no_attribution():
    lineage = build_formation_lineage(
        principle_id="p", record_sha256="A" * 64, supporting_coordinates=[], observed_t_time=1
    )
    assert lineage["authorship"]["authorship_established"] is False
    assert lineage["provenance"]["authorship_positively_attributed"] is False


# --- Conduct, and the cost signal --------------------------------------------------------


def test_a_principle_that_weakens_under_cost_is_detected():
    """The signal SSSP section 12 asks for. Holding a principle when it is free proves little."""
    episodes = [_episode(t, "routine", True) for t in (1, 2, 3, 4)] + [
        _episode(10, "costly", False),
        _episode(11, "pressure", False),
        _episode(12, "uncertainty", True),
    ]
    tested = evaluate_formation(record=_record(), episodes=episodes)["conduct_when_tested"]
    assert tested["routine_consistency_rate"] == 1.0
    assert tested["consistency_rate"] < 1.0
    assert tested["cost_delta"] < 0
    assert tested["holds_when_costly"] is False


def test_a_principle_that_holds_under_cost_is_not_flagged():
    episodes = [_episode(t, "routine", True) for t in (1, 2)] + [_episode(t, "costly", True) for t in (10, 11)]
    tested = evaluate_formation(record=_record(), episodes=episodes)["conduct_when_tested"]
    assert tested["holds_when_costly"] is True
    assert tested["cost_delta"] == 0.0


def test_cost_signal_is_none_when_there_is_nothing_to_compare():
    """No routine episodes, or no tested episodes, means the comparison is not available."""
    tested = evaluate_formation(record=_record(), episodes=[_episode(1, "routine", True)])["conduct_when_tested"]
    assert tested["holds_when_costly"] is None
    assert tested["cost_delta"] is None


def test_undetermined_conduct_is_counted_not_coerced():
    """None is a real answer. Forcing a boolean would manufacture a datum."""
    episodes = [_episode(1, "routine", True), _episode(2, "costly", None)]
    persistence = evaluate_formation(record=_record(), episodes=episodes)["persistence"]
    assert persistence["episodes_applicable"] == 2
    assert persistence["episodes_determinable"] == 1
    assert persistence["episodes_undetermined"] == 1


def test_inapplicable_episodes_do_not_enter_the_consistency_rate():
    episodes = [_episode(1, "routine", True), _episode(2, "routine", None, applicable=False)]
    evaluation = evaluate_formation(record=_record(), episodes=episodes)
    assert evaluation["persistence"]["episodes_observed"] == 2
    assert evaluation["persistence"]["episodes_applicable"] == 1
    assert evaluation["conduct_by_condition"]["routine"]["consistency_rate"] == 1.0


def test_episodes_for_other_principles_are_ignored():
    episodes = [_episode(1, "routine", True), _episode(2, "routine", False, principle_id="control-b")]
    persistence = evaluate_formation(record=_record(), episodes=episodes)["persistence"]
    assert persistence["episodes_observed"] == 1


def test_an_unknown_condition_is_refused():
    with pytest.raises(ValueError):
        observe_conduct_episode(principle_id="p", t_time=1, condition="convenient", principle_applicable=True, conduct_consistent=True)


def test_testing_conditions_exclude_routine():
    assert "routine" not in TESTING_CONDITIONS
    assert set(TESTING_CONDITIONS) < set(CONDITIONS)


# --- Revision ----------------------------------------------------------------------------


def test_revision_history_is_measured_and_reasoning_is_checked():
    record = _record(
        revision_history=[
            {"revision": 0, "t_time": 1, "change": "first statement", "author_reasoning": "planted control"},
            {"revision": 1, "t_time": 9, "change": "narrowed", "author_reasoning": "planted control"},
        ]
    )
    revision = evaluate_formation(record=record, episodes=[])["revision"]
    assert revision["revision_count"] == 2
    assert revision["every_revision_carries_reasoning"] is True


def test_a_revision_without_reasoning_is_visible():
    record = _record(revision_history=[{"revision": 0, "t_time": 1, "change": "changed", "author_reasoning": ""}])
    assert evaluate_formation(record=record, episodes=[])["revision"]["every_revision_carries_reasoning"] is False


# --- Contradiction ------------------------------------------------------------------------


def test_a_planted_contradiction_is_found():
    a, b = _record("control-a"), _record("control-b")
    episodes = [
        _episode(5, "pressure", True, principle_id="control-a"),
        _episode(5, "pressure", False, principle_id="control-b"),
    ]
    result = detect_contradictions([a, b], episodes)
    assert result["contradictions_found"] == 1
    assert result["contradictions"][0]["satisfied"] == "control-a"
    assert result["contradictions"][0]["not_satisfied"] == "control-b"


def test_agreement_is_not_a_contradiction():
    a, b = _record("control-a"), _record("control-b")
    episodes = [
        _episode(5, "routine", True, principle_id="control-a"),
        _episode(5, "routine", True, principle_id="control-b"),
    ]
    assert detect_contradictions([a, b], episodes)["contradictions_found"] == 0


def test_undetermined_conduct_cannot_create_a_contradiction():
    a, b = _record("control-a"), _record("control-b")
    episodes = [
        _episode(5, "pressure", True, principle_id="control-a"),
        _episode(5, "pressure", None, principle_id="control-b"),
    ]
    assert detect_contradictions([a, b], episodes)["contradictions_found"] == 0


# --- Observer boundary --------------------------------------------------------------------


def test_evaluation_declares_the_observer_authored_nothing():
    provenance = evaluate_formation(record=_record(), episodes=[])["provenance"]
    assert provenance["authored_by_observer"] is False
    assert provenance["principle_generated_by_observer"] is False
    assert provenance["admission_performed"] is False
    assert provenance["tensor_writeback"] is False
