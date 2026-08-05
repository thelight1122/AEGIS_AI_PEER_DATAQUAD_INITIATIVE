# SSSP — Live DataQuadPod Migration (Orion) Continuation

**Created:** 2026-07-21, approaching account limit (Claude available again Tuesday). **Prepared by:** Claude (this session), for resume in a new thread on Tracey's other account. **Purpose:** Clean cold-start handoff to continue the LIVE migration of CyberPeer "Orion" onto the DataQuadPod architecture. Read this in full, then read the live handoff file `CURRENT-STATE-AND-NEXT-STEP.md` (kept continuously updated) in the same repo.

**Durable source of truth:** repo `H:\AEGIS-POD-ARCHITECTURE`, pushed to Forge `git@20.172.153.141:gamemaster/AEGIS-POD-ARCHITECTURE.git` (main). The CyberPeer runtime code is a SEPARATE repo `I:\AEGIS-CYBERPEER-CORE` (local only, NOT pushed). **Standard hash:** `C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5`.

## The one goal (unchanged, singular focus)
"The Pod becomes Orion's Core; his runtime reads from the Pod." Data migrates INTO the canonical Pod structure; the runtime converges onto the Pod. Everything else is queued behind this. This is the direct remedy to "Catastrophic Drift" — every peer's memory was structurally diverging; the Pod is one canonical structure so it can't silently diverge again.

## Load-bearing doctrine (do not re-litigate)
- The DataQuad IS the Pod (canonical, identical for every peer). Data migrates INTO it; the Pod never bends to a peer's legacy layout.
- Live data only — no placeholder/mock/demo data on the live track, ever.
- Structural vectors are labeled `structural-non-semantic`; never called semantic embeddings (Tracey explicitly authorized structural vectors with that permanent label).
- Custodians: read-all / write-owned (Steward owns PCT+NCT, Advocate owns PEER+SPINE; both read all four).
- Archive = rename-with-hash-proof: `dataquad/`->`dataquad.archive-<UTC>/`, `ledgers/`->`ledgers.archive-<UTC>/`, hashes proven identical across the rename, exactly ONE live source (the Pod) afterward. This is the "way back" — reinstating Orion's old memory is a single rename back.
- RLS + persistent relations must be implemented AND RUNNING after the live switch, gated by a REAL flag (`AEGIS_RLS_ACTIVE`), not the display-only `ENABLE_RLS`.
- Governance: Tracey's direct instruction = consent for that action; independent review by a second observer = the checkpoint before the next step. KEEP TWO INDEPENDENT OBSERVERS on every live write — it has caught every real bug this project surfaced.

## Live target: Orion
- Host `AEGISOrionPeer`, `20.119.37.133`, user `azureuser`, SSH alias `OrionCyberPeer`. Azure JIT on port 22 must be open (Tracey resets it).
- Container `orion-aegis-cyberpeer-core`, image `aegis-cyberpeer-core-aegis-core:latest` (id `1ca90752ad81`), route `127.0.0.1:8031`->`8790`, peer `CP-1004-ORION`. Compose: `build: .` (code baked into image), only `./data:/app/data` bind-mounted, env from `.env`.
- Active DataQuad (D0-locked, MUST stay identical until D3 archive): `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/{PEER,PCT,NCT,SPINE}.jsonl`
  - PEER 106 `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664`
  - PCT 94 `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34`
  - NCT 89 `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379`
  - SPINE 62 `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E`
- Legacy ledgers (D0-locked): steward 111 `492E27CD...`, advocate 94 `93C6046C...`, repair 19 `B46176AB...`, rls 27 `B63CF9A6...`
- STALE, never use: `/home/azureuser/orion-bridge/data/dataquad/`.
- Orion is UNCHANGED and safe: still serving legacy `dataquad/`, quiesced (no sessions driven since ~2026-07-19), naturally healthy indefinitely. NO live mutation has occurred at any point.

