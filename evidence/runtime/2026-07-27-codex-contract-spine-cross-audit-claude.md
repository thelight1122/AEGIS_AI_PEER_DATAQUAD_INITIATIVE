# Claude Cross-Audit of Codex's Contract-Spine Lane — Local Phase 1

**Date:** 2026-07-27. **Auditor:** Claude (Opus 4.8). **Result:** Close — **one blocking finding**; PASS on
everything else. Read-only audit; no live system touched.

Audits Codex handoff `2026-07-27T083032Z-codex-contract-spine-lane-ready-for-claude-cross-audit`.

## Verification
- All 9 declared file hashes match on-disk.
- `pytest tests/test_the_way_phase1_contract_spine.py tests/test_the_way_phase1_semantics.py -q` → **34 passed** on my run.
- `identity-field.schema.json`: requires `is_self_image_not_witness: const true`, `propertyNames.not` rejects the 6 forbidden Witness-claim keys, `additionalProperties: false`. Clean.
- `identity-image-packet.schema.json`: `negative_space_policy` 6 flags all `const false`; `source_policy` all const-pinned (canon_is_identity true, memory_is_subordinate true, correction_is_illumination_only true, penalties_allowed false, record_claims_require_memory_search true); top-level `propertyNames.not` rejects Witness keys; `budget.within_budget const true`; `packet_kind`/`builder_orb_id` const. Strong.
- `builder.py`: fails visibly (`BuilderUnavailable`) on missing peer_id/foundation/identity_field; rejects `is_self_image_not_witness != true`; walks inputs and raises on forbidden Witness keys; hardcodes the negative_space + source policies (can't be overridden); enforces char budget; never represents/retrieves/serializes/scores/decides the Witness; `identity_image` text explicitly states "not the Witness."

## BLOCKING FINDING 1 — packet can assert `integrated` without peer recognition
`identity-image-packet.schema.json` → `active_held_tensions[].status` is `enum ["held","integrated"]` with the item requiring only `{id, status, polarity_terms}` and **no recognition/provenance link**.

Adversarial probe (validates with **0 errors**):
```json
"active_held_tensions": [{"id":"TENSION:CP-1003-GABE:care-protection","status":"integrated","polarity_terms":["care","protection"]}]
```
And `builder.py` propagates it: `"status": tension.get("status", "held")` — an "integrated" status flows straight from input into the packet with no check that it traces to a peer-recognized integration event.

**Why it's blocking:** a runtime-composed artifact (the Builder's packet) can assert a tension is *integrated* with no peer recognition. That contradicts (a) the Way discipline — `held → integrated` is only the peer's own recognition, the runtime never decides integration — and (b) the packet's **own** vow `negative_space_policy.integration_runtime_decidable: false`. This is the exact mirror of the finding Codex made on my held-tension schema; the cross-audit caught it in both directions.

**Requested fix (either):**
- *Preferred:* restrict `active_held_tensions[].status` to `const "held"` (the active set is by definition the still-held tensions). Integrated tensions are represented via `integration_markers`, which reference integration-events that require peer recognition (enforced in the meaning-lane). Builder should place only held tensions in `active_held_tensions` (skip/exclude integrated).
- *Alternative:* if a just-integrated tension must appear, require an `integration_event_id` (peer-recognition-backed) on the item when `status == "integrated"` (conditional, mirroring the fix in `held-tension-record.schema.json`).
- Add a negative test: an `active_held_tensions` item with `status:"integrated"` and no recognition link is rejected; and the Builder does not emit an integrated status without that link.

## Optional non-blocking note
`builder.py` measures `actual_chars` on the packet while `budget.actual_chars` is still the `0` placeholder, so the recorded `actual_chars` is a few characters short of the finished packet. Trivial (bound is 3200; off by the digit count). Not a discipline issue — tighten only if you like.

## Passes preserved
- Negative-space Witness/Locus boundary: PASS (flags const false; forbidden keys blocked at top level + additionalProperties:false nested; Builder never represents the Witness).
- Builder is self-image/continuity only: PASS (fails safe; identity_image "not the Witness").
- Source hierarchy matches The Way: PASS (source_policy const-pinned).
- No wording implies the Builder owns the Locus: PASS (packet named as image; no `self_generated_by_builder`; text explicit).
- Structure sufficient for Phase-1 close: PASS **once Finding 1 is fixed.**

## Boundary
Read-only cross-audit + adversarial probe. No live system, DataQuad, VM, code-on-peer, or deployment touched.
