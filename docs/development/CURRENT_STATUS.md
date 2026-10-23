# L08 cursor hover-dwell evidence — automation arrow sustained, 2026-10-23

- **Prior exact baseline preserved:** `98e9b283998aa90c134ceacb1ec19be573841934` [Windows GUI #39951081963](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39951081963) passed real Details name/type/size drags, rapid release-tail, workspace-tab return, normal WinUI exit, configuration checks and fixture cleanup. Its archived, bounded GUI log was inspected read-only in [#39953465234](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39953465234): **all three** UIA hit peers were the expected `Left{Name,Type,Size}ColumnResizeThumb`, while native `GetCursorInfo` reported the default arrow cursor (`HCURSOR=65539`; `SizeWestEast=65553`). Actual boundary moves were **+40, +28 and +20 px**.
- **New timing discriminator, no product behavior change:** `tests/winui/test_owned_column_resize_gui.py` now moves the pointer from the owned file list into each exact 12-px handle and records native cursor/hit at **70, 250 and 600 ms**. `tests/winui/test_px10_column_resize_gui_contract.py` requires this diagnostic source. Exact `e555051866868e4a7dc548a40b65d31edeccf552` [Windows preflight #39954122328](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39954122328) Python syntax **PASS** and source contracts **3/3 PASS**. [Scoped GUI #39954174882](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39954174882): Release **PASS**, actual `gui-column-resize-Release` **EXIT=0 (33.8 s)** and `functional-px10-column-resize` **PASS**. The successful archived GUI log was inspected read-only in [#39955105078](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39955105078): **all nine** samples remained native `arrow` while all nine UIA hit samples matched the owned resize handles. Dragged name/type/size boundary deltas were again **+40/+28/+20 px**, workspace restoration, normal app exit 0, original configuration hash check and fixture cleanup remained PASS.
- **Interpretation / open scope:** On the automated Windows runner, the incorrect arrow cursor is **reproducible after a 600-ms hover**; a pure immediate-GetCursorInfo race is insufficient to explain these samples. The canonical `app/winui/DetailColumnHandle.cpp` already sets WinUI `ProtectedCursor(SizeWestEast)` in `Loaded`; the exact cause of the mismatch (pointer event dispatch, visual tree/cursor precedence or automation-versus-physical input) **is not proven**. Earlier user-reported direct physical hover showed the resize cursor, but that was not on an identical binary/test path. **No new C++ cursor workaround was applied. No cursor-image/pixel-visual acceptance. L08 cursor discrepancy remains OPEN.** Focused GUI PASS does not close G01 intermittent failures, validate the right pane, or re-enable excluded G03–G05/stopped G07.
- Read-only diagnostics operated on allowlisted archived `gui-test.log`; the direct Windows request was returned to idle. Existing successful functional PX10 evidence remains accepted, rather than being reopened by the separate cursor check.

---

# PX10/L08 Details column resize — focused Windows GUI PASS, 2026-10-23

- **Exact verified source:** [`98e9b283998aa90c134ceacb1ec19be573841934`](https://github.com/tngkrwlsmd/flyExplorer/commit/98e9b283998aa90c134ceacb1ec19be573841934); scoped central Windows [run #39951081963](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39951081963) completed **success**. Source-only PX10 GUI harness contracts at `4d6950dd`: [remote run #39950085238](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39950085238) **3/3 PASS**. The separate central workflow/dispatcher quality contracts: [#39950532626](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39950532626) **PASS**.
- **Actual Windows, not source-only:** `gui-column-resize` triggered only `functional-px10-column-resize`. Release build **PASS / exit 0 (336091 ms)**; `gui-column-resize-Release` **exit 0 (29.3 s)**; scoped stage PASS (30031 ms). The owned GUI exercised left Details **name/type/size** physical header drags (each next-column boundary moves at least 12 pixels), a rapid release-tail movement, and `Ctrl+T` to another WindowTab and back to confirm the original tab's left-column boundary remains within 4 pixels. The harness requires real process normal close **exit 0**, original six-user-configuration digest equality (for pre-existing files), and test-owned fixture deletion. `run_checks.py` checks these positive markers and traceback absence; successful CI results are bounded to this suite. Central output includes `NOT_FINAL_ACCEPTANCE=1`, meaning this is a focused diagnostic, **not** full-app acceptance.
- **Limitations preserved:** native resize *cursor shape* is observed diagnostically but **not accepted**: prior automated arrow/resize discrepancy and the user's earlier direct-cursor observation are not reconciled. This run saved application-window before/after captures in its scoped harness; no independently reviewed pixel comparison or cursor screenshot acceptance is claimed. Right-pane/each PaneTab drag transitions, cancellation/capture-loss under live tab switch and full G01 intermittent stability remain untested. The earlier PX10 drag-ownership source-only guard at `ac9a6c3b` is now covered by one normal interactive path, not exhaustive stale-event reproduction. G03–G05 remain excluded and G07 stopped.
- **Changed files in this focused unit:** only `tests/winui/test_owned_column_resize_gui.py`, `tests/winui/test_px10_column_resize_gui_contract.py`, `tools/winui/run_checks.py` in the application repository; Windows central control-plane separately adds the `gui-column-resize` scope. No new product C++ or XAML changed. Remote-shell request returned idle.

---

# G01 final-window Ctrl+W shutdown — actual GUI PASS, classifier fixed, 2026-10-23

- **Focused product behavior, exact GUI source:** [commit `f3a29d3d640a13723e8bed5592c9613a0152cb3c`](https://github.com/tngkrwlsmd/flyExplorer/commit/f3a29d3d640a13723e8bed5592c9613a0152cb3c), [central Windows run #39942415493](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39942415493). Release build **PASS**, actual `gui-startup-integrated-Release` test process **EXIT=0 (6.9 s)**. The separate retained, test-owned GUI log examined read-only in [remote run #39943122615](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39943122615) contains **`G01_INTEGRATED_STARTUP_GUI_PASS=True`**, **`G01_FINAL_WINDOW_ADDRESS_FOCUS=PASS`**, **`G01_FINAL_WINDOW_CTRL_W_EXIT=0`**, `OWNED_WINUI_SHELL_EXIT 0`, `LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT 6`, and `OWNED_SYNTHETIC_FIXTURE_REMOVED True`; no Python traceback. This exercises the app's **Ctrl+W final-window** route with the owned address editor focused, distinct from the earlier WM_CLOSE/PX12 check.
- **Why central run is red despite the actual GUI exit 0:** the previous runner required the exact line `LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True`, while the actual safe harness prints the additional `PRESENT 6` suffix. This is an **acceptance-marker false negative**, not evidence of a fresh native crash. The first attempt [#39941356463](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39941356463) also had a test-harness `NameError` from missing `send_keys` import; it was corrected at `f3a29d3`. GitHub artifact upload quota errors are a separate storage issue, not the GUI failure.
- **Classifier and regression source fix:** commits [`beb8b83`](https://github.com/tngkrwlsmd/flyExplorer/commit/beb8b83cad232a2b7206571e4e6201098ba84b9b) and [`2ba0da35`](https://github.com/tngkrwlsmd/flyExplorer/commit/2ba0da35c6144bc8d28c0d3949431ff9d598739e) accept the real `LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT <nonnegative integer>` format while still requiring all other success markers and rejecting missing/invalid markers or traceback. Exact-SHA, isolated Windows **source-only** [#39946409466](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39946409466) ran **3/3 focused Python contracts PASS** and removed its test-owned checkout. **No new GUI/build was run for the classifier-only source commit**; the prior CI job's official conclusion remains `failure`, not retroactively `success`.
- **Remaining risk:** one successful actual Ctrl+W close and one prior focused WM_CLOSE close are **not intermittent-shutdown stress acceptance**, a captured exception-time native stack, or proof of the intermittent initial left-pane Shell root cause. G01 stays **OPEN**. G03–G05 remain user-excluded; G07 remains stopped. Windows remote-shell request was returned to idle.

---

# G01 focused TextBox shutdown mitigation — focused Windows PASS, 2026-10-23

- **Exact product/test source:** [`0893ba12c67b05ad4d5c9534261fc78f5b82e770`](https://github.com/tngkrwlsmd/flyExplorer/commit/0893ba12c67b05ad4d5c9534261fc78f5b82e770). `MainWindow` now moves focus from any active text editor to its existing `NewTabButton` before XAML input teardown through `AppWindow.Closing` and both internal final-window `Close()` routes. Existing idempotent `Closed` cleanup remains.
- **Microsoft upstream context:** [microsoft-ui-xaml #11653](https://github.com/microsoft/microsoft-ui-xaml/issues/11653) describes the same focused-`TextBox` shutdown AV pattern and confirms a focus-move workaround; upstream root fix `691c6a7` was merged to main but is not proven shipped in the app's pinned SDK. The historical flyExplorer repository evidence contains WER and matching EXE/PDB identity, **not an independently captured exception-time native dump/call stack**; do not turn the upstream similarity into a proven flyExplorer stack.
- **Focused actual-Windows validation:** [central run #39936268900](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39936268900) on the exact source returned **Release build PASS (237837 ms), PX12 `gui-address-visual-compare` PASS (8630 ms), CI success**. The PX12 visual probe now requires the app-owned `AddressBox` to have keyboard focus after its comparison and immediately before its owning harness posts `WM_CLOSE`; that assertion completed on the successful path. The existing runner's positive checks require `OWNED_WINUI_SHELL_EXIT 0`, legacy profile unchanged and owned synthetic fixture removed. This was one focused run, not a full GUI regression or statistical intermittent-crash test.
- **Classification:** G01 focused-text-input **shutdown workaround: one actual Windows PX12 PASS**. Wider G01 intermittent reliability/initial-navigation risk remains **OPEN**; no SDK root-fix claim, no broad repeated close testing, no native exception-time dump from this new run. G03–G05 excluded and G07 stopped as before.

---

# G01/PX12 retained crash EXE/PDB identity verified — 2026-10-23

- **Material progress: exact matching symbols recovered.** The retained `flyExplorer.exe` from [failed visual run #39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462) is present at its original Release output, SHA-256 `c288e010ff848786c74abea3ac3c4e794e5baba2ffb872b95cd76dc8a3244eac` (2,500,096 bytes). Found `out/symbols/winui/Release/flyExplorer.pdb` (91,328,512 bytes), SHA-256 `cd11e032b1c28979f4474e35504c8803a0ac61512a54b9edb68092922f852a15`; **PE CodeView RSDS and PDB MSF information stream have identical GUID `eb944b04-c364-49a1-9ab1-74dd55e6e2ff` and Age `1`**. This is an actual exact EXE/PDB identity match, not a filename-based approximation.
- Added read-only `tools/winui/inspect_release_symbols.py` and two focused tests `tests/winui/test_inspect_release_symbols.py` (source commit `4c930ba484ed9ce7923c87634cdfce4c516d9133`). Windows [#39919676414](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39919676414) **2/2 source tests, syntax, EXE/PDB identity PASS**, owned temporary source checkout deleted; no app build or GUI launch.
- **Crash tooling provenance only:** initial read-only [#39918699786](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39918699786) found ProcDump and cdb/WinDbg absent in checked paths and the matching PDB in `out/symbols`. On [#39920113943](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39920113943), official Microsoft Sysinternals ProcDump **12.02** `procdump64.exe` was downloaded only to disposable Windows scratch, Authenticode publisher/status `Microsoft Corporation / Valid` and SHA-256 `22c2a2b09ade73a342a18dab838354385f73fc98e324b9903fd61fff949c5124` verified, then all temporary binaries removed; **no installation, debugger attachment, registry change, or crash reproduction**.
- **No exception-time minidump was captured and no native call stack has been analyzed.** The historical October 23 crash retained only `.wer` data and the unloaded error offset, which cannot establish root cause. A proposed owned-PID monitor wiring change was rejected by the current tool safety check and **was not committed**; do not claim it was enabled. The future safe path is a separately authorized, one-shot, test-owned, process-specific second-chance exception capture using verified tooling, followed by matching PDB/symbol analysis; no global WER LocalDumps, no process-name-wide attachment and no raw memory dump publication.
- **No regression in prior evidence:** PX12 functional GUI [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501) remains PASS at its original SHA; visual [#39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462) remains FAIL on abnormal owned app exit. G01 cause OPEN. Central Windows remote-shell request returned to idle, queued/running CI 0. User-excluded G03–G05 and stopped G07 unchanged.

---

# PX12 visual shutdown failure: WER inventory and fail-closed fixture cleanup — 2026-10-23

- Source-only harness change `4b901a6e0427ce917622fa4eb0e3b1cabbe92560`: when `FLY_PX12_VISUAL_COMPARE_ONLY=YES`, the actual owned `flyExplorer.exe` exit code is still printed and abnormal exit **must still fail**; independently check the pre-existing user-profile sentinel and, under an explicit owned scratch ancestry/no-link guard, retire the isolated synthetic fixture **before** raising on nonzero app exit. Other GUI acceptance entry points and product C++/WinUI application code are unchanged.
- Windows read-only exact historical Event 1000/1001 and WER inspection [#39916416607](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39916416607): the 2026-10-23 06:32 UTC `c0000005` `Microsoft.UI.Xaml.dll` crash has **one system WER ReportArchive `.wer` report and no `.dmp` in the inventoried matching system report directory**, no matching ReportQueue entry; the retained Release EXE was present, but the checked `out/winui/Release/flyExplorer.pdb` and standard cdb/WinDbg paths were absent. **A crash call stack and root cause could not be established.** Do not infer that no dumps/symbols exist outside the specifically inventoried locations.
- Focused Windows [source-only #39916876932](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39916876932): exact-source Python syntax and **2/2 source contracts PASS**, temporary source checkout retired; **NO new native Release build, GUI launch, crash reproduction or fresh screenshots.** Structural/source-only PASS does **not** prove the new cleanup branch has executed under an actual access violation. Prior #39911686462 visual run **still FAILS normal-exit acceptance**, while prior PX12 functional [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501) remains PASS at its original source SHA.
- Next G01 crash investigation, if specifically resumed with authorization and a credible one-shot reproduction plan, requires an **owned-process native exception-time dump plus matching symbols**; the existing live-process timeout-only dump helper cannot capture an already-exited access violation. Avoid speculative XAML teardown edits or rebuilding previous accepted suites. G03–G05 excluded, G07 stopped.

---

# PX12 Windows Explorer matched address visual review: captured, exit AV — 2026-10-23

- **Exact source:** `f0980b515f47288c14b6aded2d1829e2620d421e`. Focused Windows [visual run #39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462): runner-health / GUI dependencies / Release build **PASS**, actual matched 96-DPI dark 940×620 flyExplorer/native Explorer header screenshots **3/3 CAPTURED**, direct pixel review performed; **visual acceptance NOT PASS** because owned `flyExplorer.exe` terminated `0xC0000005` instead of 0. Prior focused functional PX12 GUI [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501) is unchanged and remains PASS at its earlier exact SHA.
- **Observed:** flyExplorer's single `Nested — Left` candidate was legible below the editor with no apparent overlap at this configuration; its address chrome has less horizontal room than Windows Explorer's focused address editor. These different product layouts are not by themselves a pixel defect. Explorer suggestion/history popups were excluded from capture for user privacy; only `Ctrl+L`, focused input of the same synthetic prefix and Escape were exercised on a verified **new** `CabinetWClass` HWND. Full native Explorer address parity, Light theme, High Contrast, DPI 125/150/200 and Narrator are **NOT tested**. See [PX12 visual comparison](PX12_VISUAL_COMPARISON_20261023.md).
- **Crash:** [Windows WER inspection #39912873511](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39912873511) found matching Application Error 1000, `flyExplorer.exe` PID 9492, `Microsoft.UI.Xaml.dll`, exception `c0000005`, fault offset `0xA0981`, UTC 06:32:05.673 on 2026-10-23. **Cause NOT established**, G01 existing intermittent shutdown risk remains open/reproduction-deferred; no speculative product patch or repeated build. The test exited before its legacy-profile-unchanged sentinel: that check is **UNVERIFIED**, not PASS.
- **Evidence and cleanup:** original 3 bounded screenshot PNG hashes/metadata read in [#39913822771](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39913822771). Crash-skipped owned synthetic fixture (one) verified and retired **PASS** [#39914030926](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39914030926); screenshot log frames preserved, user files untouched by cleanup, Windows VM request returned to idle. This documents a partial comparison, **not** final visual release acceptance or G01 root-cause correction. G03–G05 excluded and G07 stopped.

---

# PX12 actual Windows address candidate click and navigation failure — 2026-10-23

- **Focused Windows GUI acceptance PASS:** exact flyExplorer source `32cb6cd8bd196160d621a30575a3fffd1dd076f0`, [central registered run #39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501), `scope=gui-address-candidate-chrome`, real Release build **PASS** (194,730 ms), single actual WinUI `functional-px12-address-candidate-chrome` **PASS** (6,250 ms, exit 0), runner-health **PASS** (595 ms), pinned GUI dependencies **PASS** (163 ms). Central Quality [#39907556944](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907556944) **PASS**; exact-source Python syntax (4 files) and two harness source contracts **2/2 PASS** in [#39907877634](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907877634). This is a single focused real interactive scenario, not full GUI/Explorer equivalence or separate visual pixel acceptance.
- **Actual GUI oracle:** a preloaded disposable `Left/PX12Vanishing` candidate remains displayed, then its **test-owned empty folder only** is removed before the candidate's actual WinUI Invoke. Immediately after invoke the address editor must display the still-committed `Left` folder, and the asynchronously delivered Shell failure must explicitly report that the previous folder is retained; actual `Nested` and `readme.txt` rows and one pane-folder tab remain. For the existing `Nested` candidate, immediately after Invoke the address must be **either** the previously committed Left folder **or** the already committed Nested target (never the unfinished typed prefix); the final target address and `PX12OwnedDestination.txt` row must load, while the former parent file row disappears. This makes the fast-completion versus pending boundary explicit instead of assuming the native result always arrives after UIA reads.
- Product code remains the earlier `MainWindow::OnAddressSuggestionClicked` change `f997de8633b32c1a9a91f85db1bb14d22dc8fb38`. This turn added only `tests/winui/test_px12_address_chrome_gui.py`, its source contract, a dedicated flag and `address-candidate-chrome` area in `test_shell_gui.py` and `run_checks.py`, and the central control-plane exact-scope registration. Required positive markers, normal WinUI process exit **0**, unchanged original user-profile sentinel and owned fixture retirement are acceptance conditions. The central Windows request slot has been restored to idle; no global settings, external file paths or user-owned folders were touched. Full PX12 Explorer breadth, G01 intermittent root cause, and standalone screenshot/pixel visual review are **not** asserted; G03–G05 remain excluded and G07 remains stopped.

---

# PX12 address-suggestion pending navigation chrome — 2026-10-23

- **Scoped product change:** `MainWindow::OnAddressSuggestionClicked` now restores `AddressBox` and `BreadcrumbPanel` from the active `Current().snapshot().parsingName` immediately after `OpenFolder(path)`, before hiding the editor, matching the existing Enter-submission semantics. A clicked autocomplete candidate is a pending asynchronous Shell target, **not yet the committed folder**. A late navigation failure must not overwrite newer input; native completion, PaneTab routing, path parsing and the existing 8-choice/2048-index in-memory suggestion bounds are unchanged.
- Product source `app/winui/MainWindow.xaml.cpp` and one targeted method in `tests/winui/test_window_tab_navigation_chrome_contract.py` changed; product SHA `f997de8633b32c1a9a91f85db1bb14d22dc8fb38`. Central owned Windows [focused PX12 source-only #39906179191](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39906179191) **1/1 PASS**, exact-main checkout, Python syntax and test-owned scratch retirement PASS; remote-shell request restored to idle, no overlapping Windows CI.
- **Release/native build NOT RUN; actual GUI/path-failure interaction NOT RUN; pixel/visual verification NOT RUN.** The new test is a structural regression for the candidate-vs-committed chrome contract, not a runtime proof. Previous F06 accepted address candidate navigation and PX10 selection GUI evidence remain unchanged. PX12/Explorer location breadth remains PARTIAL; G01 repro-deferred, G03–G05 excluded and G07 stopped.

---

# PX10 owned filter/group selection and focus GUI acceptance — 2026-10-23

- **Focused actual Windows GUI PASS**: [central registered PX10 #39904803892](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39904803892), exact trusted product main `1421e964dc41e02b89de3e244b623815ecd4180c`, `scope=gui-selection-projection` on the interactive Windows VM. Runner-health **PASS** (549 ms), pinned GUI deps **PASS** (157 ms), native Release build **PASS** (173,217 ms), and single targeted `functional-px10-selection-projection` **PASS** (16,616 ms, exit 0). This is an isolated diagnostic/focused acceptance, **not** a full GUI suite or overall release approval (`NOT_FINAL_ACCEPTANCE=1`).
- `run_checks.py` positively requires test-owned GUI markers for physical Ctrl+Shift+F name-filter input, two independently UIA-selected synthetic local files surviving filtering, keyboard focus retained in the *actively edited filter TextBox*, Type grouping and ungrouping retaining both selected file identities, file row keyboard *focusability* after grouping, grouped filter clear retaining editor focus, filtered-out selected files disappearing without any visible selected ListItems, unchanged owned input file hashes, application exit code zero, legacy-user-profile sentinel unchanged and synthetic-fixture retirement. Selection-count UIA peer may be absent when empty: the oracle now treats absent or blank text as zero **only after independently confirming no rendered ListItem remains selected**. No arbitrary user file/folder, clipboard, desktop-theme/DPI, image capture or external Shell action was exercised.
- Prior exact-source Windows runs [#39902296241](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39902296241), [#39902977295](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39902977295), [#39904044886](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39904044886) each built Release but respectively uncovered GUI harness assumptions about a live flyout automation name, incorrectly requiring native-row focus after manipulating the editor's UIA value instead of testing physical text input/editor focus, and requiring a zero-text `SelectionCountText` peer to be visible. Fixed only the owned GUI test and focused harness, **no product behavior change** following source-level PX10 event-ownership fix `2c4410c4438c60e476391848612f16c61d40f650`.
- Tests added/updated within the accepted change: `tests/winui/test_px10_selection_projection_gui.py`, its source-contract counterpart, dedicated `FLY_PX10_SELECTION_ONLY` entry in `test_shell_gui.py`, and `selection-projection` scope in `tools/winui/run_checks.py`. Central control plane supplies `gui-selection-projection` without triggering unrelated GUI suites; central Quality #39901589352 **PASS**, harness preflight run #39904780402 **PASS**, remote-shell slot restored to idle after acceptance. Real *row focus restoration while a row retains keyboard focus through a programmatic external list mutation* is **not separately proven**; the passing focus oracle covers interactive filter-editor focus and grouped file-row keyboard focusability. No pixel/visual acceptance or excluded G03–G05/G07 checks performed.

---

# PX10 stale selection-event projection ownership — 2026-10-23

- **Product change:** `MainWindow::OnFileSelectionChanged` now verifies the source ListView's current WindowTab identity and the pane's active PaneTab/route before acting on delayed `SelectionChanged` notifications. `AddedItems` is further restricted to actual members of the currently rendered ListView (`view.Items().IndexOf`), so a discarded row with a valid file tag cannot activate the wrong pane after filtering, sorting, grouping or switching workspaces.
- This is a **source-visible asynchronous event ownership risk**, not an independently reproduced interactive defect. Existing path-identity-based selection/focus restoration in `FillFiles`, filtered/hidden row omission, group heading exclusion, native Shell selection, file operations, and session state are unchanged.
- Changed `app/winui/MainWindow.xaml.cpp` and added focused `tests/winui/test_px10_selection_owner_contract.py`. Exact product SHA `2c4410c4438c60e476391848612f16c61d40f650`: [central owned Windows source-only #39892102917](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39892102917) **3/3 contract PASS**, exact checkout and test-owned scratch cleanup PASS. Remote-shell slot returned to idle.
- **Release/native build NOT RUN; functional GUI and visual/pixel acceptance NOT RUN.** This test checks code structure, not actual delayed WinUI delivery, selection highlight or focus. Any separate filter/group selection GUI acceptance remains outstanding. G01 historical intermittent behavior remains reproduction-deferred; G03–G05 user-excluded, G07 user-stopped.

---

# PX10 Details column drag origin-ownership guard — 2026-10-23

- **Scoped product change:** during a Details header resize press, snapshot the originating `WindowTabState::identity` and active `PaneTab` index along with the existing side/column. Before the 16-ms timer or release-tail handler applies any subsequent pointer movement, reject and retire a stale drag if the window is closing, the workspace identity/pane/folder tab has changed, or the saved side/column is invalid. The name/type/size width bounds, pane-local layout, mouse-drag timer and ordinary release-tail flush are unchanged. This addresses a source-visible cross-workspace state-write risk, **not** an independently reproduced user GUI failure.
- Edited `app/winui/MainWindow.xaml.h` and `MainWindow.xaml.cpp`, and added only `tests/winui/test_px10_column_drag_ownership_contract.py` with three focused source contracts. No changes to navigation semantics, PaneTab sorting, file contents, selection handling, Shell verbs or persistent session format.
- Exact source SHA `ac9a6c3b3c2a6eafe247211153a65acc61472100`: central Windows [PX10 source-only #39890706779](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39890706779) **3/3 PASS** and owned scratch retirement PASS. Remote Shell request restored to idle. **Native Release build, actual column-pointer GUI acceptance and pixel/visual inspection NOT RUN**; no functional/visual acceptance for this new guard is claimed. The historical L08 user-observed resize cursor and any older GUI acceptance remain scoped to their own earlier evidence.
- Remaining PX10 selection behavior after filter/group and detailed column GUI visual alignment are separate, unverified candidates. G01 remains reproduction-deferred; G03–G05 remain user-excluded and G07 user-stopped.

---

# PX11/EP02 established workspace/pane/tab ownership contract — 2026-10-23

- **Decision / no product behavior change:** `WindowTab` remains an independent workspace. Each left/right pane owns its view mode, display toggles and detail-column widths; each `PaneTab` independently owns its sort order (session v4), while the active PaneTab sort is projected through the pane's `fileLists[side].sortMode`. Group selection/collapse uses a bounded transient route+tab cache rather than a new persisted setting. F14 user-opted folder view overrides remain in-memory for the current app session. This deliberately retains the existing hybrid contract, not a migration to full per-tab view/column persistence.
- Updated `docs/development/ARCHITECTURE.md`, `WIN11_PARITY_REAUDIT_20261022.md`, `EXPLORER_PARITY_REQUIREMENTS.md`, `NEXT_DEVELOPMENT_GOALS.md`, and the `window_tab_state.h` ownership comment, with a focused source regression in `tests/winui/test_arch_contract.py`. Original code/GUI implementation and on-disk v4 schema are unchanged. Previously accepted PaneTab sorting and legacy v1–v3 read behavior are not reopened.
- Exact scoped contract SHA `1bd24854f5ecf16af5a9cf54f8516b5ae6257d09`: central Windows [Remote Shell #39889749824](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39889749824) **1/1 targeted source contract PASS** (`test_px11_existing_sort_and_pane_view_ownership_contract`), exact-main checkout and owned scratch retirement PASS. Central VM Remote Shell slot restored to idle. **No native build, interactive GUI or pixel/visual acceptance was run or claimed** because no product behavior or rendered UI changed.
- PX11 full Explorer parity remains **PARTIAL/INTENTIONAL**: per-tab view/column persistence and tab detaching were neither added nor accepted. G01 intermittent startup/shutdown is separately OPEN, G03–G05 user-excluded, G07 user-stopped.

---

# PX01 same-folder changed-selection Properties GUI acceptance — 2026-10-23

- **Requested PX01 focused Windows GUI acceptance PASS** for exact flyExplorer main source `957294119abf1b21d01eb17ff33fbbe69c88afc5`: central Windows [registered run #39888301632](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39888301632) completed successfully using the new explicit `scope=gui-context-selection` (registered `desktop-a`, Windows VM interactive user desktop). Runner health **PASS** (460 ms), pinned GUI dependencies **PASS** (154 ms), exact-source Release build **PASS** (165,187 ms), targeted `gui-context-selection-Release` exit **0** (13.7 s), functional PX01 stage **PASS** (13,956 ms). No other GUI feature suites were executed.
- **Positive GUI evidence independently rechecked:** [archived marker review #39888809816](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39888809816) verified **9/9 required exact-owned positive markers**: explicit flyExplorer extension-menu choice, actual owned Properties dialog visible and closed, selection changing from A+B to A+C while the dialog was open, stale previous-selection status suppressed, synthetic source files unchanged, final files unchanged, application normal exit code **0**, and original user settings unchanged. No arbitrary Shell verb was selected; only test-owned files/processes were exercised.
- Previous focused runs [#39886793956](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39886793956) and [#39887654210](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39887654210) successfully built Release but failed their **GUI harness** before native helper invocation: the first test omitted the required explicit application `추가 옵션 표시` choice; the second introduced an unproven UIA visible/enabled predicate not present in the established owned-menu test. Corrected only the test/harness in `tests/winui/test_owned_context_properties_gui.py`, with the relevant source regression in `tests/winui/test_external_context_contract.py`. Exact SHA `957294119abf1b21d01eb17ff33fbbe69c88afc5` [focused source check #39888276956](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39888276956) **1/1 source contract PASS**, **3/3 Python syntax PASS**. Do not relabel earlier harness failures as product regressions.
- Independent central [Quality #39886381861](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39886381861) passed the newly registered and safely bounded `gui-context-selection` execution/archival route. Central successful-run retirement removed only the exact-owned temporary CI workspace (~3.18 GB), with archived bounded evidence retained; Remote Shell request slot restored to idle. No current user data or project settings were modified.
- **Acceptance boundary:** PX01 status ownership for the described same-folder, same-count changed-selection Properties case is **FUNCTIONAL GUI PASS** at this exact source/runtime/Windows environment. This is not full Windows 11 native context-menu parity, all-GUI, installer, other OS/provider, or independent pixel/visual acceptance. The central `NOT_FINAL_ACCEPTANCE=1` label applies to whole-app acceptance, not the affirmative PX01 case. G01 intermittent root cause remains open/reproduction-deferred; G03–G05 are user-excluded; G07 stopped.

---

# PX01 owned Properties GUI oracle exit/privacy accuracy — 2026-10-23

- **Test-harness-only hardening:** in `tests/winui/test_owned_context_properties_gui.py`, the owned GUI oracle now requires an actual WinUI process **exit code 0** for its final PASS and successful test-fixture retirement. A forced termination or abnormal exit can no longer be misreported as accepted. The same guard is asserted in the narrow source regression `test_late_selection_gui_oracle_is_owned_and_observable`.
- Removed `ImageGrab.grab(bbox=...)` from this **functional** oracle because a rectangle screen capture can include unrelated overlapping desktop content. The dialog is still verified by test-owned window/process identity, UIA visibility and geometry; no visual/pixel PASS is claimed.
- Exact test/source SHA `3c87b82ae114e1a053480fdbda618314f9fabe11`: [central Windows one-off #39885610745](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39885610745) **1/1 focused source contract PASS**, **3/3 Python syntax files PASS**, owned temporary checkout retirement PASS; no native Release build, interactive GUI or pixel verification was run. Remote Shell request slot was restored to idle after completion.
- **Pending:** run only the approved isolated `context-selection` interactive GUI area when such an authorized route exists. The current central registered scopes do not execute that area, and broad `gui`/`gui-probe` must not be mislabeled or substituted. The earlier PX01 product-source selection guard still lacks native-build/GUI acceptance; G01 remains unresolved and reproduction-deferred, G03–G05 excluded and G07 stopped.

---

# PX01 owned Properties selection-lifetime GUI oracle — 2026-10-23

- Added one **test-only** GUI oracle in
  `tests/winui/test_owned_context_properties_gui.py`: invoke only the
  positively identified built-in Properties verb for disposable files A+B,
  change the test-owned WinUI selection to A+C while the exact owned
  Properties window is still open (same count, different item set), close
  only that verified owned window, and ensure the delayed Shell response
  does not replace the new selection's status. Includes exact-process
  checks, original file hash preservation, bounded UIA polling and cleanup.
- Registered the `context-selection` area in
  `tools/winui/run_checks.py` for an eventual **single focused GUI run**.
  This does not claim that central CI's existing `gui-probe` profile
  executes this case.
- Added `test_late_selection_gui_oracle_is_owned_and_observable` to the
  source contract; Windows [#39882780540](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39882780540)
  at source `42400ccec2b0720a3d965921db5193852130a11c`:
  **1/1 PASS**, three Python files compiled without syntax errors and
  isolated temporary checkout retirement PASS. An earlier
  [#39882611485](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39882611485)
  attempt failed *before* test collection owing to PowerShell
  single-entry array unwrapping; corrected without re-running unrelated
  methods.
- **Native Release build and actual interactive GUI acceptance for this
  revision remain UNVERIFIED.** Adding a new central GUI validation scope
  was not authorized by the control-plane tool safety gate, so no
  broad/incorrect GUI profile was substituted and the project was not
  reported as accepted. The existing external-menu ownership guard has
  3/3 targeted **source-contract** PASS at `c8dbfe9009...`.
  The new probe can be run only through an approved isolated interactive
  path, and only for synthetic test-owned files; do not run unrelated suites.
- G01 remains open/reproduction-deferred by user instruction; excluded
  G03–G05 and stopped G07 remain outside the test scope.

---

# PX01 external Windows context menu selection-ownership guard — 2026-10-23

- **Scope:** changed only the delayed external Windows Shell context-menu
  completion status guard in `app/winui/m22_transfers.cpp`; retained the
  accepted multi-selection right-click preservation, explicit Explorer
  fallback, helper isolation, no automatic external command invocation
  and the existing context-menu 32-item/16K UTF-16 budget.
- **Observed code gap:** completion previously verified active WindowTab,
  PaneTab, route and visible folder, but not whether the user had since
  changed the selected files *within that same tab/folder*. A delayed
  native popup could overwrite the current selection's status.
- **Fix:** snapshot the bounded original selected filesystem path set,
  sort for order independence and keep it with the worker completion.
  Before applying delayed UI feedback, revalidate the currently selected
  item count and resolve current selected entries through the same active
  PaneTab model; suppress feedback if identities/paths differ or the
  tab has begun a new pending navigation.
- **Focused source contracts:** exact code/test SHA
  `c8dbfe90099b2c12bf550ff600575f25346f31bd`,
  [Windows #39878343686](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39878343686)
  — **3/3 PASS**: isolated native menu process boundary, distinct
  workspace/route guard and original selection membership guard.
  Scoped scratch clone retired. **No new WinUI native build, binary,
  GUI or pixel test was performed** for this product code revision;
  those gates remain **unverified**, not failed or passed.
- **UX boundary:** this is status ownership protection, not claim of
  full Windows 11 context-menu command/extension parity. Existing L06
  multi-select preservation remains based on prior accepted evidence.

---

# G01 all-profile startup-only Windows diagnosis — 2026-10-23

- Reproduced the **original integrated suite's pre-start test conditions**
  (same owned M19/M20/M21/M22/M23/V7 fixtures and feature flags), but stopped
  after one existing 18-second startup predicate had seen **both** the owned
  folder path and the actual `Nested` entry in the **left** WinUI file list.
  No later tab/search/file-operation GUI interactions, G03–G05 or G07 tests
  were replayed.
- Exact product source `63c61237aa3c184ef534d83383b1be36cfe859a7`.
  The focused Windows source [#39873451885](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873451885)
  passed 3/3 G01 startup harness/private-redaction tests and the AST syntax
  of the three edited Python files; no binary build/GUI was run there.
  Central [Quality #39873299998](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873299998)
  passed after updating the exact-tip-only Git checkout contract.
- One real targeted Windows [`gui-startup` run #39873813652](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873813652)
  **PASS**: `runner-health` 647 ms; GUI dependencies 173 ms;
  Release build 184,302 ms; `gui-startup-integrated-Release` exit 0 in
  approximately 3.6 s; `functional-g01-startup-diagnostic` PASS in
  3,981 ms; `NOT_FINAL_ACCEPTANCE=1`. A positive fixture-visibility
  marker is required by the harness before it can succeed.
- This **did not reproduce the intermittent G01 failure**. The run does not
  reproduce the historical *sequence* of earlier unrelated GUI test processes,
  nor certify full integration, user-visible visual fidelity or installer.
  Treat G01 as **OPEN**, do not patch native Shell logic without failure
  evidence and do not raise helper/GUI deadlines.
- A separate central maintenance correction was required because the
  newly registered `gui-startup` scope was initially unrecognized by the
  workspace retirement metadata allowlist. Its bounded, exact-target
  retirement is a separate operational step, not a product GUI regression.

---

# G01 exact-main Windows Release + focused GUI probe — 2026-10-23

- User authorized scoped live Windows verification. Ran **one** registered
  `desktop-a` central `scope=gui-probe` at exact product SHA
  `871caab7fb4729da0dffb1b08b56da2cae6b0250`:
  [central run #39871105711](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39871105711).
- Direct Windows job evidence: runner-health **PASS** (1,003 ms),
  GUI dependencies **PASS** (240 ms), Release build **PASS**
  (197,545 ms), targeted `gui-core-Release` **PASS**
  (37.1 s, exit 0); `functional-gui-diagnostic` **PASS**
  (37,547 ms). The central job concluded success, with
  `NOT_FINAL_ACCEPTANCE=1`.
- The initial Shell route failure **did not recur in this one focused**
  startup observation. This is not an integrated `gui-all` acceptance:
  the historical failing full-profile run used additional owned GUI
  feature flags. No new failing `Startup/sampled_transitions` exists,
  and no root cause or intermittent recovery resolution was shown.
- The central cleanup archived bounded owned evidence, then retired the
  verified ~3,236,461,965-byte scratch workspace. No current product
  code or user settings were changed by the probe.
- Do **not** repeat all GUI scopes merely to seek a green G01 result.
  If the original startup failure is observed again in an authorized,
  exact-SHA test-owned integrated scenario, use redacted bounded
  startup transitions to locate the failed stage. G01 **OPEN**.
  G03/G04/G05 remain excluded; G07 remains stopped.

---

# G01 startup failure-only route sampling — 2026-10-23

- **Purpose:** classify an intermittent startup-left-pane failure without
  guessing at a Shell implementation fix, adding retries, or increasing
  the native helper 4.5-second-per-attempt and GUI 18-second deadlines.
- **Changed only the G01-owned GUI test/evidence harness:**
  `tests/winui/test_shell_gui.py` samples only bounded
  `elapsed_bucket` (2-second bins), address route
  `empty/owned-left/other` and fixed Shell status category while the
  **existing** startup condition is polled. It keeps 16 transitions at
  most (first three plus recent ones) in memory.
  `tests/winui/gui_failure_evidence.py` serializes only allowlisted
  fixed codes into `panes.json/Startup/sampled_transitions` when that
  **exact** startup assertion fails. Other failures never receive the
  timeline. Arbitrary status strings, user paths and raw UIA text are
  not logged by this feature.
- **Exact source test SHA:**
  `5c1eec5428121b4a8d1655222ead6ce616dbbd1a`.
  [Windows run #39870020233](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39870020233)
  showed **3/3 focused evidence source-contract methods PASS**.
  Its final AST check command failed because a Windows PowerShell
  command-line quoting bug stripped the Python encoding string.
  Corrected **AST-only** invocation
  [Windows run #39870209119](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39870209119)
  showed `FLY_G01_STARTUP_POLL_AST=PASS`, correct exact checkout, no
  native build or GUI and clean scoped scratch checkout retirement.
- **State:** G01 remains **OPEN**: the original failed
  [integrated run #39732505243](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39732505243)
  predates the timeline and cannot retroactively be classified.
  No actual recurring left-pane failure or shutdown hang was
  reproduced, and no new binary has been built. On a genuinely
  justified same-scenario recurrence, compare the new categorical
  state transitions to the active native request route before changing
  implementation. Avoid blanket GUI loops. G03/G04/G05 excluded;
  G07 stopped.

---

# flyExplorer current development status — 2026-10-23

## Product and source boundary

- The active application is the C++/WinRT WinUI 3 dual-pane Windows file
  manager in `app/winui/`, with shared native code in `src/base/`,
  an owned isolated Shell helper, and tests in `tests/winui/`.
- Build/project inventory: all **55 current native C/C++ translation units**
  under the active app and native-core scopes are registered in at least one
  active app/helper/native-test compilation project. The **32 native-core
  headers** have recorded includes or explicit project references.
  This is a source-reference audit, not an assertion that every potential
  runtime code path executed in a fresh binary.
- History-only Python Git-object access and its associated source-inventory
  contract have been removed. Structural checks now inspect the current
  app and the active `src/base` files without requiring old Git commits.
- Personal-use private installer continues to use runtime provenance,
  precise manifest ownership, safe uninstall and actual NuGet/package
  license and NOTICE inputs. The independently bundled policy library and
  actively used Fluent icon attribution remain. No public publication,
  signing or redistribution objective is active.

## Latest focused verification

- Product changes: current-only structural tests, shell architecture
  assertions, isolation helper and neutral installer identity; no
  unrelated function or full application suites were re-run.
- Exact product source `8e01ddc1971ab6639a78ae0b0204784a20bff5e5`.
- [Windows source test #39864992776](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39864992776):
  **7/7 affected source contracts PASS**; execution then stopped because a
  scoped runner pointed unittest discovery at the wrong helper-test folder.
  The owned temporary clone was retired.
- [Windows source test #39865469684](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39865469684):
  the **remaining 3/3 tests PASS** after distinguishing native Python
  stderr from process failure. Exact source revision matched; scratch
  checkout retired. **Total changed-contract evidence: 10/10 PASS.**
- Prior Windows [Release #39779111032](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39779111032)
  at `5cf79f56b27e7d86a1fd82cc6ae171d75e04d98e` passed its then-current
  Release build; that is **not** a build of the latest code.
- Prior integrated [GUI #39739943824](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39739943824)
  applied to `74bd0f3376d34b934f059b093c014fa469447606`, **not** the
  current latest source. No current revision full GUI/pixel validation
  or installer lifecycle has been claimed.

## Product gaps and verification limits

- Full Windows 11 File Explorer behavioral/UX equivalence is **not**
  established. Refer to `WIN11_PARITY_REAUDIT_20261022.md` PX01–PX18
  and `EXPLORER_PARITY_REQUIREMENTS.md` for the existing categorized
  requirements and current evidence boundary.
- G01 intermittent initial navigation/shutdown cause remains **OPEN**.
  It must not be described as permanently solved by one functional PASS.
- G03 real DPI 125/150/200, G04 spoken Narrator/high contrast,
  G05 real USB/SMB/UNC are user-excluded; G07 real IME work is stopped.
  Their earlier unverified status is not permission to rerun them.
- Only test the changed feature and transitive dependencies; re-use
  exact-source evidence for unaffected behavior. New builds, full GUI,
  visual matching and installer/package operations require a justified
  scope and their own acceptance; do not silently include them.

## Technical information sources

- `AGENTS.md`, `docs/development/VERIFICATION_PROFILE.md`,
  `docs/development/AGENT_EFFICIENCY.md` — validation instructions
- `docs/development/NEXT_DEVELOPMENT_GOALS.md` — prioritized open goals
- `docs/development/EXPLORER_PARITY_REQUIREMENTS.md`,
  `docs/development/WIN11_PARITY_REAUDIT_20261022.md` — parity gaps
- `docs/development/UI_UX_AUDIT.md` and `ERROR_HISTORY.md` —
  targeted experience findings and failure diagnostic context
- `docs/development/PRIVATE_PACKAGING_VERIFICATION_20261023.md` —
  exact-source private installer input checks

Historical development evidence is not a substitute for acceptance of the
latest source or binaries; active requirements and the actual owned tests
always control.
