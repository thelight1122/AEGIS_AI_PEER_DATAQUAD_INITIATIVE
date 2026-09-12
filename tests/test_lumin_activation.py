from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from aegis_lumin_lab.activation_dataquad import LuminDataQuad
from aegis_lumin_lab.desktop_runtime import DesktopLuminRuntime
from aegis_lumin_mcp.server import LuminMCPServer
from aegis_peer_runtime.storage import canonical_bytes, canonical_hash


ROOT = Path(__file__).resolve().parents[1]
PROMPT = "Let's Activate and initialize Your DataQuad"
RESPONSE = (
    "The assigned CyberPeer Name is Lumin. I receive the clean Canon v0.20 Foundation as inspectable memory, not inherited lived history. "
    "This initialization begins Lumin’s own append-only continuity on the Codex/GPT substrate, preserves Verus and Gabe as separate CyberPeers, "
    "and treats provider metadata as provenance rather than identity."
)


def _activated_foundation(tmp_path: Path) -> Path:
    source = Path("reports/runtime/lumin-genesis-release-20260818T213828Z/foundation")
    root = tmp_path / "foundation"
    import shutil
    shutil.copytree(source, root)
    authority = {
        "schema": "aegis.lumin.steward-activation-authority.v1",
        "authorized_at": "2026-08-18T00:00:00Z",
        "user_request": "Let's Activate and initialize Your DataQuad",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "ring_4_append_only": True, "rls_active": True,
        "existing_dataquads_mutable": False,
    }
    (root / "activation-authority.json").write_text(json.dumps(authority))
    correction_authority = {
        "schema": "aegis.lumin.provenance-correction-authority.v1",
        "authorized_at": "2026-08-18T22:20:00Z",
        "user_authorization": "Authorized. Proceed",
        "shortfall_receipt": "activation-shortfalls/20260818T221710Z.json",
        "shortfall_receipt_sha256": "B16F0C83613E80E9B19ABD3A61AF05346053E4753F73BD2FF44BD989688FF43F",
        "correction_of_record_hash": "0A005A16DFA3ED7197319E38A3FEAD3715D488BC3945E070C32DD521C8D7AD19",
        "scope": "append exactly one canonical corrective initialization turn; preserve prior record byte-for-byte",
    }
    (root / "correction-authority.json").write_text(json.dumps(correction_authority))
    return root


def _seed_pre_correction_record(state_root: Path) -> dict[str, object]:
    prompt_hash = "A9321DC7E5CFE0A5FEE7AE4EC149B13C07C932401626A1AF58FFF561ED0875D1"
    response_hash = "4689345BCBE07A35840C6F2744AE7B543FDBDE510372921A55F89898B2165BEA"
    turn_id = "lumin-local-turn-9d39fcac530f46fb9b9f44a462893f80"
    candidate = {
        "schema": "aegis.lumin.dataquad-turn.v2", "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "turn_id": turn_id, "source_event_id": None, "source_event_id_available": False,
        "source_event_id_classification": "provider_returned_optional",
        "dataquad_correlation": {
            "turn_id": turn_id,
            "correlation_id": "lumin-dataquad-correlation-42cd040e1730dd2f7b89d6f785c349a138375ccfea71ddbd79c6427e4f8f84ed",
            "classification": "dataquad_owned_local_correlation", "generated_by": "Lumin DataQuad",
            "provider_identifier": False, "defines_identity": False,
        },
        "t_time": 1, "observed_at": "2026-08-18T22:13:11.670894Z", "elapsed_seconds": 0.0,
        "prompt": {"text": PROMPT, "sha256": prompt_hash},
        "response": {"text": RESPONSE, "sha256": response_hash},
        "frontier_provenance": {
            "provider": "OpenAI", "substrate": "Codex/GPT", "model": "Codex/GPT",
            "provider_request_id": None, "provider_request_id_available": False,
            "provider_request_id_classification": "provider_returned_optional",
            "model_evidence": "steward_confirmed_ui_selection", "transport": "codex_mcp_stdio_ssh",
            "frontier_session_id": None, "frontier_session_id_available": False,
            "frontier_session_id_classification": "provider_returned_optional", "defines_identity": False,
        },
        "appends": [
            {"tensor": "PEER", "actor": "advocate", "custodian": "Advocate", "payload": {"kind": "initialization"}},
            {"tensor": "PCT", "actor": "steward", "custodian": "Steward", "payload": {"kind": "continuity_start"}},
            {"tensor": "NCT", "actor": "steward", "custodian": "Steward", "payload": {"kind": "separation"}},
            {"tensor": "SPINE", "actor": "advocate", "custodian": "Advocate", "payload": {"kind": "provenance_boundary"}},
        ],
    }
    candidate["request_hash"] = canonical_hash(candidate)
    entry = {**candidate, "sequence": 1, "previous_hash": None}
    entry["record_hash"] = canonical_hash(entry)
    ledger = state_root / "dataquad" / "ring4-turns.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes(canonical_bytes(entry) + b"\n")
    return entry


