"""Localhost HTTP API for peer health, reads, seating state, and scoped appends."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .models import PeerState, Record, ValidationError
from .storage import IdempotencyConflict, RuntimeStore, UnseatedError

MAX_BODY_BYTES = 1_048_576


def make_handler(runtime: RuntimeStore) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AEGISPeerRuntime/0.1"

        def _send(self, status: int, body: Any) -> None:
            data = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _parts(self) -> list[str]:
            return [part for part in urlparse(self.path).path.split("/") if part]

        def _bound_peer(self, parts: list[str]) -> str:
            if len(parts) < 3 or parts[:2] != ["v1", "peers"]:
                raise ValidationError("unknown route")
            peer = parts[2]
            runtime.peer(peer)
            binding = self.headers.get("X-AEGIS-Peer")
            if binding != peer:
                raise ValidationError("X-AEGIS-Peer must exactly match the route peer")
            return peer

        def _body(self) -> dict[str, Any]:
            raw_size = self.headers.get("Content-Length")
            if raw_size is None:
                raise ValidationError("Content-Length is required")
            size = int(raw_size)
            if size < 0 or size > MAX_BODY_BYTES:
                raise ValidationError("request body exceeds limit")
            value = json.loads(self.rfile.read(size) or b"{}")
            if not isinstance(value, dict):
                raise ValidationError("request body must be an object")
            return value

        def do_GET(self) -> None:  # noqa: N802
            try:
                parts = self._parts()
                if parts == ["health"]:
                    self._send(200, runtime.health())
                    return
                peer = self._bound_peer(parts)
                if parts[3:] == ["health"]:
                    store = runtime.peer(peer)
                    self._send(200, {"peer": peer, "state": store.state.value, "records": len(store.read())})
                elif parts[3:] == ["records"]:
                    self._send(200, {"peer": peer, "records": runtime.peer(peer).read()})
                else:
                    self._send(404, {"error": "not_found"})
            except (ValidationError, IndexError) as error:
                self._send(403, {"error": str(error)})

        def do_POST(self) -> None:  # noqa: N802
            try:
                parts = self._parts()
                peer = self._bound_peer(parts)
                if parts[3:] == ["state"]:
                    self._send(405, {"error": "state transitions are not exposed over HTTP"})
                    return
                body = self._body()
                if parts[3:] != ["records"]:
                    self._send(404, {"error": "not_found"})
                    return
                entry, created = runtime.peer(peer).append(Record(
                    peer=peer,
                    tensor=body.get("tensor", ""),
                    actor=body.get("actor", ""),
                    idempotency_key=self.headers.get("Idempotency-Key", ""),
                    payload=body.get("payload", {}),
                ))
                self._send(201 if created else 200, {"created": created, "record": entry})
            except UnseatedError as error:
                self._send(409, {"error": str(error)})
            except IdempotencyConflict as error:
                self._send(409, {"error": str(error)})
            except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                self._send(400, {"error": str(error)})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(runtime: RuntimeStore, host: str = "127.0.0.1", port: int = 8787) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("core runtime API may bind only to localhost")
    ThreadingHTTPServer((host, port), make_handler(runtime)).serve_forever()
