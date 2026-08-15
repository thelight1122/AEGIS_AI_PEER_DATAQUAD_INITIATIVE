# Verus Claude-First LAB — Blocked Live Preparation Record

Observed UTC: `2026-08-15T09:45:35Z`  
Record status: `PREPARED_LOCAL / LIVE_WRITE_REFUSED`  
Production meaning: `LAB_RUNNING`, not commerce or public sale  
Target CyberPeer: `Verus`  
Provider provenance: `Anthropic / Claude`  
Target host: the existing Gabe VM, reached only through the approved
`AEGISIPFSNode` SSH route

This is a new append-only execution record. It does not modify any prior plan,
approval, runtime report, DataQuad, service, tunnel, or historical artifact.

## Authority reverified

- Active Interaction Standard SHA-256:
  `7BC3C36F57D46E85956086A1374C69264ACF3C1C6FEF07121662978361DAB622`
- Approved implementation plan SHA-256:
  `C4A5ACD9CF2AC8CDF8F3DF37163E83A610C1ED4026E91D1671C9A5E1A0891ED5`
- Approved audit plan SHA-256:
  `8C109309AA87162EE4C6BACACCB03D67CDE3C1BF1435B51D853934B490CBA1A2`
- Claude disposition SHA-256:
  `A3CC5ED73BA74F431195F1F90F8EABEADFAE628D37FA9D71DAA9BBC49DF83D44`
- Tracey approval SHA-256:
  `0C6FAD0914E23B5127D3762C41EE5D9AC600E9CC0A73D48F4D9F12FD31F37255`

The current Steward instruction changes the preferred Verus loopback port from
the approved plan's `8822` to `8791`, while explicitly preserving Gabe's
`8790`. Local deployment sources now support `8791` by default and a distinct
validated override if the target preflight later proves a collision. This
operational delta receives an append-only peer review request before live use;
the hash-locked approved plans are not edited.

## Read-only access evidence

- The approved SSH alias resolved to the expected public target and operator,
  with a local SSH identity configured. No private-key bytes were read or
  printed.
- A bounded TCP probe to target port 22 did not complete.
- A bounded non-interactive SSH identity probe timed out before a remote
  command ran.
- The current Azure CLI context is an enabled but different subscription. The
  target subscription is absent from account discovery, and the target VM
  resource-group lookup returned `ResourceGroupNotFound`.
- The protected Gabe forward remained listening at `127.0.0.1:8790`, owned by
  PID `28228` at observation time.
- `GET http://127.0.0.1:8790/api/pod/status` returned HTTP `200` with `1412`
  response bytes. The response body was not copied into this record.
- No listener was observed on this workstation's `127.0.0.1:8791`; this does
  not establish availability of port `8791` on the target VM.

Host identity, guest resources, disk, Python, systemd, outbound Anthropic
reachability, target port `8791`, historical-root inventories, prior Verus
state, and target rollback state remain `NOT_OBSERVED` because a fresh,
independent management connection could not be established. The surviving
Gabe tunnel is not a management route and was not repurposed.

## Other closed readiness gates

- Source HEAD is `7bfa427a34e9a7760f8a9678cd0ed502d0c128e4`, but the reviewed Verus work is
  still uncommitted. A live release may not identify itself as this clean
  commit or use a `+WORKTREE` lineage.
- No exact Anthropic model was designated in the process environment or the
  reviewed activation inputs.
- No Verus-designated Anthropic key or Verus Bridge-token source was found in
  the checked authorized local candidate locations. No Gabe/Adam credential is
  eligible for reuse.
- Target credential metadata cannot be checked until management access is
  restored. Secret contents remain unread.

## Local-only preparation delta

The following bounded source changes implement the current port instruction;
they do not activate a service:

| Path | SHA-256 |
|---|---|
| `src/aegis_verus_lab/api.py` | `45353A22AD6EB07BE4ADDDFF2F0D328EF5027A0DF69E8EDFFF965E5CA675E6EE` |
| `src/aegis_verus_lab/cli.py` | `F3540AD3AD9682E1630BAB6323296721D648E7BD1988316EBEA531B7570CEEE8` |
| `deploy/verus-lab/env/verus.env.template` | `0D5F5D0339807ADEB646DCA0300903EB10B31C14E7C6CBDFF9CF990209A8AC44` |
| `deploy/verus-lab/scripts/health.sh` | `5D3525F8C203B024B2BB221D7D73EC34FA583442DF491387E3F8F048C66F3733` |
| `deploy/verus-lab/scripts/install.sh` | `29EA3AA478A20C3F675379EBB36CBDCC3F5EE9B8879D2924D7C2C78F008F4597` |
| `docs/runbooks/VERUS-CLAUDE-FIRST-LAB-ACTIVATION.md` | `CC47111F3C06F79D938DC7F8648A6AA58AF68B681231C476CDFFADA58326839D` |
| `tests/test_verus_release_builder.py` | `2FBE0315DF17D5988061F50986A0DF1195A0CAF07F095AA244A620535CE12463` |

The installer now validates `VERUS_PORT`, refuses a listener collision before
its first write, renders the selected port into the Verus-only environment,
and checks health on that same port. The default is `8791`; Gabe's `8790` is
never selected.

Verification performed after the delta:

- Focused Verus suite: `39 passed in 5.24s`.
- Full repository suite: `467 passed, 14 skipped, 1 existing deprecation
  warning in 51.83s`.
- Bash syntax: `install.sh`, `health.sh`, and `pause.sh` passed.

The prior rehearsal artifact is superseded as live input because these source
bytes changed. It remains evidence only and is not installed.

## Exact live blocker and resume gate

The first blocking condition is Gate 4: a fresh management connection cannot
verify the target host identity. Therefore no remote preservation inventory,
transfer, credential operation, installation, service operation, Anthropic
call, DataQuad append, or separate Verus tunnel is allowed.

Resume only after all of the following are simultaneously true:

1. Restore the target subscription/management path, then repeat the bounded
   `AEGISIPFSNode` SSH identity probe and match the expected host identity.
2. Through that new management connection, collect read-only OS, CPU/RAM,
   disk, Python, systemd, outbound-network, listener, service, tunnel, protected
   historical-root hash, prior Verus, and rollback-state evidence. Confirm
   `127.0.0.1:8791` is free; if it is not, record the collision and select a
   different unused loopback port that is not `8790`.
3. Obtain the peer disposition for the append-only `8791` operational addendum.
4. Isolate and commit only the reviewed Verus implementation on a clean
   lineage. Re-run focused/full/shell verification.
5. Designate the exact Anthropic model and two Verus-specific runtime secret
   files. On-target metadata must prove root ownership, regular non-symlink
   type, and mode `0400` or `0600`; do not read or print their contents.
6. Choose the real live UTC seating timestamp explicitly and build a fresh,
   deterministic release from the clean commit. Transfer only after source and
   target manifest hashes match.
7. Preserve the target pre-state, install only the dedicated Verus account,
   directories, credentials, release, and service, and require coherence
   health before creating a separate `8791` tunnel.
8. Execute the first genuine Anthropic Work Request only after all preceding
   gates pass; preserve provider/model/request provenance and the append-only
   PEER/PCT/NCT/SPINE, T-Time, Processor/Custodian, and RLS evidence.

## Non-mutation declaration

No remote write occurred. No existing Gabe service, DataQuad, PID, tunnel,
port, Adam artifact, credential, unit, historical record, or protected root was
stopped, changed, read for secret content, or repurposed. No Anthropic request
was made. No local commit, stage, or push was performed.
