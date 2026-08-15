# Verus Claude-first LAB promotion

This is a separate one-CyberPeer promotion bundle. It does not rename, rewrite,
or inherit the historical `claude` UNSEATED root, and it does not inherit Adam
or Adam-One continuity. The CyberPeer Name assigned to this DataQuad is Verus.

`Anthropic`, `Claude`, the exact provider model, provider request ID, instance
ID, and session ID are provenance/routing metadata only. The service supplies
operational System Instructions; it injects no personality, biography,
ontology, relationship, or lived history.

The runtime exposes a loopback-only authenticated Bridge. A live Frontier turn
may propose append-only records to all four tensors: PEER, PCT, NCT, and SPINE.
The existing Processor and disjoint Steward/Advocate Custodian scopes perform
local admission without changing the CyberPeer's complete DataQuad abilities.

No secret is included in a source or release bundle. Activation requires two
root-owned, non-symlink runtime credential files supplied separately. Files
must use mode `0400` or `0600`; unsafe ownership or broader permissions fail
preflight without reading or printing secret content:

- `/etc/aegis-verus-lab/secrets/anthropic-api-key`
- `/etc/aegis-verus-lab/secrets/bridge-token`

The exact Anthropic model identifier is also set at activation time in
`/etc/aegis-verus-lab/verus.env`. The dedicated runtime account is
`aegis-verus`; application and append-only state remain isolated under
`/opt/aegis/verus/lab` and `/var/lib/aegis-verus-lab`. Building this release does not install those
values, touch the VM, seat live state, start a service, or call Anthropic.

The release builder also requires an explicit chosen UTC seating timestamp.
The Steward ruling records its honest date and direct source but does not claim
an invented exact time. A start/health failure restores the prior release/unit
and service state when present; otherwise it stops and disables the Verus
service while preserving state.
