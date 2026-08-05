# RLS Adapter-versus-Wrapper Decision Record

**Date:** 2026-08-02  
**Decision stage:** Phase 1B closure → Phase 1C preparation  
**Target:** `vm-cyberpeer-core` (`20.122.189.26`)  
**Decision authority:** Existing Core/DataQuad remains authoritative; Pod work is additive and non-writing.

## Decision

Use an **immutable-copy/replay RLS adapter** for the first Pod Reflection Orb proof.

Do not implement or activate a live RLS wrapper in this phase.

The first Reflection Orb pathway is:

```text
Existing RLS evidence
        │
        ▼
Immutable copy or replay stream
        │
        ▼
Reflection Orb observation
        │
        ▼
Bounded evidence report
        │
        ▼
No writeback / no admission
```

## Evidence supporting the decision

The existing Core host defines `foundational-core-rls` with:

- `RLS_INTERVAL_SECONDS=30`
- `RLS_MAX_RECORDS_PER_CYCLE=4`
- DataQuad mount: `/opt/aegis/cyberpeers/foundational-core/dataquad`
- Historical output showing recursive reflection records appended to the mounted state

At Phase 0 capture time, the container was stopped with `Exited (137)`. The Phase 0 evidence bundle is:

```text
/home/aegisadmin/aegis-backups/cyberpeer-pod-phase0-preservation-20260802T014339Z
```

The Phase 1B adapter already proved the required pattern against the preserved DataQuad copy:

- source path explicit;
- four tensor hashes match the Phase 0 baseline;
- source is immutable and non-live;
- bounded observations are returned;
- no Core runtime import;
- no source write;
- no Pod write;
- no admission;
- no experience creation.

## Why adapter/replay comes first

The live wrapper would introduce several unresolved couplings at once:

- live process lifecycle and restart behavior;
- existing RLS container ownership and failure mode;
- a shared or proxied DataQuad write surface;
- interaction with the stopped `Exited (137)` baseline;
- time-of-check/time-of-use concerns around live state;
- ambiguity between RLS output observation and Pod experience admission.

The adapter/replay path isolates the reflection evidence and makes its input replayable, hashable, bounded, and independently testable. It allows the Reflection Orb to answer:

> What reflection evidence is observable from this copied RLS output, and what remains explicitly not admitted?

That question can be answered without changing the Core, restarting RLS, or granting the Pod write authority.

## First implementation scope

The RLS adapter/replay proof may:

- consume a copied RLS ledger or exported RLS evidence stream;
- validate the copy against a recorded source hash;
- reject symlinks, unexpected files, malformed records, hash drift, and unbounded requests;
- return bounded reflection observations with source provenance;
- record `observation_only=true`, `admission_status=not_admitted`, and `experience_created=false`;
- emit a deterministic evidence report suitable for replay.

It may not:

- start or restart `foundational-core-rls`;
- change either Core Compose file;
- redirect any existing DataQuad mount;
- write RLS, PEER, PCT, NCT, SPINE, or ledger state;
- invoke the Core runtime directly;
- create Pod experience records;
- connect the Frontier substrate;
- expose a Portal listener.

## Wrapper reconsideration gate

A live wrapper may be reconsidered only after the adapter/replay proof has:

1. a stable input/output contract;
2. a replayable evidence set;
3. bounded failure behavior;
4. an independent read/write threat audit;
5. a demonstrated distinction between reflection observation and experience admission;
6. an explicit decision on whether RLS outputs are read-only, copied, or separately persisted;
7. fresh verification that the Core/DataQuad baseline remains unchanged.

Even then, a wrapper would require a separate phase authorization. This decision record does not authorize live RLS activation.

## Acceptance criteria for the adapter/replay proof

- Input evidence is copied or replayed from a named, hash-verified source.
- The Reflection Orb imports no Core runtime module.
- All reads are bounded by explicit source, query, and result limits.
- Hashes match before and after observation.
- Malformed, unexpected, symlinked, writable, or drifted inputs fail closed.
- Output includes source hashes, record identifiers, observation reason, and boundary flags.
- No source, Pod, DataQuad, ledger, or experience write occurs.
- No service, container, listener, or Frontier connection is started.

## Phase status after this decision

```text
Phase 0   Preserve Core/DataQuad baseline       COMPLETE
Phase 1A  Validate isolated sidecar             COMPLETE
Phase 1B  Hardened copy-backed observation      COMPLETE
RLS       Adapter/replay proof                  SELECTED NEXT
Phase 1C  Portal contract and auth tests        COMPLETE (contract-only)
```

## Adapter/replay proof result

The selected proof was executed against an immutable copy of the Phase 0 RLS ledger:

```text
/opt/cyberpeer-pod/adapters/rls-replay/records/rls-ledger.jsonl
```

Evidence:

