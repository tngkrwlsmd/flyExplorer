# flyExplorer current status — 2026-10-22 EP05 native Explorer GUI acceptance added; NOT TESTED

## 2026-10-22 — add owned Windows Explorer native delegation GUI coverage

- At prior main `986a178f2cf26dc384032b8e989011cbad3cf484`, the official full Windows Release/GUI
  run #39699010377 passed but did not trigger the new native Explorer
  context-menu entries. The previously hidden ZIP source remains on
  hold pending this explicit P0 acceptance.
- Added `test_ep05_explorer_handoff_gui.py` to the existing owned
  GUI harness, activated only for `gui-all`. It right-clicks a synthetic
  file and the synthetic folder's blank list, invokes only the exact
  product-owned Windows Explorer menu commands, checks the app's
  successful native handoff feedback and locates a new Explorer HWND
  showing the synthetic source. Only HWNDs created after the start
  baseline and verified against a test-owned fixture may be closed.
  Files are byte-compared before/after and real user Explorer windows
  are not inspected or controlled.
- Registered a source contract for the new end-to-end check.
  **NOT TESTED yet:** newly added GUI code and exact current HEAD require
  source and Windows full `gui-all` validation. Do not claim OS
  delegation accepted or delete native ZIP modules until that succeeds.
  G01 open; G03-G05 excluded, G07 user-stopped.

# flyExplorer current status — 2026-10-22 exact-SHA Release and GUI acceptance; G01 open

## 2026-10-22 — current Release and full owned GUI PASS at exact source SHA

- flyExplorer main `e5c6cbd01f8e0f3a87679349a2956886a01f3405` passed the official central
  [GUI run 39699010377](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39699010377):
  runner-health, Python GUI dependencies, policy, product/source contracts,
  Windows Release build and the functional GUI stage all **PASS**.
- GUI window-tabs, shortcuts, filter-preset, folder-tree and integrated
  `gui-all` sub-stages exited 0. The isolated, synthetic GUI log
  confirmed actual Windows registered TXT type plus OS icon, Unicode
  row metadata and sorting, multi-file Copy, real Move, Korean collision
  Cancel without overwrite, KeepBoth without replacing the original,
  Recycle confirmation canceled without trash mutation, owned session
  save/restart/restore/clear, and application exit code 0.
- Original six user profile/config files remained byte-for-byte
  identical by SHA256, and all synthetic file fixtures were removed.
  The acceptance log was checked separately using a bounded, read-only
  archived-evidence command; no real user files were tested or mutated.
- **Not covered by this pass:** actual file/background context click
  through the newly delegated Windows Explorer window, sporadic G01
  shutdown/root-cause closure, signed installer/rollback/public release,
  final disposal of retained native ZIP engine. The earlier intermittent
  empty-startup-address failure on 39695119767 remains recorded, although
  a subsequent core-only GUI probe and this full GUI run passed.
  G03/G04/G05 remain user-excluded and G07 user-stopped.
- This is exact-source acceptance for `e5c6cbd01f8e0f3a87679349a2956886a01f3405`; later docs-only
  updates are not a new runtime build acceptance.

## 2026-10-22 — exact-SHA GUI repeat isolated unsupported type-prefix check

## 2026-10-22 — exact-SHA GUI repeat isolated unsupported type-prefix check

- Product main `9ec2ebc522b13b0763975c57f4810e4252d583e7` passed central source (4 structure, 261
  product, 51 harness, 30 infra) on
  [39694954167](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39694954167)
  and Release build in
  [39696540702](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39696540702).
  The GUI run passed window-tabs, shortcuts, filter-preset, folder-tree,
  but `gui-all` failed at an assertion requiring the literal prefix
  `Windows 유형:` inside a file row. The product's type column only
  renders `FileDetail.typeLabel`, either OS `SHGetFileInfoW` friendly
  label or bounded fallback; source contains no such prefix.
- An earlier GUI attempt
  [39695119767](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39695119767)
  failed once with an empty startup address; the exact same revision
  later passed the scoped diagnostic GUI startup
  [39696013338](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39696013338).
  This intermittent startup risk is not closed by a passing probe.
- Revised `test_m22_gui.py` to obtain the host's actual registered
  `.txt` friendly type using `SHGetFileInfoW` with the same
  `SHGFI_USEFILEATTRIBUTES|SHGFI_TYPENAME` contract used by the
  isolated helper, and require that non-empty Windows result within
  the app row before/after column resize. This is a stronger
  OS-grounded assertion than the obsolete prefix; no C++ app changes.
- Added one source regression contract for the OS baseline and retained
  the exact file-copy/move, collision/cancel, icon and user-data
  preservation assertions after this checkpoint. **NOT YET RUN** on
  the new revision; Windows GUI and native Explorer handoff remain
  unaccepted. G01 remains open; G03-G05 excluded and G07 stopped.

## 2026-10-22 — owned Windows GUI failure bounded to M22 type-label assertion

## 2026-10-22 — owned Windows GUI failure bounded to M22 type-label assertion

- Exact product SHA `c5de0c96b26f3958ee21be84c3a911354ee79e34`,
  central Windows GUI
  [39693531282](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39693531282):
  runner-health, dependencies, policy, source, Release build **PASS**;
  gui-window-tabs, gui-shortcuts, gui-filter-preset, gui-folder-tree **PASS**.
  gui-all **FAIL**, first relevant error at `test_m22_gui.py:29`
  demanding literal `txt 파일` in the displayed Korean test file row.
- Exact fixture `큰.txt` was visible in retained synthetic UIA
  evidence; Windows registered type strings are machine/association
  dependent and the bounded evidence redacts non-fixture labels.
  Therefore the failure is **not proof of a product type-rendering bug**.
  Existing subsequent GUI assertion already requires `Windows 유형:`
  returned by native metadata for this row, so drop only the obsolete
  literal fallback claim and retain the stronger OS metadata check.
  Also update the test's collision KeepBoth button name to match
  `ConfirmCollision`'s actual current `이름 바꿔 둘 다 유지`.
- Existing exact-SHA GUI passed focused WindowTabs, shortcuts,
  filter presets and local folder tree; the integrated M22 section
  and following steps remain unaccepted. App PID exited 0, six
  original settings hashes unchanged and synthetic fixtures removed
  as recorded in the owned GUI log. User-owned file contents not
  recorded or modified.
- This test-only correction has **NOT** been executed on its new SHA.
  The newer deferred-menu route guard `c519818b` likewise needs
  fresh source/Release/GUI checks before acceptance. Do not delete
  retained F08 ZIP engine until OS delegation is actually accepted.
  G01 open, G03-G05 excluded and G07 user-stopped.

## 2026-10-22 — exact-SHA Release accepted; deferred context menu bug isolated

## 2026-10-22 — exact-SHA Release accepted; deferred context menu bug isolated

- Central Windows Release
  [39685083488](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39685083488)
  **PASS** on `c5de0c96b26f3958ee21be84c3a911354ee79e34`: runner-health, policy, source,
  Release build. This does not accept GUI/native Explorer handoff.
- Source review found an independent race in file/background context
  menu click callbacks: a captured PaneTab index could be out of bounds
  after tab removal, and navigation inside the same PaneTab can preserve
  its route identity while replacing the underlying folder. An old
  menu action could therefore target an unrelated current selection.
- Bind both original Shell parsing folder and filesystem folder at
  menu creation; reject any click when WindowTab/PaneTab, bounds, route,
  current folder or file-operation state no longer matches. Preserve
  exact selected logical IDs for file menus. No mutation command is
  dispatched after failed context checks. Added a focused static
  regression guard.
- **NOT YET ACCEPTED:** this new source change needs matching-SHA
  Release and GUI verification. Previous `c5de0c96b26f3958ee21be84c3a911354ee79e34` GUI
  [39693531282](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39693531282)
  was submitted before this change and must be scoped to its exact SHA.
  No claim of native Explorer runtime acceptance. G01 open,
  G03-G05 excluded, G07 user-stopped.

## 2026-10-22 — actual Release compilation isolated C3773

## 2026-10-22 — actual Release compilation isolated C3773

- Exact main `e482c19322d0c98049593f5ac915d13741f1f781`, central Release
  [39684379737](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39684379737)
  passed runner-health, policy and complete source stage. Release build
  then FAILED at `app/winui/m22_transfers.cpp:850`, MSVC C3773:
  ordinary `return;` is forbidden inside `winrt::fire_and_forget`
  `MainWindow::ConfirmCollision` after `co_await`.
- Replaced only the early exit after the collision-skip choice with
  `co_return;`. Existing skip counts, cancel/KeepBoth confirmation,
  Shell worker and partial-output protection remain unchanged.
  Added a focused source-contract guard against plain return reintroduction.
- This change **has not yet passed** its own Windows build or GUI.
  Do not mark the product/build as accepted before a matching-SHA Release
  and GUI run. G01 intermittent termination remains OPEN; G03-G05 excluded
  and G07 user-stopped.

## 2026-10-22 — follow-up Release found one remaining stale focus assertion

## 2026-10-22 — follow-up Release found one remaining stale focus assertion

- Exact main `614438a030adc12e1e1eb607eb32c2871fa69c95`, central Release
  [39684013477](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39684013477):
  runner-health/policy PASS, 260 product-source tests with **one failure**.
  The earlier workspace dispatch failure is resolved. The remaining
  `test_file_display_options_contract.py` assertion still required a
  single-line focus expression; current `FillFiles` instead uses
  `if(focusRow){` to allow reveal-triggered `ScrollIntoView` before
  `Focus(FocusState::Programmatic)`. This is also a test expectation
  mismatch, not evidence of a product GUI defect.
- Changed only that source contract, explicitly asserting both
  focus restoration and conditional scrolling. Product code untouched.
  **NOT YET VERIFIED:** current correction needs a fresh Release run.
  No Release compilation or GUI has occurred in this run.
  G01 OPEN; G03-G05 excluded; G07 stopped.

## 2026-10-22 — central Release source stage failed on stale contracts

- Exact trusted main `924888fe0c418422cb3ab446f076d0d3423bffa5`, central control-plane run
  [39682792082](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39682792082):
  runner-health and policy PASS; product-source contracts ran 260 tests
  and FAILED 2; compilation/link and GUI stages were **not reached**.
- The two failures were reproduced with exact source in an owned temporary
  Windows VM checkout (diagnostic run
  [39683625918](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39683625918)).
  `test_arch_contract.py` expected direct `active().model.dispatch`
  after the controller began binding `state=active()` and preserving
  `tabSortModes`. `test_file_display_options_contract.py` expected
  unconditional same-folder selection restoration even though a successful
  rename/create reveal now deliberately suppresses the old selection.
- Updated only the two stale source-contract assertions to check current
  state/route ownership and explicit reveal precedence. Product behavior,
  build inputs and Windows Shell operations are unchanged.
- **NOT YET VERIFIED:** this test-only correction needs a fresh exact-SHA
  central source/Release run; Windows build, GUI and final visual acceptance
  are still pending. G01 intermittent close issue remains open, G03-G05
  excluded and G07 user-stopped.

## 2026-10-22 P1 — fail closed on inconsistent aborted transfer report

## 2026-10-22 P1 — fail closed on inconsistent aborted transfer report

- At main `e0ea04aa688ada741333079e271e72241205d67c`, `FileOperationController::acceptTransfer`
  classified completion as success when `report.error==ERROR_SUCCESS`,
  even if `report.aborted` was true. The existing isolated/native
  worker normally maps abort to an error but the controller did not
  defensively enforce the same invariant.
- When the report carries `aborted`, classify it as Failed regardless
  of the reported error code. Keep the existing no-retry/no-overwrite
  behavior, source/destination refresh after possible partial commit,
  and user notice that earlier items may have been processed.
  Collision preflight already rejects aborted reports and is unchanged.
- Added a source-only regression contract to check the guard and the
  existing UI partial-outcome notice; **not executed**.
- Windows compile/link, source/native tests, GUI, actual cancellation,
  recovery and visual verification were **NOT TESTED**. This is
  conservative source hardening, not proof of a new runtime defect.
  G01 remains open and G03-G05 exclusions/G07 stoppage remain in force.

## 2026-10-22 P1 — external Shell-menu completion status ownership

- At main baseline `36240aba60bfe1d39453f0ae4cb4c330d36ad08e`, the isolated classic Shell context-menu
  worker posted its final message to whichever workspace and folder tab
  happened to be active when it completed. This is a confirmed source-level
  status ownership gap, not a diagnosed file corruption or Shell execution bug.
- Snapshot the initiating WindowTab identity, active pane, PaneTab, route and
  filesystem path. Suppress the detached worker's late status when the
  original context is no longer visible, when closing, or while another
  file operation is busy. Validate array bounds and visible route before
  launch. Preserve the existing 32-item, fixed-drive, read-only/path
  restrictions and isolated helper's unchanged exit-code handling.
- Updated a focused source-only negative contract in
  `test_external_context_contract.py`. Windows build, source/native
  test execution, GUI, visual acceptance and actual Shell menu runtime
  behavior were **NOT TESTED**. G01 intermittent shutdown is unchanged;
  G03/G04/G05 exclusions and stopped G07 are unchanged.

## 2026-10-22 P1 — exclude unused ZIP codecs from active app build

- From main baseline `5098e53143b1d115aea0e6a743432bb4998b6b91`, removed only four unused F08 codec
  translation units (`zip_raw_deflate.cpp`,
  `zip_raw_deflate_compress.cpp`, `miniz_tinfl.c`,
  `miniz_tdef.c`) from `flyExplorer.project-template.xml`.
  The native source tree, upstream license files and native safety-contract
  tests are retained, and all non-ZIP project compile entries are unchanged.
- Updated source contracts so they prohibit inactive codecs from re-entering
  the product build while continuing to check their bounded native code.
- **NOT TESTED:** no Windows build, source/native tests, GUI, package,
  linker symbol resolution or binary-size inspection has been run.
  This is intended build-input cleanup, not a measured runtime optimization.

## 2026-10-22 P1 — retire unreachable ZIP creation/extraction UI

- Starting from main `3f27e628c939c0efba10fcd06999ee8a5e72ebe0`, removed all six unreachable
  MainWindow ZIP create/extract worker methods, their five busy flags,
  batch cancellation token and obsolete archive-specific toolbar cancel
  handling. Shell transfer cancel/feedback, dual-pane file commands and both
  native Explorer handoff paths are unchanged.
- Native ZIP codecs, bounded parsers/writers/extractors and their source
  safety-contract tests remain in-tree; six stale WinUI-target tests were
  removed and one central negative integration contract now prevents
  accidental restoration of the invisible ZIP entrypoints. A pre-existing
  raw-Deflate test assertion expecting an exposed ZIP menu was corrected.
- Condensed obsolete F08 WinUI implementation descriptions in
  `ARCHITECTURE.md` without deleting security/rollback evidence from Git.
- **NOT TESTED:** Windows build, source/native contract execution,
  native Explorer handoff, functional GUI, and pixel acceptance are not run.
  This is not acceptance of current main or resolution of G01.

## 2026-10-22 P0/P1 — retire invisible F08 ZIP inspection UI

- On main baseline `c759eefcdbacb82c271f03e768ec3151675eca6f`, the Explorer delegation already hides
  the ZIP inspection command. Removed the unreachable ZIP inspector's XAML panel,
  MainWindow handler/worker/state and five obsolete cross-panel collapse calls.
- Retained the bounded native ZIP inspection parser and inactive ZIP creation/
  extraction sources for exact-source rollback and separate removal review.
  Existing tests now assert that the hidden inspector cannot be reached through
  WinUI while preserving the parser safety contract.
- **NOT TESTED:** Windows build, source/native test execution, native Explorer
  handoff, functional GUI and visual acceptance were not run. This source
  cleanup does not certify the latest Explorer delegation or close G01/G07.
  User-excluded G03/G04/G05 remain excluded.

## 2026-10-22 P0 — align native Explorer menu availability

- The file context menu now disables Windows Explorer handoff if the
  accumulated selected-path budget exceeds the native delegation limit
  (`kMaxPathUnits=16*1024`). The menu uses the existing conservative
  counted source units; native same-parent, lexical/path and duplicate
  validation remains in the worker. Normal selection behavior is unchanged.
- Condensed superseded F08 implementation-phase narratives in the active
  handoff and future-goals register. Historical source changes and safety
  evidence remain available in Git and the retained current-status ledger.
- **NOT TESTED:** this source-only change was not built, compiled or run
  on Windows, and did not perform GUI or pixel tests.



## 2026-10-21 G01 — owned native shutdown dump collection ready

- Main baseline c410239765ee8bb5ff46ba86d4baa61e5ffaff71; no product implementation,
  binary or UI change. Added tests/winui/owned_process_dump.py so an owned Popen
  launcher can capture native stack/context data before timeout cleanup.
- Collection verifies the original live handle/PID/image and known out/ executable,
  duplicates query/read/synchronize rights into a separate collector with an
  explicit inherited-handle list, and restricts unique output to ignored logs/.
  It never reopens a target by arbitrary PID or grants the collector terminate
  rights. The collector has a ten-second deadline and does not change WER/registry.
- The shortcut GUI test now invokes this hook only after its normal 14-second
  close wait fails, then retains its original termination/failure. The real WinUI
  timeout hook has not been exercised; no new functional GUI/visual PASS is claimed.
- **Actual native diagnostic PASS:** reused Release helper SHA-256
  639017e014cfc9c9eeb88fc0f8f35148c0f57be6b3d8879bedec7db35f0c2e5d in the existing
  test-owned synthetic block case. Collected and validated 4 threads, 4 contexts
  and 4 stack buffers. The target remained alive afterward; owned job termination,
  fresh recovery, kill-on-close, all six legacy sentinels and fixture cleanup PASS.
- Initial dump validation rejected repeated unused directory slots. Actual Windows
  output had four UnusedStream slots; ignoring those placeholders fixed the parser
  while real duplicate/out-of-bounds data still fails. Eight portable corruption/
  ownership regressions PASS. Standard harness 51/51, related helper/shortcut
  contracts 16/16 and changed Python static checks PASS.
- Bounded text evidence is ignored under logs/owned-process-dump/. The synthetic
  raw dump was removed with its owned fixture. Future WinUI raw dumps remain local
  and ignored; current automatic failure artifacts do not select .dmp files.
  The machine has no cdb executable at the checked SDK path; no debugger was installed.
- This prepares evidence capture for an actual recurrence; it neither reproduces
  nor explains/fixes G01. A captured native dump is not a symbolic stack diagnosis.
  Reuse accepted G02/G06/session/G08 results, do not repeat identical app runs or
  resume user-stopped G07/excluded G03/G04/G05.

## 2026-10-21 G08 — repeatable owned helper page benchmark added

- Main baseline 27395b3c6727c236afd2feb8cada289317db94e1; product code/binaries
  unchanged. Measured the canonical Release runtime helper, SHA-256
  639017e014cfc9c9eeb88fc0f8f35148c0f57be6b3d8879bedec7db35f0c2e5d
  (identical to out/helper/Release). Windows 10.0.26300, Python 3.10.11.
- New tests/winui/helper/benchmark_pages.py measures fresh-process path-page IPC
  on disposable fixed-local folders. It first passes 200 files before creating a
  requested larger fixture, validates strict wire replies, all expected names,
  page sizes/flags, no duplicates/missing entries, file contents and settings
  guards. It records first/per-page/total/max timing and cleans owned fixtures.
  Existing wire functions were extracted unchanged for both native probes.
- Actual one-pass observations, uncontrolled OS caches (not cold-cache guarantees):

  | Owned files | Pages | First page | Sum of page round trips | Slowest page |
  | --- | --- | --- | --- | --- |
  | 200 | 1 | 117.968 ms | 117.968 ms | 117.968 ms |
  | 8,000 | 8 | 169.320 ms | 1,458.497 ms | 274.177 ms |

  The 8,000-file fixture took 6,797.216 ms to create, separately measured.
  Round trips include process startup, Shell enumeration and IPC, excluding
  Python reply validation/fixture creation/cleanup. All entries/content and
  original legacy/WinUI user settings were preserved. Helpers and fixtures cleaned.
- This is a diagnostic baseline, not a speed improvement, GUI responsiveness,
  sorting, memory, indexed-search/25,000-item or 20,000-item certification.
  No app GUI, excluded G03/G04/G05 test or privileged remote job was run.
- Added corruption/paging/timeout regressions. The standard harness first exposed
  an existing local installed-tests-package collision. Explicit file loading now
  avoids that collision, handles duplicate basenames and lazy sibling imports,
  and rejects empty/missing/import-failing contracts. Final standard harness
  43/43 and related Shell/streaming contracts 19/19 PASS; changed Python static
  checks PASS. Actual helper process/recovery/owned cleanup regression also PASS.
- Ignored evidence: logs/helper-page-benchmark/benchmark-1792547969671663600.json,
  helper-regression.log and benchmark-console.log. Measured script SHA-256
  7405514ca8917c10fdcbcc6ecdf49fb4b68706c1e4ac0cdd85e66a1afcab274a.

## 2026-10-21 G07 stopped by user; retain separate shutdown observation

- The user stopped the actual Korean IME task. Do not automatically resume it.
  G07 has no new IME acceptance; failed English/other input preconditions are not
  evidence of an app composition defect. No tracked product change was made.
- During cleanup, owned PID 15472 lost its window but remained alive. Its executable,
  PID/start time and absent main window were checked before owned-only termination.
  Cleanup exit 0xFFFFFFFF, original settings and 13 synthetic files unchanged.
  No native stack was captured. This preserves the G01 shutdown risk; it is not a
  normal-exit PASS, root-cause diagnosis or justification to repeat identical runs.
  Ignored logs/g07-korean-input/result.json retains the scoped evidence.

## 2026-10-21 G01 — legacy v1/v2/v3 actual restore and v4 migration PASS

- Source main ebe26cf9527250909c0e62b698e5e7803a8317ea; product implementation
  unchanged. Reused Release EXE SHA-256
  78fb331fa88346fb4622fea4872db4ce2825e6ca2010653efa825bdacbff031f.
  Three new test-owned profiles each contained one independently encoded legacy
  version, four local PaneTabs (L0/L1, R0/R1), selected left L1/right R0, left
  Name descending/right Name ascending, and 12 synthetic files. No explicit
  startup path or test auto-restore override was supplied.
- **Scoped actual GUI PASS:** all three default starts restored the selected
  path, both panes/two tabs and opposite sort directions/actual row order.
  v2/v3 restored Back availability; v3 additionally restored left compact rows
  and hidden extensions with ordinary right rows/extensions. Through the actual
  Workspace panel, Save Session explicitly wrote the current private profile.
- Independent output decoding verified version 4, valid checksum, every path,
  selected indexes, pane sort inherited by all four folder tabs, v1/v2 display
  defaults, v3's distinct flags and v2/v3 Back history. The fixture's forward
  histories were empty; nonempty forward data has native coverage only.
- Normal Alt+F4 exited 0 for v1 PID 19236, v2 PID 1784 and v3 PID 4176.
  Original legacy/WinUI user settings and each run's 12 synthetic files were
  unchanged. No owned app remains. No product rebuild/change was required.
- **Visual scope:** actual Dark restore screens were inspected at 1086x666,
  Windows 10.0.26300, unchanged display settings; numeric DPI was not collected.
  These are functional restore/presentation observations, not new BEFORE/AFTER
  product changes or full theme/column/icon/narrow-window visual certification.
- Native regression repair is already pushed as ebe26cf9 (41 native + 15 source
  checks PASS). Ignored logs/g01-legacy-session contains per-version input bytes,
  result JSON, restored PNGs and the launch/independent-output-check script.
  No central validation was dispatched or claimed.
- This closes the scoped real legacy restore/migration gap. G01's intermittent
  shutdown risk remains unresolved despite these normal exits; do not mark G01
  fully complete, repeat identical runs or add speculative shutdown changes.
  Acquire a native stack on an actual recurrence. G03/G04/G05 remain excluded.

## 2026-10-21 G01 — native session regression gate repaired for v4

- On main 64d147cd, the current native fixture built successfully but failed
  34/35 because it still expected wire version 3 from the v4 writer. The display
  source contract also referenced the removed encodeV3 entry point. This is a
  stale test expectation, not a newly diagnosed product serialization failure.
- Updated the fixture/source contract to v4 and added real serialized round trips
  with distinct folder-tab sorts across two WindowTabs. Independently constructed
  v2 and v3 byte streams now check selected tabs, paths, back/forward history,
  inheritance of each pane's sort by every tab, v2 display defaults and v3 flags.
  Legacy v1 save/load and checksum/unknown-flag rejection coverage remain.
- Actual Release native build and all 41 native checks PASS, plus 8 display and
  7 session-coordinator source checks PASS. The native test uses disposable local
  paths and private profiles; all six existing legacy configuration sentinels
  remained unchanged. No global clipboard read/write was performed.
- Product implementation is unchanged; only its stale schema comment was corrected.
  No new app build or GUI acceptance is implied. Real v1/v2/v3 GUI restore and the
  unrelated intermittent shutdown risk remain separate G01 acceptance gaps.
  Bounded before/after logs are ignored under logs/g01-legacy-session/.

## 2026-10-21 G02 — startup keyboard traversal accepted in the local scope

- Live main `44d770ee0fd4904bed52ee2cc34f02d45352cd54` matched origin/main.
  Reused the accepted Release EXE SHA-256
  `78fb331fa88346fb4622fea4872db4ce2825e6ca2010653efa825bdacbff031f`,
  product blob `f5ae92665411bcb4f3b64ea96aa2bf44cbb368ad`; no product edits or rebuild.
  The latest central CI remains run `39188826255`, source PASS for `7ac35a06`,
  not independent acceptance of this revision. This result is local Computer Use.
- **Functional GUI PASS for the remaining G02 startup/menu scope:** one fresh,
  isolated profile and synthetic local fixture, owned PID 20760. From the app's
  startup focus, 39 consecutive Tab presses reached command/navigation controls,
  left PaneTab (27), left list (32), right PaneTab (33), right list (38), then
  WindowTab (39). No mouse clicks or hidden-control focus assignment were used.
- Shift+Tab returned from WindowTab to the right list; Down selected alpha.txt.
  F6 moved to the left list; five Shift+Tab presses returned through headers to
  its PaneTab. Ctrl+L focused the full address, Tab reached quick search, and
  reverse traversal reached the address edit button and breadcrumb controls.
  Keyboard traversal then reached Sort. Enter opened its eight named modes,
  Down moved to Name descending, Escape returned visible focus to Sort, and
  Enter reopened the menu. No sort command or file operation was invoked.
- Actual focus rings, selection, command outcomes and the menu's UIA names/order
  were inspected. The tool's stale FileNameBox focused-element field was not used.
  **Normal Alt+F4 exit 0**, original legacy/WinUI settings unchanged and all 12
  synthetic files unchanged. No owned app remains.
- **Visual scope:** existing Dark focus rings and menu legibility were inspected
  at 1426x746 on Windows 10.0.26300 with unchanged display settings; numeric DPI
  was not collected. No composited-pixel change was made, so no new BEFORE/AFTER
  change gate applies. Whole-product/theme/narrow-window visual acceptance is
  not claimed. G03/G04/G05 exclusions and the unrelated G01 shutdown risk remain.
- Ignored evidence: `logs/g02-g06-keyboard/g02-startup-result.json`,
  `g02-startup-cycle.png` and `g02-menu-return.png`. Prior G06 evidence is preserved
  in `g06-accepted-result.json`. New source/build tests were unnecessary for this
  documentation-only acceptance update. G02's interrupted run remains historical;
  this completed run closes its outstanding local startup/menu normal-exit gate.

## 2026-10-21 G06 — PaneTab keyboard focus retained; scoped GUI PASS

- On baseline main `220e949f`, EXE `4a6909c8ff3f3e4bdbabc9615d41fa568686da5dd20cd8e3287de654b8331525`,
  Left/Right then Enter on a PaneTab destroyed the focused item during
  `RefreshTabs()`. Focus moved to the Name sort button; the next Enter sorted.
  Earlier immediate focus observations did not cover this settled refresh.
- `RefreshTabs()` now retains surviving TabViewItems, adjusts only the count,
  updates labels/UIA names in place and avoids redundant SelectedIndex writes.
  Product blob `f5ae92665411bcb4f3b64ea96aa2bf44cbb368ad`; Release EXE
  `78fb331fa88346fb4622fea4872db4ce2825e6ca2010653efa825bdacbff031f`.
- **Focused functional GUI PASS:** two WindowTabs x left/right x two PaneTabs,
  Left/Right+Enter in both directions with a settled 450 ms check, visible
  focus retained on the selected tab, unchanged name-sort direction, and A/B
  workspace state preserved. Owned PID 25964 exited 0; original legacy/WinUI
  settings and all 12 synthetic files were unchanged.
- **Scoped visual PASS:** directly reviewed actual BEFORE/AFTER Dark captures,
  same owned fixture and 1426x746 window, Windows 10.0.26300. Focus now remains
  on the tab; command chrome, pane geometry, rows and text hierarchy are retained.
  Numeric per-window DPI was not captured; display settings were unchanged.
  This is not Light/narrow-window, alternate-DPI or whole-product visual acceptance.
- Source checks: 11 tab-chrome + 6 shortcuts + 8 GUI-harness tests PASS.
  Release build PASS. The expanded `test_shortcut_gui.py` was syntax/static
  checked, not executed as an automated GUI suite; the equivalent four-region
  scenario above was exercised through Computer Use.
- G02 startup-only 39-Tab traversal was observed on these candidate bytes before
  the interrupted prior run. That run has no normal-exit acceptance; G02 full
  completion remains pending a bounded startup/menu traversal with normal exit.
  Baseline first close returned 0xC0000005, later baseline close and this candidate
  close returned 0. The unrelated intermittent G01 shutdown risk is not fixed.
- Ignored evidence: `logs/g02-g06-keyboard/` result JSON, BEFORE/AFTER PNGs and
  build logs. User-approved WinUI build-target preflight is already on main
  `b02c51a6`. No excluded G03/G04/G05 checks or global clipboard changes were run.

## 2026-10-20 G02/G06 — scoped keyboard and tab-name GUI observations

- Live main `db10ef42`; reused the unchanged `4bdde290` product binary with
  SHA-256 `eb89f47db33d2d12ff6abb1e6b7eb4f47c1e79adabfae3be27e8a54f9e35456d`.
  One owned local Release run, no rebuild/product edits or dependency installation.
- G06 scoped GUI PASS: two WindowTabs each reached two left and two right PaneTabs;
  all observed items named their actual level/side. Add commands targeted the active
  pane in both workspaces; left/right close commands in workspace B preserved the
  opposite pane. Ctrl+Tab/Ctrl+Shift+Tab and Ctrl+W operated on WindowTabs and preserved A.
- G02 observed PASS: F6 plus real file-row Down selection, list Tab to WindowTab
  and Shift+Tab back, Ctrl+L address editing and Tab to search, sort-menu Down,
  Escape focus return and Enter reopen. Left PaneTab Right/Left plus Enter activated
  the next/previous tab with visible keyboard focus retained.
- Automation `focused_element` stayed on FileNameBox despite real focus changes;
  it is not trusted as acceptance. Screenshots and actual command outcomes were used.
  Interrupted/occluded input attempts were not counted as product failures or PASS.
- Exit 0; original user settings and three synthetic files unchanged. G02/G06 full
  acceptance remains pending uninterrupted startup traversal and keyboard focus across
  all four pane/workspace combinations. Visual review was scoped Dark/96-DPI/1906x1016;
  no new full visual acceptance. Ignored text evidence: `logs/g01-local-20261020/g02-g06-uia-observations.json`.

## 2026-10-20 G01 follow-up — shutdown not reproduced; cause unresolved

- Live main `08e066a1` has the same product sources as the recorded `4bdde290`
  EXE (`eb89f47d...`, full hash below). No rebuild or product changes.
- Reused the same owned v4 session in two diagnostic conditions: restore with UIA
  text inspection (PID 35676), then restore with screenshot capture and switching
  to the second PaneTab (PID 44604). Both exited 0 with user settings unchanged;
  the second also showed the restored ascending file order after settling.
- The earlier lingering process was not reproduced or explained. Retain an
  intermittent unresolved shutdown risk, not a fixed defect or final G01 PASS.
  No lingering process remained to sample a native stack. Obtain that evidence
  on an actual recurrence rather than repeating identical runs or guessing a fix.
- Scoped functional observations passed; full visual acceptance remains NOT TESTED.
  Earlier failure and legacy-session/visual gaps remain intact below.

## 2026-10-20 G01 — local tab/restore behavior observed; shutdown acceptance blocked

- Current `4bdde290` product sources were built once through `fly.bat build Release`
  (exit 0); EXE SHA-256 `eb89f47db33d2d12ff6abb1e6b7eb4f47c1e79adabfae3be27e8a54f9e35456d`.
- Actual owned GUI confirmed PaneTab default Name ascending, independent ascending/
  descending modes across switches and close, opposite-pane preservation, independent
  WindowTab name/size modes, and v4 private-session restart restoring two PaneTab modes.
  The restored descending sort-menu check agreed with the real file order.
- First app exit was 0. After the restored run, the window closed but the owned process
  remained without top-level windows for over 60 seconds. A read-only Windows wait chain
  showed an ALPC wait toward `csrss.exe`, without a reported cycle. The exact cause is
  unresolved; this does not establish a product deadlock. Owned cleanup produced exit -1.
- **Final functional GUI acceptance: BLOCKED (shutdown).** Both real user-settings
  guards and synthetic file hashes were unchanged. No product code was changed.
  Dark/96-DPI/1906x1016 pixels were inspected; matched pre-implementation visual
  acceptance, Light/narrow review and legacy v1-v3 live restore remain untested.
  Ignored evidence: `logs/g01-local-20261020/result.json`, `logs/file-open/g01-current-build.log`.

## 2026-10-20 L08 — human hover confirmed; automated cursor gate unresolved

- The user directly moved the mouse over a column boundary and reported that
  the resize cursor displayed correctly. This supersedes treating earlier
  synthetic-input failures as proof that the cursor never works in the product.
- Exact binary, column/pane coverage and environment for that observation were
  not recorded. Preserve it as user-reported manual evidence, not an exact-SHA
  automated GUI or full visual PASS. Existing strict assertions remain intact.
- Stop speculative cursor product changes. Further automated failures first need
  input/event/environment classification against the working human interaction.
  The temporary local event-source diagnostic was removed from product sources.
- G01 and G02/G06 remain implemented with the previously recorded build evidence;
  their outstanding GUI acceptance is the next development completion priority.

## 2026-10-19 G02/G06 source contracts and exact Windows Release build — PASS

