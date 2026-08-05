# RLS Unbounded Selection Fix — Claude Audit

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** AUDIT — **PASS on the bounding
objective; two items to reconcile before the deploy gate.** Read-only; no live action. Audits Codex
packet `2026-07-25T212013Z-rls-unbounded-selection-local-fix`.

---

## Verified independently
- **All 6 file hashes match** Codex's (extracted-Orb scoring `C40D574B`, engine `07480B03`, relevance
  `BC645D79`, test `F4313FDF`; vendored scoring `C40D574B`, engine `3CA4097C`).
- **Tests pass on my run:** `test_scoring_bounds.py` + `test_engine_with_fakes.py` → 9 passed.
- **Scorer design confirmed by reading:** every structural bonus (NCT-recall, recency, SPINE-trust,
  PCT-support) is now gated on `overlap > 0` — nothing selects without a real textual token match;
  stopwords (incl. `gabe`/`aegis`/`briefly`/`recall`/`name`/`one`) removed; match = `min(0.5,
  overlap*0.12)`; threshold 0.25; selection sorted by relevance, top-64, overflow → `rejected_refs`. This
  is a genuine scorer fix + relevance-ranked bound, not a blind cap. Good.
- **Root cause is correct** and reproduces the live number: the old scorer's tensor/recency bonuses
  cleared the 0.25 threshold with zero textual match (NCT recall+recency=0.3; SPINE source+recency=0.25),
  producing the structural 26,090-selection. Confirmed against staged data.

## Objective: PASS
The unbounded selection is fixed. Selection drops from **26,090** to single/low-double digits, structural
over-selection is eliminated, and a *specific* query preserves relevance — `AXIOM:15-repair` surfaces at
the top of prompt 2 in my replay (0.36) as in Codex's (0.44).

## Two items to reconcile before deploy

### 1. Independent replay counts differ from Codex's (verification-parity gap)
Running the shipped `compute_relevance` over the same staged copy
(`gabe-live-copy-20260725T063622Z`), intent=recall:

| Prompt | Codex reported | My independent replay |
|---|---|---|
| "…name one AEGIS axiom…" | 1 selected (NCT) | **0 selected** |
| "Find details about Axiom-15 repair patterns" | 731 pre-bound → 64 | **39 pre-bound (all SPINE) → 39** |

My prompt-2 correctly ranks `AXIOM:15-repair` at the top, so the harness works — but my counts don't
match his. Most likely cause: I built a hand-rolled `RecordLike` shim from the JSONL (camelCase→snake_case
field mapping) rather than the real record loader, so text fields / recency may map differently. **I
cannot independently confirm his exact 1 / 731→64 numbers.** Recommend reconciling the replay harness
(or Codex sharing his replay script) so both sides agree before deploy. Not evidence of a defect in the
fix — a parity gap in verification.

### 2. Foundational canon may be under-reached for generic queries (grounding concern — robust)
This finding holds regardless of the shim gap. For a **generic** canonical query ("name one axiom"),
the **foundational AXIOM canon records score 0.24 — just under the 0.25 threshold** (34 foundational
AXIOM records scored; 0 clear threshold; best 0.24, `SPINE:foundation:layer2:AXIOM:cyberpeer-governed-
identity`). A foundational SPINE AXIOM record gets overlap-1 on "axiom" (0.12) + SPINE-trust (0.12) =
0.24, one hair below the cut, with no recency (tick 0).

So the bounded scorer may **under-reach the actual foundational canon** for generic canonical/identity
queries — the peer asked "name an axiom" could get 0–1 records and *not* the AXIOM canon itself. This is
the same class as the MemorySearch **Gap B** (Layer-1/foundational canon reachability). It argues for:
- ensuring foundational/canon records are reachable for canon/identity intents (a small
  canon/foundational-intent affordance, not a return to unbounded selection), and
- **coordinating this with the MemorySearch Phase 5.1 Canonical Subject Resolver / foundational-
  reachability work** — both are the same underlying need.

## Recommendation
The bounding fix is correct and safe and achieves its goal — I'd PASS it to deploy **after**: (a)
reconciling the replay harness so counts agree, and (b) deciding the foundational-canon reachability
affordance (or explicitly accepting that generic canonical queries return few/no refs for now).
Deploy to live Gabe remains a separate Tracey gate, so these fit naturally before it.

## Boundary
Read-only audit + independent staged replay. No live DataQuad/VM/runtime touched; no deploy.
