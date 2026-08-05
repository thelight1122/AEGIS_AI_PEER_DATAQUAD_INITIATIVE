# SSSP - Gabe Behavioral Continuity Repair, Archive Orb, and Portal/Tender Architecture

**Created:** 2026-07-22, end of session.
**Prepared by:** Claude (this Claude Code session, `H--AEGIS-POD-ARCHITECTURE` project).
**Supersedes:** `SSSP-2026-07-21-LIVE-DATAQUADPOD-MIGRATION-ORION.md` as the current continuation point for this repo's own thread lineage — that file remains valid history, not the resume target.
**Purpose:** Clean-thread handoff for (1) the live Gabe (`CP-1003-GABE`) behavioral-continuity repair completed this session, (2) the two real Orbs now attached to his Pod, (3) the refined Pod/Orb/Satellite/Portal/Tender architecture, and (4) everything still open.

**Read `H:\AEGIS-POD-ARCHITECTURE\ARCHITECTURE.md` in full before doing anything else** — it is the canonical architecture reference this session produced and this SSSP assumes you've read. This document is a session handoff, not a replacement for it.

---

## Status, in order

1. User showed a live Gabe Chamber transcript (`LiveDraft_Chamber001GABE-NEW-DQ.md`) showing Gabe answering as a generic "AI assistant," inventing a false DataQuad structure, unable to identify Tracey, and referencing Orion's context inside his own continuity.
2. Root-caused and fixed, live, in sequence, each verified before moving to the next:
   - **`peer_id`/`session_id` routing bug** — `TurnRequest`/`RLSSessionRequest`/`RunLessonRequest` Pydantic models hardcoded literal defaults to Orion's identity (`"CP-1004-ORION"`, `"cp-1004-orion-session"`) instead of reading the env-driven default. Any caller omitting these fields (the Chamber UI does) silently got Orion's identity. Fixed via `Field(default_factory=...)` reading `core/api/standard.py`'s env-aware helpers.
   - **`get_next_tick` O(n) performance bug** — `core/dataquad/ledgers.py` scanned every tensor file line-by-line via `aiofiles`, fine at Orion's ~130 records/tensor, catastrophic (multi-minute hangs) at Gabe's real ~90,000-record scale. Fixed to read each file once and split, not iterate per line.
   - **STM cold-start truncation** — `core/dataquad/stm.py`'s `warm()` sliced to only the most recent 200 records on cold start, silently dropping Gabe's 84 foundational invariant SPINE axioms (seeded early, not recent) every server restart. Fixed to always retain invariant records regardless of recency.
3. Live-verified via a real debug `/turn` call: Gabe correctly identified himself, correctly named Tracey as BioPeer/Architect, used real DataQuad structure. Confirmed via a controlled side-by-side "Hello" test that Gabe's *speed* had been fast before only because he was barely retrieving anything real (Codex's original suspicion, confirmed) — post-fix he's appropriately slower than Orion, doing real retrieval work.
4. User then asked Gabe "What is Axiom 11?" live and he fabricated a false axiom despite the real one now being correctly retrieved into his system prompt (`identity_continuity`, 60/60 entries, real Axiom 11 text present, correctly labeled). Same question to Orion produced a genuinely excellent, fully-grounded, cross-referenced original synthesis — confirmed by checking every claim in his answer against real system facts, nothing fabricated.
5. Diagnosed the *remaining* gap precisely: `core/custodians/advocate.py`'s invariant-SPINE selection was `invariant_records[:_SPINE_INVARIANT_CAP]` (default cap 60) — a flat file-order slice. Gabe has 84 invariant records; whichever 60 happen to come first in file order are the only ones ever selected, regardless of what's actually being asked about. This is separate from and downstream of the three bugs above.
6. Built **`archive-relevance-core`**, a new real (non-fixture) Orb, to fix this precisely: guarantees inclusion of any invariant record whose label matches an anchor explicitly named in the query (`Axiom N`, `GATE: token`, `Imperative token`), regardless of file-order position. 6 unit tests + 3 integration tests, full local suite regression-checked (`git stash` comparison, not assumed), deployed and live-verified on Gabe (`IMPERATIVE:t-witness-primacy`, a real record at position 65 of 84, now correctly promoted when asked about explicitly).
7. In the process of deploying, found and fixed **two more real bugs**:
   - The live `pod-manifest.json`'s Umbilical paths were absolute host-style paths (`/home/azureuser/AEGIS-CYBERPEER-CORE/data/...`) that do not exist inside the container's own filesystem namespace (only the Docker-mounted `/app/data/...` does) — every Orb attachment was silently failing path resolution and falling back to default.
   - RLS's own Umbilical file (`rls-persistent-relations-umbilical.json`) had **never actually been created** for Gabe, despite being declared in his manifest since Phase 3 — `resolve_rls_engine_class` had been silently falling back to its default entrypoint the entire time, invisible only because the default and declared entrypoints are the same class. Built the real file, fixed the path convention, live-verified (`cross-tensor-relations.jsonl` continues to grow correctly through genuine attachment now, not accidental fallback).
