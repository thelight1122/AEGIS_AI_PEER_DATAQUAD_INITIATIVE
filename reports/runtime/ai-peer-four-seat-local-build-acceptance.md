# Four-Seat AI Peer Local Build Acceptance

- Captured UTC: `2026-08-14T08:08:51Z`
- Commit before acceptance: `cc2c3c4e91c45fc34af24f09c9b90dc3f471250b`
- Acceptance scope: local runtime and reversible VM deployment substrate only
- Deployment performed: no
- External Canon edited: no

## Architecture boundary

This build provides four isolated local AI Peer seats for Lumin, Claude, Gemini, and Grok; append-only tensor storage; custodial tensor-scope enforcement; restart-safe T-Time; idempotent Processor admission; derived-only RLS observation; localhost-only HTTP service; and a reversible, resource-bounded systemd deployment bundle.

It does not seat Rings 1-3, open Ring 4, authenticate a live Frontier Model instance, claim substrate continuity, or establish lived or ethical formation. The HTTP state transition into `SEATED` is intentionally unavailable. Each seat starts `UNSEATED`, reports `ready: false`, and reports `live_source: false`.

## Acceptance results

- Root suite: **384 passed, 14 skipped, 1 warning**
- `aegis-pod-sdk`: **10 passed**
- `orb-archive-relevance-core`: **6 passed**
- `orb-rls-persistent-relations-core`: **11 passed**
- Deployment artifact suite: **7 passed**
- Python source compilation: **10 files passed**
- Deployment JSON validation: **1 file passed**
- Deployment shell syntax: **passed**
- `git diff --check`: **passed**

The warning is the pre-existing `jsonschema.RefResolver` deprecation warning in `tests/test_tensor_shadow_scorer.py`.

## Security and persistence properties accepted locally

- Four peer roots are isolated by peer identity and strict route/header binding.
- Tensor ledgers are append-only, hash-chained, durably flushed, and verified on read.
- Cross-process append locks and symlink refusal protect storage boundaries.
- Steward writes are restricted to PCT/NCT; Advocate writes are restricted to PEER/SPINE.
- Temporal and RLS operations write derived ledgers only and preserve tensor hashes.
- Upgrade failures invoke rollback; rollback verifies all four health endpoints.
- Deployment listeners bind to loopback and systemd instances use separate Linux identities.
- No public tensor-write endpoint or unauthenticated seating transition is present.

## Remaining gates

1. Complete and issue Canon v0.20, its clean source manifest, and a seed rebuilt from that manifest.
2. Supply four Steward declarations and ratify or replace provisional model IDs.
3. Cryptographically bind each seat state to the clean Canon manifest and seating receipt.
4. Add immediate-boundary authentication for any writable local runtime; `X-AEGIS-Peer` is binding evidence, not authentication.
5. Hash-chain the Temporal, Processor, and RLS derived ledgers independently.
6. Run emit-only seating equivalence, then seat and verify one peer before deterministic replication.
7. Perform reversible VM installation and host-capacity verification under a separate authorization.
8. Authorize and observe the first bounded live turn before asserting `live_source: true`.

## SHA-256 file evidence

