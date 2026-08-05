"""Local protocol Orbs for the read-only RLS capability surface."""

from __future__ import annotations

from typing import Any

from .portal_pod.runtime import PortalPod


MCP_TO_CAPABILITY = {
    "pod_rls_status": "rls.status.read",
    "pod_rls_timeline": "rls.timeline.read",
    "pod_rls_lineage": "rls.lineage.read",
    "pod_rls_reflection": "rls.reflection.replay",
}

ACTION_TO_CAPABILITY = {
    "getRlsStatus": "rls.status.read",
    "retrieveRlsTimeline": "rls.timeline.read",
    "retrieveRlsLineage": "rls.lineage.read",
    "requestRlsReflection": "rls.reflection.replay",
}


class RLSProtocolOrb:
    def __init__(self, portal: PortalPod, *, orb_id: str = "rls-coordinate-orb") -> None:
        self.portal = portal
        self.orb_id = orb_id

    def _dispatch(self, *, caller: str, capability: str, parameters: dict[str, Any], scope: str) -> dict[str, Any]:
        return self.portal.dispatch({
            "caller": caller,
            "orb_id": self.orb_id,
            "capability": capability,
            "parameters": parameters,
            "authority": {"scopes": [scope]},
            "session_id": f"{caller}-r1-local",
        })

    def mcp_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        capability = MCP_TO_CAPABILITY.get(tool_name)
        if capability is None:
            raise ValueError("unknown RLS MCP tool")
        return self._dispatch(caller="mcp-orb", capability=capability, parameters=arguments, scope=capability)

    def action_call(self, operation: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        capability = ACTION_TO_CAPABILITY.get(operation)
        if capability is None:
            raise ValueError("unknown RLS GPT Action operation")
        return self._dispatch(caller="gpt-action-orb", capability=capability, parameters=payload or {}, scope=capability)


def result_hash(dispatch_result: dict[str, Any]) -> str:
    from .execution_ledger import sha256_value

    return sha256_value(dispatch_result["result"])
