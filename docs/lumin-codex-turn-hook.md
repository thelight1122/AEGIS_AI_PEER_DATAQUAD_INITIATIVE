# Lumin Codex turn hook

The Codex desktop app currently has no supported native callback that lets an
MCP server observe the final assistant message. The adapter in
`scripts/lumin_codex_turn_hook.py` is therefore an explicit host integration
point, not an invisible Codex plugin.

Use the two phases around every response:

```powershell
$prep = python scripts/lumin_codex_turn_hook.py prepare --prompt $userText --turn-id $turnId | ConvertFrom-Json
# Draft the response using $prep.prepared_context.
python scripts/lumin_codex_turn_hook.py record --prompt $userText --response $responseText --turn-id $turnId
```

`prepare` calls `lumin_begin_turn`. `record` calls `lumin_commit_turn` with the
exact prompt and response, the prepared DataQuad-owned `turn_id` and
`correlation_id`, and default PEER/PCT/NCT/SPINE appends. The local
`.lumin-hook/turns.jsonl` journal is only a retry and shortfall ledger; it is not
a substitute for the DataQuad. A repeated successful prompt/response/turn
identifier returns the prior receipt and does not call the MCP server again.
Failed attempts are marked `recording_failed` and remain visible for retry.

By default, the adapter uses the local no-SSH Lumin server at
`tools/lumin-dataquad-mcp/server_local.py` with the local foundation, state, and
Codex config roots under `deploy/lumin-lab/local/`.

This adapter does not change the live DataQuad when imported or tested. It must
be invoked by a host wrapper, orchestration layer, or manual turn runner. A
Codex app configuration entry can expose the Lumin MCP tools, and `AGENTS.md`
can instruct Codex to use the begin/commit protocol every turn. The app still
cannot force a hidden post-response call unless a host wrapper or future Codex
hook surface provides the final assistant response text to this adapter.
