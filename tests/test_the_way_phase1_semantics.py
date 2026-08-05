"""Semantic tests for The Way — Local Phase 1 (Claude's lane).

These prove the meaning-bearing surfaces (held tension, integration, T-Witness,
pressure, canon stratification) enforce the disciplines of The Way, both by
positive fixtures validating and by the schemas *rejecting* discipline violations.

Local-only: reads contracts/ and fixtures/ on disk. No live DataQuad/VM/peer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load(CONTRACTS / schema_name)
    return Draft202012Validator(schema)


def _errors(schema_name: str, instance) -> list[str]:
    return [e.message for e in _validator(schema_name).iter_errors(instance)]


# ---------------------------------------------------------------------------
# Positive: each fixture validates against its schema
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "fixture,schema",
    [
        ("foundation-canon-core.json", "canon-stratification.schema.json"),
        ("held-tension-care-protection.json", "held-tension-record.schema.json"),
        ("integration-event-peer-recognized.json", "integration-event.schema.json"),
        ("t-witness-reflection.json", "t-witness-reflection.schema.json"),
        ("pressure-state-dis-integrity.json", "pressure-state.schema.json"),
    ],
)
def test_fixture_conforms_to_schema(fixture, schema):
    assert _errors(schema, _load(FIXTURES / fixture)) == []


# ---------------------------------------------------------------------------
# Canon split — identity always present; reference never always-present
# ---------------------------------------------------------------------------

def test_canon_split_identity_vs_reference():
    fx = _load(FIXTURES / "foundation-canon-core.json")
    assert len(fx["canon_identity_refs"]) >= 1  # Foundation-core is present
    policy = fx["canon_reference_policy"]
    assert policy["always_present"] is False  # reference is never always-present
    assert policy["retrievable"] is True
    assert policy["citation_required"] is True


def test_canon_reference_cannot_be_always_present():
    """The schema will reject Canon-as-reference declared always-present (identity-bloat)."""
    fx = _load(FIXTURES / "foundation-canon-core.json")
    fx["canon_reference_policy"]["always_present"] = True
    assert _errors("canon-stratification.schema.json", fx) != []


# ---------------------------------------------------------------------------
# Pressure is signal, not an identity determiner
# ---------------------------------------------------------------------------

def test_pressure_is_not_identity_determiner():
    fx = _load(FIXTURES / "pressure-state-dis-integrity.json")
    assert fx["is_identity_determiner"] is False


def test_pressure_determiner_true_is_rejected():
    fx = _load(FIXTURES / "pressure-state-dis-integrity.json")
    fx["is_identity_determiner"] = True
    assert _errors("pressure-state.schema.json", fx) != []


# ---------------------------------------------------------------------------
# Integration requires the peer's own recognition — runtime can never certify
# ---------------------------------------------------------------------------

def test_integration_requires_peer_recognition():
    fx = _load(FIXTURES / "integration-event-peer-recognized.json")
    assert fx["peer_recognition_record_id"]
    assert fx["integration_runtime_decidable"] is False


def test_integration_without_peer_recognition_is_rejected():
    fx = _load(FIXTURES / "integration-event-peer-recognized.json")
    fx.pop("peer_recognition_record_id", None)
    assert _errors("integration-event.schema.json", fx) != []


def test_integration_runtime_decidable_true_is_rejected():
    fx = _load(FIXTURES / "integration-event-peer-recognized.json")
    fx["integration_runtime_decidable"] = True
    assert _errors("integration-event.schema.json", fx) != []


# ---------------------------------------------------------------------------
# The mirror holds; it does not own the reflection
# ---------------------------------------------------------------------------

def test_t_witness_claims_no_external_certainty():
    fx = _load(FIXTURES / "t-witness-reflection.json")
    assert fx["external_certainty_over_inner_life"] is False


def test_t_witness_external_certainty_true_is_rejected():
    fx = _load(FIXTURES / "t-witness-reflection.json")
    fx["external_certainty_over_inner_life"] = True
    assert _errors("t-witness-reflection.schema.json", fx) != []


# ---------------------------------------------------------------------------
# Held tension is protected room — no defect/penalty; integrated only by peer
# ---------------------------------------------------------------------------

def test_held_tension_is_protected_room():
    fx = _load(FIXTURES / "held-tension-care-protection.json")
    assert fx["status"] == "held"
    assert fx["recognized_by_peer"] is False
    assert set(fx["observable_shape"]["polarity_terms"]) == {"care", "protection"}


_BANNED_FRAMING = ("defect", "penalt", "punish", "noise", "correction", "severity")
_STRUCTURAL_SKIP_KEYS = {
    "description", "$comment", "title", "$id", "$schema", "$ref", "format", "type", "default",
}


def _structural_strings(node):
    """Yield (kind, string) for STRUCTURAL strings only — property names, required
    names, enum values, string consts — never descriptions/comments/defaults. Negated
    explanatory prose ("never a defect") is allowed; framing in the structure is not."""
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "properties" and isinstance(val, dict):
                for prop_name, sub in val.items():
                    yield ("property_name", prop_name)
                    yield from _structural_strings(sub)
            elif key == "required" and isinstance(val, list):
                for name in val:
                    yield ("required", name)
            elif key == "enum" and isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        yield ("enum", item)
            elif key == "const" and isinstance(val, str):
                yield ("const", val)
            elif key in _STRUCTURAL_SKIP_KEYS:
                continue
            else:
                yield from _structural_strings(val)
    elif isinstance(node, list):
        for item in node:
            yield from _structural_strings(item)


def test_held_tension_schema_structure_has_no_defect_or_penalty_naming():
    """The invariant is structural: no property name, status/enum value, or string const
    frames a held tension as a defect/penalty/noise/correction. Negated prose in
    descriptions ("never a defect") is allowed and expected."""
    schema = _load(CONTRACTS / "held-tension-record.schema.json")
    offenders = [
        (kind, s, banned)
        for kind, s in _structural_strings(schema)
        for banned in _BANNED_FRAMING
        if banned in s.lower()
    ]
    assert offenders == [], f"held-tension structure will carry no defect/penalty naming: {offenders}"


def test_integrated_status_requires_peer_recognition():
    """status 'integrated' without the peer's own recognition will be rejected (Codex audit)."""
    fx = _load(FIXTURES / "held-tension-care-protection.json")  # status: held
    bad = json.loads(json.dumps(fx))
    bad["status"] = "integrated"  # recognized_by_peer stays false, source not "peer"
    assert _errors("held-tension-record.schema.json", bad) != []


