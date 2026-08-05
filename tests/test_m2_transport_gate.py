import json
from pathlib import Path

import pytest

from aegis_pod.m2_transport_gate import TransportGateError, load_config, validate_config


ROOT = Path(__file__).resolve().parents[1]


def test_loopback_m2_config_is_valid():
    result = validate_config(load_config(ROOT / "fixtures" / "m2-external-transport.json"))
    assert result["valid"] is True
    assert result["listener_enabled"] is False


def test_nonproduction_public_listener_fails_closed():
    config = load_config(ROOT / "fixtures" / "m2-external-transport.json")
    config["listener_enabled"] = True
    with pytest.raises(TransportGateError):
        validate_config(config)


def test_unknown_write_scope_fails_closed():
    config = load_config(ROOT / "fixtures" / "m2-external-transport.json")
    config["scopes"].append("pod.dataquad.write")
    with pytest.raises(TransportGateError):
        validate_config(config)


def test_production_requires_https_oauth_and_tls():
    config = load_config(ROOT / "fixtures" / "m2-external-transport.json")
    config.update({"mode": "production", "listener_enabled": True, "transport": "streamable_http", "bind_host": "10.0.0.4"})
    with pytest.raises(TransportGateError):
        validate_config(config, production=True)
