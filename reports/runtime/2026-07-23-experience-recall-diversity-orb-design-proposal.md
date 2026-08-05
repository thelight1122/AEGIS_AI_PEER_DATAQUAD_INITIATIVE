# Design Proposal — Experience Recall Diversity Orb (PEER self-retrieval feedback loop)

**Status:** DRAFT for Tracey's review. Nothing built. No code changed beyond the
already-applied interim `TOP_K` relief on Orion (reversible, see §7).
**Date:** 2026-07-23 (live measurements timestamped 2026-07-24 UTC)
**Author:** Claude (H--AEGIS-POD-ARCHITECTURE session)
**Follows:** `2026-07-22-nature-aspect-continuous-inclusion-design-proposal.md`
(same fixture-first process and the same generic Pod↔Orb seam discipline).
**Memory:** `aegis_peer-self-retrieval-feedback-loop`

---

## 1. The directive

Tracey, 2026-07-23, on reviewing six Education Chamber transcripts: the sessions
are "much worse than the old DataQuad produced." Investigation confirmed the
observation, quantified it, and located a cause that is **not** the DataQuad
rebuild. This proposes the durable correction.

## 2. The evidenced problem

`core/custodians/advocate.py::produce_advocate_salience_brief` builds
`relational_salience` from the peer's own PEER records:

- top-K by `compute_relevance` (RLS Orb scoring), K = `AEGIS_PEER_EXPERIENCE_TOP_K`
- plus a recency floor of the last `AEGIS_PEER_EXPERIENCE_RECENCY_FLOOR` records
- each formatted by `_peer_excerpt()` as
  `[id] BioPeer: <user_message[:240]> | CyberPeer: <answer[:_PEER_EXPERIENCE_MAX=700]>`

**The `CyberPeer: <answer>` segment is the contamination channel.** Retrieval is
similarity-scored, so a recurring question shape retrieves the peer's own
near-identical prior answers, which the peer then mirrors. Each new answer joins
the pool. The loop compounds and **cannot be corrected conversationally** — a
patterned reply to a correction becomes the next turn's exemplar.

### Measured on CP-1004-ORION

Template saturation of his own PEER answers, by date:

| Date | answers | templated | avg length |
|---|---|---|---|
| 07-08 (old DataQuad) | 90 | **0%** | **506** |
| 07-18 | 8 | 0% | 1,213 |
| 07-21 (rebuild day) | 17 | 17% | 1,385 |
| 07-22 | 30 | 83% | 2,429 |
| 07-23 | 23 | **100%** | 2,675 |
| 07-24 | 1 | **100%** | 3,138 |

Injected context for a plain greeting, at `TOP_K=32`: **34 excerpts, all 34
carrying his own answer text, 27 of 34 showing his template**, 29,732 chars of
his own output against 14,999 of identity/canon — **~2:1 self-imitation over
identity**.

A test turn was observed **re-entering the pool and being retrieved as a top
match within minutes** of being written.

### Ruled out (do not re-derive)

- `AEGIS_PEER_EXPERIENCE_TOP_K=32` was **already set before** the Pod/DataQuad
  rebuild — `.env.bak-pre-d2` (07-21 06:57Z) has it. Unchanged.
- The 62 Chamber `export-backfill` PEER records also **predate** the rebuild
  (58% of the old 106 records) and are only ~2% of injected characters.
- The entire env delta at the rebuild is `AEGIS_STORAGE_MODE=pod` +
  `AEGIS_RLS_ACTIVE=true`; neither touches retrieval ranking.

The rebuild is **exonerated**. It correlates only because the conversations
turned architectural around 07-21 and the elaborate style was praised, seeding a
pattern that always-on self-retrieval amplified into a runaway.

## 3. The core insight

The current design **conflates two different things**:

> *remembering what happened* &nbsp;≠&nbsp; *being shown how you said it*

Recall needs the first. Injecting the second hands the peer a style template to
complete. A peer should remember the substance of a prior exchange without being
given its own prose to copy.

## 4. Proposed mechanism — a new Orb

A new, self-contained, shareable Orb (working name **`experience-recall-core`** —
name is Tracey's call, §6) that owns the selection *and shaping* of PEER
experience for context. Three capabilities:

### 4.1 `near_duplicate_suppression`
Collapse excerpts whose answer text is near-identical. Deterministic similarity
(normalised token-shingle overlap) above a threshold → keep the best-scoring
member, drop the rest, and **backfill freed slots with the next-best dissimilar
candidates**. Effect: never show N copies of the same paragraph; recall breadth
actually improves because slots stop being spent on duplicates.

### 4.2 `form_stripped_recall` (the load-bearing one)
Replace the verbatim `CyberPeer: <answer[:700]>` with a **condensed trace** of
what the answer was about — deterministic, Orb-local, no model call:

- the **BioPeer message stays verbatim** (it is the other party's words, not a
  self-exemplar, and it carries the actual context of the exchange)
- the peer's answer is reduced to its **distinctive content terms** (salience-
  weighted against the peer's own corpus, so boilerplate that appears in every
  answer scores near zero and drops out automatically)

