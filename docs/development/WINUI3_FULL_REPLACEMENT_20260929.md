# flyExplorer full WinUI 3 UI replacement ? dedicated migration worktree

**2026-09-30 M2.3 소형 화면 후속(부분 수용):** 실제 작업 영역 경계·탐색 영역 부족을 수정한 WinUI Debug/Release 소유 M1.9~M2.3 통합 GUI가 범위 한정 통과했다. 실제 물리 드래그·전역 클립보드·휴지통·전체 제품 동등성은 남았다. [세부 근거](WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md).

**M2.3 후속 부분 구현:** 한국어 리소스 19개 추가, 드래그 진단 및 로컬 파일 유형 표시를 포함한다. 현재 범위의 소스 검사 102/102, WinUI Debug·Release 통합 소유 GUI는 통과했지만 드래그 이벤트 도달 여부와 전체 MFC 기능 동등성은 아직 확인되지 않았다. [M2.3 후속 세부 기록](WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md).


**M2.3 단계별 통합 (2026-09-29):** 독립 WinUI가 실제 클립보드 CF_HDROP와 명시적 개인 프로필 세션 저장/자동 복원 코드를 포함한다. 한글·사용자 설정 격리/native Debug·Release 및 소유 Debug·Release 세션 UIA가 검증됐다. **드래그는 소스와 컴파일만 완료, 물리 소유 GUI 자동화 실패**로 아직 수용되지 않았다. 외부 Shell 메뉴·실제 휴지통/복구·OS 클립보드 실사용 격리 시험, 전면 .resw, 아이콘/열·설치/되돌리기 및 MFC 동등성은 미완료. [범위와 정확한 증거](WINUI3_M23_CLIPBOARD_SESSION_DRAG_STAGING_20260929.md).


**M2.2 최종 범위:** 독립 WinUI에서 ko-KR 기본 FileToolbar/StatusFooter, Shell 복사·이동 및 휴지통 명시 확인, 로컬 메타데이터·다중 선택/정렬과 초기 리소스화를 구현. 동일 코드 Debug·Release 실기 통합 GUI 및 통제된 Debug M1.8 Shell 장애 재검증 완료. 실제 휴지통 승인/되돌리기, OS 클립보드, 외부 Shell/원격 SMB, 제품 전체 UI/설치·회귀는 미완료. [M2.2 검증 및 동등성 작업표](WINUI3_M22_SHELL_OPERATIONS_KOREAN_20260929.md).


**M2.1 KOREAN REUSABLE CONTROL AND NATIVE OPERATIONS SLICE:** Owner-approved default UI is Korean ko-KR independently of Windows language. Independent WinUI reusable header/sidebar now compile, real native private theme settings and guarded create-folder/rename operations are bound, and the actual earlier literal ?? runtime-theme bug has been corrected/verified in a rebuilt owned Debug window. Independently built native Debug/Release each pass 18/18, source guards 71/71, source-matched real owned Debug/Release combined M1.9-M2.1 GUI and renewed Debug controlled M1.8 fault replay all PASS; full product parity, packaging and real external provider/DPI/accessibility gates remain open. [Actual M2.1 implementation and precise remaining parity](WINUI3_M21_KOREAN_NATIVE_UI_COMPONENTS_20260929.md).

**M2.0 FULL-WINDOW NATIVE MODEL CHECKPOINT:**
The actual independent WinUI full-window now consumes the native C++ pane/tab command model, with a WinUI header, System/Light/Dark and This PC. Paired Debug and Release x64 builds, each native state 16/16 and real owned normal GUI passed; source checks 64/64. Remaining native advanced feature parity, physical DPI, accessibility and clean installer are still OPEN. [M2.0 scoped implementation and evidence](WINUI3_M20_FULL_WINDOW_NATIVE_COMMAND_MODEL_20260929.md). Older M1.9 status below is historical.


**FULL WINUI 3 DECISION OVERRIDES HISTORICAL ALTERNATIVES:** The owner has committed to complete WinUI 3 app-owned presentation instead of a permanent MFC/XAML Islands hybrid. Advance the independently running M1.9 WinUI preview and native C++ engine; protect default MFC until feature parity, System/Light/Dark, high contrast, accessibility, stability, user settings and clean deployment/rollback are proved. Next: reusable full-window WinUI shell and shared state/command interface, NOT another long-lived MFC theme renderer. [Active project directive](WINUI3_FULL_MIGRATION_DIRECTIVE_20260929.md). This decision changes goals, not current code readiness.


