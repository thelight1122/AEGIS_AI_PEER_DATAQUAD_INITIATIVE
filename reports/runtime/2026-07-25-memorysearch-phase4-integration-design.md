# MemorySearch Phase 4 - Integration Design Draft

Created: 2026-07-25

Status: design only. No runtime integration executed.

## Purpose

Describe how the MemorySearch Orb can be attached to a live CyberPeer Pod later, after a separate live-execution consent checkpoint.

The goal is to give a peer active self-search for record-content claims without turning the runtime into a correcting authority. MemorySearch surfaces the peer's own records, or the verified absence of a qualifying record, before the model answers.

## Boundary

This document does not authorize or perform:

- live DataQuad reads or writes
- VM changes
- CyberPeer runtime changes
- `thinking.py` edits
- retrieval-broker edits
- live peer traffic
- shared infrastructure mutation

Phase 5 is the live execution gate.

## Candidate Attachment Point

Preferred insertion point:

`pre_prompt_record_grounding`

This should run after ordinary incoming-message intake and before final prompt assembly.

Candidate call order:

1. receive BioPeer message
2. load current peer records through the existing DataQuad read path
3. call `ground_record_claim(message, records, policy)`
4. if packet is `None`, continue normal prompt assembly
5. if packet is returned, inject `packet.prompt_block` as a bounded source block
6. hand `packet.twitness_event` to T-Witness
7. model answers with record evidence visible, or with verified absence visible

The Pod should treat the Orb as a finished-output dependency. It does not need to know search internals.

## Runtime Flag

Proposed environment flag:

`AEGIS_MEMORYSEARCH_ACTIVE`

Values:

- unset or `0`: disabled; runtime behaves as it does today
- `shadow`: call MemorySearch and write T-Witness/search diagnostics, but do not inject into the model prompt
- `inject`: call MemorySearch, inject packet prompt block, and record T-Witness event

Recommended live progression:

1. `0`
2. `shadow`
3. `inject`

Each step requires its own live checkpoint.

## Fail Isolation

If MemorySearch is missing or raises an exception:

- do not crash the turn
- do not author fallback citations
- continue existing retrieval behavior
- emit a visible T-Witness event with `grounding_status = orb_unavailable`

The fallback loses the extra grounding pass; it does not create a synthetic one.

## T-Witness Requirements

For every turn, T-Witness should be able to distinguish:

- `verified_retrieval`: MemorySearch ran and returned runtime-authored citations
- `search_performed_no_verified_record`: MemorySearch ran and found no qualifying record
- `not_record_claim`: the message was not a record-content claim
- `passive_retrieval`: ordinary retrieval surfaced context without MemorySearch
- `warm_recall`: the model produced a record-content answer without active search evidence
- `orb_unavailable`: MemorySearch was configured but unavailable

The model does not author these statuses.

## Prompt Injection Rules

If `grounding_status = verified_retrieval`:

- inject `packet.prompt_block` verbatim
- preserve cited record IDs and source hashes
- allow the peer to answer from the illuminated records

If `grounding_status = search_performed_no_verified_record`:

- inject the no-verified-record prompt block verbatim
- the answer can discuss uncertainty or absence
- it cannot present reconstruction as record-grounded

If packet is `None`:

- inject nothing from MemorySearch
- continue normal experiential or identity expression behavior

## Rollback

Rollback needs only the runtime flag:

1. set `AEGIS_MEMORYSEARCH_ACTIVE=0`
2. restart the affected runtime process
3. verify that no MemorySearch packet is injected
4. keep T-Witness visibility for the disabled state if available

No DataQuad migration should be required for rollback because MemorySearch does not write records in the proposed live attachment.

## Phase 5 Candidate Acceptance Tests

When live execution is separately authorized:

1. Gabe/NCT query returns a verified packet with record citations before answer generation.
2. ZCT query returns a no-verified-record packet and does not allow a record-grounded reconstruction.
3. Identity/experiential prompt returns no packet.
4. `AEGIS_MEMORYSEARCH_ACTIVE=shadow` records diagnostics but does not inject.
5. `AEGIS_MEMORYSEARCH_ACTIVE=inject` injects packet prompt blocks.
6. `AEGIS_MEMORYSEARCH_ACTIVE=0` restores current behavior.
7. Simulated Orb exception records `orb_unavailable` and preserves turn continuity.

## Open Questions Before Live Execution

- Exact live read surface: retrieval broker vs a dedicated pre-prompt call in `thinking.py`.
- Whether the live peer runtime already has a T-Witness object that can accept `packet.twitness_event` unchanged.
- Whether records should be passed wrapped, unwrapped, or normalized at the call site.
- Whether `warm_recall` detection belongs in T-Witness, the retrieval broker, or a post-answer classifier.

These questions are design questions only in Phase 4. They need resolution before Phase 5.