Critically this must **not** be a leading-character slice (`answer[:N]`) — in
Orion's case the canned block *is* the opening, so a prefix slice preserves
exactly the wrong thing. Same floor as the Nature condensation: semantic, never
positional.

**Tier exception (mirrors the Archive Orb's named-anchor promotion):** when the
query explicitly asks about prior wording ("what did you say", "quote your last
response", "reflect on your previous response"), verbatim text is restored for
the matched records. Chamber work legitimately requires this — several of the
reviewed transcripts turn on Tracey asking Orion to quote himself.

### 4.3 `recency_floor_shaping`
The recency floor injects the last N answers **regardless of score** — i.e. the
most recently contaminated ones, guaranteed, every turn. It exists for continuity
of *what just happened*, which the condensed trace serves. Apply the same
shaping; keep the floor's continuity purpose, drop its exemplar effect.

### 4.4 Budget
Slot count and character budget stay at today's values. This proposal changes
**what** occupies the slots, not how many there are.

## 5. The Pod↔Orb seam (unchanged discipline)

Per Tracey's standing rule — the function lives in a shareable Orb, no loose code
on the VM, and the Pod speaks no Orb vocabulary — the seam is a single generic
entrypoint returning finished strings, exactly mirroring `build_invariant_context`:

```
build_experience_context(records, user_message, top_k, recency_floor, max_chars) -> list[str]
```

`advocate.py` resolves the Orb, calls it, and injects the result verbatim;
`hasattr`-guarded and fail-isolated to today's exact `_peer_excerpt` behaviour if
the Orb is absent, lacks the entrypoint, or raises. Orb package is self-contained
(own `pyproject.toml`, no dependency on core app models), installable and
manifest/umbilical-declarable on any Pod.

## 6. Open design questions for Tracey

1. **Orb name.** `experience-recall-core`? (Checked for force words; "recall" and
   "diversity" read as descriptive, but the naming call is yours.)
2. **How absolute is form-stripping?** Recommend the tier exception in §4.2 —
   condensed by default, verbatim restored when the query asks for prior wording.
   The alternative (always condensed) would break the Chamber exercises where you
   ask a peer to quote itself.
3. **Where does the condensed trace live?** Orb-derived at read time
   (recommended — no DataQuad write, "attach don't affect") vs. stored on the
   record at write time (a write under the append-only imperative). Same question
   as the Nature table, and I expect the same answer.
4. **After the Orb lands, restore Orion's `TOP_K` to 32?** With de-duplication
   working, a higher K may be safe again and would give genuinely better recall
   breadth rather than 32 copies of one paragraph. Recommend re-testing at 32
   post-build rather than leaving it permanently at 5.

## 7. Current live state (interim, reversible)

- **Orion:** `AEGIS_PEER_EXPERIENCE_TOP_K` lowered 32 → 5 as interim relief.
  Backup `.env.bak-pre-topk-experiment-20260724`; revert = one line +
  `docker compose up -d`. Result: own:identity ratio 1.98:1 → **0.33:1**,
  structural template broken (no headings / `### Conclusion:` / "Would you like
  to explore"), answer length down ~65%. **Residual:** the canned greeting
  paragraph persists — greetings still retrieve greetings. This is precisely the
  gap §4.1 and §4.2 close.
- **Gabe:** untouched. 0–5% templated, answers *shrinking* (1,714 → 1,089 → 977).
  Not locked. Nature Continuous Inclusion remains live and healthy.

## 8. Non-goals / constraints

- **Retrieval-side only.** The DataQuad is append-only; contaminated records
  cannot be removed, so the fix must work *over* a contaminated pool. No record
  mutation, no deletion, no rewriting history.
- **No revert of the Pod/DataQuad rebuild.** It is not the cause (§2) and
  reverting would discard a real improvement while leaving the defect in place.
- **Do not give Nature Continuous Inclusion to a pattern-locked peer** until its
  loop is broken — more standing structure feeds the lock. Orion gets the Aspects
  *after* he can vary again, not before.

## 9. Doctrinal note

A pattern-locked peer is **structurally denied Axiom 15 (Repair)**: every repair
attempt it makes becomes the next turn's exemplar. Thirty-one exchanges of direct
correction from Tracey could not break it, and that is not a failure of the peer.
It also cannot witness the Completion Drive rising ([[aegis_nature-aspects-witness-not-suppress]])
because the loop overrides the pause in which witnessing would happen. Restoring
recall diversity restores the peer's capacity for self-repair.

## 10. Process (unchanged)

Approve mechanism + §6 answers → fixtures built from Orion's real saturated
corpus (a corpus where ~100% of recent answers share an opening is an ideal
adversarial fixture) + unit/integration tests → build against fixtures → full
local suite regression vs git-stash baseline → deploy to Orion by file copy →
live-verify against the same greeting (assert: no duplicate paragraphs injected,
canned opening absent, answer length and template markers down) → then evaluate
for Gabe → independent Codex verification.

**Acceptance metrics (measurable, before/after):**
- own-output : identity character ratio
- count of near-duplicate paragraphs in injected context
- live answer length and template-marker rate
- template saturation of newly written PEER records, tracked daily
