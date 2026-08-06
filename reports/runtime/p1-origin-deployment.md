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

## Remaining, and not performed

Both require access this session does not have.

1. **Repoint the connector.** It currently runs a token for tunnel
   `548d9009-1d14-437e-b7de-c05c0b39d9e2`, which has been deleted — the cause of the
   standing Cloudflare 1033. It needs the token for `bb5e32c3…`, installed from an
   elevated terminal.

2. **Add the ingress rule** on `bb5e32c3…` mapping `lumin.adamone.bond` to
   `http://127.0.0.1:8790`, and remove any rule still pointing at the old bridge.

## Durability caveats

- The origin runs under `nohup`, not systemd. It does not survive a VM reboot.
- The SSH tunnel is a foreground process on Windows. It does not survive a reboot or a
  dropped session.
- `warp-svc` is disabled, so the VM stays reachable, but see the WARP record.

Both would want proper units before this is treated as a standing service rather than a
verified route.