**M1.9 ACTUAL IMPORT UPDATE:** The previously planned native `main` import is **already performed inside the separate migration branch**. Combined imported MFC Release x64/20 native PASS_WITH_SKIPS, new scoped preview UXH-07 workspace + UXH-06-like read-only opt-in recent search real GUI and actual MFC?WinUI workspace subset interchange passed. Original M1.8 isolated Shell helper/Job/watcher architecture preserved. Native default main remains untouched; WinUI is NOT full product parity (old full MFC multi-pane history/search file filters/regex/contents/operations/accessibility pending). [Current M1.9 evidence](WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md). Historical 'not imported' passages below are superseded.

---


Date: 2026-09-29.

**CURRENT post-main-consolidation baseline (docs-only):** The latest separately tested native `main` code-bearing baseline before this docs-only sync was `f074a6b` with merged UXH-07/UXH-06 and the current native ModernUI UI-02; the separately tested migration code-bearing baseline was `eb7ee1a` (M1.8) and has **NOT** been merged/rebased against the latest main source or declared production parity. Historical old Phase5 remote/UXH-07 feature-branch and dirty-worktree descriptions below are revision-scoped. Plan and validate the future native UXH-07 named-workspace and UXH-06 privacy/recent-search contract transfer separately; do not silently promote M1.8 fault tests to an untested combined tree. [Current branch state and reconciliation plan](MIGRATION_MAINLINE_ALIGNMENT_20260929.md).


**LATEST M1.8 scoped update:** The separate WinUI preview now has explanatory bounded-timeout and invalid UNC failure UI, a dedicated Shell namespace notification registration thread and test-owned COM fault/loopback GUI evidence. No real broken third-party extension or external virtual provider emission has been verified. See [M1.8 scoped evidence](WINUI3_M18_SHELL_STABILITY_20260929.md).

**HISTORICAL M1.7 scoped update (after the M1.6 standalone experiment):** [Actual WinUI two-lane native helper supervision, private Job timeout/restart, separate native watcher and full real Debug/Release GUI acceptance](WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md). The helper is now truly used by the isolated WinUI preview, NOT the default MFC product. The independent helper inherits the user's Windows token; it has not been certified against real hostile third-party extensions. The earlier M1.6 *helper-only* statements below are historical.

**Historical M1.6 scoped update:** [Current actual risk audit and isolated process-helper proof](WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md). The helper's Debug/Release and test-owned dual-lane watchdog/recovery proof PASS, but the actual WinUI UI STILL runs the old in-process STA; do not infer GUI process isolation or real extension crash recovery from this experiment. Historical M1.5 results and subsequent worktree notes below remain revision-scoped.

**Post-M1.5 housekeeping update:** The old Phase5 clean worktree was deliberately removed AFTER this earlier plan was written. Its remote productization source is retained, historical local-only evidence is safely archived, and the migration project now owns its own pinned NuGet cache. See [verified cleanup](LOCAL_GIT_WORKTREE_CLEANUP_20260929.md) for latest worktree truth; historical preservation statements below describe their original test-time state.

Branch: `migration/winui3-full-shell-20260929`, forked from clean
`experiments/phase5-productization-20260928` at `7ceeab5`.
Worktree: `C:\dev\flyExplorer-winui3-migration`.

## User-authorized target and non-negotiable invariants

Replace **all MFC-owned visual UI** with actual Windows App SDK WinUI 3
windows and controls: frame, navigation, multiple panes/tabs, folder tree,
dialogs, bookmarks/search, themed context surfaces, drag/drop affordances,
accessibility and saved workspaces. Retain and adapt proven native C++
business logic where possible instead of rewriting stable file operations.

This is a *full migration goal*, not a claim that the newly started shell
is already production-ready. Do not ship a partly converted WinUI UI as a
drop-in replacement for a complete legacy file manager. Keep the existing
native product usable and its configuration untouched until full parity
and explicit migration release gates pass.

The source worktree containing uncommitted UXH-07 named workspaces and
the earlier Phase5 WinUI3 experiment worktree must not be reset,
overwritten or silently merged. Do not change user DPI/theme,
HKCU shell registrations, hotkeys or user files. All GUI testing uses
synthetic privately owned directories. Do not push/merge/release or run
hosted GitHub Actions without separate user approval.

