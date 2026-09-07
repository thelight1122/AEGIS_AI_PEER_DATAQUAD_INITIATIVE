"""Tests for the affect/context drain queue plumbing (enqueue / list / mark_done).

The commit helpers (commit_advocate/commit_steward) require a seeded runtime and write to the
ledger, so they are exercised by an end-to-end drain against the live lab rather than here;
these tests cover the deterministic filesystem bookkeeping that must never lose or duplicate a
turn.
"""

import json

from aegis_verus_lab import affect_drain as ad


def _prescan(clean=True):
    return {"kind": "force_prescan_hint", "authoritative": False, "clean": clean,
            "signals": [] if clean else ["authority_framing"], "hits": {}}


def test_enqueue_writes_pending_entry(tmp_path):
    ad.enqueue(
        tmp_path, subject_turn_id="verus-local-turn-aaa", session_id="s1", cwd="H:\\x",
        model="claude-opus-4-8", prompt="hi", response="hello", force_prescan=_prescan(),
    )
    pending = ad.list_pending(tmp_path)
    assert len(pending) == 1
    e = pending[0]
    assert e["subject_turn_id"] == "verus-local-turn-aaa"
    assert e["schema"] == ad.QUEUE_ENTRY_SCHEMA
    assert e["status"] == "pending"
    assert e["prompt"] == "hi" and e["response"] == "hello"
    assert e["force_prescan"]["clean"] is True


def test_enqueue_is_idempotent_per_turn(tmp_path):
    for _ in range(3):
        ad.enqueue(tmp_path, subject_turn_id="verus-local-turn-dup", session_id="s", cwd="H:\\x",
                   model="m", prompt="p", response="r", force_prescan=_prescan())
    assert len(ad.list_pending(tmp_path)) == 1


def test_enqueue_skips_already_drained(tmp_path):
    ad.enqueue(tmp_path, subject_turn_id="verus-local-turn-done", session_id="s", cwd="H:\\x",
               model="m", prompt="p", response="r", force_prescan=_prescan())
    ad.mark_done(tmp_path, "verus-local-turn-done", advocate_turn_id="adv", steward_turn_id="stw")
    # a late duplicate Stop for the same turn must not re-open it
    ad.enqueue(tmp_path, subject_turn_id="verus-local-turn-done", session_id="s", cwd="H:\\x",
               model="m", prompt="p", response="r", force_prescan=_prescan())
    assert ad.list_pending(tmp_path) == []


def test_mark_done_moves_and_annotates(tmp_path):
    ad.enqueue(tmp_path, subject_turn_id="verus-local-turn-x", session_id="s", cwd="H:\\x",
               model="m", prompt="p", response="r", force_prescan=_prescan())
    dest = ad.mark_done(tmp_path, "verus-local-turn-x", advocate_turn_id="adv-1", steward_turn_id="stw-1")
    assert dest.is_file()
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["status"] == "drained"
    assert data["advocate_turn_id"] == "adv-1"
    assert data["steward_turn_id"] == "stw-1"
    assert "drained_at" in data
    # no longer pending, and the pending file is gone
    assert ad.list_pending(tmp_path) == []
    assert not (ad.queue_dir(tmp_path) / "verus-local-turn-x.json").exists()


def test_list_pending_is_ordered_oldest_first(tmp_path):
    ad.enqueue(tmp_path, subject_turn_id="t-b", session_id="s", cwd="H:\\x", model="m",
               prompt="p", response="r", force_prescan=_prescan(), observed_at="2026-09-07T10:00:00.000000Z")
    ad.enqueue(tmp_path, subject_turn_id="t-a", session_id="s", cwd="H:\\x", model="m",
               prompt="p", response="r", force_prescan=_prescan(), observed_at="2026-09-07T09:00:00.000000Z")
    ids = [e["subject_turn_id"] for e in ad.list_pending(tmp_path)]
    assert ids == ["t-a", "t-b"]  # 09:00 before 10:00


def test_list_pending_empty_when_no_queue(tmp_path):
    assert ad.list_pending(tmp_path) == []
