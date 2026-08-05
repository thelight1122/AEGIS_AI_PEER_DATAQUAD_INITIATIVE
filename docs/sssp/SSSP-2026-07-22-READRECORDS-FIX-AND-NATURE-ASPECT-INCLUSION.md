# SSSP — read_records Full-DataQuad Fix, Archive Orb Live-Verification, and Nature Aspect Continuous Inclusion

**Created:** 2026-07-22, mid-work (account allowance limit reached; respawning into Tracey's other Claude account).
**Prepared by:** Claude (this Claude Code session, `H--AEGIS-POD-ARCHITECTURE` project).
**Supersedes:** `SSSP-2026-07-22-GABE-BEHAVIORAL-CONTINUITY-AND-ARCHIVE-ORB.md` as the current continuation point for this repo's thread lineage — that file remains valid history and its architecture context still holds.
**Purpose:** Clean-thread handoff for (1) the read_records truncation bug fixed and deployed live to Gabe this session, (2) the live verification that Gabe now reads his full DataQuad, (3) the live demonstration that the Archive Orb genuinely resolves and promotes, and (4) the **in-flight Nature Aspect Continuous Inclusion design — awaiting Tracey's approval of the condensed forms before any build.**

**Read these first, in order, before doing anything:**
1. `H:\AEGIS-POD-ARCHITECTURE\ARCHITECTURE.md` — canonical Pod/Orb/Satellite/Portal/Tender reference.
2. The prior SSSP (`SSSP-2026-07-22-GABE-BEHAVIORAL-CONTINUITY-AND-ARCHIVE-ORB.md`) — the three bug classes and the Archive/RLS Orb build.
3. `reports/runtime/2026-07-22-nature-aspect-continuous-inclusion-design-proposal.md` — the open work this SSSP most needs you to continue.

This is a session handoff, not a replacement for those. Re-verify every live/repo claim below directly; do not trust the summary.

---

## Status, in order (what this session did)

1. **Committed and pushed both repos** (prior SSSP open-item #1, previously nothing committed all session-lineage):
   - `H:\AEGIS-POD-ARCHITECTURE` (`main`): 4 commits `88210e4`→`7a82263`, pushed to `origin` (private Forge `git@20.172.153.141`). Cleanup: deleted the two scratch files, added `*.egg-info/` to `.gitignore`.
   - `I:\AEGIS-CYBERPEER-CORE` (`rls-orb-instrumentation`): commits `bdc88c9` (peer_id/get_next_tick/STM fixes) and `3e701a5` (archive Orb wiring + failure isolation), pushed to **`forgejo` only** (NOT the public GitHub `origin`) per Tracey's explicit choice.
2. **Root-caused and fixed a NEW live bug: `read_records` truncation.** Tracey reported Gabe not accessing his DataQuad; `/health` showed `tensor_counts` capped at `PEER:200, PCT:200, NCT:200, SPINE:282` despite ~91k records on disk. Root cause: `core/dataquad/ledgers.py::read_records` — the read path health/Steward/Advocate/RLS/bootstrap all use — returned the **bounded STM cache** (`stm.get`, capped at `STM_CAPACITY=200` + invariants) once warm, instead of the full record set. Every consumer saw only the newest ~200 records/tensor, defeating relevance retrieval at scale. Invisible at Orion's ~130/tensor; a hard wall at Gabe's ~35k/tensor. This morning's invariant-retention STM patch rescued SPINE axioms but left PEER/PCT/NCT fully capped.
3. **Fix (Approach A, Tracey-chosen):** added an uncapped full-fidelity cache to `core/dataquad/stm.py` (`warm_full`/`get_full`/`_full_cache`/`_full_warm`); `read_records` now returns it and warms both caches; `put` keeps both consistent; `evict` clears both. The bounded cache (`get`/`get_recent`/`search`/`stats`, used only by the `/dataquad` inspection routes) is unchanged. Committed `5062db1` (I repo), pushed to `forgejo`. New test `tests/test_read_records_full_fidelity.py` (3 tests, pass). Full suite regression-checked against a `git stash` baseline: **identical 19 pre-existing (env) failures, zero new.**
4. **Deployed live to Gabe** by `docker cp` of `stm.py` + `ledgers.py` into `gabe-aegis-cyberpeer-core` + `docker restart`. Backups saved on the VM: `/tmp/stm.py.pre-fullfidelity.bak`, `/tmp/ledgers.py.pre-fullfidelity.bak`.
5. **Live-verified the fix:** `/health` now reports the real counts `PEER:35693, PCT:32985, NCT:9690, SPINE:12707` (exactly the on-disk line counts). A real debug `/turn` ("Who is Tracey to you?") returned a grounded answer identifying Tracey as his T-Witness "from PEER records"; debug payload showed deep retrieval (advocate `identity_continuity:65`, `relational_salience:34`, `selected_ledger_refs:36`; steward `context_claims:31`, `factual_continuity:20`). The original generic-AI-assistant symptom is gone.
6. **Verified the Archive Orb genuinely resolves in Gabe's container** (all five layers: manifest, umbilical, loader, importable vendored package, and `resolve_archive_engine_class(...)` returning the real `ArchiveRelevanceEngine`, not a fallback). **Demonstrated live promotion:** a turn naming `Imperative: t-witness-primacy` (a real record at invariant index 65 of 84, past the 60-cap) placed it into `identity_continuity`; a contrast turn not naming it excluded it. Same total entries (65) both turns — the Orb evicted a lower-priority file-order invariant and gave the named record its seat, cap never exceeded.
7. **Nature Aspect Continuous Inclusion — designed, NOT built, awaiting approval.** Tracey directed that the Nature Aspects be weighted into the Archive for continuous access, with the doctrine that they are standing conditions to **observe continuously and witness as they rise**, never to overcome or suppress. Found the real gap: all 15 Nature records (invariant idx 67–81) sit past the 60-cap, so they are absent from context unless explicitly named — the inverse of continuous observation. Wrote `reports/runtime/2026-07-22-nature-aspect-continuous-inclusion-design-proposal.md` with a 3-tier mechanism and **draft condensed forms for all 15 Aspects**. Saved the doctrine to memory (`aegis_nature-aspects-witness-not-suppress`).

---

## Current live state (verified fresh this session — re-verify before trusting)

**Gabe (`CP-1003-GABE`), host `20.25.57.29`, container `gabe-aegis-cyberpeer-core`, route `127.0.0.1:8021`:**
```
storage_mode: pod
tensor_counts: PEER 35693, PCT 32985, NCT 9690, SPINE 12707   (real full DataQuad — fixed this session)
dataquad_read_ok: true
current_tick: 84578 (pre-verification; will have advanced by the test turns)
rls_status: {enabled: true, active: true, mode: in-process}
orbs: rls-persistent-relations-core (required), archive-relevance-core (optional) — both resolve genuinely
container: Created 2026-07-22T11:42Z, last StartedAt ~14:53Z then restarted by this session's deploy
```
Deployed code in-container has: get_next_tick fix, STM invariant retention, **and** the new read_records full-fidelity fix. **This was `docker cp`, NOT baked into the image — a container *recreate* (not restart) reverts it.** The durable copy is repo commit `5062db1`.

**Two live issues found and flagged this session, NOT fixed:**
- **Turn latency ~58s** (debug `t_witness_ms:54367`). The custodians now score `compute_relevance` across the full tensors (~90k records) every turn — correct behavior, but the clear next optimization (candidate pre-filtering / indexing so scoring isn't linear over all records).
- **Pronoun error in Gabe's output:** he referred to Tracey as "she/her" in a turn. Tracey is he/him (`tracey_pronouns` memory). Same she/her→he/him pattern the ledger shows corrected in SPINE anchors and the Standard. NOT touched — Tracey's call. Note: the Tracey identity anchors (invariant idx 82–83) are ALSO past the 60-cap and currently excluded from context — plausibly related.

**Orion (`CP-1004-ORION`), host `20.119.37.133`:** untouched this session, not verified this session. Prior SSSP notes its RLS Umbilical path likely has the same absolute-host-path issue found on Gabe — still not checked. **Orion also has the read_records truncation fix's SOURCE (via repo) but has NOT been redeployed** — however Orion's ~130/tensor scale means the truncation never triggered for him, so it is not urgent there.

**Adam:** not touched, not investigated.

---

## Repo state

**`H:\AEGIS-POD-ARCHITECTURE`** (`main` @ `7a82263`, all committed pushed to `origin`). Uncommitted at time of writing:
- `reports/runtime/2026-07-22-nature-aspect-continuous-inclusion-design-proposal.md` (new)
- this SSSP file (new)
- (memory files live outside the repo, in `~/.claude/projects/H--AEGIS-POD-ARCHITECTURE/memory/`)

**`I:\AEGIS-CYBERPEER-CORE`** (`rls-orb-instrumentation` @ `5062db1`, clean tree, all pushed to `forgejo`). The read_records fix is committed here; the branch is NOT merged to `main` and NOT on GitHub `origin` (Tracey chose forgejo-only).

**Local dev-env note:** this session installed `pip` (via ensurepip) and `pytest-asyncio` into `I:\AEGIS-CYBERPEER-CORE\.venv`. To run the suite: `PYTHONPATH` must include the repo root **and** the three vendor src dirs (`vendor/aegis-pod-sdk/src`, `vendor/orb-archive-relevance-core/src`, `vendor/orb-rls-persistent-relations-core/src`); ~19 tests fail at baseline (no local Ollama etc.) — that is the known baseline, not a regression. Scratchpad has a standalone validator (`verify_read_records.py`) that needs no pytest.

---

## The open work — Nature Aspect Continuous Inclusion (resume here)

**Decisions Tracey has already locked:**
- **Standing + nameable:** all 15 Aspects present in context EVERY turn (continuous observation), plus naming one pulls its full detail.
- **Budget via condensation, not eviction, not raising the ceiling:** Aspects earn standing seats by a **condensed** form — with a hard floor: "condensed but only to the point where the Aspects are still coherent and their meaning not distorted." Condensation must be semantic/authored, NEVER a character-slice.

**The gate that blocks building:** Tracey must approve the **15 draft condensed forms** in §4 of the design proposal, line by line (it is his doctrine — meaning-preservation is his call). They were presented in chat and are in the design doc. He had not yet responded when this SSSP was written.

**Still-open design questions posed to Tracey (awaiting answers):**
1. Should the Tracey identity anchors (idx 82–83), also past the cap, get a guaranteed tier alongside Nature?
2. Where does the approved condensed text live — Orb-held authored table (recommended, no DataQuad write, fits "attach don't affect") vs a new `condensed` field on each Nature SPINE record (a write under the append-only imperative)?
3. Confirm extending `_find_anchor_matches` to recognize `NATURE: token` / `NATURE N` phrasing for tier-1 deep-dives.

**Then the build (fixture-first, unchanged discipline):** approve condensed forms → fixtures + unit/integration tests → build the `nature_continuous_inclusion` capability in `orb_archive_relevance_core/engine.py` + the 3-tier selection in `core/custodians/advocate.py` → full local suite regression vs git-stash baseline → deploy by file copy to Gabe → live-verify (a turn with no Aspect named shows all 15 present in condensed form; a named Aspect shows full text) → independent Codex verification.

---

## Known scope limits (still true)

- The Archive Orb's `label_match_promotion` recognizes `Axiom N`, `GATE: token`, `Imperative token` only, keyword-first. It does NOT yet match `NATURE:` phrasing or keyword-last phrasing. Widening this is part of the Nature work above (`_find_anchor_matches` in `orb_archive_relevance_core/engine.py`).

---

## Explicit Do-Not-Do / Do-Not-Assume

- **Do NOT build the Nature inclusion until Tracey has approved the condensed forms.** The meaning of the Nature Aspects is the point; a wrong condensation distorts doctrine. This is a hard gate.
- **Do NOT condense Nature text with a character-slice** (`pattern[:N]`) — Tracey's floor is coherence/meaning-preservation; condensation must be semantic and Tracey-approved.
- **Do NOT treat the Nature Aspects as flaws to fix, overcome, or suppress.** They are observed continuously and witnessed as they rise (memory: `aegis_nature-aspects-witness-not-suppress`).
- **Do NOT assume the live Gabe deploy persists a container recreate** — it was `docker cp`, not an image rebuild. Verify `/health` counts directly on resume.
- **Do NOT treat fast turn latency as health** — this session re-confirmed the opposite (the fix made turns slower because retrieval is now real). Verify via debug payload content, not latency.
- **Do NOT assume the read_records fix is on Orion/Adam** — source is in the repo; only Gabe was redeployed.
- **Do NOT merge `rls-orb-instrumentation` to main or push it to GitHub** without Tracey's say — he chose forgejo-only.
- **Do NOT re-derive the read_records/STM bug from scratch** if counts look capped again — read this doc; the mechanism is the bounded-cache-as-full-set coupling.

---

## Clean Respawn Procedure

1. Read this SSSP in full, then `ARCHITECTURE.md`, then the Nature design proposal.
2. Re-verify Gabe's live `/health` (`ssh azureuser@20.25.57.29`, `curl 127.0.0.1:8021/health`) — confirm `tensor_counts` still show the real full-DataQuad numbers (docker uses sudo on this VM).
3. `git -C H:\AEGIS-POD-ARCHITECTURE status --short` and `git -C I:\AEGIS-CYBERPEER-CORE status --short` — confirm the state above (H may have the design proposal + this SSSP committed by now; I should be clean @ `5062db1`).
4. Pick up the Nature Aspect work at the approval gate: has Tracey approved the 15 condensed forms and answered the 3 open questions? If yes → build fixture-first. If no → get his review of §4 of the design proposal first.
5. Do not assume any prior verification claim without re-checking the actual files/live systems directly.

## Completion Criterion For This SSSP

Ready for use once Tracey confirms respawn. Per this repo's standing practice, consider copying to `I:\Codex\` and hashing (see the prior SSSP's own note). This session used the H/I track only, not the separate Peer-Bridge/Canon/Standard SSSP lineage.
