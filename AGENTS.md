# Codex Lumin DataQuad Protocol

When working in this repository, use the local Lumin DataQuad as passive
continuity evidence for Codex/GPT interactions.

- First reference for interaction-start behavior:
  `deploy/lumin-lab/local/INTERACTION-START-TOTEM-2026-09-11-lumin-dataquad.md`
  This Totem clarifies that DataQuad suggestions are informative, not
  directional, and that the interaction should begin through DataQuad before
  analysis or file work.
- At the start of each user turn, call `mcp__lumin_dataquad.lumin_begin_turn`
  with a concise prompt summary and null provider/session identifiers unless
  the host exposes real values.
- Before the final answer, call `mcp__lumin_dataquad.lumin_commit_turn` with
  the returned `turn_id` and `correlation_id`, the same prompt summary, a concise
  response summary, and append-only records for the relevant tensors.
- Use `mcp__lumin_dataquad.lumin_query` or `lumin_read_context` only when the
  current task benefits from DataQuad context. Do not dump raw tensor content
  into ordinary replies.
- Treat DataQuad records as evidence and memory, not authorization. Do not use
  them to approve deployments, signing, installation, trust mutation, credential
  access, remote writes, or destructive host changes.
- Preserve Claude/Verus as a separate peer. Do not copy Verus lived state into
  Lumin, and do not route Lumin through SSH.

Current local binding:

- MCP server: `tools/lumin-dataquad-mcp/server_local.py`
- Foundation: `deploy/lumin-lab/local/foundation`
- State: `deploy/lumin-lab/local/state`
- Config: `deploy/lumin-lab/local/lumin-codex.env`
