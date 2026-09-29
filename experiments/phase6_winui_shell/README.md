# WinUI 3 full UI migration — M1.8 isolated Shell stability


**CURRENT branch context:** This is a non-default M1.8 WinUI experimental preview at `eb7ee1a`, not a substitute for the now-merged native product `main` `f074a6b` (UXH-07 named workspaces, UXH-06 opt-in recent search locations, current ModernUI UI-02). These codebases are **not source-reconciled**, so neither shared feature parity nor a new combined build is claimed. Branch details and next integration gates: [migration/mainline alignment](../../docs/development/MIGRATION_MAINLINE_ALIGNMENT_20260929.md). Historical M1.8 test evidence below remains exact for this older migration revision.

The preview retains its native two-lane private helper Jobs and independent filesystem watcher. M1.8 adds distinct exhausted-timeout and invalid UNC error messages without discarding the active folder, plus an independent hidden-window Shell notification subscription for selected virtual PIDLs. Actual owned GUI tests passed a test-only blocked COM method, both exhausted retries, an invalid localhost UNC, and a Shell event confined to a synthetic owned folder. Actual external third-party provider and virtual-folder changes remain unverified. See [M1.8 scoped verification](../../docs/development/WINUI3_M18_SHELL_STABILITY_20260929.md).

## Historical M1.7 integration

# WinUI 3 full UI migration — M1.7 actual isolated-process Shell preview

**Latest, revision-scoped:** The real WinUI navigation path now uses a native **two-lane C++ supervisor**, one test-preview-owned read-only Shell child per active-pane request (at most two simultaneous children), with bounded timeout/private Windows Job termination and one restart. A standalone **COM-free Win32 watcher thread** handles selected filesystem-pane changes independently of hung Shell helpers; paths are computed in the child, never by UI-thread SHGetPathFromIDListEx. The Debug GUI successfully tested a blocked owned LEFT child while RIGHT continued and LEFT recovered; ordinary Release GUI and native create/delete watching passed, unchanged six user hashes, static 12/12. This preview is still not the default MFC product and is not a restricted-token security sandbox. [M1.7 verification and known limits](../../docs/development/WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md).

## Historical M1.5 design and tests (the old in-process worker is no longer linked to this preview)

This is an independent **local, non-default** C++/WinRT executable in the separate migration worktree. The existing MFC product remains the safe fallback, and advanced file mutations are not enabled here.

## Native components already connected

- `src/base/shell_navigation_core.h/.cpp`: real Windows Shell absolute PIDL snapshots, virtual parsing names and transactional per-tab navigation history. The old MFC ExplorerCtrl retains its higher-level GUI/controller.
- `src/base/shell_enum_bridge.cpp`: shared low-level native Shell enumeration entry used by the old MFC ShellEnumerator and this independent WinUI preview.
- `src/base/directory_change_bridge.h/.cpp`: new MFC-free Unicode/ANSI Win32 directory watch primitives, reused by the old MFC FileChangeWatcher and this preview.
- `src/base/shell_async_worker.h/.cpp`: private COM STA, message pump, serialized Shell requests, request/route cancellation, native filesystem invalidation and nonblocking UI teardown.

Real WinUI 3 TabView/ListView panes now queue their Shell work away from the XAML UI thread. Owned native snapshots are delivered via the WinUI DispatcherQueue through weak window references. Each tab retains independent history; changing a synthetic file in the selected filesystem folder triggers asynchronous refresh. Actual Windows Shell virtual folders can be navigated but their change notifications are not yet implemented.

The old, UI-independent `fxfile::fileop::execute` is linked only for its safe invalid-null contract. Copy/move/delete are deliberately not exposed.

## Local build and tests

Run `build.cmd Debug` or `build.cmd Release` in this directory. Generated projects and x64 artifacts remain ignored and confined to the separate migration worktree. No local installer or system/user setting is changed.

Run `python -m unittest test_arch_contract.py` for focused shared-core and no-MFC source checks; run `python test_shell_gui.py` for actual test-owned UIA and physical input GUI acceptance. Set `FLY_MIGRATION_CONFIGURATION=Release` in the current process to test the Release EXE. The GUI harness checks the foreground process owns the WinUI window before each actual pointer/keyboard action; if it cannot safely acquire focus, it must abort rather than click a user's existing window.

`python test_legacy_enum_gui.py` independently starts the compiled original MFC program with private config and synthetic folders and proves its real Go Up / Back / Forward route. The local `local_ci.bat x64` in the migration worktree checks native Release x64 plus the expanded regression suite. It may SKIP the normal runtime smoke to preserve existing user HKCU; do not claim smoke PASS when that happens.

## Incomplete and unsafe for production

A hostile third-party Shell extension can still block the **single worker STA** in one `EnumObjects` or `Next`. Newer route cancellation discards obsolete results but cannot interrupt an already-running COM call; detached shutdown only prevents UI window closure from synchronously waiting, not worker resource leakage until the blocked call finishes or the process exits. Dedicated process isolation or timeout recovery is still needed for a production guarantee.

Only selected filesystem folders get native auto-change watches (up to two). The old advanced watcher and CWnd ShellChangeNotify, virtual Shell change events, sorting/metadata/thumbnails, native file operations, named workspace settings parity, IME, actual alternate DPI/high contrast, screen reader and clean-machine installer require later integration and tests.

Exact M1.5 source/build/GUI acceptance, known limitations, log paths and first Release pointer-test diagnosis: `docs/development/WINUI3_ASYNC_SHELL_CHANGE_WORKER_20260929.md`. Do not ship this preview as the default file manager or run hosted CI without an explicit per-run approval.

## M1.6 bounded process-helper experiment (not yet wired to this GUI)

The risk audit identified one serialized in-process Shell STA serving **both** panes plus filesystem watches; a genuinely stuck Shell COM call defeats cooperative cancellation. A **separate read-only native process helper** and test-owned Windows Job-object watchdog are now implemented under `isolation/`. That helper's Debug/Release x64 builds and direct two-process Windows tests passed local and virtual Shell enumeration, strict IPC/PIDL decoding, independent helper progress when the other is artificially blocked, targeted termination/restart and automatic private-job close reclamation.

This **does not** change the runtime `MainWindow`: it still uses `AsyncShellWorker`. Do not report process isolation or true third-party Shell extension recovery in the GUI until a new native per-pane supervisor and owned WinUI GUI regression are implemented and verified. Run `python -m unittest isolation/test_contract.py` for isolated source checks and see `isolation/README.md` and `docs/development/WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md` for exact test commands, risks and boundaries.
