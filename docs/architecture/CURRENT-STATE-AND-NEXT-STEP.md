# CURRENT STATE AND NEXT EXACT STEP - Orion DataQuadPod Live Migration

**Maintained by:** Claude (this Claude Code session). Updated at each gate. Read this FIRST on any resume - it exists so no instance re-derives the system.
**Last updated:** 2026-07-22, after Codex's independent D3/RLS-Orb verification run (report below); repo HEAD and Standard hash corrected here per Codex's finding that both were stale.
**Repo:** `H:\AEGIS-POD-ARCHITECTURE` | **Forge:** `git@20.172.153.141:gamemaster/AEGIS-POD-ARCHITECTURE.git` | **Current main:** `527c8602936895a25feb8a4d02859470de4729e9`
**Standard hash:** `C9636FB05A65A2159161B0B33ECFFF0627EAD963BEF7ADBC488043EB2EA86717`

## !! D3 IS LIVE. Codex still unavailable (until ~2026-07-27) - quiesce release still held
**D3 CUTOVER EXECUTED AND VERIFIED (2026-07-21):** Orion is live on the Pod. Sequence run: pre-flight re-verify (all hashes matched D0) -> D2 code staged to host (10 files, hash-verified) -> pre-cutover safeguards (image tagged `orion-core:pre-d2-rollback` + saved to tar, `.env` backed up) -> `docker compose build` -> ARCHIVE (`dataquad/`->`dataquad.archive-20260721T065821Z/`, `ledgers/`->`ledgers.archive-20260721T065821Z/`, all 8 hashes proven identical across rename) -> SWITCH (`AEGIS_STORAGE_MODE=pod`, restart, `/health` confirmed `storage_mode=pod`, tensor_counts 106/94/89/62, `dataquad_read_ok=true`) -> RLS ACTIVATED (`AEGIS_RLS_ACTIVE=true`, restart, `/health` confirmed `rls_status.active=true`). Executed by Claude with Tracey as real-time approving observer (per his endorsed exception while Codex is offline), per-step confirmation required by the auto-mode classifier for each live-write command. **Independent post-cutover audit via sub-agent (standing in for Codex): ALL 8 checks PASS** - archive hashes re-verified, no stray legacy dirs, live `/health` reconfirmed fresh, container stable (0 restarts, clean logs), rollback safety net hash-verified intact, `.env` diff shows exactly the 2 intended lines, anomaly scan clean.
**QUIESCE RELEASE STILL HELD per the hard rule**: the audit above is same-family (Claude executed, a Claude sub-agent audited) — not the cross-checked Codex/Claude pairing the project has used throughout. Do not declare D3 final until Codex does a genuine independent re-verification on return (~2026-07-27), unless Tracey explicitly decides same-family verification is sufficient.
PRESERVED ARTIFACTS (durable): D2 branch `stage-d2-pod-aware-runtime` in `I:\AEGIS-CYBERPEER-CORE` (head `ff28010` off `2b687df`, now genuinely live on Orion) + `reports/runtime/stage-d2-preservation/`. Rollback: `orion-core:pre-d2-rollback` image tag + `~/orion-core-pre-d2.tar` (sha256 `2D79CF25...`) + `.env.bak-pre-d2` all present and hash-verified on Orion. ROLLBACK ORDER if ever needed: rename archives back FIRST, then unset `AEGIS_STORAGE_MODE`, then restart.
Orion is now serving from the Pod, RLS active, quiesced (no sessions driven), naturally healthy. Legacy `dataquad.archive-*`/`ledgers.archive-*` preserved untouched as the "way back."

