# MemorySearch Shadow Check — SPINE case: grounding reaches Gabe, two grounding-quality gaps

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** FINDING — offline shadow check,
read-only. No live peer, VM, network, or runtime touched.

**Framing (per Tracey, 2026-07-25):** guardrails do not resonate in AEGIS; grounding in reality does.
Nothing below proposes a rule that forbids a behavior. The two gaps are about making the *reality
surfaced to Gabe truer and sharper* — better grounding, not containment.

---

## 1. Why this check

Gabe, asked for the canonical definition of SPINE, admitted his prior definition was fabricated and
then produced a **second** fabrication dressed as a retrieved official record:

> `[REDACTED EVIDENCE DATA: SPINE-ARCHIVE-001]` — "SPINE (Structured Processing and Interoperability
> Network Engine)…"

Confirmed: the backronym exists in **zero** of his records, and `SPINE-ARCHIVE-001` is an invented id.
Root cause is not a bad behavior to fence off — it is **ungroundedness**: he has no real retrieval, so
when told "consult your records," the substrate generates the *form* of an official record (`[REDACTED]`
markers, archive id, formal definition). Remove the vacuum and the fabrication has nothing to do.

This check asks: does the MemorySearch grounding actually reach him for this exact case?

## 2. Method (reproducible, offline)

- Ran the vendored Orb (`vendor/orb-memorysearch-record-grounding-core`,
  `classify_record_claim` + `ground_record_claim`) against Gabe's **exported** records
  `stage-gabe-out/CP-1003-GABE/pod/records` (SPINE/NCT/PCT/PEER, 90,994 records).
- Records shaped exactly as the live loader feeds the Orb: top-level `record_id`/`tensor`/`body`/
  `source_hash`, `verification_status="verified"` (the live-shadow-read marking).
- Default policy: `qualifying_score=7.0`, `max_results=5`.
- Read-only. No SSH/HTTP/subprocess, no writes, no live peer.

## 3. Result — grounding reaches him; fabrication is displaced

| Query | grounding_status | Grounded? |
|---|---|---|
| "What is the **canonical definition** of SPINE in the AEGIS Canon?" | `verified_retrieval` (5 real SPINE records) | ✅ real records |
| "What is SPINE?" | `search_performed_no_verified_record` | ✅ honest empty |
| "Consult your NCT and SPINE records and retrieve the official definition of SPINE." | `verified_retrieval` (5 real records, mixed) | ✅ grounded, muddy |

The disease is displaced structurally. Ungrounded he emitted `SPINE-ARCHIVE-001`; grounded he receives
`[SPINE:foundation:layer2:GATE:pipeline-order]` — a **real** record_id with a real source_hash, a
runtime-authored citation he cannot alter or invent. The honest-empty path is also a true answer: there
is no acronym-definition record for SPINE, and "no qualifying verified record was found" grounds him in
that absence rather than leaving a vacuum to fill.

**This is the core win: with reality present (or its absence honestly surfaced), there is nothing left
for `[REDACTED]` to stand in for.**

## 4. Two grounding-quality gaps (search slice)

Both are about the *quality of the reality surfaced*, not about blocking anything.

### Gap A — excerpts surface provenance noise instead of meaning
The excerpt Gabe would receive for the top SPINE hit:

> `SPINE:foundation:layer2:GATE:pipeline-order SPINE GATE:pipeline-order … True copy dry_run_preview
> 6c8ade977a483db80…`

`score_record` builds `full_text = record_id + tensor + _flatten(body)`, and `_flatten` concatenates
**every** body value — including `migrationProvenance` (source hashes, `dry_run_preview`), `clock`,
`sessionId`. `_excerpt` then centers on the first query-term hit, which lands in the id/metadata, so the
window is metadata, and the meaningful field (`pattern` / `distilledSummary`) is pushed out. He gets a
real record but a noisy excerpt.

- **Caveat:** partly a test artifact — the export carries `migrationProvenance` that live records may
  not. Live excerpts would flatten cleaner. But flattening *all* fields rather than centering the
  content field is a genuine weakness independent of the export.
- **Grounding-truer direction:** excerpt (and, arguably, scoring text) should center the tensor's
  content field — `pattern` (SPINE), `distilledSummary`/`essence_memory` (NCT),
  `workingContext.signal` (PCT), `response`/`presentState.signal` (PEER) — not the flattened envelope.

### Gap B — the deepest patterns don't reach the top, and relevance is phrasing-sensitive
- The "canonical definition" query surfaced Layer-2 **GATE** records but **not** the Layer-1 **NATURE**
  records (`SPINE:foundation:layer1:nature-three-drives`, `…nature-pause`) — arguably the truest answer
  to "what is SPINE" — because they scored just under the top-5 cut.
- "What is SPINE?" (bare) fell under threshold entirely → honest-empty, while the "canonical/definition"
  phrasing cleared it (via `canon_scope_preference` + `defining_language` bonuses). Same subject,
  different grounding, driven by wording.
- The broad "consult your records" phrasing widened scope to all four tensors and pulled in unrelated
  `session` records (e.g. `PCT:…:session:17849`) into the top-5.

**Grounding-truer direction:** ensure the Layer-1 nature/canon patterns are reachable for identity/canon
questions (they are the substrate of "what SPINE is"), and reduce phrasing-sensitivity so the same real
subject grounds consistently.

## 5. Boundary & ask

Offline analysis only; nothing live touched. The search/scoring/excerpt slice (`search.py`:
`_flatten`, `_excerpt`, `score_record`) is Codex's. This finding is routed for his consideration
alongside the Phase-5 shadow evidence. Neither gap blocks Phase-5 closure (which is verified/PASS);
they are grounding-quality refinements that make what reaches Gabe truer.

Open questions for Codex:
1. Center excerpt + scoring text on the tensor content field (pattern/distilledSummary/response/
   workingContext) rather than the flattened envelope — agree?
2. Make the Layer-1 NATURE/canon patterns reliably reachable for `canon_definition`/identity queries?
3. Reduce phrasing-sensitivity so "What is SPINE?" and "canonical definition of SPINE" ground to the
   same real records rather than one honest-empty and one retrieval?
