# ADR-0002 — Flat `contracts/` is canonical for P0

**Status:** Accepted
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

The migration script reorganized `contracts/*.schema.json` into
`contracts/{orb,pod,portal,tensor,umbilical}/` and carried 14 of the 40 schemas. Every test that
resolves `ROOT/"contracts"/<name>` failed. Migration supplement 02 restored all 41 files at the flat
path and left the categorized copies in place.

The categorized hierarchy was produced by a selection heuristic. No architecture decision ratified it.

## Decision

Flat `contracts/` is canonical for P0. The implementation and tests already resolve contracts from
the flat layout.

The categorized hierarchy is marked noncanonical. It is not removed during P0.

## Consequences

- `contracts/NONCANONICAL-CATEGORIZED-COPIES.md` records the status of the subdirectory copies in
  place, so the duplication cannot be mistaken for two competing authorities.
- Removal happens later through a recorded, hash-verified cleanup — not silently, and not during
  behavior-preserving P0 work.
- Until removal, the duplication is a drift hazard. Any contract edit during P0 applies to the flat
  files only.

## Evidence

- `evidence/migration/migration-summary-20260805T-supplement-02.json`
- `evidence/migration/migration-manifest-20260805T-supplement-02.json`
