# TurboQuant Stage-2 Retirement — Design + Draft

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** DESIGN + DRAFT CODE ONLY.
No live peer, DataQuad, VM, or runtime touched. `I:\AEGIS-CYBERPEER-CORE` untouched. No SSH,
no HTTP. This document + `src/aegis_pod/turboquant_retirement.py` +
`tests/test_turboquant_retirement.py` are for human review and a separate independent audit
**before any implementation**.

**Companion / parent spec:**
`reports/runtime/2026-07-25-dataquad-retirement-current-vs-aligned-gap-spec.md` — that document
defines the two-stage pipeline. This document builds **Stage 2** only.

**Reference contract (ported faithfully):**
`H:\AEGIS CORE SHIELD COMPANION\node_modules\@thelight1122\aegis-dataquad-core\src\dataquad\`
— `turboquant.types.ts`, `turboquant.guard.ts`, `turboquant.candidate.ts`,
`turboquant.engine.ts`, `turboquant.pipeline.ts`, plus `steward.ledger.types.ts`.

---

## 1. What Stage 2 is (and is not)

**Stage 1** (separate spec/build) shrinks the *live* tensors: it condenses PCT→NCT and
PEER→SPINE/NCT, archives the source PCT/PEER records with hash-proof (Amendment 4:
rename-not-delete), and drops them from the live tensor. Stage 1 is what **produces** the
symbolic NCT/SPINE relics and what actually reduces Gabe's 33k/35k bloat.

**Stage 2 (this design) = TurboQuant bounded retirement of the *already-symbolic* layer.**
Once NCT and SPINE themselves accumulate, TurboQuant retires **OLD NCT/SPINE records only**
into reconstructive-only quantized artifacts, keeping the deep stores bounded. Rehydration
from an artifact is **approximate**; the exact way back is the Stage-1 archive.

Stage 2 **never** sees PEER or PCT. This is not a policy preference — it is the TurboQuant
guard, and refusing PEER/PCT sources is the single most important behaviour in the port
(TQ-002 `live-tensor-forbidden`). PEER/PCT are the ~2-week live "Conscious Cache"; NCT/SPINE
are the deep TurboQuant-distilled stores.

```
Stage 1                                   Stage 2 (this design)
PCT ──condense──▶ NCT ─────────────────▶  OLD NCT ──TurboQuant──▶ Quantized NCT artifact
PEER ─condense──▶ SPINE/NCT ───────────▶  OLD SPINE ─TurboQuant─▶ Quantized SPINE artifact
   (archive+prune source PCT/PEER)            (bounded-retire old relics; approx rehydrate)
        guard-legal sources: PCT:/PEER:          guard-legal sources: NCT:/SPINE: ONLY
