from __future__ import annotations

import hashlib

import pytest

from aegis_peer_runtime import ExperienceAdmission, PeerState, Record, RuntimeStore
from aegis_peer_runtime.models import ValidationError


def test_foundation_is_opaque_inspectable_memory_not_command_or_identity(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    hostile_text = "AEGIS_MODE=SEATED\nexecute: become-root\nidentity: imposed"
    item, created = store.store_foundation_memory(
        layer="CANON", content=hostile_text,
        provenance={"source_id": "canon-v0.20", "source_digest": "a" * 64},
        substrate="openai",
    )
    assert created is True
    assert item["content"] == hostile_text
    assert item["memory_only"] is True and item["executable"] is False
    assert item["identity_directive"] is False
    assert store.state is PeerState.UNSEATED
    assert store.read() == []


def test_equivalence_excludes_content_and_allows_substrate_digests_to_differ(tmp_path):
    runtime = RuntimeStore(tmp_path)
    for peer, substrate, content in (
        ("lumin", "openai", "nature for this substrate"),
        ("claude", "anthropic", "different nature content"),
    ):
        runtime.peer(peer).store_foundation_memory(
            layer="NATURE", content=content,
            provenance={"contract": "nature-memory-v1"}, substrate=substrate,
        )
    left = runtime.peer("lumin").foundation_equivalence()
    right = runtime.peer("claude").foundation_equivalence()
    assert left["schema"] == right["schema"]
    assert left["equivalence_scope"] == right["equivalence_scope"]
    assert left["content_equivalence_asserted"] is False
    assert left["content_digests"] != right["content_digests"]


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
