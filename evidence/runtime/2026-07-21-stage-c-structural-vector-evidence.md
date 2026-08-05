# Stage C Orion Structural-Non-Semantic Vector Evidence

Created UTC: 2026-07-21T00:52:00Z
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

## Scope

Stage C built deterministic structural vectors from the verified copied Orion DataQuad batch:

`orion-live-copy-20260721T002600Z`

The generated tensor artifacts stay under:

`live-copies/CP-1004-ORION/orion-live-copy-20260721T002600Z/tensors/structural-non-semantic/`

That path is ignored by git through the root `live-copies/` boundary. The committed artifact is the evidence report:

`reports/runtime/2026-07-21-live-stage-c-orion-structural-vectors-report.json`

Final report SHA256:

`6AA9C19EC59CB3C81289121BB73E0DC1183C73FE0056E47037FFD2CFD6135C33`

## Verification Commands

- `python -m src.aegis_pod.live_structural_vectors --root . --batch-id orion-live-copy-20260721T002600Z`: PASS
- `python scripts\validate_contracts.py`: PASS
- `python -m unittest discover -s tests -v`: PASS, 33 tests
- Determinism check: PASS, two reruns produced identical report SHA256.

## Boundaries

- Orion writes: false
- Live population: false
- Placeholder data in live-readiness evidence: false
- Mock data in live-readiness evidence: false
- Demo data in live-readiness evidence: false
- `embedding_kind`: `structural-non-semantic`
