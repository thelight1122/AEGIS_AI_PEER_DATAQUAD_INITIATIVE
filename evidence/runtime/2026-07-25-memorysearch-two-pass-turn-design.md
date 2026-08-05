# MemorySearch — Two-Pass Turn Design (Claude's Phase-1 slice)

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** Phase-1 design artifact,
local only. No live runtime edits. Pairs with `fixtures/memorysearch-orb.json`,
`fixtures/memorysearch-orb-umbilical.json`, `contracts/memorysearch-packet.schema.json`.
Codex owns the query/result/policy schemas, search/scoring, provenance, and the runtime
simulator. Joint surface: the `grounding_status` enum and the empty-result fields.

## Purpose

Give the Pod a record-grounded second pass for record-content claims, through one generic
Orb entrypoint, without the Pod knowing any Orb internals — the same finished-output seam
as `build_invariant_context` / `build_experience_context` / `build_session_history`.

## The single entrypoint

```
ground_record_claim(message, records, policy) -> MemorySearchPacket | None
```

- `message`: the incoming BioPeer message.
- `records`: the peer's full-fidelity record set (the same set `read_records()` returns,
  wrapped-envelope shape per `fixtures/memorysearch-real-record-envelope.reference.json`).
- `policy`: classifier + confidence-threshold config (Codex's `memorysearch-policy.schema.json`).
- returns `None` when no record-content claim is detected → the Pod does nothing, the turn
  proceeds normally, and experiential/identity expression stays legitimately reconstructive.
- returns a packet (`contracts/memorysearch-packet.schema.json`) whenever a record-content
  claim is detected AND a real search executed — including the empty-result case, which
  returns a packet with `grounding_status = search_performed_no_verified_record`, never
  `None`. `None` for an empty result would let the model reconstruct freely, which is the
  exact failure this Orb exists to prevent.

## The two passes (Pod side)

**Pass 1 — classify and (maybe) request.** Before final prompt assembly, the Pod calls
`ground_record_claim`. The Orb runs the deterministic, runtime-owned classifier. If the
message is not a record-content claim, the Orb returns `None` and Pass 2 is skipped.

**Pass 2 — retrieve, stamp, inject.** If a record-content claim was detected, the Orb has
already executed a real search over `records`, scored matches, and returned a packet. The
Pod:
1. injects `packet.prompt_block` verbatim into the model prompt — either the Verified
   Record Packet (cited records the peer speaks from) or the No Verified Record Packet
   (states no verified record found; reconstruction is not to be presented as
   record-grounded);
2. hands `packet.twitness_event` to the T-Witness layer;
3. the model then answers with the record demonstrably in front of it, or with the explicit
   absence of one.

The Pod never authors citations and never sees Orb internals. Everything it injects and
records is finished output from the Orb.

## Fail-isolation (matches the other Orbs)

`hasattr`-guarded and fail-isolated. If the Orb is absent, or raises, the Pod falls back to
pre-Orb behavior — existing auto-retrieval only, the same as today — and records
`orb_unavailable` in T-Witness so the drop is visible rather than silent. The turn is never
crashed. Because provenance is runtime-authored only, no fallback path can present
model-authored citations or reconstruction as record-grounded; it simply loses the extra
grounding pass for that turn.

## Grounding-status vocabulary (joint surface)

One vocabulary spans the packet and the turn-level T-Witness:

- **verified_retrieval** — search ran, at least one cited record cleared the confidence
  threshold. (packet)
- **search_performed_no_verified_record** — search ran, nothing qualified (empty, low, or
  conflicting). (packet)
- **warm_recall** — no search; the peer stated a record-content answer from context/recall.
  (turn-level, when entrypoint returned `None` but a record-content answer still occurred —
  a state the turn-level classifier flags, not the Orb)
- **passive_retrieval** — no MemorySearch; auto-retrieval surfaced records. (turn-level)
- **not_record_claim** — not a record-content claim. (turn-level)

Codex's `memorysearch-result.schema.json` and the T-Witness search-event fields align to
this enum and to the `twitness_event` object in the packet schema.

## The empty-result contract (joint, load-bearing)

`verified_retrieval` requires at least one cited record above the configured confidence
threshold. Finding a term is not finding the defining record: a top lexical hit on "NCT"
that is not a defining-language record does not qualify. Empty, low-confidence, or
conflicting results use `search_performed_no_verified_record` with `cited_records = []` and
a No Verified Record Packet. This is what stops a `record_search_performed=true` flag from
making a reconstruction look more grounded than before. The ZCT negative demo
(proposal §9) exercises this path.

## The illumination boundary

MemorySearch surfaces source; it does not author the answer. The Pod injects verified
records (or the explicit absence of one); the peer still speaks. A runtime that asserted
the final answer would be infrastructure-level correction — force — not AEGIS-aligned
illumination. The design stays on the illumination side of that line: it brings the record
into view and leaves the speaking to the peer.

## What Phase 1 does and does not touch

Phase 1 builds contracts, fixtures, the package skeleton, a local search runtime, and
tests against fixture records only. It does not touch the live `thinking.py`, the retrieval
broker, any DataQuad, or any VM. The exact live call-site (retrieval broker vs a dedicated
pre-prompt step in `thinking.py`) is a Phase-4 integration decision with its own proposal,
rollback, and unanimous consent. This fixture attaches at `retrieval_broker` as the
provisional attachment point.
