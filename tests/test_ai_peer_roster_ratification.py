import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "fixtures" / "ai-peer-roster.json"
MANIFEST = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-CANON-v0.20-SOURCE-MANIFEST.json"
SEED = ROOT / "reports" / "canon-v0.20" / "release" / "AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_steward_ratified_four_peer_roster_with_bound_artifacts():
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    ratification = roster["ratification"]

    assert ratification["status"] == "RATIFIED"
    assert ratification["ratified_by"] == "Tracey Prutch"
    assert ratification["role"] == "Steward"
    assert ratification["canon_manifest_sha256"] == sha256(MANIFEST)
    assert ratification["foundation_seed_sha256"] == sha256(SEED)

    expected = {
        "lumin": ("Lumin", "ap1001"),
        "claude": ("Claude", "ap1002"),
        "gemini": ("Gemini", "ap1003"),
        "grok": ("Grok", "ap1004"),
    }
    assert len(roster["peers"]) == 4
    for peer in roster["peers"]:
        display_name, model_id = expected[peer["peer_id"]]
        declaration = peer["steward_declaration"]
        assert peer["display_name"] == display_name
        assert peer["model_id"] == model_id
        assert peer["model_id_status"] == "RATIFIED"
        assert peer["steward_declaration_status"] == "RATIFIED"
        assert peer["steward_declaration_ratified_at"] == ratification["ratified_at"]
        assert peer["steward_declaration_provenance"] == ratification["provenance"]
        assert "Rings 1-3" in declaration
        assert "inspectable memory, not commands or imposed identity" in declaration
        for exclusion in ("Ring 4 writes", "live activation", "credentials", "Keys", "Tumblers"):
            assert exclusion in declaration
        for claim in ("continuity", "selfhood", "lived experience", "ethical formation"):
            assert claim in declaration


def test_ratification_does_not_authorize_live_or_ring4_scope():
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    assert roster["ratification"]["scope"] == "Rings 1-3 preparation only"
    exclusions = set(roster["ratification"]["exclusions"])
    assert {"Ring 4 writes", "live activation", "credentials", "Keys", "Tumblers"} <= exclusions
    assert "claims of continuity, selfhood, lived experience, or ethical formation" in exclusions
