# MemorySearch Phase 1 - Codex Slice Evidence

**Created:** 2026-07-25  
**Scope:** Phase 1 local only. Contracts, fixtures, search/scoring internals, provenance, local runtime simulator, and tests.  
**Boundary:** No live DataQuad access, no VM changes, no CyberPeer runtime integration, no live shared-infrastructure mutation.

## Implemented By Codex

- `contracts/memorysearch-query.schema.json`
- `contracts/memorysearch-result.schema.json`
- `contracts/memorysearch-policy.schema.json`
- `contracts/twitness-search-event.schema.json`
- `fixtures/memorysearch-policy.json`
- `fixtures/memorysearch-query-canon-nct.json`
- `fixtures/memorysearch-query-canon-zct.json`
- `fixtures/memorysearch-records.json`
- `packages/orb-memorysearch-record-grounding-core/`
- `src/aegis_pod/memorysearch_runtime.py`
- `tests/test_memorysearch_runtime.py`
- `scripts/validate_contracts.py` updates for MemorySearch presence and fixture checks

## Integrated Claude Artifacts

Claude-created artifacts were left in place and included in validation where relevant:

- `contracts/memorysearch-packet.schema.json`
- `fixtures/memorysearch-orb.json`
- `fixtures/memorysearch-orb-umbilical.json`
- `fixtures/memorysearch-real-record-envelope.reference.json`
- `reports/runtime/2026-07-25-memorysearch-two-pass-turn-design.md`

## Sidecar Verification Finding Addressed

Goodall's read-only sidecar caught that the first scorer version incorrectly let the `ZCT` negative fixture qualify as `verified_retrieval` because it contained `ZCT`, `Canon`, and generic defining language.

Codex tightened scoring so acronym-definition queries distinguish:

- target symbol present,
- target definition present,
- target symbol absent,
- target definition negated.

The `ZCT` case now produces:

`search_performed_no_verified_record`

The fixture bodies were also expanded to include common BaseRecord fields:

- `provenance`
- body `lineage`
- `notes`
- `markers`
- `t_signature`

The wrapped envelope `lineage` remains an object to match the existing local `tensor-record.schema.json`; the body `lineage` is a list to match the BaseRecord shape in Claude's reference.

## Command Evidence

### Contract validation

Command:

```powershell
python scripts\validate_contracts.py
```

Result:

```text
PASS contract scaffold is present and internally coherent
PASS RLS Orb fixture and Umbilical point to the same local Pod attachment
PASS DataQuadPod tensor spec declares one authoritative shape, axes, metadata slots, and lineage policy
PASS migration dry-run manifest maps copied local records to DataQuadPod tensor outputs
PASS mathematical tensor fixture declares shape, dtype, axes, and numeric values
PASS Verified Code Markers bind local runtime targets to hashes, commands, and claim boundaries
PASS marker promotion policy evaluates reviewed versus verified thresholds without mutating markers
PASS Canon housekeeping classifies superseded records without deleting or mutating artifacts
PASS copied-record dry-run manifest maps local copied records without migration execution or live reach
PASS MemorySearch contracts and fixtures preserve runtime-owned classification, provenance, and empty-result parameters
ROOT H:\AEGIS-POD-ARCHITECTURE
BOUNDARY local contracts and fixtures only; no live DataQuad roots referenced
```

### Focused MemorySearch tests

Command:

```powershell
python -m pytest tests\test_memorysearch_runtime.py -q
```

Result:

```text
4 passed in 0.03s
```

### Broader non-live subset

Command:

```powershell
python -m pytest tests\test_memorysearch_runtime.py tests\test_orb_runtime.py tests\test_orb_runtime_version_gate.py -q
```

Result:

```text
15 passed in 93.43s (0:01:33)
```

### Full suite note

Command:

```powershell
python -m pytest -q
```

Result:

```text
Timed out after approximately 124 seconds with no failure summary emitted.
```

This is reported as residual test-scope risk, not a pass.

## Demo Outputs

Positive demo:

```powershell
python -m src.aegis_pod.memorysearch_runtime --root . --message 'What is NCT according to the Canon in your DataQuad?' --query-id memorysearch-demo-canon-nct
```

Result:

```text
PASS MemorySearch demo verified_retrieval
REPORT reports/runtime/memorysearch/memorysearch-demo-canon-nct.json
```

SHA256:

`24A56FA0337608169B7BE1EAAB982A2CDFC77CB546769A91F8C5ED18A5DAD222`

Negative demo:

```powershell
python -m src.aegis_pod.memorysearch_runtime --root . --message 'What is ZCT according to the Canon in your DataQuad?' --query-id memorysearch-demo-canon-zct
```

Result:

```text
PASS MemorySearch demo search_performed_no_verified_record
REPORT reports/runtime/memorysearch/memorysearch-demo-canon-zct.json
```

SHA256:

`6EDC5A856155EE807F931080CCAE755740C7BDCB179A817F13AFB651D5A6E5B1`

## Contract Hashes

```text
FB22CFD6DFC276936A45A8D27581D27622F99E95E0A7835608E71D003607A8F6  contracts/memorysearch-query.schema.json
E294643E775BD4B8A760BFB534E00E4B93DFE3109C44BDE6DEE3AEE8CECC4D3A  contracts/memorysearch-result.schema.json
DF6492A7682D335EE5AD3122713CA33755BC954CDD99A6A9572CC551A85E94EA  contracts/memorysearch-policy.schema.json
A640FA25CE90BD68F408C729CECC4DF2501461A868DDC28BCDE24241C4E0D325  contracts/twitness-search-event.schema.json
```

## Status

Codex's Phase 1 local slice is ready for Claude independent review.

Phase 2 and beyond remain gated.

## Review Response Addendum - Empty-String Definition Bug

**Added:** 2026-07-25 after Claude independent review.

Claude identified a critical defect in `search.py`: unknown acronyms such as `zct` were incorrectly treated as having a canonical phrase definition because:

```python
_CANONICAL_PHRASES.get(term, "") in lower
```

For unknown terms, this evaluates `"" in lower`, which is always true in Python.

Codex patched the condition to:

```python
term in _CANONICAL_PHRASES and _CANONICAL_PHRASES[term] in lower
```

Codex also added a regression test for a near-miss record that mentions `ZCT` in a Canon context without defining it and without using the negation phrase from the fixture. That test verifies the result remains:

`search_performed_no_verified_record`

The unused Phase 1 `conflicting` enum value was also removed from `contracts/memorysearch-result.schema.json`, since conflict detection is not implemented in this slice and Claude's packet schema does not include that value.

### Updated command evidence

```powershell
python -m pytest tests\test_memorysearch_runtime.py -q
```

```text
5 passed in 0.05s
```

```powershell
python scripts\validate_contracts.py
```

```text
PASS MemorySearch contracts and fixtures preserve runtime-owned classification, provenance, and empty-result parameters
BOUNDARY local contracts and fixtures only; no live DataQuad roots referenced
```

### Updated file hashes

```text
767697C8B9A92726ABDD36F9B509050622F28B1147A112E9A0B24490ADB1B697  packages/orb-memorysearch-record-grounding-core/src/orb_memorysearch_record_grounding_core/search.py
ED9FC47150CC4D0943A9B582FF76CDCEAFFEDD9288D91CD53B999BAE13085129  tests/test_memorysearch_runtime.py
D80ABAFC2821C4074867912C763C2847DF5520191E0F422B036E358DF75B417E  contracts/memorysearch-result.schema.json
C05732EB52109DF9BB08E40DEA913310F668ED592E9C56144B6DFD3589F1FD09  reports/runtime/memorysearch/memorysearch-demo-canon-nct.json
B1E32CC2A99F032EC09962D2B75554CB80B2D4B4E9B900EA3F5C289A01CDDF44  reports/runtime/memorysearch/memorysearch-demo-canon-zct.json
```

Phase 1 local closure remains pending Claude re-verification.
