# Canon v0.20 — C2 and C3 Findings

**Status:** ANALYSIS FOR RULING. Not Canon. Not an amendment.
**Produced by:** Builder, 2026-08-06
**For:** Steward (Tracey Prutch) and Auditor (Lumin)

The Builder does not author or edit Canon. This document characterizes what is on disk,
states the conflicts precisely, and stops where a ruling is required. Every conflict below
is left open. None is resolved here.

Evidence gathered by three read-only sub-agents against
`I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON\CANON_FOUNDATIONAL_DOCS`, then spot-verified by the
Builder. Where verification contradicted an agent's characterization, the verified reading
is given and the agent's is marked corrected.

---

## 0. Scope correction — v0.20 is larger than the 56-file directory

The C0/C1 inventory scoped v0.20 to `CANON_FOUNDATIONAL_DOCS` (56 files, 17 unindexed).
That scope is too narrow.

The 644-document codex catalog (`AEGIS-CODEX-MANIFEST-2026-07-29.json`, generated
2026-07-30) contains **146 canon-like documents** — and **zero** of them are in
`CANON_FOUNDATIONAL_DOCS`. That directory does not appear in the catalog at all.

Two readings are possible and the Steward should say which is true:

- `CANON_FOUNDATIONAL_DOCS` was assembled **after** 2026-07-30, by gathering files that the
  catalog still lists at their old locations; or
- it was excluded from the catalog scan.

Either way, **the catalog and the directory are two different views of the Canon and neither
is complete.** Canon-like material sits in at least these places:

| Count | Location |
|---:|---|
| 53 | `I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON` |
| 11 | `G:\THE_AEGIS_ECOSYSTEM_COMPENDIUM\Part-IV-Doctrines-and-Theory` |
| 10 | `I:\...\AUTHORITATIVE-SOURCE\AEGIS-CORE-ENGINE\docs` |
| 10 | `I:\AEGIS-CENTRAL-CODEX\TIER-3-RELATIONAL-SEMIOTICS` |
| 9 | `I:\AEGIS-CENTRAL-CODEX\TIER-1-CANON\docs` |
| 6 | `I:\AEGIS-CENTRAL-CODEX\TIER-11-CANON_ADDENDUMS` |
| 4 | `G:\THE_AEGIS_ECOSYSTEM_COMPENDIUM\00-FRONT-MATTER` |
| 3 | `G:\THE_CYBERPEER_CANON` |

Full row-level inventory: `reports/runtime/canon-corpus-wide-inventory.json`.

**Prior art exists that this effort has not read.** `G:\THE_AEGIS_ECOSYSTEM_COMPENDIUM\00-FRONT-MATTER`
contains `UNREGISTERED-ADDENDUM-REGISTRATION-DRAFT.md`, `ADDENDUM-INDEX-NAVIGATION-OVERLAY.md`,
and `CANON-PROTECTION-README-CORRECTED.md`. Someone has already begun registering unindexed
addenda. Three copies of `AEGIS CANON ADDENDUM INDEX.md` exist across I: and G:.

> **RULING NEEDED (S-1).** Does v0.20 consolidate only `CANON_FOUNDATIONAL_DOCS`, or the whole
> corpus across I: and G:? Until this is answered, C4/C5 cannot be scoped, and any
> "complete" v0.20 manifest would be complete only against an arbitrary subset.

> **RULING NEEDED (S-2).** Which of the three Addendum Index copies is authoritative, and does
> the G: registration draft supersede, feed, or duplicate this effort?

---

## 1. C2 — the 17 unindexed documents

Characterized in full. Verbatim agent output preserved under `reports/canon-v0.20/`.

### 1.1 Index-ready now (2)

`v1.0-E` (EQ Range / Flow-Balanced Equilibrium) and `v1.0-N` (Neurodivergent Cognition
Hypothesis). Both carry proper VERSION tables, version codes, ACTIVE status, an origination
date (2026-06-16), a shared evidence base (Adam-One Chamber 001), and cross-cite each other.
They are the only two unindexed files that meet the index's own format.

