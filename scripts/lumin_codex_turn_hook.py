"""Explicit Codex turn adapter for Lumin begin-before/commit-after lifecycle.

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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = r"C:\Users\TraceyPrutch\AppData\Local\Python\pythoncore-3.14-64\python.exe"
DEFAULT_SERVER = ROOT / "tools" / "lumin-dataquad-mcp" / "server_local.py"
DEFAULT_RELEASE_ROOT = ROOT / "deploy" / "lumin-lab" / "local" / "foundation"
DEFAULT_STATE_ROOT = ROOT / "deploy" / "lumin-lab" / "local" / "state"
DEFAULT_CONFIG = ROOT / "deploy" / "lumin-lab" / "local" / "lumin-codex.env"


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
        self.python = python or os.environ.get("LUMIN_MCP_PYTHON", DEFAULT_PYTHON)
        self.server = server or Path(os.environ.get("LUMIN_MCP_SERVER", str(DEFAULT_SERVER)))
        source_root = str(ROOT / "src")
        pythonpath = os.environ.get("PYTHONPATH", "")
        defaults = {
            "PYTHONPATH": source_root + (os.pathsep + pythonpath if pythonpath else ""),
            "PYTHONUTF8": "1",
            "LUMIN_LOCAL_RELEASE_ROOT": str(DEFAULT_RELEASE_ROOT),
            "LUMIN_LOCAL_STATE_ROOT": str(DEFAULT_STATE_ROOT),
            "LUMIN_LOCAL_CONFIG": str(DEFAULT_CONFIG),
            "LUMIN_SUBSTRATE": "Codex/GPT",
        }
        self.env = {**os.environ, **defaults, **(dict(env or {}))}

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

    def _prepared_turn(self, turn_id: str) -> dict[str, Any] | None:
        for entry in reversed(self._entries()):
            if entry.get("status") == "prepared" and entry.get("turn_id") == turn_id:
                return entry
        return None

    def prepare(self, prompt: str, *, turn_id: str | None = None, limit: int = 30, intent: str = "context_retrieval") -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be non-empty")
        turn_id = turn_id or f"codex-hook-{uuid.uuid4().hex}"
        begun = self.invoker.call("lumin_begin_turn", {
            "prompt": prompt,
            "source_event_id": None,
            "frontier_session_id": None,
        })
        entry = {
            "status": "prepared",
            "turn_id": turn_id,
            "prompt": prompt,
            "intent": intent,
            "prepared_at": _now(),
            "dataquad_turn_id": begun["turn_id"],
            "correlation_id": begun["correlation_id"],
            "prepared_context": begun.get("dataquad_context"),
        }
        self._append(entry)
        return entry

    def record(self, prompt: str, response_text: str, *, turn_id: str, intent: str = "context_retrieval") -> dict[str, Any]:
        if not prompt.strip() or not response_text.strip() or not turn_id.strip():
            raise ValueError("prompt, response_text, and turn_id must be non-empty")
        fingerprint = turn_fingerprint(prompt, response_text, turn_id)
        for entry in self._entries():
            if entry.get("status") == "recorded" and entry.get("fingerprint") == fingerprint:
                return {**entry, "duplicate": True}
        pending = {
            "status": "recording_pending",
            "turn_id": turn_id,
            "prompt": prompt,
            "response_text": response_text,
            "fingerprint": fingerprint,
            "recording_started_at": _now(),
        }
        self._append(pending)
        try:
            prepared = self._prepared_turn(turn_id) or self.prepare(prompt, turn_id=turn_id, intent=intent)
            pending = {
                **pending,
                "dataquad_turn_id": prepared["dataquad_turn_id"],
                "correlation_id": prepared["correlation_id"],
            }
            receipt = self.invoker.call("lumin_commit_turn", {
                "correlation_id": prepared["correlation_id"],
                "turn_id": prepared["dataquad_turn_id"],
                "prompt": prompt,
                "response_text": response_text,
                "appends": default_appends(
                    prompt=prompt,
                    response_text=response_text,
                    host_turn_id=turn_id,
                    fingerprint=fingerprint,
                    intent=intent,
                ),
                "source_event_id": None,
                "frontier_session_id": None,
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


def default_appends(
    *,
    prompt: str,
    response_text: str,
    host_turn_id: str,
    fingerprint: str,
    intent: str,
) -> list[dict[str, object]]:
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest().upper()
    response_hash = hashlib.sha256(response_text.encode("utf-8")).hexdigest().upper()
    return [
        {"tensor": "PEER", "payload": {
            "kind": "codex_turn_presence",
            "identity_assertion": "none",
            "present_state": "careful continuity work under local Lumin recording",
            "prompt_sha256": prompt_hash,
            "response_sha256": response_hash,
        }},
        {"tensor": "PCT", "payload": {
            "kind": "codex_turn_record",
            "host_turn_id": host_turn_id,
            "intent": intent,
            "prompt": prompt,
            "response_chars": len(response_text),
        }},
        {"tensor": "NCT", "payload": {
            "kind": "codex_recording_continuity",
            "summary": "Codex interaction recorded through local Lumin begin/commit adapter.",
        }},
        {"tensor": "SPINE", "payload": {
            "kind": "codex_hook_provenance",
            "adapter": "scripts/lumin_codex_turn_hook.py",
            "fingerprint": fingerprint,
            "transport": "codex_mcp_stdio_local",
            "defines_identity": False,
        }},
    ]


if __name__ == "__main__":
    raise SystemExit(main())
