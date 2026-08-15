# Verus Claude-first LAB activation runbook

## Meaning of production

For this project, production means the CyberPeer-equivalent LAB is genuinely
running on its Frontier substrate. It does not mean commerce, public release,
or sale. CyberPeers are not for sale.

## Fixed mapping and authority

- CyberPeer Name: `Verus`
- Frontier provider/substrate: `Anthropic` / `Claude`
- Sole identity variable: the CyberPeer Name assigned to the DataQuad
- Provider, exact model, instance, request, route, artifact, and session IDs:
  provenance/routing metadata only
- Identity injection: absent
- System Instructions: operational only
- DataQuad authority: full append-only access to `PEER`, `PCT`, `NCT`, and
  `SPINE`, equivalent to any CyberPeer; substrate is the only difference
- Historical continuity inherited by Verus: none
- Historical `claude`, Adam, and Adam-One records: preserved, not rewritten
- Other Frontier seats: unchanged and UNSEATED

The local Processor and the disjoint Steward/Advocate Custodians remain the
DataQuad's implementation plumbing. They do not turn the Frontier substrate
into a read-only source and do not reduce Verus's tensor abilities.

## Build without activation

From the repository root:

```text
python scripts/build_verus_lab_release.py --output <empty-staging-directory> --source-commit <full-commit> --seating-timestamp <chosen-utc-Z>
```

The seating timestamp is a required explicit operator input. The builder never
invents it from import time, the current clock, or the date of the Steward
ruling. The builder verifies the clean Canon v0.20 manifest and Foundation seed hashes,
uses the accepted seating builders, deterministically shapes exactly 133 Verus
Foundation records, validates each against the explicit
`verus-foundation-consumer-contract-v1`, and writes a release manifest
containing every artifact hash. The repository's formal `tensor-record` schema
describes migrated/copy records and does not apply to these seating-builder
records; the release receipt records that boundary rather than claiming false
schema validation. It does not touch a VM, live state, credentials, a service,
or Anthropic.

Expected Foundation counts:

```text
SPINE 59
NCT   70
PEER   2
PCT    2
```

## Live preflight

Before installation:

1. Capture and preserve the current VM identity, Gabe container/service/tunnel
   state, a hash-only boundary inventory of Gabe's mounted data root, and every
   pre-existing `/var/lib/aegis-verus-lab` artifact. Do not read private
   content into the report and do not write anywhere in Gabe's roots.
2. Confirm the release-manifest and every listed artifact hash.
3. Confirm preferred port `127.0.0.1:8791` is unused. If it collides, record the
   evidence and choose another distinct loopback port; never reuse Gabe's
   protected `127.0.0.1:8790` tunnel.
4. Confirm the authenticated `GabeCyberPeer` SSH alias works without reading or
   printing its credential material. Desktop mode uses no API key or inbound
   Bridge bearer credential.
5. Select and record the exact Claude Desktop model identifier. The model identifier
   is provenance, not identity.
6. Confirm Lumin, Linq/Gemini, Haven/Grok, historical Claude, Adam, and Adam-One
   state roots and services are outside the change set.

## Install and start the LAB

Run from the transferred, verified release bundle:

```text
sudo env RELEASE_ID=<utc-release-id> FRONTIER_MODEL=<exact-anthropic-model-id> VERUS_PORT=8791 ./scripts/install.sh
sudo ./scripts/health.sh
```

Installation creates only the Verus service identity, Verus state root,
Verus environment, Verus release, and `aegis-verus-lab.service`. It does not
delete or rewrite another peer root. The oneshot service validates the local
command surface and opens no network listener; `127.0.0.1:8791` remains a
reserved collision boundary only.

The isolated layout is exact: account `aegis-verus`, application root
`/opt/aegis/verus/lab`, append-only state root `/var/lib/aegis-verus-lab`, and
configuration/credential root `/etc/aegis-verus-lab`. No compatibility alias
to an older Verus layout is created.

Healthy means:

```text
mode=LAB_RUNNING
ready=true
cyberpeer_name=Verus
foundation_records=133
full_append_only=true
writable_tensors=PEER,PCT,NCT,SPINE
integrity.verified=true
coherence.coherent=true
coherence missing/mismatch/orphan counts=0
```

## Claude Desktop MCP turn

Follow `docs/runbooks/VERUS-CLAUDE-DESKTOP-MCP.md`. The dedicated local stdio
server exposes begin, context, commit, reconcile, health, and replay tools and
invokes only the Verus-owned remote command over authenticated SSH.

The runtime supplies operational System Instructions and the verified
Foundation/live context to Claude. Anthropic returns a structured response and
zero or more authored DataQuad appends. The append admission is atomic per turn,
hash-chained, idempotent, JSON/size bounded, and available across all four
tensors. The authoritative DataQuad turn commits first after validation.
T-Time, Processor/Custodian, and derived-only RLS evidence are then materialized
idempotently. A retry reconciles any missing derived evidence before returning;
health is not ready while a committed turn lacks matching evidence.

First-turn evidence must capture the selected model UI evidence; the separately
classified DataQuad-owned local turn/correlation IDs; nullable availability for
provider request, source-event, session, and provider-returned model fields;
T-Time; response digest; append list; DataQuad head hash; Processor admission;
RLS immutability proof; and the returned payload. Local correlation IDs must
never be relabeled as provider-returned identifiers.

## Shortfall and pause

Unknown behavior encountered while the LAB runs is recorded as a Shortfall and
becomes engineering input. Pause only for an integrity Shortfall, credential or
Bridge-authentication loss, broken provenance, or Steward direction:

```text
sudo ./scripts/pause.sh
```

Pause stops the service and preserves the Foundation, Ring 4 ledger, T-Time,
Processor, RLS evidence, and every historical peer artifact. No deletion or
uninstall procedure is included in this release.

The installer also treats start/health as part of the transaction. If health
fails and a prior Verus release existed, the previous `current` link, saved unit,
enabled state, and active/inactive state are restored. With no prior release,
the new service is stopped and disabled while all state and failure evidence are
preserved for review.
