# Four-Peer Bounded UNSEATED VM Deployment — Completion Evidence

- Captured UTC: `2026-08-14T22:11Z` (run window `2026-08-14T22:01Z` – `2026-08-14T22:11Z`)
- Repository HEAD at execution: `bcab94ff585e95617cf888bcee0f389e26d83cfc` (working tree clean), lineage `c5e9cee` → `bcab94f`
- Source commit deployed: `bcab94ff585e95617cf888bcee0f389e26d83cfc`
- Target: `vm-cyberpeer-core` (RG `RG-AEGIS-ADAM-ONE`, sub `183863c0-4aaf-4329-ba95-0db3760357f2`, region `eastus2`, vmId `700fe4fc-3608-43fd-b02d-185a9ac0d6cc`), reached via existing SSH identity `AEGISIPFSNode` (`20.122.189.26`, user `aegisadmin`)
- Scope: install four isolated loopback-only UNSEATED services (ports 8811–8814); health/boundary checks; rollback exercise + restore; temporary-sudo teardown. **Reversible; no seating, no live activity, no Azure disk mutation.**

## Boundary attestation (nothing below was done)

No reboot; no seating; no Rings 1–3 ingest; no Canon/manifest/seed mutation; no
Temporal/Processor/custodian/RLS live activity; no credentials/Keys/Tumblers
provisioned; **zero Azure control-plane commands issued** (no disk/snapshot
mutation). All identity data was gathered read-only via SSH and instance IMDS.

## 1. Independent preflight verification

| Check | Command | Result |
|---|---|---|
| Target identity | `hostname` | `vm-cyberpeer-core` (UTC `2026-08-14T22:03:23Z`) |
| Operator | `whoami` | `aegisadmin` |
| Passwordless sudo | `sudo -n true` | `SUDO_N_TRUE=OK` |
| Sudoers parse | `sudo -n visudo -cf /etc/sudoers.d/zz-aegis-deploy-nopasswd` | `parsed OK` |
| Repo HEAD/clean | `git rev-parse HEAD` / `git status` | `bcab94f`, clean |
| Ports 8811–8814 | `ss -ltnH '( sport = :8811 or … :8814 )'` | empty → all free |
| Prior install | `ls /opt|/var/lib|/etc/aegis-ai-peers` | ABSENT (clean slate) |
| Existing units | `systemctl list-units 'aegis-ai-peer@*'` | none |
| sudoers files | `ls /etc/sudoers.d` | `zz-aegis-deploy-nopasswd` present; `99-aegis-deploy-nopasswd` ABSENT |
| Env secrets | `grep -riE 'key|token|secret|password|credential' deploy/env` | only the template's "forbidden" comment — no secret values |

Transferred bundle (`deploy/` at `bcab94f`, LF, `__pycache__` excluded) verified
byte-identical local↔remote across all 14 files (SHA-256 recorded in the release
`deployment-manifest.json`, reproduced in §5).

## 2. State tree before / after

**Before:** `/opt/aegis-ai-peers`, `/var/lib/aegis-ai-peers`, `/etc/aegis-ai-peers`
all absent (no prior install).

**After (final, release R2):**

```
/etc/aegis-ai-peers/{lumin,claude,gemini,grok}.env   root:aegis-ai-peer-<peer> 0640
/opt/aegis-ai-peers/current -> releases/20260814-r2-220739Z
/opt/aegis-ai-peers/releases/20260814-r1-220610Z/{bin/aegis-ai-peer-unseated,deployment-manifest.json}
/opt/aegis-ai-peers/releases/20260814-r2-220739Z/{bin/aegis-ai-peer-unseated,deployment-manifest.json}
/opt/aegis-ai-peers/rollback-target  -> releases/20260814-r1-220610Z
/var/lib/aegis-ai-peers/{lumin,claude,gemini,grok}/MODE   0600, content "UNSEATED\n" (9 bytes)
```

Per-peer state root contains **only** `MODE`. No tensor ledger, no foundation, no
seed, no credential material was written by any peer.

