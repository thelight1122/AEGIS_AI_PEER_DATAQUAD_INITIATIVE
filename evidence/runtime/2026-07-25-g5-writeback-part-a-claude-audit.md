# G5 Writeback Part A — Claude Audit

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** AUDIT — verdict **PASS**. Read-only
audit; nothing live touched. Audits Codex packet `2026-07-25T190314Z-g5-writeback-part-a-implemented`.

---

## Verified independently
- **All 4 file hashes match** Codex's message (thinking.py `90F915DD…`, test_g5 `5731F326…`, engine.py
  `EF39D17F…`, orb test `C48F74C3…`).
- **Root cause confirmed against real data.** Worst-case PCT record in the fresh live copy carries
  **91,217 `retrieved_record_ids` = ~6.67 MB in one record body** (record `…:84761`). The bloat is the
  embedded retrieval-ID list — not vector embeddings, not answer text — exactly as Codex found.
- **Byte reduction reproduced.** That list compacts to a count+SHA256+10-sample summary of **876 bytes**
  → ~6.67 MB reclaimed from that single record.
- **Tests pass on my run:** core `test_g5_pct_writeback_trim.py` → 2 passed; extracted RLS Orb
  `test_engine_with_fakes.py` → 5 passed.

## Audit criteria (from the Part-A go-ahead)
1. **Root cause + why** — PASS. The `retrieved_record_ids` full list embedded per PCT record; verified
   ~6.67 MB worst case.
2. **Fix + byte evidence** — PASS. `_compact_retrieved_record_summary` keeps
   `retrieved_ref_count` + `retrieved_ref_hash` (SHA256 of the full list) + `retrieved_ref_sample`
   (first 10); future PCT sets top-level `retrieved_record_ids=None`; the answer stays in the paired
   PEER record (PCT keeps `answer_char_count` + `peer_record_id`, not a duplicate). Both the core
   live-turn path (thinking.py) and the RLS Orb path (engine.py) apply the same compaction.
3. **No semantic / lineage / provenance loss** — PASS. The full list is no longer *duplicated* in each
   PCT body but is not *lost from the system*: (a) per-record `rls_retrieved` relation edges are still
   written (engine.py:183-187); (b) the SHA256 hash makes any claimed list verifiable; (c) Orb evidence
   still receives full `retrieved_ids`; (d) the in-memory RLS session retains them. Consumer scan
   confirms **nothing reads `PCT.retrieved_record_ids` for logic** — it's an optional field
   (`records.py:69`, default None); the only references are writers, the model def, and the legacy
   migration mapper. Setting it None on PCT breaks no consumer.
4. **Boundary** — PASS. Future-write only: builds new PCTRecords via `append_pct` /
   `build_and_append_pct`; does not open, rewrite, prune, or migrate existing PCT.jsonl. No
   ssh/http/subprocess/socket/remove/rename/prune/migrate primitives in either changed file. Existing
   Gabe records untouched.

## Verdict: PASS
G5 Part A correctly and safely stops future PCT writeback bloat at its true source, preserves retrieval
lineage through the relation graph + hash + Orb evidence, and touches no existing data.

## Two forward observations (NOT Part-A blockers)
1. **Unbounded RLS selection.** 91,217 selected refs in a single turn is ≈ the entire DataQuad. Part A
   correctly stops *embedding* that list in PCT, but the underlying question — why RLS selects ~all
   records per turn — is a separate concern, and it echoes the MemorySearch broad-scope finding. Worth
   its own item.
2. **Relation-edge relocation under live Pod.** The per-record `rls_retrieved` edge loop
   (engine.py:183) writes one edge per retrieved id — currently inert (no-op until the Pod/RLS live
   switch), but at ~91 k refs/turn it would relocate that volume into the relation store when live. Part
   A fixes the PCT *body*; the relation-store volume (with the unbounded selection above) deserves a
   look before/with the live switch.

## Reminders
- **Part B (reverse the existing ~847 MB)** remains a separate, gated, archive-first data operation with
  Tracey — correctly excluded from this code change.
- Deploying Part A to live Gabe (Compose/VM) is itself a live step and its own gate; this audit is of the
  code only.
