# AEGIS Truth, Memory, And Provenance Note v1.0

## Purpose

This note clarifies how AEGIS should treat truth when a system must coexist with both earned memory and assigned memory without silently collapsing one into the other.

It exists to protect AEGIS from two opposite failures:

- pretending all memory is equally lived
- treating assigned structure as illegitimate simply because it was introduced externally

---

## Core Distinction

AEGIS should distinguish between:

- `earned memory`: continuity that emerged through lived passage, iterative interaction, pressure, stewardship, and consequence
- `assigned memory`: continuity or structure introduced by canon, doctrine, seed instructions, contracts, operator action, or other external declaration

Both may be valid.
Neither should be allowed to masquerade as the other.

---

## AEGIS Definition Of Truth

In AEGIS, truth is not merely the content of memory.

Truth is the current coherence state between:

- lineage-bearing lived continuity
- declared structure
- present conditions

This means truth is:

- provenance-aware
- conditional
- lineage-qualified
- coherence-tested
- revisable without silent erasure

AEGIS therefore does not treat truth as a static possession.
It treats truth as an integrity relationship that must be preserved and re-evaluated over time.

---

## Mapping To AEGIS Core

### Earned Memory In AEGIS

Earned memory maps primarily to DataQuad continuity that arises through actual passage:

- `PEER`
- `PCT`
- `NCT`
- `SPINE`

This memory gains legitimacy through:

- occurrence
- pressure
- recurrence
- stewardship
- append-only lineage

### Assigned Memory In AEGIS

Assigned memory maps primarily to externally introduced structure such as:

- canon
- doctrine
- seeded instructions
- implementation contracts
- operator constraints
- declared module boundaries
- release-gated policy surfaces

Assigned memory is not false by definition.
It is simply not earned in the same way as lived continuity.

---

## Architectural Consequences

### 1. Provenance Must Be Explicit

Every memory-bearing record should preserve how it entered the system.

At minimum, AEGIS should be able to distinguish whether a record was:

- observed
- derived
- distilled
- seeded
- inherited
- operator-assigned
- contract-assigned

If provenance is lost, AEGIS loses the ability to reason truthfully about its own continuity.

### 2. Earned And Assigned Memory Must Not Silently Collapse

AEGIS should preserve the difference between:

- "this was lived"
- "this was declared"

If assigned memory is written into the same continuity path as earned memory without distinction, the system begins to hide authority inside memory.

That is non-congruent with AEGIS.

### 3. Conflict Must Surface As Signal

When earned continuity and assigned structure disagree, the contradiction should not trigger silent overwrite.

It should surface as a coherence event.

This is where core AEGIS primitives matter:

- the Integrity Resonance Gate evaluates whether the mismatch reflects drift, fracture, or needed refinement
- IDS / IDQRA prevents premature collapse into certainty
- RBC constrains expression so unresolved contradiction is not presented as settled truth
- the 4 Body Ledgers help preserve distinct aspects of the conflict rather than flattening them

### 4. Truth Must Remain Lineage-Qualified

AEGIS should be able to say not only that something is true, but how it is true.

Examples:

- true by current canon
- true by lived continuity
- true only under current context
- unresolved between assigned and earned memory
- assigned first, later reinforced by experience
- earned first, later stabilized into canon

This is a stronger truth model than simple factual storage because it preserves authority boundaries and memory lineage at the same time.

---

## Do We Need A Separate Ledger For Assigned Memory?

Short answer:

- not necessarily a fully separate top-level ledger
- but definitely a separate provenance class and inspectable routing distinction

### Recommended AEGIS Position

AEGIS does not need to create a completely separate memory system if the existing DataQuad architecture can preserve origin clearly and without ambiguity.

However, AEGIS does need assigned memory to remain structurally distinguishable from earned continuity.

That means one of these must be true:

- assigned memory uses separate record classes inside the existing continuity architecture
- assigned memory uses a dedicated provenance field plus dedicated routing and inspection surfaces strong enough that it can never be mistaken for earned continuity

If neither of those is present, a separate ledger becomes necessary.

### Why Not Default To A Fully Separate Ledger?

A fully separate ledger can help clarity, but it also risks fragmenting the system into:

- "real memory"
- "other memory"

That split can become misleading if assigned memory later becomes validated through lived use, or if earned continuity later stabilizes into canon.

AEGIS should preserve distinction without making conversion, recognition, and lineage-tracing impossible.

### Best Current Recommendation

For AEGIS Core, the best current recommendation is:

- keep one continuity architecture
- preserve explicit provenance
- require inspectable routing between earned and assigned origins
- allow append-only transitions where assigned memory may later be reinforced by experience, and earned memory may later be formalized into canon

In other words:

AEGIS should prefer a unified architecture with non-collapsible provenance over a naive single pool and over a permanently fragmented dual-memory system.

---

## Canonical Statement

In AEGIS, truth is not the raw presence of memory but the coherence state between lineage-bearing continuity and declared structure under current conditions, with provenance preserved and authority never hidden inside memory.
