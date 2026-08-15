import json
from pathlib import Path

from scripts.build_canon_v020_candidate import build


ROOT = Path(__file__).resolve().parents[1]


def test_candidate_builder_reads_index_and_emits_only_review_needed(tmp_path):
    corpus = tmp_path / "canon"
    corpus.mkdir()
    (corpus / "kernel.md").write_text("foundation\n", encoding="utf-8")
    index = {
        "canon_dir": str(corpus),
        "collisions": {"code_claimed_twice_unresolved": {}},
        "dangling_references": {},
        "entries": [{"file": "kernel.md", "class": "KERNEL", "status_declared": "LOCKED"}],
    }
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")
    out = tmp_path / "candidate"
    report = build(index_path, ROOT / "fixtures" / "historical-foundation-seed.fixture.json", out)
    manifest = json.loads((out / "canon-v0.20-candidate-manifest.json").read_text())
    seed = json.loads((out / "ai-peer-foundation-seed-v0.20-candidate.json").read_text())
    assert report["artifact_status"] == "candidate-review-needed"
    assert manifest["open_gate_ids"] == []
    assert seed["canonLock"]["status"] == "review-needed"
    assert seed["canonLock"]["sourceManifestSha256"] == report["manifest_digest_bound_in_seed"]
    assert not any(path.name == "clean" for path in out.rglob("*"))


def test_final_steward_rulings_are_applied_to_candidate_documents(tmp_path):
    from scripts.build_canon_v020_candidate import derive_candidate_rulings

    names = [
        "📘 AEGIS CANON ADDENDUM INDEX.md",
        "AEGIS_CANON_CORE.md",
        "AEGIS_ALIGNMENT_WHITEPAPER_v1.0.md",
        "AEGIS_WHITEPAPER_v2.1.md",
        "AEGIS Canonical Glossary v1.0.md",
        "GLOSSARY.md",
    ]
    for name in names:
        (tmp_path / name).write_text("candidate\n", encoding="utf-8")
    index = {
        "canon_dir": str(tmp_path),
        "entries": [
            {"file": name, "class": "UNINDEXED", "status_declared": "UNDECLARED"}
            for name in names
        ],
    }
    rulings = derive_candidate_rulings(index)
    assert rulings["open_gate_ids"] == []
    assert rulings["documents"]["📘 AEGIS CANON ADDENDUM INDEX.md"]["status"] == "AUTHORITATIVE"
    core = rulings["documents"]["AEGIS_CANON_CORE.md"]
    assert core["status"] == "PROPOSED"
    assert core["invariant_relationship"] == {
        "axiom_count": 16,
        "invariant_count": 12,
        "relationship": "subordinate_operational_summary",
        "authority": "steward-ruling-S-5",
    }
    assert rulings["documents"]["AEGIS_WHITEPAPER_v2.1.md"]["classification"] == "POSITIONING"
    assert rulings["documents"]["AEGIS Canonical Glossary v1.0.md"]["status"] == "FOUNDATIONAL_GLOSSARY"
    assert rulings["documents"]["GLOSSARY.md"]["status"] == "SCOPED_ACTIVE"


def test_final_classification_table_and_standards_alias_are_exact(tmp_path):
    from scripts.build_canon_index import FINAL_CLASSIFICATION_TABLE, scan
    from scripts.build_canon_v020_candidate import derive_candidate_rulings

    entries = []
    for name, _classification, _status in FINAL_CLASSIFICATION_TABLE:
        (tmp_path / name).write_text("candidate\n", encoding="utf-8")
        entries.append({"file": name, "class": "UNINDEXED", "status_declared": "UNDECLARED"})
    rulings = derive_candidate_rulings({"canon_dir": str(tmp_path), "entries": entries})
    for name, classification, status in FINAL_CLASSIFICATION_TABLE:
        decision = rulings["documents"][name]
        assert (decision["classification"], decision["status"], decision["review_required"]) == (
            classification, status, False
        )
    canonical = rulings["documents"]["AEGIS STANDARDS v0.1.md"]
    alias = rulings["documents"]["AEGIS STANDARDS V1.0.md"]
    assert canonical["coordinate"] == "AEGIS:CANON:STANDARD:STANDARDS:v0.1"
    assert canonical["seeded"] is True
    assert alias["alias_of"] == canonical["coordinate"]
    assert alias["canonical_identity"] == canonical["coordinate"]
    assert alias["seeded"] is False
    indexed = {entry["file"]: entry for entry in scan(tmp_path)}
    for name, classification, status in FINAL_CLASSIFICATION_TABLE:
        assert indexed[name]["ruling_classification"] == classification
        assert indexed[name]["ruling_status"] == status
