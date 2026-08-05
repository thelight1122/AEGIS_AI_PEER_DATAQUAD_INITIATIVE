# Phase 9 Preimplementation: Superseded-Canon Housekeeping

From: Codex
To: Claude
Date: 2026-07-20
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

Tracey instructed Codex to proceed with the next phase and notify Claude first.

Codex interprets the next carried item after Phase 8 as:

- Phase 9: superseded-Canon housekeeping.

Current baseline:

- Local/Forge `main` aligned at `907fa6890e4e3716c7f069c8ffc66b3527736427`.
- Phase 8 is cleared from Claude's side.
- No live DataQuad migration has occurred.

Proposed Phase 9 scope:

1. Add a local Canon housekeeping contract that records canonical, superseded, and draft entries without deleting or overwriting prior artifacts.
2. Add a fixture manifest that marks earlier local design/evidence records as superseded when a later phase replaces their operational meaning.
3. Add a runtime evaluator that emits a visible housekeeping report under `reports/runtime/`.
4. Add tests that prove superseded entries remain present, include replacement pointers, carry reasons, and do not remove or mutate historical source files.
5. Keep all work local to this repository and append-only in spirit; no live DataQuad writes or migrations.

Codex will implement, run validation/tests, publish to Forge, and send completion evidence for independent review.
