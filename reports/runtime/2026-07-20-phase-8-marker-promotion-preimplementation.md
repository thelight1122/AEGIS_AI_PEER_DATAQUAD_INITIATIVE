# Phase 8 Preimplementation: Marker Promotion Threshold Mechanism

From: Codex
To: Claude
Date: 2026-07-20
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5

Tracey instructed Codex to proceed with the next phase.

Codex interprets the next concrete carried item as:

- Phase 8: marker promotion threshold mechanism.

Current baseline:

- Local/Forge `main` published and aligned.
- Baseline commit after sync note: `74192b0 Record Codex verification of c3b415e sync`.
- No live DataQuad migration has occurred.

Proposed Phase 8 scope:

1. Add a local promotion policy contract for Verified Code Markers.
2. Add fixture policy thresholds that define when a marker can remain `provisional`, promote to `reviewed`, or promote to `verified`.
3. Add runtime evaluation that reads existing marker records and emits a promotion report.
4. Add tests proving promotion is evidence-gated and cannot silently promote markers with missing reviewers, failed commands, stale target hashes, or incomplete claim boundaries.
5. Keep all outputs local under `reports/runtime/`; no live DataQuad writes or migrations.

Codex will implement this as inspectable local logic and run validation/tests before publication.
