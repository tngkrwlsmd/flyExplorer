# flyExplorer current status — 2026-10-02

## Product source of truth

main is the canonical C++/WinRT WinUI 3 product. Product code lives in
app/winui, UI-independent native code in src/base, tests in tests/winui, and
bounded orchestration in tools/winui/run_checks.py. The former MFC application
is retired from the working tree and is recoverable from Git revision cbffb48.

The latest product-code checkpoint before this documentation cleanup is
eb76c37 (feat: persist window tab sessions). Live Git refs always take
precedence over this recorded checkpoint.

## Accepted current behavior

- Windows 11-style WinUI 3 shell with custom title bar/Mica, navigation,
  address/search, command bar, status surface and independent dual panes.
- Functional top-level Window Tabs plus per-pane folder tabs.
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
(ERROR_INVALID_OPERATION). The current fix moves cancellation/shutdown to the
window Closed boundary, re-checks detail-worker cancellation immediately before
DispatcherQueue enqueue, and treats late detached session completion enqueue as
best-effort during dispatcher teardown. Accepted GUI evidence requires real
process exit code 0.

## Latest verified evidence

On the 2026-10-02 v7 checkpoint:
- canonical structure preflight: 4/4 PASS;
- source contracts: 125/125 PASS;
- canonical Release build: PASS;
- v7-only Release GUI: PASS with OWNED_WINUI_SHELL_EXIT 0;
- isolated Korean create/watcher/restart GUI: PASS;
- final full owned Release GUI: PASS in 95.2 seconds;
- v7 multi-WindowTab restart/session/history/split restore: PASS;
- private session clear/revoke: PASS;
- six protected user-configuration hashes: unchanged.

The first Release build wrapper in that investigation timed out while MSBuild
continued; it was not a compiler/linker failure. A normal incremental canonical
Release build subsequently completed PASS.

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

The tracked installer/provenance snapshot was last produced on 2026-10-01 and
predates v7. It must not be described as a package of the current product until
packaging is rebuilt and lifecycle/provenance checks are rerun.

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