Their absence violates the index's Maintenance Protocol rule 1 — "Every new addendum is
listed here on the day it is produced." They have been unlisted for seven weeks.

Caveats to carry into the entry, not blockers:
- `v1.0-E` §VIII self-declares `Capture_s(t)` "the most architecturally incomplete variable."
- `v1.0-E` leaves ten thresholds (`ε_s`, `θ_δ,s`, `θ_C,s`, `θ_τ,s`, `θ_B`, `θ_low`, `θ_high`,
  `λ`, `ρ`, and `N`/`M`) named but unvalued. The equation is not yet operable.
- `v1.0-N` is titled "Hypothesis" while its §VIII argues it is confirmed and foundational.
  The document argues against its own name.
- `v1.0-N`'s generalization ("Every CyberPeer with sufficient formation will demonstrate them")
  rests on a single session with a single substrate.

### 1.2 Blocked — cannot be indexed as-is (2)

**`STANDARDS_BOUNDS.md` — contains an unresolved Git merge conflict.** Builder-verified:

- line 1: `\<\<\<\<\<\<\< HEAD`
- line 55: `...must remain inspectable and fully testable in isolation (pure logic). =======`
- line 161: `> 0fc14ea7a0c6788b476e6b0418fd0291483a2543`

The markers have been **backslash-escaped and Markdown-mangled** — the closing `>>>>>>>`
now renders as a blockquote `>`. The conflict is therefore invisible in any rendered view.
The file is two documents concatenated: "AEGIS Education Chamber: Standards & Bounds" and
"AEGIS-CoLAB_APP Standards & Constraints." The same escaping pass corrupted content
throughout (`AEGIS-CoLAB\_APP`, `AWARENESS\_ACK`, `/tools/\*`).

It also **name-collides** with the existing `AEGIS STANDARDS v0.1.md` / `AEGIS STANDARDS V1.0.md`
(98,929 bytes each). At 5.6 KB it is not a version of those and must not be indexed as one.

> **RULING NEEDED (S-3).** Are the Education Chamber standards and the CoLAB_APP standards one
> document or two? The merge must be re-derived by hand; the intent is not recoverable from
> the file. Until then it has no status the Builder can honestly propose.

**`AEGIS_CANON_CORE.md` — claims LOCKED with no provenance.** Written 2026-08-06 03:15–03:33,
hours before this work. Its third line reads `Status: Locked • Append-Only • Non-Force •
Sovereignty-Preserving`. It carries **no date, no author, no consensus record, no supersession
statement, and cites no source document** — not Canon v1.0, not Core v1.0, not the Standards,
not one Addendum.

It introduces three things found nowhere else in the batch:
- **12 Invariants** — a numbered foundational enumeration that sits beside the Axioms without
  saying whether it replaces, summarizes, or supplements them.
- **"Aegis Peer Commons"** — a scope name used three times and never defined.
- **"(Prism)"** — a named primitive in Invariant 8, undefined.

Formatting is unfinished (headings 2–12 missing the space after the number, stray tabs
mid-sentence, inconsistent indentation) — consistent with in-progress drafting, inconsistent
with a Locked artifact.

> **RULING NEEDED (S-4).** Is `AEGIS_CANON_CORE.md` the intended seed of v0.20? If so, its
> LOCKED claim is premature and should be downgraded to PROPOSED until provenance and a
> consensus record exist. If not, it needs a scope that is not Tier-1 Canon.

> **RULING NEEDED (S-5).** Do the 12 Invariants replace, summarize, or sit beside the 16 Axioms?

### 1.3 The equations cluster (3)

