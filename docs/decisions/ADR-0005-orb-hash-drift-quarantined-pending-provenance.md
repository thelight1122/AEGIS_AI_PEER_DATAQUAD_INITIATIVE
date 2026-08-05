# ADR-0005 — `orb-rls-persistent-relations-core` hash drift is quarantined pending provenance

**Status:** Accepted — investigation open
**Date:** 2026-08-05
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `667b41b`

---

## Context

`test_orb_runtime_version_gate.py::test_real_orion_contracts_pass_with_matching_version_and_hash`
fails in both the source repository and the Initiative:

```text
Orb 'orb-rls-persistent-relations-core' runtime_hash mismatch
Umbilical expects   B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18
installed computes  51A1AC18887AEA9CEACC60B6F0AD428C899FA2D228D3BEE2032171F754E248CA
```

It is a pre-existing shortfall carried in from the source repository, not a migration defect.

## Decision

Neither side of the mismatch is accepted. The Umbilical pin is not updated to match the installed
source. The installed Orb is not restored to satisfy the pin.

Until provenance is resolved, the Orb/Umbilical relationship is **DRIFTED** and quarantined from
authoritative formation.

The mismatch is evidence, not a value to normalize away.

## Consequences

- Resolving the drift is a separate provenance investigation. It does not become an undocumented
  part of P0.
- P0 acceptance evidence records this test as a known DRIFTED item with its own investigation
  reference, not as a P0 regression.
- No Orb attachment claiming this Orb/Umbilical pairing proceeds to authoritative formation while
  the status is DRIFTED.

## Investigation

`docs/investigations/2026-08-05-orb-rls-persistent-relations-core-hash-drift.md`

Provenance findings recorded there answer the four questions posed by the Auditor. The findings are
recorded; the resolution is not taken.

## Evidence

- `tests/test_orb_runtime_version_gate.py`
- `src/aegis_pod/orb_runtime.py:114` — the gate that raises
- `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-umbilical.json` (source repository)
