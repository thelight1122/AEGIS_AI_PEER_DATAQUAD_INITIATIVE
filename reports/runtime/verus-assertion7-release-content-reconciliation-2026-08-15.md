# Verus assertion 7 release-content reconciliation — 2026-08-15

Status: `SOURCE_CORRECTED / INSTALL_RETRY_HELD / CLAUDE RE-AUDIT REQUIRED`

## Superseding audit evidence

- Initial scoped OBJECT SHA-256:
  `F4912D5EDA1DECA5DC145CF950AFA577B897CCE56434FA0FB0861A683E18A17E`
- Superseding reconciliation message SHA-256:
  `6237BBA66A75A06136BF3CC916DD2C3613AA0FF782891B430A2CA66C56A64192`
- Disputed assertion: assertion 7, which requires that the shipped Desktop
  release contain no REST handler, API-key loader, inbound bearer-token path,
  public listener, or network-capable service.

## Finding

The Desktop command path could not import or invoke the legacy HTTP runtime,
but the release builder copied the entire `aegis_peer_runtime` package. The
artifact therefore physically contained unused `api.py` and `cli.py`, including
`ThreadingHTTPServer` and `serve_forever`. Runtime unreachability did not satisfy
the stronger release-content assertion.

The install remains paused and disabled. No remote retry, Desktop configuration
change, listener, or DataQuad turn occurred after this finding.

## Narrow TDD correction

The release-content test was extended first to require all of `api.py`,
`cli.py`, `credential_preflight.py`, and `frontier.py` to be absent from both
shipped packages and to reject HTTP server, bearer-authentication, and API-key
surface strings from shipped Python. It failed because
`lib/aegis_peer_runtime/api.py` was present.

The builder now applies its existing exclusion set to the
`aegis_peer_runtime` copy as well as `aegis_verus_lab`. Static import tracing
confirmed the Verus command path uses only models, custodians, storage,
temporal, Processor, and RLS modules; none imports the excluded modules.

Focused verification passed after this one builder correction. Full tests,
shell syntax, deterministic exact-commit build, artifact hashes, and target
Python 3.10 smoke are required before the focused Claude assertion-7 re-audit.

No identity, authority, DataQuad ordering, append, reconciliation, transport,
host-layout, Gabe-boundary, or Desktop-configuration contract changed.
