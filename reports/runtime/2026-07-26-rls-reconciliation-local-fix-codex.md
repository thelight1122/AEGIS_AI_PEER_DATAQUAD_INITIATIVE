# RLS Reconciliation - Replay Parity And Foundational Canon Reachability

Date: 2026-07-26
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Scope

Local reconciliation only. No live Gabe deploy, no VM push, no live `/turn`, no DataQuad mutation, and no migration.

This report responds to Claude's RLS audit:

- bounding objective already passed
- two pre-deploy items remained:
  - replay parity
  - foundational-canon reachability for generic canon/identity queries

## Replay Parity

Claude's independent replay used a hand-built `RecordLike` shim and got different counts. The correct parity path is the real CyberPeer Pod loader:

`I:\AEGIS-CYBERPEER-CORE\core\dataquad\ledgers.py::DataQuadStore.read_records()`

That path:

- resolves Pod records via `AEGIS_STORAGE_MODE=pod`
- reads `pod/records/<TENSOR>.jsonl`
- calls `core.dataquad.pod.unwrap(...)`
- validates into concrete models: `PEERRecord`, `PCTRecord`, `NCTRecord`, `SPINERecord`
- preserves the fields RLS scores: `present_state`, `working_context`, `distilled_summary`, `essence_memory`, `pattern`, `clock.tick`, and `tensor`

I added a deterministic replay harness using that same loader path:

`H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\scripts\replay_rls_selection.py`

Hash:

`8873217C7E6B0987DABA955FC52FC8AEA2C3818FA0D8C147C12136F54939C1CF`

The script supports `--peer-root` for the staged live-copy layout and `--data-dir` for a normal `data_dir/peers/<peer>` layout. It uses `DataQuadStore.read_records()` rather than a generic shim.

Independent sidecar agent Boole inspected the parity path read-only and reached the same conclusion: Claude's discrepancy is likely from shim semantics, especially Pod wrapper vs `body` unwrapping and field/tick preservation.

## Foundational Canon Reachability Fix

Claude identified that foundational AXIOM records scored `0.24` for a generic query such as:

`Gabe, briefly name one AEGIS axiom you can recall.`

That was one hair below the `0.25` threshold:

- meaningful overlap on `axiom`: `0.12`
- SPINE source trust: `0.12`
- no recency because foundational records can have tick `0`
- total: `0.24`

Implemented a narrow affordance:

- only applies when there is already meaningful token overlap
- only applies to `SPINE`
- only applies when query terms include a canon-intent term such as `axiom`, `canon`, `canonical`, `identity`, `nature`, or `principle`
- only applies to foundational SPINE IDs: `SPINE:foundation:*`
- weight is `+0.02`

This changes foundational canon `0.24` to `0.26` for generic canon/identity queries without restoring unbounded structural selection.

## Modified Files And Hashes

Extracted Orb package:

- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py`
  - SHA256 `C9B270BD1B9C782465DAC2544E2D8DD36D28475C9DBBC3208BC5C97F87B5680E`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\scripts\replay_rls_selection.py`
  - SHA256 `8873217C7E6B0987DABA955FC52FC8AEA2C3818FA0D8C147C12136F54939C1CF`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_scoring_bounds.py`
  - SHA256 `327E656446BF00593A880EA45753B0C380BA6B119361170508D7D0FADE6A7884`
- `H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_engine_with_fakes.py`
  - SHA256 `300A484C51CAD060AB4826DEAA097B46E0EC3651D67AB57A5A0775E3C985FDA3`

CyberPeer vendored deploy artifact path:

- `I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py`
  - SHA256 `C9B270BD1B9C782465DAC2544E2D8DD36D28475C9DBBC3208BC5C97F87B5680E`
- `I:\AEGIS-CYBERPEER-CORE\tests\test_rls_selection_bounds.py`
  - SHA256 `6DFD78CB2CD386E0BE77301246F89852BBDD924DD712BF5913C7F1B89449B179`

## Tests

Extracted Orb package:

```powershell
$env:PYTHONPATH='H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src;H:\AEGIS-POD-ARCHITECTURE\packages\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m pytest `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_scoring_bounds.py' `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\tests\test_engine_with_fakes.py'
```

Result: `10 passed in 0.17s`

CyberPeer vendored artifact path:

```powershell
$env:PYTHONPATH='I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m pytest `
  tests\test_rls_selection_bounds.py `
  tests\test_g5_pct_writeback_trim.py
```

Result: `5 passed in 1.48s`

Vendored compile:

```powershell
$env:PYTHONPATH='I:\AEGIS-CYBERPEER-CORE\vendor\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' -m py_compile `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\scoring.py `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\engine.py `
  vendor\orb-rls-persistent-relations-core\src\orb_rls_persistent_relations_core\relevance.py
```

Result: pass

## Replay Results

Staged source:

`H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z`

Command:

```powershell
$env:PYTHONPATH='H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src;I:\AEGIS-CYBERPEER-CORE'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\scripts\replay_rls_selection.py' `
  --peer-root 'H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z' `
  --peer-id 'CP-1003-GABE' `
  --query 'Gabe, briefly name one AEGIS axiom you can recall.' `
  --intent recall
```

Result:

- loaded counts: NCT 9,769; PCT 33,123; PEER 35,754; SPINE 12,707
- pre-bound selected: 18
- post-bound selected: 18
- selected tensor counts: SPINE 17, NCT 1
- top selected records are foundational AXIOM SPINE records at `0.260`
- top reason: `Meaningful token match (overlap: 1), SPINE source trust, Foundational canon affordance`

Command:

```powershell
$env:PYTHONPATH='H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\src;I:\AEGIS-CYBERPEER-CORE\vendor\aegis-pod-sdk\src;I:\AEGIS-CYBERPEER-CORE'
& 'I:\AEGIS-CYBERPEER-CORE\.venv\Scripts\python.exe' `
  'H:\AEGIS-POD-ARCHITECTURE\packages\orb-rls-persistent-relations-core\scripts\replay_rls_selection.py' `
  --peer-root 'H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z' `
  --peer-id 'CP-1003-GABE' `
  --query 'Find details about Axiom-15 repair patterns' `
  --intent recall
```

Result:

- loaded counts: NCT 9,769; PCT 33,123; PEER 35,754; SPINE 12,707
- pre-bound selected: 751
- post-bound selected: 64
- overflow rejected by bound: 687
- selected tensor counts after bound: NCT 6, PCT 44, PEER 11, SPINE 3
- top selected: `NCT:foundation:layer2:AXIOM:15-repair`
- top score: `0.440`
- top reason: `Meaningful token match (overlap: 3), NCT recall support`

## Interpretation

Replay parity is now inspectable through the real loader path. The previous 1 and 731 counts came from an implicit replay harness before the foundational affordance was added. The current explicit harness shows:

- generic canon query reaches foundational AXIOM canon without unbounded selection
- specific Axiom-15 query still preserves the correct top record
- relation edge volume remains bounded by `MAX_SELECTED_REFS = 64`
- unrelated records still do not select through structural bonuses alone

## Boundary

Completed:

- replay harness
- bounded foundational-canon affordance
- extracted Orb tests
- CyberPeer vendored tests
- staged replay

Not completed:

- no deploy
- no VM push
- no live Gabe turn
- no DataQuad write
- no migration

Next step: Claude audit of this reconciliation packet. Live deployment remains a separate Tracey gate.
