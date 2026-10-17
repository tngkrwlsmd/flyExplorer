# F04 — expandable local folder tree (incremental implementation)

## F04-A path/identity foundation — 2026-10-17

F04 is not yet a user-visible TreeView. This first isolated logical unit
adds only the reusable, UI-independent lexical path and stale-result guards
in app/winui/folder_tree_path.h, a native executable regression, and a
source contract registered with the existing shell source suite.

- Accepted lexical shape: normalized absolute drive-letter paths, including
  the exact root, with bounded length (1,024 UTF-16 units), nesting (12 levels)
  and a documented future sibling budget (128). Reject UNC, device prefixes,
  drive-relative paths, empty/dot/dotdot segments, reserved Win32 device
  names, dangerous leaf characters and trailing dots/spaces.
- Child construction changes the output only on a valid path; Korean names
  and ordinary spaces are preserved.
- A future async expansion result must match active side, tab, navigation
  route and expansion generation. The pure identity guard rejects stale
  answers after pane/tab/route/expansion changes.
- The lexical guard proves neither volume type nor path containment against
  junctions/reparse/hardlinks. Real fixed-drive inspection and no-reparse
  decisions belong in a bounded isolated worker off the WinUI thread.
- No directory enumeration, read of personal files, global Windows-setting
  change, filesystem mutation, UI pixel change or new navigation command
  is introduced in F04-A.

## Next isolated unit — F04-B (not implemented / not accepted)

Add an explicit opt-in expandable TreeView in NavigationSidebar, local fixed
drive roots first; enumerate each expanded folder lazily with at most 128
child folders and a test-owned, cancellable isolated worker. Reject reparse,
UNC, provider and removable roots until individually reviewed. Resolve a
selected tree node to the existing active-pane OpenFolder route only, never
silently switch pane or tab. Verify keyboard/UIA focus, two-pane/tab route
changes, collapse/re-expand stale answers, empty/access-denied cases and the
mandatory actual light/dark before/after screenshot/pixel comparison.

## Acceptance boundaries

For F04-A, run the three registered stdlib source contracts and compile/run
the dedicated native fixture (C++17). Linux compiler execution checks only
portable path logic; it is not a Windows Release/GUI or visual acceptance.
F04-B remains open until exact-source Windows build, functional GUI and
independent pixel inspection are complete. Keep F03/F05/legacy paths unchanged.

## F04-B candidate implementation — source integration checkpoint

- Opt-in, initially collapsed folder TreeView is embedded below the existing
  navigation shortcuts; its root is the current active pane/tab's local folder.
- On explicit expansion, one cancellable detached native filesystem read worker
  validates a fixed drive and rejects reparse ancestors and child junctions,
  hidden children, invalid names and unsupported namespace paths. At most 128
  child folders and 4,096 examined entries per expansion (2.5s cooperative
  time budget) are projected. Existing navigation owns actual folder changes.
- UI-side nodes are invalidated on collapse, explicit hide, active pane/tab or
  route changes. The worker's result must match the same route and generation
  before UI projection. Windows path-replacement races during read-only
  enumeration are not claimed to be eliminated.
- The first version is limited to the active local folder as root rather than
  automatically scanning every disk. A single worker can be pending at a time.
  No Shell provider/UNC/mapped/removable/ZIP traversal, no content reads and no
  global Windows-setting changes are requested.
- Implementation is not acceptance evidence. Require exact-source Windows
  x64 Release, functional UIA/keyboard interaction with an owned fixture and
  matched BEFORE/AFTER Light/Dark captured pixel review before marking F04-B
  accepted.

## 2026-10-17 F04-B compile/path repair

- Original central GUI attempt #39031617203 FAILED at Release compilation (C2027/C3861): missing C++/WinRT AutomationProperties definition in NavigationSidebar.xaml.cpp. GUI never ran in that attempt. Independent artifact quota errors are not the root cause.
- The corrected candidate includes the explicit Automation header, checks the current filesystem path as well as side/tab/route to invalidate a stale tree after same-route navigation, and retries a waiting expanded node after a canceled worker finishes. A new Windows build is required; the old failure stays recorded.

## F04 owned GUI scope

- Dedicated folder-tree GUI area uses a disposable Left/Nested folder and app-owned preference files. It invokes the actual tree toggle, waits for a real child TreeItem and checks active-pane navigation and replacement of the root after in-tab navigation.
- Captures collapsed, expanded and navigated **owned-window** PNG states only when FLY_F04_TREE_VISUAL_CAPTURE=YES. The central GUI all-area chain executes this smaller test before the generic legacy GUI suite. Captured files under ignored logs still need independent pixel review.

## 2026-10-17 GUI automation diagnostic: collapsed UIA element

