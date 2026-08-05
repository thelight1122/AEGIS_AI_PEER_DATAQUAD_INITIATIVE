# Phase 1 Implementation Plan — Sidecar Pod Runtime

**Date:** 2026-08-02  
**Target:** `vm-cyberpeer-core` (`20.122.189.26`)  
**Sidecar root:** `/opt/cyberpeer-pod/`  
**Boundary:** additive, isolated, no DataQuad writes

## Objective

Turn the staged contract-first source into an independently inspectable Pod sidecar while preserving the existing CyberPeer Core and DataQuad as the authoritative baseline.

The sidecar must not replace, mount read-write, or silently share the existing DataQuad path:

```text
/opt/aegis/cyberpeers/foundational-core/dataquad/
```

## Current starting point

Phase 0 preservation is complete. The source archive and unchanged hashes are recorded in the companion deployment mapping report.

Phase 1 sidecar staging is complete:

```text
/opt/cyberpeer-pod/
├── pod/source/
├── portals/
├── orbs/
├── satellites/
├── adapters/
└── logs/
```

The sidecar is staged-not-running, has no listener, has no DataQuad copy, and has no registered service or container.

## Phase 1A — Sidecar skeleton closure

Status: **complete**

1. Keep the current directory layout and ownership stable.
2. Add a sidecar-local manifest describing runtime status, source hash record, allowed mounts, and explicit write policy.
3. Add a local validation command that checks the Pod, Orb, and Umbilical schemas without contacting the Core host.
4. Define a future service/container entrypoint, but do not register or start it yet.
5. Require a fail-closed result when a required contract or source hash is missing.

Acceptance:

- All staged source hashes reproduce.
- Schema validation is local-only and passes.
- No process, listener, DataQuad mount, or external endpoint is created.

Phase 1A completion evidence:

- Local validator: `scripts/validate_sidecar_phase1a.py`
- Sidecar manifest: `fixtures/phase1a-sidecar-manifest.json`
- Manifest schema: `contracts/sidecar-manifest.schema.json`
- Validation report: `reports/runtime/Phase1A-validation-report.json`
- Remote manifest: `/opt/cyberpeer-pod/phase1a-manifest.json`
- Remote validation report: `/opt/cyberpeer-pod/Phase1A-validation-report.json`
- Remote validator: `/opt/cyberpeer-pod/phase1a-validator.py`
- Result: Pod, Orb, Umbilical, manifest, hash, no-listener, no-DataQuad-access, and no-write-path checks all `PASS`.

## Phase 1B — Read-only DataQuad adapter

Status: **implemented against the Phase 0 immutable copy; live source remains forbidden**

Create an adapter with one-way flow:

```text
Existing DataQuad
        │
        ▼
Read Adapter
        │
        ▼
Pod Context Layer
```

The adapter must:

- open only an explicitly configured source path;
- use read-only filesystem access or an immutable copied-record set;
- never import or call the existing Core runtime;
- never write to `PEER`, `PCT`, `NCT`, `SPINE`, ledgers, locks, or source state;
- emit source path, source hash, record identifiers, selection reason, and adapter version in evidence;
- reject path traversal, symlink escape, unexpected tensor names, malformed records, and hash drift;
- distinguish source observation from Pod admission;
- avoid treating retrieved records as new experience until an explicit admission step exists.

Preferred first implementation: an offline/copy-backed adapter fixture validated against the Phase 0 archive. A live read-only mount should follow only after the copy-backed behavior is proven.

Acceptance:

- Source and archive hashes remain unchanged.
- A query produces a bounded context package with provenance.
- No write syscall or write-capable mount is present in the adapter path.
- Malformed, drifted, or out-of-bound records fail closed.

Phase 1B completion evidence:

- Adapter: `src/aegis_pod/copy_read_adapter.py`
- Tests: `tests/test_copy_read_adapter.py` — 2 passed, 1 POSIX-only permission test skipped on Windows
- Remote adapter: `/opt/cyberpeer-pod/adapters/phase1b-copy-read-adapter.py`
- Immutable copy: `/opt/cyberpeer-pod/adapters/phase1b/records/`
- Expected hashes: `/opt/cyberpeer-pod/adapters/phase1b/expected-sha256.txt`
- Remote observation report: `/opt/cyberpeer-pod/logs/Phase1B-observation-report.json`
- Local observation report: `reports/runtime/Phase1B-observation-report.json`
- Read-boundary audit: `reports/runtime/Phase1B-read-boundary-audit.json`
- Observation report SHA-256 after hardening: `CD89C38A022CEC3DE611BB976BDE104E8DA7AB3BAD2500A471AEFDC5CA96BFBC`
- Result: four tensor hashes matched Phase 0; pre/post tensor and manifest hashes matched; 5 bounded observations returned; admission and experience creation remained false.
- Hardening: source-root symlink rejection occurs before resolution; source and hash manifest are constrained to the approved sidecar root; pre/post observation hashes detect mutation during the read.

