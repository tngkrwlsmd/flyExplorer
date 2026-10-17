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
  The earlier dark pixels must not be reused as Light PASS; later
  corrected theme-specific RGBA baseline verification is below.
- **Current verdict:** F05 GUI grouping functionality retains its earlier
  exact-SHA PASS. App-owned XAML baseline capture is technically proven,
  but at that time **F05 LIGHT/DARK VISUAL ACCEPTANCE: NOT TESTED**
  for the corrected fixture and grouped states. Later baseline-only
  verification below does not establish full grouped/composited QA. OS 125/150/200% DPI, active High Contrast,
  Narrator speech and keyboard-only full workflow remain independent gates.

## 2026-10-16 Baseline-only Light/Dark XAML capture — PASS; compositor review open

- **Original baseline-only source SHA:** `3976779e14a691ecff2f3c58a479c0cec49ab35a`.
  [Real Windows run #38868358300](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38868358300)
  **SUCCESS**: Light and Dark used separate disposable preferences,
  both captured 944×510 app-owned XAML bitmaps at actual 96 DPI, both
  ran 19/19 F05 source contracts, both exited 0, all six original user
  configuration hashes remained identical, and temporary fixtures were
  removed. `F05_VISUAL_BASELINE_GUI_PASS=True` is intentionally distinct
  from four-mode group interaction acceptance.
- **Alpha diagnosis:** [run #38868792850](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38868792850)
  confirmed roughly 92% of sampled XAML pixels were transparent in both
  themes. The original Pillow BI_RGB-to-RGB conversion dropped alpha,
  making transparent regions appear black, so a black Light preview
  does **not** establish a Light product regression.
- **Lossless-alpha correction:** `40a13f78` explicitly decodes the
  top-down BGRA pixel buffer from the test-owned BMP into RGBA PNG and
  keeps a separate theme-background composite marked
  `DIAGNOSTIC_COMPOSITE_NOT_REAL_BACKDROP=True`. Source contract
  `26dce015` guards this. [Windows run #38869630768](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38869630768)
  **SUCCESS** at exact SHA `26dce015acb59da47d6fe8ee5cb46c55c6a63e14`:
  Light original RGBA PNG SHA-256
  `5b9d44e7e4066f2ab4c34ea026a79b8832a5d002ebb8ee54d5c400020c59a412`;
  Dark original RGBA PNG SHA-256
  `42d7e2f2ea0783c01f02d391669c9f44d1f83c3032663094d9d51e0e1f3ccce3`.
  Both have full exact-SHA 19-test contracts PASS, XAML baseline capture
  PASS, owned WinUI exit 0, and original user settings unchanged.
- **Acceptance boundary:** app-owned XAML *foreground RGBA extraction*
  and theme-specific baseline-only test workflows **PASS**. This is
  **not** original Windows DWM backdrop/final-composited-pixel
  inspection. The generated white/dark background composite is a
  **diagnostic reconstruction**. F05 grouped Light/Dark states were not
  captured after the current changes because keyboard/menu input was
  correctly refused when the shared user desktop could not grant the
  test app foreground ownership. Consequently, **F05 GROUPED FULL
  VISUAL ACCEPTANCE: NOT TESTED**. Actual 125/150/200% DPI, active High
  Contrast and Narrator spoken output remain independent open gates.

## 2026-10-16 F05 grouped XAML Light/Dark matrix — Release and 8/8 owned captures PASS

- **Product + test-hook Release source SHA:** `d2ed08d6cfe5f2f6235abe221657d19038e5a1f8`.
  [Central CI #38891026338](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38891026338)
  **SUCCESS**: `PASS release-build`; `flyExplorer.exe` linked on
  Windows with the opt-in grouped XAML capture timer. A second build
  in the retained owned workspace produced `flyExplorer.exe` SHA-256
  `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`.
  Its *outer* worker [#38894797967](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38894797967)
  still reported FAIL because the script did not receive its
  build-process exit code. Do not relabel that Actions run as PASS;
  the independent central Release PASS and later binary-checked GUI
  acceptance are the successful evidence.
- **Latest test source SHA:** `d51c2af050c01a56d52698eba99a34a45c42f5d7`.
  Relative to the compiled product SHA, only two Python F05 test
  files changed. The updated test allows an already-applied *Type*
  group at the pre-interaction checkpoint; the earlier Type fixture
  failed on an invalid `.md`-must-be-absent assertion despite the
  actual grouped UI already appearing. No product/XAML compilation
  or behavior change was needed for that harness correction.
- **All eight 944×510, 96 DPI owned grouping presentations:** passed
  real WinUI UIA heading checks, preserved-alpha XAML screenshots,
  normal process exit, and protected legacy user settings.
  [Light Name #38895272394](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38895272394),
  [Light Size #38895710455](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38895710455),
  [Light Type/Month and Dark Name #38896686119](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38896686119),
  [Dark Type/Size/Month #38896939618](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38896939618).
  All captures are in ignored, test-owned
  `logs/f05-visual-modes/` paths and are not committed image fixtures.
- [Read-only diagnostic image review #38897312601](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38897312601)
  verified all eight original RGBA hashes and inspected the four
  views per theme with separately applied neutral matte backgrounds.
  Name, Size, Month and Type group labels, disclosure arrows and file
  rows were visible without apparent control overlap in these
  **diagnostic composites**. Some long file-type descriptions were
  ellipsized in narrow columns; Dark grouped headings had less
  conspicuous bands than Light. This is a diagnostic observation,
  **not a finding about the actual DWM backdrop**.
- **Scoped verdict:** Windows Release **PASS**; test-owned grouping
  presentation and foreground XAML RGBA extraction **8/8 PASS**;
  synthetic-background image inspection **DONE**. Current Windows/DWM
  final-composited Light/Dark screenshots, real OS 125/150/200% DPI,
  High Contrast, Narrator speech and Korean IME remain separate
  **NOT VERIFIED** gates. This fixture never sends actual View-menu
  physical keyboard input; do not substitute its result for the
  independently scoped real GUI acceptance at `e1a95f6a`.

## 2026-10-17 keyboard disclosure focused harness — source PASS only

At test-only main `22ca4ed1f3fe155a97022f0fa474538a432fdce3`,
`test_f05_group_modes_gui.py` has a separate, explicitly opted-in
keyboard-only test for the test-owned Type grouping disclosure.
It requires actual foreground ownership, uses physical Space/Enter
on the .md group Button, and checks collapse/expand against its
test-owned file. `test_shell_gui.py` requires the paired modes flag
and excludes XAML capture. The original F05 GUI flows remain unchanged.

[Central source #38983687975](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38983687975)
passed policy and all source families for the exact test revision
(4 structure, 230 product, 20 harness, 30 infra).
**Actual keyboard GUI execution is still NOT TESTED**; neither source PASS
nor the existing programmatic XAML grouped captures proves it.
Final Windows/DWM composited pixels, real higher DPI, High Contrast,
and Narrator audio are also separate unaccepted gates.

## 2026-10-17 actual F05 keyboard disclosure acceptance — GUI PASS

Test-only `flyExplorer/main` SHA: `83152847b753edfb3ebffcb0b6c95db96a0d5489`. The reused Release executable
was independently verified by SHA-256
`7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`,
matching the prior accepted exact-owned full runtime. Only test/docs had
changed since the product Release source `d2ed08d6`; the original binary
and user settings were not modified.

[Windows GUI attempt #38989720309](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38989720309)
ran the opt-in `FLY_F05_KEYBOARD_DISCLOSURE_ONLY=YES` fixture under a real
interactive Explorer user session. It selected View → Type, physically
sent Space on the focused .md disclosure, observed its Markdown file row
collapse, physically sent Enter and observed the file row reappear. The
GUI worker wrote `status=PASS` and `stage=complete` to its task-owned
`result.json`.

The wrapper Action concluded **FAILURE** because the *outer PowerShell
result-aggregation command* used a malformed `-and` expression, after the
GUI worker had finished. This is a wrapper defect, not a failed GUI
assertion. No second GUI attempt was made. Independent **SUCCESS**
[read-only evidence #38989815625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38989815625)
confirmed the persisted result, source SHA, all physical Space/Enter
PASS markers, unchanged six original user configuration hashes,
unchanged Release executable, clean checkout and removed scheduled task.

**Scoped acceptance: F05 physical keyboard Type/.md disclosure PASS.**
This does not represent full-app keyboard-only navigation acceptance or
DWM-composited screenshot review. Actual native 125/150/200% OS scaling,
active high-contrast pixels and Narrator speech remain **NOT VERIFIED**.
The earlier source-only `NOT TESTED` statements in this document are
historical checkpoints superseded only by the scoped result above.

## 2026-10-17 F05 Light Name — actual Windows screen pixels reviewed (96 DPI)

- **Exact test-only source:** `7ba1f3af2ff9a6c2ccd8c9d6926cfb0b9188f52f`; product C++/XAML unchanged from
  accepted Release source `d2ed08d6cfe5f2f6235abe221657d19038e5a1f8`.
  Full sibling Release runtime reused with `flyExplorer.exe` SHA-256
  `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`.
- **Source CI:** the first [#38991252447](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991252447)
  **FAILED** at structure preflight because a shallow clone omitted the
  historical retired MFC Git objects. Central CI fix `fa7fb58f` now
  unshallows before every non-health scope. Control
  [Quality #38991458422](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991458422)
  7/7 PASS and independent
  [source #38991562290](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991562290)
  **SUCCESS**, with `CENTRAL_CI_CLONE_MODE=full-history-required-scope`,
  runner-health, policy and source stages all PASS.
- **Actual test-owned Windows user desktop:**
  [GUI #38991724639](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991724639)
  **SUCCESS** for Light / Name grouping; normal owned process exit, six
  protected user preference hashes identical. XAML RGBA was separately
  verified at 944×510, 96 DPI (SHA-256
  `46f56dadc7687333ee481f9e20c1c1e2b9598f73c3cc20187e92d4be6f30fad3`).
  A separately opt-in, verified owned-foreground screen crop yielded a
  **960×519, 42,838-byte PNG** (SHA-256
  `6883f6ffd21e1318ee9e2008f153ad2d55f63123c1d63689b240814ca7b7e500`).
  The scoped screen was hash-checked and retrieved in
  [#38991841905](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991841905).
- **Independent visual review:** actual full window chrome, toolbar, dual
  panes, Light group disclosure arrows, grouped heading bands and owned
  file icons/labels were present and readable, with no material overlap
  or unintended control clipping seen. File-type descriptions ellipsized
  in narrow columns; lower grouping rows require normal scrolling.
  These are non-blocking density limitations at the tested 960×519 window.
  **VISUAL ACCEPTANCE: PASS for the Light/Name 96-DPI owned screen only.**
  No product UI pixels were changed, so a before/after revision comparison
  was not needed; this was verification of the existing UI.
- **Not generalized:** Dark compositor, Type/Size/Month compositor,
  native Windows 125/150/200% scaling, Narrator speech and F05-specific
  High Contrast remain **NOT VERIFIED**. Earlier synthetic matte previews
  do not substitute for these separate scopes. The test did not capture
  an unrestricted desktop or change system scaling, and screenshots remain
  in ignored test-owned evidence rather than tracked source.


## 2026-10-17 actual 96-DPI F05 compositor matrix and scaling boundary

- **Live test source:** `b118c650d99ed27420d1dfd26ad291529987d210`
  (policy-only sync after the earlier compositor harness). Later
  `ebcbb2a3772931e3e6267b6e2fbc1142754c56ee` changed **only** the
  test's full-window readiness guard and its source contract.
  Product C++/XAML and the previously accepted Release runtime remained
  unchanged; executable SHA-256:
  `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`.
- **Actual DPI:** the active VM had **one interactive Explorer session**,
  display mode **1024×768** and owned WinUI `GetDpiForWindow` **96 DPI**.
  No Windows display scaling or user-global theme was changed. Genuine
  native **125% / 150% / 200%** screen acceptance remains **NOT TESTED /
  ENVIRONMENT UNAVAILABLE** in this unattended 96-DPI session. Process
  simulation or XAML pixel density does not substitute for an OS-scaled
  user desktop.
- **Dark/Name:** [real GUI #39014603977](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39014603977)
  **SUCCESS**, original six user settings unchanged, 944×510 XAML RGBA
  and 960×519 *real screen* PNG. Independent owned-image
  [inspection #39014681631](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39014681631)
  verified SHA-256 `e40d7267066cb038237567fa55d678c60f72b8c1a6cdad728715f2b366e085fc`
  and visually reviewed the pixel capture: **PASS** for Dark/Name/96-DPI.
- **Other six theme/mode cases:** [user-session matrix #39014847790](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39014847790)
  finished **SUCCESS** at that exact source SHA: Light/Type, Light/Size,
  Light/Month, Dark/Type, Dark/Size, Dark/Month each had XAML 96-DPI
  output, a foreground-owned 960×519 screen PNG, GUI fixture PASS,
  normal process exit and unchanged original profile hashes.
  [Read-only exact-image inspection #39014987543](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39014987543)
  confirmed all six screenshot SHA-256 values and inspected the actual pixels.
  **Visual review PASS:** Light/Size, Light/Month, Dark/Type, Dark/Size,
  Dark/Month. No material overlap or unintended icon/text clipping was
  seen in those sampled states. Long file-kind text may be ellipsized in
  narrow columns; additional group rows require expected list scrolling.
- **Light/Type full-window visual gate: OPEN / NOT ACCEPTED.** In the
  first screenshot the owned left pane showed correct type grouping,
  but the right file pane was blank. This must not be counted as a
  full-window visual PASS. A test-only safeguard at `ebcbb2a3` now waits
  for three known synthetic rows in `RightFiles` before sampling actual
  screen pixels; it does not change product behavior.
  The focused user-session [retest #39015238402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015238402)
  **FAILED** that bounded readiness assertion (the WinUI app still exited
  normally and existing user settings were preserved). The
  [read-only traceback #39015353869](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015353869)
  confirmed the failure. An independent, sanitized UIA evidence read
  [#39015560737](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015560737)
  **SUCCESS** found `LeftFiles` 44 descendant nodes, but
  `RightFiles` present with **0** descendant nodes, and a right tab
  without a displayed name. This is a **test-owned startup/Type visual
  scenario**, not proof of the same defect in normal user View-menu flows;
  investigate per-pane initial Shell navigation completion and the
  opt-in app-side Type fixture before changing product code.
  The intermediate [#39015460241](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015460241)
  was an evidence-reader StrictMode/optional-property error, corrected
  by the successful read-only evidence job; it is not a product failure.
- **Scoped matrix verdict:** for *real 96-DPI composited pixels*,
  **7 of 8** Light/Dark × Name/Type/Size/Month snapshots have been
  visually accepted across the unchanged binary
  (prior Light/Name [#38991841905](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38991841905),
  Dark/Name above, and five from the new matrix).
  The eighth, Light/Type full-window, is **OPEN**. F05-specific active
  High Contrast, Narrator spoken output, and real OS high-DPI remain
  independent **NOT VERIFIED** gates. All captured paths are synthetic,
  inside isolated test-owned evidence; no arbitrary desktop screenshots
  or personal filenames were committed.


## 2026-10-17 actual View-menu Type vs app-side visual fixture — isolated diagnostic

- **Exact source SHA:** `fa12d95e092653ae86ba72d98ff672a06a941386`
  (test-harness-only changes on top of `33c60db9`). No WinUI C++/XAML
  product code was modified; reused the previously verified Release
  executable SHA-256 `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`.
- **Source/policy check:** [central CI #39016958667](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39016958667)
  **SUCCESS** at the exact source SHA, full-history-required-scope with
  `runner-health`, `policy`, and `source` all PASS.
- **True interactive View-menu route:** [owned Windows GUI #39017082938](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39017082938)
  **SUCCESS** with user-session F05 physical Type diagnostic. Unlike
  the synthetic app timer, this route had **no**
  `FLY_F05_VISUAL_GROUP_MODE_ONLY` environment setting. The right
  pane initially contained **6** UIA ListItems. The test then activated
  the right pane, navigated to its *own* synthetic `Right` folder,
  observed the real `Secondary` row, returned to the left pane, and
  selected Type via the actual View flyout and physical Enter input.
  Group headings `.txt`, `.md`, `.log` and the file row were present.
  User profile SHA-256 values for all six protected settings were identical
  before/after; the owned app exited with **code 0**; runtime binary
  unchanged; temporary Scheduled Task removed.
- **Actual screen pixels:** one foreground-verified **960×519** Light/Type
  PNG was created (39,238 bytes; SHA-256
  `bd5e66feb67a1881364015ed34ce961d6ff99b5cef296d8d7b3f63357e131b9d`).
  The [independent hash-pinned image read #39017176600](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39017176600)
  **SUCCESS** and direct visual review showed the left Type disclosure
  bands/icons/labels and the right `Secondary` folder, without material
  overlap or unintended clipping at this sampled 96-DPI viewport.
  **Functional GUI / compositor visual PASS applies to this physical
  menu route and isolated right-folder fixture only.**
- **Still OPEN — app-side F05 visual fixture startup:** the prior
  synthetic app-triggered Light/Type screenshot showed a blank right
  pane; its [guarded retest #39015238402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015238402)
  failed, and read-only [UIA evidence #39015560737](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39015560737)
  found the `RightFiles` control present with **zero** descendants and
  a blank right tab caption. The test-only automatic F05 timer checks
  only left-pane metadata readiness before dispatching the grouping
  command, while normal product startup queues left and right Shell
  navigation independently. This is a plausible startup/fixture
  scheduling distinction, **not a proven root cause**. The successful
  physical route does not retroactively make that failed synthetic run
  PASS, establish that the empty pane can never occur in normal use, or
  certify all startup ordering cases.
- **Separate pending scopes:** real native 125/150/200% OS scaling,
  Narrator spoken output, active High Contrast and the app-side
  Light/Type initial-right-pane scenario remain unverified/open.
  A narrow tab-header caption and active-pane visual state comparison
  may also merit a later independent check; it was not accepted here.

