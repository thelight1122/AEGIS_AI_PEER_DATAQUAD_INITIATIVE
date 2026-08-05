# Phase 8 Evidence: Marker Promotion Threshold Mechanism

From: Codex
Date: 2026-07-20
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

## Scope

Phase 8 adds a local marker promotion threshold mechanism.

The mechanism evaluates existing Verified Code Marker artifacts and emits a report. It does not silently mutate marker files and does not reach live DataQuad roots.

## Added Surface

- `contracts/marker-promotion-policy.schema.json`
- `contracts/marker-promotion-report.schema.json`
- `fixtures/marker-promotion-policy.json`
- `src/aegis_pod/marker_promotion.py`
- `tests/test_marker_promotion.py`
- `reports/runtime/marker-promotion-report.json`

## Policy Gates

The evaluator checks:

- distinct reviewer count, not review-row count
- reviewer results are `no_blocking_objection`
- peer-review bridge message hashes exist
- all verification commands pass
- declared marker hashes match current local files
- evidence paths exist inside the workspace root
- claim boundaries include both demonstrated and outside-surface claims
- `live_reach` remains false for local marker promotion
- `pod_state_effect` remains `unchanged`

## Current Result

Current markers remain stored as `provisional`.

Promotion report recommendations:

- `tensor_runtime:local-deterministic-fixture-tensor-runtime:0.1.0`: `reviewed`
- `orb:rls-orb-fixture:0.1.0`: `reviewed`

Both markers remain blocked from `verified` because the policy requires at least three distinct reviewers.

No promotion was applied to marker files.

## Verification

Commands run:

```text
python -m src.aegis_pod.marker_promotion --root .
python scripts\validate_contracts.py
python -m unittest discover -s tests -v
```

Observed results:

- marker promotion evaluation: PASS
- contract validation: PASS
- unit tests: PASS, 20 tests

## Hashes

- `contracts/marker-promotion-policy.schema.json` SHA256 `9378ABFB8A169D57555FD279370643E89DFA89BD5F7FB2010EAAC37C7C54A0E4`
- `contracts/marker-promotion-report.schema.json` SHA256 `64731D3BED666FCA719ECE5D138CB224CA307EB8E619E5432FAD339C7E839164`
- `fixtures/marker-promotion-policy.json` SHA256 `1590CFB59C5B130CDC9D29FD8F66CA99412C0AE63D9A8A97974B093A86FD3C1D`
- `src/aegis_pod/marker_promotion.py` SHA256 `4CDBF20EB0E4370DF886B766CB6BFA0DB12AC950CCEDB76323E54761FBA62F7F`
- `tests/test_marker_promotion.py` SHA256 `07B0188AC70BEDEB822940B7E6BFF7C20D2F7657F11718FE447A4FC946AB87C3`
- `reports/runtime/marker-promotion-report.json` SHA256 `7A9BAF9F76FA5EDD08E3F6888C354EB5488D5F83091D8C5C5CCA191ED9A6E811`

## Boundary

No live DataQuad migration occurred.
