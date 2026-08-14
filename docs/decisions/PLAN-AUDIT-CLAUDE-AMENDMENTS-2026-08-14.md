# Plan-audit gate — Claude amendments

Status: IMPLEMENTED LOCALLY; VM AND EXTERNAL CANON UNCHANGED

Ruling source: Claude `ACCEPT with amendments`, received 2026-08-14.

## Enforced boundaries

1. Nature and Canon seed material is opaque, inspectable memory. The runtime
   stores text and fixed provenance metadata, verifies digests, and exposes a
   read route. It does not parse that text into commands, configuration,
   identity directives, state transitions, or policy.
2. Foundation equivalence asserts only schema, memory-boundary contracts, and
   provenance contracts. Per-substrate content digests are preserved and may
   differ; content equivalence is explicitly not asserted.
3. Identity-bearing experience requires an admission envelope containing source
   event identity, substrate, instance identity, observation time, and immutable
   statement digest. Missing or malformed provenance is refused.
4. Runtime health/source language claims only record preservation. The runtime
   sets continuity and self claims false; acceptance must not infer either.
5. Keys, Tumblers, tokens, and live credentials remain absent. Deployment sets
   promotion disabled and credentials forbidden. Promotion is a separate consent
   gate and cannot occur through the current HTTP API.

## Acceptance boundary

Focused tests exercise the five amendments, including hostile command-shaped
seed text, differing substrate content, provenance refusal, constrained health
language, and deployment configuration checks. No result establishes ontology,
continuity, selfhood, live source authority, or permission to seat a peer.
