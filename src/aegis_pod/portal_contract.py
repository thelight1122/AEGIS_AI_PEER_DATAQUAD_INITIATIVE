"""Offline Phase 1C Portal authentication and capability contract harness."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_LIMIT = 100
ALLOWED_METHODS = frozenset({
    "retrieve_context",
    "retrieve_canon",
    "query_continuity",
    "request_reflection",
    "record_experience",
})


class PortalDenied(PermissionError):
    """Raised for every fail-closed authentication or capability denial."""


@dataclass(frozen=True)
class PortalDecision:
    allowed: bool
    method: str
    reason: str
    access: str = "disabled"
    scope: str = "none"


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Portal manifest will be an object")
    methods = [item.get("method") for item in value.get("capabilities", [])]
    if set(methods) != ALLOWED_METHODS or len(methods) != len(set(methods)):
        raise ValueError("Portal capabilities will contain each approved method exactly once")
    return value


def _capability(manifest: dict[str, Any], method: str) -> dict[str, Any] | None:
    return next((item for item in manifest.get("capabilities", []) if item.get("method") == method), None)


def _authenticated(manifest: dict[str, Any], bearer_token: str | None) -> bool:
    if not bearer_token:
        return False
    expected = manifest.get("authentication", {}).get("credential_hash", "")
    actual = hashlib.sha256(bearer_token.encode("utf-8")).hexdigest().upper()
    return hmac.compare_digest(actual.encode("ascii"), expected.encode("ascii"))


def authorize(
    manifest: dict[str, Any],
    *,
    method: str,
    bearer_token: str | None,
    limit: int = 20,
    reflection_mode: str | None = None,
    continuity_scope: str | None = None,
) -> PortalDecision:
    if manifest.get("listener_enabled") is not False:
        return PortalDecision(False, method, "listener is not contract-only")
    if not _authenticated(manifest, bearer_token):
        return PortalDecision(False, method, "authentication fell short")
    if limit < 1 or limit > MAX_LIMIT:
        return PortalDecision(False, method, "result limit is outside bounds")
    capability = _capability(manifest, method)
    if capability is None or capability.get("enabled") is not True:
        return PortalDecision(False, method, "capability is disabled or undeclared")
    max_results = capability.get("max_results")
    if max_results is not None and limit > max_results:
        return PortalDecision(False, method, "result limit exceeds capability bound")
    if method == "request_reflection" and reflection_mode != "replay_only":
        return PortalDecision(False, method, "reflection is replay-only")
    if method == "query_continuity" and continuity_scope not in {"observed", "admitted"}:
        return PortalDecision(False, method, "continuity scope is not observed or admitted")
    return PortalDecision(True, method, "authorized", capability["access"], capability["scope"])
