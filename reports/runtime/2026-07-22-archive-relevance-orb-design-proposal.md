# Archive Relevance Orb: Design Proposal (Fixture Stage)

Date: 2026-07-22

Workspace: `H:\AEGIS-POD-ARCHITECTURE`

## Boundary

- Local contracts and fixture files only.
- No live Gabe or Orion mutation performed to produce this design.
- No changes to `core/custodians/advocate.py` yet — the real integration point is named below but not touched.
- Real (non-fixture) implementation, tests, and live attachment are explicitly out of scope for this step — see "Stopping point."

## Why this step exists

Tonight's live diagnostic work on Gabe (`CP-1003-GABE`) found and fixed three real pipeline defects in sequence: `peer_id`/`session_id` routing defaults, an O(n) per-line `get_next_tick` scan, and STM cold-start truncation of historical SPINE records. After all three fixes, a controlled test proved the real Axiom 11 record — correctly labeled, position 17 of 84 invariant SPINE records — was present verbatim in the assembled system prompt (`identity_continuity`, 60 entries). The model's answer still did not use it, fabricating a plausible-sounding but false axiom instead.

Root cause, read directly from `core/custodians/advocate.py:113-118`:

```python
invariant_records = [s for s in spines if s.invariant]
invariant_patterns = [_label(s) for s in invariant_records[:_SPINE_INVARIANT_CAP]]
```

`_SPINE_INVARIANT_CAP` defaults to 60 (`AEGIS_SPINE_INVARIANT_CAP`). Selection is a flat file-order slice — not relevance-ranked, not query-aware. For Orion (62 total SPINE records, all effectively invariant-eligible) this is a no-op; the whole set fits under the cap. For Gabe (84 invariant records out of 12,707 total SPINE), the cap is real but the *selection* is arbitrary with respect to what the current question is actually asking about. Tonight it happened to include Axiom 11 (position 17) — but nothing in the code guarantees that. A differently-ordered migration, or Gabe's continued growth past 60 invariant records active at once, would silently exclude any specific axiom a BioPeer asks about by name, with no signal that it happened.

This is exactly the gap the "Archive Orb" slot in the existing Orb taxonomy (`AEGIS-EDUCATION-CHAMBER` architecture pass, "Archive And Vault Layer") was named for, per Tracey's direct correction: a dedicated ability responsible for correctly surfacing specific content out of a peer's full historical volume, distinct from STM (recent/working memory, fixed tonight to stop dropping invariant records on cold start) and from RLS (relation-recording, already built and live on Orion).

Tracey's explicit scope boundary, following the same discipline as the RLS Orb design: this is a new **ability**, attached through a visible Umbilical — not a rewrite of the Advocate custodian itself, which remains a Pod-native component per `contracts/pod.schema.json`'s dedicated `roles` field. Only the invariant-selection algorithm at the cap boundary is in scope for the Orb; `Advocate.read_spine()`, the STM cache, and the rest of `produce_advocate_salience_brief` are unaffected and stay exactly as they are.

## What gets built (this step only — fixture stage, local)

1. `fixtures/archive-orb.json` — fixture Orb declaration, same shape as `fixtures/rls-orb.json`, `orb_id: archive-relevance-orb-fixture`.
2. `fixtures/archive-orb-umbilical.json` — fixture Umbilical, `attachment_point: "advocate"` (new attachment point — distinct from RLS's `"processor"` — naming the exact custodian this Orb serves).
3. `fixtures/archive-orb-input.json` — fixture demonstration input modeling tonight's real failure directly: a synthetic invariant SPINE set sized past the cap, with the record matching the query's named reference deliberately placed *outside* the naive cap window, to prove the ranking (not just the presence of the record) is what's being demonstrated.

## Real capability shape (for the next stage, not built here)

Named now so the fixture's `capabilities` array is not inventing anything it doesn't intend to mean later — matching how the RLS Orb's fixture stage already named its real capabilities before they were built:

- `label_match_promotion` → detect an explicit numbered/named anchor reference in the query (`"Axiom 11"`, `"GATE:pipeline-order"`, etc. — matching the `_label()` suffix convention already used by `advocate.py`) and guarantee that record's inclusion in the selected set regardless of cap position.
- `invariant_relevance_ranking` → for the remaining cap budget, rank invariant records by relevance to `user_message`/`intent` using the same `compute_relevance` function `advocate.py` already imports from `orb_rls_persistent_relations_core` for non-invariant SPINE — currently applied only to the non-invariant path, not to invariant selection at all.
- `cap_overflow_disclosure` → when total invariant records exceed the cap, report which were included vs. excluded as an observable event, rather than a silent slice. Consistent with this project's existing "no silent caps" standard.

Explicitly **not** in scope for the Orb: replacing STM, touching RLS's relation-recording, or any change to how PEER/PCT/NCT selection works — this is scoped to the one concrete, evidenced gap: invariant SPINE selection at the cap boundary.

## Discovery: no existing forward-declaration

Unlike RLS (which had a stub already written into Orion's `pod-manifest.json` `orbs[]` array by Stage D1), no Pod manifest — Gabe's or Orion's — currently references an Archive Orb at all. This proposal is the first concrete artifact toward it; there is no existing identifier to preserve.

## Stopping point

This step produces a design proposal and fixture-stage contract files only. No code in `core/custodians/advocate.py` changes, no live VM is touched, nothing is deployed. Building the real (non-fixture) capability and wiring it into `advocate.py`'s invariant-selection call site is a distinct future stage — following the same sequence RLS went through (fixture → design plan → real package on a dedicated branch → tests → Verified Code Marker → live attachment as its own separately-approved cutover) — requiring Tracey's explicit go per stage and independent verification before touching Gabe's or Orion's live Pod.

## Open question (not resolved here)

Whether `label_match_promotion` should also search *non-invariant* SPINE records for an exact anchor match (in case a future peer's canon axioms are seeded without `invariant: true` set correctly — already seen tonight as a plausible failure mode, ruled out for Gabe's actual data but not provably impossible for a future peer). Left for the real-implementation stage to decide with Codex's input.
