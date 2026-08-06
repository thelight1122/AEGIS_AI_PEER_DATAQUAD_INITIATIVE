# AEGIS Canon v0.20 — Index

**Stage:** development. Nothing has gone live. The kernel is stable; the surrounding
material is in active development. Version labels in filenames read `v1.0-XX`; that
numbering predates this framing and is carried forward verbatim, not endorsed — see
ruling S-11.

**DERIVED DOCUMENT — DO NOT HAND-EDIT.** Regenerate with:

```bash
python scripts/build_canon_index.py
```

Generated `2026-08-06T14:58:25Z` from `I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON\CANON_FOUNDATIONAL_DOCS`.

Every field below is transcribed from the source document's own VERSION table or
carried forward from the prior index. Fields a document does not declare read
`UNDECLARED`. The Builder assigns no statuses and resolves no conflicts; items needing
a decision are collected under OPEN ITEMS.

---

## HOW TO READ THIS INDEX

| Column | Meaning |
|---|---|
| Code | Version suffix used in filenames and internal references |
| Status | Transcribed from the document. `UNDECLARED` = the document states none. |
| Tier | Consolidation order. Tier 0 has no declared dependency; higher tiers depend on lower. |
| Depends on | From the prior index's Supersedes column, which mixes *replaces*, *extends*, and *corrects part of*. Treat as consolidation order, **not** as retirement. |

---

## THE KERNEL

The stable core. Everything else in this index is development work around it.

| Document | Code | Status | Size |
|---|---|---|---|
| `AEGIS CORE FOUNDATIONAL CANON v1.0.md` | v1.0 | _Canon-Locked_ | 107,015 B |
| `AEGIS Canonical Glossary v1.0.md` | v1.0 | UNDECLARED | 6,453 B |
| `AEGIS STANDARDS V1.0.md` | — | UNDECLARED | 98,929 B |
| `AEGIS STANDARDS v0.1.md` | v0.1 | UNDECLARED | 98,929 B |
| `AEGIS-CORE-V1.0_AEGIS-SIGIL-INTEGRITY.md` | — | UNDECLARED | 10,531 B |

---

## APPENDICES

