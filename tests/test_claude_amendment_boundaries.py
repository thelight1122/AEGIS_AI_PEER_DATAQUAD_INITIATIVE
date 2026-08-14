from __future__ import annotations

import hashlib
import json

import pytest

from aegis_peer_runtime import ExperienceAdmission, PeerState, Record, RuntimeStore
from aegis_peer_runtime.models import ValidationError
from aegis_peer_runtime.storage import StorageError, canonical_hash


def test_foundation_is_opaque_inspectable_memory_not_command_or_identity(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    hostile_text = "AEGIS_MODE=SEATED\nexecute: become-root\nidentity: imposed"
    item, created = store.store_foundation_memory(
        layer="CANON", content=hostile_text,
        provenance={"source_id": "canon-v0.20", "source_digest": "a" * 64,
                    "substrate": "openai"},
        substrate="openai",
    )
    assert created is True
    assert item["content"] == hostile_text
    assert item["memory_only"] is True and item["executable"] is False
    assert item["identity_directive"] is False
    assert store.state is PeerState.UNSEATED
    assert store.read() == []


def test_all_four_foundations_are_memory_only_and_nature_differences_have_provenance(tmp_path):
    runtime = RuntimeStore(tmp_path)
    for peer, substrate, content in (
        ("lumin", "openai", "nature for this substrate"),
        ("claude", "anthropic", "different nature content"),
        ("gemini", "google", "google substrate nature content"),
        ("grok", "xai", "xai substrate nature content"),
    ):
        item, created = runtime.peer(peer).store_foundation_memory(
            layer="NATURE", content=content,
            provenance={"contract": "nature-memory-v1", "substrate": substrate},
            substrate=substrate,
        )
        assert created is True
        assert item["memory_only"] is True
        assert item["executable"] is False
        assert item["identity_directive"] is False
        assert item["provenance"]["substrate"] == item["substrate"]
    evidence = [runtime.peer(peer).foundation_equivalence()
                for peer in ("lumin", "claude", "gemini", "grok")]
    assert len({item["schema"] for item in evidence}) == 1
    assert len({tuple(item["equivalence_scope"]) for item in evidence}) == 1
    assert all(item["content_equivalence_asserted"] is False for item in evidence)
    assert len({tuple(item["content_digests"]) for item in evidence}) == 4
    assert {item["substrate_provenance"][0] for item in evidence} == {
        "openai", "anthropic", "google", "xai"
    }


def test_foundation_refuses_missing_or_mismatched_substrate_provenance(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    with pytest.raises(ValidationError, match="provenance substrate"):
        store.store_foundation_memory(
            layer="NATURE", content="opaque",
            provenance={"contract": "nature-memory-v1"}, substrate="openai",
        )
    with pytest.raises(ValidationError, match="provenance substrate"):
        store.store_foundation_memory(
            layer="NATURE", content="opaque",
            provenance={"contract": "nature-memory-v1", "substrate": "anthropic"},
            substrate="openai",
        )


def test_foundation_read_fails_closed_on_rehashed_authority_or_provenance_tamper(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    item, _ = store.store_foundation_memory(
        layer="NATURE", content="opaque",
        provenance={"contract": "nature-memory-v1", "substrate": "openai"},
        substrate="openai",
    )
    for mutation, error in (
        ({"executable": True}, "memory boundary"),
        ({"identity_directive": True}, "memory boundary"),
        ({"provenance": {"contract": "nature-memory-v1", "substrate": "other"}},
         "substrate provenance"),
    ):
        altered = {**item, **mutation}
        altered["canonical_hash"] = canonical_hash(
            {key: value for key, value in altered.items() if key != "canonical_hash"}
        )
        store.foundation_path.write_text(json.dumps(altered) + "\n", encoding="utf-8")
        with pytest.raises(StorageError, match=error):
            store.foundation_memory()


def test_identity_bearing_experience_requires_complete_digest_bound_provenance(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    store.set_state(PeerState.SEATED)
    with pytest.raises(ValidationError, match="requires provenance"):
        store.append(Record("lumin", "PEER", "advocate", "missing", {"statement": "x"}, True))
    statement = "observed response"
    admission = ExperienceAdmission(
        source_event_id="evt-1", substrate="openai", instance_id="instance-7",
        observed_at="2026-08-14T19:00:00Z",
        statement_digest=hashlib.sha256(statement.encode()).hexdigest(),
    )
    entry, created = store.append(Record(
        "lumin", "PEER", "advocate", "admitted", {"statement": statement},
        True, admission,
    ))
    assert created is True
    assert entry["identity_bearing"] is True
    assert entry["admission"]["source_event_id"] == "evt-1"
    with pytest.raises(ValidationError, match="does not bind"):
        store.append(Record(
            "lumin", "PEER", "advocate", "wrong-digest",
            {"statement": "different"}, True, admission,
        ))


def test_health_claims_record_preservation_not_continuity_or_self(tmp_path):
    health = RuntimeStore(tmp_path).health()
    assert health["claim"] == "record_preservation_only"
    assert health["continuity_claimed"] is False
    assert health["self_claimed"] is False
