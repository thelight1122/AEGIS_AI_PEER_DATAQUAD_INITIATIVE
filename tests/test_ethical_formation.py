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
    build_derived_ethical_record,
    build_formation_lineage,
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
