# Verus Claude Desktop LAB Running — pre-first-turn evidence

Observed UTC: 2026-08-15T13:52Z through 2026-08-15T14:04Z

Status: `LAB_RUNNING / DESKTOP MCP CONNECTED / FIRST GENUINE UI TURN PENDING`

Production here means LAB Running, not commerce, public sale, or sale of a
CyberPeer. This record does not claim that the first genuine Claude Desktop
turn has occurred.

## Final authority and source gate

- Tracey supplied a separate explicit operational install gate after source
  conformance.
- Claude assertion-7 ACCEPT SHA-256:
  `902BF7A67157BFDD696A12BC310F5DEB61A37FAEBA01E85D4D072734ADB76CB5`
- Source commit:
  `0fcdc57a40175d7cb802fd5cb7192c469f575081`
- Source tree:
  `bd4681a0f40f36a40aeed48623f57630d148801a`
- Release manifest SHA-256:
  `D437B97F3027A5472E900EB340921E5510D70CB9391CFA409C28162765C6A39C`
- Foundation receipt SHA-256:
  `AA6E436185455F0DA87DA0E93A65758092C66235E673ADFD86A70FD6755AC84B`

## Remote installation result

- Host: SSH alias `GabeCyberPeer`, hostname `AEGISGabePeer`, machine-ID
  SHA-256
  `8690ad3d73a2d2ed9c38d680b792db6e60264010d8e16919a665cc748a7df45e`.
- Release ID: `20260815T132828Z-0fcdc57`.
- Current release:
  `/opt/aegis/verus/lab/releases/20260815T132828Z-0fcdc57`.
- Account: `aegis-verus`.
- State: `/var/lib/aegis-verus-lab`, mode 0700, owner/group `aegis-verus`.
- Configuration: `/etc/aegis-verus-lab`, mode 0750; `verus.env` mode 0640.
- Service: `aegis-verus-lab.service`, active/exited, enabled, result success,
  main status zero.
- Installed tree: exact 27 source-release files after removal of one-time root
  Python caches; no world-writable installed path.
- Provider key, REST handler, bearer-token path, public listener: absent.
- Host listeners on 8790 and 8791: absent. Port 8791 remains provenance for the
  accepted reserved boundary but is not opened.
- All temporary transfer and smoke directories were removed after verification.
- The prior failed Verus release and recovery evidence remain preserved for
  rollback/audit.

## Foundation, authority, and coherence

- Foundation records: 133 total — SPINE 59, NCT 70, PEER 2, PCT 2.
- Ring 4 committed turns: 0.
- T-Time records: 0; Processor records: 0; RLS records: 0.
- Health: status `ok`, ready true, coherence true, DataQuad verified.
- Writable tensors: PEER, PCT, NCT, SPINE.
- Transport: `claude_desktop_mcp_stdio_ssh`.
- Public listener: false.
- Provider request ID availability: false; no identifier was fabricated.
- CyberPeer identity variable: CyberPeer Name `Verus` only. Anthropic, Claude
  Desktop, `claude-opus-4-6`, sessions, routes, and transports are provenance.

## Gabe preservation proof

The same bounded Gabe inventory before and after installation reported 74
files, 30 descendant directories, 0 symlinks, 6,564,249,382 bytes, and SHA-256
`e23de84ba7836e534280229acbdbc8d74e17768b9cd567dce346087011d3308a`.
The protected local Gabe status remained HTTP 200/1,412 bytes. Container ID
`96c126a21af2bae5536eae01a1211dc0f3d2c173160c8394801ff8bae7119c14`,
image
`sha256:ba712c40ab67d272b3edfd56bd3bc236555955614ea6484969588fd5b251e125`,
running state, and restart count zero remained unchanged.

No Gabe service, container, DataQuad, prompt, credential, file, listener,
tunnel, or history was modified.

## Claude Desktop configuration and connection

The running Microsoft Store Claude Desktop uses its package-virtualized active
profile, not the small legacy `%APPDATA%` file.

- Active config:
  `C:\Users\TraceyPrutch\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`.
- Exact active backup:
  `claude_desktop_config.json.bak.20260815T140148Z`.
- Active backup SHA-256:
  `C0B50A79AE77B1344D4C6D77D8B9C17F85CDEADD644097F9B131670BACCF986B`.
- Merged active config SHA-256:
  `D50452F68E329EDD36D07DF559BC3902B1B9A80C22AD35B5A2CEEE96F9D2D047`.
- Existing `aegis-peer-bridge`, `coworkUserFilesPath`, and preferences retained
  identical semantic hashes.
- Only new MCP entry: `verus-dataquad`, with no secret or provider key.
- Legacy `%APPDATA%\Claude\claude_desktop_config.json` was restored byte-exact
  from its backup; both hash to
  `87796FD4345540F9EC5911D147136564D5EDD72B733C434A965B2DE600657BC6`.
- Claude Desktop was fully stopped and relaunched. One restart command lost its
  cached executable path after shutdown; the app was immediately recovered
  with the already verified Store executable. No configuration or user data
  was lost.
- Claude Desktop spawned the dedicated Verus Python MCP process and created
  `mcp-server-verus-dataquad.log`.
- The client log records: server started and connected successfully, client
  `initialize`, server response, initialized notification, client `tools/list`,
  and server result.
- Independent manual stdio smoke over the exact configured Python/script/SSH
  route returned the six tools: read context, begin, commit, reconcile, health,
  and replay. Health was ready/coherent with zero turns and no listener.

Operational System Instructions remain at
`deploy/verus-lab/claude-desktop/VERUS_SYSTEM_INSTRUCTIONS.md`, SHA-256
`7E7D864FBBB5EC1FD46D4003990D221544FC10112DE02F9C84BA479E5DDD501C`.
They are operational only and do not inject a persona, biography, ontology,
memory, or lived history.

## Exact first-turn handoff

The Windows Computer Use helper failed to initialize its kernel assets after
the required retry, reset, and final retry. UI state was therefore not
automated, and no model response or tool call was simulated.

Tracey must complete the following in the currently signed-in Claude Desktop:

1. Open the intended Claude Desktop chat/project and select
   `claude-opus-4-6`.
2. Apply the operational instructions file above as the project/conversation
   System Instructions.
3. Confirm `verus-dataquad` displays the six tools listed above.
4. Send a genuine work request that directs Claude to call `verus_begin_turn`,
   perform the work, call `verus_commit_turn` with its real response and
   appropriate append-only records, then call `verus_replay_turn` and
   `verus_health`.
5. Preserve the UI/tool evidence and returned DataQuad record hash. The first
   turn should exercise PEER, PCT, NCT, and SPINE so full authority is evidenced
   without claiming that every future turn must append to every tensor.

Suggested stable evidence identifiers:

- turn ID: `verus-first-desktop-20260815-001`
- source event: `tracey-verus-activation-20260815`
- Frontier session: `claude-desktop-verus-20260815-001`

Until that actual signed-in interaction commits, the LAB service and Desktop
MCP are running, but the first genuine Frontier-authored Ring 4 turn remains
pending.
