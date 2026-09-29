# Phase 6 UXH-05: custom tab native accessibility ? scoped acceptance

**Date:** 2026-09-28. **Baseline main:** ede85f35006cd69360944afc634b4c6ce6f4079f.
**Status:** Actual Dark/Light 96-DPI programmatic UIA/MSAA,
native accessible action and existing keyboard scope ACCEPTED.
Real spoken screen-reader output, actual High Contrast/larger
DPI, UIA InvokePattern and wider Tab/F6 focus assessment remain
**NOT TESTED or separately limited**; do not claim full
accessibility certification.

## Reproduced baseline defect

The existing drawn TabCtrl inherited from CWnd and did not
enable the MFC active-accessibility provider. In a fully
owned isolated Windows GUI, real Ctrl+T created three tabs
and Ctrl+Tab/Shift+Ctrl+Tab changed the selected folder,
but UI Automation showed only unnamed Pane/zero descendants
and MSAA showed CLIENT role/zero children. Baseline
evidence: ignored local logs/uxh05-owned-baseline-msaa-uia.log.

## Minimal, existing-framework correction

Only gui/TabCtrl.h and gui/TabCtrl.cpp implement the product
fix. Native MFC EnableActiveAccessibility exposes the
real TabCtrl as page-tab-list and its actual full stored
tab titles as page-tab children, each with selected/focus
state and proper screen geometry. The visible selected-tab
close glyph and optional new-tab glyph now provide named
pushbutton children, using existing localized tooltips.
IAccessible selection/focus/hit-test/default actions reuse
native setCurTab and existing observer new/close callbacks,
not synthetic test WM_COMMAND or a new UI framework.

Native reorder, tab-title name-change, selection and focus
events are posted. The strip is focusable and paints a
focus rectangle when focused. An explicit physical arrow,
Home or End operation on a focused tab strip now
restores focus to the strip after the existing pane observer
focuses the destination file list. Standard Ctrl+Tab
focus behavior and native tab storage remain unchanged.

## Final clean Release x64 actual acceptance

**Final executable SHA256:** CCB5050EC1AE316CB3D6C4728A1DDF9A724D3319DA40305CC5880B4A422ABB10.

| Actual owned test | Evidence |
| --- | --- |
| Before fix, two real Ctrl+T operations | UIA Pane / 0 items; MSAA CLIENT / 0 children |
| Final Dark and Light, 96 DPI, two real Ctrl+T operations | UIA Tab with 3 named TabItems; MSAA names, page-tab roles and exactly one selection |
| Real Ctrl+Tab and Shift+Ctrl+Tab | Selected tab and actual folder change |
| Accessible TAKEFOCUS/TAKESELECTION | Real focused/selected child index 1 |
| Real consecutive focused Right, End, Home | Actual tab selection and focus retention PASS |
| External MSAA tab Select, selected Close, New | Actual owned tab-selection, close and new behavior PASS |
| Actual Ctrl+W after accessibility new action | Real selected tab closes PASS |
| Close/new named buttons and accessible location | Localized UIA Button nodes and real MSAA bounds/actions present |
| Source contract, source invariants and clean Release | PASS |
| Existing native functional executable | 17 PASS, 0 FAIL |
| User configuration protection | All original six SHA256 values unchanged; owned test processes normal exit |

Test sources are build/test_ui_uxh05_tab_accessibility_runtime.py
and build/test_ui_uxh05_tab_accessibility_contract.py.
Full logs and screenshots are ignored and kept only on the
development computer. The tested x64 product binary above
is Release, not Debug.

## Explicit unresolved accessibility/environment gates

Physical Tab and F6 pressed **from a programmatically
focused tab strip in the owned single-pane profile**
did not move its accessible focus or selection. This
is a concrete focus-route observation, not a Tab/F6 PASS.
The existing F6 command is next-window rather than a
dedicated tab command; wider multi-pane focus traversal
remains untested. Independent physical Ctrl+Tab,
Shift+Ctrl+Tab and focused arrow keys passed.

No real screen-reader spoken/braille listening session
was performed. NVDA was not detected in standard
installation paths, and Windows Narrator was not launched
on the user's existing desktop. Source native WinEvent
calls are present, but an independent external WinEvent
listener was not validated. UIA TabItem/selected states
and named Button nodes passed; UIA InvokePattern direct
actions were not separately tested beyond real MSAA
default-action invocation.

Read-only system query found Windows High Contrast OFF.
Actual High Contrast, actual 125%, 150% and 200% DPI
remain NOT TESTED; original OS display/accessibility
settings were not modified. Full manual accessibility
review must remain a separate follow-up.

## Ownership and evidence preservation

Full local-only logs: logs/uxh05-owned-baseline-msaa-uia.log,
logs/uxh05-after-minimal-msaa-uia.log,
logs/uxh05-arrow-focus-origin-diagnostic.log,
logs/uxh05-real-ia-accessible-actions-after-focus-fix.log,
logs/uxh05-final-acceptance-batch.log,
logs/uxh05-final-*.log, and
logs/uxh05-physical-tab-f6-probe.log.
All accepted sessions used dedicated test processes
and copies of the six original settings, and did not
edit personal files. The WinUI 3 experimental worktree,
user main-window.png and manually triggered GitHub
Actions were not involved.


## Residual direct UIA verification (2026-09-28)

An external UI Automation client in a real 96-DPI
owned Windows 11 session found and **invoked** native
InvokePattern on New and selected Close buttons.
The live accessible child count changed **5 -> 6 -> 5**
after actual new and close commands. No synthetic
WM_COMMAND was used. The test-owned process exited 0
and all six original settings SHA256 hashes matched.
Read-only Windows APIs reported 96 DPI, High Contrast OFF.

Repro command: python build/test_ui_uxh05_residual_runtime.py
--invoke-probe --invoke-actions --env-inventory
--assert-accessibility. Ignored full log:
logs/uxh05-real-uia-invoke-new-close.log.

An optional private 1x2 focus-route experiment spawned
two native tab controls but could not acquire stable
test-owned foreground tab focus from the external client.
That attempt is **INCONCLUSIVE / NOT TESTED** for
multi-pane Tab/F6; an isolated diagnostic returned nonzero
and original user configuration remained unchanged.
The failing probe was NOT added to the accepted test.
Narrator spoken-output, independent WinEvent listener,
real 125/150/200% DPI and High Contrast remain NOT TESTED:
no known safe VM was available and the global original
desktop was not altered.
