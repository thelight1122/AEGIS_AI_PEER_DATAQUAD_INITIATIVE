"""P1 — Lumin GPT Action Orb behaviour.

The Action Orb defines how the Lumin substrate communicates. It holds no authority of its
own: it normalizes a request, presents exactly one scope, and lets the Portal Pod decide.
These tests check both halves — that the Orb refuses what it should never forward, and that
the Portal refuses what the Orb cannot authorize.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from aegis_pod.lumin_action_orb import (
    OPERATION_TO_CAPABILITY,
    OPERATION_TO_SCOPE,
    PROHIBITED_SCOPES,
    RETIRED_OPERATIONS,
    ActionOrbError,
    LuminActionOrb,
    refuse_retired,
)
from aegis_pod.portal_pod.runtime import PortalPod, PortalPodError

ROOT = Path(__file__).resolve().parents[1]
ACTION_CONTRACT = ROOT / "contracts" / "p1-lumin-gpt-action.openapi.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def portal() -> PortalPod:
    pod = PortalPod(_load(ROOT / "fixtures" / "p0-portal-pod.json"))
    pod.register_capability("retrieve_context", lambda p: {"records": [{"id": "fixture-peer-0001"}]}, required_scope="pod.context.read")
    pod.register_capability("retrieve_canon", lambda p: {"records": []}, required_scope="pod.canon.read")
    pod.register_capability("query_continuity", lambda p: {"coordinates": []}, required_scope="pod.continuity.observed.read")
    pod.register_capability("request_reflection", lambda p: {"packet": {}}, required_scope="pod.reflection.replay")
    pod.register_capability("pod_get_status", lambda p: {"pod_id": "aegis-portal-pod-local"}, required_scope="pod.status.read")
    return pod


@pytest.fixture
def attached(portal: PortalPod) -> LuminActionOrb:
    orb_manifest = _load(ROOT / "fixtures" / "p1-gpt-action-orb.json")
    umbilical = _load(ROOT / "fixtures" / "p1-gpt-action-umbilical.json")
    portal.attach(orb_manifest, umbilical)
    portal.enable(orb_manifest["orb_id"])
    return LuminActionOrb(portal)


# --- The retired write endpoint -------------------------------------------------------


def test_append_event_is_retired_with_no_replacement():
    assert "appendEvent" in RETIRED_OPERATIONS
    entry = RETIRED_OPERATIONS["appendEvent"]
    assert entry["path"] == "/api/live-bridge/events"
    assert entry["replacement"] is None


def test_calling_the_retired_operation_raises_and_says_why(attached: LuminActionOrb):
    with pytest.raises(ActionOrbError, match="retired"):
        attached.call("appendEvent", {"event": "anything"})


def test_refuse_retired_is_a_no_op_for_live_operations():
    for operation in OPERATION_TO_CAPABILITY:
        refuse_retired(operation)  # must not raise


def test_retired_operation_absent_from_the_published_schema():
    contract = _load(ACTION_CONTRACT)
    operations = {spec["operationId"] for verbs in contract["paths"].values() for spec in verbs.values()}
    assert "appendEvent" not in operations
    assert "/api/live-bridge/events" not in contract["paths"]


def test_retirement_is_recorded_in_the_schema_not_merely_omitted():
    """An absent endpoint and a retired endpoint look identical unless the retirement is stated."""
    contract = _load(ACTION_CONTRACT)
    retired = contract["x-aegis-retired"]["retired_operations"]
    assert any(entry["operationId"] == "appendEvent" and entry["replacement"] is None for entry in retired)


# --- Mapping --------------------------------------------------------------------------


def test_runtime_and_schema_agree_on_operations_and_scopes():
    contract = _load(ACTION_CONTRACT)
    operations = {spec["operationId"] for verbs in contract["paths"].values() for spec in verbs.values()}
    assert set(OPERATION_TO_CAPABILITY) == operations
    assert OPERATION_TO_SCOPE == contract["x-aegis-operation-scopes"]


def test_no_operation_maps_to_a_prohibited_scope():
    assert not set(OPERATION_TO_SCOPE.values()) & PROHIBITED_SCOPES


def test_orb_manifest_protocol_matches_the_contract_enum():
    manifest = _load(ROOT / "fixtures" / "p1-gpt-action-orb.json")
    schema = _load(ROOT / "contracts" / "protocol-orb.schema.json")
    jsonschema.validate(manifest, schema)
    assert manifest["protocol"] == "gpt_action"
    assert manifest["enabled"] is False


# --- Dispatch behaviour ----------------------------------------------------------------


@pytest.mark.parametrize("operation", sorted(OPERATION_TO_CAPABILITY))
def test_every_operation_dispatches_with_all_boundaries_false(attached: LuminActionOrb, operation: str):
    result = attached.call(operation, {})
    assert all(value is False for value in result["boundaries"].values())


def test_unknown_operation_is_refused(attached: LuminActionOrb):
    with pytest.raises(ActionOrbError, match="unknown"):
        attached.call("recordExperience", {})


def test_action_orb_presents_only_its_own_scope(attached: LuminActionOrb):
    """A caller cannot widen authority by supplying extra scopes; the Orb sets the scope."""
    result = attached.call("retrieveContext", {"query": "", "limit": 1})
    assert result["result"]["records"][0]["id"] == "fixture-peer-0001"


def test_write_capability_is_refused_through_the_action_orb(portal: PortalPod):
    orb_manifest = _load(ROOT / "fixtures" / "p1-gpt-action-orb.json")
    umbilical = _load(ROOT / "fixtures" / "p1-gpt-action-umbilical.json")
    portal.attach(orb_manifest, umbilical)
    portal.enable(orb_manifest["orb_id"])
    with pytest.raises(PortalPodError):
        portal.dispatch(
            {
                "caller": "lumin-gpt",
                "orb_id": orb_manifest["orb_id"],
                "capability": "record_experience",
                "parameters": {},
                "authority": {"scopes": ["pod.experience.write"]},
            }
        )


def test_a_mutating_umbilical_cannot_attach_the_action_orb(portal: PortalPod):
    umbilical = _load(ROOT / "fixtures" / "p1-gpt-action-umbilical.json")
    umbilical["mutation_authority"] = True
    with pytest.raises(PortalPodError, match="mutating authority"):
        portal.attach(_load(ROOT / "fixtures" / "p1-gpt-action-orb.json"), umbilical)


def test_describe_reports_retirement_and_boundaries(attached: LuminActionOrb):
    described = attached.describe()
    assert described["protocol"] == "gpt_action"
    assert "appendEvent" in described["retired_operations"]
    assert all(value is False for value in described["boundaries"].values())
    assert set(described["operations"]) == set(OPERATION_TO_CAPABILITY)


def test_contract_declares_every_boundary_false():
    contract = _load(ACTION_CONTRACT)
    assert all(value is False for value in contract["x-aegis-boundary"].values())
    assert contract["x-aegis-boundary"]["listener_enabled"] is False