## Architecture findings that determine the migration order

- Existing `src/fxfile/explorer_ctrl.h` declares
  `ExplorerCtrl : ListCtrlEx, DropTargetObserver`. The current
  explorer is **both a view and a controller**: directly linking it
  from a standalone WinUI app would still depend on MFC and native
  HWND ownership, not accomplish the requested full UI replacement.
- `src/fxfile/file_operation_core.h/.cpp` already has a separately
  compilable UI-independent `fxfile::fileop::execute(SHFILEOPSTRUCT*)`
  interface. The new WinUI project directly compiles this original
  native C++ source rather than duplicating it. At real WinUI app
  startup the invalid-null contract is actually called and confirms
  `ERROR_INVALID_PARAMETER` with zero file side effects.
  **No real file operation is enabled in the new UI yet.**
- Phase5 proved actual WinUI3 Windows App SDK native builds, an
  opt-in MFC-hosted XAML island, active-pane path callbacks and x64
  experimental DLL/PRI staging. Those are reusable *research evidence*;
  the new full-shell executable does NOT silently host the old MFC UI.
- Filesystem paths cannot stand for all Windows Shell namespace PIDLs.
  Define a typed opaque Shell location/item contract before enabling
  virtual folders, drag/drop or Shell context menus. Avoid duplicating
  MFC-specific command dispatch in the XAML presentation layer.
- Preserve test-owned legacy configuration data/schema exactly,
  including last-session tab state and optional named-workspace
  formats from the separate UXH-07 branch, when those are eventually
  deliberately integrated. No automatic profile migration or
  destructive write until isolated backward/forward tests pass.

## Migration milestones (complete only when evidence is attached)

| Phase | Scope | Current state |
| --- | --- | --- |
| M0 | Independent actual WinUI3 window, two side-by-side panes, actual TabView controls, per-tab local directory history, address, read-only entries, split toggle, keyboard/pointer, native core link probe; Debug/Release x64 with real owned GUI | SCOPED ACCEPTED on owned Windows 11 96-DPI Debug and Release; DOES NOT replace existing product |
| M1 | Native UI-free Shell session and file change bridge, async STA exploration/notification adapters, eventual full ExplorerCtrl extraction | PARTIALLY ACCEPTED: shared native enumeration and ANSI/Unicode directory watchers, WinUI private COM STA with owned PIDL snapshots and 96-DPI real file create/delete refresh. Complete legacy controller/advanced watchers, virtual namespace changes and interrupting blocked COM remain OPEN. |
| M2 | Replace real product tree, multi-pane ratios, persistent named tabs, sorting/columns, icons/thumbnails, bookmarks/history, address Search and pane toolbars with full WinUI3 controls | NOT IMPLEMENTED |
| M3 | Bind actual tested native copy/move/delete/rename, shell context menus, clipboard and drag/drop to WinUI command interfaces; isolated destructive-operation tests and cancellation/undo | NOT IMPLEMENTED |
| M4 | Configuration/keyboard/hotkeys/localization parity; Last Tabs and named workspace independent restore, compatibility and fail-safe rollback | NOT IMPLEMENTED |
| M5 | Native Windows App SDK x64 Release distribution, PRI, runtime bootstrapper, GFL third-party redistribution/license review, clean-machine install/uninstall | NOT IMPLEMENTED |
| M6 | Repeated true full parity acceptance against original app: Dark/Light, OS HC, 96/120/144/192 DPI, Narrator/UIA, keyboard/IME, real Shell virtual folders, large/remote folders, failure handling, performance and memory budget | NOT IMPLEMENTED |

## M0 implementation and strict scope

Located at `experiments/phase6_winui_shell` as a separately named
unpackaged WinUI3 C++/WinRT executable `FlyExplorerWinUIShell`.
Its own tracked project templates and build.cmd do not overwrite the
prior Phase5 experiment project or native product output. The Shell
navigation display is currently a **safe local-filesystem preview**:
both panes have independent vectors of native `NavigationModel` tabs
and history, tab add/close, focus activation, separate local directory
contents, Enter/Escape in the address TextBox, parent/back/forward,
split hide/show preserving the hidden pane and quick Home/Documents/
Downloads buttons.

