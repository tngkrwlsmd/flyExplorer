# 2026-09-28: Windows 11 MFC UI DPI/theme and native scrollbar audit

Scope: main 067a77d3 plus the narrow column-width patch on
tests/ui-dpi-theme-regression-20260928. The Phase 5 WinUI experiment
is independent and was not changed.

## Actual host and verified DPI / contrast matrix

Windows 11 version 10.0.26200; ONE actual monitor, 1280x1024,
effective 96 DPI. Both initial and final SPI_GETHIGHCONTRAST flags
were 126 (HC OFF). Final monitor DPI/resolution matched the initial
state. User-wide scaling and contrast settings were NEVER changed.

| Display scaling | Actual monitor DPI | Dark real GUI | Light real GUI | Real Windows HC GUI |
| --- | ---: | --- | --- | --- |
| 100% | 96 | PASS | PASS | NOT TESTED |
| 125% | 120 | NOT TESTED | NOT TESTED | NOT TESTED |
| 150% | 144 | NOT TESTED | NOT TESTED | NOT TESTED |
| 200% | 192 | NOT TESTED | NOT TESTED | NOT TESTED |

The attached display cannot expose the other actual DPIs; no
Windows Sandbox or installed VirtualBox executable was available.
Changing global display scaling can affect a real user desktop and
require sign-out, so unverified DPIs were NOT simulated or declared
tested. Enabling global Windows HC on the live user session likewise
was not considered safe to restore without a disposable VM.
A separate source contract checks the real GetDpiForWindow path,
MulDiv scaling formula at 96/120/144/192, dynamic DPI message
handlers, SPI_GETHIGHCONTRAST and system palette / overlay bypass.
This is STATIC evidence only for the missing environments.

## Existing MFC scrollbar source inventory and actual coverage

The existing UI_SCROLLBAR_MODAL_OVERLAP_AUDIT_20260928.md enumerates
every known native source reference. The previous common ModernUI
hook covers raw dialog CListCtrl/CTreeCtrl/ListBox/scrollable Edit
plus explicit BookmarkSetWnd, while ListCtrlEx, TreeCtrlEx and
ComboBoxEx address popup keep specialized native handling.
This run adds observed verification on the active 96-DPI desktop:

| Area / behavior | Dark GUI | Light GUI |
| --- | --- | --- |
| Main ExplorerCtrl native list vertical and horizontal arrows | PASS | PASS |
| Native folder TreeCtrlEx vertical and horizontal arrows | PASS | PASS |
| File-list vertical thumb drag, native track and wheel | PASS | PASS |
| Native list/tree overlay present in Dark, absent in Light | PASS | PASS |
| Native address ComboBoxEx popup modal dismissal / overlay cleanup | PASS | PASS |
| ColumnSetDlg native list scroll, header, numeric edit | PASS | PASS |
| Generic OTHER legacy dialog ListBox/Edit/Tree screens | SOURCE ONLY | SOURCE ONLY |
| Actual visible BookmarkSetWnd scrollbar | SOURCE ONLY | SOURCE ONLY |

The owned main was resized to 980x730. Native vertical and horizontal
scroll range and actual screen scrollbar geometry were checked for
both main list and folder tree; actual pointer clicks moved the
native scroll positions in BOTH themes. Main-list native vertical
thumb dragging moved scroll position 4 to 10; a real track click
moved 10 to 31, followed by mouse-wheel movement 31 to 40.
No dark layered scrollbar overlay remained in Light.

For the owned column modal, actual Dark/Light header dark sample
ratios were about 0.925/0.035. Actual native header divider dragging
changed column width from 170 to 192; actual list scrollbar pointer
click moved first visible item 0 to 1. The private copied settings
and synthetic file fixtures were used, not user-installed data.

## Live themes, compact layout, popup/modal isolation

