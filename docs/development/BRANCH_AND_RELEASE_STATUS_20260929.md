# Current branch, product and evidence map - 2026-09-29

This is the current **branch/release readiness snapshot**. The hashes below identify last independently tested **code-bearing** revisions immediately before this documentation-only sync, **not** a promise that the documentation-only Git tip retains those exact hashes. Older detailed files preserve their original revision-scoped results. Verify live Git refs for any later changes.

## Two active branches and two worktrees

| Branch | Last independently tested code commit (pre-doc sync) | Responsibility |
| --- | --- | --- |
| `main` | `f074a6b1651dae6e9a1603465078310822a8f761` | Current native MFC product, now containing UXH-07 named workspaces, UXH-06 explicitly opt-in recent search locations and the existing ModernUI dark native scrollbar solution for UI-02. Local and origin match. |
| `migration/winui3-full-shell-20260929` | `eb7ee1a335484d88128bfcf117a4f857fbee4c60` | Separate experimental WinUI 3 preview (M1.8). Local and origin match. Not the default product and not source-reconciled with the newer mainline features. |

The associated worktrees are `C:\dev\flyExplorer` and `C:\dev\flyExplorer-winui3-migration`. Original user-owned `C:\dev\flyExplorer\main-window.png` remains **untracked and untouched**: `main` has clean tracked files but not an entirely empty `git status`. No other local or remote branches were present at this snapshot.

The old UXH-07, UXH-06 and UI-02 feature branch names and the obsolete Phase 4 experiment name were removed only after integration or explicit supersession. The old remote UXH-07 and Phase 5 branch names were also removed. Historical commits are protected by local refs under `refs/archive/merge-20260929/` and `refs/archive/cleanup-20260929/`. These archive refs are **not active branches**; preserve them for rollback and audit. Old UI-02's separate `DarkScrollbarLayer` was **not** installed as a competing renderer.

## Native main product: actual rebuilt root checkout

After the two accepted feature merges, the actual original `C:\dev\flyExplorer` root checkout was freshly rebuilt at `f074a6b`. Canonical `local_ci.bat x64` exit 0: Release x64 PASS, **17 native tests passed and 0 failed**, overall **PASS WITH SKIPS** (standard HKCU runtime smoke deliberately skipped to protect the existing user profile). Rebuilt original-root executable SHA256: `41D51B87E74C839C33124F22F63AC0C7379B61E0F32A12196D1459649AF81BAC`. `bin/x64/build-revision.txt` matched `f074a6b`.

On that newly rebuilt root executable, combined native feature/UI source contracts **25/25 PASS**; owned GUI verified UXH-06 long scope preview, opt-in recent persistence, normal restart, restoration, clear, opt-out remaining empty; separate owned UI-02 **Dark** list and tree horizontal/vertical mouse scrolling and native thumb drag PASS. Before temporary worktree deletion, a separate compiled UXH-06/UI-02 integration candidate passed additional actual **Light and Dark** primary and modal native-scroll GUI. Its DIFFERENT, valid compiled EXE SHA256 was `1EDC8616E732B4E5DB277773A6D57D071960B2C74B2786EB5F01DB6778AFC8EE`. Never confuse the two build hashes. The original six actual user settings remained hash-identical across all owned tests, as did the untracked original screenshot.

Local, ignored evidence was copied **before** removing the temporary test worktree to `C:\dev\flyExplorer\logs\merge-20260929\accepted-uxh06-ui02-20260929\`. Main-root proof: `main-f074a6b-final-canonical-x64-local-ci.log`, `main-root-postbuild-25-focused-contracts.log`, `main-root-postbuild-uxh06-owned-gui.log` and `main-root-postbuild-ui02-dark-owned-gui.log`. Additional retained Light/Dark primary/modal GUI logs, original UXH-06 opt-out proof and compiled executables belong to their specifically tested revisions. Details: [UXH-06 acceptance](UXH06_MAIN_MERGE_ACCEPTANCE_20260929.md), [UI-02 superseding merge](UI02_SUPERSEDED_MERGE_ACCEPTANCE_20260929.md), [UXH-07 previous acceptance](UXH07_PUSH_VERIFICATION_20260929.md).

## WinUI 3 M1.8: independent experiment, not main feature parity

The separate migration tip `eb7ee1a` passed paired Debug/Release x64 and actual owned GUI for test-only blocking COM call recovery, BOTH exhausted 4.5s retries, invalid **loopback-only** UNC, isolated helper/private Windows Job protocol, standalone filesystem watcher and owned local Shell namespace event; focused architecture source tests **14/14 PASS**. These do **not** prove actual faulty installed third-party Shell extension safety, actual remote SMB failure, or an actual dynamic external virtual namespace provider event. The M1.8 worktree remains separate and **does not incorporate the latest UXH-07/UXH-06/UI-02 mainline code**, so do not claim its workspace/search product feature parity. Its unchanged local evidence is `C:\dev\flyExplorer-winui3-migration\logs\m18\evidence-manifest.json`, detailed in the migration branch's `docs/development/WINUI3_M18_SHELL_STABILITY_20260929.md`.

## Remaining work, not newly certified by documentation cleanup

- Real physical 125/150/200% DPI, native OS High Contrast, Narrator and installed Korean-pack testing for native GUI. The protected live-user HKCU smoke remains **SKIPPED**, not PASS.
- Explicit WinUI **feature-contract reconciliation** with the currently accepted main UXH-07 named workspaces, UXH-06 opt-in search-scope behavior and MFC/native view parity. Treat the future main/migration Git merge as a separately planned, built and GUI-tested code change; neither branch should be silently replaced.
- Only in authorized disposable environments, test truly faulty third-party Shell extensions, slow/offline authenticated network SMB shares and genuine third-party/OS virtual Shell events. Preserve user settings and original runtime.

A documentation-only commit is **not** a new native build, production release, or WinUI parity certification.
