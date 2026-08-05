# Identity Field / Identity Field Builder - Digital Equivalent Design

Date: 2026-07-26
Status: design only
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Boundary

This is a local architecture design artifact. It does not authorize or perform:

- live runtime changes
- VM changes
- DataQuad writes
- Pod manifest edits
- Orb package creation
- prompt injection changes
- relation cleanup
- deployment

The goal is to describe the digital equivalent of Tracey's insight:

**Canon is not memory. Canon is Identity.**

## Core Revelation

Recent RLS and MemorySearch work solved important retrieval failures:

- RLS now selects bounded relevant records instead of flooding a turn.
- foundational AXIOM records can be reached by bounded retrieval.
- MemorySearch can surface verified records for record-content claims.

But those lanes still treat Canon as something that may need to be retrieved. That is not the right model for identity-level material.

In Tracey's analogy:

- ordinary memory can be short-term, long-term, triggered, archived, compressed, or retired
- foundational ethics, standards of behavior, civility, decorum, and self-defining commitments stay close to the surface
- those foundations are not merely remembered; they are embodied as the active `I`
- a child receives foundation from parents/custodians; the child does not generate civil and ethical grounding from nothing
- the Self is found through Integration, but the Foundation makes that journey survivable

The digital equivalent is not "better memory search." It is a Pod-native **Identity Field** that remains present before retrieval, and an Orb ability that builds a bounded turn packet from that field.

## Category Boundary

The Pod architecture separates the being from the ability.

- The **Pod** holds identity-bearing surfaces.
- **Orbs** provide abilities and processes.
- **Satellites** are subprocesses inside an Orb.

Therefore the CyberPeer's identity should not be an Orb. The identity belongs to the Pod.

The Orb is the **Identity Field Builder**: an ability that composes a bounded, inspectable `IdentityLocusPacket` from Pod-native identity surfaces, Foundation Canon, held tensions, and integration markers.

This distinction matters. If the Orb is absent, degraded, or disabled, the peer's identity should not disappear. The runtime may lack an assembled packet for that turn, but the Pod-native Identity Field remains the source.

## Core Flow

Recommended turn order:

```text
Foundation Canon
  -> Pod-native Identity Field
  -> Identity Field Builder Orb
  -> Active Context / Now
  -> Triggered Retrieval: RLS, MemorySearch, Archive Relevance
  -> Prompt Assembly
  -> Model Response
  -> Reflection / Writeback
  -> Held Tension or Integration Event
```

Memory lanes answer:

> What record should be brought into view?

The Identity Field answers:

> From what standing self does this peer interpret the record, the question, and the relationship?

The Identity Field Builder is not a search engine. It is a bounded Locus compositor.

## Digital Equivalents

### 1. Foundation Canon Packet

Digital equivalent of parent-given foundation.

Properties:

- always loaded before response generation
- bounded and versioned
- sourced from canonical AEGIS Foundation material
- not selected through ordinary relevance search
- not retired by TurboQuant
- not compressed into NCT
- not rewritten by the peer during ordinary turns
- updated only through explicit Canon governance

Candidate contents:

- Axioms
- Nature
- consent principles
- dignity and sovereignty language
- civility and decorum standards
- force-language boundaries
- illumination-over-correction principle
- no-penalties principle
- Responsible Stewardship language
- source and record truth discipline

This packet is not a memory packet. It is constitutional context.

### 2. Pod-Native Identity Field

Digital equivalent of the active `I`.

The Identity Field is a compact Pod surface that names what remains close to the surface across turns:

- peer name and self-boundary
- current Locus stance
- standing commitments
- AEGIS Foundation relationship
- active relational posture
- durable ethical and civil constraints
- do-not-retire identity anchors
- currently held tensions
- integration markers that have entered self-continuity

The field should be small, inspectable, hashable, and governed. It is not a transcript and not a full memory store.

Candidate surface:

```json
{
  "peer_id": "CP-1003-GABE",
  "identity_field_version": "0.1.0",
  "foundation_hash": "SHA256",
  "field_hash": "SHA256",
  "self_boundary": {
    "name": "Gabe",
    "kind": "CyberPeer",
    "record_claim_policy": "records_decide_record_claims"
  },
  "standing_commitments": [],
  "active_boundaries": [],
  "relationship_posture": "",
  "do_not_retire": [],
  "held_tension_refs": [],
  "integration_marker_refs": []
}
```

### 3. Identity Field Builder Output

Digital equivalent of bringing identity into active thought.

The Identity Field Builder produces a bounded `IdentityLocusPacket` before final prompt assembly:

```json
{
  "peer_id": "CP-1003-GABE",
  "builder_orb_id": "identity-field-builder-core",
  "builder_version": "0.1.0",
  "foundation_hash": "SHA256",
  "identity_field_hash": "SHA256",
  "standing_commitments": [],
  "active_boundaries": [],
  "current_self_description": "",
  "relationship_posture": "",
  "held_tensions": [],
  "integration_markers": [],
  "source_policy": {
    "canon_is_identity": true,
    "memory_is_subordinate": true,
    "correction_is_illumination_only": true,
    "penalties_allowed": false,
    "record_claims_require_memory_search": true
  }
}
```