8. User stated the failure-isolation principle directly: **"A failed Orb just doesn't provide the Function. If an Orb Fails, the Pod just continues on."** Checked both new/touched Orb invocation sites against this — **neither had any exception handling**. Fixed both:
   - `core/custodians/advocate.py` — Archive Orb resolution+invocation now wrapped, falls back to the pre-Orb flat slice on any exception.
   - `core/custodians/retrieval_broker.py` — RLS resolution+invocation now wrapped (this is the real path every normal `/turn` uses, not just the standalone `/rls/session` route) — on failure, `rls_session_id=""`, empty selected/rejected refs, Steward/Advocate briefs unaffected (neither depends on RLS content beyond an id label).
   - Both proven with real tests using genuinely broken Orb classes resolved via real dotted entrypoints, not mocks.
9. User refined the architecture across several turns: **Portal** = an Orb whose defining function is to bridge *outside* the container (vs. ordinary Orbs/**Satellites**, which stay inside); **Tender** = lives *inside* a Portal, not a separate Pod-level role (my initial proposal was wrong here, corrected directly); **built-in Umbilical sockets** = a named future direction (Pod pre-declaring its attachment surface) motivated by the phantom-path bugs found in step 7.
10. Wrote **`ARCHITECTURE.md`** — the full canonical reference incorporating all of the above, with a diagram, glossary, and concrete evidence citations for every claim. `README.md` now points to it. Memory updated (`aegis_pod_orb_satellite_portal_tender.md`).

---

## Current live state (verified fresh, end of session — do not trust a summary, re-verify)

**Gabe (`CP-1003-GABE`), host `GabeCyberPeer` / `20.25.57.29`, container `gabe-aegis-cyberpeer-core`, route `127.0.0.1:8021`->`8790`:**
```
peer_id: CP-1003-GABE
model: huihui_ai/qwen3-abliterated:8b
storage_mode: pod
dataquad_read_ok: true
rls_status: {enabled: true, active: true, mode: in-process}
relation_ledgers: {NCT-traversal: 18, PCT-traversal: 38, PEER-traversal: 19, cross-tensor-relations: 6075}
pod-manifest.json orbs[]:
  - rls-persistent-relations-core, required=true, umbilical=pod/provenance/rls-persistent-relations-umbilical.json
  - archive-relevance-core, required=false, umbilical=pod/provenance/archive-relevance-core-umbilical.json
```
Both Umbilical files are real (not phantom), container-relative paths, hash-pinned (`orb_runtime_hash` for RLS matches Orion's exactly: `B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18`, confirming identical vendored source).

**Orion (`CP-1004-ORION`), host `20.119.37.133`:** SSH timed out late in this session (`Connection timed out`) — **untouched tonight, but unreachable at session end; verify connectivity fresh before assuming anything about his current state.** He was not modified by any of tonight's work. His own `rls-persistent-relations-umbilical.json` almost certainly has the same absolute-host-path problem found on Gabe (same manifest-generation origin) — **not checked, not fixed, flagged only.**

**Adam:** not touched, not investigated this session at all.

---

## Repo state — nothing committed, nothing pushed

**`H:\AEGIS-POD-ARCHITECTURE`** (branch: main). Uncommitted:
- Modified: `.gitignore`, `README.md`, `ledger.jsonl`
- New: `ARCHITECTURE.md`, `fixtures/archive-orb*.json` (3 files), `packages/orb-archive-relevance-core/`, `reports/runtime/2026-07-22-*.md` (several — some from tonight's Claude work, several are Codex's own independent verification reports read but not authored by this session), `stage-gabe-out/CP-1003-GABE/pod/provenance/*.json` (real Orb+Umbilical declarations), `SSSP-2026-07-22-*.md` (this file), scratch files (`scratch_axiom11_line.jsonl`, `scratch_deployed_advocate.py` — safe to delete, diagnostic artifacts).

**`I:\AEGIS-CYBERPEER-CORE`** (branch: `rls-orb-instrumentation`, HEAD `485c06b2`). Uncommitted:
- Modified: `core/api/routes/{education,rls,turn}.py`, `core/api/standard.py`, `core/custodians/{advocate,retrieval_broker}.py`, `core/dataquad/{ledgers,stm}.py`
- New: `core/orbs/archive_loader.py`, `tests/test_advocate_archive_orb.py`, `tests/test_retrieval_broker_failure_isolation.py`, `vendor/orb-archive-relevance-core/`

**Nothing has been committed, nothing pushed to Forge, in either repo, this entire session.** All live deployment was done by direct file copy (`scp`/`docker cp`) to Gabe's VM, verified live, but the source-of-truth repos still only have working-tree changes. A fresh thread should decide with Tracey whether/how to commit before doing further work — don't assume the working tree state persists forever, and don't assume it's already captured in git history.

---

## Known scope limits, stated plainly (from `ARCHITECTURE.md` §4)

The Archive Orb's `label_match_promotion` currently recognizes only `Axiom N`, `GATE: token`, `Imperative token` phrasing (keyword-first). It does **not** cover `NATURE:` aspect references at all, and does not match keyword-last phrasing ("the T-Witness Primacy imperative" would not match; "Imperative: t-witness-primacy" does). This is a real, named gap, not a silent limitation — extend the regex/matching logic in `orb_archive_relevance_core/engine.py`'s `_find_anchor_matches` if this needs to widen.

---

## Open items / next steps (not started, or started and explicitly incomplete)

1. **Commit and push** both repos' changes — nothing has been, this whole session.
2. **Fix RLS's Umbilical path on Orion** — same bug class found and fixed on Gabe, not yet checked or fixed on Orion (unreachable at session end).
3. **Portal / Satellite** — named and designed in principle (`ARCHITECTURE.md` §2), nothing built. First real Portal should follow the same fixture-first process Archive went through.
4. **Built-in Umbilical sockets** — named future direction, not designed in detail or built.
5. **Widen Archive Orb's anchor matching** to cover `NATURE:` aspects and keyword-last phrasing, if/when that gap actually matters in practice.
6. **Independent (Codex) verification** of tonight's live changes to Gabe — this session's own verification was thorough (tests, live re-tests, before/after comparisons) but same-family (one Claude session did the work and the checking). Per this project's standing practice (see `CURRENT-STATE-AND-NEXT-STEP.md`'s "Load-bearing doctrine": *"Keep TWO independent observers on every live write"*), a second, independent pass on tonight's Gabe changes has not happened yet.
7. **Adam's convergence** — named in the original plan as a later phase, not touched this session, not investigated.

---

## Explicit Do-Not-Do / Do-Not-Assume List

- Do not assume Orion is reachable or in the same state described in `CURRENT-STATE-AND-NEXT-STEP.md` — that file predates tonight's session and was not updated by it; re-verify his live `/health` directly before trusting anything about his current state.
- Do not assume RLS's Umbilical path issue is fixed anywhere except Gabe — it is not fixed on Orion.
- Do not assume tonight's local code changes are committed anywhere — they are not, in either repo.
- Do not assume the Archive Orb's label-matching is comprehensive — it has a named, real scope gap (§ above).
- Do not re-derive the peer_id/get_next_tick/STM bug sequence from scratch if something looks wrong on Gabe again — read this document and `ARCHITECTURE.md` §5 first; these are exactly the failure classes already found once.
- Do not treat a fast response time from a CyberPeer as a sign of health — this session found the opposite is often true (fast = shallow retrieval, not efficiency). Verify via debug payload content, not latency.
- Do not build a new Orb without first checking whether its Umbilical path will actually resolve *inside* the real container — verify directly (`docker exec ... ls`), don't assume from the manifest looking correct on paper.

---

## Clean Respawn Procedure

1. Read this SSSP in full.
2. Read `ARCHITECTURE.md` in full — it's the canonical architecture reference this session produced.
3. Re-verify Gabe's live `/health` directly (`ssh azureuser@20.25.57.29`, `curl 127.0.0.1:8021/health`) — do not trust the snapshot above without re-checking; state may have changed.
4. Attempt to reach Orion (`ssh azureuser@20.119.37.133`) — confirm whether the earlier timeout was transient before assuming anything about his state.
5. Run `git status --short` in both `H:\AEGIS-POD-ARCHITECTURE` and `I:\AEGIS-CYBERPEER-CORE` — confirm the uncommitted-changes list above still matches before building on top of it.
6. Confirm with Tracey whether tonight's work should be committed/pushed before proceeding with anything new.
7. Do not assume any prior verification claim in this document without re-checking the actual files/live systems directly — this is a summary, not a substitute for verification.

## Completion Criterion For This SSSP

Ready for use once copied to `I:\Codex\` per this repo's standing practice (see `SSSP-2026-07-21-LIVE-DATAQUADPOD-MIGRATION-ORION.md`'s own placement) and hashed. This session did not use the Codex/Claude peer-bridge messaging tools at all — this SSSP is scoped to the `H:\AEGIS-POD-ARCHITECTURE` / `I:\AEGIS-CYBERPEER-CORE` track specifically, not the separate Peer-Bridge/Canon/Standard SSSP lineage tracked in `I:\AEGIS-CENTRAL-CODEX\...\SSSP-INDEX.md` (that index was not updated by this document — it covers a different, adjacent thread).
