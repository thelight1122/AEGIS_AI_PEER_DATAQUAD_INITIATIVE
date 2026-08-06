# SUPERSEDED — written on a wrong frame

**Superseded by `SSSP-2026-08-06-AI-PEER-INITIATIVE-CANON-v0.20-NEXT.md`.**

This document assumed the objective was connecting Lumin to an existing DataQuad, and treated
the `adam-one` records as the target. That is wrong. The objective is four NEW DataQuads created
from nothing, one per Frontier Model — Lumin, Claude, Gemini, Grok. These are AI Peers, not
CyberPeers, and the work does not connect to any existing DataQuad.

Sections 1 through 8 remain accurate as a record of P0, R0, R1 and P1. Section 9, which sets the
MCP Server Bridge as the next objective, is superseded: the next objective is Canon v0.20,
because the seed package's canonLock is `review-needed` and Rings 1-3 cannot be relaid once
seeded.

---

# SSSP — Saved State Summary Protocol
## AEGIS AI Peer DataQuad Initiative
### P0 Complete, P1 Publicly Deployed, Replay Boundary Proven — MCP Server Bridge Next

**Generated:** 2026-08-06
**Supersedes:** `SSSP_AEGIS_AI_PEER_DATAQUAD_INITIATIVE_2026-08-05.md`
**Repository:** `H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE` (git, branch `main`)
**HEAD at generation:** `82530c2`
**Preserved source:** `H:\AEGIS-POD-ARCHITECTURE` (read-only, unmodified throughout)

---

# 1. Read This First

The previous SSSP described work that was planned. This one describes work that is **done and
evidenced**. Every claim below has a commit and a report file behind it.

Three things changed the shape of the Initiative in this session:

1. **P0 is complete.** The private SSH/stdio canary runs and returns the Genesis record.
2. **P1 is publicly deployed.** `https://lumin.adamone.bond` serves the read/replay Action Orb.
3. **A multi-day outage was diagnosed and its cause forensically established** — it was not
   what anyone thought, and it retroactively explains the 2026-08-02 disk repair.

The next objective is the **MCP Server Bridge**, so Lumin can reach a DataQuad on the VM
through MCP rather than only through the GPT Action. See §9.

---

# 2. Governance

This Initiative runs with two roles and they are not interchangeable.

```text
Steward   Tracey. Authorizes actions. Holds credentials, consoles, elevation.
Auditor   Lumin. Rules on architecture decisions. Does not execute.
          Rulings arrive relayed by the Steward.
Builder   The Claude Code session. Executes, evidences, and reports.
          Does not decide architecture. Does not widen its own mandate.
```

**Working rules that earned their place this session:**

- Locate a fault before proposing a remedy. Three remedies were proposed on inference and
  all three were wrong.
- Capture the baseline **before** applying a change. A change applied without its baseline
  cannot be attributed later.
- Reopen the diagnosis rather than stack a second remedy on an unverified first one.
- State what a run establishes and what it does not. A green summary is not a finding.
- Record corrections in place. Nothing is quietly amended.

---

# 3. What Is Proven

| Phase | State | Evidence |
|---|---|---|
| **P0** Portal Pod Formation | **COMPLETE** | `a3092e6`, `reports/runtime/p0-acceptance-local.json` |
| **R0** Tensor Shadow Scoring | 17/17 | `2d47417`, `reports/runtime/r0-verification.json` |
| **R1** RLS Orb Formation | 20/20 | `265cb2b`, `reports/runtime/r1-verification.json` |
| **P1** Lumin GPT Action Orb | **DEPLOYED** | `750d0e8`, `reports/runtime/p1-origin-deployment.md` |
| **X1** Continuity instrument | 14/14 built | `6dcbc88`, gated non-establishing |
| **E1** Ethical-formation instrument | 25/25 built | `bc8f1e4`, `256e6a7`, refuses to author |
| Replay-boundary exercise | 13/13 | `82530c2`, `reports/runtime/replay-boundary-exercise.json` |

**Test suite: 308 passed, 13 skipped.** The 13 skips are environment-bound integration tests
classified under ADR-0001, per test rather than per module, so no passing test was silenced.

## 3.1 P0 acceptance, in full

