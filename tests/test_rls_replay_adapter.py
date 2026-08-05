import hashlib
import json
import stat
from pathlib import Path

import pytest

from aegis_pod.rls_replay_adapter import RLSReplayBoundaryError, replay


def _source(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "approved"
    root.mkdir()
    source = root / "rls-ledger.jsonl"
    source.write_text(json.dumps({
        "event": "rls-recursive-reflection",
        "record": {
            "type": "RLS",
            "id": "RLS:test:1",
            "timestamp": "2026-08-02T00:00:00Z",
            "reflection": {"aspectName": "Test Aspect", "driftVisible": True},
        },
    }) + "\n", encoding="utf-8")
    manifest = root / "expected.sha256"
    manifest.write_text(f"{hashlib.sha256(source.read_bytes()).hexdigest()}  rls-ledger.jsonl\n", encoding="utf-8")
    source.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    manifest.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return root, source, manifest


def test_replay_is_observation_only(tmp_path: Path) -> None:
    root, source, manifest = _source(tmp_path)
    report = replay(source, manifest, root, "Test Aspect", 5)
    assert report["query"]["match_count"] == 1
    assert report["observations"][0]["admission_status"] == "not_admitted"
    assert report["boundary"]["writeback_performed"] is False
    assert report["source"]["source_sha256"] == report["source"]["post_replay_source_sha256"]


def test_replay_rejects_hash_drift(tmp_path: Path) -> None:
    root, source, manifest = _source(tmp_path)
    source.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    source.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    with pytest.raises(RLSReplayBoundaryError, match="hash drift"):
        replay(source, manifest, root, "", 5)
