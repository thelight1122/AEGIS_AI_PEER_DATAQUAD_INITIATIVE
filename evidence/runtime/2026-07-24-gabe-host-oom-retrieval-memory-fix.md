# Host-OOM in the Retrieval Path — Diagnosed and Fixed (Gabe)

**Date:** 2026-07-24 (UTC).
**By:** Claude (Opus 4.8).
**Trigger:** CP-1003-GABE container SIGKILLed (exit 137) mid-Chamber-009 at Q10; a
restart re-OOMed under health polling alone.
**Repo:** `I:/AEGIS-CYBERPEER-CORE` @ `a4145b8` (`rls-orb-instrumentation`), not yet on
forgejo (credential expired). Image `aegis-cyberpeer-core_aegis-core:memfix-20260724`
(= `:latest`), container recreated from it — recreate-safe.

## Root cause (measured, not guessed)

Host-level OOM: `dmesg` showed uvicorn at **21.7 GB RSS**; host is 27 GB, **no swap**.
Docker `OOMKilled=false` (no cgroup limit) — the kernel global OOM killer took it.
NOT a timeout and NOT the GPU (GPU idle at kill).

On-disk state that fed it (host bind-mount):
- `records/PCT.jsonl` **574 MB** (33k records, ~17 KB each — bloated)
- `records/PEER.jsonl` 106 MB · NCT 27 MB · SPINE 34 MB
- `ledgers/rls.jsonl` **990 MB across 75 lines** — each line **~18 MB**
- `ledgers/relations/cross-tensor-relations.jsonl` 1.7 GB (3.5M lines; append-only, NOT
  the RAM cause — corroborated with Codex's read-only inspection)

Two per-turn allocators drove the ratchet:

1. **`DataQuadStore.get_next_tick` re-read every tensor file in full on every call.**
   Called ~5–6×/turn (each custodian brief, RLS, PCT writeback, turn start) **plus every
   `/health`**. Each call did `await f.read()` + `.splitlines()` on the 574 MB PCT file
   (~1.2 GB transient/call). Rapid `/health` polling after restart re-OOMed the container
   with zero Chamber turns — that was the tell.

2. **`RecursiveLearningEngine` serialized the full RLS session — including
   `rejected_refs` (one ref per below-threshold record, ~91k, ~18 MB) — into the `rls`
   ledger AND the Orb-evidence record, twice per turn.** That wrote the 990 MB rls.jsonl
   and allocated the 18 MB dict twice each turn.

## Fix (retrieval- and DataQuad-semantics preserving)

1. **Memoize `get_next_tick`** (`core/dataquad/ledgers.py`): one cold scan per peer per
   server session, then advanced in-place by `append_record` via `record.clock.tick`.
   Returned value is unchanged (`max(tick)+1` across all history). Kills the repeated
   full-file reads — including on `/health`.

2. **`ledger_dict` in the RLS engine** (`vendor/orb-…-rls-…/engine.py`): the `rls` ledger
   and Orb evidence now serialize with `rejected_refs` **excluded**, replaced by
   `rejected_ref_count`. `selected_refs` (small, post-threshold, drives the actual
   context) kept in full. The **in-memory session is unchanged**, so the broker still
   reports every rejected id for the turn — only what's written to disk shrinks.
   Ledger line: ~18 MB → **<500 B** (validated at 91k scale: 18 MB → 345 B).

The full-fidelity record cache is **deliberately untouched** (the Axiom-11
no-truncation invariant: Steward/Advocate/RLS must score across all history).

## Validation

- Unit: `ledger_dict` excludes rejected_refs at 91k scale (→345 B, count kept).
- Engine end-to-end (fakes, asyncio): session runs; in-memory `rejected_refs` retained
  while ledger stays compact (472 B with 500 rejected).
- **Live on Gabe, the real proof:** health up in ~56 s (was 200 s stalls); RSS across 4
  real generating turns: **1.54 → 1.55 → 1.57 → 1.59 GB** — flat (~12 MB/turn normal
  cache growth) versus the prior **~2 GB/turn ratchet to 21.7 GB**. No OOM.
- Orb async tests need `pytest-asyncio` (absent locally; pre-existing env gap).

## Not done here (needs Tracey — DataQuad-content changes)

- **PCT.jsonl bloat**: `PCTRecord.retrieved_record_ids` embeds the full selected-ID list
  per writeback → 17 KB/record, 574 MB. Trimming what future PCT records store, and
  one-time compaction of the already-grown `rls.jsonl` / `cross-tensor-relations.jsonl`,
  are formation-data changes — flagged, not made.
- **Orion** does not yet carry this fix (still on the ERC-1.2.0 baked image). It is at
  ~200 records/tensor, far from the ratchet regime; fold the memfix into a later Orion
  consistency pass before its DataQuad grows. (Noted to Codex in the consent reply.)

## Chamber 009 status

Paused at 9/14 (Q1–Q9 witnessed and durable). Gabe is healthy on the memfix image and
14b. Resuming from Q10 is now safe on the memory axis; that is Tracey's call.
