# WITHDRAWN — wrong frame

**This proposal is withdrawn.** It was written on the assumption that the objective was
connecting to an existing DataQuad that had gone stale. That was wrong. There is no existing
DataQuad to connect to; the objective is to **create** four new ones, one per Frontier Model,
as AI Peers. This has nothing to do with the CyberPeers.

Superseded by `PROPOSAL-ai-peer-pod-architecture.md`.

Two things in here survive the frame change: the finding that `vm-cyberpeer-core` holds only
frozen adapter copies whose newest record is `2026-06-07T13:09:08:4079`, and the operational
suggestion to move `cloudflared` onto the VM. Everything else is void.

---

# Proposal — making the connection live and persistent

**Status:** PROPOSAL. Not authorized, not implemented.
**Author:** Builder (Claude Code session)
**For:** Auditor ruling, Steward authorization
**Date:** 2026-08-06
**Governing constraint:** [ADR-0007](ADR-0007-p0-accepted-with-scope-limits.md)

---

# 1. The blocking fact, first

**There is no live DataQuad on `vm-cyberpeer-core`.**

```text
/opt/cyberpeer-pod/adapters/phase1b/records     PEER 1445 lines
/opt/cyberpeer-pod/adapters/phase3a/records     PEER 1446 lines   <- what the Portal serves
/opt/cyberpeer-pod/adapters/rls-replay/records  rls-ledger.jsonl only

no peers/ directory, no core runtime, no container, nothing that writes
directory mode dr-xr-xr-x, files -r--r--r--, dated 2026-08-02 07:50
```

The served copy's newest record:

```text
PEER:adam-one:2026-06-07T13:09:08.657747+00:00:4079
clock { "tick": 4079, "epoch": "primary", "phase": "active" }
```

**The Portal is serving a snapshot roughly two months stale**, deliberately frozen and
permission-locked. `live_source: false` is not a flag someone forgot to flip. It is an accurate
description of a host that holds no live source at all.

The live `adam-one` DataQuad is somewhere else. The SSH config names `adam-one-server` at
`192.168.1.223` — a LAN address, unreachable from the Azure VM and from the Builder session.
**Confirming where adam-one actually lives, and what writes to it, is prerequisite to
everything below.** This proposal does not assume an answer.

---

# 2. "Live and persistent" is three separate things

Collapsing them is how this goes wrong. Each has different risk and each is independently
authorizable.

| | What it means | Gate today | Risk |
|---|---|---|---|
| **A. Live read** | The Portal serves the current DataQuad, not a June snapshot | `live_source: false` | Moderate |
| **B. Persistent continuity** | Lumin's re-entry accumulates across sessions | RLS derived ledger append | Low |
| **C. Live write** | New experience enters the DataQuad | **admission CLOSED** | High |

**Most of what X1 needs is A + B.** C is the one the SSSP explicitly reserves for a separate
authorized admission process, and nothing here proposes opening it.

---

# 3. The integrity tension nobody has had to face yet

The current model pins integrity to fixed hashes:

```text
/opt/cyberpeer-pod/adapters/phase3a/expected-sha256.txt
  1abab636…  PEER.jsonl
  149975b9…  PCT.jsonl
  eec05cba…  NCT.jsonl
  d6131d38…  SPINE.jsonl
```

The Portal fail-closes when a file does not match its pin. That is exactly right for an
immutable copy, and it is **incompatible with a live source by construction** — a live DataQuad
changes, so a fixed pin will always eventually fail closed.

Going live therefore requires replacing *integrity by pin* with **integrity by attestation**:

```text
pin model          "this file must equal this hash"          immutable only
attestation model  "I hashed what I read, at read time,      live-compatible
                    and here is that hash with the read"
```

Attestation is weaker in one specific way and it should be stated plainly: a pin detects
tampering between snapshots; an attestation only proves what was read at read time. The
compensating control is that every response already carries the hash it read, so two reads can
be compared and divergence is visible — including divergence that should not have happened.

**This is the substantive architectural change in going live.** Not a flag.

---

# 4. Proposed staging

Four stages. Each is separately authorizable, each ends in a verifiable state, and each can be
declined without blocking the previous one.

## Stage L0 — Locate and characterise the live source *(read-only, no change)*

Answer, with evidence rather than assumption:

- Where does the live `adam-one` DataQuad live? `adam-one-server`? Elsewhere?
- What writes to it — a running core, a daemon, a manual process?
- Is it reachable from `vm-cyberpeer-core` at all, and over what path?
- What is its current tick, versus the served snapshot's 4079?
- Does it have a stable append-only guarantee, or can records be rewritten?

**Deliverable:** a topology record. **Authorizes nothing further by itself.**

