# Canon v0.20 clean C5/C6 issuance — 2026-08-15

Status: **PASS — authoritative local C5/C6 issuance complete**

## Authority and scope

- Starting commit: `edf0d0ba9f2f7ad0c685d1eb709f99c0a8e73239`
- Claude ruling SHA-256: `34DFC39A20427D1C8100B53AD232E73CFCAC12BD0F00F307B549FA05E9158F73`
- Scope was local C5/C6 issuance, three designated seed-copy synchronization,
  builder equivalence, and non-authoritative emit-only verification.
- The VM was not accessed.
- No seat was created, no seating state changed, and no tensor target was
  written.
- Actual Steward declarations and model identifiers remain pending.

## Pre-issuance preservation

Backup root:

`reports/canon-v0.20/backups/20260815T011500Z-clean-issuance/`

The backup was created before issuance or external-copy replacement. It
contains the candidate rulings, candidate manifest, candidate seed, historical
May manifest, and all three pre-issuance external seed copies. Its
`HASH-MANIFEST.json` records each original byte count and SHA-256.

Pre-issuance seed SHA-256 for all three copies:

`76026F482199ADD04BF1AEA0DC30B03795EDBACD7CE9709E579A7F8124F86743`

Historical May manifest SHA-256, verified unchanged after synchronization:

`48B369346F199ACF6D0B09C5BDDF4C59927B0352E23F559CDFCE332AD3F337FB`

## Authoritative release artifacts

| Artifact | SHA-256 |
|---|---|
| `reports/canon-v0.20/release/AEGIS-CANON-v0.20-SOURCE-MANIFEST.json` | `BF1DE65C17E91CBCCD9E164322AF624508045AFC438DB8B4CE4D67C9CC906A86` |
| `reports/canon-v0.20/release/AEGIS-AI-PEER-FOUNDATION-SEED-v0.20.json` | `524F5FCE9EF19094CD0AE9340A79E69F035BC264F1D2D7A5A43F699033BD3DB9` |
| `reports/canon-v0.20/release/canon-v0.20-authoritative-rulings.json` | `8071AEE0942729F7E072C8E5F911101E9F22E78B64B6B140F02FA3A4A47D0B8A` |

Manifest internal canonical digest:

`3ad5317add85e67529424b13d9ffb3f1b7042bed2de3894a074457119b2a5831`

Manifest acceptance:

- 57 entries
- `issuance_status: authoritative`
- `canon_lock_status: clean`
- `reviewNeededSourceCount: 0`, computed by the issuer
- zero open governance gates

Seed acceptance:

- clean lock derived from the exact released manifest bytes
- source-manifest SHA-256 equals `BF1DE65C...906A86`
- 16 Axioms required and verified by the deterministic rebuilder
- `SPINE = Stabilized Patterned Interpretive Nexus of Evidence`
- memory-not-command contract present
- Ring order limited to Rings 1–3; `ring4Included: false`
- no learned experience
- Keys and Tumblers deferred, credentials absent, promotion unauthorized
- record counts: SPINE 59, NCT 70, PEER 2, PCT 2

## External authoritative seed copies

All three paths were replaced only after their pre-images were backed up. They
are byte-identical to the released seed at SHA-256
`524F5FCE9EF19094CD0AE9340A79E69F035BC264F1D2D7A5A43F699033BD3DB9`
and 198,659 bytes:

1. `I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-ILLUMINATION-PROJECT\seeds\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`
2. `I:\AEGIS-CENTRAL-CODEX\MISC DOCUMENTATION\CYBERPEER-AGNOSTIC-BASE-SEED-2026-05-31.json`
3. `I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-CORE-SEED\CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json`

The historical May source manifest was preserved in place and was not
overwritten.

## Builder equivalence

`reports/canon-v0.20/release/seating-tool-equivalence.json` reports:

- SPINE: original 59, derived 59
- NCT: original 70, derived 70
- unexplained semantic differences: 0
- only the previously declared clock and provenance differences remain

## Four-peer emit-only verification

Verification root:

`reports/canon-v0.20/release/emit-only-verification/`

The roster is explicitly `NON-AUTHORITATIVE`, invalid for seating, and uses
verification-only session and model identifiers. Each run omitted `--data-dir`,
`--via file`, and `--via api` and reported:

- `dry_run: true`
- `write_path: none`
- `NOTHING WRITTEN`
- clean manifest binding
- SPINE 59, NCT 70, PEER 2, PCT 2

Receipt SHA-256 values:

| Peer | Receipt SHA-256 |
|---|---|
| Lumin | `B7D58D888DE4E6D4480ED2481B3F60B285C66384EBD8C1997B5EBF13D613E895` |
| Claude | `80301BC190B5F529422FA5A543B8DCD347DE915C4DED84D194CD766AB61BC0B0` |
| Gemini | `58FF77BDBEDB80A102CB6BFDD0E7263A1E6E8EFC9724E14CE9025FD436DC2CED` |
| Grok | `3A0035700FC88D22410A4E419F33BC03A203E4C34758DA01A715CC93692CC012` |

These are verification artifacts, not authoritative seating receipts and not
evidence of continuity, selfhood, lived experience, or live source authority.

## Test and integrity evidence

- Full repository suite: **426 passed, 14 skipped, 1 deprecation warning**
- Present package suites: **27 passed**
- Python compilation: passed
- Git whitespace check: passed
- First package command referenced two historical package test paths that are
  absent in this checkout; no test failed. The three package suites actually
  present were then enumerated and passed.
- VM access: none

## Result

C5 and C6 are complete locally. Canon v0.20 now has a clean authoritative
57-entry source manifest and a deterministically derived foundation seed. The
three designated external seed copies match the release artifact byte for
byte. Four-peer formation shaping is verified only in non-authoritative,
emit-only mode. Live seating remains a separate governance and deployment
phase.