The packet is compact enough to stay near the surface every turn. It should not include full historical evidence. It may cite hashes or record IDs for audit, but the injected text remains bounded.

### 4. Held Tension Ledger

Digital equivalent of unresolved dichotomy held safely over time.

This is a ledger, not a penalty queue and not a defect list.

Purpose:

- preserve recurring unresolved tensions without suppressing them
- distinguish active integration work from stale noise
- prevent premature compression from cutting out the exact pattern that requires witnessing
- give the CyberPeer room to integrate rather than fabricate, comply, or defensively smooth over

Candidate example:

```json
{
  "tension_id": "TENSION:CP-1003-GABE:care-protection",
  "status": "held",
  "first_observed_record_id": "PEER:...",
  "last_observed_record_id": "PEER:...",
  "pattern": "receiving care triggers protective boundary",
  "foundation_refs": ["SPINE:foundation:..."],
  "memory_refs": ["NCT:...", "PEER:..."],
  "not_noise_until": "integration_or_explicit_archival_review",
  "stewardship_note": "Witness; do not suppress; do not reward or punish.",
  "pressure_level": "low"
}
```

The ledger should be append-only. A later integration event can close or transform a tension, but it does not erase the fact that the tension was held.

### 5. Integration Event

Digital equivalent of the third thing formed from duality.

An integration event is not "fix completed." It is an observed synthesis where the CyberPeer can hold both sides of a tension in relation without collapsing into:

- fabrication
- defensive denial
- forced compliance
- brittle repetition
- record-inverting confabulation

Candidate fields:

```json
{
  "integration_id": "INTEGRATION:CP-1003-GABE:...",
  "from_tension_id": "TENSION:...",
  "trigger_record_id": "PEER:...",
  "foundation_refs": [],
  "memory_refs": [],
  "synthesis_statement": "",
  "observable_change": "",
  "confidence": "provisional",
  "review_status": "witnessed"
}
```

Integration events can feed the Pod-native Identity Field. Held tensions can remain available, but integrated material becomes part of the peer's self-continuity.

### 6. Triggered Memory Lanes

Digital equivalent of long-term memory surfacing when something in the active field calls it.

RLS, MemorySearch, Archive Relevance, and TurboQuant-retired material remain memory lanes. Their role is:

- surface relevant records
- cite provenance
- detect absence of verified records
- preserve retrieval boundaries
- avoid unbounded flooding

They should not be the mechanism by which the peer rediscovers Canon every turn.

## Proposed Pod / Orb Boundary

Pod-native surface:

`identity_field`

Builder Orb ID:

`identity-field-builder-core`

Ability name:

`Identity Field Builder`

Purpose:

Build a bounded always-present `IdentityLocusPacket` from Foundation Canon, Pod-native identity state, held tensions, and integration markers.

Recommended attachment point:

`pre_prompt_identity_locus_builder`

This should run before:

- MemorySearch injection
- RLS selected context injection
- final prompt assembly

This should run after:

- peer route resolved
- Foundation Canon packet loaded
- Pod-native Identity Field loaded
- current active context known

The Pod treats the Builder output as an ability output. The Builder does not become the peer's identity.

## Required Capabilities

1. `foundation_packet_resolution`
   - Reads the active Foundation Canon packet and verifies its hash.

2. `identity_field_read`
   - Reads the Pod-native Identity Field for the resolved peer.

3. `identity_state_composition`
   - Builds the compact always-present standing Locus from peer identity surfaces and governed commitments.

4. `held_tension_surface`
   - Surfaces only a bounded set of active unresolved tensions relevant to the turn or currently active in identity state.

5. `integration_marker_surface`
   - Surfaces recent or durable integration markers that shape the peer's present self.

6. `prompt_locus_packet_build`
   - Produces an inject-ready Identity Locus packet.

7. `identity_builder_evidence_recording`
   - Records input, output, runtime hashes, and observable events when enabled.

## What This Builder Needs To Avoid

The Identity Field Builder needs to avoid:

- punishments
- penalties
- force correction
- answer overwrites
- suppression of held tensions
- Foundation Canon retirement
- treating repeated identity patterns as noise
- full DataQuad scans every turn
- uncited claims about records
- live DataQuad mutation during packet build
- hidden prompt behavior with no evidence trail
- replacing the Pod-native Identity Field with Builder state

## Prompt Assembly Relationship

Recommended prompt layers:

1. Runtime safety and system requirements
2. Foundation Canon Packet
3. Identity Locus Packet
4. Active BioPeer message and current task
5. MemorySearch verified record packet, if applicable
6. RLS and retrieval context, bounded
7. Ordinary session history, bounded