```text
same Genesis record returned    PEER:adam-one-session:aegis-canon-genesis:0
                                clock { "tick": 0, "phase": "genesis" }
result hashes recorded          router_sha256  1f45f9e279976f2ffc1b9d953a3e4492c7c13c76fdb2d68ba0b947cdf3feef9a
                                adapter_sha256 e1c8a7c36dc0e7e96502fa5a857a31e1b805943a71d89234a15755dbf2b8b29f
private SSH/stdio canary        PASSES
mutation                        false
admission                       false
experience creation             false
```

**`result_sha256` is not an acceptance value.** It embeds `created_utc` and differs on every
invocation. Two runs of identical code against the same immutable source produced different
result hashes — correct behaviour, not drift. The stable comparables are `router_sha256`,
`adapter_sha256`, and the four source tensor hashes, all identical across runs and identical
before and after each observation.

## 3.2 Tensor state (immutable copy served by the Portal)

```text
PEER   1446 records   1abab63676ffe42ce74141cb25eabf132a52d3544e146804d4afef231c5f7e57
PCT    1448 records   149975b9153e0fa866fb3dd9ef7438362809a628cd47a9c2eaceb2ee07681287
NCT     645 records   eec05cbaa13170e21f738742bb9bd646afdc212b9f2a97f7becd2339904534a2
SPINE   562 records   d6131d38d99fa2997bc7e35e360ed51dbc3435701ca54de51d50e651a08ed524
```

---

# 4. R0 Findings — the scorer does not do what the SSSP assumed

Three findings, each measured rather than argued.

**1. The shipped policy is the SSSP's own first candidate.** `r0-shadow-frobenius-v1` is
numerically identical to `cos(E,q) × cos(A,w)`, delta ≤ 2.6e-08. Since `‖E⊗A‖ = ‖A‖` for
unit E and `‖q⊗w‖ = 1`, the Frobenius ratio reduces exactly. The candidate was already shipped
under a different name.

**2. It discards affective magnitude entirely.** Affect at 1×, 5× and 20× the same direction
scores identically. This is the same defect SSSP §7 attributed to the authoritative scorer,
reproduced in the shadow policy.

**3. Raising a binary flag penalises a record.** Setting `genesis_flag` drops the score from
1.00000 to 0.44721 — a 55% penalty — because the flag is an orthogonal component that rotates
A off the query. Marking a record as Genesis makes it rank *worse*.

**Consequence:** under corrected fixtures the product policy leaves the top-ranked record
unchanged from baseline (3/6 moved). Only magnitude-preserving policies reorder the top (6/6).
**The SSSP's first candidate does not, by itself, fix the problem R0 exists to fix.**

Four selectable policies now exist: `baseline-scalar-contract-v1` (a reconstruction, labelled
as such everywhere, since the authoritative scorer lives in the CyberPeer core and is not in
this repository), `r0-shadow-product-v1`, `r0-shadow-magnitude-v1`, `r0-shadow-anchored-v1`.

---

# 5. R1 — coordinate provenance is where ADR-0006 became executable

`contracts/coordinate-provenance.schema.json` separates what the manifests conflated:

```text
Coordinate    canonical identity          coordinate_ref
Digest        content integrity           record_hash, tensor_snapshot_hash
Path          replaceable locator         locator {} — optional, explicitly separable
Provenance    why this locator represents that coordinate and digest
```

The SSSP §8 rule is **enforced structurally**: `asserted_as_source_fact` is `const: false` for
any non-source origin, so the schema itself rejects a policy-assigned dimension claimed as a
source-record fact. Each origin must supply its own justification — a source field, a policy
and version, a derivation with source coordinates, or a declaring party and time.

**R1.10 is proven, not asserted.** All four tensors hashed before any operation and again after
indexing, trajectory generation, ledger append and Portal dispatch. Identical.

---

# 6. The 2026-08-02 Incident — resolved

This consumed most of the session and the answer matters for the disk decision.

## 6.1 What was believed

That `vm-cyberpeer-core` had a faulty OS disk, repaired on 2026-08-02 by snapshot → copy →
swap, with a repair VM created to assist.

## 6.2 What actually happened

