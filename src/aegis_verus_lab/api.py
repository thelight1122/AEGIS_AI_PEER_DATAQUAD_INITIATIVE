"""Loopback Bridge surface for the Verus LAB runtime."""

from __future__ import annotations

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import urlparse

from .frontier import (
    FrontierAuthenticationError,
    FrontierProtocolError,
    FrontierRateLimitError,
    FrontierUnavailableError,
    SecretLoader,
)
from .runtime import VerusLabRuntime


MAX_BODY_BYTES = 1_048_576


def make_handler(runtime: VerusLabRuntime, bridge_secret_loader: SecretLoader) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "AEGISVerusLab/1.0"

        def _send(self, status: int, body: Any) -> None:
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(encoded)

        def _path(self) -> str:
            return urlparse(self.path).path

        def _authorized(self) -> bool:
            expected = bridge_secret_loader.load()
            supplied = self.headers.get("Authorization", "")
            return supplied.startswith("Bearer ") and hmac.compare_digest(supplied[7:], expected)

        def _body(self) -> dict[str, Any]:
            raw = self.headers.get("Content-Length")
            if raw is None:
                raise ValueError("Content-Length is required")
            size = int(raw)
            if size < 0 or size > MAX_BODY_BYTES:
                raise ValueError("request body exceeds limit")
            value = json.loads(self.rfile.read(size) or b"{}")
            if not isinstance(value, dict):
                raise ValueError("request body must be an object")
            return value

        def do_GET(self) -> None:  # noqa: N802
            if self._path() == "/health":
                try:
                    coherence = runtime.coherence()
                    coherent = coherence["coherent"] is True
                    public_coherence = {
                        "coherent": coherent,
                        "committed_turns": coherence["committed_turns"],
                        "temporal_records": coherence["temporal_records"],
                        "processor_records": coherence["processor_records"],
                        "rls_records": coherence["rls_records"],
                        "missing_temporal_count": len(coherence["missing_temporal"]),
                        "missing_processor_count": len(coherence["missing_processor"]),
                        "missing_rls_count": len(coherence["missing_rls"]),
                        "mismatch_count": len(coherence["mismatches"]),
                        "orphan_count": sum(len(coherence[key]) for key in
                                            ("orphan_temporal", "orphan_processor", "orphan_rls")),
                    }
                    self._send(200 if coherent else 503, {
                        "status": "ok" if coherent else "shortfall",
                        "mode": "LAB_RUNNING",
                        "ready": coherent,
                        "cyberpeer_name": "Verus",
                        "dataquad_id": "verus",
                        "full_append_only": True,
                        "writable_tensors": ["PEER", "PCT", "NCT", "SPINE"],
                        "integrity": coherence["dataquad"],
                        "coherence": public_coherence,
                    })
                except Exception:
                    self._send(503, {"status": "shortfall", "ready": False,
                                     "error": "runtime_coherence_unavailable"})
                return
            if self._path() == "/status":
                try:
                    authorized = self._authorized()
                except Exception:
                    self._send(503, {"error": "bridge_authentication_unavailable"})
                    return
                if not authorized:
                    self._send(401, {"error": "bridge_authentication_required"})
                    return
                try:
                    self._send(200, runtime.coherence())
                except Exception:
                    self._send(503, {"error": "runtime_coherence_unavailable"})
                return
            self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            if self._path() != "/v1/turn":
                self._send(404, {"error": "not_found"})
                return
            try:
                if not self._authorized():
                    self._send(401, {"error": "bridge_authentication_required"})
                    return
                if self.headers.get("X-AEGIS-CyberPeer-Name") != "Verus":
                    self._send(403, {"error": "cyberpeer_name_binding_mismatch"})
                    return
                body = self._body()
                turn_id = self.headers.get("Idempotency-Key", "")
                result = runtime.execute_turn(
                    turn_id=turn_id,
                    source_event_id=str(body.get("source_event_id", "")),
                    frontier_session_id=str(body.get("frontier_session_id", "")),
                    prompt=str(body.get("prompt", "")),
                )
                self._send(201 if result["created"] else 200, result)
            except FrontierAuthenticationError:
                self._send(503, {"error": "frontier_authentication_unavailable"})
            except FrontierRateLimitError:
                self._send(429, {"error": "frontier_rate_limited"})
            except FrontierUnavailableError:
                self._send(503, {"error": "frontier_unavailable"})
            except FrontierProtocolError:
                self._send(502, {"error": "frontier_response_invalid"})
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                self._send(400, {"error": "invalid_request"})
            except Exception:
                self._send(500, {"error": "internal_shortfall"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def serve(
    runtime: VerusLabRuntime,
    bridge_secret_loader: SecretLoader,
    *,
    host: str = "127.0.0.1",
    port: int = 8791,
) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Verus LAB Bridge may bind only to localhost")
    ThreadingHTTPServer((host, port), make_handler(runtime, bridge_secret_loader)).serve_forever()
