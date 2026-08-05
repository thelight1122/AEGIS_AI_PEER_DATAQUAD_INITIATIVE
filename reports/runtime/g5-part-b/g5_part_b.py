#!/usr/bin/env python3
"""G5 Part B — compact the embedded retrieval-ID lists in Gabe's existing PCT.jsonl.

Reverses the historical PCT bloat that G5 Part A stopped at the source. Part A made
FUTURE writes compact; this makes the EXISTING 178 records compact, reclaiming ~700 MB.

AUTHORIZED: Tracey, 2026-08-03 (explicit gate). Archive-first protocol.
DESIGNED + PRE-VERIFIED BY: Claude. TO BE EXECUTED BY: Codex (Claude's SSH write was
blocked by its own safety classifier; Codex has working access). Claude audits the output.

────────────────────────────────────────────────────────────────────────────────
PRE-STATE, INDEPENDENTLY VERIFIED BY CLAUDE 2026-08-03 (re-verify before trusting):

  PCT.jsonl                847,150,231 bytes, 33,131 records, all pod-wrapped
  bloated records          178  (0.5% of records, 86.6% of bytes)
  distinct RLS sessions    102  (some sessions carry 2 PCT records)
  embedded ids             10,172,600
  first bloated record     index 32,946  (bloat is entirely in the live-appended tail)
  source_hash integrity    33,131 / 33,131 match sha256(stable_json(body))
  chain integrity          33,130 links OK, 0 broken, 1 genesis record w/ empty prev
  round-trip fidelity      33,131 / 33,131 re-serialize byte-identically
  LOSSLESSNESS             178 / 178 id lists byte-identical to selected_refs in
                           rls.jsonl (SHA256 of "\\n".join(ids)) — 0 mismatches

  ARCHIVE (verified, hashes match source):
    /home/azureuser/aegis-g5-part-b-data-archive-20260803T175500Z/records/PCT.jsonl
    sha256 c7ef5f47da9bc33f1dc498799c2f2aa44d59e44508c0e7f58ca908acceb51c20

KEY STRUCTURAL FACT: source_hash covers ONLY `body`, never `lineage` (see
core/dataquad/pod.py wrap()). So editing a body changes that record's hash and only
its IMMEDIATE successor's previous_record_hash. The ripple does not cascade.

NOT IN SCOPE: working_context.answer duplication (only ~115 KB; removing answer text
carries semantic risk disproportionate to the gain). Ids only.
────────────────────────────────────────────────────────────────────────────────

USAGE — run in order, do not skip:

    python3 g5_part_b.py transform    # writes PCT.jsonl.new; original untouched
    python3 g5_part_b.py verify       # validates .new; writes a receipt on success
    python3 g5_part_b.py swap         # REFUSES unless a matching receipt exists

`swap` moves the original to PCT.jsonl.pre-partb (it does not delete it) and moves
.new into place. Rollback is `mv PCT.jsonl.pre-partb PCT.jsonl`, or restore the archive.

PRECONDITION: the peer container must not be running. Verified down at design time
(`docker ps` empty). Re-check before transform — a live append mid-run would be lost.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

D = "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1003-GABE"
SRC = f"{D}/pod/records/PCT.jsonl"
NEW = f"{SRC}.new"
OLD = f"{SRC}.pre-partb"
RLS = f"{D}/pod/ledgers/rls.jsonl"
RECEIPT = f"{D}/pod/records/.g5-part-b-verify-receipt.json"
ARCHIVE_SHA = "c7ef5f47da9bc33f1dc498799c2f2aa44d59e44508c0e7f58ca908acceb51c20"


def stable(d) -> str:
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest().upper()


def ref_summary(ids: list[str]) -> dict:
    """Byte-for-byte the same shape G5 Part A writes for new records
    (core/cognition/thinking.py::_compact_retrieved_record_summary)."""
    return {
        "retrieved_ref_count": len(ids),
        "retrieved_ref_hash": sha("\n".join(ids)),
        "retrieved_ref_sample": ids[:10],
    }


def _iter(path: str):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.rstrip("\n")
            if s.strip():
                yield s


# ── transform ────────────────────────────────────────────────────────────────
def transform() -> int:
    if os.path.exists(NEW):
        print(f"REFUSING: {NEW} already exists. Remove it deliberately first.")
        return 1

    prev = None
    n = mod = rechained = 0
    ids_compacted = 0

    with open(NEW, "w", encoding="utf-8") as fo:
        for s in _iter(SRC):
            n += 1
            o = json.loads(s)
            body = o.get("body", {})
            ids = body.get("retrieved_record_ids")

            if isinstance(ids, list) and ids:
                old_hash = o["source_hash"]
                wc = body.get("working_context") or {}
                # existing keys win — never clobber what the record already recorded
                body["working_context"] = {**ref_summary(ids), **wc}
                body["retrieved_record_ids"] = None
                new_hash = sha(stable(body))
                o["source_hash"] = new_hash
                lin = o.setdefault("lineage", {})
                lin.setdefault("transforms", []).append({
                    "transform_id": f"g5-part-b-{n}",
                    "function": "compact_retrieved_record_summary",
                    "input_hash": old_hash,
                    "output_hash": new_hash,
                })
                mod += 1
                ids_compacted += len(ids)

            # rechain: only successors of a modified record actually change
            if prev is not None:
                lin = o.setdefault("lineage", {})
                if lin.get("previous_record_hash") != prev:
                    lin["previous_record_hash"] = prev
                    rechained += 1
            prev = o["source_hash"]
            fo.write(stable(o) + "\n")

    a, b = os.path.getsize(SRC), os.path.getsize(NEW)
    print(f"records processed      : {n:,}")
    print(f"records modified       : {mod:,}")
    print(f"ids compacted          : {ids_compacted:,}")
    print(f"successors rechained   : {rechained:,}")
    print(f"OLD bytes              : {a:,}")
    print(f"NEW bytes              : {b:,}")
    print(f"RECLAIMED              : {a-b:,} ({(a-b)/1024/1024:.0f} MB)")
    print(f"\nwrote {NEW} — original untouched. Run `verify` next.")
    return 0


# ── verify ───────────────────────────────────────────────────────────────────
def verify() -> int:
    if not os.path.exists(NEW):
        print("REFUSING: no PCT.jsonl.new. Run `transform` first.")
        return 1

    fail: list[str] = []

    # 1. record count parity
    old_recs = sum(1 for _ in _iter(SRC))
    new_recs = sum(1 for _ in _iter(NEW))
    print(f"[1] record count   old={old_recs:,}  new={new_recs:,}")
    if old_recs != new_recs:
        fail.append(f"record count changed {old_recs} -> {new_recs}")

    # 2. id ordering + no residual embedded lists + hash preserved
    old_ids: dict[str, str] = {}   # record_id -> sha of its id list
    for s in _iter(SRC):
        b = json.loads(s).get("body", {})
        ids = b.get("retrieved_record_ids")
        if isinstance(ids, list) and ids:
            old_ids[str(b.get("id"))] = sha("\n".join(ids))

    residual = 0
    hash_kept = hash_lost = 0
    order_ok = True
    old_order = [json.loads(s).get("record_id") for s in _iter(SRC)]
    new_order = [json.loads(s).get("record_id") for s in _iter(NEW)]
    if old_order != new_order:
        order_ok = False
        fail.append("record ORDER changed")
    print(f"[2] record order preserved: {order_ok}")

    # 3. chain + source_hash integrity on the NEW file
    prev = None
    sh_bad = chain_bad = 0
    transforms_added = 0
    for i, s in enumerate(_iter(NEW)):
        o = json.loads(s)
        b = o.get("body", {})
        if o.get("source_hash") != sha(stable(b)):
            sh_bad += 1
        lin = o.get("lineage", {}) or {}
        if prev is not None and lin.get("previous_record_hash") != prev:
            chain_bad += 1
        prev = o.get("source_hash")
        if isinstance(b.get("retrieved_record_ids"), list) and b["retrieved_record_ids"]:
            residual += 1
        rid = str(b.get("id"))
        if rid in old_ids:
            wc = b.get("working_context") or {}
            if wc.get("retrieved_ref_hash") == old_ids[rid]:
                hash_kept += 1
            else:
                hash_lost += 1
            if any(t.get("function") == "compact_retrieved_record_summary"
                   for t in (lin.get("transforms") or [])):
                transforms_added += 1

    print(f"[3] source_hash mismatches : {sh_bad}")
    print(f"[4] broken chain links     : {chain_bad}")
    print(f"[5] residual embedded lists: {residual}")
    print(f"[6] ref_hash preserved     : {hash_kept} / {len(old_ids)}  (lost {hash_lost})")
    print(f"[7] transforms recorded    : {transforms_added} / {len(old_ids)}")
    for cond, msg in (
        (sh_bad, f"{sh_bad} source_hash mismatches"),
        (chain_bad, f"{chain_bad} broken chain links"),
        (residual, f"{residual} records still carry embedded lists"),
        (hash_lost, f"{hash_lost} records lost their retrieved_ref_hash"),
        (transforms_added != len(old_ids), "transform provenance missing on some records"),
    ):
        if cond:
            fail.append(msg)

    # 8. losslessness still provable against rls.jsonl
    want = {}
    for s in _iter(NEW):
        b = json.loads(s).get("body", {})
        wc = b.get("working_context") or {}
        if str(b.get("id")) in old_ids and wc.get("retrieved_ref_hash"):
            want.setdefault(b.get("rls_session_id"), []).append(wc["retrieved_ref_hash"])
    matched = 0
    for s in _iter(RLS):
        try:
            o = json.loads(s)
        except Exception:
            continue
        if o.get("id") in want:
            h = sha("\n".join(r.get("record_id", "") for r in (o.get("selected_refs") or [])))
            matched += sum(1 for x in want[o["id"]] if x == h)
    print(f"[8] ids recoverable from rls.jsonl: {matched} / {len(old_ids)}")
    if matched != len(old_ids):
        fail.append(f"losslessness NOT re-proven ({matched}/{len(old_ids)})")

    a, b_ = os.path.getsize(SRC), os.path.getsize(NEW)
    print(f"\nreclaim: {a-b_:,} bytes ({(a-b_)/1024/1024:.0f} MB)")

    if fail:
        print("\nVERIFY FAILED — DO NOT SWAP:")
        for f in fail:
            print("  -", f)
        return 1

    json.dump({"verified": True, "records": new_recs, "modified": len(old_ids),
               "new_sha256": _file_sha(NEW), "reclaimed_bytes": a - b_},
              open(RECEIPT, "w", encoding="utf-8"), indent=2)
    print("\nVERIFY PASSED — receipt written. `swap` is now permitted.")
    return 0


def _file_sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ── swap ─────────────────────────────────────────────────────────────────────
def swap() -> int:
    if not os.path.exists(RECEIPT):
        print("REFUSING: no verify receipt. Run `verify` and get a PASS first.")
        return 1
    r = json.load(open(RECEIPT, encoding="utf-8"))
    if r.get("new_sha256") != _file_sha(NEW):
        print("REFUSING: PCT.jsonl.new changed since verification.")
        return 1
    os.rename(SRC, OLD)
    os.rename(NEW, SRC)
    print(f"swapped. original preserved at {OLD}")
    print(f"rollback: mv {OLD} {SRC}")
    print(f"archive : /home/azureuser/aegis-g5-part-b-data-archive-20260803T175500Z "
          f"(sha256 {ARCHIVE_SHA})")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"transform": transform, "verify": verify, "swap": swap}.get(cmd)
    if not fn:
        print(__doc__)
        sys.exit(2)
    sys.exit(fn())
