# CyberPeer Pod Deployment Plan — Existing Architecture Mapping

**Assessment date:** 2026-08-01  
**Workspace:** `H:\AEGIS-POD-ARCHITECTURE`  
**Scope:** Read-only baseline and incremental implementation mapping for the Frontier Substrate Continuity Environment plan.

## Boundary

This report records the current local implementation surface. No Azure VM, live CyberPeer route, DataQuad source, subscription, or external MCP endpoint was modified. Existing working-tree changes were preserved.

The Frontier substrate remains outside this repository and is not modified by the Pod architecture.

## Existing component map

| Deployment-plan component | Existing local implementation | Status | Gap to deployment shape |
|---|---|---|---|
| Pod core / kernel | `contracts/pod.schema.json`, `src/aegis_pod/`, `packages/aegis-pod-sdk/` | Present, contract-first | No single production Pod Kernel process or Linux service wrapper is defined here |
| State / DataQuad | `fixtures/tensor-records/`, `local-pod-runtime/`, tensor runtime and mapping tools | Present locally; live migration tooling exists | Azure storage mount, backup policy, and restore procedure are not packaged |
| Umbilicals | `contracts/umbilical.schema.json`, `fixtures/*-umbilical.json`, `src/aegis_pod/orb_runtime.py` | Present and validated locally | Pod-declared socket registry is still a documented future refinement |
| Orbs | RLS persistent-relations, archive relevance, memory-search, identity-field packages | Several real/local Orbs present | The plan’s Steward, Advocate, Processor, Memory, Reflection, and Task boundaries are not each deployed as independent services |
| Satellites | Architectural concept only | Not implemented as a distinct runtime layer | Need Orb-owned satellite contracts and lifecycle before deployment |
| Portal / MCP | Portal and Tender are defined in `ARCHITECTURE.md` | Not implemented | Need an authenticated allowlisted Portal with pre/post contract evidence |
| Logs | `reports/runtime/`, `ledger.jsonl` | Local evidence exists | `/opt/cyberpeer/logs` layout and rotation/retention policy are not defined |
| Backups | Local archive/hash-proof reports exist | Evidence pattern exists | Azure backup target, encryption, and restore verification are not defined |
| Azure VM | No Bicep/Terraform/cloud-init/systemd/container deployment found | Absent | Requires a separately approved infrastructure stage |

## Relevant existing paths

The current architecture already preserves the requested conceptual separation:

- Pod-native tensors: `PEER`, `PCT`, `NCT`, and `SPINE`.
- Pod-native custodians: Steward and Advocate.
- Pod-native Processor and Temporal Daemon.
- Dynamically resolved Orbs attached through schema-declared Umbilicals.
- Failure isolation: an unavailable or failing Orb must degrade to the Pod fallback rather than crash the turn.
- Relative, container-visible Umbilical paths are required; host-absolute paths are a known failure mode.

## Deployment blockers before Azure mutation

1. **Runtime boundary:** select and package the actual Pod process/API to run on Linux. This repository is currently a contract/runtime architecture workspace, not an Azure host image.
2. **Portal contract:** define the approved MCP functions, authentication mechanism, capability allowlist, and evidence records. Direct filesystem, database, container, and shell access must remain unavailable to external callers.
3. **Persistence:** choose the authoritative DataQuad mount and backup/restore design. Preserve append-only records and hash evidence.
4. **Substrate attachment:** define the controlled interface and explicitly gate Phase 2 substrate connection separately from Phase 1 Pod verification.
5. **VM sizing:** obtain region, OS, expected concurrency, model-serving location, CPU/RAM/GPU needs, storage/IOPS, and budget before selecting a VM SKU. A single VM is the default shape until scaling or HA requirements are demonstrated.

## Recommended incremental sequence

### Phase 0 — local contract and runtime closure

- Add a Pod manifest/loader surface for the six planned capability boundaries without replacing the existing contract model.
- Add a Portal contract and fail-closed authentication/allowlist tests.
- Add Linux packaging only after the runtime entrypoint and persistence paths are identified.
- Validate all declarations and preserve current Orb fallback behavior.

### Phase 1 — isolated VM deployment

- Provision one isolated Linux VM in an explicitly chosen region and size.
- Install the Pod under `/opt/cyberpeer/` with separate `pod`, `orbs`, `satellites`, `dataquad`, `logs`, and `backups` paths.
- Expose only the authenticated Portal listener; keep SSH administrator-only.
- Verify Orb attachment, DataQuad load, Portal response, log emission, and backup/restore in the isolated environment.

