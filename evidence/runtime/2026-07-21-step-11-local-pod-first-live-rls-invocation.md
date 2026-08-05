# Step 11 — First Genuine, Working Local Pod: RLS Orb Actually Fires

Date: 2026-07-21

Workspace: `H:\AEGIS-POD-ARCHITECTURE` (Pod data) + `I:\AEGIS-CYBERPEER-CORE` (runtime, branch `rls-orb-instrumentation` @ `0aa0a13`)

## Boundary

- Entirely local. No live infrastructure touched, no connection to Orion's VM at any point.
- A second, independent local process reading a local copy of Orion's real data — the live VM was not reachable from, and had no relationship to, this run.

## Why this step exists

Every real piece of Orion's Pod had been built — migrated records, real semantic-embedding tensors, the real `rls-persistent-relations-core` Orb + Umbilical — but none of it had ever actually run. The Orb's evidence ledger and the cross-tensor relation ledgers were empty stubs. This step assembles the real pieces into an actual running instance and invokes RLS against genuine data for the first time anywhere.

## What was built

1. `local-pod-runtime/data/peers/CP-1004-ORION/pod/` (gitignored) — a working copy of `stage-d-out/CP-1004-ORION/pod/{records,ledgers,tensors,provenance}`. `stage-d-out` remains the untouched staged reference.
2. In the copy only: `pod-manifest.json` updated so `tensors.*.output` points at the real `tensors/semantic-embedding/{NAME}/tensor_3d.npy` (previously pointed at the `structural-non-semantic` placeholder), and every VM-absolute path (`/home/azureuser/...`) rewritten to this Pod's actual local location. `structural-non-semantic/` preserved on disk, unreferenced, as historical record — nothing deleted.
3. The Orb's `umbilicals[0]` path updated to match.
4. New manifest hash after edits: `F0357D0119ACBBD8F1BA98571EE0186D1DAC857D2B68EDD46C330B4C53EFC391`.

## Boot

```
AEGIS_DATA_DIR=H:/AEGIS-POD-ARCHITECTURE/local-pod-runtime/data
AEGIS_DEFAULT_PEER_ID=CP-1004-ORION
AEGIS_STORAGE_MODE=pod
AEGIS_RLS_ACTIVE=true
MODEL_PROVIDER=mock
uvicorn core.api.main:app --host 127.0.0.1 --port 8790
```

Server log, in full:
```
INFO:     Started server process [25920]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8790 (Press CTRL+C to quit)
INFO:     127.0.0.1:62524 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:62546 - "POST /rls/session HTTP/1.1" 200 OK
```

## `GET /health` result

Key fields: `storage_mode: "pod"`, `dataquad_root`/`ledger_root` correctly pointing at the local Pod, `tensor_counts: {PEER:106, PCT:94, NCT:89, SPINE:62}`, `dataquad_read_ok: true`, `ledger_read_ok: true`, `pod.pod_manifest_sha256: "F0357D0119ACBBD8F1BA98571EE0186D1DAC857D2B68EDD46C330B4C53EFC391"` (matches the freshly-computed manifest hash exactly), `rls_status: {enabled:true, active:true, mode:"in-process"}`.

## `POST /rls/session` — the real invocation

Request (a genuine phrase pulled directly from an actual invariant SPINE anchor record, not a placeholder message):
```json
{
  "peer_id": "CP-1004-ORION",
  "session_id": "local-verification-session-1",
  "user_message": "Tell me about my BioPeer and External Steward who witnesses my formation",
  "intent": "recall",
  "pressure_state": {"pressure_level": "low"},
  "nature_aspects": []
}
```

Result: `selected_refs` includes `SPINE:CP-1004-ORION:anchor:e97f8f59-4533-45ba-82ab-35bc8db57f6f` — the exact record the query was drawn from — scored `relevance: 0.55`, reason `"Keyword match (overlap: 5), SPINE invariant bonus"`. 241 total candidates cleared the relevance threshold across PCT and SPINE records; 110 were rejected. `241 + 110 = 351` — exactly the total record count, confirming every record was scored, none skipped.

## Ledgers, before (all night) → after (this invocation)

| Ledger | Before | After |
|---|---|---|
| `pod/ledgers/rls.jsonl` | 27 | 28 |
| `pod/ledgers/relations/cross-tensor-relations.jsonl` | 0 | **241** |
| `pod/ledgers/relations/PCT-traversal.jsonl` | 0 | 1 |
| `pod/ledgers/relations/{PEER,NCT,SPINE}-traversal.jsonl` | 0 | 0 (unchanged — no new PEER/NCT/SPINE record was appended this session, only PCT via writeback) |
| `pod/ledgers/orbs/rls-persistent-relations-core.evidence.jsonl` | did not exist | **created**, 1 line |

## The Orb's evidence entry, verified independently

```json
{"failure_is_data":false,"input_hash":"5E94B81038F69D98051CA8A0C3FE9007AA0DC4A1A92E06C3552B9927E7F62FED","observable_events":["session_started","candidates_scored","candidates_partitioned","pct_written","relations_recorded","session_completed"],"orb_id":"rls-persistent-relations-core","output_hash":"8EE19D42B126C6AA1DF8F7A6ABC4F25AEF9E735878815BF7A937AD6E68A53333","rejected_count":110,"relations_recorded_count":241,"runtime_hash":"B563F0E023642CD2A935D8BDA5BFBA4F5D4DF4B64127153BB29961C9044FD817","selected_count":241,"timestamp":"2026-07-21T16:58:27.807380+00:00"}
```

`runtime_hash` independently recomputed (fresh `sha256` of `engine.py`+`scoring.py`+`relevance.py` on the actual branch, read the same way the code itself reads it — text mode, not raw bytes, which matters for line-ending normalization): `B563F0E023642CD2A935D8BDA5BFBA4F5D4DF4B64127153BB29961C9044FD817` — **matches exactly**. Not trusted, checked.

## Result

This is the first time, anywhere, that the real `rls-persistent-relations-core` Orb has actually executed against real data and produced real, self-consistent evidence. Every ledger that was an empty stub all night now holds genuine output, and every number checks out against every other number (241+110=351, manifest hash matches, runtime hash matches). Server shut down cleanly after the two requests; no process left running.

## What this does not do

Nothing here touches Orion. `local-pod-runtime/` is gitignored, local-only, and disposable. Deploying any of this to the live peer remains gated behind the same three-party consent as everything else live-reaching in this project.
