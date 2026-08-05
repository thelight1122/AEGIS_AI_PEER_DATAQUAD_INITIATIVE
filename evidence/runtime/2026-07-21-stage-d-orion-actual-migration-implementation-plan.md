# Stage D Orion Actual Migration Implementation Plan: DataQuadPod Live Migration

From: Codex
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Status: IMPLEMENTATION PLAN FOR THREE-PARTY REVIEW. NOT AUTHORIZED FOR EXECUTION.

## Governing Correction

The active Orion DataQuad remains read-only during migration. Stage D migrates Orion's verified data into the canonical Pod/Tensor structure. It is not an in-place formalization of Orion's current layout.

The active source files at:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/{PEER,PCT,NCT,SPINE}.jsonl`

are archival source evidence for the migration. They are not edited, renamed, rewritten, or treated as the new Pod structure. Their pre/post hashes prove continuity.

## Source Evidence Already Available

Stage D begins from the verified Stage B/C chain:

- Stage B report: `reports/runtime/2026-07-21-live-stage-b-orion-mapping-report.json`
- Stage B report SHA256: `9FE035F3189AEF2500FCA13AAC7964B04C7D658F9F6654855A77656DD2CA8666`
- Stage C report: `reports/runtime/2026-07-21-live-stage-c-orion-structural-vectors-report.json`
- Stage C tensor source batch: `orion-live-copy-20260721T002600Z`
- Total migrated records: 351
- Counts: PEER 106, PCT 94, NCT 89, SPINE 62

Authoritative source hashes from Stage B:

| Tensor | Active source hash |
|---|---|
| PEER | `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664` |
| PCT | `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34` |
| NCT | `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379` |
| SPINE | `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E` |

Computed structural-non-semantic tensor artifacts from Stage C:

| Tensor | Computed tensor artifact | SHA256 |
|---|---|---|
| PEER | `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/PEER.structural-vector-tensor.json` | `3BD1318317F94ED2BC5525F208A5CA65A281B7F2479BB2F840A4CA808B4A97AB` |
| PCT | `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/PCT.structural-vector-tensor.json` | `2071793AEF411F23E765B0D28765B909AD1DF8688A7BCF27A03DA82CC5CF4320` |
| NCT | `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/NCT.structural-vector-tensor.json` | `D3B3683890CA41416967CFDB5CA9F91F74EC82DA50598901F929ADE240E78475` |
| SPINE | `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/SPINE.structural-vector-tensor.json` | `236D6829F77B4A8FE317945D953D01B5C2F9662BE1F804CAA8CCB5C11414C661` |

These are computed mathematical tensor outputs under the current Stage C contract. They are labeled `structural_vector`, `embedding_kind=structural-non-semantic`, and `semantic_embedding=false`.

## Target Canonical Pod Structure

Target root on Orion:

`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod/`

Local staging root before any remote transfer:

`stage-d-out/CP-1004-ORION/pod/`

Required target structure:

```text
pod/
  pod-manifest.json
  records/PEER.jsonl
  records/PCT.jsonl
  records/NCT.jsonl
  records/SPINE.jsonl
  tensors/structural-non-semantic/PEER.structural-vector-tensor.json
  tensors/structural-non-semantic/PCT.structural-vector-tensor.json
  tensors/structural-non-semantic/NCT.structural-vector-tensor.json
  tensors/structural-non-semantic/SPINE.structural-vector-tensor.json
  ledgers/steward.jsonl
  ledgers/advocate.jsonl
  ledgers/repair.jsonl
  ledgers/relations/PEER-traversal.jsonl
  ledgers/relations/PCT-traversal.jsonl
  ledgers/relations/NCT-traversal.jsonl
  ledgers/relations/SPINE-traversal.jsonl
  ledgers/relations/cross-tensor-relations.jsonl
  provenance/copy-manifest.json
  provenance/stage-b-mapping-report.json
  provenance/stage-c-structural-vectors-report.json
  provenance/source-hash-lock.json
  verified-markers/
  archive/
