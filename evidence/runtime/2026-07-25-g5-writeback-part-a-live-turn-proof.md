# G5 Writeback Part A - Live Turn Proof

Date: 2026-07-25
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Scope

One gated live `/turn` was run against Gabe after Path A deployment, using a short prompt:

`Gabe, briefly name one AEGIS axiom you can recall.`

The client-side command was interrupted before its output returned, but the live health counts and record tails confirm the turn completed and wrote records.

## Count Delta

Before Path A deploy verification:

- PEER: 35,754
- PCT: 33,123
- NCT: 9,769

After gated turn:

- PEER: 35,755
- PCT: 33,125
- NCT: 9,770
- current tick: 84,800

Delta:

- PEER +1
- PCT +2
- NCT +1

## New PCT Records

### RLS PCT Writeback

- line: 33,124
- id: `PCT:CP-1003-GABE:2026-07-25T19:42:01.231261+00:00:84797`
- session_id: `g5-part-a-live-verify-20260725`
- rls_session_id: `RLS:CP-1003-GABE:9973fae0-dfbb-44d9-9aa0-3cdbbbc399f9`
- raw line bytes: 2,222
- body bytes: 1,580
- top-level `retrieved_record_ids`: `None`
- working_context keys:
  - `failure_is_data`
  - `failure_reason`
  - `intent`
  - `retrieved_ref_count`
  - `retrieved_ref_hash`
  - `retrieved_ref_sample`
  - `selected_ref_count`
  - `user_message`
- `selected_ref_count`: 26,090
- `retrieved_ref_count`: 26,090
- `retrieved_ref_hash`: `FCCDD305C3517DBE3F048B4F77244FB0E6DE0462DEE6F28E6C15A73C3A9E8EF4`
- `retrieved_ref_sample` count: 10

### Live-Turn Witness PCT

- line: 33,125
- id: `PCT:CP-1003-GABE:2026-07-25T19:43:06.954221+00:00:84798`
- session_id: `g5-part-a-live-verify-20260725`
- rls_session_id: `RLS:CP-1003-GABE:9973fae0-dfbb-44d9-9aa0-3cdbbbc399f9`
- raw line bytes: 9,373
- body bytes: 8,731
- top-level `retrieved_record_ids`: `None`
- working_context keys:
  - `answer_char_count`
  - `answer_stored_in_peer_record`
  - `has_thinking`
  - `intent`
  - `memorysearch`
  - `peer_record_id`
  - `pressure_state`
  - `retrieved_ref_count`
  - `retrieved_ref_hash`
  - `retrieved_ref_sample`
  - `think_char_total`
  - `turn_kind`
  - `user_message`
- `turn_kind`: `live_turn_witness`
- `peer_record_id`: `PEER:CP-1003-GABE:2026-07-25T19:43:06.227227+00:00:84797`
- `answer_stored_in_peer_record`: `true`
- `answer_char_count`: 91
- `retrieved_ref_count`: 26,090
- `retrieved_ref_hash`: `FCCDD305C3517DBE3F048B4F77244FB0E6DE0462DEE6F28E6C15A73C3A9E8EF4`
- `retrieved_ref_sample` count: 10
- working_context has no `answer` key

## Paired PEER Record

- line: 35,755
- id: `PEER:CP-1003-GABE:2026-07-25T19:43:06.227227+00:00:84797`
- session_id: `g5-part-a-live-verify-20260725`
- raw line bytes: 8,200
- body bytes: 7,555
- present_state keys:
  - `answer`
  - `has_thinking`
  - `image_count`
  - `memorysearch`
  - `think_char_total`
  - `user_message`
- answer char count: 91
- answer head:
  `AXIOM — All systems seek equilibrium. Imbalance produces tension. Tension seeks resolution.`

This verifies that the answer was not lost; the full answer remains in PEER and is referenced by the live-turn PCT.

## Lineage

For the new RLS PCT:

- source id: `PCT:CP-1003-GABE:2026-07-25T19:42:01.231261+00:00:84797`
- exact `rls_retrieved` relation count: 26,090
- sample relation:
  - relation: `rls_retrieved`
  - source: `PCT:CP-1003-GABE:2026-07-25T19:42:01.231261+00:00:84797`
  - target: `NCT:cyberpeer-gabe-session:rls-promoted:2026-06-28T16:27:38.000Z:163`
  - tags: `["recall"]`
  - written_by: `rls-engine`

Latest Orb evidence:

- file: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1003-GABE/pod/ledgers/orbs/rls-persistent-relations-core.evidence.jsonl`
- line count: 101
- latest raw line bytes: 572
- orb_id: `rls-persistent-relations-core`
- selected_count: 26,090
- rejected_count: 0
- relations_recorded_count: 26,090
- failure_is_data: `false`
- observable_events:
  - `session_started`
  - `candidates_scored`
  - `candidates_partitioned`
  - `pct_written`
  - `relations_recorded`
  - `session_completed`
- input_hash: `BC1233962E43973C609A8EB0BC48C1CC2288C92667308E13AF0ED41B94146934`
- output_hash: `8924798AB46470DFBBA3C95AAF12E6A71A2A8803C9368A2990A31641AAC1C31A`
- runtime_hash: `FF7545BD3487EF97BF1F46D3AE0D26A83D1A29D4EF0EB02A066D3C762E24C00F`

## Conclusion

PASS from Codex side.

The deployed Path A fix was exercised live:

- future RLS PCT writes no longer embed full `retrieved_record_ids`
- future live-turn PCT writes no longer embed full `retrieved_record_ids`
- future live-turn PCT no longer duplicates the answer body
- paired PEER retains the answer
- retrieval lineage remains available through relation edges and compact hash/count/sample evidence
- Orb evidence remains compact and records relation count

The forward flags remain real:

- unbounded RLS selection still selected 26,090 refs for a simple prompt
- relation-store volume still received 26,090 `rls_retrieved` edges for this single turn

Those are not Part A blockers, but they should be treated as the next pressure point before broader live Pod/RLS activation.
