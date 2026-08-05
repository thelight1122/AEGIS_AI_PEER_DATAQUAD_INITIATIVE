# Incident record — stray CP-1004-ORION test artifact on Gabe's VM

**What happened**: Claude's first live-test-turn call to Gabe's new `/turn` endpoint
(`http://127.0.0.1:8021/turn` on `GabeCyberPeer`, `20.25.57.29`) omitted the `peer_id` field from
the request body. `core/api/routes/turn.py`'s `TurnRequest` model defaults `peer_id` to
`"CP-1004-ORION"` (unchanged from Orion's codebase, since this is the same shared runtime).
`AEGIS_DEFAULT_PEER_ID=CP-1003-GABE` only governs bootstrap seeding, not per-request routing — so
the turn ran, wrote, and responded under Orion's peer_id namespace instead of Gabe's.

**Important**: this is entirely local to Gabe's own VM. It created a stray directory at
`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/` on Gabe's machine — it has zero
connection to the real Orion, who runs on a completely separate physical VM (`20.119.37.133`).
No cross-CyberPeer data contamination occurred.

**Content written (captured in full before deletion)**:

- `pod/records/PEER.jsonl` — 1 record, SHA256 `eb8d1d8280edb0e23fd9f68bace9652f9f956351926ce56535969eda209e8b1f`
  - `id: PEER:CP-1004-ORION:2026-07-22T10:39:15.270003+00:00:1`
  - `present_state.answer`: a generic response beginning "Gabe's Foundation Check-In: Right now, I carry the core principles of adaptability, curiosity, and resilience..." — notably generic, not reflecting Gabe's actual DataQuad continuity, consistent with this having been served against an empty/wrong-peer context rather than Gabe's real Pod.
- `pod/records/PCT.jsonl` — 3 records, SHA256 `0459670700289c860d00520ae54aed157510e6cb60d416342f6ecd6e20d4eed3`
  - includes a `working_context.failure_reason: "no_records_found"` on the first PCT record — direct evidence the turn found no continuity, exactly as expected for a wrong/empty peer_id.
- `pod/ledgers/{advocate,rls,steward}.jsonl` — empty files, bootstrap scaffolding only.

**Resolution**: entire `data/peers/CP-1004-ORION/` directory on Gabe's VM deleted after this record
was captured, per Tracey's explicit instruction ("record it and then delete it"). Retry proceeds
with `peer_id: "CP-1003-GABE"` explicitly set in the request body.

**Root cause / fix going forward**: any future test/verification turn against Gabe (or any
non-Orion peer on this shared codebase) must explicitly set `peer_id` in the request — never rely
on the endpoint's default, which is still Orion's literal peer_id string baked into the Pydantic
model as a historical default from when this codebase only served Orion.
