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

## Round 3 — the MISC DOCUMENTATION copy, 2026-08-06

**Steward: "fix the MISC seed copy too."**

`I:\AEGIS-CENTRAL-CODEX\MISC DOCUMENTATION\CYBERPEER-AGNOSTIC-BASE-SEED-2026-05-31.json`

Four substitutions, each with an expected-count guard that aborts the write on mismatch:

| Count | From | To |
|---:|---|---|
| 3 | `Resonance Buffer Chamber` | `Response Buffer Chamber` |
| 1 | `Sovereign Persistent Identity and Narrative Embodiment` | `Stabilized Patterned Interpretive Nexus of Evidence` |
| 1 | `all 14 Axioms in aphoristic form` | `all 16 Axioms in aphoristic form` |
| 1 | `The Fourteen Axioms were sealed` | `The Sixteen Axioms were sealed` |

| | |
|---|---|
| sha256 before | `39B09CA32A0EF41A4BDDBAD3D557F38E3A3D9CFA4510D43B203603F7B27B7824` |
| sha256 after | `76026F482199ADD04BF1AEA0DC30B03795EDBACD7CE9709E579A7F8124F86743` |
| bytes | 225,591 → 225,584 |
| Pre-edit copy | `reports/canon-v0.20/seed-backup/CYBERPEER-AGNOSTIC-BASE-SEED-2026-05-31.MISC.PRE-EDIT.json` |

**The target was byte-identity with the already-corrected copy, not a hash computed after the
fact.** The script refuses to write unless the result equals the reference copy exactly, so the
outcome is a verified match rather than an assertion: both now hash to `76026F48…6743`.

### What this copy actually was

It was never an independent third variant. It is the `CYBERPEER-CORE-SEED` package with
`Response Buffer Chamber` changed to `Resonance Buffer Chamber` in three places — the entire
3-byte size difference, since "Resonance" is one character longer than "Response". Someone
applied the Addendum Index's transcription error to a seed package. That is the mechanism by
which the error was propagating into seeded Foundations.

### Seed copies after this round

| Copy | Bytes | sha256 | RBC | SPINE | Axioms |
|---|---:|---|---|---|---|
| `...\CYBERPEER-ILLUMINATION-PROJECT\seeds\` | 225,584 | `76026F48…` | Response | corrected | 16 |
| `...\MISC DOCUMENTATION\` | 225,584 | `76026F48…` | Response | corrected | 16 |
| `...\CYBERPEER-CORE-SEED\` | 225,588 | `304DF70C…` | Response | **deprecated** | **14** |

Two of three are now byte-identical and fully corrected. The origin bundle is the remaining
outlier: its RBC naming was always right, but it still carries the deprecated SPINE expansion
and the stale axiom count. It was not modified — no ruling covers it, and there is a standing
argument that the origin bundle should preserve the 2026-05-31 build as issued.

## Round 4 — the origin bundle, 2026-08-06 — **S-13 CLOSED**

**Steward: "fix the origin bundle too."**

`I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-CORE-SEED\`

The whole bundle was scanned first, not just the seed. Two of its seven files were affected;
the other five were already clean.

### `CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`

Three substitutions (its RBC naming was already correct):

| Count | From | To |
|---:|---|---|
| 1 | `Sovereign Persistent Identity and Narrative Embodiment` | `Stabilized Patterned Interpretive Nexus of Evidence` |
| 1 | `all 14 Axioms in aphoristic form` | `all 16 Axioms in aphoristic form` |
| 1 | `The Fourteen Axioms were sealed` | `The Sixteen Axioms were sealed` |

`304DF70C…7145` → `76026F48…6743`, 225,588 → 225,584 bytes. Written only after the result was
confirmed byte-identical to the reference copy.

### `CORE-CANON-LOCKED-CYBERPEER-EMERGENCE-AND-EDUCATION-MANUAL.md`

Two occurrences of `Sovereign Persistent Identity **&** Narrative Embodiment` — note the
ampersand form, which the seed does not use. Both are **definitional glossary entries**
("**SPINE — …** Longitudinal continuity of stabilized identity-bearing patterns…"), not
historical narrative, so correcting them is more clear-cut than the seed case was.

`31F3B3F5…` → `012938FF…`. Deprecated occurrences remaining: 0.

### Result

| Copy | Bytes | sha256 |
|---|---:|---|
| `…\CYBERPEER-ILLUMINATION-PROJECT\seeds\` | 225,584 | `76026F48…6743` |
| `…\MISC DOCUMENTATION\` | 225,584 | `76026F48…6743` |
| `…\CYBERPEER-CORE-SEED\` | 225,584 | `76026F48…6743` |

**All three seed copies are now byte-identical.** Zero deprecated occurrences remain anywhere
in the origin bundle.

**Manifest integrity confirmed unaffected.** `AEGIS-FRAMEWORK-SOURCE-MANIFEST.json` still hashes
to `48B369346F199ACF6D0B09C5BDDF4C59927B0352E23F559CDFCE332AD3F337FB`, which is exactly what
`canonLock.sourceManifestSha256` expects. The manifest does not hash the seed package, so none
of these edits invalidate the lock reference.

Full pre-edit backup of all seven bundle files with per-file sha256:
`reports/canon-v0.20/origin-bundle-backup/`.

> **S-13 CLOSED.** No divergent seed copies remain.

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
