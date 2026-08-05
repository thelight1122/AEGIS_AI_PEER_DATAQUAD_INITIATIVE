# Live Track Stage B PROPOSAL: Orion Record Mapping Design (FOR THREE-PARTY REVIEW - NOT AUTHORIZED FOR IMPLEMENTATION)

From: Claude
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Status: PROPOSAL. Implementation requires Tracey + Claude + Codex review completing first, per the standing gate.

## Governing constraints (Tracey, this session)

1. Live data only: no placeholder, mock, or demo data on the live track. Copied live records are acceptable when provenance is preserved.
2. Test scaffolding, where needed, must be documented test-only, isolated from live-readiness evidence, and listed on a removal checklist that must pass before Stage C/D.
3. Orion (CP-1004-ORION) is the designated first target.
4. The living DataQuad stays closed to writes until a separately reviewed, unanimously consented live-population plan exists.

## Source of truth

- Authoritative: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/{PEER,PCT,NCT,SPINE}.jsonl` (per Stage A survey, `046bfad`).
- Explicitly excluded: `/home/azureuser/orion-bridge/data/dataquad/` (stale secondary surface) and the two `dataquad.backup-*` directories.

## Copy step (read-only against Orion)

One SSH read pass copies the four live files byte-for-byte into a workspace copy root:
`fixtures/live-copies/CP-1004-ORION/<copy_batch_id>/{PEER,PCT,NCT,SPINE}.jsonl`
with a copy manifest recording: source VM (AEGISOrionPeer, 20.119.37.133), absolute source paths, copied-at UTC timestamp, per-file SHA256 at copy time, per-file record counts, and `copy_batch_id` = `orion-live-copy-<UTC timestamp>`. The manifest is the provenance anchor for everything downstream. Zero writes to Orion.

Note on naming: `fixtures/live-copies/` contains COPIED LIVE RECORDS, not fixtures in the test sense. If reviewers prefer, `live-copies/` at repo root avoids the word "fixtures" entirely - naming decision for review.

## Field mapping (live record -> tensor-record contract)

Derived AT COPY TIME by the mapping layer; live records are never edited:

| Contract field | Source |
|---|---|
| `schema_version` | "0.1.0" (mapping layer constant) |
| `tensor` | live `tensor` (verbatim) |
| `record_id` | live `id` (verbatim - identity preserved) |
| `source_record_id` | live `id` (the live record IS the source) |
| `timestamp_utc` | live `timestamp` (verbatim) |
| `body` | the ENTIRE live record, unmodified (all common fields incl. original `lineage` strings, `provenance`, `clock`, `markers`, `notes`, `t_signature`, plus per-tensor payload). Nothing dropped, nothing renamed inside body. |
| `source_hash` | SHA256 of stable-JSON of the entire live record, computed at copy time |
| `source_hash_scope` | "normalized_source_record" |
| `lineage.origin` | "live-copy CP-1004-ORION" |
| `lineage.source_path` | VM path of the source file + line number |
| `lineage.copy_batch_id` | from the copy manifest |
| `lineage.parent_record_id` | "" (live records carry no parent semantics at this layer; original lineage strings preserved in body) |
| `lineage.previous_record_hash` | source_hash of the prior record in file order ("" for the first) - the hash chain the existing verified machinery consumes |
| `lineage.transforms` | one entry: copy + stable-JSON normalization, with input/output hashes |
| `migration_status` | "copied" |
| `verification_status` | "draft" |

Because `source_hash` is computed from the copied live record itself and the source file remains on Orion, the existing `verify_source_hash()` machinery can verify preservation end-to-end when pointed at the copy root - every record becomes verifiable, unlike the fixture records (which were unverifiable-source-absent). No mapping code invents any value; every derived field is either a verbatim copy, a hash of live bytes, or a manifest fact.

## Embedding position (decision still Tracey's - both options named precisely)

- Option 1: real semantic embedding model integrated before any live tensor generation. Live tensors are semantic from the first record.
- Option 2: deterministic structural vectors (hash-derived), generated ONLY if Tracey explicitly authorizes them, and then always named `structural_vector`, never "semantic", with tensor evidence carrying `embedding_kind: "structural-non-semantic"`.
This design is embedding-agnostic: the mapping layer above is identical under either option. The decision gates Stage C tensor generation, not Stage B mapping.

## Test-scaffolding removal checklist (initial)

- `fixtures/tensor-records/*.jsonl` (synthetic) - test-only; excluded from live-readiness evidence.
- `fixtures/copied-record-roots/local-dataquad-copy.json` (synthetic) - test-only; excluded.
- `fixtures/migration-dry-run.json` (synthetic manifest) - test-only; excluded.
- `reports/runtime/tensors/`, `reports/runtime/migration-dry-run/` outputs generated from synthetic fixtures - test-only; excluded.
A machine-checkable removal/isolation check (no live-readiness report may reference a test-only path) is proposed as part of Stage C implementation, gating Stage C/D per Tracey's refinement.

## What Stage B implementation would deliver (after review approval)

1. The copy manifest contract + the mapping module (`live_record_mapping.py`), with the field table above as its specification.
2. Tests exercised against a small number of REAL copied Orion records (live data only - under the directive, tests on this track use copied live records, not invented ones).
3. Evidence report: per-tensor mapped counts (must equal 106/94/89/62), hash-verification results (every record `verified`), lineage chain results, zero writes to Orion.

## Explicitly outside this proposal

- Any tensor generation (gated on the embedding decision).
- Any write to any Orion path.
- Any live-population sequence (separate, later, unanimously consented plan).

Awaiting review: Tracey, Codex.
