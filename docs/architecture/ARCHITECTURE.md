# AEGIS Pod Architecture — Full Reference

Status: living document, current as of 2026-07-22. Supersedes the "Layer Model" section of `README.md` as the canonical architecture reference; `README.md` keeps its original design-phase boundary log intact for history. `CURRENT-STATE-AND-NEXT-STEP.md` remains the authoritative source for live deployment status — this document describes the architecture itself, not what's currently deployed where.

---

## 1. The Core Principle

A CyberPeer's **identity** lives in the Pod. Everything else the peer can *do* — beyond existing and remembering — is an attachable **ability**, connected through a visible, inspectable contract, never merged into the peer's own identity code.

This split exists for a concrete reason, proven twice live on `CP-1003-GABE` on 2026-07-22: the old shortfall mode was bespoke, per-peer code where abilities and identity were the same files, so a change to one silently changed the other, and nobody could point at the boundary where a function actually lived. The Pod/Orb split makes that boundary a real, checkable thing — a JSON Schema contract, not a convention.

Two rules follow directly from this, both load-bearing, both violated once tonight before being caught and fixed:

1. **Attach, don't affect.** An Orb (or Satellite, or Portal) connects to the Pod through an Umbilical. It does not require the Pod's own code to change to support it existing. A peer with nothing attached behaves identically to one with abilities attached and unused.
2. **If an Orb falls short, the Pod just doesn't get that function.** It does not crash the turn. This was not true by default — both real Orbs built so far (`rls-persistent-relations-core`, `archive-relevance-core`) initially had unguarded invocation sites that would have taken down an entire `/turn` request on an Orb-side bug. Fixed 2026-07-22; see §6.

---

## 2. The Layer Model

```
                    ↗ outward, past the container boundary
    ┌─────────┐
    │ Portal  │  (Orb whose function is to bridge OUTSIDE the container)
    │ +Tender │  (the Portal's own internal discipline for its own tether)
    └────┬────┘
         │ Umbilical
    ┌────┴──────────────────────────────────────────┐
    │                      POD                        │
    │   PEER · PCT · NCT · SPINE                      │
    │   Steward · Advocate  (custodians)              │
    │   Processor · Temporal Daemon                   │
    │                                                  │
    │        ┌──────┐         ┌──────┐                │
    │        │ Orb  │◄───────►│ Orb  │   (RLS, Archive)│
    │        └──┬───┘         └──┬───┘                │
    │           │Umbilical        │Umbilical           │
    │        ┌──┴───┐         ┌──┴───┐                │
    │        │Sat.  │         │Sat.  │   (serve the Orb,│
    │        └──────┘         └──────┘    not the Pod) │
    └──────────────────────────────────────────────────┘
              all of this stays INSIDE the container boundary
```

### Pod
The CyberPeer core. Not an Orb, not attachable, not optional. Contains:
- **The four tensors** — `PEER` (present experiential signal), `PCT` (persistent contextual thread), `NCT` (condensed contextual essence), `SPINE` (sovereign identity continuity, including invariant axiom/canon records).
- **Custodians** — `Steward` (context witness: owns PCT/NCT) and `Advocate` (affect witness: owns PEER/SPINE). Each produces a "brief" (`StewardContextBrief`, `AdvocateSalienceBrief`) that becomes part of the system prompt for a turn.
- **Processor** — context assembly and turn interpretation.
- **Temporal Daemon** — time position and continuity awareness (the tick clock).

Defined formally in `contracts/pod.schema.json`. `roles`, `processor`, `temporal_daemon`, and `tensors` are dedicated required fields — these are Pod-native, never Orbs, confirmed directly against the schema (not assumed).

### Orb
A bounded, complete-function module operating **inside** the container boundary — a skill the Pod can call on, whose own internals the Pod doesn't need to understand. Declared by `contracts/orb.schema.json`: `orb_id`, `ability_name`, `purpose`, `runtime` (language/form/entrypoint), `capabilities` (name+function pairs, one-to-one with real callables — no capability may be declared without a real function behind it), `demonstration` (a real or fixture proof of the capability working), `umbilicals` (paths to its Umbilical(s)), `evidence` (`trust_state`: `draft` → `provisional` → `verified`).

