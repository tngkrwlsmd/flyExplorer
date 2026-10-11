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
and only with a no-replace same-directory `MoveFileExW`. For non-journaled operations, normal error or cancellation retains the
pre-existing best-effort exact-stage deletion. When protected journaling
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
Failure to bind/write/read, cancellation, or a callback never occurring
when journaling is required means **no publish** and **no by-path cleanup
of the questionable stage**. The native receipt code itself performs no
file deletion, rename or publication. A successful copy keeps an inert
historical receipt; it does not grant future recovery authority.

A valid receipt only proves a correspondence at one point in time, under
the current user's access boundary. The checksum is FNV corruption
detection, **not** malicious-tamper authentication. An attacker running
under the same Windows user can affect this storage; changes to the
destination folder's path or ACL after checks can also race checks.
The same-directory publication remains based on `MoveFileExW`, not on
an exclusively pinned rename-by-handle. No completed/published receipt
state and no fsync guarantee for copied data exist. A force kill before
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

**Unrun gates:** full product WinUI Release and GUI acceptance, actual
helper IPC/known-folder provisioning on an interactive user session,
Python source contracts on the latest branch, completed/published journal
transitions, comprehensive zero-byte and initial-callback crash handling,
replacement/ACL race resistance for publish/cleanup, restart and power
loss. **Draft PR #63 is not merged.**

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

The first version of live helper-bound receipts is now present on draft
PR #63, but not merged; it has no authenticated completion transition,
restart reconciler or user-authorized recoverer. **Product cleanup of
orphan stages remains disabled**, including on a matching receipt.

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
