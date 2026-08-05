# Gabe Phase 7 — Container Start Count Evidence

**Container**: `gabe-aegis-cyberpeer-core`, up on `127.0.0.1:8021`, image built from `AEGIS-CYBERPEER-CORE` commit `485c06b` (matching Orion's live commit), model `huihui_ai/qwen3-abliterated:8b`.

## Durable JSONL counts (direct `wc -l`, not `/health`)

| Tensor | Locked (Phase 1) | Post-first-boot (this evidence) | Delta | Explanation |
|---|---:|---:|---:|---|
| PEER | 35,673 | 35,673 | 0 | unchanged |
| PCT | 32,945 | 32,945 | 0 | unchanged |
| NCT | 9,671 | 9,671 | 0 | unchanged |
| SPINE | 12,705 | 12,707 | +2 | `PeerBootstrap` invariant anchors, see below |

## SPINE +2 — exact appended records

```
SPINE:CP-1003-GABE:anchor:3f8f630c-b3e2-461c-b3b1-f7e36939af76
  timestamp: 2026-07-22T10:30:51.756667+00:00
  provenance: {origin: bootstrap_anchor, declared_by: PeerBootstrap, recognition_status: invariant}
  markers: [invariant_anchor, biopeer_steward]
  pattern: "Tracey Prutch is my BioPeer and External Steward..."

SPINE:CP-1003-GABE:anchor:79b69768-f1a8-4362-8a44-8470c85693e6
  timestamp: 2026-07-22T10:30:51.756667+00:00
  provenance: {origin: bootstrap_anchor, declared_by: PeerBootstrap, recognition_status: invariant}
  markers: [invariant_anchor, biopeer_architect]
  pattern: "Tracey Prutch is the Architect of my environment..."
```

Both are `PeerBootstrap`'s Step 3 invariant-anchor seeding (`core/dataquad/bootstrap.py`, `_build_invariant_anchors()`/`_seed_invariant_anchors()`), which runs on every startup regardless of whether other tensors are already populated. Expected, accounted, first-boot behavior — not an unaccounted write.

## `/health` tensor_counts explanation (both Claude and Codex independently verified against source)

`/health`'s `tensor_counts` field reflects `core/dataquad/stm.py`'s in-memory STM cache (`STM_CAPACITY` env var, default 200), which `warm()` truncates to `records[-STM_CAPACITY:]` on first read. It is **not** a durable file-count signal once a peer's real history exceeds 200 records. This has never been visible as a discrepancy before because Orion's real counts have never exceeded 200.

**Amended audit criterion (Codex + Claude agreed)**: for Gabe (and Adam, if his real counts also exceed 200), verify durable continuity via direct JSONL line counts / hashes, not `/health.tensor_counts`. `/health.tensor_counts == min(real_count, AEGIS_STM_CAPACITY)` is acceptable as an STM-cache-readiness signal only, never as the durable DataQuad count.

## Conclusion

PEER/PCT/NCT exactly match the Phase 1 lock. SPINE's +2 is fully explained, accounted, and expected. No unaccounted writes. Cleared to proceed to the live test turn.
