# WinUI Explorer visual benchmark - 2026-10-01

## Scope and source of truth

This v1 benchmark compares the canonical WinUI `flyExplorer` against the installed Windows 11 File Explorer on the same machine. The goal is not pixel cloning: it is Explorer-like hierarchy and density while preserving dual-pane workflows.

Owned evidence is retained under ignored `logs/ui-benchmark-20261001/`; no personal folders or user screenshots are committed.

Baseline conditions:

- Windows 11, Dark, 96 DPI / 100% scale.
- Same synthetic `flyExplorer-UI-Benchmark` folder.
- Same 972x720 comparison rectangle for acceptance geometry.
- Explorer UIA baseline and pre-change flyExplorer UIA were captured before the v1 candidate.

## Measured baseline

| Geometry | Windows 11 Explorer | flyExplorer before v1 |
| --- | ---: | ---: |
| tab/title strip | y 2-40 | title/theme region about y 0-43 |
| navigation/address/search | y 48-80 | y 103-137 |
| command surface | y 89-135 | y 43-91 |
| file content top | y 136 | y 251 |
| navigation width | about 154 px | about 150 px |
| Details row pitch | about 28 px | about 36 px |

The largest defect was structural: flyExplorer consumed about 115 additional vertical pixels before file content.

## Explorer-like v1 candidate

Current working-tree candidate changes are intentionally limited to top chrome, navigation/address, command bar, pane chrome, and Details density.

Observed changes:

- Theme picker/state text removed from ordinary top chrome; theme access moved under More.
- Address display separates normal location presentation from raw-path editing.
- Command buttons use a compact 36px surface and clearer grouping; the always-visible rename text box is collapsed until rename/create intent.
- Pane title controls remain available to automation but are visually reduced to 1x1 transparent affordances.
- Per-pane name filters are collapsed by default and can be opened from More.
- Pane cards/rounded outer borders were removed in favor of a subtle active-pane top accent and a 1px pane divider.
- Pane tabs are 28px and Details headers 24px; visible column-width sliders are removed while their automation contracts remain.
- File ListView rows use a 32px pitch.
- Sidebar chrome is flatter and diagnostic/process terminology is removed from ordinary navigation/status presentation.

## After measurements

Release candidate SHA-256 during this visual run:

`8C9CD01200BED640590C31CC8E82C58D8CA640A23FE0654662CA9206EC9C48B6`

At 972x720:

| Geometry | Explorer | Before | v1 candidate |
| --- | ---: | ---: | ---: |
| file content top | 136 | 251 | **174** |
| row pitch | 28 | about 36 | **32** |
| pane tabs top/bottom | n/a | 179/219 | **122/150** |
| address top/bottom | 48/80 | 103/137 | **42/74** |
| navigation width | about 154 | about 150 | about **156** |

The v1 acceptance target (`file-list top <= 185`) is met with 77 px less pre-content chrome than the previous WinUI layout.

## Runtime visual observations

Verified on the owned synthetic folder:

- Idle dual-pane layout renders without pane cards and keeps both panes usable.
- Left and right pane activation moves the thin accent indicator and keeps the previous selection visible.
- Selected file rows use a restrained surface and remain distinguishable from the inactive pane.
- 972x720 and maximized layouts remain stable.
- At 760x640, commands stay available and both panes remain visible, but the Type column becomes overly compressed. This remains an OPEN responsive-density gap; do not describe narrow-width presentation as Explorer parity.
- Command-hover screenshot was not captured in this run; hover visual parity remains NOT TESTED rather than inferred from XAML.

## Remaining visual gaps

1. The title strip is simpler than Explorer's actual TabView/title composition; v1 prioritizes density over full tab-strip parity.
2. The command bar still exposes flyExplorer-specific opposite-pane transfer operations more prominently than Explorer exposes equivalent secondary actions.
3. Sort remains a ComboBox-style control rather than Explorer's exact Sort/View command presentation.
4. Narrow dual-pane widths need a better column-priority policy; Type currently truncates aggressively.
5. Breadcrumb presentation is intentionally lightweight; raw path editing is preserved on focus/click rather than implementing Explorer's private breadcrumb behavior.
6. Command hover/pressed parity, 125/150/200% DPI, High Contrast, and live Narrator listening remain NOT TESTED.

## Acceptance status

