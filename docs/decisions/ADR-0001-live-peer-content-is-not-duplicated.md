# ADR-0001 — Live peer content is not duplicated into the Initiative

**Status:** Accepted
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

The migrated test suite fails 10 tests at the Initiative root. All 10 resolve repository-relative
paths into live peer state that the migration did not carry:

```text
stage-d-out/CP-1004-ORION/pod/          55 files      7.3 MB
live-copies/CP-1004-ORION/             729 files      8.0 MB
stage-gabe-out/CP-1003-GABE/pod/records                4.4 GB
```

All three are gitignored in `H:\AEGIS-POD-ARCHITECTURE` as live peer content. Copying them into a
second root would make the Initiative a second location holding authoritative peer state.

## Decision

Live peer content is not duplicated. `stage-d-out/`, `live-copies/`, and `stage-gabe-out/` remain
outside the Initiative repository.

"Exactly one live source afterward" applies to authoritative peer state wherever the system runs.
Local staging does not create an exception.

The Initiative references an explicitly configured live-state root rather than carrying one.

Tests requiring live peer state are classified as environment-bound integration tests. Ordinary
repository tests use synthetic, non-peer fixtures.

## Consequences

- The 10 failures are not migration failures and are not counted as such.
- A root `conftest.py` classifies the affected modules and skips them when the required live-state
  paths do not resolve. No test file is modified; when live state is present the tests run exactly
  as before.
- The environment-bound set at this commit:

  ```text
  tests/test_orb_runtime_version_gate.py          stage-d-out/CP-1004-ORION/pod
  tests/test_stage_d_pod_staging.py               stage-d-out/, live-copies/CP-1004-ORION
  tests/test_memorysearch_copied_record_shadow.py stage-gabe-out/CP-1003-GABE/pod/records
  ```

- `tests/test_memorysearch_copied_record_shadow.py` warrants specific attention. With its record
  root absent it does not error — it silently retrieves zero records and asserts on a degraded
  grounding status. Absent peer state read as an empty result rather than as a missing precondition.
  Classification makes that precondition explicit.

## Evidence

- `evidence/migration/migration-summary-20260805T132034.json`
- `docs/sssp/SSSP-2026-08-05-ADDENDUM-INITIATIVE-REPOSITORY-BASELINE.md` §4
- `fixtures/memorysearch-shadow-scenarios.json` → `source_root: stage-gabe-out/CP-1003-GABE/pod/records`
