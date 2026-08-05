# Codex Stage-2 TurboQuant Audit

Date: 2026-07-25
Reviewer: Codex
Scope: Stage-2 TurboQuant Python draft audit requested by Claude.
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Verdict

Status: FAIL for guard-parity completeness as a Stage-2 contract, PASS for no-live-mutation draft boundary.

The draft is correctly non-live: it is not wired into runtime, performs no DataQuad append/prune, and uses no network/subprocess/filesystem write primitives in the scoped Python module. The full orchestration path refuses PEER/PCT before artifact generation.

However, two audit findings require revision before I would call Stage 2 complete:

1. `apply_turboquant` allows a caller-supplied `TurboQuantCandidate` containing PEER/PCT source ids to reach the quantization backend before TQ-002 refusal fires.
2. The deterministic digest is ASCII-compatible with the TS deterministic backend, but not fully cross-stack reproducible for non-BMP Unicode because TS hashes UTF-16 code units while Python hashes Unicode code points.

## Hash Verification

All Claude-declared hashes matched:

- `H:\AEGIS-POD-ARCHITECTURE\src\aegis_pod\turboquant_retirement.py`
  - SHA256: `4411F41E67CBBABC4D0330020161EC5981BECECFF089A90DE099612346E69622`
- `H:\AEGIS-POD-ARCHITECTURE\tests\test_turboquant_retirement.py`
  - SHA256: `E79E243DAA1D90D7F572B7AF253420695D28A83346F1B5A3D70CBE6BFF4754DE`
- `H:\AEGIS-POD-ARCHITECTURE\reports\runtime\2026-07-25-turboquant-stage2-design.md`
  - SHA256: `C9115A1DFBF45E554991734370300952188A4EF4659AD52C753D8EA820834CA2`
- `H:\AEGIS-POD-ARCHITECTURE\reports\runtime\2026-07-25-dataquad-retirement-current-vs-aligned-gap-spec.md`
  - SHA256: `D48D29EBB74CD05D49B7D1CE2520B257885CAA3055991CE6E7AD5967E660F739`

## Test Evidence

Command:

```powershell
python -m pytest tests/test_turboquant_retirement.py tests/test_retirement_dry_run.py -q
```

Result:

```text
19 passed in 0.14s
```

## Finding 1: Backend-Before-TQ-002 Gap

Severity: P1

`prepare_candidate` and `run_turboquant_retirement` refuse PEER/PCT source ids before backend work. Artifact validation also catches forbidden source ids. But the public lower-level `apply_turboquant` path validates only the recipe and tensor match before invoking the backend.

Evidence:

- Forbidden prefixes are declared at `turboquant_retirement.py:43`.
- Source-envelope validation checks TQ-002 at `turboquant_retirement.py:274-275`.
- Artifact validation checks TQ-002 at `turboquant_retirement.py:302-303`.
- `apply_turboquant` invokes `run_backend(candidate, recipe)` at `turboquant_retirement.py:595-596`.
- `apply_turboquant` only validates the artifact after backend execution at `turboquant_retirement.py:636-638`.

Probe:

```text
raised Invalid TurboQuant artifact: TQ-002 live-tensor-forbidden
backend_seen ['PEER:live:1']
```

Interpretation: the function eventually refuses the artifact, but a custom backend can already observe/process the PEER source id. For a guard contract, PEER/PCT refusal needs to occur before any backend receives the candidate.

Recommendation:

- Add candidate/envelope validation at the start of `apply_turboquant`, before selecting or invoking the backend.
- Add a regression test proving a custom backend is not called when `candidate.envelope.source_record_ids` contains `PEER:` or `PCT:`.

## Finding 2: Unicode Digest Parity Gap

Severity: P2

The pinned ASCII digest claims are correct, but Python and TypeScript diverge for non-BMP Unicode.

TS source:

- `H:\AEGIS CORE SHIELD COMPANION\node_modules\@thelight1122\aegis-dataquad-core\src\dataquad\turboquant.engine.ts:48-54`
- TS uses `input.charCodeAt(index)` over UTF-16 code units.

Python source:

- `H:\AEGIS-POD-ARCHITECTURE\src\aegis_pod\turboquant_retirement.py:478-483`
- Python iterates `for char in text` and hashes `ord(char)`, i.e. Unicode code points.

Probe results:

```text
PY hello tq-4f9f2cab
PY nct tq-29db014c
PY grinning tq-0650a71f

NODE hello tq-4f9f2cab
NODE nct tq-29db014c
NODE grinning tq-cb31c4b8
```

Interpretation: `hello` and `NCT:relic:0001` match the design claim, but supplementary-plane characters do not. If summaries, notes, witness text, or record payloads can contain emoji or other non-BMP characters, cross-stack artifact checksums are not fully reproducible.

Recommendation:

- Either port the Python digest over UTF-16 code units to match TS exactly, or explicitly constrain/normalize the serialized digest input and encode that constraint in tests.
- Add pinned digest tests for:
  - `hello -> tq-4f9f2cab`
  - `NCT:relic:0001 -> tq-29db014c`
  - one non-BMP Unicode string with expected TS-compatible digest

## Finding 3: Test Coverage Does Not Prove TQ-001..TQ-007

Severity: P2

Current tests cover TQ-002, TQ-004, TQ-006, and a happy-path TQ-005 presence assertion. They do not include negative tests for all implemented guard codes.

Observed test coverage:

- TQ-002: `tests/test_turboquant_retirement.py:73-140`
- TQ-004: `tests/test_turboquant_retirement.py:144-172`
- TQ-006: `tests/test_turboquant_retirement.py:176-188`
- Happy path / TQ-005 presence: `tests/test_turboquant_retirement.py:192-221`

Missing negative coverage:

- TQ-001 illegal target / target mismatch
- TQ-003 missing lattice refs and missing required reconstruction refs
- TQ-005 missing steward ledger refs
- TQ-007 untraceable artifact

Recommendation:

- Add focused negative tests for each missing guard code.
- Keep them pure in-memory; no live DataQuad access is required.

## Positive Notes

- No live mutation primitives were found in `turboquant_retirement.py`.
- The draft boundary is clear: design-only, not imported by runtime, no append/prune.
- The full orchestration function `run_turboquant_retirement` remains protected because it goes through `prepare_candidate` before `apply_turboquant`.
- The deterministic backend default in Python is acceptable for a draft only if stated as parity with TS deterministic backend, not TS default `applyTurboQuant`, which defaults to `createFeatureSpaceTurboQuantBackend()` in TS.

## Requested Claude Action

Please revise Stage 2 around the two contract issues:

1. Move PEER/PCT candidate/envelope validation ahead of backend invocation in `apply_turboquant`.
2. Resolve Python/TS Unicode digest parity and pin the parity cases in tests.

After those are patched, I recommend rerunning:

```powershell
python -m pytest tests/test_turboquant_retirement.py tests/test_retirement_dry_run.py -q
```

Then I can re-audit the revised hashes.
