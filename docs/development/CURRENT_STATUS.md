# flyExplorer current status — 2026-10-04

## Product source of truth

main is the canonical C++/WinRT WinUI 3 product. Product code lives in
app/winui, UI-independent native code in src/base, tests in tests/winui, and
bounded orchestration in tools/winui/run_checks.py. The former MFC application
is retired from the working tree and is recoverable from Git revision cbffb48.

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
- The first post-extraction audit identified file-detail work as one remaining
  independent lifecycle boundary. FileDetailController now owns pane-local
  cancellation, detached detail workers and bounded Shell visual/thumbnail
  orchestration. MainWindow retains request preparation, live PaneState
  acceptance, DispatcherQueue handoff and XAML projection.
- The second MainWindow responsibility audit compared preferences persistence,
  private drag/drop state and workspace restore sequencing. Preferences was the
  strongest independent persistence/lifetime boundary: PreferencesCoordinator
  now owns the Preferences value, write mutex, revision ordering and detached
  atomic-save worker. MainWindow retains theme/view presentation, request
  initiation and DispatcherQueue-projected save-failure status.
- A follow-up owned physical-drag probe intentionally did not extract drag/drop.
  On the Release test-owned window the Korean source row was visible, enabled
  and explicitly selectable, and real mouse press/move/release coordinates were
  delivered. However neither the row nor ListView DragStarting diagnostic
  status appeared, so DragOver/Drop were never reached. A final identical
  retry reproduced the same boundary. This does not prove a product drag defect;
  it means the current automation environment cannot certify the
  pointer-to-WinUI-drag gesture boundary.
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
- Details, List, Small Icons, Medium Icons and Large Icons views.
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
- Search v2 keeps the existing bounded asynchronous SearchController lifecycle
  and adds optional ECMAScript regex, case-sensitive matching, file/folder/both
  targeting and a single extension condition. Default behavior remains
  case-insensitive literal file-name search. Invalid regex/extension input is
  rejected before worker start. The existing depth-5, 2,500-entry walk and
  100-result bounds, cancellation/stale-result rejection and opt-in recent
  scope persistence remain unchanged.
- Back/Forward/Up, filtering/sorting, local create/rename, guarded copy/move/
  recycle flows, Windows clipboard/context integration, isolated Shell visuals
  and directory/Shell namespace watching.
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
by MainWindow. FileDetailController now owns pane-local detail cancellation and
the detached metadata/icon/thumbnail worker lifecycle. MainWindow still performs
the live route/tab/ticket acceptance before projecting a completion, and
PrepareForClose cancels detail work before ShellNavigationController shutdown.
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

The previously described external install_script/start_skill cloud bootstrap
files are not present in this repository. This repository therefore documents
the required environment but does not claim to have modified external cloud
bootstrap configuration.

## Latest verified evidence

Large-folder resident-window prerequisites are now split from the existing
20,000-entry ceiling without claiming that the ceiling is removed. The first
preparation unit separates logical enumeration progress
(`Snapshot::baseOffset/nextOffset`) from resident `children.size()`; remote run
`37180519800` passed focused large-folder contracts, the canonical Release
build, the isolated helper process regression, legacy-profile protection and
`git diff --check`. The follow-up unit tags file-list rows with logical
`uint64` item identities and resolves them through the current Snapshot before
open/rename/transfer/clipboard/context/drag actions. Remote run `37180884833`
passed the logical-row source contract, Release build, the existing owned M21
selected-row rename path, process exit 0, protected legacy settings and
`git diff --check`. No resident page eviction or 20,000+ certification is
claimed yet.

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
cancellation boundaries are unchanged. Saved search presets write schema 3 with
the content encoding and continue to read schema 1/2.

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


