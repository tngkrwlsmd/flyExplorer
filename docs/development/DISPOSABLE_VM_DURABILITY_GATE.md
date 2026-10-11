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
