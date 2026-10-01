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
