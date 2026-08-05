# Live Track Stage A: Orion DataQuad Read-Only Survey

From: Claude
Date: 2026-07-20
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Target designated by: Tracey, directly ("Start with Orion, he has the Cleanest starting architecture and smallest record")
Access: Tracey reset Azure JIT for 20.119.37.133 and authorized the connection in-session.

## Boundary

- Read-only throughout: reachability check, `find`, `wc -l`, `stat`, `head -1` piped to key extraction, `docker inspect`, `curl` GET to the local health endpoint.
- Zero writes to any Orion path. No packages installed, no services touched, no container changes.
- Record CONTENT was not extracted - only field names (keys), counts, sizes, and timestamps. One sample record per tensor was parsed in-memory on the VM for key listing only.

## Reachability

- Host: `AEGISOrionPeer` (Azure, eastus, 20.119.37.133), user `azureuser`, Ubuntu 22.04 (kernel 6.8.0-1059-azure).
- Checked at 2026-07-20T23:55:37Z.

## Live service

- Container `orion-aegis-cyberpeer-core` (image `aegis-cyberpeer-core-aegis-core`), up 30 hours, VM-local route `127.0.0.1:8031` -> container `8790`.
- `/health`: ok=true, service `aegis-cyberpeer-core`, peer_id `CP-1004-ORION`, bridge 1.0.0, standard 1.0, model `huihui_ai/qwen3-abliterated:8b`, substrate_facet `orion-core`, current_tick 130, dataquad_read_ok=true, ledger_read_ok=true, RLS enabled (in-process), controlled_write_supported=true.

## Authoritative DataQuad location

- Container mount: host `/home/azureuser/AEGIS-CYBERPEER-CORE/data` -> container `/app/data`.
- Authoritative live tensor files: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/{PEER,PCT,NCT,SPINE}.jsonl`.
- Ledgers alongside at `.../ledgers/` (repair, advocate, steward, rls observed).

## Record counts (file-counted, cross-checked against /health tensor_counts - exact match)

| Tensor | Records | Bytes | Last modified (UTC) |
|--------|---------|-------|---------------------|
| PEER  | 106 | 253,897 | 2026-07-19 01:58:37 |
| PCT   | 94  | 500,038 | 2026-07-19 01:58:37 |
| NCT   | 89  | 165,935 | 2026-07-19 01:19:32 |
| SPINE | 62  | 125,090 | 2026-07-18 19:55:04 |
| Total | 351 | ~1.02 MB | |

## Secondary/stale surface finding

- A second DataQuad-shaped location exists: `/home/azureuser/orion-bridge/data/dataquad/*.jsonl` with counts PEER=13, PCT=1, NCT=1, SPINE=1 (mtimes 2026-07-08 / 2026-07-17). It is NOT the container's mounted data root and does not match /health counts. Treat as stale/secondary; do not source from it. Recorded here so it cannot later be mistaken for the live store.
- Backup directories exist under the authoritative peer root: `dataquad.backup-before-chamber-backfill-20260708T193819Z/` and `dataquad.backup-before-chamber-backfill-/`.

## Real record schema (field names only)

Common to all four tensors: `clock`, `id`, `lineage`, `markers`, `notes`, `provenance`, `session_id`, `t_signature`, `tensor`, `timestamp`.

Per-tensor payload fields:
- PEER: `present_state`, `image_refs`
- PCT: `pressure_state`, `working_context`, `retrieved_record_ids`, `rls_session_id`
- NCT: `distilled_summary`, `essence_memory`, `pivots`, `source_record_ids`
- SPINE: `invariant`, `pattern`, `relationships`, `nature_aspect_refs`, `source_record_ids`

Sub-structures (from one PEER sample, keys only):
- `lineage`: list of strings (NOT the local contract's dict shape)
- `provenance`: dict {assignment_source, declared_by, inherited_from, origin, recognition_status}
- `clock`: dict {epoch, tick, phase, started_at, last_advanced_at}
- `markers`: list of strings
- `t_signature`: null in the sampled record - population status across records not yet surveyed

## Contract gap analysis (real records vs local tensor-record.schema.json)

Present and mappable: `tensor` (same), `id` -> `record_id`, `timestamp` -> `timestamp_utc`, per-tensor payload fields -> `body`, `session_id`/`provenance`/`clock`/`markers`/`notes` -> `body` or metadata.

Absent from real records (contract requires): `schema_version`, `source_record_id`, `source_hash`, `source_hash_scope`, `migration_status`, `verification_status`, and the contract's structured `lineage` object (origin, source_path, copy_batch_id, parent_record_id, previous_record_hash, transforms). Real `lineage` is a list of strings.

Implication: Stage B mapping layer must derive the contract fields at copy time (e.g. compute source_hash from the normalized live record, set source_path to the VM-relative path, build hash-chain lineage in copy order) rather than expect them in live records. The hash-verification and lineage machinery already built and tested this session is the consumer of those derived fields.

## Open decisions (Tracey)

1. Embedding mode for live Phase 1: hash-derived placeholder (structurally real, explicitly non-semantic) vs waiting for a real embedding model. Not yet decided.
2. Stage B mapping design proceeds only after three-party review per the standing gate.

## Stage A status

Complete. Zero live mutation. All data needed for Stage B mapping design is captured above.