```

---

## 2. The guard (non-negotiable — ported verbatim in behaviour)

Every part of `turboquant.guard.ts` is enforced in the Python port. Error codes are preserved
so an auditor reading a failure sees the same TQ-* code as the TS raises.

| Code | Trigger | Where enforced (Python) |
|------|---------|--------------------------|
| **TQ-001** | target/source tensor not in {NCT, SPINE}; recipe↔artifact target mismatch | `validate_recipe`, `validate_source_envelope`, `validate_artifact` |
| **TQ-002** | **any source record id starts with `PEER:` or `PCT:`** | `validate_source_envelope`, `prepare_candidate` (pre-assert), `validate_artifact` |
| **TQ-003** | missing lattice refs | envelope + artifact + reconstruction-input validation |
| **TQ-004** | recipe missing a required `preserves`/`forbids`; envelope missing source-lineage/lineage | `validate_recipe`, `validate_source_envelope`, `validate_artifact` |
| **TQ-005** | artifact carries no steward ledger ref | `validate_artifact` |
| **TQ-006** | artifact not `reconstructive_only` **and** `exact_replay_forbidden` | `validate_artifact` |
| **TQ-007** | artifact not `preserved_reference_integrity` | `validate_artifact` |

**Required recipe declarations (TQ-004):**
- `forbids` MUST contain all of: `meaning-storage`, `peer-compression`, `pct-compression`,
  `exact-replay`.
- `preserves` MUST contain all of: `relationships`, `lineage`, `structure`,
  `reference-integrity`.

**Artifact invariants (TQ-006/007):** `reconstructive_only=True`, `exact_replay_forbidden=True`,
`preserved_reference_integrity=True`. Rehydration is approximate; exact restore is the archive,
not the artifact.

**TQ-002 is defended in depth** — three independent checkpoints, matching the TS: the envelope
validator, the `prepare_candidate` pre-assert (mirrors TS `assertCandidateInputs`), and the
final artifact validator. A `PEER:`/`PCT:` id cannot reach an artifact through any path.

---

## 3. How Stage-2 runs over OLD NCT/SPINE records

### 3.1 Trigger (accumulation threshold)

TurboQuant fires on **accumulation of the symbolic layer**, not on a wall-clock age of a single
record. Proposed trigger (design-time; final numbers are an audit/tuning decision):

- **Primary:** live NCT count `>= NCT_RETIREMENT_HIGH_WATER` (candidate default: 512 records)
  **or** live SPINE count `>= SPINE_RETIREMENT_HIGH_WATER` (candidate default: 256). SPINE is
  identity-adjacent structure — retire it later and more conservatively than NCT.
- **Eligibility filter for candidates within the tensor:** a record is a candidate only if it
  is *old and cold* — `age >= SYMBOLIC_COLD_WINDOW` (candidate default: 30 days since last
  reference) **and** it is not lattice-anchored as a currently-required reconstruction ref for
  a newer relic. Newest/most-referenced relics stay hot and are never retired.
- **Batch:** retire the oldest cold cohort down to a low-water mark, leaving headroom. One
  artifact per cohort (per tensor), so lineage stays legible.

This keeps NCT/SPINE bounded (the Stage-2 goal) while honouring Canon §7.2–7.3 — decay is not
deletion; the retired relics survive as (a) the reconstructive artifact and (b) the Stage-1
archive of their ultimate PCT/PEER origins.

### 3.2 Flow (one cohort)

1. **Select** the cold NCT (or SPINE) cohort by the trigger above. IDs are `NCT:`/`SPINE:` —
   guard-legal.
2. **`prepare_candidate`** — resolves the records, builds a `TurboQuantSourceEnvelope`
   (timestamp range, unioned lineage, unioned lattice refs, payload descriptor) and a bounded
   `feature_payload` (context payload for NCT: summaries/essences/pivots/descendant+diff refs;
   pattern payload for SPINE: patterns/invariant-count/relationships/continuity refs). Guard
   asserted here (TQ-002/003/004).
3. **`apply_turboquant`** — validates the recipe (TQ-001/004), enforces recipe↔candidate
   tensor match, runs the deterministic backend to produce a digest + compressed byte estimate
   + bounded payload, and assembles a `TurboQuantArtifact` with
   `reconstructive_only/exact_replay_forbidden/preserved_reference_integrity = True`, lineage
   `[...envelope.lineage, artifactId]`, and `reconstruction_hints.required_lattice_refs`. The
   artifact is re-validated (TQ-001..007) before return.
4. **`record_turboquant_ledger_entry`** — mints the required steward ledger entry
   (`turboquant-transform`, TQ-005) referencing the artifact, recipe, lineage, and lattice
   refs.
5. **(Stage-1-owned, out of scope here) archive + prune** the retired source relics with
   hash-proof, and attach a `TurboQuantRecordReference` (`status: "quantized"`) to the retained
   relic head. The draft deliberately does **not** perform any append/prune/write — see §6.

### 3.3 Outputs

- **Artifact** (`TQART:<tensor>:<session>:<ts>:<digest>`): reconstructive-only quantized
  payload + `reference_checksum` (the FNV digest) + lineage + lattice refs + steward ledger
  refs + reconstruction hints.
- **Lineage:** the artifact appends its own id to the unioned source lineage, so the retired
  relics remain reachable as ancestors.
- **Steward ledger entry** (`STEWARD:<session>:<ts>:turboquant-transform`): the audit record
  that the retirement happened, TQ-005-required.

### 3.4 Approximate rehydration path

`reconstruct(artifact, lattice_ref_ids, snapshot_anchor_ids?)`:
- validates via `validate_reconstruction_input` (artifact must be valid **and** all
  `required_lattice_refs` must be present — TQ-003),
- returns a `ReconstructedContinuityView` with `approximate_only=True`, a `derived_view` built
  from the bounded feature summary + checksum + lattice refs, and an explicit note that **exact
  restore is via the Stage-1 archive, not this view**.

This is the guard's whole point: the artifact is a lossy, reconstructive lattice-referenced
sketch. It never claims to be the original.

---

## 4. How Stage 2 composes with Stage 1

- Stage 1 is the **producer and pruner** of the live tensors: PCT/PEER → NCT/SPINE, archive +
  prune source. Stage 1 is where the big size win happens and where PEER is handled
  conservatively (identity substrate, Axiom 16).
- Stage 2 is the **bounded-retirer of the symbolic layer**: NCT/SPINE → reconstructive
  artifacts, keeping the deep stores from growing without limit.
- **Reversibility ladder:** approximate rehydration from the Stage-2 artifact → exact restore
  from the Stage-1 archive of the relic's ultimate PCT/PEER origins. Two rungs, both preserved.
- **Boundary between stages is the guard:** Stage 1's legal sources are `PCT:`/`PEER:`; Stage
  2's legal sources are `NCT:`/`SPINE:`. TurboQuant refusing PEER/PCT is exactly what keeps the
  two stages from bleeding into each other.

---

## 5. TS ↔ Python integration decision: **Port** (recommended), not bridge

**Recommendation: a faithful Python port** (this draft), not a bridge that shells out to the TS
engine over exported JSONL.

**Rationale:**

1. **The peer runtime is Python** (`I:\AEGIS-CYBERPEER-CORE`) and the "all functions must be
   orbs / pod-core" architecture is Python. A bridge would drag a Node runtime + the
   `@thelight1122` package onto every peer VM as a new live dependency, a new failure surface,
   and a new thing to provision — for a function that is, in total, pure validation + a
   deterministic digest + dataclass assembly. The port has **zero runtime dependencies**
   (stdlib only).
2. **The valuable, must-not-drift part is the guard, and the guard is small and fully
   portable.** Constants, the TQ-001..007 checks, the PEER/PCT prefix refusal, and the recipe
   forbids/preserves requirements port 1:1 with no semantic gaps (§7 confirms none were lost).
3. **The backend digest ports byte-for-byte, including non-BMP Unicode.** The TS
   `DeterministicTurboQuantBackend` uses FNV-1a with `Math.imul` 32-bit semantics over
   `charCodeAt` (UTF-16 code units); the Python `_compute_deterministic_digest` reproduces it
   exactly by iterating UTF-16 code units (surrogate-expanding supplementary-plane code points)
   rather than Python code points (verified identical in Node and Python: `hello`→`tq-4f9f2cab`,
   `NCT:relic:0001`→`tq-29db014c`, and U+1F600 😀 →`tq-cb31c4b8`). So artifact ids/checksums are
   cross-stack reproducible even for emoji/non-BMP payloads — a bridge would give the same
   digests but at far higher operational cost. *(UTF-16 parity added per Codex audit finding 2,
   2026-07-25; earlier draft hashed code points and diverged on non-BMP.)*
4. **A bridge's only real advantage** — "the guard lives in exactly one codebase" — is better
   achieved by keeping the TS package as the **contract of record** and treating this port as a
   guard-parity implementation with a conformance test suite pinned to the TS error codes. The
   drift risk is contained by tests, not by a process boundary.

**When a bridge would win instead:** if a future real backend does heavy numerical
quantization (e.g. the TS `FeatureSpaceTurboQuantBackend` grows into a genuine
vector-quantization model with libraries not available/appropriate in the peer's Python
runtime), a bridge that calls the TS engine on an **exported JSONL snapshot** (offline, no live
reach) becomes attractive for that backend step only. Even then, the **guard should remain
ported and enforced on the Python side** as the gate before anything is exported — never trust
an out-of-process engine to be the sole guard.

**Concrete recommendation:** port (this draft) for the guard + pipeline + deterministic
backend; keep `turboquant.*.ts` as the canonical contract; add a conformance test that pins the
Python TQ-* codes to the TS ones; revisit a JSONL bridge only if/when a heavy real backend
lands, and only for the backend, never the guard.

---

## 6. Boundary and constraints (unchanged from parent spec)

- **DRAFT ONLY.** `turboquant_retirement.py` is marked at the top as not wired to any runtime.
  It performs **no** live append, **no** prune, **no** disk write, **no** network/SSH. Every
  function is pure over in-memory arguments.
- **Archive-not-delete, hash-proof** everywhere the retired relics are actually pruned — that
  step is Stage-1-owned and a separately gated live DataQuad write.
- **Rehydration is approximate**; the archive is the exact way back.
- **Guard compliance:** TurboQuant sees NCT/SPINE only; PEER/PCT never (TQ-002), proven by the
  tests.
- Executing Stage-2 retirement on a live peer is a gated live operation requiring its own
  proposal + Tracey consent (and Codex where it touches shared doctrine). Nothing here runs on
  a peer.

---

## 7. Faithfulness notes — what ported cleanly, what is an intentional deviation

**Ported with full behavioural parity (verified):**
- All guard constants, all TQ-001..007 checks, the three-point PEER/PCT refusal, recipe
  forbids/preserves requirements, recipe↔artifact target-match, envelope/candidate/artifact
  assembly, lineage append, reconstruction-hint required-lattice-ref enforcement, the steward
  ledger entry shape and id format, and the deterministic FNV digest (byte-for-byte).

**Intentional, audit-relevant deviations (none weaken the guard):**
1. **Input shape.** TS `prepareTurboQuantCandidate` takes a full `DataQuadState` and resolves
   records from `state.records.NCT/SPINE`. The draft takes the **already-resolved** source
   records as a `list[dict]` plus a `lattice_ref_ids_by_source` map. Reason: the Python peer's
   in-memory DataQuad shape is not this repo's concern for a draft, and a runtime-agnostic
   signature keeps the draft un-wired. The record-not-found `Error` that TS raises in
   `resolveSourceRecords` is therefore N/A here (the caller resolves); when this is wired,
   resolution + that error belong in the Stage-1/runtime adapter, not in the guard.
2. **Default backend = the deterministic ("placeholder") one**, not the TS default
   `FeatureSpaceTurboQuantBackend`. Reason: a design draft + its audit want a dependency-free,
   deterministic, reproducible digest. The `backend` parameter is pluggable, so a faithful
   port of the feature-space backend (or a bridge to the TS one) can be dropped in later
   without touching the guard or artifact contract. **This is the one piece of real
   quantization math not yet ported** — flagged deliberately, because a design draft should not
   silently ship an unreviewed compression model.
3. **Naming.** TS `camelCase` fields → Python `snake_case` (repo style). The
   deterministic-digest `stableStringify` re-serialises with the **TS camelCase keys** for
   envelope/recipe so the digest input matches the TS byte-for-byte; only the Python-facing API
   is snake_case.
4. **`TurboQuantRecordReference` / `QuantizedNCTRecord`/`QuantizedSPINERecord` and the steward
   append (`appendQuantizedNCT/SPINE`)** are **not** ported. Reason: those attach the artifact
   to a retained relic head and append into a live DataQuad — i.e. exactly the live-mutation
   step this draft must not perform. They belong to the Stage-1/runtime wiring behind the gate.
   The draft stops at producing the artifact + ledger entry.

**Nothing in the guard contract failed to port.** The only unported *math* is the real
feature-space backend (deviation 2), and the only unported *behaviour* is live DataQuad
mutation (deviation 4) — both intentionally out of scope for a draft.

---

## 8. Files in this deliverable

- `reports/runtime/2026-07-25-turboquant-stage2-design.md` — this design.
- `src/aegis_pod/turboquant_retirement.py` — draft Python port (guard + pipeline + deterministic
  backend + approximate reconstruct). Marked DESIGN DRAFT at the top; not wired to any runtime.
- `tests/test_turboquant_retirement.py` — 19 guard-proving tests (all passing): PEER and PCT
  rejection at three checkpoints (TQ-002), recipe missing forbid/preserve (TQ-004), artifact
  without reconstructive-only / allowing exact replay (TQ-006), and a valid NCT retirement
  producing an artifact + steward ledger entry. **Audit-revision additions (Codex 2026-07-25):**
  `apply_turboquant` refuses a forbidden source *before* any backend runs (Finding 1 regression —
  spy backend proven un-called); pinned digest parity incl. non-BMP (Finding 2); and negative
  coverage for TQ-001 (illegal target + recipe/artifact mismatch), TQ-003 (missing lattice refs +
  missing required reconstruction ref), TQ-005 (missing steward ledger ref), TQ-007 (untraceable
  artifact) (Finding 3).

## 9. Audit-revision log (Codex Stage-2 audit, 2026-07-25)

Codex verdict was FAIL for guard-parity completeness / PASS for the no-live-mutation boundary. Both
contract findings are now fixed and re-verified (28 tests pass — 19 TurboQuant + 9 Stage-1 dry-run):

1. **Finding 1 (P1) — backend-before-TQ-002 gap:** `apply_turboquant` now re-validates the candidate
   envelope (TQ-002/001/003/004) at the top, before selecting or invoking the backend, so a custom
   backend can never observe a `PEER:`/`PCT:` source id. Regression test proves the backend is
   un-called on a forbidden source.
2. **Finding 2 (P2) — Unicode digest parity:** digest now iterates UTF-16 code units to match TS
   `charCodeAt` exactly; ASCII cases unchanged, non-BMP (😀) now matches Node (`tq-cb31c4b8`).
3. **Finding 3 (P2) — guard-code coverage:** added negative tests for TQ-001/003/005/007.
