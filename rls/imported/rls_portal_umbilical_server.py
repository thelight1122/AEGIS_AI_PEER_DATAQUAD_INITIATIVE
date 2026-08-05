from __future__ import annotations

import hashlib
import hmac
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HOST = "127.0.0.1"
PORT = 8093
MAX_BODY = 16 * 1024
METHODS = {
    "rls_status_read": "rls.status.read",
    "rls_timeline_read": "rls.timeline.read",
    "rls_lineage_read": "rls.lineage.read",
    "rls_reflection_replay": "rls.reflection.replay",
}


class RLSPortalUmbilical:
    def __init__(self) -> None:
        self.manifest_path = Path("/opt/cyberpeer-pod/portals/production/portal-manifest.json")
        self.packet_path = Path("/opt/cyberpeer-pod/logs/r2-rls-reflection-packet.json")
        self.report_path = Path("/opt/cyberpeer-pod/logs/r2-rls-shadow-run-report.json")
        self.umbilical = {
            "umbilical_id": "umbilical:rls-orb:portal-pod",
            "source_orb": "rls-coordinate-orb",
            "target_pod": "aegis-portal-pod",
            "allowed_scopes": sorted(set(METHODS.values())),
            "mutation_authority": False,
            "admission_authority": False,
            "experience_authority": False,
        }

    def _authenticated(self, token: str | None) -> bool:
        if not token:
            return False
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        expected = str(manifest.get("authentication", {}).get("credential_hash", ""))
        actual = hashlib.sha256(token.encode("utf-8")).hexdigest().upper()
        return hmac.compare_digest(actual, expected)

    def dispatch(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        if method not in METHODS:
            raise PermissionError("RLS capability is undeclared")
        requested_scope = payload.get("scope", METHODS[method])
        if requested_scope != METHODS[method]:
            raise PermissionError("RLS scope is not permitted by the Umbilical")
        packet = json.loads(self.packet_path.read_text(encoding="utf-8"))
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        if method == "rls_status_read":
            return {"umbilical": self.umbilical, "report": report, "boundaries": {"authoritative_tensor_write": False, "experience_created": False, "admission_performed": False}}
        coordinates = packet.get("source_coordinates", [])
        limit = min(max(int(payload.get("limit", 20)), 1), 50)
        if method == "rls_timeline_read":
            tensor = payload.get("tensor")
            selected = [item for item in coordinates if tensor is None or item.get("tensor") == tensor]
            return {"tick_range": packet.get("tick_range"), "coordinates": selected[:limit], "source_snapshot_hashes": packet.get("source_snapshot_hashes"), "boundary": "read_only"}
        if method == "rls_lineage_read":
            record_id = str(payload.get("record_id", ""))
            relations = [item for item in packet.get("cross_tensor_lineage", []) if item.get("record_id") == record_id]
            return {"record_id": record_id, "relations": relations, "relation_basis": "explicit_lineage_only", "boundary": "read_only"}
        return {"packet_type": packet.get("packet_type"), "orb_version": packet.get("orb_version"), "tick_range": packet.get("tick_range"), "source_coordinates": coordinates[:limit], "packet_sha256": packet.get("packet_sha256"), "provenance": packet.get("provenance"), "boundary": "replay_only"}


def serve() -> None:
    attachment = RLSPortalUmbilical()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v1/portal/rls":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > MAX_BODY:
                    raise ValueError("request body is outside bounds")
                auth = self.headers.get("Authorization", "")
                token = auth[7:] if auth.startswith("Bearer ") else None
                if not attachment._authenticated(token):
                    self._send(HTTPStatus.FORBIDDEN, {"authorized": False, "action_executed": False})
                    return
                request = json.loads(self.rfile.read(length))
                result = attachment.dispatch(str(request.get("method", "")), request)
                self._send(HTTPStatus.OK, {"authorized": True, "action_executed": True, "result": result, "mutation_performed": False, "experience_created": False, "admission_performed": False})
            except PermissionError as exc:
                self._send(HTTPStatus.FORBIDDEN, {"authorized": False, "reason": str(exc), "action_executed": False})
            except (ValueError, TypeError, json.JSONDecodeError, OSError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"authorized": False, "reason": str(exc)})

        def _send(self, status: HTTPStatus, value: dict[str, Any]) -> None:
            body = (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args: Any) -> None:
            return

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    serve()
