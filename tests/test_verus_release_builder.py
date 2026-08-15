from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import urllib.error

import pytest
import stat
from types import SimpleNamespace

from aegis_verus_lab.dataquad import VerusDataQuad
from aegis_verus_lab.frontier import (
    AnthropicMessagesAdapter,
    FileSecretLoader,
    FrontierAuthenticationError,
    FrontierProtocolError,
    FrontierRateLimitError,
    FrontierTurnRequest,
    FrontierUnavailableError,
)
from aegis_verus_lab.credential_preflight import CredentialPreflightRefused, validate_credential_source


ROOT = Path(__file__).resolve().parents[1]
SEATING_TIMESTAMP = "2026-08-15T12:34:56Z"
spec = importlib.util.spec_from_file_location("build_verus_release", ROOT / "scripts" / "build_verus_lab_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_release_builds_authoritative_verus_foundation_without_activation(tmp_path):
    historical_hash = hashlib.sha256((ROOT / "fixtures" / "ai-peer-roster.json").read_bytes()).hexdigest()
    output = tmp_path / "release"
    manifest = builder.build_release(
        output, source_commit="test-commit", seating_timestamp=SEATING_TIMESTAMP,
    )
    assert manifest["cyberpeer_name"] == "Verus"
    assert manifest["identity_variables"] == {"cyberpeer_name": "Verus"}
    assert manifest["activation_status"] == "NOT_INSTALLED"
    assert manifest["credentials_included"] is False
    assert manifest["other_peer_state_included"] is False
    assert manifest["seating_timestamp"] == SEATING_TIMESTAMP
    assert hashlib.sha256((ROOT / "fixtures" / "ai-peer-roster.json").read_bytes()).hexdigest() == historical_hash

    dataquad = VerusDataQuad(output / "foundation", tmp_path / "state")
    verified = dataquad.verify()
    assert verified == {
        "cyberpeer_name": "Verus", "dataquad_id": "verus",
        "foundation_records": 133, "records": 0, "head_hash": None, "verified": True,
    }
    receipt = json.loads((output / "foundation" / "foundation-receipt.json").read_text())
    assert receipt["record_contract"] == {
        "kind": "verus-foundation-consumer-contract-v1",
        "formal_json_schema": None,
        "reason": "The repository tensor-record schema applies to migrated/copy records, not seating-builder Foundation records.",
        "validated_records": 133,
    }
    assert {name: item["records"] for name, item in receipt["tensors"].items()} == {
        "SPINE": 59, "NCT": 70, "PEER": 2, "PCT": 2,
    }
    for tensor in ("SPINE", "NCT", "PEER", "PCT"):
        for item in (json.loads(line) for line in
                     (output / "foundation" / "dataquad" / f"{tensor}.jsonl").read_text().splitlines()):
            assert item["cyberpeer_name"] == "Verus"
            assert item["routing_provenance"]["defines_identity"] is False
            assert "model_id" not in item.get("present_state", {})
            assert "model_id" not in item.get("working_context", {})
            assert "peer_id" not in item.get("present_state", {})
            assert "peer_id" not in item.get("working_context", {})
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore")
                       for path in output.rglob("*") if path.is_file())
    assert "sk-ant-" not in text
    assert "ANTHROPIC_API_KEY=" not in text

    second = tmp_path / "release-2"
    builder.build_release(
        second, source_commit="test-commit", seating_timestamp=SEATING_TIMESTAMP,
    )
    for tensor in ("SPINE", "NCT", "PEER", "PCT"):
        first_bytes = (output / "foundation" / "dataquad" / f"{tensor}.jsonl").read_bytes()
        second_bytes = (second / "foundation" / "dataquad" / f"{tensor}.jsonl").read_bytes()
        assert first_bytes == second_bytes


def test_release_builder_refuses_nonempty_output(tmp_path):
    output = tmp_path / "release"
    output.mkdir()
    (output / "existing").write_text("preserve me")
    with pytest.raises(builder.ReleaseBuildRefused, match="absent or empty"):
        builder.build_release(output, seating_timestamp=SEATING_TIMESTAMP)
    assert (output / "existing").read_text() == "preserve me"


@pytest.mark.parametrize("value", ["", "2026-08-15", "2026-08-15T12:34:56-07:00", "not-a-time"])
def test_release_builder_requires_explicit_valid_utc_seating_timestamp(tmp_path, value):
    with pytest.raises(builder.ReleaseBuildRefused, match="seating_timestamp"):
        builder.build_release(tmp_path / value.replace(":", "_"), seating_timestamp=value)


def test_anthropic_adapter_loads_secret_only_for_call_and_maps_tool_result(tmp_path):
    secret = tmp_path / "anthropic"
    secret.write_text("runtime-secret", encoding="utf-8")
    captured = {}

    def transport(request):
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data)
        return {
            "id": "msg_123",
            "model": "claude-runtime-exact",
            "content": [{
                "type": "tool_use", "name": "complete_verus_turn",
                "input": {
                    "response_text": "done",
                    "dataquad_appends": [{"tensor": "SPINE", "payload": {"event": "done"}}],
                },
            }],
        }

    adapter = AnthropicMessagesAdapter(
        model="claude-runtime-exact", secret_loader=FileSecretLoader(secret), transport=transport,
    )
    assert "runtime-secret" not in repr(adapter)
    result = adapter.complete(FrontierTurnRequest(
        cyberpeer_name="Verus", dataquad_id="verus", turn_id="t1", source_event_id="e1",
        frontier_session_id="s1", system_instructions="operational", prompt="work", context={},
    ))
    assert captured["headers"]["X-api-key"] == "runtime-secret"
    assert captured["body"]["model"] == "claude-runtime-exact"
    assert captured["body"]["tool_choice"] == {"type": "tool", "name": "complete_verus_turn"}
    assert captured["body"]["tools"][0]["input_schema"]["type"] == "object"
    assert captured["body"]["tools"][0]["input_schema"]["additionalProperties"] is False
    assert result.provider == "Anthropic" and result.substrate == "Claude"
    assert result.model == "claude-runtime-exact"
    assert result.append_intents[0].tensor == "SPINE"


