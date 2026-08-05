# MemorySearch Local Phases 2-4 Audit Package

Created: 2026-07-25

Status: complete local package; ready for Claude audit.

## Scope

This package completes local-only MemorySearch work after Phase 1 closure:

- Phase 2: local two-pass simulator
- Phase 3: copied-record shadow replay
- Phase 4: integration design draft

No live execution occurred.

## Boundary

- No live DataQuad read or write.
- No VM change.
- No CyberPeer runtime integration.
- No `thinking.py` edit.
- No retrieval-broker edit.
- No shared infrastructure mutation.

Phase 5 remains the live execution gate.

## Phase 2

Implemented a local two-pass simulator:

`src/aegis_pod/memorysearch_two_pass_simulator.py`

Reports:

`reports/runtime/memorysearch-phase2/*.json`

Outcomes:

```text
gabe-nct-failure-prevented.json canon_definition policy_governed verified_retrieval packet=True citations=2 search=True
identity-expression-no-search.json identity_expression none not_record_claim packet=False citations=0 search=False
warmed-cache-risk-requires-packet.json record_content policy_governed verified_retrieval packet=True citations=1 search=True
zct-no-verified-record.json canon_definition policy_governed search_performed_no_verified_record packet=True citations=0 search=True
```

## Phase 3

Implemented copied-record shadow replay:

`src/aegis_pod/memorysearch_copied_record_shadow.py`

Input:

`stage-gabe-out/CP-1003-GABE/pod/records/*.jsonl`

This is a historical copied/mapped Gabe record set already present in the local repo. Phase 3 did not fetch, write, or touch live systems.

Report:

`reports/runtime/memorysearch-phase3-copied-record-shadow.json`

Outcomes:

```text
PASS gabe-copied-nct-record-shadow verified_retrieval citations=3
PASS gabe-copied-zct-no-record-shadow search_performed_no_verified_record citations=0
PASS gabe-copied-warm-cache-risk-shadow verified_retrieval citations=2
PASS gabe-copied-identity-no-search-shadow not_record_claim citations=0
```

Sample:

```text
per_tensor_limit=2000
records_loaded=8000
```

## Phase 4

Drafted integration design only:

`reports/runtime/2026-07-25-memorysearch-phase4-integration-design.md`

The design names a future `pre_prompt_record_grounding` attachment point, proposes `AEGIS_MEMORYSEARCH_ACTIVE=0|shadow|inject`, describes fail isolation with `orb_unavailable`, and defines rollback by disabling the flag. It does not perform integration.

## Validation

```powershell
python -m src.aegis_pod.memorysearch_two_pass_simulator --root .
```

```text
PASS gabe-nct-failure-prevented verified_retrieval
PASS zct-no-verified-record search_performed_no_verified_record
PASS identity-expression-no-search not_record_claim
PASS warmed-cache-risk-requires-packet verified_retrieval
REPORT_DIR reports\runtime\memorysearch-phase2
```

```powershell
python -m src.aegis_pod.memorysearch_copied_record_shadow --root .
```

```text
PASS gabe-copied-nct-record-shadow verified_retrieval citations=3
PASS gabe-copied-zct-no-record-shadow search_performed_no_verified_record citations=0
PASS gabe-copied-warm-cache-risk-shadow verified_retrieval citations=2
PASS gabe-copied-identity-no-search-shadow not_record_claim citations=0
REPORT reports/runtime/memorysearch-phase3-copied-record-shadow.json
BOUNDARY local copied records only; no live DataQuad, VM, runtime, or shared infrastructure touched
```

```powershell
python scripts\validate_contracts.py
```

```text
PASS MemorySearch Phase 3 copied-record shadow scenarios preserve local-only parameters
PASS MemorySearch Phase 2 turn fixtures preserve local two-pass simulator parameters
ROOT H:\AEGIS-POD-ARCHITECTURE
BOUNDARY local contracts and fixtures only; no live DataQuad roots referenced
```

```powershell
python -m pytest tests\test_memorysearch_entrypoint.py tests\test_memorysearch_runtime.py tests\test_memorysearch_two_pass_simulator.py tests\test_memorysearch_copied_record_shadow.py -q
```

```text
17 passed in 12.90s
```

```powershell
python -m pytest tests\test_memorysearch_entrypoint.py tests\test_memorysearch_runtime.py tests\test_memorysearch_two_pass_simulator.py tests\test_memorysearch_copied_record_shadow.py tests\test_orb_runtime.py tests\test_orb_runtime_version_gate.py -q
```

```text
28 passed in 101.14s (0:01:41)
```

Boundary grep:

```powershell
rg -n "ssh|scp|requests|http|thinking\.py|read_records|I:\\AEGIS-CYBERPEER-CORE|8011|8021" src packages tests fixtures contracts reports/runtime -g "*memorysearch*"
```

Result: no executable live reach in new MemorySearch code/tests/fixtures. Hits are schema URLs and documentation/reference text that marks live surfaces as gated or future design.

## Hashes

