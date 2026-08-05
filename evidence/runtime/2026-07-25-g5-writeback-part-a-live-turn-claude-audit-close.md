# G5 Writeback Part A — Live-Turn Verification: Claude Audit (Part A CLOSED)

**Created:** 2026-07-25. **Author:** Claude (Opus 4.8). **Status:** AUDIT — verdict **PASS; Part A
closed.** Audits Codex packet `2026-07-25T203528Z-g5-writeback-part-a-live-turn-proof`.

**Caveat on method:** this audits Codex's *reported* live-turn evidence (read from live Gabe by Codex).
It is internally cross-consistent and matches the deployed code I audited PASS. I did not independently
re-read the live records (that would need another live pull; disproportionate for a verification turn on
an accepted, reversible deploy).

---

## Turn
Prompt: *"Gabe, briefly name one AEGIS axiom you can recall."* Answer (91 chars): *"AXIOM — All
systems seek equilibrium. Imbalance produces tension. Tension seeks resolution."* — a real SPINE axiom,
correctly grounded (no fabrication). Count delta: PEER +1, PCT +2, NCT +1; tick 84,800.

## Verified — the fix works end-to-end live
| Check | Result |
|---|---|
| RLS PCT body size | **1,580 bytes** (was up to ~6.67 MB) ✓ |
| Live-turn witness PCT body size | **8,731 bytes** ✓ |
| Top-level `retrieved_record_ids` (both PCT) | `None` ✓ |
| Compact summary present | `retrieved_ref_count` 26,090 + `retrieved_ref_hash` + 10-sample ✓ |
| Answer not duplicated in PCT | no `answer` key; `answer_stored_in_peer_record=true`, `answer_char_count=91` ✓ |
| Answer preserved in PEER | present_state.answer = full 91-char axiom ✓ |
| Lineage preserved | 26,090 `rls_retrieved` edges; Orb evidence selected=relations_recorded=26,090, rejected=0 ✓ |

Internal consistency confirmed: both PCT records share the rls_session_id and retrieved_ref_hash
(`FCCDD305…`); witness PCT `peer_record_id` matches the paired PEER id; char counts and selected/edge
counts all agree.

**Verdict: PASS. Part A is closed** — future PCT writes (both the RLS path and the live-turn witness
path) no longer embed the full retrieval-ID list or duplicate the answer; lineage remains via relation
edges + compact hash/count/sample + Orb evidence.

## Forward flags — now confirmed LIVE (elevate before broader Pod/RLS activation)
1. **Unbounded RLS selection.** A one-line prompt selected **26,090 refs** (~29% of the store). This is
   the root cause; Part A only stops it from bloating the PCT body. Bounding the selection is the clear
   next priority.
2. **Relation-edge relocation is now active, not hypothetical.** This single turn wrote **26,090
   `rls_retrieved` edges** into the relation store. Part A moved the ID volume *out of the PCT body*, but
   the same volume now lands in the relation store every turn. The PCT-body win is real; the **net
   storage benefit depends on relation-store efficiency**, and at ~26k edges/turn this is the next
   pressure point. Recommend measuring relation-store growth per turn before any broader live RLS switch.

## Still separate / gated
- **Part B** (reverse the existing ~847 MB) — gated archive-first data op with Tracey.
- The two forward items above — their own scoping.
