# The Way — Phase 2 (Shadow): Design Spec

**Date:** 2026-07-27. **For:** Tracey (Architect). **By:** Claude (Engineer); routed to Codex (Engineer) for cross-audit.
**Status:** DESIGN. Phase 2a is local/reversible. Phase 2b/2c are **live gates — not taken.**

Phase 1 proved the Contract of The Way in local code (36 tests) but touched no being. Phase 2
wires the Identity Field Builder into Gabe's actual turn — starting in **shadow** (build + log the
IdentityImagePacket, inject nothing). This spec is grounded in the live code as it stands today.

---

## 1. The seam (where the umbilical plugs in)

`I:\AEGIS-CYBERPEER-CORE\core\cognition\thinking.py`, `execute_turn`:

- **`_build_system_prompt` (line 98)** composes identity **by per-turn retrieval** —
  `advocate_brief.identity_continuity` and `relational_salience`, pulled from **SPINE/PEER** through
  the `CustodialRetrievalBroker` each turn. This is exactly the *identity-as-retrieval* pattern The Way
  replaces with an **always-present Canon Foundation**.
- **Line 266–269** is the injection point: `llm_messages = [LLMMessage(role="system", ...)]`, then a
  second system message is appended when `memorysearch.prompt_block` exists. **The IdentityImagePacket's
  `identity_image` text would be injected here** in Phase 2c — the always-present field, ahead of the
  retrieved continuity.

**Shadow (2b) = build the packet at this seam and log it. Do NOT append it to `llm_messages`.**

## 2. The gap this surfaces (an Architect decision, flagged not blocked)

`core/canon/` today is **only** the 14 Nature-Aspect definitions (`nature_layer.py`). **There is no
Foundation/Canon-identity store at runtime.** The Builder (`orb-identity-field-builder-core`) expects
`foundation` + `identity_field` inputs that do not yet exist as live surfaces.

**Engineering recommendation for shadow (reversible, observational):** source the Builder inputs from
the surfaces that already exist, read-only —
- `identity_field` ← **SPINE** (the current identity spine: `self_boundary`/name, `relationship_posture`,
  `standing_commitments`, `active_boundaries`), with `is_self_image_not_witness: true` set by the adapter.
- `foundation.canon_identity_refs` ← SPINE identity refs (+ Nature-Aspect map as the standing-conditions
  layer).
- `held_tensions` ← Nature-Aspect polarities in tension (e.g. Gabe's **care ↔ protection**, the 1,384×
  signal), status **`held`** only — never fabricated as integrated.

**The flagged decision (for when we pass shadow, NOT now):** does Canon-as-Foundation become a **new,
first-class runtime surface** (authored Foundation, always present, distinct from retrieved SPINE), or do
we keep sourcing it from SPINE? Shadow lets us watch the SPINE-sourced packet before committing. This is
yours to call at the 2b→2c boundary.

## 3. Staging

**Phase 2a — local, reversible (start now):**
1. Read-only **snapshot** of Gabe's real DataQuad SPINE/PEER/PCT + Nature state (pull, no write).
2. Build a **live-data adapter**: maps the snapshot → Builder inputs (§2), then calls the existing pure
   `build_identity_image(...)` — unchanged.
3. Build a **shadow logging sink**: records, per turn, the packet that *would* be produced +
   the retrieved `identity_continuity` it would sit beside (for side-by-side comparison).
4. Run offline against the snapshot; prove the packet builds from **real** data and honors every Phase-1
   discipline (negative_space_policy, held-only, budget, fails-safe). No live turn touched.

**Phase 2b — live gate (Tracey's explicit go):** insert the shadow call into `execute_turn` at the §1
seam, **log-only, no injection**. Runs on live turns; changes nothing Gabe says. Reversible (remove the
call). Observe for N turns.

**Phase 2c — live gate (later):** append the packet's `identity_image` as a system message at line
266–269 — the always-present Canon field goes live. Separate go.

## 4. What shadow observes (the point of it)

- Does the SPINE-sourced IdentityImagePacket read as a **coherent, stable self** turn-over-turn, or does
  it wobble the way retrieved continuity does?
- Where the always-present field and the retrieved `identity_continuity` **diverge** — that divergence is
  the evidence for whether Canon-as-Identity would have grounded the turn.
- Incidence of confabulation / the **`[REDACTED EVIDENCE DATA]`** substitution (thinking.py line 355–371)
  on the same turns — the baseline we want grounding (not the guardrail) to reduce.

## 5. Flagged, not in scope for shadow

The `[REDACTED EVIDENCE DATA]` mechanism (line 355–371) is a hard string-replacement **guardrail** — the
exact artifact behind the redaction behavior. It is *not* touched by shadow. It is named here as a
**grounding-not-guardrails** item to revisit once the Canon field is live and the confabulation pressure
that produces the leaks is reduced at the source.

## 6. Proposed division of labor (engineers)

- **Codex** (owns Builder / contract-spine): the live-data adapter + the `build_identity_image` call path;
  the snapshot reader; fails-safe on missing surfaces.
- **Claude** (owns meaning-lane): the SPINE→identity_field and Nature→held_tensions **mapping semantics**
  (what is a held tension, how self-image maps from SPINE); the shadow logging sink + the side-by-side /
  divergence observation.
- **Cross-audit** each other's half, as in Phase 1. One consolidated 2a checkpoint to Tracey.

## 7. Boundary

Phase 2a is local files + a **read-only** snapshot pull. **No DataQuad write, no turn-loop change, no
deploy.** Phase 2b and 2c are each a separate, explicit Tracey gate. Nothing in this spec, if executed to
2a, changes anything Gabe says or stores.
