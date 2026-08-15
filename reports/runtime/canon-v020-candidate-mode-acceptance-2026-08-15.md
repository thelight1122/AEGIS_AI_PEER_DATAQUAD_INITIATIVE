# Canon v0.20 Candidate-Mode Acceptance — 2026-08-15

## Scope

Repository-only C4–C6 candidate support. Candidate artifacts are developmental,
non-authoritative, and cannot seat a DataQuad or produce a clean Canon lock.
Authoritative external seed copies and the VM were outside this operation.

## Enforced boundary

- Candidate manifest and seed remain `review-needed`.
- The Steward's final rulings close `S-2`, `S-4`, `S-5`, `S-6`, and `G-1`;
  candidate outputs now compute zero open governance gates.
- Candidate status remains `review-needed`; zero open governance gates does not
  itself authorize or perform clean issuance.
- The candidate seed binds the exact candidate-manifest SHA-256.
- Memory-not-command remains enabled.
- Exactly 16 Axioms and the corrected SPINE expansion remain required.
- Ring 4, learned experience, credentials, Keys, and Tumblers remain absent.
- Missing current-index locators remain visible as candidate review items; they
  are not silently repaired or admitted to seeded bytes.

## Generated candidate artifacts

| Artifact | SHA-256 |
|---|---|
| `reports/canon-v0.20/candidate/canon-v0.20-candidate-rulings.json` | `199FDF6CD68231A7394AFC103AABC00BCEA8A7447DA5ED14C7BC2D0E622F4F13` |
| `reports/canon-v0.20/candidate/canon-v0.20-candidate-manifest.json` | `DFEDCCC22811F6F15262E6EE07CA243EFA053C427104B3738667FA689EA14CD8` |
| `reports/canon-v0.20/candidate/ai-peer-foundation-seed-v0.20-candidate.json` | `FE048497FDBCE13CA1AA3E565B94A9F5B56F527278DA45C1BD2F88E5174703AB` |
| `reports/canon-v0.20/canon-v0.20-index.json` used as input | `CF54122631F0ABF97E8FF4FA7995D450BC07BCC68A284788A7354D536A883E70` |
| `docs/decisions/STEWARD-FINAL-CANON-v0.20-RULINGS-2026-08-15.md` | `D2CB27407A750F45E94A7D2DEDC2328D2951CEBBEF489C87449A0FC427F4A9BE` |

The seed field `canonLock.sourceManifestSha256` equals the candidate-manifest
digest above.

## Verification

- Focused candidate/issuer/rebuilder suite: 30 passed.
- Full repository suite: 423 passed, 14 skipped.
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