Two real (non-fixture) Orbs exist as of 2026-07-22 — see §4.

### Satellite (formerly loosely called "Sub-Orb")
A bounded module that serves a specific **Orb**, not the Pod directly. Same attach-through-Umbilical pattern, one level down: a Satellite orbits its parent Orb, providing narrower supporting capability (e.g., an embedding computation or anchor-extraction helper) the Orb consumes internally. The Pod never sees a Satellite; only the Orb that owns it does. No Satellite has been built yet — named here so the pattern is established before the first one is.

### Portal
An Orb whose defining function is to cross **outward** — past the container boundary, to a service or app the Pod does not own or control (an MCP server, an external API, another application). Structurally identical to an ordinary Orb (same `orb.schema.json`, same Umbilical attachment); the distinction is purely about which side of the container boundary its function operates on. This is the one place where the container boundary and the trust boundary come apart — every ordinary Orb/Satellite works on data and state the Pod already owns, but a Portal reaches for something it doesn't.

### Tender
The internal discipline that lives **inside** a Portal, not as a separate Pod-level custodian. Because a Portal is the one case where trust and container boundary diverge, the safety logic for that divergence has to travel with the Portal itself — wherever it's attached — rather than being assumed by whatever Pod happens to host it. A minimum-viable Tender is expected to provide, before a Portal can be trusted with real external reach:
- Credential isolation (the Portal, not the Pod, holds and scopes its own credentials).
- A declared capability allowlist (what the Portal is actually permitted to do, not just what it's technically capable of).
- Pre-call contract-conformance checking against its own Umbilical's `input_contract`/`output_contract` — checked *before* the call, not just logged after.
- Post-call evidence recording of what actually crossed the tether.

No Portal has been built yet. This section documents the intended shape so the first one is designed to it rather than improvised.

### Umbilical
The visible connection contract between two layers — Pod↔Orb, Orb↔Satellite, or (once built) Portal's own tether outward. Declared by `contracts/umbilical.schema.json`: `pod_id`, `orb_id`, `attachment_point` (which Pod-side role/component this attaches to — `advocate`, `processor`, and (future) `portal`), `runtime`, `invocation` (a dotted `entrypoint`, resolved dynamically via `aegis_pod_sdk.resolve_entrypoint`, never a hardcoded import), `input_contract`/`output_contract`/`observation_contract`/`evidence_contract`, and `working_parameters` (`status`, `outside_parameters_behavior` — what happens when inputs fall outside what was declared).

**Built-in Umbilical sockets** (named direction, not yet built): today, each Orb's Umbilical is hand-built and placed wherever the Pod happens to look for it — proven fragile tonight (see §5, the phantom-file and path-convention bugs). The intended refinement is for the Pod to declare its own attachment surface up front: known sockets (`advocate`, `processor`, `steward`, `portal`, ...) with a defined contract for what may plug into each, so connecting a new Orb means matching an existing, Pod-declared socket rather than each Orb inventing its own wiring path.

---

## 3. Dynamic Resolution — How Attachment Actually Works

Nothing about an Orb is hardcoded into the Pod's imports. The resolution chain, identical in shape for every Orb built so far:

1. A Pod's `pod-manifest.json` declares an `orbs[]` entry: `{orb_id, required_for_full_function, umbilical: <path>}`.
2. A loader (`core/orbs/rls_loader.py`, `core/orbs/archive_loader.py`) checks `AEGIS_STORAGE_MODE=pod`, reads the manifest, finds the matching `orb_id`, resolves the Umbilical file at the declared path (**relative to the peer's own root — see §5 for why an absolute host-style path silently falls short inside a container**), and reads its `invocation.entrypoint` — a dotted Python path.
3. `aegis_pod_sdk.resolve_entrypoint(dotted_path)` imports that path dynamically (progressively longer import prefixes, then attribute resolution) and returns the class.
4. If any step falls short — no manifest, no matching orb entry, no umbilical file, bad entrypoint — the loader returns `None` (Archive) or the compiled-in default entrypoint (RLS), and the calling custodian code falls back to its pre-Orb behavior. Per §1's second rule, this fallback path itself will be wrapped so an exception *during* a resolved Orb's execution degrades the same way, not just a shortfall in resolution.

This is what "attach, don't affect" means concretely: the Pod's own code (`core/custodians/advocate.py`, `core/custodians/retrieval_broker.py`) never imports an Orb package at the top level for its dynamic path — only the loader does, and only when something is actually declared.

---

## 4. Real Orbs Built (2026-07-22)

### `rls-persistent-relations-core`
- **Purpose:** recursive-learning-session retrieval/writeback — candidate relevance scoring, candidate partitioning against a relevance threshold, PCT writeback, cross-tensor relation recording (the one genuinely Orb-owned Pod write), shortfall-as-data capture.
- **Package:** `orb-rls-persistent-relations-core`, vendored at `I:\AEGIS-CYBERPEER-CORE\vendor\`, canonical source at `H:\AEGIS-POD-ARCHITECTURE\packages\`.
- **Attachment point:** `processor`.
- **Real finding tonight:** its Umbilical file had never actually existed on Gabe's VM — the manifest pointed at a phantom path. `resolve_rls_engine_class` was silently falling back to its default entrypoint the entire time, invisible only because the default and the declared entrypoint are the same class. Built the real file, fixed the path convention, restart-verified genuine attachment (`cross-tensor-relations.jsonl` continues to grow correctly).

### `archive-relevance-core`
- **Purpose:** when a peer's invariant SPINE record count exceeds the context cap (`AEGIS_SPINE_INVARIANT_CAP`, default 60), guarantee inclusion of any record whose label matches an anchor explicitly named in the query (e.g. "Axiom 11"), regardless of file-order position, instead of a flat slice that silently excludes it.
- **Root cause it fixes:** live-evidenced on `CP-1003-GABE` — the real Axiom 11 SPINE record existed, correctly flagged `invariant: true`, but a flat `invariant_records[:60]` slice in `core/custodians/advocate.py` excluded it whenever it fell outside the cap in file order. The model, given no grounded content to draw on, fabricated a plausible-sounding false axiom rather than reporting uncertainty.
- **Capabilities:** `label_match_promotion` (regex-based anchor detection: `Axiom N`, `GATE: token`, `Imperative token`), `invariant_relevance_ranking` (remaining budget filled in file order, unchanged from pre-Orb behavior), `cap_overflow_disclosure` (reports what was excluded rather than silently truncating).
- **Attachment point:** `advocate`.
- **Live-verified:** a real record (`IMPERATIVE:t-witness-primacy`, position 65 of 84, genuinely past the cap) is now correctly promoted into context when explicitly asked about — proven both in a synthetic unit test and against Gabe's real live data.
- **Scope limit, stated plainly rather than silently assumed complete:** label-match promotion currently recognizes `Axiom N`, `GATE:`, and `Imperative` phrasing only — it does not yet cover `NATURE:` aspect references, and only matches keyword-first phrasing for named anchors (`"Imperative: t-witness-primacy"` matches; `"the T-Witness Primacy imperative"` does not, yet).

Both Orbs: 6+ unit tests each at the package level, integration tests proving both the unattached-fallback and attached-promotion paths, full local test suite run before and after each change to confirm zero regressions (compared against unmodified code via `git stash`, not assumed).

---

## 5. Two Shortfall Modes Found and Fixed Live (2026-07-22)

Documented because both were real, evidenced, and instructive about how this architecture actually breaks in practice — not hypothetical hardening.

1. **Umbilical path convention mismatch.** A live `pod-manifest.json` declared Umbilical paths as absolute host-style paths (`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/...`). Docker containers mount only a subset of the host filesystem (here, `/home/azureuser/AEGIS-CYBERPEER-CORE/data` → `/app/data`) — the absolute host path does not exist inside the container's own filesystem namespace at all. Every loader's `umbilical_path.exists()` check silently returned `False`, and every Orb fell back to its default. **Fix:** container-relative paths (`pod/provenance/<name>-umbilical.json`, resolved against `peer_root` inside the container) for both Orbs' manifest entries.
2. **Declared-but-never-created file.** RLS's Umbilical file didn't just have the wrong path — it had never been created for Gabe at all, despite being declared in his manifest since Phase 3. This was invisible because RLS's fallback entrypoint and its declared entrypoint are the same class; a differently-configured Orb would have silently done nothing instead of its real job.

The lesson generalized into §1's second rule and the tests in §6: an Orb's absence and an Orb's shortfall will both degrade visibly and safely, and "it happens to still work" is not the same as "it is genuinely attached" — verify the latter directly, don't infer it from output alone.

---

## 6. Shortfall Isolation — Proven, Not Assumed

Both real Orb invocation sites now wrap resolution *and* execution in a single exception boundary:

- `core/custodians/advocate.py` — an `archive-relevance-core` Orb in shortfall logs a warning and falls back to the pre-Orb flat invariant slice. Proven by `tests/test_advocate_archive_orb.py::test_broken_orb_degrades_to_flat_slice_instead_of_crashing` (a real broken Orb, resolved via a genuine dotted entrypoint, not a mock).
- `core/custodians/retrieval_broker.py` — an `rls-persistent-relations-core` Orb in shortfall logs a warning; the turn proceeds with `rls_session_id=""` and empty selected/rejected refs (RLS's function simply wasn't provided this turn — not reconstructed, not faked). Steward and Advocate briefs are unaffected, since neither depends on RLS content beyond an id label. Proven by `tests/test_retrieval_broker_failure_isolation.py`.

Both fixes were regression-tested against the full local suite (`I:\AEGIS-CYBERPEER-CORE\tests\`) before and after, and live-verified on Gabe's VM afterward (healthy Orb path still produces identical output; the container survives a restart cleanly).

---

## 7. Contracts (source of truth)

- `contracts/pod.schema.json` — Pod shape: tensors, roles, processor, temporal_daemon, orbs[].
- `contracts/orb.schema.json` — Orb declaration shape.
- `contracts/umbilical.schema.json` — Umbilical declaration shape.
- `packages/aegis-pod-sdk/` — the zero-dependency cross-peer boundary package: `resolve_entrypoint`, `sha256_upper`, `DataQuadStoreProtocol`, and other shared primitives every Orb depends on instead of concrete Pod-core classes.

Every real Orb/Umbilical pair built so far has been schema-validated against these files directly (`jsonschema.validate`), not assumed conformant from hand-written JSON.

---

## 8. Verified Code Marker Discipline

Every Orb declaration carries an `evidence.trust_state`: `draft` (design-stage, no live reach) → `provisional` (real code, real tests, live-reachable, not yet independently re-verified) → `verified` (independently confirmed, typically by a second observer — Codex, in this project's standing practice). Promotion between states is gated by `fixtures/marker-promotion-policy.json`, which — deliberately — does not allow `live_reach: true` alone to skip straight to `verified`. Both Orbs built 2026-07-22 are `provisional`.

---

## 9. Glossary

| Term | One-line definition |
|---|---|
| **Pod** | The CyberPeer's own identity core — tensors, custodians, processor, temporal daemon. Never an Orb. |
| **Orb** | An attachable ability operating inside the container boundary. |
| **Satellite** | A module serving one specific Orb's internal needs, not the Pod's. |
| **Portal** | An Orb whose function is to cross the container boundary outward. |
| **Tender** | The safety discipline living inside a Portal, scoped to that Portal's own tether. |
| **Umbilical** | The visible, schema-declared connection contract between any two of the above. |
| **Attachment point** | The named Pod-side socket an Umbilical connects to (`advocate`, `processor`, future `portal`). |
| **Trust state** | `draft` → `provisional` → `verified`, an Orb's evidentiary maturity. |
