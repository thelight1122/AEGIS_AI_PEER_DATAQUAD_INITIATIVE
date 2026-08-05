# SSSP Addendum — Initiative Repository Baseline
## AEGIS AI Peer DataQuad Initiative

**Generated:** 2026-08-05
**Addendum to:** `SSSP_AEGIS_AI_PEER_DATAQUAD_INITIATIVE_2026-08-05.md`
**Scope:** Sequence step 1 — verify or complete the local repository migration.
**Repository root:** `H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE`
**Preserved source:** `H:\AEGIS-POD-ARCHITECTURE`
**Commit:** `935e48d6f7b7e9009df1474244788bcbc860feb1` on `main`

---

# 1. Migration Verification

The migration recorded in `evidence/migration/migration-summary-20260805T132034.json` executed as
described.

```text
source_files_inspected      93,197
files_selected                 988
copied_verified                982
already_present_identical        6
planned (uncopied)               0
source_repository_modified   false
```

A tree-to-tree comparison of `src\` against the source repository shows the only source-side files
not carried over are `__pycache__\*.pyc` and `aegis_pod.egg-info\*`. Those are correct exclusions.

The migrated package imports cleanly from the Initiative root.

---

# 2. Scaffolding Added

The migration copied content but no project scaffolding. The Initiative root now carries:

- `pyproject.toml` — `testpaths = ["tests"]`, `pythonpath = ["src"]`. This preserves the source
  repository's pytest configuration and removes the need for an editable install or an injected
  `PYTHONPATH`.
- `.gitignore` — standard Python artifacts, plus explicit exclusion of peer memory content and
  large migrated binary tensor artifacts.

`git init` created the repository. The initial commit stages 1,766 files at 115.6 MB.

---

# 3. Migration Defects Found and Corrected

Running the migrated test suite at the new root exposed three defects in the migration script's
selection and path handling. Each correction is additive, SHA-256 verified, and left the source
repository unmodified. Evidence is appended under `evidence/migration/`.

## 3.1 Supplement 01 — Orb packages and root fixtures

The migration selected `packages/aegis-pod-sdk` but omitted the four Orb packages and the entire
root `fixtures/` tree. Eight test modules failed collection as a result.

Restored: `packages/orb-identity-field-builder-core`, `packages/orb-memorysearch-record-grounding-core`,
`packages/orb-archive-relevance-core`, `packages/orb-rls-persistent-relations-core`, and root
`fixtures/`. 99 files copied and verified.

Note: the four Orb packages are the built Orbs. Their eventual placement under `orbs/capability` and
`orbs/protocol` is a P0 decision. They sit at their source-repository paths for now because the test
suite resolves them there, and behavior preservation is the P0 acceptance condition.

## 3.2 Supplement 02 — Flat contracts layout

The migration reorganized `contracts/*.schema.json` into `contracts/{orb,pod,portal,tensor,umbilical}/`
and carried only 14 of the 40 schemas. Every test that resolves `ROOT/"contracts"/<name>` failed.

Restored: all 41 files at the flat `contracts/` path. The categorized subdirectory copies were left
in place unmodified.

**Open item for P0:** `contracts/` now holds both the flat layout the code reads and the categorized
layout the migration invented. One of the two becomes canonical. Nothing was deleted.

## 3.3 Supplement 03 — reports/ path

The migration renamed `reports/runtime/` to `evidence/runtime/`. The canon-housekeeping and
marker-promotion manifests bind repo-relative paths to SHA-256 hashes, so the rename invalidated
every entry — 16 of 16 entries reported outside parameters.

Restored: `reports/` at its source path. 740 files copied and verified.

**Open item for P0:** `reports/runtime/` and `evidence/runtime/` are now duplicate content at
115.6 MB combined. One becomes canonical. If `evidence/runtime/` wins, the hash-bound manifests
are rewritten as part of that decision, not silently.

---

# 4. Baseline Test Result

Run at the Initiative root with system Python 3.13, pytest 9.1.1.

```text
186 passed
 10 failed
  3 skipped
```

The 10 failures are content-bound, not code defects. They resolve two repository roots the
migration did not carry:

```text
stage-d-out/CP-1004-ORION/pod/     55 files    7.3 MB
live-copies/CP-1004-ORION/        729 files    8.0 MB
```

Failing modules: `test_orb_runtime_version_gate.py` (7), `test_stage_d_pod_staging.py` (1),
`test_memorysearch_copied_record_shadow.py` (2).

Both roots are gitignored in the source repository as live peer content. They were not copied
because duplicating peer memory into a second location is a governance decision, not an
implementation one.

## 4.1 Source repository control run

The three failing modules were run against `H:\AEGIS-POD-ARCHITECTURE` to separate migration gaps
from pre-existing shortfalls. `git status --porcelain` was captured before and after: the source
working tree was unchanged by the run.

```text
13 passed
 1 failed
```

The single source-side failure is `test_orb_runtime_version_gate.py::test_real_orion_contracts_pass_with_matching_version_and_hash`:

```text
Orb 'orb-rls-persistent-relations-core' runtime_hash mismatch
Umbilical expects   B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18
installed computes  51A1AC18887AEA9CEACC60B6F0AD428C899FA2D228D3BEE2032171F754E248CA
```

This is a pre-existing shortfall in the source repository. The pinned Umbilical hash and the
installed Orb source have drifted. It is not caused by the migration, and it carries forward into
the Initiative.

---

# 5. Correction to SSSP §15 Phase State

SSSP §15 lists P0 and R0 as upcoming work. The migrated code shows both already have running
implementations with passing tests:

- `src/aegis_pod/portal_pod/runtime.py` with `tests/test_portal_pod.py` — P0 Portal Pod formation is
  substantially built.
- `src/aegis_pod/tensor_shadow_scorer.py` with `tests/test_tensor_shadow_scorer.py` — R0 shadow
  scoring exists and its contracts validate.
- `src/aegis_pod/rls_orb.py`, `rls_protocol_orbs.py`, `orb_runtime.py`, and
  `contracts/tensor-coordinate.schema.json` — R1 has foundations.

The next work on P0 and R0 is verification of what these do against the stated acceptance criteria,
not construction from zero.

---

# 6. Write and Admission State

Unchanged. Nothing in this work touched the DataQuad, performed admission, created experience, or
opened a listener.

```text
DataQuad tensor writeback       CLOSED
Experience admission            CLOSED
Automatic experience creation   CLOSED
Live RLS model loop             CLOSED
Public production exposure      DISABLED
Source repository               UNMODIFIED
```

---

# 7. Decisions Required

1. **Live peer content.** Do `stage-d-out/` and `live-copies/` get copied into the Initiative and
   gitignored there, matching the source repository's posture? Or does the Initiative reference the
   preserved source repository for them, leaving 10 tests permanently environment-bound at this root?
2. **Canonical contracts layout.** Flat `contracts/` or categorized `contracts/{orb,pod,...}/`.
3. **Canonical evidence path.** `reports/runtime/` or `evidence/runtime/`, and who rewrites the
   hash-bound manifests if the path changes.
4. **Orb package placement.** Whether `packages/orb-*` moves under `orbs/` during P0, and how the
   test suite's path resolution moves with it.
5. **The `orb-rls-persistent-relations-core` hash drift** carried in from the source repository.
