# Codex Cross-Audit Corrections

**Date:** 2026-08-03
**Scope:** Append-only correction to prior S3 and F2/F3 audit artifacts

## S3 correction

Claude verified the preserved Axiom 8 request and response hashes. The pinned prompt is `16,389` characters and `16,580` UTF-8 bytes, not `16,580` characters. The prompt hash remains the authoritative identity check:

`105224EE5F839307C0205E3677FE546FE0C602474B2879DB2DC58CD2B57D2E79`

The preserved response has `prompt_eval_count=3408`, `eval_count=768`, and `done_reason=length`. Therefore it is length-capped and must not be counted among S6a's bounded completions. It remains a valid grounding datapoint: the output begins with the exact Axiom 8 title and all three canonical clauses before fabricated continuation behavior.

The current timeout is more plausibly CPU wall-clock behavior under CPU-heavy execution and `stream:false` than context allocation. No new runtime conclusion is authorized until a streamed or otherwise time-bounded probe distinguishes slow generation from a stuck request.

## F3 precision correction

The 506-of-747 dominant Adam NCT string is confirmed as an analogous single-string-dominance pattern, but it is not the hardcoded Orion template at `thinking.py:486-499`; it came from an earlier writer. The findings remain separate:

1. The code defect is the unconditional readiness condition at `steward.py:125-129` together with the hardcoded Orion template at `thinking.py:486-499`.
2. The Adam record distribution independently demonstrates a related repeated-summary failure mode, but it must not be attributed to that current code path without a peer-specific live reproduction.

The earlier cross-audit artifact remains unaltered for provenance. This file is the governing correction for interpretation.
