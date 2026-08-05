import json
from pathlib import Path

import jsonschema
import pytest

from aegis_pod.portal_contract import authorize, load_manifest


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "phase1c-test-token"


def manifest() -> dict:
    return load_manifest(ROOT / "fixtures" / "phase1c-portal-manifest.json")


def test_read_only_capability_requires_authentication() -> None:
    decision = authorize(manifest(), method="retrieve_context", bearer_token=TOKEN, limit=10)
    assert decision.allowed is True
    assert authorize(manifest(), method="retrieve_context", bearer_token="wrong").allowed is False
    assert authorize(manifest(), method="retrieve_context", bearer_token=None).allowed is False


def test_disabled_and_unknown_methods_fail_closed() -> None:
    assert authorize(manifest(), method="record_experience", bearer_token=TOKEN).allowed is False
    assert authorize(manifest(), method="shell", bearer_token=TOKEN).allowed is False


def test_reflection_is_replay_only_and_continuity_is_scoped() -> None:
    assert authorize(manifest(), method="request_reflection", bearer_token=TOKEN, reflection_mode="live").allowed is False
    assert authorize(manifest(), method="request_reflection", bearer_token=TOKEN, reflection_mode="replay_only").allowed is True
    assert authorize(manifest(), method="query_continuity", bearer_token=TOKEN).allowed is False
    assert authorize(manifest(), method="query_continuity", bearer_token=TOKEN, continuity_scope="observed").allowed is True


def test_result_bounds_fail_closed() -> None:
    assert authorize(manifest(), method="retrieve_context", bearer_token=TOKEN, limit=0).allowed is False
    assert authorize(manifest(), method="retrieve_context", bearer_token=TOKEN, limit=51).allowed is False


def test_manifest_rejects_duplicate_or_unknown_capabilities(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    value = manifest()
    value["capabilities"][-1]["method"] = "retrieve_context"
    path.write_text(json.dumps(value), encoding="utf-8")
    try:
        load_manifest(path)
    except ValueError as exc:
        assert "exactly once" in str(exc)
    else:
        raise AssertionError("duplicate capability was accepted")

    value = manifest()
    value["capabilities"][-1]["method"] = "arbitrary_python"
    path.write_text(json.dumps(value), encoding="utf-8")
    try:
        load_manifest(path)
    except ValueError as exc:
        assert "exactly once" in str(exc)
    else:
        raise AssertionError("unknown capability was accepted")


def test_schema_enforces_exactly_one_of_each_method(tmp_path: Path) -> None:
    value = manifest()
    value["capabilities"][-1]["method"] = "retrieve_context"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(value, json.loads((ROOT / "contracts" / "portal.schema.json").read_text()))