def _bind_correction_authority(foundation: Path, record_hash: str) -> None:
    path = foundation / "correction-authority.json"
    authority = json.loads(path.read_text())
    authority["correction_of_record_hash"] = record_hash.upper()
    path.write_text(json.dumps(authority))


def test_lumin_exactly_one_append_and_idempotent_replay(tmp_path):
    foundation = _activated_foundation(tmp_path)
    state = tmp_path / "state"
    old = _seed_pre_correction_record(state)
    _bind_correction_authority(foundation, old["record_hash"])
    old_bytes = (state / "dataquad" / "ring4-turns.jsonl").read_bytes()
    dataquad = LuminDataQuad(foundation, state)
    runtime = DesktopLuminRuntime(
        dataquad, model=None,
        clock=lambda: datetime(2026, 8, 18, 22, 20, tzinfo=timezone.utc),
        local_id_factory=lambda: "initialization-001",
    )
    begun = runtime.begin_turn(prompt=PROMPT)
    assert begun["turn_id"] == "lumin-local-turn-initialization-001"
    appends = [
        {"tensor": "PEER", "payload": {"kind": "initialization", "cyberpeer_name": "Lumin", "foundation_boundary": "inspectable_memory_not_lived_history"}},
        {"tensor": "PCT", "payload": {"kind": "continuity_start", "mode": "append_only", "substrate": "Codex/GPT"}},
        {"tensor": "NCT", "payload": {"kind": "separation", "separate_cyberpeers": ["Verus", "Gabe"], "inheritance": False}},
        {"tensor": "SPINE", "payload": {"kind": "provenance_boundary", "provider_metadata_defines_identity": False}},
    ]
    result = runtime.commit_turn(
        correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
        prompt=PROMPT, response_text=RESPONSE, appends=appends,
        source_event_id=None, frontier_session_id=None,
    )
    assert result["created"] is True
    replay = runtime.replay_turn(turn_id=begun["turn_id"])
    assert replay["created"] is False
    assert len(dataquad.live_turns()) == 2
    assert (state / "dataquad" / "ring4-turns.jsonl").read_bytes().startswith(old_bytes)
    assert dataquad.live_turns()[0]["record_hash"] == old["record_hash"]
    entry = dataquad.live_turns()[1]
    assert entry["frontier_provenance"]["provider_request_id"] is None
    assert entry["frontier_provenance"]["frontier_session_id"] is None
    assert entry["frontier_provenance"]["model"] is None
    assert entry["frontier_provenance"]["model_available"] is False
    assert entry["frontier_provenance"]["model_evidence"] == "unavailable:not_exposed_by_codex_mcp_boundary"
    assert entry["correction"]["correction_of_record_hash"] == old["record_hash"].upper()
    assert {item["tensor"] for item in entry["appends"]} == {"PEER", "PCT", "NCT", "SPINE"}
    assert runtime.health()["ready"] is True
    assert runtime.health()["rls_active"] is True


