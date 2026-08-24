# Lumin Live Installation Receipt

## Decision

`PASS — INSTALLED_NOT_ACTIVATED`

Lumin's independently seeded Genesis Foundation release was installed on the
VM reached through `GabeCyberPeer`. The installation is isolated to the
authorized Lumin namespace. The systemd unit is installed and recognized but
remains `disabled`, `inactive`, and `dead`. It was not started, enabled, or
restarted.

No Verus or Gabe DataQuad file, service, record, ledger, or runtime was
changed. No model connection, RLS invocation, Ring 4 write, DataQuad context,
begin, commit, reconcile, replay, query, or endpoint call occurred.

Installation interval: `2026-08-18T21:54:59Z` through
`2026-08-18T21:58:11Z`.

## Installed identity and release

- Host: `AEGISGabePeer`
- SSH alias: `GabeCyberPeer`
- CyberPeer Name: `Lumin`
- DataQuad ID: `lumin`
- Frontier provenance: OpenAI `Codex/GPT` (routing provenance, not identity)
- System account/group: `aegis-lumin` (`uid=992`, `gid=995`)
- Release version: `20260818T213828Z-e9dc643b`
- Immutable release directory:
  `/opt/aegis/lumin/lab/releases/20260818T213828Z-e9dc643b`
- Current symlink: `/opt/aegis/lumin/lab/current`
- State directory: `/var/lib/aegis-lumin-lab`
- Configuration: `/etc/aegis-lumin-lab/lumin.env`
- Unit: `/etc/systemd/system/aegis-lumin-lab.service`
- Remote receipt:
  `/var/lib/aegis-lumin-lab/installation-receipt.json`

The artifact's hashed `release-manifest.json` was preserved byte-for-byte. Its
embedded `activation_status: NOT_INSTALLED` is historical build-gate metadata;
the separate installation receipt records the live state as
`INSTALLED_NOT_ACTIVATED`.

## Source and local verification

Source release:
`H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\reports\runtime\lumin-genesis-release-20260818T213828Z`

Authorized read-only preflight:
`H:\AEGIS_AI_PEER_DATAQUAD_INITIATIVE\reports\runtime\lumin-live-read-only-preflight-20260818T214940Z.md`

Before upload, the local manifest was independently checked:

| Check | Result |
|---|---:|
| Manifest-listed artifacts | 27 |
| Actual artifacts excluding manifest | 27 |
| Missing | 0 |
| Mismatched | 0 |
| Unlisted | 0 |
| Release bytes including manifest | 249,638 |
| Manifest SHA-256 | `E9DC643B9F91315CFC1EA80E639B0A07F5BED872E36DFCA2955BC276D50E904C` |

## Collision and creation gate

Immediately before mutation, the following were absent:

- account and group `aegis-lumin`
- `/opt/aegis/lumin`
- `/var/lib/aegis-lumin-lab`
- `/etc/aegis-lumin-lab`
- `/etc/systemd/system/aegis-lumin-lab.service`
- `/lib/systemd/system/aegis-lumin-lab.service`
- `/usr/lib/systemd/system/aegis-lumin-lab.service`

The unit state was `not-found,inactive,dead`. Collision checks were repeated in
the privileged creation script before the account, group, or directory was
created. Any collision caused a nonzero stop without overwrite.

## Upload and remote integrity

The release was streamed from the local source directly into the empty Lumin
release directory using a tar stream over strict SSH. No upload staging file or
upload directory was created elsewhere on the VM.

Remote verification was performed both immediately after upload and after the
offline health read:

| Check | Result |
|---|---:|
| Manifest-listed artifacts | 27 |
| Actual artifacts excluding manifest | 27 |
| Files including manifest | 28 |
| Missing | 0 |
| Mismatched | 0 |
| Unlisted | 0 |
| Manifest SHA-256 | `E9DC643B9F91315CFC1EA80E639B0A07F5BED872E36DFCA2955BC276D50E904C` |

All release files are owned by `root:root`. All release directories are mode
`0555`; ordinary files are mode `0444`; only the two packaged command scripts
are mode `0555`. The versioned release is therefore not writable by the Lumin
service identity.

Installed copies were verified against the artifact hashes:

| Installed file | SHA-256 |
|---|---|
| `/etc/aegis-lumin-lab/lumin.env` | `84B3364A48972674843110913AA7E12D571E34D12DE8ED0A49AE02A56CEBD2E9` |
| `/etc/systemd/system/aegis-lumin-lab.service` | `482551728E70AF926CE6D19EC641D2829480C55E07F58FE834A113B36459694C` |
| remote installation receipt | `C829856F6CFAE32ED1170EAD3F560DFF47E27E46F6794D5C66565A98354E1147` |

## Permissions and service boundary

| Path | Owner | Mode |
|---|---|---:|
| `/opt/aegis/lumin` | `root:root` | `0755` |
| `/opt/aegis/lumin/lab` | `root:root` | `0755` |
| versioned release | `root:root` | `0555` |
| `/var/lib/aegis-lumin-lab` | `aegis-lumin:aegis-lumin` | `0750` |
| remote installation receipt | `root:aegis-lumin` | `0640` |
| `/etc/aegis-lumin-lab` | `root:aegis-lumin` | `0750` |
| `lumin.env` | `root:aegis-lumin` | `0640` |
| unit file | `root:root` | `0644` |