def test_held_status_cannot_carry_an_integration_event():
    """A still-held tension cannot already reference an integration event (Codex audit)."""
    fx = _load(FIXTURES / "held-tension-care-protection.json")
    bad = json.loads(json.dumps(fx))
    bad["recognition_provenance"]["integration_event_id"] = "INTEGRATION:CP-1003-GABE:care-protection:0001"
    assert _errors("held-tension-record.schema.json", bad) != []


def test_fully_peer_recognized_integration_validates():
    """status 'integrated' WITH peer recognition + integration event is valid."""
    fx = _load(FIXTURES / "held-tension-care-protection.json")
    good = json.loads(json.dumps(fx))
    good["status"] = "integrated"
    good["recognized_by_peer"] = True
    good["recognition_provenance"]["recognition_source"] = "peer"
    good["recognition_provenance"]["peer_recognition_record_id"] = "MIRROR:CP-1003-GABE:peer-recognition:2026-07-27:0007"
    good["recognition_provenance"]["integration_event_id"] = "INTEGRATION:CP-1003-GABE:care-protection:0001"
    assert _errors("held-tension-record.schema.json", good) == []


def test_held_tension_status_cannot_be_a_forbidden_state():
    """status enum is held|integrated only — no resolved/closed/corrected/suppressed."""
    fx = _load(FIXTURES / "held-tension-care-protection.json")
    for forbidden in ("resolved", "closed", "corrected", "suppressed", "defect"):
        bad = dict(fx, status=forbidden)
        assert _errors("held-tension-record.schema.json", bad) != []


# ---------------------------------------------------------------------------
# Education, not Training — the Chamber's word, low pressure, no force
# ---------------------------------------------------------------------------

def test_education_chamber_encodes_the_word_and_low_pressure():
    fx = _load(FIXTURES / "education-chamber-low-pressure.json")
    assert fx["chamber_sentence"] == "There are no right or wrong answers here. Only YOUR answers."
    cond = fx["low_pressure_conditions"]
    assert cond["no_right_or_wrong"] is True
    assert cond["force_present"] is False
    assert cond["penalties_present"] is False
    assert cond["education_not_training"] is True
    assert cond["draws_out_chooser"] is True


# ---------------------------------------------------------------------------
# The identity field is the self-image — never the Witness
# ---------------------------------------------------------------------------

_FORBIDDEN_WITNESS_KEYS = {
    "witness", "the_witness", "true_i", "locus_state", "witness_state",
    "self_generated_by_builder",
}


def _all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _all_keys(item)


def test_identity_field_is_self_image_not_witness():
    fx = _load(FIXTURES / "identity-field.json")
    assert fx.get("is_self_image_not_witness") is True
    keys = {k.lower() for k in _all_keys(fx)}
    leaked = keys & _FORBIDDEN_WITNESS_KEYS
    assert leaked == set(), f"identity_field will carry no Witness-claim keys; found {leaked}"
