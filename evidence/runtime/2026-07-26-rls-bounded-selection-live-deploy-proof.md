# RLS Bounded Selection - Live Gabe Deploy And Proof

Date: 2026-07-26
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Scope

Tracey approved proceeding after Claude's audit PASS on both reconciliation items.

This deployed the audited RLS bounded-selection/canon-reachability fix to live Gabe and ran one gated live `/turn` proof.

## Live Target

- VM: `AEGISGabePeer`
- Resource group: `AEGISCYBERPEER_GROUP`
- Peer: `CP-1003-GABE`
- Container: `gabe-aegis-cyberpeer-core`
- Route: `127.0.0.1:8021 -> 8790`
- Deployed image: `aegis-cyberpeer-core_aegis-core:rls-bounded-20260726T084625Z`
- Preserved rollback container: `gabe-pre-rls-bounded-switch-20260726T084625Z`
- Preserved rollback image: `aegis-cyberpeer-core_aegis-core:g5-part-a-20260725T192355Z`

SSH timed out again, so deployment used Azure VM Run Command. Docker Compose was not used.

## Deployed Runtime Hashes

Remote source hashes after patch:

- `vendor/orb-rls-persistent-relations-core/src/orb_rls_persistent_relations_core/scoring.py`
  - SHA256 `C9B270BD1B9C782465DAC2544E2D8DD36D28475C9DBBC3208BC5C97F87B5680E`
- `vendor/orb-rls-persistent-relations-core/src/orb_rls_persistent_relations_core/engine.py`
  - SHA256 `3CA4097C826B8988C05B52680BFFE15F99161E3FA4B6E5623BBDCB9070374B67`
- `vendor/orb-rls-persistent-relations-core/src/orb_rls_persistent_relations_core/relevance.py`
  - SHA256 `BC645D799C28656F6B8124CDD6523917E011F4FBA201FD8DB9B32F1C7A33AE1A`

Imported module hashes inside running container:

- `orb_rls_persistent_relations_core.scoring`
  - path: `/usr/local/lib/python3.11/site-packages/orb_rls_persistent_relations_core/scoring.py`
  - SHA256 `C9B270BD1B9C782465DAC2544E2D8DD36D28475C9DBBC3208BC5C97F87B5680E`
- `orb_rls_persistent_relations_core.engine`
  - path: `/usr/local/lib/python3.11/site-packages/orb_rls_persistent_relations_core/engine.py`
  - SHA256 `3CA4097C826B8988C05B52680BFFE15F99161E3FA4B6E5623BBDCB9070374B67`
- `orb_rls_persistent_relations_core.relevance`
  - path: `/usr/local/lib/python3.11/site-packages/orb_rls_persistent_relations_core/relevance.py`
  - SHA256 `BC645D799C28656F6B8124CDD6523917E011F4FBA201FD8DB9B32F1C7A33AE1A`

## Health Before Live Proof

Before the gated live turn:

- PEER: 35,755
- PCT: 33,125
- NCT: 9,770
- SPINE: 12,707
- current_tick: 84,800
- cross-tensor relation lines: 5,739,214
- Orb evidence lines: 101

## Live Proof

Prompt:

`Gabe, briefly name one AEGIS axiom you can recall.`

Session:

`rls-bounded-live-verify-20260726`

Answer head:

`**Axiom 1:** All systems seek equilibrium. Imbalance produces tension. Tension seeks resolution.`

## Health After Live Proof

After the gated live turn:

- PEER: 35,756
- PCT: 33,127
- NCT: 9,771
- SPINE: 12,707
- current_tick: 84,803
- cross-tensor relation lines: 5,739,232
- Orb evidence lines: 102

Delta:

- PEER +1
- PCT +2
- NCT +1
- SPINE +0
- cross-tensor relations +18
- Orb evidence +1

## New RLS PCT Writeback

- line: 33,126
- raw bytes: 2,035
- id: `PCT:CP-1003-GABE:2026-07-26T08:51:05.964588+00:00:84800`
- session_id: `rls-bounded-live-verify-20260726`
- rls_session_id: `RLS:CP-1003-GABE:f101dd52-6e95-4e6c-893a-225f8efc1327`
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
- `selected_ref_count`: 18
- `retrieved_ref_count`: 18
- `retrieved_ref_hash`: `8ACFD9B4CE1385A644E297BA002BD8E0E105BF5433DB25BE4ED61BD994B2319A`
- `retrieved_ref_sample` count: 10

## New Live-Turn Witness PCT

- line: 33,127
- raw bytes: 9,189
- id: `PCT:CP-1003-GABE:2026-07-26T08:51:37.802195+00:00:84801`
- session_id: `rls-bounded-live-verify-20260726`
- rls_session_id: `RLS:CP-1003-GABE:f101dd52-6e95-4e6c-893a-225f8efc1327`
- top-level `retrieved_record_ids`: `None`
- `turn_kind`: `live_turn_witness`
- `answer_stored_in_peer_record`: `true`
- peer_record_id: `PEER:CP-1003-GABE:2026-07-26T08:51:37.098004+00:00:84800`
- `retrieved_ref_count`: 18
- `retrieved_ref_hash`: `8ACFD9B4CE1385A644E297BA002BD8E0E105BF5433DB25BE4ED61BD994B2319A`
- `retrieved_ref_sample` count: 10

## New PEER And NCT

PEER:

- line: 35,756
- raw bytes: 8,204
- id: `PEER:CP-1003-GABE:2026-07-26T08:51:37.098004+00:00:84800`
- session_id: `rls-bounded-live-verify-20260726`
- answer head: `**Axiom 1:** All systems seek equilibrium. Imbalance produces tension. Tension seeks resolution.`

NCT:

- line: 9,771
- raw bytes: 1,625
- id: `NCT:CP-1003-GABE:2026-07-26T08:51:41.501801+00:00:84802`

## Latest Orb Evidence

- evidence line count: 102
- selected_count: 18
- rejected_count: 0
- relations_recorded_count: 18
- failure_is_data: false
- runtime_hash: `1AE35835C51D751B6DA413B710D41495E2334D96C2F67ABFE4DD7566C6317BF8`
- input_hash: `BC1233962E43973C609A8EB0BC48C1CC2288C92667308E13AF0ED41B94146934`
- output_hash: `C66B5D6B38ECCEA7C134C07AD81D1DC49605D944DCC4A599B2D7AD0C88D8A143`

## Conclusion

PASS from Codex side.

The live proof shows the prior 26,090-selection behavior is gone for the same simple axiom prompt:

- RLS selected 18 records, not 26,090.
- Relation-store growth was +18, not +26,090.
- Foundational AXIOM canon reached Gabe's answer.
- PCT writeback remains compact: no full `retrieved_record_ids` list.
- Live-turn witness still stores answer in PEER and references it from PCT.

## Boundary

Completed:

- audited local RLS fix deployed to live Gabe
- current container preserved for rollback
- health verified
- one gated live `/turn` proof
- relation-store growth measured

Not completed:

- no broader live Pod/RLS activation beyond Gabe's already-active runtime
- no existing record rewrite
- no relation-ledger migration or pruning
- no Part B reverse trim