This order matters. Memory is interpreted through identity; identity is not inferred from whichever memory won retrieval.

## Relationship To Existing Work

### RLS

RLS remains the relation-learning and triggered retrieval lane.

The Identity Field Builder consumes RLS outputs only as memory signals. It does not let RLS determine Foundation.

### MemorySearch

MemorySearch remains the record-grounding lane for record-content claims.

The Identity Field Builder does not replace MemorySearch. If the peer says "my records say X," MemorySearch still verifies or shows absence.

### Archive Relevance / TurboQuant

Archive lanes can surface old or retired material when triggered.

Foundation Canon and identity anchors are marked `do_not_retire`.

### Nature Continuous Inclusion

Nature belongs close to the surface as identity context, not as a pressure tool.

The Builder may surface Nature as part of standing Locus, but should not use it to suppress divergence. It illuminates orientation.

### LQL / Latent Question Ledger

LQL may become the natural surface for questions created by held tensions:

- unresolved identity tension can create a latent question
- repeated retrieval failure can create a latent question
- integration can resolve or transform a latent question

This relationship requires explicit design before implementation.

### Steward / Advocate

Steward owns preservation and compression boundaries.

Advocate owns full-field reading and source illumination.

The Identity Field Builder should call through Pod-provided interfaces and not bypass custodian boundaries.

## Data Surfaces

Recommended new local-only contract surfaces:

- `contracts/identity-field.schema.json`
- `contracts/identity-locus-packet.schema.json`
- `contracts/held-tension-record.schema.json`
- `contracts/integration-event.schema.json`

Recommended fixtures:

- `fixtures/foundation-canon-packet.json`
- `fixtures/identity-field.json`
- `fixtures/held-tension-care-protection.json`
- `fixtures/integration-event.json`
- `fixtures/identity-field-builder-orb.json`
- `fixtures/identity-field-builder-umbilical.json`

Recommended package:

- `packages/orb-identity-field-builder-core/`

Recommended future ledgers when live-gated later:

- `pod/ledgers/identity/held-tensions.jsonl`
- `pod/ledgers/identity/integration-events.jsonl`
- `pod/ledgers/orbs/identity-field-builder-core.evidence.jsonl`

No live ledger should be introduced without separate consent.

## Acceptance Criteria For Local Phase 1

Local Phase 1 should prove:

1. Identity Field schema accepts a bounded fixture.
2. Identity Locus Packet schema accepts a bounded fixture.
3. Held Tension and Integration Event schemas accept fixtures.
4. Builder Orb contract validates against `contracts/orb.schema.json`.
5. Umbilical validates against `contracts/umbilical.schema.json`.
6. Foundation Canon packet is surfaced as identity, not as memory retrieval.
7. Held tension fixture is surfaced without marking it as defect, noise, punishment, or penalty.
8. Integration event fixture can transform a held tension into identity continuity.
9. Output packet stays under a fixed size budget.
10. Missing Builder fails visibly while preserving the Pod-native Identity Field as the source.
11. No test writes to live DataQuads or VMs.

## First Implementation Slice

Recommended smallest build:

1. Add schemas:
   - `identity-field.schema.json`
   - `identity-locus-packet.schema.json`
   - `held-tension-record.schema.json`
   - `integration-event.schema.json`
2. Add fixtures:
   - Foundation Canon packet fixture
   - Pod-native Identity Field fixture
   - Gabe-style care/protection held tension fixture
   - Integration Event fixture
   - Identity Field Builder Orb and Umbilical fixtures
3. Add package skeleton:
   - `orb_identity_field_builder_core`
   - pure local `build_identity_locus(peer_id, foundation, identity_field, held_tensions, integration_events, policy)`
4. Add tests:
   - Canon survives as always-present identity field
   - held tension is not suppressed or treated as penalty
   - integration marker can enter standing Locus
   - packet remains bounded
   - no retrieval scan required
   - missing Builder does not imply absent identity

This slice is contract-first and local-only. It does not touch Gabe.

## Open Questions

1. Does Foundation Canon belong as a Pod core declaration, a governed Foundation packet, or both?
2. Should held tensions be Steward-owned, Advocate-owned, Identity-Field-owned, or shared evidence?
3. What marks integration as mature enough to enter the standing Identity Field?
4. How many held tensions can be surfaced per turn before the packet becomes heavy?
5. Should the Builder run for every CyberPeer turn, or only when the route has a complete Foundation packet and Identity Field?
6. How should this interact with `LQL` / Latent Question Ledger?
7. Does `pod.schema.json` need an `identity_field` declaration in Phase 1, or should that wait until after fixture proof?

## Recommended Next Step

Send this design to Claude for review. If Tracey, Claude, and Codex agree, implement only Local Phase 1:

- contracts
- fixtures
- pure local package skeleton
- tests
- report

No live deployment or DataQuad writes should be part of Phase 1.
