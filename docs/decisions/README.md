# Architecture Decisions

Recorded decisions for the AEGIS AI Peer DataQuad Initiative. A decision lands here when it is
ruled, not when it is proposed. Superseded decisions stay in place with their status changed.

| ADR | Status | Decision |
|---|---|---|
| [ADR-0001](ADR-0001-live-peer-content-is-not-duplicated.md) | Accepted | Live peer content is not duplicated into the Initiative. Tests requiring live peer state are environment-bound integration tests. |
| [ADR-0002](ADR-0002-flat-contracts-canonical-for-p0.md) | Accepted | Flat `contracts/` is canonical for P0. Categorized copies are noncanonical. |
| [ADR-0003](ADR-0003-reports-runtime-canonical-for-p0.md) | Accepted | `reports/runtime/` remains canonical for P0. |
| [ADR-0004](ADR-0004-orb-packages-remain-in-packages-during-p0.md) | Accepted | Orb packages remain under `packages/orb-*` during P0. |
| [ADR-0005](ADR-0005-orb-hash-drift-quarantined-pending-provenance.md) | Accepted — investigation open | The `orb-rls-persistent-relations-core` hash mismatch is DRIFTED and quarantined. Neither side is normalized. |
| [ADR-0006](ADR-0006-manifest-identity-model-coordinate-digest-path-provenance.md) | Accepted as target model | Manifests separate Coordinate, Digest, Path, and Provenance. |

## Governance

Decisions on this Initiative are ruled by the Auditor and relayed by the Steward. The implementing
party records the decision, states its consequences, and names what the decision leaves open.

A decision that defers a cleanup names the cleanup. A decision that quarantines a finding names the
investigation. Nothing is closed by being deferred.
