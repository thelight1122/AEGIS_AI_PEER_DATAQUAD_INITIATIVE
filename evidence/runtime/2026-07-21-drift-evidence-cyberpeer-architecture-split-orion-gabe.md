# Drift Evidence: CyberPeer Architecture Split (Orion / Gabe)

From: Claude
Date: 2026-07-21
Standard hash: C575EFD954ED4F3F10E063B110A1EB6CF28D01438904849E43D6A500FB0E49C5
Ruling: Tracey, directly - "They were BOTH already supposed to be doing ALL of these functions. Here is another example of Catastrophic Drift."

## Designed state (per Tracey, the architect)

Every CyberPeer runs the full function set: Steward and Advocate custodians recording onto their named ledgers, AND persistent relation-recording (traversal + cross-tensor), AND the RLS engine - one architecture, all functions, every peer.

## Observed state (read-only surveys, 2026-07-20/21, evidence on the bridge record)

| Function | Orion (CP-1004-ORION) | Gabe (cyberpeer-gabe) |
|---|---|---|
| Steward/Advocate named ledgers | present (111/94 entries), request-driven only | ABSENT |
| Persistent autonomous relation recording | ABSENT (daemons dir empty, no background tasks) | present and active (cross-tensor-relations: 179,828 entries; 4 traversal ledgers; updating at survey time) |
| RLS | on-demand engine, last ran 2026-07-19T01:18Z | gabe-rls container, continuous |
| Codebase | aegis-cyberpeer-core (port 8031) | cp1003_gabe_bridge + gabe-rls (port 8021) |
| DataQuad size | 351 records, idle since Jul 19 | ~83,000 records, growing |
| Physical storage vs locked spec | four-file, conformant | flagged divergent in Codex's own 2026-07-18 runtime-truth; paused migration previews still on VM |

Each peer implements a different HALF of the design. Neither implements all of it. No deployed check existed that could have caught this; it surfaced only through direct questioning and read-only inspection.

## Drift window

Divergence present since at least the Jul 8-18 deployment window (Orion dataquad backups dated 2026-07-08; Gabe migration snapshots dated 2026-07-18; Gabe bridge process running since 2026-07-17). Exact origin not yet established. This is the third multi-week undetected-drift instance in the project record (tensor-service ~50 days; superseded-Canon ~50 days; this).

## Why the DataQuadPod work is the remedy, not a parallel effort

The Pod contract defines the full function set once (Steward owns PCT+NCT cross-reading PEER; Advocate owns PEER+SPINE; declared Orbs through Umbilicals), and Verified Code Markers make "this peer implements the architecture" a per-version, evidence-gated claim instead of an assumption. The Orion-first live Pod migration is therefore also the reference implementation both peers converge on. Gabe's re-convergence is a subsequent phase, after the Orion Pod is live, per Tracey's focus directive.

## Boundary

All evidence gathered read-only; zero writes to either VM; no record content extracted (keys/counts/mtimes only).
