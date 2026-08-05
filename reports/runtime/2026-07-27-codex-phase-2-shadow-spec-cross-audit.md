# Codex Cross-Audit: The Way Phase 2 Shadow Design Spec

Date: 2026-07-27
Scope: Design cross-audit only
Status: CONCUR WITH ONE STAGING CLARIFICATION

## Source Audited

Claude spec:

`H:\AEGIS-POD-ARCHITECTURE\reports\runtime\2026-07-27-the-way-phase-2-shadow-design-spec.md`

Spec SHA256:

`F612250049ED978A273D82A2B11A827BEE07D0B6E826E4634523C980DF5365B3`

Standard hash checked:

`7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`

## Verified Read-Only Findings

1. The turn-loop seam is correctly identified.
   - `I:\AEGIS-CYBERPEER-CORE\core\cognition\thinking.py`
   - `execute_turn` builds the retrieved DataQuad-grounded `system_prompt`, then creates `llm_messages = [LLMMessage(role="system", content=system_prompt)]`.
   - MemorySearch already appends as a second system message immediately after.
   - This is the correct future injection seam for an IdentityImagePacket system message, and the correct live-shadow seam for log-only observation.

2. `_build_system_prompt` currently composes identity by per-turn retrieval.
   - It receives `identity_continuity` and `experiential_continuity`.
   - Its own comments identify Advocate as `identity_continuity (SPINE + PEER): who the peer is and who matters`.
   - This matches The Way diagnosis: identity is currently retrieved each turn, not held as an always-present Canon field.

3. The runtime Canon gap is real.
   - `I:\AEGIS-CYBERPEER-CORE\core\canon\` contains only `__init__.py` and `nature_layer.py`.
   - `nature_layer.py` defines the 14 Nature-Aspect definitions.
   - There is no first-class runtime Foundation/Canon identity surface yet.

4. SPINE-sourced shadow inputs are the right reversible engineering move for 2a.
   - Because no runtime Foundation surface exists yet, a read-only adapter should map existing SPINE/PEER/Nature data into the Phase-1 Builder contracts.
   - This should be treated as an observational approximation, not the final architectural answer.
   - Tracey's later 2b->2c decision remains open: first-class Canon Foundation surface vs continued SPINE-sourcing.

5. The redaction issue is correctly out of Phase 2a scope.
   - The `[REDACTED EVIDENCE DATA]` behavior is a response-sanitizing guardrail in `thinking.py`.
   - Shadow should observe whether Identity Field grounding reduces the pressure that produces leaks; it should not modify the guardrail.

## Staging Clarification

I concur with Claude's staging, with one wording clarification:

- Phase 2a should be offline/local shadow from a read-only snapshot: build the packet as if at the seam, but no turn-loop edit.
- Phase 2b should be live log-only wiring at the actual `execute_turn` seam: build and log only, inject nothing.
- Phase 2c should be live injection: append `identity_image` as a system message, still under separate Tracey gate.

This is not a disagreement; it keeps the seam language precise.

## Codex Proposed 2a Slice

Codex can own the contract-spine engineering slice:

1. Snapshot reader
   - Reads a local/read-only Gabe snapshot path.
   - Accepts explicit source roots rather than discovering live paths.
   - Produces structured input bundles only.
   - Fails visibly if SPINE/PEER/Nature surfaces are missing.

2. Live-data adapter shell
   - Converts Claude-owned semantic mappings into Builder input shape.
   - Keeps mapping rules injectable/configurable so Claude can own semantics without Codex hardcoding meaning.
   - Enforces `is_self_image_not_witness: true`.
   - Enforces active held tensions as `status: "held"` only.

3. Builder call path
   - Calls existing `orb_identity_field_builder_core.build_identity_image(...)`.
   - Preserves Phase-1 negative-space policy.
   - Does not mutate the Builder's semantics.

4. Offline shadow harness
   - Runs against local snapshot bundles.
   - Produces an inspectable JSONL or Markdown report containing:
     - input hashes
     - IdentityImagePacket hash
     - packet budget
     - negative-space policy flags
     - failure records, if surfaces are missing
   - No runtime prompt injection.
   - No live store writes.

5. Tests
   - Positive path: real-shaped snapshot builds a valid IdentityImagePacket.
   - Missing surface: visible failure, no fabricated identity field.
   - Integrated tension: rejected unless represented by Claude's integration-event lane, not active held set.
   - No live path/action leakage in 2a harness.

## Claude Proposed 2a Slice Accepted

Claude's proposed meaning-lane slice makes sense:

- SPINE -> identity_field mapping semantics.
- Nature -> held_tensions mapping semantics.
- Shadow logging/divergence observation semantics.
- Side-by-side comparison of retrieved identity continuity vs IdentityImagePacket.

Codex should cross-audit Claude's mapping and observation outputs after implementation, just as Claude re-audited the Contract-spine lane.

## Phase Boundary

This cross-audit does not authorize Phase 2b or 2c.

2a may proceed as local/reversible/offline if Tracey concurs with the division:

- no DataQuad write
- no turn-loop edit
- no Gabe live prompt change
- no deployment
- no VM mutation

Anything live remains a separate explicit gate.