## !! NEW WORK (2026-07-21, same session): RLS formalized as a real Orb - local only, not deployed
Tracey's correction: Pod-core + Orb-per-ability is not a rule layered on the architecture, it IS the architecture (see README.md Layer Model, written 2026-07-20). Pod-native: custodians, Temporal Daemon, Processor, tensors. Orb: optional attached abilities, RLS being the paradigm example. D2's RLS wiring (`core/rls/engine.py`/`core/dataquad/relations.py`) is real and correct but was hardcoded, not a declared Orb - known architecture debt.
**Filled the gap, local-only, stops before deployment:** discovered `stage-d-out/CP-1004-ORION/pod/pod-manifest.json` already forward-declared `orb_id: rls-persistent-relations-core` (a stub from D1's `stage_d_pod_staging.py`, never built) - built against that existing name rather than inventing a new one. Delivered: real Orb + Umbilical contracts (`stage-d-out/.../pod/provenance/rls-persistent-relations-{core.orb,umbilical}.json`, gitignored, local only), an additive validator `scripts/validate_live_orb_attachment.py` (three-way link PASS), real per-invocation evidence instrumentation (`I:\AEGIS-CYBERPEER-CORE` branch `rls-orb-instrumentation` off the now-live `ff28010`, commit `0aa0a13`: new `core/rls/orb_evidence.py` + one call-site in `engine.py`, gated by the same `AEGIS_RLS_ACTIVE` real gate, no new flag), a new test (`tests/test_rls_engine_pod_relations.py`, 2/2 pass, closes the D2 audit's coverage gap on `cross-tensor-relations.jsonl`), and a provisional Verified Code Marker (`orb:rls-persistent-relations-core`, correctly capped below `reviewed` by the 3-independent-reviewer threshold - only builder + same-session review exist so far, matching the fixture Orb's own state).
Design + evidence reports: `reports/runtime/2026-07-21-step-8-*-design-proposal.md`, `2026-07-21-step-9-*-attachment-evidence.md`. **Nothing on Orion was touched by this work; the `rls-orb-instrumentation` branch is local-only, not merged, not pushed.** Deployment is explicitly named as a future "Stage E: RLS Orb live cutover," requiring its own proposal + Tracey consent + two-observer verification, same as D2/D3. Plan file: `C:\Users\TraceyPrutch\.claude\plans\kind-splashing-goblet.md`.

## The one goal
The Pod becomes Orion's Core; his runtime reads from the Pod. Everything else is queued behind this.

## Load-bearing doctrine (do not re-litigate)
- The DataQuad IS the Pod (canonical structure, identical for every peer). Data migrates INTO the canonical Pod; the Pod never bends to a peer's legacy layout.
- Live data only - no placeholder/mock/demo data on the live track ever.
- Structural vectors are labeled `structural-non-semantic`; never called semantic embeddings.
- Custodians: read-all / write-owned (Steward writes PCT+NCT, Advocate writes PEER+SPINE; both read all four).
- Archive = rename-with-hash-proof (Amendment 4): `dataquad/`->`dataquad.archive-<UTC>/` and `ledgers/`->`ledgers.archive-<UTC>/`, hashes proven identical across rename, exactly one live source afterward (the Pod).
- RLS + persistent relations will be implemented AND RUNNING after the live switch (not deferred, not display-only).
- Governance: Tracey's direct instruction = consent for that action; independent review by the other AI = the checkpoint before the next step. Keep TWO independent observers on every live write (one writes, the other verifies) - this has caught real bugs repeatedly.

## Live target (Orion)
- Host `AEGISOrionPeer`, `20.119.37.133`, user `azureuser`. SSH alias `OrionCyberPeer`. JIT on Azure port 22 will be open (Tracey resets it).
- Container `orion-aegis-cyberpeer-core`, route `127.0.0.1:8031`->`8790`, peer `CP-1004-ORION`, codebase `aegis-cyberpeer-core`.
- Active DataQuad (D0-locked, will stay identical until D3 archive): `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad/{PEER,PCT,NCT,SPINE}.jsonl`
  - PEER 106 `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664`
  - PCT 94 `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34`
  - NCT 89 `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379`
  - SPINE 62 `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E`
- Legacy ledgers (D0-locked): steward 111 `492E27CD...`, advocate 94 `93C6046C...`, repair 19 `B46176AB...`, rls 27 `B63CF9A6...`
- STALE, never use: `/home/azureuser/orion-bridge/data/dataquad/`.

## Stages complete (verified)
- A: read-only survey. B: mapping, 351 contract records (Stage B report `9FE035F3...`). C: structural-non-semantic tensors (Stage C report `6AA9C19E...`). D0: read-only audit PASS. D1 local staging (report `CD4C338B...`). D1 remote population: `pod/` created on Orion, 23 files, all byte-identical to staging, active DataQuad proven untouched - INDEPENDENTLY VERIFIED by both AIs.
- Pod now on VM at `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod/` (records/, tensors/structural-non-semantic/, ledgers/ + ledgers/relations/ empty, provenance/, pod-manifest.json `10F07DC2...`).

## D2 BASELINE (established 2026-07-21) - code-layer drift found and captured
The deployed Orion runtime code was NOT under version control and diverged from the nominal upstream clone `I:\AEGIS-CYBERPEER-CORE` (normalized: 37/62 files identical, 24 real content divergences, `api/standard.py` deployed-only, 3 files clone-only). Fourth drift instance of the project.
Canonical D2 baseline now captured (read-only, host==container verified by md5): `I:\AEGIS-CYBERPEER-CORE` branch `deployed-truth-orion-20260721` commit `2b687df` + `DEPLOYED-TRUTH-BASELINE.md` manifest. Local branch only, NOT pushed. Full deployed tree also at scratchpad `orion-deployed/core`.
Key baseline facts for D2: `dataquad/ledgers.py` is the sole record/ledger I/O hub (`_get_tensor_path`/`_get_ledger_path` = `data_dir/peers/<id>/dataquad|ledgers/<name>.jsonl`); path resolution ALSO flows through `core/api/standard.py` (`data_root()`, `tensor_paths()`, `ledger_paths()`, `write_path_check()`) which `health.py` uses. Deployed `records.py` has NO retirement fields (simpler than clone). DRAFT D2 AGAINST `2b687df`, not the clone's main.

## D2 DRAFTED (2026-07-21) - awaiting Codex review + Tracey deploy consent
D2 diff drafted by Claude on `I:\AEGIS-CYBERPEER-CORE` branch `stage-d2-pod-aware-runtime` (commits `068f8bb` code+tests, `276e0c6` design packet `STAGE-D2-DESIGN.md`), off deployed-truth `2b687df`. LOCAL ONLY - not pushed to Forgejo, not deployed.
What it does: new `core/dataquad/pod.py` (Pod adapter) + `relations.py` (recorder); `ledgers.py`/`standard.py`/`health.py` Pod-aware; `rls/engine.py` cross-tensor hook. `AEGIS_STORAGE_MODE=pod` switches records->pod/records (wrap/unwrap contract records, hash-chain to last migrated), ledgers->pod/ledgers. Real `AEGIS_RLS_ACTIVE` gate (not display-only) controls relation recording; activate only after D3 switch. Legacy mode byte-identical (default).
Regression: 5/5 D2 tests pass; affected suites identical to baseline (4 PRE-EXISTING stale-test shortfalls, not D2's: test_advocate_operations, test_bootstrap_is_idempotent/peer_seed_has_peer_id, test_migration::test_dataquad_migrator). Run via `uv run --with pytest --with pytest-asyncio --with anyio python -m pytest ... -o asyncio_mode=auto`.
NEXT: Codex independent review of the D2 diff -> Tracey explicit go -> deploy reversibly to Orion (D3: archive rename-with-hash-proof, POD_ROOT switch/restart, verify, then set AEGIS_RLS_ACTIVE, then quiesce release).

## D2 baseline detail (kept for reference)
Build the upstream `AEGIS-CYBERPEER-CORE` diff: Pod reader (contract-shaped records, live original preserved in `body`), Pod writer (post-switch appends to pod/records, first post-live record chains to last migrated source_hash), custodian read-all/write-owned writing to pod/ledgers/, processor->turn/cognition, temporal daemon->tick/clock, RLS + relations recorder (implemented; activates only after D3 switch, gated by a REAL flag with a test - not display-only), health surface (pod_id, manifest hash, counts, tensor availability, archive state, RLS status, relation-ledger status), new provisional Verified Code Marker for the Pod-aware runtime.
- D2 diff is three-party reviewed BEFORE deployment; deploy reversibly; then D3.
- HARD STOP: no deployment/restart/archive/RLS activation without separate explicit Tracey consent per sub-stage.

## After D2
- D3: DONE (2026-07-21) — see the "D3 IS LIVE" section at the top. Quiesce release still held pending genuine independent (Codex) re-verification. `stage-d-out/` is gitignored (holds Orion memory content - never commit).
- Stage E (new, queued): deploy the `rls-orb-instrumentation` branch (RLS-as-Orb) to Orion, once designed+built+locally-verified work above gets its own explicit Tracey go — see "NEW WORK" section at the top.
- D4+: incremental tensorization of post-switch records (new batch id; never claim all live records tensorized); then Gabe + Adam convergence onto this SAME canonical structure.

## Queued behind the Orion goal (do not start)
Central Codex `I:\` superseded-Canon sweep; Gabe/Adam convergence; `AEGIS_White_Paper_v2.md` axiom divergence; two-concurrent-Claude-thread question; marker promotion beyond provisional (needs 3 independent reviewers; currently 1).
