"""Substrate-agnostic MCP stdio gateway for the governed Pod Portal.

The gateway is deliberately a protocol translator. It has no DataQuad or RLS
reader and receives its Portal credential from the process environment, never
from MCP tool arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.client import HTTPConnection, HTTPSConnection
from typing import Any
from urllib.parse import urlparse


MAX_QUERY_LENGTH = 4096
TOOLS = (
    {
        "name": "pod_retrieve_context",
        "description": "Retrieve bounded, hash-verified continuity observations. No admission or mutation occurs.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "maxLength": MAX_QUERY_LENGTH}, "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}}, "additionalProperties": False},
    },
    {
        "name": "pod_retrieve_canon",
        "description": "Retrieve bounded Canon continuity through the Pod Portal.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "maxLength": MAX_QUERY_LENGTH}, "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}}, "additionalProperties": False},
    },
    {
        "name": "pod_query_continuity",
        "description": "Retrieve observed continuity only. Admitted continuity is unavailable.",
        "inputSchema": {"type": "object", "required": ["scope"], "properties": {"query": {"type": "string", "maxLength": MAX_QUERY_LENGTH}, "scope": {"type": "string", "const": "observed"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}}, "additionalProperties": False},
    },
    {
        "name": "pod_request_reflection",
        "description": "Retrieve bounded reflection observations from immutable RLS replay only.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "maxLength": MAX_QUERY_LENGTH}, "mode": {"type": "string", "const": "replay_only", "default": "replay_only"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5}}, "additionalProperties": False},
    },
    {
        "name": "pod_get_status",
        "description": "Return the Portal operating state and authorized read/replay capability surface.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
)


class PortalClient:
    def __init__(self, portal_url: str, portal_token: str, timeout: float = 10.0) -> None:
        parsed = urlparse(portal_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("portal URL will be an http(s) URL")
        self.base = portal_url.rstrip("/")
        self.parsed = parsed
        self.token = portal_token
        self.timeout = timeout

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        connection_class = HTTPSConnection if self.parsed.scheme == "https" else HTTPConnection
        connection = connection_class(self.parsed.hostname, self.parsed.port, timeout=self.timeout)
        try:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            connection.request("POST", self.parsed.path.rstrip("/") + path, body=body, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
            response = connection.getresponse()
            value = json.loads(response.read())
            if response.status >= 400:
                raise RuntimeError(value.get("reason", f"Portal HTTP {response.status}"))
            return value
        finally:
            connection.close()

    def health(self) -> dict[str, Any]:
        connection_class = HTTPSConnection if self.parsed.scheme == "https" else HTTPConnection
        connection = connection_class(self.parsed.hostname, self.parsed.port, timeout=self.timeout)
        try:
            connection.request("GET", self.parsed.path.rstrip("/") + "/health")
            return json.loads(connection.getresponse().read())
        finally:
            connection.close()


class McpGateway:
    def __init__(self, portal: PortalClient) -> None:
        self.portal = portal

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise ValueError("tool arguments will be an object")
        if name == "pod_get_status":
            if arguments:
                raise ValueError("pod_get_status accepts no arguments")
            health = self.portal.health()
            return {"pod_id": "adam-one", "portal_mode": "read-replay", "portal_health": health, "capabilities": ["retrieve_context", "retrieve_canon", "query_continuity:observed", "request_reflection:replay_only"], "record_experience": False, "admission": False, "dataquad_writeback": False}
        mapping = {"pod_retrieve_context": "retrieve_context", "pod_retrieve_canon": "retrieve_canon", "pod_query_continuity": "query_continuity", "pod_request_reflection": "request_reflection"}
        if name not in mapping:
            raise ValueError(f"unknown tool: {name}")
        allowed = {"query", "limit"}
        request: dict[str, Any] = {"method": mapping[name], "query": arguments.get("query", ""), "limit": arguments.get("limit", 10), "caller": "frontier_gateway"}
        if name == "pod_query_continuity":
            allowed.add("scope")
            if arguments.get("scope") != "observed":
                raise ValueError("scope will be observed")
            request["continuity_scope"] = "observed"
        elif name == "pod_request_reflection":
            allowed.add("mode")
            if arguments.get("mode", "replay_only") != "replay_only":
                raise ValueError("mode will be replay_only")
            request["reflection_mode"] = "replay_only"
        unknown = set(arguments) - allowed
        if unknown:
            raise ValueError(f"unknown tool arguments: {sorted(unknown)}")
        return self.portal.post("/v1/portal/execute", request)

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        message_id = message.get("id")
        if message_id is None:
            return None
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": message_id, "result": {"protocolVersion": "2025-11-25", "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "aegis-pod-mcp-gateway", "version": "0.1.0"}}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": message_id, "result": {"tools": list(TOOLS)}}
        if method == "tools/call":
            params = message.get("params", {})
            try:
                value = self.call_tool(str(params.get("name", "")), params.get("arguments", {}))
                return {"jsonrpc": "2.0", "id": message_id, "result": {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}], "structuredContent": value}}
            except Exception as exc:
                return {"jsonrpc": "2.0", "id": message_id, "result": {"isError": True, "content": [{"type": "text", "text": str(exc)}]}}
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the substrate-agnostic AEGIS Pod MCP Gateway.")
    parser.add_argument("--portal-url", default=os.environ.get("AEGIS_PORTAL_URL", "http://127.0.0.1:8092"))
    parser.add_argument("--portal-token", default=os.environ.get("AEGIS_PORTAL_TOKEN"))
    args = parser.parse_args()
    if not args.portal_token:
        raise SystemExit("AEGIS_PORTAL_TOKEN or --portal-token is required")
    gateway = McpGateway(PortalClient(args.portal_url, args.portal_token))
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = gateway.handle(json.loads(line))
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(exc)}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
