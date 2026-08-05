# RLS Reconciliation (replay parity + foundational-canon reachability) — Claude Audit

**Created:** 2026-07-26. **Author:** Claude (Opus 4.8). **Status:** AUDIT — **PASS on both pre-deploy
items; RLS fix now cleared for the Tracey deploy gate.** Read-only; no live action. Audits Codex packet
`2026-07-26T080930Z-rls-reconciliation-local-fix`.

---

## Verified independently
- **Hashes match** Codex's: scoring.py `C9B270BD` (extracted **and** vendored — byte-identical),
  replay harness `8873217C`, test_scoring_bounds `327E6564`.
- **Tests pass on my run:** extracted `test_scoring_bounds.py` + `test_engine_with_fakes.py` → **10
  passed**; vendored `test_rls_selection_bounds.py` + `test_g5_pct_writeback_trim.py` → **5 passed**.

## Item 1 — Replay parity: RECONCILED
Codex added a deterministic harness (`replay_rls_selection.py`) that uses the **real Pod loader**
(`DataQuadStore.read_records()` → `pod.unwrap` → concrete `PEER/PCT/NCT/SPINERecord`), not a shim. I ran
**his harness myself** against the staged copy and reproduced his numbers exactly:

| Prompt | My run (real loader) | Codex | My earlier shim |
|---|---|---|---|
| "name one axiom" | pre 18 / post 18 (SPINE 17, NCT 1) | 18 | 0 |
| "Axiom-15 repair" | pre 751 / post 64 (overflow 687) | 751→64 | 39 |

**Conclusion:** my earlier 0/39 was a hand-rolled `RecordLike` shim artifact (Pod-wrapper/`body`
unwrapping + field/tick preservation), confirmed by Codex's sidecar (Boole). The real loader is
authoritative; **we now agree.** Parity closed.

## Item 2 — Foundational-canon reachability: FIXED and verified
The affordance (scoring.py:75-78, 95-97) is **tightly gated** — I read it: it sits *inside* the
`overlap > 0 AND tensor == SPINE` block, and further requires (a) a canon-intent query term
(`axiom/canon/canonical/identity/nature/principle`) and (b) a `spine:foundation:` id, for **+0.02**. It
therefore **cannot push unrelated records over threshold** — it only nudges genuinely-relevant
foundational canon that already has a real token match.

My real-loader replay confirms the effect: for "name one axiom," the **actual foundational AXIOM canon
now surfaces at 0.260** — `AXIOM:1-balance`, `2-extremes`, `3-force`, `4-flow`, `5-awareness`,
`6-choice`, `7-integrity`, … (reason: "…SPINE source trust, Foundational canon affordance"). Previously
they sat at 0.24, just under 0.25. A peer asked "name an axiom" now reaches its own canon. The specific
"Axiom-15" query still tops `AXIOM:15-repair` (0.44), and unrelated records still don't select on
structural bonuses alone (affordance requires overlap).

## Verdict: PASS — cleared for the deploy gate
Both pre-deploy items I raised are resolved and independently verified. Combined with the earlier PASS on
the bounding objective, the RLS unbounded-selection fix is **complete and audited.** Nothing further from
me blocks it.

**Deploy to live Gabe remains a separate Tracey gate** (and, per the Part-A lesson, should not open on
"implements"). When it deploys, the earlier forward note still applies: measure relation-store
growth/turn under the bounded selection before any broader live Pod/RLS activation.

## Boundary
Read-only audit + independent real-loader replay. No live DataQuad/VM/runtime touched; no deploy.
