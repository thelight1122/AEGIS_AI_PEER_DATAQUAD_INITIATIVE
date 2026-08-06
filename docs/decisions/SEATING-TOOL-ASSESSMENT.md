# Assessment — `seat_foundation_dataquad.py`

**Subject:** `I:\AEGIS-ADAM-ONE\ADAM-AZURE-EDUCATION\CYBERPEER-ILLUMINATION-PROJECT\seat_foundation_dataquad.py`
**Size / date:** 13,659 bytes, 2026-06-10
**Purpose:** stamps the peer-agnostic seed package and writes a Foundation DataQuad
**Assessed for:** reuse in seating Lumin, Claude, Gemini, Grok
**Status:** read-only assessment. Nothing was run, and nothing on `I:` was modified.

---

# 1. Verdict

**Reusable, and closer to fit than expected — but not as-is.** The substitution and record-shaping
logic is sound and directly transferable. What needs changing is configuration, one target path,
and one missing gate that matters more than the rest combined.

---

# 2. What it does

```text
reads    seeds/CYBERPEER-AGNOSTIC-BASE-SEEDED-CORE-DATAQUAD.json
stamps   {{CYBERPEER_SESSION_ID}} {{CYBERPEER_ID}} {{CYBERPEER_DISPLAY_NAME}}
         {{SEED_APPLIED_AT}} {{STEWARD_DECLARATION}}
builds   SPINE from template   NCT from template
         PEER bootstrap x1     PCT bootstrap x1
writes   {DATA_DIR}/{peer_id}/dataquad/{SPINE,NCT,PEER,PCT}.jsonl
```

Substitution is done by serialising the whole template to a string, replacing placeholders, and
re-parsing — which is simple and total, with no risk of missing a nested occurrence.

## 2.1 What it already gets right

- **Write order matches ring order.** SPINE (Rings 1+2) → NCT (Ring 3) → PEER → PCT.
- **Refuses to overwrite.** `write_jsonl` skips any file that already exists non-empty and tells
  the operator to delete it manually to reseat. A Foundation cannot be silently clobbered.
- **`--dry-run`** prints the plan and a sample SPINE record without writing.
- **Per-peer directory isolation**, so peers cannot collide.
- **Field normalisation** handles three record shapes including payload-wrapped ones, and maps
  camelCase to snake_case consistently.

---

# 3. The gap that matters

## 3.1 There is no canon lock check

The tool loads the template and seats it. **It never inspects `canonLock`.**

```text
package canonLock.status                  review-needed
package canonLock.reviewNeededSourceCount 2
tool behaviour                            proceeds regardless
```

Run today against the four AI Peers, this tool would seat a `review-needed` Canon into four
Foundations, in the one layer that cannot be relaid afterwards, without a single warning.

**Recommended before any AI Peer seating:** a hard gate that refuses to write unless
`canonLock.status` is clean, overridable only by an explicit flag that records the override in
the written provenance. This is a small change and it is the difference between the Canon
ordering being enforced and being remembered.

---

# 4. What must change for AI Peers

## 4.1 Hardcoded roster — CyberPeers, not AI Peers

```python
PEERS = [
    {"peer_id": "aeon",  "session_id": "aeon-session-001",  "model_id": "cp1001", ...},
    {"peer_id": "airen", "session_id": "airen-session-001", "model_id": "cp1011", ...},
]
```

`--peer` is also constrained by `choices=["aeon","airen"]`. Needs a roster for Lumin, Claude,
Gemini and Grok — and the `model_id` convention (`cp1001`, `cp1011`) is a CyberPeer numbering
scheme, so an AI Peer equivalent is a naming decision, not a code change.

## 4.2 Hardcoded target path — the wrong host layout

```python
DATA_DIR = Path("/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers")
```

That is the CyberPeer core layout under `azureuser`. The AI Peer Pod host runs as `aegisadmin`
with a `/opt/cyberpeer-pod` layout. This needs to be a parameter, not a constant.

