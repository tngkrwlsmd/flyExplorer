# Windows 11 File Explorer parity re-audit — 2026-10-22

## 2026-10-29 evidence reconciliation

Current reconciliation baseline: `main@3cb5b7691a11910b2d71f5a7b0e112205f341baf`. Use the maintained
[NEXT_DEVELOPMENT_GOALS.md](NEXT_DEVELOPMENT_GOALS.md) current-work section
before selecting a task. The original 2026-10-22 comparison and its priorities
below remain a dated snapshot; their OPEN/next-step labels do not reopen a
subsequently accepted scenario. This update does not perform a new Explorer
comparison, product build, GUI or pixel review.

| Area | Latest scoped result | Remaining difference or unverified scope |
| --- | --- | --- |
| PX02 Home | [Bounded unified Home accepted](PX02_HOME_OVERVIEW_ACCEPTANCE.md), `66b2c6a4`, Release + owned GUI | Home compact Light/Dark pixels were subsequently accepted in the [Home visual review](PX02_HOME_VISUAL_REVIEW_20261029.md). Populated activity and full Explorer/cloud Home remain outside that scope. |
| PX06 Search | [Local in-flight Cancel accepted](PX06_SEARCH_CANCEL_STATUS.md), `6bbc94f4`, central #40691104646 | Full indexed/provider/cloud search remains separate. Later [compact-panel pixels](PX15_COMPACT_SEARCH_REVIEW_20261029.md) have their own finite acceptance; [folder browsing/sort performance](PX13_PIPE_DRAIN_PERFORMANCE_20261029.md) does not certify search-engine timing. |
| PX10/L08 Columns | [Left and right native cursor + physical resize accepted](UI_UX_AUDIT.md), left `b5e6e11f` and right `e887f64d` | Independent pointer-pixel review and untested drag transitions are not certified. Historical Arrow/locked-desktop results are not the current native-cursor verdict. |
| PX12 Address | [Bounded keyboard candidates accepted](PX12_KEYBOARD_CANDIDATE_ACCEPTANCE.md), exact `3bbfc73b`, central #40778973319 | Arbitrary disk/provider autocomplete remains broader than the implementation; the older visual comparison remains PARTIAL. |
| PX14/G01 Stability | [Focused startup and ToolTip-close issues completed](CURRENT_STATUS.md); #68 and #69 closed | Preserve exact scenario boundaries and reopen only on new matching evidence, without claiming every lifecycle path is fixed. |
| M23 Copy / source gate | [Finite local Copy scope accepted](M23_ACCEPTANCE_BOUNDARY.md); [source-contract repair 8ebf3d8](https://github.com/tngkrwlsmd/flyExplorer/commit/8ebf3d8980864c19d935a1532faabb779d1586b9) local product-source 301/301 | Local source PASS is not new central CI/Release/GUI acceptance; retain historical failed runs. |

The additional accepted units since the earlier `8ebf3d8` reconciliation are
Home compact restore, local app/Shell-pipe performance, Light caption contrast,
PX17's local New menu, compact search, and F03 Unicode cutoff/resize focus.
Use [CURRENT_STATUS.md](CURRENT_STATUS.md) for their exact finite evidence;
this document does not recertify their binaries or widen their acceptance.
The Home pixels/performance/New-menu sequence formerly recommended here has
been completed in its selected scope and is no longer the next-work queue.

The single current queue is [NEXT_DEVELOPMENT_GOALS.md](NEXT_DEVELOPMENT_GOALS.md),
**앞으로 진행할 작업**. First finish Release, focused collision/navigation GUI and
filtered-sort runtime/performance checks for product `7e28366c`. Its 44/44
source/model PASS is not native, GUI or measured-speed acceptance. Later scoped
L03 Type, M24 .txt icon-ready and horizontal-search pixels are accepted in their
own feature records; do not replay them to validate this different source change.
After those gates: one important uncovered PX15 action, a PX11 adoption decision,
then a separately chosen unmet PX17/PX08 candidate. No automatic feature adoption;
keep current v4 ownership, excluded G03–G05 and stopped G07. Subsequent performance
work needs new symptoms/evidence. Preserve the original comparison below.

## Original 2026-10-22 scope and judgment

Product source checked against flyExplorer main 5cf79f56b27e7d86a1fd82cc6ae171d75e04d98e
(the 2026-10-22 follow-up documentation changes did not edit UI/native product source).
Compared against documented *generally available Windows 11 File Explorer*
behavior; OS build, subscription, OneDrive account and Insider features can
change the reference. Microsoft primary references:

- https://support.microsoft.com/ko-kr/windows/experience/fileexplorer/file-explorer-in-windows
- https://support.microsoft.com/ko-kr/windows/experience/storage-filemanagement/find-your-files-and-apps-in-windows

Evidence: current MainWindow.xaml, NavigationSidebar.xaml, shell delegation,
feature requirements, NEXT_DEVELOPMENT_GOALS, UI_UX_AUDIT, feature benchmark
dated 2026-10-12 and central Windows exact-SHA Release build
https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39779111032
(policy/source/Release PASS; **not** GUI or a pixel comparison). Earlier
full integrated GUI acceptance at 74bd0f3 was successful, but G01's
intermittent initial-navigation and shutdown root causes remain open.
No new side-by-side live Explorer screenshot, input trial or GUI test was
performed for this audit. Source absence of an explicit control is a candidate
gap, not proof that a shell integration cannot perform the action.

**Verdict: NOT functionally or UX-identical.** Retain intentional dual-pane
WindowTab/PaneTab differentiation; "perfect clone" and binary/pixel equivalence
are not valid acceptance claims.

## Historical 2026-10-22 Explorer gap ledger

Status meanings: **DIFFERENT** = evidenced product architectural/interaction
difference; **PARTIAL** = implementation exists but its covered behavior is
smaller than Explorer's; **CANDIDATE** = no dedicated source/previous acceptance
found, requires narrow confirmation; **OPEN** = observed product risk or
unaccepted behavior; **INTENTIONAL** = accepted deliberate divergence.

| ID | User-visible Windows 11 reference behavior | flyExplorer observation and classification | Scoped requirement / acceptance |
| --- | --- | --- | --- |
| PX01 / EP05 | Right-click cut/copy/rename/share and provider verbs within Explorer's streamlined menu | **DIFFERENT** — selected item and empty-background actions may open a separate Explorer window through SHOpenFolderAndSelectItems/ShellExecuteEx; native in-app extension parity is not claimed | Explicitly mark external-Explorer fallback, compare single/multiple/blank selection and keyboard invoke; support built-in safe actions without falsely claiming all third-party verbs |
| PX02 / EP09 | Home combines Quick access, pinned/frequent/recent and, if entitled, cloud recommendations | **PARTIAL** — sidebar Home/bookmarks and opt-in session recent activity exist; not full Home dashboard/frequent/cloud recommendations | Distinguish local favorites, recent files, frequently used folders and search history; opt-in persistence/privacy/clear and empty state, source-aware indicators |
| PX03 / EP10 | Archive file browsing and ZIP/7z/TAR creation/extraction through Explorer's own UI (OS-version-dependent) | **DIFFERENT** — removed inactive native ZIP engine; operations delegated to externally opened Explorer, not integrated two-pane operations | Choose in-app archive scope or explicitly preserve delegated workflow; document format, safe paths, extraction limits, progress/cancel and feature visibility per OS |
| PX04 / EP15 | Cross-folder Gallery/photo view and timeline-style browsing | **CANDIDATE** — thumbnail/icon views exist but no dedicated Gallery collection verified | User-picked picture roots; date grouping, visible navigation, cancel/limits, source folder access; no automatic personal library scan |
| PX05 / EP15 | OneDrive and other provider sync/availability placeholders; relevant cloud metadata and search | **CANDIDATE** — no provider-specific badge/state handling verified; virtual Shell support is narrower | Surface state only when OS/provider supplies it and avoid false offline/cloud-success claims; no automatic login/upload or excluded G05 real SMB tests |
| PX06 / EP08 | Windows Search in Home/location, including PC/cloud scopes and Explorer query/filter interaction | **PARTIAL** — local scoped/indexed search and bounded result limits exist; not established as Windows Search/OneDrive equivalent | Make scope/index/limit/truncation unambiguous; targeted results/navigation/suggestions/cancel checks and no silent fallback |
| PX07 / EP12 | Details and Preview panes cover many file types, metadata and installed handlers | **PARTIAL** — file metadata/details and safe opt-in image/text preview exist; PDF/provider previews intentionally bounded | Clearly label supported formats, pending/error state; opt-in safe public provider extensions only, no arbitrary DLL in app |
| PX08 / EP11 | Native Windows Share sheet and Open with for selected files | **PARTIAL/CANDIDATE** — Open with implementation recorded; full native Windows Share behavior not accepted | Distinguish Open with (existing contract) from Share (not yet accepted); exact selected item, cancel, no unapproved external transfer |
| PX09 / EP06 | Undo/redo of appropriate file operations and recoverable history | **CANDIDATE** — no full Explorer-like undo/redo transaction surface accepted | Decide supported reversible operations, irreversible deletes/collisions, undo transaction expiration; do not show enabled buttons without proof |
| PX10 / EP04 | Explorer selection, details columns, context, checkboxes, view and compact-density preferences | **PARTIAL** — F01/F02 and sort/group accepted within scope; detail-column pointer L08 and some selection/scroll transitions unresolved | Reuse accepted view toggles; target column resize pointer and multi-select/scroll after filter/group only if impacted |
| PX11 / EP02 | Tab-specific independent navigation/history/view and multi-window behavior | **PARTIAL/INTENTIONAL** — two-level WindowTab/PaneTab; sort is already independent per PaneTab (v4 session), while view/display/column state is per pane within each WindowTab; grouping has a transient route/tab cache | Preserve documented hybrid ownership (2026-10-23), legacy v1–v3 sort inheritance and in-session F14 folder view. Per-tab view/column storage or Explorer drag/detach parity is not implemented/accepted |
| PX12 / EP01 | Explorer location entry, breadcrumb suggestions, Back/Forward/Up with shell namespace roots | **PARTIAL** — editable address/navigation accepted locally; arbitrary filesystem autocomplete/provider-root breadth unaccepted | Bounded path suggestions and scoped Shell targets, preserve committed state when requests fail or settle late |
| PX13 / EP13 | Usable scrolling, responsiveness and stable large-directory navigation | **OPEN** — native 8k helper tested, app-scale 20k/25k boundaries not whole-Explorer parity | Measure one app-owned large-folder scenario, cancellation/memory/latency, partial-model UX; never generalize native fixture to full app |
| PX14 / G01 | Reliable initial navigation and normal shutdown | **OPEN (historically intermittent)** — one integrated GUI PASS does not prove intermittent faults fixed | Diagnose only at reproduced boundary with exact owned dump; no blind broad-rerun cycles |
| PX15 / EP14 | Similar command bar/icon spacing, feedback, high contrast and focus across views | **CANDIDATE** — some 96 DPI light/dark and scoped focus accepted; no same-run side-by-side Explorer pixel/interaction audit | Fixed OS build/theme/window/fixture for matched visual and accessible feedback comparison; excluded G03-G05/G07 remain excluded |
| PX16 / EP03 | Explorer keyboard/menu semantics and tab shortcuts | **PARTIAL/INTENTIONAL** — Ctrl+T/W/Tab are flyExplorer workspace-tab shortcuts; existing two-level tabs differ | Document shortcuts, active target, keyboard help and focus; re-test only changed navigation |
| PX17 / EP11 | New-item flyout, templates, device-dependent extensions | **PARTIAL** — New Folder and New Text File present; generalized provider templates not accepted | Show supported new item types, collision guard and failure state; no claim of full template ecosystem |
| PX18 / EP09 | Quick access integration with OS-pinned folder entries | **PARTIAL** — private bookmarks, not established as native Explorer Quick access database or full history | Map visibility and ordering in the private app, never silently write or import OS Explorer profile |

## Historical 2026-10-22 priorities and acceptance policy

- **P0 functional correctness:** G01 unresolved intermittent navigation/shutdown; never label it fully fixed from a single PASS.
- **P1 visible parity:** PX01, PX02, PX06, PX08, PX10, PX11, PX12, PX15, PX17, PX18. Reuse the accepted F01–F06/R1 evidence and existing changed code.
- **P2 scope/design decision:** PX03, PX04, PX05, PX07, PX09, PX13. An optional provider subscription, preview-channel feature or OS-version mismatch is not a default release blocker.
- **Explicitly excluded:** real G03 DPI 125/150/200, G04 spoken Narrator/HC for F04/F05, G05 actual USB/SMB/UNC; stopped G07 real IME. Preserve NOT TESTED, do not schedule or re-propose.
- **Verification cost:** For each PX, first inspect only related source and existing exact-SHA evidence; then a focused contract and at most the impacted incremental build/targeted GUI if behavior changed. No blanket A-to-E reruns. UI changes require a separately scoped visual comparison; a policy/requirements-only edit does not require a new build.

## Definition of done for "Explorer-equivalent"

A claim must name the **exact interaction subset**, Windows Explorer build
and OS edition, WinUI exact source/binary, owned scenario and observed result.
A single screenshot or policy document cannot prove full behavior. Private
shell-provider verbs, OneDrive account-dependent features, all codecs,
Microsoft 365 recommendations and Microsoft's entire evolving extension
ecosystem are not guaranteed by this standalone local app. Record
intentional non-equivalence instead of promising impossible byte-for-byte
Explorer identity. The product's two-pane workflow is explicitly retained.
