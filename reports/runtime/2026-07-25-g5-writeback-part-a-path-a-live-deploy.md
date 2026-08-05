# G5 Writeback Part A - Path A Live Deploy

Date: 2026-07-25
Standard hash: 7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622

## Scope

Path A deployed the already-audited code-only G5 writeback fix to live Gabe.

This did not run `/turn`, did not prune existing records, did not rewrite existing Gabe PCT lines, and did not execute Part B.

## Live Target

- VM: `AEGISGabePeer`
- Resource group: `AEGISCYBERPEER_GROUP`
- Peer: `CP-1003-GABE`
- Container: `gabe-aegis-cyberpeer-core`
- Route: `127.0.0.1:8021 -> 8790`
- Image deployed: `aegis-cyberpeer-core_aegis-core:g5-part-a-20260725T192355Z`
- Previous container preserved stopped as: `gabe-pre-g5-part-a-switch-20260725T193101Z`

SSH to `GabeCyberPeer` timed out at TCP 22, so deploy used Azure VM Run Command.

## Deployed Hashes

Imported module hashes inside the running container:

- `core.cognition.thinking`
  - path: `/app/core/cognition/thinking.py`
  - SHA256: `90F915DDC893C76EDC3213284D6D4085E4EFCB3777E5D1CABFDBB360941F2E84`
- `orb_rls_persistent_relations_core.engine`
  - path: `/usr/local/lib/python3.11/site-packages/orb_rls_persistent_relations_core/engine.py`
  - SHA256: `A6CEDDE52833989B747024EC6D9E819DD4CCB64ACD222C87D547D5F1FE50B1E6`

The vendored engine hash differs from the extracted-Orb audit hash because the Core vendored file already contained the earlier compact `ledger_dict` fix. Path A merged the new PCT `retrieved_record_ids=None` trim into that existing vendored state.

## Verification

Live health after switch:

- `ok`: `true`
- `peer_id`: `CP-1003-GABE`
- `model`: `qwen3:14b`
- `current_tick`: `84797`
- `PCT` count: `33123`

PCT count remained `33123`, matching the pre-deploy health count. This supports the boundary claim that no existing PCT records were rewritten or trimmed during Path A.

## Notes

The first deploy script built the image successfully but used a short readiness window. The new container was rolled back before it finished answering health. A second switch reused the already-built image and waited through a readiness loop; it passed health and module-hash verification.

Docker Compose was not used. Prior evidence on this host showed `docker-compose` v1.29.2 is unsafe against the current Docker version. The switch used explicit `docker run` with the same route and data bind:

- `--env-file .env`
- `-p 127.0.0.1:8021:8790`
- `-v /home/azureuser/AEGIS-CYBERPEER-CORE/data:/app/data`
- `--add-host host.docker.internal:host-gateway`

## Boundary

Completed:

- future live-turn PCT writeback trim deployed
- future RLS Orb PCT writeback trim deployed
- previous runtime container preserved for rollback
- `/health` verified

Not completed:

- no Part B reverse trim
- no existing record migration
- no `/turn` writeback test
- no RLS selection-scope fix
- no relation-store volume fix