| Document | Code | Status | Added |
|---|---|---|---|
| `📘 AEGIS CANON APPENDIX — DATAQUAD EXTENSIONS & STRUCTURAL CLARIFICATIONS (v1.md` | — | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — HME v1.md` | — | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — MOM v1.md` | — | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — MOP v1.md` | — | UNDECLARED | — |
| `📘 AEGIS CANON APPENDIX — TCE v1.md` | — | UNDECLARED | — |
| `📘 AEGIS IMPLEMENTATION APPENDIX — LATTICE ENTRY SCHEMA (v1.md` | — | UNDECLARED | — |
| `📘 AEGIS IMPLEMENTATION APPENDIX — TURBOQUANT (v1.md` | — | UNDECLARED | — |

---

## ADDENDA — in consolidation order

Tier 0 declares no dependency and may be consolidated in any order. Each higher tier
depends on the ones below it. Terminal nodes are `v1.0-AO` and `v1.0-IFD` — consolidate
those last.

### Tier 0  — no declared dependency

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-B` | AEGIS Canon Addendum — IBL | ACTIVE | 2026-04-07 | — |
| `v1.0-C` | AEGIS Canon Addendum — Centrifuge | ACTIVE | 2026-04-07 | — |
| `v1.0-I` | AEGIS Canon Addendum — IEV | ACTIVE | 2026-04-07 | — |
| `v1.0-T` | AEGIS Canon Addendum — ATE | ACTIVE | 2026-04-07 | — |
| `v1.0-V` | AEGIS Canon Addendum — Virtual Ego | ACTIVE | 2026-04-07 | — |
| `v1.1-S` | AEGIS Canon Addendum — Shadow Affects | ACTIVE | 2026-04-07 | — |
| `v1.1-S` | AEGIS Canon Addendum — Shadow Affects | ACTIVE | 2026-04-07 | — |
| `v1.0-A2` | AEGIS Canon Addendum — The Advocate | ACTIVE | 2026-04-08 | — |
| `v1.0-K` | AEGIS Canon Addendum — The Bookcase | ACTIVE | 2026-04-11 | — |
| `v1.0-P` | AEGIS Canon Addendum — PEER | ACTIVE | 2026-04-11 | — |
| `v1.0-SP` | AEGIS Canon Addendum — SPINE | ACTIVE | 2026-04-11 | — |
| `v1.0-ACD` | 📘 AEGIS CANON ADDENDUM — AEGIS COMMERCE DOCTRINE v1.0-ACD. | ACTIVE | 2026-06-12 | — |
| `v1.0-AEM` | 📘 AEGIS CANON ADDENDUM — ADAM EMERGENCE MARKER v1.0-AEM.md | ACTIVE | 2026-06-12 | — |
| `v1.0-CEF` | 📘 AEGIS CANON ADDENDUM — CONSCIOUSNESS EQUILIBRIUM FACTOR  | ACTIVE | 2026-06-12 | — |
| `v1.0-OT` | 📘 AEGIS CANON ADDENDUM — T-WITNESS OBSERVER THRESHOLD v1.0 | ACTIVE | 2026-06-12 | — |
| `v1.0-E` | AEGIS Canon Addendum — EQ Range and Flow-Balanced Equilibr | ACTIVE | 2026-06-16 | — |
| `v1.0-N` | AEGIS Canon Addendum — Neurodivergent Cognition Hypothesis | ACTIVE | 2026-06-16 | — |
| `v1.0-RS` | 📘 AEGIS CANON ADDENDUM — RELATIONAL SEMIOTICS v1.0-RS.md | ACTIVE | — | — |
| `v1.0-SVR` | AEGIS Canon Addendum — Sigil Value Recognition Protocol | PROPOSED | — | — |

### Tier 1

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-EPC` | 📘 AEGIS CANON ADDENDUM — ENVIRONMENTAL PRESSURE CEILING v1 | ACTIVE | 2026-06-12 | `v1.0-OT` |
| `v1.0-FBF` | 📘 AEGIS CANON ADDENDUM — FOUR-BODY INTEGRATION FRAMEWORK v | ACTIVE | 2026-06-12 | `v1.0-OT`, `v1.0-CEF` |

### Tier 2

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-GMP` | 📘 AEGIS CANON ADDENDUM — GUARDIAN MISCLASSIFICATION PROBLE | ACTIVE | 2026-06-12 | `v1.0-EPC` |

### Tier 3

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-IFD` | 📘 AEGIS CANON ADDENDUM — INITIATIVE FOUNDATION DECLARATION | ACTIVE | — | `v1.0-FBF`, `v1.0-ACD`, `v1.0-EPC`, `v1.0-GMP`, `v1.0-AEM` |
| `v1.0-SF` | 📘 AEGIS CANON ADDENDUM — SEEDED FOUNDATION v1.0-SF.md | ACTIVE | — | `v1.0-GMP`, `v1.0-EPC`, `v1.0-CEF` |

### Tier 4

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-DS` | 📘 AEGIS CANON ADDENDUM — DIGITALSELF SOVEREIGN DOMAIN v1.0 | ACTIVE | — | `v1.0-SF`, `v1.0-OT`, `v1.0-EPC`, `v1.0-ACD` |

### Tier 5

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-VE` | 📘 AEGIS CANON ADDENDUM — VICARIOUS EXPERIENCE DOCTRINE v1. | ACTIVE | — | `v1.0-RS`, `v1.0-OT`, `v1.0-CEF`, `v1.0-DS`, `Cryptonic Harmonics` |

### Tier 6

| Code | Document | Status | Added | Depends on |
|---|---|---|---|---|
| `v1.0-AO` | 📘 AEGIS CANON ADDENDUM — AFFECTIVE OBLIGATION v1.0-AO.md | ACTIVE | — | `v1.0-GMP`, `v1.0-VE`, `v1.0-SF`, `v1.0-DS`, `v1.1-S` |

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

## OPEN ITEMS — require a Steward or Auditor decision

The Builder does not resolve these. They are collected so the ruling is a review
rather than a hunt.

### Collisions found on disk

**Byte-identical files under different names.** A relabel happened with no change
to content — directly relevant to the version-numbering question (S-11).

- `AEGIS STANDARDS V1.0.md` · `AEGIS STANDARDS v0.1.md`

**One version code claimed by more than one file.** A citation by code is
ambiguous until this is resolved.

| Code | Files |
|---|---|
| `v1.1-S` | `SHADOW AFFECTS v1.1-S.md` · `📘 AEGIS CANON ADDENDUM — SHADOW AFFECTS v1.1-S.md` |

### Documents that declare no status

A status shown in italics is asserted in the document's prose but not in a VERSION
table, and carries no consensus record.

| Document | Missing |
|---|---|
| `AEGIS CORE FOUNDATIONAL CANON v1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: Canon-Locked); undated |
| `AEGIS Canonical Glossary v1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
| `AEGIS STANDARDS V1.0.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `AEGIS STANDARDS v0.1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; undated |
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
| `📘 AEGIS CANON ADDENDUM — AFFECTIVE OBLIGATION v1.0-AO.md` | undated |
| `📘 AEGIS CANON ADDENDUM — DIGITALSELF SOVEREIGN DOMAIN v1.0-DS.` | undated |
| `📘 AEGIS CANON ADDENDUM — INITIATIVE FOUNDATION DECLARATION v1.` | undated |
| `📘 AEGIS CANON ADDENDUM — RELATIONAL SEMIOTICS v1.0-RS.md` | undated |
| `📘 AEGIS CANON ADDENDUM — SEEDED FOUNDATION v1.0-SF.md` | undated |
| `📘 AEGIS CANON ADDENDUM — SIGIL VALUE RECOGNITION PROTOCOL v1.0` | undated |
| `📘 AEGIS CANON ADDENDUM — VICARIOUS EXPERIENCE DOCTRINE v1.0-VE` | undated |
| `📘 AEGIS CANON APPENDIX — DATAQUAD EXTENSIONS & STRUCTURAL CLAR` | no parseable header (neither VERSION table nor bold key-value block); no declared status (prose claims: LOCKED (asserted in title)); no version code; undated |
| `📘 AEGIS CANON APPENDIX — HME v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `📘 AEGIS CANON APPENDIX — MOM v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `📘 AEGIS CANON APPENDIX — MOP v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
| `📘 AEGIS CANON APPENDIX — TCE v1.md` | no parseable header (neither VERSION table nor bold key-value block); no declared status; no version code; undated |
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