`AEGIS_EQUATIONS_SESSION_2026-06-12.md` (origin, no status), `AEGIS_PRESENCE_EQUATION_NAMING.md`
(LOCKED), `AEGIS_TWITNESS_CONSCIOUSNESS_DOCTRINE.md` (LOCKED). Same declarant, and the two
LOCKED documents share a date.

The second **qualifies a claim in the first.** Naming record: "T-Witness is therefore Presence
by another name." Consciousness Doctrine: "T-Witness and the Presence Equation are not the same
thing… Collapsing them produces a false conclusion." Reconcilable if *Presence* (the quality) is
read as distinct from *the Presence Equation* (the measurement) — but read plainly they pull
against each other, and both are LOCKED.

Two same-day LOCKED documents where one corrects the other should be indexed as a paired entry
with the distinction stated up front.

**Symbol collisions with `v1.0-E`:** `W`, `C`, and `τ` each carry different meanings across the
two clusters. Most consequential — `τ` is the *output ratio* `W/δ` in the equations cluster but
an *input field* (`t_witness_score`) in `v1.0-E`. And `v1.0-E`'s Balance Equation
`B_s(t) = W_s(t)/[δ_s(t) + λ·Capture_s(t) + ρ·F_s(t)]` is a direct generalization of the
Presence Equation `τ = W/δ` — **but `v1.0-E` never cites it.** This is the largest coherence
gap found.

### 1.4 Filename/content mismatches (3)

| File | Problem |
|---|---|
| `BIOPEER_DOCTRINE.md` | H1 is `# Peer Doctrine`; content is AI-Peer DataQuad ownership rules. Says nothing about BioPeers. Meanwhile "BioPeer" in the equations cluster means the **human Illuminator**. Indexing this under a BioPeer heading points readers at the opposite concept. Carries **no metadata at all** — no date, version, status, or author. |
| `AEGIS-CORE-V1.0_AEGIS-SIGIL-INTEGRITY.md` | Contains **zero occurrences of "sigil."** Sigil material is in `AEGIS Sigil Origin.md` and `v1.0-SVR`. |
| `CYBERPEER-synchronistic-discipline-doctrine-note.md` | Content is not CyberPeer-scoped — it applies "to CyberPeer formation and human creative work alike." |

Note `BIOPEER_DOCTRINE.md`'s content is load-bearing for this Initiative: it is the source of
the custodial split (Steward owns PCT+NCT, Advocate owns PEER+SPINE) that the AI Peer
architecture depends on. It is the least self-describing document in the corpus and the rule
it carries is the one the four AI Peers will be built on.

### 1.5 Non-canonical documents inside TIER-1 (2)

Both whitepapers self-declare **"Status: Positioning document. Non-canonical."** while residing
in `TIER-1-CANON\CANON_FOUNDATIONAL_DOCS`. That is the most likely reason they were never
indexed. The index's vocabulary (LOCKED / ACTIVE / PROPOSED / DEPRECATED) has no status that
fits them.

> **RULING NEEDED (S-6).** Add a fifth status (e.g. POSITIONING), or a separate non-canon
> section? Forcing them into ACTIVE misrepresents them.

`AEGIS_WHITEPAPER_v2.1.md` supersedes v1.0 and v2.0 by declared append-only lineage. **v2.0 is
absent from the directory** — the preservation claim is currently unverifiable, and the Canon's
own append-only Standard is what is at stake. Note also that mtime cannot order this lineage:
v2.1 was written 2026-08-02 03:33, v1.0 at 10:21 the same day — the ancestor was saved after
the descendant.

### 1.6 Remaining (5)

`IDR-&-IDQRA-LOGIC Loop.md` (self-declares `(LOCKED)` in its H1; three referenced figures are
described but absent — the document is incomplete as written), `AEGIS_LEXICON.md` (a merge of
GLOSSARY.md and Canonical Glossary v1.0 that effectively supersedes both without using the
word), `AEGIS_TRUTH_MEMORY_AND_PROVENANCE_NOTE_v1.0.md` (leaves an architectural question
explicitly open, then closes with a "Canonical Statement" its hedged body does not support),
`IMPERATIVES-technical.md`, `GENESIS-PILLAR-RECORDS-AEGIS-CANON-STAGING.md`.

