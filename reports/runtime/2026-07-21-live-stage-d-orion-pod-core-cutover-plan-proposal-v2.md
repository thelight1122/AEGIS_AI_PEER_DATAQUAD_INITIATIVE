# Live Track Stage D PROPOSAL v2: The Pod Becomes Orion's Core - Canonical Migration (FOR THREE-PARTY REVIEW - NOT AUTHORIZED FOR EXECUTION)

From: Claude
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Status: PROPOSAL v2. SUPERSEDES `2026-07-21-live-stage-d-orion-pod-core-cutover-plan-proposal.md` (v1), whose in-place-formalization design Tracey rejected. v1 retained on disk per append-only doctrine; it is not current.

## Architect's correction (Tracey, governing this revision)

v1 proposed building "Pod surfaces around" Orion's existing files. Rejected: "That is not how this works or the structure of every DataQuad would be different and that is what we are attempting to fix and prevent. The data needs to be migrated into the new Tensors. The daemons need to be mapped into the new Pod and the processor."

Consequence: the Pod is THE canonical structure - identical for every peer. Legacy data migrates INTO it. The runtime converges onto the Pod; the Pod never bends to a peer's legacy layout. This is the direct remedy to the Catastrophic Drift ruling (`26f29c1`): one structure, contract-defined, so no peer's DataQuad can silently diverge again.

## The canonical Pod structure (identical for every CyberPeer, per pod.schema.json + dataquadpod-core-tensor-spec-0.1.0)

```
data/peers/<PEER-ID>/pod/
  pod-manifest.json          # conforms to contracts/pod.schema.json
  records/{PEER,PCT,NCT,SPINE}.jsonl   # contract-shaped tensor-record source stores (the migrated data)
  tensors/structural-non-semantic/{...}.structural-vector-tensor.json
  ledgers/steward.jsonl advocate.jsonl repair.jsonl        # custodian ledgers (required)
  ledgers/relations/{PEER,PCT,NCT,SPINE}-traversal.jsonl cross-tensor-relations.jsonl  # persistent relations (required per Gabe evidence + drift ruling)
  provenance/                # copy manifest + mapping report chain, hash-linked to legacy originals
  verified-markers/
```

## The migration (data INTO the new tensors)

Already built and verified: Stage B produced the 351 contract-shaped records (every one hash-linked to its live original, chain-verified); Stage C produced the structural-non-semantic tensors from them. Stage D transfers that verified content into `pod/records/` and `pod/tensors/` on Orion's VM as the Pod's authoritative stores. The legacy `dataquad/` files are never modified - they remain the archival originals every migrated record's source_hash points back to. Append-only doctrine holds; rollback is deletion of `pod/`.

## The mappings (daemons and processor INTO the Pod)

Per the contract and verified against Orion's actual runtime:

| Pod element | Contract purpose | Orion runtime reality | D-stage action |
|---|---|---|---|
| Processor | Context assembly and turn interpretation | the /turn pipeline (core/api/routes/turn.py + cognition/) | pod-manifest declares the processor mapping to this component; runtime reads Pod records for context assembly |
| Temporal Daemon | Time position and continuity awareness | the tick/clock system (current_tick, per-record clock{epoch,tick,phase}) - functionally present, never named | pod-manifest names it and maps it to the tick system; its state becomes Pod-visible |
| Steward | owns PCT+NCT, reads PEER | core/custodians/steward.py (exists, request-driven) | writes to pod/ledgers/steward.jsonl; owns Pod PCT+NCT stores |
| Advocate | owns PEER+SPINE | core/custodians/advocate.py | writes to pod/ledgers/advocate.jsonl; owns Pod PEER+SPINE stores |
| Persistent relations | required capability (drift ruling) | ABSENT on Orion (present only on Gabe) | ledger files created in canonical location; recording implementation is D4+ unless review pulls it in - the STRUCTURE exists now so the function lands in the right place |

## Runtime convergence (the real code work of Stage D)