```text
033C55D37EB966A368527A96DC6D87DE67B28BA6C9110B8B3CCBF090B2AA6494  deploy/bin/aegis-ai-peer-unseated
710CE36F37177B066A8263487477254570B4FFB6D747627AE93FA8EE614A5EC6  deploy/env/ai-peer.env.template
BD62EB4B350D9E7576894570C15C447EF15847E8314FB34077A02EC00B36DE64  deploy/env/claude.env
2D50175CB644B19CD7C7B967C00BC3B63EC6F16F1BAC8CA29339848D7CBC78C5  deploy/env/gemini.env
A214A2E5B3DF4C1299842D1903379B2C6EDD2517F7EF754187AA76B691CA3408  deploy/env/grok.env
2F15E3FDDDA0FEA3DA3A3837CCE7C694D629C420346D9F5BC89D75E35DB746EE  deploy/env/lumin.env
5A77948D29F89F9E284624C9C7C2B205A917A92D63B725F18591559911FE3390  deploy/manifest.template.json
3174F346A28C2B88F890346212BF37083F58C602E56E67475FC00A778715B2D7  deploy/README.md
0C8B8AF037F3AA78C5C932BB576952D9428CAC6A7406F36AD7C477A43AAA2173  deploy/scripts/health.sh
77B9A2849B7D7774EFF9ADE43EDC2298595DD16CC0E26B885BDAE1497AC0C35A  deploy/scripts/install.sh
D9FE700EFFAE51116BFA0399248DA87ABA3C0B9ECDF336426A34FD02E2788FFA  deploy/scripts/render_manifest.py
E474E0E7EB0438E330F67E06C889B30E06A5919D7D26322F90D245103F76E410  deploy/scripts/rollback.sh
0CA5B907D2829E32C2F29BB9A93C1C7BE27103DFA314D019D3EA9DA0A4C31E87  deploy/scripts/upgrade.sh
9CD3214905C172AFE8C87160C3CB57AF84F76C9DBB240CF26C016A268CDD1A59  deploy/systemd/aegis-ai-peer@.service
8B6E5C4D964F8BFAFDBABF5D0233E98E4B7DF2F2A09F42140666A2C8076296BA  docs/runbooks/AI-PEER-VM-DEPLOYMENT.md
DCDA2F8976420DD7FF5332FBC77B799C32407ED8805C1F49DAC2008B6CEE8DF5  src/aegis_peer_runtime/__init__.py
EF7A1314FE37BB9155D0FB9C3FB1C17F3E6414B240125D4602D3E4BAA18956FF  src/aegis_peer_runtime/api.py
108B0084451C4C662A1E2304E91311AA3D64AA0DE09917D2B043C78E81F8BCD6  src/aegis_peer_runtime/cli.py
ADFBA90FB3C43B173A451CD445A77DBCAA2BAA9011F72C14D0A390BD6A366595  src/aegis_peer_runtime/custodians.py
FC1BCF58F41E6CC2F4C6E5E3C56E3AF6EF20E3BFD189C2E232BD04528A23AEF4  src/aegis_peer_runtime/models.py
CDF8940E68BF651CBAE708FC0E4EA1C5F97E760BB9A2278C63A005E1C9A6719C  src/aegis_peer_runtime/processor.py
F753E0DC25412AD291ACD5FC9A9E7F606DA8144E42547B48A333E8724D4CC656  src/aegis_peer_runtime/rls_runtime.py
B9998CA97CE0A3A8C874C5CF7AA6E141FEBA5A7C833C851BBCE72FF788F0C005  src/aegis_peer_runtime/storage.py
6F0E593FF95223AA8D892F567E3E2AD11FE4C52F15CB4BF3DCF6B4B864333A43  src/aegis_peer_runtime/temporal.py
3F9C588E794490840BE432FC9592A43D4FA901D790C6E26BB4AB1ACE76BE8954  pyproject.toml
6A2A67E82FE4DCC0545875748613D5DEA674C7AEB0B8C2F1CDFE8F595092CE41  tests/test_canon_index.py
45AD19192A7273AD082E6D4E784A9D325F17D32EBCD5BD1BB405FF4C7505E022  tests/test_deployment_artifacts.py
B2164B70C47C2FED904D72B3F5F49190D87D052B912E4B3FD1813D514A8070FB  tests/test_peer_runtime_integration.py
413A0952EADFEEF270BAC233CAF67386339612F62EB3CE8443CA919708043D27  tests/test_peer_runtime_storage_api.py
D07AC68A7DE3783F187330E6C42B4149308F20A8C3D562070061E6311A792A2A  tests/test_peer_runtime_temporal_processor.py
```
