# Post-reboot persistence verification

**Recorded:** 2026-08-06T09:14Z
**Auditor operational items 1 and 2**
**Result: all four conditions verified. The route self-restored with no intervention.**

---

## The reboot

Issued through the Azure control plane, not the guest, since `sudo` requires a password on
this host:

```text
az vm restart -g RG-AEGIS-ADAM-ONE -n vm-cyberpeer-core
requested   2026-08-06T09:09:24Z
```

The command emitted `No module named 'rpds.rpds'` from an unrelated CLI extension. That was
noise, not failure — confirmed by the boot clock:

```text
boot_time before   2026-08-02 19:32:20   (up 3 days, 13 hours)
boot_time after    2026-08-06 09:10:44   (up 1 minute)
```

SSH returned within 60 seconds of the restart request.

## 1. WARP stayed gone

```text
warp-svc is-enabled   disabled
warp-svc is-active    inactive
cloudflare-warp table absent (0)
```

This is the test Auditor sequence step 3 called for and it is now answered affirmatively.
`systemctl disable warp-svc` holds across reboot. The kill switch did not rebuild itself,
and the host remained reachable without any manual step.

## 2. Lingering user units returned by themselves

No login session, no sudo, no intervention:

```text
lumin-action-origin.service       enabled, active
aegis-private-portal.service      active
aegis-rls-portal-umbilical.service active

listeners: 127.0.0.1:8092  (Portal)
           127.0.0.1:8790  (Action Orb origin)
```

Lingering for `aegisadmin` is what makes this work. It also confirms the withdrawal recorded
in ADR-0007: `aegis-private-portal.service` is a real user unit that starts at boot, not
stale documentation.

## 3. Genesis retrieval, on-host

```text
record_id   PEER:adam-one-session:aegis-canon-genesis:0
clock       tick 0, phase genesis
mutation    False        experience_created  False
live_source False
```

## 4. Public route self-restored

No action was taken on the Windows side. The supervised tunnel reconnected on its own as
the VM came back.

```text
GET  https://lumin.adamone.bond/api/pod/status    200
POST https://lumin.adamone.bond/api/pod/context   200
     record_id   PEER:adam-one-session:aegis-canon-genesis:0
     clock       tick 0, phase genesis
     mutation    False    experience_created  False
     live_source False
     X-AEGIS-Posture: read-replay-only

POST https://lumin.adamone.bond/api/live-bridge/events   410
```

The retirement of `appendEvent` survives restart.

---

## A durability defect found and fixed before the reboot

The tunnel supervisor died on its own at approximately 07:34Z, and the scheduled task did
**not** restart it. The public route was returning 502 before the reboot was issued.

```text
task state       Ready (not Running)
LastTaskResult   3221225786 = 0xC000013A, process terminated
port 8790        not listening
```

The earlier durability claim covered one failure mode and was presented as if it covered
two. Killing the supervisor's **ssh child** and observing reconnection was a real test.
Killing the **supervisor itself** was never tested, and that is the mode that failed in
practice within ten minutes.

**Fix:** the task was re-registered with a second trigger repeating every 5 minutes
alongside the at-logon trigger, `MultipleInstances IgnoreNew` so a live supervisor is not
duplicated, and restart-on-failure retained.

Two registration attempts failed first and are recorded so the sequence is legible:
`RepetitionDuration [TimeSpan]::MaxValue` produced `P99999999DT23H59M59S`, rejected as out
of range; `[TimeSpan]::Zero` produced `PT0S`, also rejected. A finite 365-day duration was
accepted. Between the first failure and the fix there was no task registered at all,
because the old one had already been removed.

**Fix verified, not assumed:** the supervisor process and all five of its ssh children were
killed; the port dropped; recovery occurred within 30 seconds; public HTTP 200 was restored.

**Two distinct mechanisms, kept distinct.** The observed 30-second recovery came from the
task's **restart-on-failure** setting, which fires when a running task's process exits
abnormally. The **5-minute repeating trigger** is a separate and additional path: it starts
the task when it is in a non-running state, covering the case where restart-on-failure does
not fire at all — which is precisely what happened at 07:34Z, when the task sat `Ready` and
nothing revived it.

Only restart-on-failure has been demonstrated. The repeating trigger is registered and its
schedule is verified, but it has not yet been observed firing, because restart-on-failure
recovered the process first. Recording it as proven would overstate the evidence.

| Mechanism | Covers | Status |
|---|---|---|
| restart-on-failure | running task whose process exits abnormally | demonstrated, 30s |
| 5-minute repeating trigger | task in a non-running state | registered, not yet observed firing |

---

## Standing position

Per ADR-0007 the Portal declares `live_source: false` and serves an immutable copy. This
route survives reboot, but what survives is the **replay** route. Nothing here establishes
live DataQuad access, live continuity, or ethical formation.

Protected artifacts untouched throughout: `vm-cyberpeer-core-os-repair-copy` (attached),
`vm-cyberpeer-core_OsDisk_1_f79b5c49…` (unattached, preserved),
`vm-cyberpeer-core-os-snap-20260802` (preserved).
