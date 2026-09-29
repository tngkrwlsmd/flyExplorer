# Phase 6 UXH-03 — responsive native per-pane information layout (2026-09-28)

**Scope:** Actual Windows 11 x64, real 96 DPI, isolated Dark and Light
MFC GUI runs. Code baseline: `main`
`248f85c257d7d40af0cb9a6a0341d7f93d08c1ab`.
This improvement affects the existing MFC product only; the separate
WinUI 3 Phase 5 experiment remains untouched.

## 1. Observed root cause and minimal fix

The existing ExplorerPane already dynamically shrank its fixed 224-DIP
Explorer-style information sidebar to roughly one-third of the pane.
This did not prevent both sidebar text and native list filenames from
severe clipping when the overall window was 750 px wide and split 1x2.
A genuine owned baseline captured an 88-px sidebar and only 178/176 px
of usable native file-list width, with vertically fragmented descriptions
in both sidebars. The global folder-tree panel also consumed width.

When the **saved Explorer-style information bar is enabled** and a
sidebar would leave less than 280 DPI-scaled px for the file list,
ExplorerPane now switches just that pane's *existing ContentsWnd*
to the existing Basic-style horizontal visual summary (36 DIP high).
The summary continues to display its own pane's current folder icon
and name. The native file list gains the full available pane width.
Each ContentsWnd retains its original folder/selection data and bookmark
child; off-screen bookmark controls are hidden from keyboard focus
only while compact. At a sufficiently wide pane, the original Explorer
sidebar, its bookmark control and the previously saved settings return.
No new persisted option, global style mutation, tab recreation or
file-list column-width reset was introduced. The existing Basic and
disabled information-bar settings remain unaffected by this condition
(source contract; not separately acceptance-tested as GUI modes).

## 2. Before and after: measured real Win32 HWND geometry

Widths are actual px at real 96 DPI, using the same synthetic fixture
and identical 750-px outer-window conditions.

| Actual layout | Pane width | Prior sidebar / file list | New info summary / file list | Result |
| --- | ---: | ---: | ---: | --- |
| 750px outer window, 1x2, left | 266 | 88 / 178 | 266-wide by 36-high / 266 | +88 list px |
| 750px outer window, 1x2, right | 264 | 88 / 176 | 264-wide by 36-high / 264 | +88 list px |
| 750px outer window, 2x2 | 266/264 | No paired pre-change 2x2 baseline recorded | All four 266/264-wide horizontal summaries and lists | No sidebar overlap |
| 1100px outer window, 1x2 | 441/439 | 147/146 side; 294/293 list | Same 147/146 side; 294/293 list | Original wide layout |
| 1200px outer window, 2x2 | 491/489 | 163 side; 328/326 list | Same 163 side; 328/326 list | Original wide layout |
| Restored wide single pane | 982 | Not measured at the identical starting geometry | 224 side / 758 list | Original Explorer layout |

A visual review of the owned 750px screenshot confirmed that the
left summary showed the private fixture and the right summary showed
the distinct second pane's folder, rather than duplicating the
previous narrow sidebar with clipped bookmark descriptions.

## 3. Scoped actual-GUI, build and regression evidence

- Real 96-DPI owned Dark and Light: single, 1x2 at 1100 and 750 px,
  2x2 at 750 and 1200 px, resizing back to wide 1x2, and restoring
  the original single-pane layout: **PASS**. HWND coordinates showed
  the compact header ends where the file list begins, without
  overlapping hit surfaces.
- A **real keyboard** Win+Up / Win+Down maximize and restore changed
  the two owned panes from compact to their full-width Explorer info
  sidebars and back: **PASS**.
- A **real mouse** double-click of the owned title bar to maximize,
  followed by a second double-click to restore, exercised the same
  transition with both panes: **PASS**.
- Owned copied `config.info_bar.show=1` and
  `config.info_bar.style=1` stayed unchanged after execution.
  Original user's **six config SHA256 hashes unchanged** in every run;
  all tested owned app processes exited with code 0.
- Scoped Release-x64-Unicode x64 **incremental product build PASS**;
  contract `build/test_ui_uxh03_responsive_info_contract.py`,
  source invariants, original layered-scrollbar and address contracts:
  **PASS**. Existing native functional tests: **17 PASS / 0 FAIL**.
- Final tested executable SHA256:
  `4208C37E9133146BE527EB698D20F83DC47C6B9B5992318D6AB04F6C3A5662E0`.
- Reproduction and acceptance harness:
  `build/test_ui_uxh03_pane_layout_runtime.py`. Full logs and
  privately owned screenshots remain locally under ignored
  `logs/uxh03-*`; no user screenshots or profile files are committed.

## 4. Remaining boundaries and next work

At 750px with 2x2 panes, the recovered list width does not resolve
the independently limited **vertical** space caused by multiple
global toolbars, a folder tree, tab headers and status bars.
UXH-04 should measure compact command access separately; do not
remove or hide user toolbars as part of this pane-layout fix.

Actual 120/144/192-DPI, Windows High Contrast, separate GUI acceptance
of preconfigured Basic/hidden info-bar preferences, real screen-reader
tab usability and broader Shell namespace behavior are **NOT TESTED**
by this particular campaign. The opt-in WinUI 3 PRI/deployment
experiment remains separate. Do not describe this scoped result as
general cross-DPI certification.