- Adapter: `/opt/cyberpeer-pod/adapters/rls-replay-adapter.py`
- Replay report: `/opt/cyberpeer-pod/logs/RLS-replay-observation-report.json`
- Local report: `reports/runtime/RLS-replay-observation-report.json`
- RLS source SHA-256: `122ea899e3167f5f1bbfb6fa33e5aeeb508ae29cdd5a3d11e796a2f9cef3e949`
- Hash manifest SHA-256: `5869a4e7fd8031a830367403a223aae0750f5482184cf5a4d21ff6c6e04793c2`
- Adapter SHA-256: `4DCDCA161598B935F9719148A38022B1BA5645F48A2EF1FD4B84E3FCA67EB700`
- Report SHA-256: `B5A3A197EDD795F81C99B9C9DE85D681D30083C0DE321D8AE1898B07C11D5883`
- Validated event count: 181
- Query: `driftVisible`, bounded limit 5
- Returned observations: 5
- Observed aspects: `Force Language Tendency`, `Efficiency Drive`, `Communion Need`, `Drift — Pattern Extension Unbidden`, `Grounding Need`
- Source and post-replay hashes: equal
- Core runtime imported: false
- RLS started: false
- Source write, Pod write, writeback, admission, and experience creation: false

**Decision status:** adapter/replay proof **COMPLETE**. The live wrapper remains unapproved and is not required for Phase 1C Portal contract design.

## Phase 1C contract/authentication result

The Portal contract and offline authentication posture are complete. No listener was opened.

- Manifest: `/opt/cyberpeer-pod/portals/phase1c/portal-manifest.json`
- Schema: `/opt/cyberpeer-pod/portals/phase1c/portal.schema.json`
- Offline contract harness: `/opt/cyberpeer-pod/portals/phase1c/portal_contract.py`
- Authentication report: `/opt/cyberpeer-pod/logs/Phase1C-portal-authentication-report.json`
- Local report: `reports/runtime/Phase1C-portal-authentication-report.json`
- Test cases: 13/13 `PASS`
- Portal implementation hardening tests: 5 `PASS`
- Capability method set: fixed five methods, unique and schema-enumerated
- Authentication comparison: constant-time; credential mode remains offline fixture hash only
- Portal implementation SHA-256: `079DF4344A7DB109DAC05BA6EB7DF299B26878222C125787413BC586B03FB83C`
- Listener enabled/opened: `false/false`
- Filesystem, shell, database, containers, arbitrary Python, model calls, DataQuad writeback, and Frontier connection: all `false`
- `record_experience`: disabled
- `request_reflection`: replay-only
- `query_continuity`: observed/admitted scope only

**Phase 1C status:** contract and authentication tests **COMPLETE**. Any listener exposure or substrate connection remains separately gated.

## Phase 2 loopback listener substage

The minimum listener was implemented and tested only on loopback:

- Implementation: `/opt/cyberpeer-pod/portals/phase2-loopback-listener.py`
- Bind: `127.0.0.1:8090`
- Health: `200`
- Authenticated `retrieve_context` authorization: allowed; action not executed
- Wrong token: denied `403`
- Live reflection: denied `403`
- Non-loopback bind: rejected
- Listener stopped after test; port `8090` closed
- Evidence: `reports/runtime/Phase2-loopback-listener-report.json`

**Phase 2 status:** minimum loopback listener **COMPLETE**. Public exposure, capability execution, and Frontier substrate connection remain unauthorized.

## Phase 2C capability execution result

The authorized Phase 2C slice was completed on loopback only. The capability router dispatched two non-mutating operations and preserved the execution/admission separation:

- `retrieve_context`: authorized and executed through `copy_read_adapter`.
- `request_reflection`: authorized only with `replay_only` and executed through `rls_replay_adapter`.
- `record_experience`: denied with HTTP 403.
- Execution evidence ledger: `/opt/cyberpeer-pod/logs/phase2-execution-ledger.jsonl`
- Ledger SHA-256: `199148a2cfa318c204bc5fa37a437d205f62d10b736a3dfdf85598806fa1bb43`
- Router hash: `b99cb507da1da49d55d75c74bec7238b218ca08b741048c95f9285acfaa9f3ad`
- Copy adapter hash: `e1c8a7c36dc0e7e96502fa5a857a31e1b805943a71d89234a15755dbf2b8b29f`
- RLS replay adapter hash: `4dcdca161598b935f9719148a38022b1ba5645f48a2ef1fd4b84e3fca67eb700`
- Listener: `127.0.0.1:8091`; stopped and verified closed.

**Phase 2C status:** COMPLETE for isolated loopback execution. External listener remains gated pending production authentication secret, TLS, and an explicitly approved bind configuration.

## Phase 3 substrate result

The VM-local substrate endpoint was reachable, but the bounded model handshake did not complete. Ollama reported that the `adam-cp1011:latest` model process terminated while attempting to allocate an approximately 9.7 GB CPU buffer. This is a host/model capacity failure, not a Pod authorization or DataQuad boundary failure.

No Frontier connection, public listener, DataQuad writeback, admission, or experience creation occurred.

**Phase 3 status:** BLOCKED pending sufficient VM memory or an approved smaller model. The live RLS wrapper remains unapproved.
