# P0 Canary Recovery — delivery channel blocked, diagnosis reopened

**Recorded:** 2026-08-06T02:25Z
**Host:** `vm-cyberpeer-core` (AEGISIPFSNode, 20.122.189.26), RG-AEGIS-ADAM-ONE
**Ladder state:** recovery **not** applied. No rung advanced.

---

## What this record establishes

The `ufw allow 22/tcp` remedy is correct and remains unapplied. It cannot be delivered, because the
delivery channel itself is broken. Per the Auditor's contingency, the diagnosis is reopened rather
than a second remedy stacked.

## Evidence

### Run Command lifecycle, from the Azure activity log

```text
first_event_utc   2026-08-06T00:57:22Z
last_event_utc    2026-08-06T02:24:40Z
accepted_202      1
conflict_409     60
succeeded         0
```

Exactly one Run Command was accepted by ARM. It never reached a terminal state. Every subsequent
invocation — 60 of them across roughly 90 minutes — was rejected with `409 Conflict` because the
first is still considered in progress.

### Terminal status of the blocking Run Command

At 2026-08-06T02:27Z the originally accepted Run Command finally returned:

```text
VMExtensionProvisioningTimeout
Provisioning of VM extension RunCommandLinux has timed out.
Extension provisioning has taken too long to complete.
The extension did not report a message.
```

"The extension did not report a message" is the decisive phrase. ARM dispatched the goal state and
the guest-side handler never reported back at all — not a slow command, and not a command that ran
and failed. The slot released only by ARM-side timeout, roughly 90 minutes after acceptance.

### Extension handler state

```text
AADSSHLoginForLinux                Updating
AzurePerformanceDiagnosticsLinux   Updating
enablevmAccess                     Updating
MDE.Linux                          Updating
```

All four extensions are in `Updating`. None is in `Succeeded`.

### Last VM write before this session

```text
2026-08-02T19:20:18Z   Deallocate Virtual Machine   Succeeded
```

No extension write operation appears in the activity log for the preceding five days.

## Reading

The guest agent reports `Ready` at the heartbeat level (version 2.15.2.1) and the guest itself booted
cleanly — `ssh.service` and `ufw.service` both reached `OK` in the boot log. The agent accepts
goal states and does not complete them. That is an extension-handler condition, not a guest-OS
condition, consistent with the Auditor's earlier distinction.

**Whether the wedge predates this session is not fully determined.** Two readings are available and
the evidence favours the first:

1. **Pre-existing.** Extension `provisioningState` reflects the last ARM-level extension operation.
   No extension operation appears for five days. Extensions that had completed would read
   `Succeeded`. Reading `Updating` with no recent operation indicates they never completed since
   their last write, which predates this session and is contemporaneous with the 2026-08-02 repair.

2. **Induced.** An agent blocked on the accepted Run Command could fail to report extension
   completion, producing the same surface.

Reading 1 is better supported, because the five-day absence of extension operations cannot be
explained by a command accepted at 00:57:22Z on 2026-08-06. It is recorded as favoured, not proven.

## Consequence

Waiting is not a strategy. `enablevmAccess` — the VMAccess extension, the other agent-delivered
route to repair SSH — is wedged in the same state, so no extension-delivered remedy can land.

## Options, none authorized

1. **Azure Serial Console.** Bypasses both SSH and the guest agent, using boot diagnostics, which
   are already enabled on this VM. Gives a root console without restarting anything. Least
   invasive. Requires an interactive terminal session, so it is a Steward-side action.
2. **Restart the VM.** The standard remedy for a wedged agent. Touches no disk. The rollback path
   remains intact throughout. Carries the risk that a host booting from a repair copy with a known
   unexplained fault may not return cleanly.
3. **Continue waiting.** Recorded for completeness. The evidence above does not support it.

## Protected artifacts

Unchanged at 2026-08-06T02:16:27Z and not touched since:

```text
vm-cyberpeer-core-os-repair-copy       Attached      uniqueId 48405070-70fa-417c-82bf-545168d143d3
vm-cyberpeer-core_OsDisk_1_f79b5c49…   Unattached    uniqueId f79b5c49-e4f9-4a97-92b0-38ccb685615b
vm-cyberpeer-core-os-snap-20260802     snapshot      uniqueId 494a7b08-3bf9-4a46-b75c-7b6ccdf25bcd
```

No promotion, swap, rename-through-replacement, deletion, detachment, overwrite, or rollback
release has occurred. The Run Command extension has not been deleted or reinstalled.

**P0: 15/15 local; external canary pending.**
