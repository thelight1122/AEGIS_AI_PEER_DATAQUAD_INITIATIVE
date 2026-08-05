"""Stage 4 coverage: validate_attachment() now gates on schema conformance,
declared Orb version, and pinned runtime_hash — not just id-equality/path
checks, and not just post-hoc evidence. Before this, a mismatched version,
tampered source, or malformed contract would all silently pass attachment.
"""
import copy
from pathlib import Path

import jsonschema
import pytest

from src.aegis_pod.orb_runtime import load_json, validate_attachment

ROOT = Path(__file__).resolve().parents[1]

# Requires: pip install -e packages/aegis-pod-sdk -e packages/orb-rls-persistent-relations-core
# (importlib.metadata.version() needs real install metadata, not just sys.path).


def _real_orion_contracts():
    base = ROOT / "stage-d-out" / "CP-1004-ORION" / "pod"
    pod = load_json(base / "pod-manifest.json")
    orb = load_json(base / "provenance" / "rls-persistent-relations-core.orb.json")
    umbilical = load_json(base / "provenance" / "rls-persistent-relations-umbilical.json")
    return pod, orb, umbilical


def test_real_orion_contracts_pass_with_matching_version_and_hash():
    pod, orb, umbilical = _real_orion_contracts()
    attachment = validate_attachment(ROOT, pod, orb, umbilical)
    assert attachment.orb_id == "rls-persistent-relations-core"


def test_rejects_version_mismatch():
    pod, orb, umbilical = _real_orion_contracts()
    orb = copy.deepcopy(orb)
    orb["runtime"]["package"]["version_spec"] = "==99.0.0"
    with pytest.raises(ValueError, match="does not satisfy"):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_rejects_hash_mismatch():
    pod, orb, umbilical = _real_orion_contracts()
    umbilical = copy.deepcopy(umbilical)
    umbilical["invocation"]["orb_runtime_hash"] = "0" * 64
    with pytest.raises(ValueError, match="runtime_hash mismatch"):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_rejects_uninstalled_package():
    pod, orb, umbilical = _real_orion_contracts()
    orb = copy.deepcopy(orb)
    orb["runtime"]["package"]["name"] = "this-package-does-not-exist-anywhere"
    with pytest.raises(ValueError, match="is not installed"):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_rejects_malformed_orb_contract():
    pod, orb, umbilical = _real_orion_contracts()
    orb = copy.deepcopy(orb)
    del orb["purpose"]  # required by contracts/orb.schema.json
    with pytest.raises(jsonschema.ValidationError):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_rejects_malformed_umbilical_contract():
    pod, orb, umbilical = _real_orion_contracts()
    umbilical = copy.deepcopy(umbilical)
    del umbilical["attachment_point"]  # required by contracts/umbilical.schema.json
    with pytest.raises(jsonschema.ValidationError):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_rejects_malformed_pod_contract():
    pod, orb, umbilical = _real_orion_contracts()
    pod = copy.deepcopy(pod)
    del pod["peer_id"]  # required by contracts/pod.schema.json
    with pytest.raises(jsonschema.ValidationError):
        validate_attachment(ROOT, pod, orb, umbilical)


def test_missing_package_field_is_a_noop_skip():
    """An Orb with no runtime.package (not yet extracted, still source-merged)
    will be unaffected by the new gate — same fixture-orb path as before."""
    pod = load_json(ROOT / "fixtures" / "local-cyberpeer-pod.json")
    orb = load_json(ROOT / "fixtures" / "rls-orb.json")
    umbilical = load_json(ROOT / "fixtures" / "rls-orb-umbilical.json")
    attachment = validate_attachment(ROOT, pod, orb, umbilical)
    assert attachment.orb_id == "rls-orb-fixture"
