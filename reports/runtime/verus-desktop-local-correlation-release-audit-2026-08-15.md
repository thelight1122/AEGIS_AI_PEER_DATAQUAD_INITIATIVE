# Verus Desktop Local-Correlation Release Audit

Date: 2026-08-15
Status: READY FOR INDEPENDENT SOURCE/RELEASE AUDIT / INSTALL HELD

## Exact source lineage

- source commit:
  `599ee0e8a61039c60e001ce83140fe2fef7d6fb6`
- source tree:
  `27dea27b9280312af5324ef9383509b1988d231f`
- source commit subject:
  `Correct Verus Desktop identifier provenance`
- source commit scope: 14 paths, 602 insertions, 66 deletions
- source worktree after commit: clean

Source evidence:

- `reports/runtime/verus-desktop-local-correlation-contract-source-gate-2026-08-15.md`
  SHA-256:
  `CFB7528122BDE7F9B893D29EE728172C8647814CFED04C14EFB81FEBEADF7E1D`
- `reports/runtime/verus-first-turn-refusal-programdata-correction-2026-08-15.md`
  SHA-256:
  `22474553E850AC80ACA1062E92CC5329BFAEA5CD7065AF253C4A02FD4392E908`

## Verification

- focused Desktop/MCP tests: 11 passed
- full repository tests: 479 passed, 14 skipped, one pre-existing
  `jsonschema.RefResolver` deprecation warning
- deployment shell syntax: passed
- Python AST validation: 59 files passed without bytecode generation
- changed JSON parsing: 2 files passed
- staged and post-commit diff checks: clean
- Python cache/build residue inside the source worktree: none

The test evidence covers absent/null provider IDs, separate genuine provider
provenance, DataQuad-owned bounded local correlation IDs, all four append-only
tensors, DataQuad-first idempotency, retry repair, replay, reconciliation,
T-Time, Processor, RLS, and coherent health.

## Deterministic release

Release directory:

`H:\AEGIS_AI_PEER_DATAQUAD_RELEASES\verus-desktop-599ee0e8a610`

Explicit build inputs:

- source commit:
  `599ee0e8a61039c60e001ce83140fe2fef7d6fb6`
- Foundation seating timestamp preserved from the currently seated Verus
  Foundation: `2026-08-15T13:28:28Z`

Release evidence:

- release manifest SHA-256:
  `C38D7AABFD75472CE9C2FD1A9398C0032F66C83D78674A23A9D3722A949AEA51`
- Foundation receipt SHA-256:
  `A287DFF87D864F27BAFCEF0E8459E9215F31105474A26393E08A6A43A4CE3724`
- shipped files: 27
- credentials included: false
- other-peer state included: false
- activation status: `NOT_INSTALLED`
- mode after a separately approved activation: `LAB_RUNNING`

Two independent output directories built from the same explicit inputs had the
same 27 relative paths and SHA-256 values, with zero differences. The temporary
comparison directory was removed after verification; the named release above
was preserved.

The shipped `aegis_peer_runtime` contains only `__init__.py`, `custodians.py`,
`models.py`, `processor.py`, `rls_runtime.py`, `storage.py`, and `temporal.py`.
The bundle contains no `api.py`, `cli.py`, `credential_preflight.py`, or
`frontier.py`. A release-wide scan found zero `ThreadingHTTPServer`, Bearer,
Anthropic API-key, Anthropic API endpoint, or public-bind surface strings.

## Independent gate and live hold

The release has not been transferred, installed, or activated. No Gabe-owned
service, container, tunnel, port, DataQuad, credentials, prompt, file, or
history was read or mutated during this source/release round. No live Verus
turn or provider/model interaction occurred.

Independent Claude audit is requested for the exact source commit and release
manifest above, specifically confirming:

1. CyberPeer identity remains only `Verus`;
2. local DataQuad IDs are expressly non-provider correlation evidence;
3. provider source-event/session/request fields remain optional/null and are
   never populated from local IDs;
4. the Desktop MCP schema permits the first genuine turn without fabricated
   provider provenance;
5. four-tensor append authority, idempotency, reconciliation, replay, and
   health remain coherent; and
6. the shipped remote bundle remains Desktop/stdio command-only with no HTTP,
   provider-key, or public-listener surface.

Hold all live installation and first-turn activity until a new explicit Claude
`ACCEPT` cites this source commit and release manifest hash.
