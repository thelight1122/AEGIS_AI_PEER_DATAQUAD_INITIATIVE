from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from ..execution_ledger import append_record, sha256_value


READ_REPLAY_BOUNDARIES = {
    "mutation": False,
    "admission": False,
    "experience_created": False,
    "dataquad_writeback": False,
    "live_rls_invoked": False,
    "shell_access": False,
    "filesystem_access": False,
}


class PortalPodError(ValueError):
    """Fail-closed Portal Pod contract or authority error."""


@dataclass(frozen=True)
class NormalizedInvocation:
    caller: str
    orb_id: str
    capability: str
    parameters: dict[str, Any]
    scopes: frozenset[str]
    session_id: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "NormalizedInvocation":
        if not isinstance(value, dict):
            raise PortalPodError("invocation will be an object")
        caller = value.get("caller")
        orb_id = value.get("orb_id")
        capability = value.get("capability")
        parameters = value.get("parameters", {})
        authority = value.get("authority", {})
        if not all(isinstance(item, str) and item for item in (caller, orb_id, capability)):
            raise PortalPodError("caller, orb_id, and capability are required")
        if not isinstance(parameters, dict) or not isinstance(authority, dict):
            raise PortalPodError("parameters and authority will be objects")
        scopes = authority.get("scopes", [])
        if not isinstance(scopes, list) or not all(isinstance(item, str) for item in scopes):
            raise PortalPodError("authority.scopes will be a list of strings")
        session_id = value.get("session_id") or str(uuid4())
        if not isinstance(session_id, str) or not session_id:
            raise PortalPodError("session_id will be a non-empty string")
        return cls(caller, orb_id, capability, parameters, frozenset(scopes), session_id)


@dataclass(frozen=True)
class _Binding:
    orb_id: str
    umbilical_id: str
    effective_scopes: frozenset[str]
    allowed_capabilities: frozenset[str]
    attached: bool


Handler = Callable[[dict[str, Any]], dict[str, Any]]


class PortalPod:
    """Protocol-neutral membrane around existing bounded Portal handlers."""

    def __init__(self, manifest: dict[str, Any], *, evidence_ledger: Path | None = None) -> None:
        self.manifest = manifest
        self.evidence_ledger = evidence_ledger
        self._bindings: dict[str, _Binding] = {}
        self._handlers: dict[str, tuple[str, Handler, str]] = {}

    def register_capability(self, name: str, handler: Handler, *, required_scope: str) -> None:
        if not name or not callable(handler) or not required_scope:
            raise PortalPodError("capability registration is incomplete")
        declared = self._declared_capabilities()
        if name not in declared:
            raise PortalPodError(f"capability is not declared by the Portal Pod: {name}")
        if declared[name].get("enabled") is not True:
            raise PortalPodError(f"capability is disabled: {name}")
        self._handlers[name] = (name, handler, required_scope)

    def attach(self, orb: dict[str, Any], umbilical: dict[str, Any]) -> dict[str, Any]:
        pod_id = self.manifest.get("pod_id")
        orb_id = orb.get("orb_id")
        if not isinstance(orb_id, str) or not orb_id:
            raise PortalPodError("Orb id is required")
        if umbilical.get("pod_id") != pod_id or umbilical.get("orb_id") != orb_id:
            raise PortalPodError("Umbilical identity does not match the Pod and Orb")
        if orb.get("enabled") is not False:
            raise PortalPodError("Orbs will attach disabled before local proof")
        if umbilical.get("mutation_authority") or umbilical.get("admission_authority") or umbilical.get("experience_authority"):
            raise PortalPodError("mutating authority is prohibited at P0")
        allowed = frozenset(orb.get("capabilities", []))
        umbilical_allowed = frozenset(umbilical.get("allowed_capabilities", []))
        portal_allowed = frozenset(self._declared_capabilities())
        effective = allowed & umbilical_allowed & portal_allowed
        if not effective:
            raise PortalPodError("Orb/Umbilical/Portal capability intersection is empty")
        prohibited = set(umbilical.get("prohibited_capabilities", []))
        if effective & prohibited:
            raise PortalPodError("capability appears in both allowed and prohibited sets")
        binding = _Binding(
            orb_id=orb_id,
            umbilical_id=str(umbilical["umbilical_id"]),
            effective_scopes=frozenset(umbilical.get("allowed_scopes", [])),
            allowed_capabilities=effective,
            attached=False,
        )
        self._bindings[orb_id] = binding
        return {
            "orb_id": orb_id,
            "umbilical_id": binding.umbilical_id,
            "attached": False,
            "effective_capabilities": sorted(effective),
            "effective_scopes": sorted(binding.effective_scopes),
        }

    def enable(self, orb_id: str) -> None:
        binding = self._bindings.get(orb_id)
        if binding is None:
            raise PortalPodError("Orb is not attached")
        self._bindings[orb_id] = _Binding(**{**binding.__dict__, "attached": True})

    def dispatch(self, invocation: NormalizedInvocation | dict[str, Any]) -> dict[str, Any]:
        request = invocation if isinstance(invocation, NormalizedInvocation) else NormalizedInvocation.from_dict(invocation)
        binding = self._bindings.get(request.orb_id)
        if binding is None or not binding.attached:
            raise PortalPodError("Orb is not enabled")
        if request.capability not in binding.allowed_capabilities:
            raise PortalPodError("capability denied by Orb/Umbilical/Portal intersection")
        registered = self._handlers.get(request.capability)
        if registered is None:
            raise PortalPodError("capability has no registered handler")
        _, handler, required_scope = registered
        if required_scope not in request.scopes or required_scope not in binding.effective_scopes:
            raise PortalPodError("required scope is not present in the authority intersection")
        result = handler(request.parameters)
        if not isinstance(result, dict):
            raise PortalPodError("capability handler will return an object")
        evidence = {
            "schema_version": "0.1.0",
            "record_type": "portal_pod_invocation_evidence",
            "request_id": str(uuid4()),
            "session_id": request.session_id,
            "caller": request.caller,
            "orb_id": request.orb_id,
            "umbilical_id": binding.umbilical_id,
            "capability": request.capability,
            "required_scope": required_scope,
            "result_sha256": sha256_value(result),
            "boundaries": dict(READ_REPLAY_BOUNDARIES),
        }
        if self.evidence_ledger is not None:
            append_record(self.evidence_ledger, evidence)
        return {"result": result, "evidence": evidence, "boundaries": dict(READ_REPLAY_BOUNDARIES)}

    def status(self) -> dict[str, Any]:
        return {
            "pod_id": self.manifest.get("pod_id"),
            "mode": self.manifest.get("mode"),
            "attached_orbs": sorted(self._bindings),
            "enabled_orbs": sorted(key for key, value in self._bindings.items() if value.attached),
            "capabilities": sorted(self._declared_capabilities()),
            "boundaries": dict(READ_REPLAY_BOUNDARIES),
        }

    def _declared_capabilities(self) -> dict[str, dict[str, Any]]:
        return {item["name"]: item for item in self.manifest.get("capability_orbs", [])}


def contract_hash(*documents: dict[str, Any]) -> str:
    payload = json.dumps(documents, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()
