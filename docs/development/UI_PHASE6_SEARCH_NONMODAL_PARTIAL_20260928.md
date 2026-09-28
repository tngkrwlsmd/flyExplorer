# Phase 6 UXH-02 ? nonmodal search completion, partial acceptance

Status: **IN PROGRESS / NOT MERGED TO MAIN**.
Branch: fix/uxh02-search-success-nonmodal-20260928,
based on main 82709107dc05570920630587c1d4059b5993cf62.
No changes to the separate WinUI 3 experiment or original
user configuration files.

## Problem, scope and source changes

SearchDlg::OnFinalize already refreshes its result count and elapsed
time via mStatusBar and has a separate new search-result tab in the
existing ExplorerView. Its additional MB_ICONINFORMATION MessageBox
on ordinary search completion was redundant and bright under Dark.
The source change removes only that success modal and sends
EVENT_OBJECT_NAMECHANGE on the existing native status bar. Native
search engine, explicit wrong-location MB_ICONSTOP error handling,
and OnCancel's stop/close logic were not changed.
Screen reader announcement itself is SOURCE ONLY, not independently
accepted in an actual assistive-technology session.

Added dedicated source and actual owned-GUI tests:
- build/test_ui_search_completion_contract.py
- build/test_ui_search_completion_runtime.py

The GUI test creates private copies of all six original settings,
launches only an owned app, and searches real synthetic files.
SearchResultCtrl is a new SysListView32 in MainFrame's newly created
search result tab, NOT a child of the modeless SearchDlg; the test
was corrected to watch each newly created main list HWND instead
of incorrectly searching the dialog's children.

## Direct test results on actual Windows 11, 96 DPI Dark

- Source contract PASS; scoped product incremental x64
  Release-x64-Unicode build EXIT 0.
- Actual normal completion: zero results 0, exact file 1, wildcard
  multi-file results 3, each in a separate new native search tab.
  Zero unexpected native information modals across all three.
- Physically entered an absent directory INSIDE the test fixture:
  existing explicit wrong-location native ERROR modal retained
  and dismissed without changing any user settings.
- Owned GUI test process exited 0 and each of six original
  configuration file SHA256 hashes matched.
- Source invariants EXIT 0; native functional regression
  17 passed, 0 failed.
- Tested product build SHA256:
  D3771805FF57CBCD87F0D04E24652FA6974F2A502B10BD2AA8C06E965B45A81F.
- Full logs are LOCAL only in ignored logs/uxh02-*.

## Unmet required acceptance gates and exact next test

- **Real active cancellation NOT TESTED:** a 3,500-file nested
  synthetic fixture still finished before the automation could
  observe an active search, even with IDC_SEARCH_SUBFOLDER checked.
  Existing OnCancel mSearchFile->stop()/DestroyWindow() was
  source-preserved, but that is not physical cancel acceptance.
  The costly 3,500-file attempt is now opt-in with --cancel-probe.
  Next test needs a deterministic, safely test-owned slow worker
  or other genuine active-search fixture without affecting the
  user's filesystem/network; DO NOT repeatedly recreate almost
  identical fast fixtures and mark cancellation PASS.
- **Search result double-click or containing-folder navigation
  NOT TESTED.** Establish the actual SearchResultPane command
  mapping and exercise only the owned synthetic search result.
  Do not launch default external apps or use the user's clipboard.
- Actual assistive-technology announcement, real High Contrast,
  120/144/192-DPI and light-mode search-specific GUI have NOT
  been independently accepted in this change.

The scoped UXH-02 code and tests are committed to an independent
local work branch for continued testing; the known-good
main UXH-01 commit stays untouched. Do not merge UXH-02 until
these user-requested acceptance gates are actually satisfied.
