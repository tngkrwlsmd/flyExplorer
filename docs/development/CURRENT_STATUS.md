# flyExplorer current status — 2026-10-02

## Product source of truth

main is the canonical C++/WinRT WinUI 3 product. Product code lives in
app/winui, UI-independent native code in src/base, tests in tests/winui, and
bounded orchestration in tools/winui/run_checks.py. The former MFC application
is retired from the working tree and is recoverable from Git revision cbffb48.

The current product architecture includes V8-A WindowWorkspaceController and
V8-B SessionCoordinator extraction. Live Git refs always take precedence over
recorded checkpoints.

## Accepted current behavior

- Windows 11-style WinUI 3 shell with custom title bar/Mica, navigation,
  address/search, command bar, status surface and independent dual panes.
- Functional top-level Window Tabs plus per-pane folder tabs.
- V8-A extracts live WindowTab/Pane/PaneTab state-transition ownership into the
  UI-independent WindowWorkspaceController under app/winui; MainWindow keeps
  XAML presentation plus Shell/watcher side effects.
- V8-B extracts private-session capture/save/load/restore/clear generation and
  close invalidation into the UI-independent SessionCoordinator under app/winui.
  MainWindow now keeps only session-related XAML projection, status and
  Shell/watcher side effects.
- Ctrl+T, Ctrl+W, Ctrl+Tab and Ctrl+Shift+Tab Window Tab behavior.
- Details, List, Small Icons and Medium Icons views.
- Back/Forward/Up, filtering/sorting, local create/rename, guarded copy/move/
  recycle flows, Windows clipboard/context integration, isolated Shell visuals
  and directory/Shell namespace watching.
- Private session schema v2 persists/restores the active Window Tab, per-tab
  split state/ratio and active pane, both panes' tabs, selected tabs,
  view/sort/name-column state and bounded filesystem Back/Forward history.
  Legacy session v1 remains readable.
- ko-KR is the default app-owned UI language.

## Shell and shutdown safety

Potentially blocking Shell/provider work must not execute synchronously on the
XAML UI thread. FlyShellIsolationHelper.exe and bounded native worker paths
provide the process/thread fault boundary.

The v7 session acceptance exposed a repeatable close race with
CoreMessagingXP.dll / 0xC000027B and WER 0x800710DD
(ERROR_INVALID_OPERATION). Cancellation/shutdown remains at the window Closed
boundary. V8-B moves session epoch/revision invalidation into
SessionCoordinator::prepareForClose(); detached session workers retain only
shared native generation state and post through a close-safe callback supplied
by MainWindow. Detail-worker cancellation and late DispatcherQueue completion
guards remain unchanged. Accepted GUI evidence requires real process exit code
0.

## Build and test environment

Canonical Windows full builds now have one explicit toolchain contract:
- Visual Studio/MSBuild 18.x;
- MSVC v145 x64 tools;
- Windows SDK 10.0.26100.0.

VS 2022/v143 is not claimed as a supported full-build path. The app, Shell
helper, M19-M23 native fixtures and installer template use v145 consistently.
MSBuild discovery verifies the x64 compiler/toolset/SDK, and the app build
verifies the restored WinUI/XAML assets after NuGet restore.

Direct NuGet references are Microsoft.WindowsAppSDK 2.5.1,
Microsoft.Windows.CppWinRT 2.0.250303.1,
Microsoft.Windows.SDK.BuildTools 10.0.26100.9169 and
Microsoft.Windows.ImplementationLibrary 1.0.260126.7. Actual transitive restore
is verified from project.assets.json rather than inferred from these four
references.

Source-only contracts are suitable for a non-Windows/Python stdlib environment.
Product compilation/execution requires Windows. GUI automation additionally
requires the pinned tests/winui/requirements-gui.txt set and an interactive
Windows desktop. Debug is framework-dependent; Release is self-contained but
still requires its complete sibling runtime/resources.

The previously described external install_script/start_skill cloud bootstrap
files are not present in this repository. This repository therefore documents
the required environment but does not claim to have modified external cloud
bootstrap configuration.

## Latest verified evidence

On code revision `1b504299d1541a599f65419e27ad899098ce4fe5`, validated on 2026-10-02 by self-hosted
Windows remote-task run `37015301375`:
- canonical structure preflight: 4/4 PASS;
- source contracts: 144/144 PASS;
- canonical Debug and Release app builds: PASS;
- actual NuGet restore direct references and WinUI/XAML build assets: PASS;
- M19-M23 native fixtures remain covered by the canonical source/GUI suite;
- owned Debug and Release GUI validation: PASS with
  OWNED_WINUI_SHELL_EXIT 0 and protected legacy configuration hashes identical;
- pinned GUI dependencies pywinauto 0.6.9, Pillow 12.3.0 and psutil 7.2.2:
  validated on the self-hosted Windows runner;
- current installer template materialization and setup build: PASS;
- bounded /TESTROOT install/uninstall: PASS with no remaining test directory or
  test uninstall registry key;
- existing six protected legacy user-configuration files on the current VM:
  unchanged during native fixture execution.

Historical v7-only GUI/session evidence remains valid for the product behavior
described above. DPI scaling, accessibility, physical drag, signing and public
distribution remain separate gates.

## Known functional coverage limits

Current source and the last parity evidence still show these limits:
- Shell enumeration is bounded at 2,600 entries; larger folders, streaming
  virtualization, network/virtual providers and sustained thumbnail-cache
  behavior are not certified.
- Persistent bookmark edit/import/delete and bookmark toolbar parity are not
  implemented in the current WinUI product.
- Search is bounded filename search; content search, regex and advanced
  multi-criteria search are not implemented.
- Saved filter/mask rule sets and the complete historical command/provider
  verb/fault matrix are not implemented or not fully tested.
- User-configurable accelerators and a complete historical shortcut map are
  not implemented.

## Packaging state

The installer project is now reproducible from a tracked project template, and
a current local Release setup build plus bounded /TESTROOT install/uninstall
has passed. The tracked licensing/provenance snapshot still predates v7, so
this does not by itself clear public distribution or prove a signed clean-machine
machine-wide install/update/rollback path.

## Open gates

Not certified by current automated evidence:
- actual 125%, 150% and 200% OS display scaling;
- High Contrast ON;
- human Narrator and Korean IME composition acceptance;
- physical pointer drag acceptance;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance;
- Large Icons and optional path-specific Known Folder artwork.

Do not convert source support, RDP-only checks or a prior package into
certification of these gates.
