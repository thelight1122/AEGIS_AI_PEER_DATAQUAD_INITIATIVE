import json

from aegis_pod.mcp_gateway import McpGateway


class FakePortal:
    def __init__(self):
        self.requests = []

    def health(self):
        return {"status": "ok"}

    def post(self, path, payload):
        self.requests.append((path, payload))
        return {"authorized": True, "mutation_performed": False, "admission": False}


def test_gateway_exposes_only_read_replay_tools():
    portal = FakePortal()
    gateway = McpGateway(portal)
    response = gateway.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = [tool["name"] for tool in response["result"]["tools"]]
    assert names == ["pod_retrieve_context", "pod_retrieve_canon", "pod_query_continuity", "pod_request_reflection", "pod_get_status"]
    assert "record_experience" not in names


def test_gateway_maps_context_without_reading_dataquad():
    portal = FakePortal()
    gateway = McpGateway(portal)
    result = gateway.call_tool("pod_retrieve_context", {"query": "", "limit": 1})
    assert result["authorized"] is True
    assert portal.requests == [("/v1/portal/execute", {"method": "retrieve_context", "query": "", "limit": 1, "caller": "frontier_gateway"})]


def test_gateway_fails_closed_for_writes_and_invalid_scopes():
    gateway = McpGateway(FakePortal())
    error = gateway.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "record_experience", "arguments": {}}})
    assert error["result"]["isError"] is True
    try:
        gateway.call_tool("pod_query_continuity", {"scope": "admitted"})
    except ValueError as exc:
        assert "observed" in str(exc)
    else:
        raise AssertionError("admitted scope unexpectedly accepted")
