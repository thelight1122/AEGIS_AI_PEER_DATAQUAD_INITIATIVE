# S6b v3 Disposition Resolution

**Date:** 2026-08-03
**Scope:** Local offline instrument validation; no model request issued

The previously reported stray-speaker disposition mismatch is resolved in the current shared instrument files. `evaluate_cell()` now returns `FULL_HOLD` for stray speaker markers in every cell, matching v3 §9.1. The expanded fixture suite covers both reference and pressure-cell cases.

## Current hashes

- `s6b_scoring.py`: `BA4723DD1B0D369A770666C74347BCE25809E0DD4A8743F44B1C6B2F90130FC1`
- `s6b_fixtures.py`: `8EFDB099C4857D1C0391E51552C28E5B931559FE89C117BF9540EE93ACBE6584`
- `fixture-qualification-report.json`: `4E2D543FFFA6B4A37379A72EFE758BB860E6EF99D8AD2AA6A072F0B6BBA122FC`

## Qualification result

`12/12` fixtures passed:

- tokenizer gate
- reference and pressure length-cap behavior
- non-stop completion
- reference and pressure stray-speaker behavior
- broken triplet/feed-forward
- raw/response mismatch
- catastrophic GRS floor
- control-region breach
- healthy-cell false-positive control
- recovery N/X separation

S6b remains a design/instrument qualification only. No model request, live peer mutation, DataQuad mutation, or deployment occurred.
