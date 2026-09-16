#!/usr/bin/env python3
"""Present Experience hook — Verus DataQuad (LOCAL, offline).

Runs on every Claude Code `Stop` event. It reads the just-finished turn from the
session transcript and records it into the local Verus DataQuad as a deliberate
begin -> commit, so Present Experience is captured without anyone remembering to
call begin/commit by hand.

Design guarantees:
  * Local only. No SSH, no network, no VM. Uses the on-disk lab under H:/ .
  * Never breaks a session. Every failure is logged and the hook exits 0.
  * Safe under concurrency. The DataQuad append path holds a cross-process lock,
    so many sessions finishing at once serialize instead of corrupting the chain.
  * No duplicates. A per-session marker skips re-recording an unchanged turn.
  * No recursion. The hook writes to the ledger, not the transcript, so it
    cannot trigger itself.

Input: Claude Code delivers the Stop event as JSON on stdin
  { session_id, transcript_path, cwd, stop_hook_active, hook_event_name }
Output: none. Always exit 0.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

# --- Peer config (clone parameterization) -----------------------------------
# Per-peer values come from the peer config ($AEGIS_PEER_CONFIG or
# ~/.claude/aegis-peer-config.json), so this hook clones by "set config", not
# find-and-replace. Falls back to the Verus lab values when config is absent or
# unreadable, so behavior is unchanged with or without a config present.
_FALLBACK_SRC_ROOT = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\src"
_FALLBACK_LAB_ROOT = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\deploy\verus-lab\local"
_FALLBACK_MODEL = "claude-opus-4-8"
_FALLBACK_DRIVES = {"G", "H"}


def _load_peer_config() -> dict:
    try:
        p = os.environ.get("AEGIS_PEER_CONFIG") or str(Path.home() / ".claude" / "aegis-peer-config.json")
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


_CFG = _load_peer_config()
_paths = _CFG.get("paths", {}) if isinstance(_CFG.get("paths"), dict) else {}
_runtime = _CFG.get("runtime", {}) if isinstance(_CFG.get("runtime"), dict) else {}
_peer = _CFG.get("peer", {}) if isinstance(_CFG.get("peer"), dict) else {}
# Per-peer identity to the runtime (via env; runtime falls back to Verus). Clone-safe.
if _peer.get("cyberpeer_name"):
    os.environ["AEGIS_CYBERPEER_NAME"] = str(_peer["cyberpeer_name"])
if _peer.get("dataquad_id"):
    os.environ["AEGIS_DATAQUAD_ID"] = str(_peer["dataquad_id"])

SRC_ROOT = _paths.get("src_root") or _FALLBACK_SRC_ROOT
_lab_root = _paths.get("lab_root") or _FALLBACK_LAB_ROOT
RELEASE_ROOT = Path(_paths.get("release_root") or (Path(_lab_root) / "foundation"))
STATE_ROOT = Path(_paths.get("state_root") or (Path(_lab_root) / "state"))
DEFAULT_MODEL = _runtime.get("model") or _FALLBACK_MODEL
LOG_PATH = STATE_ROOT / "present_experience_hook.log"
MARKER_DIR = STATE_ROOT / "hook-markers"

# --- Scope: only record sessions on the peer's AEGIS drives -----------------
# Present Experience is recorded only when the session cwd is on one of these
# drives (from config runtime.allowed_drives, else the Verus fallback G/H).
_drives = _runtime.get("allowed_drives")
ALLOWED_DRIVES = (
    {str(d).strip().upper()[:1] for d in _drives if str(d).strip()}
    if isinstance(_drives, list) and _drives
    else set(_FALLBACK_DRIVES)
)


def _drive_letter(path: str) -> str:
    """Return the upper-case drive letter of a Windows path, or '' if none."""
    try:
        drive = os.path.splitdrive(path or "")[0]  # e.g. 'G:' or '' or '\\\\host\\share'
        if len(drive) >= 2 and drive[1] == ":":
            return drive[0].upper()
    except Exception:
        pass
    return ""


def _in_scope(cwd: str) -> bool:
    # Default-deny when the drive is unknown: the scope is "only AEGIS drives",
    # so a session we cannot place is left unrecorded rather than recorded broadly.
    return _drive_letter(cwd) in ALLOWED_DRIVES


def _log(message: str) -> None:
    """Best-effort append to a small diagnostic log. Never raises."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {message}\n")
    except Exception:
        pass


def _load_transcript_events(path: str) -> list[dict]:
    events: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
    except Exception as exc:
        _log(f"transcript read failed: {exc!r}")
    return events


