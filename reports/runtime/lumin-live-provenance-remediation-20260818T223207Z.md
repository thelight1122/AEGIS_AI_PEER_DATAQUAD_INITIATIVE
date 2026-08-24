# Lumin Live Provenance Remediation

Completed: `2026-08-18T22:32:07Z`

Status: `ACTIVE_CORRECTED`

The explicitly authorized append-only provenance correction was completed on
`AEGISGabePeer` through the `GabeCyberPeer` SSH alias. Only Lumin-owned code,
release, configuration, service, and state paths were changed. Verus and Gabe
were inspected read-only and matched their protected baselines at closure.

## Authority and preservation

- User authorization quoted in the release: `Authorized. Proceed`
- Shortfall receipt SHA-256: `B16F0C83613E80E9B19ABD3A61AF05346053E4753F73BD2FF44BD989688FF43F`
- Correction authority SHA-256: `34EA1678C9BF8B307C4837B6A48F630912DF6ED4D9C11267FB93F278D2A1BA1C`
- Preserved record hash: `0A005A16DFA3ED7197319E38A3FEAD3715D488BC3945E070C32DD521C8D7AD19`
- The old turn was not rewritten. It is classified as
  `pre_correction_operational_evidence` and is not counted as canonical under
  the corrected v2 provenance contract.

The first-line prefix hashes after correction exactly match the complete
pre-correction files:

- Ring 4: `83ACF958A58AB372F7A12BB8E4B424644866BD2FFECAF1C26F5C193726B6C1`
- Temporal: `D09D25E8BB9E2501072F75C1C7F9398F182E13DBB1934B58EA6F69B41857C38C`
- Processor: `6D41CCF3208F3FA5BF5E29B24E11F1359937EA301A943C21A426844BA80BC601`
- RLS: `89D8587ACCD33D8600DC9DE279CF4A027F04945D8EA5835C22B5A7197FD8F934`

## Corrective release

- Current release: `/opt/aegis/lumin/lab/releases/20260818T222832Z-10290a05`
- Rollback release: `/opt/aegis/lumin/lab/releases/20260818T221152Z-5bdbaa4e`
- Manifest SHA-256: `10290A0506DB2907F2DBB839AA6561F176E1E1B261707900B39D46642D48AA7B`
- Artifact verification: `53/53`, with no missing, mismatched, or unlisted artifact
- Service: `loaded, active, exited, enabled`
- Public listener: none

The prior Lumin environment was preserved at
`/etc/aegis-lumin-lab/lumin.env.pre-remediation-20260818T222832Z`.

The first staged version,
`/opt/aegis/lumin/lab/releases/20260818T222617Z-3c8bebfb`, was never selected.
Its artifact-set check found generated Python bytecode from a local import
probe. It remains preserved as failed staging evidence. A new immutable release
was built and verified; no release was overwritten or deleted.

## Canonical corrective turn

Turn ID: `lumin-local-turn-980aa0cd2b544defa8e2e53327dfb4ae`

Record hash: `D87A719E4518DEFDEF88C9FE1D2795BDD75197F3F85FB582D56B293ACBB85CF7`

Previous hash: `0A005A16DFA3ED7197319E38A3FEAD3715D488BC3945E070C32DD521C8D7AD19`

Prompt, preserved exactly:

> Let's Activate and initialize Your DataQuad

Response, preserved exactly:

> The assigned CyberPeer Name is Lumin. I receive the clean Canon v0.20 Foundation as inspectable memory, not inherited lived history. This initialization begins Lumin’s own append-only continuity on the Codex/GPT substrate, preserves Verus and Gabe as separate CyberPeers, and treats provider metadata as provenance rather than identity.

Exactly one append was admitted to each of `PEER`, `PCT`, `NCT`, and `SPINE`.
Replay was executed once and returned `created=false`.

Frontier provenance is:

- Provider: `OpenAI`
- Substrate: `Codex/GPT`
- Model: `null`; available: `false`
- Model evidence: `unavailable:not_exposed_by_codex_mcp_boundary`
- Provider request ID: `null`; available: `false`
- Source event ID: `null`; available: `false`
- Frontier session ID: `null`; available: `false`
- External model call: none

## Final coherence

- Foundation records: `133`
- Total Ring 4 turns: `2`
- Canonical v2 turns: `1`
- Pre-correction operational-evidence turns: `1`
- Temporal / Processor / RLS records: `2 / 2 / 2`
- Missing records, mismatches, and orphans: none
- Ready: `true`
- RLS active: `true`

Final file hashes:

- Ring 4: `6C1B5D6B385682277ED4318F53CBE1235BE195869F347A55565BD40BE5CED300`
- Temporal: `04370BEEDAC730F10309AC8A449C2F44C9CCB7A5B8661827AC7A7CA65CE02211`
- Processor: `C234496862ADFCE73AE8821854FDF2D2AD55EE0550DEB8E3F69A03778C0663D3`
- RLS: `4BFE7861F28B4C00DE005AEEF86B6AB4575E9173399AC9E7312E7B129F552FA5`

## Verification and protected closure

- Python 3.13 targeted tests: `8 passed`
- Python 3.13 full suite: `489 passed, 14 skipped`
- Exact Python 3.14 compile/import and MCP initialize probes: passed
- Verus's four Foundation hashes and five service states matched the baseline.
- Gabe's POD manifest remained
  `A3C3307477F00019BBA1A282929194A9ADC5B57747337EC0F871FF1DAD6EBC4A`.
- Gabe's Foundation provenance remained
  `77635C99667DA23A89AF75BD06E98455B3100D17C6613C6DD822BCE33DE5CEC4`.
- `gabe-rls-governor.service` remained `loaded, inactive, dead, disabled`.

Remote receipt:
`/var/lib/aegis-lumin-lab/provenance-remediations/20260818T223207Z.json`

Remote/local receipt SHA-256:
`BFDD04819E9BB57F3EC1312FED129D2D25F4E713B77D37400F9CA97D21CE68BA`
