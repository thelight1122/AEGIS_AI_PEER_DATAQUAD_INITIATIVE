"""P1 — the Lumin GPT Action Orb origin service.

Serves the five read/replay endpoints of contracts/p1-lumin-gpt-action.openapi.json and
forwards them to the loopback Portal. Runs on the Pod host so the Portal credential is read
locally and never travels, exactly as run_private_mcp_gateway.sh does.

    Lumin Custom GPT -> Cloudflare -> cloudflared -> SSH tunnel
        -> this service (127.0.0.1) -> Portal (127.0.0.1:8092) -> DataQuad

Posture
-------
Binds loopback only. Read and replay only. `POST /api/live-bridge/events` is answered 410
Gone with the reason stated, because a retired endpoint and an absent one are
indistinguishable to a caller unless the retirement is declared. Nothing here can write,
admit, or create experience; the Portal enforces that independently and this service never
asks it to.

ADR-0007
--------
The Portal declares `live_source: false` and serves an immutable copy. Every response from
this service carries `aegis_source_authority` saying so, so no consumer can represent this
connection as live DataQuad access.

Usage:
    AEGIS_PORTAL_TOKEN=... python3 lumin_action_origin.py [--port 8790]
    or let it read the token file directly, as the MCP gateway does.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

TOKEN_FILE = Path("/home/aegisadmin/.config/aegis/portal-gateway.token")
PORTAL_URL = os.environ.get("AEGIS_PORTAL_URL", "http://127.0.0.1:8092")
CALLER = "lumin_gpt_action_orb"

#: Action operationId -> (path, Portal method, extra request fields)
ROUTES: dict[str, dict[str, Any]] = {
    "/api/pod/status":     {"operation": "getPodStatus",      "method": None,                 "http": "GET"},
    "/api/pod/context":    {"operation": "retrieveContext",   "method": "retrieve_context",   "http": "POST"},
    "/api/pod/canon":      {"operation": "retrieveCanon",     "method": "retrieve_canon",     "http": "POST"},
    "/api/pod/continuity": {"operation": "queryContinuity",   "method": "query_continuity",   "http": "POST",
                            "extra": {"continuity_scope": "observed"}},
    "/api/pod/reflection": {"operation": "requestReflection", "method": "request_reflection", "http": "POST",
                            "extra": {"reflection_mode": "replay_only"}},
}

#: Retired in P1. Answered explicitly rather than 404, so the retirement is legible.
RETIRED: dict[str, dict[str, str]] = {
    "/api/live-bridge/events": {
        "operationId": "appendEvent",
        "retired_in": "P1",
        "reason": (
            "Writing is incompatible with the read and replay only posture. Experience "
            "admission is a separate authorized process and is not reachable from a GPT "
            "Action Orb."
        ),
    }
}

SOURCE_AUTHORITY = {
    "live_source": False,
    "source_mode": "immutable_copy",
    "establishes_live_continuity": False,
    "note": (
        "This Action reaches a Portal serving an immutable copy. It exercises transport and "
        "retrieval. It does not establish live DataQuad access, live continuity, experience "
        "formation, or ethical formation. See ADR-0007."
    ),
}

BOUNDARIES = {
    "mutation": False,
    "admission": False,
    "experience_created": False,
    "dataquad_writeback": False,
    "live_rls_invoked": False,
    "shell": False,
    "filesystem": False,
}


def read_token() -> str:
    token = os.environ.get("AEGIS_PORTAL_TOKEN")
    if token:
        return token.strip()
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no Portal credential: set AEGIS_PORTAL_TOKEN or provide {TOKEN_FILE}")


class Portal:
    def __init__(self, url: str, token: str, timeout: float = 15.0) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise SystemExit("the Portal URL will be loopback http; this service does not reach off-host")
        self.parsed = parsed
        self.token = token
        self.timeout = timeout

    def _connect(self) -> HTTPConnection:
        return HTTPConnection(self.parsed.hostname, self.parsed.port, timeout=self.timeout)

    def health(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            connection.request("GET", "/health")
            return json.loads(connection.getresponse().read())
        finally:
            connection.close()

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connect()
        try:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            connection.request(
                "POST",
                "/v1/portal/execute",
                body=body,
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            )
            response = connection.getresponse()
            value = json.loads(response.read())
            if response.status >= 400:
                raise RuntimeError(value.get("reason", f"Portal HTTP {response.status}"))
            return value
        finally:
            connection.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "aegis-lumin-action-orb/1.0"
    portal: Portal = None  # type: ignore[assignment]

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    # --- helpers ---------------------------------------------------------------------

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        payload = dict(payload)
        payload.setdefault("aegis_source_authority", SOURCE_AUTHORITY)
        payload.setdefault("aegis_boundaries", BOUNDARIES)
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-AEGIS-Posture", "read-replay-only")
        self.send_header("X-AEGIS-Live-Source", "false")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"request body is not valid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError("request body will be a JSON object")
        return value

    def _retired(self, path: str) -> bool:
        entry = RETIRED.get(path)
        if entry is None:
            return False
        self._send(410, {
            "error": "operation_retired",
            "operationId": entry["operationId"],
            "retired_in": entry["retired_in"],
            "reason": entry["reason"],
            "replacement": None,
        })
        return True

    # --- verbs -----------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if self._retired(path):
            return
        if path == "/openapi.json":
            contract = Path(__file__).with_name("p1-lumin-gpt-action.openapi.json")
            if not contract.exists():
                self._send(500, {"error": "schema_missing", "reason": str(contract)})
                return
            self._send(200, json.loads(contract.read_text(encoding="utf-8")))
            return
        if path == "/api/pod/status":
            self._status()
            return
        if path in ROUTES:
            self._send(405, {"error": "method_not_allowed", "expected": ROUTES[path]["http"]})
            return
        self._send(404, {"error": "not_found", "path": path, "available": sorted(ROUTES)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if self._retired(path):
            return
        route = ROUTES.get(path)
        if route is None:
            self._send(404, {"error": "not_found", "path": path, "available": sorted(ROUTES)})
            return
        if route["http"] != "POST":
            self._send(405, {"error": "method_not_allowed", "expected": route["http"]})
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send(400, {"error": "bad_request", "reason": str(exc)})
            return

        allowed = {"query", "limit"}
        unknown = set(payload) - allowed
        if unknown:
            self._send(400, {"error": "unknown_parameters", "unknown": sorted(unknown), "allowed": sorted(allowed)})
            return

        limit = payload.get("limit", 10)
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            self._send(400, {"error": "bad_request", "reason": "limit will be an integer from 1 to 100"})
            return
        query = payload.get("query", "")
        if not isinstance(query, str) or len(query) > 4096:
            self._send(400, {"error": "bad_request", "reason": "query will be a string of at most 4096 characters"})
            return

        request = {"method": route["method"], "query": query, "limit": limit, "caller": CALLER}
        request.update(route.get("extra", {}))
        try:
            result = self.portal.execute(request)
        except Exception as exc:  # Portal refusal or transport failure
            self._send(502, {"error": "portal_error", "operation": route["operation"], "reason": str(exc)})
            return
        self._send(200, {"operation": route["operation"], "result": result})

    def _any_other(self) -> None:
        self._send(405, {"error": "method_not_allowed", "reason": "this Action is read and replay only"})

    do_PUT = do_PATCH = do_DELETE = _any_other  # type: ignore[assignment]

    def _status(self) -> None:
        try:
            health = self.portal.health()
        except Exception as exc:
            self._send(502, {"error": "portal_unreachable", "reason": str(exc)})
            return
        self._send(200, {
            "operation": "getPodStatus",
            "pod_id": "adam-one",
            "portal_mode": "read-replay",
            "portal_health": health,
            "capabilities": ["retrieveContext", "retrieveCanon", "queryContinuity", "requestReflection", "getPodStatus"],
            "retired_operations": {name: dict(entry) for name, entry in RETIRED.items()},
            "record_experience": False,
            "admission": False,
            "dataquad_writeback": False,
        })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("this service binds loopback only; exposure is the tunnel's job, not the service's")

    Handler.portal = Portal(PORTAL_URL, read_token())
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    sys.stderr.write(
        f"lumin action orb origin on http://{args.host}:{args.port} -> Portal {PORTAL_URL}\n"
        f"read/replay only; appendEvent retired; live_source false\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
