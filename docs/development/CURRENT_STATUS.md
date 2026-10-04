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

Local large-folder coverage now includes an owned 5,000-file filesystem folder.
Product revision `51182fed05e32dfbd90ee320a4a259b1b884d0df` raises the isolated Shell enumeration ceiling
from 2,600 to 6,000 entries while retaining the 8 MiB wire-body bound and
160-item progressive WinUI rendering. Remote run `37135593385` completed the
Release build and helper protocol suite, then verified 5,000-item navigation,
name-descending sort to `bench-4999.txt`, and progressive paging
`160/5000 -> 320/5000`. Its later filename-filter UIA assertion was outside
the enumeration-ceiling change; filter and Ctrl+Shift+F behavior stay covered
by the existing 2,300-item case.


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
- Local filesystem Shell enumeration is bounded at 6,000 entries and has owned
  5,000-item navigation/sort/progressive-paging evidence. Folders above 6,000,
  true streaming virtualization, network/virtual providers and sustained
  thumbnail-cache behavior are not certified.
- Search remains bounded name search. Regex, case sensitivity, entry-kind and
  single-extension conditions are implemented, but content search and broader
  saved/compound multi-criteria queries are not implemented.
- Persistent pane filter/mask rule sets are implemented with up to 20 named
  private presets, case-insensitive wildcard masks and legacy substring
  compatibility. Saved size/date/compound query composition and historical
  per-rule color/icon classification are not implemented.
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
