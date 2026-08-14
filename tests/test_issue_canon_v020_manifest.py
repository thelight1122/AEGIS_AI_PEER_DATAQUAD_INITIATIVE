import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.issue_canon_v020_manifest import IssuanceError, issue, main


def write_json(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def ruled_inputs(tmp_path):
    corpus = tmp_path / "canon"
    corpus.mkdir()
    (corpus / "kernel.md").write_text("stable kernel\n", encoding="utf-8")
    (corpus / "addendum.md").write_text("active addendum\n", encoding="utf-8")
    index = {
        "canon_dir": str(corpus),
        "entries": [{"file": "kernel.md"}, {"file": "addendum.md"}, {"file": "nature-v2.md"}],
        "collisions": {"code_claimed_twice_unresolved": {}},
        "dangling_references": {"Shadow Effects.md": "historical typo"},
    }
    rulings = {
        "canon_version": "v0.20",
        "ruling_status": "approved",
        "documents": {
            "kernel.md": {"coordinate": "AEGIS:CANON:KERNEL", "classification": "KERNEL", "status": "LOCKED", "seeded": True, "provenance": {"ruling": "S-1"}},
            "addendum.md": {"coordinate": "AEGIS:CANON:ADDENDUM:A", "classification": "ADDENDUM", "status": "ACTIVE", "seeded": True, "provenance": {"ruling": "S-1"}, "supersession": ["AEGIS:CANON:KERNEL"]},
            "nature-v2.md": {"coordinate": "AEGIS:NATURE-LAYER-CANON:v2", "classification": "EXCLUDED_LOCATOR_UNRESOLVED", "status": "EXCLUDED", "seeded": False, "provenance": {"ruling": "Steward recommendation 1"}, "locator_unresolved": True, "exclusion_reason": "locator_unresolved_excluded_from_seeded_bytes"},
        },
        "references": {"Shadow Effects.md": {"disposition": "corrected", "coordinate": "AEGIS:CANON:ADDENDUM:A", "note": "Shadow Affects"}},
    }
    return write_json(tmp_path / "index.json", index), write_json(tmp_path / "rulings.json", rulings), corpus, rulings


def test_issues_canonical_deterministic_manifest(ruled_inputs):
    index, rulings, _, _ = ruled_inputs
    first = issue(index, rulings)
    second = issue(index, rulings)
    assert first == second
    assert first["reviewNeededSourceCount"] == 0
    assert [e["coordinate"] for e in first["entries"]] == sorted(e["coordinate"] for e in first["entries"])
    assert first["manifest_digest"] == hashlib.sha256(
        (json.dumps({k: v for k, v in first.items() if k != "manifest_digest"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    nature = next(e for e in first["entries"] if e["coordinate"] == "AEGIS:NATURE-LAYER-CANON:v2")
    assert nature["digest"] is None and nature["seeded"] is False


@pytest.mark.parametrize("mutation,match", [
    (lambda i, r: r["documents"].pop("addendum.md"), "unruled"),
    (lambda i, r: r["documents"]["addendum.md"].update(status="UNDECLARED"), "undeclared"),
    (lambda i, r: i["collisions"]["code_claimed_twice_unresolved"].update(A=[1, 2]), "collision"),
    (lambda i, r: r["references"].clear(), "dangling references"),
    (lambda i, r: r["documents"]["addendum.md"].update(supersession=["AEGIS:MISSING"]), "dangling supersession"),
    (lambda i, r: r["documents"]["nature-v2.md"].update(seeded=True), "unresolved required locator"),
])
def test_fail_closed_ruling_defects(ruled_inputs, mutation, match):
    index_path, rulings_path, _, rulings = ruled_inputs
    index = json.loads(index_path.read_text())
    changed = copy.deepcopy(rulings)
    mutation(index, changed)
    write_json(index_path, index)
    write_json(rulings_path, changed)
    with pytest.raises(IssuanceError, match=match):
        issue(index_path, rulings_path)


def test_refuses_merge_markers(ruled_inputs):
    index, rulings, corpus, _ = ruled_inputs
    (corpus / "addendum.md").write_text("<<<<<<< ours\n=======\n>>>>>>> theirs\n")
    with pytest.raises(IssuanceError, match="merge marker"):
        issue(index, rulings)


def test_refuses_asserted_digest_mismatch(ruled_inputs):
    index, rulings_path, _, rulings = ruled_inputs
    rulings["documents"]["kernel.md"]["digest"] = "0" * 64
    write_json(rulings_path, rulings)
    with pytest.raises(IssuanceError, match="digest mismatch"):
        issue(index, rulings_path)


def test_emit_only_writes_nothing(ruled_inputs, tmp_path, capsys):
    index, rulings, _, _ = ruled_inputs
    output = tmp_path / "must-not-exist.json"
    assert main(["--index", str(index), "--rulings", str(rulings), "--output", str(output), "--emit-only"]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["manifest_id"] == "AEGIS:CANON:v0.20:SOURCE-MANIFEST"
