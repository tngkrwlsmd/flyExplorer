# Staged Copy interruption and orphan recovery safety contract

**Status:** fail-closed production policy; **no automatic orphan removal**.
Product implementation: `src/base/shell_transfer_core.cpp`. Windows
verification: test-owned native fixture `tests/winui/m22/test_native.py`.
This document describes a future *opt-in* product recovery feature and the
safety guarantees currently established. It does **not** authorize cleaning
arbitrary filesystem folders.

## Current invariant

For fixed-drive regular-file Copy with `Collision::Reject`, the helper writes
`.flyExplorer-copy-{GUID}.partial` into the destination directory. The
requested filename is published only after a successful full `CopyFileExW`
using an explicitly **no-replace** same-directory operation.
The legacy non-journalled path uses `MoveFileExW`; the private-receipt
path now pins the source file HANDLE and uses Win32 `FileRenameInfo`
with an absolute destination name. For non-journalled operations,
normal error or cancellation retains the pre-existing best-effort
exact-stage deletion. When protected journaling
is enabled, failed/cancelled stages instead remain untouched for human
inspection; no automatic orphan scan or deletion is enabled.
A force-killed process can strand the stage, with or without a receipt. **The stage filename pattern,
a GUID, last-modified timestamp or ownership SID alone is not proof of
exclusive stage ownership.** Never scan and purge matching names.

## Read-only exact-stage identity inspection (2026-10-11)

`inspectStageFile(exactPath, identity)` in
`src/base/shell_transfer_core.cpp` examines **only** the specifically
supplied staged-Copy pathname. It does not enumerate directories, modify
attributes, rename or delete anything. It fails closed unless the path is
lexically normalized and on an existing fixed-drive folder without junction/
symlink components, the leaf has the exact staged-Copy GUID shape, and a
`FILE_FLAG_OPEN_REPARSE_POINT` handle identifies a regular single-link file.
The resulting `StageFileIdentity` records the OS `FileIdInfo` volume serial
and 128-bit file ID; `sameStageFile` rejects default/unobserved IDs and
compares exact recorded identities.

