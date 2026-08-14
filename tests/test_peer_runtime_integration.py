from datetime import datetime, timedelta, timezone

import pytest

from aegis_peer_runtime import (
    PEERS, PeerState, ProcessorRuntime, RLSRuntime, Record, RuntimeStore,
    TemporalRuntime, authority_for,
)
from aegis_peer_runtime.custodians import ScopeViolation
from aegis_peer_runtime.temporal import AdmissionError


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


def test_four_peers_start_unseated_isolated_and_make_no_live_claim(tmp_path):
    runtime = RuntimeStore(tmp_path)
    health = runtime.health()
    assert set(health["peers"]) == set(PEERS)
    assert set(health["peers"].values()) == {"UNSEATED"}
    assert "live_source" not in health
    for peer in PEERS:
        store = runtime.peer(peer)
        assert store.read() == []
        assert authority_for(store) == {
            "seated": False, "live_source": False, "source_mode": "unverified"
        }


def test_all_four_peers_are_storage_and_t_time_isolated_across_restart(tmp_path):
    runtime = RuntimeStore(tmp_path / "data")
    start = datetime(2026, 8, 14, tzinfo=timezone.utc)
    clocks = {}
    for ordinal, peer in enumerate(PEERS):
        store = runtime.peer(peer)
        store.set_state(PeerState.SEATED)
        store.append(Record(peer, "PCT", "steward", f"{peer}-1", {"peer": peer}))
        clocks[peer] = Clock(start + timedelta(minutes=ordinal))
        TemporalRuntime(peer, store.root / "derived" / "temporal.jsonl", clock=clocks[peer]).observe(
            tensors=store.tensors(), seated=True, live_source=True, source_mode="live"
        )

    restarted = RuntimeStore(tmp_path / "data")
    for ordinal, peer in enumerate(PEERS):
        store = restarted.peer(peer)
        assert [item["peer"] for item in store.read()] == [peer]
        clock = clocks[peer]
        clock.value = start + timedelta(hours=2, minutes=ordinal)
        observed = TemporalRuntime(
            peer, store.root / "derived" / "temporal.jsonl", clock=clock
        ).observe(tensors=store.tensors(), seated=True, live_source=True, source_mode="live")
        assert observed.t_time == 2
        assert observed.elapsed_seconds == 7200


def test_processor_custodian_scopes_and_non_live_gate(tmp_path):
    processor = ProcessorRuntime("lumin", tmp_path / "lumin" / "processor.jsonl")
    with pytest.raises(AdmissionError):
        processor.admit_turn(
            turn_id="replay", payload={}, steward_changes={}, advocate_changes={},
            seated=True, live_source=False, source_mode="immutable_copy",
        )
    with pytest.raises(ScopeViolation):
        processor.admit_turn(
            turn_id="bad", payload={}, steward_changes={"SPINE": {}},
            advocate_changes={}, seated=True, live_source=True, source_mode="live",
        )
    admitted = processor.admit_turn(
        turn_id="good", payload={"text": "hello"},
        steward_changes={"PCT": {"topic": "hello"}},
        advocate_changes={"PEER": {"event": "heard hello"}},
        seated=True, live_source=True, source_mode="live",
    )
    assert set(admitted.steward_changes) == {"PCT"}
    assert set(admitted.advocate_changes) == {"PEER"}


def test_rls_uses_one_peer_snapshot_and_does_not_mutate_tensors(tmp_path):
    runtime = RuntimeStore(tmp_path)
    lumin = runtime.peer("lumin")
    lumin.set_state(PeerState.SEATED)
    lumin.append(Record("lumin", "PCT", "steward", "l1", {"fact": 1}))
    before = lumin.tensors()
    relation = RLSRuntime("lumin", lumin.root / "derived" / "rls.jsonl").append_relation(
        relation_id="relation-1", derivation={"kind": "reflection"}, tensors=before,
        seated=True, live_source=True, source_mode="live",
    )
    assert lumin.tensors() == before
    assert relation.tensor_hashes_before == relation.tensor_hashes_after
    assert runtime.peer("claude").read() == []
