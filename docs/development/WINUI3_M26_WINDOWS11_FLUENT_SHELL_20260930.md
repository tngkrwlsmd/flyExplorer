# M2.6 - Windows 11 Fluent Shell redesign (2026-09-30)

Worktree: `C:\dev
lyExplorer-winui3-migration`
Branch: `migration/winui3-full-shell-20260929`
Protected native MFC main: `C:\dev
lyExplorer` at `cbffb48` (not modified)

## Why this slice exists

The independent Phase6 WinUI shell had already accumulated real navigation, two-pane state, file operations, isolated Shell helpers, clipboard, Recycle Bin, thumbnails, registered file types, context popup cancellation, paging/filtering and private-session behavior, but the visual hierarchy still looked like a developer-oriented set of WinUI controls. M2.6 changes the presentation layer toward Windows 11 File Explorer's public Fluent design language without importing private Explorer implementation details and without replacing the proven native model.

## New shell hierarchy

The active view is now organized as:

1. Public WinUI custom title bar + Mica backdrop, with theme fallback.
2. Thin dynamic-overflow `CommandBar` for file commands.
3. Back / Forward / Up + address + current-folder search row.
4. Scrollable Fluent navigation rail.
5. Independent left/right pane chrome with pane title, per-pane tabs, filename filter, aligned detail columns and file list.
6. Existing status footer.

The native route/session model remains the source of truth. XAML controls forward intent to the existing handlers rather than duplicating file-operation or Shell logic.

## Deliberate dual-pane divergence from Explorer

Windows 11 Explorer has one top-level tab strip. flyExplorer has two independently navigable panes, each with independent tab/history state. M2.6 therefore uses the public custom title bar for the app shell but intentionally keeps each pane's `TabView` inside that pane instead of fabricating one shared top tab strip. This preserves the product's dual-pane behavior and avoids a misleading duplicate tab model. The selected pane is indicated with subtle accent chrome rather than a heavy border.

## Title bar, backdrop and theme

- `ExtendsContentIntoTitleBar(true)` + `SetTitleBar(...)` use only public WinUI 3 APIs.
- `MicaBackdrop` is requested through `SystemBackdrop`.
- Runtime-restricted hosts fall back to the existing themed page background.
- System / Light / Dark behavior and the existing preference callback remain.
- No DWM private chrome imitation or undocumented Explorer APIs were added.

## Explorer-like command and route surfaces

`FileToolbar` now exposes a compact dynamic-overflow `CommandBar` with existing handlers for create, rename, cut/copy/paste, internal copy/move, Recycle Bin and related commands. Existing handlers were reused; no second file-operation path was introduced.

The route row now exposes Back / Forward / Up, an address box, current-folder search, new/close tab, split, workspace and advanced-search affordances. Address entry still accepts the existing filesystem / Shell route forms. For the real virtual This PC PIDL, M2.6 presents the friendly `내 PC` label while retaining the native PIDL in the model/history; the UI maps that label back to `shell:MyComputerFolder` only when used as address input.

## Navigation rail

`NavigationSidebar` is restyled around transparent Fluent navigation buttons with icons, hover/pressed states, selection accent and bounded width. Current destinations include Home, This PC, Desktop, Downloads, Documents, Pictures, Music and Videos. It remains scrollable and still calls the existing route callback. It does not introduce a second `NavigationView` navigation state machine.

## File panes and detail list

The independent pane model, multi-select, context menu, drag diagnostics, sort, filter, progressive page state and metadata cache remain unchanged in ownership.

Visual changes include:

- lower, rounded Fluent row chrome;
- subtle pane borders and active-pane accent;
- consistent pane title and filter placement;
- explicit Name / Type / Size / Modified headers aligned with row columns;
- retained registered system icon / PNG thumbnail path with generic glyph fallback;
- existing UIA row names preserved;
- existing per-pane name-width control preserved.

M2.6 does not claim full Explorer ItemsView virtualization or pixel-identical private Shell rendering.

## This PC

The real virtual `shell:MyComputerFolder` still comes from the isolated native Shell snapshot. For direct fixed/removable drive roots only, the WinUI renderer adds a bounded capacity presentation using `GetDriveTypeW` and `GetDiskFreeSpaceExW`:

- drive/system visual;
- display name;
- thin usage progress bar;
- free/total GiB text.

No generic `DRIVE_REMOTE` capacity probe, WNet enumeration or blocking provider query was added. Network/cloud providers remain Shell items and are not treated as local disks.

