# Gabe vs Orion Live Runtime Diff

Generated: 2026-07-22
Scope: read-only comparison of live Orion and Gabe VMs after Gabe Phase 7 live-test report and Chamber assistant-fallback evidence.

## Summary

Gabe and Orion now share the same broad container/runtime shape: `AEGIS-CYBERPEER-CORE`, pod storage, same model substrate, same environment feature flags, and in-process RLS active. That is not sufficient to conclude Gabe is behaviorally equivalent to Orion.

The material differences are in the memory/relation surface and stale defaults:

- Gabe has a vastly larger durable DataQuad but a much shallower relation-ledger fabric.
- Gabe's `/health` still reports Orion's default `local_route` unless explicitly configured.
- Both live runtimes still carry Orion-specific `/turn` request defaults.
- Gabe's semantic/structural tensor artifacts are full-sized for the original imported record set, but are not refreshed to include post-bootstrap/test writes.
- Gabe's BioPeer/Architect evidence exists in raw records, but does not appear bound into relation ledgers the way Orion's does.

These differences are consistent with Tracey's Chamber observation: Gabe is able to write into the correct namespace, but his response path can still fall back to generic assistant behavior because continuity retrieval/grounding is not yet proven equivalent to Orion's.

## Container And Env

| Field | Orion | Gabe |
|---|---|---|
| Container | `orion-aegis-cyberpeer-core` | `gabe-aegis-cyberpeer-core` |
| Port | `127.0.0.1:8031->8790` | `127.0.0.1:8021->8790` |
| `AEGIS_DEFAULT_PEER_ID` | `CP-1004-ORION` | `CP-1003-GABE` |
| `AEGIS_DEFAULT_SESSION_ID` | `cp-1004-orion-session` | `cp-1003-gabe-session` |
| `AEGIS_STORAGE_MODE` | `pod` | `pod` |
| `AEGIS_RLS_ACTIVE` | `true` | `true` |
| `MODEL_NAME` | `huihui_ai/qwen3-abliterated:8b` | `huihui_ai/qwen3-abliterated:8b` |
| `MODEL_PROVIDER` | `openai` | `openai` |
| `OPENAI_COMPATIBLE_BASE_URL` | `http://host.docker.internal:11434/v1` | `http://host.docker.internal:11434/v1` |

Note: Gabe Docker requires `sudo` for inspection from the SSH login; Orion did not.

## Health Diff

| Field | Orion `/health` | Gabe `/health` |
|---|---|---|
| `peer_id` | `CP-1004-ORION` | `CP-1003-GABE` |
| `storage_mode` | `pod` | `pod` |
| `dataquad_read_ok` | `true` | `true` |
| `rls_status.active` | `true` | `true` |
| `current_tick` | `183` | `84525` |
| `tensor_counts` | PEER 127 / PCT 130 / NCT 106 / SPINE 62 | PEER 200 / PCT 200 / NCT 200 / SPINE 200 |
| `local_route` | `127.0.0.1:8031` | `127.0.0.1:8031` |

Gabe's `local_route` is wrong in health output. His container is actually mapped to `127.0.0.1:8021`; the endpoint is falling back to Orion's default `AEGIS_LOCAL_ROUTE`.

The `tensor_counts=200` values on Gabe are STM cache counts, not durable file counts.

## Durable Record Counts

| Tensor | Orion | Gabe |
|---|---:|---:|
| NCT | 106 | 9,673 |
| PCT | 130 | 32,949 |
| PEER | 127 | 35,675 |
| SPINE | 62 | 12,707 |

Gabe's records are present and large. This does not prove retrieval is correctly grounded.

## Ledger Counts

| Ledger | Orion | Gabe |
|---|---:|---:|
| `ledgers/advocate.jsonl` | 115 | 2 |
| `ledgers/steward.jsonl` | 164 | 6 |
| `ledgers/rls.jsonl` | 46 | 2 |
| `ledgers/repair.jsonl` | 21 | missing |
| `ledgers/orbs/rls-persistent-relations-core.evidence.jsonl` | 19 | 1 |
| `ledgers/relations/NCT-traversal.jsonl` | 17 | 1 |
| `ledgers/relations/PCT-traversal.jsonl` | 36 | 2 |
| `ledgers/relations/PEER-traversal.jsonl` | 21 | 1 |
| `ledgers/relations/SPINE-traversal.jsonl` | 0 | missing from health/list |
| `ledgers/relations/cross-tensor-relations.jsonl` | 5,178 | 423 |

