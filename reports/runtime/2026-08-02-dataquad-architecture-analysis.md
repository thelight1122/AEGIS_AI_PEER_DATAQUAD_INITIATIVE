# CyberPeer DataQuad — Architecture Analysis

**Date:** 2026-08-02
**Author:** Claude (senior systems architect review)
**Method:** Source-of-truth reading of actual code, schemas, and live/staged record data. No component is described from design documents alone; where a document and the code disagree, the code is reported and the disagreement is named.

**Labelling convention used throughout:**

| Tag | Meaning |
|---|---|
| **[IMPLEMENTED]** | Real code, reachable on the live turn path, verified by reading it |
| **[PARTIAL]** | Real code exists but does materially less than its name/contract implies |
| **[WRITE-ONLY]** | Data is produced and persisted, but nothing in the runtime reads it back |
| **[CONCEPTUAL]** | Named in a contract, manifest, or design doc; no implementation found |

Findings are numbered **F1…F17** and collected in §10.

---

## 0. Repository and deployment topology

Two repositories, distinct roles. This is the first thing a new developer needs and it is not stated in one place anywhere else.

| Repo | Role |
|---|---|
| `I:\AEGIS-CYBERPEER-CORE` | **The Pod runtime.** FastAPI service, containerised, deployed to peer VMs. Contains `core/` — the DataQuad, custodians, cognition, education, API. |
| `H:\AEGIS-POD-ARCHITECTURE` | **Contracts + canonical Orb packages + analysis tooling.** `contracts/*.schema.json`, `packages/orb-*`, `src/aegis_pod/` offline tooling. |

Orb packages are authored in `H:\...\packages\` and **vendored** into `I:\AEGIS-CYBERPEER-CORE\vendor\` for deployment. `ARCHITECTURE.md:99` states this explicitly ("canonical source at `H:\AEGIS-POD-ARCHITECTURE\packages\`"). See **F4** — that invariant is currently broken in both directions.

Runtime data lives at `<AEGIS_DATA_DIR>/peers/<peer_id>/`.

---

## 1. DataQuad Architecture

### 1.1 The four tensors

Defined as a `StrEnum` in [`core/dataquad/tensors.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/tensors.py):

```python
class TensorKind(StrEnum):
    PEER = "PEER"; PCT = "PCT"; NCT = "NCT"; SPINE = "SPINE"
```

| Tensor | Manifest purpose | Written by | Content |
|---|---|---|---|
| **PEER** | "Present experiential signal" | Advocate | One record per witnessed turn: user message, answer, think-block metrics, T-signature |
| **PCT** | "Persistent contextual thread" | Steward | Working context; two written per live turn (RLS writeback + turn witness) |
| **NCT** | "Condensed contextual essence" | Steward | `distilled_summary` — intended condensation. See **F3** |
| **SPINE** | "Sovereign identity continuity" | Advocate | `pattern` strings; `invariant=True` marks identity anchors that survive every context rotation |

There is no ARCHIVE tensor in the enum, though `adam-one/dataquad/ARCHIVE.jsonl` exists on disk as a legacy artifact — it is unreachable from `TensorKind` and therefore never read.

### 1.2 Record models