The UI reads up to 1200 directory entries per pane synchronously on
the UI thread; this is an explicit PROTOTYPE LIMIT, not acceptable
responsiveness for slow network or huge folders. There is no
real Shell namespace, full native file operations, settings
persistence, thumbnails or virtual folder navigation yet. The newly
linked native `file_operation_core` is called only with NULL,
so no copy/delete/move operation may touch user data.

Actual owned Windows GUI test `test_shell_gui.py` checks both
WinUI TabView/ListView automation controls, preview file enumeration,
direct native-core null contract, left tab add/close, split
hide/restore, physical Enter for address and Back navigation,
and independence of left/right directory listings. It captures a
local-only screenshot and checks owned process exit code 0;
test directories, APPDATA, LOCALAPPDATA and TEMP are disposable.
This test is deliberately **NOT** proof of M1-M6 parity.

### M0 binary and real-GUI acceptance (2026-09-29)

- Actual independent Debug and Release x64 C++/WinRT builds PASS.
  The Release executable SHA256 is
  `70080FECEA2AEDE6A545E5712CD2B6AD6E712BF0637D713C7FA661006D0C32C5`.
- Final Release 96-DPI test-owned GUI passed discovery of 12
  genuine named WinUI3 automation controls, read-only local
  enumeration, independent left/right file listings and paths,
  tab add 1->2->1, split hide/restore, actual Enter/Back
  navigation and native-core NULL API rejection.
  The owned process exited 0, all six ORIGINAL user configuration
  SHA256 hashes stayed identical, and disposable test fixtures
  were removed.
- Static migration architecture contracts: 3/3 PASS.
  Evidence:
  `logs/phase6-winui-release-x64-full-build.log`,
  `logs/phase6-winui-release-final-privacy-gui.log`,
  `logs/phase6-winui-static-contract.log`.
  The local-only actual final GUI capture is
  `logs/phase6-winui/migration-first-shell-real-gui.png`.
- Initial Debug GUI exposed unintended delayed TabView selection
  changing the active pane; the corrected model now ignores
  programmatic selections matching the model and provides
  explicit clickable pane-activation headers. New-tab creation
  copies the path before vector reallocation. The test also
  correctly treats collapsed panes as ABSENT UIA elements.
  These fixes were actually exercised in the final Release GUI.

This is the M0 visual/interaction foundation. It does NOT establish
real Shell namespaces, file-operation parity, persistent config,
installation readiness or production UI replacement.

## M1.5 asynchronous COM STA and shared directory changes (2026-09-29)

LOCAL scoped acceptance: original MFC Release x64 CI 20/0
PASS_WITH_SKIPS, owned old MFC GUI success; independent
WinUI Release x64 real 96-DPI GUI auto-refreshed
synthetic files on native create AND delete, performed
real COM/PIDL navigation, handled canceled/stale requests
and preserved original six user configuration SHA256
values. Native async tests cover worker thread isolation,
supersession, actual watcher signal and nonblocking
shutdown of a deliberately held TEST CALLBACK, not a
blocked third-party COM extension. Source contracts 5/5.

An initial Release pointer test failure was diagnosed
as a different user Explorer window covering the
test-owned UI; a PID-gated foreground guard fixed the
test harness and the SAME Release binary then passed.
Full traces, exact SHA256 markers, documented limits and
unfinished virtual Shell notification coverage:
[M1.5 scoped acceptance](WINUI3_ASYNC_SHELL_CHANGE_WORKER_20260929.md).

## Immediate next change before affecting the legacy default

1. M1 partial extraction has been implemented and scoped-verified;
   see the subsequent M1 evidence section. Next, isolate existing
   native ExplorerCtrl item filtering, asynchronous change notification,
   and Shell extension operations without retaining MFC HWND state
   in the new engine. Add a dedicated cancellable COM STA worker:
   the current atomic cancel check cannot interrupt a blocked
   Shell extension's EnumObjects/Next call.
2. Expand actual native Shell item properties, sorting, icons,
   thumbnails, selection, network folders and command handling.
   Reuse existing native file operations without enabling any
   untested destructive operations or touching real user files.
3. Preserve original last-session and optional local UXH-07 named
   workspace schema with separately approved compatibility tests.
   Continue M2-M6 integration and OS acceptance before any default
   application swap.

## M1 partial real shared-shell extraction evidence (2026-09-29)

