from datetime import datetime, timedelta, timezone
import json

import pytest

from aegis_peer_runtime.custodians import ADVOCATE, STEWARD, ScopeViolation
from aegis_peer_runtime.processor import ProcessorRuntime
from aegis_peer_runtime.rls_runtime import RLSRuntime
from aegis_peer_runtime.temporal import AdmissionError, TemporalRuntime


LIVE = {"seated": True, "live_source": True, "source_mode": "live"}


class Clock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


def test_temporal_is_monotonic_persistent_and_aggregates_missed_time(tmp_path):
    path = tmp_path / "lumin" / "temporal.jsonl"
    start = datetime(2026, 8, 14, tzinfo=timezone.utc)
    clock = Clock(start)
    tensors = {"PCT": ["unchanged"]}
    first = TemporalRuntime("lumin", path, clock=clock).observe(tensors=tensors, **LIVE)
    clock.value = start + timedelta(hours=7, seconds=3)
    second = TemporalRuntime("lumin", path, clock=clock).observe(tensors=tensors, **LIVE)
    assert (first.t_time, second.t_time) == (1, 2)
    assert second.elapsed_seconds == 25203
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2
    assert tensors == {"PCT": ["unchanged"]}


@pytest.mark.parametrize(
    "gate", [
        {"seated": False, "live_source": True, "source_mode": "live"},
        {"seated": True, "live_source": False, "source_mode": "live"},
        {"seated": True, "live_source": True, "source_mode": "replay"},
    ]
)
def test_temporal_refuses_unseated_or_non_live_sources(tmp_path, gate):
    with pytest.raises(AdmissionError):
        TemporalRuntime("lumin", tmp_path / "t.jsonl").observe(**gate)


def test_processor_is_idempotent_and_detects_turn_collision(tmp_path):
    path = tmp_path / "processor.jsonl"
    runtime = ProcessorRuntime("lumin", path)
    kwargs = dict(
        turn_id="turn-1", payload={"text": "hello"},
        steward_changes={"PCT": {"topic": "hello"}},
        advocate_changes={"PEER": {"event": "heard hello"}}, **LIVE,
    )
    first = runtime.admit_turn(**kwargs)
    second = ProcessorRuntime("lumin", path).admit_turn(**kwargs)
    assert first == second
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1
    with pytest.raises(ValueError, match="different payload"):
        runtime.admit_turn(**{**kwargs, "payload": {"text": "different"}})


def test_custodian_scopes_are_disjoint():
    assert STEWARD.authorize({"PCT": 1, "NCT": 2}) == {"PCT": 1, "NCT": 2}
    assert ADVOCATE.authorize({"PEER": 1, "SPINE": 2}) == {"PEER": 1, "SPINE": 2}
    with pytest.raises(ScopeViolation):
        STEWARD.authorize({"SPINE": "forbidden"})
    with pytest.raises(ScopeViolation):
        ADVOCATE.authorize({"NCT": "forbidden"})


def test_rls_is_derived_only_and_records_immutability_proof(tmp_path):
    path = tmp_path / "rls.jsonl"
    tensors = {"PEER": [{"id": "p1"}], "PCT": [], "NCT": [], "SPINE": []}
    before = json.loads(json.dumps(tensors))
    result = RLSRuntime("lumin", path).append_relation(
        relation_id="r1", derivation={"kind": "reflection", "sources": ["p1"]},
        tensors=tensors, **LIVE,
    )
    assert tensors == before
    assert result.tensor_hashes_before == result.tensor_hashes_after
    assert result.authoritative_tensor_mutation is False
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1