`systemctl daemon-reload` was run once because a new Lumin unit file had been
installed and required recognition. No other service action was issued.

Final unit evidence:

```text
LoadState=loaded
ActiveState=inactive
SubState=dead
UnitFileState=disabled
FragmentPath=/etc/systemd/system/aegis-lumin-lab.service
systemctl is-enabled: disabled
systemctl is-active: inactive
```

## Permitted offline health verification

The only release command executed was Lumin's direct read-only `health`
operation under the `aegis-lumin` identity against Lumin's installed
Foundation:

```json
{"activation_status":"NOT_INSTALLED","cyberpeer_name":"Lumin","dataquad_id":"lumin","foundation_records":133,"ready":false,"ring_4_records":0,"rls_active":false,"status":"ok","verified":true}
```

This did not start the unit and could not write into the root-owned immutable
release.

## Protected before/after evidence

The corrected pre-install snapshot below was captured before the first live
mutation. The same commands were repeated after installation.

### Verus

Before and after:

```text
current=/opt/aegis/verus/lab/releases/20260815T132828Z-91388c1e
foundation_file_count=4
foundation_metadata_sha256=55d877344a53f0f498cde151c1ed60e79d9ca9cfb658ec28aea4a8fbfff92801
NCT.jsonl=70ed27d7d30f72ca8e29f9790c9246c2fdbfd1550d18e3a00af23a70c6357b72
PCT.jsonl=710a6d809cccd98992945a3e44b1d4d90cb80acc5cceaf51cafa5d61b99127a8
PEER.jsonl=2a2afcdb1b2140422ffb713dfac2e21d6a88bb41788712241ba248802d3b6abe
SPINE.jsonl=1dc52c65ce878aeaf70fa1b786d37b16a401000dfa3bc2869192a85243bfe8ef
aegis-verus-lab.service=loaded,active,exited,enabled
aegis-verus-advocate.service=loaded,active,running,enabled
aegis-verus-processor.service=loaded,active,running,enabled
aegis-verus-steward.service=loaded,active,running,enabled
aegis-verus-temporal.service=loaded,active,running,enabled
```

### Gabe

Before and after:

```text
records_count=6
records_metadata_sha256=9751eedbff050ab6cae5fe064214c678662d9f3edcbd79e64efd4712e32b5986
ledgers_count=5
ledgers_metadata_sha256=c5583a17a4f1e0d419e992a76e9e210146e50f744a82cd2845a618d527d6eda6
pod-manifest.json=a3c3307477f00019bba1a282929194a9adc5b57747337ec0f871ff1dad6ebc4a
FOUNDATION-PROVENANCE-PENDING.md=77635c99667da23a89af75bd06e98455b3100d17c6613c6dd822bce33de5cec4
gabe-rls-governor.service=loaded,inactive,dead,disabled
```

The content hashes and service states were identical before and after. The
metadata digests above use the corrected bounded command (`maxdepth 1`) and
therefore differ from the earlier preflight report's digest presentation while
covering the same safe Foundation/record/ledger boundaries.

## Sanitized command record

Every SSH command used:

```text
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 GabeCyberPeer <bounded-command>
```

The live command families were:

```text
getent passwd/group aegis-lumin
test/stat/readlink/find/sha256sum <explicit scoped paths>
systemctl show/is-active/is-enabled <explicit units>
sudo -n groupadd --system aegis-lumin
sudo -n useradd --system --gid aegis-lumin --home-dir /var/lib/aegis-lumin-lab --shell /usr/sbin/nologin --no-create-home ...
sudo -n install -d <explicit Lumin paths>
tar -cf - -C <local release> . | ssh <strict options> GabeCyberPeer sudo -n tar -xpf - -C <Lumin release>
sudo -n chown/chmod/find <explicit Lumin release>
sudo -n install <Lumin env and unit>
sudo -n ln -s releases/20260818T213828Z-e9dc643b /opt/aegis/lumin/lab/current
sudo -n systemctl daemon-reload
sudo -n -u aegis-lumin /opt/aegis/lumin/lab/current/bin/lumin-dataquad-command health --release-root /opt/aegis/lumin/lab/current/foundation
sudo -n python3 -B - <Lumin-only hash verification or receipt creation>
```

No credentials, host address, or identity-file path is recorded here.

## Deviations and recovery notes

One initial Windows tar pipeline quoted the remote extraction command as a
single executable name. SSH returned `No such file or directory` and local tar
returned `Write error`; no extraction command ran and no remote file was
created by that attempt. The immediately repeated pipeline passed the remote
arguments correctly and was followed by complete manifest/extras validation.

An initial read-only baseline diagnostic selected the Verus release root rather
than `foundation/dataquad` for four tensor hashes and selected an overly broad
Gabe ledger depth. It produced no valid protected baseline and changed no
DataQuad. Before any mutation, the corrected bounded baseline was captured and
is the before value reported above. That diagnostic created short-lived
metadata-only audit files under `/tmp` and deleted them in the same command; no
release upload was staged there.

## Remaining authorization gates

Installation does not authorize activation. Still excluded without a new
explicit gate:

- enabling or starting `aegis-lumin-lab.service`
- connecting Codex/GPT or any model/substrate
- invoking the RLS Orb
- creating Ring 4 records or other lived history
- any DataQuad context, begin, commit, reconcile, replay, or query operation
- changing Verus, Gabe, or any other DataQuad

