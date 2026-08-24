from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis_lumin_lab.dataquad import LuminFoundationDataQuad
from aegis_lumin_mcp.server import LuminMCPServer, SSHRemoteCommandTransport


ROOT = Path(__file__).resolve().parents[1]
SEATING_TIMESTAMP = "2026-08-18T12:00:00Z"
spec = importlib.util.spec_from_file_location(
    "build_lumin_release", ROOT / "scripts" / "build_lumin_genesis_release.py",
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def invoke(self, operation, payload):
        self.calls.append((operation, payload))
        return {"status": "ok", "operation": operation}


def test_lumin_release_is_independently_rooted_read_only_and_not_installed(tmp_path):
    output = tmp_path / "lumin-release"
    manifest = builder.build_release(
        output, source_commit="test-commit", seating_timestamp=SEATING_TIMESTAMP,
    )
    assert manifest["release_kind"] == "LUMIN_GENESIS_FOUNDATION_PREPARATION"
    assert manifest["activation_status"] == "NOT_INSTALLED"
    assert manifest["cyberpeer_name"] == "Lumin"
    assert manifest["identity_variables"] == {"cyberpeer_name": "Lumin"}
    assert manifest["frontier_provenance"] == {
        "provider": "OpenAI", "substrate": "Codex/GPT", "defines_identity": False,
    }
    assert manifest["ring_4_writes_authorized"] is False
    assert manifest["rls_active"] is False
    assert manifest["live_state_written"] is False
    assert manifest["other_peer_state_included"] is False

    dataquad = LuminFoundationDataQuad(output / "foundation")
    assert dataquad.health() == {
        "status": "ok", "ready": False, "activation_status": "NOT_INSTALLED",
        "cyberpeer_name": "Lumin", "dataquad_id": "lumin",
        "foundation_records": 133, "ring_4_records": 0,
        "rls_active": False, "verified": True,
    }
    context = dataquad.context()
    assert context["identity_variables"] == {"cyberpeer_name": "Lumin"}
    assert context["foundation_is_lived_history"] is False
    assert context["append_contract"] == {"mode": "not-authorized", "tensors": []}
    assert set(context["foundation"]) == {"SPINE", "NCT", "PEER", "PCT"}

    receipt = json.loads((output / "foundation" / "foundation-receipt.json").read_text())
    assert receipt["built_from"]["roster_mapping"] == {
        "peer_id": "lumin", "session_id": "lumin-session-001", "model_id": "ap1001",
    }
    assert receipt["foundation_boundary"]["inspectable_memory"] is True
    assert receipt["foundation_boundary"]["lived_history"] is False
    assert receipt["authority"]["rings_1_3"] == "AUTHORIZED_PREPARATION"
    assert receipt["authority"]["ring_4_writes"] == "NOT_AUTHORIZED"
    for tensor, expected in {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}.items():
        records = [json.loads(line) for line in
                   (output / "foundation" / "dataquad" / f"{tensor}.jsonl").read_text().splitlines()]
        assert len(records) == expected
        assert all(record["cyberpeer_name"] == "Lumin" for record in records)
        assert all(record["routing_provenance"] == {
            "dataquad_id": "lumin", "foundation_session_id": "lumin-session-001",
            "prior_model_id": "ap1001", "provider": "OpenAI",
            "substrate": "Codex/GPT", "defines_identity": False,
        } for record in records)
        for record in records:
            non_routing = {key: value for key, value in record.items() if key != "routing_provenance"}
            assert "peer_id" not in json.dumps(non_routing)
            assert "model_id" not in json.dumps(non_routing)

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in output.rglob("*") if path.is_file()
    )
    assert "/opt/aegis/lumin/lab" in combined
    assert "aegis-lumin" in combined
    assert "AEGIS_RLS_ACTIVE=false" in combined
    assert "NOT_INSTALLED" in combined
    assert "aegis-verus" not in combined
    assert "/opt/aegis/verus/lab" not in combined
    assert "ring4-turns.jsonl" not in combined
    assert not any("ledger" in path.name.lower() for path in output.rglob("*"))
    context_files = {
        path.name for path in (output / "pod" / "context").glob("*.jsonl")
    }
    assert context_files == {"PEER.jsonl", "PCT.jsonl", "NCT.jsonl", "SPINE.jsonl"}
    assert all((output / "pod" / "context" / name).read_bytes() == b""
               for name in context_files)
    mcp_config = json.loads((output / "codex" / "lumin-dataquad.mcp.json").read_text())
    assert set(mcp_config) == {"mcpServers"}
    assert set(mcp_config["mcpServers"]) == {"lumin-dataquad"}
    gate = json.loads((output / "DEPLOYMENT-GATE.json").read_text())
    assert gate["current_phase"] == "LOCAL_PREPARATION_ONLY"
    assert gate["remote_boundary"]["verified_on_vm"] is False


