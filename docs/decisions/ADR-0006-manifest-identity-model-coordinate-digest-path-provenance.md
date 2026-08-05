# ADR-0006 — Manifest identity model: Coordinate, Digest, Path, Provenance

**Status:** Accepted as target model
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

The doctrine states that Tensor Coordinates are canonical and filesystem paths are implementation
details. The manifests contradict it.

`fixtures/canon-housekeeping-manifest.json` and the marker-promotion manifests bind identity-like
integrity claims to filesystem paths. When the migration renamed `reports/runtime/` to
`evidence/runtime/`, 16 of 16 manifest entries reported outside parameters. No artifact changed. Only
a locator changed.

Paths are still participating in identity. The contradiction is now demonstrated rather than
theoretical.

## Decision

The target manifest model distinguishes four things that are currently conflated:

```text
Coordinate    canonical identity
Digest        content integrity
Path          replaceable local locator
Provenance    why this locator currently represents that coordinate and digest
```

A path change then updates location without pretending the underlying artifact changed.

## Consequences

- This is the target model, not a P0 deliverable. P0 preserves behavior; it does not rewrite the
  manifest schema.
- [ADR-0003](ADR-0003-reports-runtime-canonical-for-p0.md) defers the `reports/` versus
  `evidence/runtime/` question to a coordinate-transition change. That change is the first
  application of this model.
- [ADR-0004](ADR-0004-orb-packages-remain-in-packages-during-p0.md) defers Orb relocation for the
  same reason. Relocation becomes safe once locators stop carrying identity.
- [ADR-0005](ADR-0005-orb-hash-drift-quarantined-pending-provenance.md) is the same failure mode in
  a different surface: a pinned digest with no provenance record for why it represents what it
  claims to represent.
- The R1 Tensor Coordinate schema and coordinate provenance schema are the natural place this model
  first becomes executable. SSSP §8 already names the provenance categories: source-derived,
  tensorization-policy assigned, RLS-derived, Steward-declared.

## Origin

Identified during the step 1 migration verification. Accepted by the Auditor as the strongest
finding of that work.
