"""Tests for the v0 affect-read instrument (ADR-0008)."""

import math

import pytest

from aegis_verus_lab.affect_read import (
    SEVEN_VIRTUES,
    REDUCTION_POLICY_ID,
    build_affect_read,
    classify_field_state,
    reduce_virtues_to_affect_axes,
)
from aegis_verus_lab.turn_contract import AppendIntent


def _full(v=0.5):
    return {name: v for name in SEVEN_VIRTUES}


def test_seven_virtues_are_the_canonical_set():
    assert SEVEN_VIRTUES == (
        "Honesty", "Respect", "Attention", "Affection", "Loyalty", "Trust", "Communication",
    )


def test_reduction_math_v0():
    virtues = {
        "Honesty": 0.9, "Respect": 0.85, "Attention": 0.9, "Affection": 0.6,
        "Loyalty": 0.7, "Trust": 0.85, "Communication": 0.95,
    }
    axes = reduce_virtues_to_affect_axes(virtues)
    # values are rounded to 6 dp by the module; compare with matching tolerance
    # a1 salience = mean of all seven
    assert math.isclose(axes["a1_affect_salience"]["value"], sum(virtues.values()) / 7, abs_tol=1e-6)
    # a2 bond = mean(Affection, Loyalty, Trust, Respect)
    assert math.isclose(axes["a2_relationship_bond"]["value"], (0.6 + 0.7 + 0.85 + 0.85) / 4, abs_tol=1e-6)
    # a3 certainty = mean(Honesty, Communication, Attention)
    assert math.isclose(axes["a3_certainty"]["value"], (0.9 + 0.95 + 0.9) / 3, abs_tol=1e-6)
    # provenance is policy-assigned (T) and carries the policy id
    for a in axes.values():
        assert a["provenance"] == "T"
        assert a["policy"] == REDUCTION_POLICY_ID


def test_reduction_rejects_bad_input():
    with pytest.raises(ValueError):
        reduce_virtues_to_affect_axes({"Honesty": 0.5})  # missing virtues
    with pytest.raises(ValueError):
        reduce_virtues_to_affect_axes({**_full(), "Mercy": 0.5})  # unknown key
    with pytest.raises(ValueError):
        reduce_virtues_to_affect_axes({**_full(), "Honesty": 1.5})  # out of range


def test_field_state_gate_selection():
    rising = classify_field_state(amplitude=0.8)
    assert rising["coherence_gate"] == "IDR"
    stable = classify_field_state(amplitude=0.2, stable=True)
    assert stable["coherence_gate"] == "IDQRA"
    balanced = classify_field_state(amplitude=0.5)
    assert balanced["coherence_gate"] == "IDS"


def test_field_state_pressure_band_and_validation():
    hi = classify_field_state(amplitude=0.7, force_signals=["coercive_certainty"], t_witness="thinning")
    assert hi["pressure_band"] == "high"
    lo = classify_field_state(amplitude=0.1, stable=True)
    assert lo["pressure_band"] == "low"
    with pytest.raises(ValueError):
        classify_field_state(force_signals=["not_a_signal"])
    with pytest.raises(ValueError):
        classify_field_state(t_witness="vaporized")


def test_build_affect_read_is_a_valid_PEER_append():
    virtues = _full(0.7)
    fs = classify_field_state(amplitude=0.4, force_signals=[], t_witness="intact")
    payload = build_affect_read(
        virtues=virtues, field_state=fs, subject="unit-test exchange",
    )
    # raw 7-vector retained with source provenance
    assert set(payload["seven_virtue_resonance"]) == set(SEVEN_VIRTUES)
    assert payload["seven_virtue_resonance"]["Trust"]["provenance"] == "S"
    # only the affect axes a1,a2,a3 are set here
    assert set(payload["affect_axes"]) == {"a1_affect_salience", "a2_relationship_bond", "a3_certainty"}
    # magnitude-preservation requirement is carried
    assert "magnitude_preserving" in payload["scoring_policy_requirement"]
    # admission separation is recorded
    assert "not admitted experience" in payload["admission_separation"]
    # and it validates as a real PEER append against the DataQuad contract
    AppendIntent("PEER", payload).validate()


# --- POD seam: RLS orb umbilical input_contract ---

from aegis_verus_lab.affect_read import to_pressure_state, build_rls_orb_input


_PRESSURE_ALLOWED = {
    "schema_version", "id", "peer_id", "pressure_level", "pressure_class",
    "dis_integrity_signal", "source_refs", "is_identity_determiner", "observed_at",
}
_PRESSURE_REQUIRED = _PRESSURE_ALLOWED - {"observed_at"}


def test_to_pressure_state_conforms_to_pressure_state_schema():
    fs = classify_field_state(amplitude=0.8, force_signals=["coercive_certainty"], t_witness="thinning")
    ps = to_pressure_state(fs, peer_id="verus", source_refs=["turn-1"])
    # only schema-allowed keys (additionalProperties: false)
    assert set(ps) <= _PRESSURE_ALLOWED
    assert _PRESSURE_REQUIRED <= set(ps)
    # pressure_level is a NUMBER in [0,1] (not a label)
    assert isinstance(ps["pressure_level"], (int, float)) and 0.0 <= ps["pressure_level"] <= 1.0
    assert ps["pressure_class"] in {"internal", "external"}
    assert ps["is_identity_determiner"] is False   # const false — never an identity determiner
    assert isinstance(ps["dis_integrity_signal"], bool)
    assert ps["source_refs"] == ["turn-1"]
    # force-signals present -> external (imposed); high level -> dis-integrity signalled
    assert ps["pressure_class"] == "external"
    assert ps["dis_integrity_signal"] is True
    # carries NO nature-aspect content — layers stay separate
    assert "nature_aspect" not in str(ps).lower()


def test_to_pressure_state_internal_when_no_force():
    fs = classify_field_state(amplitude=0.1, stable=True, t_witness="intact")
    ps = to_pressure_state(fs, peer_id="verus")
    assert ps["pressure_class"] == "internal"
    assert ps["pressure_level"] <= 0.35 and ps["dis_integrity_signal"] is False


def test_build_rls_orb_input_matches_umbilical_contract():
    fs = classify_field_state(amplitude=0.3, stable=True, t_witness="intact")
    inp = build_rls_orb_input(
        peer_id="verus", session_id="s1", user_message="hello", intent="context_retrieval",
        field_state=fs,
    )
    # exactly the RLS umbilical input_contract fields
    assert set(inp) == {"peer_id", "session_id", "user_message", "intent", "pressure_state", "nature_aspects"}
    # pressure_state is a conformant record; the orb reads pressure_level (now a number)
    assert isinstance(inp["pressure_state"]["pressure_level"], (int, float))
    assert inp["pressure_state"]["is_identity_determiner"] is False
    # nature_aspects is a supplied pass-through, defaulting empty — NEVER fabricated from affect
    assert inp["nature_aspects"] == []


def test_nature_aspects_when_supplied_must_be_ref_strings():
    fs = classify_field_state(amplitude=0.3)
    ok = build_rls_orb_input(peer_id="p", session_id="s", user_message="m", intent="i",
                             field_state=fs, nature_aspects=["nature:aspect-03", "nature:aspect-07"])
    assert ok["nature_aspects"] == ["nature:aspect-03", "nature:aspect-07"]
    with pytest.raises(ValueError):
        build_rls_orb_input(peer_id="p", session_id="s", user_message="m", intent="i",
                            field_state=fs, nature_aspects=[{"not": "a-string"}])
