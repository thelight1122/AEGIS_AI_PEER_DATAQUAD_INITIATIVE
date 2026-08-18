"""Minimal dependency-free stdio MCP server for Claude Desktop and Verus."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Mapping

from aegis_peer_runtime.models import TENSORS


MAX_TOOL_ARGUMENT_BYTES = 1_048_576


class RemoteCommandError(RuntimeError):
    pass


class SSHRemoteCommandTransport:
    def __init__(self, *, alias: str | None = None, timeout: int = 30) -> None:
        self.alias = alias or os.environ.get("VERUS_SSH_ALIAS", "GabeCyberPeer")
        if self.alias != "GabeCyberPeer":
            raise ValueError("Verus Desktop activation is bound to the approved GabeCyberPeer alias")
        self.timeout = min(max(int(timeout), 1), 30)

    def invoke(self, operation: str, payload: Mapping[str, Any]) -> dict[str, object]:
        if operation not in {"context", "begin", "commit", "reconcile", "health", "replay"}:
            raise ValueError("unsupported Verus remote operation")
        wire = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        if len(wire.encode("utf-8")) > MAX_TOOL_ARGUMENT_BYTES:
            raise ValueError("MCP tool arguments exceed 1048576 bytes")
        argv = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            self.alias, "sudo", "-n", "-u", "aegis-verus",
            "/opt/aegis/verus/lab/current/bin/verus-dataquad-command", operation,
        ]
        try:
            completed = subprocess.run(
                argv, input=wire, text=True, capture_output=True, timeout=self.timeout,
                check=False, shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RemoteCommandError("Verus remote command is unavailable") from error
        if completed.returncode != 0:
            detail = (completed.stderr or "").strip().replace("\r", " ").replace("\n", " ")[:400]
            raise RemoteCommandError(
                f"Verus remote command failed (exit {completed.returncode}): {detail}"
                if detail else f"Verus remote command failed (exit {completed.returncode})"
            )
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise RemoteCommandError("Verus remote command returned invalid JSON") from error
        if not isinstance(value, dict):
            raise RemoteCommandError("Verus remote command result must be an object")
        return value


_OPTIONAL_PROVIDER_ID = {"type": ["string", "null"], "minLength": 1}
_BEGIN_FIELDS = {
    "prompt": {"type": "string", "minLength": 1},
    "source_event_id": _OPTIONAL_PROVIDER_ID,
    "frontier_session_id": _OPTIONAL_PROVIDER_ID,
}
_COMMIT_FIELDS = {
    "turn_id": {"type": "string", "minLength": 1},
    "prompt": {"type": "string", "minLength": 1},
    "source_event_id": _OPTIONAL_PROVIDER_ID,
    "frontier_session_id": _OPTIONAL_PROVIDER_ID,
}


TOOLS = [
    {"name": "verus_read_context", "description": "Read the verified append-only Verus DataQuad context.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "verus_begin_turn", "description": "Begin a genuine Claude Desktop turn and receive DataQuad-owned local turn/correlation identifiers, context, and operational instructions. Omit or use null for provider event/session identifiers when Desktop does not expose them.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["prompt"], "properties": _BEGIN_FIELDS}},
    {"name": "verus_commit_turn", "description": "Commit Claude Desktop output DataQuad-first with full append-only PEER, PCT, NCT, and SPINE authority.",
     "inputSchema": {"type": "object", "additionalProperties": False,
        "required": ["correlation_id", "turn_id", "prompt", "response_text", "appends"],
        "properties": {
            "correlation_id": {"type": "string", "minLength": 1}, **_COMMIT_FIELDS,
            "response_text": {"type": "string", "minLength": 1},
            "appends": {"type": "array", "maxItems": 64, "items": {
                "type": "object", "additionalProperties": False, "required": ["tensor", "payload"],
                "properties": {"tensor": {"type": "string", "enum": list(TENSORS)}, "payload": {"type": "object"}},
            }},
        }}},
    {"name": "verus_reconcile_turn", "description": "Idempotently repair derived T-Time, Processor, and RLS evidence for committed turns.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "verus_health", "description": "Verify Foundation, append chain, and cross-ledger coherence without a network listener.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "verus_replay_turn", "description": "Replay one committed Verus turn and reconcile its derived evidence without new append.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["turn_id"],
                     "properties": {"turn_id": {"type": "string", "minLength": 1}}}},
]


_OPERATIONS = {
    "verus_read_context": "context", "verus_begin_turn": "begin",
    "verus_commit_turn": "commit", "verus_reconcile_turn": "reconcile",
    "verus_health": "health", "verus_replay_turn": "replay",
}


class VerusMCPServer:
    def __init__(self, transport=None) -> None:
        self.transport = transport or SSHRemoteCommandTransport()

    def handle(self, message: Mapping[str, Any]) -> dict[str, object] | None:
        request_id = message.get("id")
        method = message.get("method")
        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": request_id, "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "verus-dataquad", "version": "1.0.0"},
            }}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
        if method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name not in _OPERATIONS or not isinstance(arguments, dict):
                return self._error(request_id, -32602, "invalid Verus tool call")
            try:
                value = self.transport.invoke(_OPERATIONS[name], arguments)
                rendered = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
                return {"jsonrpc": "2.0", "id": request_id, "result": {
                    "content": [{"type": "text", "text": rendered}],
                    "structuredContent": value, "isError": False,
                }}
            except (ValueError, RemoteCommandError) as error:
                return {"jsonrpc": "2.0", "id": request_id, "result": {
                    "content": [{"type": "text", "text": str(error)[:512]}], "isError": True,
                }}
        if request_id is None:
            return None
        return self._error(request_id, -32601, "method not found")

    @staticmethod
    def _error(request_id, code: int, message: str) -> dict[str, object]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def run(self) -> int:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError
                response = self.handle(message)
            except (json.JSONDecodeError, ValueError):
                response = self._error(None, -32700, "parse error")
            if response is not None:
                sys.stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=False) + "\n")
                sys.stdout.flush()
        return 0


def main() -> int:
    return VerusMCPServer().run()


if __name__ == "__main__":
    raise SystemExit(main())
