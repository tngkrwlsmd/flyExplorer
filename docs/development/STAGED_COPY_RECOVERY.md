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
and only with a no-replace same-directory `MoveFileExW`. Normal error or
cancellation best-effort deletes the current request's exact stage path.
A force-killed process can strand the stage. **The stage filename pattern,
a GUID, last-modified timestamp or ownership SID alone is not proof of
exclusive stage ownership.** Never scan and purge matching names.

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

There is **no durable receipt implementation today**. Therefore product
cleanup of orphan stages is disabled and remains an open gate.

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
