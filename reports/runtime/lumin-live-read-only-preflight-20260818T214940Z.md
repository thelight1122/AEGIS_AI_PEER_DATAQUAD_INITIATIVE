# Lumin Live Read-Only VM Preflight

## Decision

`PASS_READ_ONLY_PREFLIGHT — STOP_BEFORE_INSTALLATION`

The proposed Lumin namespace is collision-free on the VM reached through
`GabeCyberPeer`. The Lumin release remains local and `NOT_INSTALLED`. No upload,
account/group creation, directory creation, unit installation, service action,
DataQuad command, RLS invocation, listener creation, model connection, or live
write was performed.

The SSH and read-only privileged-inspection commands may be represented in the
host's ordinary authentication/audit logs. No command was issued to alter an
AEGIS workload, DataQuad, service, process, container, file, directory, account,
group, network listener, or runtime configuration.

## Authority and boundary

- Authorized phase: strictly read-only preflight for Lumin only.
- SSH alias: `GabeCyberPeer`.
- Proposed account/group: `aegis-lumin`.
- Proposed release root: `/opt/aegis/lumin/lab/current`.
- Additional reserved state/config roots checked:
  `/var/lib/aegis-lumin-lab`, `/etc/aegis-lumin-lab`.
- Proposed unit: `aegis-lumin-lab.service`.
- Excluded: existing DataQuad mutation, installation, upload, account/directory
  creation, systemd mutation, Docker mutation/exec, endpoint calls, DataQuad
  commands, RLS, and model/substrate calls.
- Preflight observation interval: `2026-08-18T21:46:07Z` through
  `2026-08-18T21:49:40Z`.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Local manifest integrity | PASS | 27 listed artifacts; 27 hash matches; 0 mismatches; 0 unlisted files |
| Local release identity/boundary | PASS | Lumin/lumin; release artifact only; independently seeded; no inherited Verus records; Ring 4/RLS/live activation unauthorized |
| SSH alias resolution | PASS | `azureuser@[REDACTED_VM_IP]:22`; configured identity-file path redacted |
| Strict SSH connection | PASS | Batch mode, strict host-key checking, 10-second connect timeout; exit 0 |
| Remote host identity | PASS | `AEGISGabePeer`, Ubuntu 22.04, Linux 6.8.0-1064-azure, x86_64 |
| Capacity | PASS | 61.98 GiB free at `/` and `/opt`; 27.40 GiB RAM total; 24.78 GiB available; 4 CPUs |
| Lumin account/group collision | PASS | account absent; group absent before and after |
| Lumin path collision | PASS | all proposed/reserved paths and all three common unit locations absent before and after |
| Lumin unit/process collision | PASS | unit not found/inactive; no matching process |
| Lumin container collision | PASS | read-only `sudo -n docker ps -a`; exit 0; no Lumin match |
| Lumin listener/port collision | PASS | package is stdio/SSH command transport; no port or socket unit declared |
| Namespace isolation | PASS | no `*lumin*` names beneath scoped `/opt/aegis`, `/var/lib`, systemd, or Gabe Core roots |
| Verus unchanged | PASS | root metadata, current symlink target, 4-file count, metadata digest, 4 content hashes, and 5 service states unchanged |
| Gabe unchanged | PASS | root metadata, 6 record-file count/digest, 5 ledger-file count/digest, and two safe small-file hashes unchanged |
| Stop boundary | PASS | Lumin remains absent/not installed; no deployment action taken |

## Local release verification

Release:
`reports/runtime/lumin-genesis-release-20260818T213828Z`

- Release manifest SHA-256:
  `E9DC643B9F91315CFC1EA80E639B0A07F5BED872E36DFCA2955BC276D50E904C`
- Manifest-listed artifacts: `27`
- Missing/mismatched artifacts: `0`
- Unlisted files: `0`
- Total release bytes, including manifest: `249638`
- Foundation receipt SHA-256:
  `16FC75F05E31ABB4813E84634F8A32BB792B17B24C4F9F1C72158932A32E637B`
- Canon source manifest SHA-256 recorded by the receipt:
  `BF1DE65C17E91CBCCD9E164322AF624508045AFC438DB8B4CE4D67C9CC906A86`
