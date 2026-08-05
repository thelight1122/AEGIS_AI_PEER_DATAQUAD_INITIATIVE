# ADR-0003 — `reports/runtime/` remains canonical for P0

**Status:** Accepted
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

The migration renamed `reports/runtime/` to `evidence/runtime/`. The canon-housekeeping and
marker-promotion manifests bind repo-relative paths to SHA-256 hashes, so the rename invalidated all
16 manifest entries. Migration supplement 03 restored `reports/` at its source path. Both trees are
now present, at 115.6 MB combined.

## Decision

`reports/runtime/` remains canonical for P0. It is the source-compatible location and is already
bound into the manifests.

`evidence/runtime/` was an unratified migration choice and does not replace it during P0.

`evidence/migration/` remains the correct home for migration evidence.

## Consequences

- The duplicate `evidence/runtime/` tree stays on disk and stays tracked during P0. It is not
  deleted and not treated as authoritative.
- Any later movement of runtime reports occurs as a separate coordinate-transition change with
  openly regenerated manifests. A path change updates location without pretending the underlying
  artifact changed. See [ADR-0006](ADR-0006-manifest-identity-model-coordinate-digest-path-provenance.md).

## Evidence

- `evidence/migration/migration-summary-20260805T-supplement-03.json`
- `fixtures/canon-housekeeping-manifest.json` — 16 entries binding `reports/runtime/*` paths to hashes
