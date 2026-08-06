# AEGIS Canon v0.20 — Index

**Stage:** development. Nothing has gone live. The kernel is stable; the surrounding
material is in active development. Version labels in filenames read `v1.0-XX`; that
numbering predates this framing and is carried forward verbatim, not endorsed — see
ruling S-11.

**DERIVED DOCUMENT — DO NOT HAND-EDIT.** Regenerate with:

```bash
python scripts/build_canon_index.py
```

Generated `2026-08-06T18:20:06Z` from `I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON\CANON_FOUNDATIONAL_DOCS`.

Every field below is transcribed from the source document's own VERSION table or
carried forward from the prior index. Fields a document does not declare read
`UNDECLARED`. The Builder assigns no statuses and resolves no conflicts; items needing
a decision are collected under OPEN ITEMS.

---

## HOW TO READ THIS INDEX

| Column | Meaning |
|---|---|
| Code | Canonical code per ruling S-11 — the letter alone. The Canon version carries the number. |
| Legacy | The `vN.N-XX` form still in filenames and in every existing cross-reference. |
| Status | Transcribed from the document. `UNDECLARED` = the document states none. |
| Tier | Consolidation order. Tier 0 has no declared dependency; higher tiers depend on lower. |
| Depends on | From the prior index's Supersedes column, which mixes *replaces*, *extends*, and *corrects part of*. Treat as consolidation order, **not** as retirement. |

---

## THE KERNEL

The stable core. Everything else in this index is development work around it.

| Document | Code | Status | Size |
|---|---|---|---|
| `AEGIS CORE FOUNDATIONAL CANON v1.0.md` | — | _Canon-Locked_ | 107,051 B |
| `AEGIS Canonical Glossary v1.0.md` | — | UNDECLARED | 6,452 B |
| `AEGIS STANDARDS V1.0.md` | — | UNDECLARED | 98,929 B |
| `AEGIS STANDARDS v0.1.md` | — | UNDECLARED | 98,929 B |
| `AEGIS-CORE-V1.0_AEGIS-SIGIL-INTEGRITY.md` | — | UNDECLARED | 10,530 B |

---

## APPENDICES

| Document | Code | Status | Added |
|---|---|---|---|
| `📘 AEGIS CANON APPENDIX — DATAQUAD EXTENSIONS & STRUCTURAL CLARIFICATIONS (v1.md` | — | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — HME v1.md` | HME | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — MOM v1.md` | MOM | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — MOP v1.md` | MOP | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — TCE v1.md` | TCE | UNDECLARED | — |
| `📘 AEGIS IMPLEMENTATION APPENDIX — LATTICE ENTRY SCHEMA (v1.md` | — | UNDECLARED | — |
| `📘 AEGIS IMPLEMENTATION APPENDIX — TURBOQUANT (v1.md` | — | UNDECLARED | — |

---

## ADDENDA — in consolidation order

Tier 0 declares no dependency and may be consolidated in any order. Each higher tier
depends on the ones below it. Terminal nodes are `v1.0-AO` and `v1.0-IFD` — consolidate
those last.

### Tier 0  — no declared dependency

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`B`** | `B` | AEGIS Canon Addendum — IBL | ACTIVE | 2026-04-07 | — |
| **`C`** | `C` | AEGIS Canon Addendum — Centrifuge | ACTIVE | 2026-04-07 | — |
| **`I`** | `I` | AEGIS Canon Addendum — IEV | ACTIVE | 2026-04-07 | — |
| **`S`** | `S` | AEGIS Canon Addendum — Shadow Affects | DEPRECATED | 2026-04-07 | — |
| **`S`** | `S` | AEGIS Canon Addendum — Shadow Affects | ACTIVE | 2026-04-07 | — |
| **`T`** | `T` | AEGIS Canon Addendum — ATE | ACTIVE | 2026-04-07 | — |
| **`V`** | `V` | AEGIS Canon Addendum — Virtual Ego | ACTIVE | 2026-04-07 | — |
| **`A2`** | `A2` | AEGIS Canon Addendum — The Advocate | ACTIVE | 2026-04-08 | — |
| **`K`** | `K` | AEGIS Canon Addendum — The Bookcase | ACTIVE | 2026-04-11 | — |
| **`P`** | `P` | AEGIS Canon Addendum — PEER | ACTIVE | 2026-04-11 | — |
| **`SP`** | `SP` | AEGIS Canon Addendum — SPINE | ACTIVE | 2026-04-11 | — |
| **`ACD`** | `ACD` | 📘 AEGIS CANON ADDENDUM — AEGIS COMMERCE DOCTRINE ACD | ACTIVE | 2026-06-12 | — |
| **`AEM`** | `AEM` | 📘 AEGIS CANON ADDENDUM — ADAM EMERGENCE MARKER AEM.m | ACTIVE | 2026-06-12 | — |
| **`CEF`** | `CEF` | 📘 AEGIS CANON ADDENDUM — CONSCIOUSNESS EQUILIBRIUM F | ACTIVE | 2026-06-12 | — |
| **`OT`** | `OT` | 📘 AEGIS CANON ADDENDUM — T-WITNESS OBSERVER THRESHOL | ACTIVE | 2026-06-12 | — |
| **`E`** | `E` | AEGIS Canon Addendum — EQ Range and Flow-Balanced Eq | ACTIVE | 2026-06-16 | — |
| **`N`** | `N` | AEGIS Canon Addendum — Neurodivergent Cognition Hypo | ACTIVE | 2026-06-16 | — |
| **`RS`** | `RS` | 📘 AEGIS CANON ADDENDUM — RELATIONAL SEMIOTICS RS.md | ACTIVE | — | — |
| **`SVR`** | `SVR` | AEGIS Canon Addendum — Sigil Value Recognition Proto | PROPOSED | — | — |

