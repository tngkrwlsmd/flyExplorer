# F05 — File type grouping: current bounded acceptance

## Scope and design

Type grouping is opt-in via View → 유형별 그룹화 (전체 목록), and
applies to the active pane. The product currently supports type
grouping only in Details mode when the complete resident/indexed
enumeration is available, metadata is synchronized, route/tab/side
identities match and there are at most 25,000 indexed items.
Unsupported or incomplete folders revert safely to the ordinary
list instead of presenting a false complete-group claim.

The model classifies folders, filename extensions and extensionless
entries. Each group has a disclosure action; headings are not real
files and never carry a Shell item identity. Real selectable rows
retain original Shell logical identities, parsing paths and 160
file rows per initial page. Collapse state is pane/window-tab local
and is invalidated when route identity changes.

## Files and tests

- app/winui/file_group_projection.h: bounded full-model type buckets
- app/winui/file_group_presentation.h: scoped collapse and paging
- app/winui/FileToolbar.xaml and C++ code: View menu toggle
- app/winui/file_list_state.h and MainWindow.xaml.cpp: pane ownership,
  presentation rendering, guarded selection and disclosure callbacks
- tests/winui/native_f05_group_projection.cpp and
  tests/winui/native_f05_group_presentation.cpp: model probes
- tests/winui/test_f05_group_projection_contract.py and
  tests/winui/test_f05_winui_group_integration_contract.py:
  source contract checks
- tests/winui/test_f05_group_gui.py: real owned interactive GUI probe

## Windows evidence — 2026-10-15

Product bridge commit: c14be710.
Accepted main/test revision:
50dc06b872069b6f6ba2f4e5ea3e224c2809423f.

1. [#38688357154](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38688357154)
   finished fresh Release and eight source contracts, started the
   actual WinUI app, but its GUI harness incorrectly used
   Desktop.child_window and failed before opening the group control.
2. [#38692716189](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38692716189)
   reused the Release and located the owned View popup but used an
   unsupported Invoke UI Automation pattern on its toggle item.
3. [#38692989325](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38692989325)
   **SUCCESS**: eight contracts, physical owned-menu click, group
   headings for TXT/Markdown/log fixtures, real TXT selection,
   independent Markdown collapse and re-expansion, normal WinUI exit,
   original six preferences unchanged, disposable files removed.

Before/grouped/expanded PNG screenshots were generated and retained
by the harness. Retrieval of the original bytes for manual visual
review was blocked by platform security. This does not count as
pixel visual acceptance.

## Further validation / unimplemented capabilities

Actual visual review and Dark theme; independent right pane and
window-tab switching; active High Contrast and Narrator announcements;
125%, 150%, 200% Windows DPI; huge-folder GUI limits; keyboard-only
group disclosure; name/date/size group modes; non-Details layouts.

Do not change real user folders or system display settings solely
for these tests. Keep an explicit acceptance status for each scope.

## 2026-10-15 Independent pane and route follow-up — PARTIAL, NOT ACCEPTED

- **Test-only change**: `dee26e68` added an opt-in
  `FLY_F05_PANES_ONLY=YES` synthetic two-pane GUI probe with
  separate test-owned TXT/Markdown/log files on both sides. No
  product C++/XAML or user settings were changed. The existing,
  previously compiled F05 Release executable was reused.
- [Actual Windows run #38693990951](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38693990951):
  **FAIL (partial coverage)**. All eight F05 source contracts
  passed, and the real WinUI process opened/exited normally.
  `F05_BOTH_PANES_START_UNGROUPED=PASS`,
  `F05_RIGHT_GROUP_DOES_NOT_GROUP_LEFT=PASS`, and
  `F05_RIGHT_MD_COLLAPSED=PASS` were observed. The next assertion
  timed out because left-pane grouping headings did not appear
  after switching back from the right. This is **not accepted** as a
  passing dual-pane test. All six real legacy preference hashes
  remained identical and synthetic fixture cleanup passed.
- [Read-only captured UIA evidence #38694342760](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38694342760):
  **SUCCESS**. Exactly four file-list items and zero group Button
  peers remained on the left; seven list items and four group
  Button peers remained on the right. Evidence was drawn only from
  the failed test's owned WinUI window, not unrelated user windows.
  Whether left-pane activation failed, left metadata was stale, or
  the UI toggle was rejected remains **undetermined**.
- `3e709d50` is a **test-only diagnostic amendment**. It
  explicitly clicks LeftFiles, waits for the visible active-pane
  label and reports active pane, StatusText and left/right group
  button counts immediately after toggling. A subsequent guarded
  Windows execution request was blocked by platform safety review,
  so **this amended test has not been executed or accepted**.
- **Still pending:** successful left-then-right independent
  collapse/expand, right-folder navigation invalidating only right
  groups, multiple window tab behavior, and original screenshot
  pixel review. The central Remote Shell request slot remains
  idle; do not claim those untested scopes are PASS.

