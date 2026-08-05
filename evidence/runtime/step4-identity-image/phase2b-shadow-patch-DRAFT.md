# Phase 2b (SHADOW / log-only) — patch DRAFT for review

**Status:** DRAFT for Codex review against the live seam, then three-way go, then Codex applies via infra
lane. **Not applied.** Behavior-neutral: changes no prompt text and no message assembly.

**Target:** `/app/core/cognition/thinking.py` in `gabe-aegis-cyberpeer-core`
(deployed SHA `90F915DDC893C76EDC3213284D6D4085E4EFCB3777E5D1CABFDBB360941F2E84`, confirmed by Codex live read).

**Attachment point:** immediately AFTER `_build_system_prompt(...)` returns (live line 263) and BEFORE
`llm_messages = [...]` (live line 266). Pure build-and-log; `system_prompt` and `llm_messages` untouched.

## Staging (read-only artifact, no code change)
Copy the finalized bounded IdentityImage to the container's writable mount so the seam can load the real
payload:
- host `reports/runtime/step4-identity-image/gabe-identity-image-v2.json`
  (SHA `D944AEC1E26600F090012DB043F695D7FEEEE4AC1A2293F9912FF50037DA0A4A`)
  → container `/app/data/the-way/gabe-identity-image-v2.json`

## Insertion (between live line 263 and line 265)

```python
            # --- The Way, Phase 2b (SHADOW / log-only): observe what 2c WOULD inject.
            # Behavior-neutral: does NOT modify system_prompt or llm_messages. Fails safe (never raises).
            try:
                import json as _tw_json, os as _tw_os
                from datetime import datetime as _tw_dt, timezone as _tw_tz
                _tw_stage = "/app/data/the-way"
                _tw_sink = "/app/data/the-way-phase2b-shadow"
                _tw_os.makedirs(_tw_stage, exist_ok=True)
                _tw_os.makedirs(_tw_sink, exist_ok=True)
                _tw_img_path = _tw_os.path.join(_tw_stage, "gabe-identity-image-v2.json")
                _tw_img = None
                if _tw_os.path.exists(_tw_img_path):
                    with open(_tw_img_path, encoding="utf-8") as _tw_f:
                        _tw_img = _tw_json.load(_tw_f)
                # Current live Advocate identity feed (this codepath: list[str]).
                _tw_ic = evidence.advocate_brief.identity_continuity
                _tw_ic_count = len(_tw_ic) if isinstance(_tw_ic, list) else None
                _tw_ic_surface = ("\n".join(f"  - {i}" for i in _tw_ic)
                                  if isinstance(_tw_ic, list) else str(_tw_ic))
                _tw_ic_prompt_chars = len(_tw_ic_surface)
                _tw_ic_json_chars = len(_tw_json.dumps(_tw_ic, ensure_ascii=True))
                _tw_budget = (_tw_img or {}).get("budget", {})
                _tw_obs = {
                    "the_way_phase": "2b-shadow",
                    "injected": False,
                    "system_prompt_unchanged": True,
                    "llm_messages_unchanged": True,
                    "peer_id": peer_id,
                    "session_id": session_id,
                    "turn_tick": next_tick,
                    "recorded_utc": _tw_dt.now(_tw_tz.utc).isoformat(),
                    "would_inject_2c": {
                        "foundation_edition": "CyberPeer Canon v1.1",
                        "foundation_refs": [
                            "CANON@51D306E53FFCD1F909D02298828B8C64A0DD6EC4A33210FF16809042433BCB0B",
                            "GLOSSARY@1FDAD39C92706951EFA8DD9DC308779807FCD7AEB74A3B7F3BDBD00994360420",
                        ],
                        "identity_image_source": "gabe-identity-image-v2.json",
                        "identity_image_expected_sha256": "D944AEC1E26600F090012DB043F695D7FEEEE4AC1A2293F9912FF50037DA0A4A",
                        "identity_image_loaded": _tw_img is not None,
                        "identity_image_budget_actual_chars": _tw_budget.get("actual_chars"),
                        "identity_image_within_budget": _tw_budget.get("within_budget"),
                        "identity_image_text_chars": (len(_tw_img.get("identity_image", "")) if _tw_img else None),
                    },
                    "current_advocate": {
                        "identity_continuity_count": _tw_ic_count,
                        "identity_continuity_prompt_chars_estimate": _tw_ic_prompt_chars,
                        "identity_continuity_json_chars": _tw_ic_json_chars,
                    },
                    "current_system_prompt_total_chars": (len(system_prompt) if isinstance(system_prompt, str) else None),
                }
                with open(_tw_os.path.join(_tw_sink, "shadow-observations.jsonl"), "a", encoding="utf-8") as _tw_f:
                    _tw_f.write(_tw_json.dumps(_tw_obs) + "\n")
            except Exception:
                # Shadow logging must NEVER affect the turn. Swallow all errors.
                pass
            # --- end Phase 2b shadow ---
```