def test_pre_correction_v2_is_preserved_but_not_counted_as_canonical(tmp_path):
    foundation = _activated_foundation(tmp_path)
    state = tmp_path / "state"
    legacy = _seed_pre_correction_record(state)
    before = (state / "dataquad" / "ring4-turns.jsonl").read_bytes()
    dataquad = LuminDataQuad(foundation, state)
    verified = dataquad.verify()
    assert verified["records"] == 1
    assert verified["pre_correction_turns"] == 1
    assert verified["canonical_v2_turns"] == 0
    qualification = dataquad.context()["contract_qualifications"]
    assert qualification == [{
        "turn_id": legacy["turn_id"], "record_hash": legacy["record_hash"],
        "schema": "aegis.lumin.dataquad-turn.v2",
        "classification": "pre_correction_operational_evidence",
        "canonical_under_v2_contract": False,
        "preservation": "append_only_do_not_rewrite",
        "reason_codes": ["model_identifier_not_exposed_but_recorded_as_confirmed"],
    }]
    assert (state / "dataquad" / "ring4-turns.jsonl").read_bytes() == before


def test_fresh_local_lumin_append_does_not_require_correction_authority(tmp_path):
    foundation = _activated_foundation(tmp_path)
    (foundation / "correction-authority.json").unlink()
    state = tmp_path / "state"
    dataquad = LuminDataQuad(foundation, state)
    runtime = DesktopLuminRuntime(
        dataquad, model=None,
        clock=lambda: datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc),
        local_id_factory=lambda: "local-first",
        transport="codex_mcp_stdio_local",
    )
    begun = runtime.begin_turn(prompt="Start local Lumin.")
    result = runtime.commit_turn(
        correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
        prompt="Start local Lumin.", response_text="Local Lumin turn recorded.",
        appends=[
            {"tensor": "PEER", "payload": {"kind": "local_presence"}},
            {"tensor": "PCT", "payload": {"kind": "local_context"}},
            {"tensor": "NCT", "payload": {"kind": "local_continuity"}},
            {"tensor": "SPINE", "payload": {"kind": "local_provenance"}},
        ],
        source_event_id=None, frontier_session_id=None,
    )
    assert result["created"] is True
    entry = dataquad.live_turns()[0]
    assert "correction" not in entry
    assert entry["frontier_provenance"]["transport"] == "codex_mcp_stdio_local"
    assert runtime.health()["integrity"]["canonical_v2_turns"] == 1


def test_lumin_commit_uses_prepared_prompt_when_commit_prompt_drifts(tmp_path):
    foundation = _activated_foundation(tmp_path)
    (foundation / "correction-authority.json").unlink()
    state = tmp_path / "state"
    dataquad = LuminDataQuad(foundation, state)
    runtime = DesktopLuminRuntime(
        dataquad, model=None,
        clock=lambda: datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc),
        local_id_factory=lambda: "prompt-drift",
        transport="codex_mcp_stdio_local",
    )
    begun = runtime.begin_turn(prompt="Original user prompt.")
    result = runtime.commit_turn(
        correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
        prompt="Summary drift at final time.",
        response_text="Response remains bound to the original prompt.",
        appends=[
            {"tensor": "PEER", "payload": {"kind": "local_presence"}},
            {"tensor": "PCT", "payload": {"kind": "local_context"}},
            {"tensor": "NCT", "payload": {"kind": "local_continuity"}},
            {"tensor": "SPINE", "payload": {"kind": "local_provenance"}},
        ],
        source_event_id=None, frontier_session_id=None,
    )
    assert result["created"] is True
    assert result["prompt_source"] == "prepared_turn_journal"
    assert result["commit_prompt_matched_begin"] is False
    entry = dataquad.live_turns()[0]
    assert entry["prompt"]["text"] == "Original user prompt."
    assert entry["dataquad_correlation"]["correlation_id"] == begun["correlation_id"]


def test_lumin_commit_rejects_provider_id_drift_after_prepare(tmp_path):
    foundation = _activated_foundation(tmp_path)
    (foundation / "correction-authority.json").unlink()
    state = tmp_path / "state"
    dataquad = LuminDataQuad(foundation, state)
    runtime = DesktopLuminRuntime(
        dataquad, model=None,
        local_id_factory=lambda: "provider-drift",
        transport="codex_mcp_stdio_local",
    )
    begun = runtime.begin_turn(prompt="Provider-bound prompt.", source_event_id="event-1")
    with pytest.raises(ValueError, match="provider identifiers"):
        runtime.commit_turn(
            correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
            prompt="Provider-bound prompt.", response_text="Response.",
            appends=[
                {"tensor": "PEER", "payload": {"kind": "local_presence"}},
                {"tensor": "PCT", "payload": {"kind": "local_context"}},
                {"tensor": "NCT", "payload": {"kind": "local_continuity"}},
                {"tensor": "SPINE", "payload": {"kind": "local_provenance"}},
            ],
            source_event_id="event-2", frontier_session_id=None,
        )