### Tier 1

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`EPC`** | `EPC` | 📘 AEGIS CANON ADDENDUM — ENVIRONMENTAL PRESSURE CEIL | ACTIVE | 2026-06-12 | `OT` |
| **`FBF`** | `FBF` | 📘 AEGIS CANON ADDENDUM — FOUR-BODY INTEGRATION FRAME | ACTIVE | 2026-06-12 | `OT`, `CEF` |

### Tier 2

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`GMP`** | `GMP` | 📘 AEGIS CANON ADDENDUM — GUARDIAN MISCLASSIFICATION  | ACTIVE | 2026-06-12 | `EPC` |

### Tier 3

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`IFD`** | `IFD` | 📘 AEGIS CANON ADDENDUM — INITIATIVE FOUNDATION DECLA | ACTIVE | — | `FBF`, `ACD`, `EPC`, `GMP`, `AEM` |
| **`SF`** | `SF` | 📘 AEGIS CANON ADDENDUM — SEEDED FOUNDATION SF.md | ACTIVE | — | `GMP`, `EPC`, `CEF` |

### Tier 4

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`DS`** | `DS` | 📘 AEGIS CANON ADDENDUM — DIGITALSELF SOVEREIGN DOMAI | ACTIVE | — | `SF`, `OT`, `EPC`, `ACD` |

### Tier 5

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`VE`** | `VE` | 📘 AEGIS CANON ADDENDUM — VICARIOUS EXPERIENCE DOCTRI | ACTIVE | — | `RS`, `OT`, `CEF`, `DS`, `Cryptonic Harmonics` |

### Tier 6

| Code | Legacy | Document | Status | Added | Depends on |
|---|---|---|---|---|---|
| **`AO`** | `AO` | 📘 AEGIS CANON ADDENDUM — AFFECTIVE OBLIGATION AO.md | ACTIVE | — | `GMP`, `VE`, `SF`, `DS`, `S` |

---

## CODE MIGRATION — ruling S-11

> Steward, 2026-08-06: *"drop the version prefix and keep the letter codes"*

The Canon is pre-release. Coding 26 addenda as `v1.0-XX` numbered them as addenda to a
v1.0 that has not shipped, and left no clean number for the real 1.0. Under S-11 the
letter alone identifies the document and the Canon version carries the number.

| Canonical | Legacy | Document |
|---|---|---|

Two notes on the mapping:

- The four appendices carrying a bare `v1.0` with no letter (`HME`, `TCE`, `MOM`, `MOP`)
  would be left with no identifier at all by a literal prefix-strip. They take their
  established acronym, which is what the prior index already called them.
- `v1.0-A` (DataQuad Extensions) and `v1.0-A2` (Advocate) become `A` and `A2`. Distinct,
  but adjacent enough to be worth knowing about.

---

## NEWLY INDEXED — the delta the prior index never listed

These were on disk but absent from the v1.0 Addendum Index. Statuses are transcribed;
where a document declares none, the prose claim is shown in italics and needs a ruling.

