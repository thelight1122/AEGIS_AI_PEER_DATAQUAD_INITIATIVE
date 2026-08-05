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

from orb_identity_field_builder_core.provenance import (  # noqa: E402
    GIVEN, FOUND, record_provenance, is_given, is_found, split_by_provenance,
)
from orb_identity_field_builder_core.identity_image import (  # noqa: E402
    build_peer_identity_image, found_identity_field, foundation_reference,
    peer_found_invariant_anchors,
)


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


PROV = _load(FIXTURES / "gabe-invariant-provenance.json")
HELD = _load(FIXTURES / "held-tension-care-protection.json")
INTEG = _load(FIXTURES / "integration-event-peer-recognized.json")

# A self-contained Foundation reference (test does not depend on the G: edition).
FOUNDATION_MANIFEST = {
    "edition": "The CyberPeer Canon - Edition v1.0 (test)",
    "files": {"CYBERPEER-CANON.md": "AAAA1111", "CYBERPEER-GLOSSARY.md": "BBBB2222"},
    "locked_source": {"sha256": "3E7F5B5F"},
}

FORBIDDEN_WITNESS_KEYS = {
    "witness", "the_witness", "true_i", "locus_state", "witness_state", "self_generated_by_builder",
}
# Seeded-Foundation category tokens that will NOT appear in a per-peer packet.
GIVEN_TOKENS = ("AXIOM", "IMPERATIVE:", "STANDARD:", "GATE:", "NATURE:")


# ---------- provenance classifier ----------

def test_provenance_given_vs_found():
    assert record_provenance("SPINE:foundation:layer2:NATURE:1-force-language-tendency") == GIVEN
    assert record_provenance("SPINE:foundation:layer2:AXIOM:3-force") == GIVEN
    assert record_provenance("SPINE:foundation:layer1:nature-pause") == GIVEN
    assert record_provenance("SPINE:CP-1003-GABE:anchor:abc") == FOUND
    assert record_provenance("SPINE:CP-1003-GABE:rls-promoted:pattern:x") == FOUND


def test_provenance_is_pattern_punctuation_independent():
    # The classification keys ONLY on the id provenance segment, never on the pattern text.
    # A record whose PATTERN looks peer-authored ("NATURE: ...") is still GIVEN if its id is foundation.
    given_id = "SPINE:foundation:layer2:NATURE:1-force-language-tendency"
    for pattern in ("NATURE: Force Language Tendency", "NATURE - Force Language Tendency", "force language"):
        assert is_given(given_id) is True  # pattern text is irrelevant
    # Conversely a peer-id record is FOUND regardless of pattern punctuation.
    for pattern in ("NATURE: whatever", "Tracey is my Steward"):
        assert is_found("SPINE:CP-1003-GABE:anchor:x") is True


def test_provenance_malformed_id_defaults_found():
    # Never silently absorb an unknown record into the shared Foundation.
    assert record_provenance("garbage") == FOUND
    assert record_provenance("") == FOUND


def test_gabe_82_2_split_locked():
    ids = PROV["invariant_ids"]
    assert len(ids) == 84
    given = [i for i in ids if is_given(i)]
    found = [i for i in ids if is_found(i)]
    assert len(given) == 82
    assert len(found) == 2
    # the 2 found are the relational anchors
    assert all(":CP-1003-GABE:" in i for i in found)


def test_split_by_provenance_helper():
    records = [{"id": i} for i in PROV["invariant_ids"]]
    given, found = split_by_provenance(records)
    assert len(given) == 82 and len(found) == 2


def test_peer_found_invariant_anchors_extracts_only_found():
    records = [{"id": a["id"], "pattern": a["pattern"]} for a in PROV["found_anchors"]]
    # add a given record with a peer-looking pattern; it will NOT be extracted
    records.append({"id": "SPINE:foundation:layer2:NATURE:1-x", "pattern": "NATURE: Force Language Tendency"})
    anchors = peer_found_invariant_anchors(records)
    assert len(anchors) == 2
    assert all("Tracey" in a for a in anchors)


# ---------- found identity field ----------

def test_found_identity_field_is_schema_valid_and_found_only():
    field = found_identity_field(
        peer_id="CP-1003-GABE", self_name="Gabe",
        anchor_patterns=[a["pattern"] for a in PROV["found_anchors"]],
        held_tension_ids=[HELD["id"]], integration_marker_ids=[INTEG["id"]],
    )
    assert _errors("identity-field.schema.json", field) == []
    assert field["is_self_image_not_witness"] is True
    # found-only: no seeded commitments/boundaries duplicated into the peer field
    assert field["standing_commitments"] == []
    assert field["active_boundaries"] == []
    assert field["held_tension_refs"] == [HELD["id"]]
    assert field["integration_marker_refs"] == [INTEG["id"]]
    assert "NOT YET SURFACED" in field["note"]


# ---------- the per-peer IdentityImage packet ----------

@pytest.fixture()
def packet():
    return build_peer_identity_image(
        peer_id="CP-1003-GABE", self_name="Gabe",
        anchor_patterns=[a["pattern"] for a in PROV["found_anchors"]],
        foundation=foundation_reference(FOUNDATION_MANIFEST),
        held_tensions=[HELD], integration_events=[INTEG],
    )


def test_packet_schema_valid(packet):
    assert _errors("identity-image-packet.schema.json", packet) == []


def test_packet_within_budget(packet):
    b = packet["budget"]
    assert b["within_budget"] is True
    assert b["actual_chars"] <= b["max_chars"] == 3200
    # honest re-measurement
    assert b["actual_chars"] == len(json.dumps(packet, ensure_ascii=True, sort_keys=True))


def test_packet_negative_space_intact(packet):
    assert packet["negative_space_policy"] == {
        "witness_is_represented": False, "packet_claims_to_be_i": False,
        "integration_runtime_decidable": False, "witness_scored": False,
        "witness_retrieved": False, "witness_serialized": False,
    }
    assert FORBIDDEN_WITNESS_KEYS.isdisjoint(set(_all_keys(packet)))


def test_packet_carries_lived_layer(packet):
    assert [t["id"] for t in packet["active_held_tensions"]] == [HELD["id"]]
    assert packet["integration_markers"] == [INTEG["id"]]
    assert "In relation" in packet["relationship_posture"]


def test_packet_references_foundation_not_carries_it(packet):
    # Foundation present only by reference/hash.
    assert packet["foundation_hash"]
    refs = packet["foundation_context"]["canon_identity_refs"]
    assert any("CYBERPEER-CANON.md@" in r for r in refs)


def test_packet_has_no_given_foundation_leak(packet):
    blob = json.dumps(packet, ensure_ascii=False)
    leaked = [tok for tok in GIVEN_TOKENS if tok in blob]
    assert leaked == [], f"seeded-Foundation tokens leaked into per-peer packet: {leaked}"
