# DataQuad Retirement — Current-vs-Aligned Gap Spec

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** analysis/spec only. No
live peer, DataQuad, VM, or runtime touched. **Trigger:** Tracey's proposal to reduce Gabe's
PCT (574 MB / 33k records) and PEER (106 MB / 35k records) bloat by condensing into NCT/SPINE
with rehydration, and the finding that TurboQuant is not deployed and its guard forbids
PEER/PCT as source.

## 1. The problem being solved

Gabe's live tensors grow unbounded. PCT is the worst: ~17 KB/record, bloated by the full
`retrieved_record_ids` embedded in every RLS writeback. The full-fidelity retrieval cache
loads all of this into RAM (the source of the 2026-07-24 host OOM, since fixed at the
allocator level but not at the data-size level). More records also means more retrieval
noise, which degrades grounding (relevant to MemorySearch). The intended lifecycle —
active tensors condense and retire into deep symbolic stores — is not running.

## 2. Canon / aligned target (what SHOULD happen)

- Canon §7.2–7.3: memory migrates by use, not age. **"Decay is not deletion. Condensation
  is not loss."** PCT (Persistent Context Tensor, active working memory) condenses into NCT
  (Nostalgic Context Tensor — relics: markers, pattern summaries, reference nodes).
- Nexus alignment audit (`I:\AEGIS-CYBERPEER-CORE\docs\CYBERPEER-NEXUS-BM-ALIGNMENT-AUDIT.md`):
  - Steward path: **PCT → NCT** after a ~2-week inactivity window, via a TurboQuant
    retirement audit.
  - Advocate path: **PEER → SPINE** when a record is established+stable (confirmation count,
    no contradictions, age threshold).
  - PEER and PCT are the active ~2-week "Conscious Cache"; **NCT and SPINE are the deep
    stores — TurboQuant-distilled artifacts, accessed during RLS and deep rehydration.**
- TurboQuant (`@thelight1122/aegis-dataquad-core`) is the bounded-retirement engine for the
  **symbolic** layer, with hard guards:
  - `TURBOQUANT_FORBIDDEN_SOURCE_PREFIXES = ["PEER:", "PCT:"]` → TQ-002 live-tensor-forbidden.
  - `targetTensor` ∈ {NCT, SPINE} only; recipe must forbid meaning-storage / peer-compression
    / pct-compression / exact-replay.
  - artifacts `reconstructiveOnly: true`, `exactReplayForbidden: true` → rehydration is
    **approximate**, not exact restore; every recipe must `preserve` relationships, lineage,
    structure, reference-integrity.

## 3. Current state (what ACTUALLY runs), grounded

- Live runtime is Python (`I:\AEGIS-CYBERPEER-CORE`). It has a basic consolidation: a
  `"retirement"` clock phase (`steward.py`), `evaluate_recursive_learning_readiness` (>5 PCT
  → consolidation recommended), and a per-turn `nct_consolidation` that writes NCT records.
- This consolidation writes NCT relics but **does not archive or prune the source PCT/PEER
  records** — the live tensors keep growing (33k / 35k). It is a write-more mechanism, not a
  retire-and-shrink one.
- **TurboQuant is not deployed here.** No TurboQuant code in the Python runtime (only the
  docs mention above); `records.py` NCTRecord/SPINERecord have no `quantization` field; no
  live record is a TurboQuant artifact. TurboQuant exists only in the TypeScript package and
  the `AEGIS-DATAQUAD-PEER` TS project — a different stack with no TS↔Python bridge.
- Ongoing bloat source unaddressed: PCT writeback embeds full `retrieved_record_ids`
  (~17 KB/record).

## 4. The gap (aligned − current)

| # | Aligned | Current | Gap |
|---|---------|---------|-----|
| G1 | ~2-week inactivity retirement audit triggers PCT→NCT | consolidation runs on a >5-PCT heuristic, no inactivity window, no source retirement | build the inactivity-windowed retirement audit |
| G2 | Retire = condense + ARCHIVE source (hash-proof), tensors shrink | NCT written, source PCT/PEER kept forever | build archive-and-prune with hash-proof (Amendment 4) |
| G3 | Advocate PEER→SPINE on established+stable | not implemented as a retiring promotion | build PEER→SPINE promotion criteria + archive |
| G4 | NCT/SPINE bounded by TurboQuant distillation | TurboQuant absent from the runtime | integrate TurboQuant (Python port or TS↔Python bridge on exported JSONL) |
| G5 | PCT writebacks stay lean | ~17 KB/record from embedded retrieved IDs | trim what new PCT records store (prevention) |

## 5. The correct pipeline (guard-compliant)

Two stages. TurboQuant is stage 2 only; it never sees PEER/PCT.

**Stage 1 — condense the live tensors and archive the sources (this is what shrinks
PCT/PEER):**
- PCT → NCT: select PCT records past the inactivity window, condense to NCT relics
  (distilled_summary / essence / pivots, with `source_record_ids` + lineage back to the
  originals), then archive the source PCT records with hash-proof (rename-not-delete,
  Amendment 4) and drop them from the live tensor.
- PEER → SPINE/NCT: for established+stable PEER records only, extract pattern → SPINE (or
  essence → NCT), archive source PEER. Handle PEER conservatively — it is identity substrate
  (Axiom 16); never retire SPINE-anchored, high-uniqueness, or recent/contested experience.
  Good first candidates: the confabulation-tainted turns and redacted-leak records (pure
  noise).
- Reversibility: the archived originals + lineage refs are the "way back"; approximate
  rehydration is available from the relics, exact restore from the archive.

**Stage 2 — bounded-retire the symbolic layer:**
- Once NCT/SPINE accumulate, run TurboQuant on OLD NCT/SPINE records (guard-legal: NCT:/SPINE:
  sources), producing reconstructiveOnly quantized artifacts with a steward TurboQuant ledger
  entry, keeping the deep stores bounded. Rehydration is approximate, on demand, via lattice
  refs.

## 6. Constraints and boundary

- **Archive-not-delete, hash-proof** everywhere (Canon: decay ≠ deletion; Amendment 4).
- **Rehydration is approximate**, not exact — so the archive (not the relic) is the exact
  way-back. Important for PEER.
- **Guard compliance**: TurboQuant sees NCT/SPINE only; PEER/PCT never (TQ-002).
- **PEER > PCT in caution**: PCT is working context (safe to condense broadly); PEER is lived
  experience/identity (selective, conservative).
- **Integration**: TurboQuant is TS; the peer is Python — needs a Python port or a bridge
  operating on exported JSONL. Decide before any execution.
- **Boundary**: everything above is a spec. Executing retirement on a live peer is a gated
  live DataQuad write (reversible via archive), requiring its own proposal + Tracey consent
  (and Codex where it touches shared doctrine). Nothing here runs on a peer.

## 7. Recommended sequence (if pursued)

1. Fix G5 first (trim PCT writeback embed) — cheap prevention, stops re-bloat, code-only.
2. Build Stage 1 (condense + archive + prune) as a local, dry-run-first tool against an
   EXPORTED copy of Gabe's DataQuad; verify hash-proof archive and lineage; measure the
   size reduction; audit before any live apply.
3. Decide TurboQuant integration (port vs bridge) and build Stage 2 against the exported copy.
4. Only then propose a gated live apply on Gabe, archive-first, reversible.