- Central Windows run [#39032765974](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39032765974)
  built the exact F04 product Release successfully and passed window tabs,
  shortcut keyboard and filter GUI. Focused F04 GUI failed before any tree
  interaction: the baseline assertion called WindowSpecification.is_visible()
  on FolderTreeView while its parent was intentionally Collapsed. WinUI
  omitted it from the UIA automation tree; pywinauto threw a TimeoutError
  resolving auto_id FolderTreeView. The historical failure is retained.
- Test now resolves optional UIA visibility using exists(timeout=.2) before
  is_visible(); a matching source regression contract protects the guard.
  No product C++/XAML was changed in this logical unit.
- The predecessor Release build does not certify the revised Python harness;
  independent F04 input, completed owned window screenshots and pixel review
  remain OPEN.

## 2026-10-17 F04 right-pane-focused GUI isolation

- [Central #39033656455](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39033656455) FAILED after source and Release PASS. The focused GUI failed *before F04 input* at the shared Left cold-start address readiness assertion. Retained owned evidence showed RightFiles containing the synthetic Nested/readme fixture, but LeftFiles and active AddressBox empty; test-owned application exited normally and removed its fixture. This does not establish an F04 TreeView defect.
- Focused F04 now waits for the populated RightFiles, activates that pane by a real owned click, and checks that its active address matches the same synthetic Left fixture before tree interaction. This tests an actual right-pane route rather than treating Left cold-start as a prerequisite.
- The normal GUI startup assertion for Left remains unchanged outside F04-only scope, and the full GUI chain still runs afterward. Right-focused F04 PASS, normal cold-start reliability, keyboard input, and independent Light/Dark pixel acceptance remain unverified until exact-revision evidence.

## F04 active-pane selection, October 17

Windows GUI #39035310336: source and Release PASS; F04-only FAIL before tree interactions. Archived owned UIA showed a populated LeftFiles and matching active address, but empty RightFiles. An earlier run saw the opposite side ready. The focused test now chooses either pane only after an owned Nested child is observed, activates that pane, and checks the active address. It reports the other pane state without claiming two-pane startup acceptance. Original general startup gate is preserved. GUI and visual acceptance remain OPEN.

## F04 TreeItem invocation, 2026-10-17

Windows GUI #39036073150: Release and existing three GUI areas passed. F04 test selected a ready pane, displayed the TreeView, located Nested and captured collapsed/expanded states. Clicking the full TreeItem did not update the active address. Revised harness clicks the actual Nested text label, not the bounding TreeItem area, and prints bounded failure diagnostics. Whether the WinUI event or navigation command is defective remains unverified. Light/Dark independent pixel review remains open.

## 2026-10-17 F04 tree selection event repair

Exact-source Windows GUI #39036967934 built Release and passed three pre-F04 GUI suites, but a real click on the Nested label did not navigate. The owned address remained the existing root and the app status was the last successful folder load. WinUI documents TreeView SelectionChanged as a response to the selected node changing and SelectedNode as the node selected. The candidate now uses SelectionMode=Single and SelectionChanged instead of depending only on ItemInvoked to translate an ordinary mouse/keyboard selection into the existing active-pane OpenFolder command. A guard rejects null, unowned, unsupported and same-root nodes. This is an unaccepted product behavior change pending the exact-source Windows Release and GUI test; the failure alone did not establish that the old ItemInvoked handler fired.

## 2026-10-17 F04 owner-scoped event trace checkpoint

Central GUI #39038874824 compiled Release and passed the three existing GUI areas, but the test-owned Nested label click again left AddressBox at its previous root even after switching to TreeView SelectionChanged. The retained GUI failure log contained no direct information about selected-node identity or event delivery. A follow-up candidate adds **opt-in diagnostics exclusively for the disposable F04 owned fixture**, restricted to the explicitly flagged process and owned folder marker. The FolderTreeStatus exposes one stage token: EVENT_ENTERED, OWNER_REJECTED, NODE_NULL, PATH_REJECTED, CURRENT_ROOT_SELECTED, or NAV_REQUESTED. GUI failure logs now also show the observed UIA selection state if exposed, without publishing a path or reading unrelated windows. This candidate has no accepted Windows build/GUI result yet. Successful F04 navigation and visual accessibility remain open.

## 2026-10-17 F04 physical row selection diagnostic

- Central GUI [#39039635912](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39039635912) built Release and passed legacy GUI tabs, shortcuts and filter, but failed focused tree navigation. Retained owned evidence proved the TreeView's Nested label was present; after clicking the text, `F04_TREE_UIA_SELECTED=False` and the app's opt-in `F04_TREE_SELECTION_STAGE` was blank. No selection event was observed in this owned fixture, so failure cannot yet be attributed to route/path guards.
- Updated focused GUI candidate physically clicks the TreeItem row now that SelectionMode=Single. If this still fails, it records whether UI Automation's SelectionItem.Select pattern navigates. **The UIA probe never converts a failed physical click into PASS**; the initial failure is re-raised. These observations are distinct from keyboard acceptance and final Light/Dark pixel review, both OPEN.
