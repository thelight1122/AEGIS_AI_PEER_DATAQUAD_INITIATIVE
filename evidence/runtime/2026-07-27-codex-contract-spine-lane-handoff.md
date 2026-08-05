# Codex Contract-Spine Lane Handoff

Date: 2026-07-27
Scope: Local Phase 1 only
Status: READY FOR CLAUDE CROSS-AUDIT

## Boundary

This handoff covers the Codex-owned Contract-spine lane for The Way / Pod Architecture Identity Field Builder. It does not mutate Gabe, Orion, any VM, any live DataQuad, any runtime prompt route, or shared infrastructure.

## Implemented Local Artifacts

- `contracts/identity-field.schema.json`
  - Defines Identity Field as self-image surface, not Witness/Locus.
  - Requires `is_self_image_not_witness: true`.
  - Rejects forbidden top-level Witness-claim keys.
- `contracts/identity-image-packet.schema.json`
  - Defines the bounded `identity-image-packet` emitted by the Builder Orb.
  - Requires negative-space flags as structural `const: false` values.
  - Requires source policy flags: Canon identity, memory subordinate, illumination-only correction, penalties disallowed, record claims require MemorySearch.
- `fixtures/identity-field-builder-orb.json`
  - Declares the local `identity-field-builder-core` Orb.
- `fixtures/identity-field-builder-umbilical.json`
  - Declares the local pre-prompt IdentityImagePacket umbilical.
  - Explicitly states local fixture-only Phase 1 behavior.
- `packages/orb-identity-field-builder-core/`
  - Pure local Python package.
  - Provides `build_identity_image`.
  - Provides `compute_runtime_hash`.
  - Fails visibly on missing required foundation/identity field.
  - Does not represent, retrieve, serialize, score, or decide Witness/Locus.
- `tests/test_the_way_phase1_contract_spine.py`
  - Validates positive schemas/fixtures.
  - Validates adversarial forbidden-key rejection.
  - Validates negative-space policy drift rejection.
  - Validates bounded output.
  - Validates runtime-hash exposure.
  - Guards against live path/action leakage in the new Contract-spine artifacts.

## Verification

Command:

```powershell
python -m pytest tests/test_the_way_phase1_contract_spine.py tests/test_the_way_phase1_semantics.py -q
```

Result:

```text
34 passed in 0.97s
```

This includes Codex Contract-spine tests plus Claude's already-cleared meaning-lane tests.

## Artifact Hashes

```text
B6CCC9E8D15D037A0DF6AF52A9CE59E55601AB7252F39E665B7138EAF5A899E7  H:\AEGIS-POD-ARCHITECTURE\contracts\identity-field.schema.json
24D80C392A58426D24F24C4E76FC6192D6E75314F1923C80ABCC7260650540C6  H:\AEGIS-POD-ARCHITECTURE\contracts\identity-image-packet.schema.json
58C25783859F26020E974AE07BC4BDBF040548E7F639B24B1268BF7126DC18ED  H:\AEGIS-POD-ARCHITECTURE\fixtures\identity-field-builder-orb.json
9675B7F2DCB37B2EDF7C2F9C4E1BBDD15F8AB823B1007BE6ABDE43296D3A42DF  H:\AEGIS-POD-ARCHITECTURE\fixtures\identity-field-builder-umbilical.json
AFB4D9A9289BD2B17BB5375E4254B2F0FCFF5DD9C31D329083424E4F3FFDBD24  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\pyproject.toml
1A60E4E05AE97192F0286D553B7940BBA17C2DE340F111FAEB4DD5229E1F4F8E  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\__init__.py
98D2E7BD233D8ECEEE5736E95E284EEDD5DE49DAF11F1291FD2C191FAC165F44  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\builder.py
07FB552E7BD0A1102E41A7F3E24B9C960FB91E297AC58ADC5BC285F228CC16B5  H:\AEGIS-POD-ARCHITECTURE\packages\orb-identity-field-builder-core\src\orb_identity_field_builder_core\orb_evidence.py
C2B25B57A6A1842DBA4950511306DC969CC4955A03EBAE275C8BBD423D1BD4EA  H:\AEGIS-POD-ARCHITECTURE\tests\test_the_way_phase1_contract_spine.py
```

## Cross-Audit Request

Claude should audit:

1. Whether the contracts preserve the negative-space Witness/Locus boundary.
2. Whether the Builder Orb remains a self-image/continuity surface only.
3. Whether source hierarchy matches The Way: Canon as identity foundation, memory subordinate, record claims requiring MemorySearch, no penalties.
4. Whether schema/fixture/package/test structure is enough for Local Phase 1 close.
5. Whether any wording or field name still risks implying that the Builder owns the Locus.

Requested answer: PASS for Local Phase 1 Contract-spine lane, or exact file/field/test deltas needed before close.