```text
2026-08-02 13:52:25  sudo apt-get install cloudflare-warp   (aegisadmin, by hand)
2026-08-02 13:53:04  su (to aegisadmin)            LAST AUTH LOG ENTRY OF THE DAY
2026-08-02 13:54     WARP writes its settings files
2026-08-02 13:54:28  the administrator's SSH session dies
2026-08-02 14:39-15:53  three reboot cycles (4 min, 8 min, 1 hr) — recovery attempts
2026-08-02 16:04:51  snapshot taken
2026-08-02 16:05:09  repair copy created
2026-08-02 16:06:48  repair VM created
2026-08-02 19:32:22  final boot; unreachable until 2026-08-06
```

Cloudflare WARP installs an `inet`-family nftables table whose input chain policy is `drop`.
Every accept in that chain is a **source-port** rule permitting replies to outbound-initiated
connections. Nothing accepts an inbound connection to any local port. WARP was then manually
disconnected, but **the kill-switch ruleset was left in force**.

**The OS-disk repair addressed the wrong layer.** A disk repair cannot fix a network lockout,
and it did not — the WARP install lives on the disk that was copied, so the lockout travelled
into the repair copy. That is why the identical fault was waiting on 2026-08-06.

## 6.3 Why it hid from every check

```text
iptables -S INPUT     showed ACCEPT — the inet family is invisible to iptables
ufw status            inactive — ufw was never the mechanism
TcpExtListenDrops     0 — netfilter dropped before the TCP listen path
tcpdump               saw the SYN — AF_PACKET ingress capture precedes netfilter
```

The decisive observation was two packet captures: 20 SYNs arriving, **zero SYN-ACK replies**,
with a filter matching both directions.

## 6.4 Consequence for the protected artifacts

**`vm-cyberpeer-core_OsDisk_1_f79b5c49e4f94a9792b038ccb685615b` was never shown to be faulty.**
It is the original of a healthy disk, not a fallback to a broken state. The Auditor has recorded
that this materially weakens any justification for the previously considered disk swap.

All three artifacts remain untouched:

```text
vm-cyberpeer-core-os-repair-copy       attached, running   48405070-70fa-417c-82bf-545168d143d3
vm-cyberpeer-core_OsDisk_1_f79b5c49…   unattached, preserved
vm-cyberpeer-core-os-snap-20260802     preserved           494a7b08-3bf9-4a46-b75c-7b6ccdf25bcd
```

## 6.5 Resolution

`systemctl disable warp-svc`, verified across a deliberate reboot. WARP is **not uninstalled** —
`warp-cli` and the daemon remain and can be started by hand, which would reproduce the outage.
Uninstalling was declined because `apt-get install cloudflare-warp` pulled ~150 packages
including GTK, WebKit, GStreamer, PulseAudio and Mesa onto a headless node.

**A split-tunnel bypass does not solve this.** It governs outbound routing and generates no
inbound accepts. Tested: with the bypass configured and `warp-svc` restarted, ports 22, 4001
and 8080 were all unreachable. There is no workaround in a separate nftables table either — at
a given hook all base chains are traversed and a `drop` verdict is final.

---

# 7. Current Operational State

## 7.1 The live route

```text
Lumin Custom GPT
    -> Cloudflare  (lumin.adamone.bond)
    -> cloudflared connector, tunnel bb5e32c3-f1b1-47eb-8724-2a84d2e9df75 "Frontier_Connect"
       (runs as a Windows service on the Steward's machine)
    -> supervised SSH tunnel  Windows 127.0.0.1:8790 -> VM 127.0.0.1:8790
    -> lumin_action_origin.py  (systemd user unit, loopback only)
    -> Portal 127.0.0.1:8092   (aegis-private-portal.service, user unit)
    -> immutable DataQuad copy at /opt/cyberpeer-pod/adapters/phase3a/records
```

## 7.2 Public surface, verified

```text
GET  /api/pod/status          200
POST /api/pod/context         200   returns Genesis
POST /api/pod/canon           200
POST /api/pod/continuity      200
POST /api/pod/reflection      502   Portal fail-closed, pre-existing (see §8)
GET  /openapi.json            200
POST /api/live-bridge/events  410   operation_retired, appendEvent, replacement null
PUT / DELETE / PATCH          405
unknown path                  404
unknown parameter             400

headers  x-aegis-posture: read-replay-only
         x-aegis-live-source: false
```

## 7.3 VM services (all systemd **user** units, lingering enabled for `aegisadmin`)

