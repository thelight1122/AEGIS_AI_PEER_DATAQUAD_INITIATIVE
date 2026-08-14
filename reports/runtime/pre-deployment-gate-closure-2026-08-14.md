# Four-Peer Pre-Deployment Gate Closure

- Captured UTC: `2026-08-14T20:01:26Z`
- Source commit before closure: `c5e9cee5c1ce6690766d1fdcea62e4ba9315bc59`
- Scope: local evidence closure and read-only VM readiness verification
- VM deployment performed: **no**
- External Canon edited: **no**

## PASS/FAIL matrix

| Gate | Result | Evidence |
|---|---|---|
| 1. Every Lumin, Claude, Gemini, and Grok foundation seeding is fail-closed memory, not command | **PASS** | The four-peer test requires `memory_only=true`, `executable=false`, and `identity_directive=false` for every peer. Command-like content remains opaque text. The runtime constructs these fields and verifies the memory boundary and content/canonical digests on read. |
| 2. Universal/structural Nature equivalence does not require identical substrate-specific Nature content | **PASS** | The four-peer test requires one shared schema and equivalence scope while requiring `content_equivalence_asserted=false`. Four intentionally different Nature contents produce four different content digests without breaking structural equivalence. |
| 2a. Every substrate-specific Nature difference has substrate provenance | **PASS** | Foundation storage now refuses missing or mismatched `provenance.substrate`. The four-peer test proves OpenAI/Lumin, Anthropic/Claude, Google/Gemini, and xAI/Grok provenance bindings independently. |
| 3. VM readiness is current and explicit | **PASS** | Read-only Azure/SSH checks at capture time: VM running; provisioning succeeded; external SSH succeeded; hostname `vm-cyberpeer-core`; ports 8811-8814 free; WARP disabled; no failed units reported; 72,870,180 KiB root free; 5,986,944 KiB memory available. |
| 3a. Rollback is bounded and returns only to an UNSEATED release | **PASS** | Upgrade records the prior release and invokes rollback on failure. Rollback changes only the current release symlink, restarts four services, and runs the health gate. Health requires all four to report `mode=UNSEATED`, `ready=false`, `live_source=false`, and `writes_enabled=false`. |
| 3b. Protected disks and snapshots are outside deployment/rollback scope | **PASS** | Deployment tests prohibit disk formatting, detachment, destructive state deletion, and Azure disk commands. The runbook names all three protected artifacts and prohibits modification, detachment, rename, and deletion. Azure read-only inspection confirms attached OS disk `vm-cyberpeer-core-os-repair-copy`; no data disks are attached. |

## Protected-artifact boundary

The deployment and rollback bundle performs no operation on:

- `vm-cyberpeer-core-os-repair-copy`
- `vm-cyberpeer-core_OsDisk_1_f79b5c49e4f94a9792b038ccb685615b`
- `vm-cyberpeer-core-os-snap-20260802`

Rollback is a release-symlink transition only. It neither modifies peer state nor performs any VM disk operation.

## Test results

- Focused amendment/deployment suite: **26 passed, 1 skipped**
- Full root suite: **393 passed, 14 skipped, 1 pre-existing warning**
- Package suites present on disk: **27 passed**
- `git diff --check`: **passed**

The warning is the existing `jsonschema.RefResolver` deprecation warning in `tests/test_tensor_shadow_scorer.py`.

## SHA-256 evidence

```text
97742B993E47E5555EFD5EFA18EA641B257CC0DC1FB2562966D4DC46FE7B8FCD  src/aegis_peer_runtime/storage.py
B66024796ACDB49EA1DC0F321496DE0EA5DFC4B09BBCF6C545B8C1DF6FB92F95  tests/test_claude_amendment_boundaries.py
720A8D84B06DC44B2FE9F90FFE7493FA0BCF3AF59C023A6358EA1E9F057FE856  tests/test_peer_runtime_storage_api.py
8484EE531CD50CF4845B7302DF109F76BE55EA2949AAA81313DB14C29215A470  tests/test_deployment_artifacts.py
0C8B8AF037F3AA78C5C932BB576952D9428CAC6A7406F36AD7C477A43AAA2173  deploy/scripts/health.sh
E474E0E7EB0438E330F67E06C889B30E06A5919D7D26322F90D245103F76E410  deploy/scripts/rollback.sh
0CA5B907D2829E32C2F29BB9A93C1C7BE27103DFA314D019D3EA9DA0A4C31E87  deploy/scripts/upgrade.sh
47A0D1635F8B9F6AA426EFF0A31ECF37FA431D9C612D2C8991A085E44CBF4FFE  deploy/manifest.template.json
74A6C6FB39C3F300899E3B8D963A596C91190F0A77ABEA8AD99536C0048C1FE8  docs/runbooks/AI-PEER-VM-DEPLOYMENT.md
905EB8AAF741F75BEDE5B2E11E75BBB42256CAEB6A6E822B13B9A52D9FFB5C7B  docs/decisions/PLAN-AUDIT-CLAUDE-AMENDMENTS-2026-08-14.md
```

## Disposition

Claude's three pre-deployment evidence conditions are closed locally. This record does not authorize or perform deployment, seating, live writes, credential installation, Keys, Tumblers, or external Canon changes.
