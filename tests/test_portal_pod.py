import json
from pathlib import Path

import jsonschema
import pytest

from aegis_pod.portal_pod.runtime import NormalizedInvocation, PortalPod, PortalPodError, contract_hash


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


def test_p0_contracts_validate_and_authority_intersects():
    pod = load("p0-portal-pod.json")
    orb = load("p0-mcp-protocol-orb.json")
    umbilical = load("p0-mcp-umbilical.json")
    for schema_name, document in (
        ("portal-pod.schema.json", pod),
        ("protocol-orb.schema.json", orb),
        ("portal-umbilical.schema.json", umbilical),
    ):
        jsonschema.validate(document, json.loads((ROOT / "contracts" / schema_name).read_text(encoding="utf-8")))
    portal = PortalPod(pod)
    portal.register_capability("retrieve_context", lambda params: {"records": [{"id": "fixture-peer-0001"}], "query": params}, required_scope="pod.context.read")
    attachment = portal.attach(orb, umbilical)
    assert attachment["attached"] is False
    assert attachment["effective_capabilities"] == ["pod_get_status", "query_continuity", "request_reflection", "retrieve_canon", "retrieve_context"]
    portal.enable(orb["orb_id"])
    result = portal.dispatch(NormalizedInvocation.from_dict({
        "caller": "local-canary",
        "orb_id": orb["orb_id"],
        "capability": "retrieve_context",
        "parameters": {"query": "", "limit": 1},
        "authority": {"scopes": ["pod.context.read"]},
        "session_id": "p0-test-session",
    }))
    assert result["result"]["records"][0]["id"] == "fixture-peer-0001"
    assert all(value is False for value in result["boundaries"].values())


def test_p0_denies_scope_not_in_intersection():
    portal = PortalPod(load("p0-portal-pod.json"))
    portal.register_capability("retrieve_context", lambda params: {}, required_scope="pod.context.read")
    portal.attach(load("p0-mcp-protocol-orb.json"), load("p0-mcp-umbilical.json"))
    portal.enable("mcp-protocol-orb")
    with pytest.raises(PortalPodError, match="required scope"):
        portal.dispatch({"caller": "test", "orb_id": "mcp-protocol-orb", "capability": "retrieve_context", "parameters": {}, "authority": {"scopes": ["pod.canon.read"]}})


def test_p0_rejects_enabled_or_mutating_orb():
    portal = PortalPod(load("p0-portal-pod.json"))
    orb = load("p0-mcp-protocol-orb.json")
    orb["enabled"] = True
    with pytest.raises(PortalPodError, match="attach disabled"):
        portal.attach(orb, load("p0-mcp-umbilical.json"))
    orb["enabled"] = False
    umbilical = load("p0-mcp-umbilical.json")
    umbilical["mutation_authority"] = True
    with pytest.raises(PortalPodError, match="mutating authority"):
        portal.attach(orb, umbilical)


def test_contract_hash_is_stable():
    documents = [load("p0-portal-pod.json"), load("p0-mcp-protocol-orb.json"), load("p0-mcp-umbilical.json")]
    assert contract_hash(*documents) == contract_hash(*documents)