An owned main running Light received the existing real theme
command to change to Dark without restarting; the actual modal
header rendered Dark. Switching back to Light in the same process
produced a native address popup dark ratio about 0.018 with ZERO
remaining dark overlays and a reopened Light modal header ratio
about 0.035. A separate 790x610 owned main at actual 96 DPI
passed the same live transitions. Address-bar bottom was 304px,
modal top 314px (10px gap); the numeric width input and adjacent
px unit label did NOT overlap or extend beyond the dialog.
Normal-width owned Dark and Light runs also passed the existing
modal/address no-overlap and popup cleanup checks.
A smaller real MONITOR resolution was not tested by resizing the
owned main window; these are separate environments.

## Newly discovered and fixed real native column-width defect

PRE-FIX actual real-product test: the visible, non-pinned Size
column changed from width 80 to width ZERO after physically typing
0 in ColumnSetDlg and clicking its actual OK button. The data
assignment used an unchecked GetDlgItemInt in FOUR independent
commit paths, and ES_NUMBER did not enforce usable width bounds.

The narrow fix introduces one common readEditedColumnWidth helper
used by all four commit paths. A NEW edit is normalized to
24..4096 native pixels at 96 DPI, scaled from the actual dialog
DPI for other real displays when available. Parsing saturates
before integer overflow. Empty / invalid parsing restores the
previous selected width. Unchanged pre-existing values are
preserved, including historically out-of-range stored values;
there is no forced migration of user preferences.

POST-FIX actual owned GUI gates:
- Physical keyboard 0 / actual native OK: Size 80 -> 24.
- Physical keyboard 99999 / actual native OK: Size 24 -> 4096.
- Actual alphabetic entry attempted in the numeric Edit: the
  native ES_NUMBER field rejected it and the real Size width
  remained 4096; this third diagnostic dialog was canceled,
  NOT treated as a successful invalid-input OK action.
- The new source contract checks all four commit call sites,
  scaled range, saturating parse and unchanged-value preservation.

## Reproducibility, user-state protection, final outcome

GUI scripts: build/test_ui02_modal_scrollbar_runtime.py (existing);
build/test_ui_primary_scrollbars_runtime.py;
build/test_ui_live_theme_runtime.py (pass --live-theme and optional
--narrow); build/test_ui_column_width_bounds_runtime.py.
New source contracts: build/test_ui_column_width_bounds_contract.py
and build/test_ui_dpi_high_contrast_contract.py. The latter verifies
source and positive DPI arithmetic, NOT real high-DPI/HC GUI.

Release-x64-Unicode x64 product INCREMENTAL BUILD: PASS after product
source changes. Tested binary SHA256:
137DDA525F0D1FDAE62475DE4FA2A5C1E38A916FAA76C63479BB6B3235AC828C.
Final Dark/Light modal GUI, final primary Light GUI (native arrows,
thumb, track, wheel), final compact live-theme GUI and physical
min/max/invalid keyboard gates PASS. Primary Dark thumb/track GUI
PASS on the same final product revision. SIX relevant source test
suites, source invariant validator and native functional regressions
17 passed / 0 failed. All test-owned processes exited normally.
Original SIX user config SHA256 values matched after each run.

Screenshots and raw logs stay LOCAL under ignored logs, with no
personal files committed. The sole actual monitor remained 96 DPI,
1280x1024; Windows HC remained OFF. No installer/full clean-machine
build or GitHub Actions was run. The user's original untracked
main-window.png and separate Phase 5 worktree were preserved.

## Merge and next isolated-environment gates

The real 96-DPI native non-pinned column-width defect, source fix
and focused tests meet their merge gate independently. The 120,
144 and 192 ACTUAL DPI modes and real Windows High Contrast require
a disposable VM or an appropriately configured additional monitor
before they may be marked PASS. Individual additional raw dialog
ListBox/Edit and BookmarkSetWnd screen-level checks remain OPEN.
A later independent source patch must be justified by real failed
evidence in those environments, not guessed from source math.
