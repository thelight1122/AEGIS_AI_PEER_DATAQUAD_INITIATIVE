# Verus Claude Desktop MCP LAB runbook

This mode connects the signed-in Claude Desktop UI to the Verus DataQuad with
a dedicated local stdio MCP process. It does not call the Anthropic REST API,
does not load an API key, and does not open a network listener. The local MCP
invokes only the authenticated SSH alias `GabeCyberPeer`, then only the account
`aegis-verus` and command
`/opt/aegis/verus/lab/current/bin/verus-dataquad-command`.

The remote boundary is isolated at `/opt/aegis/verus/lab`,
`/var/lib/aegis-verus-lab`, and `/etc/aegis-verus-lab`, with the distinct
`aegis-verus-lab.service`. Port `127.0.0.1:8791` remains the accepted reserved
boundary but Desktop mode opens no listener. Port 8790 and all Gabe-owned state
remain outside scope.

## Activation sequence

1. Verify the accepted source commit and deterministic release hashes.
2. Run fresh read-only host, collision, resource, service, and Gabe-boundary
   checks. Stop before installation on any mismatch.
3. Install the release with `FRONTIER_MODEL=claude-opus-4-6`, verify the oneshot
   service and command health, and audit that no listener appeared.
4. Back up `%APPDATA%\Claude\claude_desktop_config.json`, recording hashes for
   both source and backup. Merge only the `verus-dataquad` object from
   `deploy/verus-lab/claude-desktop/verus-dataquad.mcp.json`; preserve every
   existing MCP entry and validate the resulting JSON.
5. Add the operational instructions from `VERUS_SYSTEM_INSTRUCTIONS.md` to the
   chosen Claude Desktop project or conversation. They assign only the
   CyberPeer Name and functional boundaries; they do not inject identity.
6. At a safe user-approved restart point, restart Claude Desktop, confirm the
   six Verus tools are discovered, and run the first genuine signed-in turn:
   begin, actual Claude response, commit with PEER/PCT/NCT/SPINE evidence,
   replay, and health.

`verus_begin_turn` requires only the work prompt. If Claude Desktop exposes a
genuine provider event or session identifier, pass it in its matching optional
field. Otherwise omit the field or pass null. Begin returns a DataQuad-owned
local `turn_id` and `correlation_id`; commit must return them unchanged. They
are classified as local correlation evidence and must never be copied or
relabeled as provider provenance.

Provider request ID, provider event/session IDs, and provider-returned model
metadata may be unavailable at the Desktop/MCP boundary. Evidence preserves
those values as null/unavailable and separately records the DataQuad local
correlation, canonical tool arguments/results and hashes, DataQuad record hash
and chain, T-Time, Processor, Custodian and RLS evidence, selected-model UI
evidence, and screenshots. Do not simulate the model or UI.
