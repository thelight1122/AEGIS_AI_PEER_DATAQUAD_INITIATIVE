# Lumin Codex turn hook

The Codex desktop app currently has no supported native callback that lets an
MCP server observe the final assistant message. The adapter in
`scripts/lumin_codex_turn_hook.py` is therefore an explicit host integration
point, not an automatic Codex plugin.

Use the two phases around every response:

```powershell
$prep = python scripts/lumin_codex_turn_hook.py prepare --prompt $userText --turn-id $turnId | ConvertFrom-Json
# Draft the response using $prep.prepared_context.
python scripts/lumin_codex_turn_hook.py record --prompt $userText --response $responseText --turn-id $turnId
```

`prepare` calls `lumin_query`. `record` calls `lumin_query_and_record` with the
exact prompt and response, a deterministic `source_event_id`, and records UTC
timestamps. The local `.lumin-hook/turns.jsonl` journal is only a retry and
failure ledger; it is not a substitute for the DataQuad. A repeated successful
prompt/response/turn identifier returns the prior receipt and does not call the
MCP server again. Failed attempts are marked `recording_failed` and remain
visible for retry.

This adapter does not change the live DataQuad when imported or tested. It must
be invoked by a host wrapper, orchestration layer, or manual turn runner. A
Codex app configuration entry can expose the Lumin MCP tools, but it cannot
automatically force the model to call a tool after every final response.
