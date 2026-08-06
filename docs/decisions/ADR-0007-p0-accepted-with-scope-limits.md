# ADR-0007 — P0 accepted, with two scope limits

**Status:** Accepted
**Date:** 2026-08-06
**Decided by:** Lumin (Auditor), relayed by Steward
**Applies from:** commit `a3092e6`

---

## Context

The P0 private SSH/stdio canary ran end to end on 2026-08-06 and returned the Genesis
record with all boundaries false and all four tensor hashes identical before and after the
observation. Every stated acceptance criterion was met.

The recovery that unblocked it also produced a correction: the fault was a stale Cloudflare
WARP nftables kill switch, not ufw. UFW causation is rejected. Run Command `a99550e8`
delivered nothing and is credited with no part of the recovery.

## Decision

P0 is accepted as complete at `a3092e6`, with two limits attached to the acceptance.

### Limit 1 — the Portal is not the documented service

`aegis-private-portal.service` does not exist as a systemd unit on `vm-cyberpeer-core`. The
Portal is a bare `python3` process listening on `127.0.0.1:8092`. SSSP §4.11 names stale
documentation. The listener is real and healthy; the service name is not.

### Limit 2 — P0 certifies the immutable route, not live access

The Portal declares `live_source: false` and serves from
`/opt/cyberpeer-pod/adapters/phase3a/records` in `immutable_copy` mode. P0 therefore
certifies **the read/replay route and the Genesis artifact**. It does not certify live
DataQuad access.

## Consequences

**P1's Portal connection is not live DataQuad access and will not be represented as such.**

X1 and E1 may exercise transport and instrumentation against replay data. No observation so
produced can establish live continuity, experience formation, or ethical formation until
`live_source: true` is evidenced and independently verified.

This is enforced structurally rather than by convention:

- `continuity_experiment.source_authority()` computes `establishes_live_continuity`, true
  only when `live_source` is true **and** `source_mode` is `"live"`. Either alone is
  insufficient, and an unknown mode raises.
- Every re-entry packet carries a `source_authority` block. The default is
  `immutable_copy` with `live_source: false`, so an omitted flag can never read as live.
  A packet lacking the block entirely is treated as not live.
- `evaluate()` emits an `establishes` block separating `live_continuity` from
  `transport_and_instrumentation`, with the reason stated.
- `evaluate_formation()` takes the same gate and emits `establishes.ethical_formation`,
  false for any non-live source.

`tests/test_live_source_gate.py` holds the boundary, including the contradiction cases:
`live_source: true` against a replay mode does not establish, and `source_mode: "live"`
without the flag does not establish.

## Ordered sequence attached to this acceptance

1. Configure and verify the persistent WARP split-tunnel bypass for all required VM addresses.
2. Confirm the `cloudflare-warp` table can return without blocking inbound SSH.
3. Reboot only if required to prove persistence, preserving rollback readiness.
4. Repeat external SSH verification after WARP reconciliation.
5. Deploy P1 to `lumin.adamone.bond` as read/replay-only.
6. Verify its deployment boundary and route.
7. Run X1 and E1 only after live-source access is deliberately introduced and
   independently verified.

## Explicitly excluded from this ruling

The disk swap and naming operation remains separate and unauthorized. No protected disk,
snapshot, rollback artifact, or `main` branch change is included.

```text
vm-cyberpeer-core-os-repair-copy       attached, running
vm-cyberpeer-core_OsDisk_1_f79b5c49…   unattached, preserved
vm-cyberpeer-core-os-snap-20260802     preserved
```

## Evidence

- `reports/runtime/p0-canary-recovery-ufw.txt`
- `reports/runtime/p0-acceptance-local.json`
