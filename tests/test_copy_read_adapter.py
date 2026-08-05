import json
import os
import stat
from pathlib import Path

import pytest

from aegis_pod.copy_read_adapter import AdapterBoundaryError, observe


def _write_copy(root: Path) -> Path:
    records = {
        "PEER": {"id": "peer-1", "body": "present signal"},
        "PCT": {"id": "pct-1", "body": "persistent thread"},
        "NCT": {"id": "nct-1", "body": "condensed essence"},
        "SPINE": {"id": "spine-1", "body": "sovereign continuity"},
    }
    for tensor, record in records.items():
        (root / f"{tensor}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    for path in root.iterdir():
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    hashes = root.parent / "expected.sha256"
    lines = []
    import hashlib

    for tensor in ("PEER", "PCT", "NCT", "SPINE"):
        digest = hashlib.sha256((root / f"{tensor}.jsonl").read_bytes()).hexdigest()
        lines.append(f"{digest}  {tensor}.jsonl")
    hashes.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return hashes


def test_observe_is_bounded_and_not_admitted(tmp_path: Path) -> None:
    source = tmp_path / "copy"
    source.mkdir()
    expected = _write_copy(source)
    report = observe(
        source,
        expected,
        query="persistent",
        limit=1,
        approved_root=source.parent,
        require_immutable=False,
    )
    assert report["query"]["match_count"] == 1
    assert report["observations"][0]["admission_status"] == "not_admitted"
    assert report["boundary"]["experience_created"] is False


def test_rejects_extra_file(tmp_path: Path) -> None:
    source = tmp_path / "copy"
    source.mkdir()
    expected = _write_copy(source)
    extra = source / "ledger.jsonl"
    extra.write_text("{}\n", encoding="utf-8")
    extra.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    with pytest.raises(AdapterBoundaryError, match="unexpected source files"):
        observe(source, expected, approved_root=source.parent, require_immutable=False)


@pytest.mark.skipif(os.name == "nt", reason="Windows chmod does not reliably set directory write bits")
def test_rejects_writable_copy(tmp_path: Path) -> None:
    source = tmp_path / "copy"
    source.mkdir()
    expected = _write_copy(source)
    os.chmod(source, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    with pytest.raises(AdapterBoundaryError, match="source root is writable"):
        observe(source, expected)
