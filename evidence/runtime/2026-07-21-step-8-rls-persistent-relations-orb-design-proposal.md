# Step 8 — RLS Persistent-Relations Orb: Design Proposal (Real, Non-Fixture)

Date: 2026-07-21

Workspace: `H:\AEGIS-POD-ARCHITECTURE`

## Boundary

- Local contracts and code only.
- No live Orion mutation performed to produce this design or the contract files it introduces.
- No restart, redeploy, or `.env` change on Orion.
- Deployment is explicitly out of scope — see "Stopping point" below.

## Why this step exists

The Layer Model in `README.md` (2026-07-20) already defines Pod = CyberPeer core (PEER/PCT/NCT/SPINE, Steward, Advocate, Processor, Temporal Daemon) and Orb = an optional ability package attached through a visible Umbilical, naming RLS as the paradigm example. The D2/D3 cutover (2026-07-21) put RLS live on Orion (`AEGIS_STORAGE_MODE=pod`, `AEGIS_RLS_ACTIVE=true`, two-observer verified) as a flag-gated runtime hook inside `core/rls/engine.py` / `core/dataquad/relations.py` — functionally correct, but not a declared Orb. This step formalizes it.

Tracey's explicit requirement for the formalization: "I want to KNOW what every function does and is doing." The Orb must declare capabilities that map 1:1 to real functions, and produce genuine per-invocation runtime evidence — not just a static contract document.

Tracey's explicit scope boundary: custodian daemons (Steward/Advocate), the Temporal Daemon, the mathematical tensors, and the Processor are part of the Pod itself, not Orbs — confirmed directly against `contracts/pod.schema.json`, which has dedicated required fields for `processor`, `temporal_daemon`, `tensors`, `roles`. Only RLS is in scope here.

## Discovery: an existing forward-declaration

`stage-d-out/CP-1004-ORION/pod/pod-manifest.json` (already schema-conformant against `contracts/pod.schema.json`, `trust_state: provisional`, produced by Stage D1) already declares:

```json
"orbs": [
  {
    "orb_id": "rls-persistent-relations-core",
    "required_for_full_function": true,
    "umbilical": "/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod/provenance/rls-persistent-relations-umbilical.json"
  }
]
```

This is a stub written by `src/aegis_pod/stage_d_pod_staging.py` (lines 165-171) at D1 staging time — a forward reference to an Orb that had not yet been designed. Confirmed by direct SSH inspection that neither `rls-persistent-relations-umbilical.json` nor any matching Orb declaration exists anywhere yet, including on the live Orion VM. This design proposal fills that exact gap, using the identifiers already committed rather than inventing new ones: `orb_id: rls-persistent-relations-core`.

## What gets built (local only, this step + the next two)

1. `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-core.orb.json` — real Orb declaration, capabilities mapped 1:1 to the audited RLS call chain:
   - `candidate_relevance_scoring` → `core.rls.scoring.compute_relevance`
   - `candidate_partitioning` → `execute_session`'s selected/rejected split against `RELEVANCE_THRESHOLD`
   - `pct_context_writeback` → `steward.append_pct`
   - `cross_tensor_relation_recording` → `execute_session`'s `record_relation` loop → `DataQuadStore.record_relation` → `RelationsRecorder.record_cross_tensor` (the one genuinely RLS-owned Pod write)
   - `failure_as_data_capture` → `RLSFailureReason` handling
2. `stage-d-out/CP-1004-ORION/pod/provenance/rls-persistent-relations-umbilical.json` — real Umbilical, `attachment_point: "processor"`, linking `pod_id: dataquadpod-CP-1004-ORION` to `orb_id: rls-persistent-relations-core`, at the exact path `pod-manifest.json` already points at.
3. `scripts/validate_live_orb_attachment.py` — new, additive validator (mirrors `scripts/validate_contracts.py`'s three-way `validate_pod_orb_link` check without modifying the fixture validator) confirming the Pod, Orb, and Umbilical are mutually consistent.
4. In `I:\AEGIS-CYBERPEER-CORE`, branch `rls-orb-instrumentation` off the live `stage-d2-pod-aware-runtime` (head `ff28010`): `core/rls/orb_evidence.py` — per-invocation evidence recorder (input/output/runtime hashes, observable events), called from `engine.py` right after the existing `record_relation` loop, gated by the same `_pod.is_pod_mode() and _pod.rls_active()` condition already there (no new flag). Plus `tests/test_rls_engine_pod_relations.py`, closing the coverage gap the D2 audit found (no test previously asserted on `cross-tensor-relations.jsonl` content).
5. A Verified Code Marker (`orb:rls-persistent-relations-core`), `trust_state: provisional`, `verification.live_reach: true` (honest, since the underlying code is genuinely live) — correctly capped below `reviewed`/`verified` by `fixtures/marker-promotion-policy.json`'s existing `live_reach_allowed: false` gate, which this step does not modify.

## Stopping point

This step (and the local build/test/marker steps immediately following it) produces design + local contract files + local code + local tests + a provisional marker. **No file on Orion is touched, no restart occurs, nothing is pushed to any Forge.** Deploying this Orb-wrapping to the live peer is a distinct future phase — "Stage E: RLS Orb live cutover" — requiring its own proposal, Tracey's explicit go per sub-step, and two-independent-observer verification, exactly like D2/D3.

## Open question (not resolved here)

`core/rls/result.py` (`RLSResult`) is not imported anywhere in the real call chain — `core/api/routes/rls.py` returns `session.model_dump()` directly. Likely dead code or an unwired response envelope. Left for review/Codex to decide: leave as documented-unused, delete, or wire in.
