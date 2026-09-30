# WinUI 3 main-branch cutover (2026-09-30)

## Owner decision

On 2026-09-30 the owner explicitly directed that the new WinUI 3 implementation become `main` now and that the duplicate local migration worktree be retired. This is an explicit override of the earlier staged-cutover rule that kept the native MFC branch as the default until every release gate was complete.

The override changes **branch/worktree ownership now**. It does not silently turn unverified release gates into PASS.

## Git lineage

- Previous native-MFC `main` tip: `cbffb487635a94e625070d5bee9d5e6680006f12`.
- Accepted WinUI M2.6 tip before cutover: `3476ecd863b289244a06159fa59d719e9a48d49a`.
- A no-tree-change lineage merge `d754384bd18de9f310991dad995eb4b018767501` records the previous `main` as a parent while keeping the verified WinUI tree as the resulting tree.
- The local `main` worktree was then fast-forwarded to that lineage merge before this cutover-status update.

This keeps the old native `main` commit reachable in normal Git history without reviving its stale tree as the new default.

## Active local layout

After final validation and remote publication:

- canonical worktree: `C:\devlyExplorer`
- canonical branch: `main`
- active WinUI implementation: `experiments/phase6_winui_shell`
- duplicate local worktree `C:\devlyExplorer-winui3-migration` is to be removed
- local migration branch is to be deleted after it is confirmed merged into `main`

The `experiments/phase6_winui_shell` path is now a historical source-layout name, not evidence that the implementation is non-main. A later source-layout refactor may move it, but branch cutover does not combine that large path move with the validated M2.6 checkpoint.

The pre-cutover untracked user screenshot `main-window.png` was not deleted. It was moved into ignored local evidence at `logs/preserved-user/main-window-pre-winui-cutover.png` with SHA256 `65A634A3B16696FB1E9AEB3DA21138EF36C7F19FA0DDCFE1BF3F6106F21BC909`.

## What is now authoritative

New UI/product development targets the WinUI 3 implementation on `main`. The old MFC UI remains only as legacy/reference source where still present and must not be treated as the default presentation architecture.

Phase5 remains retired. Do not recreate `phase5_winui3`, `phase5_island_bridge`, `FLYEXP_PHASE5_*` or `FlyExplorerIslandBridge` as production dependencies.

## Remaining release gaps are still real

The owner-authorized branch cutover does not erase these known gaps:

- physical drag remains separately unverified;
- 125/150/200% DPI, High Contrast ON, Narrator and Korean IME composition still require controlled environment/human evidence;
- legacy `dist/copy.bat` is not a WinUI production installer;
- signed clean-machine install/update/rollback/default-product deployment is not certified;
- arbitrary third-party Shell verb execution remains outside the accepted automated scope.

Until those are implemented and verified, describe `main` as the canonical WinUI development/product branch, not as a fully release-certified installer.

## Validation rule for this cutover

Before pushing the new `main`, run from `C:\devlyExplorer`:

1. official source preflight + full scoped source contracts;
2. x64 Debug and Release WinUI builds;
3. full owned Debug and Release GUI regression including compact layout and six-config hash protection;
4. Git diff/status verification.

After publication, verify remote `main` equals local `main`. Only then remove the duplicate local migration worktree/branch.

## Actual cutover validation from canonical main worktree

All final acceptance commands below ran from `C:\devlyExplorer` while checked out on local `main`, after the WinUI tree had replaced the previous native-default tree.

- official source preflight: PASS
- final source contracts: **141 run, OK, 1 environmental skip**
  - `logs/winui-scoped/20260930-171028-source.log`
- fresh x64 Debug build from the canonical main path: PASS, 106.2 sec
  - `logs/winui-scoped/20260930-165946-build-Debug.log`
- fresh x64 Release build from the canonical main path: PASS, 97.7 sec
  - `logs/winui-scoped/20260930-170133-build-Release.log`
- final full owned Debug GUI + compact boundary: PASS, 70.1 sec
  - `logs/winui-scoped/20260930-170620-gui-Debug.log`
- final full owned Release GUI + compact boundary: PASS, 69.5 sec
  - `logs/winui-scoped/20260930-171246-gui-Release.log`
- the six original MFC user-config SHA256 values remained identical in the final Debug and Release GUI runs.

The build timings are observations from this workstation after moving the canonical worktree, not performance targets.

## Cutover-time failures retained as evidence

Three failures occurred while validating the relocated canonical main worktree and are not hidden by the final PASS:

1. The first source run failed because an M1.9 architecture contract still asserted that `main` could only be the old native tip. The contract now verifies that both the last native-default `cbffb48` and accepted WinUI M2.6 `3476ecd` are ancestors of canonical `main`.
2. The first full Debug GUI run timed out waiting for an exact-owned M2.3 restart child to expose both restored panes. No product or profile data changed; the complete Debug run passed on the next attempt with no product-code change. A single root cause was not proven.
3. One Release run observed the previous successful rename Refresh landing after the duplicate-create command and replacing the short-lived duplicate error status. The owned harness now waits for that exact prior Refresh to settle before issuing the duplicate command, while retaining the actual no-overwrite filesystem assertion. A subsequent Release run then observed one exact-owned theme-restart child exit with `3221226107` after it had already displayed the expected restored Dark theme; this did not reproduce on the final full Release run and no product-code change was made for that shutdown anomaly.

These observations do not change the known external release gaps listed above.
