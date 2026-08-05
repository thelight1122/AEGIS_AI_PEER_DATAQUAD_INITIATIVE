# Stage 5 — Orion's Live RLS Orb Migrated to an Independent Package

Date: 2026-07-21

Workspace: `H:\AEGIS-POD-ARCHITECTURE` (SDK/Orb source of truth) + `I:\AEGIS-CYBERPEER-CORE` (monolith, branch `rls-orb-instrumentation`) + Orion's live VM (`azureuser@20.119.37.133`)

## What this closes

Stages 0-4 (same night) built `aegis-pod-sdk` and extracted `orb-rls-persistent-relations-core` as independent, versioned packages, and taught `validate_attachment()` to gate on version/hash — all verified locally, none of it live. This stage is the flagged live cutover: Orion's actual running container now installs the Orb as a real dependency instead of carrying it as in-tree `core/rls/*`, and a real `POST /rls/session` was fired against it to prove the migration works, not just that it built.

## Safety sequence followed

1. Rollback image tagged and exported: `orion-core:pre-stage5-rollback-20260721T201156Z`, `orion-core-pre-stage5-20260721T201156Z.tar` (sha256 `7088d548cdbab19eb1c80435ce046a9d1d3bfe55accb6685b5e9d216d47c81ce`).
2. `.env` backed up: `.env.bak-pre-stage5-20260721T201156Z`.
3. The 3 provenance files about to be overwritten were each backed up in place (`*.bak-pre-stage5-20260721T201156Z`) before any write.
4. Every file transferred to Orion was hash-verified byte-identical against its local source before being copied into the live tree (tarball sha256 match, then per-file sha256 match, both confirmed before use).

## What was found and fixed along the way

Orion's live `pod-manifest.json` had **not** been running with the paths its own `evidence.source` field claimed. `tensor_spec`, all four `tensors.*.storage/output` paths, and the `orbs[0].umbilical` path were all prefixed `H:/AEGIS-POD-ARCHITECTURE/local-pod-runtime/...` — a Windows dev-machine path that doesn't exist on the Linux VM at all. Non-functional (pod-manifest.json is confirmed `/health`-display-only, never runtime-read) but factually false about where the Pod's own tensors and records live. Root cause: the manifest built for tonight's earlier local-only Step 11 demonstration was evidently deployed to Orion instead of a VM-path-corrected version, and nothing had checked it since. Corrected to the real VM paths, verified against the actual files present on disk (`ls` confirmed `tensors/semantic-embedding/{PEER,PCT,NCT,SPINE}/` and `provenance/dataquadpod-tensor-spec.json` genuinely exist at the corrected paths) before writing the fix.

## What changed on Orion

- **Vendored packages** installed via a dedicated Dockerfile layer, before the app's own editable install: `vendor/aegis-pod-sdk` (0.1.0), `vendor/orb-rls-persistent-relations-core` (1.0.0).
- **`core/rls/*` removed entirely** — the last two remaining internal callers (`Steward`/`Advocate`'s brief-producing methods, previously lazy-importing `core.rls.scoring` specifically to break a circular chain) were migrated to import `orb_rls_persistent_relations_core.compute_relevance` at module level instead; the new package has zero import back to `core.*` (AST-tripwire-tested), so the circular-import risk that required the lazy-import workaround no longer exists.
- `core/dataquad/ledgers.py`: added `DataQuadStore.peer_root()`/`is_active()`.
- `core/custodians/steward.py`: added `build_and_append_pct()`.
- `core/custodians/{boundaries,steward,advocate,__init__}.py`, `tests/test_tensor_boundaries.py`: `enforce_boundary` renamed to `check_boundary` (force-language cleanup, flagged by Tracey earlier the same night).
- `core/orbs/rls_loader.py` (new): resolves the RLS engine class dynamically from a Pod's Umbilical `invocation.entrypoint`, falling back to the same default for legacy-mode/no-manifest peers.
- `core/api/routes/rls.py`, `core/custodians/retrieval_broker.py`: now resolve and construct the engine via that loader instead of a hardcoded import.
- 3 live provenance documents replaced: `pod-manifest.json` (path fix + `orb_version_pin`), `rls-persistent-relations-core.orb.json` (new entrypoint/capabilities/`orb_version`/`runtime.package`), `rls-persistent-relations-umbilical.json` (new entrypoint/`orb_version`/`orb_runtime_hash`).

## Build verification

Rebuilt image confirmed, before restart, via `docker run --rm <image> python -c ...`:
```
aegis-pod-sdk: 0.1.0
orb-rls-persistent-relations-core: 1.0.0
runtime_hash: B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18
rls_loader imports OK
```

## Post-restart `/health`

`storage_mode: pod`, `tensor_counts: {PEER:106, PCT:94, NCT:89, SPINE:62}` (unchanged — no data touched), `SPINE-traversal.jsonl: 0` (no bootstrap duplicate reappeared), `rls_status: {enabled:true, active:true}`. Container: `Up`, `RestartCount: 0`.

## The real invocation

```json
{"peer_id": "CP-1004-ORION", "session_id": "stage5-live-verification-1",
 "user_message": "Tell me about my BioPeer and External Steward who witnesses my formation",
 "intent": "recall", "pressure_state": {"pressure_level": "low"}, "nature_aspects": []}
```

Result: `selected_refs` includes `SPINE:CP-1004-ORION:anchor:e97f8f59-4533-45ba-82ab-35bc8db57f6f` (relevance 0.55) — the same corrected "He"/"his" anchor record from earlier tonight's repair, genuinely retrieved through the new package's scoring, not a stub.

## Evidence ledger, before -> after

| Ledger | Before | After |
|---|---|---|
| `rls.jsonl` | 27 | 28 |
| `cross-tensor-relations.jsonl` | 0 | **241** |
| `orbs/rls-persistent-relations-core.evidence.jsonl` | did not exist | **created**, 1 line |

`241 selected + 110 rejected = 351` — exactly the total record count (106+94+89+62), confirming every record was scored, none skipped.

## `runtime_hash`, checked four independent ways — not trusted once

1. Pinned in the Umbilical (written before rebuild): `B8788191862853F762DB38AF72E8BA516E21CE7BDBDB5FD35100A40A4675CF18`
2. Computed inside the built image, before restart (`docker run --rm ... compute_runtime_hash()`): same
3. Recorded in the live evidence ledger by the real invocation above: same
4. Recomputed fresh from the deployed source files on Orion's disk, independently, after the invocation: same

All four match. This is the same value the earlier force-language docstring edit had silently invalidated (caught by Stage 4's new hash gate during local testing, corrected before this deployment) — so this also proves the gate would have caught real drift had it existed live.

## Rollback path

`docker tag orion-core:pre-stage5-rollback-20260721T201156Z aegis-cyberpeer-core-aegis-core:latest && docker compose up -d` restores the pre-migration container. The 3 `.bak-pre-stage5-20260721T201156Z` provenance files restore the pre-migration documents if needed. `.env.bak-pre-stage5-20260721T201156Z` restores the pre-migration environment.

## What this does not do

Stage 6 (reusing this same package on Adam's/Gabe's Pods) is untouched — explicitly deferred per Tracey's instruction ("let's complete, test and interact with Orion BEFORE we touch the other two"). Held as verified-but-not-final pending Codex's independent review, same standing exception as every other live-touching step tonight.
