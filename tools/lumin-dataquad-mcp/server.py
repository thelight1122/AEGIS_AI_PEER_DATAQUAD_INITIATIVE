"""Minimal dependency-free stdio MCP server for Codex/GPT and Codex."""

from __future__ import annotations

import itertools
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
        self.alias = alias or os.environ.get("LUMIN_SSH_ALIAS", "GabeCyberPeer")
        if self.alias != "GabeCyberPeer":
            raise ValueError("Lumin Desktop activation is bound to the approved GabeCyberPeer alias")
        self.timeout = min(max(int(timeout), 1), 30)

    def invoke(self, operation: str, payload: Mapping[str, Any]) -> dict[str, object]:
        if operation not in {"context", "begin", "commit", "reconcile", "health", "replay", "query", "query_and_record"}:
            raise ValueError("unsupported Lumin remote operation")
        wire = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        if len(wire.encode("utf-8")) > MAX_TOOL_ARGUMENT_BYTES:
            raise ValueError("MCP tool arguments exceed 1048576 bytes")
        argv = [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            self.alias, "sudo", "-n", "-u", "aegis-lumin",
            "/opt/aegis/lumin/lab/current/bin/lumin-dataquad-command", operation,
        ]
        try:
            completed = subprocess.run(
                argv, input=wire, text=True, capture_output=True, timeout=self.timeout,
                check=False, shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RemoteCommandError("Lumin remote command is unavailable") from error
        if completed.returncode != 0:
            detail = (completed.stderr or "").strip().replace("\r", " ").replace("\n", " ")[:400]
            raise RemoteCommandError(
                f"Lumin remote command failed (exit {completed.returncode}): {detail}"
                if detail else f"Lumin remote command failed (exit {completed.returncode})"
            )
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise RemoteCommandError("Lumin remote command returned invalid JSON") from error
        if not isinstance(value, dict):
            raise RemoteCommandError("Lumin remote command result must be an object")
        return value


_SUBSTRATE = os.environ.get("LUMIN_SUBSTRATE", "Codex/GPT")

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
_QUERY_RECORD_FIELDS = {
    "prompt": {"type": "string", "minLength": 1},
    "response_text": {"type": "string", "minLength": 1},
    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
    "intent": {"type": "string", "minLength": 1},
    "source_event_id": _OPTIONAL_PROVIDER_ID,
    "frontier_session_id": _OPTIONAL_PROVIDER_ID,
}


TOOLS = [
    {"name": "lumin_read_context", "description": "Read the verified append-only Lumin DataQuad context.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "lumin_begin_turn", "description": "Begin a genuine turn and receive DataQuad-owned local turn/correlation identifiers, context, and operational instructions. Omit or use null for provider event/session identifiers when the substrate does not expose them.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["prompt"], "properties": _BEGIN_FIELDS}},
    {"name": "lumin_commit_turn", "description": "Commit output DataQuad-first with full append-only PEER, PCT, NCT, and SPINE authority.",
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
    {"name": "lumin_reconcile_turn", "description": "Idempotently repair derived T-Time, Processor, and RLS evidence for committed turns.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "lumin_health", "description": "Verify Foundation, append chain, and cross-ledger coherence without a network listener.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}}},
    {"name": "lumin_replay_turn", "description": "Replay one committed Lumin turn and reconcile its derived evidence without new append.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["turn_id"],
                     "properties": {"turn_id": {"type": "string", "minLength": 1}}}},
    {"name": "lumin_query", "description": "Query the DataQuad through the Advocate-Steward-Processor custodian pipeline. Returns curated, scored results rather than raw tensor dumps.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["prompt"],
                     "properties": {
                         "prompt": {"type": "string", "minLength": 1},
                         "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                         "intent": {"type": "string", "minLength": 1},
                     }}},
    {"name": "lumin_query_and_record", "description": "Run a custodian query, then append the supplied assistant response and query-context provenance to the append-only DataQuad. The response is required because an MCP server cannot observe host assistant output after a tool call returns.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["prompt", "response_text"],
                     "properties": _QUERY_RECORD_FIELDS}},
]


