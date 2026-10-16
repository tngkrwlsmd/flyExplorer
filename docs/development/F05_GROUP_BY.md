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
Size and Modified-Month modes, including per-tab restored collapse, have now
passed dedicated **actual Windows GUI** acceptance as recorded below.
The F05 original Light/Dark pixels remain unreviewed. Separate gates:
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


## 2026-10-15 Four-mode integration (historical pre-acceptance status)

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
- **Evidence limit at this date:** pre-expansion type grouping and independent
  pane/tab GUI evidence did not certify the new modes. The later focused
  Windows test below closed this functional gap, but not visual acceptance.

## 2026-10-16 Four-mode focused Windows GUI — PASS

- **Exact accepted source SHA:** `e1a95f6adee897c803e2dfec74e93a43953878b3`.
  The grouped product implementation was introduced at `8e4bfe99`;
  following source-contract fixes did not change the product C++/XAML.
- [Central CI #38736462369](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38736462369)
  **SUCCESS** for product-identical SHA `a378722a`: source and policy,
  Windows Release, window/tab, shortcuts, filter presets and complete
  default GUI checks. The subsequent `e1a95f6a` diff was documentation.
- [Focused actual Windows GUI #38809769293](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38809769293)
  **SUCCESS** for exact `e1a95f6a` on 2026-10-16 06:44 KST:
  17 targeted F05 source contracts passed; Release was rebuilt; actual
  interactive WinUI confirmed **Name, Size, Modified Month, Type** headings,
  collapse isolation, a newly ungrouped tab, original-tab collapse restore,
  close-tab coherence and explicit grouping opt-out. The run emitted
  `F05_FOUR_MODES_AND_TAB_GUI_PASS=True` and all nine individual
  `F05_GUI_*=PASS` checks.
  The application exited with code 0, all six original user-setting file
  SHA-256 hashes remained identical and the test-owned folder was removed.
  Bounded test evidence remains in the owned Windows evidence directory.
- **Separate pending gates:** `VISUAL ACCEPTANCE: NOT TESTED` for F05
  Light/Dark composited pixels; actual 125/150/200% DPI, active High
  Contrast, Narrator speech, keyboard-only disclosure end-to-end,
  large-directory GUI performance and arbitrary Shell providers remain
  unverified. Do not infer those outcomes from UI Automation success.

## 2026-10-16 Four native C++ probes — PASS; outer Windows task timeout

- **Exact tested source SHA:** `1f85741cd1ec183719cc0cbce1d2460d89ab033a`.
  The canonical `tools/winui/run_f05_group_native.py` now runs four
  sources, including `native_f05_group_modes.cpp` and
  `native_f05_group_tab_cache.cpp`. MSVC invokes `/utf-8` along
  with `/W4 /WX` so the Korean cp949 environment does not reject
  valid UTF-8 source as warning C4819. A source contract guards both
  the four-source list and this required compiler option.
- [Windows compiler run #38823430041](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38823430041)
  **GitHub Actions FAILURE** because the outer scheduled-task worker
  did not write its final `result.json` before a seven-minute timeout.
  The failure is **not** an observed native assertion or compiler failure.
- [Read-only evidence #38826356423](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38826356423)
  and [binary/marker verification #38826480894](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38826480894)
  both **SUCCESS**: eight focused Python contracts showed `OK`; the
  retained native log independently recorded all five markers:
  `F05_NATIVE_COMPLETE_MODEL_GROUPING_PASS`,
  `F05_NATIVE_COLLAPSIBLE_GROUP_PAGE_PASS`,
  `F05_NATIVE_GROUP_NAME_SIZE_MONTH_PASS`,
  `F05_NATIVE_PER_TAB_GROUPING_PASS`, and
  `F05_NATIVE_ALL_FOUR_GROUP_AND_TAB_PROBES=PASS`.
  Each of the four corresponding .exe outputs exists under the
  test-owned `out/f05-native` directory at that exact SHA.
- **Scoped verdict:** all four **native C++ compilation/execution probes
  PASS**, and eight focused source contracts PASS. The outer one-shot
  worker's final-result/exit contract is **NOT ACCEPTED**; the Actions
  run itself must not be relabeled as success. No additional product
  C++/XAML change was made. F05 GUI acceptance remains scoped to
  the earlier exact GUI binary; Light/Dark visual pixels are still
  **NOT TESTED**.

## 2026-10-16 XAML Light/Dark capture diagnostics — NOT ACCEPTED

- **Source under GUI trials:** `91179a0e` (first owned XAML capture)
  and `6b0f8865` (guarded UI foreground retry). All new native
  screenshot code is test-opt-in, with output under ignored
  `logs/f05-visual-modes/` and isolated `LOCALAPPDATA` preferences.
- [Source CI #38854939427](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38854939427)
  **SUCCESS** at `91179a0e` for policy and source, not Release/GUI.
  [Windows attempt #38855103261](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38855103261)
  **FAILURE**: retained output confirms `flyExplorer.exe` was linked;
  however `Start-Process -Wait` in the scheduled worker did not reach
  `result.json` (11-minute timeout). Binary generation is not a
  successful outer worker completion.
- [GUI-only attempt #38866523813](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38866523813)
  confirmed a **nonblank 944×510 actual XAML** `before.png` at 96 DPI.
  All six protected original configuration hashes were unchanged,
  the owned fixture was removed and app exited 0. Subsequent physical
  group-menu input was refused because the app was not foreground.
  [Guarded focus attempt #38866979641](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38866979641)
  likewise refused input after bounded attempts to focus the owned HWND.
  This is an interactive desktop input-gate failure, **not evidence of
  incorrect grouping functionality**.
- [Owned screenshot review transfer #38867304886](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38867304886)
  retrieved and visually inspected the exact test-owned baseline PNG
  (`light-aljdaevm/before.png`, SHA-256
  `6f3cbbacc3263a7ea2c08b9dea6b04c570749c791c27bf35965c54a6b000d6c4`).
  Although labeled `light`, the captured actual window pixels are
  **dark**. The isolated preference fixture accidentally wrote literal
  backslash-r/backslash-n characters instead of CRLF. Corrected in
  `8f67352e`; protected by source contract `7717d8e0`.
  The fix has **not yet been revalidated by actual Windows Light-theme
  screenshots**; the earlier dark pixels must not be reused as Light PASS.
- **Current verdict:** F05 GUI grouping functionality retains its earlier
  exact-SHA PASS. App-owned XAML baseline capture is technically proven,
  but **F05 LIGHT/DARK VISUAL ACCEPTANCE: NOT TESTED** for the corrected
  fixture and grouped states. Dark theme capture and group-mode visual
  comparison have not completed. OS 125/150/200% DPI, active High Contrast,
  Narrator speech and keyboard-only full workflow remain independent gates.

## 2026-10-16 Baseline-only acceptance path (prepared; not yet executed)

- **Main test-only SHA:** `9077a1ac39e68c3a0232613bb09e255131ae2846`.
  The private-preferences CRLF fix (`8f67352e`) and its regression
  contract (`7717d8e0`) are included.
- The F05 owned GUI harness now recognizes opt-in
  `FLY_F05_VISUAL_BASELINE_ONLY=YES` *only together with*
  `FLY_F05_VISUAL_CAPTURE=YES`. It captures app-owned XAML
  `before.bmp`/`before.png` and exits normally without physical input.
  It emits `F05_VISUAL_BASELINE_GUI_PASS=True`, **not**
  `F05_FOUR_MODES_AND_TAB_GUI_PASS=True`. The latter remains reserved
  for actually exercised group-mode interactions.
- **Next independent Windows acceptance:** verify the exact source SHA,
  run the focused source contracts, reuse the same accepted Release
  binary (no C++/XAML changes since `91179a0e`), exercise Light and
  Dark baseline-only in separate test-owned profiles, verify six real
  user settings unchanged, exit 0 and both image hashes, then retrieve
  and inspect both original XAML pixels before assigning theme PASS.
  Grouped-state Light/Dark screenshot comparison remains separate.
- No Windows acceptance or pixel review has been claimed for this
  corrected baseline-only mode yet. The shared central Remote Shell
  request was occupied by an unrelated request at the latest preflight;
  **do not replace or overwrite that request**. Await an idle slot or
  use another explicitly authorized independent route.
