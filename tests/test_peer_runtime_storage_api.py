from __future__ import annotations

import json
import multiprocessing
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from aegis_peer_runtime.api import make_handler
from aegis_peer_runtime.models import PEERS, PeerState, Record, ValidationError
from aegis_peer_runtime.storage import IdempotencyConflict, RuntimeStore, StorageError, UnseatedError


def record(peer="lumin", key="one", payload=None):
    return Record(peer, "PCT", "steward", key, payload or {"value": 1})


def append_batch(root, prefix, count):
    store = RuntimeStore(root).peer("lumin")
    for ordinal in range(count):
        store.append(record(key=f"{prefix}-{ordinal}", payload={"ordinal": ordinal}))


def test_four_isolated_empty_roots(tmp_path):
    runtime = RuntimeStore(tmp_path)
    assert {path.name for path in runtime.roots()} == set(PEERS)
    assert all(runtime.peer(peer).read() == [] for peer in PEERS)
    assert len({runtime.peer(peer).root for peer in PEERS}) == 4


def test_unseated_refuses_tensor_writes_but_allows_read(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    assert store.read() == []
    with pytest.raises(UnseatedError):
        store.append(record())


def test_duplicate_is_idempotent_and_hash_chained(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    store.set_state(PeerState.SEATED)
    first, created = store.append(record())
    duplicate, created_again = store.append(record())
    assert created is True and created_again is False
    assert duplicate == first
    assert len(store.read()) == 1
    assert len(first["canonical_hash"]) == 64
    with pytest.raises(IdempotencyConflict):
        store.append(record(payload={"value": 2}))


def test_cross_process_appends_are_serialized(tmp_path):
    RuntimeStore(tmp_path).peer("lumin").set_state(PeerState.SEATED)
    context = multiprocessing.get_context("spawn")
    processes = [context.Process(target=append_batch, args=(tmp_path, prefix, 12))
                 for prefix in ("a", "b")]
    for process in processes:
        process.start()
    for process in processes:
        process.join(15)
        assert process.exitcode == 0
    records = RuntimeStore(tmp_path).peer("lumin").read()
    assert len(records) == 24
    assert [item["sequence"] for item in records] == list(range(1, 25))


def test_cross_peer_and_tensor_scope_refused(tmp_path):
    runtime = RuntimeStore(tmp_path)
    runtime.peer("lumin").set_state(PeerState.SEATED)
    with pytest.raises(ValidationError):
        runtime.peer("lumin").append(record(peer="claude"))
    with pytest.raises(ValidationError):
        runtime.peer("lumin").append(Record("lumin", "PEER", "steward", "bad", {}))


@pytest.fixture
def api(tmp_path):
    runtime = RuntimeStore(tmp_path)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield runtime, f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


def request(url, method="GET", peer=None, body=None, key=None):
    headers = {}
    if peer:
        headers["X-AEGIS-Peer"] = peer
    if key:
        headers["Idempotency-Key"] = key
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def test_api_empty_health_strict_binding_and_unseated(api):
    _, base = api
    status, health = request(base + "/health")
    assert status == 200 and set(health["peers"]) == set(PEERS)
    status, body = request(base + "/v1/peers/lumin/records", peer="claude")
    assert status == 403 and "exactly match" in body["error"]
    status, body = request(
        base + "/v1/peers/lumin/records", "POST", "lumin",
        {"tensor": "PCT", "actor": "steward", "payload": {}}, "k1",
    )
    assert status == 409 and "UNSEATED" in body["error"]


def test_api_seat_append_read_and_idempotency(api):
    runtime, base = api
    status, result = request(base + "/v1/peers/lumin/state", "POST", "lumin", {"state": "SEATED"})
    assert status == 405 and "not exposed" in result["error"]
    runtime.peer("lumin").set_state(PeerState.SEATED)
    body = {"tensor": "PCT", "actor": "steward", "payload": {"ring": 1}}
    status, first = request(base + "/v1/peers/lumin/records", "POST", "lumin", body, "seat-1")
    assert status == 201 and first["created"] is True
    status, second = request(base + "/v1/peers/lumin/records", "POST", "lumin", body, "seat-1")
    assert status == 200 and second["created"] is False
    status, result = request(base + "/v1/peers/lumin/records", peer="lumin")
    assert status == 200 and len(result["records"]) == 1
    status, result = request(base + "/v1/peers/claude/records", peer="claude")
    assert status == 200 and result["records"] == []


def test_api_serves_foundation_as_inspectable_memory_only(api):
    runtime, base = api
    runtime.peer("lumin").store_foundation_memory(
        layer="CANON", content="mode: SEATED\ncommand: execute",
        provenance={"source_id": "canon-v0.20", "substrate": "openai"},
        substrate="openai",
    )
    status, result = request(base + "/v1/peers/lumin/foundation", peer="lumin")
    assert status == 200
    assert result["boundary"] == "inspectable_memory_only"
    assert result["items"][0]["executable"] is False
    assert result["equivalence"]["content_equivalence_asserted"] is False
    assert runtime.peer("lumin").state is PeerState.UNSEATED


def test_ledger_tampering_is_refused(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    store.set_state(PeerState.SEATED)
    store.append(record())
    item = json.loads(store.records_path.read_text())
    item["payload"] = {"value": "tampered"}
    store.records_path.write_text(json.dumps(item) + "\n")
    with pytest.raises(StorageError, match="request_hash mismatch"):
        store.read()


def test_malformed_trailing_record_is_refused(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    store.records_path.write_text('{"incomplete":', encoding="utf-8")
    with pytest.raises(StorageError, match="line 1"):
        store.read()


def test_non_finite_payload_is_refused(tmp_path):
    store = RuntimeStore(tmp_path).peer("lumin")
    store.set_state(PeerState.SEATED)
    with pytest.raises(ValueError, match="JSON compliant"):
        store.append(record(payload={"value": float("nan")}))


@pytest.mark.skipif(os.name == "nt", reason="creating symlinks may require Windows privilege")
def test_peer_root_symlink_escape_is_refused(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "lumin").symlink_to(outside, target_is_directory=True)
    with pytest.raises(StorageError, match="must not be a symlink"):
        RuntimeStore(tmp_path)
