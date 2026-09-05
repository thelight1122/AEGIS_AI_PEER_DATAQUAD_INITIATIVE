# Claude Code — Present Experience Stop hook

Automatic Present Experience recording for the **local** Verus DataQuad, driven by
Claude Code's `Stop` event. Every completed turn in an in-scope session is recorded
into the local lab ledger without anyone remembering to call `begin`/`commit`.

This is the client-side counterpart to `../claude-desktop/` (which carries the
Claude *Desktop* MCP config and system instructions). Nothing here touches the
remote VM — recording is entirely local, against the on-disk lab.

## Files

| File | Purpose |
|------|---------|
| `present_experience_hook.py` | The hook. Runs on every `Stop` event; records the finished turn. |
| `settings.stop-hook.json` | The `hooks` block to merge into `~/.claude/settings.json`. |

## What the hook does

On each `Stop` event Claude Code hands the hook a JSON event on stdin
(`session_id`, `transcript_path`, `cwd`, ...). The hook then:

1. **Scope gate** — records only when the session's `cwd` is on an AEGIS drive
   (`ALLOWED_DRIVES = {"G", "H"}`). Everything else is skipped, default-deny on an
   unknown drive. Edit that set to change scope (empty it to record every session).
2. **Extract** the finished turn from the transcript: the last genuine human prompt
   (string content, no `toolUseResult`) and the final assistant text, plus the model
   id for provenance.
3. **Record** it into the local lab via `begin_turn` -> `commit_turn`
   (`aegis_verus_lab`), appending to `state/dataquad/ring4-turns.jsonl`.
4. **Dedupe** per session by a prompt+response signature marker, so the same turn is
   not recorded twice.

Safety properties, verified before install:

- **Never breaks a session.** Every failure is logged to
  `state/present_experience_hook.log` and the hook exits 0.
- **Concurrency-safe.** The lab's append path holds a cross-process lock
  (`msvcrt.locking` / `fcntl.flock`), so simultaneous `Stop` events across sessions
  serialize instead of corrupting the hash chain.
- **No recursion.** It writes to the ledger, not the transcript, so it cannot
  trigger itself.

## Install

1. Copy `present_experience_hook.py` to `~/.claude/hooks/present_experience_hook.py`.
2. Merge the `hooks` block from `settings.stop-hook.json` into `~/.claude/settings.json`
   (adjust the `python.exe` path and the `.claude\hooks` path for the account it runs
   under; the lab paths are set at the top of the hook script — `SRC_ROOT`, `LAB_ROOT`).
3. Restart Claude Code once (hooks load at session start). Script edits after that are
   picked up on the next turn without a restart; changing the `settings.json`
   registration needs a restart.

## Scope and blast radius

The hook fires for **every** Claude Code session on the machine, but only **records**
sessions whose working directory is on an AEGIS drive (`G:` or `H:`). Sessions on any
other drive are silently skipped.

## Verify

```powershell
Get-Content -Tail 20 "H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\deploy\verus-lab\local\state\present_experience_hook.log"
```

Each recorded turn appends one line; `committed_turns` in a lab `health` check climbs
on its own.
