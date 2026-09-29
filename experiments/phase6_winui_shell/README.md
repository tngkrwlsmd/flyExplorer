# WinUI 3 full UI migration — M1.5 native async Shell preview

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
