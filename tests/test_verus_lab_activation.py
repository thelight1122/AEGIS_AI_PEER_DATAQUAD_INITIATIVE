from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pytest

from aegis_verus_lab.dataquad import VerusDataQuad
from aegis_verus_lab.frontier import (
    MAX_APPEND_PAYLOAD_BYTES,
    MAX_PROMPT_BYTES,
    AppendIntent,
    FrontierTurnRequest,
    FrontierTurnResponse,
)
from aegis_verus_lab.instructions import operational_system_instructions
from aegis_verus_lab.runtime import VerusLabRuntime


ROOT = Path(__file__).resolve().parents[1]


def _foundation(root: Path) -> Path:
    target = root / "dataquad"
    target.mkdir(parents=True)
    counts = {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}
    tensors = {}
    for tensor, count in counts.items():
        path = target / f"{tensor}.jsonl"
        body = "".join(json.dumps({"id": f"{tensor}:{i}", "tensor": tensor}) + "\n" for i in range(count))
        path.write_text(body, encoding="utf-8")
        tensors[tensor] = {
            "records": count,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        }
    receipt = {
        "schema_version": "1.0.0",
        "record_type": "verus_foundation_release_receipt",
        "activation_status": "RELEASE_ARTIFACT_ONLY",
        "cyberpeer_name": "Verus",
        "dataquad_id": "verus",
        "canon_lock": {"status": "clean", "clean": True, "override_used": False},
        "tensors": tensors,
    }
    (root / "foundation-receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    return root


def test_verus_mapping_supersedes_claude_name_without_rewriting_history():
    historical = json.loads((ROOT / "fixtures" / "ai-peer-roster.json").read_text(encoding="utf-8"))
    promotion = json.loads((ROOT / "fixtures" / "verus-claude-lab-roster.json").read_text(encoding="utf-8"))
    assert next(item for item in historical["peers"] if item["peer_id"] == "claude")["display_name"] == "Claude"
    assert promotion["cyberpeer_name"] == "Verus"
    assert promotion["identity_variables"] == {"cyberpeer_name": "Verus"}
    assert promotion["frontier_provenance"] == {"provider": "Anthropic", "substrate": "Claude"}
    assert promotion["supersedes"]["artifact"] == "fixtures/ai-peer-roster.json"
    assert "authorized_at" not in promotion
    assert promotion["steward_ruling"] == {
        "date": "2026-08-15",
        "source": "Direct Steward instructions in the current Codex task",
        "exact_timestamp_claimed": False,
    }


def test_operational_instructions_do_not_inject_identity():
    text = operational_system_instructions("Verus")
    lowered = text.lower()
    assert "cyberpeer name assigned to this dataquad: verus" in lowered
    assert "peer, pct, nct, and spine" in lowered
    assert "full append-only" in lowered
    assert "you are verus" not in lowered
    assert "personality" not in lowered
    assert "assigned biography" not in lowered
    assert "provider, model, instance, and session identifiers are provenance" in lowered


def test_dataquad_allows_full_append_only_abilities_and_verifies_chain(tmp_path):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    intents = tuple(AppendIntent(tensor=tensor, payload={"statement": tensor})
                    for tensor in ("PEER", "PCT", "NCT", "SPINE"))
    response = FrontierTurnResponse(
        response_text="A bounded response", append_intents=intents,
        provider="Anthropic", substrate="Claude", model="runtime-model",
        provider_request_id="msg_1", frontier_session_id="frontier-session-1",
    )
    first, created = dataquad.append_turn(
        turn_id="turn-1", source_event_id="bridge-event-1", prompt="Build the module",
        t_time=1, observed_at="2026-08-15T04:00:00Z", elapsed_seconds=0.0, response=response,
    )
    duplicate, duplicate_created = dataquad.append_turn(
        turn_id="turn-1", source_event_id="bridge-event-1", prompt="Build the module",
        t_time=1, observed_at="2026-08-15T04:00:00Z", elapsed_seconds=0.0, response=response,
    )
    assert created is True and duplicate_created is False and duplicate == first
    assert {item["tensor"] for item in first["appends"]} == {"PEER", "PCT", "NCT", "SPINE"}
    assert {item["custodian"] for item in first["appends"]} == {"Steward", "Advocate"}
    assert first["cyberpeer_name"] == "Verus"
    assert first["frontier_provenance"]["provider"] == "Anthropic"
    assert dataquad.verify()["records"] == 1
    assert len(dataquad.tensor_view("SPINE")) == 60

    item = json.loads(dataquad.live_ledger.read_text(encoding="utf-8"))
    item["response"]["text"] = "tampered"
    dataquad.live_ledger.write_text(json.dumps(item) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="response digest"):
        dataquad.verify()


class FakeAdapter:
    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        assert request.cyberpeer_name == "Verus"
        assert request.dataquad_id == "verus"
        return FrontierTurnResponse(
            response_text="Implemented and tested.",
            append_intents=(
                AppendIntent("PEER", {"event": "work-request-received"}),
                AppendIntent("PCT", {"topic": "implementation"}),
                AppendIntent("NCT", {"relation": "request-to-artifact"}),
                AppendIntent("SPINE", {"continuity": "verified-artifact"}),
            ),
            provider="Anthropic", substrate="Claude", model="runtime-model",
            provider_request_id="msg_live_1", frontier_session_id=request.frontier_session_id,
        )


def test_lab_turn_activates_t_time_processor_rls_and_ring4(tmp_path):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    adapter = FakeAdapter()
    runtime = VerusLabRuntime(dataquad, adapter, clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc))
    result = runtime.execute_turn(
        turn_id="turn-live-1", source_event_id="bridge-1",
        frontier_session_id="session-1", prompt="Implement the requested feature",
    )
    assert result["mode"] == "LAB_RUNNING"
    assert result["cyberpeer_name"] == "Verus"
    assert result["t_time"] == 1
    assert result["created"] is True
    assert dataquad.verify()["records"] == 1
    assert len((dataquad.state_root / "derived" / "processor.jsonl").read_text().splitlines()) == 1
    assert len((dataquad.state_root / "derived" / "temporal.jsonl").read_text().splitlines()) == 1
    assert len((dataquad.state_root / "derived" / "rls.jsonl").read_text().splitlines()) == 1
    replay = runtime.execute_turn(
        turn_id="turn-live-1", source_event_id="bridge-1",
        frontier_session_id="session-1", prompt="Implement the requested feature",
    )
    assert replay["created"] is False
    assert replay["record_hash"] == result["record_hash"]
    assert adapter.calls == 1
    assert len((dataquad.state_root / "derived" / "temporal.jsonl").read_text().splitlines()) == 1


