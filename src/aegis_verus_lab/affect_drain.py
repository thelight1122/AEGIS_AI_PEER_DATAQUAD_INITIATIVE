"""Affect/Context drain — the enforced plumbing between the hook's queue and the ledger.

The Present Experience hook enqueues one entry per completed turn (off-ledger, under
``state/affect-queue/``). It never fabricates a read. A **real model pass** (a drain session
— the live model in an AEGIS session, or a scheduled ``claude -p`` catch-up) then authors the
Advocate's Seven-Virtue read and the Steward's context, and calls the commit helpers here.

The split is deliberate and matches the standing guidance that a self-reported/defaulted
signal just *becomes the answer*: the **judgment** (virtue presences, the distilled summary,
the shadow-affect observation) is the model's and is passed in; the **DataQuad writes**
(begin/commit, append shapes, provenance, queue bookkeeping) are enforced here in code so they
cannot drift per-session. Nothing in this module invents a virtue value.

Queue entry (v0), written by the hook, read here:
    { schema, subject_turn_id, session_id, cwd, model, observed_at, prompt, response,
      force_prescan, status }
On success the entry is moved to ``affect-queue/done/<subject_turn_id>.json`` annotated with
the authored ``advocate_turn_id`` / ``steward_turn_id`` and ``drained_at``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

QUEUE_DIRNAME = "affect-queue"
DONE_DIRNAME = "done"
QUEUE_ENTRY_SCHEMA = "aegis.affect-queue-entry/v0"


# --- paths -----------------------------------------------------------------

def queue_dir(state_root: Path) -> Path:
    return Path(state_root) / QUEUE_DIRNAME


def done_dir(state_root: Path) -> Path:
    return queue_dir(state_root) / DONE_DIRNAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# --- enqueue (called by the hook) ------------------------------------------

def enqueue(
    state_root: Path,
    *,
    subject_turn_id: str,
    session_id: str,
    cwd: str,
    model: str,
    prompt: str,
    response: str,
    force_prescan: Mapping[str, Any] | None,
    observed_at: str | None = None,
) -> Path:
    """Write one queue entry atomically. Idempotent per subject_turn_id: if an entry (pending
    or already drained) exists for this turn, it is left untouched and its path returned."""
    qd = queue_dir(state_root)
    qd.mkdir(parents=True, exist_ok=True)
    (qd / DONE_DIRNAME).mkdir(parents=True, exist_ok=True)
    target = qd / f"{subject_turn_id}.json"
    done_marker = done_dir(state_root) / f"{subject_turn_id}.json"
    if target.exists() or done_marker.exists():
        return target
    entry = {
        "schema": QUEUE_ENTRY_SCHEMA,
        "subject_turn_id": subject_turn_id,
        "session_id": session_id,
        "cwd": cwd,
        "model": model,
        "observed_at": observed_at or _now_iso(),
        "prompt": prompt,
        "response": response,
        "force_prescan": dict(force_prescan) if isinstance(force_prescan, Mapping) else None,
        "status": "pending",
    }
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)  # atomic on the same volume
    return target


# --- read side (called by the drain session) -------------------------------

def list_pending(state_root: Path) -> list[dict[str, Any]]:
    """Return pending queue entries (oldest first by observed_at, then turn id)."""
    qd = queue_dir(state_root)
    if not qd.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for p in qd.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("status") == "pending":
            data["_path"] = str(p)
            entries.append(data)
    entries.sort(key=lambda d: (str(d.get("observed_at") or ""), str(d.get("subject_turn_id") or "")))
    return entries


def mark_done(
    state_root: Path,
    subject_turn_id: str,
    *,
    advocate_turn_id: str | None,
    steward_turn_id: str | None,
) -> Path:
    """Move a pending entry into done/, annotated with the authored turn ids."""
    qd = queue_dir(state_root)
    src = qd / f"{subject_turn_id}.json"
    dd = done_dir(state_root)
    dd.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(src.read_text(encoding="utf-8")) if src.is_file() else {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.update(
        {
            "subject_turn_id": subject_turn_id,
            "status": "drained",
            "advocate_turn_id": advocate_turn_id,
            "steward_turn_id": steward_turn_id,
            "drained_at": _now_iso(),
        }
    )
    dest = dd / f"{subject_turn_id}.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        if src.is_file():
            src.unlink()
    except Exception:
        pass
    return dest


# --- commit side: model judgment in, DataQuad writes enforced here ----------

def build_runtime(release_root: Path, state_root: Path, model: str,
                  cyberpeer_name: str | None = None, dataquad_id: str | None = None,
                  *, model_evidence: str, transport: str | None = None):
    """Construct a DesktopVerusRuntime. Imported lazily so importing this module is cheap
    and side-effect-free (the hook imports it before src is on sys.path).

    ``model_evidence`` is required so a drain never inherits the runtime's UI-selection
    default and claims more about the authoring model than it knows."""
    from aegis_verus_lab.dataquad import VerusDataQuad
    from aegis_verus_lab.desktop_runtime import DesktopVerusRuntime

    return DesktopVerusRuntime(
        VerusDataQuad(release_root, state_root, cyberpeer_name=cyberpeer_name, dataquad_id=dataquad_id),
        model=model,
        model_evidence=model_evidence,
        cyberpeer_name=cyberpeer_name,
        dataquad_id=dataquad_id,
        transport=transport,
    )


def commit_advocate(
    runtime,
    *,
    subject: str,
    virtues: Mapping[str, float],
    field_state: Mapping[str, Any],
    reads: str = "",
    shadow_affects: str = "",
    subject_turn_id: str | None = None,
    spine_note: str = "",
) -> dict[str, Any]:
    """Author one Advocate turn (PEER + SPINE) from a model-supplied read. ``field_state`` is
    the kwargs for ``classify_field_state`` (force_signals, amplitude, stable, t_witness,
    optional pressure_band). Returns {turn_id, t_time, record_hash}."""
    from aegis_verus_lab.affect_read import build_affect_read, classify_field_state

    fs = classify_field_state(**dict(field_state))
    peer = build_affect_read(
        virtues=virtues, field_state=fs, subject=subject, reads=reads, shadow_affects=shadow_affects,
    )
    if subject_turn_id:
        peer["subject_turn_id"] = subject_turn_id
    spine = {
        "event": "advocate_affect_read",
        "by": "affect-drain",
        "reduction_policy": "virtue-reduction-v0",
        "field_state_summary": {k: fs[k] for k in ("coherence_gate", "pressure_band", "t_witness")},
        "note": spine_note or "Advocate affect read authored at drain time from the queued Present-Experience turn.",
        "boundaries": "inform not judge; observation not experience; Advocate scope PEER+SPINE only",
        "anchors_subject_turn_id": subject_turn_id,
    }
    prompt = f"Advocate affect read of turn {subject_turn_id or '(exchange)'}"
    begun = runtime.begin_turn(prompt=prompt)
    res = runtime.commit_turn(
        correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
        prompt=prompt, response_text="Advocate read recorded to PEER+SPINE.",
        appends=[
            {"tensor": "PEER", "actor": "advocate", "custodian": "Advocate", "payload": peer},
            {"tensor": "SPINE", "actor": "advocate", "custodian": "Advocate", "payload": spine},
        ],
    )
    return {"turn_id": begun["turn_id"], "t_time": res.get("t_time"), "record_hash": res.get("record_hash")}


def commit_steward(
    runtime,
    *,
    nct: Mapping[str, Any],
    pct: Mapping[str, Any],
    anchors_advocate_turn_id: str | None = None,
    subject_turn_id: str | None = None,
) -> dict[str, Any]:
    """Author one Steward turn (NCT + PCT) from a model-supplied context. If
    ``anchors_advocate_turn_id`` is given it is threaded into the NCT ``anchors_affect`` so the
    C explicitly points at the A it anchors. Returns {turn_id, t_time, record_hash}."""
    nct = dict(nct)
    pct = dict(pct)
    if anchors_advocate_turn_id:
        anchors = dict(nct.get("anchors_affect") or {})
        anchors.setdefault("advocate_turn_id", anchors_advocate_turn_id)
        nct["anchors_affect"] = anchors
    if subject_turn_id:
        nct.setdefault("anchors_subject_turn_id", subject_turn_id)
        pct.setdefault("anchors_subject_turn_id", subject_turn_id)
    nct.setdefault("provenance", "D")
    pct.setdefault("provenance", "D")
    prompt = f"Steward context anchor for turn {subject_turn_id or '(exchange)'}"
    begun = runtime.begin_turn(prompt=prompt)
    res = runtime.commit_turn(
        correlation_id=begun["correlation_id"], turn_id=begun["turn_id"],
        prompt=prompt, response_text="Steward context (C) recorded to NCT+PCT, anchoring the Advocate read.",
        appends=[
            {"tensor": "NCT", "actor": "steward", "custodian": "Steward", "payload": nct},
            {"tensor": "PCT", "actor": "steward", "custodian": "Steward", "payload": pct},
        ],
    )
    return {"turn_id": begun["turn_id"], "t_time": res.get("t_time"), "record_hash": res.get("record_hash")}