The runtime currently parses the legacy record schema. Reading from the Pod means the runtime gains a Pod reader: parse contract-shaped records (the live original is intact inside body - existing cognition logic keeps working on exactly the same data), read tensor artifacts, write custodian ledger entries to Pod ledgers, expose pod_id + pod-manifest hash + tensor availability on /health. Applied as a reviewed diff to aegis-cyberpeer-core, deployed reversibly (previous image/config preserved), switched by POD_ROOT config. Rollback: revert config, restart - legacy path untouched throughout.

## Sub-stages, each gated on Tracey's explicit go

- D1: Transfer verified Pod content (records, tensors, provenance, markers) to `pod/` on Orion's VM. Additive writes only; pre/post SHA256 of all four legacy files prove them untouched; transferred files hash-verified against local Pod evidence.
- D2: Pod reader + custodian ledger + health changes to the runtime, as a three-party-reviewed diff BEFORE deployment; deploy reversibly; restart; before/after /health captured.
- D3: Verification - runtime serving from Pod stores; tensor_counts correct from Pod records; legacy hashes unchanged (quiesce held); independent review on the VM by Claude; Codex verification; evidence committed. Then Tracey decides quiesce release.
- D4+ (out of scope, recorded): persistent-relations recording implementation; incremental tensorization of post-release records; Gabe/Adam convergence onto this same canonical structure.

## Unchanged boundaries

Legacy record files never modified. No semantic embeddings. No placeholder/mock/demo data. Every transferred artifact hash-verified. Quiesce (no driven sessions) from D1 start through D3 completion, proven by hashes.

## Open questions for review

1. Custodian ledger MIGRATION: do the existing steward/advocate/repair ledger entries (111/94/19) migrate into pod/ledgers/ (same contract-mapping treatment as records), or do Pod ledgers start fresh with the legacy ledgers archived? v2 recommends migrating them - they are relational history, and "the data needs to be migrated" plausibly includes them. Tracey's call.
2. Does the D2 diff land in the AEGIS-CYBERPEER-CORE upstream repo (so Gabe/Adam convergence inherits it) or as an Orion-local overlay first? v2 recommends upstream branch, deployed to Orion first.
3. Persistent-relations recording: structure-now/function-D4 as proposed, or pull the recording implementation into D2's diff?

Awaiting review: Tracey, Codex.

---

## Amendment 1 (2026-07-21, from Codex's review `...010203Z`, accepted by Claude - appended per append-only doctrine)

1. **Terminology precision, binding for all Stage D evidence**: `pod/records/*.jsonl` are the canonical Pod TENSOR-RECORD STORES (contract: tensor-record.schema.json) - the migrated data. `pod/tensors/...` are the COMPUTED MATHEMATICAL TENSOR OUTPUTS (contract: mathematical-tensor.schema.json) derived from those stores. Both are part of the Pod tensor system; only the latter are mathematical tensor outputs. Tracey's "migrated into the new Tensors" is satisfied by the pair; no evidence may blur the two.

2. **Custodian read scope corrected to read-all / write-owned**: the local fixture's narrow read declarations (Steward reads PEER only; Advocate reads nothing) are stale relative to the intended design already established in the Orion custodian read-boundary repair: BOTH custodians read across all four tensors for context; writes remain limited to owned tensors (Steward writes PCT+NCT; Advocate writes PEER+SPINE). The Orion pod-manifest and the local fixture/contract will encode read-all/write-owned BEFORE D2, so Stage D does not carry the known read-boundary drift forward.

3. Codex's leans on the three open questions are recorded as matching Claude's recommendations: migrate existing custodian ledgers into pod/ledgers/ with source hashes and legacy paths preserved; D2 lands upstream in AEGIS-CYBERPEER-CORE on a reviewed branch deployed to Orion first; relations STRUCTURE in Stage D now, recording behavior in D4 with Stage D evidence visibly stating the function remains absent until D4. Tracey's answers finalize.

---

## Amendment 2 (2026-07-21, Tracey's answers - THE THREE-PARTY DESIGN GATE IS NOW CLOSED)

Tracey, verbatim: "Not a fresh start. You can't rewind time. The runtime changes need to reflect the CyberPeer changes. RLS was always to be implemented and running."

