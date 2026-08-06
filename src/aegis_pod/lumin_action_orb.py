"""P1 — the Lumin GPT Action Orb.

The Action Orb is the outer Orb through which the Lumin Custom GPT enters the Portal Pod.
It defines how that substrate communicates. It does not define what may be requested; the
Portal Pod and the Capability Orbs do that, and the effective authority is the intersection.

    Lumin Custom GPT -> GPT Action Orb -> Portal Pod -> Capability Orbs -> DataQuad / RLS

Every operation is read or replay. The prior bridge Action exposed `appendEvent` against
`POST /api/live-bridge/events`; that operation is retired with no replacement, because
experience admission is a separate authorized process and is not reachable from an Action
Orb. `RETIRED_OPERATIONS` keeps the retirement legible rather than silent, and
`refuse_retired` raises on any attempt to call one.

This module opens no listener and performs no network operation. Serving it from a live
origin is a separate authorized deployment.
"""

from __future__ import annotations

from typing import Any

from .portal_pod.runtime import PortalPod, PortalPodError

ORB_ID = "lumin-gpt-action-orb"

#: Action operationId -> Portal Pod capability.
OPERATION_TO_CAPABILITY: dict[str, str] = {
    "getPodStatus": "pod_get_status",
    "retrieveContext": "retrieve_context",
    "retrieveCanon": "retrieve_canon",
    "queryContinuity": "query_continuity",
    "requestReflection": "request_reflection",
}

#: Action operationId -> the single scope that operation may present.
OPERATION_TO_SCOPE: dict[str, str] = {
    "getPodStatus": "pod.status.read",
    "retrieveContext": "pod.context.read",
    "retrieveCanon": "pod.canon.read",
    "queryContinuity": "pod.continuity.observed.read",
    "requestReflection": "pod.reflection.replay",
}

#: Operations that existed on the prior bridge Action and are deliberately not carried forward.
RETIRED_OPERATIONS: dict[str, dict[str, Any]] = {
    "appendEvent": {
        "method": "POST",
        "path": "/api/live-bridge/events",
        "retired_in": "P1",
        "replacement": None,
        "reason": "Writing is incompatible with the read and replay only posture. Experience admission is a separate authorized process and is not reachable from a GPT Action Orb.",
    }
}

#: Scopes an Action Orb will never present, regardless of what a caller supplies.
PROHIBITED_SCOPES: frozenset[str] = frozenset(
    {
        "pod.experience.write",
        "pod.admission.perform",
        "pod.dataquad.write",
        "pod.rls.live",
        "pod.shell",
        "pod.filesystem",
    }
)


class ActionOrbError(ValueError):
    """Raised when an operation is unknown, retired, or outside the Orb's authority."""


def refuse_retired(operation: str) -> None:
    """Raise if `operation` was retired. Named so the refusal reads as deliberate."""
    retired = RETIRED_OPERATIONS.get(operation)
    if retired is not None:
        raise ActionOrbError(
            f"operation '{operation}' was retired in {retired['retired_in']} "
            f"({retired['method']} {retired['path']}): {retired['reason']}"
        )


class LuminActionOrb:
    """Maps Lumin Action operations onto Portal Pod capabilities.

    The Orb holds no authority of its own. It normalizes a request, presents exactly one
    scope, and lets the Portal Pod decide. A capability the Portal has not registered, or a
    scope the Umbilical does not allow, is refused by the Portal, not here.
    """

    def __init__(self, portal: PortalPod, *, orb_id: str = ORB_ID, caller: str = "lumin-gpt") -> None:
        self.portal = portal
        self.orb_id = orb_id
        self.caller = caller

    @property
    def operations(self) -> tuple[str, ...]:
        return tuple(sorted(OPERATION_TO_CAPABILITY))

    def describe(self) -> dict[str, Any]:
        return {
            "orb_id": self.orb_id,
            "orb_class": "protocol",
            # Matches the enum in contracts/protocol-orb.schema.json.
            "protocol": "gpt_action",
            "operations": {
                operation: {"capability": OPERATION_TO_CAPABILITY[operation], "scope": OPERATION_TO_SCOPE[operation]}
                for operation in self.operations
            },
            "retired_operations": {name: dict(detail) for name, detail in RETIRED_OPERATIONS.items()},
            "prohibited_scopes": sorted(PROHIBITED_SCOPES),
            "boundaries": {
                "authoritative_tensor_write": False,
                "experience_created": False,
                "admission_performed": False,
                "live_rls_invoked": False,
                "shell": False,
                "filesystem": False,
                "listener_enabled": False,
            },
        }

    def call(self, operation: str, payload: dict[str, Any] | None = None, *, session_id: str | None = None) -> dict[str, Any]:
        refuse_retired(operation)

        capability = OPERATION_TO_CAPABILITY.get(operation)
        if capability is None:
            raise ActionOrbError(f"unknown Lumin Action operation: {operation}")

        scope = OPERATION_TO_SCOPE[operation]
        if scope in PROHIBITED_SCOPES:  # Defensive: the maps above must never drift into a write scope.
            raise ActionOrbError(f"operation '{operation}' maps to prohibited scope '{scope}'")

        try:
            return self.portal.dispatch(
                {
                    "caller": self.caller,
                    "orb_id": self.orb_id,
                    "capability": capability,
                    "parameters": dict(payload or {}),
                    "authority": {"scopes": [scope]},
                    "session_id": session_id or f"{self.caller}-p1",
                }
            )
        except PortalPodError:
            raise