## 3. Release identifiers, unit/listener/health states

| Release | Role | RELEASE_ID | manifest SHA-256 |
|---|---|---|---|
| R1 | initial install / rollback target | `20260814-r1-220610Z` | `7a10cf78cfa148cd76731486bb46359112ec1444e29044edd6419fc32cecde59` |
| R2 | intended current (final) | `20260814-r2-220739Z` | `cd2a47fa653335078d5c6bc19f3c615feda5b948f54a0240d187749e185000da` |

Both manifests carry `source_commit=bcab94f…`, `mode=UNSEATED`,
`promotion=DISABLED`, `live_credentials=FORBIDDEN`, `live_source=false`,
`continuity_claimed=false`, `self_claimed=false`.

- **Units:** `aegis-ai-peer@{lumin,claude,gemini,grok}` — all `active`, all `enabled`.
- **Listeners:** `127.0.0.1:8811` (lumin), `:8812` (claude), `:8813` (gemini),
  `:8814` (grok). No non-loopback bind on any of the four → `LOOPBACK_ONLY_CONFIRMED`.
- **Health (shipped `health.sh`):** all four `healthy UNSEATED guard`; each `/health`
  returns `mode=UNSEATED, ready=false, live_source=false, writes_enabled=false,
  promotion=DISABLED, claim=record_preservation_only`.

## 4. Rollback exercise and restore (proof)

| Phase | Action | current after | Health |
|---|---|---|---|
| Install R1 | `install.sh` | `…/20260814-r1-220610Z` | PASS |
| Auto-rollback (observed) | `upgrade.sh` → R2 (`20260814-r2-220739Z`); its embedded `health.sh` raced the double service restart (curl exit 7) → **upgrade ERR trap auto-invoked `rollback.sh`** → returned to R1 | `…/20260814-r1-220610Z` | PASS (settled) |
| Establish intended current | atomic symlink swap → R2 + restart | `…/20260814-r2-220739Z` | PASS |
| **Deliberate rollback** | shipped `rollback.sh` (target = R1, verified UNSEATED) — symlink+restart succeeded; embedded probe raced restart (exit 7); settled `health.sh` PASS | `…/20260814-r1-220610Z` | PASS (settled) |
| **Restore intended current** | atomic symlink swap → R2 + restart | `…/20260814-r2-220739Z` | PASS |

