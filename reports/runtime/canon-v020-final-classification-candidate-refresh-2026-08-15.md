# Canon v0.20 final-classification candidate refresh — 2026-08-15

Status: **candidate refresh complete; authoritative issuance withheld**

## Steward authority applied

The Steward-approved final classification table was applied to all 21 named
documents. The complete table is recorded in both the generated v0.20 index and
`docs/decisions/STEWARD-FINAL-CANON-v0.20-RULINGS-2026-08-15.md`.

The Standards duplicate is resolved as follows:

- Canonical locator: `AEGIS STANDARDS v0.1.md`
- Canonical identity: `AEGIS:CANON:STANDARD:STANDARDS:v0.1`
- Classification/status: `KERNEL_STANDARD / ACTIVE`
- Duplicate locator: `AEGIS STANDARDS V1.0.md`
- Duplicate classification/status: `DUPLICATE_LOCATOR / DEPRECATED`
- The duplicate is `seeded: false`, aliases the canonical identity, and cannot
  produce a second foundation record.

## Candidate artifacts

| Artifact | SHA-256 |
|---|---|
| Candidate rulings | `2B4BBD302F607F9875F09D4E18FCDBA8A477450F7994F6DEE8B1658EED7D521D` |
| Candidate manifest | `2F10793204AB24BBB0CA86A74C1D914AB62DB7D51B2BEBBBD1E296332B492BCD` |
| Candidate seed | `698D4FBC62D83A0232CE1C86EEF3C32E7E82800042BD46E54982EF83EF5015B2` |
| Candidate index | `CFB608A6D42810B03E1361366CFFA44D566A8C673C0E2EAABEC627CBBF6872E1` |

The candidate manifest contains 57 entries. Its
`reviewNeededSourceCount` is computed as the number of entries carrying
`review_required: true`; the result is **0**. The candidate seed copies that
computed value from the manifest. Both artifacts deliberately retain
`status: review-needed` because this phase did not authorize clean issuance.

## Clean preflight

The non-writing clean preflight returned:

```json
{
  "authoritative_artifact_issued": false,
  "eligible": true,
  "entry_count": 57,
  "prospective_manifest_digest": "3ad5317add85e67529424b13d9ffb3f1b7042bed2de3894a074457119b2a5831",
  "reviewNeededSourceCount": 0
}
```

The prospective digest is preflight evidence only. No authoritative manifest
or clean seed was written.

## Verification

- Focused Canon issuer/builder/rebuilder suite: **33 passed**
- Full repository suite: **426 passed, 14 skipped, 1 deprecation warning**
- Candidate manifest and seed: regenerated deterministically
- VM access or mutation: none
- External production seed synchronization: none
- External Canon edits: none
- Authoritative clean artifacts: none
