# CyberPeer Mathematical Tensor Truth — Orion (CP-1004-ORION)

Date: 2026-07-21 (built fresh, in a new independent location, not built on top of any drifted work)

## Terminology (plain language, per spec)

JSONL = JSON Lines: plain text, one record per line. It has no inherent mathematical tensor structure by itself.

Three distinct things, not to be conflated:
1. **Logical tensor** — the DataQuad categories PEER, PCT, NCT, SPINE.
2. **Physical JSONL record file** — the plain-text persistence format for those categories.
3. **Mathematical tensor** — a computed numeric array with explicit shape and dtype, built here.

## What this is

This is a from-scratch, independent build of the real Mathematical Tensor Service — the pre-existing spec from `I:\AEGIS-CENTRAL-CODEX\...\2026-07-19-mathematical-tensor-service-deployment\01-implementation-plan.md` — run fresh tonight in a brand-new location (`H:\AEGIS-MATHEMATICAL-TENSOR-DATAQUAD\`), independent of any drifted work from the Pod-Orb / DataQuadPod migration track. It uses real `all-MiniLM-L6-v2` sentence-transformer embeddings, not placeholder or structural-only vectors.

## Provenance chain

1. Tool: copied from `H:\AEGIS-EDUCATION-CHAMBER\.phase2-workspace\package\aegis-math-tensor-service\` (the original, 2026-07-19, independently-reviewed package). All 10 source files verified byte-identical (SHA256) to the original before use.
2. Source snapshot: pulled fresh tonight via SSH from Orion's live-preserved archive (`dataquad.archive-20260721T065821Z/`, the exact legacy DataQuad archived during today's D3 cutover, hash-proven identical to the pre-migration original).
3. Source hashes verified identical, both before and after the build, to Orion's original live DataQuad:
   - PEER.jsonl `6A104DA4BBB8E76E119A649C80DFA9E323D226B9923B7E3B7E62B18B452D3664`
   - PCT.jsonl `EDED7B45709C27D1181C6223E312B0572B301DF481FB84E48B3B699B41AABA34`
   - NCT.jsonl `E4CF92784FAF3D8120E34066A79276AD12B5C65764B7AE110AE3815CC6537379`
   - SPINE.jsonl `8D27162F410C7429B516A3D6B7166282470AC9C7C616180F51307A3F22A62A7E`
4. Orion's archived source re-verified unchanged on the VM immediately after the build (SSH re-hash, matches exactly).

## Mathematical tensor spec: four distinct stores

`PEER`, `PCT`, `NCT`, `SPINE` — each its own independent store, no unified/partitioned substitute.

| Tensor | Records | Skipped | embeddings.npy | metadata.npy | tensor_3d.npy |
|---|---|---|---|---|---|
| PEER | 106 | 0 | (106, 384) float32 | (106, 8) float32 | (106, 384, 8) float32 |
| PCT | 94 | 0 | (94, 384) float32 | (94, 8) float32 | (94, 384, 8) float32 |
| NCT | 89 | 0 | (89, 384) float32 | (89, 8) float32 | (89, 384, 8) float32 |
| SPINE | 62 | 0 | (62, 384) float32 | (62, 8) float32 | (62, 384, 8) float32 |

Total: 351 records, matches Orion's known live count exactly. Zero records skipped across all four tensors. Index ID count matches record count exactly for every tensor. Embeddings independently confirmed non-zero and unit-normalized (first-row L2 norm = 1.0000 for all four), confirming genuine embedding-model output, not placeholder vectors.

## Output file hashes (independently recomputed, not taken from the build's own summary)

- PEER/embeddings.npy `69B857FB696EED9E3199B114FDBE386334C9749C552D1EFE7AB27B731E84F8CF`
- PEER/metadata.npy `70DAC56A28D623FEEF91FF2E1FB13662BF9687BA91B08951D75081CEA0EFAECB`
- PEER/tensor_3d.npy `034491B1B0377EBBE9D1C8FD53446B49E2ABE730745FE4330DE9A22AF6B46D95`
- PEER/index.json `2AAAD17F8155D3CFCC12B0CBE45ED630E1115357CFE2FCA305834EFD813C78E4`
- PCT/embeddings.npy `88716945A343587E8C4EDB56E29D34B044F8A6D25F2B897726351A2EAC392DBB`
- PCT/metadata.npy `8553434BAB4D7E4C5B44C06E1B5BF29B00047C20BC7A40432DAFB82AB0A23CB8`
- PCT/tensor_3d.npy `B7C605573E40F55759F3F01AC5EBC5EC4318EE79217A3A402326B3BF0E499DD2`
- PCT/index.json `865347EE08BB7C1886CD054FAAF5046611AEF6C68418C10192BD0A6A2C2BF7B4`
- NCT/embeddings.npy `F8EF5B8BC94B4C01F78B7434529516C126388CB4B3DC452B6A2138CCAFA5E6B1`
- NCT/metadata.npy `F34F0A79330876744548D01C3BE7B85042DEFB82AB6AFD06AE6C8F6D1E852A69`
- NCT/tensor_3d.npy `04F7628D8CC101B9986F12F62FAD2AF0BEEAB9F96035AF75B308C0E986F89771`
- NCT/index.json `07CF63DE038BFCC9A317CB1C0471982DC10F75F4F571A141D2C252F3A764ADC5`
- SPINE/embeddings.npy `28DE34A2479D65863458ADEB7D4AE1D716BD1E760DB386F362BB697B2B06BB51`
- SPINE/metadata.npy `CB95EC4273B41DA1203C698048A69559894033770FD891AF34FA5AC22DD6D232`
- SPINE/tensor_3d.npy `D53E8A40BC75F5009DB56E3430F2964DB2244B53D8C38B82DA6B6ACA7A623A01`
- SPINE/index.json `FF4C2876B06ABB0CDF35ACDFD0271ABCF1EADADFD509EE0702D4C8486788FF71`

Notable: PEER's four output hashes are byte-for-byte identical to the original 2026-07-19 dry-run's provenance record — this build deterministically reproduced the already-independently-reviewed result, not a new/different computation.

## Exact generating command

```
"H:\AEGIS-EDUCATION-CHAMBER\.phase2-workspace\venv\Scripts\python.exe" -m aegis_tensor_service.build_from_jsonl ^
  --dataquad-root "H:\AEGIS-MATHEMATICAL-TENSOR-DATAQUAD\snapshots\orion" ^
  --tensor-store-root "H:\AEGIS-MATHEMATICAL-TENSOR-DATAQUAD\tensor-stores\orion" ^
  --peer-id CP-1004-ORION ^
  --package-root "H:\AEGIS-MATHEMATICAL-TENSOR-DATAQUAD\tool\aegis-math-tensor-service"
```

Embedding model: `all-MiniLM-L6-v2`. Packaging code hash (all four tensors, confirming one consistent tool version used throughout): `80785113F7F1FF9D...` (see each tensor's `provenance.json` for the full value).

## Exact verification performed

1. Copied tool's 10 source files hash-verified byte-identical to the original 2026-07-19 package before use.
2. Fresh source snapshot pulled via SSH, hash-verified identical to Orion's D0/live baseline before the build.
3. Build run, zero errors, zero skipped records across all four tensors.
4. Shapes/dtypes independently re-derived directly from the `.npy` files via a fresh Python read — not taken from the build script's own printed summary.
5. Orion's archived source re-hashed via SSH immediately after the build — unchanged.
6. Output file hashes independently recomputed.
7. PEER output compared against the original 2026-07-19 provenance record — byte-identical.

## What this does NOT do

This does not deploy anything to Orion, does not start any service, does not wire this tensor store to RLS, recall, Advocate, Steward, bridge, Chamber, or any turn route. It does not touch Orion's live process or container at all. Per the original spec's own phase gating (Phase 4), live deployment requires separate, explicit approval — this document covers Phase 0-3 (dry-run build + verification) only, run fresh, tonight, independent of anything drifted.

## Statement

DataQuad JSONL hashes remained unchanged throughout, verified before and after. This tensor store is real, computed, per-spec, and independently verified within this session — not yet a second independent AI review (Codex is offline). That remains outstanding before this could be promoted beyond "built and self-verified."