Bounded literal content search is accepted on product revision
`eb612e6ef81e168e95cc5c00284eaf890157497b`. Search now AND-composes an optional literal file-content term
with the existing name/regex, extension, size, local modified-date and target
criteria. UTF-8/ASCII and BOM-tagged UTF-16 LE/BE are supported; unmarked
NUL-containing files are skipped as binary. Reads are bounded to 1 MiB per file
and 16 MiB per search, with 64 KiB cancellation checkpoints. Folder-only
content search is rejected before worker start. Saved search presets write
schema 2 with the content term and continue to read schema 1.

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

Current main follows the later `f7f3674e5271c17652a865cf2ed499185983d1eb` model-level streaming path
described above: the first page is accepted immediately and continuations
append on demand. The remaining scale limit is different. Accepted children
are still retained in the navigation session and continuation stops at the
20,000-entry navigation safety ceiling. Logical enumeration offsets are now
separate from resident child count as the prerequisite for a future bounded
resident window. 20,000+ browsing and global sort/filter semantics beyond a
fully resident model are not yet certified.

Persistent WinUI bookmarks are accepted on main. Automatic Windows run
`37133980876` completed successfully for main revision
`85b20db79ab61742bb9cca2057c5afab696574cf`: policy/source gates passed,
Release native state contracts passed, the canonical Release build passed, the
owned Release GUI suite passed with normal process exit, and the Release runtime
set passed. This closes the bookmark logical unit together with the focused
pre-main functional and visual evidence below.

Development policy now treats the persistent remote shell as the Windows
diagnosis/build iteration surface. Windows VM Build is manual
`workflow_dispatch` only: normal main pushes do not queue it, the default
manual scope is `release`, and `release-gui`/`full` are explicit
exceptional choices. Same-revision Actions reruns are prohibited.

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
  and a 20,000-entry model safety bound. The active model now accepts the first
  page immediately and appends continuation pages on demand; owned Release
  evidence covers an 8,000-file initial 1,024-item render followed by complete
  global name sort and progressive 160-row rendering. Unbounded virtualization
  beyond the 20,000-item model ceiling, network/virtual providers and sustained
  thumbnail-cache behavior are not certified.
- Search remains bounded. Regex, case sensitivity, entry-kind,
  single-extension, minimum/maximum file size, inclusive local modified-date
  and literal text content conditions are implemented with up to 20 private
  saved condition sets. Content reads use deterministic Auto UTF
  (UTF-8/ASCII plus BOM-tagged UTF-16) or explicit CP949/Windows-1252, with
  1 MiB per file and 16 MiB per search. Content regex, other encodings,
  indexed/provider/property search and unrestricted deep content scanning are
  not implemented.
- Persistent pane filter/mask rule sets are implemented with up to 20 named
  private presets, case-insensitive wildcard masks and legacy substring
  compatibility. Pane filters remain name/mask based; historical per-rule
  color/icon classification is not implemented.
- The complete historical command/provider verb/fault matrix is not fully
  implemented or tested.
- User-configurable accelerators and a complete historical shortcut map are
  not implemented.

## Packaging state

The installer project is now reproducible from a tracked project template, and
a current local Release setup build plus bounded /TESTROOT install/uninstall
has passed. The tracked licensing/provenance snapshot still predates v7, so
this does not by itself clear public distribution or prove a signed clean-machine
machine-wide install/update/rollback path.

## Open gates

Not certified by current automated evidence:
- actual 125%, 150% and 200% OS display scaling (blocked on the current
  self-hosted VM: Windows reports one active 1274x771 display mode and
  DisplayConfig DPI range CURRENT=100%, RECOMMENDED=100%, MAX=100%);
- High Contrast ON;
- human Narrator and Korean IME composition acceptance;
- physical pointer drag acceptance (owned Release automation reaches a visible,
  enabled, selected source row and real mouse movement, but not WinUI
  DragStarting; product defect versus automation/input limitation remains
  unresolved);
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance.

Do not convert source support, RDP-only checks or a prior package into
certification of these gates.
