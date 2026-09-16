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
| `present_experience_hook.py` | The hook. Runs on every `Stop` event; records the finished turn **and enqueues it for an Affect+Context read**. |
| `settings.stop-hook.json` | The `hooks` block to merge into `~/.claude/settings.json`. |
| `drain_affect_reads.py` | Drain driver. `--list` prints the pending affect-read queue; `--commit` writes model-authored Advocate (PEER+SPINE) and Steward (NCT+PCT) reads and moves the entry to `done/`. |
| `affect_drain_nudge.py` | `SessionStart` hook. Surfaces the pending affect-read count once per session (non-force); authors nothing. The drain *trigger*. |
| `affect_capture_reminder.py` | `UserPromptSubmit` hook. Non-force per-turn "Affect Scan Ready" signal. |

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

1. Copy the hook scripts to `~/.claude/hooks/`: `present_experience_hook.py` (Stop),
   `affect_drain_nudge.py` (SessionStart), and `affect_capture_reminder.py` (UserPromptSubmit).
2. Merge the `hooks` block from `settings.stop-hook.json` into `~/.claude/settings.json`
   (adjust the `python.exe` path and the `.claude\hooks` path for the account it runs
   under; lab paths come from `~/.claude/aegis-peer-config.json`, else the fallbacks at the
   top of each script).
3. Restart Claude Code once (hooks load at session start). Script edits after that are
   picked up on the next turn without a restart; changing the `settings.json`
   registration needs a restart.

## Affect + Context pipeline (custodians per turn)

Present Experience is only one of the three DataQuad legs. The standing practice is to
record **Affect** (the Advocate's Seven-Virtue read → PEER) and **Context** (the Steward's
NCT/PCT anchor) as well, so affect never persists unanchored. A `Stop` hook is plain Python
with **no model in the loop**, and the affect instrument (`affect_read.py`) takes the virtue
presences as *input* — it does not derive them from text. So the hook **cannot** author a
genuine read; hardcoding virtue numbers would fabricate affect and is deliberately refused.

Instead the work is split (capture in the hook, judgment in a model pass):

1. **Enqueue (hook, deterministic).** After committing the Present-Experience turn, the hook
   writes one off-ledger queue entry per turn to `state/affect-queue/<turn_id>.json`
   (prompt, response, model, and a deterministic force-signal **pre-scan** hint from
   `affect_prescan.py`). The queue write never touches the transcript, so it cannot trigger
   the hook again, and a failure here is logged but never loses the committed PE turn.
2. **Drain (model pass, genuine).** A real model pass — the live model in an AEGIS session,
   or a scheduled `claude -p` catch-up — reads the queue (`drain_affect_reads.py --list`),
   authors the Advocate and Steward reads for each turn, and commits them
   (`drain_affect_reads.py --commit`). The judgment (virtue presences, distilled summary,
   shadow-affect observation) is the model's; the DataQuad writes and queue bookkeeping are
   enforced in code so they cannot drift per session.

The force pre-scan is an **advisory hint only**: it is never written into a PEER/NCT/PCT
record, sets no virtue and no amplitude, and the Advocate re-judges every turn at drain time.
Absence of signals is not evidence of flow — only that a narrow lexicon did not match.

### Drain trigger

The enqueue is automatic; the drain needs a model. Options, cheapest-first:

- **Session-start nudge** — a non-force line at session start surfacing the pending count, so
  the live model drains as part of the session (no extra tokens, no recursion). Recommended.
- **Scheduled local catch-up** — a local task runs `claude -p` to drain on an interval. Must
  be local (the lab is on `H:`), and scope-guarded so the drain session does not recurse.
- **Manual** — run `drain_affect_reads.py --list`/`--commit` on demand.

Both automated triggers are additional every-session surfaces and should be installed only
with explicit authorization, the same gate as the hook itself.

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