1. **Ledger migration: CONFIRMED.** Existing custodian ledgers (steward 111 / advocate 94 / repair 19 entries) migrate into `pod/ledgers/` with source hashes and legacy paths preserved. History is continuous; time does not rewind.
2. **Upstream: CONFIRMED.** The runtime changes land in AEGIS-CYBERPEER-CORE itself - the CyberPeer core evolves; Orion deploys first as the reference convergence implementation; Gabe/Adam inherit the same code.
3. **RLS and persistent relations: IN STAGE D, IMPLEMENTED AND RUNNING - the deferral option is REJECTED.** "RLS was always to be implemented and running." The D2 runtime diff therefore includes: the persistent relations recording function (traversal + cross-tensor ledgers, writing continuously to pod/ledgers/relations/) AND RLS as an actually-running persistent function, not on-demand-only. Gabe's working recorder (surveyed entry shapes: cross-tensor {id, relation, source, target, t, tags, timestamp, written_by}; traversal {action, append_only, id, record_id, source, tensor, timestamp}) serves as behavioral evidence for the canonical implementation in the core. Stage D completion evidence must show these functions RUNNING on Orion, not merely present.

D2's scope is accordingly larger and its diff review correspondingly stricter. Execution still proceeds only on Tracey's explicit go per sub-stage (D1 transfer -> D2 runtime -> D3 verification).

---

## Amendment 3 (2026-07-21, Tracey's sequencing correction - RLS starts after Pod migration and archive)

Tracey clarified the sequence: RLS begins again when Orion's data has been migrated into the new Tensors, his current DataQuad has been archived, and he is running live from the Pod.

This refines Amendment 2 without changing its governing requirement that RLS and persistent relations are part of the Stage D final live state:

1. **Migration window:** legacy `dataquad/*.jsonl` source files remain quiesced and hash-stable while the Pod is populated and verified.
2. **Archive point:** Orion's current DataQuad is archived after migrated Pod records, computed tensor artifacts, ledgers, provenance, and markers are hash-verified.
3. **Live switch:** Orion runs live from the canonical Pod/Tensor structure after archive verification.
4. **RLS start:** persistent RLS/relation recording starts after the live switch, writing to `pod/ledgers/relations/` as the new running state.
5. **Verification consequence:** D3 first proves migration/archive/live-switch integrity, then proves RLS/relation recording is running from the Pod. Relation-ledger append growth is expected only after the RLS start point, not during the migration/archive window.

---

## Amendment 4 (2026-07-21, Tracey's archive-mechanism confirmation - "confirm now")

Tracey confirmed the archive mechanism proposed by Claude (`...011323Z`) and supported by Codex (`...011513Z`). It is now the governing D3 archive design, superseding the earlier "not renamed, not moved" boundary language from v1/v2, because Tracey's archive directive governs.

**Mechanism (D3, at the live-switch point, after Pod content is fully hash-verified):**

1. `data/peers/CP-1004-ORION/dataquad/` is RENAMED to `data/peers/CP-1004-ORION/dataquad.archive-<UTC>/`. Byte content untouched; all four file SHA256 verified identical across the rename (pre-rename hashes = the D0-locked baselines PEER 6A104DA4.../PCT EDED7B45.../NCT E4CF9278.../SPINE 8D27162F...).
2. `data/peers/CP-1004-ORION/ledgers/` is RENAMED to `data/peers/CP-1004-ORION/ledgers.archive-<UTC>/` at the same moment (its history already migrated into `pod/ledgers/`); the four legacy ledger hashes (steward 492E27CD.../advocate 93C6046C.../repair B46176AB.../rls B63CF9A6...) verified identical across the rename.
3. Both old and new paths, pre/post hashes, the UTC suffix, and the exact rollback command are recorded in `pod/archive/` and the D3 report.
4. Post-rename, exactly ONE live source exists: the Pod. No split-brain where the runtime could silently read a legacy root.
5. Rollback: rename back + config revert; all Pod artifacts preserved (deletion only on Tracey's explicit instruction).

This closes the last open Stage D design item. Execution of the archive remains gated on D3 arrival and Tracey's explicit go; this amendment confirms the mechanism, not its execution timing.
