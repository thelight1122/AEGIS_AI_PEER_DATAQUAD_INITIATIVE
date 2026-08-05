# RLS Unbounded Selection - Local Fix

Date: 2026-07-25
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Scope

Local implementation only. No live Gabe deploy, no VM push, no Part B, and no existing-record migration.

Claude asked for root-cause diagnosis before fixing the unbounded RLS selection. This report covers the diagnosis, local fix, tests, and staged-data replay.

## Root Cause

The old RLS scorer allowed tensor/recency bonuses to select records without real grounding:

- `NCT` received `+0.2` for recall intent.
- any record with `clock.tick > 0` received up to `+0.1` recency.
- `SPINE` received `+0.15` invariant/source bonus.
- `PCT` received `+0.05`.
- threshold was `0.25`.

That means:

- NCT recall + recency = `0.3`, so almost every NCT with a tick selected with zero textual match.
- SPINE source + recency = `0.25`, so almost every SPINE with a tick selected with zero textual match.
- PCT generic token + recency + PCT bonus = `0.25`, so one generic overlap could select.
- There was no post-ranking bound; all selected refs became relation edges.

Real staged Gabe replay, old scorer, prompt:

`Gabe, briefly name one AEGIS axiom you can recall.`

Old counts:

- PCT selected: 2,951 / 33,123
- NCT selected: 9,739 / 9,769
- PEER selected: 771 / 35,754
- SPINE selected: 12,629 / 12,707
- total selected: 26,090

Dominant old reasons:

- 12,526 SPINE records selected from `Recency bonus (+0.100), SPINE invariant bonus`
- 8,836 NCT records selected from `NCT priority for recall intent, Recency bonus (+0.100)`

So the live 26,090 selection was not a meaningful retrieval event. It was structural over-selection.

## Fix

Implemented in the extracted Orb package and mirrored into the CyberPeer vendored package.

Scoring changes:

- normalize tokens with regex instead of whitespace split
- remove generic/domain stopwords such as `gabe`, `aegis`, `briefly`, `recall`
- tensor, intent, and recency bonuses now require a meaningful overlap first
- reduced secondary weights:
  - NCT recall support: `+0.08`
  - recency: max `+0.05`
  - SPINE source trust: `+0.12`
  - PCT context support: `+0.03`

Selection changes:

- add `MAX_SELECTED_REFS = 64`
- sort selected refs by descending relevance
- keep top 64
- move overflow selected candidates into `rejected_refs` with reason `outside bounded top 64 relevant refs`
- relation writes therefore cap at selected-ref count

This is not a blind cap alone; it is a scorer fix plus a relevance-ranked bound.

## Staged Data Replay

Staged source:

`H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\pod\records`

Prompt 1:

`Gabe, briefly name one AEGIS axiom you can recall.`

New scorer:

- pre-bound selected total: 1
- post-bound selected total: 1
- selected tensor counts: NCT 1
- top record: `NCT:cyberpeer-gabe-session:rls-promoted:2026-07-07T03:40:51.000Z:10071`
- reason: `Meaningful token match (overlap: 1), NCT recall support, Recency bonus (+0.050)`

Prompt 2:

`Find details about Axiom-15 repair patterns`

New scorer:

- pre-bound selected total: 731
- post-bound selected total: 64
- pre-bound tensor counts:
  - PCT: 90
  - NCT: 52
  - PEER: 550
  - SPINE: 39
- top record: `NCT:foundation:layer2:AXIOM:15-repair`
- top score: `0.44`
- top reason: `Meaningful token match (overlap: 3), NCT recall support`

This preserves retrieval quality for a specific canonical target while bounding the relation-edge volume.

## Modified Files And Hashes

Extracted Orb package:

- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py`
  - SHA256 `C40D574B4BAB8127AFFB1F28160B225AFD2B8ED1A89098A68E5B1BE77DAE0D56`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\engine.py`
  - SHA256 `07480B03FBFE32B76FA3DB9E7ED9CAD7F9AC73968A646A7E7DD5C94F0AACC096`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\relevance.py`
  - SHA256 `BC645D799C28656F6B8124CDD6523917E011F4FBA201FD8DB9B32F1C7A33AE1A`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_scoring_bounds.py`
  - SHA256 `F4313FDF08BABCD9A3896B5F2B05A92CCD96A990DE1C6296CF839C96B728F07D`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_engine_with_fakes.py`
  - SHA256 `300A484C51CAD060AB4826DEAA097B46E0EC3651D67AB57A5A0775E3C985FDA3`

CyberPeer vendored deploy artifact path:

- `I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py`
  - SHA256 `C40D574B4BAB8127AFFB1F28160B225AFD2B8ED1A89098A68E5B1BE77DAE0D56`
- `I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\engine.py`
  - SHA256 `3CA4097C826B8988C05B52680BFFE15F99161E3FA4B6E5623BBDCB9070374B67`
- `I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\relevance.py`
  - SHA256 `BC645D799C28656F6B8124CDD6523917E011F4FBA201FD8DB9B32F1C7A33AE1A`
- `I:\AEGIS-CYBERPEER-CORE\tests\test_rls_selection_bounds.py`
  - SHA256 `6C203787C9EB74A1D87FD503D5A3B6448130E4BFD3FB20B9F37E939B1E388D05`

Note: the extracted Orb engine and CyberPeer vendored engine differ because the vendored engine also contains the previously accepted compact `ledger_dict` fix and the Part A compact PCT writeback changes.

## Tests

Extracted Orb package:

```powershell
$env:PYTHONPATH='H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src;H:\AEGIS-POD-ARCHITECTURE\packages\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m pytest `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_scoring_bounds.py' `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_engine_with_fakes.py'
```

Result: `9 passed in 0.19s`

CyberPeer vendored artifact path:

```powershell
$env:PYTHONPATH='I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m pytest `
  tests\test_rls_selection_bounds.py `
  tests\test_g5_pct_writeback_trim.py
```

Result: `4 passed in 1.65s`

Vendored compile check:

```powershell
$env:PYTHONPATH='I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m py_compile `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\engine.py `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\relevance.py
```

Result: pass.

## Boundary

Completed:

- local diagnosis
- extracted Orb package fix
- CyberPeer vendored artifact fix
- local tests
- staged-data replay

Not completed:

- no live Gabe deploy
- no VM push
- no live `/turn`
- no Part B
- no data migration

Next step: Claude audit. Live deployment remains a separate Tracey gate.
