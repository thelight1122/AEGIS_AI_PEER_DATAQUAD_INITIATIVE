# Codex Verification - Orion Mathematical Tensors and JSONL Context

Timestamp: 2026-07-22T04:25Z

Boundary: read-only live verification. No Orion mutation, tensor rebuild, DataQuad write, restart, archive operation, or cleanup was performed.

Host:

- SSH alias: `OrionCyberPeer`
- Hostname: `AEGISOrionPeer`
- Checked path: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1004-ORION/pod`

## Result

PASS with freshness caveat.

Orion's live Pod contains mathematical tensor artifacts and JSONL context/record files.

The JSONL Pod records are current through the live post-switch appends. The generated tensor arrays and structural tensor JSON files represent the prior generated tensor batch and have not yet been incrementally refreshed for the later live appends.

## JSONL Context / Record Files

Verified parseable JSONL with zero JSON parse failures:

| Tensor | JSONL path | Current record count | SHA256 |
| --- | --- | ---: | --- |
| PEER | `pod/records/PEER.jsonl` | 127 | `004ee1834cc2e12a234242f343e16400214bb8800075325f5e9b9e437c86695e` |
| PCT | `pod/records/PCT.jsonl` | 130 | `2a509b59950a606290e7cd1f191cb0d40029034d36cb01d5a068a37c7ae37768` |
| NCT | `pod/records/NCT.jsonl` | 106 | `0263a8f496fb1bb57e059608aba71990bc1fc20feef490fab56a3531758c14c4` |
| SPINE | `pod/records/SPINE.jsonl` | 62 | `7b3b76e841d048b749fccaa3dabb8c5c2b71b598387a0ca215ea2edda5de9419` |

The live `pod-manifest.json` points each tensor storage field to these JSONL files, and all four manifest storage paths matched the actual files.

## Semantic Mathematical Tensor Files

Verified `.npy` headers directly, without requiring NumPy on the VM:

| Tensor | File | Shape | dtype | SHA256 |
| --- | --- | --- | --- | --- |
| PEER | `pod/tensors/semantic-embedding/PEER/tensor_3d.npy` | `(106, 384, 8)` | `float32` | `034491b1b0377ebbe9d1c8fd53446b49e2abe730745fe4330de9a22af6b46d95` |
| PCT | `pod/tensors/semantic-embedding/PCT/tensor_3d.npy` | `(94, 384, 8)` | `float32` | `b7c605573e40f55759f3f01ac5ebc5ec4318ee79217a3a402326b3bf0e499dd2` |
| NCT | `pod/tensors/semantic-embedding/NCT/tensor_3d.npy` | `(89, 384, 8)` | `float32` | `04f7628d8cc101b9986f12f62fad2af0beeab9f96035af75b308c0e986f89771` |
| SPINE | `pod/tensors/semantic-embedding/SPINE/tensor_3d.npy` | `(62, 384, 8)` | `float32` | `d53e8a40bc75f5009db56e3430f2964db2244b53d8c38b82da6b6aca7a623a01` |

Each tensor directory also contains:

- `embeddings.npy`
- `metadata.npy`
- `index.json`
- `provenance.json`
- `skipped-records.jsonl`

For all four semantic tensor directories:

- `index.json` was parseable.
- `index.ids` count matched the semantic tensor row count.
- `index.id_to_row` count matched the semantic tensor row count.
- `skipped-records.jsonl` was empty.
- `provenance.json` included hashes for `tensor_3d.npy`, `embeddings.npy`, `metadata.npy`, `index.json`, and `skipped-records.jsonl`.

## Structural Mathematical Tensor Files

Verified structural tensor JSON files:

| Tensor | File | Shape | dtype | SHA256 |
| --- | --- | --- | --- | --- |
| PEER | `pod/tensors/structural-non-semantic/PEER.structural-vector-tensor.json` | `[106, 8, 4]` | `float32` | `3bd1318317f94ed2bc5525f208a5ca65a281b7f2479bb2f840a4ca808b4a97ab` |
| PCT | `pod/tensors/structural-non-semantic/PCT.structural-vector-tensor.json` | `[94, 8, 4]` | `float32` | `2071793aef411f23e765b0d28765b909ad1df8688a7bcf27a03da82cc5cf4320` |
| NCT | `pod/tensors/structural-non-semantic/NCT.structural-vector-tensor.json` | `[89, 8, 4]` | `float32` | `d3b3683890ca41416967cfdb5ca9f91f74ec82da50598901f929ade240e78475` |
| SPINE | `pod/tensors/structural-non-semantic/SPINE.structural-vector-tensor.json` | `[62, 8, 4]` | `float32` | `236d6829f77b4a8fe317945d953d01b5c2f9662be1f804caa8ccb5c11414c661` |

## Caveat

The current JSONL records have advanced beyond the tensor batch counts:

| Tensor | Current JSONL count | Semantic tensor rows | Structural tensor rows | Delta |
| --- | ---: | ---: | ---: | ---: |
| PEER | 127 | 106 | 106 | +21 |
| PCT | 130 | 94 | 94 | +36 |
| NCT | 106 | 89 | 89 | +17 |
| SPINE | 62 | 62 | 62 | 0 |

This matches the separately verified post-switch live append growth. Therefore the correct statement is:

Orion has mathematical tensor artifacts and JSONL context/record files, but the tensor artifacts are a generated batch over the earlier migrated set. The current live JSONL context files include later records that are not yet reflected in a refreshed/incremental tensor batch.
