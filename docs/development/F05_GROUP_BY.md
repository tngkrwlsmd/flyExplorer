# F05 — Four-mode file grouping: implementation and bounded acceptance

## Scope and design

Grouping is opt-in via the active pane's View menu. Commit `8e4bfe99`
extends the original type grouping to four modes: Type (유형), Name
(이름), Size (크기), and Modified Month (수정 월). All four require
Details mode, complete resident/indexed enumeration, synchronized
metadata, matching route/tab/side identities and at most 25,000
indexed items.
Unsupported or incomplete folders revert safely to the ordinary
list instead of presenting a false complete-group claim.

Type groups classify folders, filename extensions and extensionless
entries; the additional modes bucket the existing bounded filename,
size and last-modified metadata. Group headings are not real files and
never carry a Shell item identity. Real selectable rows retain their
original logical identities and parsing paths, with 160 file rows on
the initial page. Each pane/window-tab stores its own group mode and
collapse state. Switching tabs may defer restoration until that tab's
current complete metadata model is available; obsolete route identity
is never a license to render stale group rows.

## Files and tests

- app/winui/file_group_projection.h: bounded full-model type buckets
- app/winui/file_group_modes.h: name/size/month bucket projection
- app/winui/file_group_presentation.h: scoped collapse and paging
- app/winui/file_group_tab_cache.h: per-pane/route/tab deferred group restoration
- app/winui/FileToolbar.xaml and C++ code: View menu toggle
- app/winui/file_list_state.h and MainWindow.xaml.cpp: pane ownership,
  presentation rendering, guarded selection and disclosure callbacks
- tests/winui/native_f05_group_projection.cpp and
  tests/winui/native_f05_group_presentation.cpp: model probes
- tests/winui/test_f05_group_projection_contract.py and
  tests/winui/test_f05_winui_group_integration_contract.py:
  source contract checks
- tests/winui/test_f05_group_gui.py: real owned type-group GUI probe
- tests/winui/test_f05_group_modes_gui.py: opt-in four-mode owned GUI probe
- tests/winui/native_f05_group_modes.cpp and
  tests/winui/native_f05_group_tab_cache.cpp: extended native probes

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

The original type-grouping implementation has real independent left/right
pane and left-tab acceptance recorded below. The newly integrated Name,
Size and Modified-Month modes, including their per-tab restored collapse
state, still require dedicated **actual Windows GUI** acceptance; the
source-level contracts alone do not prove those interactions. The F05
original Light/Dark pixels also remain unreviewed. Further separate gates:
active High Contrast, Narrator speech, actual 125/150/200% Windows DPI,
large-folder GUI, full keyboard-only disclosure and provider/non-Details
behavior. Non-Details grouping is intentionally unsupported, not an
unimplemented promise of automatic fallback.

Do not change real user folders or system display settings solely
for these tests. Keep an explicit acceptance status for each scope.

## 2026-10-15 Earlier dual-pane attempt — FAIL (superseded by later acceptance)

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
- **As of the earlier failed attempt:** independent
  collapse, route and multiple window tab behavior had not yet
  passed. The later accepted runs below supersede those limits;
  screenshot pixel review remains pending.


## 2026-10-15 Final scope: both panes and left pane tabs accepted

**Exact `main` test SHA:** `10bfbce585d2e8e773bba56b30fa0a046a1a20a4`.
Original product C++/XAML implementation is unchanged from
`c14be710`; the existing clean Release was reused.

- [Windows owned UI #38712034722](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38712034722):
  **SUCCESS**; actual right/left group headings, per-pane Markdown
  and Log collapse, pane switching, right-folder route reset,
  eight source contracts, clean app exit, original six preference
  hashes unchanged, synthetic fixture removed.
- [Windows owned UI #38712448964](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38712448964):
  **SUCCESS**; repeated the preceding checks and proved
  `F05_LEFT_TAB_ADD_RIGHT_PANE_SAFE=PASS`,
  `F05_LEFT_TAB_SELECT_ORIGINAL=PASS`,
  `F05_LEFT_TAB_SWITCH_AND_CLOSE_ISOLATED=PASS`.
  Both file panes retained test-owned file rows across tab add,
  selected-tab change, and close.
- The failed predecessor [#38693990951](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38693990951)
  and follow-up diagnosis [#38711709550](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38711709550)
  found the live left-pane grouping menu returned ToggleState
  `0` both before and after `click_input()`, although the
  pane was active. The accepted harness focuses the same
  owned WinUI ToggleMenuFlyoutItem and sends physical Enter;
  it correctly toggles group state. This resolves the bounded
  automated input failure, without claiming mouse-only parity
  for every screen or that C++ code was defective.
- **Not certified:** original F05 Light/Dark screenshot pixels,
  narrator spoken announcements, High Contrast, 125/150/200%
  DPI, large directory practical performance, the newly integrated
  name/size/modified-month GUI behavior, or arbitrary shell providers.


## 2026-10-15 Four-mode integration: new behavior requires its own acceptance

- Product integration: `8e4bfe990f0a5fec6cd83888f58ebb9df707555b` on `main`.
  The new menu routes four explicit modes through the active pane; native
  projection uses existing metadata and retains logical Shell file identities.
  A bounded per-tab cache defers collapse restoration until the original
  route's complete model is available.
- Source-contract corrections following the initial central run:
  `aa5039afe6c22382b4e240bba7ae91abe77e8f91` (exclude heading
  selection as a command target), `694f4a067495bd81e9940a0d7314bf9f29cb48ee`
  (group-file count versus sequential resident offset), and
  `a378722ab87221c1415b07281e64fca6fd979cd2` (legitimate F03
  Preview terminology versus retired product branding). These are
  **test-only** corrections, not changes to the grouping product code.
- **Evidence limit:** pre-expansion type grouping and independent pane/tab
  GUI evidence cannot certify the newly added modes. Neither the presence
  of an opt-in four-mode GUI test nor a general central GUI acceptance
  automatically certifies focused F05 mode interaction or final pixels.
