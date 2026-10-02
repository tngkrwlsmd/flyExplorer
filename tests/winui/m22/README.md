# Native Shell file-operation fixture

The m22 directory name is retained for compatibility. This fixture validates
current UI-independent Shell/file-operation behavior against disposable
test-owned folders.

It covers guarded copy/move/recycle-related contracts, multi-selection and
collision/cancel behavior without treating test cancellation as proof of every
real OS integration case.

The ordinary automated path must not alter the user's global clipboard or
arbitrary user files. Use the canonical source/full orchestration.
