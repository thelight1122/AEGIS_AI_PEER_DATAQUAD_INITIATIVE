# Codex Phase 2a Shadow Harness Slice

Date: 2026-07-27
Scope: Local/offline Phase 2a only
Status: READY FOR CLAUDE CROSS-AUDIT

## Boundary

This slice is a pure local/offline adapter and harness. It does not:

- read live Gabe paths
- write any DataQuad
- change `execute_turn`
- inject a prompt
- deploy
- touch a VM
- alter any code-on-peer runtime

## Implemented

### `phase2_shadow.py`

New package module:

`H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\phase2_shadow.py`

Responsibilities:

1. Accept already-loaded local snapshot dicts or explicit local fixture paths.
2. Call Claude's meaning-lane functions:
   - `spine_snapshot_to_identity_field`
   - `observations_to_held_tensions`
   - `build_shadow_observation`
3. Call Codex's Builder:
   - `build_identity_image`
4. Return one offline report with:
   - input hashes
   - identity field hash
   - foundation hash
   - IdentityImagePacket hash
   - shadow observation hash
   - packet
   - shadow observation
   - `injected: false`
   - `live_system_touched: false`
5. Fail safe:
   - Missing invariant SPINE returns `emitted_packet: false`.
   - No packet is fabricated.
   - Failure is visible as data.

### Package Exports

Updated:

`H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\__init__.py`

Exports:

- `ShadowHarnessError`
- `ShadowHarnessResult`
- `build_phase2_shadow_report`
- `build_phase2_shadow_report_from_files`

### Runtime Hash Scope

Updated:

`H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\orb_evidence.py`

Runtime hash now includes:

- `builder.py`
- `spine_mapping.py`
- `shadow_observation.py`
- `phase2_shadow.py`

### Tests

New:

`H:\AEGIS-POD-ARCHITECTURE\tests\test_the_way_phase2_shadow_harness.py`

Covers:

- positive offline shadow report builds packet and observation
- IdentityImagePacket validates against contract
- negative-space policy intact
- active held tensions remain held-only
- bidirectional retrieval divergence present
- missing invariant SPINE fails safe with no packet
- file wrapper writes only to explicit output path
- missing local file raises visible harness error
- implementation module contains no live-action tokens

## Verification

Command:

```powershell
python -m pytest tests/test_the_way_phase2_shadow_harness.py tests/test_the_way_phase2_mapping.py tests/test_the_way_phase1_contract_spine.py tests/test_the_way_phase1_semantics.py -q
```

Result:

```text
60 passed in 1.06s
```

## Hashes

```text
BE011F6997E7397C8BBD6CB8C32DAF0F1E42FB89378D7C06B2F4A568455E8BC3  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\phase2_shadow.py
54B80F77A8B6C6291AF6F1A0B6F17ED8C0ADF02ED072B529A62521827E425CB2  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\__init__.py
540D85EE94DA73FFEDAAC01220BAB1B17B8FA50F6CF7CAB61C63ED227556AED1  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\orb_evidence.py
364061D1F1F0F8585F9A85169987EBCA58A94BB8A4046EE6CCDBA4493C3E9278  H:\AEGIS-POD-ARCHITECTURE\tests\test_the_way_phase2_shadow_harness.py
```

## Cross-Audit Request

Claude: please audit whether this adapter/harness:

1. Correctly preserves your meaning-lane ownership by importing your mapping functions rather than reimplementing them.
2. Correctly preserves Codex's Contract-spine boundary by calling `build_identity_image` unchanged.
3. Fails safe on insufficient identity surface without fabricating a packet.
4. Remains Phase 2a only: local/offline, no live read, no live write, no injection.
5. Produces enough side-by-side shadow evidence for the eventual consolidated 2a checkpoint.

Requested response: PASS or exact file/test deltas required before PASS.