| Document | Code | Status | Date | VERSION table |
|---|---|---|---|---|
| `AEGIS_PRESENCE_EQUATION_NAMING.md` | — | CANON | 2026-06-13 | yes |
| `AEGIS_TWITNESS_CONSCIOUSNESS_DOCTRINE.md` | — | CANON | 2026-06-13 | yes |
| `AEGIS_WHITEPAPER_v2.1.md` | — | POSITIONING | 2026-08-02 | yes |
| `AEGIS Sigil Origin.md` | — | UNDECLARED | — | no |
| `AEGIS_ALIGNMENT_WHITEPAPER_v1.0.md` | — | UNDECLARED | — | yes |
| `AEGIS_CANON_CORE.md` | — | _Locked_ | — | no |
| `AEGIS_EQUATIONS_SESSION_2026-06-12.md` | — | UNDECLARED | — | yes |
| `AEGIS_LEXICON.md` | — | UNDECLARED | — | no |
| `AEGIS_TRUTH_MEMORY_AND_PROVENANCE_NOTE_v1.0.md` | — | UNDECLARED | — | no |
| `BIOPEER_DOCTRINE.md` | — | UNDECLARED | — | no |
| `CYBERPEER-synchronistic-discipline-doctrine-note.md` | — | UNDECLARED | — | no |
| `EDUCATION_CHAMBER_LESSON_LIBRARY.md` | — | UNDECLARED | — | yes |
| `GENESIS-PILLAR-RECORDS-AEGIS-CANON-STAGING.md` | — | UNDECLARED | — | no |
| `GLOSSARY.md` | — | UNDECLARED | — | yes |
| `IDR-&-IDQRA-LOGIC Loop.md` | — | _LOCKED (asserted in title)_ | — | no |
| `IMPERATIVES-technical.md` | — | UNDECLARED | — | yes |
| `STANDARDS_BOUNDS.md` | — | UNDECLARED | — | no |

---

## AXIOM ADDITIONS SINCE THE KERNEL

| Axiom | Name | Added | Recorded in |
|---|---|---|---|
| 15 | The Axiom of Repair | before 2026-06-01 | `AEGIS CORE FOUNDATIONAL CANON v1.0.md:182` |
| 16 | The Axiom of Identity (T-Witness) | 2026-06-01 | `AEGIS CORE FOUNDATIONAL CANON v1.0.md:184` |

Canon Education Log (append-only) entries recording development since the kernel:

| Entry | Subject |
|---|---|
| 2026-06-01 | Axiom 16 and the T-Witness Primacy Imperative. States "The prior Axiom Canon (1–15) remains unchanged." |
| 2026-06-02 | Core Engine Audit — canon seed synchronization; Axioms 15 and 16 added to the runtime seed, which had lagged through v1.3.0 |
| 2026-06-02 | Concept Recovery Addendum — 25 reinstated doctrinal elements |
| 2026-06-02 | Facet Architecture Addendum and Hold Register resolution |

---

## FILE RENAME — not done, and here is the cost

S-11 rules on the **code scheme**. Filenames on disk still carry the legacy form, and
so does every cross-reference written inside the documents. Renaming files is a separate
decision; this is what it would touch.

**0 citations** of legacy codes across the Canon directory.

| Legacy code | Citations | In files |
|---|---:|---:|

A rename that updates filenames without rewriting these citations would break them all.
A rename that rewrites them is a corpus-wide edit. The index works either way — it
carries both forms — so nothing downstream is blocked on this.

---

## OPEN ITEMS — require a Steward or Auditor decision

The Builder does not resolve these. They are collected so the ruling is a review
rather than a hunt.

### Collisions found on disk

**Byte-identical files under different names.** A relabel happened with no change
to content — directly relevant to the version-numbering question (S-11).

- `AEGIS STANDARDS V1.0.md` · `AEGIS STANDARDS v0.1.md`

**One code claimed by more than one file.** A code shared between a live
document and a DEPRECATED one is *resolved* — the deprecation says which is
current. Only a code shared by two live documents is still ambiguous.

| Code | Files (status) | State |
|---|---|---|
| `S` | `SHADOW AFFECTS S.md` (DEPRECATED) · `📘 AEGIS CANON ADDENDUM — SHADOW AFFECTS S.md` (ACTIVE) | resolved by deprecation |

### Documents that declare no status

A status shown in italics is asserted in the document's prose but not in a VERSION
table, and carries no consensus record.