_OPERATIONS = {
    "lumin_read_context": "context", "lumin_begin_turn": "begin",
    "lumin_commit_turn": "commit", "lumin_reconcile_turn": "reconcile",
    "lumin_health": "health", "lumin_replay_turn": "replay",
    "lumin_query": "query", "lumin_query_and_record": "query_and_record",
}


def _read_content_length_message(stream) -> dict[str, Any] | None:
    """Read a Content-Length framed JSON-RPC message from a binary stream."""
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        decoded = line.decode("utf-8") if isinstance(line, bytes) else line
        decoded = decoded.strip()
        if not decoded:
            if headers:
                break
            continue
        if ":" in decoded:
            key, _, value = decoded.partition(":")
            headers[key.strip().lower()] = value.strip()
    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None
    body = stream.read(content_length)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return json.loads(body)


def _write_content_length_message(stream, response: dict[str, object]) -> None:
    """Write a Content-Length framed JSON-RPC message to a binary stream."""
    body = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    stream.write(header)
    stream.write(body)
    stream.flush()


class LuminMCPServer:
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
                "serverInfo": {"name": "lumin-dataquad", "version": "1.1.0"},
            }}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
        if method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name not in _OPERATIONS or not isinstance(arguments, dict):
                return self._error(request_id, -32602, "invalid Lumin tool call")
            arguments = dict(arguments)
            arguments.setdefault("_substrate", _SUBSTRATE)
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
        bin_in = sys.stdin.buffer
        first_line = bin_in.readline()
        if not first_line:
            return 0
        decoded = first_line.decode("utf-8", errors="replace").strip()
        if decoded.lower().startswith("content-length"):
            return self._run_content_length(bin_in, first_line)
        return self._run_line_delimited(first_line.decode("utf-8", errors="replace"))

    def _run_content_length(self, bin_in, first_header_line: bytes) -> int:
        """Content-Length framed transport (Codex). All binary I/O."""
        bin_out = sys.stdout.buffer
        first_message = self._finish_content_length_read(bin_in, first_header_line)
        if first_message is not None:
            response = self._dispatch(first_message)
            if response is not None:
                _write_content_length_message(bin_out, response)
        while True:
            try:
                message = _read_content_length_message(bin_in)
                if message is None:
                    break
                response = self._dispatch(message)
            except (json.JSONDecodeError, ValueError):
                response = self._error(None, -32700, "parse error")
            if response is not None:
                _write_content_length_message(bin_out, response)
        return 0

    def _finish_content_length_read(self, bin_in, first_header_line: bytes) -> dict[str, Any] | None:
        """Complete reading a Content-Length message given the first header line already consumed."""
        headers: dict[str, str] = {}
        decoded = first_header_line.decode("utf-8", errors="replace").strip()
        if ":" in decoded:
            key, _, value = decoded.partition(":")
            headers[key.strip().lower()] = value.strip()
        while True:
            line = bin_in.readline()
            if not line:
                return None
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                break
            if ":" in text:
                key, _, value = text.partition(":")
                headers[key.strip().lower()] = value.strip()
        content_length = int(headers.get("content-length", "0"))
        if content_length <= 0:
            return None
        body = bin_in.read(content_length)
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None

    def _dispatch(self, message) -> dict[str, object] | None:
        if not isinstance(message, dict):
            return self._error(None, -32700, "parse error")
        return self.handle(message)

    def _run_line_delimited(self, first_line: str) -> int:
        """Line-delimited transport (Codex/GPT)."""
        for line in itertools.chain((first_line,), sys.stdin):
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
    return LuminMCPServer().run()


if __name__ == "__main__":
    raise SystemExit(main())

