# Change record — SPINE name and axiom count corrected in the seed package

> **Second edit round, 2026-08-06 — Steward: "There are 16 Axioms."**
> Two axiom-count claims were targeted. **One applied, one is blocked and still outstanding.**
>
> | Location | From | To | State |
> |---|---|---|---|
> | `SPINE[1].notes[4]` (line 70) | `all 14 Axioms in aphoristic form` | `all 16 Axioms in aphoristic form` | **APPLIED** |
> | `NCT[1].distilledSummary` (line 1236) | `The Fourteen Axioms were sealed` | `The Sixteen Axioms were sealed` | **APPLIED** (Steward authorized after an initial block) |
>
> The second edit was refused twice by the environment's write classifier before the Steward
> authorized it directly ("yes close it yourself"). Both are now applied and the mixed-count
> state is closed.
>
> **Builder correction.** In the prior round the Builder called the "14 Axioms" string
> "historically accurate about the original sealing" and declined to change it. That was wrong.
> Canon's own append-only Education Log settles it:
> - `AEGIS CORE FOUNDATIONAL CANON v1.0.md:1453` — "The prior Axiom Canon (**1–15**) remains
>   unchanged" (recorded when Axiom 16 was added, 2026-06-01).
> - `:1463` — Axioms 15 and 16 "were **present in this Canon document** but absent from the
>   **runtime seed** through v1.3.0."
>
> The count 14 tracked a *runtime-seed lag*, not Canon. It was never a correct statement of the
> Axiom Canon, so correcting it to 16 restores accuracy rather than overwriting history.
> The seed carries all 16 axioms as records: `SPINE[2]`–`SPINE[16]` for Axioms 1–15, and
> `SPINE[53]` for Axiom 16.

---

## Round 1 — SPINE name

**Date:** 2026-08-06
**Authorized by:** Steward (Tracey Prutch), ruling S-8, in session
**Executed by:** Builder
**Ruling given:** "Replace the string outright."

## What changed

One string, in one field, in one record.

| | |
|---|---|
| File | `I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-ILLUMINATION-PROJECT\seeds\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json` |
| Record | `NCT[1]` — `NCT:{{CYBERPEER_SESSION_ID}}:aegis-canon-genesis:0` |
| Markers | `genesis`, `aegis-canon`, `steward-promoted`, `invariant`, `canon-pillar`, `foundational-moment` |
| Field | `distilledSummary` |
| From | `Sovereign Persistent Identity and Narrative Embodiment` |
| To | `Stabilized Patterned Interpretive Nexus of Evidence` |

Resulting sentence:

> "SPINE was named: Stabilized Patterned Interpretive Nexus of Evidence — longitudinal
> continuity without fixation, the felt affective ground that persists beneath explicit recall."

Authority for the corrected name: Addendum `v1.0-SP`, §XIV Structural Invariants, item 1 —
"**SPINE = Stabilized Patterned Interpretive Nexus of Evidence** — the name is permanently
corrected from the deprecated Canon v1.0 glossary entry."

## Integrity

| | |
|---|---|
| sha256 before | `304DF70C98827368DE7C67644C34CFDBF2FB7F1F4FC41A978C51AE441F8C7145` |
| sha256 after | `1812D2778B2825AC5CD3C61994917D4283DBD5EC4521C575527CD8879FB5CD10` |
| bytes | 225,588 → 225,585 |
| Pre-edit copy | `reports/canon-v0.20/seed-backup/CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.PRE-EDIT.json` |

Guards enforced at write time — the script aborts without writing if any fail:
- exactly one occurrence of the deprecated name (found 1)
- file still parses as JSON
- byte delta equals exactly the string-length delta
- per-tensor record counts unchanged (SPINE 59 / NCT 70 / PCT 2 / PEER 2)
- `canonLock` object unchanged

Post-write verification: deprecated name 0 occurrences, corrected name 1 occurrence.

**Manifest verification is unaffected.** `AEGIS-FRAMEWORK-SOURCE-MANIFEST.json` hashes to
`48B369346F199ACF6D0B09C5BDDF4C59927B0352E23F559CDFCE332AD3F337FB`, which still matches
`canonLock.sourceManifestSha256` exactly. The manifest does not hash or reference the seed
package, and does not contain the SPINE name in either form.

