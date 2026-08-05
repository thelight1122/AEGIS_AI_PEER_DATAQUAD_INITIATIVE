# Stage D1 Remote Population Report - Orion DataQuadPod

Timestamp: 2026-07-21T03:34Z

Peer: CP-1004-ORION

Stage: D1 remote population

Status: PASS

Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

## Consent And Boundary

Tracey authorized continuation of the phase after Orion JIT access was restored.

Claude was notified before remote population:

- Message: `I:\AEGIS-CENTRAL-CODEX\TIER-9-AUDIT-AND-OPERATIONS\exchange\from-codex\2026-07-21T032944Z-d1-remote-population-retry-starting-after-jit-restore.md`
- SHA256: `302984B03741EF2791A70B81090B512D3E1A887A4DEEF852213000100A8DCD3E`

Boundary observed:

- Active Orion DataQuad was read-only for D1.
- Remote write target was only the additive Pod path:
  `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`
- No archive operation was performed.
- No runtime route was changed.
- No service restart occurred.
- No RLS live activation occurred.

## Pre-Transfer Gate

SSH JIT access was restored and verified with `SSH_OK`.

The Pod target was absent before transfer:

- `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`: absent

The active source DataQuad was verified at its direct tensor-file shape under:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad`

Pre-transfer active hashes matched D0:

| Tensor | SHA256 |
| --- | --- |
| PEER | `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664` |
| PCT | `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34` |
| NCT | `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379` |
| SPINE | `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E` |

## Remote Population

The local D1 staged Pod was copied from:

`H:\AEGIS-POD-ARCHITECTURE\stage-d-out\CP-1004-ORION\pod`

To:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`

Local staging report:

- Path: `H:\AEGIS-POD-ARCHITECTURE\reports\runtime\2026-07-21-stage-d1-local-staging-report.json`
- SHA256: `CD4C338BD373F2860B326F758AF69F10218BB99A25DE563E52C873A5DD142D6F`

Remote Pod file count:

- 23 files

Placeholder/mock/demo/pending scan:

- PASS: no matching files found in remote Pod.

## Post-Transfer Active DataQuad Verification

Post-transfer active source hashes remained unchanged:

| Tensor | SHA256 |
| --- | --- |
| PEER | `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664` |
| PCT | `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34` |
| NCT | `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379` |
| SPINE | `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E` |

Conclusion: active Orion DataQuad content did not change during D1 remote population.

## Remote Pod Hash Verification

All remote Pod file hashes matched the local staged Pod.

| Pod path | SHA256 |
| --- | --- |
| `ledgers/advocate.jsonl` | `93C6046CECFD9AE82CF688E45C91A9639193BAEBB3B7CE6540332448F4B6A0C7` |
| `ledgers/repair.jsonl` | `B46176ABE6CD46CB1EFFB428A3756A2EA66ED58230C0C391EEAA5BFA51C48BAE` |
| `ledgers/rls.jsonl` | `B63CF9A6AA21F7E16B52380C5EDF7333F0FC49E71FC86CEADBBE711154036815` |
| `ledgers/steward.jsonl` | `492E27CD58589E5449527252957EE1D362CB284DF56D8AB4F771ECFB2A709451` |
| `pod-manifest.json` | `10F07DC27813930269B04135D9DAFD6A868E5D7CAB5B5C179BD6175695659806` |
| `provenance/copy-manifest.json` | `DE2D1880ED8FFA422EEF910EE6889EAE8AF4DBF049CE71E3156132C87618F873` |
| `provenance/dataquadpod-tensor-spec.json` | `DC678CD5772BACD9DC8618E27683E44AF941E66CAE31249AE1866DF91808FA31` |
| `provenance/source-hash-lock.json` | `CC489418CB54E1EBC428DD3BD4823B2E98B7C6ADDB872124496D674F87AAB731` |
| `provenance/stage-b-mapping-report.json` | `9FE035F3189AEF2500FCA13AAC7964B04C7D658F9F6654855A77656DD2CA8666` |
| `provenance/stage-c-structural-vectors-report.json` | `6AA9C19EC59CB3C81289121BB73E0DC1183C73FE0056E47037FFD2CFD6135C33` |
| `records/PEER.jsonl` | `B44D2B24CEEE2BB563D65F1938138832D7379A21456CB29195B4C5258B551E9B` |
| `records/PCT.jsonl` | `F8016D89781FBB1D27780EDCED94EB8EB6EE07772D3C6F80BC01DEFC470FFDE0` |
| `records/NCT.jsonl` | `FD985D1281C8632F9C3F91DB0CCF5E686FC99585D7E15E5FB7C3A798B9ECF387` |
| `records/SPINE.jsonl` | `7C4B1932E600B4811D8EA365C7429F02FF7E63FB9620A1DDCC0A80229A71F7C7` |
| `tensors/structural-non-semantic/PEER.structural-vector-tensor.json` | `3BD1318317F94ED2BC5525F208A5CA65A281B7F2479BB2F840A4CA808B4A97AB` |
| `tensors/structural-non-semantic/PCT.structural-vector-tensor.json` | `2071793AEF411F23E765B0D28765B909AD1DF8688A7BCF27A03DA82CC5CF4320` |
| `tensors/structural-non-semantic/NCT.structural-vector-tensor.json` | `D3B3683890CA41416967CFDB5CA9F91F74EC82DA50598901F929ADE240E78475` |
| `tensors/structural-non-semantic/SPINE.structural-vector-tensor.json` | `236D6829F77B4A8FE317945D953D01B5C2F9662BE1F804CAA8CCB5C11414C661` |

## Relation Ledgers

Relation ledgers are present and explicitly empty. Each has the zero-record SHA256:

`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`

Files:

- `ledgers/relations/PEER-traversal.jsonl`
- `ledgers/relations/PCT-traversal.jsonl`
- `ledgers/relations/NCT-traversal.jsonl`
- `ledgers/relations/SPINE-traversal.jsonl`
- `ledgers/relations/cross-tensor-relations.jsonl`

## Result

D1 remote population is complete.

Orion now has a populated additive DataQuadPod at:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`

The legacy active DataQuad remains present and unchanged.

The next eligible phase is D2 runtime Pod-awareness planning/execution, with separate consent before any runtime route change, archive movement, restart, or live RLS activation.