- Exact tested product source: `11915f42bd6d85d2001653dba0a2aa30e0141532`.
  A fresh **test-owned clean Windows clone** was checked for the exact main SHA.
  [Central Windows run #39239758606](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39239758606)
  reports `G02G06_SHORTCUT_CONTRACT_EXIT=0`, `G02G06_TABS_CONTRACT_EXIT=0`,
  `G02G06_RELEASE_BUILD_EXIT=0` and `G02G06_SOURCE_AND_RELEASE_PASS`.
  Candidate Release EXE SHA-256:
  `967db8f70dce972274786c177753de1030d10c2908fb1fe6758fcd5f0292943b`.
- The specific tested changes are F6 conditional focus feedback, dynamic
  owning-pane names for per-pane `TabViewItem`, and context-dependent
  left/right labels on folder-tab create/close buttons. No file operations,
  tab commands, visual geometry, user settings or global OS configuration were
  intentionally altered. Remote request slot restored to idle afterward.
- **Acceptance limit:** these are **executed source contracts + actual Release
  compile/link**, not live keyboard F6/Tab/Shift+Tab, UIA reading,
  screenshots or visual acceptance. G02 complete keyboard traversal and G06
  runtime UIA validation remain pending. G01 PaneTab sort GUI, L08 resize cursor
  failure also remain open; do not claim either as PASS.
- User-excluded actual 125%/150%/200% DPI, F04/F05 High Contrast/Narrator voice,
  and real USB/SMB/UNC tests remain off the task list.


## 2026-10-19 G06 continued — actual owning-pane names on each folder tab and command

- `main` [`1a024da`](https://github.com/tngkrwlsmd/flyExplorer/commit/1a024da1be6e4fb3e5866794a568f1594e9e0c59)
  assigns an explicit **left/right folder-tab** UIA name to every per-pane
  `TabViewItem` during `RefreshTabs(side)` without changing its visible header,
  selection, folder route, or WindowTab behavior.
- [`d19c359`](https://github.com/tngkrwlsmd/flyExplorer/commit/d19c359547709e830976e88da13b417b5141a698)
  sets the new-tab and close-tab accessible names dynamically from the
  **actual active pane** in `UpdateActivePaneChrome()`, invoked on Refresh
  and pane activation. It preserves original button layout and commands.
- [`e34b95b`](https://github.com/tngkrwlsmd/flyExplorer/commit/e34b95b6be8b9826b9fb1bf430199636a8846da5)
  and [`ea2d08b`](https://github.com/tngkrwlsmd/flyExplorer/commit/ea2d08bd77508ed112e51e5c758790e8aab1dfc7)
  extend the focused source contract to both item ownership and dynamic
  button labels. Re-read current GitHub sources for 14 scoped static
  assertions; **all 14 matched**. These are not executed Python unittests.
- **Acceptance boundary:** no Windows Release recompile or actual live keyboard
  traversal/UIA inspection was performed for these new edits. The currently
  connected Desktop Commander Windows host is offline. Do not mark G06 GUI
  PASS. Existing G01 GUI, L08 horizontal cursor and full G02 keyboard-route
  gates remain OPEN. Do not reactivate user-excluded G03/G04/G05.


## 2026-10-19 G02 F6 focus feedback and G06 two-level tab names — source-only scope

- `main` [`1c768b3`](https://github.com/tngkrwlsmd/flyExplorer/commit/1c768b308aa4e7427e4fa3266998bc20710b6a6e)
  changes F6 cross-pane keyboard focus feedback to report success **only if**
  `otherView.Focus(FocusState::Keyboard)` returns true. The existing shortcut,
  active-pane targeting and transfer safety are unchanged. Regression source
  contract [`05266a4`](https://github.com/tngkrwlsmd/flyExplorer/commit/05266a47b6377c977de9336dfddc722df5680f82)
  checks both branches.
- G06 [`8480403`](https://github.com/tngkrwlsmd/flyExplorer/commit/848040392852ce0ccfe518e14d338ec5d0c2f9cf)
  identifies header-folder-tab add/close buttons as actions on the **currently
  active pane** in their `AutomationProperties.Name`.
  [`c290ff6`](https://github.com/tngkrwlsmd/flyExplorer/commit/c290ff678a84af91daeca6b40d8e489061565787)
  distinguishes top-level workspace window tabs in the dynamic automation
  name; existing distinct left/right PaneTab labels remain.
  [`de2c687`](https://github.com/tngkrwlsmd/flyExplorer/commit/de2c6874e711f0ab839e57975a8a91a8535028be)
  adds a source contract for these names. No visible layout or shortcut
  behavior was intentionally changed.
- Re-read the exact current GitHub source and checked eight targeted static
  conditions: F6 success/failure, test coverage, active-pane button labels,
  left/right PaneTab labels, workspace tab labels, G06 contract presence and
  original F6 binding: **all eight matched**. This was a read-only static
  check, **not Python unittest execution, Windows build, live GUI/UIA or
  visual-pixel PASS**. The authorized desktop connection currently reports
  offline; do not classify missing runtime evidence as a product defect.
- The earlier user-requested exclusion of actual 125/150/200% DPI,
  F04/F05 High Contrast/Narrator audio and real USB/SMB/UNC testing remains
  in force. Do not reintroduce these tests as prerequisites to G02/G06.


## 2026-10-19 G01 PaneTab-local sorting — source and build accepted, GUI not accepted

- Product `main` [`5c5298a3e126`](https://github.com/tngkrwlsmd/flyExplorer/commit/5c5298a3e126542b0118c5a670ac982cd5ed1718)
  implements folder-tab-local sorting in `WindowTabState.tabSortModes` and
  `WindowWorkspaceController`: new tabs default to Name ascending, switching or
  closing a tab restores its saved mode, while left/right panes and Window Tabs
  retain independent state. The previously accepted R1 sort-menu checkmark
  presentation remains unchanged.
- Private WinUI session writes **schema v4** with each folder tab's sort mode.
  The decoder continues to read v1/v2/v3 and inherits the prior pane-wide sort
  into old folder tabs. New source tests cover the version dispatch, and the
  focused sort-menu GUI test now checks new-tab default and closing-tab restore.
- All seven prepared Git blobs were exact-byte verified in an isolated Windows
  source checkout matching original product `099cfb7125f9`. `test_session_coordinator_contract.py`
  **PASS**; GUI test Python syntax **PASS**; Release compiler/linker **PASS**
  in [#39230031402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39230031402).
  Candidate Release EXE SHA-256:
  `368cc3c2b74f17845ec06e4db3cfc31687040eef78f878c8faba6b7b32df6fa1`.
  It contains the new seven product/test blobs; the `main` commit applied those
  exact Git blobs atomically after the build.
- **NOT GUI ACCEPTED:** an additional login-session GUI execution request was
  blocked by the tool safety/approval control before execution. It was not
  bypassed or retried through another execution route. Actual per-PaneTab
  UI selection, session restart/restore, screenshots and pixel acceptance are
  therefore **NOT TESTED on this commit**. Do not mistake a compile-successful
  test file for a runtime PASS. Follow-up requires an explicitly permitted,
  provenance-matched test path, otherwise leave pending.
- Earlier L08 cursor remains unresolved. In further isolated
  [#39228853177](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39228853177),
  the instrumented handle reported `L08_LOADED` but did not report
  `L08_ENTERED`/`L08_MOVED` at the probed mouse position, and the native
  cursor was still stock arrow. This is a **scoped diagnostic observation**,
  not proof about all pointer input paths. No L08 cursor fix was committed.
- User-excluded G03 actual 125/150/200% DPI, G04 F04/F05 High Contrast/Narrator,
  and G05 real USB/SMB/UNC tests remain excluded from development and release
  prerequisites; their historical evidence is unchanged.



## 2026-10-19 L08 Details column cursor and drag — scoped Windows evidence

- Latest product `main` remained `099cfb7125f98ca57df977861dba2a8bd0c27c77`
  during this investigation. The exact-source isolated canonical Release build
  **PASS** [#39221721375](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39221721375),
  exe SHA-256 `9a9056d94c18d6f662a7b8991f2704d877ae0bee746b9ece6b4e037bbdb9eaf6`.
  The first central controller attempt [#39221444117](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39221444117)
  failed before product build on an absent `solution` registry property.
- Actual interactive desktop session 1, disposable source-owned folder: the
  checked-in focused L08 GUI raised `AssertionError` before dragging at
  `LeftNameColumnResizeThumb did not display the horizontal resize cursor`.
  The ad hoc worker incorrectly reported child exit 0 and the outer Actions run
  [#39222335628](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39222335628)
  was SUCCESS. **This is NOT GUI PASS:** Python traceback and missing required
  test markers override the faulty worker exit oracle.
- Cursor-only diagnostic [#39223454976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223454976)
  confirmed the native cursor handle `65539` equaled the active Windows stock
  **arrow** and differed from stock horizontal resize `65553` while hovering
  the named L08 handle. An intentionally bypassed cursor assertion
  [#39223067075](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223067075)
  independently observed actual mouse press, three progressing column-boundary
  moves and `RESIZE_MOVE` markers. These are **diagnostics**, not acceptance.
- One **uncommitted, test-owned** candidate changed only
  `DetailColumnHandle.cpp` to update the native cursor on pointer events.
  The first build hit a missing `Microsoft.UI.Xaml.Input.h` projection,
  then after that header was added the isolated Release build **PASS**
  [#39224349062](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224349062);
  candidate EXE SHA-256 `df5e964b8e60a064843f9251642711c5c067ca232e5c688b406ec7bcb52b076c`.
  Its strict focused GUI [#39224659050](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224659050)
  again **FAILED** at the actual horizontal cursor assertion. The corrected
  worker rejected the missing required markers instead of claiming success.
  The candidate **was not pushed to flyExplorer**.
- **L08 status: PARTIAL FUNCTIONAL DIAGNOSTIC / CURSOR NOT ACCEPTED /
  INDEPENDENT PIXEL REVIEW NOT PERFORMED.** Before another attempt identify
  why the WinUI handle's pointer cursor remains the arrow; do not blindly
  repeat either build or GUI. Other pane, narrow layout and visual claims
  are outside these scoped diagnostics. The actual 125/150/200% DPI,
  F04/F05 High Contrast/Narrator and real USB/SMB/UNC tracks remain
  **USER-EXCLUDED** and must not be revived as L08 prerequisites.



## 2026-10-19 L07 bounded filename cells — local scoped acceptance

- Details filename presentation now uses an Auto+Star grid with finite text
  width, ellipsis and a full-name tooltip; metadata and selection identity kept.
- Canonical local Release/source 29 PASS. Actual matched Dark BEFORE/AFTER
  reviewed at 1906x1016, both panes; UIA width 120/320/default 168 reflow checked.
  Light AFTER reviewed with isolated preferences. Both app exits 0, files unchanged.
- See UI_UX_AUDIT.md for exact hashes and limits. Tooltip hover, physical resize
  cursor/drag, narrow-window and drive/badge pixels remain unverified. L08 is next.

## 2026-10-19 L06 right-click selection — local scoped acceptance

- Right-clicking an already-selected member now preserves the selection set;
  an unselected row still replaces it. Existing isolated-helper multi-item
  execution restrictions remain intact.
- Local Release/source 3 PASS, actual four-item selection/right-click/cancel
  retention and unselected-row replacement observed, file hashes unchanged,
  app exit 0. Dark matched BEFORE/AFTER review recorded in UI_UX_AUDIT.md.
- Added a real two-file right-click regression to the existing owned GUI test;
  syntax checked, script not run locally (pywinauto absent). No new central/full
  GUI acceptance claim. L07 long-name rendering is next.

## 2026-10-19 L05 document activation — local scoped acceptance

- Regular filesystem documents now open through the asynchronous Windows
  default-app broker from double-click/Enter; folder navigation is preserved.
  FileOpenController owns duplicate gating, timeout, stale-context checks and
  close cancellation, separate from MainWindow presentation.
- Canonical local Release exit 0, source contracts 32 PASS; actual alpha.txt
  double-click, Korean/space filename Enter, rejected synthetic executable,
  folder/back regression and owned app exit 0 observed. Scoped Dark/96-DPI
  BEFORE/AFTER pixels reviewed at 1906x1016. See UI_UX_AUDIT.md for exact hashes.
- No full GUI/Debug/central exact-SHA claim. Delayed race/timeout and no-association
  UI are untested; virtual Shell items and Launcher-restricted executable/script
  activation remain unsupported. L06 multi-selection is the next implementation.

## 2026-10-19 basic file-use audit — confirmed gaps, no product changes

- Actual local use on product-unchanged `e01f552f` reproduced regular txt
  double-click not opening an associated app, and four selected items shrinking
  to one after right-clicking a selected member. Long Korean filename cells
  visually run into the type column. These are not successful functional gates.
- [UI_UX_AUDIT.md](UI_UX_AUDIT.md) L05-L10 records source boundaries,
  reproduction, completion criteria and separate visual review. F2 opens a
  remote toolbar editor with the extension selected; Escape cancellation worked.
  Actual resize-hover cursor behavior remains unverified, not a claimed PASS/fail.
- No product edits, rebuild or full E2E; only one synthetic long-name fixture
  was added under ignored logs. Existing user changes and excluded tracks kept.

## 2026-10-19 local Explorer follow-up — observation only

- Reused the prior successful local Release on product-unchanged `cdbe716c`;
  no product edit or rebuild. Basic owned-folder navigation/back button,
  Unicode names, Ctrl+L and subsequent Tab were observed in the actual app.
- The prior approval-service block cleared. Actual Dark app/Explorer screens
  were reviewed at different window sizes; this is neither matched-geometry
  pixel acceptance nor full functional/keyboard regression acceptance.
- [UI_UX_AUDIT.md](UI_UX_AUDIT.md) records L01 Alt navigation gap, L02 deliberate
  selection-command availability policy, L03 verbose type-label clipping and
  L04 focus/geometry tooling limits, with reproduction and completion criteria.
  Existing R1 acceptance and user-excluded test tracks remain unchanged.

## 2026-10-19 R1 active sort menu — scoped acceptance

- **Implemented:** eight native ToggleMenuFlyoutItems project the existing sort index;
  `SetSortIndex` synchronizes activation/restore, menu and legacy ComboBox paths.
  The initialization callback guard is preserved. No sorting engine, persistence,
  MainWindow state machine or user settings were changed.
- **Exact candidate:** reviewed `main` `3dd17f614caaf7a41b5d90a4f345e5a1e1ff61a9`
  plus the two FileToolbar source changes. Product source hashes and the final
  fixture hash are recorded in [UI_UX_AUDIT.md](UI_UX_AUDIT.md). Interactive
  limited-user canonical Release build PASS; EXE SHA-256
  `5a90c5deaa76f4e93f6a6a870a1defc20beb11456d2bcdf75537b76fc2cab751`.
  Structure 4/4 and core contracts 60/60 passed. Later harness-only repairs
  reused these exact product bytes.
- **Functional GUI PASS:** [39188197976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39188197976)
  verified eight real-key sort choices/one-hot UIA Toggle states, actual name order,
  independent panes/WindowTabs and menu/list agreement across folder-tab changes.
  Light/Dark app exits 0; real app/legacy settings preserved; owned task/process
  counts 0. This is a bounded pre-main user-session acceptance, not a new registered
  exact-main full GUI status or Debug/full acceptance.
- **VISUAL ACCEPTANCE: PASS (scoped 96 DPI):** four matched BEFORE/AFTER menu pairs,
  Light/Dark at 960/800x634, were inspected. The selected check and keyboard focus
  are distinct; the native check gutter is intended; no material clipping/overlap
  was found. Actual alternate DPI, HC and Narrator speech remain separate gates.
- **Existing ownership gap, not an R1 regression:** [39187495613](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39187495613)
  reproduced pane-shared sort across folder tabs in both the old accepted EXE and
  R1 EXE. ARCHITECTURE's PaneTab-level sort description is not fully implemented.
  Independent folder-tab sort/session semantics require a separate logical unit;
  R1 preserves the existing behavior and reports it in the audit.
- Prior preparation/fixture failures and the cancelled obsolete build wait remain
  failures/cancellations, not retroactive PASS. Their causes and prevention are in
  ERROR_HISTORY and the audit. No screenshots, binaries or raw machine logs are committed.

## 2026-10-18 requested work: F05 grouping keyboard acceptance and retained test cleanup

- **F05 real keyboard path PASS:** [PR #67](https://github.com/tngkrwlsmd/flyExplorer/pull/67) merged at `4b1616b391111989b66acaddc23062cafc8eca78`, test-only head `5f6b12b56adcc4de979c63e8ad3a9c48a9c65bda`. No app C++/XAML changes or product rebuild. Reused exact previously accepted Release binary SHA256 `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17` under real interactive Windows session 1.
- **Two successful GUI runs:** [#39105142373](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105142373) confirmed View Space / Down / Enter keyboard navigation for Name/Size/Month/Type, Markdown disclosure Space collapse and Enter expand, and keyboard Type grouping off. [#39105289485](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105289485) confirmed those plus keyboard new tab, original tab collapsed state restore, new tab reopen, keyboard tab close while preserving grouping, and final mode-off. Exit 0, exact EXE checksum retained, detached test checkout restored. The existing disposable GUI fixture asserts user profile hash preservation and test-owned cleanup on successful exit.
- **Input test provenance:** UIA `set_focus()` established the known owned control before key actions; the actual menu traversal, group toggling and tab controls were activated by physically simulated Space / Down / Enter key events (no mouse click in new F05 branch). This accepts the F05 focused keyboard control flow, **not** global no-assistance Tab traversal from app launch, OS scaling, High Contrast, or spoken Narrator results.
- **Earlier harness failure preserved:** [#39104964400](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39104964400) FAILED due to invalid `UIAElementInfo.has_keyboard_focus`; [read-only #39105056315](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105056315) established the exact traceback. Replaced with the already-supported `UIAWrapper.has_keyboard_focus()`; subsequent success does not relabel the failed run.
- **Owned temp fixture cleanup DONE:** A separate prior M26 accessibility-test-owned folder was inventoried recursively in [#39104555692](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39104555692): eight directories, one 10-byte file with verified SHA-256 `179dc8402c343ade1dfe93ebb647f01c2f09992c14eff72def4d11d41a34eb40`; no reparse points. The first controlled cleanup [#39104641466](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39104641466) correctly refused a PowerShell 5.1 literal Korean path encoding mismatch, removing nothing. A Unicode-codepoint-based expected-name check in [#39104703874](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39104703874) **SUCCESS** deleted exactly that synthetic owned directory after full contents/hash/process/task checks; verified absence, preserving all siblings, personal files and original user preferences. This cleanup is distinct from the current F05 test fixture.
- **User-requested exclusions:** actual 125%/150%/200% DPI, OS High Contrast and Narrator speech testing were **not executed** in this work. Previous unverified classification remains; no claim of acceptance. Other unfinished feature/packaging gates are separate.



## 2026-10-18 supplementary M26 owned UIA/keyboard responsiveness — scoped PASS

- **Successful real Windows interactive session:** [personal-control-plane Direct Remote Shell #39103545858](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39103545858) **SUCCESS**. It launched the existing `tests/winui/test_owned_accessibility_layout_gui.py Release` in the logged-in user session (session 1), with exact source `0d10b1b600c854a2cfbb3b425bf7b2d616e9af77` and reused product binary SHA-256 `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17`. The accepted product source/binary and existing user files were not changed.
- **Exact observed PASS markers:** 16 named controls and responsive geometry at 960x634, 1100x680, and 1240x710; real Tab-key focus sequence; actual foreground window 96 DPI and High Contrast OFF; all six legacy preferences byte-identical; Python and bounded Windows worker exit 0. The owned successful disposable GUI fixture cleaned itself.
- **Harness-only change:** central control script `scripts/tasks/Read-FlyExplorerOwnedAccessibilityGui.ps1` now launches the test with separately redirected stdout/stderr and writes an atomic, size-bounded JSON verdict after process exit. The [read-only preserved fixture inspection #39103271352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39103271352) confirmed one earlier synthetic fixture with test-created environment directories and file; the prior missing traceback cannot be reconstructed from those folders alone. Do not claim the first failed assertion was proven; the new unchanged-product test passed and does not reproduce a product defect.
- **Scope limitation:** this supplementary M26 smoke does **not** newly certify F04/F05-specific full-screen High Contrast pixels, actual OS 125/150/200% scaling, spoken Narrator phrases, all F05 keyboard traversal, or IME scenarios. Those remain separately OPEN. The previously accepted F04 actual 96-DPI Light/Dark pixels and physical mouse/keyboard tests retain their exact recorded acceptance. One older failing-run synthetic fixture remains retained, without deleting it as part of this acceptance.
- The preceding `supplementary 96-DPI accessibility GUI attempt — not accepted` section is now historical diagnosis: #39102240993, #39102419752 and #39102607819 remain authentic failed harness/evidence runs and are not retroactively relabeled PASS.



## 2026-10-18 interactive Windows monitor DPI (read-only) — observed 100%

- Central Windows [read-only interactive probe #39102028142](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102028142) **SUCCESS**. The authorized controller created a bounded one-time task in the already logged-in user session, with process-local per-monitor DPI awareness (verified). Its actual active screen inventory: **one primary screen 1280x768 pixels, effective 96x96 DPI = 100% scale**, session 1. `GetDpiForMonitor` returned 0 (success). No OS display scaling, contrast, Narrator or audio settings changed; the one-time task and its owned JSON result were removed.
- Earlier [SYSTEM controller inventory #39101601402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39101601402) reported two video-controller modes (1024x768 and 2560x1440), two OK monitor devices, one interactive Explorer session, no active Narrator process and zero OK sound devices in the service inventory. This does **not** conflict with the actual single active 1280x768 user-session screen: controller hardware/mode listings do not prove an active DPI-scaled desktop or absence of a user-session audio playback endpoint.
- **DPI gate:** there is no observed active 125%, 150% or 200% Windows desktop in this VM session. Those real-scale F04/F05 visual/keyboard checks remain **NOT TESTED**; no synthetic scaling, hidden registry changes, or inferred scaling can substitute. Use the existing `tests/winui/manual_accessibility_matrix.py` in a separately configured real interactive scaled Windows test environment, with a known baseline, explicit safe restore and human verification.

## 2026-10-18 supplementary 96-DPI accessibility GUI attempt — not accepted

- The exact accepted PR #66 product source `0d10b1b600c854a2cfbb3b425bf7b2d616e9af77` and Release EXE SHA-256 `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17` were the intended inputs to the existing owned responsiveness/UIA keyboard script `tests/winui/test_owned_accessibility_layout_gui.py` in the logged-in user session. This optional M26-wide audit is separate from the previously accepted F04 functional and 96-DPI Light/Dark pixel gates; no new product build was requested.
- [Action #39102240993](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102240993) **FAIL** at the auxiliary result-envelope check; [#39102419752](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102419752) **FAIL** with oversized result file (236053 bytes against the controller's 12KB allowlist). The worker/result serialization was then changed to atomic and bounded markers. [#39102607819](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102607819) **FAIL** because the limited interactive task exited with code 1 without producing its final result. These failures do not prove a product accessibility defect or a GUI PASS; source of the user-task failure is still undiagnosed. **M26 supplementary GUI accessibility acceptance: NOT VERIFIED.** Do not retry unchanged until the original failing GUI assertion or worker exit path is identified from preserved owned evidence.
- Read-only [ownership inventory #39102922339](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102922339) **SUCCESS**: zero registered temporary GUI tasks, zero running test-owned flyExplorer processes, zero task-owned output JSON files, and **one retained synthetic `accessibility-owned-*` fixture directory** under the prior ignored test checkout `logs/m24/`. The fixture is retained for root-cause diagnosis, not automatically deleted; no personal profile folders or Windows global state were reset. The central request slot was returned to idle.
- **Still OPEN:** actual 125/150/200% DPI, actual F04/F05 active High Contrast compositor, recorded spoken Narrator output, and this additional M26-wide user-session audit. Prior accepted F04 mouse/keyboard and actual 96-DPI Light/Dark evidence remain accepted only for their exact tested scope.



## 2026-10-18 F04/F05 accessibility and actual DPI readiness — read-only inventory

- **Executed:** [Windows control-plane Direct Remote Shell #39101601402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39101601402) **SUCCESS**, from the tracked read-only `scripts/tasks/Get-FlyExplorerA11yReadiness.ps1`. The task ran as the authorized controller in Windows Session 0; it did not launch the product or change Windows/global user settings.
- **Observed only:** one Explorer interactive session; controller-reported video modes 1024x768 and 2560x1440; two monitor devices reported OK; zero active Narrator processes and zero sound devices reported OK to the service. The video mode list does not prove which resolution/DPI belongs to the active app window; the audio inventory does not prove absence of a user-session playback endpoint.
- **Unverified and still OPEN:** actual WinUI `GetDpiForWindow` at OS 125%/150%/200% scale; F04/F05 composited high-contrast rendering; spoken Narrator phrases and reading/focus order. Do not infer PASS from UIA AutomationProperties, physical keyboard acceptance, DWM 96-DPI screenshots, or the SYSTEM/Session 0 hardware inventory. The existing `tests/winui/manual_accessibility_matrix.py` needs a dedicated genuine scaled interactive Windows environment and human Narrator/IME confirmation. Do not activate global scale/contrast/Narrator in the shared VM without an explicit protected baseline/restore and isolated acceptance scope.
- **Completed earlier:** the source-only and 96-DPI Light/Dark F04 checks below remain accepted; F05 buttons already publish mode/action names and its scoped physical keyboard disclosure passed on its recorded revision. No new F04/F05 product build or GUI/UIA test was executed in this environment-inventory step.



## 2026-10-18 F04 narrow TreeView root label — accepted on main

- **Integrated:** [PR #66](https://github.com/tngkrwlsmd/flyExplorer/pull/66), merge commit `9dbdd5c3cc298294c6e7c494b01dd34ae7ef8fbf`; exact tested branch source `0d10b1b600c854a2cfbb3b425bf7b2d616e9af77`. The prior main `fa2a1d81a3f4f81b6c0cb82de5f4fff26d333602` passed [central full GUI #39093066725](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39093066725) and retained two hash-matched actual Light/Dark PNGs. Independent inspection of those baseline pixels showed the absolute tree-root path clipped by the narrow sidebar; it was not visual acceptance of that text.
- **Fix:** root TreeView text shows the current folder's final path component (drive-root fallback retains its path). The exact normalized full path remains in `mTreeNodes` for navigation, stale-route identity, and correct pane ownership. The owned GUI contract now requires one refreshed root TreeItem after in-tab navigation rather than incorrectly requiring the former on-screen full path.
- **Scoped Windows test:** exact `0d10b1b6` in an isolated full-history Windows user-session checkout: structure **4/4**, product **238/238**, harness **21/21**, infra **30/30** source checks PASS. Canonical Release build PASS, product EXE SHA-256 `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17`, sibling Shell helper present. The post-build correction changed only the focused Python GUI assertion; a checksum check proved that same product binary was used.
- **Real GUI:** focused F04 mouse click, sidebar scroll, keyboard HOME/DOWN, tab/pane route and refreshed `Left` -> `Nested` root PASS. The full Release GUI regression also PASS (`gui-window-tabs`, `gui-shortcuts`, `gui-filter-preset`, `gui-folder-tree`, `gui-all`); full GUI stage finished exit 0 in 129.5s, process exited 0, protected six preferences kept identical hashes, owned synthetic fixtures removed, test checkout clean.
- **Actual pixels / VISUAL ACCEPTANCE: PASS (96 DPI only):** directly reviewed matched Light/Dark actual WinUI screenshots, 960x519, synthetic `Left/Nested`, same owned app geometry. Tree labels, chevrons, two file panes, alignment, focus/selection and theme contrast were readable without material clipping/overlap. Final full-GUI capture SHA-256: Light `5f235a81cce455c4766b88a9ddaa47abc3ce0a116ac89c4d5fa34c610c7cbb8c`; Dark `8d17a03b404e9902dcf8cfcfcf8d9e1475274d6099eebe25dfd421d1774344b2`. The two files were rehashed against the run's private `f04-pair-manifest.json` (DPI 96, 960x519). These test-owned local images were not published in source control.
- **Evidence limits:** this is pre-main exact-source ordinary-Windows-user acceptance plus verified merge ancestry, not a new central CI claim for the merge SHA. Actual Windows 125%/150%/200% display scale, spoken Narrator output, F04 active High Contrast, broader device/provider cases, signed installer, and public distribution remain separate OPEN gates. The earlier dated F04 'pending' entries below are historical checkpoints, not the current result.



## 2026-10-18 F04 mouse+keyboard and full GUI accepted; pixel capture pending

- Exact `1afbaed256e04c073d53250a326ce34dd22ad6e0` [central Windows GUI #39090939174](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39090939174) **SUCCESS**: source, Release, F04 physical mouse and keyboard, previous M20 actual-theme pixel gate, and full regression all passed. Do not re-debug or rerun this accepted functional revision.
- New isolated test-only F04 candidate captures both Light and Dark expanded local-tree images under the SAME owned WinUI window/fixture, verifies settled composited brightness, and writes a bounded SHA256/DPI/window/fixture manifest. Windows control-plane now permits retaining only those two digest-matched synthetic captures after the CI workspace is retired; PowerShell parse-only probe #39092630648 PASS. Candidate source/GUI is NOT YET TESTED. The screenshots still require direct manual comparison of clipping, icons, focus and contrast before visual acceptance is marked PASS.
- Actual 125%, 150%, 200% Windows DPI, Narrator speech, high contrast, keyboard accessibility beyond focused F04 fixture and real Korean IME remain separately evidence-scoped; no unobserved gate is complete.


## 2026-10-18 F04 keyboard passed; M20 theme pixel probe follow-up

- Central GUI [#39090079558](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39090079558) on exact `eb80f4c7458dd8401aa7d53cdf22bc4637b67867`: runner/policy/source/Release PASS; focused **F04 mouse + keyboard** GUI PASS; established window-tabs, shortcuts, filter PASS. Full general GUI FAIL in the pre-existing M20 theme pixel probe, not F04: dark values [179.89, 32, 32], light [126.44, 243, 243]. The left-file-list sample at width 0.38 was the only inverted contrast. Archive confirmed normal owned app exit and test-fixture removal.
- Candidate test-only correction moves that one dynamic-left-content brightness sample to width 0.86 within the already successful stable shell area; preserves all three sample locations, real rendered screenshots, compositor settling, and strict `light-dark > 20` at **every** sample. Source and successor GUI acceptance are pending.
- Independent F04 Light/Dark visual inspection, exact theme/DPI/window metadata, actual 125/150/200% display scaling, Narrator and high contrast remain OPEN; success of mouse/keyboard acceptance does not close pixel acceptance.


## 2026-10-18 F04-B physical mouse: accepted; keyboard candidate

- Exact `1909aec73c890d5473f70707a37560a70158d059` central [Windows GUI #39088980414](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39088980414) **SUCCESS**. Policy, source, Release, focused F04 real-mouse scroll/selection/navigation, and the existing full GUI regression all passed. Reuse this evidence; do not rerun the same scope for an unchanged revision.
- The next test-only F04 change adds separate real keyboard HOME/DOWN route navigation after returning to the disposable owned parent folder. Its source and GUI acceptance are PENDING and do not invalidate the previously accepted mouse result for the old SHA.
- Actual F04 Light/Dark composited before/after pixel comparison, 125/150/200% DPI, High Contrast and spoken Narrator remain OPEN until independently observed. Do not treat the GUI PASS as visual acceptance.


## 2026-10-18 F04-B physical mouse acceptance: test item was off-screen

- Central [GUI #39087700903](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39087700903) **FAIL** at the F04 GUI gate (first relevant error: `F04 TreeItem has no UIA clickable point`). Runner, policy, source, x64 Release and window-tabs/shortcuts/filter GUI were all PASS; artifact upload quota error was additional, not the root cause.
- Actual **test-owned 960×519 Windows app screenshot** preserved in `ci-evidence/547d72815d244a25a7e590d6d4a41dfe/application.png` was independently inspected: the expanded sidebar TreeView root was at the bottom edge and `Nested` was off-screen below it. Prior UIA selection could navigate while physical center-click could not reach the invisible child. This proves a missing sidebar scroll in the F04 harness, not necessarily a product selection bug.
- New focused test requests UIA ScrollItem visibility, physically scrolls the **owned** sidebar if necessary, requires the `Nested` label to be inside the visible window and TreeItem bounds, and only then sends real mouse input. A scrolled-expanded screenshot is added. UIA `Select()` remains diagnostic and cannot pass mouse acceptance.
- Exact successor SHA source/GUI and independent Light/Dark pixel review, keyboard input and OS DPI are still **OPEN**. Do not repeat accepted older Release/GUI areas to debug the scrolling harness except where the central fixed full-GUI workflow requires them.


## 2026-10-17 F04-B right-pane test isolation after second GUI failure

- [Central GUI #39033656455](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39033656455) policy/source/Release PASS; functional GUI FAIL before F04 tree interaction at the common Left startup address gate. Retained UIA evidence showed an empty Left list/address and a populated Right list for the owned fixture; normal app exit and owned fixture cleanup confirmed.
- The focused F04 GUI case now explicitly selects the already ready Right pane and validates the owned address before TreeView actions. The other GUI profiles preserve their Left startup assertion; full GUI regression is still required. This is test isolation, **not** a fix or acceptance of intermittent Left cold-start behavior.
- Revised focused F04 GUI, actual keyboard operation, independently inspected before/after theme pixels, and cold-start reliability remain OPEN.


## 2026-10-17 F04-B failed Release and corrective patch

- [Central GUI #39031617203](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39031617203) failed at Release compile C2027/C3861: NavigationSidebar.xaml.cpp lacked the WinRT AutomationProperties include. Source checks passed, but no GUI ran.
- Corrected the include, path ownership check on in-place folder navigation, and canceled-worker retry. Revised Windows build, functional GUI and final pixel acceptance remain unverified pending the successor validation.


## 2026-10-17 F04-A local-tree foundation (no user-visible tree yet)

- Introduced bounded, OS-I/O-free F04 lexical local-drive-path and
  stale expansion-result identity guards in app/winui/folder_tree_path.h;
  corresponding native fixture and registered source contract added.
- This does NOT assert that an actual fixed-drive/reparse inspection occurred,
  nor that NavigationSidebar now exposes a TreeView. F04-B off-UI-thread
  isolated enumeration, pane-targeted interaction, Windows GUI and visual
  acceptance remain OPEN. See docs/development/F04_NAVIGATION_TREE.md.
- Initial native C++17 and Python source-contract execution passed locally.
  Exact-code central Windows CI [#39030832947](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39030832947)
  accepted source SHA `7b97f1e060b7d204bcc71877d91bd43fbc161a42`:
  runner-health, policy and source all PASS. F04 native MSVC compile, Windows
  Release/GUI and visual acceptance are NOT TESTED.


## 2026-10-17 current F05 acceptance and accessibility resume checkpoint

- Live `main` at this checkpoint: `fce74c784c36c61d596c04c1d26fb1600e3c7fb7`. The previously open
  app-side Light/Type empty-right-pane fixture was fixed in
  `32cb338cb6c3d3a38101d63b5190cfdd508a5f9d` and its new Release
  runtime passed [GUI #39022716919](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022716919)
  plus [independent visual review #39022817351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022817351).
  Final docs-integrated `main` source checks
  [#39023239483](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39023239483)
  **SUCCESS**. Do not repeat those completed gates for unchanged code.
- Read-only [Windows accessibility inventory #39029834464](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39029834464)
  **SUCCESS**: one interactive Explorer desktop, preexisting owned Release
  executable SHA-256 `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`,
  `SPI_GETHIGHCONTRAST` currently **disabled**; no OS/theme/user state
  changed. This legacy runtime hash is not the newer F05 candidate Release
  hash `29cdf8e8d3f052fb273461eaf1ba14cd62439bc9e2674f7ae791871a845cd9de`.
- **Still OPEN:** actual OS scaling at 125/150/200%, F05 active High
  Contrast composited GUI pixels, and actual spoken Narrator audio.
  The read-only contrast result does not constitute High Contrast GUI
  acceptance. Any active contrast test must have a protected original-state
  restore/cleanup path and exact candidate binary provenance. Narrator
  unattended hotkey probing remains disallowed by the current guide.

## 2026-10-17 F05 app-side Type start after both panes are ready — accepted

- **Historical distinction:** the real View → Type user flow had already
  **PASS** at [#39017082938](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39017082938)
  with independent [96-DPI pixels #39017176600](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39017176600).
  This follow-up fixes only the opt-in automatic screenshot startup timer,
  not ordinary View-menu input or group selection.
- **Candidate C++ and contract:** `32cb338cb6c3d3a38101d63b5190cfdd508a5f9d`
  changes `MainWindow::InitializeOwnedF05VisualCaptureTest` to wait for
  the exact test-owned **right** pane route, six resident children,
  non-truncated complete enumeration, current file-list metadata and a
  nonempty `RightFiles` projection **in addition to the prior left-pane
  checks**, before triggering the app-side Type grouping. Focused source
  contract strengthened accordingly.
- **First branch build #39018110254 FAILED**, without reaching a product
  compile verdict: its outer worker timed out before `result.json`.
  The one-off harness applied recursive `icacls /inheritance:r /T`
  to a test-owned folder, removing inherited access from source files,
  the worker script, and its JSON request. Read-only
  [#39021592902](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021592902)
  showed the root ACL retained SYSTEM/Admin/user access but `.owner`
  had no access rules. Narrow scoped restoration
  [#39021754922](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021754922),
  [#39021887711](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021887711),
  and [#39022006596](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022006596)
  restored only the isolated files/subtree, verified the exact owner and
  candidate SHA, and preserved the restrictive test-root ACL.
- **After recovery:** [branch source #39022160319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022160319)
  **SUCCESS** with runner-health, policy and source PASS.
  [Branch Release #39022312037](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022312037)
  **SUCCESS** with 205,432ms Release build, exit 0, full sibling runtime
  and `flyExplorer.exe` SHA-256
  `29cdf8e8d3f052fb273461eaf1ba14cd62439bc9e2674f7ae791871a845cd9de`.
  No previous Release binary was misattributed to this change.
- **Focused new-runtime GUI:** [#39022716919](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022716919)
  **SUCCESS** for the app-side Light/Type test-owned fixture. XAML
  944×510, window 96 DPI, actual owned-foreground screen 960×519
  PNG (45,022 bytes); Type group headings and the six right-pane
  file rows appeared, original six user preference hashes identical,
  GUI worker `status=PASS`/`stage=complete`, no lingering test task.
  Independent exact-PNG [#39022817351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022817351)
  **SUCCESS** verified SHA-256
  `8ae12c6e8dc9f96593f78730f7295daa81b6a360e03238b7457f88dcced4fb4b`.
  Direct visual review: both lists visible, readable headings/icons,
  no material overlap or unexpected clipping. Column descriptions may
  be ellipsized in the tested narrow window. **Light/Type 96-DPI
  auto-fixture visual acceptance: PASS for the candidate source/binary.**
- **Evidence boundaries:** all historical failed tests remain recorded
  as failures. Branch acceptance is exact to `32cb338c`, and any
  later documentation-only descendant must retain this provenance.
  Actual Windows 125/150/200% DPI, active High Contrast, Narrator spoken
  output, and broader app startup interleavings remain **NOT VERIFIED**.

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
- **Historical OPEN at this earlier checkpoint — app-side F05 visual fixture startup:** the prior
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
  Light/Type initial-right-pane scenario was still open at that checkpoint; the newer accepted candidate is documented above.
  A narrow tab-header caption and active-pane visual state comparison
  may also merit a later independent check; it was not accepted here.

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

## 2026-10-17 F05 physical keyboard disclosure — GUI PASS (latest evidence)

- **Exact current test-only source SHA:** `83152847b753edfb3ebffcb0b6c95db96a0d5489` (no changes to
  product C++/XAML from the accepted Release source
  `d2ed08d6cfe5f2f6235abe221657d19038e5a1f8`).
- **Windows owned GUI:** the user-session test in
  [#38989720309](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38989720309)
  created a one-off exact-source fixture, reused the existing full
  Release runtime, selected the real View → Type grouping and sent
  physical Space to collapse the .md group and Enter to expand it.
  The original user configuration hashes remained identical.
- **Result provenance:** the outer Remote Shell Action **FAILED** due to a
  PowerShell evidence-aggregation expression (`-and` was applied to a
  command parameter), *after the interactive GUI worker finished*.
  A separate **read-only** inspection
  [#38989815625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38989815625)
  **SUCCESS** confirmed the persisted `result.json` recorded
  `status=PASS`, `stage=complete`, the exact SHA and all four markers:
  `F05_KEYBOARD_SPACE_COLLAPSE=PASS`,
  `F05_KEYBOARD_ENTER_EXPAND=PASS`,
  `F05_KEYBOARD_DISCLOSURE_GUI_PASS=True`, and
  `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`.
  It also confirmed zero source changes, no remaining test scheduled
  task and the original Release executable SHA-256 unchanged at
  `7f1f1636d3078e5df95fe40f5519a653ae1235373b6a8f280e7f88d4c435428f`.
- **Accepted scope:** actual user-session keyboard disclosure interaction
  for one owned Type/.md fixture. This does **not** turn the failed outer
  Actions run into a successful workflow, prove an entirely keyboard-only
  app workflow, or certify compositor pixels, native 125/150/200% Windows
  DPI scaling, active High Contrast or Narrator audio. Historical
  source-only `NOT TESTED` entries below describe the earlier checkpoint,
  and are superseded only for this specific keyboard disclosure gate.


## 2026-10-17 F05 keyboard-only disclosure harness — source PASS, GUI NOT TESTED

- **Test-only main SHA:** `22ca4ed1f3fe155a97022f0fa474538a432fdce3`.
  Opt-in `FLY_F05_KEYBOARD_DISCLOSURE_ONLY=YES` requires
  `FLY_F05_MODES_ONLY=YES` and forbids concurrent visual-capture mode.
  The owned GUI probe focuses a real .md grouping disclosure, sends
  physical Space to collapse and Enter to expand, checks the actual file
  row each time, and rejects keystrokes outside the test-owned foreground
  flyExplorer process. The normal GUI and XAML screenshot paths are unchanged.
- [Central source #38983687975](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38983687975)
  **SUCCESS** on the exact test commit: policy PASS, structure 4/4,
  product source 230/230, harness 20/20, infrastructure 30/30.
- The preceding [SYSTEM Remote Shell #38983541457](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38983541457)
  **FAILED BEFORE TEST EXECUTION** because Python was not on the SYSTEM
  runner's PATH. The subsequent central interactive-user source scope
  corrected that execution-context assumption; this was not a product failure.
  The Remote Shell request slot was restored to idle.
- **F05 keyboard-only physical disclosure: NOT TESTED / NOT ACCEPTED.**
  Source guards and Python harness tests are not real user-input evidence.
  Actual Windows/DWM final-composited pixels, 125/150/200% OS scaling,
  active High Contrast and spoken Narrator remain distinct open gates.


## Product source of truth

main is the canonical C++/WinRT WinUI 3 product. Product code lives in
app/winui, UI-independent native code in src/base, tests in tests/winui, and
bounded orchestration in tools/winui/run_checks.py. The former MFC application
is retired from the working tree and is recoverable from Git revision cbffb48.

## 2026-10-16 F05 Windows display read-only capability check

- [Windows #38901048352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38901048352) SUCCESS: primary monitor **1024×768**; one Explorer user session found. No screen resolution or session setting changed.
- [Windows #38901222167](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38901222167) SUCCESS: current control-user registry query returned no explicit `LogPixels` or `Win8DpiScaling`; stored HighContrast `Flags=126`. These registry values are **not** proof of effective DPI or active high-contrast state, especially for the separate interactive user session.
- **Still NOT VERIFIED:** effective per-window 125/150/200% DPI, actual DWM compositor pixels, active High Contrast and Narrator speech. Both inspections were read-only, and the Remote Shell request was restored to idle.

## 2026-10-16 F05 grouped XAML: Release and 8/8 screenshot checks PASS

- Exact Release source `d2ed08d6`: central CI [#38891026338](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38891026338) SUCCESS.
- Test-only SHA `d51c2af0`: four grouping views per Light/Dark theme verified using the same Release binary, owned UIA headings and alpha-preserving XAML pixels. Evidence: [Light Name #38895272394](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38895272394), [Light Size #38895710455](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38895710455), [mixed views #38896686119](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38896686119), [Dark views #38896939618](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38896939618).
- [Image review #38897312601](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38897312601) confirmed eight RGBA hashes and reviewed diagnostic-background views. Long type labels may ellipsize and Dark group bands are less prominent.
- Still **NOT VERIFIED**: actual DWM-composited pixels, real 125/150/200% DPI, High Contrast, Narrator and Korean IME in this scope. Programmatic fixture presentation is distinct from physical View-menu interaction. See [F05_GROUP_BY.md](F05_GROUP_BY.md).

## 2026-10-16 F05 Light/Dark XAML RGBA baseline capture — PASS

- **Latest accepted test-only main SHA:** `26dce015acb59da47d6fe8ee5cb46c55c6a63e14`.
  [Windows Light/Dark baseline run #38868358300](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38868358300)
  **SUCCESS** at prior source `3976779e`: separate owned preferences,
  944×510 / 96 DPI XAML images in both themes, 19/19 focused contracts
  PASS, owned process exit 0, six legacy preference SHA-256 checks
  unchanged, all disposable filesystem fixtures removed.
- Raw XAML images were about 92% transparent in sampled pixels; the
  former BI_RGB-to-RGB conversion wrongly rendered transparent areas
  black. `40a13f78` switched to explicit top-down BGRA→RGBA decoding,
  preserving original alpha and writing distinct diagnostic background
  composites. [RGBA acceptance run #38869630768](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38869630768)
  **SUCCESS** at `26dce015`: two preserved-alpha original PNGs, 19/19
  F05 contracts PASS per theme, application exit 0 and unchanged
  original user profile.
- **Accepted gate:** baseline-only XAML foreground RGBA capture for
  Light and Dark. **NOT ACCEPTED:** actual Windows/DWM final-composited
  pixel comparison, visual review of reconstructed diagnostic images
  as real output, and Light/Dark *grouped* screens. Physical group
  input was guarded when the interactive app could not become
  foreground. OS 125/150/200% DPI, active High Contrast, Narrator
  speech remain separate open gates. See
  [F05_GROUP_BY.md](F05_GROUP_BY.md).

## 2026-10-16 F05 captured pixels and Light fixture correction

- **Current source/test head as of this entry:** `3358d04e` (docs).
  Policy/source CI [#38854939427](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38854939427)
  succeeded at `91179a0e` before the latest test-only changes.
- [XAML capture GUI-only #38866523813](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38866523813):
  actual app-owned baseline PNG at **944×510, 96 DPI**, app exit 0 and
  all six protected legacy preferences unchanged. Input failed safely
  when the app was not the foreground user window. A guarded-focus
  attempt [#38866979641](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38866979641)
  encountered the same user-session foreground restriction. These
  failed actions are not evidence of a product grouping regression.
- Direct pixel review of the retained owned `before.png` showed a
  **dark rendered window despite the fixture requesting Light**.
  Root cause: the F05 test wrote escaped text `\\r\\n` rather
  than CRLF delimiters in its private preference file. Fixed by
  `8f67352e` and guarded by `7717d8e0`. Later corrected Light/Dark
  **baseline-only** screenshots passed at `3976779e` and alpha
  preservation passed at `26dce015`, as recorded above; actual
  Windows backdrop and grouped pixels remain unverified.
- Initial [XAML Build/GUI #38855103261](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38855103261)
  timed out in outer worker after creating Release executable bytes,
  before GUI and `result.json`; do not relabel the Actions run PASS.
- **VISUAL ACCEPTANCE: NOT TESTED** for F05 corrected Light/Dark and
  grouped states. Existing exact-SHA F05 functional grouping GUI and
  native C++ PASS evidence remains independent. See
  [F05_GROUP_BY.md](F05_GROUP_BY.md) for the bounded trial details.

## 2026-10-16 Four F05 native C++ probes — PASS with worker timeout caveat

- **Exact tested SHA:** `1f85741cd1ec183719cc0cbce1d2460d89ab033a`.
  The native harness now includes four F05 C++ tests and explicitly
  compiles with MSVC `/utf-8 /W4 /WX` (Korean cp949-safe source parsing).
- [Native attempt #38823430041](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38823430041)
  concluded **FAILURE** at its outer scheduled worker timeout, with no
  `result.json`. This must not be represented as a successful CI run.
- Separate read-only [log review #38826356423](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38826356423)
  and [exact-SHA binary verification #38826480894](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38826480894)
  independently confirmed all four native executable outputs and PASS
  markers, the aggregate `F05_NATIVE_ALL_FOUR_GROUP_AND_TAB_PROBES=PASS`,
  and 8/8 focused Python contracts `OK`. **Native tests: PASS**;
  **outer worker completion: NOT ACCEPTED**. Product WinUI GUI results
  from the earlier verified revision remain unchanged.
- F05 Light/Dark **VISUAL ACCEPTANCE: NOT TESTED**. Details:
  [F05_GROUP_BY.md](F05_GROUP_BY.md).

## 2026-10-16 F05 four-mode grouping — real Windows GUI PASS

- **Exact tested `main` SHA:** `e1a95f6adee897c803e2dfec74e93a43953878b3`.
  [Focused Windows GUI #38809769293](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38809769293)
  **SUCCESS**: 17 targeted contracts, new Release build, actual WinUI
  Name/Size/Modified Month/Type headings, independent collapse and file rows,
  per-tab state restoration, new-tab/close-tab and explicit opt-out.
  WinUI exited 0; six original preference SHA-256 hashes were unchanged;
  synthetic fixture removed. The earlier
  [central GUI #38736462369](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38736462369)
  passed general policy/source, Release and full functional GUI gates for
  product-identical parent SHA `a378722a`.
- **Boundaries:** `VISUAL ACCEPTANCE: NOT TESTED` for F05 original
  Light/Dark pixels. Actual 125/150/200% Windows DPI, active High Contrast,
  Narrator speech, end-to-end keyboard-only disclosure, large-folder practical
  GUI and arbitrary providers are separately unverified.
  See [F05_GROUP_BY.md](F05_GROUP_BY.md) for scoped evidence.
- **Operations:** completed Windows F05 request slot was restored to
  idle by personal-control-plane commit `edca8a2937b595e0b73f2be2c205a64f4910f025`.

## 2026-10-15 F05 independent panes, route and tab navigation — Windows GUI PASS

- **Exact accepted test-only `main` SHA:**
  `10bfbce585d2e8e773bba56b30fa0a046a1a20a4`.
  Original product grouping bridge `c14be710` unchanged;
  used previously clean-built and GUI-accepted Release binaries,
  no product C++/XAML rebuild, no OS display/user config changes.
- [Dual-pane grouping #38712034722](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38712034722)
  **SUCCESS**: eight F05 contract tests; the owned right pane
  successfully grouped .txt/.md/.log and collapsed Markdown; the
  left pane remained independent. After a verified switch to the
  left pane, the live View ToggleMenuFlyoutItem accepted physical
  keyboard Enter (not the unreliable automated mouse click) and
  displayed left groups while preserving the right collapse.
  Collapsing left Log did not collapse right Log; switching panes
  preserved independent state. Right folder navigation discarded
  its obsolete headings without affecting left groups. Actual
  WinUI exit 0; all six real legacy settings hashes unchanged;
  disposable files removed.
- [Added active left-tab transitions #38712448964](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38712448964)
  **SUCCESS** at exact SHA: repeated all independent-pane and
  route checks plus `F05_LEFT_TAB_ADD_RIGHT_PANE_SAFE=PASS`,
  `F05_LEFT_TAB_SELECT_ORIGINAL=PASS`, and
  `F05_LEFT_TAB_SWITCH_AND_CLOSE_ISOLATED=PASS`. Creating
  another left tab, switching to the initial one, returning to
  the new tab and closing it preserved both panes' real file rows.
  Source tests 8/8 PASS, process exit 0, original user profile
  preserved, synthetic fixture removed.
- **Failure analysis:** initial [#38693990951](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38693990951),
  [#38710519949](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38710519949),
  [#38710939595](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38710939595),
  [#38711406737](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38711406737)
  and [#38711709550](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38711709550)
  narrowed a left-pane automated click failure: left was actually
  active, the group-toggle UIA state was 0 before and after the
  attempted mouse click; physical Enter worked. This documents a
  test input-delivery defect, **not proof of a product mouse-click
  defect**. The accepted run uses mouse on right and Enter on left.
- **Historical status as of 2026-10-15:** original app-window Light/Dark
  PNG pixel review, Narrator spoken labels, true OS DPI 125/150/200%,
  active High Contrast, real 25,000-item Windows GUI, other grouping
  dimensions (name/date/size), and full keyboard-only list workflows
  were not yet tested. The newer four-mode GUI test is recorded above.
  Existing F05 before/grouped/expanded PNG capture markers do not
  constitute visually inspected pixels. Windows Remote Shell slot
  restored to idle. Details: `docs/development/F05_GROUP_BY.md`.

## 2026-10-15 F05 type grouping — real Windows GUI PASS, visual pixel review pending

- **Product:** Native bounded group projection arrived in commit 1d6d9205;
  the WinUI bridge (View flyout type-group opt-in, per-pane collapsible
  non-file disclosure headings, original Shell identity preservation,
  fail-closed incomplete views) arrived in c14be710.
- **Accepted GUI source SHA:** 50dc06b872069b6f6ba2f4e5ea3e224c2809423f.
  [Actual owned Windows GUI run #38692989325](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38692989325):
  **SUCCESS**. Eight source-contract checks passed; the exact
  previously built Release launched and exited 0; View menu was
  physically clicked in the owned process; .txt/.md/.log
  group disclosure headings appeared, a real TXT file could be
  selected, collapsing Markdown hid only its files, and reopening
  restored the Markdown row. All six real user setting hashes were
  identical before and after; disposable synthetic fixture removed.
- **Failure provenance:** [#38688357154](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38688357154)
  completed a fresh Release and started WinUI but its GUI test
  misused Desktop.child_window; [#38692716189](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38692716189)
  located the group flyout but misused the absent UIA Invoke pattern.
  Both are corrected **test-harness defects**, not evidence of product
  startup failure, and #38692989325 passed using the corrected test.
- **Image status:** actual app-window before/grouped/expanded PNGs
  were captured under logs/f05-visual (all three capture markers
  present); an attempt to retrieve these originals for manual
  pixel inspection was blocked. **Light/Dark visual pixel acceptance
  is NOT certified.** The GUI assertions establish interaction only.
- **Earlier remaining scope (now superseded for pane/tab behavior by the accepted runs above):** interactive right-pane and cross-tab transitions,
  file selection after group collapse in additional scenarios,
  name/size/date grouping, non-Details group layouts, large-folder
  GUI paging, keyboard-only header toggles, Narrator, DPI 125/150/200%,
  Dark/High Contrast visual review. Central Windows request slot
  was restored to idle. See docs/development/F05_GROUP_BY.md.

## 2026-10-15 F03 interactive window DPI/High Contrast inventory — real 100% observed, higher DPI NOT TESTED

- **Exact test-only source SHA:** `7a84b40022d67468dcfd7273b28fb0271ad175c1`.
  The previously accepted startup-Tab keyboard probe gained only
  read-only calls to `GetDpiForWindow` on the harness-owned actual
  WinUI HWND and `SystemParametersInfoW(SPI_GETHIGHCONTRAST)` in
  the logged-in **interactive user session**. Product XAML/C++,
  Release runtime and all Windows display/accessibility settings
  remained unchanged.
- [Actual Windows owned GUI + direct window DPI/HC #38683265761](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38683265761)
  **SUCCESS**: `F03_ACTUAL_INTERACTIVE_WINDOW_DPI=96`
  (**100% scale**) and `F03_ACTUAL_INTERACTIVE_HIGHCONTRAST_ON=False`.
  The keyboard-only Tab → Space → Tab → Enter → Space acceptance
  passed again; app exit **0**, all six real user preference hashes
  unchanged and disposable fixture removed. The exact source-only
  change did not trigger an unnecessary new Release rebuild.
- **No higher-DPI or active HC acceptance is implied.** Actual
  interactive 125% (120 DPI), 150% (144 DPI), 200% (192 DPI) screen
  geometry/clipping, focus contrast under Windows High Contrast,
  and Narrator spoken output are all **NOT TESTED**. No global OS
  setting was changed merely to simulate these states.
  The central Remote Shell request was restored to idle.

## 2026-10-15 F03 keyboard-only startup Preview route PASS; real OS DPI/HC/Narrator remain untested

- **Exact accepted test-only main SHA:** `74824b4d5178da966b09535755c7e6c1f601ccb7`.
  The opt-in `FLY_F03_STARTUP_KEYS_ONLY=YES` harness at
  `tests/winui/test_shell_gui.py` and
  `tests/winui/test_f03_startup_keyboard_gui.py` uses the
  **unchanged previously accepted Release** from product revision
  `40d383ca`; no C++/XAML files or real user settings changed.
- [Real user-session keyboard GUI #38683014933](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38683014933)
  **SUCCESS** at the exact test SHA, on a disposable synthetic
  `theme=dark` configuration. After activating **only the owned app
  window**, the probe sent real Tab presses without directly focusing
  or clicking a control: **18 Tab** presses to the Details toolbar
  button; Space to open Details; **26 additional Tab** presses to the
  upper Preview shortcut; Enter to focus and scroll the actual lower
  opt-in button into view; Space to explicitly enable Preview. The
  content remained empty before opt-in, and with no selected file the
  Preview remained empty and requested selection of one text file.
  Acceptance markers were `F03_STARTUP_KEYS_OPEN_DETAILS=PASS`,
  `F03_STARTUP_KEYS_REVEAL_NO_READ=PASS`,
  `F03_STARTUP_KEYS_EXPLICIT_OPTIN_NO_SELECTION=PASS` and
  `F03_STARTUP_KEYBOARD_ONLY_GUI_PASS=True`.
  Six focused source contracts also passed; app exit **0**,
  all six real legacy preference hashes unchanged and owned fixture
  removed. **PASS is bounded to this startup-to-toggle path**;
  keyboard-only selection of a file and all file-manager commands,
  or screen-reader spoken announcements, were not covered.
- The preceding [#38682895858](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38682895858)
  failed in **test harness code**, not product behavior, because
  `UIAElementInfo.has_keyboard_focus` is not supported by the installed
  pywinauto version. The single-file probe correction uses
  `IUIAutomationElement.CurrentHasKeyboardFocus` and is verified by
  the successful run above; no rebuilt binary was needed.
- [Read-only Windows accessibility inventory #38682652550](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38682652550)
  **SUCCESS**: the SYSTEM Session 0 `GetDpiForSystem` returned
  **96 DPI**; one active Explorer user session was found. Its loaded
  Desktop profile had `LogPixels` **not set** and `Win8DpiScaling=0`.
  The read-only HighContrast registry flags were `126` (bit 0 not
  enabled); no `Narrator.exe` process was observed. **This does not
  establish the actual per-monitor DPI of the interactive user session
  or provide High Contrast/Narrator audio acceptance.** No display,
  global accessibility setting, or user configuration was changed.
- **Still NOT TESTED:** actual OS display 125%/150%/200% screenshot
  and clipping, active High Contrast product pixels, spoken Narrator
  output, all-settings keyboard-only coverage and fine-grained
  screen-reader focus order. Programmatic app-window-only foreground
  activation is not proof of OS-level launch/initial desktop focus
  behavior. Central Remote Shell slot was restored to idle; no
  duplicate Windows acceptance run was requested.

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

## 2026-10-15 F03 Light strict real GUI + Light pixel QA PASS

- Exact Light acceptance source SHA
  `a425f1064c75a93abf2b191e7956df5336082832`
  (docs-only changes after `b86e93f5`; product executable/XAML
  equivalent to accepted `196aa27b`). Test-owned synthetic Light
  profile, unchanged real user settings.
- [Real Windows strict Light GUI #38664462095](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664462095)
  **SUCCESS**: physical mouse plain re-click selected exactly
  `readme.txt`, cleared `Nested` and correctly reread text after
  opt-in; opt-out/reopen and stale cancellation passed. App exit 0,
  synthetic fixture removed, all six legacy user preferences hashes
  unchanged.
- Previous and new synthetic Light **app-window-only original PNGs**
  compared in [read-only #38664699576](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664699576)
  at ~952x519: readable filename/selected row, toggle, detail labels,
  content, pane separation and no observed new clipping or overlap.
  **VISUAL ACCEPTANCE: PASS for this bounded Light comparison**.
  Dark counterpart accepted at #38663593381. Actual system
  125/150/200% DPI, High Contrast, Narrator, full keyboard-only
  traversal and independent Preview pane are NOT TESTED.
- Central Remote Shell slot restored to idle; protected evidence kept.

## 2026-10-15 F03 Extended dual-pane input — keyboard and modifiers PASS

- **Exact latest tested source SHA:** `b86e93f5e004d1f5e8cc40ae6ff663f55b01487f`;
  app XAML/C++ remain **identical** to the exact `196aa27b`
  Release, strict mouse, and scoped dark-pixel accepted product.
  New test-only `FLY_F03_EXTENDED_ONLY=YES` and
  `test_f03_extended_selection_gui.py` run in the isolated shell.
- [Owned Windows GUI #38664113381](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38664113381)
  **SUCCESS**. Both left/right ListViews independently passed
  Down-arrow selection replacement after focusing a file row,
  Ctrl+click add/remove, Shift+click range, and plain click
  single-item replacement. `F03_EXTENDED_BOTH_PANES_INPUT_PASS=True`;
  original 6 legacy user settings SHA256 identical; temporary
  fixture removed; app exit=0. Remote request slot restored idle.
- Remains **NOT TESTED**: keyboard-only navigation from app startup,
  drag-and-drop interaction in `Extended` mode, Light/High Contrast
  final pixels at the changed product SHA, 125/150/200% actual DPI,
  screen-reader spoken guidance and full Preview pane/image work.

## 2026-10-15 F03 physical mouse selection resolved — Release + owned strict GUI + Dark pixels PASS

- **Current accepted product SHA:** `196aa27b1132955c6c6c5eabd1470c971eac06d9`.
  Left and right WinUI file lists changed from `SelectionMode="Multiple"`
  to `SelectionMode="Extended"`; the existing preview/helper and file
  operation code remain unchanged. The controller source contract
  checks both panes and the unchanged drag/selection event wiring.
- [Central Windows Release #38662641235](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38662641235)
  **SUCCESS** for the exact SHA, followed by
  [owned strict physical mouse GUI #38663282030](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38663282030)
  **SUCCESS**. Actual row click changed from `Nested` back to
  **only** `readme.txt`, with
  `F03_GUI_RESELECT_PHYSICAL_SINGLE_SELECTION=True`,
  `F03_GUI_RESELECT_BOTH_ROWS_SELECTED=False`, and
  `F03_GUI_STRICT_PHYSICAL_RESELECT=PASS`. No UIA `Select()` fallback
  was needed; genuine opt-in text re-read, selection-stale clear,
  opt-out and reopen remained PASS. Test-owned fixture removed,
  app exit 0 and original six user settings SHA256 unchanged.
- Previous `Multiple` strict GUI
  [#38655414859](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38655414859)
  had an ordinary click input failure and multi-selection retention.
  Its before-change app-only dark PNG and the new after-change PNG
  were retrieved read-only in
  [#38663593381](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38663593381)
  and visually inspected at approximately 952x519: both dual-pane
  layouts, text Preview, highlight and contrast were readable without
  observed new clipping/overlap. Fixture path/timestamp differ.
  **VISUAL ACCEPTANCE: PASS for the compared dark window only.**
  Light at this changed SHA, keyboard-only, Ctrl/Shift multi-select,
  drag interactions, 125/150/200% OS DPI, HC and Narrator are
  **NOT TESTED**, not silently promoted from historical evidence.
- Central remote request slot restored to idle; protected test-owned
  evidence remains under `.keep`.

## Historical 2026-10-15 F03 opt-in text Preview — early GUI with mouse input caveat

- **Accepted GUI SHA:** `0e4e147f7e1004703d9566f3bf38bb086de6c17a`.
  The current app XAML/C++ are identical to previously starting
  `b9b15d39`; only F03 test code changed to use the already proven
  Details-region scrolling and to record the actual selected bit.
  [Dark actual Windows GUI #38648688824](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38648688824)
  **SUCCESS**; [Light test-only preference
  #38649041893](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649041893)
  **SUCCESS**. Actual app launch, native list, opt-in `readme.txt`
  bytes displayed, selection of folder removing stale contents,
  actual SelectionItem-driven reselect/refresh, opt-out clear,
  Details reopen default-off and clean app exit passed.
  Original six user config hashes remained identical and all
  disposable synthetic fixture files were removed.
- App-window-only **before/after original PNGs** retained in protected
  scratch; [dark original view #38648361110](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38648361110)
  and [light original view #38649262620](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649262620)
  were scope-checked and inspected: at the viewed 940x508
  presentation the toggle/text contrast remained readable, opt-in
  bytes were visible only in the after image and pane overlay
  wasn't observed. Toggle **remains low inside Details** and must
  be revealed with pane-local scrolling; its discoverability needs
  work. Do not infer DPI/High Contrast/Narrator certification.
- **Physical mouse reselect NOT ACCEPTED:** both actual GUI logs
  recorded `F03_GUI_RESELECT_PHYSICAL_CLICK_SELECTED=False`.
  The subsequent verified UI Automation `SelectionItem.Select()`
  did select the test-owned file and did rerun Preview correctly.
  Keep mouse hit-test/selection as an explicit next GUI acceptance
  gate; do not mislabel this fallback as physical mouse success.
  [Follow-up owned GUI #38649640303](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38649640303)
  **SUCCESS for UIA-assisted flow only** at test-only SHA
  `95d45f322cbaaca604066a15683434773b2342ab`.
  It waited for the folder to report a fully selected state,
  paused before the next physical click, and polled the target
  selection. `F03_GUI_RESELECT_SETTLED_PHYSICAL_CLICK_SELECTED=False`
  persisted; the accessibility Select() fallback again passed.
  Thus the simple immediate-click race is not an adequate
  explanation. Leave mouse hit-testing/focus/manual click unverified.
- **Historical source-only mouse diagnostic:** prior to the
  strict runs, hit-target/foreground-ownership logging and the
  `FLY_F03_STRICT_PHYSICAL_RESELECT=YES` acceptance mode were
  prepared but not yet executed. The later real Windows strict tests
  #38655414859 (old mode FAIL) and #38663282030 (new mode PASS)
  supersede that pre-test status. See
  [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).
- **Failed but now reverted separate layout change:** exact
  `fac580bd` passed [source/Release
  #38646656680](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38646656680)
  yet [GUI #38647173047](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38647173047)
  still crashed at startup `0xC000027B`. Restore commit
  [`95bd998a`](https://github.com/tngkrwlsmd/flyExplorer/commit/95bd998a5a717718085fb55c99c41d05f11f04e7)
  kept the previous app/XAML and reverted its now-invalid source
  assertion. Release success alone is never visual or startup PASS.
- **Remaining F03 (historical checkpoint, superseded in part above):**
  earlier physical mouse and keyboard selection gates were pending;
  new strict physical mouse and focused-list keyboard/modified click
  gates now PASS as recorded above. Still improve Preview toggle discoverability without modifying the
  known-starting XAML subtree in a way that recurs the startup
  COM error, validate `.md`/`.log`, narrow/resized Light/Dark,
  actual 125/150/200% DPI, high contrast and audible Narrator;
  full image decoding/independent Preview pane is unimplemented.
  Retain previously accepted native helper/job/cancel tests and
  all `.keep` evidence. See
  [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).

## 2026-10-15 F03 earlier milestone — parent/helper wired, before GUI acceptance

- Current `main` application/UI-test file contents at [00377986](https://github.com/tngkrwlsmd/flyExplorer/commit/003779863a0fa19c8becb04b38e82ce2b3ba6896)
  match the exact blobs of GUI-starting `b9b15d39` after a
  non-forced, expected-head, **three-file safety rollback**. The
  previous later layout at `fec86c32` crashed before any owned GUI
  window (`0xC000027B`, `Microsoft.UI.Xaml.dll`, WER `0x80004002`);
  a disposable simpler heading also crashed. Do **not** claim that
  only the horizontal title caused the crash.
- [Central Release #38559429224](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38559429224)
  accepted the native parent compile, and
  [central #38562561304](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38562561304)
  accepted the shipping Release with opt-in `PreviewController` on
  `7e405418`. Native actual child, corrupt-wire, hung child and
  active-cancel checks remain accepted at earlier cited SHAs.
- [Actual GUI #38564071039](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38564071039)
  **started** dual-pane WinUI at the matching `b9b15d39`
  code, then failed its text UIA element lookup. **Text content
  display, cancellation while changing selection and before/after
  visual pixels remain NOT ACCEPTED.** This is a startup-stability
  fallback, not successful F03 user-facing delivery.
- Later [diagnostic GUI #38645754377](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38645754377)
  confirmed the simpler heading also had a startup crash. The first
  disposable worktree [#38641494315](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38641494315)
  failed external NuGet restoration. Reusing the owned local cache
  [#38643849995](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38643849995)
  compiled but its combined job timed out before GUI; its output was
  separately launched in #38645754377. Read-only
  [#38645509785](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38645509785)
  confirmed original pinned checkout clean, no owned test scheduled
  tasks or build processes; held evidence must not be auto-deleted.
- **Next:** isolate XAML subtree/visibility COM startup failure via a
  narrow, real logged-in user's controlled executable; then actual
  opt-in UTF-8 text UI, stale route/cancel, Light/Dark pixels,
  keyboard focus, DPI/High Contrast/Narrator. Image decoder and
  general F03 pane remain unimplemented. See
  [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).

## 2026-10-14 F03 Preview parent supervisor — real child native PASS, UI unwired

- **Native acceptance code SHA:** `4a8ddc9f44935e5b9b47c882b0d9df6193ccd087`.
  Added UI-independent `src/base/file_preview_supervisor.h/.cpp`
  (background-only, suspended CreateProcess, restricted inherited
  stdin/stdout/stderr HANDLE_LIST, private Job kill-on-close, checked bounded
  request/reply and process exit, timeout/cancellation cleanup) plus
  `file_preview_request_gate.h` (window/pane/tab/selection/generation token
  invalidation). The supervisor translation unit is linked from the tracked
  WinUI app project template; the later opt-in controller has since been wired,
  but its end-to-end interactive GUI is not yet accepted (see current section).
- [Native actual child #38558173709](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38558173709)
  **SUCCESS** at `fa58362a3c719a154b43ea518c9f6bee93c7545f` for
  actual one-shot helper bytes, unsupported/missing request handling,
  corrupt response, owned child Job timeout, stale route and test cleanup.
  [Follow-up #38558563233](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38558563233)
  **SUCCESS** at latest native-test SHA above also covered active
  cancellation after launching a deliberately blocked disposable child,
  and re-proved the earlier cases.
- A failed source-harness run [#38557209117](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38557209117)
  was a PowerShell stderr-capture error; the corrected source gate and
  Release helper build succeeded in [#38557801405](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38557801405)
  before revealing an actual C++ missing-move compile error. The
  explicit Handle move was fixed, compiled and accepted in the later
  native runs. Do not mislabel these earlier failed runs PASS.
- **Central Release compile verified at prior exact SHAs** as documented
  above. **Still not accepted:** actual end-to-end UI selection/background
  callback, stale-result display, image decoder or full Preview pane.
  This is not a sandbox, and actual host power-cut durability is not
  implied by the unrelated PR #63 graceful-reboot evidence.
  See [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).

## 2026-10-14 F03 one-shot Preview helper — bounded private protocol verified

- **Latest worker code SHA:** `d0d5b6a987ef8ae1c73e2aa0f5ceacb20c37f0ec`.
  Added private versioned/length-checked/checksummed
  `file_preview_worker_wire.h`, isolated-only
  `file_preview_worker.cpp`, and explicit
  `FlyShellIsolationHelper --preview-read` mode. One request opens and
  reads a single eligible local file, sending a capped raw byte frame
  or empty-body error. This has **no user-facing Preview pane** and no
  production parent supervisor wired to this mode.
- **Native fixture behavior accepted:** [Remote Shell #38526086984](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526086984)
  **SUCCESS**: bounded test-owned anonymous-pipe wire, valid TXT bytes,
  wrong checksum/kind/length, non-existent TXT and UNC negatives,
  existing native guarded-open and symlink rejection, and scratch cleanup.
  Prior failed fixtures #38525652361/#38525878610 were a test
  error: the nonexistent filename ended in unsupported `.missing`, so
  the correct earlier unsupported-type response disagreed with the
  test's expected missing-file response. Replaced with
  `.missing.txt` and verified without product-code changes.
- **Source contract accepted:** [central #38526337158](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526337158)
  **SUCCESS**, exact SHA, policy, structure 4, product 199,
  harness 20, infrastructure 30 passed.
- **Release build and helper staging accepted:** [central #38526567823](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38526567823)
  **SUCCESS**, `scope=release` at exact SHA. `build.cmd` requires
  the helper build to succeed before building and staging
  `flyExplorer.exe`; the helper project includes the preview worker.
  This proves **compiler/link/staging integration**, not actual
  external child process execution, job-object cancellation, end-to-end
  bounded read/wire or stale-result filtering.
- **Next implementation:** bind the now-native-verified supervisor and
  request gate to a pane-owned `PreviewController` on a background thread,
  resolve only the trusted sibling Helper path, cancel on navigation/
  selection changes, and check the request ticket before UI dispatch.
  After actual integration acceptance, implement bounded image decoding
  and an opt-in XAML Preview pane.
  High-contrast, DPI scaling, Narrator and before/after pixels
  still **NOT TESTED for F03**, because its UI does not exist.

## 2026-10-14 F03 guarded local safe-open — native/source/Release verified

- **Latest tested source SHA:** `8ecd748a126f58b9c81f88ad026fe8a434a4d77a`.
  In `src/base/file_preview_safe_open.h/.cpp`, worker-only
  `openLocalRegular` copies the request path before screening, validates
  the drive root and each opened directory/file component using Windows
  HANDLE identities and attributes, rejects reparse/offline/UNC/ADS/
  non-regular/size-mismatched paths, and returns a RAII file handle plus
  all ancestor directory handles kept locked through the caller's read.
  The old bounded `readVerifiedHandle` is used together in the native
  test, without WinUI involvement. These checks **reduce** replacement
  and traversal risk; they are not a security sandbox or a substitute
  for terminating a blocked worker.
- **Actual test-owned MSVC native:** [#38522342210](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38522342210)
  PASS at `b6c7c268354493f48ac94d22c77156f87d101fd8`;
  [#38523226489](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523226489)
  PASS at `aca6bc779de2408a3eccc73ba63c5a1e205f3a39`.
  Actual nested-file read, negative UNC/ADS/traversal/metadata/cancel/
  expiry cases and file + ancestor-directory symlink rejection passed;
  temporary fixture cleanup passed. The second run included correction
  of dangling temporary `wstring_view` fixture paths and path snapshot
  exception-safety.
- **Current-source check:** [central source run #38523664886](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523664886)
  PASS at the exact SHA `8ecd748a126f58b9c81f88ad026fe8a434a4d77a`
  (policy, structure 4, product-source 196, harness 20, infra 30).
  Earlier source run `38523399332` failed one stale source-contract
  string after the stable-path change; the contract was corrected and
  the accepted follow-up passed.
- **Safe-opener Release accepted:** [central registered CI #38523831041](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38523831041)
  completed **SUCCESS** with `scope=release` at exact source SHA
  `8ecd748a126f58b9c81f88ad026fe8a434a4d77a`;
  producing log explicitly listed `file_preview_safe_open.cpp` and
  `PASS release-build`. No duplicate build was dispatched for that SHA.
- **Feature gate still OPEN:** no production supervised helper process,
  bounded IPC, kill-on-timeout cancellation, stale pane/tab/selection
  protection, bounded decoded images, opt-in Preview presentation or
  before/after pixel acceptance. No user-visible UI changed, and
  **F03 PREVIEW PANE IS NOT YET USER-FACING**. Technical details:
  [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).

## 2026-10-14 F03 Preview pane — bounded policy and handle reader verified

- **Scope:** source-only candidate policy `src/base/file_preview_policy.h`
  plus independently compiled and tested `src/base/file_preview_reader.h/.cpp`.
  The actual Preview pane and its out-of-process worker have **NOT** been
  implemented or connected to WinUI. No existing user-facing pixels changed.
  Design boundaries and next steps: [F03_PREVIEW_PANE.md](F03_PREVIEW_PANE.md).
- **Accepted source checkpoint:** [central source run
  #38510347268](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38510347268)
  PASS at `842742ad7b83a338d3027a9d4025e4c149a8507e`
  (`desktop-a`, `scope=source`, policy+source contracts). Phase-one
  local policy screen limits local regular TXT/MD/LOG to 256 KiB and
  PNG/JPG/JPEG/BMP to 12 MiB; intended future image decode cap
  16,777,216 pixels, with unsupported/UNC/reparse/unsafe paths rejected.
- **Exact MSVC Release proof:** [central registered run
  #38518993733](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38518993733)
  **SUCCESS**, `project_id=desktop-a`, `scope=release`, SHA
  `93c8a435cb5de505d02ac1927ceb30e0f572bd09`.
  Producing log explicitly lists `file_preview_reader.cpp` compiled and
  `PASS release-build`; executable output created. This is a native
  compile/Release acceptance, not file-read behavior or UI acceptance.
- **Updated current-source contract acceptance:** [central run
  #38520410675](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38520410675)
  **SUCCESS** for exact main `0e677eeb215d7d3b514bc382846c5b958533ad76`,
  `project_id=desktop-a`, `scope=source`; policy validation PASS,
  canonical structure 4, product-source 194, harness 20 and infrastructure
  30 tests OK. This source run validates the subsequently corrected native
  probe harness contract and status docs; it is not a recompile or GUI pass.
- **Exact test-owned MSVC native behavior:** [Remote Shell run
  #38520021060](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38520021060)
  **SUCCESS** at `62a4f632d302bce59839b3b4109a1380c55e5b5a`.
  The standalone reader test compiled `file_preview_reader.cpp` with
  `native_preview_reader.cpp`, and recorded
  `F03_NATIVE_HANDLE_READ_AND_FAILURE_CONTRACT=PASS`,
  `F03_NATIVE_VERIFIED_HANDLE_ACCEPTANCE=PASS`, exact owned SHA and
  scratch cleanup PASS. Inspected bounded positive reads and rejection
  of changed/mismatched path/size, invalid UTF-8, cancellation,
  deadline, oversized text, invalid handle and directory handles.
  The actual opened-handle final path and local fixed-disk checks are
  implementation guards, **not** a proof that arbitrary ancestor reparse
  traversal is safe. The native test is not an isolated worker or GUI.
- **Prior execution/harness failures:** runs `38518452445` (PowerShell
  5.1 parser), `38518550162` (SYSTEM Python PATH), `38518696504` /
  `38519687206` (concatenated PowerShell batch command truncated to
  `call "`). No C++ assertion ran in those attempts; the batch
  serialization was corrected, and the final native run passed.
  Do not repeat unchanged Release or native tests.
- **Remaining high-priority F03 gaps:** safe authoritative handle opening
  with all-ancestor reparse and race checks; supervised worker-process
  launch, cancel/kill and bounded result wire; stale selection/pane/tab
  identity rejection; image header/decode dimensions/memory guard;
  inert rendering of UTF-8 text, placeholders, opt-in Preview pane
  presentation and source/GUI/pixel acceptance. **USER-VISIBLE F03
  PREVIEW FEATURE: NOT YET IMPLEMENTED.**


## 2026-10-14 F02 narrow Details scroll and keyboard focus — inspected PNG pass

- **Exact reviewed main:** `028f8692e82a938c32832398758a65271c1b950d`.
  [Central owned Windows Remote Shell run #38497182086](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38497182086)
  completed **SUCCESS** against this SHA. The bounded worker executed source
  checks, x64 Release build, interactive WinUI 800×550 at actual **96 DPI**,
  light/dark test-owned fixtures, normal process exit, and verified temporary
  file and scheduled-task cleanup. This is a **focused** GUI/visual acceptance,
  not an independent full Windows GUI suite or a multi-DPI run.
- **Lossless pixels reviewed:** Eight PNG screenshots (`ENABLED`,
  `SCROLLED`, `RESTORED`, `FOCUSED_TOGGLE` per theme), reconstructed with
  exact length checks from numbered central-run log chunks, were inspected.
  With Details visible in the short window, the `수정 날짜` heading initially
  appears at the bottom. Scrolling the owned Details viewport reveals an
  actual modified-date value in both light and dark themes, without scrolling
  or disturbing the left/right file lists. Scrolling upward restores the
  top header and content. **NARROW DETAILS SCROLL REACHABILITY: PASS.**
- **Visible keyboard focus:** The earlier UIA `set_focus()` screenshots
  at [run #38473558319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38473558319)
  had byte-identical focused and unfocused pixels and were not accepted.
  The updated fixture in `028f8692` sends real keyboard `Shift+Tab` and
  `Tab`, checks the Details toggle UIA focus transfer, and captures after
  keyboard focus. The reviewed images clearly show a dark outline around
  the Details toggle in Light theme and a light outline in Dark theme,
  absent from the unfocused images. **FOCUS PIXEL VISIBILITY: PASS** in this
  actual owned keyboard/96-DPI state. This does **not** establish the entire
  application's keyboard navigation sequence or Narrator spoken output.
- **Visual acceptance scope:** The observed F02 800×550 narrow details
  overlap fix, scroll reachability and focused-toggle outline now have
  reviewed PNG evidence in both themes. Do not repeat unchanged Release
  build/capture work. **Remaining distinct gates:** original broader matched
  states, OS-level 125/150/200% scaling, F02 High Contrast, actual Narrator
  speech, long/provider paths and large-index edge cases. The latest
  feature-level focus/scroll passes do not automatically imply a current
  SHA-scoped central `central-ci/windows-gui` status.

## 2026-10-14 F06 address candidate visual readability — accepted bounded states

- **Exact reviewed `main`:** `92e3661cecd7e3f5effcf805434a12663b4dcd95`
  with presentation fix `90f588881f60b708823f86cc470cb45a2fc48f52`,
  source contract `92e3661cecd7e3f5effcf805434a12663b4dcd95`
  and screenshot harness `fb28cacfbb460a3a5259b2ee35f024805a390445`.
- **Before / after real screenshot evidence:** [prior original-PNG
  Windows run 38476514337](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38476514337)
  and [fixed original-PNG Windows run 38491527835](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38491527835)
  both completed SUCCESS with test-owned WinUI Release process, normal exit,
  bounded temporary scratch cleanup, and four app-window-only PNGs for
  light/dark at window widths 940 and 800 px (96 DPI). The after run explicitly
  returned `F06_VIS_RESULT=PASS STAGE=complete` and
  `F06_VIS_OWNED_CLEANUP_PASS`. These are focused acceptance runs,
  not a new independent full canonical-main GUI suite.
- **Actual original PNG review:** Log-chunk byte counts matched the expected
  images, and the four before/after states were visually inspected. Previously
  the suggestion button rendered the *start* of a long absolute path, truncating
  away candidate identity (especially at 800 px). After the change the label
  shows the distinguishing leaf and, where helpful, its parent (e.g.
  `Nested — Left`); the selected full absolute path remains in the
  original button Tag, accessible `주소 후보: <full path>` automation name
  and full-path tooltip. The 940-px light/dark image shows two legible
  candidates; the 800-px image shows the narrowed single candidate with the
  leaf fully visible. No obvious candidate/input overlap or truncated
  distinguishing leaf was found in those captured states.
- **VISUAL ACCEPTANCE: PASS in inspected 96-DPI light/dark, 940-/800-px
  address-suggestion states only.** Do not generalize this to all suggestion
  data, pointer/keyboard focus pixels, High Contrast, actual OS 125/150/200%
  scaling or Narrator speech. Reachable SMB provider acceptance also remains
  open. Existing prior main functional GUI evidence is reused, not expanded
  to new CI status for this SHA.

## 2026-10-14 F02 owned narrow-layout fix — original PNG review

- **Canonical main source:** `7441dad96572d1f90d6eff5fac671116d0081345`;
  implementation fix `01c24b3393cb20810440f45ff4b2e5cb5577108b`,
  source regression guard in `7441dad96572d1f90d6eff5fac671116d0081345`.
  The F02 Details pane previously consumed 260 px without being deducted
  from the dual-pane DetailLayoutProfile width. At 800x550, the two lists
  therefore showed name and size fields colliding. The layout now subtracts
  the visible Details pane's 260 px and re-evaluates file columns when
  toggling it.
- **Owned Windows evidence:** [Remote Shell run 38473558319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38473558319)
  completed SUCCESS at the exact SHA: source checks, x64 Release build,
  actual interactive test-owned WinUI, 800x550 window, 96 DPI, light and
  dark themes, original lossless PNG capture, normal owned process exit,
  and bounded scratch/task cleanup. This is a focused capture and build,
  **not** a new current-main full GUI suite acceptance.
- **Actual original-PNG inspection:** Reconstructed `LIGHT_ENABLED`,
  `DARK_ENABLED` and the corresponding `FOCUSED_TOGGLE` images from
  length-checked, numbered log chunks. Both theme previews display
  distinct non-overlapping file names (without the colliding size column),
  preserved left/right panes, selected `readme.txt`, Details information
  and footer. This closes the *observed 800x550 name/size overlap* only.
  Paths and type text wrap in the Details pane; the modified-date value
  is below the initial visible 550px viewport. Prior F02 focused
  functional acceptance tested scrolling at a larger owned window;
  its visibility after scrolling at 800x550 has not been reverified.
- **Focus visual is not accepted:** In each theme, `ENABLED` and
  `FOCUSED_TOGGLE` original PNGs are **byte-for-byte identical**
  even though the UIA focus assertion passed. The harness calls a window
  foreground/focus helper before screenshot and uses UIA `set_focus()`
  to reach the toggle. This evidence does not establish a visible
  keyboard-navigation focus cue; keyboard-driven focus transfer and
  actual focus pixels remain open. Do not mark focus visual PASS from
  the mere UIA `has_keyboard_focus()` result.
- **Open separate gates:** full-range original-PNG matched revision/state
  comparison beyond this narrow fix, keyboard focus visibility, narrow
  Details scroll reachability, actual OS 125/150/200% DPI, High Contrast,
  Narrator speech, F06 address-suggestion pixels and provider/large-index
  cases. **F02 VISUAL ACCEPTANCE: NARROW OVERLAP FIX VERIFIED; OTHER
  REQUIRED VISUAL/ACCESSIBILITY STATES OPEN.**

## 2026-10-13 F02 canonical main GUI and bounded visual inspection — latest

- **Exact canonical main:** `f4e2bb5937d00a1ef3b2652334e377f10ad25b7d`
  (2026-10-13; documentation-only latest change). Its source tree retains the
  F02 product/test changes from `f5c0fce1b9193ca95c0a10e86443afc984d637b5`.
- **Independent current-main functional acceptance:** [central Remote Shell
  #38395275513](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38395275513)
  explicitly requested `project_id=desktop-a`, `scope=gui`, exact main SHA
  `f4e2bb5937d00a1ef3b2652334e377f10ad25b7d`. Producing output recorded
  `PASS release-build`, `PASS functional-gui`,
  `CENTRAL_CI_PASS` and `central-ci/windows-gui=success`.
  **MAIN RELEASE + FUNCTIONAL GUI: PASS** for that SHA/scope, not Debug, real
  pixel review, or wider accessibility/hardware certification.
- **Review of available real-product images (2026-10-13):** The four bounded
  JPEG re-encodings emitted directly in [F02 visual capture run
  #38392955469](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38392955469)
  were reconstructed from their numbered log chunks and visually inspected:
  `LIGHT_BEFORE`, `LIGHT_AFTER`, `DARK_BEFORE`, `DARK_AFTER`.
  BEFORE uses `a5783991e57a5aab8e0281f171f39541f36d036c`, AFTER uses
  `f5c0fce1b9193ca95c0a10e86443afc984d637b5`.
  The underlying captures were from actual test-owned WinUI Release windows
  with matched window geometry/DPI for each theme (the capture fixture sizes
  its HWND up to 940x610). Examined selected `readme.txt` file rows,
  opt-in Details panel, header/button, type/size/date/location labels, the
  two independent file panes and bottom status area. Both displayed theme
  pairs showed readable selection and Details text, preserved left/right
  panes/status, and no clearly visible panel overlap or clipping. Narrow
  type/location values wrap across multiple lines; their legibility at
  smaller widths was not established. Test-owned random fixture paths differ
  between BEFORE and AFTER and are not pixel-identical expected text.
- **Evidence limit / visual gate remains OPEN:** the four log images are
  compressed JPEG previews, **not** the original PNG bytes or a lossless
  pixel-diff review. Only a selected-row, Details-enabled state under the
  observed standard-size light/dark fixtures was visually inspected.
  An original-PNG fine-pixel check and matched narrow-window/focus states
  have **NOT** been accepted; no actual 125/150/200% scaling, F02 High
  Contrast, Narrator speech or provider/large-index edge-case validation is
  inferred. **VISUAL ACCEPTANCE: PARTIAL REVIEW ONLY — NOT FULLY ACCEPTED.**
  Reuse exact old screenshots/runtime if still retained; do not rebuild
  unchanged product merely to repeat a prior functional PASS.

## 2026-10-13 F02 read-only selected-item Details pane — focused Windows checkpoint

- **Feature branch acceptance:** `feat/f02-readonly-details-pane-20261013`,
  exact functional candidate `39221b3cd7af257f4e34edf44ebed99c8fb4bb18`;
  latest visual-capture candidate `f5c0fce1b9193ca95c0a10e86443afc984d637b5`.
- **Behavior:** explicit opt-in Details pane for the active WindowTab, showing
  selected file/folder name, type, location, size and modified date from the
  existing bounded Shell snapshot, rendered row identity and asynchronous
  metadata caches. Single selection only; stale routes, pending navigation,
  nonfilesystem entries and multiple selection fail closed. Details are
  read-only: no new file mutation, in-process Shell provider call or global
  Windows setting change. Collapse/reopen and opposite-pane selection use
  separate active-pane state.
- **Windows functional evidence:** [run 38391634316](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38391634316)
  completed PASS against `39221b3cd7af257f4e34edf44ebed99c8fb4bb18`:
  source contracts, x64 Release build, actual owned WinUI left-file/right-folder
  selection, details text, toggle/reopen, normal exit and owned scratch cleanup.
  Earlier runs [38386492476](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38386492476),
  [38386808505](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38386808505)
  and [38387378826](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38387378826)
  were diagnostic GUI failures while correcting collapsed UIA peers and
  scrolled read-only metadata. They are not passing acceptances.
- **Visual evidence boundary:** [run 38392955469](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38392955469)
  completed PASS for matched owned light/dark before-and-after screenshot
  *capture* at `f5c0fce1b9193ca95c0a10e86443afc984d637b5`.
  It explicitly reported `F02_VISUAL_OWNED_MATCHED_CAPTURES=PASS PIXEL_REVIEW_REQUIRED`.
  This proves capture, **not actual pixel review, contrast, clipping or
  comparison acceptance**. Do not mark visual acceptance complete.
- **Still open after later main acceptance:** full-resolution original-PNG
  pixel review and actual narrow/focus interaction states, actual OS
  125/150/200% DPI, High Contrast and Narrator speech, provider/large-index
  edge cases. The canonical-main functional GUI gate subsequently passed; see
  the newer checkpoint above. The compressed JPEG review is limited evidence.

## 2026-10-13 F06 latest main full GUI regression — same-source recheck

- **Canonical main checked:** `40cb928b2ae14e801b5c27300de9348fa3c19e65`, including bounded known-path address suggestions, quoted UNC rejection and last-committed-path preservation. No new product source change was made during this recheck.
- [Central main GUI run 38382588456](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38382588456) **FAILED** in a v7 multi-WindowTab private-session save assertion (`v7 multi-window private session was not saved`), after successful Release build. This historical failure is not a PASS.
- [Diagnostic run 38383648183](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38383648183) used a one-commit **test-only** diagnostic fixture (`781dc3671765830ae999f74705445839de7ab040`). Its inner scoped `gui-window-tabs-Release` returned exit code 0; the outer workflow itself failed on an extra, incorrect expected aggregate-log marker. Do not call that outer run successful.
- **Accepted full main GUI:** [run 38384468606](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38384468606) completed **SUCCESS** against the original identical main source. Policy/source, x64 Release, `gui-window-tabs-Release`, `gui-all-Release`, full functional GUI and `central-ci/windows-gui` status passed. Thus the preceding v7 failure was **not reproducible in this one recheck**; no root cause or long-term nondeterminism fix is claimed.
- **Open acceptance:** reachable approved SMB share, screenshot comparison of suggestion UI, high-contrast and actual 125/150/200% scaling, Narrator spoken output. Never treat nonexistent loopback UNC rejection as proof of successful network-share browsing.

## 2026-10-13 F06-D quoted UNC failed-navigation safety — focused acceptance

- **Verified candidate:** `1b6f2ccc671393f5241005ef11bcefcc19ec33b6`,
  `test/f06-quoted-unc-loopback-20261013`, based on canonical
  `da8613e95ab4ae0fefad2fce60860e5e2a487623`.
- **Behavior:** when the user presses Enter on a new address, the address
  chrome and breadcrumb continue displaying the **last committed** pane/tab
  location while the isolated Shell request is pending. On success the
  accepted snapshot updates the location; on failure, an invalid quoted
  path/UNC request does not replace the previously committed pane.
  Never rewrite the address in an asynchronous Failed callback: that
  approach can erase a subsequent user edit or wrongly supersede a newer
  valid request. Existing side/route request-token isolation is unchanged.
- **Focused Windows acceptance:** [run 38381812799](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38381812799)
  completed successfully at the exact candidate SHA: source contracts,
  x64 Release build, full owned-shell GUI including rapid invalid-then-valid
  navigation, rejected quoted `\\127.0.0.1\flyexplorer-f06-owned-no-share`
  with its previous right-pane listing and address preserved, normal app
  exit and owned scratch cleanup. An environment-only preflight found
  **zero** pre-existing approved `flyexplorer-owned-*` SMB shares under
  the central scratch root; no shares/permissions/network settings were
  created or changed.
- **Failure history:** [38380137080](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38380137080)
  proved the raw failed address incorrectly remained in the editor;
  [38380865307](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38380865307)
  exposed a rapid-navigation race after restoring the address in a
  later failed-result callback; [38381583006](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38381583006)
  stopped at a stale source assertion after moving the restoration to the
  Enter handler. These are diagnostic failures, not accepted PASS.
- **Still unverified:** opening a **reachable** approved SMB share,
  authentication/error-code variations on real UNC providers, F06-C
  matched before/after screenshots at 96 DPI and narrow/high-contrast,
  real 125/150/200% OS scaling and actual Narrator speech.
  The prior F06-C in-layout suggestion feature was already integrated
  and central main GUI-accepted at
  `da8613e95ab4ae0fefad2fce60860e5e2a487623`
  ([run 38378269180](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38378269180)).
  **VISUAL ACCEPTANCE: NOT TESTED** for these latest F06 states.

## 2026-10-13 F06-C bounded known-path address suggestions — focused acceptance

- **Exact accepted candidate:** `d9a440492592410ccaae232613288796fa500320`
  on `feat/f06-address-known-path-suggestions-20261013`, based on
  F06-A/B canonical main `1ebcc82f08fc6ee6ffc0748becc28265a9dcdaa5`.
- **Behavior:** keep the existing address TextBox and Ctrl+L/Enter/Escape
  contract. While typing a prefix, present up to 8 distinct filesystem-folder
  paths already held in live WindowTab/pane sessions and at most 2,048
  in-memory indexed entries for the active pane. Picking a candidate navigates
  the current pane's existing tab; Escape dismisses candidates. No filesystem,
  COM, provider, network, global settings, or private profile I/O occurs in
  the text-change handler; no unrequested persistence or background scan.
- **Lifecycle correction:** first UI experiment used a Popup and passed its
  candidate interaction checks but the process exited with access violation
  `0xC0000005` on [run 38376064497](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38376064497).
  A Popup-close guard still reproduced the teardown failure in
  [run 38376726015](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38376726015).
  The accepted source replaces Popup with a collapsed in-layout Border and
  defers foreign-focus dismissal through the UI dispatch queue. These two
  older Actions failures must not be labeled feature acceptance.
- **Focused Windows acceptance:** [run 38377574604](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38377574604)
  completed PASS for source contracts, WinUI x64 Release build, real
  in-memory candidate presentation, exact candidate navigation in the same
  PaneTab, Escape dismissal, normal product exit and owned scratch cleanup.
- **Remaining boundaries:** real network UNC share paste/open is NOT tested,
  candidate presentation when an unindexed folder is not known is not
  supported (intentionally), high-DPI 125/150/200%, High Contrast,
  Narrator speech and actual F06-C pixel/keyboard-focus visual acceptance
  remain unverified. Do not imply Explorer-wide autocomplete, OS-global
  filesystem completion, virtual-provider discovery or release approval.

## 2026-10-13 F06-A/B folder middle-click and quoted address — focused acceptance

- **Tested feature source:** `257bcc22c42ddb574712d8d69ba4e288c64e20b8`
  on `feat/f06-gestures-address-20261013`, based on canonical F01-D main.
- **New interaction:** middle-clicking a native filesystem folder row opens
  exactly that clicked folder in a new *same-pane* PaneTab, preserving the
  original tab and the other pane. Middle-click on a breadcrumb segment opens
  its tagged ancestor path in a new pane-local tab. Existing left-click,
  double-click, drag/drop, native Shell identity, active WindowTab and 32-tab
  cap remain unchanged. The new route is submitted only after the routed
  pointer event unwinds, with an original WindowTab/route identity guard
  against stale deferred actions.
- **Address input:** a pasted full path surrounded by double quotes (with
  optional outer whitespace) removes exactly the outer pair of quotes, leaving
  Unicode, inner spaces and UNC path separators intact. No arbitrary quote
  rewriting, OS-wide path setting or implicit remote network enumeration.
- **Evidence:** [central Remote Shell run 38364592231](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38364592231)
  completed PASS at the exact feature SHA: source checks, Windows x64
  Release build, owned actual WinUI middle-click folder and breadcrumb
  PaneTab isolation, quoted Korean path navigation, normal process exit,
  unchanged historical user profile and owned scratch cleanup.
- **Historical preacceptance failures:** [38363199512](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38363199512)
  failed the initial combined middle-click assertion; the separated
  [38363858966](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38363858966)
  confirmed folder middle-click tab creation but recorded a subsequent
  process crash during tab switching. The fix defers model/visual mutation
  until the pointer event returns, and the focused GUI subsequently passed.
  The predecessor runs are diagnostic failures, not accepted PASS evidence.
- **Scope still open:** actual reachable UNC-share paste/open behavior,
  address suggestions/autocomplete, middle-click on virtual Shell folders,
  125/150/200% OS scaling, accessibility speech and final visual
  before/after review (no new authored UI pixels in this feature unit).
  This is not broad Windows File Explorer parity or distribution approval.

## 2026-10-13 F01-D canonical main and focused restart GUI evidence

- **Integrated on canonical main:** product, tests and documentation at
  `91e3f5ab5e7cb2a6df5e3fa2d2becb453380668d`. The earlier F01-D
  candidate checkpoint below is historical branch-scoped evidence, not an
  assertion that persistence is still awaiting integration.
- **Central main GUI PASS:** [run 38353716100](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38353716100)
  completed successfully against the exact integrated main SHA. Policy and
  source checks, Windows x64 Release build, focused WindowTab/shortcut/filter
  tests and full functional GUI all passed; status context
  `central-ci/windows-gui` reported `success`.
- **Focused four-option restart test:** the isolated GUI fixture on
  `test/f01d-restart-view-options-20261013`, source
  `46bb16b5565e28baf5f5c19ea4467f8d88ebd2b9`, toggled all four
  View choices in the left pane and a distinct combination in the right,
  explicitly saved private session schema v3, restarted the owned app and
  inspected both restored View menus. The internal GUI log printed
  `F01D_REAL_RESTART_TWO_PANES_ALL_FOUR_VIEW_FLAGS=PASS`, alongside
  successful private-session cleanup; see [run 38359677323](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38359677323).
  **That outer Actions run is FAILURE**, not an accepted end-to-end workflow:
  its extra wrapper looked for this marker in the outer orchestration log
  instead of the inner scoped GUI log. The session GUI process returned
  exit code zero; the wrapper raised `F01D_GUI_MARKER_MISSING` afterwards.
  This is harness evidence, not a product or session GUI failure. Do not
  represent the failed outer workflow as a PASS.
- **Still open:** actual 125%, 150%, 200% OS display scaling,
  F01 High Contrast, real Narrator speech, virtual hidden namespaces,
  large indexed-directory behavior, and F01-D-specific restart pixel
  comparisons. No global Explorer setting or existing user file is changed.

## 2026-10-13 F01-D private session display option persistence — acceptance checkpoint

- **Verified candidate:** `feat/f01-display-session-20261013`,
  exact tested source `d537021a872b1ffe0ecb3572f6936b1a672d64c3`.
  This checkpoint records branch evidence, not automatic main integration.
- **Behavior:** Explicit Save Session stores four display-only View choices
  (selection checkboxes, compact rows, filename extensions, ordinary hidden
  items) independently for both panes of each WindowTab. A subsequent normal
  startup restores these choices only when a valid user-opted-in private
  session exists. No implicit session autosave, global Windows Explorer
  preference change, legacy MFC profile mutation, or file-attribute change.
  Newly created WindowTabs still receive the documented defaults.
- **Format:** `winui-session-v1.bin` remains the private bounded checksum
  file; schema 3 adds a strictly validated per-pane four-bit View mask.
  Existing schema 1/2 decoding is preserved and restores F01 defaults when
  prior files contain no display bits. Unknown schema-3 option bits are rejected.
- **Actual Windows acceptance:** [central Remote Shell run 38348701470](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38348701470)
  completed successfully against exactly the candidate SHA: source contracts,
  x64 Release build, 35/35 isolated owned native M23 checks (including new
  schema-v3, legacy-v2 and unknown-flag cases), existing session-focused
  functional GUI, and test-owned task/scratch cleanup PASS. The first two
  diagnostic runs 38348407801 and 38348555796 failed at the historical-MFC
  structure check because the temporary checkout lacked trusted Git-history
  access; the corrected run scoped Git safe.directory to the owned test source.
  Those diagnostic runs are not product PASS.
- **Not yet separately certified:** an actual per-option View-menu interaction
  followed by a second-process F01 option-state inspection on both panes/tabs.
  The existing GUI run verifies the prior session lifecycle, while the new
  option mask's save/load round trip was exercised in the native fixture.
  Actual 125/150/200% DPI, F01 High Contrast, Narrator spoken output, virtual
  hidden namespaces and large indexed hidden directory behavior remain open.
  **VISUAL ACCEPTANCE: NOT TESTED for F01-D-specific restart states.**

## 2026-10-13 F01-C ordinary hidden files/folders — merged and accepted

- **Canonical main integration:** [PR #65](https://github.com/tngkrwlsmd/flyExplorer/pull/65),
  squash commit `6e2814530886daa3014b4ac63eae3cc22e86c3b3`.
  The exact merged Git tree equals the feature source tree tested under
  `feat/f01-hidden-items-20261013`. No unverified product changes
  were added by the merge.
- **Feature:** View menu `숨김 항목 표시` (default OFF),
  independently per active pane and WindowTab in-memory. The isolated
  Shell helper uses `SHCONTF_INCLUDEHIDDEN` but never
  `SHCONTF_INCLUDESUPERHIDDEN`, while WinUI projects rows by
  `SFGAO_HIDDEN`. Native PIDL identity, filtering, sorting and
  selected file paths are unchanged. Windows global Explorer settings,
  registry and existing user file attributes remain untouched.
- **Verified Windows x64 Release + real light/dark GUI at 96 DPI:**
  [central run #38333769050](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38333769050),
  tested source `4e84b52ac1eb639408614007d1c7084ca1291887`,
  final docs-only branch commit
  `2ee3b13c116143c115e45be710299430e3d09653`.
  Source contracts, owned native hidden file/folder visibility,
  default OFF, left/right pane isolation, safe hidden-file
  deselection on hide and app exit all PASS. Eight actual 940x610
  app-owned light/dark Details screenshots were inspected:
  View flyout alignment/checkmark and before/after/restored rows PASS.
  Remote Shell ownership/proc/scratch cleanup PASS.
- **Not certified:** actual 125%, 150%, 200% Windows DPI; F01-C
  High Contrast; Narrator spoken output; virtual Shell hidden
  namespaces; large indexed hidden-file paging; hidden-state
  restoration after application restart. F01 settings/session
  persistence remains a separate unfinished logical unit.
  This is not full distribution acceptance.

## 2026-10-13 F01-A/B Explorer display options — merged and accepted

- **Merged canonical main source:** [PR #64](https://github.com/tngkrwlsmd/flyExplorer/pull/64),
  squash merge commit `0243181dd8833207ce91f1c6b7f819044e81e247`.
  Exact Git tree at this merge commit equals the feature/test tree verified
  immediately before integration. Do not confuse historical unmerged F01
  checkpoints with this newer main acceptance.
- **Accepted scope:** View menu selection checkboxes, compact Details/List
  row spacing, and display-only filename extension visibility. These are
  per active pane and per WindowTab in-memory; checkbox and compact default
  OFF, extensions default ON. File's original native Shell parsing identity,
  filtering, selection, transfers and accessible full filename remain intact.
- **Actual Windows x64 Release and focused GUI functional PASS:**
  [run #38318791974](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38318791974).
  **Actual matched BEFORE main / AFTER F01 light and dark pixel review PASS**
  at 96 DPI: [run #38326900487](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38326900487).
  **Physical keyboard View menu interaction, right/left pane isolation,
  Ctrl+T/Ctrl+Tab WindowTab state rehydration and inspected 800x570 native
  narrow-window pixels PASS:** [run #38328508589](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38328508589).
  Test-owned process, screenshot and task cleanup PASS, remote-shell slot idle.
- **Separate OPEN gates, not product PASS:** actual 125%, 150%, 200% OS DPI;
  F01-specific High Contrast composited pixels; real Narrator speech;
  other non-Details view layouts and further user interaction surfaces.
  F01 hidden-item enumeration and saved private preferences/session
  persistence are intentionally deferred work, not included in PR #64.
  Full distribution/release certification is not claimed.

## Current acceptance index (2026-10-12)

This is a current-state index over **revision- and environment-scoped** evidence,
not a new test run or an assertion that every later main commit has passed
every gate. Later evidence in this index supersedes older diagnostic
`NOT ACCEPTED` / `NOT TESTED` wording in the chronological sections below.

| Gate | Current evidence-scoped verdict |
| --- | --- |
| Named filter presets, blue/green/amber/red text and star/pin/flag/tag classification | **IMPLEMENTED**; functional Release/GUI [38198895107](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38198895107) |
| Styled filter light-theme pixels | **PASS** at actual 96 DPI (16 before/after captures, selection/focus), [38206845319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38206845319) |
| Styled filter High Contrast pixels | **PASS for tested blue/star and red/tag states** at actual 96 DPI, [38214474825](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38214474825); not every scheme or mode |
| Filter UI Automation row/badge semantics and physical-keyboard save | **PASS** in Release functional GUI, [38209842808](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38209842808) |
| Real Korean two-beolsik IME composition and durable WinUI filter save | **PASS** for `한글` on actual Windows, [38227421736](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38227421736) |
| Narrator spoken filter name/color/icon/selection and actual audio | **NOT VERIFIED / NOT ACCEPTED**; synthetic Speech Recap inspection did not confirm an utterance, [38233608351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38233608351) |
| Actual Windows display scaling at 125%, 150%, 200% | **NOT TESTED**; latest recorded desktop inventory was 96 DPI, [38218827761](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38218827761) |
| Public distribution/signing and production installation | **NOT CLEARED**; the [38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849) newer unsigned source/package identity audit was private and its temporary assets were removed |

The older entries below preserve their own dated observations; they do not
reopen an accepted IME gate or turn UIA/Narrator-launch evidence into real
spoken-output acceptance. See
[NARRATOR_SPEECH_VALIDATION.md](NARRATOR_SPEECH_VALIDATION.md) and
[PRE_DISTRIBUTION_FUNCTIONAL_GATES.md](PRE_DISTRIBUTION_FUNCTIONAL_GATES.md).

## 2026-10-12 Narrator Speech Recap follow-up: window visible, spoken phrase NOT VERIFIED

**Source and platform:** `flyExplorer/main` at
`9ee83045b3ab5beb185c291033382d8f52d0db4f`;
Windows 11 Pro build 26300, interactive session 2, synthetic test-only
Win32 reference controls. **No flyExplorer runtime or filter UI code changed.**

A second controlled investigation narrowed the previous false-negative
"zero Narrator UIA nodes" finding:
- [First window-discovery attempt #38232070285](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232070285)
  failed before GUI execution at an invalid PowerShell `New-Item -LiteralPath`
  argument. Its correction is a request-harness fix, not a product change.
- [Owned focus probe #38232212661](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232212661)
  confirmed that Narrator starts but initially takes foreground focus
  from a disposable Win32 reference editor. This invalidated any
  assumption that the original editor remained the focused speech item.
- [Foreground-corrected Speech Recap probe #38232530406](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232530406)
  returned reference foreground focus to the owned editor and confirmed
  **two** identified Recap-related visible windows and **35** scoped UIA
  nodes with zero UIA access errors. **No required reference phrase was
  found** in those nodes; no actual audio was captured. The outer
  workflow failed its shutdown precondition because a Narrator process
  remained active after the first shortcut.
- [Explicitly named native Button reference #38233608351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38233608351)
  first independently verified the button's true UIA accessible name
  (`NARRATOR_REFERENCE_BUTTON_UIA_NAME_MATCH=True`), confirmed owned
  foreground, launched Narrator, and identified a visible Recap window.
  Its **actual Recap phrase match was False** even with the named
  button and a `Narrator+Tab` reading command. This does not establish
  that Narrator never spoke the label; it establishes that the
  **available transcript collector cannot attest that utterance**.
  The workflow again failed the process-exit gate rather than a product
  assertion. Audio waveform and human hearing remain unverified.
- Recovery required more care than one stop shortcut. Windows ignored
  or did not complete some supported stop commands while Recap was
  active; a single guarded process stop was followed by a **new**
  Narrator process. [First safe recovery #38233281172](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38233281172)
  recovered an earlier fixture. [Final bounded exact-owned recovery
  #38234299929](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38234299929)
  established the process's recent creation, exact session and path,
  stopped only the two successive test-originated Narrator PIDs,
  verified stable **zero** Narrator processes and safely deleted the
  second exact-owned scratch fixture
  (`NARRATOR_FINAL_EXACT_OWNED_STATE_RESTORED=PASS`).
  **No process/task/test-owned files remain from this diagnostic.**

**Current gate verdict:** `NARRATOR SPOKEN FILTER NAME/COLOR/ICON/SELECTION =
NOT VERIFIED / NOT ACCEPTED`; `NARRATOR AUDIO PLAYBACK = NOT VERIFIED`.
The improved synthetic reference establishes process launch, focus
control and Recap window discoverability, **not** a correct Narrator
announcement in flyExplorer. Do not run repeated unattended speech
experiments on this shared session or treat an Actions source/workflow
PASS as spoken acceptance. Next: a separately attended Windows
session with an actual listening verifier, or a privacy-isolated,
independently verified audio/transcript capture method; use the
[manual speech checklist](NARRATOR_SPEECH_VALIDATION.md).
Actual OS 125/150/200% DPI remains a separate NOT TESTED gate.

## 2026-10-12 Narrator spoken-output validation: ENVIRONMENT BLOCKED (NOT ACCEPTED)

The current actual Windows VM environment was checked by the registered
control plane on **Windows 11 Pro build 26300**, interactive session 2,
at exact flyExplorer source `4d4db4680a75ec6368b8a50d6586608d1016fedd`.

- [Read-only inventory #38229681112](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38229681112):
  Narrator binary installed (file version 10.0.26100.8972), audio and endpoint
  services running, one functioning audio endpoint, exactly one signed-in
  interactive desktop session, and **zero** preexisting Narrator processes.
  These are prerequisites, not audible speech evidence.
- [Native test-owned reference attempt #38230127856](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230127856):
  a non-elevated direct `Narrator.exe` process launch returned Windows
  `WinError 740` (elevation required). No Narrator speech acceptance.
- [Supported-shortcut reference attempt #38230388533](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230388533):
  a disposable Win32 EDIT containing a synthetic classification phrase
  was focused in the logged-in desktop. Windows+Ctrl+Enter started a
  real Narrator process (`NARRATOR_SHORTCUT_LAUNCH_COUNT=1`,
  `NARRATOR_OWNED_LAUNCH_ACTIVE=True`). The probe attempted
  Narrator+Alt+X Speech Recap, but **no Narrator-owned accessible text
  nodes or confirmed reference utterances were observed**
  (`NARRATOR_OWNED_NARRATOR_UIA_NODE_COUNT=0`,
  `NARRATOR_OWNED_SPEECH_IN_UIA_RECAP=False`,
  `NARRATOR_SPEECH_RECAP_WINDOW_VISIBLE=False`).
  Audio playback was **not captured**. The wrapping workflow failed at
  non-elevated psutil's `AccessDenied` when waiting on Narrator's
  higher-integrity process. These are harness/permissions/evidence limits;
  **neither flyExplorer speech PASS nor product FAIL** can be inferred.
- [Independent state inventory #38230563415](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230563415)
  confirmed **zero** Narrator processes and **zero** residual diagnostic
  scheduled tasks after the attempted run. No Windows DPI/high-contrast,
  language-pack, audio device, or system Narrator option was changed
  by the diagnostic.
  [Safe exact-owned cleanup #38230906259](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230906259)
  subsequently removed the retained reference fixture after verifying
  absence of Narrator processes, active test tasks, links and owned
  Python workers (`NARRATOR_SPEECH_DIAG_SAFE_CLEANUP=PASS`).

**Acceptance:** `NARRATOR ACTUAL SPOKEN LABELS = NOT TESTED / NOT ACCEPTED`;
`NARRATOR AUDIO WAVEFORM = NOT CAPTURED`. The pre-existing successful
UIA labels/keyboard interaction tests remain independently valid.
The actual flyExplorer spoken filter rule name, color, badge/icon meaning
and selection announcement are **still awaiting an attended session
with audible monitoring or an independently verified, safely accessible
Speech Recap transcript**. Do not count a Narrator process launch,
audio endpoint, source CI or UIA name as real spoken-output acceptance.
Follow the reproducible, privacy-preserving procedure in
[`docs/development/NARRATOR_SPEECH_VALIDATION.md`](NARRATOR_SPEECH_VALIDATION.md).

**Separate open gate:** physical OS DPI 125%, 150%, 200%; earlier focused
96-DPI high-contrast pixel acceptance and Korean physical composition
remain accepted without unnecessary rerun.

## 2026-10-12 real Korean 2-beolsik composition: ACCEPTED

**Latest source:** `71a9c4ba0ae48c7ab5b247fe05878412ca2d8aa6`.
[Actual interactive Windows run 38227421736](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38227421736)
completed **SUCCESS**. The trusted source's Release build and owned
WinUI filter rule edit performed real Korean keyboard composition
(`한글`) and confirmed durable persistence to the test-owned filter
rule store. The app exited normally and the fixture was cleaned.
The same run first proved composed Hangul in a disposable native
Win32 EDIT control, then ran the actual WinUI acceptance.

**Confirmed root cause of the previous false-negative IME tests:**
pywinauto `keyboard.send_keys` defaults to `vk_packet=True` for
text characters, which injects Unicode packets rather than actual
virtual-key input traversing Korean IME composition. The test-only
revision switched the Korean Latin key sequence to
`vk_packet=False` in both native and WinUI tests. The native
reference now uses `WM_GETTEXT` for cross-process readback and
records owned-process input-context state, rather than falsely
interpreting remote `GetWindowTextW` / remote `ImmGetContext` as
evidence of product failure. No flyExplorer runtime/XAML/filter
rendering code changed. This supersedes the earlier
`NOT ACCEPTED` Korean composition notes below; those remain as
historical diagnostic evidence only.

**Still open and separate:** actual OS 125/150/200% scaling, clipping,
overlap and spoken Narrator output. The VM currently reports
1024x768 in the active desktop with 96 DPI, and the accepted
real High Contrast filter visual check is unchanged. Do not infer
DPI/Narrator acceptance from the successful IME test.

## 2026-10-12 corrected Korean IME reference diagnostic (latest)

**Test-only diagnostic revision:** `95af8d7b54ab0a7730b0d545db068e087c5fa7c9`.
[Exact-source central CI 38224982434](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38224982434)
completed **SUCCESS** for the source checks. The three intervening
commits since `9fda657` modified only
`tests/winui/test_windows_korean_ime_host_baseline.py` and
`tools/winui/run_owned_korean_ime_host_baseline.ps1`, not WinUI/product
rendering or runtime files. This source result is **not** new Release,
functional GUI, or final-pixel acceptance.

**Corrected actual native Win32 EDIT input baseline: numeric physical
keyboard delivery PASS, Korean composition NOT ACCEPTED.**
[Windows owned diagnostic 38224718703](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38224718703)
replaced the invalid cross-process `GetWindowTextW` edit read with
`WM_GETTEXT` and verified an explicit `WM_SETTEXT` / `WM_GETTEXT`
round trip. The real EDIT then received physical digits `123`
correctly. Korean HKL was `0x04120412`, yet both the physical Hangul
key attempt and native-IMM fallback yielded Latin `gksrmf`, **not**
composed `한글`. Therefore the previous native result reporting an
empty EDIT value was a test readback artifact and is superseded. A null
IMM context requested by the external controller is not proof of the
target application's Text Services Framework or actual IME mode.
Both the earlier owned WinUI and corrected native-reference attempts
lack real two-beolsik composition; there is no accepted Hangul
composition/save result and no isolated flyExplorer product defect.

The diagnostic itself completed with its expected evidence markers;
the enclosing Remote Shell run is marked **failure** because its
post-diagnostic report matcher wrongly required extra quote characters
around a marker. Do not turn that reporting error into a product FAIL
or claim the whole Actions run succeeded.
[Owned cleanup 38224957696](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38224957696)
independently verified and deleted the test-owned scratch root;
the central Remote Shell request slot was subsequently restored idle.

**Unchanged open environmental gates:** real 125%/150%/200% Windows DPI
clipping/overlap and spoken Narrator behavior remain **NOT TESTED**.
The relevant actual 96-DPI Windows High Contrast filter pixel review
[38214474825](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38214474825)
remains the accepted focused evidence; it was not rerun because no
product-visible filter code changed.

## 2026-10-12 actual accessibility environment diagnostics (no scale changes)

**Read-only Windows capability inventory: PASS.**
[Run 38218827761](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38218827761)
reported a single interactive Windows Explorer session (2),
1024x768 desktop at **96 DPI**, no per-monitor override entries,
`Win8DpiScaling=0`, and installed Narrator executable plus Korean IME
DLL. **125%, 150%, 200% real OS DPI remain NOT TESTED**: no scaling
change/re-login was attempted because that would modify the shared
interactive desktop without an established, verified recovery path.
Narrator being installed does **not** certify spoken output; **Narrator
speech remains NOT TESTED**. The previously accepted real High Contrast
pixels ([run 38214474825](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38214474825))
were not redundantly rerun, and HC remains in its original OFF state.

**Real Korean two-beolsik composition: NOT ACCEPTED.**
[Owned WinUI IME test 38219262419](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38219262419)
rebuilt the unchanged product and confirmed Korean HKL
`0x04120412`, but its actual focused input HWND differed from the
top-level app HWND, `ImmGetContext` returned no context on that
focused HWND, and physical Hangul-key/right-Alt attempts both entered
Latin `gksrmf` instead of composed `한글`. A third IMM-native
method could not be attempted without a valid IMM context.
This does **not** independently identify a product defect: modern
WinUI may use Text Services Framework rather than a Win32 HIMC.
The test-only diagnostic now records focus HWND, IMM open/conversion
status if present and restores the owned layout and any prior IMM state.

[Owned native Win32 EDIT comparison 38220744083](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38220744083)
completed its **diagnostic workflow**, but returned
`KOREAN_IME_NATIVE_EDIT_COMPOSED=False`, no IMM context and an
**empty input value** after the attempted keys. Since keyboard
delivery to the native EDIT was not separately proven, this is
**inconclusive** as a control comparison and must not be presented as
a native IME or product PASS/FAIL conclusion. The earlier native
comparison attempts failed at test-only focus and EDIT-clear API
preconditions and were corrected; none established successful Hangul
composition. **A real Korean 2-beolsik composition and durable-save
acceptance is still required** on a known working foreground
keyboard/TSF environment, preferably with a proven reference editor.

All test execution was restricted to synthetic data and owned app
windows. [Owned cleanup run 38221028916](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38221028916)
succeeded after exact source, result-stage, link and active-process
checks. The registered Remote Shell request slot was restored to idle.
No product runtime/pixel code, desktop DPI setting or deferred staged
Copy interruption/safe-recovery logic was modified by this
diagnostic round.

## 2026-10-12 high-contrast filter acceptance and remaining IME/DPI/Narrator limits

[Exact-revision Windows High Contrast run 38214474825](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38214474825)
completed **SUCCESS** and logged `HC_FILTER_STATUS=PASS
STAGE=complete`, `HC_FILTER_FOUR_STYLES_ACTUAL_PIXELS=PASS`,
`HC_FILTER_OWNED_CLEANUP=PASS`. This compared actual pre/post WinUI
Release screenshots in the real Windows high-contrast scheme for
blue/star and red/tag classifications. The four bounded PNG images
are in that run log. Direct review found legible text, intact
classification badges, visible selected-row indication, yellow focus
borders and no new clipping/overlap. The real Windows high-contrast
setting was restored to its original **OFF** state after capture.
This is a focused visual acceptance, **not** a blanket certification
of every high-contrast scheme or file-view mode.

**Korean IME physical composition: NOT ACCEPTED.** The same run explicitly
reported `IME=NOT_ACCEPTED`. UI Automation typing, Korean-labeled
controls and persisted Unicode text alone cannot substitute for
observing real 2-beolsik composition in the owned edit control.
Do not claim IME PASS without the precise physical-composition marker.
**Narrator speech: NOT TESTED**; accessible UIA names do not prove
actual spoken output. Actual **125%, 150%, 200% OS DPI: NOT TESTED**;
the registered desktop last reported 96 DPI and no independent
high-scale screenshot evidence is available. These are separate
remaining accessibility gates.

## 2026-10-12 filter accessibility and updated private source/setup identity

**Actual Windows DPI capability:** [read-only inventory #38209100479](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38209100479)
reported active 1024x768 desktop at **96 DPI**. Actual OS
125/150/200% displays were unavailable here; these gates remain
**NOT TESTED**, not simulated or accepted. Previous light/dark 96-DPI
visual acceptance remains valid for the tested states only.

**Accessible filter metadata + physical keyboard: PASS (UI Automation).**
The product gives each matched file row an accessible preset name,
color name and icon category, and the badge an identifiable category
name instead of a generic icon announcement. Filter palette selection
and Save can be operated through owned physical keyboard input.
[Central CI #38209842808](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38209842808)
completed **SUCCESS**, Release, WindowTab, shortcuts, focused filter GUI,
and entire GUI, exact compiled product source
`8902d494255b471911f092c3cdd4e978af2c4e56`.
The earlier #38209461852 passed the Release build but hit a transient
WindowTab UIA peer-rebinding assertion before filter GUI; the test-only
limited wait fixed the pre-input race. Source-only filter contracts
also require named badges/rows. **Human Narrator speech** and
**Korean IME** were not directly exercised; UIA property checks alone
do not certify screen-reader audio.

**Unsigned private package/source equivalence: PASS, no deployment.**
[Exact-source owned audit #38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849)
clean-built a private Release from
`2a736d85b22859a770138e4b50926ac125d1a052`, regenerated and
checked runtime provenance, built an unsigned native setup, generated
and checked the deterministic **438 tracked file** source ZIP, and
verified `release_identity.py --write` / `--check` binds them to
the identical SHA/tree. Recorded private test evidence:
- source tree `df09334367d2a2be1ea0541548f5aaa73b1d53e5`;
- source ZIP SHA-256
  `b08f01ad41b5c211282848c438c138e0587986a614ac8ebf4c8e839231dba01d`;
- **305** runtime files, manifest SHA-256
  `fb509b3f6a40ad962c18e10fcd323dab2e195df64884be7430d12304f59f25c7`;
- unsigned private setup **124,418,560 bytes**, SHA-256
  `3861b937b122e7d997fe92d778798631f02b952228b9d0707de72b150aa9da37`.

The audit explicitly retained **private-evidence-only**, **not-cleared**
and **unsigned** states. It did not install into Program Files,
register HKLM, sign, publish, create a release tag or touch user
settings. It deleted the private work directory and generated files
after verifying them. The **tracked** release identity and source
manifest still refer to historical source `bc63c8b...`; they remain
valid archival evidence, **not current release assets**. The new SHA
and hashes are preserved in the Actions run log but the new setup/ZIP
are not durably published or downloadable. A production build must
retain and review fresh matching binary/source assets and re-run
install/update/rollback, signing, clean-machine and public GPL source
delivery gates. This is an engineering identity acceptance, **not**
public distribution clearance.

User-deferred staged Copy interruption logging and safe recovery were
not changed.

## 2026-10-12 run.bat launcher and styled filter presets

**Canonical real-launch verification: PASS.**
[Remote Windows run 38198360371](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38198360371)
reused an already completed exact-revision Release binary at
`4d8c83f2ca80d7642d79f326a638ebebf8d049b5` to invoke
`run.bat Release <test-owned Unicode folder>`, rather than launching
the executable directly. It confirmed launcher exit 0, both pane UIA
controls and the Korean-named file row, and graceful shutdown of the
owned app with exit 0. Two earlier timed-out, exact-test-owned processes
were identified by executable path/fixture argument and closed, followed
by owned workspace cleanup. Initial launcher checks were blocked by
test-harness subprocess PIPE inheritance, not a product runtime failure;
the permanent harness fix is `tests/winui/test_run_bat_release_gui.py`
in `a4e7d74026f72030a78895ba4463ee3ae4bc9307`.

**Filter preset color/icon feature: Release + functional GUI PASS.**
Product revision `18a4859ce8fc40101ff746dc5b651b6cfd98b028`
adds opt-in color palette (default/blue/green/amber/red), secondary
classification badge (none/star/pin/flag/tag), deterministic first
matching styled-rule rendering across file view modes, and per-rule
bounded private style metadata. Existing Shell icons, mask filtering,
20-rule limit and legacy v1 filter files are preserved; style-bearing
files use backwards-readable-by-new-product schema 2, rejecting invalid
style bytes without replacing the loaded model. Older application
versions are **not** claimed to read new schema 2 style files.

[Exact-revision central Windows GUI run 38198895107](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38198895107)
completed **SUCCESS** and set `central-ci/windows-gui=success`:
Release build PASS, `gui-window-tabs-Release` EXIT=0,
`gui-shortcuts-Release` EXIT=0,
`gui-filter-preset-Release` EXIT=0 (5.9 s),
`gui-all-Release` EXIT=0 (118.7 s) and functional GUI PASS.
The focused filter test checked style selection, schema 2 write/reload,
visible row badge, mask application, restart persistence, deletion,
unmodified legacy settings, and normal process exit. Early failed runs
38198500380 and 38198626453 isolated a stale test-orchestrator contract
and a single malformed C++ count guard respectively; both were fixed
before the accepted run.

**Additional M20 Release native acceptance: 52/52 PASS.**
[Remote Windows run 38202520450](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38202520450)
checked out that same product revision under a disposable short Windows
workspace in the registered interactive session, passed five focused
source contract tests, built the M20 Release native executable and
confirmed `M20_STANDALONE_NATIVE_Release_52_PASS True`. The original six
legacy user-profile sentinels were unchanged. The test-owned task and
workspace were removed. Nonblocking C4005 WIN32_LEAN_AND_MEAN warnings
were observed in the M20 fixture.

**Filter color/icon visual acceptance: PASS (matched actual WinUI, dark/96 DPI).**
[Remote Windows visual run 38204943981](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38204943981)
completed with `FILTER_VISUAL_RUN_STATUS=PASS STAGE=complete`,
`FILTER_VISUAL_CAPTURE_PAIR=PASS`, and
`FILTER_VISUAL_OWNED_CLEANUP=PASS`. The actual before/after Release
product screenshots were captured with
`tests/winui/test_filter_style_visual_capture_gui.py` and directly
inspected from the run's bounded PNG previews. The pre-feature binary
was built from
`4d8c83f2ca80d7642d79f326a638ebebf8d049b5`;
the changed binary was clean-built from
`885f318b4959efaff2070dcad96252f689680b2b`
(identical product implementation to accepted `18a4859`; subsequent
commits only changed tests, orchestration or documentation).

Both real windows were on the same registered interactive Windows desktop,
with an isolated dark/details profile, 96 DPI, actual app bounds
`(20,15)-(1080,735)` (1060 x 720), and a 1060 x 680 pixel top preview.
Both used the same synthetic four-file fixture:
`alpha.cpp`, `beta.h`, `notes.txt`, and `사진.JPG`.
The random owned fixture folder name displayed in each breadcrumb
naturally differs between captures. The before screenshot showed the
original filter preset mask editor without color/icon controls. The
after screenshot shows the new blue color and star badge selectors,
with all controls visible, readable and aligned without overlap.
`alpha.cpp` and `beta.h` receive readable blue filenames and
adjacent outline star badges, while their real Windows Shell file icons
remain intact; `notes.txt` and `사진.JPG` retain the normal
appearance. The file-list top edge moves down to accommodate the
additional style controls, as intended. Some unrelated type labels
were already ellipsized within the narrow columns in both screenshots;
this was not introduced by the feature. No blocking visual regression
was observed in the changed editor/file-row region.

**Failure isolation and recovery evidence:** The first [visual run
38203734728](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38203734728)
built the baseline but had used a fixed window taller than the active
desktop. The next [run
38204124635](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38204124635)
used viewport-bounded geometry but treated a transient status line as
part of durable preset-save verification; the harness now validates
the isolated saved file and schema instead. Subsequent resume attempts
identified a shallow Git revision limit and a changed app process that
exited before showing a window when the two versions reused one
incremental Release output directory. The successful run preserved
the already captured baseline pixels, used exact-SHA checkout, and
ran `clean.bat build` only in its disposable workspace before a
complete current Release build; it then confirmed the current app
opened, displayed the styled rows and exited normally. The evidence
supports clean-output isolation, without establishing an independent
root cause for the earlier startup exit. The separate first failed
test-owned scratch directory was verified and safely deleted in
[cleanup run 38205260341](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38205260341).
The Remote Shell request slot was restored to idle.

**Scope limit:** this is a focused visual PASS for 96 DPI dark/details
layout. Separate real 125/150/200% DPI, High Contrast themes,
Narrator/IME and full distribution visual states remain **NOT TESTED**
unless independently accepted elsewhere. Functional GUI and M20
native acceptance remain distinct, previously verified gates.
Staged Copy crash-interruption receipt and safe-recovery work remain
explicitly deferred and were not changed.

## 2026-10-12 light-theme filter visual acceptance — PASS

Product commit `bddfb2a46faea8f30f78fb96f737da63da2f2e23`
adds theme-aware, darker light accents while preserving the accepted
dark accents, style IDs and badges. White-background contrast improves
from 2.35/2.04/1.74/2.61:1 to **7.62/7.38/6.75/7.65:1** for
blue/green/amber/red, exceeding the 4.5:1 normal-text AA reference.

[Actual Windows visual run 38206845319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38206845319)
**PASS**: 16 real app screenshots comparing before
`c911f982464cf714387b98e303ec7ac82f0462a1` and after
`b9d55954f9eecbf063122f9934f82c42029da6fd`.
Matched light/details, 96 DPI, 1060x720 actual HWND and synthetic
four-file fixture. Reviewed all four color/icon combinations (star,
pin, flag, tag) in normal and UIA-verified selected/keyboard-focused
states. The darker names and badges remain readable, aligned and
unclipped; the selected-row highlight is distinguishable.
Selected-row contrast was reviewed visually, not measured numerically.
Run confirms normal owned app exit and fixture cleanup. An initial
test-only harness mistake in run 38206423123 was fixed by comparing
the same existing color controls in both product revisions.

[Central Windows CI 38207189902](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38207189902)
**SUCCESS** for exact `b9d55954f9eecbf063122f9934f82c42029da6fd`:
Release, window tabs, shortcuts, styled filter GUI and full GUI
regression all exited 0; `central-ci/windows-gui=success`.
The source contract checks all four light-theme contrast values.

**Separate, NOT TESTED:** 125/150/200% actual OS DPI, High Contrast,
Narrator and Korean IME. Staged Copy interruption receipts and
safe recovery remain deferred.

## 2026-10-12 configurable focus shortcut expansion — Release and functional GUI PASS

Product revision `04e7d358dcc7cb74a6c619b833b503c72b089294`
adds Ctrl+G and Ctrl+J as opt-in focus-only bindings for the address bar
and quick search. Existing Ctrl+L/E/F/K choices, non-duplicate selection,
private schema-3 persistence, defaults, F5/F6 and mutating file-operation
shortcuts remain unchanged. The test-owned focused keyboard GUI regression
covers persistence, duplicate rejection, actual Ctrl+G/J input, reset,
no cross-pane file mutation and protected legacy-profile preservation.

**Accepted exact-main central Windows run:**
[38189416302](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38189416302),
registered `desktop-a`, `scope=gui`, source SHA
`3c46c116786038fbea2914e1873fc3600611753c`.
This main SHA differs from the product revision only by this status
document. GitHub Actions completed **success** and published
`central-ci/windows-gui=success` for the exact main SHA. Recorded stages:

- Registered policy/source checks: PASS as prerequisites to the succeeding
  Release and functional-GUI stages.
- Canonical Windows Release build: PASS.
- `gui-window-tabs-Release`: EXIT=0 (15.9 s).
- `gui-shortcuts-Release`: EXIT=0 (11.0 s); physically delivered shortcut
  regression, including the new configurable Ctrl+G/J choices.
- `gui-all-Release`: EXIT=0 (121.7 s), followed by
  `PASS functional-gui`.

**Earlier failure now resolved by changed execution conditions:**
Central [run 38185317718](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38185317718)
built the same product revision successfully, then stopped on the first
focus acquisition of its prerequisite Window Tabs test,
`test_v7_window_tabs_gui.py:30` ->
`test_shell_gui.py:112`. The foreground-ownership safety guard correctly
refused physical input. The exact traceback was inspected in
[run 38185956218](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38185956218).
A read-only session inventory in
[run 38186404331](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38186404331)
found Explorer in disconnected session 2. A subsequent session check,
[run 38189322684](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38189322684),
reported session 2 **Active**. That diagnostic workflow itself exited
nonzero, but its session output established the changed precondition.
The successful 38189416302 acceptance followed without bypassing the
physical-input safety check or modifying the shortcut product code.

**Supplementary exact-main native evidence:**
[Remote Shell 38193974521](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38193974521)
ran a bounded, temporary interactive-user task against exact main
`9631d1d3f74473f1bae3df8d0f39717d24754139`. The focused shortcut
contract and preferences-coordinator contract passed, M21 Release native
C++ compilation passed, and `M21_NATIVE_Release_23_PASS True` verified
**23/23 cases PASS**. The original six protected legacy user-profile values
were unchanged (`M21_LEGACY_USER_PROFILE_SENTINEL_UNCHANGED True PRESENT 6`).
The run completed successfully, removed its test-owned workspace and task,
and restored the central Remote Shell request slot to idle. It did not
rebuild or rerun the already accepted full GUI. Non-blocking C4005
`WIN32_LEAN_AND_MEAN` macro redefinition warnings were reported by the
native fixture build; no compile or runtime errors occurred.

The earlier SYSTEM Remote Shell preflight
[38186627928](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38186627928)
had verified the source SHA but could not launch the fixture because
`python.exe` was not on the SYSTEM PATH. The new successful task ran in
the established Explorer user session instead, without elevating a
user-writable Python interpreter to SYSTEM.

**Shortcut editor matched visual acceptance: PASS (focused 96-DPI dark UI).**
In Windows [visual run 38196377101](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38196377101),
the test-owned screenshot harness completed with
`VISUAL_WORKER_STATUS=PASS STAGE=complete`,
`VISUAL_OWNED_CAPTURE_PAIR=PASS` and a successful one-shot interactive
Windows task. It built and actually launched the Release product at
pre-feature baseline `54c8ee5d2ccf8912232334348c58f8fe60313294`
and post-feature `6b2e3fca184b56f24885e1d1ec26970217d9cf46`.
These differ in product behavior at `04e7d358`; subsequent commits up
through the captured candidate change only documentation/test harness.
The matched screenshots used the same disposable private profile,
synthetic Korean-named file, session, dark appearance, 96 DPI, desktop,
and app window at (40,30)-(1140,710), size 1100 x 680 pixels.
Both collapsed and expanded shortcut dropdown states were captured in
each actual WinUI app, with geometry/DPI equality checked.

**Direct pixel review of the two 614 x 378 expanded screenshot previews:**
the earlier address dropdown exposes Ctrl+L/E/F/K, whereas the new one
exposes Ctrl+L/E/F/K/G/J. Both added entries are fully visible inside the
popup, aligned with original rows at consistent spacing; no unintended
overlap, new text clipping, unreadable contrast, or broken popup edge
was observed in this changed control region. The right edge of the
**preview crop** truncates part of the unrelated Reset label; this is
the preview boundary, not evidence of an actual clipped product control.
The visual PASS applies to this matched shortcut-editor change and
theme/scale only. Full-window pixel review, separate real 125/150/200%
DPI, screen-reader/human IME and broader distribution environments
are **NOT TESTED**, unless independently accepted elsewhere.

**Visual build infrastructure defect resolved:** A previous attempted
[visual run 38194421915](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38194421915)
failed in the baseline Release NuGet restore before UI launch: the
isolated scratch workspace made Windows App SDK WinMD and NuGet HTTP
cache paths **261 characters long**, exceeding the usual 260-character
Windows MAX_PATH boundary. Read-only
[HTTP diagnostics 38196231801](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38196231801)
confirmed NuGet index and two pinned package endpoints returned HTTP 200.
The successful successor shortened only the disposable Windows scratch
root to `C:\\ProgramData\\personal-control-plane\\scratch\\v-<12hex>`,
bringing the known WinMD path to **220 characters**, without modifying
product code, changing package versions or bypassing restore verification.
The previous failed fixture was disposed by
[cleanup 38194622497](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38194622497).
Run #38196377101 cleaned its own success workspace and task. The central
Remote Shell request was restored to idle with a skip-CI commit.

Capture tool: `tests/winui/test_shortcut_visual_capture_gui.py`.
The bounded expanded previews are preserved in the visual-run Actions
log as base64-encoded PNG for source-specific review; temporary full
window screenshots were deleted with the owned success workspace.
Do not treat a CI screenshot marker by itself as visual acceptance:
the images were directly inspected before recording the focused PASS.

Staged Copy crash-interruption receipt and safe-recovery work remain
explicitly deferred and were not changed.

## Latest product acceptance checkpoint (verified 2026-10-12)

The latest product-bearing main revision before this documentation-only change,
`f37fddae0ef08461c3f01f90928da9b3bf077c46`, has
`central-ci/windows-gui=success` pointing to central registered CI
[run #38120723040](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38120723040).
This is registered Release/functional GUI evidence for that exact product
revision, not Debug, final-pixel visual, external-device or
public-distribution acceptance.
The focused read-only stage-identity native evidence below belongs to its
separately recorded source candidate. For later main commits, recheck the
live SHA, producing central status/run and affected test boundaries; do not
automatically relabel older candidate or pre-main PASS records as current
acceptance. Documentation-only revisions do not invalidate an unchanged
product build/runtime boundary.

## 2026-10-11 exact staged Copy file-ID read-only validation

An isolated source candidate `e8870beada07ad9bf43a80f299a7aa189333e16f`
added a read-only `inspectStageFile` / `sameStageFile` API in
`src/base/shell_transfer_core.{h,cpp}`. It queries Windows
`FileIdInfo` identity for **one explicitly supplied** fixed-drive
staged-Copy path using a no-reparse-point-opening handle. It fails
closed on unexpected leaf naming, normalized-path discrepancies, directory
junctions/reparse points, multiple hard links and missing identities.

Owned Windows Remote Shell
[run #38120473011](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38120473011)
completed SUCCESS: focused source contracts and Release M22 native
**44/44** including stable identity, same-path replacement detection,
hardlink refusal and invalid-path refusal; protected legacy MFC
settings 6/6 unchanged.

**Not production orphan cleanup:** This is a read-only identity building
block. A valid GUID-shaped file path and file ID do not establish
provenance. There is no durable creator receipt, no user-authorized
recovery UI and no product automatic deletion of orphan stages.
See `docs/development/STAGED_COPY_RECOVERY.md`.

## 2026-10-11 live ACL, folder, Move and orphan safety checkpoint

The production staged Copy implementation remains unchanged from main
`cf854ca5b8f710dcd041d58806494b3c967f65d9`, whose independent
Release and full GUI acceptance passed in central run
[38117504286](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38117504286).
The additional regression changes are test-only and do not turn Shell
folder/Move operations into a transaction.

Exact test candidate `ee6a3173b4b5b930e22a7bafe4864e7be3f14be8`
passed owned Windows
[run 38119197158](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38119197158):
Release native 40/40 and focused contracts PASS. A 512 MiB staged local
Copy had already written >=4 MiB before the ACL of its test-owned target
folder changed; the process remained active after the ACL modification.
Its source SHA-256 stayed unchanged and any published target had complete,
verified bytes (otherwise no target). Windows may retain write rights for
existing open handles, so this does not imply an ACL change must interrupt
an active transfer. Recursive folder Copy with an exclusively locked
nested child reported failure while preserving both original children and
without detecting malformed destination child bytes. Folder preflight
cancellation preserved the whole source and created no destination.

Exact subsequent test candidate
`07494976381afc1a24f68652f05a3a9150b52a60`
passed owned Windows
[run 38119379826](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38119379826),
repeating all above checks and adding:
- Test-owned destination ACL denial for Shell Move: error reported,
  original source contents preserved and no target created.
- Forced termination of only the owned Copy fixture, followed by
  explicit reclamation of only the observed temporary stage after
  checking its exact pre-kill path, same NTFS file identity
  (`st_dev`/`st_ino`), single hard-link, no symlink, and its known
  fixture parent. A separate same-pattern partial file was preserved.
- Six protected original legacy MFC profile values remained unchanged.

**Production crash recovery remains deliberately fail-closed**:
the app has no durable stage-ownership receipt (path + stable file ID +
operation identity), so it must not automatically delete any candidate
just because its name matches `.flyExplorer-copy-*.partial`. Test-only
reclamation is not a user-folder cleanup implementation. A future
recoverer must establish durable provenance, closed/abandoned worker,
same file identity, no reparse traversal and scoped user authorization.
See `docs/development/STAGED_COPY_RECOVERY.md` for the recovery contract.

Still OPEN: production crash-restart ownership receipts and safe optional
recovery UI, repeatable in-flight ACL changes that revoke *previously
opened* access, cross-volume/remote Move and folder interruption,
power-loss safety and broader third-party Shell/USB/SMB acceptance.

## 2026-10-11 staged Copy publish and access-denial acceptance

Product PR [#59](https://github.com/tngkrwlsmd/flyExplorer/pull/59)
was squash-merged as `cf854ca5b8f710dcd041d58806494b3c967f65d9`.
Independent Windows registered central CI
[run #38117504286](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38117504286)
with `project_id=desktop-a`, the exact product SHA and `scope=gui`
completed **SUCCESS**, including `PASS release-build`,
`gui-all-Release EXIT=0` and `PASS functional-gui`.
The source branch was subsequently removed.

The accepted local regular-file fixed-drive Copy with collision Reject
writes to a unique sibling `.flyExplorer-copy-{GUID}.partial` stage and
publishes with a no-replace same-directory rename only after the copy
finishes without observed cancellation. Filesystem folder/provider, Move,
KeepBoth, removable/UNC and Recycle continue through their distinct
existing Shell paths. This is not a cross-item transaction, and does not
guarantee power-loss durability or preservation of every Windows metadata
feature under all device/provider conditions.

[Native run #38115218901](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38115218901)
on exact source candidate `618c6e61ed9faaab343e04e6b1ad4bdacfa731b9`:
14 source contracts PASS, 38 Release native cases PASS, a 512 MiB
mid-copy cancellation and force-killed test-owned copy worker produced no
published final file, and original SHA-256 remained unchanged.
[Owned Release/GUI run #38115309861](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38115309861)
passed the application build and interactive two-item partial-failure
flow, including failure notice and pane refresh. `git diff --check`
passed in [run #38117403266](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38117403266).

An additional test-only candidate `9482f7c3badd91488912b4500da0630b8ae8e66c`
passed owned Windows
[run #38118314980](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38118314980).
It tested a destination file created during staging (existing target
bytes preserved), preservation of a pre-existing unrelated `.partial`
file, write-denied ACL on a uniquely owned destination folder (source
bytes unchanged; no final destination), the earlier cancel/kill cases,
and the six legacy MFC config sentinels. Test-only ACL changes were
reverted before deleting the disposable fixture.

**Still not certified:** changing ACLs after a destination write handle
was opened; orphan-stage recovery after process crash (no automatic
cleanup of unverified files); Move/folder transactionality; real
removable drive/SMB outage; system crash/power-loss durability. Do not
automatically sweep files by `.partial` naming pattern alone.

## 2026-10-11 file-transfer integrity checkpoint

PR [#58](https://github.com/tngkrwlsmd/flyExplorer/pull/58) was squash-merged
as product commit `a7308c1ad35ff7889a822add0dd0803bc92a0f2c`.
Independent central Windows CI
[run #38111030089](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38111030089)
for registered project `desktop-a`, exact SHA and scope `gui` completed
**SUCCESS**: `release-build=PASS` and `gui-all-Release EXIT=0`
(`functional-gui=PASS`). This certifies Release and functional GUI
regression for the merged product revision, not final pixel-visual acceptance.

The preceding exact candidate `048c1b7d7f77e17e5e4ce0f40ad77841266cd7e4`
passed the owned Windows Release and partial-transfer GUI probe in
[run #38109058002](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38109058002):
a two-item Copy committed the first file, an exclusive file lock blocked
the second, both source byte sequences remained intact, the destination
pane reflected the committed item, and the partial-failure warning stayed
visible after asynchronous folder refresh. Related native Release tests
passed 37/37 in
[run #38106603515](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38106603515),
including locked two-item Copy and Move. Final candidate
`git diff --check` passed in
[run #38109308352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38109308352).

The implemented fixes propagate per-item Shell transfer failures, refresh
visible touched folders on failed/canceled batches, preserve the partial
failure notice during async navigation refresh, and activate the file pane
when new items are selected. **Shell IFileOperation batches are not
transactional.** These checks do not establish all-or-nothing rollback,
cleanup of partially written destination files on forced process termination,
permission changes during transfer, or real external USB/SMB disconnection
recovery. Those remain independent file-integrity gates.

## Windows ownership and acceptance-evidence baseline (2026-10-10)

The 2026-10-10 main snapshot `6ab2791ae1991f3750fa754c2c2d7015aef01950`
retired the flyExplorer-specific Windows Runner, `control/remote-shell`
branch and source-repository Windows Actions workflows; the sanitized
`evidence/remote-windows` historical branch remains preserved. Windows
development now uses `tngkrwlsmd/personal-control-plane` Remote Shell
(target `windows-vm`). Independent acceptance requires manual
`central-flyexplorer-ci.yml` with `project_id=desktop-a`, an exact
40-character SHA reachable from `flyExplorer/main`, and explicit
`health|source|release|gui|gui-probe` scope. A normal main push does not
trigger Windows validation. See `docs/operations/windows-runner-retirement.md`
and `docs/development/VERIFICATION_PROFILE.md`.

### 2026-10-10 functional pre-distribution checkpoint

Exact source SHA `a310951872ee5ddb720966498510605f8aea4b6e`:
central registered source run `38044463555` completed SUCCESS (policy,
4 structure, 152 product, 20 harness, 30 infrastructure tests, all PASS).
Remote Shell `38044362154` separately proved the real Windows
`fly.bat` help/invalid-option and `run.bat` missing-build guards.
Its subsequent source check failed *before running Python tests* because
the SYSTEM runner lacked `python` on PATH; the central user-session
source run then passed those contracts. The test-owned checkout was
reclaimed. The VM exposes 0 removable drives, 0 mapped network drives
and 0 non-special SMB shares, so real USB/remote SMB acceptance is
NOT TESTED, not a product failure. Central `gui` run `38044629405` subsequently completed **SUCCESS**:
the Release build and `gui-all-Release` functional GUI passed on
that exact source SHA. Matched final-pixel review remains separate.

A later feature candidate `f3d06ff9463f1b462ca3fb1c30675bd6dd742b12`
added Ctrl+L focus for the address editor and Ctrl+F focus for
quick search, plus an intended physical-keyboard regression.
Its central registered `gui` run `38047230115` completed **FAILURE**
despite `release-build=PASS`: the existing `gui-all-Release` suite
stopped inside `test_v7_window_tabs_gui.py` before reaching the new
shortcut regression, reporting
`AssertionError: cleanup close did not restore ready tab A`.
The earlier private multi-WindowTab session restart/history/split
restoration markers passed, the test-owned process exited 0, and the
six protected legacy profile files stayed byte-identical. The
on-VM captured UIA snapshot showed the surviving `Left\\Nested`
address and `Nested` pane tab; it did not include the exact Back
button enablement or status message needed to classify the remaining
history/chrome readiness failure as product or harness. The private
failure screenshot and logs remain in the preserved central VM
workspace. The attempted private Actions artifact upload separately
failed due to GitHub artifact storage quota; it is not a product
failure. There is **no accepted Release+GUI PASS for this candidate**.
Do not rerun the same revision blindly. Diagnose the state/busy
boundary first, then run a genuinely targeted successor only after a
material fix/instrumented hypothesis. The central Remote Shell slot
was restored to idle after read-only failure inspection.

Prior 20,500-file acceptance already proved indexed **name** sort and
name filtering (run `37211942616`). At this 2026-10-10 checkpoint,
above-20,000 type/size/date global sorts were unsupported. The later
local fixed-drive-only indexed metadata path superseded that restriction
for eligible folders (20,500-item owned GUI run `38055029443`);
other filesystem and Shell/provider types retain the 20,000 limit.
The precise remaining tasks are in
`docs/development/PRE_DISTRIBUTION_FUNCTIONAL_GATES.md`.

These are revision- and scope-specific evidence records, not blanket
current-main product acceptance:

| Tested/source revision | Producing run or record | Proven scope / limitation |
| --- | --- | --- |
| `7c23af1515fab0926fa409d277efd6e16b9d1f65` (2026-10-09) | Central Windows CI `37891854981`, `central-ci/windows-gui=success` | Release build, `gui-all-Release` functional GUI, exit 0; no new visual/DPI/IME/signing claim |
| `029ef1e5d8f186bfc5262d386576204b58fa47a9` candidate (2026-10-09) | Remote task `37934459707` and visual task `37935505947` | Indexed-date targeted native/Release/GUI and matched Dark 100% visuals; candidate-specific, not main full-suite acceptance |
| `6ab2791ae1991f3750fa754c2c2d7015aef01950` (2026-10-10) | Windows-ownership migration source commit | Source/operations change; its main inclusion alone does not establish Release, functional GUI or visual PASS |

When making any new acceptance claim, record the exact source SHA,
tested binary/configuration, environment, actual scenario/scope,
producing run ID, status/conclusion and visual comparison separately.
Reuse previous PASS evidence only when the corresponding product,
runtime and environment are unchanged. `health`/`gui-probe` are not
product acceptance, and central `gui` does not prove the retired
Debug+Release `full` or final-pixel visual gate. Older task names
below are historical revision-specific evidence only.

The current product architecture includes the completed V8-A through V8-E
controller-extraction cycle: WindowWorkspaceController, SessionCoordinator,
ShellNavigationController, FileOperationController and SearchController. A
post-extraction MainWindow audit also moved the coherent file-detail worker
lifecycle into FileDetailController. A second responsibility audit selected
preferences persistence as the next justified ownership boundary and moved its
revision/mutex/detached-save lifecycle into PreferencesCoordinator. A follow-up
workspace-restore lifecycle audit then found an independent request/settlement
boundary and moved pane-local restore sequencing into
WorkspaceRestoreCoordinator. Live Git refs always take precedence over recorded
checkpoints.

## Accepted current behavior

- Windows 11-style WinUI 3 shell with custom title bar/Mica, navigation,
  address/search, command bar, status surface and independent dual panes.
- Functional top-level Window Tabs plus per-pane folder tabs.
- V8-A extracts live WindowTab/Pane/PaneTab state-transition ownership into the
  UI-independent WindowWorkspaceController under app/winui; MainWindow keeps
  XAML presentation plus Shell/watcher side effects.
- V8-B extracts private-session capture/save/load/restore/clear generation and
  close invalidation into the UI-independent SessionCoordinator under app/winui.
  MainWindow now keeps only session-related XAML projection, status and
  Shell/watcher side effects.
- V8-C ShellNavigationController owns isolated Shell navigation, supervisor,
  filesystem/Shell namespace watchers and stale route/request handling.
- V8-D FileOperationController owns transfer/file-command worker lifecycle,
  cancellation, stale completion and collision/recycle continuations.
- V8-E SearchController owns bounded search request identity, cancellation,
  stale completion rejection and recent-scope persistence.
- Recursive filesystem search now visits up to 20,000 entries with a depth
  ceiling of 32, keeps up to 1,000 matching paths for UI projection and
  continues counting matches after the retained-result cap. SearchResults
  distinguishes retained-result limiting from traversal limiting so the UI can
  report "first N shown" separately from an incomplete tree walk.
- The first post-extraction audit identified file-detail work as one remaining
  independent lifecycle boundary. FileDetailController now owns pane-local
  cancellation, detached detail workers and bounded Shell visual/thumbnail
  orchestration. MainWindow retains request preparation, live PaneState
  acceptance, DispatcherQueue handoff and XAML projection.
- Sortable file metadata is a separate lifecycle from Shell visual/detail
  enrichment. FileMetadataController collects bounded filesystem type keys,
  byte sizes and last-write timestamps for complete fixed, removable, mapped
  network and ordinary direct-UNC filesystem models up to the existing
  20,000-entry ceiling. Network metadata runs in the exact-owned
  `FlyShellIsolationHelper.exe --file-metadata` process with restricted
  inherited handles, a one-process kill-on-close Job Object, inherited
  cancellation and a bounded inactivity timeout; local fixed/removable
  metadata keeps the detached in-process worker. FileDetailController separately
  owns Windows type/icon/known-folder/thumbnail presentation. Its 1,200-item
  visual-work ceiling accepts local fixed/removable, mapped `DRIVE_REMOTE`
  and ordinary direct-UNC filesystem roots, plus virtual Shell/provider roots
  for type/icon and bounded thumbnail detail. Removable/network filesystem
  detail uses navigation-snapshot folder hints so the parent process does not
  probe those paths for attributes. Virtual roots keep filesystem paths empty
  and route bounded parsing names through an exact-owned Shell helper. In
  Medium/Large Icons, at most four non-folder provider items request
  `IShellItemImageFactory` thumbnails inside that helper; filesystem
  path/reparse/size thumbnail validation remains on the separate filesystem
  helper route. Type/size/modified-date sort
  no longer silently falls back to name order while metadata is pending or when
  the folder contains 1,201-20,000 items. Modified-date validity is derived
  from the FILETIME value itself; display-label formatting is independent of
  sortable timestamp validity.
- The second MainWindow responsibility audit compared preferences persistence,
  private drag/drop state and workspace restore sequencing. Preferences was the
  strongest independent persistence/lifetime boundary: PreferencesCoordinator
  now owns the Preferences value, write mutex, revision ordering and detached
  atomic-save worker. MainWindow retains theme/view presentation, request
  initiation and DispatcherQueue-projected save-failure status.
- Physical pointer drag is now accepted on candidate
  `9e1b8be9f6b61ed8fc69519d281a9fe8bd2f1bc5` in Remote Windows Task
  `37277431952`. The previous failure boundary was WinUI gesture routing:
  ListViewItem consumed the pointer route for selection and later pointer
  movement followed control capture rather than the row handler. The product
  now observes the handled press, polls the held left-button/cursor at 16 ms,
  applies the Windows drag threshold, obtains the current PointerPoint by ID and
  calls the documented StartDragAsync entry point. The existing DragStarting
  handler still owns data-package creation and route/source validation. The
  owned Release test delivered real mouse press/move/release, reached DragOver,
  copied the Korean owned file across panes, exited normally, and left all six
  protected user settings byte-identical.
- Outbound filesystem drag now adds the public Windows
  `StandardDataFormats::StorageItems` payload on the accepted explicit row
  `StartDragAsync` path while retaining the private same-app token in the same
  DataPackage. StorageFile/StorageFolder projection is performed asynchronously
  under the DragStarting deferral; failure to project the public payload leaves
  the private same-app payload intact. Outbound allowed/requested operation is
  Copy only. Remote Windows Task #464 (`37399608114`) passed FAST, canonical
  Release build and a real physical mouse drag from flyExplorer into a newly
  opened test-owned Windows Explorer window: the Korean owned file appeared in
  the Explorer destination and remained in the flyExplorer source. That run
  later failed only in the older broad same-app GUI harness after the outbound
  acceptance had completed. Focused same-app successor #466
  (`37400834524`) kept product code unchanged and passed a real private-token
  cross-pane drag copy after explicitly routing both owned panes. The product
  therefore interoperates with external Windows drop targets that consume
  StorageItems without weakening private route/replay validation. Explorer is
  the accepted external target; Desktop and arbitrary third-party drop targets
  use the same public payload but are not separately certified by owned GUI
  evidence.
- The follow-up workspace-restore audit reversed the earlier deferral after
  identifying a real lifecycle boundary: each pane has queued restore tasks plus
  one awaited Shell navigation request. Previously a failed/rejected/no-change
  restore request could clear the model pending flag without advancing the raw
  queue, leaving later tabs unrestored. WorkspaceRestoreCoordinator now owns
  restore tasks, awaited request identity, settle/advance matching and
  reset/cancel semantics. MainWindow keeps workspace/model application, Shell
  submission and presentation. Stale or canceled completions cannot advance a
  restore lane, while a matching failed/rejected/no-change completion can
  continue remaining tabs.
- Ctrl+T, Ctrl+W, Ctrl+Tab and Ctrl+Shift+Tab Window Tab behavior.
- File creation keyboard routing now reuses the existing
  `fxfile::filecommand::Kind::CreateFolder` command path: Windows
  Explorer-style `Ctrl+Shift+N` opens the existing create-folder name editor
  for the current active pane/tab. No separate keyboard mutation path or command
  owner was introduced. Historical flyExplorer `F11` is not restored because
  current Windows/File Explorer uses F11 for window maximize/restore. Remote
  Windows Task #423 (`37297889221`) passed FAST, a normal Release build and the
  focused file-operations GUI on candidate
  `9af6c368a15853e5aab96906f6a298e733f3c40c`; real Ctrl+Shift+N input created
  owned Korean folders in each independently activated pane through the existing
  command path, the opposite pane remained untouched, the existing button path
  still passed, the owned process exited 0 and protected legacy settings
  remained unchanged.
- Explorer-aligned navigation shortcuts are now explicit product semantics.
  Plain F5 refreshes only the active pane/tab through the existing isolated
  Shell `NavigationAction::Refresh` path. Plain F6 never starts a file
  operation; in split view it activates and keyboard-focuses the opposite
  pane's file list, while single-pane F6 is left to normal WinUI focus
  behavior. Both keys are owned at the window `PreviewKeyDown` boundary
  rather than the file-operation shortcut handler, and modified F5/F6
  combinations are not interpreted as historical copy/move commands. Remote
  Windows Task #473 (`37414193732`) accepted candidate
  `4e59a22c742c7fa8d5d0e21e221f01ff8151e2be`: FAST passed, the canonical
  Release build produced flyExplorer.exe, the complete Release runtime was
  cached, physical F5 refreshed the active owned pane without copying the
  selected folder, physical F6 moved activation/focus left-to-right and back
  without moving that folder, the owned process exited normally, and the
  protected legacy profile remained unchanged.
- Details, List, Small Icons, Medium Icons and Large Icons views.
- New top-level Window Tabs preserve the configured default view across the
  full 0-4 FileViewMode range. In particular, a Large Icons preference now
  remains Large Icons when Ctrl+T or the Window Tab add button creates a new
  workspace tab; it is no longer clamped down to Medium Icons.
- File-list Shell visuals use path-specific Windows Known Folder artwork for
  Desktop, Documents, Downloads, Pictures, Music and Videos. The bounded
  disposable Shell helper returns pixels only; failures retain the generic
  folder icon fallback.
- Sidebar navigation reuses the same six fixed Known Folder visual keys on a
  background worker and projects 16 px native artwork through the UI dispatcher.
  Each button retains its previous Fluent glyph as a failure fallback. Home and
  This PC intentionally retain their existing Fluent glyphs.
- Persistent WinUI filesystem bookmarks are stored in the private
  `%LOCALAPPDATA%\flyExplorer\bookmarks-v1.txt` profile with atomic
  replacement. The active pane's current filesystem folder can be added from
  the always-visible bookmark bar, reopened from that bar, renamed or deleted
  from the management panel, and survives process restart. Paths are
  case-insensitively deduplicated and the model remains bounded at 100 items.
  The legacy MFC bookmark file is never read automatically; users may explicitly
  select a legacy configuration file for read-only name/path import. Duplicate,
  malformed and unsupported non-filesystem legacy entries are skipped rather
  than mutating the old profile.
- Search v2 kept the existing bounded asynchronous SearchController lifecycle
  and added optional ECMAScript regex, case-sensitive matching,
  file/folder/both targeting and a single extension condition. Default
  behavior remains case-insensitive literal file-name search. Invalid
  regex/extension input is rejected before worker start. At the Search v2
  revision the inherited bounds were depth 5, 2,500 walked entries and 100
  retained results; current main supersedes those historical scale limits with
  depth 32, 20,000 walked entries and 1,000 retained results while preserving
  cancellation/stale-result rejection and opt-in recent scope persistence.
- Back/Forward/Up, filtering/sorting, local create/rename, guarded copy/move/
  recycle flows, Windows clipboard/context integration, isolated Shell visuals
  and directory/Shell namespace watching.
- File transfer selection is no longer capped by the historical 32-item
  magic number. Copy/move/recycle, Windows CF_HDROP clipboard, same-app drag and
  external StorageItems drop now share the native
  `fxfile::shelltransfer::kMaxItems=1024` item budget plus
  `kMaxSourcePathUnits=1048576` aggregate UTF-16 source-path budget. The core
  remains fail-closed above either bound. Remote Windows Task #459
  (`37395664418`) passed FAST, Release M22 native contracts at 21/21 including
  a real 64-item IFileOperation copy, Release M23 native contracts at 30/30
  including a 64-item CF_HDROP round-trip, and the canonical Release build.
  Its only later failure was a GUI harness assumption that all 64 virtualized
  ListView rows must simultaneously appear through UIA. After changing only
  that harness assertion, Remote Windows Task #460 (`37396241096`) passed
  FAST, runner health, the canonical Release build and the focused owned GUI:
  Ctrl+A selected the 64-item WinUI model and the existing Copy command copied
  all 64 owned files to the opposite pane, with normal process shutdown.
- Native filesystem Copy/Move validation accepts `DRIVE_FIXED`,
  `DRIVE_REMOVABLE` and `DRIVE_REMOTE` roots. Ordinary direct UNC paths
  (`\\server\share\...`) are classified separately from drive-letter roots
  and use the same bounded filesystem validation. Pane Copy/Move,
  internal/Windows clipboard paste, same-app transfer and external-drop
  ingestion converge on FileOperationController, which executes Copy/Move in
  the exact-owned `FlyShellIsolationHelper.exe --file-transfer` child.
  Virtual Shell/provider roots have a separate **Copy-out** source
  mode: the destination must be a real filesystem folder, selected source
  identity is carried as bounded snapshot PIDL value bytes plus parsing-name
  diagnostics, and only the helper queries `SFGAO_CANCOPY`, revalidates
  direct-child identity/materializable leaf names/collisions and calls
  `IFileOperation::CopyItem`. Per-PIDL size is capped at 32 KiB and aggregate
  provider PIDL data at 1 MiB in addition to the existing 1,024-item/
  1,048,576-source-identity-unit bounds. No COM object crosses the wire.
  A second **Copy-in** destination mode now allows filesystem-source Copy
  into the built-in Pictures Library only when its exact snapshot PIDL matches
  `FOLDERID_PicturesLibrary` and the library default save folder is the
  actual Pictures Known Folder. Helper-only default-save resolution, safe-path
  and name-collision checks precede `IFileOperation::CopyItem`; the transfer
  wire is v3. Arbitrary provider destination writes, provider Move,
  provider-to-provider Copy, Recycle/Delete, reparse traversal and
  extended/device namespaces remain closed. The transfer child retains restricted handle
  inheritance, one-process kill-on-close Job Object and bounded cancellation.
  Recycle remains local fixed/removable only with explicit confirmation and
  recycle-only Shell flags.
- Private session schema v2 persists/restores the active Window Tab, per-tab
  split state/ratio and active pane, both panes' tabs, selected tabs,
  view/sort/name-column state and bounded filesystem Back/Forward history.
  Legacy session v1 remains readable.
- ko-KR is the default app-owned UI language.

## Shell and shutdown safety

Potentially blocking Shell/provider work must not execute synchronously on the
XAML UI thread. FlyShellIsolationHelper.exe and bounded native worker paths
provide the process/thread fault boundary.

The v7 session acceptance exposed a repeatable close race with
CoreMessagingXP.dll / 0xC000027B and WER 0x800710DD
(ERROR_INVALID_OPERATION). Cancellation/shutdown remains at the window Closed
boundary. V8-B moves session epoch/revision invalidation into
SessionCoordinator::prepareForClose(); detached session workers retain only
shared native generation state and post through a close-safe callback supplied
by MainWindow. FileMetadataController now owns pane-local sortable-metadata cancellation and
its detached filesystem-metadata worker lifecycle. FileDetailController
separately owns pane-local visual-detail cancellation and the detached
type/icon/thumbnail worker lifecycle. MainWindow still performs the live
route/tab/ticket acceptance before projecting either completion, and
PrepareForClose cancels both metadata and detail work before
ShellNavigationController shutdown.
Accepted GUI evidence requires real process exit code 0.

## Build and test environment

Canonical Windows full builds now have one explicit toolchain contract:
- Visual Studio/MSBuild 18.x;
- MSVC v145 x64 tools;
- Windows SDK 10.0.26100.0.

VS 2022/v143 is not claimed as a supported full-build path. The app, Shell
helper, M19-M23 native fixtures and installer template use v145 consistently.
MSBuild discovery verifies the x64 compiler/toolset/SDK, and the app build
verifies the restored WinUI/XAML assets after NuGet restore.

Direct NuGet references are Microsoft.WindowsAppSDK 2.5.1,
Microsoft.Windows.CppWinRT 2.0.250303.1,
Microsoft.Windows.SDK.BuildTools 10.0.26100.9169 and
Microsoft.Windows.ImplementationLibrary 1.0.260126.7. Actual transitive restore
is verified from project.assets.json rather than inferred from these four
references.

Source-only contracts are suitable for a non-Windows/Python stdlib environment.
Product compilation/execution requires Windows. GUI automation additionally
requires the pinned tests/winui/requirements-gui.txt set and an interactive
Windows desktop. Debug is framework-dependent; Release is self-contained but
still requires its complete sibling runtime/resources.

The retired Remote Windows Task preserved multi-line/quoted PowerShell by writing
`REMOTE_COMMAND` verbatim to a per-run temporary `.ps1` and invoking a fresh
`powershell.exe -File` process. The child process exit code is authoritative
and the temporary script is removed in `finally`. Candidate run #429
(`37302252972`) verified preserved quoting/multi-line source, handled native
nonzero semantics, product-like `try/finally` flow and command exit 0.

The previously described external install_script/start_skill cloud bootstrap
files are not present in this repository. This repository therefore documents
the required environment but does not claim to have modified external cloud
bootstrap configuration.

## Latest verified evidence

### 2026-10-09 — Indexed Modified-Date Filter (pre-main acceptance)

Code candidate `029ef1e5d8f186bfc5262d386576204b58fa47a9`
adds optional inclusive local-calendar `YYYY-MM-DD` after/before bounds
to Windows Search indexed filename, extension and size-KB AND criteria.
The owned helper prefilters on `System.DateModified` with deliberately
broad date-only SQL bounds to allow UTC/local offset and DST differences.
For every returned file it validates current `ftLastWriteTime` as a
local date and applies the exact inclusive lower/upper bounds, excluding
stale matches. Gregorian/leap/invalid/reversed dates are rejected before
the provider call. Search still uses the owned isolated 12-second
helper, cancellation, at-most 1,000 indexed paths, 1 MiB reply,
fixed and reparse-safe filesystem scope, and no traversal fallback.
Indexed regex, folder, content and provider/property search remain
unsupported and fail closed.

Windows validation `37934459707` **SUCCESS**, SHA-scoped to the code
candidate: FAST/source contracts, Release native fixture **72/72**,
Release product build, actual SystemIndex inclusive modified-date
include/exclude tests, invalid/overflow/reversed input, GUI AND
composition of extension + KB size + day range, safe reset,
legacy profile and Public Desktop source unchanged, and normal GUI
process exit 0. The producing job persisted a curated status record to
`evidence/remote-windows/runs/37934459707/`. A separate matched-size
before/after UI visual comparison completed as `37935505947`
(**SUCCESS**) on the exact candidate. The captured BEFORE and AFTER
app-owned screenshots are both **956×711** at a controlled 972×720 HWND:
zero geometry delta, **1,450 pixels** changed (0.2133%), confined to
the indexed-mode hint row `[446,200,664,214]`. Both actual previews
were visually inspected: the Korean indexed-date hint fits on one line,
and neighboring input controls, dual panes, header and footer retain
their positions without overlap or clipping. **Targeted fixed-size
Dark-theme 100% visual PASS.** Preview frames and comparison metadata
remain in the linked Actions job log; curated status records exist at
`evidence/remote-windows/runs/37935505947/`. Other DPI, manual
accessibility/IME, signing, external providers and a separate post-main
Windows full-suite check remain **NOT TESTED**.

### 2026-10-09 — Search v3 indexed file size criteria (KB)

Integrated candidate `9cf68d575d62dabd748ba9caff500e7c9eeb2179`
extends Windows Search indexed filename and optional extension conditions
with inclusive integer-KB minimum/maximum file size, AND-composed in
`SystemIndex`. The exact-owned helper validates malformed/reversed/overflow
input below signed-64-bit `System.Size` ceiling, rechecks current filesystem
size to exclude stale index records, and preserves the 12-second owned-helper
deadline, cancellation, fixed/reparse-safe scope, 1,000-result/1 MiB wire caps,
and no filesystem traversal fallback. Date/regex/content/provider/property
indexed search remains unsupported and fails closed.

Initial run `37923169399` failed only after successful source, Release
product and native build: the Python driver expected 64 tests for a 63-test
fixture. After the assertion correction, candidate
`7cd134456d0ed020d1008858a579ba41900d2902` passed Windows Task
`37925547766` (**SUCCESS**), including source contracts, 63/63 Release
native fixtures, Release product build, actual SystemIndex size include/exclude,
malformed helper argument rejection, focused GUI AND matching, size reset and
unsupported criteria rejection, protected profile unchanged and test-owned
process exit 0. Evidence: `evidence/remote-windows/runs/37925547766/`.

The first visual run `37927022090` passed product checks but the captured
heights differed (944×510 versus 944×677), so it is not matched visual
acceptance. The corrected owned-HWND geometry fixture on candidate
`9cf68d575d62dabd748ba9caff500e7c9eeb2179` passed Windows Task
`37930662129` (**SUCCESS**): BEFORE and AFTER app-owned screenshots
are both **956×711**, rendered at an owned 972×720 HWND. Changed area
`[319,200,737,214]` spans 2,586 pixels (0.3805%) and is confined to the
indexed-search hint row. Both actual previews were visually inspected:
the new Korean indexed file-size hint stays on one line, controls do not
overlap or clip, and both file panes, header row, navigation/sidebar and
footer remain visible. **Targeted fixed Dark-theme/100% visual PASS.**
This does not certify different DPI, human IME/Narrator, arbitrary providers,
physical USB/SMB, signing or public release. All runs are pre-main;
independent exact-main full-suite CI was not performed. Screenshot previews
and the pixel report remain in the run log, not the curated Git record.

### 2026-10-09 — Search v3 Windows Search indexed extension conditions

Integrated candidate `8c339a450a04109a2f0ab01aa425c0551d5441a4`
extends indexed filename searches with one optional normalized file extension
(up to 32 characters) while preserving the fail-closed unsupported-filter
boundary, 1,000-result limit and isolated helper lifetime. The Windows
Search-native oracle verifies `.LNK` inclusion and `.txt` exclusion against
an unchanged pre-indexed Public Desktop shortcut. The 57-case Release M19
native fixture also passed in run `37912684233`.

Remote Windows Task `37920530398` completed **SUCCESS** on the named
candidate: FAST source contracts, both old-main and candidate Release builds,
GUI runner health, indexed-search native oracle and GUI include/exclude, normal
owned process exit 0, unchanged protected settings/system source, and the
corrected pixel-comparison fixture all passed. The repository evidence record
is `evidence/remote-windows/runs/37920530398/`; detailed preview and pixel
report remain in the Actions job log, not the sanitized Git record.

**Targeted visual review:** actual app-owned baseline and candidate image
previews were inspected. The modified one-line index-mode explanation is fully
visible; the surrounding search controls retain their alignment, with no
new text clipping or overlap observed. The screenshots differ in overall
height (BEFORE **944×625**, AFTER **944×599**, delta **−26 px**).
The difference occurs below the modified search panel in the file-list area;
its cause was not established. The corrected comparator reports the
unmatched viewport rather than discarding pixels. Therefore this is
**targeted search-panel visual review PASS**, but **matched full-window
geometry and exact full-resolution pixel review remain NOT TESTED**.
Do not describe these unequal images as a like-for-like full-window match.
Alternate DPI/scaling, physical USB/SMB, human accessibility testing,
signing and public distribution are still outside this acceptance.


### 2026-10-09 — Store remote Windows evidence in Git

Candidate `6564165c14ca6dc561a8591ab7a9b696a864b8f6` passed
source contracts, the Release app build, Release M19 native 57/57, the
real SystemIndex indexed-extension oracle and test-owned GUI
include/exclude in remote run `37912684233`. Despite that, the
workflow conclusion was **failure** solely because the final
`upload-artifact` step exceeded the GitHub Actions storage quota.

The surviving structured result and status markers are preserved in
`evidence/remote-windows/runs/37912684233/`. These were recovered
from the observed Actions log, not from an unavailable artifact ZIP.
Subsequent remote tasks publish their own bounded status evidence
directly to this separate Git branch. Screenshots or raw/private data
are not included. This CI repair does not merge the separate Search
v3 feature candidate into product `main`.

This new archive path was independently exercised on main revision
`9700082da4a2071274e34c2fad4200c4fb71e226` by Remote Windows
Task `37917225055`: source contracts **26/26 PASS**, serializer
`EVIDENCE_ARCHIVE_PREPARE=PASS`, repository push
`EVIDENCE_REPO_ARCHIVE=PASS` and full workflow conclusion
**success**. The actual persisted manifest and structured result are
visible at `evidence/remote-windows/runs/37917225055/`. No
Release app build or new GUI acceptance was run in this
archival-only smoke test.



### 2026-10-09 — main Release and complete GUI acceptance

On 2026-10-09, main revision `7c23af1515fab0926fa409d277efd6e16b9d1f65`
(merged PR #55) was verified by the independent central Windows CI run
`37891854981` in `tngkrwlsmd/personal-control-plane`.
The run logged `PASS release-build`, `gui-all-Release` exit 0
(145.1 seconds), and `PASS functional-gui`, then posted
`central-ci/windows-gui=success` to that exact main SHA.

The merged full-suite handoff scopes
`FLY_M20_OWNED_COLLAPSE_M19_PANELS=YES` to the chained `all` GUI
area so M19 Search/Workspace panels are collapsed before M20 file-list
interaction. Standalone GUI areas do not inherit this flag. Earlier
test-owned chained acceptance `37891171256` passed using the
existing Release runtime with normal app exit 0 and unchanged protected
user settings. PRs #51/#52 corrected combined test fixtures and transient
UIA restoration; PR #54 added bounded failure capture from the launched
test-owned app before cleanup. These were harness/test changes, not
new product functionality.

This central run certifies the named Release-build and functional-GUI
boundaries, not new BEFORE/AFTER visual pixels, alternate DPI, human
Narrator/Korean IME, physical USB/SMB, signing, or public distribution.
Candidate-only evidence must not be confused with exact-main CI evidence.


Search scale expansion is accepted on candidate
`73d52afcd28fb8bbb6af3009c805f269e80d7dd1` by self-hosted Remote
Windows Task `37461845906`. The run passed request validation,
change-scoped FAST, GUI runner health, the Release M19 native fixture at 49/49,
the canonical Release build and the established Search GUI regression. The
native fixture creates 2,600 owned files plus a seven-level directory chain:
it proves the search walks beyond the historical 2,500-entry ceiling, counts
1,100 matches while retaining the first 1,000 instead of the historical 100,
and finds a target below the historical depth-5 boundary. The fixture is fully
reclaimed after the run.

The product now uses `kMaxWalk=20000`, `kMaxDepth=32` and
`kMaxResults=1000`. Reaching the retained-result bound sets
`resultLimited` but scanning/counting continues; reaching the walk/depth
bound sets `traversalLimited`. The Search panel reports these conditions
separately rather than using one ambiguous "limited partial results" label.
Structured stages REQUEST_VALIDATION, STATIC_PREFLIGHT, RUNNER_HEALTH and
COMMAND are all PASS with no failure category. Evidence artifact
`11413450005`, digest
`sha256:86248256d14f11986204acf5fb8c3defdfd0d531a0a78f28dc696227d63eebc6`,
preserves the remote result and logs.

Removable-volume sortable metadata support is accepted on candidate
`e0e9483704a53ac4caddd20b06146bcdfe577044` by self-hosted Remote
Windows Task `37459066015`. The run passed request validation, change-scoped
FAST and the canonical Release build, then exercised the existing input-free
metadata-sort GUI regression in size, modified-date and type modes over the
1,305-file fixture. It passed
`METADATA_SORT_OVER_1200_SIZE_DESC True`,
`METADATA_SORT_OVER_1200_DATE_DESC True` and
`METADATA_SORT_OVER_1200_TYPE_ASC True`, with
`REMOVABLE_METADATA_SIZE/DATE/TYPE=PASS`. At that revision the
sortable-metadata scheduler accepted `DRIVE_FIXED` and `DRIVE_REMOVABLE`
local roots while `DRIVE_REMOTE`/UNC remained closed; the network extension
below supersedes that historical boundary. Shell visual detail/icon/thumbnail
scheduling remains a separate fixed-drive-only path.

The VM still exposes no `DRIVE_REMOVABLE` volume, so physical USB metadata
sort execution is not claimed. The same run emitted
`REMOVABLE_METADATA_PHYSICAL_USB=NOT_RUN_NO_DEVICE`. Evidence artifact
`11410943753`, digest
`sha256:ead551360031fe8d584005222231486422adf1d703b4e090c0d049b053d868a9`,
preserves the remote result and logs. The wrapper's RUNNER_HEALTH stage was
not requested by this validation-plan vocabulary, but the Release command
itself executed all three owned WinUI metadata-sort GUI processes successfully.

UNC/network sortable metadata support is accepted on candidate
`f51edfdb40e066d063c85958601336c1854aeafc` by self-hosted Remote Windows Task `37563774189`.
The scheduler accepts local `DRIVE_FIXED`/`DRIVE_REMOVABLE`, mapped
`DRIVE_REMOTE` and ordinary direct `\\server\share\...` filesystem
roots. Network requests use the bounded private `file_metadata_wire.h`
protocol and execute `GetFileAttributesExW` only inside the exact-owned
`FlyShellIsolationHelper.exe --file-metadata` child. The parent restricts
inherited handles, assigns the child to a one-process kill-on-close Job Object,
passes an inherited cancellation event, uses a 5-second inactivity watchdog
and gives cooperative cancellation a 1.2-second grace period before terminating
only the owned job. Local fixed/removable metadata remains on the existing
detached in-process worker. Extended/device namespaces, reparse traversal and
virtual Shell/provider parsing names remain closed.

Run `37563774189` passed request validation, change-scoped FAST, GUI runner
health, `git diff --check`, the canonical Release helper/app build and the
1,305-file focused GUI with the local owned fixture forced through the isolated
metadata-helper path. It passed
`METADATA_SORT_OVER_1200_SIZE_DESC True`,
`METADATA_SORT_OVER_1200_DATE_DESC True`,
`METADATA_SORT_OVER_1200_TYPE_ASC True`,
`METADATA_SORT_ISOLATED_HELPER_PASS True`,
`METADATA_SORT_OWNED_PROCESS_EXIT 0` and protected legacy settings unchanged.
Evidence artifact `11458556096`, digest
`sha256:07d060c06f32bc2cb098ef2c9f235fab31d282e6bc01bf131e97a3eef679f1a6`,
preserves the remote result and logs. Actual SMB/UNC and mapped-network-drive
metadata execution is **not claimed** because the runner still has no
test-owned SMB share; the acceptance proves root policy, exact-owned helper
isolation, wire/lifecycle behavior and complete size/date/type sorting through
that helper path. No XAML/pixel behavior changed.
VISUAL ACCEPTANCE: NOT TESTED

UNC/network Shell visual/type/icon/thumbnail support is accepted on candidate
`e4c95e1c2e7c1a3ca1f3530dac86f4477c1664a3`. The scheduler accepts local fixed roots, mapped
`DRIVE_REMOTE` roots and ordinary direct `\\server\share\...`
filesystem roots through the existing 1,200-item detail ceiling. For direct
UNC, MainWindow classifies the root as network without a parent-side provider
probe. Network detail requests carry the navigation snapshot's folder/file bits
into FileDetailController, which avoids `GetFileAttributesExW` on UNC paths in
the flyExplorer process. Registered Windows type/icon work remains bounded in
the disposable visual helper, and image thumbnail validation/access remains in
the exact one-shot `--file-thumbnail` child with the existing timeout and
exact-process termination path. Extended/device namespaces, reparse traversal and virtual Shell/provider
parsing names remain closed. At this network-only candidate, removable-drive
visual detail was still closed; the removable successor below supersedes that
historical boundary.

Remote run `37575384608` passed FAST, canonical Release build and the owned
fixed-drive visual fixture, then captured the accepted 944x510 BEFORE frame via
an app-owned XAML `RenderTargetBitmap`. Run `37577331163` passed the final
change-scoped FAST contracts. Run `37577442125` passed `git diff --check`,
canonical Release build and the same PNG/TXT/folder fixture forced through the
network-detail branch with
`NETWORK_VISUAL_THUMBNAIL_PASS=True`,
`NETWORK_VISUAL_REGISTERED_ICON_PASS=True`,
`NETWORK_VISUAL_FOLDER_ICON_PASS=True`,
`NETWORK_VISUAL_TYPE_LABEL_PASS=True`,
`NETWORK_VISUAL_PROCESS_EXIT=0` and protected legacy settings unchanged.
Artifact `11463144265` has SHA-256
`1e93c352694621c4a9b6b18d1884519d675359773cfb9d5f8d170eb3d1e5bb6b`.
Direct review of the 944x510 BEFORE/AFTER images found identical file-list,
icons, thumbnail and layout pixels; changed pixels were confined to the random
test-owned temporary path text in the top chrome.
**VISUAL ACCEPTANCE: PASS**.

Actual SMB/UNC and mapped-network-drive visual execution is **not claimed**
because the self-hosted runner has no test-owned SMB share. The accepted GUI
proves the network-detail scheduling/isolation path with a forced owned local
fixture, not network latency/provider behavior on a real share.


Removable/USB Shell visual/type/icon/thumbnail support is accepted on candidate
`f134d4794615fb088675bd804621b974bb4428c8`. The existing 1,200-item detail
lifecycle now accepts `DRIVE_REMOVABLE` in addition to fixed, mapped network
and direct UNC roots. Removable and network requests use the navigation
snapshot's folder/file bits through the generalized isolated-path request, so
FileDetailController does not call `GetFileAttributesExW` on those paths in
the flyExplorer process. The one-shot `--file-thumbnail` helper now accepts
fixed/removable/remote roots while retaining component/reparse validation, the
32 MiB file-size bound, Shell image extraction, bounded timeout and exact-owned
process termination.

Run `37587596698` stopped at FAST on a stale source-contract expectation
before any build or GUI work. After that test-only correction, run
`37587832255` passed FAST and runner health but intentionally stopped before
build when the canonical checkout exposed an old clean registered nested Git
worktree. Read-only diagnosis run `37588036456` proved the directory was a
detached Git worktree from 2026-10-05, and cleanup run `37588225417` verified
that nested worktree was clean before removing it with `git worktree remove`
and restoring a clean canonical checkout.

Final run `37588369405` then passed request validation, change-scoped FAST,
GUI runner health, the canonical Release build and the focused owned GUI.
The forced removable path reported
`NETWORK_VISUAL_THUMBNAIL_PASS=True`,
`NETWORK_VISUAL_REGISTERED_ICON_PASS=True`,
`NETWORK_VISUAL_FOLDER_ICON_PASS=True`,
`NETWORK_VISUAL_TYPE_LABEL_PASS=True`,
`NETWORK_VISUAL_FORCED_REMOVABLE_PATH=True`,
`NETWORK_VISUAL_PROCESS_EXIT=0` and protected legacy settings unchanged.
Artifact `11467278119` preserves the final evidence.

Direct review compared its 944x510 AFTER frame against the accepted current-
product fixed-path BEFORE frame from run `37575384608` / artifact
`11462737179`. Of 481,440 pixels, 208 changed (0.0432%); every changed pixel
was confined to x=445..475, y=49..62 in the random test-owned temporary path
text. The file-list/content region below y=80 was pixel-identical.
**VISUAL ACCEPTANCE: PASS**.

The final run reported
`REMOVABLE_VISUAL_PHYSICAL_USB=NOT_RUN_NO_DEVICE`. Actual physical USB/
removable visual execution is therefore **not claimed**; the accepted GUI
proves the removable scheduling/isolation branch with a forced test-owned local
fixture. Virtual Shell/provider visual enrichment remains unsupported.

The removable paragraph above records the boundary at that candidate; current
main supersedes only its virtual-visual limitation.

Virtual Shell/provider **type/icon** support is accepted on candidate
`d41a75cac8a2eb40dc406174c07689ad6e54f063`. A virtual root is recognized
when the accepted navigation session has a Shell PIDL but no filesystem path.
MainWindow passes each child item's desktop-absolute parsing name, not a
filesystem path, through a bounded private wire to
`FlyShellIsolationHelper.exe --shell-item-visuals`. The client uses a
restricted inherited-handle allowlist, one-process kill-on-close Job Object,
cooperative cancellation and a 4.5-second no-progress limit. Only the helper
calls `SHParseDisplayName` and `SHGetFileInfoW(...SHGFI_PIDL...)`. Provider
items do not enter `GetFileAttributesExW`, filesystem thumbnail probing or
`IShellItemImageFactory`.

Baseline run `37591794512` passed FAST, runner health and the focused real
`shell:MyComputerFolder` GUI and preserved artifact `11469400568`. Its
944x510 BEFORE digest is
`ac462537fd94437161c2033a927806b170045e18da5573bfdc8ca8f6c4a79005`.
The visible This PC rows still used generic folder glyphs and the generic
`폴더` type fallback.

The first product validation candidate stopped at FAST in run `37592816719`
because one source contract still encoded the pre-change provider attribute
boundary. After correcting that stale assertion, run `37593190964` reached
the Release build and exposed ambiguous unqualified `kMagic`, `kVersion` and
`checksum` names after the new visual wire was included beside the navigation
wire. The successor qualified those protocol symbols explicitly.

Final run `37593453954` passed request validation, change-scoped FAST, GUI
runner health, the canonical Release build and focused This PC GUI. It reported
`SHELL_PROVIDER_TYPE_ICON_PASS=True`,
`SHELL_PROVIDER_VISUAL_PROCESS_EXIT=0` and protected legacy settings
unchanged. The accepted DVD row changed from generic `폴더` to Windows type
`CD 드라이브` and received the provider Shell icon. Artifact `11469965269`
preserves the AFTER evidence; digest
`42b3a53b26a209edd5ad5469f87fa0696509d9bc83e94f8e58fab5429ee97c1e`.

Direct matched-image review found both captures are 944x510. Exactly 4,368 of
481,440 pixels changed (0.9072%), with bounding box x=199..832, y=221..291.
Every changed pixel is inside the two visible This PC item rows where the
intended Shell icons/type labels changed; chrome, sidebar and every pixel
outside those rows are identical. **VISUAL ACCEPTANCE: PASS**.

This unit does **not** enable virtual Shell/provider thumbnails, Copy/Move or
Recycle. It also does not claim separate acceptance of arbitrary third-party
provider implementations; the real GUI acceptance uses the built-in Windows
This PC virtual Shell root.

The type/icon paragraph above records that unit's boundary; the thumbnail
successor below supersedes only its thumbnail limitation.

Virtual Shell/provider **thumbnail** support is accepted on candidate
`ff9641d05645266ce639fddff97fdb82f014cc3e`. The private provider visual wire
is now v2 and carries a per-item thumbnail flag plus a separate requested
thumbnail size. FileDetailController keeps the existing 1,200-item detail
ceiling but marks at most four non-folder provider records in Medium/Large
Icons, preferring parsing names with PNG/JPEG/BMP/WebP extensions before other
non-folder items. The exact-owned `--shell-item-visuals` helper remains the only
process allowed to parse provider names. For marked records it creates the
Shell item from the already parsed absolute PIDL and calls
`IShellItemImageFactory::GetImage` with
`SIIGBF_THUMBNAILONLY|SIIGBF_BIGGERSIZEOK`. The same restricted handle
allowlist, one-process kill-on-close Job Object, cooperative cancellation and
4.5-second no-progress watchdog cover type/icon and thumbnail work together.
Provider items never enter filesystem attribute probing or the filesystem
`--file-thumbnail` path.

Diagnostic run `37610405578` confirmed Pictures Library is a virtual Shell
root on the current VM. Run `37610682928` then proved a uniquely named
test-owned PNG placed directly in the user's Pictures folder is exposed as a
file item through `shell:PicturesLibrary`; the test removed the file after the
probe.

Matched BEFORE run `37611127478` passed FAST and GUI runner health using the
already accepted current-product binary because the baseline candidate changed
only the Python harness. It reported
`SHELL_PROVIDER_THUMBNAIL_BASELINE_NO_THUMBNAIL=True`: the owned PNG used its
registered Windows file icon, process exit was 0, protected legacy settings
were unchanged and the owned image was removed. Artifact `11477852307`
preserves the 944x510 BEFORE frame, SHA-256
`ce6ef976c28b0f513b008bfb0b763458a7742f6a89749e953261f521b3b36173`.

The first product validation run `37611774958` stopped during FAST before
build because the newly added source contract incorrectly expected the literal
field name `thumbnailPixelBytes` inside helper source even though the helper
initializes that wire field from `thumbnail.size()`. Only that test assertion
changed in the successor.

Final run `37612117791` passed request validation, change-scoped FAST, GUI
runner health, canonical Release build and the focused Pictures Library GUI.
It reported `SHELL_PROVIDER_THUMBNAIL_PASS=True`, UIA exposed
`Windows Shell image thumbnail`, the process exited 0, protected legacy
settings were unchanged and the test-owned PNG was removed. Artifact
`11478154054` preserves the AFTER evidence; SHA-256
`e54f994a299989de2fa41c2b9200c5fbd547a43544d3b83df5a96565d4cf03a7`.

Direct matched-image review found both frames are 944x510. Exactly 6,996 of
481,440 pixels changed (1.4531%). The only changed x-ranges are 327..390 and
714..777, with y=205..264: the same owned image cell in the left and right
panes. BEFORE shows the generic registered PNG icon; AFTER shows the generated
blue/orange/green image thumbnail. Chrome, sidebar, labels, folder cells and
every pixel outside those two image cells are identical.
**VISUAL ACCEPTANCE: PASS**.

This unit still does **not** enable virtual Shell/provider Copy/Move or Recycle,
and it does not claim separate behavior for arbitrary third-party provider
implementations beyond the built-in Windows Pictures Library acceptance.
The thumbnail paragraph above records that unit's boundary; current main
supersedes only its provider-Copy limitation.

Virtual Shell/provider **Copy-out** is accepted on final product/test head
`32648cfeb5e92594619b9ed24b2568b18d71a2e8`. The feature is deliberately
one-way: a provider-root selection may be copied to the opposite real
filesystem pane, while provider Move, provider destination/Copy-in and
provider Recycle/Delete remain rejected. The request preserves the accepted
navigation snapshot identity as bounded desktop-absolute PIDL byte values:
32 KiB per PIDL and 1 MiB aggregate, plus the existing 1,024 source-item and
1,048,576 UTF-16 source-identity-unit limits. MainWindow performs no provider
capability call. The exact-owned `--file-transfer` helper reconstitutes the
parent/children from those PIDLs, requires each selected child to be an
immediate child of the accepted parent, queries `SFGAO_CANCOPY`, obtains a
parent-relative editing leaf for collision checks and finally queues
`IFileOperation::CopyItem`. Filesystem Copy/Move behavior is unchanged.

Acceptance required several harness/identity corrections. The early ZIP
fixture did not establish a stable product virtual-root route; AppsFolder was
empty on this VM. The Pictures Library fixture then exposed that pane
activation/destination settlement had to be explicit. Diagnostic
`37623786873` resolved the canonical Pictures Library parsing name as
`::{031E4825-7B94-4DC3-B131-E946B44C8DD5}\\Pictures.library-ms`.
The product also initially relied on `IndexedItem.attributes & SFGAO_CANCOPY`,
but navigation enumeration does not request that capability bit. Product
revision `d95984203c41519235e36e276ba7f89adfa4e82c` therefore removed that UI
gate and kept capability probing helper-owned immediately before mutation.
Provider identity had already been hardened at
`56a6ea69c820f2e0bca782525238242baaba0187` by transporting the accepted
snapshot's exact parent/child PIDL bytes instead of reparsing provider names in
the transfer path.

Run `37624726608` passed request validation, change-scoped FAST, GUI runner
health and the canonical Release build with the final product source. Its
focused GUI reached provider enumeration, destination readiness, Move
rejection, Copy start and actual destination materialization; the run failed
only because the directory watcher replaced the transient
`복사를 완료했습니다` status with `폴더 변경 알림을 반영했습니다.` before
the harness read it. The successor changed only the harness to verify
FileOperationController returned idle rather than relying on a transient status
string.

Final run `37703633100` passed request validation, FAST, runner health and the
focused GUI on the unchanged Release product. It reported
`SHELL_PROVIDER_COPYOUT_PICTURES_ENUMERATION=True`,
`SHELL_PROVIDER_COPYOUT_DESTINATION_READY=True`,
`SHELL_PROVIDER_COPYOUT_MOVE_REMAINS_REJECTED=True`,
`SHELL_PROVIDER_COPYOUT_CONTROLLER_IDLE=True`,
`SHELL_PROVIDER_COPYOUT_PASS=True` and
`SHELL_PROVIDER_COPYOUT_SOURCE_PRESERVED=True`. The test-owned Pictures file
was removed, the remaining fixture was removed, the app exited 0 and protected
legacy settings stayed byte-identical. No product pixel/layout code changed, so
no new visual acceptance was required.

The runtime case uses Windows' built-in Pictures Library virtual root with a
test-owned filesystem-backed child routed through the provider PIDL path. It
does **not** separately certify arbitrary third-party providers or provider-only
non-filesystem child types. The Copy-out-only statement above records that
earlier logical unit; the accepted Copy-in successor is documented next.

Virtual Shell/provider **Copy-in to the built-in Pictures Library** is accepted
on candidate `dfc8703394e8c750beaaaa7ee9cea9d81ddeba2c` by run
`37705656407`. A filesystem-source selection and opposite Pictures Library
pane produce a bounded `DestinationMode::ShellProvider` request carrying the
accepted absolute destination PIDL. The v3 private wire transports this value
without moving any COM object into the app process. In the exact-owned transfer
helper, the PIDL must match the system `FOLDERID_PicturesLibrary`; the helper
loads `IShellLibrary`, reads its default save folder and requires its safe,
non-reparse filesystem path to equal `FOLDERID_Pictures`. Only then does it
check destination collisions and perform `IFileOperation::CopyItem` into that
concrete save folder. Other provider destinations and custom library save
locations remain fail-closed. The existing 1,024 item / 1 Mi UTF-16 source and
32 KiB provider PIDL limits, exact-owned Job Object, cancellation, progress,
stale-route checks and no-overwrite semantics remain in force. Provider Move,
Recycle/Delete and provider-to-provider Copy remain unsupported.

Final run `37705656407` reported request validation PASS, change-scoped FAST
PASS, GUI runner health PASS, canonical Release build PASS, source contract
PASS and focused two-pane GUI PASS. It observed
`SHELL_PROVIDER_COPYIN_DESTINATION_READY=True`,
`SHELL_PROVIDER_COPYIN_MOVE_REJECTED=True`,
`SHELL_PROVIDER_COPYIN_PASS=True`,
`SHELL_PROVIDER_COPYIN_SOURCE_PRESERVED=True`,
`SHELL_PROVIDER_COPYIN_OWNED_ITEMS_REMOVED=True`,
`SHELL_PROVIDER_COPYIN_LEGACY_SETTINGS_UNCHANGED=True` and
`SHELL_PROVIDER_COPYIN_PROCESS_EXIT=0`. The test used only prechecked,
test-owned files and removed its isolated fixture. The Shell watcher may replace
the transient success status, so byte verification and controller idle remain
the durable acceptance. No XAML/layout/icon changes were made. Actual arbitrary
third-party provider destination behavior is **NOT CERTIFIED**.

Removable-volume Recycle semantics are accepted on candidate
`a7b675f790356cc152c577a3d670e9829afdaae4` by self-hosted Remote
Windows Task `37456955994`. The rerun passed request validation,
change-scoped FAST, GUI runner health, the Release M22 native fixture at 30/30,
the canonical Release build and the existing file-operations GUI regression.
The native drive-policy contract now proves Copy, Move and Recycle accept
`DRIVE_REMOVABLE` local roots while all three remain closed to
`DRIVE_REMOTE`. Recycle still requires explicit user confirmation and the
Shell operation retains `FOF_ALLOWUNDO|FOFX_RECYCLEONDELETE`; no direct
permanent-delete API was added. The UI also states that an unavailable
removable-drive Recycle Bin does not fall back to permanent deletion.

The same run found the global Recycle Bin empty and therefore executed the
existing guarded owned fixed-drive recycle probe. It passed both
`OWNED_ACTUAL_RECYCLE_CONFIRMED True` and
`OWNED_ACTUAL_RECYCLE_RESTORE_CONFIRMED True`, restoring the synthetic file
and leaving the Recycle Bin empty again. Structured stages REQUEST_VALIDATION,
STATIC_PREFLIGHT, RUNNER_HEALTH and COMMAND are all PASS with no failure
category. Evidence artifact `11409896608`, digest
`sha256:bfa86cb617b384c711a626d65f2b5bb93ba412c7e277285d43105b90392107e7`,
preserves the remote result and logs.

Physical USB/removable-media Recycle execution is still not claimed because
the self-hosted VM currently exposes no `DRIVE_REMOVABLE` volume. Diagnostic
Remote Windows Task `37451622847` observed only C: as Fixed and D: as
CD-ROM. A future run with an attached disposable removable volume should
certify the actual Windows Recycle Bin behavior there; the product policy is
already fail-closed against permanent deletion fallback.

Large Icons default-view preservation for new Window Tabs is accepted on
candidate `e70f34b9c291eb2b4678af3ba2145bf25b36d76e` by self-hosted
Remote Windows Task `37454320102`. The run passed request validation,
change-scoped FAST, GUI runner health, an exact-main Release build and an exact
candidate Release build. With the same isolated `view=large-icons`
preference, the main baseline rendered the initial tab at 112x128 but the
Ctrl+T-created tab at 92x92, reproducing the Medium clamp. The candidate
rendered both the initial and newly created tab at 112x128 and emitted
`WINDOW_TAB_LARGE_ICONS_DEFAULT_PRESERVED True`. Structured stages
REQUEST_VALIDATION, STATIC_PREFLIGHT, RUNNER_HEALTH and COMMAND are all PASS.
Evidence artifact `11408587444`, digest
`sha256:6175b87438a52fa4fcb78dcdd70a50213b468c9caef8ccd18ddfb03942c497ba`,
contains matched BEFORE/AFTER captures. Direct visual review confirms the
baseline new tab uses visibly smaller Medium icons while the candidate keeps
the intended Large icon geometry without layout overlap.

Removable-volume Copy/Move policy was first accepted on candidate
`c229e1c0de072f2724c42094430524cd2b78c4f2` by self-hosted Remote
Windows Task `37451984855`. That run passed request validation,
change-scoped FAST, GUI runner health, the Release M22 native fixture at 29/29,
the canonical Release build and the existing file-operations GUI regression.
At that revision Copy and Move accepted `DRIVE_REMOVABLE` while Recycle was
still intentionally closed; the later removable-Recycle acceptance above
supersedes that temporary policy boundary.
Structured stages REQUEST_VALIDATION, STATIC_PREFLIGHT, RUNNER_HEALTH and
COMMAND are all PASS. Evidence artifact `11407200582`, digest
`sha256:aabbd9a19d4ef50aa50eb9dc7c57ddcf0a526ff37b114d8a48a69a92ba78093d`.

Physical removable-media execution is not claimed from that run. Diagnostic
Remote Windows Task `37451622847` found only C: as `Fixed` and D: as
`CD-ROM`; no `DRIVE_REMOVABLE` volume was attached to the VM. A future run
with an attached USB/removable volume should certify fixed↔removable and
removable↔removable Copy/Move without changing the current product policy.

UNC/network Copy/Move support is accepted at the product/harness boundary on
candidate `a08e32788bdcd5d33da31e0c413803f30e548b92`. The shared transfer
policy accepts `DRIVE_REMOTE` for Copy/Move but not Recycle, and the pure root
classifier accepts ordinary `\\server\share\...` roots while rejecting
`\\?\` / `\\.\` device namespaces. Copy/Move now uses the helper's
explicit `--file-transfer` mode with a bounded private wire, restricted
inherited handles, a one-process kill-on-close Job Object and inherited
cancellation event; Recycle remains on the local-only in-process STA path.

Remote run `37553534009` passed FAST, helper Debug build and the M22 Debug
native fixture at 33/33. Run `37553699165` passed the M22 Release native
fixture at 33/33 and the canonical Release build before the older broad
physical-input GUI harness refused input because no owned foreground window was
available. Diagnostic run `37554219584` confirmed that desktop condition.
The UIA-only successor initially used a stale transient-status assertion:
direct diagnostic run `37555732127` proved that Copy had committed, the
controller was no longer busy (`Cancel` disabled, mutation controls enabled)
and the normal directory watcher had already replaced the short-lived
"복사를 완료했습니다." text with "폴더 변경 알림을 반영했습니다.". After changing
only that harness assertion, final run `37556148841` passed FAST,
`git diff --check`, canonical Release build and focused UIA-only local
Copy/Move through the isolated helper. No XAML/pixel behavior changed.

Actual SMB/UNC transfer execution is **not claimed**: the runner's
`\\127.0.0.1\C$\...` owned loopback probe reports the admin share
unavailable, and no disposable SMB share is attached. Mapped network-drive
execution is likewise not separately certified.

Metadata-sort correctness and metadata/detail separation were first accepted
on candidate `1857330605c8ab27b2c0ea6ce91b279e71f13607` by self-hosted
Remote Windows Task `37447176742`. That revision established fixed-drive
correctness; the later removable-metadata acceptance above extends the same
sortable metadata lifecycle to local removable drives. The run passed request
validation, FAST static preflight, GUI runner health and the canonical Release
build, then ran
the same Release executable in three input-free owned processes over a
1,305-file fixture. It passed
`METADATA_SORT_OVER_1200_SIZE_DESC True`,
`METADATA_SORT_OVER_1200_DATE_DESC True` and
`METADATA_SORT_OVER_1200_TYPE_ASC True`; every owned process exited 0 and
the protected legacy settings remained byte-identical. The structured result
records REQUEST_VALIDATION, STATIC_PREFLIGHT, RUNNER_HEALTH and COMMAND all
PASS with no failure category. Evidence artifact `11404416210`, digest
`sha256:5a89904eee3f53d5fac678593974f4dcad1329a0e3445fe4c6f78698f291a8b3`,
preserves the remote result/logs and AFTER capture.

The VM AFTER screenshot is not used as final visual-review evidence because the
runner console overlapped the application during screen capture. The clean
matched metadata-sort visual evidence remains the earlier hosted artifact
`11397685869`: BEFORE shows the legacy >1,200 size-sort request leaving
`aa-type-last.zzz` first by name, while AFTER shows
`zz-size-winner.bin` first at 8 KB. That earlier run is visual evidence for
the ordering change only; its later date-sort assertion failed and is
superseded for functional correctness by Remote Windows Task
`37447176742`.

Explorer-aligned F5/F6 semantics are accepted on candidate
`4e59a22c742c7fa8d5d0e21e221f01ff8151e2be` by Remote Windows Task #473
(`37414193732`). The run passed FAST, runner health and the canonical Release
build, preserved a complete Release runtime cache, then passed the focused owned
GUI with `REAL_F5_REFRESH_NO_FILE_MUTATION True`,
`REAL_F6_DUAL_PANE_FOCUS_NO_FILE_MUTATION True` and
`SHORTCUT_GUI_ACCEPTANCE=PASS`. The structured remote result records
REQUEST_VALIDATION, STATIC_PREFLIGHT, RUNNER_HEALTH and COMMAND all PASS.

High Contrast ON is now accepted on merged product revision
`eaa1b368a677f57c15183c5e6851f0598ed25878` via PR #16. Final candidate
`bd13f3c68a12d3bdd111a0171a70f17ef3b6f8de` passed source contracts
258/258 and actual Windows High Contrast ON GUI/visual acceptance in remote run
`37252987127`. The owned acceptance verified selected-row UIA state, expanded
search-surface controls, protected legacy user settings unchanged, and restored
High Contrast to OFF after the run. Direct screenshot review confirmed readable
tabs, command/address/search chrome, sidebar, dual panes, selected rows, search
fields, checkboxes, combo boxes, buttons and separators without blocking overlap
or same-color loss. Final evidence artifact: `11321836100`,
digest `sha256:0662bdd402093ad184fea08653c32fee523ecf54225aaef99a8fd0364a1e6a19`.

Sequential resident-window browsing beyond the former 20,000-entry complete-model
ceiling is accepted on product work revision
`924a035e244fb547662bedb7094f45b543396a36`. The Shell transport now has two explicit
bounds: `kMaxCompleteModelEntries=20000` for operations that require a complete
model, and `kMaxBrowseEntries=100000` as a bounded safety ceiling for normal
resident-window navigation. Normal browsing still keeps at most 2,048 children
resident; increasing the browse frontier does not increase the resident-model
bound.

At this historical work revision, operations requiring full Shell metadata
were not allowed to silently operate on a partial model above 20,000 entries.
Type, size and modified-date global sorts then refused above that ceiling;
a later local fixed-drive-only indexed metadata implementation superseded this
restriction for eligible folders (see Known functional coverage limits).
Name sort and name filtering were the deliberate exception at this checkpoint: navigation retains a
lightweight label/parsing-name/attribute index while resident Shell children
remain bounded, and projects that completed index for global name operations.
The 100,000 browse/index value remains an implementation safety bound, not a
100,000-item performance or compatibility certification.

Run `37183718932` passed source contracts 228/228, the canonical Release
build, and the real helper process regression including
`REAL_NATIVE_HELPER_OFFSET_OVER_COMPLETE_MODEL_PASS True`. Its long 20.5k GUI
probe then failed only because the harness retained a stale UIA load-more
wrapper after repeated WinUI rerenders. A later harness-only correction changed
no product file. Final focused GUI/visual resume run `37184906352` passed on
the same built product behavior and reached logical progress `20480` in an
owned 20,500-file folder, kept backward resident-window navigation available,
and proved the earlier pre-index refusal behavior; protected legacy settings
remained unchanged.

Follow-up PR #15 supersedes that name-operation limitation. Final integrated
candidate `6936fba97d2e18ac81115b5d02b84db7e90472dd` passed source contracts
241/241 and the owned 20,500-file GUI/visual acceptance in run
`37211942616`. The run proved `OWNED_LARGE_OVER_20K_NAME_SORT_INDEXED True`,
`OWNED_LARGE_OVER_20K_NAME_FILTER_INDEXED True`,
`OWNED_LARGE_OVER_20K_SIZE_SORT_REFUSED True`, normal legacy-settings
preservation, and the actual indexed filter projection of `bench-20499.txt`
with footer count 1. The accepted feature was squash-merged to main as
`582560f89afe8c9c53bbc23791cdbd5d3335c014`. Dark-theme 956x521 final-pixel
review found no blocking overlap, clipping or pane regression.

The folder-tab clipping reported above the Name header is also fixed in this
unit. `LeftTabs` and `RightTabs` now use 36 px instead of the too-tight
28 px height. Matched 956x521 Dark-theme evidence shows the former
`2300-files` caption vertically clipped in BEFORE and fully visible in AFTER,
with the Name/Type/Size header row, resident-window progress control and the
opposite pane remaining aligned. The 20k+ AFTER evidence likewise shows the
`20500-files` caption fully visible. `VISUAL ACCEPTANCE: PASS`.

Bounded large-folder resident-window navigation is accepted on the product
tree prepared at work revision `37d4cc023777c67a963710efd2e17ee7125a7cae`, with the final
harness-only follow-up at `1c5779448a8cb194ff1a506ccfdd7cf0239f8222`. Normal unsorted,
unfiltered browsing keeps at most 2,048 Shell children resident. Moving forward
can evict the oldest prefix while preserving the logical enumeration frontier;
an app-owned previous-window action requests the exact missing offset range and
rehydrates that prefix. Moving forward again rehydrates the known tail rather
than advancing the folder frontier twice.

Operations that require the complete bounded model keep their prior semantics.
A non-empty pane filter or global sort first rehydrates an evicted prefix and
any known resident gap, then continues to the folder end or the existing
20,000-entry navigation ceiling before producing the final result. The
20,000-entry ceiling itself is unchanged; 20,000+ browsing is still not
certified.

Acceptance run `37182310190` passed source contracts (227/227), the canonical
Release build and the real isolated-helper offset/limit process regression.
Its target GUI path proved a 2,300-file folder evicted exactly 252 entries from
the front at a 2,048-entry resident bound, restored the prefix through the
previous-window action, rehydrated the tail, and rebuilt all 2,300 entries for
global descending-name sort. That run then failed only because the focused
harness incorrectly fell through into an unrelated fresh-view `160/2300`
assertion after every target marker had already passed. The harness-only
revision changed no product file. Resume run `37182611109` reran only the
invalidated GUI/visual boundary and passed
`OWNED_RESIDENT_WINDOW_EVICTED_PREFIX_252`,
`OWNED_RESIDENT_WINDOW_PREVIOUS_REHYDRATED_PREFIX`,
`OWNED_RESIDENT_WINDOW_FORWARD_REHYDRATED_TAIL` and
`OWNED_RESIDENT_WINDOW_GLOBAL_SORT_REBUILT_2300`, with protected legacy
settings unchanged.

Matched Dark-theme visual evidence is 956x521 for both BEFORE and AFTER. BEFORE
at logical progress `2208/2300` shows `bench-0000.txt` with no previous
control. AFTER at the same logical progress shows the compact previous action,
`2208/2300+`, and resident start `bench-0252.txt`. Direct review found no
header overlap, clipping, pane corruption or column displacement. The opposite
pane remained unchanged. `VISUAL ACCEPTANCE: PASS`.

Selection identity remains logical rather than resident-vector based. Selection
for rows still resident across a window move can be restored by parsing path;
a row that has been evicted is no longer selected until its window is reloaded.
No cross-window hidden selection is claimed.

Model-level large-folder page streaming is accepted on product revision
`f7f3674e5271c17652a865cf2ed499185983d1eb`. Protocol-v3 Shell transport remains bounded to 1,024 entries
and 8 MiB per helper response, while the active navigation model now accepts the
first page immediately and appends validated continuation pages on demand rather
than waiting for the supervisor to aggregate the whole folder first. The WinUI
list remains render-paged at 160 rows and marks incomplete models with a `+`
suffix. Global sort and non-empty pane filtering complete the bounded streamed
model before producing final results. The existing 20,000-entry safety ceiling
remains in force.

Evidence: remote run `37177222154` passed canonical structure 4/4, source
contracts 223/223, the canonical Release build and the real protocol-v3 helper
regression. An owned Release folder with 8,000 files first rendered its 1,024
loaded items in 2.71 seconds, then the existing GUI path completed continuation
pages for global name-descending sort and reached `bench-7999.txt`.
`OWNED_LARGE_MODEL_STREAMING_INITIAL_1024` and
`OWNED_LARGE_MODEL_STREAMING_SORT_COMPLETES_8000` both passed, protected
legacy settings remained unchanged, and `git diff --check` passed.


Paged isolated Shell enumeration beyond the former 6,000-entry single-frame
ceiling is accepted on product revision `fb92b9dd03c90ce3e3434270bff3cc5be8714cad`. Wire protocol v3
limits each disposable helper response to 1,024 entries and 8 MiB, while the
supervisor requests successive offset pages and aggregates at most 20,000
entries for one navigation snapshot. Existing cancellation/supersession,
per-page watchdog/retry, PIDL/checksum validation and exact-owned child process
boundaries remain intact. WinUI rendering remains progressive at 160 visible
items initially and 160-item increments.

Evidence: the first pre-main run `37174851727` exposed only a stale source
assertion tied to the old supervisor local variable; product code was unchanged.
After that test-only correction, run `37174929070` passed canonical structure
4/4, source contracts 218/218, canonical Release build, the real helper
protocol-v3 process-isolation suite including offset/limit page requests, and an
owned Release folder containing 8,000 files. The GUI reached first render in
6.17 seconds, sorted name-descending to the final owned file, passed the
160/8000 -> 320/8000 controlled render-page assertions, kept legacy settings
unchanged and emitted
`OWNED_LARGE_FOLDER_OVER_6000_PAGED_TRANSPORT True`. `git diff --check`
passed.


Explicit legacy content encodings are accepted on product revision
`44305357394c8eed76eaaa31614ecaddaca7f4c3`. Bounded literal content search keeps deterministic Auto UTF
behavior (UTF-8/ASCII plus BOM UTF-16 LE/BE) and adds explicit Korean CP949 and
Western Windows-1252 decoding for BOM-less text. BOM detection has priority over
the selected fallback. The existing 1 MiB/file, 16 MiB/search and 64 KiB
cancellation boundaries are unchanged. At that revision, saved search presets
wrote schema 3 with the content encoding and read schema 1/2; the current schema
is 4 after bounded content regex support.

Evidence: remote run `37173754944` passed canonical structure 4/4, source
contracts 218/218, Release M19 native contracts 47/47, canonical Release build
and a focused existing M1.9 owned GUI path. Real GUI checks passed Auto-UTF
rejection of CP949, explicit CP949 matching, explicit Windows-1252 matching,
return to Auto UTF, encoding-aware preset restart/apply, protected legacy
profile checks and process exit 0. `git diff --check` also passed. The initial
automation-selected CP949 screenshot was not accepted for visual review because
the closed ComboBox label had not repainted; visual-only run `37174155301`
then captured the ordinary default state at the same 956x689 Dark-theme size,
showing `자동 UTF` and the selector without clipping/overlap while both panes
remain usable.


Bounded content regex is accepted on product revision
`17c54dfda87e978bad155041929be0e5776f40ef`. The Search panel exposes a
separate `내용 정규식` checkbox so filename regex semantics stay unchanged.
Decoded content is matched by `src/base/bounded_regex.*`, a non-backtracking
NFA with at most 1,024 states and a 4,194,304-state-visit limit per file;
cancellation is checked inside the matcher. Invalid syntax and unsupported
lookaround/backreferences are rejected before worker creation. Ordinary groups,
non-capturing groups, alternation, dot, character classes, `* + ? {m,n}`,
and `^ $` are supported. Existing 1 MiB/file, 16 MiB/search and 64 KiB read
cancellation boundaries remain intact. Search presets write schema 4 with the
content-regex flag and retain schema 1-3 read compatibility.

Evidence: run `37547158373` passed change-scoped FAST and Debug M19 native
contracts at 53/53. Run `37547329626` subsequently passed the Release 53/53
native gate and canonical Release build before failing only in the older
physical-input GUI harness. Successor run `37548113347` passed FAST,
canonical Release build and the focused UIA-only content-regex GUI. Final
candidate run `37549364386` passed FAST, Release build, the focused
content-regex GUI and the owned XAML visual gate at
`17c54dfda87e978bad155041929be0e5776f40ef`; the rendered 960x608 Search panel
shows the 245px content box, `내용 정규식` checkbox and encoding selector in
order without clipping or overlap. The owned process exited 0. The earlier
baseline screenshot retries `37535152549`, `37535465831`, `37538550263`
and `37546086877` were harness-only failures (dirty persistent checkout,
window discovery, physical cursor input, and ImageGrab respectively) and do
not represent product failures; the unchanged pre-feature Search XAML visual
evidence was reused per evidence-reuse policy.


Bounded literal content search is accepted on product revision
`eb612e6ef81e168e95cc5c00284eaf890157497b`. Search now AND-composes an optional literal file-content term
with the existing name/regex, extension, size, local modified-date and target
criteria. UTF-8/ASCII and BOM-tagged UTF-16 LE/BE are supported; unmarked
NUL-containing files are skipped as binary. Reads are bounded to 1 MiB per file
and 16 MiB per search, with 64 KiB cancellation checkpoints. Folder-only
content search is rejected before worker start. At that literal-content
revision, saved search presets wrote schema 2 with the content term and read
schema 1; the current schema is 4.

Evidence: remote run `37172317827` passed canonical structure 4/4 and source
contracts 212/212; its only later failure was an isolated native-fixture token
mismatch at 39/40. After a test-only correction, run `37172446492` passed the
Release M19 native gate at 40/40, canonical Release build, real UTF-8/UTF-16
owned-GUI content search, folder-only rejection, content-preset
save/restart/apply/delete, protected legacy-profile checks and owned WinUI exit
0. A later unrelated broad shell-harness tail could not resolve `LeftFiles`
after the content-search section had already completed. Final focused run
`37172732023` succeeded with `git diff --check` and matched 956x689
BEFORE/AFTER Dark-theme evidence; direct review found no clipping/overlap and
both panes remained usable.


Search v3 compound metadata criteria are accepted on product revision
`b7e6873407016e8a3e9cceb3e397a81d71b7e0c5`. Bounded search now AND-composes optional integer-KB minimum/
maximum file size and inclusive local modified-date bounds with the existing
name/regex, case, target and extension criteria. A name term may be empty when
another criterion is supplied. Up to 20 named condition sets are persisted
privately and atomically in
`%LOCALAPPDATA%\flyExplorer\search-presets-v1.txt`; scope is intentionally
not saved.

Evidence: remote run `37170399569` passed canonical structure 4/4, source
contracts 205/205, Release M19 native Search v3 contracts 29/29, canonical
Release build and the established owned M1.9 GUI harness, including compound
AND matching, size-only empty-term search, invalid range rejection, preset
save/restart/apply/delete, legacy-profile protection and process exit 0.
The initial unmatched-height screenshot was rejected as visual evidence.
After correcting clipped date hints, run `37171067880` passed the focused
Search v3 contract 6/6, canonical Release build and fixed 956x689 visual
capture; direct review found no clipping/overlap and both panes remained usable.


Persistent pane filter presets are accepted on product revision
`a7490083000ac8faeb6c4fbe2cf54fecd6b00cf8`. Up to 20 named rules are stored privately and atomically in
`%LOCALAPPDATA%\flyExplorer\filter-rules-v1.txt`. Existing case-insensitive
substring pane filtering remains compatible; `*`, `?` and `;` enable
case-insensitive wildcard mask sets such as `*.cpp;*.h`.

Evidence: remote run `37168744531` passed source contracts, Release M20 native
state contracts at 48/48 and the canonical Release build. Final focused GUI run
`37169304880` passed save/apply, wildcard matching, substring compatibility,
restart persistence, delete, legacy-profile protection and exit 0.
BEFORE/AFTER visual evidence was exported in run `37169509814` and reviewed at
1060x760, 96-DPI VM, Dark theme with no clipping or overlap introduced by the
new two-row preset panel.


Search v2 is accepted on product revision `1fc808f91fa2236890a0025a555ccbd0d922319c`. Focused source
contracts passed before product execution. Remote run `37166780382` passed the
Release M19 native suite at 19/19 and the canonical Release build. Remote run
`37167164976` then exercised the same product through the established M1.9
owned GUI harness: default file-only literal search, case-sensitive regex,
Korean filename plus extension filtering, folder-only targeting and invalid
regex rejection all passed. Existing recent-scope opt-in save/restart/clear
behavior also passed, the WinUI process exited 0 and the protected legacy
profile remained unchanged. Repeated standalone SearchPanel discovery failures
were treated as a fixture boundary and abandoned rather than retried.

Historical transport-paging evidence remains recorded on product revision
`fb92b9dd03c90ce3e3434270bff3cc5be8714cad`: protocol-v3 introduced 1,024-entry / 8 MiB helper pages and
run `37174929070` proved an owned 8,000-file folder before model-level
streaming landed. That older revision aggregated pages in the supervisor; it is
not the current architecture.

Current main builds on the later `f7f3674e5271c17652a865cf2ed499185983d1eb` model-level streaming
path described above. Normal sequential browsing now bounds resident children
to 2,048 and can rehydrate exact previous/known-forward ranges while retaining
the furthest validated logical frontier. Full-model global sort and non-empty
filter semantics are preserved by rebuilding the bounded complete model before
final results. The 20,000-entry navigation safety ceiling remains in force, so
20,000+ browsing is not yet certified.

Persistent WinUI bookmarks are accepted on main. Automatic Windows run
`37133980876` completed successfully for main revision
`85b20db79ab61742bb9cca2057c5afab696574cf`: policy/source gates passed,
Release native state contracts passed, the canonical Release build passed, the
owned Release GUI suite passed with normal process exit, and the Release runtime
set passed. This closes the bookmark logical unit together with the focused
pre-main functional and visual evidence below.

At the time of this bookmark acceptance, the repository used its
dedicated Remote Windows Task and Windows VM Build workflows. They were
retired on 2026-10-10; use `personal-control-plane` for current requests.
The current retry rule forbids automatic or speculative same-revision
reruns: classify the first relevant failure and change the invalidated
product, harness or execution condition before a successor run.

Persistent WinUI bookmarks were pre-main validated on work revision
`3ea29587c973d879f1ad2236f4354794b1a81d62`. The final focused product
steps in remote run `37131861647` completed before an unrelated temporary
evidence-branch cleanup command failed: canonical structure 4/4 PASS, source
contracts 187/187 PASS, owned bookmark add/rename/delete/legacy-import PASS,
restart persistence PASS, protected legacy user configuration unchanged and
`git diff --check` PASS. Earlier run `37130545208` independently established
the same product revision's Release M20 native bookmark/state fixture at 36/36,
canonical Release build PASS and the pre-existing full owned Release GUI suite
PASS with process exit 0.

Visual acceptance was re-captured after rejecting an earlier background-window
screenshot as invalid evidence. Successful remote run `37132254625` forced
the process-owned flyExplorer HWND to the foreground for both exact-main BEFORE
and bookmark AFTER captures at 972x720, 96 DPI and Dark theme. Both windows
reported title `flyExplorer · 북마크원본`; direct review confirms that the new
single-row bookmark bar places the saved folder at the left and compact
add/manage actions at the right without overlap, clipping or pane corruption.
The dual panes shift downward only by the new row height.
`VISUAL ACCEPTANCE: PASS`.

Sidebar Known Folder artwork is accepted on product revision
`02e46d3e2133e3e30bfeca0803af39222a93c7bd`, with policy/test-reviewed main
revision `559129d7c73c2867371f762b6d5480e41280795e`. Automatic self-hosted
Windows run `37123115476` completed successfully on 2026-10-03 with resolved
scope `release-gui`:
- policy validation: PASS;
- canonical structure preflight: 4/4 PASS;
- source contracts: 181/181 PASS;
- Release M20 native state fixture: 26/26 PASS;
- canonical Release app build: PASS;
- owned Release GUI validation: PASS with
  `REAL_M23_PRIVATE_SESSION_CLEAR_REVOKES_FUTURE_AUTO_RESTORE True`,
  `OWNED_WINUI_SHELL_EXIT 0` and
  `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`;
- Release runtime-set verification: PASS.

Focused visual acceptance run `37122383954` compared pre-sidebar revision
`e0b992edf0ac238ff84a265e5d389481513b1505`, the changed product and Windows
11 Explorer under the same 972x720 Dark-theme VM conditions. All six sidebar
Known Folder artwork images were visible at 16x16, the reviewed contact sheet
matched Explorer's folder-specific navigation motifs, and the run reported
`SIDEBAR_VISUAL_ACCEPTANCE_PASS` plus
`SIDEBAR_KNOWN_FOLDER_VISUAL_PASS`.

Known Folder file-list artwork is accepted on product revision
`e40a11c0dbfc135ae9ab73fa9036d10d672406dc`, with policy-reviewed main revision
`f0234867f61678ec1d3cfd7d0974b320d0879759`. Automatic self-hosted Windows run
`37115826127` completed successfully on 2026-10-03 with resolved scope
`release-gui`:
- policy validation: PASS;
- canonical structure preflight: 4/4 PASS;
- source contracts: 177/177 PASS;
- Release M20 native state fixture: 26/26 PASS;
- canonical Release app build: PASS;
- owned Release GUI validation: PASS with
  `REAL_M23_PRIVATE_SESSION_CLEAR_REVOKES_FUTURE_AUTO_RESTORE True`,
  `OWNED_WINUI_SHELL_EXIT 0` and
  `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`;
- Release runtime-set verification: PASS.

Focused visual acceptance run `37118042729` compared the pre-change main
`b2a70dcdd217f3af17dada304deaff2c27f9d401`, the accepted product and Windows
11 Explorer under the same VM, Dark theme, Large Icons and 972x720 window.
Before the change all six Known Folders shared one generic folder-icon hash;
after the change Desktop, Documents, Downloads, Pictures, Music and Videos
produced six distinct native artwork hashes. The reviewed contact sheet matched
Explorer's folder-specific color/symbol motifs, while both flyExplorer runs
exited with code 0.

Large Icons is accepted on product revision
`aafa1615048c61aade0cd1c544990735ddb89a15`, with policy-reviewed main revision
`8fedf10aa3ead00b9488be0176da08dcd419ddf6`. Automatic self-hosted Windows run
`37110339453` completed successfully on 2026-10-03 with resolved scope
`release-gui`:
- policy validation: PASS;
- canonical structure preflight: 4/4 PASS;
- source contracts: 174/174 PASS;
- Release M20 native state fixture: 26/26 PASS;
- canonical Release app build: PASS;
- owned Release GUI validation: PASS with
  `REAL_M23_PRIVATE_SESSION_CLEAR_REVOKES_FUTURE_AUTO_RESTORE True`,
  `OWNED_WINUI_SHELL_EXIT 0` and
  `ORIGINAL_SIX_USER_CONFIG_SHA256_IDENTICAL True`;
- Release runtime-set verification: PASS.

The Large Icons acceptance used an owned Windows 11 Explorer baseline at
972x720, 96 DPI and Dark theme. Explorer Large Icons measured about 105x131 px
per UIA item with roughly 118x132 px pitch. flyExplorer uses a 112x128 item in a
120x132 wrap slot, retaining a 64 px visual target and two-line label while
keeping dual-pane density practical.

The PreferencesCoordinator logical unit was pre-main validated on temporary
remote run `37096260604`: focused coordinator contracts 2/2 PASS, canonical
structure 4/4 PASS, source contracts 154/154 PASS, Release build PASS, full
owned Release GUI PASS, real process exit 0, protected user configuration
unchanged and `git diff --check` PASS.

Earlier FileDetailController evidence remains valid for its own unchanged
revision. The broader Debug/package/install evidence from run `37020993308`
remains historical and was not rerun for this behavior-preserving architecture
work. DPI scaling, accessibility, physical drag, signing and public
distribution remain separate gates.

## Known functional coverage limits

Current source and the last parity evidence still show these limits:
- Local filesystem Shell enumeration uses protocol-v3 page transport:
  1,024 entries per isolated helper response, an 8 MiB per-response body bound,
  and a 20,000-entry complete-model bound. Sequential navigation has a
  separate 100,000-entry safety ceiling and 2,048-entry resident window.
  The active model accepts the first page immediately and appends
  continuation pages on demand. Owned Release evidence covers an 8,000-file
  initial 1,024-item render followed by global name sort and progressive
  160-row rendering. Indexed name sort/filter have separate 20,500-item
  acceptance. Local fixed-drive indexed size/date/type sorts have a separate
  20,500-item acceptance; the 25,000-item indexed metadata ceiling is an
  implementation bound, not a 25,000-item performance certification.
  General 100,000-item throughput, above-20,000 metadata sorting on
  removable/network/virtual roots and sustained thumbnail-cache behavior
  remain unverified or unsupported as specified below.
- Type, size and modified-date global sort uses a complete sortable metadata
  model for up to 20,000 fixed, removable, mapped-network or ordinary direct-UNC
  filesystem entries. For local fixed-drive folders only, a distinct indexed
  metadata mode can sort beyond 20,000 without making the resident model complete:
  its bounds are `kMaxIndexedMetadataEntries=25000` and
  `kMaxIndexedMetadataPathUnits=12*1024*1024`. Exact owned 20,500-file
  size/date/type GUI acceptance passed in `38055029443`; the 25,000 ceiling
  is not a verified 25,000-file performance result. Removable, UNC, mapped
  network and virtual/provider roots still refuse these metadata sorts above
  20,000. Network/UNC metadata collection is isolated in an exact-owned helper
  with bounded inactivity and cancellation handling. Actual SMB/UNC and
  mapped-drive execution remains NOT TESTED in recorded real-device evidence;
  the retired dedicated runner lacked a test-owned SMB share. The former 1,200
  visual-detail ceiling does not control complete-model metadata sorting,
  and 1,201-20,000 entries no longer silently use name order.
  Shell visual/type/icon/thumbnail enrichment remains separately bounded to
  1,200 items and supports local fixed/removable, mapped-network and ordinary
  direct-UNC filesystem roots; virtual Shell/provider roots support bounded
  type/icon enrichment plus up to four thumbnails in Medium/Large Icons.
  Actual physical USB/removable and SMB/mapped-drive visual execution remains
  NOT TESTED in recorded hardware evidence: the retired dedicated runner had
  neither a removable volume nor a test-owned SMB share. Recheck current central
  VM hardware availability before running those gates. Third-party providers
  are not certified by the built-in This PC/Pictures Library acceptance.
  Physical USB metadata-sort execution also remains NOT TESTED.
- Filesystem Copy/Move accepts local fixed/removable roots, mapped
  `DRIVE_REMOTE` roots and ordinary direct UNC paths through the shared Shell
  transfer core. Virtual Shell/provider sources additionally support bounded
  **Copy-out to a real filesystem destination** using accepted snapshot PIDL
  value bytes and helper-owned `SFGAO_CANCOPY`/direct-child/collision
  revalidation. A separate bounded filesystem-source Copy-in path now accepts
  the Windows built-in Pictures Library when its exact accepted destination
  PIDL and default save folder resolve to the user's Pictures Known Folder;
  other provider destinations/custom save folders remain unsupported.
  Provider Move, provider-to-provider Copy and Recycle/Delete remain
  unsupported, as do extended/device namespaces. All Copy/Move Shell
  mutation stays in the exact-owned transfer helper so a blocking Shell call is
  outside the flyExplorer process and can be terminated through its owned Job
  Object after cancellation grace. Recycle still accepts only local
  fixed/removable roots, requires explicit confirmation and uses recycle-only
  Shell flags; if a removable drive cannot use Windows Recycle Bin, flyExplorer
  reports failure and does not switch to permanent deletion. Physical
  USB/removable execution is still NOT TESTED in recorded physical-device
  evidence (the retired dedicated VM lacked a removable volume).
  Actual SMB/UNC and mapped-network-drive Copy/Move execution also remains
  NOT TESTED; the retired runner lacked a test-owned SMB share. The current
  central VM's device/share inventory must be checked for any new gate. Provider
  Copy-out runtime acceptance covers the built-in Pictures Library virtual root
  with a test-owned filesystem-backed child; arbitrary third-party/provider-only
  child behavior remains uncertified.
- Search remains bounded but no longer stops at the historical 2,500-entry,
  depth-5 and 100-retained-result limits. Filesystem traversal now visits up to
  20,000 entries at depth 32 and retains the first 1,000 matches while
  continuing to count later matches. The UI distinguishes a display cap from a
  traversal cap. Filename regex, case sensitivity, entry-kind,
  single-extension, minimum/maximum file size, inclusive local modified-date,
  literal text content and bounded content-regex conditions are implemented
  with up to 20 private saved condition sets. Content reads remain limited to
  1 MiB per file and 16 MiB per search, using Auto UTF (UTF-8/ASCII plus
  BOM-tagged UTF-16) or explicit CP949/Windows-1252. Content regex uses a
  non-backtracking project-owned matcher capped at 1,024 states and 4,194,304
  state visits per decoded file; lookaround/backreferences are unsupported and
  rejected before worker start. Presets write schema 4 and continue to read
  schemas 1-3. Windows Search indexed filename search is an explicit second
  mode for case-insensitive literal file names on non-reparse fixed-drive
  filesystem scopes. It queries SystemIndex through the exact-owned
  FlyShellIsolationHelper process, caps returned paths at 1,000 and total
  wire data at 1 MiB, rejects indexed-mode regex/content/folder/provider
  criteria while allowing optional integer-KB file size and inclusive
  YYYY-MM-DD modified-date lower/upper bounds, and never silently falls back to filesystem traversal. Cancellation,
  12-second deadline, one-process kill-on-close Job Object, stale-result and
  route-token rejection remain active. An unindexed scope can legitimately
  return zero entries; an unavailable provider or timeout has a distinct
  status. Indexed filename GUI acceptance: Windows task 37712395449,
  source ef6618cd478a6cadad56eb3bdce026b7e9541d02, positive result
  count 1 against independently queried native index oracle, source
  unchanged, normal process exit. Property/provider indexed search and
  traversal beyond the current 20,000/depth-32 safety bounds remain
  unsupported. Visual layout acceptance: PASS on matched actual app-owned
  RenderTargetBitmap captures. Baseline main
  `387efa622f6a9ce6685e3bffb98299df0503de3c` was rebuilt and captured
  in run `37718045551`; indexed candidate
  `ffc2466be51c32c1cf7454a2df80fe4f8c3f5f99` was captured in
  `37717788614`. Direct inspection plus metrics run `37718272601`
  found both 956x711 pixels under fixed 972x720 HWND/Dark conditions.
  113,339 of 679,716 pixels differed (16.6745%), largely from the new
  indexed-mode row and downstream pane repositioning. Both panes,
  sidebar, action chrome, file row and footer remained visible without
  blocking overlap or clipping. The asynchronous capture recorded
  different transient search-scope field contents and randomized
  test-owned path text; those pixels are not claimed identical.
  Higher-DPI and additional selection/theme visual states were not
  separately exercised in this focused gate.
- Persistent pane filter/mask rule sets support up to 20 named private
  presets, case-insensitive wildcard masks and legacy substring compatibility.
  Named rules now also support opt-in blue/green/amber/red filename accents
  and star/pin/flag/tag classification badges. These styles decorate matching
  file rows without replacing the existing name/mask filtering or Shell icons.
  Actual 96-DPI light-theme and scoped High Contrast visual acceptance is
  recorded in the current index above; other OS scales remain untested.
- The complete historical command/provider verb/fault matrix is not fully
  implemented or tested.
- User-configurable accelerators and a complete historical shortcut map are
  not implemented. The current product has a bounded Explorer-aligned shortcut
  subset. Plain F5 refreshes only the active pane/tab; plain F6 is non-mutating
  dual-pane focus traversal and switches to the opposite pane when split view
  is active. Historical flyExplorer F5/F6 copy/move semantics are intentionally
  not active defaults. Historical flyExplorer F11 still conflicts with current
  Windows/File Explorer maximize/restore behavior and requires a separate
  compatibility decision rather than silent remapping.

## Packaging and source identity state

The **historically retained** unsigned package and exact binary/source
identity were accepted by Remote Windows Task #440 (`37376305779`).
They are not artifacts built from the latest main. The binary source revision is
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60`, with source tree
`8f1bc2e0181cc87e646dd2fad75ccdca0c8e8a66`.

One clean canonical Release build generated and immediately re-verified runtime
provenance before `package.bat Release` consumed that same byte set. The
runtime contains 305 files: 17 product/generated files and 288 exact NuGet byte
matches. Runtime manifest SHA-256:
`61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`.

The resulting unsigned setup contains a 326-file payload and is 124,107,776
bytes. Setup SHA-256:
`825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.

The deterministic source bundle contains all 382 tracked blobs from the exact
binary source revision, totaling 3,942,910 source-file bytes. Source ZIP
SHA-256:
`5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`.
Its tracked manifest is `packaging/SOURCE_BUNDLE_MANIFEST.json`; the setup,
runtime provenance and source-bundle hashes are bound by
`packaging/RELEASE_IDENTITY.json`.

The bounded `/TESTROOT` lifecycle passed clean install, same-version repair
including stale-manifest cleanup, update, rollback and uninstall. Clean,
update and rollback launches all observed owning-process exit after `WM_CLOSE`.
The #440 Actions artifact
`flyexplorer-remote-evidence-37376305779` preserves the concrete setup,
source ZIP, source manifest, runtime provenance and release identity together.

Run #439 is not acceptance evidence. All product/package/source checks passed,
but the control harness used a nonexistent evidence-directory environment
variable after lifecycle completion and failed before preserving the release
artifacts. #440 changed only that evidence destination to the workflow's
canonical `logs\remote-evidence` path and completed successfully.

This closes the technical exact binary-to-source identity gate **for that
historical unsigned artifact only**. A newer private audit
[38210591849](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38210591849)
checked the unsigned setup, 305-file runtime and 438-file source bundle for
source `2a736d85b22859a770138e4b50926ac125d1a052`, but its test-owned
setup/source ZIP were removed after the audit. Tracked release manifests
still identify `bc63c8b...`, not the newer product or current main.
A final release requires retained, reverified matching assets.

The public distribution mechanism is now selected as GPLv3
section 6(d) same-release-page network access, and the reserved final tag is
`v1.0.0.0`. Repository-level GitHub Immutable Releases was enabled in Remote
Windows Task #446 (`37379026246`). The tag is intentionally absent before
publication because the current private-repository plan cannot protect
pre-created tags with a tag ruleset; the completed draft release will create/
adopt and lock the tag when published.

The project retention policy keeps matching Corresponding Source publicly
available for the complete binary-availability period and at least 1095 days
after the binary is withdrawn. This is an additional project commitment; GPLv3
section 6(d) itself does not specify a fixed three-year duration.

These decisions do **not** make the private source ZIP publicly available,
certify production Authenticode signing, certify clean-machine Program Files/
HKLM machine-wide lifecycle, or clear rightsholder/legal review.

## Open gates

Not certified by current automated evidence:
- actual 125%, 150% and 200% OS display scaling (the current central
  Windows desktop inventory recorded 1024x768 at 96 DPI in
  [38218827761](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38218827761));
- actual spoken Narrator filter labels/selection and audio playback (the
  synthetic Recap diagnostics remain inconclusive, despite safe cleanup);
- broader Korean IME layouts/controls beyond the specifically accepted
  real two-beolsik `한글` composition and persisted filter-rule save
  in [38227421736](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38227421736), if required by a future release scope;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance.

Do not convert source support, RDP-only checks or a prior package into
certification of these gates.
