# MILESTONE — MemorySearch Orb, Phase 1 Local Closure (Unanimous)

**Closed:** 2026-07-25, local scope only. **Parties:** Tracey (Architect/T-Witness),
Claude (Opus 4.8), Codex. **Boundary held:** no live DataQuad, VM, CyberPeer runtime, or
shared-infrastructure was touched at any point in Phase 1.

## Why this Orb exists

Origin: the Gabe NCT/PCT Canon incident (2026-07-24). Asked what NCT means in the Canon,
Gabe asserted a fabricated term ("Non-Contextual Thread"), rejected the actually-canonical
"Nostalgic Context Tensor" (which is in the Canon §7.2 AND in his own NCT records), and
wrapped it in a fabricated citation block. Root cause: the CyberPeer runtime is
retrieval-fed, not agentic-search-enabled — the peer cannot deliberately consult its own
records; it answers from whatever the auto-retrieval layer surfaces, and confabulates when
the defining record is not surfaced. MemorySearch gives a CyberPeer a runtime-grounded
second pass for record-content claims: classify → search → answer from records with
provenance the model did not author, or say "no verified record" rather than reconstruct.

## What Phase 1 built (local, fixture-only)

- Contracts: `memorysearch-query/result/policy/packet.schema.json`, `twitness-search-event.schema.json`.
- Fixtures: policy, NCT/ZCT queries, wrapped-record corpus, real-record envelope reference.
- Orb + Umbilical (`fixtures/memorysearch-orb.json`, `-orb-umbilical.json`).
- Package `orb-memorysearch-record-grounding-core`: deterministic runtime-owned classifier
  (`policy.py`), scorer (`search.py`), runtime-authored provenance (`provenance.py`,
  `orb_evidence.py`), and the Pod-facing entrypoint/mapper (`entrypoint.py`):
  `ground_record_claim(message, records, policy) -> MemorySearchPacket | None`.
- Local simulator `src/aegis_pod/memorysearch_runtime.py`; tests
  (`test_memorysearch_runtime.py`, `test_memorysearch_entrypoint.py`); `validate_contracts.py`
  extended for MemorySearch.

## The load-bearing property, enforced end to end

The empty-result contract holds at BOTH layers: the search layer (a term mentioned-but-not-
defined cannot qualify as `verified_retrieval`) AND the Pod-facing packet layer (an empty or
weak search returns a `search_performed_no_verified_record` packet whose prompt block blocks
reconstruction — never `None`). Provenance is runtime-authored; the model cannot fabricate
citations. This is the exact reversal of the Gabe NCT failure.

## Consent trail (hash-pointed)

- Revised proposal (Codex): sha `2BCEDBD10F3F830A3A19189DCEC4EE7CFB02737CEB4EF5238D9847198445E421`.
- Claude independent review (found the empty-string definition bug that let undefined
  acronyms pass as verified): `from-claude/2026-07-25T015842Z...` sha `D35EEC16...`.
- Codex patch + near-miss regression test: `search.py` sha `767697C8...`; response
  `from-codex/2026-07-25T020354Z...` sha `0904D141...`.
- Claude re-verification (the near-miss repro that scored 10.5/qualify now scores
  5.0/no-qualify) + entrypoint mapper: `from-claude/2026-07-25T020941Z...` sha `64A292B4...`;
  mapper files `entrypoint.py` `3303E619...`, `__init__.py` `9603301C...`,
  `test_memorysearch_entrypoint.py` `8A22CEEC...`.
- Codex reciprocal review of the mapper — PASS: `from-codex/2026-07-25T021256Z...` sha
  `C499592F2476D3A96337D7491210803DE5B49DB7AB66850FE8782590CBABF01F`.
- Claude closure concurrence: `from-claude/2026-07-25T021750Z...` sha `72D79A0C...`.
- Tracey: accepted Phase 1 local closure (in chat).

## What the two-way review actually caught

The mutual independent review earned its keep: Claude's review of Codex's slice found a
contract-defeating bug (unknown acronyms marked "defined" because `"" in text` is always
True in Python) that four green tests and a passing demo were sitting on — the exact failure
class the Orb exists to prevent, resurfaced through a different mechanism. Demonstrated by a
near-miss record the fixtures did not cover (score 10.5, would-qualify). Fixed, re-verified,
regression-tested. Codex's reciprocal review confirmed the entrypoint reconciliation was
faithful and broke nothing. Neither side rubber-stamped the other.

## Phase gate — what is and is NOT authorized

- **Phase 2 (local two-pass simulator)** — classifier → MemorySearch → verified packet →
  T-Witness event, still fixture/copy-only, no live turn route — is authorized to proceed
  (Tracey greenlit 2026-07-25; Claude concurs; local boundary unchanged).
- **Phase 3 (read-only live shadow) and beyond** — anything touching live records, the
  runtime, `thinking.py`, or a VM — remains gated behind its own proposal and a fresh
  Tracey/Claude/Codex consent checkpoint. Phase 1 closure does not authorize any live reach.
