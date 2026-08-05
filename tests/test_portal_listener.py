import json
import threading
from http.client import HTTPConnection
from pathlib import Path

import pytest

from aegis_pod.portal_listener import create_server


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "phase1c-test-token"


@pytest.fixture
def listener():
    server = create_server(ROOT / "fixtures" / "phase1c-portal-manifest.json", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(port: int, method: str, body: dict | None = None, token: str | None = TOKEN, path: str = "/v1/portal/authorize"):
    conn = HTTPConnection("127.0.0.1", port, timeout=2)
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    conn.request(method, path, json.dumps(body or {}).encode(), headers)
    response = conn.getresponse()
    payload = json.loads(response.read())
    conn.close()
    return response.status, payload


def test_loopback_health_and_authorization(listener: int) -> None:
    conn = HTTPConnection("127.0.0.1", listener, timeout=2)
    conn.request("GET", "/health")
    health = conn.getresponse()
    assert health.status == 200
    assert json.loads(health.read())["frontier_connection"] is False
    conn.close()

    status, payload = request(listener, "POST", {"method": "retrieve_context", "limit": 5})
    assert status == 200
    assert payload["authorized"] is True
    assert payload["action_executed"] is False


def test_loopback_denies_unauthorized_and_live_reflection(listener: int) -> None:
    status, _ = request(listener, "POST", {"method": "retrieve_context"}, token="wrong")
    assert status == 403
    status, _ = request(listener, "POST", {"method": "request_reflection", "reflection_mode": "live"})
    assert status == 403


def test_listener_rejects_non_loopback_bind() -> None:
    with pytest.raises(ValueError, match="loopback-only"):
        create_server(ROOT / "fixtures" / "phase1c-portal-manifest.json", host="0.0.0.0", port=0)


def test_execute_route_requires_configured_router(listener: int) -> None:
    status, payload = request(listener, "POST", {"method": "retrieve_context"}, path="/v1/portal/execute")
    assert status == 503
    assert payload["action_executed"] is False


def test_frontier_handshake_is_fixed_and_routes_to_pod(tmp_path: Path) -> None:
    class FakeRouter:
        def execute(self, **kwargs):
            assert kwargs["method"] == "retrieve_context"
            assert kwargs["limit"] == 1
            assert kwargs["caller"] == "frontier_substrate"
            return {"authorized": True, "action_executed": True, "mutation_performed": False}

    server = create_server(ROOT / "fixtures" / "phase1c-portal-manifest.json", port=0, router=FakeRouter())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, payload = request(server.server_address[1], "POST", {"method": "retrieve_context", "query": "", "limit": 1}, path="/v1/frontier/handshake")
        assert status == 200
        assert payload["handshake"] == "frontier_to_pod_continuity"
        assert payload["frontier_model_loaded_on_vm"] is False
        status, _ = request(server.server_address[1], "POST", {"method": "retrieve_context", "query": "unexpected", "limit": 1}, path="/v1/frontier/handshake")
        assert status == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
