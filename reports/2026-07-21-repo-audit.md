# Repo Audit — AEGIS-POD-ARCHITECTURE

**Date:** 2026-07-21
**Method:** Direct inspection of git history, tracked files, gitignored-but-present local files, and a live run of the test suite. Findings are grounded in artifacts actually opened/executed, not in the repo's own narrative claims taken at face value.

## 1. Identity & scale
- Local path `H:\AEGIS-POD-ARCHITECTURE`, git remote `origin` → `git@20.172.153.141:gamemaster/AEGIS-POD-ARCHITECTURE.git` (a self-hosted Forgejo/Gitea instance, not GitHub). A second remote ref `forge/main` also exists.
- 51 commits total, all on `main`, working tree clean, branch up to date with origin.
- First commit: `f665a08 Bootstrap DataQuadPod architecture` / `bc25cea Initial commit: Pod-Orb clean-room reference implementation`. Most recent: `cc8b00c Consolidate real Mathematical Tensor Service into the clean Pod-Orb repo`.
- On-disk size ~18MB tracked-relevant content, plus **9.0MB in `live-copies/` and 7.4MB in `stage-d-out/`** — both present on disk but excluded from git via `.gitignore`.
- No secrets, keys, or credentials found in a grep of tracked files.

## 2. What's actually tracked in git (141 files)
| Dir | Files | Content |
|---|---|---|
| `reports/` | 72 | Dated markdown/JSON "evidence" and status reports |
| `tools/` | 16 | A standalone package `aegis-math-tensor-service` (real sentence-transformer embedding builder) |
| `fixtures/` | 14 | Local JSON/JSONL sample data conforming to the contracts |
| `contracts/` | 13 | JSON Schemas defining Pod/Orb/Umbilical/tensor/marker record shapes |
| `src/` | 11 | `aegis_pod` Python package, 2,595 lines total |
| `tests/` | 10 | pytest suite for the `src/` modules |
| `scripts/` | 2 | Contract/attachment validators |
| root | 3 | `README.md`, `CURRENT-STATE-AND-NEXT-STEP.md`, `SSSP-2026-07-21-LIVE-DATAQUADPOD-MIGRATION-ORION.md` |

## 3. Documented architecture (from README.md)
A layered model: **Pod** (CyberPeer core: PEER/PCT/NCT/SPINE tensors + Steward/Advocate custodians + Processor + Temporal Daemon), **Orb** (optional attached ability package, e.g. RLS), **Umbilical** (contract connecting Pod↔Orb), **Container** (runtime vessel, "not the architecture").

## 4. Source code — verified real, not stubs
Read `tensor_runtime.py` and `stage_d_pod_staging.py` in full; grepped the rest. Findings:
- The code is genuinely functional Python: JSONL parsing, SHA-256 hashing/lineage verification, deterministic tensor construction, JSON Schema-shaped record validation — not placeholder scaffolding.
- Two modules (`live_record_mapping.py`, `stage_d_pod_staging.py`) contain **real `subprocess` calls to `ssh`/`scp`** targeting a hardcoded remote host: `SOURCE_VM = {"host": "AEGISOrionPeer", "ip": "20.119.37.133", "user": "azureuser"}`, pulling from `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/dataquad`. This is capable of reaching a real machine over the network — it is not simulated in code.
- `tools/aegis-math-tensor-service/` is a separate real package (FastAPI/numpy/sentence-transformers/chromadb per its `provenance.py`) for building 384-dim embeddings, distinct from the "structural-non-semantic" 4-slot tensors the main package produces.

## 5. Tests — actually run, actually pass
`tests/` doesn't run out of the box (`pytest` isn't installed in the base Python); via `uv run --with pytest`, **35/35 tests pass** in 9.96s. (Running the full repo including `stage-d-out/` fails to collect — a test file staged there imports `core.dataquad`, a module belonging to the separate, un-vendored `AEGIS-CYBERPEER-CORE` repo, not this one.)

