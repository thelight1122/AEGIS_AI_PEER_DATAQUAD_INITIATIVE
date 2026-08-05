from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aegis_pod.retirement_dry_run import analyze, assert_local_readonly_path


# --------------------------------------------------------------------------------------
# Small synthetic in-test fixture (NOT the large stage-gabe-out copy)
# --------------------------------------------------------------------------------------
NOW = datetime(2026, 7, 22, 0, 0, 0, tzinfo=timezone.utc)


def _envelope(tensor: str, rid: str, ts: str, body: dict) -> dict:
    return {
        "record_id": rid,
        "tensor": tensor,
        "timestamp_utc": ts,
        "schema_version": "1.0",
        "source_hash": "declared-" + hashlib.sha256(rid.encode()).hexdigest()[:8],
        "source_hash_scope": "normalized_source_record",
        "source_record_id": rid,
        "migration_status": "copied",
        "verification_status": "draft",
        "lineage": {"origin": "synthetic-test"},
        "body": body,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as h:
        for r in records:
            h.write(json.dumps(r))
            h.write("\n")


@pytest.fixture()
def source_root(tmp_path: Path) -> Path:
    root = tmp_path / "records"
    root.mkdir()

    # PCT: two OLD (>14d) -> retirement candidates; one RECENT -> not a candidate.
    pct = [
        _envelope("PCT", "PCT:sy:old-condensed:1", "2026-06-28T00:00:00Z", {
            "clock": {"phase": "rls-steward", "tick": 3},
            "workingContext": {"signal": "old condensed working thought"},
            "referenceCount": 3, "retired": True,
            "retiredToId": "NCT:sy:rls-promoted:2026-06-28T15:08:13.000Z:18",
        }),
        _envelope("PCT", "PCT:sy:old-fresh:2", "2026-07-01T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 500},
            "workingContext": {"signal": "old but never condensed"},
            "referenceCount": 0,
        }),
        _envelope("PCT", "PCT:sy:recent:3", "2026-07-21T00:00:00Z", {
            "clock": {"phase": "live-session", "tick": 900},
            "workingContext": {"signal": "recent working thought"},
            "referenceCount": 2,
        }),
    ]

    # PEER records exercising each caution rule + one clean promotion candidate.
    peer = [
        # established+stable: old, duplicated (2 confirmations), not anchored/contested -> candidate
        _envelope("PEER", "PEER:sy:established-a:10", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 10},
            "presentState": {"signal": "a steady reinforced identity pattern"},
            "markers": ["inter-peer", "exchange"],
        }),
        _envelope("PEER", "PEER:sy:established-b:11", "2026-06-30T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 11},
            "presentState": {"signal": "a steady reinforced identity pattern"},
            "markers": ["inter-peer", "exchange"],
        }),
        # recent -> excluded recent_experience
        _envelope("PEER", "PEER:sy:recent:12", "2026-07-21T00:00:00Z", {
            "clock": {"phase": "live-session", "tick": 12},
            "presentState": {"signal": "a steady reinforced identity pattern"},
        }),
        # SPINE-anchored -> excluded spine_anchored (old + duplicated otherwise)
        _envelope("PEER", "PEER:sy:anchored:13", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 13},
            "presentState": {"signal": "anchored reinforced pattern"},
            "lineage": ["SPINE:sy:foundation:axiom-16"],
        }),
        _envelope("PEER", "PEER:sy:anchored-dup:14", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 14},
            "presentState": {"signal": "anchored reinforced pattern"},
            "lineage": ["SPINE:sy:foundation:axiom-16"],
        }),
        # contested -> excluded contested (old + duplicated otherwise)
        _envelope("PEER", "PEER:sy:contested:15", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 15},
            "presentState": {"signal": "a contested reinforced claim"},
            "markers": ["contested", "disputed"],
        }),
        _envelope("PEER", "PEER:sy:contested-dup:16", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 16},
            "presentState": {"signal": "a contested reinforced claim"},
            "markers": ["contested", "disputed"],
        }),
        # unique + old -> excluded high_uniqueness (only one copy of this content)
        _envelope("PEER", "PEER:sy:unique:17", "2026-06-29T00:00:00Z", {
            "clock": {"phase": "inter-peer", "tick": 17},
            "presentState": {"signal": "a singular never-repeated lived moment"},
        }),
    ]

    nct = [
        _envelope("NCT", "NCT:sy:relic:18", "2026-06-28T15:08:13.000Z", {
            "distilledSummary": "condensed relic", "referenceCount": 0, "retired": False,
        }),
    ]
    spine = [
        _envelope("SPINE", "SPINE:sy:foundation:axiom-16", "2026-06-27T00:00:00Z", {
            "pattern": "PEER is identity substrate", "invariant": True,
        }),
    ]

    _write_jsonl(root / "PCT.jsonl", pct)
    _write_jsonl(root / "PEER.jsonl", peer)
    _write_jsonl(root / "NCT.jsonl", nct)
    _write_jsonl(root / "SPINE.jsonl", spine)
    return root


def _dir_fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    fp: dict[str, tuple[int, str]] = {}
    for p in sorted(root.glob("*.jsonl")):
        data = p.read_bytes()
        fp[p.name] = (len(data), hashlib.sha256(data).hexdigest())
    return fp


