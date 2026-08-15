# Verus on GabeCyberPeer — Read-Only Preflight and Layout Gate

Observed UTC: 2026-08-15T10:29:09Z through 2026-08-15T10:29:43Z

Status: `READ_ONLY_PREFLIGHT_COMPLETE / INSTALLATION_NOT_STARTED`

This is an append-only evidence record. It does not edit an approved plan or
addendum and does not claim that Verus is installed or LAB Running.

## Verified authority

- Active Interaction Standard SHA-256:
  `7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`
- Target/model addendum SHA-256:
  `7E43BB63A5F6EA6B58FC4814971229B56602E8723767B7C46CA42B78BB94FE7E`
- Claude `ACCEPT` message SHA-256:
  `CC512573502AB4478B04644248740D51A4074775B90B9C5BD20E7B8902DE8C40`
- Source commit inspected:
  `a7953fdf8bcfb1a215e9bcf29bc59d7fa3f3b323`
- Exact model designation: `claude-opus-4-6`, routing provenance only
- Sole CyberPeer identity: `Verus`

## Target identity

- SSH alias: `GabeCyberPeer`
- Resolved operator and address: `azureuser@20.25.57.29`
- Strict known-host verification: PASS
- Known ED25519 host-key fingerprint:
  `SHA256:FrIgPcXlcaJXWGWpjyGK+6ywtHUOxyOfzLe4CfCk0ds`
- Hostname: `AEGISGabePeer`
- Machine-ID SHA-256:
  `8690ad3d73a2d2ed9c38d680b792db6e60264010d8e16919a665cc748a7df45e`
- OS: Ubuntu 22.04.5 LTS
- Kernel: Linux 6.8.0-1064-azure x86_64

No private key or secret value was read, printed, transmitted, or hashed.

## Resource and runtime checks

- CPUs: 4
- Memory: 29,423,820,800 bytes total; 18,135,633,920 bytes available
- Root filesystem: 133,003,395,072 bytes total; 68,598,960,128 bytes available
- Python: 3.10.12
- systemd: 249; system state `running`
- Anonymous HTTPS reachability to the Anthropic Messages endpoint returned
  HTTP 405, proving DNS/TLS/outbound routing without supplying a credential.
- Host listener on 8791: absent
- Host listener on 8790: absent. Gabe uses a separate host/container boundary
  described below; this does not authorize Verus to use 8790.

## Gabe preservation boundary

- Protected Codex-local tunnel: `127.0.0.1:8790`, SSH PID 28228, unchanged.
- `GET /api/pod/status` through that tunnel: HTTP 200, 1,412 response bytes.
- Container: `gabe-aegis-cyberpeer-core`
- Container ID:
  `96c126a21af2bae5536eae01a1211dc0f3d2c173160c8394801ff8bae7119c14`
- Image/content digest:
  `sha256:ba712c40ab67d272b3edfd56bd3bc236555955614ea6484969588fd5b251e125`
- Container state: running; restart count 0
- Gabe network mapping: host `127.0.0.1:8021` to container `8790/tcp`
- Gabe data mount: `/home/azureuser/AEGIS-CYBERPEER-CORE/data` to
  `/app/data`, read/write for Gabe's container
- Mounted-data metadata: 74 files, 31 directories, 0 symlinks,
  6,564,249,382 file bytes
- Sorted path/size/mtime metadata-manifest SHA-256:
  `b713a545d4597ad101cf26a469679264115ec2bde3ce18806bcd4a2168c7ec83`
- Gabe state directory contained no regular files at observation time.
- Existing small boundary artifacts:
  - `data/the-way/gabe-identity-image-v2.json` SHA-256
    `d944aec1e26600f090012db043f695d7feeee4ac1a2293f9912ff50037da0a4a`
  - `data/the-way-phase2b-shadow/shadow-observations.jsonl` SHA-256
    `1d1f83aec49d93648b3e3c197d656df3ccb2053a40af2b3d67827626b77b1190`
- `gabe-rls-governor.service`: loaded, inactive, disabled

No Gabe container, service, process, prompt, file, credential, DataQuad,
tunnel, listener, or historical record was changed.

## Verus collision and credential checks

The accounts `aegis-verus` and `aegis-ai-peer-verus` were absent. All checked
Verus application, state, configuration, environment, and unit paths were
absent. `aegis-verus-lab.service` was not loaded. Port 8791 was free.

Metadata-only checks found no Verus-specific Anthropic credential or Bridge
secret at either the accepted-addendum layout or the earlier installer layout.
No file content was opened. Credential absence is an external activation gate;
Gabe or Adam credentials are not eligible for reuse.

## Source/addendum mismatch discovered before first write

The accepted addendum requires exactly:

- account `aegis-verus`
- application root `/opt/aegis/verus/lab`
- append-only state root `/var/lib/aegis-verus-lab`
- configuration/credential root `/etc/aegis-verus-lab`
- service `aegis-verus-lab.service`
- listener `127.0.0.1:8791`

Commit `a7953fdf8bcfb1a215e9bcf29bc59d7fa3f3b323` instead packaged an older
Verus-only account and root layout. Installing those bytes would contradict the
accepted addendum even though they remained separate from Gabe. The mismatch
was detected before transfer, account creation, directory creation, credential
operation, unit installation, service transition, or DataQuad append.

The corrective source round is therefore local-only and creates a new commit;
it does not amend the accepted authority or create compatibility aliases to the
older layout. Activation remains blocked until that corrected release is
reviewed and the two Verus-specific credential files exist with safe metadata.

## Non-mutation declaration

No remote write, upload, install, account/group creation, directory creation,
credential read, service operation, container operation, firewall change,
public bind, new tunnel, Anthropic call, or DataQuad append occurred during this
preflight.
