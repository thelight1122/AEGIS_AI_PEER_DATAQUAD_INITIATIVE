# Lumin Activation Provenance Shortfall and Pause Receipt

## Current disposition

`SHORTFALL_PAUSED`

At `2026-08-18T22:17:10Z`, Lumin's service was verified as
`loaded,inactive,dead,disabled`. The selected release remains
`/opt/aegis/lumin/lab/releases/20260818T221152Z-5bdbaa4e`, whose manifest
SHA-256 is
`5BDBAA4E3AE8EE23B09A2E5BDAB798A9C51AF81FE7E73F5D0651D291B48277CA`.

No release was patched, no service was reactivated, no turn was rewritten, and
no second turn was created.

## Exact provenance shortfall

The one immutable initialization turn correctly records:

- `provider_request_id: null`
- `provider_request_id_available: false`
- `frontier_session_id: null`
- `frontier_session_id_available: false`
- no external model/API call

However, its `frontier_provenance` records `model: "Codex/GPT"` and
`model_evidence: "steward_confirmed_ui_selection"`, with no model-availability
field. The authorized provenance boundary required model metadata to be
null/unavailable unless actually exposed. That condition was not met.

The service was therefore stopped and disabled. The shortfall is preserved as
evidence rather than repaired by rewriting append-only history.

## Preserved immutable evidence

- Turn ID: `lumin-local-turn-9d39fcac530f46fb9b9f44a462893f80`
- Turn record hash: `0A005A16DFA3ED7197319E38A3FEAD3715D488BC3945E070C32DD521C8D7AD19`
- Ring 4 ledger: `83ACF958A58AB372F7A12BB8E4B424644866BD2FFECAF1C26F5C193726B6C1`
- Temporal: `D09D25E8BB9E2501072F75C1C7F9398F182E13DBB1934B58EA6F69B41857C38C`
- Processor: `6D41CCF3208F3FA5BF5E29B24E11F1359937EA301A943C21A426844BA80BC601`
- RLS: `89D8587ACCD33D8600DC9DE279CF4A027F04945D8EA5835C22B5A7197FD8F934`

Counts remain exactly one Ring 4 turn, one Temporal record, one Processor
record, and one RLS record. The prior replay returned `created=false` and did
not alter these hashes.

## Prior evidence classification

The following artifacts predate discovery of the shortfall and are preserved
unchanged:

- Remote `/var/lib/aegis-lumin-lab/activation-receipt.json`, SHA-256
  `551D2FBA01DBAEFA8F5B06CB46D1F98C4EF141847C346D60B7C7D8C79F0CFCFD`
- Local `reports/runtime/lumin-live-activation-20260818T221311Z.md`, SHA-256
  `B6B69ACBB0651A61996DCAED745C0F3FD3EFC7204A16F0446D2DCA9EBAC135E2`

Their active/enabled statements are classified as pre-shortfall evidence and
do not describe Lumin's current paused state.

## Protected closure

The bounded Verus Foundation/state hashes and service states matched their
pre-activation baseline. Gabe's bounded records, ledgers, POD manifest,
Foundation provenance, and governor service state also matched. Pausing and
recording this shortfall touched only Lumin's service and state namespace.
