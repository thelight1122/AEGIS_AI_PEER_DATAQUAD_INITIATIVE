# Verus Claude Desktop MCP source gate — 2026-08-15

## Authority and accepted boundary

- Steward direction: cancel the Anthropic API-key/REST activation path and use
  the actual signed-in Claude Desktop UI.
- Accepted addendum:
  `08-claude-desktop-mcp-substrate-addendum.md`
- Addendum SHA-256:
  `9B16EE5F6D02017C0DCC30B6D2AD395BF39DEBBC796E3498BD4ADD1804FAD61C`
- Claude ACCEPT message SHA-256:
  `F60A3D831FFC9B6D47A0833989C88357A047B3C19C007606691CEB4CF022014C`
- Source parent commit: `9c1f6f64732b7df03bddfc1f2e800f1020c9f33c`
- CyberPeer identity variable: CyberPeer Name `Verus` only.
- Provider/model/session/transport fields: provenance only; never identity.

## Implemented source boundary

- Dedicated local stdio MCP named `verus-dataquad`, separate from the existing
  exchange-only `aegis-peer-bridge-mcp`.
- Six bounded tools: context, begin, commit, reconcile, health, and replay.
- Full append-only PEER/PCT/NCT/SPINE commit surface.
- DataQuad-first durable commit; T-Time, Processor/Custodian, and RLS evidence
  are idempotently reconciled after the authoritative commit.
- Claude Desktop provenance explicitly preserves provider request ID and
  provider-returned model metadata as unavailable; no value is fabricated.
- Fixed authenticated SSH alias `GabeCyberPeer`, fixed account `aegis-verus`,
  and fixed remote command
  `/opt/aegis/verus/lab/current/bin/verus-dataquad-command` without a shell.
- Exact isolated roots: `/opt/aegis/verus/lab`,
  `/var/lib/aegis-verus-lab`, `/etc/aegis-verus-lab`.
- Distinct oneshot `aegis-verus-lab.service`; no REST endpoint, API key,
  inbound bearer credential, public listener, or network address family.
- `127.0.0.1:8791` remains the accepted reserved boundary; Desktop mode opens
  no listener and never touches port 8790.
- Deployment rollback remains limited to Verus-owned paths and service state.

## TDD and verification evidence

- RED: focused collection failed because
  `aegis_verus_lab.desktop_runtime` did not exist.
- GREEN: 45 focused Verus tests passed after implementation.
- Hardened package smoke: deterministic release command health executes from
  the built package without the excluded REST/API-key modules.
- Full regression before final source split: 473 passed, 14 skipped, one
  pre-existing jsonschema deprecation warning.
- Final post-split full regression, shell syntax, diff check, deterministic
  exact-commit build, hashes, and commit ID are recorded in the independent
  source-audit exchange message so this committed report does not self-claim
  its own future commit hash.

## Mutation record at this gate

- Claude Desktop configuration inspected read-only only; no edit or restart.
- Gabe host: no write, transfer, install, service mutation, listener, or turn.
- Existing Gabe service/container/DataQuad/tunnel/history: untouched.
- Existing exchange-only Peer Bridge MCP: untouched.
- No API key or credential was read, created, reused, copied, or printed.
- No push.