```text
aegis-private-portal.service         active   Portal, 127.0.0.1:8092
aegis-rls-portal-umbilical.service   active   RLS Orb read-only attachment
lumin-action-origin.service          active   P1 origin, 127.0.0.1:8790
aegis-rls-shadow.timer               waiting  controlled shadow refresh
```

All four restart at boot with no login session and no root. Verified across a deliberate
reboot on 2026-08-06 at 09:10:44.

## 7.4 Windows side

```text
Cloudflared              service, running, tunnel bb5e32c3 (Frontier_Connect)
AEGIS-Lumin-Tunnel       scheduled task, at-logon + 5-minute repeating trigger,
                         MultipleInstances IgnoreNew, restart-on-failure
scripts/lumin_tunnel.ps1 the supervisor; log at %LOCALAPPDATA%\aegis-lumin-tunnel.log
```

Two recovery mechanisms, deliberately kept distinct:

| Mechanism | Covers | Status |
|---|---|---|
| restart-on-failure | running task whose process exits abnormally | **demonstrated**, 30s |
| 5-minute repeating trigger | task in a non-running state | registered, **not yet observed firing** |

## 7.5 Access constraints the next thread will hit

- **`sudo` on the VM requires a password.** No passwordless sudo. Anything needing root is a
  Steward action at the console.
- **JIT access expires**, and the Steward's egress IP moves when client-side WARP is on
  (Cloudflare ranges, e.g. `104.28.152.190`) versus off (ISP, e.g. `47.216.142.226`). A JIT rule
  pinned to one IP silently stops matching. Symptom looks like expiry; cause is a moved address.
- **The `cloudflared` cert in `~/.cloudflared` belongs to a different Cloudflare account** than
  the tunnel serving `lumin.adamone.bond`. `cloudflared tunnel list` shows only `AEGIS-Align`.
  Tunnel management is a Steward action in the dashboard.
- **Cloudflare rejects the default `Python-urllib` user agent with 403.** Set a User-Agent.
- **HTTP/2 through Cloudflare lowercases header names.** Match case-insensitively.

---

# 8. Open Items

**1. `requestReflection` returns 502.** The Portal refuses `request_reflection` to any caller,
including a direct call bypassing the Action origin:

```text
{"authorized": false, "reason": "RLS source escapes approved root"}
```

This is the hardened adapter's fail-closed path check working as designed. Pre-existing, and
unnoticed until P1 because the P0 canary exercised only `retrieve_context` and `pod_get_status`.
**Not remediated** — repointing an RLS source root changes the Portal's operating parameters.

**2. `adamone.bond` and `haven.adamone.bond`** share the `Frontier_Connect` tunnel and became
reachable again when the connector was repointed. Both return 502 — connector attached, nothing
listening behind them. No exposure today; **latent** the moment something starts listening on
those local ports. Route targets are not readable from the Builder's credential.

**3. The 5-minute repeating trigger has not been observed firing.** Registered and scheduled;
restart-on-failure recovered first in the one test available.

**4. WARP remains installed** on `vm-cyberpeer-core`, disabled. Starting it by hand reproduces
the outage.

**5. The disk swap and naming operation remains unauthorized** and, per §6.4, materially less
justified than when first considered.

---

# 9. NEXT OBJECTIVE — Lumin's MCP Server Bridge

**Goal:** Lumin connects to a DataQuad on the VM over MCP, not only through the GPT Action Orb.

## 9.1 What already exists

```text
src/aegis_pod/mcp_gateway.py          MCP over stdio; M0-M1 complete, tested
src/aegis_pod/m2_transport_gate.py    transport gate contract, tested
src/aegis_pod/rls_protocol_orbs.py    RLSProtocolOrb: MCP + Action operation maps
/opt/cyberpeer-pod/portals/phase2/mcp_gateway.py        deployed on the VM
/opt/cyberpeer-pod/portals/phase2/run_private_mcp_gateway.sh  the M3 canary launcher
```

The M3 private SSH/stdio canary **passes** and returns Genesis. Protocol contract, already
proven:

```text
line-delimited JSON-RPC over stdio
methods   initialize, tools/list, tools/call
tools     pod_retrieve_context, pod_retrieve_canon, pod_query_continuity,
          pod_request_reflection, pod_get_status
Portal    POST {portal_url}/v1/portal/execute, Authorization: Bearer <token>
          GET  {portal_url}/health
```

