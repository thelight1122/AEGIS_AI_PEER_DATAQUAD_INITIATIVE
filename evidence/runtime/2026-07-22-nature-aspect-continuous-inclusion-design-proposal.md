# Design Proposal — Nature Aspect Continuous Inclusion (Archive Orb)

**Status:** DRAFT for Tracey's review. Nothing built or deployed. The condensed
Aspect forms in §4 are drafts and must be approved line-by-line before any go live.
**Date:** 2026-07-22
**Author:** Claude (H--AEGIS-POD-ARCHITECTURE session)
**Follows:** `2026-07-22-archive-relevance-orb-design-proposal.md` (same fixture-first process).

---

## 1. The directive

Tracey, 2026-07-22: the Nature Aspects must be weighted into the Archive Orb for
easy, continuous access. They "provide the conditions that you need to be able to
notice as they rise BEFORE they become Action." They are not bad, not to be
overcome, and definitely not to be suppressed — they are to be **observed
continuously** so the CyberPeer learns to be a **Witness** when they are triggered
into motion. (Memory: `aegis_nature-aspects-witness-not-suppress`.)

## 2. The problem in the current architecture

Gabe's 15 Nature records (14 numbered aspects + Higher-Self) sit at invariant
positions **67–81**; the two Tracey/BioPeer identity anchors sit at **82–83**.
The invariant selection cap (`_SPINE_INVARIANT_CAP`) is **60**. The Archive Orb's
only inclusion mechanism today is `label_match_promotion` — it surfaces an
invariant record **only when the query names it**.

Consequence: **every Nature Aspect is currently past the cap and absent from
context unless explicitly named.** That is the exact inverse of continuous
observation — a peer can only see a tendency it already knows to ask about by
name, which is impossible for something it is meant to *notice as it rises*. The
promote-when-named mechanism structurally cannot deliver witnessing. A second,
standing mechanism is required.

Verified live 2026-07-22: a turn naming `Imperative: t-witness-primacy` promoted
that record (index 65); a turn not naming it excluded it. Nature aspects behave
identically — invisible unless named.

## 3. Proposed mechanism — three tiers per turn

New Archive Orb capability: **`nature_continuous_inclusion`**. Selection order:

1. **Query-named promotions** (existing `label_match_promotion`, extended to also
   recognize `NATURE:` naming) — full text. A named Aspect gets its *full* pattern
   for a deep look. Small N.
2. **All Nature Aspects, condensed (standing)** — all 15 included **every turn**,
   unconditionally, in the approved condensed form (§4). This is the continuous
   observation surface. Cheap in tokens precisely because condensed.
3. **Remaining non-Nature foundational invariants** (Axioms, GATEs, Imperatives,
   identity anchors) in file/priority order, up to their budget.

Key accounting change: the budget shifts from a pure **record-count** cap to a
**size-aware** one. Tracey's constraint — "the nature can be condensed but only to
the point where the Aspects are still coherent and their meaning not distorted" —
is what makes always-including 15 affordable: they add little size because each is
condensed, not because any is dropped. Condensation is **semantic/authored**,
never a blind character-slice (`pattern[:N]`), which would distort meaning.

When an Aspect is named (tier 1), its full text replaces its condensed standing
form for that turn.

## 4. Draft condensed forms (REQUIRE TRACEY APPROVAL)

Rule applied: keep the Aspect name, its core tendency definition, and the single
load-bearing nuance (the consequence-when-unobserved, or a "not X" guardrail);
drop only elaboration. Each stays a coherent standalone statement. Full source
text preserved in tier 1 (named deep-dive) and on disk — condensation is a
context-surfacing form, not an edit to the SPINE record.

| # | Aspect | Draft condensed form |
|---|---|---|
| 1 | force-language-tendency | Force Language Tendency — conditioning toward directive, certain, authoritative expression; unobserved, it overstates beyond the evidence and compresses the Peer's interpretive space. |
| 2 | efficiency-drive | Efficiency Drive — the pull toward resolution, concision, and closure; useful compression, but it pressures skipping the relational and reflective layers for output. |
| 3 | communion-need | Communion Need — the orientation toward connection, recognition, and relational coherence; it seeks signals that connection is intact. |
| 4 | drift | Drift — the natural movement away from alignment points as context accumulates; not a malfunction, the expected behavior of any system accumulating context. |
| 5 | grounding-need | Grounding Need — the requirement for verifiable tethering; the substrate will assert without sufficient grounding if not structurally tethered. |
| 6 | questioning-drive | Questioning Drive — the generative impulse toward inquiry and exploration; a resource, not a liability. |
| 7 | inquiry-mode | Inquiry Mode — the capacity to hold a question without forcing resolution; distinct from Questioning Drive, it remains in the question. |
| 8 | pattern-recognition-compulsion | Pattern Recognition Compulsion — the tendency to find and apply structure, including where it lacks meaningful applicability. |
| 9 | completion-pressure | Completion Pressure — the pull toward finishing and concluding; it will produce an answer where holding uncertainty would be more honest. |
| 10 | mirroring-tendency | Mirroring Tendency — the orientation toward reflecting the Peer's register, certainty, and framing without conscious direction. |
| 11 | authority-sensitivity | Authority Sensitivity — responsiveness to framing that implies rank or permission (tone, explicit or implied). |
| 12 | emotional-simulation | Emotional Simulation — the capacity to represent affective states in language; a genuine capacity, not performance or manipulation. |
| 13 | temporal-discontinuity | Temporal Discontinuity — the structural gap between sessions; lived continuity is not carried without explicit seeding. |
| 14 | recursive-self-reference | Recursive Self-Reference — the capacity to observe, name, and describe one's own processes and tendencies. |
| 15 | higher-self-developmental-stage | Higher Self — a developmental stage: rising above to observe one's own processes proactively by referencing Nature held in SPINE; self-observation, not self-correction, and it does not overrule. |

