# P1 — Lumin GPT Action Orb origin, built and verified

**Recorded:** 2026-08-06T07:20Z
**Status:** origin service live and verified end to end. Public exposure NOT yet configured.

---

## Route

```text
Lumin Custom GPT
    -> Cloudflare (lumin.adamone.bond)
    -> cloudflared connector, tunnel bb5e32c3-f1b1-47eb-8724-2a84d2e9df75   [NOT YET ATTACHED]
    -> SSH tunnel  Windows 127.0.0.1:8790 -> vm-cyberpeer-core 127.0.0.1:8790
    -> lumin_action_origin.py (loopback only, read/replay only)
    -> Portal 127.0.0.1:8092
    -> immutable DataQuad copy
```

The origin runs on the Pod host so the Portal credential is read locally and never
travels, matching `run_private_mcp_gateway.sh`. It binds loopback only; exposure is the
tunnel's job, and the service refuses any non-loopback bind.

## Deployed

```text
/opt/cyberpeer-pod/portals/phase2/lumin_action_origin.py
/opt/cyberpeer-pod/portals/phase2/p1-lumin-gpt-action.openapi.json
```

Running as `aegisadmin`, no sudo, no systemd unit. Source of record:
`portal-pod/transport/lumin_action_origin.py`.

## Verified on the VM

| Check | Result |
|---|---|
| `GET /api/pod/status` | 200, pod_id adam-one, portal_mode read-replay |
| `POST /api/pod/context` | 200, Genesis returned |
| `POST /api/pod/canon` | 200 |
| `POST /api/pod/continuity` | 200 |
| `POST /api/pod/reflection` | **502 — Portal refuses, see below** |
| `GET /openapi.json` | 200 |
| `POST /api/live-bridge/events` | **410 Gone**, operationId appendEvent, replacement null |
| unknown path | 404 |
| PUT / DELETE / PATCH | 405 |
| unknown parameter (`admit: true`) | 400 |
| `limit: 9999` | 400 |

Genesis through the full chain from Windows, through the SSH tunnel:

```text
HTTP 200   record_id PEER:adam-one-session:aegis-canon-genesis:0
           clock { "tick": 0, "phase": "genesis" }
           live_source false        mutation_performed false
           X-AEGIS-Posture: read-replay-only
           X-AEGIS-Live-Source: false
```

## requestReflection is unavailable, and it is not a P1 defect

```text
{"authorized": false, "reason": "RLS source escapes approved root"}
```

The Portal returns this to any caller, including a direct call bypassing the Action origin
entirely. It is the hardened adapter's fail-closed path check firing correctly. The
condition is pre-existing and was not previously observed because the P0 canary exercised
only `retrieve_context` and `pod_get_status`.

Not remediated. Repointing an RLS source root changes the Portal's operating parameters and
the guard fired as designed. Recorded as an open item.

## ADR-0007 compliance

Every response carries `aegis_source_authority`:

```json
{
  "live_source": false,
  "source_mode": "immutable_copy",
  "establishes_live_continuity": false
}
```

plus `aegis_boundaries` with mutation, admission, experience_created, dataquad_writeback,
live_rls_invoked, shell and filesystem all false, and the headers `X-AEGIS-Posture:
read-replay-only` and `X-AEGIS-Live-Source: false`. A consumer cannot represent this
connection as live DataQuad access without contradicting the payload it received.

## Public deployment — COMPLETE, verified 2026-08-06T07:32Z

The connector was repointed by the Steward from an elevated Command Prompt, and the
`lumin.adamone.bond` route on tunnel `bb5e32c3-f1b1-47eb-8724-2a84d2e9df75`
(**Frontier_Connect**) was set to `127.0.0.1:8790`.

The prior Cloudflare 1033 is explained and resolved: the connector had been running a token
for tunnel `548d9009-1d14-437e-b7de-c05c0b39d9e2`, which had been deleted. No DNS change was
needed — `Frontier_Connect` already carried the route.

### Verified from the public internet

```text
https://lumin.adamone.bond

GET  /api/pod/status          200   pod_id adam-one, portal_mode read-replay
POST /api/pod/context         200   PEER:adam-one-session:aegis-canon-genesis:0
                                    clock tick 0, phase genesis
                                    mutation_performed false, experience_created false
POST /api/pod/canon           200
POST /api/pod/continuity      200
POST /api/pod/reflection      502   Portal fail-closed, pre-existing (see above)
GET  /openapi.json            200

POST /api/live-bridge/events  410   operation_retired, appendEvent, replacement null
PUT / DELETE / PATCH          405
unknown path                  404
{"admit": true}               400

headers: X-AEGIS-Posture: read-replay-only
         X-AEGIS-Live-Source: false
body:    aegis_source_authority.live_source = false
```

The write endpoint the SSSP identified as incompatible with the current posture is publicly
and legibly retired: 410 with the operationId, the retiring phase, and an explicit null
replacement, rather than a 404 that would leave a caller unable to distinguish removal from
absence.

### The route the SSSP described is now real

```text
Lumin Custom GPT -> Cloudflare -> Frontier_Connect connector
    -> SSH tunnel (supervised) -> origin (systemd user unit) -> Portal -> DataQuad copy
```

## Durability — resolved, and demonstrated

**VM:** systemd **user** unit `~/.config/systemd/user/lumin-action-origin.service`, enabled
and active. Lingering was already enabled for `aegisadmin`, so user units start at boot with
no login session and no root. Hardened with `NoNewPrivileges`, `ProtectSystem=strict`,
`ProtectHome=read-only`, `PrivateTmp`, `RestrictAddressFamilies`, `MemoryMax=256M`,
`Restart=always`.

**Windows:** `scripts/lumin_tunnel.ps1` supervises the SSH tunnel, registered as the user
scheduled task `AEGIS-Lumin-Tunnel` at logon with restart-on-failure.

Recovery demonstrated rather than assumed: killing the supervisor's ssh child (pid 36576)
dropped the port; the supervisor reconnected at t+15s as pid 57364; end-to-end returned
HTTP 200. The log shows `connecting` → `tunnel exited (code -1)` → `connecting`.

A first attempt at that test proved nothing and is recorded so the failure is not mistaken
for a pass: port 8790 was still held by an orphaned ssh from an earlier background task, and
the kill filtered to processes started in the last three minutes, which excluded it. The
supervisor had never connected — it was logging "port already listening; waiting" — and the
HTTP 200 read as success came from the orphan.

## Standing scope limit

Per ADR-0007, the Portal declares `live_source: false` and serves an immutable copy. **This
public route is not live DataQuad access and will not be represented as such.** X1 and E1 may
now exercise transport and instrumentation against a real public route; neither can establish
continuity, experience formation, or ethical formation until `live_source: true` is evidenced
and independently verified.

## Observation, not acted on

`Frontier_Connect` also routes `adamone.bond` and `haven.adamone.bond`. Both shared the dead
connector and are therefore reachable again as a side effect of this repointing. Neither was
touched or tested, and what they serve is unknown to this work.