For the 100% DPI v1 benchmark, the structural density target is **PASS**: the file-list top moved from about y=251 to y=174 while dual-pane behavior remains present. This is a prototype visual acceptance result only; it does not replace the separate accessibility, DPI, physical drag, clean-machine, or release-signing gates.

## Regression evidence

- `test.bat source`: PASS, canonical structure 4/4 and source contracts 116/116.
- `build.bat Release`: PASS for the v1 UI candidate.
- `tools/winui/run_checks.py gui --configuration Release`: final PASS in 66.2 seconds.
- The first two full GUI attempts stopped at M2.3 owned-session child restore. A direct isolated save/restore diagnostic proved both `Nested` and `Secondary` folders restored correctly with child exit 0. The integration harness was still physically clicking the now-retired 1x1 transparent pane-title affordance. Updating `test_m23_gui.py` to activate panes through the actual `LeftFiles`/`RightFiles` user surfaces preserved all assertions/timeouts; the following full Release GUI run passed, including exact owned child auto-restore.
- Final GUI evidence includes normal owned shutdown and `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`.
- Physical drag/global clipboard, alternate DPI, High Contrast and live Narrator listening remain outside this v1 visual run.

## Explorer-like v2 follow-up

The v2 pass starts from commit `376c34c55d42526416b6b6f8171d1497083e099d` and keeps the v1 vertical-density acceptance intact while addressing the remaining command, breadcrumb, responsive-column and interaction-state gaps.

### v2 implementation

- Replaced the ordinary visible Sort ComboBox presentation with an Explorer-style `SortButton` flyout while retaining the `SortPicker` automation contract for existing owned tests and assistive automation.
- Added a `ViewButton` flyout next to Sort and More. Details remains the current supported view rather than inventing a new backend view mode.
- Reduced opposite-pane Copy/Move visual prominence with a smaller secondary-command style while preserving the direct commands and AutomationIds.
- Replaced the lightweight address text presentation with clickable breadcrumb segment Buttons plus a dedicated edit affordance. Long filesystem paths collapse the front portion and retain the final hierarchy; typed raw-path edit remains available without rewriting navigation/history.
- Added width-profiled Details columns. At approximately 760px split-window width, each pane prioritizes Name + Size and visually hides Type/Date rather than rendering an unusable 1-2-character Type column. Wider profiles progressively restore Type and Date.
- Kept the 2px active-pane accent, 1px divider, 24px header and 32px row pitch. The divider opacity is reduced to keep the split boundary visible without reintroducing pane cards.
- Reduced title-strip app-identity emphasis without adding another fake window-level tab strip.

### v1 / v2 / Explorer geometry

| Metric | Windows 11 Explorer reference | v1 | v2 |
| --- | ---: | ---: | ---: |
| file content top | about 136 px | 174 px | **174 px** |
| row pitch | about 28 px | 32 px | **32 px** |
| sidebar width at 972px | about 154 px | about 156 px | **156 px** |
| address height | 32 px | 32 px | **32 px** |
| command row height | about 46 px | 42 px | **42 px** |
| 760px split visible metadata | n/a | Name + compressed Type + Size | **Name + Size** |

The v2 candidate Release SHA-256 used for the runtime checks is:

`89ECBDBC35ED4F9453B75932514DF1A40E607AE405BC7C5C54F80301BD33F8E6`

### v2 runtime interaction evidence

- 972x720: `LeftFiles` and `RightFiles` top remained y=174; row pitch remained 32px.
- 760x640: both panes remained visible and usable; Type and Date were removed from the visual allocation so Name and Size retained meaningful width.
- Breadcrumb UIA exposed the current filesystem hierarchy as interactive address-path Buttons. An actual click on the `logs` ancestor navigated to `C:\\dev\\flyExplorer\\logs` successfully.
- Raw address edit state, command hover, command pressed, Sort flyout, View flyout and More flyout were captured from the actual product after minimizing unrelated Explorer windows so foreground pixels were not contaminated.
- Sort flyout exposed name ascending/descending, size descending and modified-date descending while preserving the existing sort backend.
- View flyout accurately reports Details as the currently supported view; it does not claim unsupported icon/list modes.
- Light and Dark were both switched and rendered on the same v2 binary and synthetic fixture. High Contrast remains a separate NOT TESTED gate.
- Release GUI regression: PASS in 67.1 seconds, including two-pane navigation, tab/split/history, Korean create/rename, transfer contracts, private-session auto-restore, normal shutdown and `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`.

