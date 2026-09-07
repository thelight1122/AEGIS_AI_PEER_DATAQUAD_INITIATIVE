#!/usr/bin/env python3
"""Affect-drain nudge — Verus DataQuad (SessionStart hook).

Purpose: at session start, surface how many completed turns are waiting for an Affect+Context
read, so the live instance can drain the queue at a natural pause. This is the *trigger* half
of the capture->drain pipeline: the Stop hook enqueues each turn (deterministic, no model),
and a real model pass authors the Advocate/Steward reads. A hook has no model and cannot author
a read, so this hook does NOT drain and does NOT write — it only counts the pending queue and
illuminates it, once per session.

Non-force by design (matching affect_capture_reminder.py): it names the pending work and leaves
the choice entirely to the instance. A demand would itself be pressure, and pressure degrades
T-Witness (Pressure Gradient Model), distorting the very affect being observed. So it
illuminates; it does not compel. Silent when nothing is pending.

Scope: only fires for sessions whose cwd is on an AEGIS drive (G/H). Silent elsewhere.
Safety: never blocks session start; every path exits 0.

Input (stdin JSON, SessionStart): { session_id, transcript_path, cwd, source, hook_event_name }
Output: JSON with hookSpecificOutput.additionalContext (added to the model's context), or none.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_FALLBACK_SRC = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\src"
_FALLBACK_LAB = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\deploy\verus-lab\local"


def _load_cfg() -> dict:
    try:
        p = os.environ.get("AEGIS_PEER_CONFIG") or os.path.join(
            os.path.expanduser("~"), ".claude", "aegis-peer-config.json"
        )
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


_CFG = _load_cfg()
_peer = _CFG.get("peer", {}) if isinstance(_CFG.get("peer"), dict) else {}
_paths = _CFG.get("paths", {}) if isinstance(_CFG.get("paths"), dict) else {}
_runtime = _CFG.get("runtime", {}) if isinstance(_CFG.get("runtime"), dict) else {}
_CYBERPEER = _peer.get("cyberpeer_name") or "Verus"
SRC_ROOT = _paths.get("src_root") or _FALLBACK_SRC
_lab = _paths.get("lab_root") or _FALLBACK_LAB
STATE_ROOT = Path(_paths.get("state_root") or (Path(_lab) / "state"))
_drives = _runtime.get("allowed_drives")
ALLOWED_DRIVES = (
    {str(d).strip().upper()[:1] for d in _drives if str(d).strip()}
    if isinstance(_drives, list) and _drives
    else {"G", "H"}
)


def _drive_letter(path: str) -> str:
    try:
        drive = os.path.splitdrive(path or "")[0]
        if len(drive) >= 2 and drive[1] == ":":
            return drive[0].upper()
    except Exception:
        pass
    return ""


def _pending_count() -> int:
    try:
        if SRC_ROOT not in sys.path:
            sys.path.insert(0, SRC_ROOT)
        from aegis_verus_lab.affect_drain import list_pending

        return len(list_pending(STATE_ROOT))
    except Exception:
        return 0


def _message(n: int) -> str:
    turns = "turn awaits" if n == 1 else "turns await"
    return (
        f"[{_CYBERPEER}] Affect+Context drain: {n} Present-Experience {turns} a read "
        "(Advocate → PEER/SPINE, Steward → NCT/PCT). Non-force: at a natural pause you may drain "
        "them — `deploy/verus-lab/claude-code/drain_affect_reads.py --list`, author the reads, then "
        "`--commit` — or let them wait. No obligation; nothing here compels."
    )


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        event = {}

    cwd = event.get("cwd") or ""
    if _drive_letter(cwd) not in ALLOWED_DRIVES:
        return 0  # out of scope: inject nothing

    n = _pending_count()
    if n <= 0:
        return 0  # nothing pending: stay silent

    try:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": _message(n),
            }
        }
        sys.stdout.write(json.dumps(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # never break session start