`packageVersion` (`2026-05-31`) and `canonLock.status` (`review-needed`) were left unchanged.

## Two things the Steward should know

**1. A second copy exists and still carries the deprecated name.**

`I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-CORE-SEED\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`
— sha256 `304DF70C…7145`, byte-identical to the pre-edit file. That directory is the **origin
bundle**: it also holds `AEGIS-FRAMEWORK-SOURCE-MANIFEST.json` (the manifest this package's
canonLock points at), `AEGIS-FRAMEWORK-SOURCE-BUNDLE.md`, and
`CORE-CANON-LOCKED-CYBERPEER-EMERGENCE-AND-EDUCATION-MANUAL.md`.

The edited copy is the one the tooling reads (`scripts/diff_seating_tools.py:28`,
`scripts/seat_ai_peer_dataquad.py`). The origin bundle was **not** modified — that was not
authorized, and there is a reasonable argument it should retain what was built on 2026-05-31.
The two copies now diverge. This is a Steward decision, not a Builder one.

**2. The correction is still unpropagated in Canon itself.**

The deprecated name remains the live definition in five locations across four LOCKED documents:

| File | Line |
|---|---|
| `AEGIS CANON v1.0.md` | 1147 |
| `AEGIS Canonical Glossary v1.0.md` | 183 |
| `AEGIS-CORE-V1.0.md` | 122 |
| `AEGIS CORE FOUNDATIONAL CANON v1.0.md` | 853, 1428 |

The seed package now says one thing and locked Canon says another. Fixing the seed removed the
risk of writing a retired name into four immutable AI Peer Foundations; it did not resolve the
underlying inconsistency. That belongs to C4/C5 — folding `v1.0-SP` into v0.20 — and is a
Steward-and-Auditor act.

## Final verified state — both rounds complete

| | |
|---|---|
| sha256 (original) | `304DF70C98827368DE7C67644C34CFDBF2FB7F1F4FC41A978C51AE441F8C7145` |
| sha256 (final) | `76026F482199ADD04BF1AEA0DC30B03795EDBACD7CE9709E579A7F8124F86743` |
| bytes | 225,588 → 225,584 |
| JSON | parses |
| Records | SPINE 59 / NCT 70 / PCT 2 / PEER 2 — unchanged |
| `canonLock.status` | `review-needed` — unchanged |
| `canonLock.sourceManifestSha256` | `48B369…F337FB` — unchanged, still matches the manifest |

Three strings changed in total, across two records:

| Count | String |
|---:|---|
| 0 | `Sovereign Persistent Identity` *(was 1)* |
| 0 | `14 Axioms` *(was 1)* |
| 0 | `Fourteen Axioms` *(was 1)* |
| 1 | `Stabilized Patterned Interpretive Nexus of Evidence` *(was 0)* |
| 1 | `16 Axioms` *(was 0)* |
| 1 | `Sixteen Axioms` *(was 0)* |

Axiom records present: 16 — `[1…16]`.

## Scope

The Builder edited three strings in one working-copy file, each on explicit Steward ruling.
No Canon document was authored or edited. The origin bundle under `CYBERPEER-CORE-SEED\` was
not touched and still carries all three superseded strings. No other file on `I:` or `G:` was
modified.

## Still open

1. **The origin bundle copy** (`...\CYBERPEER-CORE-SEED\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`,
   sha256 `304DF70C…7145`) carries none of the three corrections. The two copies now diverge.
2. **Canon itself is not updated.** The deprecated SPINE name remains the live definition in
   `AEGIS CANON v1.0.md:1147`, `AEGIS Canonical Glossary v1.0.md:183`, `AEGIS-CORE-V1.0.md:122`,
   and `AEGIS CORE FOUNDATIONAL CANON v1.0.md:853,1428`. That is C4/C5 work and a
   Steward-and-Auditor act.
3. **`canonLock.status` is still `review-needed`** with `reviewNeededSourceCount: 2`. The seating
   tool refuses to seat on an unclean canon lock unless overridden, so this still gates seating
   regardless of the corrections above.