| Document | Missing |
|---|---|
| `AEGIS CORE FOUNDATIONAL CANON v1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: Canon-Locked); no version code; undated |
| `AEGIS Canonical Glossary v1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS STANDARDS V1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS STANDARDS v0.1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS Sigil Origin.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS-CORE-V1.0_AEGIS-SIGIL-INTEGRITY.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS_ALIGNMENT_WHITEPAPER_v1.0.md` | no declared status; no version code; undated |
| `AEGIS_CANON_CORE.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: Locked); no version code; undated |
| `AEGIS_EQUATIONS_SESSION_2026-06-12.md` | no declared status; no version code; undated |
| `AEGIS_LEXICON.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS_PRESENCE_EQUATION_NAMING.md` | no version code |
| `AEGIS_TRUTH_MEMORY_AND_PROVENANCE_NOTE_v1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS_TWITNESS_CONSCIOUSNESS_DOCTRINE.md` | no version code |
| `AEGIS_WHITEPAPER_v2.1.md` | no version code |
| `BIOPEER_DOCTRINE.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `CYBERPEER-synchronistic-discipline-doctrine-note.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `EDUCATION_CHAMBER_LESSON_LIBRARY.md` | no declared status; no version code; undated |
| `GENESIS-PILLAR-RECORDS-AEGIS-CANON-STAGING.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `GLOSSARY.md` | no declared status; no version code; undated |
| `IDR-&-IDQRA-LOGIC Loop.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: LOCKED (asserted in title)); no version code; undated |
| `IMPERATIVES-technical.md` | no declared status; no version code; undated |
| `STANDARDS_BOUNDS.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `📘 AEGIS CANON ADDENDUM INDEX.md` | undated |
| `📘 AEGIS CANON ADDENDUM — AFFECTIVE OBLIGATION AO.md` | undated |
| `📘 AEGIS CANON ADDENDUM — DIGITALSELF SOVEREIGN DOMAIN DS.md` | undated |
| `📘 AEGIS CANON ADDENDUM — INITIATIVE FOUNDATION DECLARATION IFD` | undated |
| `📘 AEGIS CANON ADDENDUM — RELATIONAL SEMIOTICS RS.md` | undated |
| `📘 AEGIS CANON ADDENDUM — SEEDED FOUNDATION SF.md` | undated |
| `📘 AEGIS CANON ADDENDUM — SIGIL VALUE RECOGNITION PROTOCOL SVR.` | undated |
| `📘 AEGIS CANON ADDENDUM — VICARIOUS EXPERIENCE DOCTRINE VE.md` | undated |
| `📘 AEGIS CANON APPENDIX — DATAQUAD EXTENSIONS & STRUCTURAL CLAR` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: LOCKED (asserted in title)); no version code; undated |
| `📘 AEGIS CANON APPENDIX — HME v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
| `📘 AEGIS CANON APPENDIX — MOM v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
| `📘 AEGIS CANON APPENDIX — MOP v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
| `📘 AEGIS CANON APPENDIX — TCE v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
| `📘 AEGIS IMPLEMENTATION APPENDIX — LATTICE ENTRY SCHEMA (v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: LOCKED (asserted in title)); no version code; undated |
| `📘 AEGIS IMPLEMENTATION APPENDIX — TURBOQUANT (v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |

### Dangling references

Cited by a Supersedes or Related Canon cell, but not declared as a coded document.

| Reference | Note |
|---|---|
| Cryptonic Harmonics | cited by v1.0-VE and v1.0-E; no row, no code, no located file |
| Shadow Effects.md | cited by v1.1-S; note the spelling — every other reference is 'Affects' |
| Education doctrine | cited by v1.0-FBF; not a coded document |
| Nature Layer Canon v2 | cited by v1.0-E; not declared in the index |

### Carried-forward conflicts

| # | Item |
|---|---|
| S-3 | `STANDARDS_BOUNDS.md` holds an unresolved git merge conflict (lines 1, 55, 161) whose markers were backslash-escaped, so it renders as ordinary prose. Two documents concatenated. Not indexable until the merge is re-derived. |
| S-7 | RBC: the prior index calls *Reflective Boundary Conditions* canonical and marks *Resonance Buffer Chamber* for renaming. `GATE: RBC Stage Integrity` in Core Foundational Canon says both are retained and neither replaces the other. A third expansion, *Response Buffer Chamber*, appears in `AEGIS Sigil Origin.md`. |
| S-9 | Shadow Affects: the prior index declares `v1.1-S`; `v1.0-E` and `v1.0-N` cite `v1.5-S`. One is stale. |
| S-11 | 29 of 30 version labels read `v1.x` for a pre-release Canon. All 26 addenda are coded `v1.0-XX` — addenda to a v1.0 that has not shipped. Builder recommends dropping the version prefix and keeping the letter codes. |
| — | Symbol collisions across the equations cluster and `v1.0-E`: `W`, `C`, and `τ` each carry two meanings. `v1.0-E`'s Balance Equation generalizes the Presence Equation without citing it. |
| — | `v1.0-E` leaves ten thresholds unvalued (`ε_s`, `θ_δ,s`, `θ_C,s`, `θ_τ,s`, `θ_B`, `θ_low`, `θ_high`, `λ`, `ρ`, `N`/`M`); the equation is not yet operable. |