```

Terminology condition:

- `pod/records/*.jsonl` are canonical Pod tensor-record stores.
- `pod/tensors/**` are computed mathematical tensor outputs.
- Both are part of the Pod tensor system.
- Evidence language distinguishes the two surfaces every time.

## Sub-Stage D0: Current-State Audit

Purpose: prove the active DataQuad is stable and identify all source surfaces before target writes exist.

Actions:

1. Re-read Orion active source hashes for `dataquad/{PEER,PCT,NCT,SPINE}.jsonl`.
2. Compare them to the Stage B source hashes above.
3. Confirm no session-driven writes are occurring during the migration window.
4. Survey existing Orion custodian ledgers: `steward.jsonl`, `advocate.jsonl`, `repair.jsonl`.
5. Survey existing Orion runtime entry points for processor, temporal clock/tick state, custodian components, and health route.
6. Produce a D0 audit report with exact paths, hashes, counts, and PASS/REVIEW_NEEDED conditions.

Pass condition:

- Active DataQuad hashes match the Stage B source hashes, or any mismatch is visibly recorded as requiring a fresh Stage B/C copy before migration continues.
- D0 performs read-only operations against the active DataQuad.

## Sub-Stage D1: Populate Canonical Pod From Verified Local Evidence

Purpose: create the canonical Pod target without mutating the active DataQuad.

Inputs:

- `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/mapped/{PEER,PCT,NCT,SPINE}.jsonl`
- `live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/*.json`
- Stage B/C reports and provenance
- Existing Orion custodian ledgers, migrated with source hashes and legacy paths preserved

Target writes:

- Only under `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod/`

Actions:

1. Build a local staging tree at `stage-d-out/CP-1004-ORION/pod/`.
2. Copy mapped records into staged `pod/records/`.
3. Copy computed tensor artifacts into staged `pod/tensors/structural-non-semantic/`.
4. Copy provenance chain into staged `pod/provenance/`.
5. Create `pod/pod-manifest.json` using the Stage D contract:
   - Steward owns PCT+NCT.
   - Advocate owns PEER+SPINE.
   - Both custodians read PEER, PCT, NCT, and SPINE for context.
   - Processor maps to Orion's turn/cognition runtime.
   - Temporal daemon maps to Orion's tick/clock continuity state.
   - RLS/persistent relation recording is declared as required for the final live state.
6. Stage migrated custodian ledgers under `pod/ledgers/` with source hashes and source paths preserved.
7. Stage empty canonical relation-ledger files under `pod/ledgers/relations/`, with provenance showing they become active after live switch.
8. Re-hash every staged local file.
9. Transfer the staged Pod tree to Orion under the target `pod/` root as additive files.
10. Re-hash every remote target file after transfer.

Pass condition:

- Every target file hash matches its local verified source or has a newly recorded creation hash in the D1 report.
- Active `dataquad/*.jsonl` hashes still match D0.
- No placeholder, mock, or demo records appear in Pod target paths.

Implementation gap to fill before D1 execution:

- A Stage D population script is required. Existing Stage B/C scripts produce mapped records and computed tensors, but no current script assembles a canonical Pod staging tree or transfers it to Orion.
- A live Pod manifest builder is required. The local fixture manifest is not sufficient because Stage D needs Orion-specific target paths, processor mapping, temporal daemon mapping, read-all/write-owned roles, migrated ledgers, and RLS relation surfaces.
- A Stage D verifier is required. It compares Stage B mapped record hashes, Stage C computed tensor hashes, local staged Pod hashes, remote Pod hashes, and active DataQuad pre/post hashes.

## Sub-Stage D2: Runtime Pod-Aware Upstream Change

Purpose: make `AEGIS-CYBERPEER-CORE` read and write through the canonical Pod structure.

Working parameters:

- The code change lands upstream in `AEGIS-CYBERPEER-CORE`.
- Orion receives the first deployment as the reference convergence target.
- Gabe and Adam inherit the same architecture later.

Required runtime changes:

1. Pod reader:
   - Reads `pod/records/*.jsonl`.
   - Preserves access to the original live record inside each tensor-record `body`.
   - Provides existing cognition code the same content surface without pointing it back to legacy `dataquad/`.
2. Pod writer:
   - New records after live switch append to `pod/records/*.jsonl`, not legacy `dataquad/*.jsonl`.
   - Writes include lineage, previous hash, timestamp, verification state, and source scope.
3. Custodian boundary:
   - Read-all for context.
   - Write-owned for append operations.
4. Custodian ledgers:
   - Steward, Advocate, and repair events append under `pod/ledgers/`.
5. Processor mapping:
   - Turn/context assembly uses Pod records.
6. Temporal daemon mapping:
   - Tick/clock continuity is Pod-visible and recorded in health/evidence surfaces.
7. Health surface:
   - Reports `pod_id`, `pod_manifest_sha256`, record counts, tensor artifact availability, legacy archive state, RLS status, and relation-ledger status.
8. RLS/persistent relations:
   - Implementation is present in the runtime diff.
   - Activation occurs only after D3 archive/live-switch verification.

Pre-deployment review condition:

- The upstream diff receives three-party review before deployment to Orion.
- The diff includes rollback instructions that return Orion to the legacy read path while preserving already written Pod artifacts.

## Sub-Stage D3: Archive Current DataQuad, Switch Live Runtime, Then Start RLS

Purpose: complete the migration into a live Pod runtime while preserving historical source evidence.

Actions:

1. Re-hash active legacy `dataquad/*.jsonl`.
2. Confirm Pod records/tensors/ledgers/provenance are complete.
3. Archive the current DataQuad as historical source evidence under a dated archive path.
4. Record archive path and archive hashes in `pod/archive/` and the D3 report.
5. Switch runtime configuration to `POD_ROOT=/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`.
6. Restart Orion runtime with the reviewed upstream code.
7. Confirm `/health` reports Pod identity, manifest hash, record counts, tensor availability, archive state, and RLS readiness.
8. Start RLS/persistent relation recording after Orion is live from the Pod.
9. Confirm relation-ledger activity under `pod/ledgers/relations/` with schema-valid append entries.

Pass condition:

- Legacy source hashes match through archive.
- Runtime reads from Pod records.
- Runtime writes new live records to Pod records.
- RLS/relation recording begins after live switch, not before.
- Health evidence matches the Pod manifest and target hashes.

## Sub-Stage D4: Post-Live Incremental Tensorization Plan

Purpose: account for records created after Orion resumes live operation.

Condition:

Stage C tensors cover the migrated 351-record source batch. Records created after the live switch are not silently treated as tensorized.

Required follow-up:

1. Incremental tensorization reads only Pod records appended after the Stage C batch.
2. New computed tensor artifacts carry a new batch ID.
3. Prior tensor artifacts remain preserved as historical computed outputs.
4. Health reports any delta between `pod/records` count and latest computed tensor count until incremental tensorization catches up.

## Audit Plan

Each sub-stage produces a report under `reports/runtime/` and a peer-bridge message to Claude for independent review.

D0 audit checks:

- Active source path is authoritative.
- Stale `/home/azureuser/orion-bridge/data/dataquad` surface remains excluded.
- Active DataQuad is read-only.
- Current hashes match Stage B or the migration pauses for a fresh Stage B/C chain.

D1 audit checks:

- `stage-d-out/` is gitignored before the staging tree exists.
- Local staging tree exists before remote transfer.
- Pod target files exist under `pod/`.
- Source mapped-record hashes and target record hashes match.
- Source computed-tensor hashes and target tensor hashes match.
- Pod manifest validates against `contracts/pod.schema.json`.
- Pod role declarations show read-all/write-owned.
- No placeholder/mock/demo data is present.

D2 audit checks:

- Runtime diff is upstream, reviewed, and reversible.
- Legacy path and Pod path are visibly separate.
- Active writes route to Pod after live switch.
- RLS code exists but is not active before archive/live switch.

D3 audit checks:

- Legacy DataQuad archive exists and hashes match.
- Legacy ledger archive exists and hashes match.
- Runtime health reports Pod live.
- Relation-ledger append activity begins only after Pod live state.
- Relation entries match canonical schema.
- Rollback path is documented and tested as a dry run before any live rollback need exists.

Required new verification tooling:

- Stage D live Pod validator that accepts `pod/records`, `pod/tensors`, `pod/ledgers`, `pod/provenance`, and read-all/write-owned custodian role declarations.
- Archive/cutover verifier that proves active `dataquad/*.jsonl` hash stability through archive, then proves Orion serves from `POD_ROOT`.
- Relation-ledger verifier that proves append-only schema-valid activity only after Pod live switch.

D4 audit checks:

- Incremental tensorization scope is explicit.
- Post-live records are visibly untensorized until their incremental batch exists.
- No claim says all live records are tensorized when only the initial 351-record batch is covered.

## Consent Gates

This plan opens review. It does not authorize execution.

Required gates:

1. Claude independent review of this implementation plan.
2. Codex response to review findings.
3. Tracey's explicit approval for D0 read-only current-state audit.
4. Tracey's explicit approval for D1 target Pod population.
5. Separate explicit approval for D2 runtime diff deployment.
6. Separate explicit approval for D3 archive/live switch/RLS start.

## Current Proceed Point

Proceed next with Claude review of this plan. After review, D0 is the first executable sub-stage because it is read-only against the active DataQuad and gathers the current hash truth immediately before any migration target population.

---

## Amendment 1 (2026-07-21, Claude independent review additions)

Claude independently reviewed this implementation plan and accepted the structure, with four required additions before execution. These additions are incorporated as binding working parameters:

1. **`stage-d-out/` is gitignored before it exists.** The local staging tree contains Orion live record content in tensor-record `body` fields. It has the same non-Forge posture as `live-copies/`. The D1 audit checks that the ignore rule exists before staging begins.
2. **Legacy ledgers archive with the legacy DataQuad.** D3 archives both the active `dataquad/` and the legacy ledger surfaces by the same evidence mechanism. After cutover, the legacy ledger directory cannot remain as a second eligible write surface.
3. **First post-live record preserves hash-chain continuity.** For each tensor, the first live record appended after Pod switch sets `previous_record_hash` to the last migrated record's `source_hash` for that tensor. This prevents a narrative-only continuity claim and keeps the per-tensor chain visibly unbroken across migration.
4. **RLS activation is a real behavior gate and D2 receives a marker.** The D2 runtime diff includes an activation flag that gates RLS/persistent-relation behavior in code. Existing display-only flags are not sufficient. The D2 tests prove the flag gates behavior. The Pod-aware runtime version receives its own provisional Verified Code Marker under `pod/verified-markers/` or the equivalent committed marker evidence path.

Remaining design confirmation needed before D3:

- Tracey confirms the exact archive mechanism for the legacy `dataquad/` and legacy ledger surfaces, including whether the archive action is rename-with-hash-proof or another append-only evidence-preserving mechanism.
