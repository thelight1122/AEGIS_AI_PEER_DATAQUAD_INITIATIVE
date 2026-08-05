"""Fail-closed M2 transport and identity configuration gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ALLOWED_SCOPES = {
    "pod.context.read", "pod.canon.read", "pod.continuity.observed.read",
    "pod.reflection.replay", "pod.status.read",
}


class TransportGateError(ValueError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TransportGateError("transport config will be an object")
    return value


def validate_config(config: dict[str, Any], *, production: bool = False) -> dict[str, Any]:
    if set(config.get("scopes", [])) - ALLOWED_SCOPES:
        raise TransportGateError("scope outside the approved read/replay set")
    auth = config.get("authentication", {})
    tls = config.get("tls", {})
    backend = config.get("portal_backend", {})
    parsed = urlparse(str(backend.get("url", "")))
    if not backend.get("credential_source") or "token" in backend.get("credential_source", "").lower() and not backend.get("credential_source"):
        raise TransportGateError("Portal credential source is required")
    def embedded_secret(value: Any, key: str = "") -> bool:
        if key.lower() in {"token", "secret", "password", "private_key"}:
            return True
        if isinstance(value, dict):
            return any(embedded_secret(child, child_key) for child_key, child in value.items())
        if isinstance(value, list):
            return any(embedded_secret(child, key) for child in value)
        return False

    if embedded_secret(config):
        raise TransportGateError("credentials will not be embedded in transport config")
    if production:
        if config.get("mode") != "production" or not config.get("listener_enabled"):
            raise TransportGateError("production gate requires production mode and an explicitly enabled listener")
        if config.get("transport") != "streamable_http" or parsed.scheme != "https":
            raise TransportGateError("production transport requires Streamable HTTP and HTTPS Portal backend")
        if auth.get("scheme") != "oauth2_oidc" or not auth.get("issuer") or not auth.get("audience"):
            raise TransportGateError("production OAuth/OIDC issuer and audience are required")
        if not tls.get("required") or not tls.get("certificate_reference") or not tls.get("private_key_reference"):
            raise TransportGateError("production TLS references are required")
        if config.get("bind_host") in {"127.0.0.1", "localhost", "0.0.0.0"}:
            raise TransportGateError("production bind host will be an explicitly approved interface or tunnel")
    else:
        if config.get("listener_enabled"):
            raise TransportGateError("non-production listener will remain disabled")
        if config.get("bind_host") != "127.0.0.1":
            raise TransportGateError("non-production bind will remain loopback")
    return {"valid": True, "production": production, "listener_enabled": bool(config.get("listener_enabled")), "scopes": sorted(config.get("scopes", [])), "portal_backend": parsed.geturl()}
