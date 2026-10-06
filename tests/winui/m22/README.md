# Native Shell file-operation fixture

The m22 directory name is retained for compatibility. This fixture validates
current UI-independent Shell/file-operation behavior against disposable
test-owned folders.

It covers guarded copy/move/recycle-related contracts, multi-selection and
collision/cancel behavior. Drive-policy contracts explicitly allow Copy/Move
on fixed and removable local volumes while keeping Recycle fixed-only and
remote/network roots closed. The fixture can prove the drive-type policy
without attached removable hardware; real removable-media execution still
requires an owned USB/removable test volume.

The ordinary automated path must not alter the user's global clipboard or
arbitrary user files. Use the canonical source/full orchestration.