@pytest.mark.parametrize(
    ("wire_error", "expected"),
    [
        (urllib.error.HTTPError("https://api.anthropic.com", 401, "secret detail", {}, None), FrontierAuthenticationError),
        (urllib.error.HTTPError("https://api.anthropic.com", 429, "secret detail", {}, None), FrontierRateLimitError),
        (urllib.error.HTTPError("https://api.anthropic.com", 503, "secret detail", {}, None), FrontierUnavailableError),
        (urllib.error.URLError("secret network detail"), FrontierUnavailableError),
        (urllib.error.HTTPError("https://api.anthropic.com", 400, "secret detail", {}, None), FrontierProtocolError),
    ],
)
def test_anthropic_adapter_bounds_expected_wire_failures(tmp_path, wire_error, expected):
    secret = tmp_path / "anthropic"
    secret.write_text("runtime-secret", encoding="utf-8")

    def transport(_):
        raise wire_error

    adapter = AnthropicMessagesAdapter(
        model="exact-model", secret_loader=FileSecretLoader(secret), transport=transport,
    )
    request = FrontierTurnRequest(
        cyberpeer_name="Verus", dataquad_id="verus", turn_id="t", source_event_id="e",
        frontier_session_id="s", system_instructions="ops", prompt="work", context={},
    )
    with pytest.raises(expected) as captured:
        adapter.complete(request)
    assert "runtime-secret" not in str(captured.value)
    assert "secret detail" not in str(captured.value)


def test_verus_deployment_is_one_peer_loopback_only_and_preserving():
    deploy = ROOT / "deploy" / "verus-lab"
    unit = (deploy / "systemd" / "aegis-verus-lab.service").read_text()
    env = (deploy / "env" / "verus.env.template").read_text()
    installer = (deploy / "scripts" / "install.sh").read_text()
    pause = (deploy / "scripts" / "pause.sh").read_text()
    assert "AEGIS_BIND=127.0.0.1" in env
    assert "AEGIS_PORT=SET_PORT_AT_ACTIVATION" in env
    assert "AEGIS_CYBERPEER_NAME=Verus" in env
    assert "SET_AT_ACTIVATION" in env
    assert "LoadCredential=anthropic_api_key:" in unit
    assert "LoadCredential=bridge_token:" in unit
    assert "ReadWritePaths=/var/lib/aegis-ai-peers/verus" in unit
    assert "full_append_only_dataquad" in installer
    assert "VERUS_PORT=${VERUS_PORT:-8791}" in installer
    assert "loopback port is already in use" in installer
    assert 'AEGIS_PORT="$VERUS_PORT" "$RELEASE_DIR/scripts/health.sh"' in installer
    assert "aegis_verus_lab.credential_preflight" in installer
    assert "trap restore_or_pause_on_error ERR" in installer
    assert "PRIOR_SERVICE_ENABLED" in installer
    assert 'install-recovery/$RELEASE_ID' in installer
    assert '"$RECOVERY_DIR/aegis-verus-lab.service"' in installer
    assert '"$RELEASE_DIR/scripts/health.sh"' in installer
    assert "prior release and service state restored" in installer
    assert "Prior Verus release was restored but failed health; service paused safely." in installer
    assert "service is paused and state is preserved" in installer
    assert "rm " not in installer and "rm " not in pause
    assert "systemctl stop aegis-verus-lab.service" in pause

    health = (deploy / "scripts" / "health.sh").read_text()
    assert "${AEGIS_PORT:-8791}" in health


@pytest.mark.parametrize(
    ("mode", "uid", "message"),
    [
        (stat.S_IFLNK | 0o777, 0, "must not be a symlink"),
        (stat.S_IFDIR | 0o700, 0, "regular file"),
        (stat.S_IFREG | 0o600, 1000, "owner must be root"),
        (stat.S_IFREG | 0o640, 0, "0400 or 0600"),
        (stat.S_IFREG | 0o644, 0, "0400 or 0600"),
    ],
)
def test_credential_preflight_refuses_unsafe_metadata_without_reading_content(mode, uid, message):
    def metadata_only(_):
        return SimpleNamespace(st_mode=mode, st_uid=uid)

    with pytest.raises(CredentialPreflightRefused, match=message):
        validate_credential_source("/secret/source", lstat=metadata_only)


@pytest.mark.parametrize("mode", [0o400, 0o600])
def test_credential_preflight_accepts_root_owned_private_regular_file(mode):
    validate_credential_source(
        "/secret/source",
        lstat=lambda _: SimpleNamespace(st_mode=stat.S_IFREG | mode, st_uid=0),
    )
