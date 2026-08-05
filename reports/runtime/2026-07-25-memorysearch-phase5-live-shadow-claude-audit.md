# MemorySearch Phase 5 — Live Gabe Shadow Deployment: Claude Audit

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** AUDIT — verdict PASS with the
performance concern re-scoped. Read-only audit; I did not reach the live Gabe VM (that would be a gated
live action). Live-only facts are marked as **attested by Codex**; everything else is independently
verified here.

Audits Codex packet `2026-07-25T034942Z-memorysearch-phase-5-live-gabe-shadow-deployment-ready-for-audit.md`.

---

## Independently verified (from committed source)
- Commit `3d83fae` "Attach MemorySearch shadow mode for Gabe" is **HEAD**, **working tree clean**.
- All six deployed-core hashes match Codex's message byte-for-byte (thinking.py `4F7F64E3…`,
  memorysearch_loader.py `BBE901DF…`, session_repair_loader.py `AC3E986E…`, test `BB742921…`,
  entrypoint.py `3303E619…`, search.py `767697C8…`).
- Evidence doc matches (`9CD69241…`).
- The MemorySearch files are **byte-identical to the code I already audited PASS** (Phase-5 code audit,
  2026-07-25T033543Z). The code-level boundary guarantees carry over unchanged.
- **Offline reproduction matches live exactly:** my offline run of the broad canon query selected the
  identical five records the live `/turn` selected (session:17849, session:17848,
  GATE:nostalgic-lineage-integrity, rls-promoted:44, rls-steward:17). The offline export is a faithful
  mirror of live behavior.

## The five audit points

1. **Scope boundary (Gabe-only; Orion off)** — PASS. Code: `_DEFAULT_PEER_IDS={CP-1003-GABE}`, any
   non-allowlisted peer → `off` (test-proven). Live: container env
   `AEGIS_MEMORYSEARCH_PEER_IDS=CP-1003-GABE`, in-container check `mode_for_orion=off` — **attested by
   Codex**. Even if an Orion turn hit this code, it returns `off` without an explicit allowlist, so the
   guarantee is structural, not just configuration.
2. **Prompt boundary (no injection in shadow)** — PASS. `prompt_block` only in `inject`; both the live
   in-container check and the live `/turn` show `prompt_injected=false`.
3. **Record boundary** — PASS with note. The loader writes **no records of its own**; thinking.py embeds
   the MemorySearch diagnostic into the existing turn's PEER/PCT record via `to_record_value()`. Note:
   this means the search-event packet now rides inside PEER/PCT turn records — not a violation, but it
   does add MemorySearch content to those tensors; worth tracking as the DataQuad grows.
4. **Deployment boundary (live Gabe healthy)** — PASS (attested). Health `ok=true`, qwen3:14b,
   storage_mode=pod, tensor counts PEER=35753/PCT=33121/NCT=9768/SPINE=12707, pod_manifest
   `A3C33074…` — **attested by Codex**; not independently reachable from here without a gated live
   action. One real live-tree change beyond MemorySearch: `session_repair_loader.py` was copied to Gabe
   (its tree was missing it; live thinking.py imports it). I read it — it mirrors `rls_loader.py`,
   resolves the Session Repair Orb engine from the pod manifest with a clean fallback, and has **zero**
   MemorySearch/inject/Orion/scope references — boundary-neutral. Flagged only because it is a change to
   the deployed tree.
5. **Performance concern — RE-SCOPED (this is the important audit finding).**
   - Measured: the broad all-tensor MemorySearch search takes **~14.3s offline over 90,994 records**
     (single-thread, no model). The narrow single-tensor live check was **2.8s**.
   - The full cold `/turn` exceeded **240s**. Since the search is ~14s and the narrow path is ~3s, the
     **240s is dominated by qwen3:14b cold model generation, not by MemorySearch.**
   - **Therefore:** narrowing the classifier scope for acronym/canon questions (Phase 5.1 Subject
     Resolver) is worthwhile — it cuts the search from ~14s to ~2–3s *and* fixes relevance — **but it is
     not, by itself, sufficient to bring a cold `/turn` under 240s.** The turn/model budget is a
     separate driver and must be measured and budgeted independently (note: `MODEL_TIMEOUT_S` is now
     env-configurable, commit `01b97a4`). Do not conflate "narrow the search" with "fix the timeout."

## Verdict
**PASS.** The live Gabe shadow deployment is sound on all boundaries (code-verified + Codex-attested for
live-only facts), inject is correctly off, and my offline method reproduces live behavior exactly. I
concur with Codex: **do not flip `inject`** — and the gate should require *both* (a) the Phase-5.1
search-scope/quality refinement **and** (b) a measured turn/model budget, since the 240s is
model-dominated, not search-dominated.