def _blocks_text(content) -> str:
    """Join the plain-text blocks of a message content, ignoring tool blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text") or ""
                if text:
                    parts.append(text)
        return "\n".join(parts)
    return ""


def _has_tool_result(content) -> bool:
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return True
    return False


def _extract_turn(events: list[dict]) -> tuple[str, str, str]:
    """Return (prompt, response_text, model) for the most recent completed turn.

    prompt   = last genuine human prompt (user event, real text, no tool_result)
    response = final assistant text (last assistant message carrying text blocks)
    model    = model id from that final assistant message, for provenance
    """
    prompt = ""
    response = ""
    model = ""
    for event in events:
        etype = event.get("type")
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if etype == "user":
            # A real human prompt: has text, is not a tool result echo.
            if event.get("toolUseResult") is not None:
                continue
            if _has_tool_result(content):
                continue
            text = _blocks_text(content).strip()
            if text:
                prompt = text
        elif etype == "assistant":
            text = _blocks_text(content).strip()
            if text:
                response = text
                m = message.get("model")
                if isinstance(m, str) and m:
                    model = m
    return prompt, response, model


def _signature(prompt: str, response: str) -> str:
    h = hashlib.sha256()
    h.update(prompt.encode("utf-8"))
    h.update(b"\x00")
    h.update(response.encode("utf-8"))
    return h.hexdigest()


def _marker_path(session_id: str) -> Path:
    safe = hashlib.sha256((session_id or "unknown").encode("utf-8")).hexdigest()[:32]
    return MARKER_DIR / f"{safe}.sig"


def _already_recorded(session_id: str, signature: str) -> bool:
    try:
        marker = _marker_path(session_id)
        if marker.is_file():
            return marker.read_text(encoding="utf-8").strip() == signature
    except Exception:
        pass
    return False


def _write_marker(session_id: str, signature: str) -> None:
    try:
        MARKER_DIR.mkdir(parents=True, exist_ok=True)
        _marker_path(session_id).write_text(signature, encoding="utf-8")
    except Exception as exc:
        _log(f"marker write failed: {exc!r}")


def _record(prompt: str, response: str, model: str, session_id: str, cwd: str) -> None:
    if SRC_ROOT not in sys.path:
        sys.path.insert(0, SRC_ROOT)
    # _model() reads AEGIS_FRONTIER_MODEL from the environment first; set it so the
    # recorded provenance matches the model that actually produced this turn.
    os.environ["AEGIS_FRONTIER_MODEL"] = model or os.environ.get(
        "AEGIS_FRONTIER_MODEL", DEFAULT_MODEL
    )
    os.environ.setdefault("PYTHONUTF8", "1")

    from aegis_verus_lab.dataquad import VerusDataQuad
    from aegis_verus_lab.desktop_runtime import DesktopVerusRuntime

    runtime = DesktopVerusRuntime(
        VerusDataQuad(RELEASE_ROOT, STATE_ROOT),
        model=os.environ["AEGIS_FRONTIER_MODEL"],
    )
    begun = runtime.begin_turn(prompt=prompt)
    runtime.commit_turn(
        correlation_id=begun["correlation_id"],
        turn_id=begun["turn_id"],
        prompt=prompt,
        response_text=response,
        appends=[],
    )
    _log(
        f"recorded turn_id={begun['turn_id']} session={session_id} "
        f"cwd={cwd} model={os.environ['AEGIS_FRONTIER_MODEL']} "
        f"prompt_chars={len(prompt)} response_chars={len(response)}"
    )
    # Enqueue the turn for a later model-authored Affect+Context read. The hook has no model,
    # so it CANNOT author a genuine Seven-Virtue read (that would be fabrication); it records
    # Present Experience above and leaves an off-ledger work item here. A real drain pass (the
    # live model in an AEGIS session, or a scheduled `claude -p` catch-up) authors the Advocate
    # (PEER+SPINE) and Steward (NCT+PCT) reads. The queue write never touches the transcript,
    # so it cannot trigger the hook again; failure here must not lose the Present-Experience
    # record already committed, so it is caught and logged, never raised.
    try:
        from aegis_verus_lab.affect_prescan import scan_force_signals
        from aegis_verus_lab.affect_drain import enqueue

        prescan = scan_force_signals(prompt)
        enqueue(
            STATE_ROOT,
            subject_turn_id=str(begun["turn_id"]),
            session_id=session_id,
            cwd=cwd,
            model=os.environ["AEGIS_FRONTIER_MODEL"],
            prompt=prompt,
            response=response,
            force_prescan=prescan,
        )
        _log(
            f"enqueued affect-read subject_turn_id={begun['turn_id']} "
            f"force_signals={prescan.get('signals')}"
        )
    except Exception as exc:  # never lose the committed PE turn over a queue-write failure
        _log(f"affect enqueue failed (subject_turn_id={begun['turn_id']}): {exc!r}")


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}

    transcript_path = event.get("transcript_path") or ""
    session_id = event.get("session_id") or ""
    cwd = event.get("cwd") or ""

    if not _in_scope(cwd):
        # Out of scope (not an AEGIS drive). Skip quietly, no log noise.
        return 0

    if not transcript_path or not Path(transcript_path).is_file():
        _log(f"no usable transcript_path (session={session_id}); skipping")
        return 0

    events = _load_transcript_events(transcript_path)
    prompt, response, model = _extract_turn(events)
    if not prompt or not response:
        _log(
            f"nothing to record (session={session_id}, "
            f"prompt={bool(prompt)}, response={bool(response)})"
        )
        return 0

    signature = _signature(prompt, response)
    if _already_recorded(session_id, signature):
        return 0

    try:
        _record(prompt, response, model, session_id, cwd)
        _write_marker(session_id, signature)
    except Exception as exc:
        _log(f"record failed (session={session_id}): {exc!r}\n{traceback.format_exc()}")
    return 0


if __name__ == "__main__":
    # Always exit 0 — a Present Experience hook must never break a session.
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