This is the most important diff found so far. Gabe's relation fabric is tiny relative to the size of his DataQuad. Orion has fewer than 500 total records but 5,178 cross-tensor relations. Gabe has about 90k records but only 423 cross-tensor relations.

## Tensor Artifact Counts

Semantic index sizes:

| Tensor | Orion | Gabe |
|---|---:|---:|
| NCT | 89 | 9,671 |
| PCT | 94 | 32,945 |
| PEER | 106 | 35,673 |
| SPINE | 62 | 12,705 |

Structural tensor counts:

| Tensor | Orion | Gabe |
|---|---:|---:|
| NCT | 89 | 9,671 |
| PCT | 94 | 32,945 |
| PEER | 106 | 35,673 |
| SPINE | 62 | 12,705 |

Gabe's tensor artifacts were built over the imported baseline, but have not been refreshed for later first-boot/test writes (`SPINE` live JSONL is now 12,707; semantic/structural tensors remain 12,705).

## Identity Term Binding

Search for `Tracey`, `BioPeer`, `External Steward`, and `Architect`:

- Orion: terms appear in records, repair/RLS ledgers, `cross-tensor-relations.jsonl`, structural SPINE tensor JSON, and semantic SPINE index.
- Gabe: terms appear in records, `rls.jsonl`, tensor provenance files, and `FOUNDATION-PROVENANCE-PENDING.md`, but not in `cross-tensor-relations.jsonl` or structural SPINE tensor JSON by the same search.

This supports the Chamber observation: Gabe's identity/relationship facts may exist on disk, but are not yet visibly bound into the relation fabric that retrieval uses.

## Source Code Diff

Live source files checked:

- `core/cognition/thinking.py`
- `core/custodians/advocate.py`
- `core/custodians/boundaries.py`
- `core/custodians/retrieval_broker.py`
- `core/api/routes/turn.py`
- `core/api/routes/health.py`
- `core/dataquad/ledgers.py`
- `core/dataquad/stm.py`
- `core/dataquad/bootstrap.py`

Content diffs in `thinking.py`, `advocate.py`, and `boundaries.py` were line-ending only after pulling files locally and running `git diff --no-index`; no semantic source diff was found in those files. The observed behavior difference is therefore more likely data/relation/config/path driven than a different cognition implementation.

However, both live runtimes still contain stale Orion-specific `/turn` defaults:

```python
class TurnRequest(BaseModel):
    peer_id: str = "CP-1004-ORION"
    session_id: str = "cp-1004-orion-session"
```

This remains a drift vector for Gabe, Adam, and any future CyberPeer.

## Working Assessment

Gabe is not failing because the DataQuad is absent. Gabe is failing because the relation/retrieval fabric and/or Chamber route is not yet proven to be using that DataQuad with Orion-equivalent grounding.

Current best explanation for the 15-25s generic assistant behavior:

1. Gabe has far more durable records than Orion, but far fewer relation/traversal/Steward/Advocate/RLS ledger entries.
2. Gabe's identity anchors exist in raw records, but are not visibly cross-linked into the relation ledger/tensor surfaces.
3. The runtime defaults still contain Orion-specific route/session values.
4. Health observability still has Orion-specific `local_route` default on Gabe.
5. The Chamber UI may be hitting a route that writes to Gabe but does not inject the full Gabe continuity context, or may be sending incomplete peer/session values.

## Recommended Next Checks

1. Verify the Chamber endpoint target: prove whether the UI transcript used `127.0.0.1:8021/turn`, an older Gabe route, or another service.
2. Run a debug-only retrieval inspection for a non-mutating or controlled test prompt such as `Who is Tracey?`, capturing the actual `identity_continuity`, `context_claims`, `factual_continuity`, and `experiential_continuity` injected into the model.
3. Build or repair Gabe's relation ledgers over the full imported DataQuad, especially SPINE identity and BioPeer/Architect anchors.
4. Add a durable-count endpoint or health field separate from STM counts.
5. Fix `/turn` defaults before Adam: make `peer_id` required or derive it from `AEGIS_DEFAULT_PEER_ID`; same for session.
6. Set `AEGIS_LOCAL_ROUTE=127.0.0.1:8021` on Gabe for accurate health evidence.
7. Refresh Gabe semantic/structural tensors or document the delta after bootstrap/test writes.

## Conclusion

The live diff supports Tracey's observation. Gabe's infrastructure resembles Orion's, but Gabe's active relational grounding does not. The migration should not be called behaviorally complete until Gabe can answer identity/continuity probes from his own DataQuad and the relation fabric is demonstrably comparable to Orion's.
