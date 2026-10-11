# Disposable Windows durability lab — provisioning gate

Status: **NOT PROVISIONED / READ-ONLY INVENTORY COMPLETE**.
Do not restart the shared Windows VM, modify its runtime, or treat a
worker-process crash as a machine-level storage durability test.

## Observed infrastructure

- The flyExplorer canonical main is WinUI 3. Draft PR #63 adds
  staged-Copy ownership receipts and immutable phase markers.
- Central CI serves multiple projects from **one shared Windows VM**.
- Read-only Remote Shell audit
  [#38174021618](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38174021618)
  confirmed: VM detected, hypervisor present, nested CPU virtualization
  **not available**, Hyper-V management **not available**,
  `vmms` **not running**, Sandbox **not enabled**,
  system drive about **38 GiB free**.
- These are properties of the **guest**. They do not describe the
  physical host or prove that a separate disposable VM exists.
- The central Remote Shell request was returned to idle after the audit.

## Hyper-V host is a separate computer — host connection not yet established

The operator confirmed that the Hyper-V host is a **different physical
computer** from both the shared Windows guest and the separately
registered `personal-pc` control target. Do not route host-management
or disk-provisioning commands to either of those targets.

The available Desktop Commander device inventory currently lists
only `DESKTOP-FJM09OG` (offline), not the separate Hyper-V host.
Connecting the host requires a **new user-authorized device
registration**. Until that registration or a host-local audit result
exists, no real host resource or spare VM claim can be made.

**Host-local alternative:** on the separate Hyper-V computer, open an
authorized Windows PowerShell session with Hyper-V management access
and run the versioned read-only
`tools/winui/Inspect-HyperVDurabilityHost.ps1` script from a trusted
checkout of this exact branch. Share only its `FLY_HYPERV_...`
summary lines; no host names, VM names, VM GUIDs or storage paths are
required for this first capacity review. The script only queries
Hyper-V availability and capacity; it does not provision resources.

If remote access is preferred, register **that separate host**, not the
shared guest, in the authorized Desktop Commander device manager:
https://mcp.desktopcommander.app/. Then confirm the connected device
identity before any script execution, and run read-only inventory
only. VM creation, VHDX creation, checkpoint/export and any
reboot/power-off remain distinct state-changing gates.

## Hyper-V host identified by operator — host connection not yet established

The operator identified the outer virtualization platform as **Hyper-V**.
The existing Windows VM remains a **guest**, and its lack of nested
virtualization does not imply the Hyper-V host lacks the ability to
create an independent test VM.

A new **read-only host audit script** is versioned at
`tools/winui/Inspect-HyperVDurabilityHost.ps1`. On the **actual Hyper-V
host**, from a PowerShell session permitted to query the Hyper-V service,
run:

```powershell
& .\tools\winui\Inspect-HyperVDurabilityHost.ps1
```

This prints only VM/switch counts, remaining host RAM, available
free GiB at Hyper-V's default VHD location, whether the default
directories exist, whether the dedicated name
`flyExplorer-DurabilityLab` is unused, and whether checkpoint/export
query commands exist. It does **not** display guest names, VM IDs,
account identities, disk paths or modify host resources.

Do **not** run this inside the shared `windows-vm`: it has no Hyper-V
management service. An authorized host control channel must be
identified first; the central `personal-pc` runner is *not assumed*
to be the Hyper-V host merely because it exists.

### Provisioning blueprint after a successful host audit

1. Identify the existing shared VM by **its actual host-side VM GUID**
   and explicitly exclude it from all subsequent command targets.
2. Select an unused test VM name and a new, isolated Hyper-V storage
   directory on a host volume whose free space is adequate for a
   Windows OS and a separate owned test VHDX. Verify the host can
   still run its current production guests without memory pressure.
3. Use a **Generation 2** guest where the OS image supports it.
   Plan separate system and test data VHDX, with no attached existing
   shared guest disk and no physical-disk passthrough.
4. Keep the disposable VM isolated from production networks unless
   necessary for product setup; if connectivity is needed, use a
   separately reviewed Hyper-V virtual switch arrangement.
5. Save a **host-side export or otherwise independently restorable
   image**, separately from any VM checkpoint, and verify the
   restore process and exact new VM ID. A checkpoint by itself is
   not proof of safe external recovery.
6. Use unique owned test roots and preserve hashes, immutable
   receipt paths, marker phase and FileIdInfo evidence **outside**
   the guest. Do not enable deletion/recovery by default.

Provisioning, checkpoint creation and guest interruption are
separate, state-changing steps: **do not run them without the host
identity, storage path, resource budget and explicit scope being
reviewed first**. A guest's read-only
[capability audit #38174021618](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38174021618)
cannot satisfy the host audit.

## 2026-10-12 host-local Hyper-V audit results — CAPACITY PRELIMINARY PASS

The operator ran the read-only inspection statements on the separate
Hyper-V host and supplied the `FLY_HYPERV_...` results directly:

| Host measure | Observed |
| --- | --- |
| Hyper-V management and running VMMS | PASS / TRUE |
| Existing VM count | 2 |
| Existing running VMs | 1 |
| Virtual switches | 1 |
| Default VHD and VM config directories | both exist |
| Free space on default VHD storage volume | 142 GiB |
| Total host RAM | 63 GiB |
| Available host RAM at time of inspection | 45 GiB |
| Proposed `flyExplorer-DurabilityLab` VM name already registered | No |
| Checkpoint query and export commands | both available |
| New disposable VM and separate test VHDX | **NOT VERIFIED / NOT PROVISIONED** |
| Independent export/restore actually performed | **NOT VERIFIED** |

**Interpretation:** the separate Hyper-V host has plausible capacity to
run a disposable guest alongside the existing guests, but these values
are only a point-in-time snapshot. `FLY_HYPERV_HOST_AUDIT=PASS` means
the management reads succeeded; it does NOT prove a Windows installer
image, licensed guest OS, spare physical capacity for both checkpoint
growth AND independent VM export, or a usable rollback.

The operator pasted each PowerShell statement interactively; the
initial `#requires` directive produced a console parsing error.
That header belongs at the beginning of a script file, not pasted
as an interactive prompt command. The independent Hyper-V queries
and summary results followed successfully. For reproducibility, use
the exact reviewed `.ps1` file for subsequent audits instead of
copying escaped/HTML-formatted Markdown into the console.

### Proposed isolated machine — pending exact host review

- VM name: `flyExplorer-DurabilityLab`, **new VM ID required**
- VM generation: Gen 2, supported Windows version, OS installation
  ISO/image supplied legitimately by the operator
- Initial test sizing for review: **2 virtual CPUs, 8 GiB guest RAM**;
  dynamic system VHDX **64 GiB logical maximum**, and separate test
  data VHDX **16 GiB logical maximum** (not already allocated)
- Hyper-V checkpoint/export: keep **separate off-VM recovery media**
  and reserve physical space for the actual OS payload, any test data,
  checkpoint delta growth and independent export; 142 GiB *free* does
  not guarantee two full copies of the provisioned guest will fit.
- Switch: the single existing switch is **not automatically approved**.
  Confirm its isolation properties before any VM network attachment;
  prefer no NIC if installation/testing can proceed offline.
- Creation preconditions: separate host management authorization,
  exact existing VM ID protection, Windows installation media,
  host storage location, disk capacity budget and restore/export
  location reviewed. First planned execution is a **non-destructive**
  host identity/backup feasibility check, NOT any VM reset.

**Current gate: HOST CAPACITY OBSERVED; PROVISIONING AND RECOVERY
UNVERIFIED.** Keep the shared Windows VM running and do not modify
its disk attachments, checkpoint tree, runner, settings or profiles.

## Required independent resources

Before any machine interruption, obtain the following from a
**separately controlled host or cloud virtualization service**:

| Gate | Required evidence |
| --- | --- |
| VM ownership | Distinct test VM resource ID, explicitly *not* the shared `windows-vm` |
| Isolation | Dedicated Windows guest and separate test data disk/volume, neither used by CI nor user profiles |
| Resource budget | Sufficient CPU/RAM and disk capacity for Windows plus an owned 512 MiB file fixture, temporary stages and journal |
| Reversibility | Verified original image/backup and recovery procedure controlled from outside the guest |
| Host control | Independent host-side boot/stop/restart authority for only the disposable test VM |
| Provenance | Recorded exact flyExplorer Git SHA, Windows build, filesystem, disk identity and test-run UUID |
| Baseline | Pre-test SHA-256 of source/sentinel and off-guest copy of the test manifest |
| Verification | Post-boot **read-only** exact receipt/stage/target inspection, with immutable marker and FileIdInfo comparison |
| Approval | Separate confirmation identifying exact disposable VM and disk before any reset, reboot or power-loss simulation |

If a gate is absent, the verdict is **NOT READY**, not a PASS.
A new virtual disk file alone inside the shared VM is insufficient:
interrupting the shared guest would still disrupt central CI.

## Test ordering once an isolated VM is approved

1. Establish a baseline with a unique test-owned source, empty file,
   final destination, protected receipt folder and unrelated sentinel.
2. First test normal independent verifier-process restart.
3. Next test a **normal OS restart of the disposable guest only**.
4. Only after host backup and exact VM/disk identification, evaluate
   abnormal interruption at distinct stage-copy and published-marker
   boundaries, one fresh test root at a time.
5. After resuming, compare source/target/sentinel hashes and the
   recorded FileIdInfo and phase state: `CopyingOrInterrupted`,
   `CompletedOnStage`, `PublicationUnconfirmed`,
   `PublishedVerified`, `Inconsistent`, or `Invalid`.
6. Treat an unobserved interruption window as `INCONCLUSIVE`.
   Never auto-publish, sweep directories or delete ambiguous stages.

The existing
[65/65 Release Move/Copy native run](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38140715382),
[real-user WinUI/IPC run](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38139086195),
and [worker-kill/read-only inspector run](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38139795233)
are independently verified, but are **not** physical power-loss
or whole-OS reboot acceptance.

Related: `docs/development/STAGED_COPY_RECOVERY.md`.