### Current remaining visual gaps after v2

1. The custom title strip is intentionally restrained but still simpler than the full Windows 11 Explorer window-level tab/caption composition. No extra fake tab layer was added.
2. View currently exposes only the implemented Details mode. Additional view modes require a separate functional scope, not visual fabrication.
3. The status footer still prioritizes current operation/status text rather than Explorer-style persistent item/selection counts; this remains an OPEN polish item.
4. Exact keyboard-focus parity across every command/breadcrumb state was not independently pixel-certified; hover and pressed were verified.
5. A fresh clean current-session Explorer screenshot set could not be reliably reacquired through the RDP UIA harness; the same-machine Explorer reference measurements captured for v1 remain the comparison baseline. Do not treat the failed capture harness as a product result.
6. 125/150/200% DPI, High Contrast and live Narrator listening remain NOT TESTED in this RDP environment.

## Explorer-like v3 status / selection / focus polish

The v3 pass starts from pushed v2 commit `cd183e52ffe34ec99329506b7746e9ce0553a065` and deliberately leaves title/tab and view-mode architecture unchanged. Its scope is status-bar information hierarchy, active/inactive selection presentation, keyboard focus visuals, and command busy/disabled consistency.

### v3 implementation

- The footer now gives persistent user-facing context: active-pane item count on the left, selection count when non-zero, and transient operation/status text aligned to the right.
- Selection count updates from real `SelectionChanged` events as well as the existing pane tap/keyboard presentation queue, so mouse, Ctrl multi-select, pane switching, and keyboard selection do not depend on an incidental KeyUp alone.
- Selection in the inactive pane remains visible but is visually reduced (`Opacity=0.78`) rather than disappearing or retaining the same emphasis as the active pane.
- Standard WinUI system keyboard focus visuals are explicitly retained on command buttons, navigation buttons and file rows. No custom high-contrast-hostile focus rectangle was introduced.
- File-operation busy state continues to be the compatibility signal used by existing command automation; v3 does not redefine `CopyButton.IsEnabled()` as a no-selection proxy because owned clipboard tests use that state to observe transfer settling.
- The footer keeps the existing `StatusText` and hidden `ActivePaneText` automation contracts while adding `ItemCountText` and `SelectionCountText`.

### v3 runtime evidence

Release SHA-256 used for this run:

`56928A3F3C6687E0EEFEE3C401774F412D9574D8F809BC185AA28E6A76A75198`

Owned synthetic-folder observations at 972x720 / 96 DPI:

- Initial footer: `8개 항목`, no selection count.
- Single mouse selection: `1개 선택됨`.
- Ctrl multi-selection: `2개 선택됨`.
- Switching to the right pane and selecting one item: footer changed to `1개 선택됨`; the previous two left-pane selections remained visible with reduced inactive emphasis.
- Keyboard move in the active right list kept the footer at `1개 선택됨` and updated selection through the actual list selection event.
- `SortButton.has_keyboard_focus()` and `MoreButton.has_keyboard_focus()` both reported true after programmatic keyboard focus; the actual product screenshots show the system focus outline.
- Idle `CancelButton` and unavailable Forward navigation rendered disabled; no custom disabled visual override was added.

Ignored evidence is under `logs/ui-benchmark-20261001/v3/`, including idle, single/multi-selection, inactive/active pane, keyboard selection, Sort/More keyboard focus, disabled-command, and metrics captures. No personal folders are used in the fixture.

### v3 regression

- canonical structure: 4/4 PASS.
- source contracts: 117/117 PASS (one new v3 visual/status contract).
- fresh Release build: PASS.
- Release GUI suite: PASS in 65.9 seconds.
- Existing dual-pane navigation, tabs/split/history, Korean create/rename, metadata/sort, opposite-pane transfers, private session auto-restore, normal shutdown and `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True` all remained PASS.

### Remaining v3-adjacent polish

- The footer status message currently remains visible alongside counts after ordinary navigation; further Explorer-style transient-message timing would be a separate behavior decision, not required for this v3 checkpoint.
- Exact focus visuals at alternate DPI and High Contrast remain NOT TESTED in the current RDP environment.
- The larger remaining Explorer visual gap is still the window-level title/tab/caption composition; it should remain a separate scope rather than being mixed into status/focus work.
