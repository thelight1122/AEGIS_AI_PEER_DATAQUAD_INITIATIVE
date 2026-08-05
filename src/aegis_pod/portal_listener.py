"""Minimum viable loopback-only Portal listener.

The loopback listener also exposes a narrowly bounded Frontier-to-Pod
continuity handshake. It never loads a model and never grants mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from .portal_contract import authorize, load_manifest
    from .capability_router import CapabilityRouter
except ImportError:  # Standalone staged file under /opt/cyberpeer-pod/portals.
    sys.path.insert(0, str(Path(__file__).resolve().parent / "phase1c"))
    from portal_contract import authorize, load_manifest
    from capability_router import CapabilityRouter


MAX_BODY_BYTES = 16 * 1024
ALLOWED_HOST = "127.0.0.1"


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def create_server(manifest_path: Path, host: str = ALLOWED_HOST, port: int = 8090, router: Any = None) -> ThreadingHTTPServer:
    if host != ALLOWED_HOST:
        raise ValueError("Phase 2 listener is loopback-only and will bind to 127.0.0.1")
    manifest = load_manifest(manifest_path)

    class PortalHandler(BaseHTTPRequestHandler):
        server_version = "CyberPeerPortalLoopback/0.1"

        def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            self._send(HTTPStatus.OK, {
                "status": "ok",
                "mode": "loopback-contract-only",
                "bound_host": ALLOWED_HOST,
                "action_execution": False,
                "dataquad_access": False,
                "frontier_connection": False,
            })

        def do_POST(self) -> None:  # noqa: N802
            if self.path not in {"/v1/portal/authorize", "/v1/portal/execute", "/v1/frontier/handshake"}:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length < 1 or content_length > MAX_BODY_BYTES:
                    raise ValueError("request body is outside bounds")
                request = json.loads(self.rfile.read(content_length))
                if not isinstance(request, dict):
                    raise ValueError("request will be a JSON object")
                token = self.headers.get("Authorization", "")
                if not token.startswith("Bearer "):
                    token_value = None
                else:
                    token_value = token[7:]
                decision = authorize(
                    manifest,
                    method=str(request.get("method", "")),
                    bearer_token=token_value,
                    limit=int(request.get("limit", 20)),
                    reflection_mode=request.get("reflection_mode"),
                    continuity_scope=request.get("continuity_scope"),
                )
                if not decision.allowed:
                    self._send(HTTPStatus.FORBIDDEN, {
                        "authorized": False,
                        "method": decision.method,
                        "reason": decision.reason,
                        "action_executed": False,
                    })
                    return
                if self.path == "/v1/portal/execute":
                    if router is None:
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {
                            "authorized": True,
                            "action_executed": False,
                            "reason": "capability router is not configured",
                        })
                        return
                    result = router.execute(
                        method=str(request.get("method", "")),
                        bearer_token=token_value,
                        query=str(request.get("query", "")),
                        limit=int(request.get("limit", 20)),
                        reflection_mode=request.get("reflection_mode"),
                        continuity_scope=request.get("continuity_scope"),
                        caller=str(request.get("caller", "portal_client")),
                    )
                    self._send(HTTPStatus.OK if result.get("authorized") else HTTPStatus.FORBIDDEN, result)
                    return
                if self.path == "/v1/frontier/handshake":
                    if router is None:
                        self._send(HTTPStatus.SERVICE_UNAVAILABLE, {
                            "authorized": True,
                            "action_executed": False,
                            "reason": "capability router is not configured",
                        })
                        return
                    if request.get("method") != "retrieve_context" or request.get("query", "") != "" or int(request.get("limit", 1)) != 1:
                        self._send(HTTPStatus.BAD_REQUEST, {
                            "authorized": False,
                            "reason": "Frontier continuity handshake is fixed to retrieve_context with empty query and limit 1",
                        })
                        return
                    result = router.execute(
                        method="retrieve_context",
                        bearer_token=token_value,
                        query="",
                        limit=1,
                        caller="frontier_substrate",
                    )
                    result["handshake"] = "frontier_to_pod_continuity"
                    result["frontier_model_loaded_on_vm"] = False
                    self._send(HTTPStatus.OK if result.get("authorized") else HTTPStatus.FORBIDDEN, result)
                    return
                self._send(HTTPStatus.OK, {
                    "authorized": True,
                    "method": decision.method,
                    "access": decision.access,
                    "scope": decision.scope,
                    "action_executed": False,
                    "execution": "not_started",
                    "evidence": {"contract_only": True, "request_recorded": False},
                })
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"authorized": False, "reason": str(exc)})

        def log_message(self, *_args: Any) -> None:
            return

    server = ThreadingHTTPServer((host, port), PortalHandler)
    server.daemon_threads = True
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the loopback-only Portal contract listener.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--host", default=ALLOWED_HOST)
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--router-context-root", type=Path)
    parser.add_argument("--router-context-hashes", type=Path)
    parser.add_argument("--router-rls-source", type=Path)
    parser.add_argument("--router-rls-hashes", type=Path)
    parser.add_argument("--router-approved-root", type=Path)
    parser.add_argument("--router-evidence-ledger", type=Path)
    args = parser.parse_args()
    router = None
    router_args = [args.router_context_root, args.router_context_hashes, args.router_rls_source, args.router_rls_hashes, args.router_approved_root]
    if any(value is not None for value in router_args):
        if not all(value is not None for value in router_args):
            raise SystemExit("all router paths are required when configuring capability execution")
        router = CapabilityRouter(
            load_manifest(args.manifest),
            context_root=args.router_context_root,
            context_hashes=args.router_context_hashes,
            rls_source=args.router_rls_source,
            rls_hashes=args.router_rls_hashes,
            approved_root=args.router_approved_root,
            evidence_ledger=args.router_evidence_ledger,
        )
    server = create_server(args.manifest, args.host, args.port, router=router)
    print(f"LISTENING {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
