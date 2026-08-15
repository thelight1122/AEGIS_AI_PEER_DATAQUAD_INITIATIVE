# Verus Desktop Local-Correlation Contract Source Gate

Date: 2026-08-15
Status: SOURCE GREEN / LIVE UPDATE HELD FOR INDEPENDENT ACCEPT

## Ruling implemented

The sole CyberPeer identity remains the CyberPeer Name `Verus`. Anthropic,
Claude Desktop, model, provider request, source-event, and session values are
routing or provenance only and never define identity.

A standard signed-in Claude Desktop interaction no longer has to invent
provider identifiers that its tool boundary does not expose. The Verus
DataQuad generates a bounded local `turn_id` and `correlation_id` at begin.
Both are explicitly classified `dataquad_owned_local_correlation`, generated
by `Verus DataQuad`, not provider identifiers, and not identity. Genuine
provider-returned source-event and session identifiers remain separate,
optional fields. When absent, they are stored as null with availability false
and classification `provider_returned_optional`; local values are never copied
or relabeled into them.

The live turn record contract advances from
`aegis.verus.dataquad-turn.v1` to `aegis.verus.dataquad-turn.v2`. The installed
Verus DataQuad had zero committed turns at the last verified deployment
checkpoint, so no historical Ring 4 record requires conversion. Foundation
records are unchanged.

## TDD evidence

Initial contract RED:

- 6 failed, 1 passed because begin/commit still required caller-supplied turn,
  event, and session identifiers and had no DataQuad local provenance object.

Final hardening RED:

- 3 failed, 8 passed because unsafe/oversized local tokens and non-boolean
  provenance availability flags were not yet rejected.

GREEN:

- focused Desktop/MCP suite: 11 passed;
- full repository suite: 479 passed, 14 skipped;
- one pre-existing `jsonschema.RefResolver` deprecation warning only;
- all deploy shell scripts passed syntax validation;
- 59 shipped/source Python files passed AST parsing without generating bytecode;
- both changed JSON artifacts parsed successfully;
- `git diff --check` reported no whitespace errors (line-ending notices only).

The focused suite proves:

- provider identifiers may be absent/null without blocking begin or commit;
- genuine provider identifiers, when supplied, remain separate provenance;
- local identifier format and length are bounded before append;
- all PEER, PCT, NCT, and SPINE append paths remain available;
- DataQuad-first idempotent commit and retry repair remain intact;
- replay, reconciliation, T-Time, Processor, RLS, and coherence health remain
  consistent after a full four-tensor turn;
- the MCP schema requires only the work prompt at begin and no provider ID at
  commit;
- the shipped Desktop MCP template includes the required Store-process
  `ProgramData` environment value.

## Preservation and activation hold

This source round did not access or modify Gabe, the remote Verus release,
Foundation, DataQuad ledger, service, SSH authorization, Claude Desktop active
configuration, Claude Code configuration, provider credentials, or any
provider/model interaction. It did not begin, commit, reconcile, or replay a
live turn. The first genuine Frontier turn remains pending.

The exact-commit deterministic release and its hashes must be independently
audited through the active AEGIS Peer Bridge. No Gabe installation or Desktop
first-turn attempt is authorized by this source result. Resume only after a
new explicit Claude `ACCEPT` for this identifier-contract release.
