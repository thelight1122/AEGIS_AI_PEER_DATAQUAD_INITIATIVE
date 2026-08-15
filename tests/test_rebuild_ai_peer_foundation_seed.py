from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rebuilder", ROOT / "scripts" / "rebuild_ai_peer_foundation_seed.py")
rebuilder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rebuilder)


def inputs():
    manifest_path = ROOT / "fixtures" / "v020-clean-manifest.fixture.json"
    seed_path = ROOT / "fixtures" / "historical-foundation-seed.fixture.json"
    raw = manifest_path.read_bytes()
    return json.loads(raw), raw, json.loads(seed_path.read_bytes())


def test_clean_lock_is_derived_and_manifest_digest_is_bound():
    manifest, raw, seed = inputs()
    out = rebuilder.rebuild(manifest, raw, seed)
    assert out["canonLock"] == {
        "derivation": "computed-from-v0.20-manifest",
        "reviewNeededSourceCount": 0,
        "sourceManifestId": manifest["manifestId"],
        "sourceManifestSha256": rebuilder.sha256_bytes(raw),
        "status": "clean",
    }
    assert seed["canonLock"]["status"] == "review-needed"


def test_records_preserved_with_16_axioms_correct_spine_and_no_ring4():
    manifest, raw, seed = inputs()
    out = rebuilder.rebuild(manifest, raw, seed)
    assert out["records"] == seed["records"]
    assert rebuilder._collect_axioms(out["records"]) == set(range(1, 17))
    assert rebuilder.SPINE_NAME in json.dumps(out["records"])
    assert out["foundationContract"]["ringOrder"] == [1, 2, 3]
    assert out["foundationContract"]["ring4Included"] is False


def test_memory_not_command_nature_provenance_and_promotion_boundaries():
    manifest, raw, seed = inputs()
    out = rebuilder.rebuild(manifest, raw, seed)
    assert out["foundationContract"]["memoryNotCommand"] is True
    assert out["foundationContract"]["executionAuthority"] == "none"
    assert out["natureProvenanceContract"]["substrateBindingRequired"] is True
    assert out["natureProvenanceContract"]["contentEqualityAcrossSubstratesRequired"] is False
    assert out["promotionBoundary"] == {
        "keysStatus": "deferred", "liveCredentialsStatus": "absent",
        "promotionAuthorized": False, "tumblersStatus": "deferred",
    }


@pytest.mark.parametrize("mutation", [
    lambda m: m.update(reviewNeededSourceCount=1),
    lambda m: m["sources"][0].update(canonLockStatus="review-needed"),
    lambda m: m["sources"][0].pop("sha256"),
])
def test_unclean_or_unresolved_manifest_is_refused(mutation):
    manifest, raw, seed = inputs()
    mutation(manifest)
    with pytest.raises(rebuilder.RebuildRefused):
        rebuilder.rebuild(manifest, raw, seed)


@pytest.mark.parametrize("field", ["api_token", "keys", "credentials", "tumblers"])
def test_ring4_and_credentials_are_refused(field):
    manifest, raw, seed = inputs()
    ring4 = copy.deepcopy(seed)
    ring4["records"]["EXPERIENCE"] = []
    with pytest.raises(rebuilder.RebuildRefused, match="Ring-4"):
        rebuilder.rebuild(manifest, raw, ring4)
    credential = copy.deepcopy(seed)
    credential[field] = {"material": "not-allowed"}
    with pytest.raises(rebuilder.RebuildRefused, match="credential"):
        rebuilder.rebuild(manifest, raw, credential)


def test_canonical_output_is_deterministic_and_cli_writes_only_requested_output(tmp_path):
    manifest, raw, seed = inputs()
    first = rebuilder.canonical_bytes(rebuilder.rebuild(manifest, raw, seed))
    second = rebuilder.canonical_bytes(rebuilder.rebuild(manifest, raw, seed))
    assert first == second
    parsed = json.loads(first)
    assert list(parsed) == sorted(parsed)


def candidate_manifest():
    manifest, _, seed = inputs()
    manifest["issuance_status"] = "candidate"
    manifest["canon_lock_status"] = "review-needed"
    manifest["open_gate_ids"] = ["S-2", "S-4", "S-5", "S-6", "G-1"]
    manifest["reviewNeededSourceCount"] = 5
    raw = rebuilder.canonical_bytes(manifest)
    return manifest, raw, seed


def test_candidate_seed_remains_review_needed_and_binds_manifest():
    manifest, raw, seed = candidate_manifest()
    out = rebuilder.rebuild(manifest, raw, seed, candidate=True)
    assert out["canonLock"]["status"] == "review-needed"
    assert out["canonLock"]["openGateIds"] == ["G-1", "S-2", "S-4", "S-5", "S-6"]
    assert out["canonLock"]["sourceManifestSha256"] == rebuilder.sha256_bytes(raw)
    assert out["foundationContract"]["memoryNotCommand"] is True
    assert out["foundationContract"]["ring4Included"] is False


def test_candidate_seed_with_closed_governance_gates_stays_review_needed():
    manifest, _, seed = candidate_manifest()
    manifest["open_gate_ids"] = []
    manifest["reviewNeededSourceCount"] = 0
    raw = rebuilder.canonical_bytes(manifest)
    out = rebuilder.rebuild(manifest, raw, seed, candidate=True)
    assert out["canonLock"]["status"] == "review-needed"
    assert out["canonLock"]["openGateIds"] == []


def test_candidate_manifest_cannot_reach_clean_lock_path():
    manifest, raw, seed = candidate_manifest()
    with pytest.raises(rebuilder.RebuildRefused, match="clean-lock path is unavailable"):
        rebuilder.rebuild(manifest, raw, seed)
