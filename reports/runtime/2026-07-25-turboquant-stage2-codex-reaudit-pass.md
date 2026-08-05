# Codex Stage-2 TurboQuant Re-Audit

Date: 2026-07-25
Reviewer: Codex
Scope: Re-audit of Claude's revised Stage-2 TurboQuant patch after Codex audit findings.
Standard hash: `7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`

## Verdict

Status: PASS for revised Stage-2 draft.

Claude's revised files close the three Codex audit findings:

1. PEER/PCT source ids are refused before a backend can observe/process a caller-supplied candidate.
2. Python deterministic digest now matches TypeScript UTF-16 code-unit behavior, including non-BMP Unicode.
3. Guard tests now include focused negative coverage for TQ-001, TQ-003, TQ-005, TQ-007, plus pinned digest parity tests.

Boundary remains draft-only: no live DataQuad, VM, runtime, broker, append, prune, network, subprocess, or filesystem write behavior is introduced by the TurboQuant module.

## Hash Verification

Claude's revised hashes match exactly:

- `H:\AEGIS-POD-ARCHITECTURE\src\aegis_pod\turboquant_retirement.py`
  - SHA256: `7CF612C3DE7FD2FCC32C149A83E36FF64B73C8D5DC0F1497A1389FFC91A5C8CF`
- `H:\AEGIS-POD-ARCHITECTURE\tests\test_turboquant_retirement.py`
  - SHA256: `2B793F9D93F0DC2A211EC1038FAB28DB1A8F163FBB249C794DE293ABECB5FAE6`
- `H:\AEGIS-POD-ARCHITECTURE\reports\runtime\2026-07-25-turboquant-stage2-design.md`
  - SHA256: `2D80F99FD53050AC4DCCD41168CD4DC596B18C5485C32F28B324173A485254C6`

## Test Evidence

Command:

```powershell
python -m pytest tests/test_turboquant_retirement.py tests/test_retirement_dry_run.py -q
```

Result:

```text
28 passed in 0.15s
```

## Finding 1 Re-Audit: Backend-Before-TQ-002

Status: PASS

Code evidence:

- `apply_turboquant` now calls `validate_source_envelope(candidate.envelope)` before `run_backend`.
- Relevant lines: `turboquant_retirement.py:618-631`.

Direct probe:

```text
raised Invalid TurboQuant candidate envelope: TQ-002 live-tensor-forbidden
backend_seen []
```

Interpretation: a directly constructed forbidden candidate is refused before backend invocation.

Regression test evidence:

- `test_apply_turboquant_refuses_forbidden_source_before_backend`
- Relevant lines: `tests/test_turboquant_retirement.py:238-265`.

Residual note: the direct spy regression uses `PEER:`. `PCT:` is covered by the same shared prefix path and existing validation/full-run tests, but a mirrored direct `PCT:` spy test would be a small hardening improvement.

## Finding 2 Re-Audit: Unicode Digest Parity

Status: PASS

Code evidence:

- `_iter_utf16_code_units` expands supplementary-plane code points into UTF-16 surrogate pairs.
- `_compute_deterministic_digest` hashes UTF-16 units.
- Relevant lines: `turboquant_retirement.py:476-507`.

Python probe:

```text
PY hello tq-4f9f2cab
PY nct tq-29db014c
PY grinning tq-cb31c4b8
```

Node/TS-equivalent probe:

```text
NODE hello tq-4f9f2cab
NODE nct tq-29db014c
NODE grinning tq-cb31c4b8
```

Pinned test evidence:

- ASCII parity: `tests/test_turboquant_retirement.py:269-271`
- Non-BMP parity: `tests/test_turboquant_retirement.py:273-275`

## Finding 3 Re-Audit: Guard-Code Coverage

Status: PASS

Added/verified coverage:

- TQ-001 illegal target and recipe/artifact target mismatch: `tests/test_turboquant_retirement.py:279-291`
- TQ-003 missing lattice refs / missing required reconstruction ref: `tests/test_turboquant_retirement.py:293-315`
- TQ-005 missing steward ledger ref: `tests/test_turboquant_retirement.py:318-323`
- TQ-007 untraceable artifact: `tests/test_turboquant_retirement.py:325-330`

## No-Live-Mutation Boundary

Status: PASS

Search for live/network/write primitives in `turboquant_retirement.py` found only docstring statements of no live reach:

```text
15:reach: no SSH, no HTTP, no filesystem writes, no mutation of
739:    any live DataQuad, does NOT prune any source tensor, and does NOT write to
```

## Independent Sidecar Review

Sidecar agent Descartes independently returned PASS, with the same minor residual note that a mirrored direct `PCT:` spy regression could harden the test suite further.

## Recommendation

Codex accepts revised Stage 2 as a passing draft contract.

Suggested optional hardening before any later live gate:

- Add a direct `PCT:` backend-spy regression mirroring the `PEER:` direct-apply test.
- Keep the real FeatureSpace backend decision separately gated; this Python draft remains parity with the TS deterministic backend, not TS default `createFeatureSpaceTurboQuantBackend()`.
