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
    assert manifest["open_gate_ids"] == ["G-1", "S-2", "S-4", "S-5", "S-6"]
    assert seed["canonLock"]["status"] == "review-needed"
    assert seed["canonLock"]["sourceManifestSha256"] == report["manifest_digest_bound_in_seed"]
    assert not any(path.name == "clean" for path in out.rglob("*"))
