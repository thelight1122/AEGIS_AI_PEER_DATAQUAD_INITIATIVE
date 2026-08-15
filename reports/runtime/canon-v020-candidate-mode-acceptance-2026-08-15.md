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
| `reports/canon-v0.20/candidate/canon-v0.20-candidate-manifest.json` | `916E05E3667C711F9FD90A3650E2A5574DB39728AA17AAA9F948F080C8DE372B` |
| `reports/canon-v0.20/candidate/ai-peer-foundation-seed-v0.20-candidate.json` | `80E0F1DA62B2888494486232603BF12147483716204EE13BB5BCAF4881D8CEE2` |
| `reports/canon-v0.20/canon-v0.20-index.json` used as input | `966B369B4BE0196F793D9B2B6CEBE489FD4308E32982D7B28E6BB2AA1BCE1639` |

The seed field `canonLock.sourceManifestSha256` equals the candidate-manifest
digest above.

## Verification

- Focused Canon/index/candidate/issuer/rebuilder suite: 53 passed.
- Full repository suite: 420 passed, 14 skipped.
- Candidate report/hash binding verification: passed.
- Active implementation and generated-candidate whitespace validation: passed.
- Immutable pre-repair backups intentionally retain their original conflict
  markers and trailing whitespace as forensic evidence; those backup-only lines
  are excluded from the active-file cleanliness claim.

## External candidate-source verification

- Both Glossary copies preserve both scoped bodies and contain zero live merge markers.
- Both former `BIOPEER_DOCTRINE.md` copies are renamed to
  `AI_PEER_DOCTRINE_CANDIDATE.md`, byte-identical at SHA-256
  `94A4694DA04172AEA3E80F013D8DB432EE7ECF6B9F1790610E73B88041527560`.
- The stale `Shadow Effects.md` filename reference has zero remaining occurrences
  in the active candidate corpus.
- Cryptonic Harmonics is registered as `AEGIS:CRYPTONIC-HARMONICS:v1.0` with
  SHA-256 `3324BDFEB872959C59473D6737D1385431584848F677744FC79FAD6DEFD6DED2`.
- The April DataQuad Model is recorded as historical lineage and superseded for
  current tensor definitions; its source was not modified.
- Pre-edit copies and hashes are preserved beneath
  `reports/canon-v0.20/backups/20260815T003650Z/`.

## Claim limit

These outputs demonstrate deterministic candidate construction and invariant
preservation only. They do not issue Canon v0.20, establish a clean lock, seat
any peer, create Ring-4 experience, activate live services, or establish
continuity or selfhood.