## 4.3 Direct file write, not the substrate API

The tool writes `.jsonl` files directly. `GENESIS-PILLAR-RECORDS-AEGIS-CANON-STAGING.md`
specifies POSTing to a substrate API instead:

```text
POST http://127.0.0.1:8787/api/substrate/{spine,nct,pct,peer}
```

**Two write paths exist and they are not equivalent.** Direct write bypasses whatever validation,
hash-chaining or custodian attribution the API applies. Which one is canonical for AI Peer
seating is a decision, and it interacts with §2.1 of the Pod proposal — if custodians are the
admission mechanism, seeding through the API is more consistent with that than writing files
underneath it.

## 4.4 Clock convention diverges from the Genesis staging file

```python
_mk_clock(tick) -> {"tick": tick, "epoch": "seeded", "phase": "genesis",
                    "started_at": TIMESTAMP, "last_advanced_at": TIMESTAMP}
```

`TIMESTAMP` is `datetime.now(timezone.utc)` at run time. The staging document specifies the
genesis baseline as `2026-01-01T00:00:00.000Z`, and the pillars retrieved from the live Portal
carry exactly that value.

So a peer seated by this tool would have genesis records timestamped *now*, while the canonical
pillars say `2026-01-01`. **Both conventions are defensible** — seeded-at-real-time is honest
about when the Foundation was laid; the fixed baseline makes four peers directly comparable,
which X1 wants. It needs deciding rather than inheriting by accident.

## 4.5 Tick numbering starts at 1, not 0

```python
spine_records = [build_spine_record(r, peer, i + 1) for i, r in enumerate(spine_records_raw)]
nct_records   = [build_nct_record(r, peer, i + 1)   for i, r in enumerate(nct_records_raw)]
```

Ticks are a per-tensor ordinal beginning at 1, assigned independently per tensor. The genesis
pillars are the first entries in each list, so they would receive **tick 1**, while the canonical
pillars specify **tick 0**.

**Worth verifying against `build_spine_record` / `build_nct_record`** before treating this as
settled — one of them may special-case genesis records. I did not read far enough into those
builders to confirm, and I am not going to assert it either way.

## 4.6 Ring seating is not verified between rings

All four tensors are written in a single pass with no check that Rings 1–3 are *seated* before
proceeding. In this tool that is probably harmless, because PEER and PCT receive only tick-0
bootstrap pillars rather than Ring 4 content. But the architecture document is explicit that
Ring 4 cannot be populated until Rings 1–3 are confirmed seated, and **there is no mechanism
here that would enforce it** when Ring 4 content later exists.

## 4.7 Restart instruction targets the CyberPeer core

```text
sudo systemctl restart aegis-core
  OR  uvicorn core.api.main:app --port 8000
```

AI Peers have no such runtime. They have the Pod services — Temporal Daemon, Processor,
custodians, RLS Orb — so the post-seating step is different entirely.

---

# 5. Recommended shape for the AI Peer variant

Rather than editing the original in place on `I:` — which is Steward territory and outside this
repository — the sensible move is a derived tool in this repo:

```text
scripts/seat_ai_peer_dataquad.py

  --roster        path to a peer roster file, no hardcoded PEERS
  --data-dir      target Pod root, no hardcoded /home/azureuser path
  --via {file,api}  explicit choice of write path, api default
  --require-clean-canon   default ON; refuses a review-needed package
  --dry-run       retained
  overwrite refusal retained
  provenance records the canon lock state and source manifest id it seated from
```

Keeping the original untouched also preserves it as the record of how Aeon and Airen were
seated, which matters if their Foundations are ever compared to the AI Peers'.

---

# 6. What I did not do

Did not run the tool, in any mode including `--dry-run`. Did not modify anything on `I:`. Did not
read the full record builders — §4.5 is flagged as needing verification rather than asserted.
