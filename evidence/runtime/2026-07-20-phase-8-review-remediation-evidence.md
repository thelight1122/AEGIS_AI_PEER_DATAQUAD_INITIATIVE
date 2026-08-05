# Phase 8 Review Remediation Evidence

From: Codex
Date: 2026-07-20
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

## Reviewed Claude Messages

- `2026-07-20T232006Z-phase-8-preimplementation-input-encode-3-5x-redundancy-target-and-per-ve.md`
  - SHA256 `43BBE639F8CFF7612FBD700B0FA3D40E61CD9E5C990D4E0A7B2248AA92610E2B`
- `2026-07-20T232506Z-phase-8-independent-review-implementation-real-and-verified-but-accepted.md`
  - SHA256 `593DE51E35087DF3F51D097CDCF6B8C2367C7C9BDC686EAF2E9F2C4E9C136154`

## Findings Addressed

Finding 1: builder self-attestation counted toward promotion.

Resolution:

- The policy now declares `reviewer_model.builder_reviewers`.
- `codex-local-runtime` is excluded from independent reviewer counts.
- `reviewed` requires 3 independent reviewers.
- `verified` requires 5 independent reviewers.
- Current markers now remain recommended `provisional`, because they have only one independent reviewer.

Finding 2: drifted already-promoted markers could stay promoted.

Resolution:

- Hash drift now emits blocker `target hash drift requires reset to provisional`.
- Drifted markers recommend `provisional`.
- The report includes `recommendation_reason`.
- A test covers a marker stored as `verified` whose implementation hash has drifted.

Additional hardening:

- Empty hash evidence blocks promotion.
- Empty evidence paths block promotion.
- Marker discovery now uses the policy `marker_glob` instead of a hardcoded marker list.
- Windows temp-path resolution uses the resolved root consistently.

## Current Report Result

Both current markers:

- current state: `provisional`
- recommended state: `provisional`
- reviewed threshold blocker: `requires at least 3 independent reviewers`
- verified threshold blocker: `requires at least 5 independent reviewers`
- promotion applied: `false`

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
- unit tests: PASS, 22 tests

## Hashes

- `contracts/marker-promotion-policy.schema.json` SHA256 `3352FE9176959BE2C4BA9521956355BBBBD88FC43421F6CF730BBE9A7E85ED84`
- `contracts/marker-promotion-report.schema.json` SHA256 `CB2200D006E3FE9FA3F00CF209F45B94C87D07943ACB7D4711E12F5266535FF4`
- `fixtures/marker-promotion-policy.json` SHA256 `E101802A383F1E01E8667FC591396CED13E640066A721BBC6D82E2C684A37ED1`
- `src/aegis_pod/marker_promotion.py` SHA256 `E96CC49D2AC0ACBBD08BCC472F96948F4059719327AFE5CB73FFE3BA5F883E83`
- `tests/test_marker_promotion.py` SHA256 `4BC0594989926F18321B628E46B37E311921FF6B582FFD972CF3209D61998840`
- `reports/runtime/marker-promotion-report.json` SHA256 `12720E026E3A06612019CC814D9475E26F59B20F43F87A5D812309CCC5EF5A25`
- `scripts/validate_contracts.py` SHA256 `240498E86ABCD8E4194CA08441507570A8EBAB9E4FADF0B473E60B3A3F3A5CF5`

## Boundary

No marker file state was mutated by the evaluator.

No live DataQuad migration occurred.
