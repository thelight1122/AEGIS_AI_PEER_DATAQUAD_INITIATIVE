# Canon v0.20 Candidate-Mode Acceptance — 2026-08-15

## Scope

Repository-only C4–C6 candidate support. Candidate artifacts are developmental,
non-authoritative, and cannot seat a DataQuad or produce a clean Canon lock.
Authoritative external seed copies and the VM were outside this operation.

## Enforced boundary

- Candidate manifest and seed remain `review-needed`.
- Open gates are explicitly enumerated: `S-2`, `S-4`, `S-5`, `S-6`, `G-1`.
- Any open gate makes the clean-lock rebuild path fail closed.
- The candidate seed binds the exact candidate-manifest SHA-256.
- Memory-not-command remains enabled.
- Exactly 16 Axioms and the corrected SPINE expansion remain required.
- Ring 4, learned experience, credentials, Keys, and Tumblers remain absent.
- Missing current-index locators remain visible as candidate review items; they
  are not silently repaired or admitted to seeded bytes.

## Generated candidate artifacts

| Artifact | SHA-256 |
|---|---|
| `reports/canon-v0.20/candidate/canon-v0.20-candidate-rulings.json` | `28D77DAD1AC992A0418E5D4CE406A8F6B4BBE9E65FCA7AEA9F54B9AB8EB48550` |
| `reports/canon-v0.20/candidate/canon-v0.20-candidate-manifest.json` | `3EC79FEA2D1F4B839FDA30B12812C4B3B99CE91F4A2FFF25276EFA82612EF39B` |
| `reports/canon-v0.20/candidate/ai-peer-foundation-seed-v0.20-candidate.json` | `91C46001F54952BAD49D56FBA6C5A3A21E14872DF9C8FA80D908BB68B9DA4CCF` |
| `reports/canon-v0.20/canon-v0.20-index.json` used as input | `691B3FA1D084DCC88171405350A08EF050C76D137DD368BB8816E8FA73B18908` |

The seed field `canonLock.sourceManifestSha256` equals the candidate-manifest
digest above.

## Verification

- Focused candidate/issuer/rebuilder suite: 27 passed.
- Full repository suite: 420 passed, 14 skipped.
- Candidate report/hash binding verification: passed.
- Active implementation and generated-candidate whitespace validation: passed.
- Immutable pre-repair backups intentionally retain their original conflict
  markers and trailing whitespace as forensic evidence; those backup-only lines
  are excluded from the active-file cleanliness claim.

## Claim limit

These outputs demonstrate deterministic candidate construction and invariant
preservation only. They do not issue Canon v0.20, establish a clean lock, seat
any peer, create Ring-4 experience, activate live services, or establish
continuity or selfhood.
