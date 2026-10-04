#!/usr/bin/env python3
"""Affect/Context drain driver — Verus DataQuad (LOCAL, offline).

Two modes, mirroring the two halves of the pipeline:

  * ``--list``  : print the pending affect-read queue as JSON (subject_turn_id, prompt,
                  response, force_prescan hint, ...). A drain session reads this, then AUTHORS
                  the Advocate's Seven-Virtue read and the Steward's context for each turn.
  * ``--commit``: read a JSON array of authored reads on stdin and commit them — for each
                  entry an Advocate turn (PEER+SPINE) then a Steward turn (NCT+PCT, anchored to
                  that Advocate), then move the queue entry to done/.

The model judgment lives in the authored-reads JSON (produced by a real model pass). This
driver only enforces the DataQuad writes and the queue bookkeeping; it invents no virtue value.

Authored-read entry (stdin, --commit):
  {
    "subject_turn_id": "verus-local-turn-...",
    "advocate": { "virtues": {7 virtues 0..1}, "field_state": {force_signals, amplitude,
                  stable, t_witness, [pressure_band]}, "subject": str, "reads": str,
                  "shadow_affects": str, "spine_note": str },
    "steward":  { "nct": {...}, "pct": {...} }   # optional but strongly recommended
  }

Config comes from $AEGIS_PEER_CONFIG or ~/.claude/aegis-peer-config.json, with the Verus lab
values as fallback — identical resolution to the Present Experience hook.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_FALLBACK_SRC = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\src"
_FALLBACK_LAB = r"H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\deploy\verus-lab\local"
_FALLBACK_MODEL = "claude-opus-4-8"


def _load_cfg() -> dict:
    try:
        p = os.environ.get("AEGIS_PEER_CONFIG") or str(Path.home() / ".claude" / "aegis-peer-config.json")
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _resolve():
    cfg = _load_cfg()
    paths = cfg.get("paths", {}) if isinstance(cfg.get("paths"), dict) else {}
    runtime = cfg.get("runtime", {}) if isinstance(cfg.get("runtime"), dict) else {}
    peer = cfg.get("peer", {}) if isinstance(cfg.get("peer"), dict) else {}
    src = paths.get("src_root") or _FALLBACK_SRC
    lab = paths.get("lab_root") or _FALLBACK_LAB
    release = Path(paths.get("release_root") or (Path(lab) / "foundation"))
    state = Path(paths.get("state_root") or (Path(lab) / "state"))
    model = runtime.get("model") or _FALLBACK_MODEL
    transport = runtime.get("transport") or "local_entrypoint_no_ssh"
    return src, release, state, model, peer.get("cyberpeer_name"), peer.get("dataquad_id"), transport


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="print pending queue entries as JSON")
    g.add_argument("--commit", action="store_true", help="commit authored reads from stdin JSON")
    ap.add_argument("--limit", type=int, default=0, help="with --list, cap the number returned")
    ap.add_argument("--model", default="",
                    help="with --commit, the exact model id authoring these reads (recorded as provenance)")
    args = ap.parse_args(argv)

    src, release, state, cfg_model, name, did, transport = _resolve()
    # Provenance: an operator-declared model wins, then the environment, and only then the
    # config setting -- each labelled with how it was learned so none claims more than it knows.
    if args.model.strip():
        model, evidence = args.model.strip(), "drain_operator_declared"
    elif os.environ.get("AEGIS_FRONTIER_MODEL", "").strip():
        model, evidence = os.environ["AEGIS_FRONTIER_MODEL"].strip(), "environment_AEGIS_FRONTIER_MODEL"
    else:
        model, evidence = cfg_model, "config_setting_unverified"
    os.environ.setdefault("PYTHONUTF8", "1")
    if src not in sys.path:
        sys.path.insert(0, src)

    from aegis_verus_lab import affect_drain as ad

    if args.list:
        pending = ad.list_pending(state)
        if args.limit and args.limit > 0:
            pending = pending[: args.limit]
        # Drop the internal _path key from the emitted view.
        for e in pending:
            e.pop("_path", None)
        print(json.dumps({"pending_count": len(pending), "pending": pending}, ensure_ascii=False, indent=2))
        return 0

    # --commit
    raw = sys.stdin.read()
    try:
        authored = json.loads(raw or "[]")
    except Exception as exc:
        print(json.dumps({"error": "bad_json", "message": str(exc)[:300]}), file=sys.stderr)
        return 2
    if isinstance(authored, dict):
        authored = [authored]
    if not isinstance(authored, list):
        print(json.dumps({"error": "authored reads must be a JSON array or object"}), file=sys.stderr)
        return 2

    rt = ad.build_runtime(release, state, model, name, did, model_evidence=evidence, transport=transport)
    results = []
    for entry in authored:
        if not isinstance(entry, dict):
            results.append({"error": "entry not an object", "entry": str(entry)[:120]})
            continue
        stid = entry.get("subject_turn_id")
        adv = entry.get("advocate") or {}
        stw = entry.get("steward") or {}
        try:
            adv_res = ad.commit_advocate(
                rt,
                subject=str(adv.get("subject", "")),
                virtues=adv["virtues"],
                field_state=adv.get("field_state", {}),
                reads=str(adv.get("reads", "")),
                shadow_affects=str(adv.get("shadow_affects", "")),
                subject_turn_id=stid,
                spine_note=str(adv.get("spine_note", "")),
            )
            stew_res = None
            if stw.get("nct") and stw.get("pct"):
                stew_res = ad.commit_steward(
                    rt,
                    nct=stw["nct"],
                    pct=stw["pct"],
                    anchors_advocate_turn_id=adv_res["turn_id"],
                    subject_turn_id=stid,
                )
            ad.mark_done(
                state, str(stid),
                advocate_turn_id=adv_res["turn_id"],
                steward_turn_id=(stew_res or {}).get("turn_id"),
            )
            results.append({
                "subject_turn_id": stid,
                "advocate": adv_res,
                "steward": stew_res,
                "steward_authored": stew_res is not None,
            })
        except Exception as exc:
            import traceback
            results.append({"subject_turn_id": stid, "error": type(exc).__name__,
                            "message": str(exc)[:400], "trace": traceback.format_exc()[-800:]})
    print(json.dumps({"committed": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
