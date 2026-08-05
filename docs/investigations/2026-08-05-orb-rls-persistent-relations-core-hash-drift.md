# Provenance Investigation — `orb-rls-persistent-relations-core` runtime hash drift

**Opened:** 2026-08-05
**Status:** Findings recorded. Resolution not taken.
**Governing decision:** [ADR-0005](../decisions/ADR-0005-orb-hash-drift-quarantined-pending-provenance.md)
**Orb/Umbilical status:** DRIFTED — quarantined from authoritative formation

---

## The mismatch

```text
Orb            orb-rls-persistent-relations-core
Umbilical expects   B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18
installed computes  51A1AC18887AEA9CEACC60B6F0AD428C899FA2D228D3BEE2032171F754E248CA
```

Raised by `src/aegis_pod/orb_runtime.py:114`, exercised by
`tests/test_orb_runtime_version_gate.py::test_real_orion_contracts_pass_with_matching_version_and_hash`.
Present in both `H:\AEGIS-POD-ARCHITECTURE` and the Initiative. Not caused by the migration.

---

## The four questions

### 1. Which artifact produced the pinned hash?

The pin lives in the Umbilical contract:

```text
H:\AEGIS-POD-ARCHITECTURE\stage-d-out\CP-1004-ORION\pod\provenance\rls-persistent-relations-umbilical.json
```

Last written **2026-07-21 12:50:16**. The companion Orb contract
`rls-persistent-relations-core.orb.json` was written **2026-07-21 14:23:23**.

The Umbilical declares:

```text
orb_version              1.0.0
orb_runtime_hash         B8788191...
working_parameters.status  draft
```

The pin therefore represents the Orb source as it stood on 2026-07-21, during the Step 8 design and
Step 9 attachment work recorded in `reports/runtime/2026-07-21-step-8-*` and `2026-07-21-step-9-*`.

The pinning artifact is **untracked**. `stage-d-out/` is gitignored in the source repository. The
Umbilical has a filesystem mtime and nothing else.

### 2. Which commit or release produced the installed source?

```text
f2419232202270b3ff60781fdf18a6da6e6f4516
2026-08-05 12:04:11 -0700
"RLS bounded selection, compact PCT writeback, and grounded scoring"
```

`git status --porcelain -- packages/orb-rls-persistent-relations-core` reports clean. The installed
source matches its committed state exactly.

Preceding commits touching the package:

```text
ca81326  Apply AEGIS language standards to tracked governing surfaces
1a9ed73  Stage 4: validate_attachment() gates on schema/version/hash, not just paths
32fc75b  Reword force-language ("enforce"/"enforcing") in two docstrings
1b18516  Orb-as-independent-package: SDK, extracted RLS Orb, contract additions
```

### 3. Was the installed source deliberately changed?

Yes. Commit `f241923` on 2026-08-05 is a deliberate, described change to the Orb's selection,
writeback, and scoring behavior. It is not accidental modification and not corruption.

It landed roughly one hour before the migration script ran at 13:20 the same day.

Note that `1a9ed73` — "validate_attachment() gates on schema/version/hash, not just paths" — is the
commit that made this gate capable of detecting the drift at all. The gate did its job.

### 4. Does either artifact have an append-only build, release, or installation record?

| Artifact | Record |
|---|---|
| Installed Orb source | Git history. Tracked, clean, attributable to `f241923`. |
| Umbilical pin | None. Untracked, gitignored, `status: draft`, filesystem mtime only. |

The asymmetry is the finding. The side of the relationship that carries a cryptographic claim
carries no provenance for that claim. The side that carries no claim has a full append-only record.

---

## What this does not decide

The findings above indicate which artifact moved and when. They do not by themselves authorize
re-pinning.

Open before resolution:

1. Whether the 2026-07-21 attachment evidence in `reports/runtime/2026-07-21-step-9-*` was itself
   verified against a hash that any append-only record can reproduce today.
2. Whether `orb_version` stays `1.0.0` across a behavioral change to selection and scoring, or
   whether the version is wrong independently of the hash.
3. Whether the Umbilical's `status: draft` means the pin was ever authoritative, or whether it was
   provisional from the start and the gate is reporting a condition that was always true.
4. Where the Umbilical contract should live such that it acquires an append-only record. It is
   currently gitignored peer-adjacent content with a cryptographic claim inside it — which is the
   same conflation [ADR-0006](../decisions/ADR-0006-manifest-identity-model-coordinate-digest-path-provenance.md)
   names: a digest with no provenance for why it represents what it claims.

Question 4 is the one that generalizes. Answering it likely resolves the other three as a
consequence.