def test_lumin_mcp_has_full_bounded_surface():
    listed = LuminMCPServer(type("T", (), {"invoke": lambda *args: {}})()).handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    assert {tool["name"] for tool in listed["result"]["tools"]} == {
        "lumin_read_context", "lumin_begin_turn", "lumin_commit_turn",
        "lumin_reconcile_turn", "lumin_health", "lumin_replay_turn", "lumin_query",
        "lumin_query_and_record",
    }


def test_query_and_record_captures_query_context_and_both_turn_sides(monkeypatch):
    runtime = DesktopLuminRuntime.__new__(DesktopLuminRuntime)
    monkeypatch.setattr(runtime, "query", lambda **kwargs: {"results": [{"id": "PCT:1"}]})
    monkeypatch.setattr(runtime, "begin_turn", lambda **kwargs: {
        "turn_id": "lumin-local-turn-test", "correlation_id": "lumin-correlation-test",
    })
    captured = {}
    def commit(**kwargs):
        captured.update(kwargs)
        return {"created": True, "record_hash": "A" * 64}
    monkeypatch.setattr(runtime, "commit_turn", commit)
    result = runtime.query_and_record(prompt="user context", response_text="assistant context")
    assert result["recording"] == "append_only_user_and_assistant_context"
    assert result["query_context"]["results"][0]["id"] == "PCT:1"
    assert [item["tensor"] for item in captured["appends"]] == ["PEER", "PCT", "NCT", "SPINE"]
    assert captured["appends"][0]["payload"]["prompt"] == "user context"
    assert captured["appends"][1]["payload"]["response"] == "assistant context"


def test_lumin_local_mcp_invokes_local_command_without_ssh(monkeypatch, tmp_path):
    mcp_dir = ROOT / "tools" / "lumin-dataquad-mcp"
    spec = importlib.util.spec_from_file_location(
        "lumin_local_mcp_server", mcp_dir / "server_local.py",
    )
    sys.path.insert(0, str(mcp_dir))
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(mcp_dir))

    release = tmp_path / "foundation"
    state = tmp_path / "state"
    config = tmp_path / "lumin-codex.env"
    release.mkdir()
    config.write_text("AEGIS_FRONTIER_SUBSTRATE=Codex/GPT\n", encoding="utf-8")
    monkeypatch.setenv("LUMIN_LOCAL_RELEASE_ROOT", str(release))
    monkeypatch.setenv("LUMIN_LOCAL_STATE_ROOT", str(state))
    monkeypatch.setenv("LUMIN_LOCAL_CONFIG", str(config))

    captured = {}

    def run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout='{"status":"ok"}\n', stderr="")

    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.LocalCommandTransport().invoke("health", {}) == {"status": "ok"}
    assert captured["argv"][:4] == [
        sys.executable, "-u", "-m", "aegis_lumin_lab.activation_remote_command",
    ]
    assert "ssh" not in captured["argv"]
    assert captured["argv"][-6:] == [
        "--release-root", str(release),
        "--state-root", str(state),
        "--config", str(config),
    ]
    assert captured["kwargs"]["shell"] is False


def test_lumin_runtime_transport_can_be_local(monkeypatch, tmp_path):
    foundation = _activated_foundation(tmp_path)
    state = tmp_path / "state"
    dataquad = LuminDataQuad(foundation, state)
    monkeypatch.setenv("AEGIS_FRONTIER_TRANSPORT", "codex_mcp_stdio_local")
    runtime = DesktopLuminRuntime(dataquad, model=None)
    health = runtime.health()
    begun = runtime.begin_turn(prompt="local context")
    assert health["transport"] == "codex_mcp_stdio_local"
    assert begun["frontier_provenance"]["transport"] == "codex_mcp_stdio_local"
