# Canonical repository layout (2026-09-30)

After WinUI 3 became `main`, the old `experiments/phase6_winui_shell` path and
MFC-first root commands were misleading. This refactor changes paths, not product
behavior.

## Current layout

- `app/winui`: product XAML/C++/WinUI project, runtime helper, resources
- `src/base`: UI-independent native core
- `tests/winui`: contracts, owned GUI probes, M1.9-M2.3 native fixtures
- `tools/winui`: scoped local check runner
- `legacy/mfc`: former MFC source plus its build/distribution/library tooling
- `src`: canonical shared native source; currently only `src/base`

## Root commands

- `build.bat [Debug|Release]`
- `run.bat [Debug|Release] [folder]`
- `test.bat source`
- `python -X utf8 tools\winui\run_checks.py full`

## Dependency boundary

The active WinUI project compiles shared code from `src/base`. The small
`file_operation_core` seam was moved from `src/fxfile` into `src/base`, removing
the last direct product-project compile dependency on the legacy MFC application
source tree.

## Deliberate non-goals

This pass does not rewrite or delete old MFC history. Its retained local source
and tooling are quarantined under `legacy/mfc`; exact runnable recovery remains
the historical `cbffb48` commit. Phase5 remains retired.

## Validation evidence

The refactor was validated through the new canonical entry points and moved test
tree, not by relying on pre-move binaries alone.

- `test.bat source`: canonical structure preflight **4/4 PASS**, remaining WinUI source
  contracts **103/103 PASS** (107 unique source/structure tests total): `logs/winui-scoped/20260930-183545-source.log`.
- `build.bat Debug` and `build.bat Release`: both produced the current WinUI
  executable and matching helper from the new `app/winui` path. Existing
  compiler/MSBuild warnings are still present; this refactor does not claim a
  warning-free build.
- Full test-owned GUI regression from `tools/winui/run_checks.py`:
  - Debug PASS: `logs/winui-scoped/20260930-182136-gui-Debug.log`
  - Release PASS: `logs/winui-scoped/20260930-183345-gui-Release.log`
  - both retained `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`.
- Focused Release checks after the move also passed three responsive
  accessibility sizes + keyboard Tab focus, the 2,300-item page/filter/sort
  scenario (~1.68s first row on this workstation), and the exact-owned isolated
  Shell context-popup + ESC path.

No GitHub Actions workflow was dispatched. The workflow definitions were only
retargeted so a future separately authorized manual run uses the canonical
WinUI paths instead of the former MFC/default or experiment paths.
