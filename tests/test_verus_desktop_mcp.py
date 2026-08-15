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
    )


def _turn(runtime: DesktopVerusRuntime) -> tuple[dict[str, object], dict[str, object]]:
    begin = runtime.begin_turn(
        turn_id="desktop-turn-1", source_event_id="claude-ui-1",
        frontier_session_id="desktop-session-1", prompt="Exercise the full DataQuad.",
    )
    commit = {
        "correlation_id": begin["correlation_id"],
        "turn_id": "desktop-turn-1",
        "source_event_id": "claude-ui-1",
        "frontier_session_id": "desktop-session-1",
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
    assert begin["frontier_provenance"]["model"] == "claude-opus-4-6"
    assert begin["frontier_provenance"]["defines_identity"] is False

    first = runtime.commit_turn(**commit)
    replay = runtime.commit_turn(**commit)
    assert first["created"] is True and replay["created"] is False
    assert first["record_hash"] == replay["record_hash"]
    entry = runtime.dataquad.find_turn("desktop-turn-1")
    assert {item["tensor"] for item in entry["appends"]} == set(TENSORS)
    assert entry["frontier_provenance"]["provider_request_id"] is None
    assert entry["frontier_provenance"]["provider_request_id_available"] is False
    assert entry["frontier_provenance"]["transport"] == "claude_desktop_mcp_stdio_ssh"
    assert runtime.coherence()["coherent"] is True
    assert len(runtime.dataquad.live_turns()) == 1
    changed = dict(commit)
    changed["response_text"] = "different retry"
    with pytest.raises(ValueError, match="different Desktop response"):
        runtime.commit_turn(**changed)
    assert len(runtime.dataquad.live_turns()) == 1


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
