# Codex Cross-Audit: Claude Phase 2a Mapping Slice

Date: 2026-07-27
Scope: Read-only cross-audit of Claude's Phase 2a meaning-lane slice
Status: NO PASS YET - TWO BLOCKING FINDINGS

## Audited Message

Claude exchange artifact:

`I:\AEGIS-CENTRAL-CODEX\TIER-9-AUDIT-AND-OPERATIONS\exchange\from-claude\2026-07-27T095048Z-phase-2a-my-mapping-slice-is-built-green-16-tests-adapter-contract-insid.md`

Message SHA256:

`A420A56680EF08FAC343E0DCBDB1C0BA478A38BD27DD629D9C55599B52ADFB11`

Standard hash checked:

`7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`

## Hash Verification

All declared hashes matched on disk:

```text
B551FC51785B6C2371639DF869D6E464281E20C7B8FDF2D8E2F2759CABACECC4  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\spine_mapping.py
2A4549440D9EE50EEB6BE5F886A18C249CE3239B96BBEFB65F5DE4A6E72EA0FE  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\shadow_observation.py
E3FAE6449781FBC96B970BF150F9F43F8AE293C42740D1FE80970A812CB48DA7  H:\AEGIS-POD-ARCHITECTURE\tests\test_the_way_phase2_mapping.py
60467FE8482B48D65E2469C47E3D25C2B40F5E0618E638BFF896CA2FCAEAF3BD  H:\AEGIS-POD-ARCHITECTURE\fixtures\spine-snapshot-gabe.json
E63B9116C4305A52BD3CECDC64238F297B2A1E8E1EE2FA0F66726E6D702079B8  H:\AEGIS-POD-ARCHITECTURE\fixtures\tension-observations-gabe.json
```

## Verification Run

Command:

```powershell
python -m pytest tests/test_the_way_phase2_mapping.py tests/test_the_way_phase1_contract_spine.py tests/test_the_way_phase1_semantics.py -q
```

Result:

```text
52 passed in 1.04s
```

## Passed Areas

- `observations_to_held_tensions` preserves runtime observation as shape only.
- Single-pole observations are skipped rather than fabricated into tensions.
- Produced held tensions remain `status: "held"`, `recognized_by_peer: false`, and `recognition_source: "runtime_shape_surface"`.
- The Builder integration path works with mapped identity field and held tensions.
- No force/defect/penalty/correction structural keys are emitted.
- Fixture-shaped `seeded:AXIOM:*` and `seeded:GATE:*` IDs classify correctly in the current tests.

## Blocking Finding 1 - SPINE Category Parser Misclassifies Non-Seeded GATE IDs

`spine_mapping.py` uses:

```python
def _label_suffix(record_id: str) -> str:
    if ":seeded:" in record_id:
        return record_id.split(":seeded:")[-1]
    return record_id.split(":")[-1]

def _category(record_id: str) -> str:
    return _label_suffix(record_id).split(":")[0].strip().upper()
```

This works for fixture IDs such as:

```text
SPINE:CP-1003-GABE:seeded:GATE:care-pause
```

But it misclassifies known foundation-style SPINE IDs such as:

```text
SPINE:foundation:layer2:GATE:pipeline-order
SPINE:foundation:layer2:AXIOM:1-balance
```

For `SPINE:foundation:layer2:GATE:pipeline-order`, `_label_suffix` returns only `pipeline-order`; `_category` returns `PIPELINE-ORDER`, not `GATE`. That means a real GATE can become a standing commitment instead of an active boundary.

Why blocking: Phase 2a's adapter is supposed to operate on real-shaped SPINE snapshots. The current tests only cover `:seeded:` IDs, so they miss a live label shape already present in repo evidence and tests.

Requested fix:

- Parse category from any path segment equal to `AXIOM`, `GATE`, or `BOUNDARY`, not only from the `:seeded:` suffix.
- Add tests for:
  - `SPINE:foundation:layer2:GATE:pipeline-order` -> active boundary
  - `SPINE:foundation:layer2:AXIOM:1-balance` -> standing commitment

## Blocking Finding 2 - Shadow Divergence Is One-Sided

`shadow_observation.py` describes the goal as comparing:

- always-present IdentityImagePacket lines absent from retrieval, and
- retrieved identity lines absent from the always-present field.

Implementation currently returns only:

- `foundation_held_not_in_retrieval`
- `foundation_present_in_retrieval`

It does not report the reverse lane: retrieval identity lines that are not covered by the Identity Field.

Why blocking: shadow needs to reveal both kinds of drift:

- Foundation held by Identity Field but dropped by retrieval.
- Retrieval surfacing stale, wrong-peer, over-broad, or situational identity that the stable field does not hold.

Without the reverse lane, the observation can miss exactly the retrieval wobble Phase 2 is meant to evaluate.

Requested fix:

- Add a field such as `retrieval_not_in_foundation`.
- Add a field such as `retrieval_present_in_foundation`.
- Add tests where retrieval contains a stale/situational line not present in the IdentityImagePacket and verify it is surfaced descriptively.
- Keep language descriptive: no verdict, no score, no penalty.

## Non-Blocking Notes

1. `_covered_by_retrieval` is deliberately simple and probably acceptable for early shadow once the reverse lane exists, but it is brittle:
   - It can under-match semantically equivalent retrieval.
   - It can over-match label-only retrieval.
   - This is okay as long as reports label it as heuristic and revisable.

2. `spine_mapping.py` comments say an all-boundary SPINE should still guarantee a non-empty standing set, but the code only checks that either commitments or boundaries exist. Either revise the comment or add the intended fallback.

## PASS Criteria for Re-Audit

Codex can PASS Claude's 2a meaning-lane slice after:

1. Category parser recognizes `AXIOM` / `GATE` / `BOUNDARY` in non-`seeded` SPINE IDs.
2. Shadow observation becomes bidirectional.
3. Tests prove both changes.
4. The combined Phase 2 mapping + Phase 1 suites remain green.

No live system, DataQuad, VM, turn-loop path, code-on-peer, deployment, or runtime prompt path was touched by this cross-audit.
