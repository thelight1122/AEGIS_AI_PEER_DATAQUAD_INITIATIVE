from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE = Path(__file__).parents[1] / "scripts" / "lumin_codex_turn_hook.py"
spec = importlib.util.spec_from_file_location("lumin_codex_turn_hook", MODULE)
hook_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook_module)


class FakeInvoker:
    def __init__(self):
        self.calls = []

    def call(self, tool, arguments):
        self.calls.append((tool, dict(arguments)))
        if tool == "lumin_begin_turn":
            return {
                "turn_id": "lumin-turn-1",
                "correlation_id": "lumin-correlation-1",
                "dataquad_context": {"recent_live_turns": []},
            }
        return {"recorded": True, "created": True, "turn_id": "lumin-turn-1"}


def test_prepare_queries_and_persists_context_without_recording(tmp_path):
    invoker = FakeInvoker()
    result = hook_module.LuminTurnHook(invoker, tmp_path).prepare("What is Axiom 4?", turn_id="turn-1")
    assert result["status"] == "prepared"
    assert invoker.calls == [("lumin_begin_turn", {
        "prompt": "What is Axiom 4?",
        "source_event_id": None,
        "frontier_session_id": None,
    })]
    entry = json.loads((tmp_path / "turns.jsonl").read_text())
    assert entry["dataquad_turn_id"] == "lumin-turn-1"
    assert entry["correlation_id"] == "lumin-correlation-1"


def test_record_is_idempotent_for_same_turn(tmp_path):
    invoker = FakeInvoker()
    hook = hook_module.LuminTurnHook(invoker, tmp_path)
    first = hook.record("hello", "world", turn_id="turn-1")
    second = hook.record("hello", "world", turn_id="turn-1")
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert [call[0] for call in invoker.calls] == ["lumin_begin_turn", "lumin_commit_turn"]
    commit = invoker.calls[1][1]
    assert commit["turn_id"] == "lumin-turn-1"
    assert commit["correlation_id"] == "lumin-correlation-1"
    assert [item["tensor"] for item in commit["appends"]] == ["PEER", "PCT", "NCT", "SPINE"]


def test_failed_record_is_explicit_and_can_be_retried(tmp_path):
    class Failing:
        def call(self, tool, arguments):
            raise RuntimeError("offline")

    hook = hook_module.LuminTurnHook(Failing(), tmp_path)
    try:
        hook.record("hello", "world", turn_id="turn-1")
    except RuntimeError:
        pass
    statuses = [json.loads(line)["status"] for line in (tmp_path / "turns.jsonl").read_text().splitlines()]
    assert statuses == ["recording_pending", "recording_failed"]


def test_retry_after_failed_record_can_succeed(tmp_path):
    class Flaky:
        def __init__(self):
            self.calls = []

        def call(self, tool, arguments):
            self.calls.append((tool, dict(arguments)))
            if len(self.calls) == 1:
                raise RuntimeError("offline")
            if tool == "lumin_begin_turn":
                return {
                    "turn_id": "lumin-turn-2",
                    "correlation_id": "lumin-correlation-2",
                    "dataquad_context": {"recent_live_turns": []},
                }
            return {"recorded": True, "created": True, "turn_id": "lumin-turn-2"}

    hook = hook_module.LuminTurnHook(Flaky(), tmp_path)
    try:
        hook.record("hello", "world", turn_id="turn-1")
    except RuntimeError:
        pass

    result = hook.record("hello", "world", turn_id="turn-1")
    assert result["status"] == "recorded"
    assert result["duplicate"] is False
    statuses = [json.loads(line)["status"] for line in (tmp_path / "turns.jsonl").read_text().splitlines()]
    assert statuses == ["recording_pending", "recording_failed", "recording_pending", "prepared", "recorded"]


def test_stdio_invoker_defaults_to_local_lumin_server(monkeypatch):
    monkeypatch.delenv("LUMIN_MCP_SERVER", raising=False)
    invoker = hook_module.StdioMCPInvoker()
    assert invoker.server == hook_module.DEFAULT_SERVER
    assert invoker.server.name == "server_local.py"
    assert "LUMIN_SSH_ALIAS" not in invoker.env
    assert invoker.env["LUMIN_LOCAL_RELEASE_ROOT"].endswith(r"deploy\lumin-lab\local\foundation")
    assert invoker.env["LUMIN_LOCAL_STATE_ROOT"].endswith(r"deploy\lumin-lab\local\state")
    assert invoker.env["LUMIN_LOCAL_CONFIG"].endswith(r"deploy\lumin-lab\local\lumin-codex.env")
