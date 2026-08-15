from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

import pytest

from aegis_verus_lab.api import make_handler
from aegis_verus_lab.dataquad import VerusDataQuad
from aegis_verus_lab.frontier import (
    AppendIntent,
    FrontierAuthenticationError,
    FrontierProtocolError,
    FrontierRateLimitError,
    FrontierTurnResponse,
    FrontierUnavailableError,
)
from aegis_verus_lab.runtime import VerusLabRuntime


class StaticSecret:
    def load(self):
        return "bridge-secret"


class Adapter:
    def complete(self, request):
        return FrontierTurnResponse(
            response_text="complete",
            append_intents=(AppendIntent("PEER", {"event": "completed"}),),
            provider="Anthropic", substrate="Claude", model="exact-model",
            provider_request_id="msg-1", frontier_session_id=request.frontier_session_id,
        )


class ErrorAdapter:
    def __init__(self, error):
        self.error = error

    def complete(self, request):
        raise self.error


def foundation(root: Path):
    dataquad = root / "dataquad"
    dataquad.mkdir(parents=True)
    tensors = {}
    for tensor, count in {"SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2}.items():
        path = dataquad / f"{tensor}.jsonl"
        path.write_bytes(b"".join(json.dumps({"tensor": tensor, "id": str(i)}).encode() + b"\n" for i in range(count)))
        tensors[tensor] = {"records": count, "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()}
    (root / "foundation-receipt.json").write_text(json.dumps({
        "record_type": "verus_foundation_release_receipt",
        "activation_status": "RELEASE_ARTIFACT_ONLY",
        "cyberpeer_name": "Verus", "dataquad_id": "verus",
        "canon_lock": {"clean": True, "override_used": False}, "tensors": tensors,
    }))


@pytest.fixture
def bridge(tmp_path):
    release = tmp_path / "foundation"
    foundation(release)
    runtime = VerusLabRuntime(
        VerusDataQuad(release, tmp_path / "state"), Adapter(),
        clock=lambda: datetime(2026, 8, 15, 4, tzinfo=timezone.utc),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime, StaticSecret()))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield runtime, f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


def request(url, *, method="GET", token=None, name=None, key=None, body=None):
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if name is not None:
        headers["X-AEGIS-CyberPeer-Name"] = name
    if key is not None:
        headers["Idempotency-Key"] = key
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def test_health_is_verus_lab_running_with_full_append_authority(bridge):
    _, base = bridge
    status, body = request(base + "/health")
    assert status == 200
    assert body["mode"] == "LAB_RUNNING" and body["ready"] is True
    assert body["cyberpeer_name"] == "Verus"
    assert set(body["writable_tensors"]) == {"PEER", "PCT", "NCT", "SPINE"}
    assert body["coherence"]["coherent"] is True


def test_bridge_requires_runtime_secret_and_exact_name_then_is_idempotent(bridge):
    runtime, base = bridge
    body = {"source_event_id": "event-1", "frontier_session_id": "session-1", "prompt": "work"}
    assert request(base + "/v1/turn", method="POST", body=body)[0] == 401
    assert request(base + "/v1/turn", method="POST", token="bridge-secret", name="Claude", key="t1", body=body)[0] == 403
    status, first = request(base + "/v1/turn", method="POST", token="bridge-secret", name="Verus", key="t1", body=body)
    assert status == 201 and first["created"] is True
    status, replay = request(base + "/v1/turn", method="POST", token="bridge-secret", name="Verus", key="t1", body=body)
    assert status == 200 and replay["created"] is False
    assert replay["record_hash"] == first["record_hash"]
    assert runtime.dataquad.verify()["records"] == 1


def test_health_detects_committed_turn_missing_processor_evidence(bridge):
    runtime, base = bridge
    body = {"source_event_id": "event-1", "frontier_session_id": "session-1", "prompt": "work"}
    assert request(base + "/v1/turn", method="POST", token="bridge-secret", name="Verus", key="t1", body=body)[0] == 201
    runtime.processor.ledger_path.unlink()
    status, health = request(base + "/health")
    assert status == 503 and health["ready"] is False
    assert health["coherence"]["missing_processor_count"] == 1
    assert health["coherence"]["coherent"] is False


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (FrontierAuthenticationError("secret sk-ant-never-return"), 503, "frontier_authentication_unavailable"),
        (FrontierRateLimitError("secret sk-ant-never-return"), 429, "frontier_rate_limited"),
        (FrontierUnavailableError("secret sk-ant-never-return"), 503, "frontier_unavailable"),
        (FrontierProtocolError("secret sk-ant-never-return"), 502, "frontier_response_invalid"),
        (RuntimeError("secret sk-ant-never-return"), 500, "internal_shortfall"),
    ],
)
def test_bridge_maps_frontier_and_unexpected_failures_without_secret_leak(
    bridge, error, expected_status, expected_code,
):
    runtime, base = bridge
    runtime.adapter = ErrorAdapter(error)
    body = {"source_event_id": "event-1", "frontier_session_id": "session-1", "prompt": "work"}
    status, result = request(
        base + "/v1/turn", method="POST", token="bridge-secret", name="Verus",
        key=f"turn-{expected_code}", body=body,
    )
    assert status == expected_status and result == {"error": expected_code}
    assert "sk-ant" not in json.dumps(result)
    assert runtime.dataquad.live_turns() == []
    runtime.adapter = Adapter()
    recovery_status, recovery = request(
        base + "/v1/turn", method="POST", token="bridge-secret", name="Verus",
        key=f"recovery-{expected_code}", body=body,
    )
    assert recovery_status == 201 and recovery["created"] is True