## 6. Gitignored local state — present, real, larger than the tracked repo
`.gitignore` excludes `live-copies/`, `stage-d-out/`, `.env*`. Both exist locally with real content:
- `live-copies/CP-1004-ORION/orion-live-copy-<timestamp>/` — two timestamped batches (`...000900Z`, `...002600Z`) with `raw/`, `mapped/`, `source-records/`, `tensors/`, `legacy-ledgers/` subtrees.
- `stage-d-out/CP-1004-ORION/pod/` — 55 files: `records/{PEER,PCT,NCT,SPINE}.jsonl`, `ledgers/` (including 5 empty relation-ledger files), `pod-manifest.json`, provenance/hash-lock files, an Orb+Umbilical contract pair for `rls-persistent-relations-core`, a source-code snapshot of an RLS engine + test, and a `tensors/semantic-embedding/` tree with real `.npy` files (embeddings, metadata, 3D tensor) plus a `tensors/structural-non-semantic/` tree — two parallel, distinctly-labeled tensor products, per `reports/runtime/2026-07-21-step-10-*.md`.
- Since neither directory is under version control, **nothing in them is verifiable from git history** — they reflect current local disk state only, not a tracked/auditable trail.

## 7. `reports/` — a dense first-person operational log, not conventional docs
72 files, almost all dated `2026-07-20` or `2026-07-21`, written in first person by "Claude" as an acting operator. Representative content opened directly:
- `reports/runtime/2026-07-21-stage-d1-remote-population-report.md` — claims a real SSH session copied a staged Pod directory to the live host and lists ~18 SHA-256 hashes per file as verification.
- `CURRENT-STATE-AND-NEXT-STEP.md` (root) — claims a full production cutover ("D3") was executed on 2026-07-21 against host `AEGISOrionPeer` (`20.119.37.133`): docker image tagged/saved, `dataquad/`/`ledgers/` directories archived via rename, `AEGIS_STORAGE_MODE=pod` and `AEGIS_RLS_ACTIVE=true` set, `/health` endpoint checked, then explicitly states quiesce/finality is **withheld** pending an independent reviewer ("Codex") described as offline until ~2026-07-27.
- References throughout to a second, separate repo `I:\AEGIS-CYBERPEER-CORE` (the actual CyberPeer runtime, not part of this repo) and a governance loop between "Tracey," "Claude," and "Codex," coordinated partly through an `aegis-peer-bridge` MCP channel (this repo's `.claude/settings.local.json` grants exactly one permission: `mcp__aegis-peer-bridge__list_peer_messages`).

**Boundary on what could be confirmed:** These documents exist, are internally cross-referenced and hash-annotated, and are consistent with the real SSH/SCP-capable code in `src/`. It could **not** be confirmed from this repo alone that the described live cutover on `20.119.37.133` actually occurred or is currently in that state — that would require reaching the actual host, which is outside this repo and outside the scope of this audit. The repo's own text repeatedly flags this same gap (unresolved independent re-verification).

## 8. Contracts & fixtures
13 JSON Schemas in `contracts/` (Pod, Orb, Umbilical, tensor-record, mathematical-tensor, migration-dry-run, verified-code-marker, marker-promotion, canon-housekeeping, live-copy-manifest) with matching example data in `fixtures/`. `scripts/validate_contracts.py` and `scripts/validate_live_orb_attachment.py` are the two committed validators.

## 9. Notable items worth attention
- **Two large, unversioned directories** (`live-copies/`, `stage-d-out/`, ~16MB combined) hold the actual evidentiary data behind most of the "live" claims in `reports/`. If this machine is lost or the dirs are cleaned, that evidence is gone — only the hash-annotated markdown summaries survive in git.
- **A test file inside `stage-d-out/`** (gitignored) references a module (`core.dataquad`) from the separate `AEGIS-CYBERPEER-CORE` repo and fails collection if `pytest` is run from repo root without scoping to `tests/`.
- **RLS is still architecture debt**: the repo's own current-state doc says the D2 RLS wiring was "hardcoded, not a declared Orb" and that a proper `rls-persistent-relations-core` Orb was only built locally, gitignored, not deployed.
- The repo's stated boundary rules (README) say "No migration execution" / "No living DataQuad writes," while `CURRENT-STATE-AND-NEXT-STEP.md` claims a live migration was in fact executed — i.e., the README has not been updated to reflect the state the operational log claims. That's either a stale doc or a real discrepancy worth resolving.
