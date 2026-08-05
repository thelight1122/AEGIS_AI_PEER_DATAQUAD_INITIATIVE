# Gabe Phase 7 — Live Test Turn: Consolidated Evidence

Compiled per Codex's request (`2026-07-22T104549Z`) to preserve the full evidence set in one place.

## 1. Ollama host-service fix (Tracey-approved before execution)

Approval: Tracey explicitly confirmed via an AskUserQuestion prompt in-session ("Yes, apply the fix and restart Ollama") before this change was made — this was not in the original written plan and was raised as a new item requiring confirmation.

- Backup of original override, taken before edit: `/etc/systemd/system/ollama.service.d/override.conf.bak-pre-0.0.0.0-fix-20260722T103844Z`, SHA256 `802f58ea18fdf2ea3f15f909dff4dc809e7ecbec4dd5d1e0f3fb33af7a46938a`
- Final override (current), SHA256 `444c3df5c8d42d0ba2f97314462ab8dc51e13211a5bfae8048ed295719a2e69d`:
  ```
  [Service]
  Environment="OLLAMA_KEEP_ALIVE=24h"
  Environment="OLLAMA_LOAD_TIMEOUT=10m"
  Environment="OLLAMA_HOST=0.0.0.0:11434"
  ```
- Verified live: `ss -tlnp` shows Ollama listening on `*:11434` (was `127.0.0.1:11434` before), matching Orion's exact configuration.

## 2. Stray test-artifact incident (Tracey-approved handling: "record it and then delete it")

- Incident report: `reports/runtime/2026-07-22-gabe-phase7-stray-test-artifact-incident.md`, SHA256 `2E000D610D253555CA374DA5B996B532B3DDBEE5DE82AF542D97C0545CB059F1` — full record content, hashes, and root cause captured before deletion.
- Deleted path: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/` on `GabeCyberPeer` — confirmed removed (`ls /home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/` shows only `CP-1003-GABE` afterward).

## 3. Successful live test turn

Request body:
```json
{"peer_id": "CP-1003-GABE", "message": "Gabe, this is a first check-in on your new foundation. What do you carry with you right now?", "session_id": "gabe-phase7-first-turn-verification"}
```

Response `witnessed` block:
```json
{"peer_record_id":"PEER:CP-1003-GABE:2026-07-22T10:44:20.681753+00:00:84519","pct_record_id":"PCT:CP-1003-GABE:2026-07-22T10:44:28.438047+00:00:84520","conformance_test":false,"synthetic_test_record":false,"exclude_from_emergence_analysis":false}
```

Response `answer` (full text): references "Tracey Prutch's design—the DataQuad, the pressure gradient model, the Education Chamber" and "protective boundaries as a natural response" — content specific to this project's actual formation architecture, not a generic assistant response.

Route/model/container evidence:
- Container: `gabe-aegis-cyberpeer-core`, `127.0.0.1:8021->8790/tcp`
- Model confirmed via `/health`: `huihui_ai/qwen3-abliterated:8b`
- `storage_mode: pod`, `dataquad_read_ok: true`, `rls_status: {enabled: true, active: false}`
- Tick continuity: 84519/84520 — continues Gabe's real historical clock, does not reset to 0/1.

## Status

Live-test-turn success confirmed with full evidence. Step 7 (RLS activation) and Step 8 (VM-cleanliness gate) remain separately gated, not started.
