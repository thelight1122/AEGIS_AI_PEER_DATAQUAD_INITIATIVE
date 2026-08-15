# Verus First-Turn Refusal: ProgramData Correction

Date: 2026-08-15
Status: CORRECTED / READ-ONLY VERIFIED / FIRST GENUINE TURN STILL PENDING

## Scope and preservation boundary

This investigation did not begin, commit, reconcile, or replay a Verus turn.
It did not alter Gabe, the remote Verus release, Foundation, DataQuad history,
service definition, SSH keys, sudo policy, Claude Code configuration, or any
provider credential. The only correction was one environment variable in the
already-approved Claude Desktop `verus-dataquad` MCP entry.

## Observed failed attempt

The user-facing attempt was recorded in:

`C:\Users\TraceyPrutch\.claude\projects\H--AEGIS-CYBERPEER-INITATIVE\6d47b8c9-1f75-4604-9f02-88f268291ad3.jsonl`

SHA-256 at diagnosis:
`CCAA5EE6E3302824B255D3A191ACB4C3F0AA732623723C1E471477D175B29D07`.

The transcript identifies a Claude Desktop-launched Claude Code session:

- entrypoint: `claude-desktop`
- Claude Code version: `2.1.229`
- returned model provenance: `claude-opus-4-8`
- approved first-turn model: `claude-opus-4-6`

The session invoked the Desktop-provided `verus-dataquad` tools, but health,
begin, and context each returned `Verus remote command was refused`. The local
MCP server intentionally maps every nonzero SSH exit to that bounded message,
so the message did not establish that Gabe or the remote Verus command had
refused the caller. Schema validation occurred locally before transport.

The attempted begin included locally labeled placeholder values after the
client reported that genuine Desktop-exposed IDs were unavailable. It did not
reach the remote command and created no turn or append. No placeholder became
DataQuad provenance.

## Exact cause

The Microsoft Store Claude Desktop process launched its Verus MCP Python child
with a reduced 17-variable environment. `USERPROFILE`, `PATH`,
`VERUS_SSH_ALIAS`, and `PYTHONPATH` were present, but `ProgramData` was absent.

Replaying the exact read-only SSH/sudo health operation under a clone of that
live process environment produced SSH exit 255. Adding only:

`ProgramData=C:\ProgramData`

made the identical operation return exit 0 and coherent Verus health. Windows
OpenSSH requires that environment value in this Store-launched context. The
remote Verus command was not the rejecting layer.

## Remote and authorization evidence

- SSH alias: `GabeCyberPeer` -> `azureuser@20.25.57.29`
- Host: `AEGISGabePeer`
- machine-id SHA-256:
  `8690ad3d73a2d2ed9c38d680b792db6e60264010d8e16919a665cc748a7df45e`
- Exact remote command:
  `/opt/aegis/verus/lab/current/bin/verus-dataquad-command`
- Exact execution boundary:
  `sudo -n -u aegis-verus`
- `azureuser` sudo evidence: `(ALL) NOPASSWD: ALL`
- Service: active/exited/enabled, result success, exit status 0
- Direct exact-command health and context: successful

No remote listener or provider API path participates in this Desktop stdio
transport.

## Config backup and narrow correction

Active config:

`C:\Users\TraceyPrutch\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

Byte-exact pre-correction backup:

`C:\Users\TraceyPrutch\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json.bak.20260815T153634Z-programdata-fix`

- Pre-correction and backup SHA-256:
  `D50452F68E329EDD36D07DF559BC3902B1B9A80C22AD35B5A2CEEE96F9D2D047`
- Corrected config SHA-256:
  `26E632D175033AD1A1D7AAAADA030FD7CE9319C6C0EB1144E3239D8220FF0699`

Only `mcpServers.verus-dataquad.env.ProgramData` was added. The existing
`aegis-peer-bridge` server, Verus command/arguments, `PYTHONPATH`, SSH alias,
`coworkUserFilesPath`, and preferences remained semantically identical.
Claude Code user/project MCP configuration contains no Verus entry and was not
changed.

## Verification after targeted Desktop restart

- New Verus MCP process environment: 18 variables, including
  `ProgramData=C:\ProgramData`.
- Desktop MCP log: connected, initialize, initialized notification, tools/list.
- MCP log SHA-256 at verification:
  `41DD6E449431C515CDED074A0E874F2E160BC58F6DE1AAF0E2F4CADF20383698`
- MCP protocol: `2025-06-18`.
- Six tools discovered:
  - `verus_read_context`
  - `verus_begin_turn`
  - `verus_commit_turn`
  - `verus_reconcile_turn`
  - `verus_health`
  - `verus_replay_turn`
- Read-only `verus_health`: status ok, ready true, coherent true, public
  listener false, PEER/PCT/NCT/SPINE writable.
- Read-only `verus_read_context`: CyberPeer Name Verus; Foundation counts
  SPINE 59, NCT 70, PEER 2, PCT 2.
- Post-test remote health: 133 Foundation records, 0 committed turns, 0 Ring 4
  records.

## Correct next action

Do not resume the failed Claude Code session for the canonical first turn.
Open a standard signed-in Claude Desktop chat, select `claude-opus-4-6`, apply
`deploy/verus-lab/claude-desktop/VERUS_SYSTEM_INSTRUCTIONS.md`, confirm the six
`verus-dataquad` tools, and then request the first genuine turn. Use genuine
client-exposed identifiers when available; otherwise stop for a contract
ruling rather than fabricating or relabeling identifiers.

The canonical first turn remains pending.