- Canon lock: clean; override used: false; review-needed sources: 0.

Foundation tensors:

| Tensor | Records | Bytes | SHA-256 |
|---|---:|---:|---|
| SPINE | 59 | 104801 | `A3077B38D83F07200842887004E785D993F1BB080DD969CE00D83366DE1425D1` |
| NCT | 70 | 99655 | `653F686B32A72A0B885013DED85C939E2B996FB3DF4F4DBB5EEDA55F771C70BE` |
| PEER | 2 | 2196 | `C8C6C6068CDF92CBAFF2AE3DFEEA1E215E19930D89CE64A9FB4600CE641DF817` |
| PCT | 2 | 2168 | `82E3BCD8CAA89137B8CD832E80E90D9900C2E883A81D3A5213F0982268AC697F` |

Total Foundation records: `133`.

The copied RLS Orb remains `copied_inactive`; its recorded runtime hash is
`51A1AC18887AEA9CEACC60B6F0AD428C899FA2D228D3BEE2032171F754E248CA`.

## SSH resolution and remote facts

Sanitized `ssh -G GabeCyberPeer` output:

```text
host GabeCyberPeer
user azureuser
hostname [REDACTED_VM_IP]
port 22
batchmode no
canonicalizehostname false
stricthostkeychecking ask
identityfile [REDACTED_LOCAL_KEY_PATH]
connecttimeout none
```