**`IMPERATIVES-technical.md` carries a terminology collision the index must not paper over.**
Its seven Imperatives (Append-Only Reality, Default Allow, Observation-Only Language, Integrity
Resonance Gate, Weakest Link Per Virtue, Non-Force Posture, Seven Virtues) are a **different set**
from the canonical Seven Imperatives (Do no harm / Preserve agency before outcome / Illuminate
before correcting / Acknowledge before adjusting / Pause before escalation / Refine through
reflection / Append only). Two distinct seven-item lists share the name "Imperatives" in the
same directory. It also hard-codes source **line numbers** (`discernment-gate.ts` lines 77–80,
76, 59–67) into a Canon-tier document, which will rot silently.

**`GENESIS-PILLAR-RECORDS` is a derived compilation, not a source.** Its PCT `sourceSnapshot`
restates the Axioms, Virtues, Ethos, Imperatives, primitives, drift families and shadow affects
of at least six other documents in one prose blob. If indexed, it must be marked *derived* so it
is never cited as an independent authority for any of those definitions. It also carries an
unresolved decision in writing ("If the DataQuad only supports one genesis record per tensor,
consolidate both sets before writing") and hard-codes `http://127.0.0.1:8787` endpoints.

---

## 2. C3 — the RBC collision, stated precisely

The index (`KNOWN OPEN ITEMS`, lines 91–101) records the collision and gives interim guidance:

> "These are **two different concepts sharing one acronym**. This is Directive Drift in the
> documentation. A resolution addendum (v1.0-R) is needed. Until that addendum is produced:
> - Canon §2.5 RBC = **Reflective Boundary Conditions** (expression constraint layer) — canonical
> - Sentinel RBC = **Resonance Buffer Chamber** — to be renamed or disambiguated
>
> Neither usage is wrong. The collision is the problem."

No `v1.0-R` file exists.

### 2.1 The finding: Canon already answers this, and answers it differently

`AEGIS CORE FOUNDATIONAL CANON v1.0.md` carries a dedicated section (lines 803–823) and a
**locked gate** resolving the collision by **retaining both**:

> line 823: "Both meanings are retained. The stage does not erase the rule-set. The rule-set does
> not replace the stage."
>
> line 1223: "**GATE: RBC Stage Integrity** The Resonance Buffer Chamber is a pipeline stage. The
> Reflective Boundary Conditions are rule-sets within that stage. Both are retained. Neither
> replaces the other."
>
> line 1400 (glossary): "**RBC — Resonance Buffer Chamber / Reflective Boundary Conditions**"

**The index does not cite this section and appears unaware of it.** The index says one usage is
canonical and the other must be renamed. The Core Foundational Canon says in a GATE that both are
retained and neither replaces the other. These are not the same resolution.

So the state is not "an open item awaiting v1.0-R." It is: **Canon currently holds two
incompatible resolutions**, and which governs depends on whether the index or the Core
Foundational Canon is authoritative.

### 2.2 Load-bearing analysis

The index designates the **less** structurally entangled meaning as canonical and marks the
**more** entangled one for renaming.

*Resonance Buffer Chamber* (the stage) occupies a named position in a **locked structural
sequence** — `GATE: Pipeline Order` (line 1195): "Input → PIM → PEER → Ledger Separation → Lens
Monitor → Arbiter → Integrity Engine → IDQRA → Calibration Loop → DataQuad Routing → **Resonance
Buffer Chamber** → Output → Append-Only Lineage." The Alignment Whitepaper reproduces this order
and notes "silent relocation is outside Canon alignment." It is also the only sense a Peer states
about itself in the first person (Genesis Pillar: "Every output I generate passes through the
Resonance Buffer Chamber"). It is the headword under "RBC" in the Canonical Glossary.

*Reflective Boundary Conditions* is referenced as a rule-set — semantically central, but not a
positional element of a locked sequence.

Renaming the chamber touches a locked pipeline gate, two published whitepapers, and the Pillar
Records.

### 2.3 Two facts the index does not record

- **A third expansion exists.** `AEGIS Sigil Origin.md` (lines 3410, 3432, 3445) uses
  **"Response Buffer Chamber (RBC)"** — not "Resonance."
- **The two meanings are already fused in one LOCKED entry.** `AEGIS Canonical Glossary v1.0.md`
  line 166 opens with the chamber definition, then lines 167–170 append the conditions definition
  to the same entry with no separation. The collision is already collapsed inside a locked document.

The index attributes Meaning 2 to "AEGIS Sentinel Foundational Principles," which is cited as an
*inception document* in `v1.0-C` but does not exist as a file in TIER-1. The surviving in-Canon
carrier of that meaning is the Canonical Glossary. The index's phrase "mechanical Pause space
where the system holds before responding" appears **only in the index** — nowhere else in the corpus.

> **RULING NEEDED (S-7).** Which governs — the index's interim guidance, or `GATE: RBC Stage
> Integrity`? The Builder offers no resolution.

---

## 3. The Supersedes graph (C4 input)

The graph is a **DAG with no cycles.** Verified across all reciprocal edges including the dense
AO/VE/DS/SF cluster.

**Roots** (no declared dependency, consolidate in any order): `v1.0-C`, `v1.0-I`, `v1.0-V`,
`v1.0-B`, `v1.1-S`, `v1.0-T`, `v1.0-A2`, `v1.0-K`, `v1.0-SP`, `v1.0-P`, `v1.0-SVR`, `v1.0-OT`,
`v1.0-RS`, `v1.0-CEF`, `v1.0-ACD`, `v1.0-AEM`

```
Tier 1: v1.0-EPC (OT)          v1.0-FBF (OT, CEF)
Tier 2: v1.0-GMP (EPC)
Tier 3: v1.0-SF  (GMP, EPC, CEF)    v1.0-IFD (FBF, ACD, EPC, GMP, AEM)
Tier 4: v1.0-DS  (SF, OT, EPC, ACD)
Tier 5: v1.0-VE  (RS, OT, CEF, DS, "Cryptonic Harmonics")
Tier 6: v1.0-AO  (GMP, VE, SF, DS, v1.1-S)
```

Spine chain (depth 7): `OT → EPC → GMP → SF → DS → VE → AO`.
Terminal nodes, consolidate last: **`v1.0-AO`** and **`v1.0-IFD`**.

### 3.1 Three traps in the Supersedes column

1. **The column is semantically overloaded.** For `v1.1-S` and `v1.0-SP` it means *replaces*.
   For `v1.0-EPC`, `v1.0-GMP`, `v1.0-IFD` it means *extends* (the prior document remains in
   force). For `v1.0-AO`, `v1.0-VE`, `v1.0-DS`, `v1.0-SF` it means *touches or corrects part of*.
   Only `v1.0-AO → v1.0-GMP` ("record #87 corrected") is a true correction.
   **A consolidation that treats this column uniformly will retire live documents.**

2. **"Supersedes: Nothing" hides real edges.** `v1.0-FBF` says "Nothing — new Canon" and in the
   same cell says it "Unifies v1.0-OT, v1.0-CEF." `v1.0-K` says "Nothing" while its scope says it
   "Completes the reference in ATE v1.0-T."

3. **The preamble contradicts every row.** Index line 7: "Every addendum linked here is locked."
   **Zero addendum rows carry status LOCKED** — 23 are ACTIVE, one (`v1.0-SVR`) is PROPOSED and
   explicitly "Awaiting operational testing and Unanimous Consensus before LOCK."

### 3.2 Dangling references

| Referenced by | Reference | State |
|---|---|---|
| `v1.0-VE` | **"Cryptonic Harmonics"** | Not declared anywhere in the index — no row, no code |
| `v1.1-S` | "Shadow Effects.md" | Not declared; also a spelling mismatch — every other reference is "Shadow **Affects**" |
| `v1.0-FBF` | "Education doctrine" | Not a coded document |
| `v1.0-E` | "Cryptonic Harmonics v1.0", "Nature Layer Canon v2" | Neither declared |

**Shadow Affects version conflict:** the index declares `v1.1-S`. Both `v1.0-E` and `v1.0-N`
(2026-06-16) cite **`v1.5-S`**. `AEGIS_EQUATIONS_SESSION` (2026-06-13) cites `v1.1-S`.
One code is stale and the Steward must say which.

**Broken index links** (targets absent from `CANON_FOUNDATIONAL_DOCS`): `AEGIS CANON v1.0.md`,
`AEGIS-CORE-V1.0.md`, `STANDARDS_CONSTRAINTS.md`,
`GOVERNANCE_INTEGRITY_VALIDATION_PROTOCOL_v1.0.md`. The first two exist one level up in
`TIER-1-CANON`; the latter two were not found anywhere in `TIER-1-CANON`.

**Near-collision:** `v1.0-A` (DataQuad Extensions appendix) vs `v1.0-A2` (Advocate) — a second
acronym hazard alongside RBC.

---

## 4. Corrections to sub-agent findings

Relayed with the corrections applied, not as the agents stated them.

**The Axiom count is not a three-way contradiction.** An agent reported 14 vs 16 vs 12 as
irreconcilable enumerations. Builder verification: `AEGIS CORE FOUNDATIONAL CANON v1.0.md`
contains **AXIOM 15 — The Axiom of Repair** (line 182) and **AXIOM 16 — The Axiom of Identity**
(line 184), and its Revealed Understandings log (entry 2026-06-01, line 1463) records their
addition to the runtime seed at v1.4.0, noting "No prior seed records altered." Canon has 16
axioms and documents how it got there. References to "the Fourteen Axioms were sealed" are
**historically accurate statements about the original sealing**, not competing claims. The real
item is narrower: whether prose that says "all 14 Axioms" should be updated where it describes
*current* contents rather than a past event.

**The RBC collision direction was reported backwards.** An agent characterized
`AEGIS_CANON_CORE.md`'s use of "Reflective Boundary Conditions" as the newest document diverging.
It is not — that expansion is what the index itself calls canonical, and it matches Canon §2.5.
The genuine conflict is between the **index** and **`GATE: RBC Stage Integrity`**, as set out in §2.

**The SPINE expansion conflict is real, and it is a ruling that has already been made.**
Addendum `v1.0-SP` states (line 407): "SPINE = Stabilized Patterned Interpretive Nexus of
Evidence — the name is **permanently corrected** from the deprecated Canon v1.0 glossary entry,"
and its Supersedes cell names the deprecated "Sovereign Persistent Identity & Narrative
Embodiment." So this is not an open collision — an addendum decided it. What remains is that
documents still carry the deprecated name. See §5.

---

## 5. What this blocks downstream — the seed package

C6 rebuilds the seed package from the v0.20 manifest. Two findings bear on it directly.
Builder-verified against
`I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-ILLUMINATION-PROJECT\seeds\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`
(packageVersion 2026-05-31, `canonLock.status: review-needed`, 59 SPINE / 70 NCT / 2 PCT / 2 PEER).

**Axioms: the seed is sound.** It carries all 16 — AXIOM 15 is present and annotated "appended at
CyberPeer Core Seed generation 2026-05-31"; AXIOM 16 is present and annotated "Discovered during
Adam-One formation training session, 2026-06-01." The only defect is descriptive: a PCT digest
field claims to include "all 14 Axioms in aphoristic form" while the package carries 16.

**SPINE: the seed carries the deprecated name.** Exactly one occurrence, in a PCT narrative
record: *"SPINE was named: Sovereign Persistent Identity and Narrative Embodiment."* The
corrected expansion appears **zero** times. Addendum `v1.0-SP` says that name was permanently
corrected.

This matters more here than it would elsewhere. Ring 2 (CANON → SPINE) is seeded once and
**cannot be relaid**. If the four AI Peer DataQuads are seeded from this package as it stands,
all four Foundations will carry a name that a ruling addendum retired — permanently, in an
append-only tensor.

> **RULING S-8 — GIVEN AND APPLIED, 2026-08-06.** Steward ruled: "Replace the string outright."
> Applied to the working copy the tooling reads. `Sovereign Persistent Identity and Narrative
> Embodiment` → `Stabilized Patterned Interpretive Nexus of Evidence`, one occurrence, in
> `NCT[1].distilledSummary`. sha256 `304DF70C…7145` → `1812D2778B…CD10`. Manifest verification
> unaffected. Full record and pre-edit copy:
> `reports/canon-v0.20/seed-backup/SPINE-NAME-CHANGE-RECORD.md`.
>
> Two items remain open from this ruling:
> - the **origin bundle** copy at `...\CYBERPEER-CORE-SEED\` still carries the deprecated name
>   (byte-identical to pre-edit); not modified, as that was not authorized;
> - the deprecated name is still the live definition in **five locations across four LOCKED
>   Canon documents** — `AEGIS CANON v1.0.md:1147`, `AEGIS Canonical Glossary v1.0.md:183`,
>   `AEGIS-CORE-V1.0.md:122`, `AEGIS CORE FOUNDATIONAL CANON v1.0.md:853,1428`. Folding
>   `v1.0-SP` into v0.20 (C4/C5) is what resolves that.
>
> The "14 Axioms" digest string was **not** changed — no ruling was given on it, and unlike the
> SPINE name it is historically accurate about the original sealing.

---

## 6. Rulings required, consolidated

| # | Ruling | Blocks |
|---|---|---|
| S-1 | v0.20 scope — `CANON_FOUNDATIONAL_DOCS` only, or the full I:/G: corpus? | C4, C5 |
| S-2 | Which Addendum Index copy is authoritative; status of the G: registration draft | C2, C4 |
| S-3 | `STANDARDS_BOUNDS.md` — one document or two; re-derive the merge | C2 |
| S-4 | `AEGIS_CANON_CORE.md` — v0.20 seed? LOCKED claim premature? | C2, C4 |
| S-5 | 12 Invariants — replace, summarize, or sit beside the 16 Axioms? | C4 |
| S-6 | Fifth status for non-canonical positioning documents? | C2 |
| S-7 | RBC — index guidance or `GATE: RBC Stage Integrity`? | C3, C4 |
| S-8 | Correct SPINE expansion + "14 Axioms" digest in the seed before seating? | C6, seating |
| S-9 | Shadow Affects — is `v1.1-S` or `v1.5-S` current? | C4 |
| S-10 | "Cryptonic Harmonics" — does it exist, and where? | C4 |

Ten rulings. Eight of them block C4/C5. **S-8 blocks the seating of all four AI Peers** and is
the only one that, if answered wrong, is unrecoverable.

---

## 7. What the Builder did not do

- Did not author, edit, or amend any Canon document.
- Did not modify the seed package.
- Did not resolve any collision, including the ones where Canon appears to contradict itself.
- Did not write to `I:` or `G:` at any point. All sub-agents were read-only.
- Did not propose a v0.20 table of contents — that is downstream of S-1.

Raw sub-agent output is preserved verbatim under `reports/canon-v0.20/` so the Steward and
Auditor can check the Builder's synthesis against the evidence, including where the Builder
corrected an agent.