A final owned Release visual check showed the address as `내 PC` and rendered the local drive capacity card. Local-only visual evidence: `logs/m26/m26-final-thispc-release.png`.

## Responsive layout and accessibility

The shell responds to actual window size by reducing navigation width and current-folder search width rather than hiding the address field. The existing compact-monitor resize safeguard is preserved.

Actual owned accessibility/layout checks passed at:

- 960 x 634
- 1100 x 680
- 1240 x 710

The current test checks 16 named Fluent controls spanning title/search/command/navigation/file panes and performs a physical Tab focus sequence. Current workstation state was 96 DPI / 100%, High Contrast OFF. 125/150/200%, High Contrast ON, Narrator speech and Korean IME composition are still NOT VERIFIED and require a separate controlled Windows environment.

## Reused native/runtime functionality

M2.6 intentionally did not rewrite:

- per-pane native Shell navigation/history;
- isolated Shell supervisor and helpers;
- filesystem/Shell watchers;
- file create/rename/copy/move/collision logic;
- Windows clipboard;
- guarded owned Recycle Bin path;
- registered file type/icon/thumbnail helpers;
- context-menu helper;
- 160-item progressive paging / 2,300-item bounded local snapshot;
- private session/workspace/search behavior.

Phase5 remains retired and no `FLYEXP_PHASE5_*` or `FlyExplorerIslandBridge` dependency was reintroduced.

## Actual validation

Final source/build evidence after the friendly This PC label correction:

- official source preflight: PASS
- source contracts: **140 run, OK, 1 environmental skip**
  - `logs/winui-scoped/20260930-162816-source.log`
- x64 Debug build: PASS
  - `logs/winui-scoped/20260930-162826-build-Debug.log`
- x64 Release build: PASS
  - `logs/winui-scoped/20260930-162843-build-Release.log`
- full owned Debug integration GUI + compact boundary: PASS
  - `logs/winui-scoped/20260930-163000-gui-Debug.log`
- full owned Release integration GUI + compact boundary: PASS
  - `logs/winui-scoped/20260930-163111-gui-Release.log`
- original six MFC user-config SHA256 values: identical in both full GUI runs

Additional actual owned runtime checks after the M2.6 redesign:

- Debug and Release each passed 960x634 / 1100x680 / 1240x710 responsive accessibility checks, physical Tab focus and original-settings preservation.
- Debug 2,300-item local folder: first row ~2.02 sec on this workstation; page/filter/sort/Ctrl+Shift+F PASS.
- Release 2,300-item local folder: first row ~1.55 sec; same checks PASS.
- Exact-owned isolated Shell context popup reached helper foreground and was cancelled with ESC in both Debug and Release; source file/settings unchanged.
- Final Release This PC visual probe confirmed UIA address `내 PC` and real local drive capacity UI.

These timing numbers are workstation observations, not performance guarantees.

## Implementation-time defects caught and corrected

Two validation issues were kept distinct from product acceptance:

1. The first helper used to add the friendly This PC C++ literal was sent through a PowerShell/Python text path that replaced the Korean character with `?`. The source was inspected with Unicode escaping, corrected to ASCII-only C++ universal character syntax `L"내 PC"`, rebuilt in both configurations and revalidated with the real GUI.
2. The native watcher can replace a ListView UIA peer while the test acquires foreground focus. The owned double-click harness now re-resolves the exact owned `Nested` row immediately after focus acquisition, matching the existing bounded UIA re-query strategy rather than treating a stale peer as a product failure.

## Known visual differences and remaining gates

This is intentionally not a pixel-for-pixel Explorer clone. Remaining differences include:

- the dual-pane app keeps one tab strip per pane rather than a single Explorer title-bar tab model;
- the theme picker remains app-owned;
- column resizing is not yet a complete Explorer-style four-column interaction;
- generic glyph fallback still exists where system visual extraction is unavailable;
- no private Explorer breadcrumb/control implementation is copied;
- no tens-of-thousands streaming virtualization;
- no new provider protocol;
- no signed production installer/default-app switch;
- physical drag remains a separate unresolved validation item;
- alternate DPI/HCM/Narrator/IME and fresh-machine installer gates remain separate.

## Release boundary

M2.6 is a presentation-layer and bounded rendering upgrade on the independent migration branch. It is not permission to merge into native `main`, replace the default product, revive Phase5, run arbitrary third-party Shell verbs, change registry defaults or publish a release.