def test_no_files_mutated(source_root: Path):
    before = _dir_fingerprint(source_root)
    listing_before = sorted(p.name for p in source_root.iterdir())
    analyze(source_root, now=NOW)
    after = _dir_fingerprint(source_root)
    listing_after = sorted(p.name for p in source_root.iterdir())
    assert before == after, "source files will be byte-identical after a dry run"
    assert listing_before == listing_after, "no file may be created/deleted in the source dir"


def test_pct_candidates_selected_by_age(source_root: Path):
    result = analyze(source_root, now=NOW, pct_inactivity_days=14.0)
    manifest_ids = {c["record_id"] for c in result["manifest"] if c["tensor"] == "PCT"}
    # Two old PCT records qualify; the recent one does not.
    assert "PCT:sy:old-condensed:1" in manifest_ids
    assert "PCT:sy:old-fresh:2" in manifest_ids
    assert "PCT:sy:recent:3" not in manifest_ids
    assert result["report"]["stage1_candidates"]["pct_retirement"]["count"] == 2
    # The already-condensed one reuses its existing relic; the other needs a projected relic.
    assert result["report"]["stage1_candidates"]["pct_retirement"]["already_condensed"] == 1
    assert result["report"]["stage1_candidates"]["pct_retirement"]["needs_new_relic"] == 1


def test_pct_age_threshold_is_configurable(source_root: Path):
    # A 30-day window excludes everything (export spans < 30 days).
    result = analyze(source_root, now=NOW, pct_inactivity_days=30.0)
    assert result["report"]["stage1_candidates"]["pct_retirement"]["count"] == 0


def test_peer_caution_exclusions_fire(source_root: Path):
    result = analyze(source_root, now=NOW, peer_stability_days=14.0, peer_min_confirmations=2)
    by_reason = result["report"]["peer_exclusions"]["by_reason"]
    assert by_reason.get("recent_experience", 0) >= 1
    assert by_reason.get("spine_anchored", 0) >= 1
    assert by_reason.get("contested", 0) >= 1
    assert by_reason.get("high_uniqueness_unique_experience", 0) >= 1

    excluded_ids = {e["record_id"]: e["reason"] for e in result["peer_exclusions_full"]}
    assert excluded_ids["PEER:sy:recent:12"] == "recent_experience"
    assert excluded_ids["PEER:sy:anchored:13"] == "spine_anchored"
    assert excluded_ids["PEER:sy:contested:15"] == "contested"
    assert excluded_ids["PEER:sy:unique:17"] == "high_uniqueness_unique_experience"


def test_peer_promotion_candidate_survives(source_root: Path):
    result = analyze(source_root, now=NOW)
    peer_ids = {c["record_id"] for c in result["manifest"] if c["tensor"] == "PEER"}
    # Only the clean established+stable pair should promote.
    assert "PEER:sy:established-a:10" in peer_ids
    assert "PEER:sy:established-b:11" in peer_ids
    # None of the cautioned records may appear as candidates.
    for bad in ("PEER:sy:recent:12", "PEER:sy:anchored:13", "PEER:sy:contested:15", "PEER:sy:unique:17"):
        assert bad not in peer_ids


def test_manifest_entries_carry_source_hashes(source_root: Path):
    result = analyze(source_root, now=NOW)
    assert result["manifest"], "expected a non-empty archive manifest"
    for entry in result["manifest"]:
        h = entry["source_hash"]
        assert isinstance(h, str) and len(h) == 64  # sha256 hex
        int(h, 16)  # valid hex
        assert entry["source_hash_scope"] == "raw_jsonl_record_line_utf8"
        # lineage link relic -> source is present and self-consistent
        assert entry["lineage_link"]["source_record_id"] == entry["record_id"]
        assert entry["lineage_link"]["relic_id"] == entry["relic_id"]
        # a conceptual archive destination is projected, never a real path that exists
        assert entry["projected_archive_dest"]
        assert not Path(entry["projected_archive_dest"]).exists()


def test_source_hash_matches_raw_line(source_root: Path):
    # The manifest source_hash will equal sha256 of the exact stored JSONL line.
    raw_by_id = {}
    for name in ("PCT.jsonl", "PEER.jsonl"):
        for line in (source_root / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                raw_by_id[json.loads(line)["record_id"]] = line
    result = analyze(source_root, now=NOW)
    for entry in result["manifest"]:
        expected = hashlib.sha256(raw_by_id[entry["record_id"]].encode("utf-8")).hexdigest()
        assert entry["source_hash"] == expected


def test_projected_shrinkage_computed(source_root: Path):
    result = analyze(source_root, now=NOW)
    sh = result["report"]["projected_shrinkage"]
    # PCT: 3 records total, 2 retired out.
    assert sh["PCT"]["current_records"] == 3
    assert sh["PCT"]["retired_out_records"] == 2
    assert sh["PCT"]["projected_remaining_records"] == 1
    assert sh["PCT"]["retired_out_bytes"] > 0
    assert sh["PCT"]["projected_remaining_content_bytes"] < sh["PCT"]["current_content_bytes"]
    # PEER: exactly the 2 established records retire out.
    assert sh["PEER"]["retired_out_records"] == 2
    assert sh["PEER"]["projected_byte_reduction_pct"] >= 0.0
    assert sh["net_live_tensor_records_removed"] == 4


def test_forbidden_path_guard():
    with pytest.raises(ValueError):
        assert_local_readonly_path(Path(r"I:\AEGIS-CYBERPEER-CORE\core\dataquad"), purpose="test")
    with pytest.raises(ValueError):
        assert_local_readonly_path(Path(r"C:\somewhere\AEGIS-CYBERPEER-CORE\x"), purpose="test")
