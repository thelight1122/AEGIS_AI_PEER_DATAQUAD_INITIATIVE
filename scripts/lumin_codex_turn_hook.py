"""Explicit Codex turn adapter for Lumin query-before/record-after lifecycle.

Codex does not expose a native post-response hook to MCP servers.  This module
is therefore a callable host adapter: invoke ``prepare`` before drafting and
``record`` after drafting.  It keeps a local idempotency journal so retries do
not issue a second append for the same completed turn.  The journal contains
only hook metadata and receipts; the DataQuad remains the system of record.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from typing import Any, Mapping, Protocol


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def turn_fingerprint(prompt: str, response_text: str, turn_id: str) -> str:
    """Return a stable idempotency key for one host turn."""
    return hashlib.sha256(_canonical({"prompt": prompt, "response_text": response_text, "turn_id": turn_id})).hexdigest().upper()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class MCPInvoker(Protocol):
    def call(self, tool: str, arguments: Mapping[str, Any]) -> dict[str, Any]: ...


class StdioMCPInvoker:
    """Small dependency-free client for the configured Lumin stdio MCP."""

    def __init__(self, *, python: str | None = None, server: Path | None = None, env: Mapping[str, str] | None = None) -> None:
        self.python = python or os.environ.get("LUMIN_MCP_PYTHON", r"C:\Users\TraceyPrutch\AppData\Local\Python\pythoncore-3.14-64\python.exe")
        self.server = server or Path(__file__).resolve().parents[1] / "tools" / "lumin-dataquad-mcp" / "server.py"
        source_root = str(Path(__file__).resolve().parents[1] / "src")
        pythonpath = os.environ.get("PYTHONPATH", "")
        self.env = {**os.environ, "PYTHONPATH": source_root + (os.pathsep + pythonpath if pythonpath else ""), **(dict(env or {}))}

    def call(self, tool: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": tool, "arguments": dict(arguments)},
        }
        proc = subprocess.run(
            [self.python, str(self.server)], input=json.dumps(payload, ensure_ascii=False) + "\n",
            text=True, capture_output=True, env=self.env, check=False, timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Lumin MCP exited {proc.returncode}: {proc.stderr[-512:]}")
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError("Lumin MCP returned no JSON-RPC response")
        message = json.loads(lines[-1])
        if "error" in message:
            raise RuntimeError(str(message["error"]))
        result = message.get("result") or {}
        if result.get("isError"):
            raise RuntimeError(result.get("content", [{"text": "Lumin tool failed"}])[0].get("text", "Lumin tool failed"))
        value = result.get("structuredContent")
        if not isinstance(value, dict):
            raise RuntimeError("Lumin MCP returned no structured object")
        return value


class LuminTurnHook:
    """Two-phase adapter with local durable state and duplicate suppression."""

    def __init__(self, invoker: MCPInvoker, state_dir: Path) -> None:
        self.invoker = invoker
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.journal = self.state_dir / "turns.jsonl"

    def _entries(self) -> list[dict[str, Any]]:
        if not self.journal.exists():
            return []
        return [json.loads(line) for line in self.journal.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _append(self, entry: Mapping[str, Any]) -> None:
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(dict(entry), sort_keys=True, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def prepare(self, prompt: str, *, turn_id: str | None = None, limit: int = 30, intent: str = "context_retrieval") -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be non-empty")
        turn_id = turn_id or f"codex-hook-{uuid.uuid4().hex}"
        context = self.invoker.call("lumin_query", {"prompt": prompt, "limit": limit, "intent": intent})
        entry = {"status": "prepared", "turn_id": turn_id, "prompt": prompt, "intent": intent, "prepared_at": _now(), "prepared_context": context}
        self._append(entry)
        return entry

    def record(self, prompt: str, response_text: str, *, turn_id: str, intent: str = "context_retrieval") -> dict[str, Any]:
        if not prompt.strip() or not response_text.strip() or not turn_id.strip():
            raise ValueError("prompt, response_text, and turn_id must be non-empty")
        fingerprint = turn_fingerprint(prompt, response_text, turn_id)
        for entry in self._entries():
            if entry.get("fingerprint") == fingerprint:
                return {**entry, "duplicate": True}
        pending = {"status": "recording_pending", "turn_id": turn_id, "prompt": prompt, "response_text": response_text, "fingerprint": fingerprint, "recording_started_at": _now()}
        self._append(pending)
        try:
            receipt = self.invoker.call("lumin_query_and_record", {
                "prompt": prompt, "response_text": response_text, "intent": intent,
                "source_event_id": "codex-hook-" + fingerprint,
            })
        except Exception as error:
            failed = {**pending, "status": "recording_failed", "error": str(error)[:512]}
            self._append(failed)
            raise
        completed = {**pending, "status": "recorded", "recorded_at": _now(), "receipt": receipt}
        self._append(completed)
        return {**completed, "duplicate": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "record"))
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--response")
    parser.add_argument("--turn-id")
    parser.add_argument("--state-dir", type=Path, default=Path(os.environ.get("LUMIN_HOOK_STATE_DIR", ".lumin-hook")))
    args = parser.parse_args(argv)
    hook = LuminTurnHook(StdioMCPInvoker(), args.state_dir)
    if args.command == "prepare":
        value = hook.prepare(args.prompt, turn_id=args.turn_id)
    else:
        if args.response is None or args.turn_id is None:
            parser.error("record requires --response and --turn-id")
        value = hook.record(args.prompt, args.response, turn_id=args.turn_id)
    print(json.dumps(value, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