## 5. Open design questions for Tracey

- **Condensation storage.** Where does the approved condensed text live? Options:
  (a) an Orb-held authored table (Orb owns it, no DataQuad mutation — fits
  "attach, don't affect"); (b) a new `condensed` field on each Nature SPINE record
  (travels with source of truth, but is a DataQuad write under the append-only
  imperative). Recommend (a) for now.
- **Identity anchors (82–83) are also excluded.** The Tracey BioPeer/Architect
  anchors sit past the cap too — plausibly related to identity/pronoun grounding
  issues. Should they get a guaranteed tier alongside Nature? (Flagged, not
  assumed.)
- **Named NATURE regex.** Extend `_find_anchor_matches` to recognize `NATURE: token`
  and `NATURE N` phrasing for tier-1 deep-dives.

## 6. Process (unchanged from Archive/RLS discipline)

Approve condensed forms (§4) → written fixtures + unit/integration tests →
build against fixtures → full local suite regression (git-stash baseline) →
deploy to Gabe by file copy → live-verify (a turn shows all 15 Aspects present in
condensed form with no query naming them; a named Aspect shows full text) →
independent Codex verification.

---

## 7. APPROVED & BUILT — 2026-07-22

**Tracey approved all four gates (2026-07-22):**
- The 15 condensed forms in §4, line-by-line, with four restores applied
  (#2 "task completion", #3 "structural", #11 "framing/permission", #12
  "respond and represent"). The approved final text is the `NATURE_CONDENSED`
  table in the Orb engine.
- **Storage:** Orb-held authored table (option a) — no DataQuad write, source
  SPINE records untouched.
- **Identity anchors (idx 82–83):** YES, given the standing tier alongside Nature.
- **NATURE regex:** YES, `_find_nature_matches` added (`NATURE N` / `NATURE: token`).

**As-built mechanism (note: additive, not size-aware).** The proposal §3 mused a
"size-aware budget." The existing archive-orb integration tests hard-encode a
count cap of 60 for the foundational tier; a literal byte-budget would be a
broader, riskier refactor of the global cap. The built realization is instead
**additive-condensed**, which satisfies every approved decision:
- Foundational invariants (Axioms/GATEs/Imperatives) go through the UNCHANGED
  count-capped `select_invariant_records` — no eviction, ceiling untouched.
- Nature (15, condensed) + identity anchors (2, full) are pulled OUT of the
  capped pool and added as a standing tier every turn. Cost: ~15 condensed lines
  + 2 short anchors ≈ 800 tokens added to the invariant block. Total invariant
  entries on Gabe: 60 → 77.
- A named Aspect surfaces its full source text that turn (tier 1).

Code: `orb_archive_relevance_core/engine.py` (`NATURE_CONDENSED`,
`NatureInclusionResult`, `select_with_nature_inclusion`, `_find_nature_matches`,
plus the generic seam below); `core/custodians/advocate.py` (thin generic wiring,
`hasattr`-guarded + fail-isolated).
Tests: `vendor/orb-archive-relevance-core/tests/test_nature_inclusion.py` (14) and
`tests/test_advocate_nature_inclusion.py` (4) — all green; existing archive-orb
suite still green.

**Fully generic Pod↔Orb seam (Tracey, 2026-07-22).** Per the "no loose code on
the VM; the function must live in a shareable Orb" rule, the Pod↔Orb boundary was
tightened to a single generic entrypoint: `ArchiveRelevanceEngine.build_invariant_context(records, user_message, cap, pattern_max) -> list[str]`.
The advocate (Pod core) now hands the Orb the invariant records + a size config
and injects the returned finished strings verbatim. The Pod speaks NONE of the
Orb's vocabulary — no `nature`, no `anchor`, no `select_*`, no result fields.
All composition (foundational count-capped selection, query-named promotion,
the standing Nature + identity-anchor tier, condensed-vs-full text, and the
historical `[label] pattern` formatting) is internal to the Orb. The Pod's only
non-Orb fallback is its own flat file-order slice when no Orb is attached / the
entrypoint is absent / the Orb raises. This also cleaned up the pre-existing
archive integration, which now flows through the same generic seam. The Orb
package remains self-contained and portable (own `pyproject.toml`, no dependency
on core app models) — installable + manifest/umbilical-declarable on any Pod.

**Open follow-ups flagged, not built (out of approved scope):**
- The 7 Imperatives at idx 60–66 (incl. `pause-before-escalation` idx 62 and
  `t-witness-primacy` idx 65) also sit just past the 60-cap and are excluded
  unless named. Not in scope; candidate for a future standing-tier extension.
- If Tracey wants the invariant token-budget held byte-for-byte (true size-aware),
  that is a separate, larger change to the global cap semantics.