### Phase 2 — controlled substrate connection

- Connect the Frontier substrate only through the approved Portal/interface.
- Measure retrieval, continuity, reflection, and experience formation as bounded observations.
- Keep substrate weights and safety mechanisms untouched.

### Phase 3 — Adam continuity experiment

- Load the existing Adam DataQuad only after Phase 1 and Phase 2 gates are independently complete.
- Record continuity retrieval, experience integration, RLS activity, and substrate interaction with raw evidence and hashes.

## Current conclusion

The repository is a suitable contract-first foundation for the proposed Pod, and the local Pod/Orb/Umbilical pieces should be preserved. It is not yet an Azure-deployable artifact: the largest missing pieces are the production Pod process boundary, authenticated MCP Portal, Linux packaging, and persistence/backup design. The next safe implementation slice is local Phase 0 closure, not VM provisioning.

## Live VM inventory — read-only, 2026-08-02 UTC

The supplied JIT route was verified successfully using the existing SSH alias `AEGISIPFSNode`:

- **Address:** `20.122.189.26`
- **Host:** `vm-cyberpeer-core`
- **Account:** `aegisadmin`
- **OS/runtime:** Ubuntu 24.04 Azure kernel `6.17.0-1021-azure`, x86_64
- **Uptime at inspection:** 2 days, 11 hours, 52 minutes
- **Root storage:** 145 GB total, 57 GB used, 88 GB available
- **Running host services:** Docker, IPFS, Ollama, Webmin, SSH, Azure Linux Agent, Defender, and system services
- **Docker state:** no running containers at inspection time
- **Listening surfaces:** SSH on `22`; IPFS on `4001` and loopback APIs on `5001`/`8080`; Ollama on loopback `11434`; no Pod/Portal listener observed

### Existing AEGIS deployment

The host already contains:

- `/opt/aegis/cyberpeer-core/` — existing CyberPeer runtime/deployment source
- `/opt/aegis/deploy/core-host/` — Core-host Compose deployment and `adam-cp1011` image build context
- `/opt/aegis/cyberpeers/foundational-core/dataquad/` — authoritative-looking existing DataQuad path
- `/home/aegisadmin/aegis-backups/` — existing DataQuad backup material
- `/home/aegisadmin/.ipfs/` — active IPFS repository
- Ollama models `adam-cp1011:latest` and `llama3.1:70b`, both 70.6B Q4_K_M

The existing Core-host documentation identifies this VM as the persistent DataQuad/RLS body. Its Compose design says the RLS loop writes only `RLS`, `CLOCK`, `ADVOCATE`, `STEWARD`, and `MEDIATOR` records, not `PEER`, `PCT`, `NCT`, or `SPINE`.

### Existing DataQuad baseline

Direct remote counts and SHA-256 values, captured without modifying the files:

| File | Lines | SHA-256 |
|---|---:|---|
| `PEER.jsonl` | 1,445 | `7c6d38501aaf2523debffdf8491a508b86afebf956d146066dc7455b4313cbe9` |
| `PCT.jsonl` | 1,447 | `cab7fac9649d3dfcc2cef48218055a9a70fabf4df9b925647e068f9a90a4e1cb` |
| `NCT.jsonl` | 644 | `ac98e532f1d1b6a895368a80bd28a5aaa53db5a5bd4468fa79d882f9626e580e` |
| `SPINE.jsonl` | 561 | `29a947e81d8fa480a959b02cc6bb226cc6187b8cd7987845311b279b4494e3bb` |

### Live deployment implication

This VM should be treated as an existing stateful Core host, not as a blank Pod target. The first live implementation slice must be additive and isolated:

1. Preserve and independently archive/hash the existing Core/DataQuad state before any deployment change.
2. Stage the Pod runtime under a separate path and namespace; do not replace `/opt/aegis/cyberpeers/foundational-core/dataquad/`.
3. Define an explicit read-only or copied-record admission boundary before loading the existing DataQuad into a Pod.
4. Build and verify the Portal locally/isolated before exposing any listener.
5. Keep substrate attachment and any DataQuad writeback as separately authorized phases.

No live runtime or DataQuad mutation was performed during the inventory; the Phase 0 preservation bundle below was the only authorized remote write.

