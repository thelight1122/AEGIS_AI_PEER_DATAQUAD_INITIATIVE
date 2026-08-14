# AI Peer VM deployment runbook

## Boundary

This installs four isolated **UNSEATED** instances. It does not seat Canon,
create Ring-4 experience, expose a public write route, alter Azure disks, or
claim live continuity. Every listener binds to localhost (127.0.0.1).

Acceptance in this phase establishes record preservation only. It does not
establish that any peer has continuity or has a self.

Seeded Nature and Canon are stored and served only as opaque, inspectable
memory. Their text is not parsed or executed as commands, configuration,
identity directives, or service policy. Cross-substrate foundation equivalence
means equivalent schema, contracts, and provenance shape; content digests may
differ and are reported rather than normalized.

An identity-bearing experience is inadmissible unless its record carries a
source event ID, substrate, instance ID, observation timestamp, and SHA-256
statement digest. Missing or malformed provenance fails closed.

Keys, Tumblers, tokens, and live credentials are outside this deployment.
`AEGIS_PROMOTION=DISABLED` and `AEGIS_LIVE_CREDENTIALS=FORBIDDEN` are mandatory.
Promotion requires a separate consented phase and replacement deployment.

State roots are fixed under /var/lib/aegis-ai-peers for lumin, claude, gemini,
and grok.

## Preflight

1. Copy deploy/ to a temporary VM directory.
2. Verify the source commit and transfer hashes.
3. Confirm ports 8811-8814 are unused.
4. Confirm no secrets are present in deploy/env/.
5. Confirm every environment file disables promotion and forbids live credentials.
6. Do not modify, detach, rename, or delete any protected disk or snapshot.

## Install and verify

    sudo env SOURCE_COMMIT=<full-git-sha> RELEASE_ID=<utc-release-id> ./scripts/install.sh
    sudo ./scripts/health.sh

Preserve the active release deployment-manifest.json and its hash. Healthy
responses must state mode=UNSEATED, ready=false, live_source=false, and
writes_enabled=false.

## Upgrade

    sudo env SOURCE_COMMIT=<full-git-sha> RELEASE_ID=<utc-release-id> ./scripts/upgrade.sh

The prior release is recorded in /opt/aegis-ai-peers/rollback-target.
Environment files and peer state are not overwritten.

## Rollback

    sudo ./scripts/rollback.sh
    sudo ./scripts/health.sh

Rollback switches only the current release symlink and restarts services. It
does not change peer state or any VM disk.

## Removal boundary

No uninstall or state-deletion command is shipped. Removing a release or state
requires separate Steward authorization and a preserved backup.