def test_lumin_release_reuses_verified_rls_code_without_verus_records(tmp_path):
    output = tmp_path / "release"
    builder.build_release(output, seating_timestamp=SEATING_TIMESTAMP)
    source = ROOT / "deploy" / "verus-lab" / "pod" / "vendor" / "orb-rls-persistent-relations-core"
    copied = output / "pod" / "vendor" / "orb-rls-persistent-relations-core"
    for source_path in source.rglob("*.py"):
        copied_path = copied / source_path.relative_to(source)
        assert copied_path.read_bytes() == source_path.read_bytes()
    marker = json.loads((output / "pod" / "markers" / "rls-persistent-relations-core.verified-code-marker.json").read_text())
    assert marker["source_hash"] == "51A1AC18887AEA9CEACC60B6F0AD428C899FA2D228D3BEE2032171F754E248CA"
    assert marker["lumin_attachment_status"] == "COPIED_NOT_ACTIVATED"
    pod = json.loads((output / "pod" / "lumin-cyberpeer-pod.json").read_text())
    assert pod["peer_id"] == "lumin"
    assert pod["processor"]["status"] == "inactive_not_authorized"
    assert pod["temporal_daemon"]["status"] == "inactive_not_authorized"
    assert pod["orbs"][0]["status"] == "attached_via_umbilical"


def test_lumin_release_contains_architecture_only_daemon_and_tensor_context_layout(tmp_path):
    output = tmp_path / "release"
    builder.build_release(output, seating_timestamp=SEATING_TIMESTAMP)
    runtime = output / "lib" / "aegis_peer_runtime"
    assert {path.name for path in runtime.glob("*_daemon.py")} == {
        "steward_daemon.py", "advocate_daemon.py", "temporal_daemon.py",
        "processor_daemon.py",
    }
    assert (output / "pod" / "tensor-spec.json").is_file()
    assert (output / "pod" / "daemon-topology.json").is_file()
    assert "attached_via_umbilical" in (output / "pod" / "lumin-cyberpeer-pod.json").read_text()


def test_lumin_mcp_exposes_activated_operations_and_fixed_remote_boundary(monkeypatch):
    transport = FakeTransport()
    server = LuminMCPServer(transport)
    listed = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert {tool["name"] for tool in listed["result"]["tools"]} == {
        "lumin_read_context", "lumin_begin_turn", "lumin_commit_turn",
        "lumin_reconcile_turn", "lumin_health", "lumin_replay_turn", "lumin_query",
    }
    called = server.handle({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": "lumin_health", "arguments": {}},
    })
    assert called["result"]["isError"] is False
    assert transport.calls == [("health", {"_substrate": "Codex/GPT"})]

    captured = {}
    def run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout='{"status":"ok"}\n', stderr="")

    monkeypatch.setattr("aegis_lumin_mcp.server.subprocess.run", run)
    assert SSHRemoteCommandTransport().invoke("health", {}) == {"status": "ok"}
    assert captured["argv"] == [
        "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
        "GabeCyberPeer", "sudo", "-n", "-u", "aegis-lumin",
        "/opt/aegis/lumin/lab/current/bin/lumin-dataquad-command", "health",
    ]
    assert captured["kwargs"]["shell"] is False


def test_lumin_remote_dispatch_consumes_transport_substrate_metadata():
    from aegis_lumin_lab.activation_remote_command import dispatch

    class Runtime:
        def query(self, **kwargs):
            assert kwargs == {"prompt": "Axiom 4", "limit": 5}
            return {"ok": True}

    assert dispatch(Runtime(), "query", {
        "prompt": "Axiom 4", "limit": 5, "_substrate": "Codex/GPT",
    }) == {"ok": True}


def test_lumin_builder_refuses_nonempty_output_and_non_utc_time(tmp_path):
    output = tmp_path / "occupied"
    output.mkdir()
    (output / "preserve").write_text("user data")
    with pytest.raises(builder.ReleaseBuildRefused, match="absent or empty"):
        builder.build_release(output, seating_timestamp=SEATING_TIMESTAMP)
    assert (output / "preserve").read_text() == "user data"
    with pytest.raises(builder.ReleaseBuildRefused, match="seating_timestamp"):
        builder.build_release(tmp_path / "bad-time", seating_timestamp="2026-08-18")


def test_lumin_release_is_deterministic_for_explicit_inputs(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    builder.build_release(first, source_commit="same", seating_timestamp=SEATING_TIMESTAMP)
    builder.build_release(second, source_commit="same", seating_timestamp=SEATING_TIMESTAMP)
    assert (first / "release-manifest.json").read_bytes() == (second / "release-manifest.json").read_bytes()
    assert {
        str(path.relative_to(first)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in first.rglob("*") if path.is_file()
    } == {
        str(path.relative_to(second)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in second.rglob("*") if path.is_file()
    }