## Phase 0 completion — Preservation and Observation

Phase 0 was executed on the JIT-enabled VM on 2026-08-02 UTC. The operation was limited to preservation and observation:

- **Remote evidence bundle:** `/home/aegisadmin/aegis-backups/cyberpeer-pod-phase0-preservation-20260802T014339Z`
- **DataQuad archive:** `dataquad.tar.gz`
- **Archive SHA-256:** `07e464e4285e2ac861f7c1040ba6d8bb82299265142ead3484dc4915b3fec2d9`
- **Archive contents:** 20 DataQuad files
- **Source unchanged gate:** `PASS`
- **Evidence bundle hash list:** `bundle-files.sha256`
- **Evidence bundle hash-list SHA-256:** `9e22eca39f11bc5aef1cf21a5fa9238569251dc4d3c3b543fa9bb83754f542c0`

Captured evidence includes:

- `dataquad-sha256.before` and `dataquad-sha256.after`
- `dataquad-files.before`
- `services.running.txt` and `services.enabled.txt`
- `rls-state.txt`
- `rls-behavior.txt`
- deployment source hashes

Observed RLS state:

- Docker Compose still defines `foundational-core-rls` with `RLS_INTERVAL_SECONDS=30` and `RLS_MAX_RECORDS_PER_CYCLE=4`.
- The container is currently stopped and recorded as `Exited (137)`; it was created eight weeks ago and finished on 2026-06-09.
- Historical container output shows the loop targeting `/dataquad/agnostic-peer-state.json` and appending 1–4 recursive reflection records per cycle.
- No RLS container was started, stopped, rebuilt, or otherwise changed during Phase 0.

Phase 0 is complete. Phase 1 remained separately gated until the sidecar staging recorded below; the existing DataQuad path remains untouched.

## Phase 1 completion — Sidecar Pod Runtime

Phase 1 was staged on the JIT-enabled VM after the target directory became available:

- **Sidecar root:** `/opt/cyberpeer-pod/`
- **Pod source:** `/opt/cyberpeer-pod/pod/source/`
- **Directories:** `pod`, `portals`, `orbs`, `satellites`, `adapters`, `logs`
- **Staged source file count:** 113
- **Manifest:** `/opt/cyberpeer-pod/phase1-manifest.txt`
- **Layout record:** `/opt/cyberpeer-pod/phase1-layout.txt`
- **Source hash record:** `/opt/cyberpeer-pod/phase1-source-sha256`
- **Manifest SHA-256:** `b81895627bdde84289b04d98fed6c68fabf6e04e8e9e2db26f72ab3a3beb17e1`
- **Layout SHA-256:** `f1de7087a509fab287a978221191c3e034376aadeaaa0793f9b3b549350d1424`
- **Source hash-record SHA-256:** `bd23e2a534158fb733ad35d1139f9028c0b5f23cde649c6ca08f2bf48a7bc0c8`

Closeout gates:

- Sidecar status: `staged-not-running`
- Sidecar listener: none
- Sidecar container: none
- Sidecar DataQuad directory: absent
- Existing DataQuad hashes: unchanged from Phase 0 baseline
- Existing Core runtime: untouched

The staged source is contract-first architecture material only. No dependency installation, service registration, container start, Portal exposure, or DataQuad adapter/writeback was performed. Phase 2 remains separately gated.

## Baseline evidence

At assessment time:

- Git branch: `main`, ahead of `origin/main` by 3 commits.
- Working tree: pre-existing modifications and untracked evidence were present; none were altered by this assessment.
- `ARCHITECTURE.md` SHA-256: `C356BB67C1D11A4FFC5AB51F1C3A53052A6468753E7E5FA350FC3EBE564A1186`.
- `README.md` SHA-256: `CEC5EBC4EC75DBDAAAAC87123695D3F976F7507CD33D9ABEC4F40BBBF0B98AC6`.
- `CURRENT-STATE-AND-NEXT-STEP.md` SHA-256: `155F9FF2F163110D0EBC46D1518E7E2A0A24FBF3134D555DDD9584DADF26FC70`.
- Live VM inventory was read-only over JIT SSH; remote file hashes above are the captured baseline for the four DataQuad JSONL files.
- Phase 0 archive and observation bundle were created under the remote backup path above; the source-unchanged verification passed.
