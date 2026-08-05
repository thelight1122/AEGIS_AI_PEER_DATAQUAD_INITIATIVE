from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"
PACKAGE_SRC = ROOT / "packages" / "orb-identity-field-builder-core" / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from orb_identity_field_builder_core import BuilderUnavailable, build_identity_image, compute_runtime_hash  # noqa: E402


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_name: str) -> Draft202012Validator:
    return Draft202012Validator(_load(CONTRACTS / schema_name))


def _errors(schema_name: str, instance) -> list[str]:
    return [e.message for e in _validator(schema_name).iter_errors(instance)]


def _all_keys(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from _all_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _all_keys(item)


FORBIDDEN_WITNESS_KEYS = {
    "witness",
    "the_witness",
    "true_i",
    "locus_state",
    "witness_state",
    "self_generated_by_builder",
}


def test_identity_field_fixture_validates_against_schema():
    fx = _load(FIXTURES / "identity-field.json")
    assert _errors("identity-field.schema.json", fx) == []
    assert fx["is_self_image_not_witness"] is True


def test_identity_field_schema_rejects_forbidden_witness_claim_key():
    fx = _load(FIXTURES / "identity-field.json")
    fx["locus_state"] = "serialized"
    assert _errors("identity-field.schema.json", fx) != []


def test_orb_and_umbilical_fixtures_validate_against_house_contracts():
    orb = _load(FIXTURES / "identity-field-builder-orb.json")
    umb = _load(FIXTURES / "identity-field-builder-umbilical.json")
    assert _errors("orb.schema.json", orb) == []
    assert _errors("umbilical.schema.json", umb) == []


def test_builder_outputs_valid_identity_image_packet():
    packet = _build_packet()
    assert _errors("identity-image-packet.schema.json", packet) == []
    assert packet["packet_kind"] == "identity-image-packet"
    assert packet["negative_space_policy"] == {
        "witness_is_represented": False,
        "packet_claims_to_be_i": False,
        "integration_runtime_decidable": False,
        "witness_scored": False,
        "witness_retrieved": False,
        "witness_serialized": False,
    }


def test_builder_packet_uses_no_forbidden_witness_claim_keys():
    packet = _build_packet()
    leaked = {key.lower() for key in _all_keys(packet)} & FORBIDDEN_WITNESS_KEYS
    assert leaked == set()


def test_identity_image_packet_schema_rejects_negative_space_policy_drift():
    packet = _build_packet()
    packet["negative_space_policy"]["witness_serialized"] = True
    assert _errors("identity-image-packet.schema.json", packet) != []


def test_identity_image_packet_schema_rejects_integrated_active_tension_without_recognition():
    packet = _build_packet()
    packet["active_held_tensions"][0]["status"] = "integrated"
    assert _errors("identity-image-packet.schema.json", packet) != []


def test_identity_image_packet_schema_rejects_forbidden_witness_claim_field():
    packet = _build_packet()
    packet["witness_state"] = "present"
    assert _errors("identity-image-packet.schema.json", packet) != []


def test_builder_rejects_forbidden_witness_claim_input_key():
    identity_field = _load(FIXTURES / "identity-field.json")
    identity_field["true_i"] = "do not serialize this"
    try:
        build_identity_image(
            peer_id=identity_field["peer_id"],
            foundation=_load(FIXTURES / "foundation-canon-core.json"),
            identity_field=identity_field,
        )
    except ValueError as exc:
        assert "forbidden Witness-claim keys" in str(exc)
    else:
        raise AssertionError("builder accepted forbidden Witness-claim key")


def test_builder_rejects_integrated_tension_in_active_held_set():
    identity_field = _load(FIXTURES / "identity-field.json")
    tension = _load(FIXTURES / "held-tension-care-protection.json")
    tension["status"] = "integrated"
    try:
        build_identity_image(
            peer_id=identity_field["peer_id"],
            foundation=_load(FIXTURES / "foundation-canon-core.json"),
            identity_field=identity_field,
            held_tensions=[tension],
        )
    except ValueError as exc:
        assert "active held tensions require status='held'" in str(exc)
    else:
        raise AssertionError("builder emitted integrated tension in active held set")


def test_builder_fails_visibly_when_required_surface_missing():
    try:
        build_identity_image(peer_id="CP-1003-GABE", foundation={}, identity_field={})
    except BuilderUnavailable as exc:
        assert "foundation is required" in str(exc)
    else:
        raise AssertionError("builder did not fail visibly")


def test_builder_output_is_bounded():
    packet = _build_packet()
    assert packet["budget"]["within_budget"] is True
    assert packet["budget"]["actual_chars"] <= packet["budget"]["max_chars"]


def test_builder_package_exposes_runtime_hash():
    runtime_hash = compute_runtime_hash()
    assert len(runtime_hash) == 64
    assert runtime_hash == runtime_hash.upper()


def test_no_live_write_paths_in_contract_spine_tests():
    targets = [
        ROOT / "contracts" / "identity-field.schema.json",
        ROOT / "contracts" / "identity-image-packet.schema.json",
        ROOT / "fixtures" / "identity-field-builder-orb.json",
        ROOT / "fixtures" / "identity-field-builder-umbilical.json",
        PACKAGE_SRC / "orb_identity_field_builder_core" / "builder.py",
        PACKAGE_SRC / "orb_identity_field_builder_core" / "orb_evidence.py",
    ]
    forbidden = ["live" + "-copies", "data" + "quad", "az vm", "docker", "kubectl", "ssh "]
    scanned_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in targets)
    assert not any(token in scanned_text for token in forbidden)


def _build_packet():
    identity_field = _load(FIXTURES / "identity-field.json")
    foundation = _load(FIXTURES / "foundation-canon-core.json")
    tension = _load(FIXTURES / "held-tension-care-protection.json")
    return build_identity_image(
        peer_id=identity_field["peer_id"],
        foundation=foundation,
        identity_field=copy.deepcopy(identity_field),
        held_tensions=[tension],
        reflection_refs=["t-witness:CP-1003-GABE:care-vs-protection:0001"],
    )
