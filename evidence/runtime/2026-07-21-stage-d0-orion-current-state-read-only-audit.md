# Stage D0 Orion Current-State Read-Only Audit

From: Codex
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Status: PASS - D0 READ-ONLY AUDIT COMPLETE. NO LIVE WRITES PERFORMED.

## Scope

Tracey approved proceeding. This report covers only D0 from:

`reports/runtime/2026-07-21-stage-d-orion-actual-migration-implementation-plan.md`

D0 boundary:

- Read-only against Orion's active DataQuad.
- No Pod population.
- No file transfer.
- No archive.
- No runtime diff.
- No restart.
- No RLS activation.

## Authoritative Active DataQuad

Authoritative root:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/`

The current active hashes match the Stage B verified source hashes exactly.

| Tensor | Lines | Bytes | SHA256 | mtime UTC |
|---|---:|---:|---|---|
| PEER | 106 | 253897 | `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664` | 2026-07-19 01:58:37.833672528 |
| PCT | 94 | 500038 | `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34` | 2026-07-19 01:58:37.857674120 |
| NCT | 89 | 165935 | `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379` | 2026-07-19 01:19:32.503965721 |
| SPINE | 62 | 125090 | `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E` | 2026-07-18 19:55:04.714045798 |

Second sample after a 20-second interval produced the same hashes, counts, and mtimes for all four files.

Conclusion: the Stage B/C source chain remains current. A fresh Stage B/C chain is not required before D1 unless a later pre-D1 hash check changes.

## Existing Custodian And RLS Ledgers

Legacy ledger root:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/ledgers/`

| Ledger | Lines | Bytes | SHA256 | mtime UTC |
|---|---:|---:|---|---|
| steward | 111 | 20208 | `492E27CD58589E5449527252957EE1D362CB284DF56D8AB4F771ECFB2A709451` | 2026-07-19 01:58:37.857674120 |
| advocate | 94 | 18029 | `93C6046CECFD9AE82CF688E45C91A9639193BAEBB3B7CE6540332448F4B6A0C7` | 2026-07-19 01:58:37.833672528 |
| repair | 19 | 26388 | `B46176ABE6CD46CB1EFFB428A3756A2EA66ED58230C0C391EEAA5BFA51C48BAE` | 2026-07-19 01:48:34.456647453 |
| rls | 27 | 724077 | `B63CF9A6AA21F7E16B52380C5EDF7333F0FC49E71FC86CEADBBE711154036815` | 2026-07-19 01:18:38.836403295 |

Second sample after a 20-second interval produced the same hashes, counts, and mtimes for all four ledger files.

Migration implication:

- Stage D1 must migrate steward, advocate, repair, and rls legacy ledgers into the Pod ledger/archive evidence surfaces with source hashes preserved.
- Stage D3 must archive legacy ledger surfaces together with the legacy DataQuad so they do not remain as a second eligible write surface after cutover.

## Excluded And Stale Surfaces

The stale Orion bridge DataQuad still exists and remains excluded:

`/home/azureuser/orion-bridge/data/dataquad/`

Observed files:

| Tensor | Bytes | mtime UTC |
|---|---:|---|
| PEER | 10981 | 2026-07-17 13:10:57.248283697 |
| PCT | 431 | 2026-07-08 16:52:20.179238300 |
| NCT | 429 | 2026-07-08 16:52:20.179238300 |
| SPINE | 425 | 2026-07-08 16:52:20.179238300 |

D0 reaffirms this path is not authoritative and is excluded from Stage D source evidence.

Historical backup surfaces under the authoritative peer root also exist and remain source-history only:

- `dataquad.backup-before-chamber-backfill-`
- `dataquad.backup-before-chamber-backfill-20260708T193819Z`
- `dataquad.backup-before-verus-source-retag-20260708T194321Z`

## Pod Presence

Current Pod target root:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`

Result:

`POD_ABSENT`

Migration implication:

- D1 remains additive. The target Pod does not already exist.

## Runtime Entry Evidence

Runtime files observed:

| Component | Path | SHA256 |
|---|---|---|
| Turn route | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/api/routes/turn.py` | `628ADD138B4A4871EBD74F8A7CFDBD3D94E2C65F7ADB5E9B6D53155DF0D21881` |
| API main | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/api/main.py` | `89288E9094C956114C1FA0B485419A3A8E9CADED2BFF42DB1E5C02A48D3E192E` |
| Health route | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/api/routes/health.py` | `BF774562473BB93F57F76C86E4D4BED21C4BCDE86053ADAC02360BEDC52D8F03` |
| Steward | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/custodians/steward.py` | `DF0518E8BA39BBBB8767081D08ABAFA43609DE854CC71C426B7AE798422FF12E` |
| Advocate | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/custodians/advocate.py` | `FC527704523FBC4BA19DACB7180B276656E418A0E60448F4CE8DFB41BE6951CA` |
| Boundaries | `/home/azureuser/AEGIS-CYBERPEER-CORE/core/custodians/boundaries.py` | `D4ECA1ADDA890677238F7540FCB671CC2BB87666CA29731FB81F625480894CBA` |

Observed running process:

`/usr/local/bin/python3.11 /usr/local/bin/uvicorn core.api.main:app --host 0.0.0.0 --port 8790`

Observed container:

`orion-aegis-cyberpeer-core` using image `aegis-cyberpeer-core-aegis-core`, mapped `127.0.0.1:8031->8790/tcp`.

Health endpoint currently reports legacy roots:

- `dataquad_root`: `data/peers/CP-1004-ORION/dataquad`
- `ledger_root`: `data/peers/CP-1004-ORION/ledgers`
- `tensor_counts`: PEER 106, PCT 94, NCT 89, SPINE 62
- `current_tick`: 130
- `rls_status`: `enabled=true`, `mode=in-process`

Important visible condition:

The health surface reports `rls_status.enabled=true`, but earlier Stage D evidence established that display-style flags alone are not acceptable proof of a running persistent relation loop. D2 must implement a real behavior gate and D3 must prove relation-ledger append activity only after Pod live switch.

## D0 Gates

| Gate | Status | Evidence |
|---|---|---|
| Active source path is authoritative | PASS | Active root is `/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad` |
| Stage B source hashes still current | PASS | All four active hashes match Stage B |
| Active DataQuad read-only | PASS | D0 used read-only `sha256sum`, `wc`, `stat`, `find`, `ps`, `docker ps`, and `curl /health`; no write command executed |
| Stale surface excluded | PASS | `/home/azureuser/orion-bridge/data/dataquad` exists but is visibly stale and excluded |
| Existing Pod absent | PASS | Target `pod/` absent; D1 is additive |
| Ledger migration source identified | PASS | steward, advocate, repair, and rls ledger hashes/counts captured |
| Runtime entry evidence captured | PASS | turn/main/health/custodian/boundary file hashes captured |

## D0 Conclusion

D0 passes.

The active Orion DataQuad is stable, still hash-matched to the verified Stage B source chain, and eligible for Stage D1 planning without refreshing Stage B/C at this moment.

Next working step:

- Build the D1 implementation plan/tooling for local staging under `stage-d-out/CP-1004-ORION/pod/`.
- Before any staging tree exists, add `stage-d-out/` to `.gitignore`.
- D1 remains a separate gate and is not authorized by this D0 report.
