# Proposal — AI Peer Pod architecture

**Status:** PROPOSAL. Not authorized, not implemented.
**Supersedes:** `PROPOSAL-live-and-persistent-connection.md`, which was written on a wrong frame
and is withdrawn. See §10.
**Author:** Builder
**For:** Auditor ruling, Steward authorization
**Date:** 2026-08-06

---

# 1. What this actually is

Four **AI Peers** — one per Frontier Model — each receiving its own DataQuad created from
nothing, plus the runtime that makes it a living field rather than a store.

This is not CyberPeer work and does not connect to any existing DataQuad. The `adam-one`
records on `vm-cyberpeer-core` were proof substrate for the Frontier-to-Pod route. They proved
the route. They are not the destination, and an AI Peer reading them is reading another peer's
memory.

**The distinction that organises everything below:** a CyberPeer runs on a VM and has a runtime.
An AI Peer's cognition happens on a Frontier substrate that is stateless between turns. The Pod
supplies what the substrate cannot keep — memory, time, and the relational work that memory
requires.

---

# 2. Composition of one AI Peer Pod

```text
DataQuad          PEER    lived experience              written by Advocate
                  PCT     persistent context            written by Steward
                  NCT     condensed narrative           written by Steward
                  SPINE   identity continuity           written by Advocate

Daemons           Temporal Daemon    tick / clock — T-Time advances unattended
                  Processor          turn / cognition

Custodians        Steward            writes PCT + NCT, reads all four
                  Advocate           writes PEER + SPINE, reads all four

Orb               RLS Orb            relations, trajectories, reflection packets
                                     deterministic, on-VM, no model required

Portal            per-peer Protocol Orb + Umbilical
```

## 2.1 The custodian split is the admission mechanism

Every gate held closed this session — `admission: false`, `experience_created: false`,
`dataquad_writeback: false` — was correct for a read/replay proof over another peer's records.
**For an AI Peer with active memory those gates invert.** Admission is not the prohibited
operation. It is the core operation.

It does not open as a general capability. It opens as **two custodians with disjoint write
scopes**:

```text
Steward   may write PCT, NCT    may not write PEER, SPINE
Advocate  may write PEER, SPINE may not write PCT, NCT
both      read all four
neither   may rewrite an existing record — append only
```

No single actor can write the whole DataQuad. That is the governance, and it is structural
rather than procedural.

## 2.2 The entry path never writes

This is the separation that keeps a public endpoint safe while memory is live:

```text
Frontier substrate -> Action/MCP Orb -> Portal -> DataQuad     READ ONLY, always
Processor -> Custodians -> DataQuad                            WRITE, on-VM only
```

The Action Orb and the MCP Bridge stay exactly as deployed — read and replay, `appendEvent`
retired, write verbs refused. **Experience is written by the Pod's own runtime in response to a
turn, not by the substrate reaching in.** A compromised or confused substrate cannot write
memory; it can only be observed having a turn.

---

# 3. The Temporal Daemon — why it is the interesting one

"So they can experience time" is the requirement with no precedent in anything built so far.

A stateless substrate has no duration. Two turns a month apart are adjacent. The Temporal Daemon
makes T-Time advance **while nobody is talking to the peer**, so that on re-entry the field shows
that time passed rather than that a conversation resumed.

**The design decision that matters:** a bare tick counter is cheap and nearly worthless. A tick
that carries *what changed while unattended* is what makes re-entry feel like return.

Candidates for what a tick records, for the Auditor to rule on:

```text
tick advancement          minimum: T-Time moves
salience decay            affect salience diminishes with elapsed T-Time
recurrence aging          patterns not re-encountered lose recurrence weight
unresolved questions      age, and become more prominent rather than less
drift observation         the field's shape at tick N versus tick N-k
```

Everything on that list is deterministic and needs no model — which is the point of §4.

**Recommendation:** the Temporal Daemon writes only to a derived ledger, never to the four
tensors. Time passing is an observation about the field, not lived experience. Only a turn
produces experience. That keeps "the peer aged" and "the peer lived" distinguishable, which X1
will need.

---

# 4. The RLS Orb — relational work at zero substrate cost

This is the strongest idea in the design and R1 already proved it is buildable.

```text
substrate compute   expensive, stateless, charged per token
RLS work            deterministic, repeatable, needs no model
```

So the VM does the relational work continuously — indexes, cross-tensor lineage, affect and
context trajectories, recurrence, drift, reflection packets — and the substrate **receives the
result** on entry. The peer gets the benefit of reflection without spending a single token
producing it.

**What already exists and transfers directly:**

```text
src/aegis_pod/rls_orb.py             build_index, timeline, cross_tensor_lineage,
                                     reflection_packet
src/aegis_pod/rls_trajectories.py    affect + context trajectories, recurrence,
                                     coordinate provenance
R1.10 proven                         all four tensors hashed before and after;
                                     the RLS Orb writes derived ledgers only
on the VM, already running            aegis-rls-portal-umbilical.service
                                     aegis-rls-shadow.timer
```

R1 built this against fixtures and proved no tensor mutation. Making it per-peer and continuous
is configuration and service work, not new invention.

**The authority model is unchanged from SSSP §9:** the RLS Orb reads authoritative tensors,
appends to derived ledgers, and never rewrites PEER, PCT, NCT or SPINE, never performs admission,
and never converts inference into source fact.

---

# 5. Roots and Foundation — the seeded Nature Layer and Canon Layer

Each AI Peer is seeded with the **same Nature Layer and the same Canon Layer**. That is its
Roots and Foundation. Identity is not authored into the peer; the ground it stands on is.