```text
FB22CFD6DFC276936A45A8D27581D27622F99E95E0A7835608E71D003607A8F6  contracts\memorysearch-query.schema.json
D80ABAFC2821C4074867912C763C2847DF5520191E0F422B036E358DF75B417E  contracts\memorysearch-result.schema.json
DF6492A7682D335EE5AD3122713CA33755BC954CDD99A6A9572CC551A85E94EA  contracts\memorysearch-policy.schema.json
A640FA25CE90BD68F408C729CECC4DF2501461A868DDC28BCDE24241C4E0D325  contracts\twitness-search-event.schema.json
EEAC031B2D2F4BB284848EFBFBDB8E793BF2C1A3C4BDD944C1A8604BD83B66C3  contracts\memorysearch-turn-report.schema.json
6EA442BA7DF633A12D427A9CB48B083E78C9297EDBAA17334964A2FECB3A08C8  contracts\memorysearch-shadow-report.schema.json
6DD96647A33DA161F052F3B2951E46AB3578DD6D0B4A3455B6A0C54094FB5CC9  fixtures\memorysearch-policy.json
98A052FA92B7A8BFA98AF77DA0E127D2448F280C580082BFAAF199C1AA82BDE1  fixtures\memorysearch-query-canon-nct.json
1FF752AFED82EEE9845ACA70A258F59C252737182EBB318E7CD4057971983394  fixtures\memorysearch-query-canon-zct.json
B0010199EE59EC7EBB2C8939A4847D011763C67EBF99609FB5A50775D4E540EB  fixtures\memorysearch-records.json
B2FEA181BB301FB1A50125F2F2BDF1CD30AB8E04820C0D9A5F59643304A1DBA8  fixtures\memorysearch-turns.json
393F98A64BA235B7677F9C37565E15CD07B2365D75E361BCD5D96040786D630F  fixtures\memorysearch-shadow-scenarios.json
420C7ECF0F0058E08669D3343ECD77635FFB4F0B6435C3513404D168E9275619  packages\orb-memorysearch-record-grounding-core\pyproject.toml
38983EECD2FA9F6BB0C10ECADEB8676D87F49514DF4F1E8016768E8C7EE7CB03  packages\orb-memorysearch-record-grounding-core\src\orb_memorysearch_record_grounding_core\orb_evidence.py
6F460F51E35853E7F99D455D1739AC9F2296B26E047A9F0D60BB338D69C22C2F  packages\orb-memorysearch-record-grounding-core\src\orb_memorysearch_record_grounding_core\policy.py
23424CAFA96CAD3E5625BC537EAA399392EADF2B6F87295B99E9FFEDABADA2CA  packages\orb-memorysearch-record-grounding-core\src\orb_memorysearch_record_grounding_core\provenance.py
767697C8B9A92726ABDD36F9B509050622F28B1147A112E9A0B24490ADB1B697  packages\orb-memorysearch-record-grounding-core\src\orb_memorysearch_record_grounding_core\search.py
4CDDCEB386FCCA50EBC5FA0E2183ACD71EEE9862E38BDF1F9B363A98FA31D9B2  src\aegis_pod\memorysearch_runtime.py
8EA1AA5DFEAD5808C0C11F238F9264057BBECB640E74CD03891105C55CDC447B  src\aegis_pod\memorysearch_two_pass_simulator.py
150C17C7B30BD3A692373FEA41962A72CC0DF07147899D9F2E0F1E22D9207D40  src\aegis_pod\memorysearch_copied_record_shadow.py
ED9FC47150CC4D0943A9B582FF76CDCEAFFEDD9288D91CD53B999BAE13085129  tests\test_memorysearch_runtime.py
38FCBF751F7A999AF13643445BF1836FBD9C0DC24CD68D0A7D09ED3AA2B5CB50  tests\test_memorysearch_two_pass_simulator.py
27620141637BB29FFAA66C51F780D8CEAAE76B88F7B561F16C4A689087B27E94  tests\test_memorysearch_copied_record_shadow.py
76B9C5D52AD4D0C8AB6BD2818EA28B522625AEB42B9EFE13ADB0762BEA897086  reports\runtime\2026-07-25-memorysearch-codex-phase1-slice-evidence.md
27AD2A32502CBF3D9572DED8BA8A38AE585E8F20505627C6908E56D96492C72D  reports\runtime\2026-07-25-memorysearch-phase2-local-two-pass-evidence.md
F97F73BF63D6638D9B255F2CF1C520768270CD3DA09087AA1037BD49A0BEBB77  reports\runtime\2026-07-25-memorysearch-phase4-integration-design.md
22DDB7119A930E9C574389C971830423FE9EC78FA0B8A64463807D78F1C79228  reports\runtime\memorysearch-phase3-copied-record-shadow.json
DD71887280F132B3D3E2494FA108DB7A4AA4BFDBD80FBF49B468AB6E6EF0BAD6  scripts\validate_contracts.py
```

## Open Local Enhancement

Orion copied records can serve as a cleaner provenance/control set, but the current Orion copy is raw/unwrapped. Adding that control needs a small wrapper/normalizer path before feeding MemorySearch. It is not required for this local package because the Gabe copied-record shadow directly exercises the original NCT failure class.
