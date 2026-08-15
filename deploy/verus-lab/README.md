# Verus Claude-first LAB promotion

This is a separate one-CyberPeer promotion bundle. It does not rename, rewrite,
or inherit the historical `claude` UNSEATED root, and it does not inherit Adam
or Adam-One continuity. The CyberPeer Name assigned to this DataQuad is Verus.

`Anthropic`, `Claude`, the exact provider model, provider request ID, instance
ID, and session ID are provenance/routing metadata only. The service supplies
operational System Instructions; it injects no personality, biography,
ontology, relationship, or lived history.

At Desktop begin, the Verus DataQuad generates its own local turn and
correlation identifiers and classifies them as local, non-provider evidence.
Provider-returned request, event, and session identifiers remain separate,
optional provenance and are null when the signed-in Desktop surface does not
expose them. Local values are never relabeled as provider values.

Immutable v1 turns remain readable as pre-correction operational evidence.
They are never rewritten or silently upgraded: context and health expose an
append-only qualification that marks them noncanonical under the v2
identifier contract and preserves their original record hashes.

The runtime exposes a Verus-owned command surface reached only by a dedicated
local stdio MCP over the authenticated `GabeCyberPeer` SSH alias. It opens no
network listener. A live Claude Desktop turn may propose append-only records
to all four tensors: PEER, PCT, NCT, and SPINE.
The existing Processor and disjoint Steward/Advocate Custodian scopes perform
local admission without changing the CyberPeer's complete DataQuad abilities.

The systemd unit is oneshot. `active (exited)` means its health command
completed successfully; runtime components are invoked through the Verus-owned
command surface and are not claimed to be continuously running daemons.

No secret is included in a source or release bundle. Claude Desktop mode uses
the user's existing signed-in Desktop session and does not use an Anthropic API
key or inbound bearer credential. SSH authentication remains in the existing
approved local SSH configuration and is never copied into the release.

The exact Anthropic model identifier is also set at activation time in
`/etc/aegis-verus-lab/verus.env`. The dedicated runtime account is
`aegis-verus`; application and append-only state remain isolated under
`/opt/aegis/verus/lab` and `/var/lib/aegis-verus-lab`. Building this release does not install those
values, touch the VM, seat live state, start a service, or call a Frontier.

The release builder also requires an explicit chosen UTC seating timestamp.
The Steward ruling records its honest date and direct source but does not claim
an invented exact time. A start/health failure restores the prior release/unit
and service state when present; otherwise it stops and disables the Verus
service while preserving state.