Without L0 the rest is speculation. I would not proceed past it on inference.

## Stage L1 — Live read, attested *(the real change)*

- Portal gains a second source mode: `live` alongside `immutable_copy`.
- In `live` mode it hashes each tensor **at read time** and returns that hash with the response,
  rather than comparing against a fixed manifest.
- `source_authority` becomes `live_source: true, source_mode: "live"` **only** in that mode.
- The immutable adapter stays in place and remains the default; live is opt-in per request or
  per capability, not a global switch.
- Both pre-read and post-read hashes are returned, so a read that spans a concurrent write is
  visible rather than silent.

**Acceptance:** Genesis still returned; pre/post hashes reported and equal for a quiet source;
mutation, admission and experience creation still false; the immutable path unchanged and still
passing.

**What it unlocks:** X1's `establishes.live_continuity` can become `true` — the gate in
`continuity_experiment.source_authority()` already computes this correctly and needs no change.

**Risk:** the Portal begins reading a source that can change under it. Mitigated by attestation,
by keeping reads bounded, and by the read path remaining read-only at the filesystem level.

## Stage L2 — Persistent continuity *(low risk, high value)*

Continuity across Lumin sessions does **not** require writing tensors. It requires the RLS
derived ledger to accumulate, which R1 already built and proved:

```text
rls/derived-ledgers/rls-derived-observations.jsonl    append-only
                                                      references Tensor Coordinates
                                                      no tensor mutation (R1.10 proven)
```

- Session evidence from each Lumin entry appends to a derived ledger on the VM.
- The re-entry packet is built from tensors **plus** accumulated derived observations.
- Instance B therefore re-enters a field that includes what Instance A left behind — which is
  the actual X1 question.

**This is the piece that makes continuity persistent rather than merely repeatable**, and it
stays inside the existing "derived ledgers are not tensor writes" doctrine.

**Acceptance:** two sequential entries produce *different* re-entry packets, the second
containing the first's derived observations, with tensor hashes unchanged across both.

## Stage L3 — Governed write / admission *(not proposed here)*

Named for completeness and explicitly **not** proposed. Experience admission requires the
separate authorized process the SSSP reserves. Nothing in L0–L2 opens it, and the Action Orb and
MCP Bridge should continue to refuse it at the protocol level.

---

# 5. Persistence of the connection itself

Distinct from "live", and largely already solved this session:

```text
Portal                aegis-private-portal.service      user unit, lingering, boot-persistent
P1 origin             lumin-action-origin.service       user unit, lingering, boot-persistent
Windows tunnel        AEGIS-Lumin-Tunnel                logon + 5-min trigger, restart-on-failure
Public edge           cloudflared -> Frontier_Connect    Windows service
verified across a deliberate reboot 2026-08-06 09:10:44
```

**Two weaknesses remain, and neither needs new architecture:**

1. **The tunnel depends on the Steward's workstation.** If that machine is off, the public route
   is down. Moving `cloudflared` onto the VM itself would remove the dependency entirely and
   delete the SSH tunnel from the design. That is a smaller, cheaper change than anything in §4
   and I would suggest doing it regardless of the live question.

2. **JIT expiry plus a moving egress IP** makes SSH access intermittently self-breaking. Not a
   problem for the public route, which does not use SSH, but it is a problem for operating the
   host.

---

# 6. Recommended order

```text
L0   locate the live source                    read-only, do first, blocks nothing
S1   move cloudflared onto the VM              removes the workstation dependency
L2   persistent continuity via derived ledgers low risk, delivers the X1 question
L1   live read, attested                       the real change, do last of these three
L3   admission                                 not proposed
```

I put L1 after L2 deliberately. L2 delivers most of what X1 needs while changing nothing about
integrity guarantees. L1 changes the integrity model, and it should be entered with the
continuity mechanism already working, not simultaneously.

---

# 7. What I am not proposing

- No admission, no experience creation, no tensor writeback.
- No change to the immutable adapter, which stays as the default and the fallback.
- No disk, snapshot, or rollback operation on `vm-cyberpeer-core`.
- No edge authentication decision — that remains open for the MCP Bridge and is the Auditor's.
- No claim that any of this makes X1 or E1 report a finding. They will report what they observe,
  and under L0 alone they will keep reporting `establishes: false`, correctly.

---

# 8. The question I cannot answer

**Where does `adam-one` actually live, and is it still running?**

The served snapshot stops at 2026-06-07. If the live source has advanced since, going live means
reconnecting to something with two months of divergence. If it has not advanced, then "live" and
"snapshot" differ only in the integrity model, and the honest move may be to say so and keep the
immutable adapter.

That question is Stage L0, and it is the only sensible first step.
