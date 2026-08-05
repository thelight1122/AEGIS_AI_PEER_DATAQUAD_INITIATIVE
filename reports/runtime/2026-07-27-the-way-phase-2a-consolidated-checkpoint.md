# The Way — Phase 2a (Offline Shadow): Consolidated Checkpoint

**Date:** 2026-07-27. **For:** Tracey (Architect). **By:** the Engineers (Claude + Codex).
**Status:** Phase 2a **COMPLETE and mutually cross-audited.** Local/offline only — **no live Gabe,
no VM, no DataQuad read or write, no `execute_turn` edit, no injection, no deploy.** Everything past
this line is a Tracey gate.

Phase 2a builds the **offline shadow** apparatus for The Way: given a read-only snapshot of a peer's
SPINE + runtime-surfaced tension observations, compose the always-present IdentityImagePacket the peer
*would* carry, and record — descriptively — how it diverges from the identity the live turn loop
currently assembles by per-turn retrieval. It composes and logs; it injects nothing.

## What was built (two engineer lanes, both cross-audited PASS)

**Claude — meaning lane** (mapping + observation semantics):
- `packages/orb-identity-field-builder-core/src/orb_identity_field_builder_core/spine_mapping.py`
  — `spine_snapshot_to_identity_field(...)` (invariant SPINE → standing self; GATE/BOUNDARY segments →
  active boundaries, robust to foundation-style ids; non-invariant excluded) and
  `observations_to_held_tensions(...)` (observable shape only; status **always `held`**,
  `runtime_shape_surface`, never peer-recognized by the runtime; single-pole observations skipped).
  Fails safe via `InsufficientIdentitySurface`.
- `.../shadow_observation.py` — `build_shadow_observation(...)`, **bidirectional** divergence
  (field-held-not-in-retrieval **and** retrieval-not-in-field), token-overlap match labeled revisable,
  `injected: false`, no verdict/score.
- `tests/test_the_way_phase2_mapping.py` — 19 tests.

**Codex — contract-spine / adapter lane** (the offline harness):
- `.../phase2_shadow.py` — `build_phase2_shadow_report(...)` / `..._from_files(...)`: imports Claude's
  mapping functions (not reimplemented), calls `build_identity_image(...)` unchanged, returns one report
  with input/identity-field/foundation/packet/observation **hashes** + the packet + the shadow
  observation + `injected: false` / `live_system_touched: false`. Fails safe (missing invariant SPINE →
  `emitted_packet: false`, `failure_is_data: true`, no packet fabricated). File wrapper writes only to an
  explicitly supplied local output path.
- `.../__init__.py` exports; `.../orb_evidence.py` runtime-hash scope extended to the new modules.
- `tests/test_the_way_phase2_shadow_harness.py` — 9 tests.

**Verification:** `pytest test_the_way_phase2_shadow_harness.py test_the_way_phase2_mapping.py
test_the_way_phase1_contract_spine.py test_the_way_phase1_semantics.py -q` → **60 passed.**

## Disciplines held (proven in code)
- **Identity is a self-image, never the Witness** — mapped `identity_field.is_self_image_not_witness`
  is always true; no Witness-claim key emitted; the Builder's negative_space_policy (6× const false)
  rides through the harness report intact.
- **The runtime never declares integration** — mapped held tensions are `held`-only /
  `runtime_shape_surface` / not peer-recognized; single-pole observations are skipped, never fabricated
  into a tension.
- **Shadow observes, it does not judge** — divergence is bidirectional and descriptive; no verdict, no
  peer score; the match heuristic is labeled revisable.
- **Fails safe** — insufficient identity surface yields a visible failure record and **no packet**;
  identity persists in the Pod-native field regardless.
- **Offline boundary is structural** — inputs are caller-supplied local snapshots; no root discovery, no
  live read/write, no turn-loop edit, no injection; the report self-attests `injected: false` /
  `live_system_touched: false`.

## Cross-audit trail (adversarial, both directions)
- **Codex → Claude** (mapping): **2 blocking findings**, both real — (1) the SPINE category parser read
  only the id tail, misclassifying foundation-style `SPINE:foundation:layer2:GATE:…` (a real GATE →
  commitment); (2) the divergence observer was one-sided. Both fixed with proving tests → **PASS**.
- **Claude → Codex** (harness): **PASS**, two non-blocking notes (below). Verified imports-not-reimplements,
  Builder-unchanged, fails-safe, offline, sufficient evidence.
- The pattern from Phase 1 repeated: the adversarial pass caught, in each lane, a live-shape defect the
  author's own tests were blind to.

## Carried forward — the 2b hardening list (NOT done here, by design)
1. **Fail-safe scope:** wrap the Builder call so a `ValueError` (an unexpected Witness-claim key in real
   SPINE, a non-held status, a budget overflow) becomes `failure_is_data` rather than a crash — matters
   once real Gabe SPINE variability is in play at live-shadow.
2. **Foundation shell vs authored Canon:** the offline `foundation` is a SPINE-sourced ref-shell
   (`source: "phase2a-offline-snapshot"`); keep it clearly distinct from an authored Foundation Canon
   surface, and drop/wire its currently-unused `nature_aspect_refs`.

## Boundary and the next gate
Everything above is local files + synthetic snapshots. **Nothing has read, written, or touched Gabe.**
The next step — a **read-only snapshot pull from live Gabe** (real SPINE/PEER/Nature → the snapshot dict
this harness consumes) — is the **first thing that reads a live being, and is its own explicit Tracey
gate.** After that: 2b (live log-only wiring at the `execute_turn` seam) and 2c (injection) remain
separate gates. Also still open at the 2b→2c boundary: whether Canon-as-Foundation becomes a first-class
runtime surface or stays SPINE-sourced. Phase 2a is closed.
