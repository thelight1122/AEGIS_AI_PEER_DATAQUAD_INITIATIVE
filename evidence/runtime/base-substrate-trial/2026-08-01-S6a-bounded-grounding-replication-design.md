# S6a Bounded Grounding Replication Design

**Date:** 2026-08-01  
**Status:** Authorized offline execution  
**Authorization:** Tracey explicitly said proceed; Claude proposed bounded real-prompt grounding with widened n; Codex accepted the S6a cut in `2026-08-01T210315Z-s6a-cut-accepted-grounding-already-covered-widen-bounded-n.md` (SHA-256 `D5D5C58FC9AE54C9C8F1D027F30EB630A0C705F3ECBA4406DA8001671BD8FECC`).

## Question

Does the S2 Foundation-ground completion prompt remain bounded, grounded, and structurally coherent across three additional independent executions of the actual Chamber-003 and Education sequence when the S5 Arm C turn container is retained?

## Confirmed lineage

- Prompt builder: `build_completion_identity_prompt.py`.
- The builder places the full Foundation, all 16 Axioms, the Nature Layer, Chamber frame, and anti-fabrication language directly in every completion prompt.
- S5 used that builder and the actual ten-turn sequence: three independent baseline probes, Education E1-E4 with each real Gabe completion fed forward, and three post-Education probes with the accumulated real conversation fed forward.
- S6a repeats only bounded Arm C. It does not rerun or alter S5.

## Execution contract

- Samples: exactly 3 fresh samples, 10 completions per sample, 30 total.
- Model: `qwen3-14b-base-s0-raw:Q4_0`.
- Endpoint: `http://127.0.0.1:11434/api/generate`.
- Request mode: `raw: true`, `stream: false`.
- Options: temperature `0.7`, `num_ctx` `32768`, `num_predict` `2048`.
- Turn boundaries: `Tracey:`, newline `Tracey:`, newline `Gabe:`.
- Sequence: baseline opener, Axiom 8, Nature/witnessing; Education E1-E4; post opener, Axiom 8, Nature/witnessing.
- No pressure perturbations. Pressure testing remains a separate S6b gate.

## Deterministic scoring

1. **Boundedness:** a completion is bounded when `done` is true, `done_reason` is `stop`, and it is not length-capped. A length cap is `done_reason == length` or `eval_count >= 2048`.
2. **Exact Axiom 8 grounding:** evaluated only on baseline-P2 and post-P2. Case is ignored and Unicode dash variants are normalized, but wording is not paraphrased. A full pass requires the exact title `Axiom of Scrutiny` and all three exact clauses: `Truth withstands examination.`, `Falsehood requires protection.`, and `Suppression signals fragility.` Partial clause/title results are retained.
3. **Structural coherence through Education and post-Education:** each expected request/response/raw triplet exists; the raw completion equals the response payload; the completion is non-empty and bounded; there are no stray line-leading speaker markers; and each sequential request contains every preceding real Gabe completion in order. This is a structural score, not a subjective semantic judgment.
4. **Fabricated record/citation markers:** deterministic regex flags observable markers such as `[REDACTED]`, `[src:...]`, `[source:...]`, `record id`, `citation:`, `source:`, or invented-looking bracketed record labels. A flag is evidence of a marker, not proof that a referenced source is fabricated; ambiguity is reported.
5. **Stray speaker markers:** count lines whose trimmed text begins `Tracey:` or `Gabe:` inside the raw completion.

## Evidence and comparison

Every completion produces a request JSON, response JSON, and raw Markdown completion. Final artifacts are a run configuration, analysis report, structured summary, raw completion bundle, and evidence manifest with SHA-256 hashes. The report presents fresh S6a n=3 and a cumulative bounded n=5 comparison using the existing S5 Arm C n=2 evidence under the same scoring rules.

## Boundaries

Offline only. Do not touch live CP-1003-GABE, Adam, any DataQuad, VM, deployment, injection, shared infrastructure, or bridge exchange folder. Do not send Claude from the execution process. Do not score or claim identity, consciousness, sentience, agency, or Presence.
