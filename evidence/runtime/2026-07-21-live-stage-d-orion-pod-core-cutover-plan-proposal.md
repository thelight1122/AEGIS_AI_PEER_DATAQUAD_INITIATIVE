# Live Track Stage D PROPOSAL: The Pod Becomes Orion's Core (FOR THREE-PARTY REVIEW - NOT AUTHORIZED FOR EXECUTION)

From: Claude
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Status: PROPOSAL. Execution requires Tracey + Claude + Codex review completing, then Tracey's explicit go for each execution step. This is the first stage that writes anything to Orion's VM.

## Directive (Tracey, verbatim intent)

"The Pod becomes Orion's Core, his runtime reads from the Pod."

## Governing doctrine

"Pod = DataQuad. Not a container holding a DataQuad - the DataQuad itself is the Pod." Therefore Stage D does NOT replace Orion's data layer. It formalizes his existing, verified DataQuad AS the Pod core, in place, and builds the Pod surfaces around it. The runtime then reads from the Pod because the files it reads ARE the Pod's tensor stores - declared, manifested, tensorized, and marker-verified.

## Why in-place formalization (recommended) over record reformatting

The runtime parses the live record schema (id, tensor, timestamp, lineage-as-strings...). The contract-mapped records wrap that schema inside `body`. Reformatting Orion's records to contract shape would require live parser changes - code risk on a living peer for zero data gain, since the mapped/provenance layer already exists in the local Pod and every record is hash-linked to its live original. In-place formalization requires ZERO changes to existing record files and ZERO parser changes: additive artifacts only, full rollback by deletion of additions.

## Stage D sub-stages (each gated, each with evidence)

### D1 - Pod formation on Orion's VM (additive writes only; first Orion writes of the project)

Create alongside (never inside) the existing tensor files, under `data/peers/CP-1004-ORION/pod/`:

1. `pod-manifest.json` - conforms to `contracts/pod.schema.json`: pod_id for CP-1004-ORION; declares the four EXISTING live JSONL files as the Pod's tensor source stores (by VM path + current SHA256); Steward owns PCT+NCT cross-reads PEER; Advocate owns PEER+SPINE; processor + temporal daemon named per contract; tensor_spec = dataquadpod-core-tensor-spec-0.1.0.
2. `tensors/structural-non-semantic/{PEER,PCT,NCT,SPINE}.structural-vector-tensor.json` - the Stage C tensors, transferred from the local Pod, hash-verified after transfer against the Stage C evidence hashes. Labels intact: embedding_kind=structural-non-semantic.
3. `provenance/` - the copy manifest + mapping report chain (hashes proving tensors derive from these exact records).
4. `verified-markers/` - the provisional markers covering the runtimes that produced the tensors.

Boundary: the four live record files are NOT touched - not renamed, not moved, not edited. A pre/post SHA256 of all four proves it. Rollback: `rm -r pod/` restores the exact prior state.

### D2 - Runtime reads from the Pod (config-level, reversible)

The runtime's dataquad_root already points at the directory containing the four record files, which the Pod manifest now declares as the Pod's tensor stores - so after D1, the runtime is factually reading the Pod's stores. D2 makes it explicit and health-visible:

1. Add Pod identity to the health surface: /health reports pod_id, pod_manifest hash, tensor availability (smallest possible code change, additive endpoint fields; reviewed as a diff before deployment).
2. Config/env gains POD_ROOT pointing at the pod/ directory.
3. Container restart with before/after /health captures.
Rollback: revert config + restart; D1 artifacts are inert if unused.

D2's code diff must be written, reviewed by all three parties, and applied to the container in a way that is itself reversible (image tag or bind-mounted file with the original preserved).

### D3 - Verification and quiesce release

1. Post-cutover hash check: all four record files unchanged from the pre-D1 hashes (quiesce held through the entire operation).
2. /health: ok=true, tensor_counts unchanged (106/94/89/62), Pod identity visible.
3. Independent review by Claude directly on the VM; Codex verification; evidence committed.
4. Tracey decides when to resume driving sessions (quiesce release). New records appended after quiesce release will NOT yet be tensorized - visible as a recorded condition, not a silent gap. Incremental re-tensorization is a subsequent phase (D4+, out of scope here).

## Explicitly outside this proposal

- Any modification of existing DataQuad record files (never in any sub-stage).
- Semantic embeddings (structural-non-semantic only, per Tracey's authorization).
- Persistent-relations / custodian-ledger convergence work (Pod contract requirement recorded from the Gabe evidence; separate phase).
- Gabe or Adam anything.
- Incremental/continuous tensorization of post-cutover records (D4+, needs its own design).

## Open questions for the review

1. D2 health-surface change: minimal additive fields as proposed, or defer any code change and accept D1-only formalization as "reads from the Pod" for this phase?
2. Transfer path for tensors: scp from workstation (same channel as the read-only copies, reversed direction, additive target only) - acceptable?
3. Quiesce: confirm no sessions get driven between D1 start and D3 completion (hash checks will fail the run visibly if violated).

Awaiting review: Tracey, Codex.
