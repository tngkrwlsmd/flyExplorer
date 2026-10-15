# F03 — bounded local Preview pane development boundary

## 2026-10-15 F03 Preview reveal shortcut — Light/Dark Windows GUI and scoped pixels PASS

- **Current accepted product and GUI source SHA:**
  `40d383ca63d886d2906363f82d054346da270c7f`; functional
  C++/XAML addition was committed at `a9beab25`, followed only by
  a source-contract correction at `40d383ca`.
  The new focusable `TextPreviewRevealButton` lives near the top of
  the existing Details ScrollViewer, ahead of metadata. Its
  `OnRevealTextPreview` handler only focuses the original, still
  bottom-positioned `TextPreviewToggleButton` and calls
  `StartBringIntoView()`. It does not opt in, read bytes, or move
  the known-starting Preview subtree. Earlier relocation that caused
  startup `0xC000027B` was **not** reintroduced.
- [Exact Windows source-contract + fresh Release + Light GUI #38680081184](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38680081184):
  **SUCCESS**. All six focused source tests passed. Real WinUI app
  started; test-owned `FLY_F03_REVEAL_ONLY=YES` verified default off,
  visible top shortcut, physical Enter activation after focusing that
  shortcut, existing lower opt-in Button scrolled into view while
  content stayed empty, then separate physical Space opt-in showing
  owned TXT bytes. The GUI reported
  `F03_REVEAL_STARTS_OFF=PASS`,
  `F03_REVEAL_KEYBOARD_FOCUS=PASS`, and
  `F03_REVEAL_EXPLICIT_OPTIN=PASS`.
  App exit 0, all six real legacy user preference hashes unchanged,
  disposable fixture removed and one-shot user task unregistered.
- [Same exact Release reused for test-owned Dark GUI #38681808840](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38681808840):
  **SUCCESS**, including six source contracts, the same keyboard
  reveal/opt-in checks, clean app exit, untouched six real settings
  and fixture cleanup. Only synthetic private `theme=dark` differs.
  Dark acceptance did **not** recompile the unchanged Release.
- **Actual original app-window PNG visual inspections**:
  [Light read-only #38681658077](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38681658077)
  and [Dark read-only #38681921317](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38681921317).
  For each theme, the original ~952x519 `top` and `focused`
  screenshots were inspected: visible/readable reveal action at the
  top of Details, both file lists, selected TXT row, readable metadata,
  and focused original Preview opt-in at the bottom after scrolling.
  No new list/Details overlap, unreadable control label or observed
  focus-button clipping. **VISUAL ACCEPTANCE: PASS for the inspected
  Light and Dark owned-window states only**. These are before/after
  *focus/scroll states*, not pixel-aligned old/new-product diffs.
  Hashes of original files:
  Light top `d590eca01362dee4195e2ab410ca6785dd6d2c6d566a23e33d0ea9544cc64533`,
  Light focused `3ae40458fedf301f57587855b03467e784f2979ee1ac56227444dc014174222c`,
  Dark top `7f2a38f6db41a4cdc84b84ec571f1799f8ba2bc4de5d63cf9ab060175b0d807c`,
  Dark focused `56cb1a20c546d11f11d31880ed626799fee5b75d72970ac3eb159746aa786385`.
  Protected `.owner`/`.keep` evidence was retained.
- Three earlier attempts failed only **before product GUI/Release
  acceptance**: #38679756547 used unavailable Python on the SYSTEM
  service PATH; #38679862974 generated a malformed PowerShell
  worker; #38679960589 caught an incorrect static assertion expecting
  a literal screenshot label instead of a dynamically assembled one.
  The defects were corrected and accepted by #38680081184; none
  constitutes a user-facing product failure at the final revision.
- **Scope not certified:** keyboard-only traversal from initial app
  launch (the owned test explicitly focused the top shortcut before
  pressing Enter); OS 125/150/200% DPI, High Contrast, Narrator
  spoken output, image preview, independent Preview panel,
  and controlled identical-state old/new-product pixel diffs.
  Prior TXT/MD/LOG Preview and selection acceptance evidence remains
  valid at unchanged underlying implementation. The central remote
  request slot was restored to idle after all runs.

## 2026-10-15 F03 Markdown/LOG Preview — real Windows GUI PASS (test-only)

- **Exact tested main source SHA:** `f0b47f10b6f6f22cc79acc065773603649789f2c`.
  Only `tests/winui/test_shell_gui.py` and
  `tests/winui/test_f03_text_preview_gui.py` were extended at
  `6752e0ba`, then the latter's offscreen UIA assertion was corrected
  at `f0b47f10`. No C++/XAML, policy, or runtime product file changed.
- [Owned interactive Windows GUI #38670792871](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38670792871)
  completed **SUCCESS** at the exact SHA. Opt-in-only synthetic
  `FLY_F03_EXTRA_FORMATS=YES` covered actual `guide.md` Markdown text,
  `events.log` text, invalid UTF-8 `invalid.LOG` fail-closed with no
  stale bytes, return to `readme.txt`, default-off/opt-out/reopen,
  selection churn and strict physical single-row reselection.
  The GUI log recorded `F03_GUI_MARKDOWN_PREVIEW=PASS`,
  `F03_GUI_LOG_PREVIEW=PASS`,
  `F03_GUI_MALFORMED_LOG_FAIL_CLOSED=PASS`, and
  `F03_GUI_FORMAT_SWITCH_RESTORES_TXT=PASS`.
  Application exit was **0**; all six original legacy user-setting
  SHA-256 hashes were unchanged and disposable owned fixture removed.
- The first [#38668316201](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38668316201)
  **FAILED in the GUI test harness**, after displaying Markdown text:
  `FileInfoName` was virtualized/offscreen inside the intentionally
  scrolled Details area, so an extra UIA lookup raised
  `ElementNotFoundError`. The corrected test checks selected file-list
  identity and distinct preview bytes instead; the previous product
  bytes were retained. The same retained Release app and helper were
  **reused without rebuilding** on the successful follow-up, after
  confirming only that one Python probe differed.
- **Acceptance scope:** focused real Windows text-format and cancellation/
  selection behavior. The unchanged product's previously reviewed Light/
  Dark pixels remain their own scoped evidence; this test did not conduct
  another visual pixel review or a fresh Release compilation. Actual
  125/150/200% DPI, High Contrast, Narrator speech, keyboard-only startup
  traversal, `.md`/`.log` non-UTF-8 legacy encodings, raster-image
  decoding and independent Preview layout are **NOT TESTED**.
  The central Remote Shell request was restored to idle and test-owned
  evidence retained.

## 2026-10-15 F03 Light theme — strict mouse and original-pixel comparison PASS

- **Exact Light GUI test SHA:** `a425f1064c75a93abf2b191e7956df5336082832`;
  only project documentation changed since the earlier
  `b86e93f5` both-pane keyboard/Ctrl/Shift success. Product XAML/C++
  are still the `196aa27b` Release and strict dark GUI accepted
  blobs. Light preference `FLY_F01_HIDDEN_ONLY=YES` /
  `FLY_F01_HIDDEN_THEME=light` was confined to the synthetic test
  profile, without modifying the real user's theme.
- [Owned real Windows Light GUI #38664462095](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664462095)
  **SUCCESS**: physical row re-click restored exactly one TXT
  selection (`F03_GUI_RESELECT_SETTLED_PHYSICAL_CLICK_SELECTED=True`,
  `F03_GUI_RESELECT_BOTH_ROWS_SELECTED=False`,
  `F03_GUI_STRICT_PHYSICAL_RESELECT=PASS`); explicit opt-in text,
  folder stale-content clear, opt-out, reopening default-off,
  clean GUI exit and synthetic fixture removal passed. The six
  original legacy user settings hashes remained unchanged.
- **Light before/after visual QA** from original
  [#38649041893](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649041893)
  and new strict #38664462095, original test-owned app window PNGs
  retrieved in read-only
  [#38664699576](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664699576).
  Both ~952x519 Light screenshots have readable selected filename,
  visible list icons, Details labels, opt-in toggle/body and footer,
  with no observed new pane overlap, cut-off or loss of selection
  contrast. Only synthetic fixture path and timestamp changed.
  **VISUAL ACCEPTANCE: PASS for this bounded Light comparison**.
  Real OS 125/150/200% DPI, High Contrast, full focus rings,
  screen-reader spoken output, and additional file types remain
  separate untested gates. Dark visual review remains accepted
  at the unchanged product revision.

## 2026-10-15 F03 Extended selection — both panes keyboard + Ctrl/Shift GUI PASS

- **Exact latest tested source:** `b86e93f5e004d1f5e8cc40ae6ff663f55b01487f`.
  Product C++/XAML bytes are unchanged from the successful
  `196aa27b` strict mouse/Release revision. New
  `tests/winui/test_f03_extended_selection_gui.py` and opt-in
  `FLY_F03_EXTENDED_ONLY=YES` in `test_shell_gui.py` exercise the
  existing Windows GUI harness with test-owned files only.
- [Owned real-user GUI #38664113381](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664113381)
  **SUCCESS** at the exact source SHA. Both `LeftFiles` and
  `RightFiles` individually passed **physical keyboard Down arrow**
  moving from the selected folder to only the TXT file,
  **Ctrl+click** adding and removing the other selection,
  **Shift+click** selecting the contiguous two-row range and then
  **plain click** restoring exactly one selected file. Actual
  `F03_EXTENDED_BOTH_PANES_INPUT_PASS=True` and
  `F03_EXTENDED_OWNED_GUI_PASS True`. GUI exited with code 0,
  disposable fixture removed and all six legacy profile hashes
  remained identical. Test-owned evidence kept.
- **Scope limits:** this verifies keyboard selection **once a file-list
  item has been physically focused**. Keyboard-only navigation from
  the first app focus, screen reader spoken labels, drag-and-drop,
  Light/HC, and 125/150/200% OS DPI remain separate, untested gates.
  Strict F03 text-preview acceptance and the dark visual comparison
  remain pinned to unchanged product SHA `196aa27b`; do not
  mislabel the newer test-only commit as a separate visual retest.

## 2026-10-15 F03 file-list mouse reselection — fixed, strict Windows PASS

- **Product and test commit:** `196aa27b1132955c6c6c5eabd1470c971eac06d9`.
  The only product modification is the **two** WinUI file-list
  `SelectionMode="Multiple"` attributes becoming `"Extended"`;
  the second changed file adds a source contract for both panes.
  No PreviewController, Shell helper, drag transfer implementation
  or user preference code was changed.
- **Exact Windows Release:** registered central CI
  [#38662641235](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38662641235)
  **SUCCESS**, `SCOPE=release SHA=196aa27b...`. This build success
  is separate from real GUI acceptance.
- **Strict physical input (no UIA Select fallback):** owned interactive
  [#38663282030](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38663282030)
  **SUCCESS** at that same exact SHA. WinUI started in a real user
  desktop session; `F03_GUI_RESELECT_SETTLED_PHYSICAL_CLICK_SELECTED=True`,
  `F03_GUI_RESELECT_BOTH_ROWS_SELECTED=False`,
  `F03_GUI_RESELECT_PHYSICAL_SINGLE_SELECTION=True`, and
  `F03_GUI_STRICT_PHYSICAL_RESELECT=PASS` after selecting the
  `Nested` folder and physically re-clicking `readme.txt`.
  The normal row-target physical click now establishes **exactly one**
  selected text file; no accessibility selection fallback ran.
  Fresh opt-in text, stale selection clear, opt-out, default-off
  reopen, app exit 0 and test fixture cleanup also passed; the
  original six legacy user configuration hashes were unchanged.
- **Controlled dark screenshot comparison:** previous strict
  `Multiple` screenshot from
  [#38655414859](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38655414859)
  and new `Extended` screenshot from #38663282030 were read
  **read-only** from protected test-owned app-window PNGs in
  [#38663593381](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38663593381).
  Both ~952x519 dark-theme views show two file panes, one highlighted
  `readme.txt` row and readable Details opt-in content. No material
  overlap, new cropping, selection/readability regression or contrast
  loss was observed in these screenshots; synthetic fixture path/time
  differs. This is a bounded **Dark visual review**, not real Light,
  High Contrast, 125/150/200% DPI, Narrator, keyboard-only, Ctrl/Shift
  multi-select or drag-and-drop acceptance at this SHA.
- The previous GUI #38655414859 **failed correctly** on the old
  `Multiple` mode: a filename-side physical click did select
  `readme.txt` but left `Nested` selected too. The new strict GUI
  establishes the regression fix at the same logical gate, not merely
  an assumed selection-mode behavior.
- Remote Shell request slot restored to `idle` after both tests.
  Protected `.owner`, `.keep` and previous evidence retained.

## 2026-10-15 F03 opt-in text Preview — scoped Windows GUI acceptance

- **Exact passing GUI source SHA:** `0e4e147f7e1004703d9566f3bf38bb086de6c17a`.
  The **product XAML/C++ blobs are unchanged** from the earlier
  startup-working `b9b15d39`/safety rollback; subsequent commits
  adjusted **only** the F03 owned GUI test. The 2026-10-15 attempted
  XAML relocation `fac580bd` passed [central Release
  #38646656680](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38646656680)
  but then **crashed at GUI startup**
  ([#38647173047](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38647173047),
  `0xC000027B`). This was restored by non-force
  [`95bd998a`](https://github.com/tngkrwlsmd/flyExplorer/commit/95bd998a5a717718085fb55c99c41d05f11f04e7).
  Therefore **Release PASS does not imply GUI startup PASS**.
- **Owned real-user dark GUI**
  [#38648688824](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38648688824)
  **SUCCESS** at the exact SHA above: application startup, two panes,
  native Shell list, details opt-in control exposed after *pane-local*
  scrolling, default-off/no contents, test-owned UTF-8
  `readme.txt` displayed as `owned synthetic only` only after explicit
  opt-in; selecting `Nested` cleared old contents; reselecting
  `readme.txt` via its verified UI Automation SelectionItem pattern
  delivered fresh contents; turning Preview off cleared text; closing/
  reopening Details returned to default off. All evidence in the
  protected owned test directory; app exit=0, original six user
  settings SHA256 identical and disposable synthetic files cleaned.
- **Owned Light GUI**
  [#38649041893](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649041893)
  **SUCCESS** with the same source and a **test-owned only**
  `theme=light` preference. All bounded F03 steps and profile
  integrity passed again; no user-wide theme/setting changes.
- **Real pixel inspection:** captured only the verified
  harness-owned application window before/after user opt-in; the
  original PNGs are held under `logs/f03-visual` in the protected
  scratch. Dark
  [#38648361110](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38648361110)
  and Light
  [#38649262620](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649262620)
  returned scope-checked **read-only** image views. At the viewed
  940x508 presentation, button/body/status had visible contrast,
  the synthetic text appeared only in the after image and no pane
  overlap was observed. This is *observed Dark/Light scoped acceptance*,
  **not** a blanket DPI, accessibility, narrow-resize or high-contrast
  claim. The Preview toggle remains at the **bottom** of Details and
  needs in-pane scrolling: discoverability is still a UX issue.
- **Important input limitation, both themes:** test log recorded
  `F03_GUI_RESELECT_PHYSICAL_CLICK_SELECTED=False`.
  Re-clicking a row through `pywinauto.click_input` did not change
  WinUI's actual selected bit; the verified UI Automation
  `SelectionItem.Select()` then selected the row and the native
  Preview rerequest completed correctly. **Do not claim verified
  physical mouse reselection** or that the user-facing click issue is
  resolved. First isolate hit-testing/focus and re-check actual mouse
  selection on the owned application; only then claim a complete
  mouse-operated acceptance.
- **Follow-up click-timing isolation:** [owned actual mouse test
  #38649640303](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649640303)
  **SUCCESS only for the scoped UIA-assisted Preview flow** at
  `95d45f322cbaaca604066a15683434773b2342ab`.
  The test waited for `Nested` to report a settled real selection,
  paused before clicking `readme.txt`, and polled its actual
  SelectionItem state after the physical click. It still reported
  `F03_GUI_RESELECT_SETTLED_PHYSICAL_CLICK_SELECTED=False`.
  The UIA `Select()` fallback again triggered a correct preview.
  This rules out the *simple immediate-back-to-back click timing*
  explanation in this fixture. **Pointer hit-testing, item target
  geometry, keyboard modifiers, and actual manual mouse use remain
  separate unverified diagnoses**. No product code was changed.
- **Earlier prepared mouse hit-target experiment (historical, before acceptance):**
  `tests/winui/test_f03_text_preview_gui.py` now logs the UIA-row
  center attempt versus a bounded filename-side pixel click, verifies
  the foreground and pixel-owning HWND belong to this test process,
  checks Ctrl/Shift state, and distinguishes a single selected TXT
  from a multi-selection. The optional environment flag
  `FLY_F03_STRICT_PHYSICAL_RESELECT=YES` makes the GUI smoke
  **fail** if a true single-file physical reselection did not occur;
  it does **not** allow UIA `SelectionItem.Select()` to conceal this
  gate. Without that flag, the previously accepted UIA-assisted
  baseline remains available. The exact newer diagnostic is
  **UNVERIFIED on Windows** because the remote invocation was
  blocked, and the connected Desktop Commander device was offline.
  Do not report a mouse fix until the strict owned test logs
  `F03_GUI_STRICT_PHYSICAL_RESELECT=PASS` on its pinned commit.
- **Still not verified:** full independent F03 Preview pane, image
  decode, `.md`/`.log` GUI fixture cases, 125/150/200% real OS DPI,
  high contrast/forced colors, audible Narrator, and complete
  keyboard-only opt-in/selection flow. Prior supervisor native
  corrupt-wire, timeouts, process kill, cancellation cases are
  retained at their own SHAs and not implied by the GUI test.
  Historic earlier failures below remain evidence, not current status.

## Earlier F03 safety and UI acceptance boundary (2026-10-15)

- **Current app code content:** commit [`00377986`](https://github.com/tngkrwlsmd/flyExplorer/commit/003779863a0fa19c8becb04b38e82ce2b3ba6896)
  restores **only** `app/winui/MainWindow.xaml`,
  `app/winui/m24_preview.cpp`, and
  `tests/winui/test_f03_text_preview_gui.py` to the exact blob contents of
  [`b9b15d39`](https://github.com/tngkrwlsmd/flyExplorer/commit/b9b15d39fa1ee34a406ca29c6cfc6055c165e22d)
  in one non-force, expected-head Git commit; compare confirmed these
  contents are identical. All earlier verified native F03 supervision,
  background `PreviewController`, and request cancellation/generation
  gates remain present. This is a **bounded app-startup safety rollback**,
  not F03 GUI acceptance or a return to the old MFC app.
- **Compilation and native evidence:** actual
  [Release #38562561304](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38562561304)
  passed policy/source plus shipping WinUI Release at
  `7e4054182faffe92fc750d582ce3ac47a6b6ffcd`.
  [Real child and active-cancel #38558563233](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38558563233)
  previously passed a scoped, exact native test. These do not validate
  an end-user text UI or certify a new current-head GUI screenshot.
- **Last observed successful app startup:** [owned interactive GUI
  #38564071039](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38564071039)
  on exact `b9b15d39` reached the real WinUI dual panes, tabs,
  and native directory items; it failed **later** when its UIA test
  could not locate `TextPreviewStatus`. It did **not** prove
  explicit text content display or visual usability. The opt-in button
  remained low in the scrollable Details region, so the narrow layout
  and initial keyboard discoverability are not accepted.
- **Rejected later GUI modification:** [#38565384749](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38565384749)
  on `fec86c32` failed **at application startup**, code
  `0xC000027B` in `Microsoft.UI.Xaml.dll`; scoped Windows
  Application Error/WER events recorded `0x80004002`
  COM interface failure. No GUI acceptance happened.
  A disposable, protected test-only simpler heading layout was compiled
  but [actual test-only launch #38645754377](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38645754377)
  still exited `3221226107` before exposing an owned window.
  Therefore, blaming only the horizontal heading layout is not
  supported; future debugging must isolate the added visibility/state
  and XAML subtree wiring separately.
- **Failed diagnostic build scope:** [#38641494315](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38641494315)
  could not restore NuGet packages in a fresh worktree.
  [#38643849995](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38643849995)
  built the alternate layout using the prior owned local cache but
  reached the test deadline before publishing its GUI result. Its
  built executable was then run separately as the diagnostic above.
  Final read-only [#38645509785](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38645509785)
  confirmed exact original source SHA `fec86c32`, clean Git
  worktree, **zero** test-owned scheduled tasks and **zero** associated
  remaining build processes. All evidence remains in an owned,
  `.keep`-protected scratch root; never auto-clean it.
- **Next required F03 gate:** diagnose text/visibility COM activation
  in a **test-owned, pinned and reversible** Release build without
  repeated clean NuGet restores. Then get an actual interactive
  user opt-in test to PASS: default bytes hidden, exactly one
  selected local UTF-8 text file displayed, cancel during child IO,
  stale selection/window/pane/tab ignored, turn-off and reopen clear
  content, test-owned profile unchanged. Capture and inspect original
  narrow Light/Dark window pixels and relevant focus/accessibility
  behavior before visual acceptance. Image decoding, full Preview
  pane, 125/150/200% DPI and audible Narrator are **not verified**.

## Status (2026-10-14)

**Phase 1 policy and partial phase 2 safe open, bounded reader and
one-shot helper entry.** `file_preview_policy.h` screens candidates,
`file_preview_safe_open.h/.cpp` validates each local component and retains
opened ancestor handles, and `file_preview_reader.h/.cpp` reads bounded bytes.
`file_preview_worker_wire.h` defines a separate versioned/bounded request and
reply protocol. `file_preview_worker.cpp` runs one request in the existing
`FlyShellIsolationHelper --preview-read` mode. The helper was built in
Release at this **historical phase-2 checkpoint**; the later native parent
and opt-in WinUI controller milestones are described above.
The one-shot worker has no GUI, persistence, Shell extension, web content or
image decoder. Blocking filesystem work stays out of the XAML thread.
This is a fault boundary, **not** a security sandbox.

**MSVC Release compile accepted:** [registered central Windows run
#38518993733](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518993733)
reported `PASS release-build` at exact source SHA
`93c8a435cb5de505d02ac1927ceb30e0f572bd09`, including actual
`file_preview_reader.cpp` translation-unit compilation.

**Verified focused native handle-read behavior:** [owned Windows
run #38520021060](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38520021060)
completed **SUCCESS** with exact source SHA
`62a4f632d302bce59839b3b4109a1380c55e5b5a` after an isolated
MSVC compile of `src/base/file_preview_reader.cpp` with
`tests/winui/native_preview_reader.cpp`. The test-owned, regular local files
exercised correct UTF-8 and opaque image bytes, mismatched opened path and
size, invalid UTF-8, cancellation, deadline, oversized text, invalid handle
and directory rejection. The producing log recorded
`F03_NATIVE_HANDLE_READ_AND_FAILURE_CONTRACT=PASS`,
`F03_NATIVE_VERIFIED_HANDLE_ACCEPTANCE=PASS`, and owned scratch cleanup
PASS. The *actual compiled behavior* of this handle-only primitive is now
**accepted within those bounded fixture cases**, not as an isolated helper
service or a shippable preview feature.

**Earlier harness failures correctly classified:** [#38518452445](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518452445)
(PowerShell 5.1 parser),
[#38518550162](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518550162)
(SYSTEM session did not expose `python`),
[#38518696504](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518696504)
and diagnostic [#38519687206](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38519687206)
(truncated `call "` batch serialization from unparenthesized PowerShell
array string expressions). The native test helper now parenthesizes each
concatenated array element, checks serialized commands before execution and
retains a bounded developer-command setup log on failure. These earlier
failed runs never executed the C++ assertions and must not be recorded as
product regressions.
## Phase 2 one-shot preview helper wire — bounded acceptance evidence

- **Exact code SHA:** `d0d5b6a987ef8ae1c73e2aa0f5ceacb20c37f0ec`.
  Private request/reply headers are 28/24 bytes, version 1, with UTF-16
  path length/checksum and capped body sizes (256 KiB text, 12 MiB image).
  The helper checks canonical path, extension and size before opening;
  all actual file access remains in the child. It responds with empty
  bodies on errors. No raw file contents are written to logs.
- **Actual MSVC native entry test:** [owned run #38526086984](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526086984)
  **SUCCESS**: `F03_NATIVE_WORKER_WIRE_BOUNDS=PASS`, existing safe-open
  and read tests PASS, owned cleanup PASS. The fixture uses anonymous
  pipes with `runOne` invoked in another thread of the *same process*;
  it verifies valid text, bad checksum, wrong kind, excess length,
  missing TXT, UNC, and error replies. It does **not** prove real
  CreateProcess/job supervision or kill-on-timeout handling.
  Prior runs [#38525652361](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38525652361)
  and [#38525878610](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38525878610)
  failed this newly added test: the negative missing-file fixture used
  `.missing` (unsupported extension) instead of `.missing.txt`,
  so the correct earlier format rejection was mismatched against the
  later unsafe-file status. Test fixture corrected; product behavior
  unchanged.
- **Exact source suite:** [central #38526337158](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526337158)
  **SUCCESS** at this SHA: policy, structure 4, product source 199,
  harness 20, infrastructure 30.
- **Exact Release build:** [central #38526567823](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526567823)
  **SUCCESS** with `scope=release` at this SHA. The tracked
  `app/winui/build.cmd` invokes `helper/build.cmd` first and requires
  the resulting helper executable before staging the app; the tracked
  helper project links the new worker, reader and safe-open code. This
  establishes compile/link/staging integration, **not** actual parent
  launch/response/timeout/shutdown acceptance.
- **Next acceptance gate:** integrate the native-verified parent
  supervisor and request gate into a pane-owned PreviewController that
  runs outside XAML STA; derive an exact app-sibling Helper path in the
  composition root, own cancellation when pane/tab/selection changes,
  and recheck the generation ticket before DispatcherQueue presentation.
  The real `--preview-read` child, corrupt reply, timeout and active
  cancellation are already accepted at the separately listed native SHA;
  actual WinUI integration is not yet tested.

## 2026-10-14 F03 parent-side one-shot supervisor — native acceptance

- **Exact native code/test SHA:** `4a8ddc9f44935e5b9b47c882b0d9df6193ccd087`.
  `src/base/file_preview_supervisor.h/.cpp` is a UI-independent,
  *background-thread-only* parent invocation of the already isolated
  `FlyShellIsolationHelper.exe --preview-read`. It creates the exact
  process suspended, puts it in a private kill-on-close Windows Job before
  resuming it, and limits inherited handles with
  `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` to the one-request stdin/stdout
  pipes and a NUL stderr sink. The parent checks a pre-screened request,
  bounded reply length and kind, status and checksum, plus actual child exit.
  Cancellation and the independent parent deadline terminate **only this
  exact-owned Job** and join the IO thread before returning. This is
  **process fault containment, not a security sandbox**.
- `src/base/file_preview_request_gate.h` owns request tickets per future
  pane owner. Every replacement/clear invalidates the previous cancellation
  token; delivery is permitted only while the same window, pane, tab,
  selection identity, generation and token remain current. It is a
  UI-independent primitive; there is **no MainWindow/PreviewController
  invocation or DispatcherQueue binding yet**.
- [Actual Windows native release-helper/parent #38558173709](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38558173709)
  **SUCCESS** on `fa58362a3c719a154b43ea518c9f6bee93c7545f`:
  real child text-bytes wire, missing/oversized/rejected cases, malformed
  reply checksum, test-owned hung-child deadline with Job reclamation,
  stale window/pane/tab/selection generation gate and owned test-file
  cleanup. Earlier first compile in
  [#38557801405](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38557801405)
  failed on a missing move constructor for the parent-side private
  HANDLE wrapper; the wrapper was corrected to move, never duplicate,
  the pipe HANDLE.
- [Follow-up active cancellation #38558563233](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38558563233)
  **SUCCESS** at the exact SHA above. A disposable hung child was
  cancelled **after launch**, reaped within a bounded interval, and
  all previously accepted wire/deadline/gate tests passed again.
  The matching Release helper binary was reused because this exact
  follow-up changed only the native test and its source contract.
- The previous [#38557209117](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38557209117)
  source-gate attempt was interrupted by a PowerShell 5.1
  native-stderr `RemoteException` before any compiler or product test.
  The succeeding [#38557801405](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38557801405)
  used separate Python stdout/stderr capture, confirmed the source
  contract PASS and actual Release helper build; it then revealed the
  concrete C2280 move-wrapper compiler defect noted above. These failed
  harness/compiler runs must **not** be called accepted validation.
- The native supervisor translation unit is listed in the *tracked app
  project template*. **Full shipping app Release compile/link at the new
  revision is a separate pending gate**. This layer is not yet called
  by production selection state; UI async ownership, stale-result
  DispatcherQueue application, actual raster decoding, XAML Preview pane,
  Light/Dark pixels, DPI and Narrator remain **NOT TESTED**. The app
  composition root must supply and verify its own trusted sibling helper
  path; accepting an arbitrary basename is not proof of helper provenance.

## Phase 2 safe-open acceptance evidence (bounded)

- [MSVC owned native run #38522342210](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38522342210):
  PASS at SHA `b6c7c268354493f48ac94d22c77156f87d101fd8` for guarded
  nested-file open/read, rejected UNC/ADS/traversal/changed-size/cancelled
  input and actual **file and ancestor-directory symbolic link** rejection
  (both symlink creation probes succeeded, not skipped). Cleanup PASS.
- [Corrected native run #38523226489](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523226489):
  PASS at SHA `aca6bc779de2408a3eccc73ba63c5a1e205f3a39`. The test
  fixes dangling `wstring_view` fixtures by retaining path storage and
  deleting the temporary-string helper overload. The safe opener now
  copies the candidate path *before* policy screening; path allocation
  exceptions are caught instead of crossing a `noexcept` boundary.
- [Final corrected source suite #38523664886](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523664886):
  PASS at SHA `8ecd748a126f58b9c81f88ad026fe8a434a4d77a`, scope
  `source`: policy, structure 4, product-source 196, harness 20 and
  infrastructure 30 all passed. The prior run
  [#38523399332](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523399332)
  failed because one static test still searched for `screen(candidate)`
  after the code was refactored to `screen(stable)`; the test was
  corrected without weakening the owned-path requirement.
- **Release validation at this code SHA:** [central run #38523831041](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523831041)
  subsequently completed **SUCCESS**: `file_preview_safe_open.cpp`
  was included in the app Release build. Exact-SHA evidence is limited
  to this original worker-free code revision.

The opener walks canonical drive paths component by component, opening
directories using `FILE_FLAG_OPEN_REPARSE_POINT`, verifying opened-handle
final DOS paths, reparse/offline/directory attributes, volume serial, regular
file size and fixed-local drive, and retaining ancestor handles through the
file read to reduce rename/reparse swaps. It refuses unsafe paths rather
than following them. It does **not** yet isolate blocking OS calls or
provide a bounded wire, worker termination, pixel decoder, or stale
PaneTab/WindowTab result rejection. Those remain explicit gates.

## Intended behavior

An explicit opt-in read-only Preview pane for the currently selected
single item of the **active pane and WindowTab**. Keep flyExplorer's two
independent file panes. Preview and the existing Details pane must have
a coherent responsive layout: neither may silently squeeze both file lists
into overlapping columns. Prefer a mutually exclusive right-side mode at
small widths; preserve each mode's own toggle and state, with explicit
switching semantics.

Supported first phase: bounded *local regular files* `.txt`, `.md`,
`.log` (displayed as inert text) and `.png`, `.jpg`, `.jpeg`,
`.bmp` (decoded raster, without shell extension/preview handlers).
Unsupported, empty selection, multiple selection, virtual Shell entry,
UNC, disconnected drive, reparse-point path and unstable/unknown size
display a localized safe placeholder rather than launching handlers.
SVG, HTML, executable formats, PDFs, archives, web content and active
preview handlers remain OUT OF SCOPE.

## Two independent security boundaries

1. **Cheap UI-independent candidate decision (implemented):**
   `previewpolicy::screen` requires filesystem, known fixed-local drive,
   regular file, no advertised reparse point, known size and canonical
   absolute drive path without `.`/`..`, slash mixing, ADS or device
   prefixes. Text is limited to **256 KiB**, image encoded data to
   **12 MiB**, with a separate **16,777,216-pixel** decode cap.
   The screen only decides whether a request MAY be submitted; its
   caller-supplied flags and path are not proof that a file is safe.
2. **Authoritative worker/handle validation (PARTIALLY IMPLEMENTED):**
   The `readVerifiedHandle` primitive checks an already-opened file
   handle, final path/volume, reparse/directory flags, file size and changed
   metadata, performs bounded reads with cooperative cancellation and strict
   inert UTF-8 validation. It is currently called only in a test executable.
   A production safe opener must run outside the XAML thread in a bounded,
   cancellable worker or existing isolated helper. Require handle-based local fixed
   volume validation; reject reparse/junction traversal of *all*
   components, not just the leaf; reject directories/device/provider
   files; verify file identity, attributes and size on the opened
   handle, and cap the actual read. Prevent TOCTOU substitution; enforce
   bounded time, no output on partial/error/timeout. Validate decoded
   image dimensions and allocation before returning a pixel buffer.
   User-controlled text remains inert (no HTML/link/script execution),
   UTF decoding is bounded and malformed/binary inputs fail closed.

## Lifetime and ownership

A dedicated PreviewController/worker owns request creation, timeout,
cancellation, buffer limits and completion. It must not add a new
state machine to MainWindow. WindowTab/PanTab+side selection and current
navigation route, rendered path/identity and request generation must
match on completion; close, selection churn, pane switching, disabling
preview and window shutdown invalidate prior work. No provider/Shell,
disk open, raster decode or active preview-handler DLL executes on the
WinUI/XAML thread. File contents must not be persisted or logged.

## Incremental acceptance plan

1. **Phase 1:** conservative native candidate screen + tested bounds
   (current stage; local portable C++17 probe and source contracts).
2. **Phase 2:** separately test-owned worker/decoder with forged extension,
   huge encoded/decoded size, UNC, symlinks/junctions, short reads, binary
   text, malformed UTF, cancellation and stale selection regression.
3. **Phase 3:** WinUI presentation, opt-in toggle, placeholders, dual-pane
   layout, UIA text and keyboard focus. Capture actual test-owned
   **BEFORE** and matched **AFTER** pixels at light/dark, narrow/default
   widths and supported actual DPI. Inspect screenshots, fix visual
   defects and repeat the affected checks.
4. **Final scope:** source, native build, functional owned GUI process
   exit, original pixel inspection, current exact-main central acceptance.
   High Contrast, 125/150/200% OS scaling and Narrator speech remain
   explicitly **untested** until independently measured.

Do not mark F03 complete merely because a format's extension passes
`screen`; preview bytes, lifetime, UI and visual review are later gates.