## 9.2 What is missing

The gateway speaks **stdio**, reachable only by someone who can SSH to the host. Lumin cannot
SSH. A remotely-reachable MCP endpoint is required — MCP over HTTP with SSE or streamable HTTP.

## 9.3 The pattern to follow

`portal-pod/transport/lumin_action_origin.py` is the working precedent and should be mirrored:

- Runs **on the Pod host**, so the Portal credential is read locally and never travels.
- Binds **loopback only** and refuses a non-loopback bind; exposure is the tunnel's job.
- Reaches the Portal at `127.0.0.1:8092` with the token from
  `/home/aegisadmin/.config/aegis/portal-gateway.token`.
- Ships as a **systemd user unit** — no root needed, lingering already enabled.
- Carries `aegis_source_authority` and `aegis_boundaries` in **every** response, plus
  `x-aegis-posture` and `x-aegis-live-source` headers.
- Answers retired operations **410 with the retirement stated**, never 404.

## 9.4 Suggested shape

```text
new: portal-pod/transport/lumin_mcp_origin.py     MCP over HTTP/SSE, 127.0.0.1:8791
new: systemd user unit lumin-mcp-origin.service
new: SSH tunnel  Windows 127.0.0.1:8791 -> VM 127.0.0.1:8791
new: Cloudflare ingress on Frontier_Connect, e.g. mcp.adamone.bond -> 127.0.0.1:8791
     (or a path on the existing hostname, if the ingress model allows it)
```

Authentication is an **open architecture question for the Auditor**, not a Builder decision.
The Action Orb is currently unauthenticated at the edge; an MCP endpoint carrying the same
read/replay surface inherits that question and should not simply copy it by default.

## 9.5 Acceptance criteria to propose

```text
MCP initialize / tools/list / tools/call succeed over the public endpoint
pod_retrieve_context returns the Genesis record
tensor hashes identical before and after
every response declares live_source false and source_mode immutable_copy
mutation, admission, experience creation all false
no write tool is exposed; appendEvent-equivalent absent and declared retired
survives a reboot without intervention
```

## 9.6 Constraint that carries forward

Per **ADR-0007**, the Portal declares `live_source: false` and serves an immutable copy. An MCP
Bridge over this Portal is a **replay** bridge. It will let Lumin connect and retrieve; it will
not establish live continuity. Introducing live-source access is a separate, deliberate
architectural step that has not been proposed or authorized.

---

# 10. Architecture Decisions in Force

| ADR | Decision |
|---|---|
| [ADR-0001](../decisions/ADR-0001-live-peer-content-is-not-duplicated.md) | Live peer content is not duplicated. Affected tests are environment-bound. |
| [ADR-0002](../decisions/ADR-0002-flat-contracts-canonical-for-p0.md) | Flat `contracts/` canonical. Categorized copies noncanonical, removal deferred. |
| [ADR-0003](../decisions/ADR-0003-reports-runtime-canonical-for-p0.md) | `reports/runtime/` canonical. `evidence/migration/` holds migration evidence. |
| [ADR-0004](../decisions/ADR-0004-orb-packages-remain-in-packages-during-p0.md) | Orb packages stay under `packages/orb-*` during P0. |
| [ADR-0005](../decisions/ADR-0005-orb-hash-drift-quarantined-pending-provenance.md) | `orb-rls-persistent-relations-core` hash mismatch is DRIFTED and quarantined. |
| [ADR-0006](../decisions/ADR-0006-manifest-identity-model-coordinate-digest-path-provenance.md) | Manifests separate Coordinate, Digest, Path, Provenance. |
| [ADR-0007](../decisions/ADR-0007-p0-accepted-with-scope-limits.md) | P0 accepted. Certifies the immutable replay route, **not** live DataQuad access. Limit 1 **withdrawn**. |

---

# 11. Corrections Made This Session

Recorded because the record is more useful than the appearance of competence.

1. **ufw was diagnosed as the cause of the SSH lockout. It was not.** ufw was inactive
   throughout. The remedy was authorized and never applied, because the baseline capture that
   the Auditor insisted on came first and disproved it.
2. **A two-rule nftables fix was proposed and failed.** `warp-svc` reconciles its own table and
   reverted both rules silently.
