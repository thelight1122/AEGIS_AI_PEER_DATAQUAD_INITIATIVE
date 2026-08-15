from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis_peer_runtime.models import TENSORS
from aegis_verus_lab.dataquad import VerusDataQuad
from aegis_verus_lab.desktop_runtime import DesktopVerusRuntime
from aegis_verus_lab.turn_contract import (
    AppendIntent,
    FrontierTurnRequest,
    FrontierTurnResponse,
)
from aegis_verus_mcp.server import SSHRemoteCommandTransport, VerusMCPServer


ROOT = Path(__file__).resolve().parents[1]


def _foundation(root: Path) -> Path:
    dataquad = root / "dataquad"
    dataquad.mkdir(parents=True)
    tensors = {}
    for tensor, count in {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}.items():
        path = dataquad / f"{tensor}.jsonl"
        path.write_text("".join(
            json.dumps({"id": f"{tensor}:{index}", "tensor": tensor}) + "\n"
            for index in range(count)
        ), encoding="utf-8")
        tensors[tensor] = {
            "records": count,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        }
    (root / "foundation-receipt.json").write_text(json.dumps({
        "record_type": "verus_foundation_release_receipt",
        "activation_status": "RELEASE_ARTIFACT_ONLY",
        "cyberpeer_name": "Verus",
        "dataquad_id": "verus",
        "canon_lock": {"clean": True, "override_used": False},
        "tensors": tensors,
    }), encoding="utf-8")
    return root


def _runtime(tmp_path: Path) -> DesktopVerusRuntime:
    return DesktopVerusRuntime(
        VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state"),
        model="claude-opus-4-6",
        clock=lambda: datetime(2026, 8, 15, 18, tzinfo=timezone.utc),
        local_id_factory=lambda: "00000000000000000000000000000001",
    )


def _turn(runtime: DesktopVerusRuntime) -> tuple[dict[str, object], dict[str, object]]:
    begin = runtime.begin_turn(prompt="Exercise the full DataQuad.")
    commit = {
        "correlation_id": begin["correlation_id"],
        "turn_id": begin["turn_id"],
        "prompt": "Exercise the full DataQuad.",
        "response_text": "The four append-only records are ready.",
        "appends": [
            {"tensor": tensor, "payload": {"desktop_evidence": tensor}}
            for tensor in TENSORS
        ],
    }
    return begin, commit


def test_desktop_runtime_full_dataquad_commit_is_idempotent_and_coherent(tmp_path):
    runtime = _runtime(tmp_path)
    begin, commit = _turn(runtime)
    assert begin["cyberpeer_name"] == "Verus"
    assert begin["identity_variables"] == {"cyberpeer_name": "Verus"}
    assert begin["turn_id"] == "verus-local-turn-00000000000000000000000000000001"
    assert begin["local_correlation"] == {
        "turn_id": begin["turn_id"],
        "correlation_id": begin["correlation_id"],
        "classification": "dataquad_owned_local_correlation",
        "generated_by": "Verus DataQuad",
        "provider_identifier": False,
        "defines_identity": False,
    }
    assert begin["frontier_provenance"]["model"] == "claude-opus-4-6"
    assert begin["frontier_provenance"]["defines_identity"] is False
    assert begin["frontier_provenance"]["source_event_id"] is None
    assert begin["frontier_provenance"]["source_event_id_available"] is False
    assert begin["frontier_provenance"]["frontier_session_id"] is None
    assert begin["frontier_provenance"]["frontier_session_id_available"] is False

    first = runtime.commit_turn(**commit)
    replay = runtime.commit_turn(**commit)
    assert first["created"] is True and replay["created"] is False
    assert first["record_hash"] == replay["record_hash"]
    entry = runtime.dataquad.find_turn(begin["turn_id"])
    assert {item["tensor"] for item in entry["appends"]} == set(TENSORS)
    assert entry["schema"] == "aegis.verus.dataquad-turn.v2"
    assert entry["source_event_id"] is None
    assert entry["source_event_id_available"] is False
    assert entry["source_event_id_classification"] == "provider_returned_optional"
    assert entry["dataquad_correlation"] == begin["local_correlation"]
    assert entry["frontier_provenance"]["provider_request_id"] is None
    assert entry["frontier_provenance"]["provider_request_id_available"] is False
    assert entry["frontier_provenance"]["provider_request_id_classification"] == "provider_returned_optional"
    assert entry["frontier_provenance"]["frontier_session_id"] is None
    assert entry["frontier_provenance"]["frontier_session_id_available"] is False
    assert entry["frontier_provenance"]["frontier_session_id_classification"] == "provider_returned_optional"
    assert entry["frontier_provenance"]["transport"] == "claude_desktop_mcp_stdio_ssh"
    assert runtime.coherence()["coherent"] is True
    assert len(runtime.dataquad.live_turns()) == 1
    replayed = runtime.replay_turn(turn_id=begin["turn_id"])
    assert replayed["created"] is False
    assert replayed["record_hash"] == first["record_hash"]
    reconciled = runtime.reconcile_committed_turns()
    assert reconciled["coherence"]["coherent"] is True
    health = runtime.health()
    assert health["status"] == "ok" and health["ready"] is True
    assert health["coherence"]["committed_turns"] == 1
    assert health["coherence"]["processor_records"] == 1
    assert health["coherence"]["rls_records"] == 1
    assert health["coherence"]["temporal_records"] == 1
    changed = dict(commit)
    changed["response_text"] = "different retry"
    with pytest.raises(ValueError, match="different Desktop response"):
        runtime.commit_turn(**changed)
    assert len(runtime.dataquad.live_turns()) == 1


