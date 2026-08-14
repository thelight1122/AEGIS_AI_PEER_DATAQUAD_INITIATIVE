# Canon v0.20 Manifest and Seed Issuers — Preparatory Acceptance

Date: 2026-08-14

## Scope

This change adds deterministic tooling and test fixtures for a future Canon v0.20 source-manifest issuance and foundation-seed rebuild. It is preparatory only.

No authoritative Canon v0.20 manifest or seed was issued. No external Canon, production seed copy, VM runtime, DataQuad, tensor, credential, Key, Tumbler, protected disk, or snapshot was changed.

## Integrated behavior

- The manifest issuer fails closed on merge markers, undeclared or unruled sources, unresolved coordinate collisions, missing or mismatched digests, unresolved required locators, and dangling reference or supersession edges.
- The approved Nature Layer Canon v2 unresolved-locator exception is accepted only when the source is explicitly excluded from seeded bytes.
- The seed rebuilder derives `canonLock: clean` only from a clean manifest whose computed review-needed count is zero.
- The rebuilt seed binds the manifest digest, requires exactly 16 Axioms and the corrected SPINE expansion, preserves historical Rings 1–3 records, and refuses Ring-4 or learned-experience content.
- Memory-not-command and substrate-specific Nature provenance boundaries are included.
- Credential, Key, Tumbler, token, certificate, and secret-shaped material is refused.
- Canonical JSON generation is deterministic.

## Verification

- Focused issuer/rebuilder suite: 21 passed.
- Full repository suite: 414 passed, 14 skipped, 1 pre-existing deprecation warning.
- Python compilation: passed.
- Git whitespace/diff validation: passed.
- Secret scan: no values found; matches were limited to intended refusal code and tests.
- External production seed copies: unchanged.
- Authoritative issuance: not performed.

## Status

Accepted as repository-only construction tooling. Governance ruling and an explicit issuance action remain required before these tools may create authoritative Canon v0.20 manifest or seed artifacts.
