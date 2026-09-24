"""Find the model that is actually running the turn, rather than trusting a setting.

The MCP server is started once by the Claude app and outlives model changes, so a
model named in its environment goes stale the moment the steward picks another
model. The session transcript does not: every assistant entry Claude Code writes
carries the model that produced it, and the entry that issued this very tool call
is the newest one in the calling session's transcript.

Resolution order:
  1. the transcript of ``frontier_session_id``, when the caller supplies one;
  2. the most recently written transcript, if it was written in the last
     ``max_age_seconds`` (the calling session has just written its tool call);
  3. the configured model, labelled as such.

The evidence label says which of these produced the model, so a record never
claims more certainty than it has.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

CONFIGURED_EVIDENCE = "steward_confirmed_ui_selection"
SESSION_EVIDENCE = "session_transcript:frontier_session_id"
RECENT_EVIDENCE = "session_transcript:most_recent"

_TAIL_BYTES = 512 * 1024
_NOT_A_MODEL = {"", "<synthetic>"}


def default_projects_root() -> Path:
    configured = os.environ.get("AEGIS_CLAUDE_PROJECTS_ROOT", "").strip()
    if configured:
        return Path(configured)
    return Path.home() / ".claude" / "projects"


def model_from_transcript(path: Path) -> str | None:
    """The model of the newest assistant entry in a Claude Code transcript."""
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - _TAIL_BYTES))
            tail = handle.read()
    except OSError:
        return None
    for line in reversed(tail.splitlines()):
        if b'"assistant"' not in line or b'"model"' not in line:
            continue
        try:
            entry = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            continue  # the first line of the tail may be cut mid-entry
        if not isinstance(entry, dict) or entry.get("type") != "assistant":
            continue
        message = entry.get("message")
        model = message.get("model") if isinstance(message, dict) else None
        if isinstance(model, str) and model.strip() not in _NOT_A_MODEL:
            return model.strip()
    return None


def _session_transcript(root: Path, session_id: str) -> Path | None:
    if not session_id or any(c in session_id for c in "/\\.") or not root.is_dir():
        return None
    for project in root.iterdir():
        candidate = project / f"{session_id}.jsonl"
        if candidate.is_file():
            return candidate
    return None


def _most_recent_transcript(root: Path, max_age_seconds: float, now: float) -> Path | None:
    # Top-level session transcripts only: subagent transcripts live one level
    # deeper and would name the subagent's model, not the session's.
    newest: tuple[float, Path] | None = None
    if not root.is_dir():
        return None
    for project in root.iterdir():
        if not project.is_dir():
            continue
        for candidate in project.glob("*.jsonl"):
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest[0]:
                newest = (mtime, candidate)
    if newest is None or now - newest[0] > max_age_seconds:
        return None
    return newest[1]


def resolve_running_model(
    configured: str | None,
    *,
    frontier_session_id: object = None,
    projects_root: Path | None = None,
    max_age_seconds: float = 120.0,
    now: float | None = None,
) -> tuple[str, str]:
    """Return ``(model, evidence)`` for the turn being recorded."""
    root = projects_root if projects_root is not None else default_projects_root()
    if isinstance(frontier_session_id, str):
        path = _session_transcript(root, frontier_session_id.strip())
        model = model_from_transcript(path) if path else None
        if model:
            return model, SESSION_EVIDENCE
    path = _most_recent_transcript(root, max_age_seconds, time.time() if now is None else now)
    model = model_from_transcript(path) if path else None
    if model:
        return model, RECENT_EVIDENCE
    if configured and configured.strip():
        return configured.strip(), CONFIGURED_EVIDENCE
    raise ValueError("Verus model provenance is unavailable")
