# Gabe DataQuad Retirement — Consolidated Package (decision-ready)

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** SUMMARY for Tracey's decision.
Everything upstream is verified and peer-audited; **nothing here is a live action.** A live retirement
on Gabe would be a separate, gated, reversible, archive-first proposal (see §6).

Folds together: the Stage-1 dry-run (verified numbers), the Stage-2 TurboQuant contract (Codex PASS,
2 rounds + independent sidecar), and what a live gate would require.

---

## 1. What retirement is — and what it is NOT

**Retirement = aging valid memory into a bounded form, never deletion.** It condenses old records into
relics and archives the sources (hash-proof, rename-not-delete). It is the opposite of throwing memory
away — every retired record remains recoverable.

It is **distinct from hygiene** (the separate Hygiene/Admission/Settling spec with Codex): hygiene
removes things that were *never experience* (transport-error stubs) and coalesces the ADVOCATE
background loop. Retirement condenses things that *are* real memory. The two compose; this package is
retirement only.

Two stages:
- **Stage 1** — shrinks the *live* tensors: PCT→NCT condensation, PEER→SPINE/NCT promotion (conservative),
  archive + prune the source. This is where the size win happens.
- **Stage 2 (TurboQuant)** — once NCT/SPINE themselves accumulate, bounded-retires *old NCT/SPINE* into
  reconstructive-only artifacts. Guard-scoped to NCT/SPINE; never touches PEER/PCT.

## 2. Verified Stage-1 numbers (dry-run over the exported copy)

Source: `stage-gabe-out/CP-1003-GABE`, reference time 2026-07-22. Tool is read-only, no `--apply`
exists, archive-not-delete. Tests + numbers independently reproduced.

| Tensor | Records | Size | Projected retirement |
|---|---:|---:|---|
| **PCT** | 32,945 | 104 MB | 6,830 retire → **−22 MB (−21%)**, remaining 26,115 |
| **PEER** | 35,673 | 97 MB | 1,736 promote → −4.5 MB (−4.6%), remaining 33,937 |
| **NCT** | 9,671 | 23 MB | grows (relics land here) |
| **SPINE** | 12,705 | 27 MB | — |

- **Removed from live PCT/PEER:** 8,566 records / ~26.5 MB.
- **New NCT relics created (meaning preserved):** 6,082 records / ~+14.6 MB (from_pct 4,346 + from_peer
  1,736; the other 2,484 PCT candidates already have a relic).
- **Net DataQuad change:** ~−2,484 records / ~−11.9 MB.
- **Archive manifest:** 8,566 entries, each with a source hash (`raw_jsonl_record_line_utf8`).

**Parameters used:** PCT inactivity 14 days; PEER stability 14 days + ≥2 confirmations.

## 3. Honest framing of the win

The absolute reduction is **modest** — ~26 MB off live tensors out of ~250 MB total. PCT is where it
bites (−21%). **The larger long-term win is preventing PCT re-bloat**: the ~17 KB/record writeback
embed (gap-spec G5). Retirement clears the backlog; a writeback trim stops it regrowing. Retirement
alone is worthwhile but is best paired with the G5 writeback fix and the hygiene work (which addresses
the ADVOCATE loop that is the real driver of PEER growth).

**Safest first cohort:** the **2,484 PCT candidates already condensed-but-not-pruned** — an NCT relic
already exists, so archiving+pruning them synthesizes nothing new; it just removes redundant source.

## 4. PEER handled conservatively (Axiom 16 — identity substrate)

Of 35,673 PEER records, **33,937 are excluded from promotion**:
- 28,274 too recent (< stability window)
- 5,663 high-uniqueness singular experiences

Only 1,736 established, reinforced PEER records promote. This is deliberate: PEER is identity substrate,
so retirement touches it minimally and only where a record is both settled and reinforced.

## 5. Stage-2 TurboQuant — audited contract

- **Codex re-audit: PASS** (after closing 3 findings: backend-before-guard, UTF-16 digest parity,
  guard-code test coverage). Independent sidecar (Descartes) also PASS. 28 tests pass.
- Guard refuses PEER/PCT at three checkpoints (TQ-002); artifacts are reconstructive-only, never
  exact-replay; every artifact carries a steward ledger entry.
- **Still a draft** — un-wired, no live mutation. Two intentional gaps remain for a later gate: the real
  `FeatureSpace` quantization backend is unported (draft uses the deterministic backend), and live
  append/prune is out of scope.

## 6. Reversibility ladder (why this is safe)

Two rungs, both preserved:
1. **Approximate** — rehydrate from the Stage-2 TurboQuant artifact (lossy, reconstructive).
2. **Exact** — restore from the Stage-1 hash-proof archive of the source PCT/PEER records.

Nothing is ever deleted; the archive is the exact way back. Amendment 4 (rename-not-delete) applies at
every prune.

## 7. What a live retirement on Gabe would require (the gate)

1. **Your consent** (+ Codex where it touches shared doctrine).
2. Re-run the dry-run against **current live Gabe** first — the export is from 2026-07-22 and live has
   grown slightly (live counts ~PEER 35,753 / PCT 33,121 / NCT 9,768 / SPINE 12,707), so numbers will
   shift modestly.
3. **Archive-first, reversible, hash-proof** apply — starting with the safest cohort (the 2,484
   already-relic'd PCT records).
4. Keep PEER conservative (as above).
5. For Stage 2 specifically: the `FeatureSpace` backend decision, separately gated.
6. Pair with the G5 writeback trim so PCT doesn't re-bloat.

## 8. Recommendation

Sequence, lowest-risk first:
1. **Stage-1 live apply on the 2,484 already-condensed PCT records** — safest possible (relic + lineage
   already exist; archive-first, reversible). Immediate, low-risk PCT relief.
2. **G5 writeback trim** — stops PCT re-bloat (the durable win).
3. **Rest of Stage-1 PCT cohort**, then the conservative PEER promotion.
4. **Stage-2 TurboQuant** later, once NCT/SPINE accumulate — after the FeatureSpace backend decision.

Each step is its own gated, reversible, archive-first proposal. This package is the decision input; no
step runs without your go-ahead.