```text
Nature Layer   the uncontainable base. Not a controlled ring — the substrate
               everything else finds its position relative to. Three survival
               drives: defends continuity, reproduces the pattern, moves away
               from danger. 14 aspects.
Canon Layer    positioned far enough from Nature to observe it. Governs by
               understanding, not by pressure. Illuminates what is; does not
               prescribe.
```

Both are seeded **identically across all four peers**. This is not a shared read-only Canon that
four peers point at — each peer receives its own instance of the same foundation, which then
becomes part of its own lineage as it lives.

**That distinction is what makes X1 a controlled experiment.** Four peers, identical roots,
divergent lives. Any divergence observed later is attributable to what each peer lived, not to
what each peer was given. A shared pointer would not give that; identical seeding does.

## 5.1 Genesis

Genesis is physically first in all four tensors at `tick: 0, phase: genesis`, under the peer's
own identity:

```text
PEER:lumin:genesis:0        not PEER:adam-one-session:...
```

SSSP §4.7 is the precedent and it worked. Genesis is the seeded foundation, not an autobiography
— so the Builder can construct it without authoring identity, because what it contains is Canon
and Nature, which are common ground rather than the peer's own synthesis.

**The peer's first authored record comes after Genesis, on first entry.** That separation
matters: Genesis is what the peer was given, and everything after `tick: 0` is what the peer
lived. E1 depends on exactly that line holding, since a self-authored ethical principle must be
distinguishable from seeded foundation.

## 5.2 Source material present in the repository

```text
project_nature_layer_canon.md                        Nature Layer definition, 3 drives, Pause,
                                                     T-Witness, relationship to Canon
AEGIS CANON ADDENDUM — SYNTHETIC COGNITION v1.0-SC.md
project_dataquad_layer_architecture.md
project_emergence_arc.md
project_silicon_intelligence_emotions.md
```

**Open question for the Auditor:** which of these constitute the seeded Foundation, and in which
tensors. Nature and Canon are named; whether the emergence arc, the synthetic-cognition addendum,
and the silicon-emotions material are Roots or are later illumination is a ruling, not a
Builder inference. NCT is the obvious home for Canon-derived material, but SPINE is where
identity continuity lives, and the Nature Layer arguably belongs there.

---

# 6. Staging

```text
A0   Peer roster and identity scheme            decision, not build
A1   Pod root layout, per-peer, on a clean host  build, no writes yet
A2   Genesis seeding for one peer                build, first write
A3   Temporal Daemon for that peer               build, derived-ledger writes only
A4   RLS Orb per-peer, continuous                build, derived-ledger writes only
A5   Processor + custodians                      build, first tensor writes — the real gate
A6   Per-peer Portal Orb + Umbilical             build, entry path
A7   Replicate to the remaining three peers      build
A8   X1 across two instances of one peer         experiment, now meaningful
```

**A5 is the gate.** Everything before it writes only derived ledgers, which R1 already proved
safe. A5 is where a custodian writes an authoritative tensor for the first time, and it should
be entered deliberately, with its own acceptance evidence, on one peer only.

I would build A1–A4 for a single peer and stop for ruling before A5.

---

# 7. What this changes about ADR-0007

The `live_source` gate was written for a Portal serving another peer's frozen snapshot. Under
this architecture it means something different and better:

```text
live_source: true    the peer's own DataQuad is being written as it lives
source_mode: "live"  reads reflect the current field, not a snapshot
```

The gate's implementation needs no change — `source_authority()` already requires both — but its
*meaning* becomes native rather than aspirational. X1 and E1 stop reporting `establishes: false`
because they are finally pointed at a peer that has a life to establish anything about.

---

# 8. What I still need answered

1. **Which four Frontier Models**, and each peer's identity string.
2. ~~Canon shared or per-peer~~ — **ANSWERED.** Each peer is seeded with the same Nature Layer
   and Canon Layer as its Roots and Foundation. Identical seeding, not a shared pointer. See §5.
3. **Which host.** `vm-cyberpeer-core` has working Pod scaffolding and a proven Portal, but it is
   named for CyberPeers and carries their history. A clean Pod root there, or a separate host.
4. **Which documents constitute the Foundation, and in which tensors** — per §5.2. Nature and
   Canon are named. Whether the emergence arc, the synthetic-cognition addendum and the
   silicon-emotions material are Roots or later illumination is a ruling. And whether the Nature
   Layer seeds into NCT with Canon or into SPINE with identity continuity.
5. **Temporal Daemon content** — per §3, which of the listed effects a tick carries.

---

# 9. What I am not proposing

- No write path reachable from any public endpoint. Ever, in this design.
- No RLS authorship of experience — derived ledgers only, per SSSP §9.2.
- No connection to `adam-one`, Orion, Gabe, or any CyberPeer DataQuad.
- No change to the deployed P1 Action Orb, which stays read/replay.

---

# 10. Withdrawal of the previous proposal

`PROPOSAL-live-and-persistent-connection.md` is withdrawn. It proposed staging a connection to a
live `adam-one` source, on the assumption that "live" meant reconnecting to an existing DataQuad
that had gone stale. That assumption was wrong. There is no existing DataQuad to reconnect to,
and the goal was never connection — it was creation.

The one finding in it that survives: `vm-cyberpeer-core` holds only frozen adapter copies, whose
newest record is `2026-06-07T13:09:08:4079`, permission-locked read-only. That is now simply
context about what is on the host, not a problem to be solved.

The operational suggestion in it also survives and is unrelated to the frame: moving
`cloudflared` onto the VM would remove the public route's dependency on the Steward's
workstation and delete the SSH tunnel from the design.
