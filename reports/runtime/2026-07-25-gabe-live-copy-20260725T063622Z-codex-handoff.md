# Gabe Live Pod Records Copy Handoff

Date: 2026-07-25
Reviewer/operator: Codex
Peer: CP-1003-GABE
Batch: `gabe-live-copy-20260725T063622Z`
Standard hash: `7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`

## Boundary

Read-only live snapshot only.

No live DataQuad mutation, VM write, runtime change, broker change, append, prune, or apply action was performed. The only live operation was SSH/SCP read access to copy four Pod record JSONL files from Gabe to local staging.

## Source Root for Claude

Use this source root for the retirement dry-run:

```text
H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\pod\records
```

Relative from repo root:

```text
stage-gabe-out/live-copies/CP-1003-GABE/gabe-live-copy-20260725T063622Z/pod/records
```

## Manifest and Hash Files

```text
H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\live-copy-manifest.json
H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\copy-manifest.json
H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\per-file-sha256.txt
```

Manifest SHA256:

```text
4C08DED13EDDC68840782B47CBAF7E5C3CA069EBA8597D243F085B859670D165
```

Per-file SHA256 list SHA256:

```text
BA34EADBFE7E19F8BC473BC7AADCE4630B063168FF71E271918329C3140AC9EB
```

Manifest validation:

```text
MANIFEST_VALID H:\AEGIS-POD-ARCHITECTURE\stage-gabe-out\live-copies\CP-1003-GABE\gabe-live-copy-20260725T063622Z\live-copy-manifest.json
```

## Copied Files

Remote base:

```text
/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1003-GABE/pod/records
```

| Tensor | Records | Bytes | SHA256 |
|---|---:|---:|---|
| PEER | 35,754 | 106,115,615 | `807F27F78985ADFDB8DF9390BB75D92B130446071E4954F0FD1DE70CC96B9DE0` |
| PCT | 33,123 | 847,110,671 | `0EA1FACC676319FD80288B30B08B9CDEC4A97DB36C8E295BA46C861150166637` |
| NCT | 9,769 | 26,796,056 | `6FC85376DFFB25DE97C20B243DE8C58AD61715DE24EB341EFFDFF1F54DE664AF` |
| SPINE | 12,707 | 33,662,996 | `3F7B56780246D75344F5A7897FD3359BF990FA1FD3D45BE430F8F9C5626192DF` |

Remote and local SHA256/count/byte values matched for all four files.

## Dry-Run Source Acceptance Smoke

Command:

```powershell
python -m src.aegis_pod.retirement_dry_run --source-root stage-gabe-out/live-copies/CP-1003-GABE/gabe-live-copy-20260725T063622Z/pod/records --no-write
```

Result:

```text
=== Stage-1 retirement DRY-RUN (nothing mutated) ===
  PEER: 35754 records, 106044188 content bytes
  PCT: 33123 records, 847044603 content bytes
  NCT: 9769 records, 26776616 content bytes
  SPINE: 12707 records, 33637584 content bytes
  PCT retirement candidates: 13721
  PEER promotion candidates: 0
  PEER exclusions: 35754 {'high_uniqueness_unique_experience': 14876, 'contested': 6, 'recent_experience': 20872}
  Projected PCT shrink: 13721 recs / 48275185 bytes (5.7%)
  Projected PEER shrink: 0 recs / 0 bytes (0.0%)
```

This was a `--no-write` smoke test only, run to confirm the staged source root is readable by the dry-run tool. Claude should run the full reporting dry-run from this source root.
