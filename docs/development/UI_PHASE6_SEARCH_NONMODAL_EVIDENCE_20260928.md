# Phase 6 UXH-02: nonmodal Search completion ? final scoped evidence

**Status:** actual Windows 11, real 96-DPI Dark and Light, scoped
Release and GUI acceptance PASS. Main starting baseline was
82709107dc05570920630587c1d4059b5993cf62.
Earlier isolated WIP checkpoint 53383fbae27f06eb23f95dadfd7dbc212c4bde3d
is preserved in Git history and was not pushed independently.

## Product changes and diagnosed root cause

SearchDlg::OnFinalize already updated visible result-count and elapsed-time
panes plus the native search result tab, but additionally blocked users
with a light-colored information modal on every normal success. That
redundant success modal has been removed; existing wrong-location
errors and real Stop/Cancel paths were preserved.

The custom gui/StatusBar intercepted WM_SETTEXT to replace visible
pane 0. An ordinary SetWindowText did not give the accessibility
provider a readable name and would duplicate the visible summary.
New StatusBar::announceAccessibleStatus bypasses that interception
through native DefWindowProc WM_SETTEXT, exposes the existing localized
result count plus elapsed time in a separate accessible HWND name,
and sends the actual Windows name-change notification. Both visual
panes keep their original independent text.

## Actual, externally observed acceptance

- Owned, isolated, actual Windows 11 GUI, real 96 DPI.
- Dark and Light: normal zero, one and three-result searches created
  the matching native search result tabs with NO completion modal.
  An invalid directory inside the private fixture still produced
  its existing native warning dialog.
- Active Stop: actual text-content search across two synthetic
  160-MiB owned files; the Search button physically changed to Stop,
  Close was disabled while the worker was active, a physical mouse
  click on Stop ended the work and restored the idle Search button
  and Close availability.
- Search result navigation: physically selected the private file,
  opened the real native Shell context menu, confirmed the first
  entry was the localized Open parent folder command, and physically
  clicked that item's actual UIA rectangle. The active flyExplorer
  title changed to the expected private parent folder; no external
  program, clipboard action or original user file was involved.
- Live native accessibility: external Windows
  EVENT_OBJECT_NAMECHANGE callback observed on the actual status
  HWND; UI Automation Name and native HWND text both contained the
  localized one-result and elapsed-time summary.
  The native event is verified; no full listening session with
  Narrator/NVDA was conducted.
- Search source contract PASS, scoped incremental x64
  Release-x64-Unicode product build PASS, source invariant PASS and
  native functional regressions **17 PASS / 0 FAIL**.
- Every test-owned process exited normally. All six original
  configuration SHA256 hashes remained unchanged on every run.
  No global display settings, user processes, user files or global
  clipboard were changed.
- Final tested Release executable SHA256: 22D0568AB047E4A08F690B7461FB7D63E2B90A23E447BE03650D8818B2559575.

Source contracts: build/test_ui_search_completion_contract.py.
Owned GUI: build/test_ui_search_completion_runtime.py (Dark/Light)
and build/test_ui_search_cancel_navigation_runtime.py.
Full logs and the private native context menu screenshot are retained
ONLY under ignored local logs, not committed with personal context.
The regression harness removes its own 320-MiB synthetic payload
on subsequent runs to avoid accumulating large test data.

## Explicit boundaries

Real Windows High Contrast, actual 125/150/200% scaling,
actual screen-reader listening and duplicate-readout assessment,
large slow network shares, permission-denied directories and
arbitrary Shell extensions are **NOT TESTED** in this scoped
release. They remain environment/integration gates, not implied PASS.
UXH-03 through UXH-07 and the WinUI 3 Phase 5 experiment
are independent, unfinished tasks.