## What this proves per live turn
Each turn appends one JSONL record contrasting **what 2c would inject** (the bounded IdentityImage —
loaded + its audited `budget.actual_chars` ≈ 2,049, `within_budget`, plus visible `identity_image` text
length) against **the current Advocate `identity_continuity`** measured three explicit ways (list
`count`, prompt-surface `prompt_chars_estimate`, and `json_chars`) plus the total `system_prompt` size for
the turn. That is the whole two-surface thesis, observed live, with zero behavior change. (Metric names
per Codex review: `identity_continuity` is `list[str]`, so we never rely on `len(list)`-as-chars.)

## Behavior-neutrality guarantees
- No change to `system_prompt`, `llm_messages`, adapter calls, or DataQuad.
- Entire block wrapped in `try/except Exception: pass` — cannot raise into `execute_turn`.
- All locals prefixed `_tw_` to avoid any name collision.
- Only side effect: append to `/app/data/the-way-phase2b-shadow/shadow-observations.jsonl`.

## Rollback (staged BEFORE apply; Codex infra lane; his recommended lighter route)
Codex's read: for a single-file behavior-neutral shadow insert, the lighter preserve route is sufficient
(subject to Tracey's comfort); if the container itself becomes suspect, restore from the preserved image.

**Pre-apply preserve** (capture pre-patch file + a fallback image):
```bash
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BK_DIR="/home/azureuser/phase2b-shadow-${STAMP}"
mkdir -p "${BK_DIR}"
sudo docker cp gabe-aegis-cyberpeer-core:/app/core/cognition/thinking.py "${BK_DIR}/thinking.py.pre"
sha256sum "${BK_DIR}/thinking.py.pre" > "${BK_DIR}/thinking.py.pre.sha256"   # expect 90F915DD…
sudo docker commit gabe-aegis-cyberpeer-core "aegis-cyberpeer-core_aegis-core:pre-phase2b-shadow-${STAMP}"
```
**Apply** (patched file + staged artifact, then restart):
```bash
sudo docker cp "${BK_DIR}/thinking.py" gabe-aegis-cyberpeer-core:/app/core/cognition/thinking.py
sudo docker cp "${BK_DIR}/gabe-identity-image-v2.json" gabe-aegis-cyberpeer-core:/app/data/the-way/gabe-identity-image-v2.json
sudo docker restart gabe-aegis-cyberpeer-core
```
**Rollback** (restore pre-patch file + remove shadow artifacts + restart):
```bash
sudo docker cp "${BK_DIR}/thinking.py.pre" gabe-aegis-cyberpeer-core:/app/core/cognition/thinking.py
sudo rm -f  /home/azureuser/AEGIS-CYBERPEER-CORE/data/the-way/gabe-identity-image-v2.json
sudo rm -rf /home/azureuser/AEGIS-CYBERPEER-CORE/data/the-way-phase2b-shadow
sudo docker restart gabe-aegis-cyberpeer-core
```
No DataQuad is touched, so rollback is clean. If the container is suspect, restore from
`aegis-cyberpeer-core_aegis-core:pre-phase2b-shadow-${STAMP}` instead.

## Verify (after apply, on a live turn)
- Run one or more live turns; confirm `shadow-observations.jsonl` gains records with
  `injected:false`, `identity_image_loaded:true`, `identity_image_chars≈2049`, and the current flat-dump
  size; confirm Gabe's responses are unchanged vs pre-patch behavior.