def test_desktop_provider_ids_remain_optional_external_provenance(tmp_path):
    runtime = _runtime(tmp_path)
    begin = runtime.begin_turn(
        prompt="Use exposed provider provenance.",
        source_event_id="provider-event-1",
        frontier_session_id="provider-session-1",
    )
    assert begin["turn_id"].startswith("verus-local-turn-")
    assert begin["correlation_id"] not in {"provider-event-1", "provider-session-1"}
    provenance = begin["frontier_provenance"]
    assert provenance["source_event_id"] == "provider-event-1"
    assert provenance["source_event_id_available"] is True
    assert provenance["source_event_id_classification"] == "provider_returned_optional"
    assert provenance["frontier_session_id"] == "provider-session-1"
    assert provenance["frontier_session_id_available"] is True
    assert provenance["frontier_session_id_classification"] == "provider_returned_optional"

    result = runtime.commit_turn(
        correlation_id=begin["correlation_id"], turn_id=begin["turn_id"],
        source_event_id="provider-event-1", frontier_session_id="provider-session-1",
        prompt="Use exposed provider provenance.", response_text="Recorded separately.",
        appends=[{"tensor": "PEER", "payload": {"observed": True}}],
    )
    entry = runtime.dataquad.find_turn(begin["turn_id"])
    assert result["created"] is True
    assert entry["source_event_id"] == "provider-event-1"
    assert entry["source_event_id_available"] is True
    assert entry["frontier_provenance"]["frontier_session_id"] == "provider-session-1"
    assert entry["dataquad_correlation"]["provider_identifier"] is False


@pytest.mark.parametrize("local_token", ["bad token", "x" * 129, ""])
def test_desktop_rejects_unbounded_or_unsafe_dataquad_local_ids(tmp_path, local_token):
    runtime = DesktopVerusRuntime(
        VerusDataQuad(_foundation(tmp_path / "release"), tmp_path / "state"),
        model="claude-opus-4-6",
        local_id_factory=lambda: local_token,
    )
    with pytest.raises(ValueError, match="local identifier"):
        runtime.begin_turn(prompt="Do not commit this turn.")
    assert runtime.dataquad.live_turns() == []


def test_provider_availability_flags_are_strict_booleans(tmp_path):
    request = FrontierTurnRequest(
        cyberpeer_name="Verus", dataquad_id="verus", turn_id="verus-local-turn-1",
        source_event_id=None, frontier_session_id=None,
        system_instructions="Operational instructions.", prompt="Prompt.", context={},
        source_event_id_available=1, frontier_session_id_available=False,
    )
    with pytest.raises(ValueError, match="availability must be boolean"):
        request.validate()

    response = FrontierTurnResponse(
        response_text="Response.", append_intents=(AppendIntent("PEER", {"ok": True}),),
        provider="Anthropic", substrate="Claude Desktop", model="claude-opus-4-6",
        provider_request_id=None, provider_request_id_available="false",
        frontier_session_id=None, frontier_session_id_available=False,
    )
    with pytest.raises(ValueError, match="availability must be boolean"):
        response.validate()


