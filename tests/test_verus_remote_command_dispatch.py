"""The remote command surface must tolerate the MCP server's provenance stamp.

tools/verus-dataquad-mcp/server.py adds _substrate to every tool payload. The
runtime methods take keyword-only arguments, so an unstripped _substrate raises
TypeError — which main()'s (ValueError, OSError, JSONDecodeError) handler does
not catch, so the command exits 1 with a raw traceback and begin, commit, query
and replay all fail on the frontier path.

This was hand-patched on the VM on 2026-08-15 and never returned to source. A
release built from the repository regressed it on 2026-08-20 and took recording
down until rollback. The line stays covered.
"""

from __future__ import annotations

import pytest

from aegis_verus_lab.remote_command import OPERATIONS, dispatch


class _Recorder:
    """Stands in for DesktopVerusRuntime, recording the kwargs it is handed."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.dataquad = self

    def context(self) -> dict:
        self.calls.append(("context", {}))
        return {"operation": "context"}

    def _record(self, name: str):
        def call(**kwargs):
            self.calls.append((name, kwargs))
            return {"operation": name}
        return call

    def __getattr__(self, name: str):
        if name in {
            "begin_turn", "commit_turn", "replay_turn", "query",
            "reconcile_committed_turns", "health",
        }:
            return self._record(name)
        raise AttributeError(name)


SUBSTRATE_PAYLOAD = {"_substrate": "Claude Code"}


@pytest.mark.parametrize("operation", sorted(OPERATIONS))
def test_every_operation_survives_the_substrate_stamp(operation):
    runtime = _Recorder()
    payload = dict(SUBSTRATE_PAYLOAD)
    if operation == "begin":
        payload["prompt"] = "p"
    elif operation == "commit":
        payload.update(correlation_id="c", turn_id="t", prompt="p", response_text="r", appends=[])
    elif operation == "replay":
        payload["turn_id"] = "t"
    elif operation == "query":
        payload["prompt"] = "p"

    result = dispatch(runtime, operation, payload)

    assert result
    for _, kwargs in runtime.calls:
        assert "_substrate" not in kwargs


def test_substrate_is_removed_from_the_caller_payload():
    payload = {"_substrate": "Claude Code", "prompt": "p"}

    dispatch(_Recorder(), "query", payload)

    assert payload == {"prompt": "p"}


def test_real_arguments_are_still_forwarded():
    runtime = _Recorder()

    dispatch(runtime, "query", {"_substrate": "Claude Code", "prompt": "p", "limit": 5})

    assert runtime.calls == [("query", {"prompt": "p", "limit": 5})]


def test_unsupported_operation_is_refused():
    with pytest.raises(ValueError):
        dispatch(_Recorder(), "not-an-operation", {})