The actual connection overrode the permissive defaults:

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 GabeCyberPeer <read-only-script>
```

Connection result:

```text
utc=2026-08-18T21:46:44Z
hostname=AEGISGabePeer
identity=uid=1000(azureuser) gid=1000(azureuser) groups=...sudo...,ollama
kernel=Linux 6.8.0-1064-azure x86_64 GNU/Linux
os=Ubuntu 22.04
uptime=up 1 week, 1 day, 11 hours, 48 minutes
disk_root=129886128,64879888,64989856,50%  # KiB: total,used,free,use%
disk_opt=129886128,64879888,64989856,50%
memory=29423820800,2349023232,6661681152,26608869376  # bytes: total,used,free,available
cpu_count=4
python3_path=/usr/bin/python3
python3_version=Python 3.10.12
systemd_version=systemd 249 (249.11-0ubuntu3.22)
SSH_EXIT=0
```

## Exact read-only command families

All SSH executions used the strict options shown above. The remote commands
were limited to:

```sh
date -u +%Y-%m-%dT%H:%M:%SZ
hostname
hostname -f
id
uname -srmo
. /etc/os-release
uptime -p
df -P / /opt
free -b
getconf _NPROCESSORS_ONLN
getent passwd aegis-lumin
getent group aegis-lumin
stat -c '%n|%F|%U|%G|%a|%s|%y|%z' <explicit-path>
readlink -f /opt/aegis/verus/lab/current
find <explicit-scoped-root> -xdev -maxdepth <bounded-depth> -printf <metadata-only-format>
systemctl show <explicit-unit> -p LoadState -p ActiveState -p SubState -p UnitFileState -p FragmentPath --value
systemctl list-units --all --type=service --no-legend --no-pager
systemctl list-unit-files --type=service --no-legend --no-pager
ps -eo pid=,comm=,args=
ss -H -lntup
sha256sum <four-small-Verus-Foundation-files>
sha256sum <Gabe-pod-manifest-and-small-provenance-file>
sudo -n docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}'
python3 -B --version
systemctl --version
```

No recursive content hash was taken over Gabe's large tensors or ledgers. Gabe
record and ledger integrity evidence uses bounded file counts plus a SHA-256 of
the sorted metadata listing. Only the 6,168-byte POD manifest and 3,223-byte
provenance note were content-hashed.

Local hash verification used only:

```powershell
Get-Content -LiteralPath <release-manifest> -Raw | ConvertFrom-Json
Get-FileHash -Algorithm SHA256 -LiteralPath <manifest-listed-file>
Get-ChildItem -LiteralPath <release-root> -Recurse -File
```

## Lumin collision evidence

Before and after:

```text
account=ABSENT
group=ABSENT
/opt/aegis/lumin|ABSENT
/var/lib/aegis-lumin-lab|ABSENT
/etc/aegis-lumin-lab|ABSENT
/etc/systemd/system/aegis-lumin-lab.service|ABSENT
/lib/systemd/system/aegis-lumin-lab.service|ABSENT
/usr/lib/systemd/system/aegis-lumin-lab.service|ABSENT
aegis-lumin-lab.service|not-found,inactive,dead
lumin_processes=NONE
sudo_docker_exit=0
NO_LUMIN_CONTAINER_MATCH
```

The scoped filename/directory search returned no `*lumin*` match. The VM had 19
existing TCP/UDP listener rows at both checks, but the Lumin release declares
none: the client-side MCP is stdio and invokes a bounded remote command over
SSH; the proposed systemd unit is `Type=oneshot` and restricts address families
to `AF_UNIX`. There is no Lumin socket unit or network port in the package.

## Existing Verus unchanged evidence

Current target before and after:

```text
/opt/aegis/verus/lab/current -> /opt/aegis/verus/lab/releases/20260815T132828Z-91388c1e
file_count=4
metadata_sha256=491a148d8d34784b2596b9b46d096a08e2228901411731191c55d44768fea7ee
```

Content hashes before and after:

```text
NCT.jsonl   70ed27d7d30f72ca8e29f9790c9246c2fdbfd1550d18e3a00af23a70c6357b72
PCT.jsonl   710a6d809cccd98992945a3e44b1d4d90cb80acc5cceaf51cafa5d61b99127a8
PEER.jsonl  2a2afcdb1b2140422ffb713dfac2e21d6a88bb41788712241ba248802d3b6abe
SPINE.jsonl 1dc52c65ce878aeaf70fa1b786d37b16a401000dfa3bc2869192a85243bfe8ef
```

Service states before and after:

```text
aegis-verus-lab.service|loaded,active,exited|enabled
aegis-verus-advocate.service|loaded,active,running|enabled
aegis-verus-processor.service|loaded,active,running|enabled
aegis-verus-steward.service|loaded,active,running|enabled
aegis-verus-temporal.service|loaded,active,running|enabled
```

Verus root, state, configuration, and symlink metadata were identical across
the paired observations.

## Existing Gabe unchanged evidence

Authoritative observed POD root:
`/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1003-GABE/pod`

Before and after:

```text
records_count=6
records_metadata_sha256=fcc3244aab404b0b2b582733fdb787fe0358329ad402158e7eca1cb06dd0614a
ledgers_count=5
ledgers_metadata_sha256=0b2b4711277709ebf57a366434f41b50e82bec8dd2d87d1d1ecc96d9daeda99c
pod-manifest.json=a3c3307477f00019bba1a282929194a9adc5b57747337ec0f871ff1dad6ebc4a
FOUNDATION-PROVENANCE-PENDING.md=77635c99667da23a89af75bd06e98455b3100d17c6613c6dd822bce33de5cec4
gabe-rls-governor.service|loaded,inactive,dead|disabled
```

The root, POD, records, and ledgers directory metadata were identical across
the paired observations. The multi-hundred-megabyte records and 1.38 GB RLS
ledger were not content-read or hashed.

## Namespace conclusion and next gate

Lumin's proposed namespace does not overlap the existing roots observed:

- Verus: `/opt/aegis/verus/...`, `aegis-verus-*` units, `aegis-verus` account.
- Gabe: `/home/azureuser/AEGIS-CYBERPEER-CORE/data/peers/CP-1003-GABE/pod` and
  `gabe-rls-governor.service`.
- Lumin proposal: `/opt/aegis/lumin/...`, `/var/lib/aegis-lumin-lab`,
  `/etc/aegis-lumin-lab`, `aegis-lumin-lab.service`, and `aegis-lumin`.

Absence of the Lumin account, group, directories, and unit is expected and is
positive collision evidence, not installation completion. Any creation,
upload, ownership/permission assignment, unit installation, daemon reload,
enable/start, MCP activation, DataQuad access, RLS use, Ring 4 write, or model
connection remains a separate authorization gate.
