"""Canon v0.21: v0.20 plus AXIOM 17 (The Axiom of Deletion), by addition only."""

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import issue_canon_v020_manifest as issuer  # noqa: E402
import rebuild_ai_peer_foundation_seed as rebuilder  # noqa: E402

V020 = ROOT / "reports" / "canon-v0.20" / "release"
V021 = ROOT / "reports" / "canon-v0.21" / "release"
SEALED_SHA = "00692CAB739E38A5C3B20EC44714D3417081C85BE7E743C1A2F69388148085BB"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v021_manifest_is_clean_and_adds_exactly_axiom_17():
    m20 = _load(V020 / "AEGIS-CANON-v0.20-SOURCE-MANIFEST.json")
    m21 = _load(V021 / "AEGIS-CANON-v0.21-SOURCE-MANIFEST.json")
    assert m21["canon_version"] == "v0.21"
    assert m21["manifest_id"] == "AEGIS:CANON:v0.21:SOURCE-MANIFEST"
    assert (m21["canon_lock_status"], m21["issuance_status"], m21["reviewNeededSourceCount"]) == ("clean", "authoritative", 0)
    d20 = {e["coordinate"]: e["digest"] for e in m20["entries"]}
    d21 = {e["coordinate"]: e["digest"] for e in m21["entries"]}
    added = set(d21) - set(d20)
    assert added == {"AEGIS:CANON:v0.21:AEGIS-CANON-ADDENDUM-AXIOM-17-THE-AXIOM-OF-DELETION-D-MD"}
    assert all(d21[c] == d20[c] for c in d20), "a v0.20 source changed under v0.21"


def test_v021_seed_is_v020_records_plus_one_sealed_axiom_17():
    s20 = _load(V020 / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json")
    s21 = _load(V021 / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.21.json")
    assert s21["packageId"] == "AEGIS-AI-PEER-FOUNDATION-SEED:v0.21"
    assert s21["canonLock"]["status"] == "clean"
    for tensor, records in s20["records"].items():
        assert s21["records"][tensor][: len(records)] == records
    extra = s21["records"]["SPINE"][len(s20["records"]["SPINE"]):]
    assert [r["id"] for r in extra] == ["SPINE:{{CYBERPEER_SESSION_ID}}:seeded:AXIOM:17-deletion"]
    assert hashlib.sha256(extra[0]["pattern"].encode("utf-8")).hexdigest().upper() == SEALED_SHA
    assert rebuilder._collect_axioms(s21["records"]) == set(range(1, 18))


def test_v021_rebuild_refuses_a_seed_without_axiom_17():
    s20 = _load(V020 / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json")
    with pytest.raises(rebuilder.RebuildRefused, match="Axioms 1-17"):
        rebuilder.validate_historical_seed(copy.deepcopy(s20), version="v0.21")


def test_v020_rebuild_still_requires_exactly_16():
    s20 = _load(V020 / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json")
    rebuilder.validate_historical_seed(copy.deepcopy(s20))  # default v0.20 unchanged


def test_issuer_refuses_rulings_for_another_version(tmp_path):
    rulings = _load(V020 / "canon-v0.20-authoritative-rulings.json")
    path = tmp_path / "r.json"
    path.write_text(json.dumps(rulings), encoding="utf-8")
    with pytest.raises(issuer.IssuanceError, match="must be v0.21"):
        issuer.issue(ROOT / "reports" / "canon-v0.20" / "canon-v0.20-index.json", path, canon_version="v0.21")
