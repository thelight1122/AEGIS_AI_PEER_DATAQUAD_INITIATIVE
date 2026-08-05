# Step 9 — RLS Persistent-Relations Orb: Local Build + Test Evidence

Date: 2026-07-21

Workspace: `H:\AEGIS-POD-ARCHITECTURE` (contracts) + `I:\AEGIS-CYBERPEER-CORE` branch `rls-orb-instrumentation` (implementation)

## Boundary

- Local contracts, local code, local tests only.
- No live Orion mutation, no restart, no `.env` change.
- Nothing pushed to any Forge; branch stays local.

## What was built

1. `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-core.orb.json` — real Orb declaration, `trust_state: draft`.
2. `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-umbilical.json` — real Umbilical, `trust_state: draft`, linking `pod_id: dataquadpod-CP-1004-ORION` to `orb_id: rls-persistent-relations-core` at the exact path already forward-declared in `pod-manifest.json`.
3. `scripts/validate_live_orb_attachment.py` — new additive validator, three-way cross-checks the above without touching the fixture validator.
4. `I:\AEGIS-CYBERPEER-CORE`, branch `rls-orb-instrumentation` (off `stage-d2-pod-aware-runtime` @ `ff28010`), commit `0aa0a13`:
   - `core/rls/orb_evidence.py` (new) — `RLSOrbEvidenceRecorder.record_invocation()`.
   - `core/rls/engine.py` — wired the recorder call after the existing `record_relation` loop, gated by the same `_pod.is_pod_mode() and _pod.rls_active()` condition (no new flag).
   - `tests/test_rls_engine_pod_relations.py` (new) — drives a real `execute_session` in pod+RLS-active mode.

## Local Verification

Command:

```powershell
python scripts\validate_contracts.py
```

Result: `PASS` (all 9 checks), unchanged — confirms the fixture boundary was not disturbed.

Command:

```powershell
python scripts\validate_live_orb_attachment.py
```

Result:

```text
PASS live Orb, Umbilical, and Pod-manifest three-way link is internally coherent
PASS orb_id=rls-persistent-relations-core pod_id=dataquadpod-CP-1004-ORION umbilical_id=rls-persistent-relations-core-umbilical
ROOT H:\AEGIS-POD-ARCHITECTURE
BOUNDARY live-target contract documents only; live_reach is declared honestly where the underlying code is genuinely deployed, but no live Orion mutation is performed by this validator
```

Command (from `I:\AEGIS-CYBERPEER-CORE`):

```powershell
uv run --with pytest --with pytest-asyncio --with anyio python -m pytest tests/test_rls_engine_pod_relations.py -v -o asyncio_mode=auto
```

Result:

```text
tests/test_rls_engine_pod_relations.py::RLSOrbPodRelationsTest::test_orb_evidence_is_noop_when_rls_inactive PASSED
tests/test_rls_engine_pod_relations.py::RLSOrbPodRelationsTest::test_rls_session_records_cross_tensor_relation_and_orb_evidence PASSED
2 passed in 0.21s
```

Full-suite regression check (same command against `tests/test_rls_engine_pod_relations.py tests/test_pod_runtime.py tests/test_rls_engine.py`): 10/11 passed. The one failure, `test_rls_engine.py::test_rls_engine_failure_is_data`, is **pre-existing and unrelated** — confirmed to fail identically on the unmodified `stage-d2-pod-aware-runtime` baseline (via `git stash`), a module-level STM-cache test-isolation issue (same class as the previously-documented `test_bootstrap_is_idempotent` stale failure), not caused by this work. `test_pod_runtime.py` stayed 7/7 green (zero regressions in the D2 suite).

## File Hashes

- `contracts/orb.schema.json` SHA256 `41BDBD402E5D28E099DA9D83C5114C8BBE011E71A31D1A19C5628B846BE6599E`
- `contracts/umbilical.schema.json` SHA256 `D0222934AE88EC91490838A421526E87F937763DA85C7A687D7F06EA69973421`
- Implementation (concatenation of `engine.py` + `scoring.py` + `relevance.py` + `orb_evidence.py`, snapshotted at `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-core-source-snapshot/`) SHA256 `1975395C7E1BE3C536007751B36865B6FA3EC74064CB17BFDF5BC7FE8D36103E`

## Correction made during this step

The initial design draft proposed `verification.live_reach: true` on the marker to acknowledge the demonstrated code is genuinely deployed live. On review this was imprecise: `live_reach` is used consistently elsewhere in this repo to mean "did this verification act touch live infrastructure" — and this verification ran against a temp Pod (`tempfile.mkdtemp()`), not the actual Orion VM. Corrected to `live_reach: false` for the verification act itself, with a separate explicit note distinguishing "this code targets the live Pod and shares its exact engine.py lineage" from "this verification touched live Orion" (it did not).

## Current state / stopping point

Design, contracts, code, and tests are complete and locally green. Marker build (Step 10) is next. **No file on Orion has been touched.** Deployment remains a distinct future phase — "Stage E: RLS Orb live cutover" — requiring its own proposal and Tracey's explicit go.