## RLS integration decision gate

The existing `foundational-core-rls` behavior must be treated as an observed subsystem, not recreated prematurely.

Two options require explicit comparison:

| Option | Description | Initial posture |
|---|---|---|
| RLS wrapper | Pod Reflection Orb invokes the existing RLS interface through a narrowly scoped adapter | Preferred if the existing loop can expose a stable read/observation contract without sharing write state |
| RLS adapter | Pod Reflection Orb consumes copied RLS outputs or a replayable evidence stream | Preferred for first live proof if the existing loop has no safe interface |

The first implementation must not start the stopped RLS container, change its Compose file, or redirect its DataQuad mount. The decision should be based on an offline replay/copy contract and an explicit write-boundary review.

## Phase 1C — Portal contract

Status: **COMPLETE; contract and authentication hardened; no listener by default**

Define the Portal before exposing any listener:

- `retrieve_context()` — read-only retrieval from the Pod context layer;
- `query_continuity()` — historical pattern retrieval from admitted records;
- `retrieve_canon()` — bounded Nature/Canon access;
- `record_experience()` — initially disabled or copy-only until writeback authorization;
- `request_reflection()` — initially disabled or offline/replay-only until the RLS gate closes.

Every method requires:

- authenticated caller identity;
- capability allowlist check;
- input schema validation;
- output schema validation;
- timeout and bounded result size;
- evidence record containing request ID, source hashes, method, decision, and outcome.

The Portal must not expose filesystem, database, container, VM shell, arbitrary Python import, or unrestricted model access.

Acceptance:

- Contract tests pass without a listener.
- Unauthorized methods fail closed.
- No external endpoint is opened until the isolated Portal test suite passes.

## Explicit non-goals for Phase 1

- No existing DataQuad migration or replacement.
- No DataQuad writeback.
- No live RLS restart or reconfiguration.
- No Frontier substrate connection.
- No identity injection or prompt modification.
- No public or externally reachable Portal listener.

## Required evidence before Phase 2

1. Sidecar manifest and source hashes.
2. Phase 0 archive hash reference.
3. Offline read-adapter test report.
4. Read-boundary threat/path audit.
5. RLS wrapper-versus-adapter decision record.
6. Portal contract and authentication test report.
7. Fresh verification that the existing Core/DataQuad hashes remain unchanged.

## Decision

Phase 1B is closed. The immutable-copy/replay RLS adapter proof is complete. Proceed with the Phase 1C Portal contract and authentication tests. The live RLS wrapper remains unapproved.

Phase 1C contract/authentication work is now complete. The Portal remains contract-only and has no listener.

Phase 2 minimum listener substage is complete as a bounded loopback test. The listener was bound only to `127.0.0.1`, stopped after verification, and performed authorization only; no capability execution or substrate connection occurred.

## Phase 2C — Isolated capability execution proof

Status: **COMPLETE on loopback; external exposure remains gated**

- Router: `src/aegis_pod/capability_router.py`
- Evidence writer: `src/aegis_pod/execution_ledger.py`
- VM listener: `/opt/cyberpeer-pod/portals/phase2/portal_listener.py`
- Execution ledger: `/opt/cyberpeer-pod/logs/phase2-execution-ledger.jsonl`
- Ledger SHA-256: `199148a2cfa318c204bc5fa37a437d205f62d10b736a3dfdf85598806fa1bb43`
- Authorized `retrieve_context`: executed through the copy-backed adapter; source hashes remained equal.
- Authorized `request_reflection`: executed in `replay_only` mode; 181 events validated and bounded observations returned.
- `record_experience`: rejected with HTTP 403.
- Provenance: request ID, router hash, adapter hash, source hash, result hash, mutation, admission, and experience flags recorded.
- Listener bind: `127.0.0.1:8091` only; stopped after test; port confirmed closed.

## Phase 3 — Substrate handshake

Status: **BLOCKED at model-load handshake; no Pod or external state changed**

- VM Ollama was reachable on `127.0.0.1:11434`.
- Available model endpoint included `adam-cp1011:latest`.
- Bounded `READY` probe returned HTTP 500 because the model process could not allocate its CPU buffer; the reported allocation attempt was approximately 9.7 GB.
- No model turn completed, no Frontier connection was established, and no listener was exposed publicly.
- Resolution required before retry: provide sufficient VM memory or an approved smaller model, then repeat the same bounded probe.
