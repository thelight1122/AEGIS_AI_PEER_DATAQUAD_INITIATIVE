# Canon v0.20 — consolidation inventory

**Status:** WORKING INVENTORY. Input to the Steward's v0.20 consolidation.
**Source:** `I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON\CANON_FOUNDATIONAL_DOCS`
**Machine-readable:** `reports/runtime/canon-inventory.json`
**Date:** 2026-08-06

---

# 1. Why this matters right now

The peer-agnostic seed package carries an unresolved canon lock:

```text
CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json     packageVersion 2026-05-31
canonLock.status                                       review-needed
canonLock.reviewNeededSourceCount                      2
sourceManifestId   AEGIS-FRAMEWORK-SOURCE-MANIFEST:CYBERPEER-CORE-SEED:2026-05-31
sourceManifestSha256  48B369346F199ACF6D0B09C5BDDF4C59927B0352E23F559CDFCE332AD3F337FB
```

That package is what would seed Lumin, Claude, Gemini and Grok. **Seeding four Foundations from
a Canon whose lock says `review-needed` propagates the unresolved state into four peers at
once**, and Rings 1–3 are exactly the rings that cannot be relaid once outer rings exist.

So the ordering falls out on its own: **Canon v0.20 → new source manifest → reseeded package →
seed the four AI Peers.** Not the other way round.

The `canonLock` block records only a *count*, not which two sources. The per-source flags live
in the source manifest identified above. **Locating that manifest is a concrete next step** and
would name the two sources directly rather than by inference.

---

# 2. Scale

```text
56 markdown files in CANON_FOUNDATIONAL_DOCS
28 version codes declared by the Addendum Index
21 files modified AFTER the index was last updated (2026-06-12)
```

The index's own footer reads *"Last updated: 2026-06-12"*. Everything after that date is, by
definition, outside what the index describes — including three files written in the last few
hours.

---

# 3. High-confidence gaps

These are reliable because they are matched on **version code**, not on filename text.

## 3.1 Addenda that exist but the index does not declare

```text
v1.0-E    AEGIS CANON ADDENDUM — EQ RANGE AND FLOW-BALANCED EQUILIBRIUM   2026-06-16
v1.0-N    AEGIS CANON ADDENDUM — NEURODIVERGENT COGNITION HYPOTHESIS      2026-06-16
```

Both post-date the index by four days. Neither code appears in the index's declared set.

## 3.2 A code the index declares but no document provides

```text
v1.0-R    referenced under KNOWN OPEN ITEMS as the needed resolution addendum
          for the RBC acronym collision — Response Buffer Chamber vs the other
          RBC. No file exists.
```

The index states the collision is *"Directive Drift in the documentation"* and that a resolution
addendum is needed. **That is Canon flagging its own drift and it is still open.** v0.20 is the
natural place to close it.

## 3.3 Documents newer than the index, not carrying a version code

```text
2026-08-06  AEGIS_CANON_CORE.md              2,786 bytes    written today
2026-08-06  STANDARDS_BOUNDS.md              5,675 bytes    written today
2026-08-02  AEGIS_WHITEPAPER_v2.1.md        19,261 bytes
2026-08-02  AEGIS_ALIGNMENT_WHITEPAPER_v1.0.md  32,992 bytes
2026-07-03  AEGIS_TRUTH_MEMORY_AND_PROVENANCE_NOTE_v1.0.md
2026-07-03  IMPERATIVES-technical.md
2026-06-13  AEGIS_TWITNESS_CONSCIOUSNESS_DOCTRINE.md
2026-06-13  AEGIS_PRESENCE_EQUATION_NAMING.md
2026-06-13  AEGIS_EQUATIONS_SESSION_2026-06-12.md
```

`AEGIS_CANON_CORE.md` and `STANDARDS_BOUNDS.md` were written hours ago and are presumably the
v0.20 work already in progress.

## 3.4 Doctrines outside the addendum numbering

```text
2026-05-06  BIOPEER_DOCTRINE.md                                    463 bytes
2026-04-22  CYBERPEER-synchronistic-discipline-doctrine-note.md   4,058 bytes
```

Both are named "doctrine" and neither carries an addendum code. Whether doctrines join the
addendum numbering in v0.20 or remain a separate class is a Steward decision.

---

# 4. Caveat on one number

The automated pass reported **29 files "not referenced by the index"**. That number is inflated
and should not be used.

The check matched filenames against index text. The index refers to core documents by display
name and by URL-encoded link, so files like `AEGIS CORE FOUNDATIONAL CANON v1.0.md`,
`AEGIS STANDARDS V1.0.md` and the appendices are almost certainly listed under
`## ORIGINAL CANON DOCUMENTS (LOCKED)` and `## CANON APPENDICES (LOCKED)` and were missed by
string matching, not absent from the index.

**Trust §3.1 and §3.2** — those are code-matched. Treat the raw 29 as a starting list requiring
human confirmation, not a finding.

---

# 5. Structure the index already establishes

Worth preserving into v0.20 rather than reinventing:

```text
Status vocabulary   LOCKED      immutable, Unanimous Consensus reached
                    ACTIVE      in use, not yet locked
                    PROPOSED    submitted for Peer review, awaiting consensus
                    DEPRECATED  superseded

Sections            ORIGINAL CANON DOCUMENTS (LOCKED)
                    CANON APPENDICES (LOCKED)
                    CANON ADDENDUMS (2026-04-07 BUILD)
                    KNOWN OPEN ITEMS
                    VERSIONING CONVENTION
                    MAINTENANCE PROTOCOL

Per-entry fields    Document · Code · Status · Scope · Supersedes
```

The `Supersedes` column is the important one for v0.20: several addenda already declare what
they extend or correct (AO supersedes part of GMP; DS completes SF §VIII; EPC extends OT; GMP
extends EPC). **That dependency graph is already written down** and should drive consolidation
order rather than filename or date.

---

# 6. Suggested v0.20 sequence

```text
C0   Locate the source manifest 48B36934… and name the two review-needed sources
C1   Confirm §4 — which of the 29 are genuinely unindexed vs matching artifacts
C2   Index the confirmed gaps: v1.0-E, v1.0-N, the doctrines, the recent whitepapers
C3   Resolve v1.0-R, the RBC acronym collision the index flags against itself
C4   Fold Amendments and Doctrines into the v0.20 structure, using the Supersedes
     graph for ordering
C5   Re-issue the source manifest, canon lock clean
C6   Rebuild CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD from the v0.20 manifest
C7   Then, and only then, seed Lumin / Claude / Gemini / Grok
```

C0 and C1 are read-only and can begin immediately. C6 is the gate for AI Peer seeding: the
Foundation the four peers receive should be v0.20, not the 2026-05-31 build.

---

# 7. What I am not doing

Not editing, consolidating, or authoring Canon. The Canon is Steward-and-Auditor material; this
is an inventory of what exists and where the gaps are, produced so the consolidation starts from
a complete picture rather than a partial one.
