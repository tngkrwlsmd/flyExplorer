# flyExplorer current status — 2026-10-09

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

Remote Windows Task now preserves multi-line/quoted PowerShell source by writing
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

### 2026-10-09 — main Release and complete GUI acceptance

Current main revision `7c23af1515fab0926fa409d277efd6e16b9d1f65`
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

Operations that require full Shell metadata are still not allowed to silently
operate on a partial model above 20,000 entries. Type, size and modified-date
global sorts continue to refuse above the complete-model ceiling. Name sort and
name filtering are now the deliberate exception: navigation retains a
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

Development policy now treats the persistent remote shell as the Windows
diagnosis/build iteration surface. Windows VM Build is manual
`workflow_dispatch` only: normal main pushes do not queue it, the default
manual scope is `release`, and `release-gui`/`full` are explicit
exceptional choices. Deterministic product/source failures require a new revision; one controlled same-revision rerun is allowed only for a clearly classified infrastructure/transient failure.

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
- Type, size and modified-date global sort requires a complete sortable
  metadata model and is supported through 20,000 fixed, removable, mapped
  network or ordinary direct-UNC filesystem entries. Network/UNC metadata
  collection is isolated in the exact-owned helper with bounded inactivity/
  cancellation handling; actual SMB/UNC and mapped-drive execution remains
  uncertified because the self-hosted runner has no test-owned SMB share.
  The previous 1,200 visual-detail ceiling no longer controls these sorts and
  1,201-20,000 items no longer silently use name order. Above 20,000 these
  metadata sorts remain explicitly refused. Shell visual/type/icon/thumbnail
  enrichment is separately bounded to 1,200 items and now supports local
  fixed/removable, mapped network and ordinary direct-UNC filesystem roots,
  while virtual Shell/provider roots support bounded type/icon enrichment plus
  up to four provider thumbnails in Medium/Large Icons. Actual physical
  USB/removable and SMB/mapped-drive visual execution remain uncertified because
  the self-hosted runner has neither a removable volume nor a test-owned SMB
  share; arbitrary third-party provider implementations are not separately
  certified by the built-in This PC/Pictures Library acceptance. Physical USB
  metadata-sort execution is also still awaiting a removable device on the
  self-hosted VM.
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
  USB/removable execution is still uncertified because the VM has no removable
  volume. Actual SMB/UNC and mapped-network-drive Copy/Move execution is also
  not yet certified because the runner has no test-owned SMB share. Provider
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
  wire data at 1 MiB, rejects indexed-mode regex/contents/metadata options,
  and never silently falls back to filesystem traversal. Cancellation,
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
- Persistent pane filter/mask rule sets are implemented with up to 20 named
  private presets, case-insensitive wildcard masks and legacy substring
  compatibility. Pane filters remain name/mask based; historical per-rule
  color/icon classification is not implemented.
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

The current unsigned package and exact binary/source identity are accepted by
Remote Windows Task #440 (`37376305779`). The binary source revision is
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

This closes the technical exact binary-to-source identity gate for the accepted
unsigned artifact. The public distribution mechanism is now selected as GPLv3
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
- actual 125%, 150% and 200% OS display scaling (blocked on the current
  self-hosted VM: Windows reports one active 1274x771 display mode and
  DisplayConfig DPI range CURRENT=100%, RECOMMENDED=100%, MAX=100%);
- human Narrator and Korean IME composition acceptance;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance.

Do not convert source support, RDP-only checks or a prior package into
certification of these gates.
