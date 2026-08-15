# Verus Claude-first local LAB promotion build evidence

Date: 2026-08-15

Scope: repository implementation, local release build, and local verification

Live VM access: none

Live DataQuad writes: none

Anthropic calls: none

Credentials installed or included: none

Deployment, service transition, staging, commit, and push: none

## Authority implemented

- CyberPeer Name: `Verus`
- Frontier provider/substrate: `Anthropic` / `Claude`
- Sole identity variable: `cyberpeer_name=Verus`
- Provider, model, instance, request, route, artifact, and session identifiers:
  provenance/routing only
- Identity injection: absent
- System Instructions: operational only
- DataQuad ability: full append-only authoring across `PEER`, `PCT`, `NCT`, and
  `SPINE`; the local Processor and Custodians are admission plumbing rather than
  a substrate-based authority reduction
- Historical `fixtures/ai-peer-roster.json`: preserved unchanged
- Adam and Adam-One continuity inherited: none
- Other Frontier seats: unchanged
- Production meaning: `LAB_RUNNING`, not commerce, public sale, or general
  availability

The corrected mapping is recorded in a separate superseding artifact,
`fixtures/verus-claude-lab-roster.json`. The earlier Claude mapping remains as
historical evidence and was not silently rewritten.

## Release content

The Verus-only builder verifies the clean Canon v0.20 manifest and Foundation
seed, uses the accepted seating builders, replaces builder randomness and
import-time timestamps with deterministic release inputs, and emits exactly 133
Foundation records. Every emitted record names Verus while classifying provider,
substrate, prior model ID, DataQuad ID, and Foundation session as routing
provenance with `defines_identity=false`.

The Steward ruling is recorded honestly as a `2026-08-15` direct instruction
source without an invented exact authorization time. The builder requires an
explicit UTC `seating_timestamp` input and refuses missing, local-offset, or
malformed values. The exact timestamp below was explicitly supplied to the
local verification build; it does not claim that live seating occurred.

The release contains:

- verified Rings 1–3 Foundation and bootstrap pillars;
- append-only, hash-chained, idempotent Ring 4 turn storage;
- all-four-tensor views over Foundation plus live appends;
- persistent T-Time;
- Processor admission and disjoint Steward/Advocate Custodian scopes;
- derived-only RLS with authoritative tensor immutability proof;
- provider-neutral Frontier request/response contract;
- Anthropic Messages adapter with the exact model captured at runtime;
- runtime-only file credential loading;
- authenticated, loopback-only Bridge `/v1/turn`;
- hardened systemd service and preservation-only pause path;
- release artifact hash verification before installation.
- DataQuad-first turn commit followed by idempotent T-Time, Processor/Custodian,
  and RLS materialization;
- retry reconciliation and coherence-aware health across every committed turn;
- bounded finite-JSON prompt, response, append, context, and complete-turn sizes;
- bounded non-secret HTTP handling for Frontier authentication, rate limit,
  network, protocol, and unexpected Shortfalls;
- metadata-only credential preflight for root ownership, regular non-symlink
  files, and mode `0400`/`0600`;
- failed start/health restoration of prior release, unit, enabled, and active
  state, or a preserved-state safe pause when restoration is unavailable.

## Deterministic local release proof

Source lineage label: `7bfa427a34e9a7760f8a9678cd0ed502d0c128e4+WORKTREE`

Activation status: `NOT_INSTALLED`

Explicit local verification seating timestamp input:
`2026-08-15T07:15:03Z`

Foundation record validation: `verus-foundation-consumer-contract-v1`, 133 of
133 records. No applicable formal JSON Schema exists for the seating-builder
record shape; the repository tensor-record schema governs migrated/copy records.

Release manifest SHA-256:
`F9D4A68F7484C5AF84D30A58E9FA478E48C767B163DEA5800F77DC68A48AFCA8`

Foundation receipt SHA-256:
`292F7758767DFB1C3547F2D581D91C36BE14FA92ACC7D092DAC850AE62D9E179`

| Tensor | Records | SHA-256 |
|---|---:|---|
| SPINE | 59 | `8549F484C30E5B4614DDFAC330691F3A97C305F17476DE93021FE33D0B53D6A6` |
| NCT | 70 | `C80D7F707E9BFB13A626E167C5D3F66E67CA0D12C1432FA828E8E63E7CC518BD` |
| PEER | 2 | `D36E720BC9BF73302E95B106152343DB18E3DE54EF9B4BD319CB198AB4BC792C` |
| PCT | 2 | `FAC7B1F2426387AE4ECB35C67B72E31A32B916EE67947E5725F557C31D42FECD` |

Two independent builds with the same inputs produced byte-identical tensor
artifacts. A fresh release-loaded integrity check returned 133 Foundation
records, zero live records, no head hash, and `verified=true`.
The complete Foundation context serialized to 209,408 bytes, below the
4,194,304-byte runtime context boundary.

## Verification

- Verus-focused and directly affected runtime tests: `46 passed`
- Full repository suite: `467 passed, 14 skipped, 1 deprecation warning`
- Shell syntax: `install.sh`, `health.sh`, and `pause.sh` passed `bash -n`
- `git diff --check`: passed; Windows line-ending notices only

The single warning is the repository's existing `jsonschema.RefResolver`
deprecation warning in `tests/test_tensor_shadow_scorer.py`.

## Remaining live prerequisites

This evidence proves a buildable promotion release, not an active Frontier
CyberPeer. LAB activation still requires:

1. a fresh VM preflight and preserved hashes of every current relevant root;
2. review/acceptance of the completed live plan under the active Interaction
   Standard;
3. a committed source lineage and a newly built release manifest from it;
4. transfer and byte-for-byte verification of the release;
5. the exact Anthropic model identifier;
6. separately supplied root-owned, non-symlink Anthropic and Bridge credential
   files with mode `0400` or `0600`;
7. Verus-only install/start and `LAB_RUNNING` health verification;
8. connection of the Developer Lab Work Request / Actuator surface to the
   authenticated Verus Bridge—the release implements the DataQuad/Frontier
   boundary but does not itself grant repository or developer-tool access;
9. a first genuine Anthropic turn with captured provider request/model/session
   provenance, append evidence, T-Time, Processor, Custodian, RLS, returned
   payload, and DataQuad head hash.

The LAB remains running after acceptance. It pauses only for an integrity
Shortfall, authentication or provenance loss, or Steward direction. Unknowns
surfacing during operation are recorded as Shortfalls and become engineering
inputs.