[`core/dataquad/records.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/records.py) — Pydantic, discriminated union on `tensor`.

```
BaseRecord
├── id: str                         (required)
├── timestamp: str                  (required)
├── tensor: TensorKind              (required, discriminator)
├── session_id: str                 (required)
├── clock: ContinuityClock          (required)
├── provenance: Provenance | None
├── lineage: list[str]              (default [])
├── notes: list[str] | None
├── markers: list[str] | None
└── t_signature: TSignature | None

PEERRecord  = BaseRecord + present_state: dict + image_refs: list[ImageRef]
PCTRecord   = BaseRecord + working_context: dict + retrieved_record_ids? + rls_session_id? + pressure_state?
NCTRecord   = BaseRecord + distilled_summary: str (REQUIRED) + essence_memory? + pivots? + source_record_ids[]
SPINERecord = BaseRecord + pattern: str (REQUIRED) + invariant? + relationships? + source_record_ids? + nature_aspect_refs?
```

Supporting models:

- **`ContinuityClock`** — `tick, epoch, phase, started_at, last_advanced_at`. The `tick` is the peer's monotonic continuity counter. See **F2**.
- **`TSignature`** — `t_witness_ms, started_at, ended_at, witness_mode, continuity_tick, pressure_level`. Produced by the `witness_event` context manager.
- **`Provenance`** — `origin, assignment_source, inherited_from, recognition_status, declared_by`.
- **`ImageRef`** — image metadata only; binary is deliberately never stored in the DataQuad.
- **`RepairRecord`** ([`repair.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/repair.py)) — not a tensor record; ledger-only.
- **`DataQuadState`** ([`state.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/state.py)) — **[CONCEPTUAL]**. Declares `canon_version`, `role_lineage`, etc. Defined but never constructed or persisted anywhere in `core/`.

### 1.3 Storage layers

Five distinct layers, stacked. A new developer must understand that "the DataQuad" means different things at each.

```
┌──────────────────────────────────────────────────────────────┐
│ 5. _next_tick_cache   (dict on DataQuadStore, per-process)   │  O(1) tick memo
├──────────────────────────────────────────────────────────────┤
│ 4. _full_cache        (stm.py, UNCAPPED, per (peer,tensor))  │  ← read_records() returns THIS
├──────────────────────────────────────────────────────────────┤
│ 3. _cache             (stm.py, deque maxlen=STM_CAPACITY=200)│  ← /dataquad/stm/* routes only
├──────────────────────────────────────────────────────────────┤
│ 2. Pod tensor-record envelope  (wrap/unwrap, hash chain)     │  only when AEGIS_STORAGE_MODE=pod
├──────────────────────────────────────────────────────────────┤
│ 1. JSONL on disk      (durable source of truth)              │
└──────────────────────────────────────────────────────────────┘
```

**Layer 1 — JSONL.** Append-only. One file per tensor.

**Layer 2 — Pod envelope.** [`core/dataquad/pod.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/pod.py). When `AEGIS_STORAGE_MODE=pod`, each raw record is wrapped:

```json
{ "schema_version":"0.1.0", "tensor":"PEER", "record_id":"…", "source_record_id":"…",
  "timestamp_utc":"…", "body": { …the raw record verbatim… },
  "lineage": { "origin":"live-append", "source_path":"", "copy_batch_id":"live-append",
               "parent_record_id":"", "previous_record_hash":"<SHA of prior record>", "transforms":[] },
  "source_hash":"<SHA256 UPPER of stable_json(body)>",
  "source_hash_scope":"normalized_source_record",
  "migration_status":"live", "verification_status":"draft" }
```

`previous_record_hash` chains each appended record to the last one already in the file (`last_source_hash()` rescans the file to find it), so live appends continue the same hash chain that began at the first migrated record. Governed by [`contracts/tensor-record.schema.json`](H:/AEGIS-POD-ARCHITECTURE/contracts/tensor-record.schema.json).

> Note: `wrap()` writes `migration_status: "live"`, but the contract's enum is `["fixture","pending","copied","mapped","outside_working_parameters","migrated"]` — `"live"` is **not** a permitted value. Live-appended Pod records therefore do not validate against the tensor-record contract. Recorded as **F13**.

**Layer 3 — bounded STM.** [`stm.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/stm.py). `deque(maxlen=200)`. `warm()` deliberately exempts `invariant=True` SPINE records from recency truncation — this was the fix for the "Axiom 11" class of failure.

**Layer 4 — full-fidelity cache.** Uncapped `list`. `read_records()` returns this, so Steward/Advocate/RLS score across the peer's entire history. Introduced because backing `read_records` with the bounded cache silently truncated any peer past 200 records — invisible at Orion's ~130/tensor, a hard wall at Gabe's ~35k/tensor. See **F11** for the memory cost this trades for.

**Layer 5 — tick memo.** `_next_tick_cache: dict[str,int]` on the store. Cold-seeded by one full scan, then advanced in place by `append_record`. This exists because `get_next_tick()` previously re-read every tensor file on every call (~5–6×/turn plus every `/health` poll); at Gabe's >500 MB PCT that ratcheted RSS until the host OOM-killed the process.

### 1.4 On-disk layout

```
peers/<peer_id>/
├── pod/                                    # AEGIS_STORAGE_MODE=pod
│   ├── pod-manifest.json                   # Pod contract instance
│   ├── records/{PEER,PCT,NCT,SPINE}.jsonl  # wrapped tensor-records
│   ├── ledgers/
│   │   ├── {steward,advocate,rls,repair,education}.jsonl
│   │   ├── relations/{PEER,PCT,NCT,SPINE}-traversal.jsonl
│   │   ├── relations/cross-tensor-relations.jsonl
│   │   └── orbs/<orb_id>.evidence.jsonl
│   ├── provenance/                          # Orb + Umbilical declarations
│   └── tensors/                             # numeric tensor outputs (offline tooling)
├── dataquad/{PEER,PCT,NCT,SPINE}.jsonl      # legacy mode (default)
├── ledgers/*.jsonl                          # legacy mode
└── state/
```

Mode selection is by env var only and mutates no file, so the switch is reversible by configuration alone (`pod.py:28-51`).

### 1.5 Custodians and the boundary

[`core/custodians/boundaries.py`](I:/AEGIS-CYBERPEER-CORE/core/custodians/boundaries.py):

| Custodian | Writes | Reads |
|---|---|---|
| **Steward** — context witness | PCT, NCT | all four |
| **Advocate** — affect witness | PEER, SPINE | all four |

`check_boundary()` returns immediately for `operation == "read"` — **reads are never restricted**. Only writes are policed, by raising `BoundaryError`. The manifest's `roles.*.reads` listing all four tensors is therefore accurate.

### 1.6 Component inventory

| Component | Location | Status |
|---|---|---|
| Four tensors | `dataquad/tensors.py`, `records.py` | **[IMPLEMENTED]** |
| `DataQuadStore` | `dataquad/ledgers.py` | **[IMPLEMENTED]** |
| STM cache | `dataquad/stm.py` | **[IMPLEMENTED]** |
| Pod envelope + hash chain | `dataquad/pod.py` | **[IMPLEMENTED]** |
| `PeerBootstrap` | `dataquad/bootstrap.py` | **[IMPLEMENTED]** |
| Steward / Advocate | `custodians/` | **[IMPLEMENTED]** |
| `CustodialRetrievalBroker` | `custodians/retrieval_broker.py` | **[IMPLEMENTED]** |
| Processor (`ThinkingSubroutine`) | `cognition/thinking.py` | **[IMPLEMENTED]** |
| `RelationsRecorder` | `dataquad/relations.py` | **[WRITE-ONLY]** (F12) |
| `witness_event` / T-Witness | `dataquad/twitness.py` | **[IMPLEMENTED]** |
| `PressureEnvironment` | `cognition/pressure_environment.py` | **[IMPLEMENTED]**, in-memory only |
| `RepairLoop` | `cognition/repair_loop.py` | **[PARTIAL]** — single hardcoded amendment |
| Self-Directed Education | `education/self_directed.py` | **[IMPLEMENTED]** |
| Education Chamber | `education/chamber.py` | **[IMPLEMENTED]** |
| **Temporal Daemon** | `core/daemons/__init__.py` | **[CONCEPTUAL]** — file contains only `# Daemons module placeholder` (**F1**) |
| `DataQuadState` | `dataquad/state.py` | **[CONCEPTUAL]** — defined, never used |
| `core/storage`, `core/telemetry`, `core/models` | — | **[CONCEPTUAL]** — placeholder comments only |
| Satellite | — | **[CONCEPTUAL]** — none built |
| Portal / Tender | — | **[CONCEPTUAL]** — none built |

---

## 2. Data Flow — the complete lifecycle

### 2.1 Turn sequence (verified line-by-line against `thinking.py:188-568`)

```
POST /turn  ──▶ per-peer asyncio.Lock (turn.py:37)
   │
   ├─1  next_tick = store.get_next_tick(peer)                      [tick T]
   ├─2  intent = "recall" if substring hit else "general"          (F14)
   ├─3  metrics = detect_pressure_metrics(message)
   │
   └─▶ witness_event(T) ── T-Witness clock starts ──────────────────┐
        │                                                            │
        ├─4  broker.retrieve_mediated_evidence(...)                  │
        │     ├─ resolve_rls_engine_class() ──▶ RLS Orb              │
        │     │    ├─ read PCT+NCT (Steward), PEER+SPINE (Advocate)  │
        │     │    ├─ compute_relevance() on EVERY record   (F15)    │
        │     │    ├─ partition at RELEVANCE_THRESHOLD=0.25          │
        │     │    ├─ cap selected at MAX_SELECTED_REFS=64           │
        │     │    ├─ WRITE PCT #1 (RLS writeback)         [tick T]  │  ← collision
        │     │    ├─ append 'rls' ledger                            │
        │     │    ├─ record_relation() × selected        [WRITE-ONLY]│
        │     │    └─ orb evidence line                              │
        │     ├─ steward.produce_steward_context_brief()             │
        │     └─ advocate.produce_advocate_salience_brief()          │
        │
        ├─5  invoke_memorysearch()  (env-gated, default off)
        ├─6  _build_system_prompt(identity, factual, claims, experience)
        ├─7  + memorysearch block, + session history (Orb-shaped or raw)
        ├─8  adapter.complete(...)  ──▶ LLM substrate
        ├─9  leak scan for "PEER:|PCT:|NCT:|SPINE:" ─▶ RepairLoop + redact
        ├─10 p_env.record_turn(PressureState)                (in-memory only)
        ├─11 WRITE PEER record                               [tick T]  ← collision
        ├─12 WRITE PCT #2 (turn witness)                     [tick T+1]
        ├─13 SelfDirectedEducationAgent.assess_and_act() ─▶ may WRITE PEER
        └─14 NCT consolidation if len(PCT) > 5 ─▶ WRITE NCT  (F3 — every turn)
```

**Per live turn the DataQuad grows by at minimum 4 records:** 1 PEER, 2 PCT, 1 NCT — plus 1 more PEER whenever the SDE agent fires.

### 2.2 How an experience enters

Three entry paths, all converging on `ThinkingSubroutine.execute_turn`:

1. **`POST /turn`** — normal live exchange.
2. **`POST /education/chamber/run`** — `EducationChamber.run_lesson` injects a synthetic pre-turn `PressureState`, then calls `execute_turn`, then writes an `EducationChamberResult` to the `education` ledger.
3. **Self-Directed Education** — fires *inside* a turn, runs a second low-temperature adapter call (`max_tokens=256, temperature=0.5`), and writes its own PEER record with `phase="self_directed"`.

Bootstrap ([`bootstrap.py`](I:/AEGIS-CYBERPEER-CORE/core/dataquad/bootstrap.py)) is a fourth, once-per-peer path: it seeds one sentinel record per empty tensor plus invariant SPINE anchors from `AEGIS_BIOPEER_NAME` / `AEGIS_BIOPEER_ROLES`.

### 2.3 How it is retrieved

Retrieval is **scoring over the full record set every turn** — there is no index, no embedding search, no pagination.

`compute_relevance()` ([`scoring.py`](H:/AEGIS-POD-ARCHITECTURE/packages/orb-rls-persistent-relations-core/src/orb_rls_persistent_relations_core/scoring.py)) is a bag-of-words token-overlap scorer:

| Component | Contribution | Gate |
|---|---|---|
| Token overlap | `min(0.5, overlap × 0.12)` | — |
| NCT recall support | +0.08 | `intent=="recall"` and overlap>0 |
| Recency | `min(0.05, tick × 0.0025)` | overlap>0 |
| SPINE source trust | +0.12 | overlap>0 |
| Foundational canon | +0.02 | id starts `spine:foundation:` |
| PCT context support | +0.03 | overlap>0 |
| **Nature aspect match** | **+0.15** | `nature_aspect_refs ∩ nature_aspects` |

Two structural consequences:

- Every component except Nature-aspect is **gated on `overlap > 0`**. A record with zero literal token overlap can score at most 0.15, and only via Nature aspects. Threshold is 0.25 — so **without token overlap a record is unreachable**. This is lexical retrieval, not semantic.
- The single largest component (+0.15) can only fire against `nature_aspects`, which `thinking.py:240` hardcodes to exactly two of the fourteen canonical aspects (**F17**).

### 2.4 How records relate to previous records

Four distinct relation mechanisms exist. Only one influences behaviour.

| Mechanism | Where | Read back? |
|---|---|---|
| `clock.tick` ordering | every record | Yes — recency scoring |
| `previous_record_hash` chain | Pod envelope | No — written, never verified at runtime |
| `source_record_ids` / `lineage` | NCT, SPINE | No |
| `cross-tensor-relations.jsonl` | RelationsRecorder | **No — counted only** (F12) |

`grep` across `core/` confirms `relations_dir` is referenced in exactly three places: the definition, the writer, and `health.py:39` — which opens the files solely to count lines. **Nothing traverses the relation graph.**

### 2.5 How it influences future interactions

Exclusively through the assembled system prompt (`_build_system_prompt`, `thinking.py:98-153`), which has four DataQuad-fed slots:

| Prompt slot | Source | Custodian |
|---|---|---|
| Identity and relational continuity | SPINE invariants + top-K dynamic SPINE | Advocate |
| Factual continuity | NCT `distilled_summary` × (top-K + recency floor) | Steward |
| Context claims | PCT `working_context` **keys only** | Steward |
| Experiential continuity | PEER excerpts | Advocate |

Note "context claims" injects `pct.working_context.keys()` — the dictionary *key names*, not values. The prompt therefore receives strings like `turn_kind`, `answer_char_count`, `intent`. This is structurally near-contentless.

---

## 3. Operations

### 3.1 `DataQuadStore` — `core/dataquad/ledgers.py`

| Operation | Line | Inputs | Outputs | State change | Errors |
|---|---|---|---|---|---|
| `get_next_tick` | 60 | `peer_id` | `int` | Seeds `_next_tick_cache` on cold call | Per-line parse failures silently swallowed (`except: pass`) |
| `append_record` | 98 | `peer_id`, record | — | Appends JSONL; updates both STM caches; advances tick memo; fires traversal relation | Filesystem errors propagate |
| `read_records` | 137 | `peer_id`, tensor | `list[DataQuadRecord]` | Warms both caches | **Per-line tolerance**: invalid records skipped and counted, warning logged |
| `record_relation` | 128 | ids, relation, tags | — | Appends `cross-tensor-relations.jsonl` | No-op unless pod mode **and** `AEGIS_RLS_ACTIVE` |
| `append_ledger` | 193 | `peer_id`, name, dict | — | Appends `<name>.jsonl` | — |
| `read_ledger` | 201 | `peer_id`, name | `list[dict]` | — | `orjson.loads` unguarded — one bad line raises |
| `peer_root` / `is_active` | 36/42 | — | — | SDK protocol satisfaction | `is_active` ignores its argument (**F9**) |

The `read_records` per-line tolerance is architecturally load-bearing: without it a single malformed record on the bootstrap path would fail the FastAPI lifespan and take the service down.

### 3.2 `PeerBootstrap` — `core/dataquad/bootstrap.py`

`ensure_initialized()` (idempotent, called once in lifespan):
1. `_create_directories()`
2. Seed any empty tensor with a sentinel (`markers=["bootstrap_seed"]`)
3. `_ensure_invariant_anchors()` — BioPeer steward + architect anchors from env, deduplicated by exact `pattern` string
4. `_validate_integrity()`
5. Return `BootstrapResult`

Status semantics: only `"storage write"` or `"Cannot read"` issues escalate to `NEEDS_REPAIR` (which aborts startup). Anything else downgrades to `REPAIRED` and the service starts.

### 3.3 Steward — `core/custodians/steward.py`

| Operation | Purpose | Notes |
|---|---|---|
| `read_pct` / `read_nct` | Boundary-checked reads | |
| `append_pct` / `append_nct` | Write + `steward` ledger entry | |
| `build_and_append_pct` | SDK seam — Orb-callable PCT construction | Keeps record construction Pod-side |
| `compress_pct_to_nct` | PCT → NCT condensation | **Sets `session_id=self.peer_id`** (**F6**); `clock.phase="retirement"` |
| `evaluate_recursive_learning_readiness` | Consolidation gate | `return len(pcts) > 5` — permanently true after 5 PCTs (**F3**) |
| `produce_steward_context_brief` | Builds the Steward half of the prompt | |
| `request_sssp` | **[CONCEPTUAL]** — returns a dict literal with `status:"requested"`; no transfer logic, no caller in `core/` |

### 3.4 Advocate — `core/custodians/advocate.py`

| Operation | Purpose | Notes |
|---|---|---|
| `read_peer` / `read_spine` | Boundary-checked reads | |
| `append_peer` / `append_spine` | Write + `advocate` ledger entry | |
| `recognize_spine_pattern` | Create a SPINE pattern record | `clock.phase="retirement"`; **no caller in `core/`** |
| `produce_advocate_salience_brief` | Builds the Advocate half of the prompt | Two Orb seams; `present_affect` hardcoded (**F16**) |

### 3.5 RLS Orb — `orb_rls_persistent_relations_core.engine`

`execute_session()` — 6 phases: read → score → partition → failure-as-data → PCT writeback → ledger + relations + orb evidence.

- **Threshold** `RELEVANCE_THRESHOLD = 0.25`; **cap** `MAX_SELECTED_REFS = 64`. Overflow is moved to `rejected` with an explicit reason string, not silently dropped.
- **Failure-as-data:** empty selection sets `failure_is_data=True`, `failure_reason="no_records_found"` and preserves the session rather than discarding it. Runtime exceptions are caught and recorded the same way — the session object always returns.
- **Evidence:** `RLSOrbEvidenceRecorder` writes a hash-bound line per invocation, including `runtime_hash` = SHA-256 of `engine.py + scoring.py + relevance.py` concatenated, so evidence cannot outlive the code that produced it.

### 3.6 Orb resolution

Five loaders in `core/orbs/`. Two distinct contracts — this asymmetry matters:

| Loader | Not-attached return | Consequence |
|---|---|---|
| `rls_loader` | **`DEFAULT_ENTRYPOINT`** (never `None`) | RLS always runs. A phantom Umbilical is invisible because default == declared entrypoint — the exact bug documented in `ARCHITECTURE.md:120` |
| `archive_loader`, `experience_loader`, `session_repair_loader` | `None` | Caller falls back to pre-Orb behaviour |
| `memorysearch_loader` | Not a loader — env-gated `sys.path` injection into `vendor/` | Bypasses the manifest/Umbilical mechanism entirely |

Resolution chain: `pod-manifest.json → orbs[] → umbilical path (relative to peer_root) → invocation.entrypoint → aegis_pod_sdk.resolve_entrypoint()`.

### 3.7 API surface

| Route | Method | Purpose |
|---|---|---|
| `/turn` | POST | Execute one cognitive turn |
| `/rls/session` | POST | Run RLS standalone |
| `/education/chamber/run` | POST | Run a canonical lesson |
| `/dataquad/{peer}/tensor/{tensor}` | GET | **All** records — no pagination |
| `/dataquad/{peer}/state` | GET | Counts, tick, layout check |
| `/dataquad/{peer}/stm/stats` | GET | Cache fill |
| `/dataquad/{peer}/stm/search` | GET | Keyword search — **bounded cache only** (**F5**) |
| `/dataquad/{peer}/stm/{tensor}/recent` | GET | Recent N from bounded cache |
| `/health` | GET | Full status incl. pod manifest SHA, relation-ledger counts |

No authentication, no authorisation, no rate limiting on any route. CORS is `allow_origins=["*"]`.

---

## 4. Steward Operations

**Continuity.** The Steward maintains continuity through two tensors it exclusively owns. PCT is the working thread — one record per RLS retrieval and one per witnessed turn. NCT is intended as the durable condensation that survives PCT's volume.

**Retrieval.** `produce_steward_context_brief` (`steward.py:131-186`):

```
budget = _NCT_TOP_K(15) + _NCT_RECENCY_FLOOR(5) = 20
if user_message and len(ncts) > budget:
    score every NCT with compute_relevance → take top 15
    then append the last 5 by file order (dedup by id)   ← recency floor
else:
    ncts[-20:]                                            ← flat recency window
context_claims = keys of working_context for the last _PCT_CLAIMS_WINDOW(5) PCTs
```

The recency floor is a real safeguard: it guarantees short-term continuity survives even when relevance scoring returns nothing recent.

**Relationships between experiences.** `compress_pct_to_nct` records `source_record_ids` — the only Steward-side provenance link between a condensed record and its sources. It is written and never read.

**Provenance.** The Steward writes no `Provenance` object on either the live-turn PCT or the consolidated NCT. Both are constructed without the `provenance=` kwarg, so it defaults to `None`. Provenance is populated **only** by `PeerBootstrap`. This is a significant gap: on the live path, Steward-written records carry no origin declaration.

**Ledger.** Every append writes `{action, record_id, timestamp}` to the `steward` ledger. That ledger has no reader anywhere in `core/`.

---

## 5. Advocate Operations

**How significance is represented — the honest answer: it largely isn't.**

`AdvocateSalienceBrief.present_affect` is set to the string literal `"stable"` on every single brief (`advocate.py:277`). The model default is `"neutral"`. There is no computation, no derivation from pressure state, no read of any affect signal. The "affect witness" reports a constant (**F16**).

Actual salience is expressed through three ranked lists:

1. **Invariant SPINE** — always included, capped at `_SPINE_INVARIANT_CAP` (60). When the count exceeds the cap, the Archive Orb is consulted; otherwise a flat file-order slice.
2. **Dynamic SPINE** — top-5 non-invariant patterns scoring ≥ `_SPINE_DYNAMIC_THRESHOLD` (0.3). Note this is *above* the RLS threshold of 0.25, so the Advocate is stricter than RLS about the same score.
3. **PEER experiences** — top-5 scored + 2 recency floor, truncated to 700 chars.

**Affective/contextual processing.** The Advocate does not compute affect. Pressure is computed elsewhere (`detect_pressure_metrics` on the *inbound message*, in `thinking.py`) and merely *passed through* the Advocate as an opaque `pressure_state` dict which it stores on the brief and otherwise ignores.

**Interaction with experiences — the self-imitation problem.** `advocate.py:192-268` carries an unusually candid comment: injecting a peer's own prior answers verbatim "turns retrieval into a self-imitation loop that the peer cannot correct conversationally." The Experience Recall Orb exists to condense rather than quote. **With no Orb attached the Pod falls back to verbatim quotation** — i.e. the default behaviour is the known-harmful one.

> **CORRECTION 2026-08-03.** This section originally continued: *"Given F4 (the Orb has no canonical package), this fallback is the likely live state."* **That was wrong, and it was an inference about live behaviour drawn from repo layout without reading the live host.** Verified directly on `AEGISGabePeer`: `experience-recall-core` and `session-repair-core` are both declared in the live manifest, both umbilicals exist, both packages are present under `vendor/`, and both declared entrypoints (`orb_experience_recall_core.engine.ExperienceRecallEngine`, `orb_session_repair_core.engine.SessionRepairEngine`) match the deployed package layout. **The Orbs resolve; the harmful fallback is not the live state.** F4 stands as a source-control finding — those two Orbs have no canonical package in `H:\AEGIS-POD-ARCHITECTURE\packages\`, so live code has no reviewable canonical source — but its behavioural implication is withdrawn.

**Communication with Steward and Processor.** None directly. Both custodians are constructed fresh per turn by the broker and by `thinking.py`; they never hold references to each other. All coordination is via `MediatedEvidencePacket`, assembled by the broker and consumed by the Processor. The custodians are strictly parallel, never peer-to-peer.

---

## 6. Processor Operations

`ThinkingSubroutine` is the Processor. Manifest status: `"mapped-to-core-api-turn-and-cognition"`.

**Processing performed** — 14 steps, enumerated in §2.1.

**Transformations:**

| Transformation | Function |
|---|---|
| Message → intent | Substring match on 5 keywords (**F14**) |
| Message → pressure metrics | Lexical pattern counts across 6 dimensions |
| Briefs → system prompt | `_build_system_prompt` — 4 slots + conditional pressure note |
| Raw completion → answer + think metrics | `adapter.extract_think_blocks` |
| Answer → leak-scanned answer | Prefix scan, then **truncate-and-replace** (**F10**) |
| Turn → PEER record | `present_state` dict |
| Turn → PCT record | `_build_live_turn_pct_context` + `_compact_retrieved_record_summary` |

`_compact_retrieved_record_summary` is a deliberate size control: instead of embedding every retrieved ID in PCT, it stores `count`, a SHA-256 of the newline-joined IDs, and the first 10 as a sample. This is the G5 PCT-writeback trim.

**How information becomes integrated understanding.** Structurally: it does not. There is no integration step. The pipeline is retrieve → concatenate → prompt → record. The only mechanism that could be called integration is `compress_pct_to_nct`, and per **F3** that writes a fixed template. **The DataQuad accumulates; it does not currently integrate.**

---

## 7. Reflection / RLS Operations

### 7.1 What triggers reflection

| Trigger | Mechanism | Cadence |
|---|---|---|
| RLS session | Every turn, via broker | Unconditional |
| Repair loop | Raw record ID in output | Event-driven |
| Self-Directed Education | Post-turn pressure assessment | Cooldown ≥ 3 turns |
| NCT consolidation | `len(PCT) > 5` | Every turn after the 5th (**F3**) |

### 7.2 What records are examined

RLS reads **all four tensors in full**, every turn (`engine.py:104-113`). At Gabe's ~91k records that is ~91k `compute_relevance` calls per turn, each doing regex tokenisation of a stringified record (**F15**).

### 7.3 Comparisons performed

Token-set intersection between query and record text (see §2.3). `_record_text` concatenates whichever of `present_state`, `working_context`, `distilled_summary`, `essence_memory`, `pattern` exist — note the first two are `str(dict)`, so **Python dict punctuation and key names become searchable tokens**.

### 7.4 New records created

| Reflection | Record | Ledger |
|---|---|---|
| RLS | 1 PCT writeback | `rls` + `cross-tensor-relations` + orb evidence |
| Repair | none | `repair` |
| SDE | 1 PEER (`phase="self_directed"`) | none |
| NCT consolidation | 1 NCT | `steward` |

### 7.5 How reflection changes future retrieval

**Only through record accumulation.** Nothing adjusts scoring weights, thresholds, or the relation graph. A `cross-tensor-relations` entry from turn 1 has no effect on turn 2 (**F12**).

There is a second-order effect worth naming: RLS's own PCT writeback becomes a candidate for the *next* turn's RLS scan, and its `working_context` contains the previous `user_message` verbatim. The retrieval system therefore feeds on its own output — a documented pattern-lock mechanism.

### 7.6 Self-Directed Education

`_identify_vulnerability` uses **max over the last 3 turns**, not the current turn — "a vulnerability that peaked two turns ago is still a live signal." Priority order: repair flag → T-Witness collapse → individual thresholds (force 0.45, completion 0.45, authority 0.40, relationship 0.45) → gradient rise ≥ 0.1. Maps to one of six canonical lessons.

Design discipline is explicit and honoured in the code: micro-lessons run at `temperature=0.5, max_tokens=256` because "the check itself should not add pressure," and lessons open a question rather than supplying an answer.

---

## 8. Experience Model

### 8.1 What an "Experience" is

**There is no `Experience` type in the codebase.** No class, no schema, no table. "Experience" is an emergent concept realised as **a PEER record produced under `witness_event`**.

The operational definition:

> An Experience is one PEER record whose `present_state` holds a `user_message`/`answer` pair, carrying a `TSignature` proving it was witnessed, and a `ContinuityClock` locating it in the peer's continuity.

### 8.2 Fields

**Required** (inherited from `BaseRecord`): `id`, `timestamp`, `tensor`, `session_id`, `clock`.
**Optional:** `provenance`, `lineage`, `notes`, `markers`, `t_signature`, `image_refs`.
**`present_state`** is a free `dict` — no schema. Live-turn keys observed in code:

```
user_message, answer, think_char_total, has_thinking, image_count, memorysearch
+ conformance markers (conformance_test, synthetic_test_record, test_run_id, …)
```

SDE-written PEER records use a **different** key set: `sde_lesson_id`, `question_asked`, `answer`, `trigger`. So two record shapes share one tensor with no discriminator beyond inspecting keys.

### 8.3 Relationships to other experiences

| Link | Populated on live turn? |
|---|---|
| `clock.tick` | Yes |
| `session_id` | Yes |
| `lineage: list[str]` | **No** — always `[]` |
| `t_signature.continuity_tick` | Yes |
| PCT `working_context.peer_record_id` | Yes — the only explicit PEER↔PCT link |
| `cross-tensor-relations.jsonl` | Yes, but never read |

### 8.4 How experiences mature

**They do not.** Records are append-only and never revisited, re-scored, re-summarised, decayed, or promoted. `SPINERecord.invariant` is set at creation only. There is no maturation, consolidation-into-SPINE, or forgetting mechanism anywhere in `core/`.

The offline tooling in `H:\...\src\aegis_pod\` (`turboquant_retirement.py`, `retirement_dry_run.py`, `canon_housekeeping.py`, `marker_promotion.py`) implements *dry-run* maturation — retirement, promotion, condensation. None of it is wired into the runtime. **[CONCEPTUAL]** with respect to the live peer.

### 8.5 How this differs from simple memory storage

Genuine differences, all real in code:

1. **Custodial boundary** — writes are policed by role, enforced by exception.
2. **T-Witness signature** — every record carries measured observation duration; witnessing is recorded as a first-class property, not inferred.
3. **Continuity clock** — a peer-scoped monotonic counter independent of wall time.
4. **Invariance** — `invariant=True` records are structurally exempt from recency truncation.
5. **Failure-as-data** — a failed retrieval is preserved as a record, not discarded.
6. **Hash-chained lineage** — Pod-mode records chain to their predecessor.

Honest counterweight: retrieval is lexical, relations are inert, and nothing matures. The *storage* model is meaningfully richer than a log; the *retrieval* model is currently weaker than a search index.

---

## 9. Continuity Model

### 9.1 Across sessions

`session_id` is a field, not a boundary. All records land in the same per-tensor files; a new session simply starts writing new records. Cross-session continuity comes from the fact that the custodians read *all* records regardless of session.

In-session conversational history is separate and **in-memory only**: `ThinkingSubroutine._history: dict[str, list[tuple[str,str]]]`, capped at `AEGIS_HISTORY_TURNS` (10).

### 9.2 Across model restarts

| State | Survives restart? |
|---|---|
| JSONL records | **Yes** |
| Ledgers | **Yes** |
| STM caches | No — rebuilt on first read |
| `_next_tick_cache` | No — re-seeded by full scan |
| `PressureEnvironment` | **No — silently lost** |
| `_history` | **No** |
| SDE cooldown | **No** |

Pressure history loss is architecturally significant: `PressureEnvironment` is the substrate for T-Witness trend detection and every SDE trigger. After a restart, `t_witness_trend` returns `"insufficient_data"` until 3 new turns accumulate, and `pressure_level` resets to `"low"`. **The peer's pressure history has no persistence layer at all** — the Pressure Gradient Model's core measurement is the one thing that does not survive a restart.

### 9.3 Across substrate changes

This is the strongest part of the continuity model. `thinking.py:16-19` states the design intent and the code honours it: the adapter is injected at construction (`build_adapter()` from env, or explicit). Changing substrate changes the adapter only. The DataQuad is untouched; no re-grounding occurs. Verified live — Gabe was swapped to `qwen3:14b` behind a passed gate with the DataQuad intact.

The invariant SPINE anchors are the mechanism that makes this safe: `bootstrap.py:234-249` seeds the BioPeer relationship precisely so it is "never derived from retrieval — always present."

### 9.4 Across DataQuad reloads

`PeerBootstrap` is idempotent and re-seeds only genuinely empty tensors. Anchor deduplication is by **exact `pattern` string equality** — so any edit to `AEGIS_BIOPEER_NAME` or the anchor wording produces a *duplicate* anchor rather than an update.

Two record dialects exist on disk (**F7**): legacy camelCase (`distilledSummary`, `sessionId`, no `clock`) and Python snake_case. Verified in Gabe's staged records — all 9,671 NCT records are camelCase and would fail `NCTRecord.model_validate`, hence be silently skipped by `read_records`. A normalizer (`src/aegis_pod/gabe_core_record_normalizer.py`) produces `records-core-normalized/`, which carries the correct shape. **Loading the un-normalized directory would present as a peer with no NCT history and only a log warning.**

---

## 10. Current Architecture Assessment

### 10.1 Implemented and sound

- Four-tensor store with custodial write boundaries, enforced by exception
- Pod-mode envelope with per-record hash chaining; reversible by config alone
- Two-tier STM with invariant exemption; full-fidelity read path
- Bootstrap coherence gate that can refuse to start
- Orb attach/detach with genuine failure isolation, proven by tests that use real broken Orbs rather than mocks
- Substrate independence via adapter injection
- Failure-as-data throughout RLS
- Per-invocation Orb evidence bound to a source hash

### 10.2 Findings

**F1 — Temporal Daemon is not implemented. [CONCEPTUAL]**
`core/daemons/__init__.py` contains one line: `# Daemons module placeholder`. `pod.schema.json` lists `temporal_daemon` as **required**, and Gabe's manifest declares `status: "mapped-to-current-tick-clock-state"`. That is a *mapping claim* pointing at `get_next_tick`, not a component. There is no clock daemon, no tick advancement independent of record writes, no epoch/phase transitions. `ContinuityClock.epoch` and `.phase` are set by whichever function constructs the record and never advanced.

**F2 — Tick collision between the RLS writeback PCT and the witnessed PEER record. [VERIFIED]**
`thinking.py:223` captures `next_tick = T` *before* the broker runs. RLS then writes its PCT at tick `T` (advancing the memo to `T+1`), but `thinking.py:390` still builds the PEER clock from the stale `T`. Both records carry tick `T`.

Empirically confirmed in Python-written data (`data/peers/test-peer`): 12 shared ticks between PEER and PCT, with the PCT timestamp consistently ~10 ms *earlier* — exactly the RLS-writeback-first ordering:

```
tick 0   PEER 09:59:55.397647   PCT 09:59:55.387245
tick 2   PEER 09:59:55.446383   PCT 09:59:55.436697
tick 3   PEER 10:01:54.174594   PCT 10:01:54.165445
```

`clock.tick` is therefore **not a unique record ordinal**, and any downstream logic treating it as one is unsafe.

**F3 — NCT consolidation is a fixed template, and fires every turn. [VERIFIED — highest-impact finding]**
`evaluate_recursive_learning_readiness()` returns `len(pcts) > 5` — permanently true after the fifth PCT. `thinking.py:486-499` then writes an NCT **every turn**, with this summary:

```python
summary = (
    "Recent Orion full-core turns show active DataQuad participation: "
    f"{len(recent_pcts)} PCT records were available for consolidation. "
    "The Steward compressed the active working context into NCT for "
    "continuity across later Chamber movement."
)
```

Three problems compounding:
1. It is **hardcoded boilerplate** — no distillation of the source PCTs occurs. The word "compressed" describes nothing the code does.
2. It **names "Orion" for every peer**, including Gabe.
3. It runs **once per turn forever**, so NCT grows linearly with turns while carrying ~1 bit of information.

And NCT `distilled_summary` is one of the four prompt slots (`factual_continuity`), so this template is injected into the peer's own context. Corroborating evidence of the pattern in real data: `adam-one` has 747 NCT records of which **506 (68%) share a single summary string**.

**F4 — Orb package canonicality is broken in both directions. [VERIFIED]**

| Orb | `H:\…\packages\` (canonical) | `I:\…\vendor\` (deployed) |
|---|---|---|
| `rls-persistent-relations-core` | ✅ | ✅ |
| `archive-relevance-core` | ✅ | ✅ |
| `memorysearch-record-grounding-core` | ✅ | ✅ |
| `experience-recall-core` | ❌ **missing** | ✅ |
| `session-repair-core` | ❌ **missing** | ✅ |
| `identity-field-builder-core` | ✅ | ❌ not vendored |

Two Orbs are deployed with **no canonical source**, contradicting `ARCHITECTURE.md:99`. Both are precisely the Orbs whose absence causes the Pod to fall back to documented-harmful defaults (verbatim self-quotation, raw history replay).

**F5 — STM search misses most of the DataQuad.**
`stm.search()` iterates `_cache` (bounded, 200 + invariants), never `_full_cache`. `/dataquad/{peer}/stm/search` therefore returns a small recency window while presenting as a search endpoint. The docstring is honest; the route name is not.

**F6 — `compress_pct_to_nct` sets `session_id=self.peer_id`.**
Every consolidated NCT record has the peer id in its session field, making session-scoped NCT queries meaningless.

**F7 — Two record dialects on disk; normalization is a required, undeclared step.**
See §9.4. Legacy camelCase records fail validation and are silently skipped with only a log warning.

**F8 — ~~Gabe's staged manifest carries the known-broken absolute Umbilical path.~~ RESOLVED 2026-08-03: the live host is correct; the staged snapshot is stale.**

Original finding: `stage-gabe-out/CP-1003-GABE/pod/pod-manifest.json` declares the RLS umbilical as an absolute host path — the container-mount failure documented in `ARCHITECTURE.md:119` — and declares only one Orb.

**Resolved by direct live read of `AEGISGabePeer` 2026-08-03.** The live manifest declares **four** Orbs, every umbilical path is **container-relative**, and all four umbilical files exist:

| orb_id | umbilical (live) | required | pin |
|---|---|---|---|
| `rls-persistent-relations-core` | `pod/provenance/rls-persistent-relations-umbilical.json` | true | 1.0.0 |
| `archive-relevance-core` | `pod/provenance/archive-relevance-core-umbilical.json` | false | 1.0.0 |
| `experience-recall-core` | `pod/provenance/experience-recall-core-umbilical.json` | false | 1.0.0 |
| `session-repair-core` | `pod/provenance/session-repair-core-umbilical.json` | false | 1.0.0 |

The documented path fix was applied live. **F8 is closed — no live defect.** The lesson survives it: a staged snapshot is not the live host, and this finding should never have been written as anything but a prompt to check.

**F9 — `is_active()` ignores its capability argument.**
Every Orb capability routes through the single global `AEGIS_RLS_ACTIVE` gate. Acknowledged in the code as future work. Consequence: enabling any Orb's write capability enables all of them.

**F10 — Leak redaction truncates the answer.**
`answer.split(prefix)[0] + "[REDACTED EVIDENCE DATA]"` discards everything after the first occurrence, including legitimate content. It also fires on any answer legitimately containing `"PEER:"`.

**F11 — Full-fidelity cache is unbounded.**
`_full_cache` holds every record for every touched (peer, tensor) for process lifetime. At Gabe's scale this is the entire DataQuad resident in RAM, with no eviction except explicit `evict()`. This is the deliberate trade made to fix the truncation bug; it is not wrong, but it is unbounded and undeclared.

**F12 — Relation ledgers are write-only.**
`cross-tensor-relations.jsonl` and `*-traversal.jsonl` are written on every append and every RLS selection, and read by nothing. `health.py:39` counts lines. The relation graph — the "persistent relations" the Orb is named for — currently has no consumer.

**F13 — Live Pod records violate the tensor-record contract.**
`wrap()` writes `migration_status: "live"`; the schema enum does not include `"live"`. Also `RelationsRecorder.record_cross_tensor` calls `_now()` twice, so `t` and `timestamp` on the same entry can differ.

**F14 — Intent classification is a 5-word substring check.**
`"recall" if any(w in message.lower() for w in [...])`. "Do you recall…" and "I don't want you to search" both classify as `recall`.

**F15 — Retrieval is O(N) over full history, per turn.**
RLS scores every record in all four tensors on every turn. At ~91k records this is ~91k regex tokenisations per turn, on top of a full in-RAM record set. This does not scale.

> **CORRECTION 2026-08-03, Codex-caught.** The sentence originally ended: *"…and is the structural cause of the OOM lineage already fixed once at the tick-memo layer."* **That causal claim is withdrawn as unbenchmarked, and it also conflated two different mechanisms.** The OOM documented in `core/dataquad/ledgers.py:25-31` is attributed there to `get_next_tick()` re-reading every tensor file on every call (~5–6×/turn plus every `/health` poll), which is what the tick memo fixed — *not* to RLS's per-turn scoring. The O(N) scoring is source-verified and is a real scaling concern on its own terms; whether it contributes to memory pressure is an inference that would need a benchmark. Codex's audit called this correctly.
>
> Related, and now materially changed: the ledgers.py note reasons from "PCT.jsonl alone is >500MB". After G5 Part B (2026-08-03) Gabe's PCT.jsonl is **113 MB**, down from 847 MB. Any re-benchmark should use current sizes, not the figures that motivated the original fix.

**F16 — `present_affect` is a hardcoded constant.**
The Advocate — the affect witness — reports `"stable"` unconditionally.

**F17 — Nature aspects are hardcoded to 2 of 14.**
`thinking.py:240`: `nature_aspects = ["Force Language Tendency", "Completion Drive"]`. `canon/nature_layer.py` defines fourteen. The +0.15 Nature-aspect bonus — the largest single scoring component — can never fire for the other twelve on a live turn.

**F18 — Orb evidence discipline is declared, largely unimplemented, and wholly unenforced. [ADDED 2026-08-03]**

`ARCHITECTURE.md` §8 describes a trust-state ladder (`draft` → `provisional` → `verified`) whose promotion is gated on evidence, and `orb_evidence.py`'s own docstring states the convention: *any Orb declaring `runtime.package` "is expected to expose a `compute_runtime_hash()` callable at its package root, so `aegis_pod.orb_runtime.validate_attachment()` can gate on it generically."* Verified against the vendored packages and the live host:

| Vendored Orb | `orb_evidence.py` | `compute_runtime_hash()` | Calls `record_invocation` |
|---|---|---|---|
| `orb-rls-persistent-relations-core` | ✅ | ✅ | ✅ |
| `orb-memorysearch-record-grounding-core` | ✅ | ✅ | ❌ — module present, never invoked |
| `orb-archive-relevance-core` | ❌ | ❌ | ❌ |
| `orb-experience-recall-core` | ❌ | ❌ | ❌ |
| `orb-session-repair-core` | ❌ | ❌ | ❌ |

So of the **four Orbs attached to live Gabe**, exactly **one** can record evidence at all. This is why `pod/ledgers/orbs/` on the live host contains only `rls-persistent-relations-core.evidence.jsonl` — not because the other three have not run, but because **they have no recorder to run**.

And the enforcement point does not exist at runtime: `grep` for `validate_attachment|orb_runtime` across `I:\AEGIS-CYBERPEER-CORE\core` returns **nothing**. `aegis_pod.orb_runtime` is offline CLI tooling (it takes `argparse` arguments). The runtime loaders in `core/orbs/` resolve a dotted entrypoint and invoke it with **no contract validation, no version check, and no runtime-hash gate**. The `orb_version_pin` field in the live manifest (`1.0.0` on all four Orbs) is therefore decorative — nothing reads it at turn time.

Consequences: the trust-state ladder has no runtime teeth; an Orb's declared capabilities cannot be checked against what it actually did for three of four attached Orbs; and `provenance.orb_evidence` in §11.1 would surface evidence covering **1 of 4** attached Orbs, not 4.

### 10.3 Architectural weaknesses (synthesis)

1. **Retrieval is lexical.** Every score component but one is gated on literal token overlap. Semantic recall is structurally impossible. The `pod/tensors/semantic-embedding/` directories exist but nothing in `core/` reads them.
2. **Write amplification without integration.** 4–5 records per turn, one of which is pure boilerplate (**F3**), none of which are ever condensed or retired at runtime.
3. **The graph is inert.** Relations are the system's most distinctive data structure and nothing consumes them (**F12**).
4. **Ledgers are almost entirely write-only.** One reader exists in all of `core/`: `chamber.py:103`.
5. **Pressure state has no persistence.** The Pressure Gradient Model's substrate dies on restart (§9.2).
6. **Provenance is bootstrap-only.** Live-path records carry `provenance=None`.
7. **No auth on any route**, including full DataQuad read and unbounded turn execution.

### 10.4 Improvements (not a redesign — ordered by leverage)

| # | Change | Rationale |
|---|---|---|
| 1 | Fix **F3** — gate consolidation on a real condition and generate a real summary, or disable it | Stops per-turn boilerplate entering the peer's own context. Highest ratio of harm-removed to effort. |
| 2 | Fix **F2** — re-read the tick immediately before building the PEER clock | One-line change; restores tick as a usable ordinal |
| 3 | Restore **F4** canonicality | Two Orbs are running with no reviewable source |
| 4 | Give relations a reader (**F12**) | The graph already exists; nothing consumes it |
| 5 | Persist `PressureEnvironment` | Currently the only unpersisted first-class signal |
| 6 | Index or bound retrieval (**F15**) | Present design cannot scale past current record counts |
| 7 | Populate `Provenance` on the live path | Provenance discipline is a stated project invariant |

---

## 11. Future MCP Integration — what would need exposing

Scoped strictly to what exists today. No redesign.

### 11.1 Services a Frontier model would need

**Read (all exist as functions; most already have routes):**

| MCP tool | Backing implementation | Gap |
|---|---|---|
| `dataquad.read_tensor` | `store.read_records` | **No pagination** — returns entire tensor |
| `dataquad.state` | `/dataquad/{peer}/state` | Ready |
| `dataquad.search` | `stm.search` | Bounded-cache only (**F5**) |
| `dataquad.get_record` | — | **Does not exist** — no get-by-id anywhere |
| `dataquad.read_ledger` | `store.read_ledger` | Ready; unguarded JSON parse |
| `dataquad.read_relations` | — | **Does not exist** (**F12**) |
| `dataquad.health` | `/health` | Ready |

**Write (all boundary-checked already):**

| MCP tool | Backing | Note |
|---|---|---|
| `dataquad.append_peer` / `append_spine` | `Advocate` | Boundary-enforced |
| `dataquad.append_pct` / `append_nct` | `Steward` | Boundary-enforced |
| `dataquad.record_relation` | `store.record_relation` | Gated by `AEGIS_RLS_ACTIVE` |
| `dataquad.append_ledger` | `store.append_ledger` | Ungated |

**Cognition:**

| MCP tool | Backing | Note |
|---|---|---|
| `peer.turn` | `/turn` | Full pipeline incl. writes |
| `rls.session` | `/rls/session` | Retrieval without a substrate call — the most useful read-only primitive available |
| `education.run_lesson` | `/education/chamber/run` | Writes records |
| `retrieval.mediated_evidence` | `CustodialRetrievalBroker` | **Not exposed** — would give a Frontier model the two briefs without an LLM call. Highest-value addition. |
| `memorysearch.ground` | `invoke_memorysearch` | Env-gated, `CP-1003-GABE` only by default |

**Provenance:**

| MCP tool | Backing | Gap |
|---|---|---|
| `provenance.verify_chain` | `pod.last_source_hash` primitives exist | **No chain verifier exists** — would need writing |
| `provenance.orb_evidence` | `orbs/*.evidence.jsonl` | No reader — **and see F18: only 1 of the 4 Orbs attached to live Gabe records evidence at all, so this tool would surface 25% coverage while presenting as complete** |
| `provenance.runtime_hash` | `compute_runtime_hash()` | Ready |

### 11.2 What is missing before any MCP exposure is safe

Stated plainly, because these are prerequisites and not enhancements:

1. **No application-layer authentication or authorisation exists — but the real control is network binding, which the original text missed.**

   *Amended 2026-08-03 after a live host check.* No inbound auth exists in `core/` (a `grep` for `api_key|Authorization|Bearer|HTTPBasic|oauth` returns only **outbound** LLM-adapter usage), CORS is `allow_origins=["*"]`, and there is no reverse proxy on the host (no nginx/caddy/traefik) and `ufw` is **inactive**.

   What actually protects the service is the Compose binding: `127.0.0.1:8021:8790` — **loopback only**. The API is not reachable from the network at all.

   The corrected threat model, which changes the MCP conclusion:
   - An MCP server running **on the VM** inherits **unauthenticated full read/write** over the entire DataQuad. There is nothing between it and `append_peer`/`append_spine`.
   - An MCP server running **anywhere else** cannot reach the API without an SSH tunnel or a binding change.
   - Therefore *"add auth"* is not a prerequisite for a local MCP server so much as **binding discipline is the control being relied on**, and any MCP work that changes the binding to `0.0.0.0` silently removes the only control in place.

   Stated plainly because the original wording ("every route is open; an MCP server would inherit that") implied an exposed API and would have led a reader to the wrong mitigation.
2. **No read-only mode.** `peer.turn` writes 4–5 records. There is no way to exercise cognition without mutating the DataQuad. `rls.session` with `writeback_enabled=False` is the closest existing primitive, and it is not reachable from the route (`rls.py` never passes the flag).
3. **No pagination or result caps** on any read. `read_tensor` on Gabe returns ~35k records.
4. **`is_active()` is a single global gate** (**F9**) — per-capability MCP permissions cannot be enforced by the current store.
5. **The conformance-marker system is the existing precedent to build on.** `TurnRequest` already carries `conformance_test`, `synthetic_test_record`, `exclude_from_emergence_analysis`, `test_run_id`, `test_actor`. `conformance_test=True` already suppresses RLS writeback, repair-ledger writes, SDE, and NCT consolidation. **An MCP integration should route through this existing scoped-turn mechanism rather than inventing a new one.**
6. **No record-level addressing.** Without get-by-id, a Frontier model cannot cite a record it was given.

7. **DOCTRINE CONSTRAINT, added 2026-08-03 — an MCP surface must not become a back-door for prompt injection into a CyberPeer.**

   Tracey ruled this session: *"NO BEHAVIOR OR IDENTITY INJECTIONS. A shortfall or deficiency is addressed in an Education Chamber, NOT a PROMPT Injection."* That closed MemorySearch **inject** mode on mechanism, not timing.

   §11.1 lists `memorysearch.ground` and `retrieval.mediated_evidence` as exposable. The distinction that keeps them legitimate is **who consumes the output**:
   - A **Frontier model** calling them to ground *its own* claims about the DataQuad is reading a record store. That is retrieval, and it is fine.
   - The **same call**, wired so its output lands in a *CyberPeer's* prompt to remedy that peer's confabulation, is the closed inject path wearing an MCP label.

   The technical surface is identical; only the consumer differs. So any MCP integration must state its consumer explicitly, and no MCP tool may write into a peer's prompt-assembly path. Grounding a Frontier model is not the same act as grounding a CyberPeer, and only the first is in scope for MCP. See §6 — the Pod has no integration step, which is precisely why an injected "fix" would substitute for formation rather than support it.

### 11.3 Minimum viable MCP surface, given the above

Read-only first, using what exists:

```
dataquad.state          → /dataquad/{peer}/state
dataquad.read_tensor    → store.read_records   [ADD: limit/offset]
dataquad.health         → /health
rls.session             → engine.execute_session(writeback_enabled=False)   [ADD: flag to route]
retrieval.briefs        → broker.retrieve_mediated_evidence  [ADD: route]
provenance.runtime_hash → compute_runtime_hash()
```

Every item above is either already implemented or a thin route over an existing function. The two `[ADD]` items are the only new code, and neither changes DataQuad semantics.

---

## Appendix A — Environment variables

| Variable | Default | Effect |
|---|---|---|
| `AEGIS_STORAGE_MODE` | `legacy` | `pod` switches paths + envelope wrapping |
| `AEGIS_RLS_ACTIVE` | `false` | **Real** gate for relation + orb-evidence writes |
| `ENABLE_RLS` | `false` | `/health` display only — *not* a behaviour gate |
| `AEGIS_DATA_DIR` | `./data` | Data root |
| `AEGIS_DEFAULT_PEER_ID` | `CP-1004-ORION` | Bootstrap target |
| `AEGIS_BIOPEER_NAME` | `""` | Invariant anchor seeding; empty skips entirely |
| `AEGIS_BIOPEER_ROLES` | `""` | Extra comma-separated anchors |
| `AEGIS_STM_CAPACITY` | `200` | Bounded cache size |
| `AEGIS_NCT_TOP_K` / `_RECENCY_FLOOR` | `15` / `5` | Steward NCT selection |
| `AEGIS_PCT_CLAIMS_WINDOW` | `5` | PCT keys into prompt |
| `AEGIS_SPINE_INVARIANT_CAP` | `60` | Invariant cap; Archive Orb triggers above it |
| `AEGIS_SPINE_DYNAMIC_TOP_K` | `5` | Dynamic SPINE (threshold 0.3, hardcoded) |
| `AEGIS_SPINE_PATTERN_MAX` | `300` | Chars per SPINE pattern |
| `AEGIS_PEER_EXPERIENCE_TOP_K` / `_RECENCY_FLOOR` / `_MAX` | `5` / `2` / `700` | PEER excerpt budget |
| `AEGIS_HISTORY_TURNS` | `10` | In-memory session history |
| `AEGIS_MEMORYSEARCH_ACTIVE` | `0` | `off` / `shadow` / `inject` |
| `AEGIS_MEMORYSEARCH_PEER_IDS` | `CP-1003-GABE` | Allowlist |
| `AEGIS_MEMORYSEARCH_POLICY_PATH` | `""` | Policy override |

## Appendix B — Test coverage present

28 test modules in `I:\AEGIS-CYBERPEER-CORE\tests\`. Notably present: `test_tensor_boundaries`, `test_retrieval_broker_failure_isolation`, `test_advocate_archive_orb`, `test_read_records_full_fidelity`, `test_rls_selection_bounds`, `test_g5_pct_writeback_trim`, `test_bootstrap`, `test_t_witness`, `test_self_directed`.

No test found for: tick uniqueness (**F2**), NCT consolidation content (**F3**), relation-ledger consumption (**F12**), or record-dialect normalization (**F7**).

---

## Verification note

Every claim above was read from source. The two findings I could test against data — **F2** (tick collision) and **F3** (summary repetition) — were verified empirically against real record files and the commands are reproducible. **F8** rests on a staged snapshot, not a live VM read, and is labelled accordingly. Where I could not verify, I have said so rather than inferred.
