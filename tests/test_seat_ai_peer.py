"""Gates on the AI Peer seating tool.

The tool's value is almost entirely in what it refuses. These tests exercise the refusals
directly, because a seeding tool that only works on the happy path is the one that seeds four
Foundations from an unresolved Canon and cannot be undone.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("seat_ai_peer", ROOT / "scripts" / "seat_ai_peer_dataquad.py")
seat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seat)


def _package(status: str = "clean", spine: int = 2, nct: int = 2) -> dict:
    def rec(tensor: str, i: int, genesis: bool) -> dict:
        return {
            "id": f"{tensor}:{{{{CYBERPEER_SESSION_ID}}}}:" + ("genesis:0" if genesis else f"seeded:item-{i}"),
            "markers": ["genesis"] if genesis else ["steward-seeded"],
            "tensor": tensor,
        }
    return {
        "packageId": "TEST-PACKAGE",
        "packageVersion": "test",
        "canonLock": {"status": status, "reviewNeededSourceCount": 0 if status == "clean" else 2,
                      "sourceManifestId": "TEST-MANIFEST", "sourceManifestSha256": "A" * 64},
        "records": {
            "SPINE": [rec("SPINE", i, i == 0) for i in range(spine)],
            "NCT": [rec("NCT", i, i == 0) for i in range(nct)],
            "PEER": [rec("PEER", 0, True)],
            "PCT": [rec("PCT", 0, True)],
        },
    }


def _roster(declaration: str = "Steward declaration, supplied.") -> dict:
    return {"peers": [{"peer_id": "lumin", "session_id": "lumin-session-001",
                       "display_name": "Lumin", "steward_declaration": declaration}]}


def _args(**over) -> argparse.Namespace:
    base = dict(via="file", api_base="http://127.0.0.1:8787", clock_policy="genesis-baseline",
                dry_run=True, emit_only=False, data_dir=None, peer=None)
    base.update(over)
    return argparse.Namespace(**base)


# --- the canon lock gate -----------------------------------------------------------------


def test_review_needed_canon_is_refused_by_default():
    """The gate that did not exist in the original tool."""
    with pytest.raises(seat.SeatingRefused, match="canonLock.status"):
        seat.check_canon_lock(_package(status="review-needed"), allow_unclean=False)


def test_missing_canon_lock_is_refused():
    with pytest.raises(seat.SeatingRefused):
        seat.check_canon_lock({"records": {}}, allow_unclean=False)


def test_clean_canon_passes_and_reports_no_override():
    canon = seat.check_canon_lock(_package(status="clean"), allow_unclean=False)
    assert canon["clean"] is True
    assert canon["override_used"] is False


def test_override_is_permitted_but_records_itself():
    canon = seat.check_canon_lock(_package(status="review-needed"), allow_unclean=True)
    assert canon["clean"] is False
    assert canon["override_used"] is True
    assert canon["review_needed_source_count"] == 2


def test_override_propagates_into_every_record_provenance():
    """An override must be visible in the Foundation, not only in the console."""
    canon = seat.check_canon_lock(_package(status="review-needed"), allow_unclean=True)
    prov = seat.build_provenance(canon)
    assert prov["canon_override_used"] is True
    assert prov["canon_lock_clean"] is False
    assert prov["canon_lock_status"] == "review-needed"


# --- roster validation --------------------------------------------------------------------


def test_pending_steward_declaration_is_refused():
    """The declaration is a Steward act; a placeholder must not reach a Foundation."""
    with pytest.raises(seat.SeatingRefused, match="PENDING"):
        seat.validate_roster(_roster(declaration="PENDING — Steward act."))


def test_missing_required_field_is_refused():
    roster = _roster()
    del roster["peers"][0]["session_id"]
    with pytest.raises(seat.SeatingRefused, match="missing"):
        seat.validate_roster(roster)


def test_duplicate_peer_id_is_refused():
    roster = _roster()
    roster["peers"].append(dict(roster["peers"][0]))
    with pytest.raises(seat.SeatingRefused, match="duplicate"):
        seat.validate_roster(roster)


def test_empty_roster_is_refused():
    with pytest.raises(seat.SeatingRefused):
        seat.validate_roster({"peers": []})


# --- ring order ---------------------------------------------------------------------------


def test_missing_spine_or_nct_refuses_before_any_write():
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    peer = _roster()["peers"][0]
    with pytest.raises(seat.SeatingRefused, match="Rings 1-2|Ring 3"):
        seat.seat_peer(peer, _package(spine=0), canon, _args(dry_run=False, data_dir="/tmp/x"), "2026-08-06T00:00:00Z")


def test_bootstrap_pillars_refuse_when_rings_not_seated(tmp_path):
    """SPINE already present and non-empty means it is not written, so Rings 1-3 are not seated."""
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    peer = _roster()["peers"][0]
    d = tmp_path / "lumin" / "dataquad"
    d.mkdir(parents=True)
    (d / "SPINE.jsonl").write_text("pre-existing\n", encoding="utf-8")
    with pytest.raises(seat.SeatingRefused, match="Rings 1-3 are not seated"):
        seat.seat_peer(peer, _package(), canon, _args(dry_run=False, data_dir=str(tmp_path)), "2026-08-06T00:00:00Z")


def test_ring_order_constant_puts_spine_and_nct_first():
    assert seat.RING_ORDER[:2] == ("SPINE", "NCT")


# --- clock and tick policy -----------------------------------------------------------------


def test_genesis_records_take_tick_zero_not_one():
    """The original numbered every record from 1, which would put genesis at tick 1."""
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    shaped = seat.shape_records(_package(spine=3)["records"]["SPINE"], "SPINE",
                                "genesis-baseline", "2026-08-06T00:00:00Z", canon)
    assert shaped[0]["clock"]["tick"] == 0
    assert [r["clock"]["tick"] for r in shaped] == [0, 1, 2]


def test_genesis_baseline_policy_uses_the_canonical_timestamp():
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    shaped = seat.shape_records(_package()["records"]["SPINE"], "SPINE",
                                "genesis-baseline", "2026-08-06T09:99:99Z", canon)
    assert shaped[0]["clock"]["started_at"] == seat.GENESIS_BASELINE == "2026-01-01T00:00:00.000Z"


def test_seeded_now_policy_uses_the_run_timestamp():
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    applied = "2026-08-06T12:00:00Z"
    shaped = seat.shape_records(_package()["records"]["SPINE"], "SPINE", "seeded-now", applied, canon)
    assert shaped[0]["clock"]["started_at"] == applied


# --- overwrite refusal ----------------------------------------------------------------------


def test_write_refuses_to_overwrite_a_non_empty_tensor(tmp_path):
    path = tmp_path / "SPINE.jsonl"
    path.write_text("existing Foundation\n", encoding="utf-8")
    outcome = seat.write_file(path, [{"id": "x"}], "SPINE")
    assert outcome["written"] is False
    assert "refusing to overwrite" in outcome["reason"]
    assert path.read_text(encoding="utf-8") == "existing Foundation\n"


def test_write_succeeds_on_an_empty_target(tmp_path):
    outcome = seat.write_file(tmp_path / "NCT.jsonl", [{"id": "a"}, {"id": "b"}], "NCT")
    assert outcome["written"] is True
    assert outcome["records"] == 2
    assert len(outcome["sha256"]) == 64


# --- substitution -----------------------------------------------------------------------------


def test_every_placeholder_is_substituted():
    peer = {"peer_id": "lumin", "session_id": "lumin-session-001",
            "display_name": "Lumin", "steward_declaration": "declared"}
    text = json.dumps(_package())
    out = seat.stamp(text, peer, "2026-08-06T00:00:00Z")
    assert "{{" not in out
    assert "lumin-session-001" in out


def test_dry_run_writes_nothing(tmp_path):
    canon = seat.check_canon_lock(_package(), allow_unclean=False)
    peer = _roster()["peers"][0]
    result = seat.seat_peer(peer, _package(), canon, _args(dry_run=True, data_dir=str(tmp_path)), "2026-08-06T00:00:00Z")
    assert result["dry_run"] is True
    assert not list(tmp_path.iterdir())