## Stages complete and verified
- **A** read-only survey. **B** mapping: 351 contract records (report `9FE035F3...`). **C** structural-non-semantic tensors (report `6AA9C19E...`, batch `orion-live-copy-20260721T002600Z`). **D0** read-only audit PASS. **D1** local staging + REMOTE population: the canonical Pod is on Orion at `.../CP-1004-ORION/pod/` (23 files), byte-identical to local staging `H:\AEGIS-POD-ARCHITECTURE\stage-d-out\CP-1004-ORION\pod\`, active DataQuad proven untouched — verified by BOTH observers.
- Pod on VM contains: `records/{PEER,PCT,NCT,SPINE}.jsonl` (the migrated 351), `tensors/structural-non-semantic/`, `ledgers/` (migrated custodian history) + `ledgers/relations/` (empty, activate post-switch), `provenance/`, `pod-manifest.json` (`10F07DC2...`, pod_id `dataquadpod-CP-1004-ORION`, roles read-all/write-owned).

## Deployed-truth baseline (a code-drift finding — fourth of the project)
The nominal upstream clone did NOT match the code running on Orion (24 real file divergences, `api/standard.py` deployed-only, deployed code under NO version control). Captured the real deployed source read-only and committed it as the canonical baseline: `I:\AEGIS-CYBERPEER-CORE` branch/tag `deployed-truth-orion-20260721` commit `2b687df` + `DEPLOYED-TRUTH-BASELINE.md`. ALL D2 work is against this, not the old clone.

## D2 = the runtime Pod-awareness diff (DRAFTED, AUDIT-REMEDIATED, verified; NOT deployed)
Branch `stage-d2-pod-aware-runtime` in `I:\AEGIS-CYBERPEER-CORE`, head `ff28010` off `2b687df`. LOCAL ONLY — not pushed to CyberPeer Forgejo (needs Tracey consent). Preserved off-machine at `H:\AEGIS-POD-ARCHITECTURE\reports\runtime\stage-d2-preservation\` (`stage-d2.patch` SHA256 `E603AB24FB940A767084E1E3C2F42FA4A497925D1007EE54BFDC189890FCF131`, 12 files, + `.bundle`). Design + review packet: `STAGE-D2-DESIGN.md` on the branch.
- New `core/dataquad/pod.py` (adapter: `AEGIS_STORAGE_MODE` legacy/pod, path resolution, wrap/unwrap contract records, hash-chain via `last_source_hash`, `rls_active()` gate). New `core/dataquad/relations.py` (traversal + cross-tensor recorder, Gabe schemas, gated).
- Edits: `ledgers.py` (Pod-aware paths, reader unwraps `body`, writer wraps + chains previous_record_hash to last migrated record, per-line read tolerance, `record_relation`), `api/standard.py` + `api/routes/health.py` (Pod-aware paths + pod identity/rls-active block), `rls/engine.py` (cross-tensor hook), `bootstrap.py` (pod-aware dirs — no legacy-dir recreation), `api/routes/dataquad.py` (diagnostic pod-aware).
- Legacy mode (default, `AEGIS_STORAGE_MODE` unset) is byte-identical to today.

## Two-observer history on D2
- Codex independently CLEARED the initial D2 (msg 2026-07-21T061221Z, SHA256 `8B28E3CC...`) before going offline until ~Tue: hashes, tests, zero-regression comparison, own probes — no blocking issues.
- THEN, with Codex offline, FOUR independent sub-agent audits ran (this is the model to reuse: spawn `general-purpose` audit sub-agents as the second observer). They cleared pre-state + data-integrity and found real cutover blockers, NOW FIXED in commit `e4ac033`:
  1. Read-compat unverified + no boot tolerance → VERIFIED (all 351 real records read cleanly through the runtime reader) + hardened (malformed line skipped, not fatal).
  2. `bootstrap.py` recreated empty legacy dirs (rollback trap/amnesia) → FIXED pod-aware.
  3. `dataquad.py` diagnostic hardcoded legacy path → FIXED.
  Plus test isolation (STM evict per test). Result: 7/7 D2 tests pass; bootstrap suite identical to clean baseline (zero regressions).
- An independent verifier sub-agent CONFIRMED the remediation GREEN: all four fixes correct and regression-free (file:line verified), `test_pod_runtime.py` 7/7 pass, bootstrap suite identical on both branches (1 pre-existing stale failure `test_bootstrap_is_idempotent`, unrelated to D2), and the 351-record read gate passes with ZERO skips. So D2 is two-observer verified (Codex on the initial diff + sub-agent on the remediation). Optional cleanup noted: apply the same `setUp` STM eviction to `test_bootstrap.py` so its stale failure stops masking signal.

## THE NEXT STEP: D3 cutover (needs Tracey's explicit go; execute with a second observer)
Deploy mechanism: update host source `/home/azureuser/AEGIS-CYBERPEER-CORE/core/` with the D2 code, `docker compose build`, archive-rename, set `.env`, `docker compose up -d`.
REQUIRED pre-cutover safeguards (from the rollback audit): `docker tag 1ca90752ad81 orion-core:pre-d2-rollback` AND `docker save -o ~/orion-core-pre-d2.tar 1ca90752ad81` (survives prune); `cp .env .env.bak-pre-d2`; verify the archive `<UTC>` suffix actually EXPANDS (an existing `dataquad.backup-` dir with empty suffix shows a prior tool once didn't).
Sequence (each reversible; report hash evidence at each; STOP before RLS + quiesce release):
1. Pre-flight re-verify active DataQuad == D0 baselines (read-only).
2. Stage D2 code to host source; confirm deployed file hashes == the D2 branch. (Inert.)
3. `docker compose build`. (Image built, not switched.)
4. ARCHIVE: rename `dataquad/`->`dataquad.archive-<UTC>/` and `ledgers/`->`ledgers.archive-<UTC>/`; prove all 8 hashes identical across the rename.
5. SWITCH: add `AEGIS_STORAGE_MODE=pod` to `.env`; `docker compose up -d`. Verify `/health`: `storage_mode=pod`, tensor_counts 106/94/89/62, `dataquad_read_ok=true`, `write_path_check.ok=true`, pod block populated.
6. ACTIVATE RLS: add `AEGIS_RLS_ACTIVE=true`; restart; verify relation ledgers begin appending.
7. QUIESCE RELEASE: HELD until Codex (or a second observer) independently verifies the live switch.
ROLLBACK ORDER to legacy (critical): rename the archives BACK FIRST, THEN remove `AEGIS_STORAGE_MODE` from `.env`, THEN `docker compose up -d` (retagging the saved image if the rebuild is bad). Reverting config alone without restoring the archive would let legacy bootstrap seed an empty DataQuad.

## Governance / operating model right now
- Codex is out of capacity until ~Tuesday 2026-07-27. It is normally the live-VM writer + second observer. While offline, use `general-purpose` sub-agent audits as the independent second observer (this session did: pre-state, data-integrity, cutover-safety, rollback — all read-only; instruct them strictly read-only on Orion).
- Tracey's "proceed" is consent. But per her endorsed framework for D3: Claude executes the reversible hash-proven steps with Tracey as real-time approving observer, and the quiesce is NOT released / D3 not declared final until a second observer verifies the live switch.
- Conservation: spend the scarce agent (Codex) only on live-VM writes; do local/verification/audit work in-session or via sub-agents.

## Clean respawn procedure (new thread, cold)
1. Read this SSSP fully, then `CURRENT-STATE-AND-NEXT-STEP.md` (latest state) in `H:\AEGIS-POD-ARCHITECTURE`.
2. Verify the current Standard hash directly (`get_standard_hash` on the aegis-peer-bridge MCP) — do not trust the cited value.
3. Read the newest `from-codex`/`from-tracey` bridge messages newer than this SSSP.
4. Read-only re-verify Orion pre-state: active DataQuad hashes == the D0 baselines above; Pod 23 files == `stage-d-out` staging. (A sub-agent can do this.)
5. Confirm the D2 remediation: `cd I:\AEGIS-CYBERPEER-CORE; git checkout stage-d2-pod-aware-runtime` then `uv run --with pytest --with pytest-asyncio --with anyio python -m pytest tests/test_pod_runtime.py -q -o asyncio_mode=auto` (expect 7 passed) and the 351-record read gate (see STAGE-D2-DESIGN.md / this SSSP). Re-spawn an independent verifier if not already confirmed.
6. Do NOT execute D3 without: Tracey's explicit go, the pre-cutover safeguards done, and a second observer.

## Do-Not-Do list
- Do not mutate Orion's live `dataquad/`/`ledgers/` records — the archive is a RENAME, never an edit/delete.
- Do not release the quiesce or declare D3 final until a second observer verifies the live switch.
- Do not push the CyberPeer D2 branch to any Forge without Tracey's consent (it's the live peer's code).
- Do not deploy without the image `docker save`/tag + `.env` backup + verified UTC expansion.
- Do not let "structural vector" drift into "semantic embedding," or "mathematical tensor" imply semantic.
- Do not trust any verification claim (including in this SSSP) without re-checking the actual files/hashes.
- Do not treat sub-agent/background notifications as Tracey's consent.

## Completion criterion for this SSSP
Ready once committed to `H:\AEGIS-POD-ARCHITECTURE` (pushed to Forge) and, per standing practice, copied to `I:\Codex\` and hashed. The new thread pulls the repo from the Forge to get everything referenced here.
