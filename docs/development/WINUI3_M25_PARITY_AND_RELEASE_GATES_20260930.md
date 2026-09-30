# M2.5 independent WinUI stabilization and parity (2026-09-30)

Scope: migration/winui3-full-shell-20260929 only. Never mutate original MFC main or real existing user settings. Passing the independent preview tests is not a production cutover decision.

## 1. Context-menu error regression

The earlier owned UIA right-click diagnostic intermittently failed to expose the app flyout entry even though native helper enumeration and one earlier popup+ESC run had succeeded. The current bounded harness clips the right-click coordinate to the intersection of the exact selected row and its actual owned ListView viewport, verifies the exact WinUI foreground PID, launches only the sibling helper with `--context-menu`, confirms the helper owns the foreground, and sends ESC only to that exact owned popup. No provider verb is invoked.

After the M2.5 layout/filter changes and fresh binaries, the same strict harness passed twice consecutively in Debug and once in Release. Each pass confirmed the synthetic source bytes and all six original MFC settings were unchanged. The previous failure remains historical evidence; there is not enough direct evidence to attribute it solely to WinUI or solely to pywinauto. **Current bounded launch/cancel path: PASS; arbitrary third-party verb execution/fault behavior: NOT TESTED.**

## 2. Bounded large-folder improvement

Only the separate WinUI helper wire changed from 1,200/4MiB to at most 2,600 entries/8MiB. The legacy MFC navigation default is unchanged. New WinUI native-snapshot view paging renders 160 sorted items initially and explicitly reveals +160 more without replacing the native snapshot. A non-destructive per-pane filename substring filter resets the view page without mutating model items. Async file metadata now cancels stale route work before additional type/icon/thumbnail helper launches.

A test-owned 2,300-file fixed-drive folder passed on freshly compiled Debug and Release. Debug first-row render was ~1.83s and Release ~1.48s on this workstation. Both actually expanded the visible page 160?320, filtered to `bench-2299.txt`, cleared the filter back to the sorted snapshot, and preserved six original MFC settings. The new `Ctrl+Shift+F` shortcut was also sent as a real key chord from the owned file list and moved keyboard focus to the current pane's name filter. **2,300 bounded local items: PASS. More than 2,600 entries, streaming virtualization, network/virtual providers and sustained thumbnail cache behavior remain NOT TESTED/NOT IMPLEMENTED.**

## 3. Actual source-grounded MFC parity map

| Feature | Existing MFC tracked source | Current WinUI preview | Remaining gap |
|---|---|---|---|
| Bookmarks | `src/fxfile/bookmark.cpp`, `src/fxfile/bookmark_toolbar.cpp`, `src/fxfile/cmd/cmd_bookmark.cpp` | Named workspaces and opt-in recent search scopes | Persistent bookmark edit/import/delete and toolbar |
| Advanced search | `src/fxfile/search_dlg.cpp`, `src/fxfile/cmd/cmd_search.cpp` | Bounded filename substring search (2,500 walk / 100 results) | Contents, regex and advanced multi-criteria |
| Filters | `src/fxfile/file_filter.cpp`, `src/fxfile/cfg/filter_set_dlg.cpp` | New non-destructive per-pane filename substring view filter | MFC saved rules, mask sets, exclusion/type dialogs |
| Menus | `src/fxfile/cmd/router/cmd_command_map.cpp` | Owned file operations and isolated OS Shell popup | Complete MFC commands and provider verb/fault matrix |
| Preferences | `src/fxfile/cfg/` | Independent preview theme, recents, workspaces and opt-in session | Full reversible original MFC preference mapping/dialogs |
| Shortcuts | `src/fxfile/accel_table.cpp` and `src/fxfile/cmd/accel_table_dlg.cpp` | Ctrl+A/C/X/V, F5/F6/Delete plus new Ctrl+Shift+F | User-configurable accelerators and complete shortcut map |

This phase implements a first bounded filter and shortcut slice. Do not claim whole-MFC feature parity, including bookmarks or regex, from these changes.

## 4. Actual environment and production installer gate

The connected workstation exposes one 1280x768 monitor at 96 DPI / 100% and High Contrast OFF. The owned accessibility test passed three responsive window sizes (960x634, 1100x680, 1240x710), nine UIA names and physical Tab focus sequencing on the newly compiled Release. Actual 125/150/200% DPI, High Contrast ON, Narrator speech and Korean IME composition still require a separately controlled Windows environment; this host exposes no usable Hyper-V management environment and these global OS states were not changed.

The previous genuine Release-v1 snapshot and the newly compiled M2.5 Release-v2 were exercised in a unique test-owned unpackaged run directory. v1 launch ? v2 update ? exact v1 binary rollback ? test-only uninstall all passed and original MFC settings remained identical. The lifecycle harness was hardened after two harness-only failures: stale isolated profile directories now cannot block a later run because every run uses a unique owned directory, and before renaming stages it waits only for processes whose executable path is inside that exact private stage so short-lived helper children cannot retain file locks. This remains an **unpackaged private file lifecycle**, not a signed NSIS/MSI/MSIX installer or fresh-machine Windows App SDK prerequisite test.

Latest full test-owned M1.9?M2.3 regression GUI also passed on both newly compiled Debug and Release after the M2.5 list/filter changes. Source/preflight and targeted contracts pass before these runtime checks.

No automatic default-app change, main merge or release.