The owned Windows Release regression
[run #38120473011](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38120473011)
on source `e8870beada07ad9bf43a80f299a7aa189333e16f`
passed 44 native cases and source contracts, including stable file-ID
comparison, hardlink refusal, replacement of the file behind an unchanged
path, and malformed/un-normalized path refusal. Legacy profile sentinels
remained unchanged.

This API supplies **read-only evidence**, not durable provenance. In
particular a newly created unrelated file can have a plausible stage name
and a valid file ID. A successful inspection alone MUST NEVER trigger
unattended deletion, publication, or recovery. A future feature needs the
private durable receipt and explicit user authorization described below,
with any destructive action targeting the verified open file object rather
than a path subject to replacement.

## Live helper-bound durable receipt — draft, no cleanup (2026-10-11)

PR [#63](https://github.com/tngkrwlsmd/flyExplorer/pull/63) now includes
both the isolated `stage_receipt_core.{h,cpp}` storage primitive and
an **opt-in, process-local binding** from `copyStagedFiles` into a real
`CopyFileExW` progress callback. This is not a restore or cleanup feature.

The isolated Shell helper chooses its own user-scoped Windows
`FOLDERID_LocalAppData` path:
`flyExplorer-transfer-receipts-v1`. It creates only a missing, exact
directory under that Known Folder with an owner-only protected DACL, or
verifies an already-private directory; an unsafe pre-existing folder is
not modified. No client/user-input path enters the helper wire request.
If provisioning is unavailable, the helper deliberately falls back to
the older staged Copy with **no receipt**. Native fixtures configure an
explicit private directory **only inside their disposable test root**.

On the first callback, the writer compares the actual CopyFileEx target
HANDLE's `FileIdInfo` to a separate open-reparse-point exact-stage
inspection. It writes one bounded versioned binary record with
`CREATE_NEW`, `FILE_FLAG_WRITE_THROUGH` and `FlushFileBuffers`.
The record contains the stage's exact path, intended target leaf, volume
serial, 128-bit file ID, creator PID and kernel process start time.
A subsequent read and identity revalidation gate final-name publication.
Failure to bind/write/read or cancellation when journaling is required
means **no publish** and **no by-path cleanup of the questionable stage**.
A completed zero-byte copy with no callback may now bind an exact
stage HANDLE before completion and publication markers are written. The native receipt code itself performs no
file deletion, rename or publication. A successful copy keeps an inert
historical receipt; it does not grant future recovery authority.

A valid receipt only proves a correspondence at one point in time, under
the current user's access boundary. The checksum is FNV corruption
detection, **not** malicious-tamper authentication. An attacker running
under the same Windows user can affect this storage; changes to the
destination folder's path or ACL after checks can also race checks.
The original staged Copy path used `MoveFileExW`; the journalled path
now uses a source-file-ID-verified handle through the rename as described
below. The newer append-only transition records distinguish completion
and publication, but they do not fsync copied bytes, authenticate stage
content or eliminate destination pathname resolution races. A force kill before
the first callback can leave an unrecorded stage; no code may infer its
provenance based on the GUID name or search-and-delete such files.

Read-only `inspectReceiptCreator` compares the PID **and** kernel
process creation time and returns Running, Exited or Unknown.
A reused, inaccessible or no-longer-openable PID gives Unknown,
which is *not* permission to delete. Even Exited does not itself
authorize file operations; the worker's complete request lifecycle is
not durably recorded.

### Windows verification (exact SHA scoped)

- [#38122600482](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38122600482):
  initial standalone receipt native **48/48**.
- [#38125429517](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38125429517):
  protected ACL and creator-state native **52/52** on
  `050ab1a85d52859fcdd7f5ad92e18f5a96d519cb`.
- [#38127271345](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38127271345):
  production isolated Shell helper **Release build PASS** and native
  53/54, with one test fixture incorrectly pre-populating the target.
- [#38127383070](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38127383070):
  on `2597cc7f29ec5786f11c22038621e745302fd4d4`,
  Windows Release native **54/54** including actual live bound
  CopyFileEx receipt-before-publication and private-store rejection.
- [#38127536317](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38127536317):
  on `7d503803ee7af379c781a6f15e03afdcfca48c94`,
  test-owned 512 MiB **active copy forced kill**: journal and stage
  identity matched after termination, owning worker was not Running,
  source SHA-256 and an unrelated partial were unchanged, and no
  truncated final target appeared. The exact stage was **not** deleted.

**At the earlier isolated native checkpoint:** full WinUI Release
build, real helper IPC and Python source contracts still needed independent
verification. Those three scoped gates are now covered in the newer section
below. Interactive *shipping-helper* Known Folder behavior, GUI, initial
pre-callback crash handling, replacement/ACL races, restart reconciliation
and power-loss safety remain untested. **Draft PR #63 is not merged.**

## Immutable phase records and cross-process read-only inspection

In the newer draft PR #63 implementation, the helper creates two
separate immutable phase files derived from one known private receipt path:
`<receipt>.complete` and `<receipt>.published`. Both use `CREATE_NEW`,
write-through and `FlushFileBuffers`, then require successful readback,
correct phase, exact original stage FileIdInfo/volume and creator PID/start
timestamp. An existing, invalid or partially written phase record cannot
be overwritten or used as proof.

**Copy completion:** the `.complete` marker is attempted only after
`CopyFileExW` reports completion and cancellation is not observed.
Failure or a corrupt marker prevents publishing the requested filename.
For empty copies with no progress callback, a successfully finished stage
is reopened with read-only/no-reparse semantics, tied to its actual
file ID and journaled before completion/publication.

**Publication:** after the complete stage passes identity checks, the
helper now uses the no-replace source-handle `FileRenameInfo` operation
for journalled active copies (legacy non-journalled copies remain on
`MoveFileExW`). A successful rename is followed by read-only revalidation that
the target's FileIdInfo matches the saved stage and the old stage pathname
is absent; only then is the `.published` marker flushed. When marker
writing or verification fails after the rename, the final file is **not
rolled back or deleted**, and the operation reports a metadata error.
Thus a crash in the rename-to-published-marker interval is **ambiguous**,
not interpreted as successful publication.

`inspectStageReceiptState(exactReceiptPath)` reads *only* one explicitly
named receipt, the two associated marker files and the exact stage/target
paths. Its states include CopyingOrInterrupted, CompletedOnStage,
PublicationUnconfirmed, PublishedVerified, Invalid and Inconsistent.
Missing, corrupt or mismatched phases and target replacements never
grant deletion, restoration or publish authority. The inspector neither
enumerates directories nor opens files with write/delete access; it can
run in a **different process** from the original transfer. This is
snapshot evidence, not a background restart service.

On exact source `d27854627b47fda529edf174e4bd1a5d5c1a010d`,
[Windows Remote Shell #38128693863](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38128693863)
passed Release M22 native **61/61**, the isolated Shell helper Release
build, whitespace preflight, six standalone phase-state regressions,
a real 0-byte staged copy with both markers, and **3/3** independent
new-process read-only inspections (two real published-copy receipts and
one intentionally damaged/inconsistent record). Original actual owned
active-copy forced termination and source-hash preservation were proven
separately on the preceding code in
[run #38127536317](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38127536317).

**Remaining safety limits:** A malicious process with the same owner SID
can forge an unsigned checksum; read-only FileIdInfo snapshots do not
pin the identity through arbitrary future renames; no stage-content
hash, durable directory flush guarantee, power-loss proof, user-facing
recovery consent or safe cleanup operation exists. A kill before the
first receipt still leaves an unowned-by-evidence stage. No automatic
recovery or cleanup was added.

## Canonical product build and owned real helper IPC — no profile mutation

The draft PR's completed/posted journal is now exercised through actual
parent/child transfer pipes and its production WinUI Release build:

- [Remote Shell #38129284452](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38129284452)
  on exact `404a7450943476a5b23320211e7b4bd9d7b425c2`:
  original `build.bat Release` and sibling shipping helper presence
  **PASS**, focused source contracts **15/15 PASS**. An already installed
  Python interpreter was added **only to this child process's PATH**,
  not installed or configured machine-wide.
- [Remote Shell #38129563278](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38129563278)
  on `f50e17a659d238310758c53464cc9fb0453aeb1f`:
  independent native fixture and explicit test-only isolated helper both
  compiled. Real `executeIsolated` pipes and a real child process copied
  a Korean-named 8 MiB file and a 0-byte file, reporting byte-for-byte
  equality and full phase/receipt `PublishedVerified` state for each;
  focused source contracts **15/15 PASS**.
- [Remote Shell #38129744148](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38129744148)
  on `b302ab7f6d566e642d1679399a9a492f43f061a0`:
  unsafe inherited-ACL receipt store was rejected across child-process
  IPC (reported error 31), test source SHA-256 and empty target remained
  unchanged; source contracts **15/15 PASS**, new native fixture Release
  compilation and original `build.bat Release` **PASS** again.

The IPC fixture deliberately uses a **different, explicitly opted-in
test-only helper build**. A compile guard
`FLY_M22_TEST_ISOLATED_RECEIPT_STORE`, activated only by
`/p:FlyM22OwnedHelper=true`, permits its child process to consume
`FLY_M22_OWNED_RECEIPT_STORE` after strict owner-only private-DACL
validation. This never enters production request serialization. Normal
`app/winui/helper/build.cmd` and `build.bat Release` do **not** set the
fixture property, and the production helper continues to resolve its
own protected `FOLDERID_LocalAppData` directory. The fixture prevents
experiments from writing to the SYSTEM profile or real user folders.
Production Known Folder behavior in a *logged-in interactive user
session* is **not** established by this fixture.

No test scanned or deleted orphan stages or changed user settings.
No automatic cleanup, final-name restoration or auto-reconciliation
authorization is implied. Production GUI integration, user-profile
provisioning, publisher races, true power-loss durability and an
explicitly consented recovery UI remain open.

## Source HANDLE-verified publication — absolute target remains a race

The newest draft PR #63 active-worker implementation uses an exact,
still-open stage file HANDLE with `DELETE|FILE_READ_ATTRIBUTES`,
`FILE_FLAG_OPEN_REPARSE_POINT`, one hard link, and an exact OS
`FileIdInfo` match to the previously flushed ownership receipt. It
also opens the destination directory and confirms the resolved location
and expected volume. The critical source file **object** is held through
`SetFileInformationByHandle(FileRenameInfo)` with
`ReplaceIfExists=FALSE` and an explicit no-overwrite requirement.
This function is part of the synchronous active transfer only: no
published/complete/expired receipt allows a post-crash file operation.

Windows' documented `FILE_RENAME_INFO` supports describing an output
relative to `RootDirectory`, but the VM's Win32 API rejected that
combination with `ERROR_INVALID_PARAMETER (87)` on the initial attempt.
We instead use `RootDirectory=NULL` and a full, normalized destination
pathname. This is a supported Win32 call, but **it does not use
the opened directory HANDLE as the rename root**. The subsequent
active-worker ancestor sharing guard below has been experimentally
shown to block ordinary target-parent and ancestor renames during this
window. Privileged, unusual filesystem, mounted-volume and
reparse/namespace races remain unproven. A source HANDLE match prevents
renaming the wrong source file; it does **not** by itself certify where
an absolute destination pathname will resolve. Do not market this as
fully race-safe.

[Windows Remote Shell #38131991165](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38131991165)
on exact `10204fcab9b1e82c52d9377bbef74fe60e33cdd1`:
Release native M22 **61/61** passed after the change. A test-owned
512 MiB copy was still writing its stage when an unrelated same-name
target was created; after `FileRenameInfo` returned
`ERROR_ALREADY_EXISTS (183)`, the source SHA-256 and original target
bytes remained identical, and the complete but unpublished stage retained
its exact receipt. No orphan cleanup was run.

[Windows Remote Shell #38132115933](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38132115933)
on the **same source** passed focused source contracts **15/15**,
actual child-helper IPC for a Korean-named 8 MiB source and an empty
source (both bytes and `PublishedVerified` receipt state matched),
separate IPC rejection of an inherited-ACL journal store (error 31),
and the canonical WinUI `build.bat Release` with the shipping Shell
helper present. All IPC test records were confined to disposable owned
folders with a special **test-only** helper build. Interactive user
Known Folder, actual GUI acceptance, power loss, historical record
retention and full destination path-race protection are **not tested**.

## Active publication pinned ancestor sharing gate (2026-10-11)

The draft active-worker file-handle rename still gives Win32 an absolute
destination pathname rather than a directory-relative rename via a trusted
root handle. **Before attempting that rename**, the worker now opens
**every existing ancestor directory from the fixed drive root to the exact
destination parent**. Each handle requires actual
`FILE_LIST_DIRECTORY|FILE_READ_ATTRIBUTES` access, allows normal
FILE_SHARE_READ/FILE_SHARE_WRITE but *not* FILE_SHARE_DELETE, and remains
open until after the no-replace rename. Each resolved canonical DOS path
must match the expected lexically normalized path; direct reparse points
and a changed/non-directory path fail closed. This decreases the interval
in which an ordinary competing rename of an ancestor can redirect
absolute target resolution. If a pin cannot be established, the stage
is not published and is not automatically removed.

**Regression that changed the design:** `FILE_READ_ATTRIBUTES` alone
does not reliably stop directory renaming on the actual Windows VM;
a deterministic test-owned callback demonstrated the rename succeeding
even while that metadata-only handle was open. Replacing it with
`FILE_LIST_DIRECTORY|FILE_READ_ATTRIBUTES` caused the exact folder
and its immediate ancestor rename attempts to fail with Win32
`ERROR_SHARING_VIOLATION (32)`, although the two folders were
renameable before acquiring the pinned handles. The test-only callback
is compiled solely into M22 through
`FLY_M22_TEST_DIRECTORY_RENAME_LOCK`, not the shipping app/helper.
Windows `GetFinalPathNameByHandleW` buffer-capacity vs returned-string
length is handled separately; the required length can include the
terminating NUL even though the successful returned string count does not.

On exact source `6ae307b815d4874885e1f90c6838ad31ed65377b`,
[Remote Shell #38133470149](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38133470149)
passed native M22 Release **62/62** (including both blocked rename attempts),
focused Python contracts **15/15**, actual child-helper IPC ordinary and
zero-byte `PublishedVerified` copies, strict untrusted-store IPC
rejection, and the original `build.bat Release` app and shipping helper.
No profile mutation or user-file cleanup was undertaken.

**Residual risk and compatibility:** the Windows absolute target remains
re-resolved, so this is an **observed sharing lock, not a formal
directory-anchored atomic rename**. Code running with privileged access,
unusual filesystem and volume/mount behaviors, adversarial ACL changes,
missing `FILE_LIST_DIRECTORY` rights, and unsupported paths may violate
the tested assumptions. The conservative response to denied ancestor
access is to leave an unpublished stage with its receipt and return a
failure, not to silently fall back to weaker publication. The missing
pre-callback record, unsigned journal, reboot/power-loss durability,
user-profile Known Folder and GUI integration gates are unchanged.
No orphan enumeration, cleanup or recovery is permitted.

## Pending real-user GUI + Known Folder acceptance gate (not run)

Draft PR #63 now carries an **explicitly opted-in and still unverified**
interactive user acceptance path:
`tests/winui/test_owned_user_receipt_gui.py`,
M22 `--real-user-shipping-helper-ipc`,
`tools/winui/Invoke-InteractiveReceiptGate.ps1`, and
`tools/winui/OwnedInteractiveReceiptWorker.ps1`.

The test is intended to run as the existing logged-in **non-SYSTEM**
InteractiveToken, with an exact copied shipping WinUI Release binary,
its production Shell helper, and a newly compiled native receipt
inspector. Its only Copy inputs are new, test-owned file paths. It
uses the OS's **real FOLDERID_LocalAppData** rather than an environment
override to test whether the shipping helper creates (if absent)
and later reads an owner-private receipt folder. A unique GUI Copy
is required to produce a new `PublishedVerified` receipt after the
WinUI Copy action, and the direct shipping IPC helper must separately
verify a new exact staged Copy. Older receipt **contents** are not read
or changed, no journal is deleted, and any app-created records remain
inert unless a future user-authorized retention policy is approved.

An owned one-shot InteractiveToken task is intended to be registered
only for the gate and unregistered in `finally`. The bounded runner
copies the exact executable runtime into a new test-owned directory,
requires the source SHA and refuses another checkout, and never
runs as SYSTEM in Session 0. It makes no system-wide preference/ACL
changes except granting the active user access to that newly created
test-owned staging directory.

The Windows VM read-only preflight
[run #38134659901](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38134659901)
found an existing interactive Explorer/login session, but the
workflow failed due to an ancillary command exit status. A subsequent
Remote Shell attempt to build/validate the new gate was **blocked by
the remote tool's safety validation before dispatch**. Therefore no
interactive GUI or Known Folder acceptance has been established for
these new files. Their Python/PowerShell syntax, native fixture
compilation, and test results remain to be checked before use.

Follow-up acceptance should proceed only through an authorized
interactive-user path. The already accepted Windows
[62/62 M22 + Release + isolated test helper IPC](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38133470149)
still applies only to the older SHA in that run, **not** these
new test harness files. Restricted ancestors, force-termination,
OS restart and power-loss integrity remain future, independent
tests; don't simulate an actual machine power cut without separate
authorization and a reversible test environment.

## Minimum provenance before implementing production cleanup

An interrupted operation must have a durable, versioned and private
receipt written and flushed *before* a stage can be treated as recoverable.
Its provenance must bind all of:

- The exact normalized destination parent and stage leaf path, uniquely
  generated operation ID, kind=Copy and intended final leaf name.
- The NTFS volume identity and file identity captured from an open
  no-reparse-point handle. Path spelling and `st_ino` alone are not a
  production-grade identity contract across all supported volumes.
- The initiating app/helper operation identity, creation state and
  published/unpublished transition. Recovery must not race any live worker.
- Receipt file integrity and application-controlled access restrictions.
  Do not accept filenames or metadata supplied by an unrelated process as
  a cleanup authorization.

The draft PR #63 now has persistent completion/publication markers
and a read-only exact-receipt state inspector but no authenticated
completed-file content, unattended restart reconciler or user-authorized
recoverer. **Product cleanup of orphan stages remains disabled**,
including on a matching receipt or published marker.

## Conservative recovery decision

1. Only after user-visible request/authorization for a specific known
   receipt, confirm no owning worker or still-active transfer is using it.
2. Open the exact stage with open-reparse-point semantics and inspect
   final-path identity, same volume/file ID, file type and hard-link count.
   Reject changed identities, reparse points, hard links, directories,
   unexpected destination location and any permission/read failure.
3. A complete staged file is *not* assumed publishable solely from length
   or matching names. Without verified source content and completion
   state, do not rename it into the requested final name.
4. On a mismatch, ambiguous state, active handle or failed cleanup, keep
   the file unchanged and report it for manual review. Never fall back to
   deleting by glob, modified timestamp or directory-wide recursion.
5. Actual removal requires a separately approved exact-file operation;
   record its outcome. Do not touch unrelated files, legacy MFC profiles,
   global Recycle Bin or clipboard.

## Test-owned proof and remaining limits

Windows [run 38119379826](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38119379826)
proved a **test-only** workflow: kill only a spawned copy fixture after an
active stage was observed; compare its exact known stage path and
(`st_dev`, `st_ino`) before/after; reject symlink/multiple hard links;
delete the one observed stage in a disposable test root while preserving
a same-pattern unrelated file. The fixture is not the production
recoverer and uses its test-owned root as a trusted boundary.

Windows [run 38119197158](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38119197158)
confirmed a destination ACL mutation after writes began, recursive
folder Copy locked-child failure and preflight cancellation. Existing
Windows Shell Move and directory Copy use different non-transactional
paths. No cross-item rollback is implied.

**Open gates:** durable receipt format/flush/cleanup under crash-restart;
safe explicit recovery UI; process liveness/handle and volume identity
validation; reparse/hardlink/race resistance; Windows restart/power
failure; cross-volume/USB/SMB and arbitrary Shell providers. The
production acceptance bar remains CLOSED until an isolated implementation
and real owned Windows fault-injection tests pass.
