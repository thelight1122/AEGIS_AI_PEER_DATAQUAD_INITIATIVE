import json
from pathlib import Path

from aegis_pod.portal_pod.runtime import PortalPod
from aegis_pod.rls_orb import RLSOrb
from aegis_pod.rls_protocol_orbs import RLSProtocolOrb, result_hash


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def build_surface() -> tuple[RLSOrb, RLSProtocolOrb]:
    orb = RLSOrb(ROOT)
    orb.build_index()
    pod = PortalPod(load("r0-portal-pod.json"))
    pod.register_capability("rls.status.read", lambda params: orb.status(), required_scope="rls.status.read")
    pod.register_capability("rls.timeline.read", lambda params: orb.timeline(tensor=params.get("tensor")), required_scope="rls.timeline.read")
    pod.register_capability("rls.lineage.read", lambda params: orb.cross_tensor_lineage(params["record_id"]), required_scope="rls.lineage.read")
    pod.register_capability("rls.reflection.replay", lambda params: orb.reflection_packet(), required_scope="rls.reflection.replay")
    pod.attach(load("r0-rls-capability-orb.json"), load("r0-rls-umbilical.json"))
    pod.enable("rls-coordinate-orb")
    return orb, RLSProtocolOrb(pod)


def test_mcp_and_action_orbs_return_identical_reflection_results():
    _, surface = build_surface()
    mcp = surface.mcp_call("pod_rls_reflection", {})
    action = surface.action_call("requestRlsReflection", {})
    assert result_hash(mcp) == result_hash(action)
    assert mcp["result"]["packet_type"] == "rls_structural_reflection_packet"
    assert mcp["boundaries"] == action["boundaries"]


def test_unknown_protocol_operations_fail_closed():
    _, surface = build_surface()
    try:
        surface.mcp_call("appendEvent", {})
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("write-like MCP operation was not rejected")
