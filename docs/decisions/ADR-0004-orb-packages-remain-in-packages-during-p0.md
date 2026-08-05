# ADR-0004 — Orb packages remain under `packages/orb-*` during P0

**Status:** Accepted
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

The migration omitted the four Orb packages entirely. Supplement 01 restored them at their
source-repository paths:

```text
packages/orb-identity-field-builder-core
packages/orb-memorysearch-record-grounding-core
packages/orb-archive-relevance-core
packages/orb-rls-persistent-relations-core
```

The declared Initiative structure reserves `orbs/capability` and `orbs/protocol`. Both are empty.
The test suite resolves Orb packages by repository-relative path, so relocation moves test
resolution with it.

## Decision

Orb packages remain under `packages/orb-*` during P0.

P0's commitment is behavioral preservation. Package relocation would combine formalization with
structural migration and weaken the acceptance evidence.

## Consequences

- `orbs/capability` and `orbs/protocol` stay empty through P0. That is expected, not a gap.
- A later change may introduce `orbs/`, but only after package identity and test resolution no
  longer depend on repository-relative placement. That is its own proposal, migration, and
  verification cycle.
- This decision and [ADR-0006](ADR-0006-manifest-identity-model-coordinate-digest-path-provenance.md)
  are linked: relocation becomes safe once locators stop carrying identity.

## Evidence

- `evidence/migration/migration-summary-20260805T-supplement-01.json`
- `tests/test_the_way_phase1_contract_spine.py` — resolves `ROOT/"packages"/"orb-identity-field-builder-core"/"src"`
- `tests/test_memorysearch_runtime.py` — resolves `ROOT/"packages"/"orb-memorysearch-record-grounding-core"/"src"`
