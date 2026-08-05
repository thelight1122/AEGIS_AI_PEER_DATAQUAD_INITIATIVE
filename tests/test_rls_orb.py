import json
from pathlib import Path

import jsonschema

from aegis_pod.portal_pod.runtime import PortalPod
from aegis_pod.rls_orb import RLSOrb


ROOT = Path(__file__).resolve().parents[1]


def load_fixture(name: str) -> dict:
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def test_rls_orb_indexes_all_four_tensors_and_emits_structural_packet():
    orb = RLSOrb(ROOT)
    status = orb.build_index()
    assert set(status["tensor_counts"]) == {"PEER", "PCT", "NCT", "SPINE"}
    assert status["record_count"] > 0
    assert status["writes"] == {"authoritative_tensors": False, "derived_ledgers": True}
    packet = orb.reflection_packet(t_from=0)
    schema = json.loads((ROOT / "contracts" / "rls-reflection-packet.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(packet, schema)
    assert packet["provenance"]["interpretation"] == "structural_only"
    assert packet["provenance"]["experience_created"] is False


def test_rls_orb_attaches_through_portal_pod_and_dispatches_read_only():
    orb = RLSOrb(ROOT)
    orb.build_index()
    pod = PortalPod(load_fixture("r0-portal-pod.json"))
    pod.register_capability("rls.status.read", lambda params: orb.status(), required_scope="rls.status.read")
    pod.register_capability("rls.timeline.read", lambda params: orb.timeline(tensor=params.get("tensor")), required_scope="rls.timeline.read")
    pod.register_capability("rls.lineage.read", lambda params: orb.cross_tensor_lineage(params["record_id"]), required_scope="rls.lineage.read")
    pod.register_capability("rls.reflection.replay", lambda params: orb.reflection_packet(), required_scope="rls.reflection.replay")
    pod.attach(load_fixture("r0-rls-capability-orb.json"), load_fixture("r0-rls-umbilical.json"))
    pod.enable("rls-coordinate-orb")
    result = pod.dispatch({"caller": "r0-test", "orb_id": "rls-coordinate-orb", "capability": "rls.reflection.replay", "parameters": {}, "authority": {"scopes": ["rls.reflection.replay"]}})
    assert result["result"]["packet_type"] == "rls_structural_reflection_packet"
    assert all(value is False for value in result["boundaries"].values())