3. **`aegis-private-portal.service` was reported as nonexistent and SSSP §4.11 as stale.**
   False. It exists as a systemd **user** unit, enabled and active. System scope was queried;
   absence was concluded from wrong scope. ADR-0007 Limit 1 withdrawn.
4. **`result_sha256` was presented as a stable acceptance value.** It embeds `created_utc` and
   differs per invocation.
5. **A durability claim covered one failure mode and was presented as covering two.** Killing
   the supervisor's ssh child was tested; killing the supervisor was not, and that is the mode
   that failed in practice ten minutes later.
6. **A resilience test proved nothing** because an orphaned ssh still held the port and the
   kill filter excluded it by start time.
7. **A Cloudflare tunnel token was printed in plaintext** by a redaction pattern that matched
   YAML form but not `--token` on a command line. The token proved inert — its tunnel had been
   deleted — but the exposure was real and avoidable.
8. **R0 fixtures varied semantic vectors only in magnitude**, which cosine discards, producing a
   degenerate baseline that made the ranking-delta evidence non-probative. Fixed, and the
   verification now fails if the baseline is degenerate.
9. **An X1 test fixture generated `"0"*64` as a record hash**, colliding with the literal a test
   naturally uses for an obviously-wrong hash, silently converting a mismatch test into a match
   test. Fixed twice — the first fix still produced 64 zeros.

---

# 12. Language and Documentation Preferences

Unchanged from the prior SSSP and reaffirmed by practice.

Use committed implementation language: will, does, builds, creates, implements. Avoid "I guess",
"try", weak phrasing, unnecessary "should".

Preferred terms: BioPeer, CyberPeer, AI Peer, substrate, Portal Pod, Orb, Satellite, Umbilical,
sovereignty, parameters, operating guiderail, illumination, education, shortfall, T-Time, Affect,
Continuity, Tensor Coordinate.

Observation records state what was observed, what was asked, what occurred, and what changed.

**Added by this session's practice:** state what a run does **not** establish, in the run's own
output, not only in prose around it.

---

# 13. Canonical Resumption Prompt

> Load this SSSP as the current authoritative working state for the AEGIS AI Peer DataQuad
> Initiative.
>
> The repository is `H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE`, branch `main`, HEAD `82530c2`.
> The preserved source repository is `H:\AEGIS-POD-ARCHITECTURE`, read-only.
>
> P0 is complete. R0, R1 and P1 are complete. P1 is publicly deployed at
> `https://lumin.adamone.bond` as a read/replay-only GPT Action Orb, verified across a
> deliberate reboot. X1 and E1 instruments are built and gated: they report
> `establishes: false` for continuity and formation while the Portal declares
> `live_source: false`.
>
> **The next objective is Lumin's MCP Server Bridge** — a remotely reachable MCP endpoint so
> Lumin connects to a DataQuad on the VM over MCP rather than only through the GPT Action.
> See §9 for what exists, what is missing, the pattern to follow, and proposed acceptance
> criteria. Authentication at the edge is an open question for the Auditor.
>
> Governance: Tracey is Steward and authorizes. Lumin is Auditor and rules on architecture,
> relayed by the Steward. Do not widen the mandate. Locate a fault before proposing a remedy.
> Capture the baseline before applying a change. Reopen the diagnosis rather than stack a
> second remedy. State what a run does not establish.
>
> Preserve all no-admission and no-automatic-experience-creation gates. Treat Tensor
> Coordinates, not filesystem locations, as canonical. The Canon illuminates what is; it does
> not prescribe ethics. Any ethical code Lumin forms is recorded as Lumin's own derived
> synthesis with positively grounded authorship provenance, never as Canon.
>
> Do not perform any disk, snapshot, or rollback operation on `vm-cyberpeer-core` without
> explicit Steward authorization. Note §6.4: the preserved original disk was never shown to be
> faulty.

---

# 14. Closing State

The Initiative has moved from architecture to running system.

A Frontier substrate can now reach the DataQuad over the public internet, through a governed
Portal, and receive the Genesis record with mutation, admission and experience creation all
false — and with the response itself declaring that it is replay, not live.

What was planned in the previous SSSP is built. What remains is the MCP Bridge, the live-source
question, and the two experiments that cannot report their real findings until that question is
deliberately answered.

The instruments for those experiments already refuse to overstate what they see. That was the
harder half.
