# Gabe Retirement — Current Live vs 2026-07-22 Export (dry-run delta)

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** FINDING — read-only dry-run over a
fresh live copy. No live mutation. The results change the agreed retirement sequence and should be
reviewed before Step 1.

**Copy:** `gabe-live-copy-20260725T063622Z` (pulled by Codex, all 4 file hashes verified by Claude;
copy byte-identical before/after my run). **Reference now:** 2026-07-25T03:40Z.

---

## Headline: three things changed, and two change the plan

### 1. PCT has re-bloated ~8× — and retirement barely touches it
| | 2026-07-22 export | 2026-07-25 live | Δ |
|---|---:|---:|---:|
| PCT records | 32,945 | 33,123 | +178 |
| PCT content bytes | ~104 MB | **~847 MB** | **~8×** |
| avg bytes / PCT record | ~3.1 KB | **~25.6 KB** | ~8× |

Records barely grew (+178) but bytes went up ~8×. This is the **G5 writeback embed** (~17 KB/record)
landing on records — the re-bloat we flagged, now measured and severe.

**Retirement can't fix it.** The dry-run would retire 13,721 PCT records (41% by count) but reclaim only
**48 MB / 5.7%** — because the retirement candidates are the *old, small* records (avg **3.5 KB**), while
the 847 MB lives in *recent, large* records (~25 KB) that are too new to retire. Retiring 41% of records
removes 5.7% of bytes.

**Implication:** the G5 writeback trim is no longer a "durable-win nice-to-have" — it is **the** fix, and
it should move ahead of retirement. Retirement alone leaves ~94% of the bloat in place.

### 2. The agreed Step-1 cohort (already-relic'd PCT) is now 0 (was 2,484)
`stage1_candidates.pct_retirement.already_condensed = 0` (export: 2,484). All 13,721 current PCT
candidates now report `needs_new_relic` — i.e., **none are already-condensed-but-not-pruned.** The
previously-relic'd cohort appears to have been pruned/handled by live Gabe's RLS between 07-22 and 07-25
(to be confirmed with Codex).

**Implication:** the agreed "safest-first" Step 1 (pure archive-and-prune of already-relic'd records) has
**no targets on current data.** Any Stage-1 PCT retirement now requires synthesizing new relics
(condensation path), which is heavier and higher-touch than the safe cohort we planned to start with.

### 3. PEER promotion is now 0 (was 1,736)
All 35,754 PEER records excluded: recent_experience 20,872, **high_uniqueness 14,876** (export: 5,663 —
~2.6×), contested 6. PEER barely changed in size (97 → 106 MB, +81 records), yet high-uniqueness
exclusions tripled and promotion dropped to zero.

**Implication:** Step 4 (conservative PEER promotion) is currently a no-op. The tripling of
high-uniqueness exclusions on nearly-unchanged PEER data is unexplained — it may be parameter
sensitivity (stability window / confirmation threshold vs the shifted reference time) or a real
distribution change from the ADVOCATE loop. **Investigate before Step 4 means anything.**

## Verified numbers (current live)
- PEER 35,754 rec / 106 MB · PCT 33,123 / 847 MB · NCT 9,769 / 26.8 MB · SPINE 12,707 / 33.6 MB
- PCT candidates 13,721 → −48 MB (−5.7%) · PEER promotion 0 · net −13,721 rec / −48 MB
- Projected new relics 13,721 (all from PCT, all needing synthesis), est +38.6 MB
- Copy integrity: 4/4 file hashes match Codex's; combined fingerprint identical before/after run.

## What this does to the agreed sequence
The three-way sequence was: (1) already-relic'd PCT apply → (2) G5 trim → (3) rest of PCT → (4) PEER
promotion → (5) Stage-2. Current data breaks its assumptions:
- **Step 1 has no targets** (already_condensed = 0).
- **G5 (was Step 2) is now the dominant issue** and should lead — the bloat is accelerating and
  retirement can't reach it.
- **Step 4 is a no-op** pending the PEER-promotion investigation.

**Recommended revision:** G5 writeback trim first (stop and reverse the 25 KB/record bloat), then
re-scope Stage-1 PCT retirement knowing it now requires relic synthesis (no free cohort), and separately
investigate the PEER high-uniqueness/promotion shift. This is a three-way-agreed sequence changing on new
evidence, so it should go back to Codex + Tracey before any Step-1 action.