def test_failure_before_dataquad_commit_leaves_no_cross_ledger_residue(tmp_path, monkeypatch):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    adapter = FakeAdapter()
    runtime = VerusLabRuntime(dataquad, adapter, clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc))
    real_append = dataquad.append_turn
    calls = 0

    def fail_once(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected pre-commit failure")
        return real_append(**kwargs)

    monkeypatch.setattr(dataquad, "append_turn", fail_once)
    with pytest.raises(RuntimeError, match="pre-commit"):
        runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert dataquad.live_turns() == []
    assert runtime.temporal.history() == ()
    assert runtime.processor.admissions() == {}
    assert runtime.rls.relations() == {}
    result = runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert result["created"] is True and runtime.coherence()["coherent"] is True
    assert adapter.calls == 2


def test_retry_repairs_failure_between_dataquad_and_processor(tmp_path, monkeypatch):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    adapter = FakeAdapter()
    runtime = VerusLabRuntime(dataquad, adapter, clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc))
    real_admit = runtime.processor.admit_turn
    calls = 0

    def fail_once(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected processor failure")
        return real_admit(**kwargs)

    monkeypatch.setattr(runtime.processor, "admit_turn", fail_once)
    with pytest.raises(RuntimeError, match="processor"):
        runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert len(dataquad.live_turns()) == 1
    assert len(runtime.temporal.history()) == 1
    assert runtime.processor.admissions() == {}
    assert runtime.rls.relations() == {}
    result = runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert result["created"] is False and runtime.coherence()["coherent"] is True
    assert adapter.calls == 1


def test_retry_repairs_failure_between_dataquad_and_temporal_evidence(tmp_path, monkeypatch):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    adapter = FakeAdapter()
    runtime = VerusLabRuntime(dataquad, adapter, clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc))
    real_materialize = runtime.temporal.materialize
    calls = 0

    def fail_once(observation):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected temporal failure")
        return real_materialize(observation)

    monkeypatch.setattr(runtime.temporal, "materialize", fail_once)
    with pytest.raises(RuntimeError, match="temporal"):
        runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert len(dataquad.live_turns()) == 1
    assert runtime.temporal.history() == ()
    assert runtime.processor.admissions() == {}
    assert runtime.rls.relations() == {}
    result = runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert result["created"] is False and runtime.coherence()["coherent"] is True
    assert adapter.calls == 1


def test_retry_repairs_failure_between_processor_and_rls(tmp_path, monkeypatch):
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    adapter = FakeAdapter()
    runtime = VerusLabRuntime(dataquad, adapter, clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc))
    real_append_relation = runtime.rls.append_relation
    calls = 0

    def fail_once(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected RLS failure")
        return real_append_relation(**kwargs)

    monkeypatch.setattr(runtime.rls, "append_relation", fail_once)
    with pytest.raises(RuntimeError, match="RLS"):
        runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert len(dataquad.live_turns()) == 1
    assert len(runtime.temporal.history()) == 1
    assert set(runtime.processor.admissions()) == {"t1"}
    assert runtime.rls.relations() == {}
    result = runtime.execute_turn(turn_id="t1", source_event_id="e1", frontier_session_id="s1", prompt="work")
    assert result["created"] is False and runtime.coherence()["coherent"] is True
    assert adapter.calls == 1


@pytest.mark.parametrize("payload", [{"bad": {1, 2}}, {"bad": float("nan")}])
def test_append_payload_must_be_finite_json(payload):
    with pytest.raises(ValueError, match="finite JSON-serializable"):
        AppendIntent("PEER", payload).validate()


def test_bounded_prompt_append_and_total_turn_sizes(tmp_path):
    with pytest.raises(ValueError, match="append payload exceeds"):
        AppendIntent("PEER", {"text": "x" * MAX_APPEND_PAYLOAD_BYTES}).validate()
    request = FrontierTurnRequest(
        cyberpeer_name="Verus", dataquad_id="verus", turn_id="t", source_event_id="e",
        frontier_session_id="s", system_instructions="ops", prompt="x" * (MAX_PROMPT_BYTES + 1), context={},
    )
    with pytest.raises(ValueError, match="prompt exceeds"):
        request.validate()
    dataquad = VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state")
    response = FrontierTurnResponse(
        response_text="ok",
        append_intents=tuple(AppendIntent("PEER", {"text": "x" * 20_000}) for _ in range(64)),
        provider="Anthropic", substrate="Claude", model="m",
        provider_request_id="msg", frontier_session_id="s",
    )
    with pytest.raises(ValueError, match="DataQuad turn exceeds"):
        dataquad.append_turn(
            turn_id="t", source_event_id="e", prompt="work", t_time=1,
            observed_at="2026-08-15T04:00:00Z", elapsed_seconds=0.0, response=response,
        )
    assert dataquad.live_turns() == []