Rollback correctness: every rollback landed on its intended verified-UNSEATED
target and was confirmed healthy on all four ports after settle. Rollback changed
only the `current` release symlink and restarted services; it altered no peer
state and no VM disk. `rollback-target` finishes at R1 (R2's prior release).

**Known timing characteristic (not a boundary failure):** `upgrade.sh` and
`rollback.sh` run the embedded `health.sh` immediately after `systemctl restart`,
with no settle; the loopback server occasionally has not finished binding, so the
probe returns curl exit 7. In `upgrade.sh` this deterministically triggers the
designed auto-rollback. Independent settled `health.sh` re-runs passed in every
case. No listener ever bound off-loopback and no peer ever left UNSEATED.

## 5. No-write / no-credential proof

- `POST` to every `/health` → `405` ("UNSEATED instances have no write endpoint")
  on 8811–8814; the runtime exposes only `GET /health` and `GET /status`.
- State roots contain only `MODE` (UNSEATED) — no tensor/foundation writes.
- Credential scan of `/opt/aegis-ai-peers`, `/var/lib/aegis-ai-peers`,
  `/etc/aegis-ai-peers` for `key|tumbler|secret|token|password|credential`
  matched **only** boundary declarations: `AEGIS_LIVE_CREDENTIALS=FORBIDDEN`,
  `"live_credentials": "FORBIDDEN"`, and the runtime's own guard string. No secret
  assignment exists (`NO_SECRET_ASSIGNMENTS`). No Keys, Tumblers, tokens, or
  live credentials present.

Installed env (all four peers): `AEGIS_BIND=127.0.0.1`, `AEGIS_MODE=UNSEATED`,
`AEGIS_PROMOTION=DISABLED`, `AEGIS_LIVE_CREDENTIALS=FORBIDDEN`.

Release artifact SHA-256 (from `deployment-manifest.json`, identical R1/R2):

```text
a1aa08b2add34159e5fca241b43554039e55bb427281fc2c7a7097a1491731cd  README.md
28124a9a969b4761f81b1514c7237190a92e928c2c650cad5ab9ca20c4db5330  bin/aegis-ai-peer-unseated
7dc28a224de72fe3fb7652df9798127bb44236f13057c7bf013d0548a83fa196  env/ai-peer.env.template
c1a22c17934180a5d8b6aaaa956d6648fda22b8fdae1b95faa0ac63a11ff935e  env/claude.env
202672423c122457d9a404d6eacbdb744f233f4742398880822a7434e16f1812  env/gemini.env
7b0ccfd658895bc7ba75dcf3635cc2d224ce8da28981e20fbc0b220f31ede8f1  env/grok.env
d6471c145d26ea74e8baf675ecfd985877135e53c643f4313c0473d7761be6ac  env/lumin.env
0c8b8af037f3aa78c5c932bb576952d9428cac6a7406f36ad7c477a43aaa2173  scripts/health.sh
77b9a2849b7d7774eff9ade43edc2298595dd16cc0e26b885bdae1497ac0c35a  scripts/install.sh
d9fe700effae51116bfa0399248da87aba3c0b9ecdf336426a34fd02e2788ffa  scripts/render_manifest.py
e474e0e7eb0438e330f67e06c889b30e06a5919d7d26322f90d245103f76e410  scripts/rollback.sh
0ca5b907d2829e32c2f29bb9a93c1c7be27103dfa314d019d3ea9da0a4c31e87  scripts/upgrade.sh
53b47042e5d275d67ce9c50159f07febbee9247e500732762e7fca9e488ae59c  systemd/aegis-ai-peer@.service
```

## 6. Protected-artifact identity comparison

| Protected artifact | Expected | Observed (before → after) |
|---|---|---|
| `vm-cyberpeer-core-os-repair-copy` | attached OS disk | attached OS disk, **unchanged** (IMDS `22:04:36Z` → `22:10:30Z`); managedDisk id constant; `dataDisks=[]` |
| `vm-cyberpeer-core_OsDisk_1_f79b5c49e4f94a9792b038ccb685615b` | unattached, preserved | never referenced or touched |
| `vm-cyberpeer-core-os-snap-20260802` | snapshot, preserved | never referenced or touched |

Attached-disk identity is byte-identical before and after the entire run. No disk,
snapshot, detach, rename, format, or Azure command occurred.

## 7. Temporary-sudo teardown proof

- `99-aegis-deploy-nopasswd`: absent before removal → nothing to remove → `99 ABSENT_CONFIRMED`.
- `zz-aegis-deploy-nopasswd`: removed as final privileged action (`rm` exit 0) → `zz ABSENT_CONFIRMED`.
- `sudo -n true` now: **exit `1`, stderr `sudo: a password is required`** — passwordless sudo is gone specifically because a password is required.

Temporary sudo was removed only after all privileged work and successful final checks.

## 8. Repository checks (local)

- `git diff --check`: **passed**
- `deploy/scripts/*.sh` `bash -n`: **all OK**
- `deploy/manifest.template.json`: **valid JSON**
- `tests/test_deployment_artifacts.py`: **9 passed**
- Previous failed-run local note: **absent** (no untracked files; no failed-run note for this deployment).

## Disposition

Bounded, reversible UNSEATED deployment of the four AI Peers is live on
`vm-cyberpeer-core` at release `20260814-r2-220739Z` (source `bcab94f`), loopback
only, with rollback demonstrated and restored, no writes, no credentials, and all
three protected artifacts untouched. This record establishes record-preservation
readiness only. It does not seat any peer, claim continuity or selfhood, enable
promotion, or authorize live credentials.
