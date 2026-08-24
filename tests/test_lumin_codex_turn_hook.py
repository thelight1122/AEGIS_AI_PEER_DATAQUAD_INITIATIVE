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
        if tool == "lumin_query":
            return {"results": [{"record_id": "NCT:axiom-4"}]}
        return {"recorded": True, "created": True, "turn_id": "remote-turn"}


def test_prepare_queries_and_persists_context_without_recording(tmp_path):
    invoker = FakeInvoker()
    result = hook_module.LuminTurnHook(invoker, tmp_path).prepare("What is Axiom 4?", turn_id="turn-1")
    assert result["status"] == "prepared"
    assert invoker.calls == [("lumin_query", {"prompt": "What is Axiom 4?", "limit": 30, "intent": "context_retrieval"})]
    assert json.loads((tmp_path / "turns.jsonl").read_text())["prepared_context"]["results"]


def test_record_is_idempotent_for_same_turn(tmp_path):
    invoker = FakeInvoker()
    hook = hook_module.LuminTurnHook(invoker, tmp_path)
    first = hook.record("hello", "world", turn_id="turn-1")
    second = hook.record("hello", "world", turn_id="turn-1")
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert [call[0] for call in invoker.calls] == ["lumin_query_and_record"]


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