**What actually moved:** The original
`src/base/shell_enumerator_win.cpp` still preserves its
legacy list-type/hidden/system flag mapping and owner HWND, but now
calls `fxfile::shellnav::openEnumeration` implemented in the
separate MFC-free, old-SDK-compatible
`src/base/shell_enum_bridge.cpp`.
The new `src/base/shell_navigation_core.h/.cpp` supplies
native absolute PIDL RAII cloning, Windows Shell parsing,
item enumeration/attributes, transactional snapshots,
per-tab back/forward/up history and cooperative cancellation
checks. It has no MFC view type and compiles directly into the
independent WinUI 3 executable together with the SAME low-level
bridge. The old MFC product compiles only the compatible bridge
and retains its existing UI and high-level controller logic.
This is a real shared native enumeration code path, NOT
complete extraction of old ExplorerCtrl responsibilities.

**Compatibility issue resolved:** The old MFC product's
forced legacy stdafx/PCH hides some newer shell API
declarations that the independent WinUI session requires.
Compiling all modern code inside the legacy product
initially FAILED. Splitting the pure EnumObjects bridge
from the modern higher-level session restored compiler
compatibility without changing the legacy project-wide
Windows API macros or requiring MFC inside the new core.

**Existing MFC actual results:** Migration worktree's
local `local_ci.bat x64` exit 0, source preflight,
Release-x64-Unicode build/link/warning policy PASS;
native functional suite **18 passed / 0 failed**
(original 17 plus a synthetic native Shell/PIDL/
invalid-path/atomic-cancel/local-history contract).
Official local CI runtime smoke **SKIPPED** because
existing real HKCU state was detected, so the result
is strictly PASS_WITH_SKIPS, not a smoke PASS.
This legacy binary SHA256:
`54C6F0C5584E957B8088670DB91414DB90A2D3BD3488B493D053177D5FD529D7`.
Separately, the actual MFC product launched on a
private configuration/APPDATA/TEMP and synthetic
child folder. Direct product Go Up, Back and
Forward commands all passed through the original
MainFrame/ExplorerCtrl path; the owned process
exited 0, synthetic fixture was removed, and
all SIX original user-setting SHA256 hashes matched.
Logs:
`logs/m1-shared-enum-legacy-native-local-ci-v2.log`,
`logs/m1-real-legacy-explorer-shared-enum-gui-v2.log`.

**Independent actual WinUI 3 results:** Debug x64
and final Release x64 compile/link PASS. Final
Release executable SHA256:
`12EE36CB7DC6758A824D4EAA669CFA24E0C81E497022FC36508BD0C973729F18`.
Actual privately owned Win11 **96-DPI Release GUI**
passed discovery of all 12 test-targeted XAML
controls, local synthetic entries, **real folder-row
doubleclick via its owned absolute Shell PIDL**,
local folder Back/Forward/Up, independent two
panes and native tabs, split hide/restore,
typed physical address Enter, opening the actual
virtual Shell `shell:MyComputerFolder` (This PC)
and native virtual-folder Back history.
The owned process exited 0; synthetic directories
were removed and the same original six user
configuration SHA256 hashes remained identical.
Static architecture/source contracts **4/4 PASS**.
Logs:
`logs/m1-native-shell-winui-release-build.log`,
`logs/m1-native-shell-winui-release-real-gui.log`,
`logs/m1-final-arch-contract.log`.
Screenshots remain LOCAL ONLY and under ignored logs.

**Explicit remaining limits:** Existing ExplorerCtrl
still owns MFC ListCtrlEx, high-level view options,
filtering, Shell-change/watchers, drag/drop, menu
presentation, native copy/move/delete commands and
product settings. The new Shell session enumerates
at most 1200 entries and executes COM Shell
EnumObjects/Next synchronously on a COM-initialized
calling STA. Atomic cancellation is cooperative
between calls only: blocking third-party Shell
extensions, long-running network folders, and
background thread isolation are NOT proven.
The new UI has no destructive file operations
enabled; real other DPI, OS High Contrast,
spoken screen-reader, IME, saved workspace
schema parity, install/uninstall and hosted CI
were NOT TESTED. Original separate UXH-07 and
Phase5 worktrees remain untouched.

The main MFC product remains unchanged as the user-data-safe fallback
until this independent new UI reaches full accepted parity.
