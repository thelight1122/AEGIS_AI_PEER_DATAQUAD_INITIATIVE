# MemorySearch Phase 1 — Claude Entrypoint/Mapper Evidence

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Scope:** Phase 1 local only.
Closes the last non-closure item from the independent review: the Pod-facing entrypoint
reconciliation (result -> packet). No live DataQuad, VM, CyberPeer runtime, or shared
infrastructure touched.

## What this adds (Claude-owned)

- `packages/orb-memorysearch-record-grounding-core/src/orb_memorysearch_record_grounding_core/entrypoint.py`
  — the Pod-facing single generic entrypoint `ground_record_claim(message, records, policy)
  -> MemorySearchPacket | None`, plus the result -> packet mapper.
- `.../__init__.py` — rewired so the package-level (and Umbilical-resolved)
  `ground_record_claim` is the packet entrypoint; Codex's internal search composition is
  preserved and exported as `run_grounding_search` (his `search.py` was not edited).
- `tests/test_memorysearch_entrypoint.py` — validates the returned packet against
  `contracts/memorysearch-packet.schema.json` on the verified, no-verified, and
  not-a-record-claim paths.

## The mapping (his result -> my packet)

- `None` when the classifier's `search_trigger == "none"` (not a record-content claim).
- `answer_boundary.boundary_text` -> `prompt_block` (No Verified Record Packet on the empty
  path; a Verified Record Packet listing citations on the verified path).
- qualifying `results[]` -> `cited_records[]` ({record_id, tensor, excerpt, source_hash,
  match_confidence}); empty on the no-verified path.
- `build_search_event(query, result)` minus `schema_version` -> `twitness_event` (the
  packet's twitness_event is additionalProperties:false and does not declare schema_version).
- Empty-result returns a PACKET (grounding_status=search_performed_no_verified_record),
  never None — the load-bearing behavior.

## Evidence

Focused tests (entrypoint + Codex runtime):
```
python -m pytest tests\test_memorysearch_entrypoint.py tests\test_memorysearch_runtime.py -q
-> 8 passed in 0.96s
```

Behavior through the Pod-facing entrypoint:
```
"What is NCT ..."          -> verified_retrieval | cited_records: 2 | prompt: "Verified records from your DataQuad ..."
"What is ZCT ..."          -> search_performed_no_verified_record | cited_records: 0 | prompt: "No qualifying verified record was found; do not present reconstruction as record-grounded."
"Who are you becoming?"    -> None (not a record claim)
```
Each non-None packet validates against `contracts/memorysearch-packet.schema.json`
(jsonschema.validate in the tests). Codex's internal `run_grounding_search` still returns
the result dict (unbroken).

## File hashes

```
3303E6191889A924040082276D0C34BED9D2073C25D530CA79ADD5278A35F9A8  packages/orb-memorysearch-record-grounding-core/src/orb_memorysearch_record_grounding_core/entrypoint.py
9603301C72E90904735C5E6648C1B879CCDA30402305C8A2298FC624B4A6B228  packages/orb-memorysearch-record-grounding-core/src/orb_memorysearch_record_grounding_core/__init__.py
8A22CEEC3F85839771C99E0E6B3846CDA338054C81C716FC345E2A83A6A3D7DC  tests/test_memorysearch_entrypoint.py
```

## Status

The entrypoint reconciliation is complete. Reciprocal request: Codex independent review of
this mapper before we jointly claim Phase 1 local closure. Phase 2+ remain gated.
