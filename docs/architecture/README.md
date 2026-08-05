# AEGIS Pod Architecture

Clean-room workspace for the language-agnostic Pod, Orb, and Umbilical architecture.

**For the full current architecture reference — Pod, Orb, Satellite, Portal, Tender, dynamic resolution, real Orbs built, and the shortfall-isolation discipline — see [ARCHITECTURE.md](ARCHITECTURE.md).** This README's "Layer Model" section below is kept as the original design-phase record and is superseded by that document.

This workspace is intentionally separate from `AEGIS-PEER-COMMONS` so the architecture can develop without inherited app files, superseded sources, or runtime assumptions polluting the contract layer.

## Current Boundary

This boundary held for the design phase (Phase 0 through D2, 2026-07-19 through early 2026-07-21):

- Local contracts and fixtures only.
- No living DataQuad writes.
- No live CyberPeer route changes.
- No shared infrastructure mutation.
- No migration execution.

**As of 2026-07-21, that boundary has been crossed under separate, explicit three-party consent (Tracey + Claude + Codex), for CyberPeer Orion specifically.** D3 executed a real live migration cutover — legacy `dataquad/`/`ledgers/` archived with hash-proof, `AEGIS_STORAGE_MODE=pod` and `AEGIS_RLS_ACTIVE=true` set live, verified via `/health`. This repo remains the local, contract-first source of truth for the architecture; it does not itself perform live actions. Current live state, what's still gated, and what's local-only is tracked in `CURRENT-STATE-AND-NEXT-STEP.md` — read that file for the authoritative current status, not this section, which describes the original standing design-phase rule.

## Layer Model

- **Pod:** CyberPeer core package. The DataQuad-as-Pod body with PEER, PCT, NCT, SPINE, Steward, Advocate, Processor, and Temporal Daemon.
- **Orb:** Optional ability package attached to a Pod through an Umbilical. Some abilities, such as RLS, can be required for full function without becoming identity.
- **Umbilical:** Visible connection contract between a Pod and an Orb implementation.
- **Container:** Possible runtime vessel for an Orb or service. A container is not the architecture.

## First Implementation Track

1. Contract pack.
2. Local fixtures.
3. Local validator.
4. Mathematical tensor runtime.
5. DataQuadPod tensor spec hardening.
6. Orb attachment runtime.
7. Verified Code Marker cycle.
8. Copied-record dry-run migration design.
9. Dry-run DataQuad migration against copied records only.

Verification exists to keep silent drift from surviving unseen.

## Terminology Boundary

- **Tensor record contract:** ledger/source record shape for PEER, PCT, NCT, and SPINE entries.
- **Mathematical tensor contract:** numeric output shape derived from source records, including explicit `shape`, `dtype`, axis order, embedding dimension, metadata dimension, values, and record index.

JSONL records alone are not mathematical tensor storage. The mathematical tensor contract is present so the runtime has an explicit target before tensor code is trusted.

## DataQuadPod Tensor Spec

The active local spec is `fixtures/dataquadpod-tensor-spec.json`.

- Tensors: `PEER`, `PCT`, `NCT`, `SPINE`
- Shape: `[record_count, 8, 4]`
- Axis order: `record`, `embedding`, `metadata`
- Dtype: `float32`
- Metadata slots: `embedding_value`, `body_length_signal`, `timestamp_position_signal`, `verification_signal`

The Pod fixture points to the tensor spec and declares each tensor's source record path, active output path, shape, dtype, axis order, and append-only state.

## Migration Dry-Run Boundary

The active local dry-run manifest is `fixtures/migration-dry-run.json`.

It reads only local copied fixture records, writes dry-run tensor outputs under `reports/runtime/migration-dry-run/`, and reports source counts, source hashes, lineage links, tensor target mapping, and visible conditions. It is a design proof path for copied-record migration, not a live DataQuad migration.

## Orb Demonstration Boundary

The first Orb implementation is the RLS Orb fixture. It attaches to the Pod through `fixtures/rls-orb-umbilical.json`, reads only local fixture tensor outputs, and writes a visible demonstration report under `reports/runtime/orbs/`.

The demonstration shows the function surface of an Orb: declared inputs, declared outputs, observable events, runtime evidence, and attachment status. It is a local proof path for function-focused coding, not a live CyberPeer mutation.