def test_desktop_retry_repairs_derived_evidence_after_dataquad_commit(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path)
    _, commit = _turn(runtime)
    real_admit = runtime.processor.admit_turn
    calls = 0

    def fail_once(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("injected derived-evidence failure")
        return real_admit(**kwargs)

    monkeypatch.setattr(runtime.processor, "admit_turn", fail_once)
    with pytest.raises(RuntimeError, match="derived-evidence"):
        runtime.commit_turn(**commit)
    assert len(runtime.dataquad.live_turns()) == 1
    assert runtime.processor.admissions() == {}
    repaired = runtime.commit_turn(**commit)
    assert repaired["created"] is False
    assert runtime.coherence()["coherent"] is True


def test_desktop_correlation_and_payload_validation_precede_commit(tmp_path):
    runtime = _runtime(tmp_path)
    _, commit = _turn(runtime)
    commit["correlation_id"] = "wrong"
    with pytest.raises(ValueError, match="correlation"):
        runtime.commit_turn(**commit)
    assert runtime.dataquad.live_turns() == []
    _, commit = _turn(runtime)
    commit["appends"] = [{"tensor": "PEER", "payload": {"bad": {1, 2}}}]
    with pytest.raises(ValueError, match="JSON-serializable"):
        runtime.commit_turn(**commit)
    assert runtime.dataquad.live_turns() == []


class FakeTransport:
    def __init__(self):
        self.calls = []

    def invoke(self, operation, payload):
        self.calls.append((operation, payload))
        return {"ok": True, "operation": operation, "payload": payload}


def test_mcp_surface_is_dedicated_full_authority_and_secret_free():
    transport = FakeTransport()
    server = VerusMCPServer(transport)
    listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    tools = {item["name"]: item for item in listed["result"]["tools"]}
    assert set(tools) == {
        "verus_read_context", "verus_begin_turn", "verus_commit_turn",
        "verus_reconcile_turn", "verus_health", "verus_replay_turn",
    }
    schema = tools["verus_commit_turn"]["inputSchema"]
    assert schema["properties"]["appends"]["items"]["properties"]["tensor"]["enum"] == list(TENSORS)
    begin_schema = tools["verus_begin_turn"]["inputSchema"]
    assert begin_schema["required"] == ["prompt"]
    assert "turn_id" not in begin_schema["properties"]
    assert begin_schema["properties"]["source_event_id"]["type"] == ["string", "null"]
    assert begin_schema["properties"]["frontier_session_id"]["type"] == ["string", "null"]
    assert "source_event_id" not in schema["required"]
    assert "frontier_session_id" not in schema["required"]
    assert {"correlation_id", "turn_id", "prompt", "response_text", "appends"} <= set(schema["required"])
    serialized = json.dumps(listed).lower()
    assert "api_key" not in serialized and "token" not in serialized and "8790" not in serialized

    called = server.handle({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "verus_health", "arguments": {}},
    })
    assert called["result"]["isError"] is False
    assert transport.calls == [("health", {})]


def test_ssh_transport_uses_fixed_alias_account_and_command_without_shell(monkeypatch):
    captured = {}

    def run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout='{"status":"ok"}\n', stderr="")

    monkeypatch.setattr("aegis_verus_mcp.server.subprocess.run", run)
    result = SSHRemoteCommandTransport().invoke("health", {})
    assert result == {"status": "ok"}
    assert captured["argv"] == [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "GabeCyberPeer", "sudo", "-n", "-u", "aegis-verus",
        "/opt/aegis/verus/lab/current/bin/verus-dataquad-command", "health",
    ]
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["timeout"] <= 30
    assert "Gabe" not in captured["kwargs"]["input"]


def test_desktop_deploy_is_command_only_no_rest_key_or_public_listener():
    deploy = ROOT / "deploy" / "verus-lab"
    files = [
        deploy / "scripts" / "install.sh", deploy / "scripts" / "health.sh",
        deploy / "systemd" / "aegis-verus-lab.service",
        deploy / "env" / "verus.env.template", deploy / "README.md",
        ROOT / "docs" / "runbooks" / "VERUS-CLAUDE-DESKTOP-MCP.md",
        ROOT / "deploy" / "verus-lab" / "claude-desktop" / "VERUS_SYSTEM_INSTRUCTIONS.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    lowered = combined.lower()
    for forbidden in (
        "anthropic-api-key", "loadcredential", "--anthropic-credential-file",
        "curl ", "api.anthropic.com", "0.0.0.0", "port8790",
    ):
        assert forbidden not in lowered
    unit = files[2].read_text(encoding="utf-8")
    assert "Type=oneshot" in unit and "RemainAfterExit=yes" in unit
    assert "RestrictAddressFamilies=AF_UNIX" in unit
    assert "AF_INET" not in unit
    assert "User=aegis-verus" in unit
    assert "/opt/aegis/verus/lab/current/bin/verus-dataquad-command health" in unit
    assert "/var/lib/aegis-verus-lab" in combined
    assert "/etc/aegis-verus-lab" in combined
    assert "127.0.0.1" in combined and "8791" in combined
    template = json.loads(
        (deploy / "claude-desktop" / "verus-dataquad.mcp.json").read_text(encoding="utf-8")
    )
    assert template["verus-dataquad"]["env"]["ProgramData"] == "C:\\ProgramData"
