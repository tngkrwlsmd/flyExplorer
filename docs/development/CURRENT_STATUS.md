# flyExplorer — current project status (2026-09-28 baseline; 2026-09-29 migration-branch addendum)

**M2.4 actual OS integration follow-up (2026-09-30):** User-approved global clipboard reset enabled a full one-session real Windows Explorer <-> WinUI 4/4 file Copy/Cut GUI pass with exact owned files and final clipboard clear. Actual installed Windows TXT/PNG association icons, WinUI Debug accessible icon and true PNG Shell thumbnail, and real isolated Windows context menu (20 native entries; exact GUI popup/Esc) were verified. The active desktop is DPI96/100% and HC OFF; owned windows at three real sizes, 9 UIA names and physical Tab focus passed, but alternate actual DPI/HC/Narrator/IME require a separate VM/human-run script. Two distinct real unpackaged Release builds completed strictly test-owned install/update/exact rollback/uninstall; this is NOT signed installer/clean machine certification. Following a bounded metadata singleton-fallback change the actual current full Release integrated GUI passed. [Exact evidence and remaining release gates](WINUI3_M24_REAL_OS_INTEGRATION_AND_PRIVATE_LIFECYCLE_20260930.md). The native/older owned Shell popup succeeded, but a newer bounded UIA right-click automation cannot currently find the app flyout entry; keep OPEN and do not mark that newer test PASS (see M2.4 matrix and ERROR_HISTORY).


**M2.4 scoped Windows integration follow-up (2026-09-30):** Independent WinUI migration branch: actual guarded one-item OS Recycle Bin move and exact restore PASS; native Windows registered type names with generic icons and pane-adjustable name columns PASS in full revised x64 Debug+Release owned GUI. Real 1,100-item folder navigation+descending sort passes on both revised builds after fixing premature pipe EOF on fast child exit (2.4s Debug; 0.98s Release). Read-only current OS DPI 96/100%, High Contrast OFF, actual UIA accessible names passed in Release. Owned portable copy smoke launched 20 hashed Release resource/runtime files, not a system installer or rollback. Source invariant PASS, 119 contracts (118 PASS, 1 environmental SKIP), original 6 real MFC configuration hashes preserved, original main untouched. The real clipboard was occupied and four-direction Explorer interoperability remains human-owned NOT TESTED. Per-extension real Windows icons/thumbnail, >1,200 paging, external context menu providers, varied DPI/Narrator/IME, clean installer/update/rollback and total MFC parity remain open. [Exact partial acceptance matrix](WINUI3_M24_SCOPED_WINDOWS_INTEGRATION_20260930.md).


**2026-09-30: M2.3 후속 소형 화면 GUI 회귀 수정(독립 WinUI 한정).** 원격 Windows 모니터의 실제 작업 영역 하단은 720px이었으며, 창 시작 좌표 y=78에서 확장 가능 높이 634px을 과거 최소 640px 조건이 거부해 탐색 영역이 지나치게 작아지는 것을 확인했다. 모니터 작업 영역에 한정한 확장 조건을 개선하고, 작업 공간 명령의 두 줄 배치·사이드바 스크롤·검색 결과 높이 축소를 적용했다. 소유 창을 정확히 (78,78,960,519)로 배치한 Debug M1.9→M2.0 테스트에서 실제 창 높이가 634px로 확장되고 내 PC 조작·탭·분할을 통과했다. 이후 동일 소형 화면 조건의 M1.9~M2.3 Debug 및 Release **전체 소유 GUI가 모두 통과**했다. 다중 선택 뒤 UIA 목록 재조회가 순간적으로 실패한 시험 하네스는 단일 제한 재시도 안에서 새 행을 다시 조회하고 실제 단일 선택을 확인하도록 수정했다. 독립 파일 작업의 실제 이동·이름 충돌 취소·개인 세션 저장/별도 프로세스 복원/삭제가 양쪽 구성에서 확인됐다. 사용자 기존 설정 6개는 해시 동일했다. 공식 소스 사전 검사 및 관련 소스 106/106, 두 구성 빌드도 통과했다. 실제 사람 포인터 드래그, 전역 Windows 클립보드·휴지통 변경 및 전체 MFC 기능 동등성은 여전히 검증하지 않았다. 증거: `logs/winui-scoped/20260930-compact-boundary-m19-m20.log`, `20260930-065505-gui-Debug.log`, `20260930-065643-gui-Release.log`. 빌드한 Debug SHA256=901BB2042A1CCBC5D548B0A1A24EB23896924F0D7E1EDFF7252A7375F5BB86DD, Release SHA256=10280A72167E247578BD38F4993ADA86DE52E545EAC84D505B0EB4A63AAA5D5F. 이 결과는 소유 100% 배율의 해당 기능 범위 수용이며 배포 인증이 아니다. 상세: [M2.3 후속](WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md).


**LOCAL SCOPED HANDOFF (2026-09-29, migration branch only):** Remote-call optimization now uses `experiments/phase6_winui_shell/run_scoped_checks.py` with a bounded official source preflight, named scoped contract/WinUI build/owned GUI stages, and ignored full local logs. Five corrupted newest Korean document sections were reconstructed from preserved evidence, not guessed byte-for-byte; source guards protect those sections. WinUI file-list metadata, sort, route and rendered paths now share a per-pane pure-C++ `PaneState`; native Shell helpers, route/epoch acceptance and MFC default remain untouched. Current official source preflight and 105 scoped source tests PASS; actual paired WinUI Debug/Release builds PASS. Segmented actual owned GUI: M2.0 standalone and M1.9+M2.0 with optional panels collapsed passed; M2.1+M2.2+M2.3 reached real guarded transfer and second-process private-session restore. Two GUI acceptance cases remain OPEN: with M1.9 panels still expanded, M2.0 cannot locate ThisPCButton after split restore; after an owned M2.3 second process exits, the parent ClearSessionButton appears in one UIA existence snapshot but subsequent wrapper resolution/physical click is unreliable even with M2.3 alone. Therefore full new combined GUI acceptance FAILED, not a product PASS. Actual physical pointer drag requires a separate human-owned manual test; global Windows clipboard/recycle remain NOT TESTED. Existing six original user settings remained hash-identical in test-owned executions. Logs and manual procedure remain local/ignored. These are local changes awaiting a migration-branch-only checkpoint, not a main cutover.


**M2.3 후속 검증 (2026-09-29):** 드래그 오류 문구 7개를 올바른 한국어로 복구하고, ko-KR 정적 리소스 19개를 추가했으며, 로컬 파일의 확장자 기반 유형 표시를 구현했다. 소스 검사 102/102 및 독립 WinUI Debug·Release 통합 소유 GUI가 해당 범위에서 통과했다. 자동 포인터 입력에서는 실제 드래그 이벤트 발생을 관찰하지 못해 드래그 기능 자체는 미검증 상태다. 실제 전역 클립보드·휴지통 동작도 별도 검증이 필요하다. [M2.3 후속 세부 기록](WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md).


**M2.3 단계별 통합 (2026-09-29):** 기본 언어 ko-KR 독립 WinUI에 Windows CF_HDROP/Preferred DropEffect 공통 C++ 계약 및 사용자 명령, 격리된 개인 세션의 명시 저장·시작 시 자동 복원·기록 삭제, 화면 크기/정렬/탭 복원 범위를 추가했다. WinUI Debug·Release 소스 일치 빌드 성공, 현재 통합 소스 97/97·격리 native Debug/Release 각각 26/26 통과. 원래 M1.8 통제 장애의 COM/namespace/루프백 UNC 및 연속 두 번 시간 초과 Debug 실기 회귀도 통과. M1.9~M2.3 소유 Debug·Release 실제 GUI에서 명시 저장, 새 정확한 소유 프로세스의 두 폴더 자동 복원·삭제까지 통과했다. 시스템 전체 클립보드의 실제 읽기·쓰기는 사용자 소유 데이터 보호를 위해 자동 시험하지 않았고, 마우스로 실행한 내부 드래그 GUI 진단은 실패하여 드래그 동작을 **미검증** 상태로 유지한다. OS 외부 드래그, 실제 휴지통 삭제/복원, 유형·아이콘·컬럼·Windows Shell 확장 메뉴 등 아직 M2.3 후속 게이트이다. [구현, 증거 수준과 상세 동등성 표](WINUI3_M23_CLIPBOARD_SESSION_DRAG_STAGING_20260929.md). 기본 MFC main 미수정.


**M2.2 최종 검증 (2026-09-29):** 독립 WinUI FileToolbar/StatusFooter, ko-KR 일부 .resw, COM STA Shell 복사·이동·휴지통 확인 계약, 비동기 로컬 파일 메타데이터 및 다중 선택·정렬을 구현. 소유 임시 경로의 독립 네이티브 Debug·Release 각 18/18, 통합 소스 79/79, 실제 M1.9~M2.2 **Debug·Release 통합 GUI 모두 통과**, 기존 M1.8의 통제된 COM/Shell 알림/루프백 UNC·두 번 시간 초과 Debug 회귀 통과. 원본 사용자 설정 6개, 기본 MFC main 및 원본 사용자 스크린샷 보호. [M2.2 정확한 검증과 남은 기능 동등성](WINUI3_M22_SHELL_OPERATIONS_KOREAN_20260929.md).


**M2.1 KOREAN-DEFAULT FIRST SLICE:** The existing independent WinUI full window now embeds compiled reusable ShellHeader/NavigationSidebar controls, Korean-first main/workspace/search text, dedicated MFC-independent private ko-KR System/Light/Dark preferences, and guarded native create-folder/rename commands. Native Debug+Release 18/18, combined source 71/71, and source-matched actual Debug AND Release full M1.9+M2.0+M2.1 owned GUI PASS, including literal Korean System UIA, dark/light private restart and guarded actual Korean create/rename/non-overwrite. Renewed Debug M1.8 independent COM/private Job/owned Shell notification/loopback UNC and two-attempt fault GUIs PASS. Exact limits, the real corrected ?? theme bug and final integrated GUI gates: [M2.1 detailed evidence](WINUI3_M21_KOREAN_NATIVE_UI_COMPONENTS_20260929.md). The protected default MFC main remains unchanged.


**M2.0 LATEST VERIFIED SCOPE:** Experimental WinUI native full-window main header, runtime System/Light/Dark and This PC, plus real `src/base/explorer_ui_state` pane/tab/route/request/command owner are compiled and verified in Debug. Owned actual Debug final theme pixels, split, tabs, virtual PIDL and Back PASS; independent native Debug 16/16 and combined source 64/64 PASS. Exact compiled Release x64 native 16/16, full Release real owned M1.9+M2.0 GUI and renewed M1.8 controlled COM/notification/two-timeout owned GUI also PASS; protected native `main` remains unchanged. [Exact scope and evidence](WINUI3_M20_FULL_WINDOW_NATIVE_COMMAND_MODEL_20260929.md).


**OWNER-DECIDED FULL WINUI 3 PRODUCT GOAL:** All app-owned presentation is targeted for Windows App SDK WinUI 3 replacement with existing proven C++ core and isolated Shell workers. MFC is a temporary product/default and fallback until full functional, visual/theme, accessibility, data, install and rollback acceptance passes. A permanent MFC-hosted hybrid is not the target; older neutral comparisons and historical tests below do not override this decision. [Binding product UI directive](WINUI3_FULL_MIGRATION_DIRECTIVE_20260929.md). Last separately accepted code baselines at this decision: native main 3a4d27c and WinUI M1.9 e84741a. This documentation edit is NOT a new build or product release.


## M1.9 FINAL RESUMED ACCEPTANCE ? separate preview, default native main unchanged

Final imported M1.9 source passed actual merged MFC Release x64 native **20/0 PASS_WITH_SKIPS** (the existing user HKCU smoke remains intentionally SKIPPED), full owned MFC UXH-07/UXH-06 GUI and merged native UI-02 real Dark/Light primary and modal GUI. The WinUI preview itself passed **Debug + Release** full owned actual workspace/recent-search/independent Shell navigation GUI, **12/12 same-source native workspace/search contracts in each build**, combined **56/56** source/architecture checks, real MFC-produced safe workspace compatibility and M1.8 controlled fault/notification/two-timeout regression. Original six user-setting hashes and the original untracked screenshot remained unchanged. Last exact final WinUI binaries and precise missing full-parity gates: [M1.9 scoped acceptance](WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md). Older M1.9 preliminary and M1.8 pre-merge sections below are dated history, not current integration status.

---

## M1.9 CURRENT ACTUAL SOURCE IMPORT ? migration only (2026-09-29)

Imported default native `main` `3a4d27c` into previously separate WinUI `34936ee`; preserved two-parent merge ancestry and both historical document histories while resolving three doc conflicts. Actual combined MFC source Release x64 local CI **20 passed / 0 failed, PASS WITH SKIPS** (live HKCU smoke intentionally SKIPPED). WinUI native XAML UI now supports a **bounded compatible subset** of UXH-07 UTF-16 schema1 named-workspace Save new/Open distinct process and independently queued selected/inactive tabs, and an **opt-in only** WinUI-private (not MFC-profile) bounded read-only UXH-06-like filename search/history. Native UI-02 ModernUI stays for MFC and WinUI uses native XAML scrollbars. Real owned Debug/Release GUI, actual MFC?WinUI workspace file two-way interoperability, native bridge 12/12 Debug+Release and combined architecture 20/20 PASS. Original six user settings unchanged. Separate later renewed Shell/Job/UNC failure tests are revision-specific. Full MFC search filters/history/layout and true third-party extension network/display accessibility certification remain OPEN. [M1.9 implementation and exact limits](WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md). **All earlier statements below that main has not been imported are historical pre-M1.9 status; default native main is still untouched and WinUI preview is NOT production-parity.**

---



## CURRENT CROSS-BRANCH ALIGNMENT (2026-09-29) - documents only, no new code integration

**After native mainline branch consolidation**, the last independently tested native `main` source commit before these documentation-only updates was `f074a6b1651dae6e9a1603465078310822a8f761`, with UXH-07 named workspaces, UXH-06 opt-in recent search scopes and the existing ModernUI solution superseding UI-02's older duplicate renderer. The native original-root x64 build passed **17/0 PASS WITH SKIPS** (live HKCU smoke deliberately skipped), combined 25/25 contracts and actual owned root UXH-06/Dark UI-02 GUI; additional isolated Light/Dark primary/modal tests passed. The original-root EXE SHA256 is `41D51B87E74C839C33124F22F63AC0C7379B61E0F32A12196D1459649AF81BAC`; six user settings and original screenshot were preserved.

This branch remains the **separately tested, non-default M1.8 WinUI preview** at `eb7ee1a335484d88128bfcf117a4f857fbee4c60`, not yet source-merged or feature-reconciled with that newer mainline. Its own existing M1.8 paired Debug/Release/owned GUI and 14/14 architecture evidence stays valid ONLY for the migration revision. Exactly TWO active local/remote branches and two worktrees remain; old branch names were removed and unique history archived locally. [Current alignment and explicit future code/test gates](MIGRATION_MAINLINE_ALIGNMENT_20260929.md).

**All older branch/worktree cleanup, uncommitted UXH-07 and earlier-phase notes below are revision-specific historical records, NOT the present mainline or migration branch state.** Real hostile external Shell extensions, live network SMB, external virtual namespace events, native/WinUI feature parity, physical other-DPI/HC/Narrator remain unverified.


## Latest 2026-09-29: M1.8 Shell timeout, owned COM/UNC faults and virtual notifications — SCOPED PASS

The experimental WinUI preview now distinguishes exhausted two-attempt Shell timeout failures from inaccessible UNC path errors while retaining its last accepted folder. In actual owned Debug GUI tests, a disposable native helper ran a self-contained 30-second blocking IUnknown COM method: the other pane continued and the affected helper was terminated and restarted. A separate owned GUI run exhausted BOTH 4.5-second COM helper attempts and verified the actionable timeout message and unchanged left/right folder lists. An invalid, read-only LOCAL loopback UNC path was rejected with the network-specific message and last good pane retained. No third-party extension was installed, and no actual remote SMB failure was exercised.

A private ShellNamespaceWatcher now subscribes to selected virtual-folder absolute PIDLs on an independent hidden-window message thread. The real notification-to-WinUI refresh path passed using an event for a disposable OWNED local folder, while normal virtual This PC navigation and filesystem create/delete watches still passed. A genuine dynamic This PC or third-party virtual namespace event is NOT yet verified. Final Debug/Release x64 builds, owned GUI, Release native helper/Job checks and 14/14 focused source checks PASS; six original user-setting SHA256 hashes unchanged. Default MFC product source unchanged; its earlier 20/0 PASS_WITH_SKIPS is historical, NOT rerun. See [M1.8 exact scope and evidence](WINUI3_M18_SHELL_STABILITY_20260929.md). Current work is local, not pushed/merged or shipped.

## Historical 2026-09-29: M1.7 actual WinUI 3 per-pane Shell-process isolation — scoped GUI PASS

The local WinUI migration preview now REALLY routes Shell navigation through a native C++ **two-lane supervised out-of-process** reader. Each lane creates an exact owned, same-config sibling child in its own private KILL_ON_JOB_CLOSE Job; a 4.5s helper deadline has at most one automatic retry and cannot affect the other pane's owned child. WinUI rejects obsolete route/request tokens and only accepts bounded, checked snapshot/PIDL bytes; no COM interfaces travel between processes. Real filesystem change watching is now a separate **COM-free Win32 thread**, no longer tied to the Shell navigation STA; filesystem paths come from the child rather than UI-thread SHGetPathFromIDListEx. The old in-process async worker was removed from the WinUI project, but remains unchanged for legacy native tests.

Exact paired **Debug x64 and Release x64 builds PASS**. An actual owned Win11 96DPI Debug GUI intentionally blocked the LEFT child for 30 seconds: RIGHT finished normally; LEFT automatically timed out and recovered with a new owned child; real synthetic file create AND delete refresh, independent panes, virtual This PC, own-process exit 0 and unchanged SIX original config hashes all PASS. The actual Release GUI repeated the full ordinary navigation/watcher/virtual-panes regression and passed. Standalone version-2 PIDL/IPC+Job regression PASS; focused source contracts **12/12 PASS**. MFC product and native test sources were NOT changed; the historical same-source M1.5 native 20/0 PASS_WITH_SKIPS result was reused, NOT a new native test run. The child is **not a restricted-token security sandbox**; real hostile extensions/UNC, OS HC/DPI and full file-manager feature parity are still NOT certified. [M1.7 exact architecture, logs, binary hashes and limits](WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md). These changes are currently LOCAL, not pushed/merged/released; check Git refs for live publication state.

## Historical 2026-09-29: M1.6 investigation and owned process-isolation proof — scoped only

On the separate WinUI migration branch, an actual source audit confirmed that the existing single in-process COM STA serializes both panes and its directory watches; an in-flight blocked Shell extension defeats cooperative cancellation and delays both panes. `SHGetPathFromIDListEx` also remains on the preview's UI thread. **These existing product issues are not yet fixed.** The architecture decision is to eventually isolate all untrusted Shell parsing/enumeration/name/attribute calls behind TWO bounded supervised processes (one per active pane), keep UI history and configuration in the host and decouple filesystem watches from stalled Shell work. File operations/context menus are out of scope. Full rationale and gates: [M1.6 process-isolation decision and exact proof](WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md).

A new read-only, UI-free `experiments/phase6_winui_shell/isolation` native helper compiles the actual shared Shell navigation engine into an independent Windows process. Debug and Release x64 builds PASS; **both** real Windows 11 process tests PASS: owned local and virtual This PC enumeration, bounded validated IPC, invalid/corrupt inputs, two concurrent helper lanes, test-owned 30-second block in one lane with the other still succeeding, bounded exact-child Job termination and fresh helper recovery, and automatic child reclamation upon private Job-handle closure. Original SIX user-settings SHA256 hashes remained unchanged; isolated 3/3 source and existing 5/5 architecture checks PASS. **Current WinUI GUI does NOT yet call this helper**; its native host supervisor, real blocking Shell extension tests and new GUI integration are next. Neither the default MFC product nor the remote branch was modified by this scoped local experiment.

## Historical feature-branch publication checkpoint (2026-09-29)

The dated M0, M1, M1.5 and cleanup notes below were written before branch publication; their references to a locally uncommitted branch describe the historical test-time state. Publishing this isolated migration checkpoint to a remote feature branch does **not** merge it into main, replace the current MFC product, release an installer or certify complete MFC feature parity. For the live commit and remote branch status, verify the current Git refs; the confirmed scoped build, GUI and unchanged-profile evidence remains indexed below.

## Earlier 2026-09-29: verified Git/worktree and C:\dev cleanup

Only two worktrees remain: the untouched dirty original UXH-07 tree and the still-uncommitted WinUI migration tree. Verified the real remote has only main and retained Phase5 productization; pruned 21 obsolete local remote-tracking refs and removed five strictly redundant local Phase5 branch names, with local rollback refs saved. The old CLEAN Phase5 worktree was removed after archiving 394 unique evidence files and relocating its complete pinned NuGet package cache into this migration worktree. The new WinUI Debug x64 build PASS was verified AFTER removing the old folder. See [exact inventory, archive checksums and rollback paths](LOCAL_GIT_WORKTREE_CLEANUP_20260929.md). No remote branch was deleted, no hosted Actions or push, and neither dirty active worktree was reset.

## Earlier 2026-09-29: WinUI M1.5 async COM STA and shared file watching — SCOPED PASS

**LOCAL ONLY; default MFC product NOT replaced.**
Original MFC FileChangeWatcher and the independent
WinUI 3 Shell worker now share a small MFC-free
Win32 directory change bridge (Unicode and ANSI).
WinUI folder navigation and enumeration run on a
dedicated COM-initialized STA instead of blocking
the XAML UI thread; results enter via a weak
DispatcherQueue recipient. Stable per-tab routes,
cooperative cancellation, stale result rejection,
async native file-list refresh on creation/deletion
and non-joining shutdown are implemented.

Original MFC Release x64 local CI **20/0 native PASS**,
overall **PASS WITH SKIPS** (official smoke skipped
to protect pre-existing HKCU). Owned old MFC
Go Up/Back/Forward GUI PASS, original six profile
SHA256 hashes identical. Final legacy EXE:
`B35F7ADC0768436851F8F485A70C0D042B5C70FBE9EDFF2E333C8CAE221CC835`.
New WinUI Release x64 build PASS; real owned Win11
96-DPI GUI PASS: native folder PIDL doubleclick,
real virtual This PC, independent panes/tabs,
actual automatic synthetic file create AND delete,
rapid path supersession and closing tabs without
resurrected results; exit 0, six original hashes
identical. Final new Release EXE:
`5944CB8DBAA4BB730F5E0D43DB3C7FA463B4701556644329192B95BBFA41D694`.

First Release GUI pointer attempt FAILED when
an existing Windows Explorer window covered the
test WinUI. A failure screenshot established the
test-input ownership fault; an owned foreground
PID guard was added for real pointer/keyboard
input. Same Release EXE then passed full GUI.
Native blocked-*callback* shutdown test does NOT
prove forced cancellation of hung third-party
COM calls. Virtual Shell *change notifications*,
full MFC advanced watcher extraction,
slow network extension isolation, other DPI/HC,
workspace and complete file operation parity
remain NOT ACCEPTED. See
[exact phase evidence and safety limits](WINUI3_ASYNC_SHELL_CHANGE_WORKER_20260929.md).

## Historical 2026-09-29: shared native Windows Shell engine M1 PARTIAL, separately verified

LOCAL/UNMERGED `migration/winui3-full-shell-20260929`
at old Phase5 baseline `7ceeab5` with all new work
uncommitted. A genuine MFC-independent native
`src/base/shell_navigation_core.h/.cpp` implements
Shell absolute-PIDL ownership, transactional
enumeration, parsing, per-pane/tab history and
cooperative cancellation. An old-SDK-compatible
`shell_enum_bridge.cpp` shares the original
`ShellEnumerator::enumerate` COM EnumObjects path
with the new WinUI engine. The original
`ExplorerCtrl : ListCtrlEx` still owns its UI
and advanced legacy responsibilities: complete
controller/view separation is NOT done.

Existing MFC local CI x64 exit 0,
Release native functional **18/0 PASS** (new
shared Shell/PIDL/cancel/history case), official
HKCU-sensitive smoke SKIPPED; total
PASS_WITH_SKIPS. An additional test-owned
real MFC GUI proved Go Up, Back, Forward
through the original MainFrame/ExplorerCtrl;
owned exit 0 and original six user config
hashes identical. Legacy binary SHA256:
`54C6F0C5584E957B8088670DB91414DB90A2D3BD3488B493D053177D5FD529D7`.

Independent real WinUI 3 Debug and Release
x64 builds PASS. New WinUI Release SHA256:
`12EE36CB7DC6758A824D4EAA669CFA24E0C81E497022FC36508BD0C973729F18`.
Real owned Win11 96-DPI Release GUI PASS:
two independent native Shell pane/tab snapshots,
physical folder-row doubleclick via full PIDL,
local path/history, split mode, opening
`shell:MyComputerFolder` and Back from
the virtual Shell location. Own process exit 0,
private fixture removed, six original config
SHA256 hashes unchanged. Source contracts 4/4 PASS.
[Precise logs, architecture, limits and remaining milestones](WINUI3_FULL_REPLACEMENT_20260929.md).

Remaining mandatory work: full legacy
ExplorerCtrl change notification/filtering
and file operations extraction,
asynchronous STA Shell work with interruption
boundary and UI-thread dispatch, advanced
native UI parity, settings/workspace compatibility,
actual other DPI, OS HC/accessibility and
deployment. Neither the MFC default nor
other UXH-07 and Phase5 worktrees were
changed; no hosted CI, merge or push.

## Historical 2026-09-29 full WinUI 3 replacement: M0 local scoped acceptance only

User-directed migration work is isolated in branch
`migration/winui3-full-shell-20260929` (forked from
experimental Phase5 commit `7ceeab5`) and a SEPARATE
`C:\dev\flyExplorer-winui3-migration` worktree.
The original UXH-07 dirty worktree, previous Phase5
worktree, normal native product and real user data are
untouched. No push, merge, installer or hosted CI.

A separately named real C++/WinRT Windows App SDK WinUI 3
executable now renders two independent TabView/ListView
panes, optional split layout, per-tab read-only local
folder history/address, add/close tabs and direct
navigation controls. It also links the EXISTING
UI-independent native file_operation_core.cpp, which
is only safely tested with a rejected null request;
NO user file operation is enabled yet. It does NOT
embed or reuse any old MFC view.

Actual Debug and Release x64 builds PASS. Final Release
exe SHA256:
`70080FECEA2AEDE6A545E5712CD2B6AD6E712BF0637D713C7FA661006D0C32C5`.
The exact final Release binary passed independently owned
real 96-DPI WinUI 3 GUI validation: two independent
folder listings/paths, native-core contract, left tabs
add/close, split toggle, physical address Enter/Back;
normal process exit 0, complete owned test cleanup
and unchanged SHA256 of SIX real original user settings
files. Scoped source architecture contracts 3/3 PASS.
This is **NOT a product replacement or a claim of parity**.
The remaining M1-M6 migration stages are explicitly
tracked in
[full WinUI 3 replacement plan](WINUI3_FULL_REPLACEMENT_20260929.md).

Historical Phase5 native-host experiments and all
subsequent material below remain experiment-specific and
must not be interpreted as M0 product integration.


**Latest 2026-09-28 Phase5 strict bridge teardown correction — 96-DPI isolated regression PASS, integration still experimental:** After reproducing the strict bridge failure, runtime HWND enumeration established that the WinUI 3 process owns both its actual main window and a second visible notification-host window. The Python test's cleanup `top_for(pid, lambda title: bool(title))` required exactly one visible titled window and therefore silently chose no HWND and never sent WinUI WM_CLOSE. A diagnostic with short-lived UIA subprocesses still failed, so the earlier UIA-lifetime hypothesis was rejected. The isolated experiment test now retains the already-validated product MainFrame and WinUI main HWNDs, confirms each belongs to the corresponding test-owned PID, and closes exactly that HWND.

The unchanged existing WinUI Debug x64 and production binaries were exercised on the connected Windows 11 machine at real 96 DPI. The fixed strict bridge test passed once and then **three consecutive repeats**: actual Up/Back/Forward commands, real product and reflected WinUI titles/status, clean exit code 0 for both owned processes, and unchanged SHA256 hashes of all six original user settings files per run. The separate actual WinUI 3 mouse/keyboard standalone GUI regression also PASSED and exited 0. Python syntax and git diff checks passed. Only the experiment's test harness and its README changed; no product source, binary or original user settings changed. Experiment revision: [277951e4134449734ad0ee5b26103703f8728e31](https://github.com/tngkrwlsmd/flyExplorer/commit/277951e4134449734ad0ee5b26103703f8728e31) on `experiments/phase5-real-winui3-20260928` (NOT merged to main). The older strict-teardown FAIL reports below are historical and superseded **only for this observed harness defect**. Same-process WinUI hosting, active-pane/address/Shell parity, full HKCU isolation, actual 125/150/200% DPI, OS High Contrast, clean-machine reproducibility, production packaging and framework lifetime-cost comparison remain NOT TESTED. GitHub Actions were not dispatched. See UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md.


## CURRENT POST-MERGE STATUS - UXH-07, UXH-06, UI-02 and separate WinUI M1.8 (2026-09-29)

The last independently rebuilt native source commit in the `main` lineage (immediately before this documentation-only update) is `f074a6b1651dae6e9a1603465078310822a8f761`, containing UXH-07 named workspaces, UXH-06 opt-in recent search scopes, and the **existing** ModernUI scrollbar solution. The old competing UI-02 `DarkScrollbarLayer` was intentionally superseded. On the actual rebuilt ROOT checkout, Release x64 native **17/0 PASS WITH SKIPS** (real HKCU smoke deliberately skipped), combined **25/25** focused source contracts, and actual owned UXH-06 and Dark UI-02 GUI passed. Additional isolated merged-candidate Light/Dark primary and modal GUI passed. Exact original-root executable SHA256 is `41D51B87E74C839C33124F22F63AC0C7379B61E0F32A12196D1459649AF81BAC`; the older candidate EXE hash below belongs to a **different build**. The six original user settings and untracked original screenshot remained unchanged.

There are exactly **two active local and remote branches**: `main` and the independently tested, **not yet source-reconciled** WinUI 3 experiment `migration/winui3-full-shell-20260929` at `eb7ee1a335484d88128bfcf117a4f857fbee4c60`. Historical removed branches retain local archive refs. [Current authoritative branch, test-artifact and next-gate map](BRANCH_AND_RELEASE_STATUS_20260929.md).

**All sections below are revision-scoped historical reports.** Earlier mentions of local-only, unmerged, candidate, dirty UXH-07 worktrees or in-progress old feature branches do NOT reflect the present mainline. Physical other-DPI/OS High Contrast/Narrator and genuinely broken external Shell/SMB/provider scenarios remain unverified.


## Latest 2026-09-29: UI-02 historic branch resolved with CURRENT ModernUI (owned GUI accepted)

The old local UI-02 branch was compared to the independent, already integrated native ModernUI dark scrollbar compositor in main. The old cross-thread DarkScrollbarLayer would paint the same native scrollbars a second time and conflicted with ListCtrlEx and TreeCtrlEx, so the integration intentionally **retains the existing, proven ModernUI renderer** while connecting the old feature history as a documented superseding merge. No old layer was added to the product. On the exact Release-x64 compiled post-UXH-06 source, static negative/coverage tests 19/19 and strengthened owned GUI harness contracts 3/3 (**22/22 total**) passed.

Earlier native input GUI failures reproduced in both Light and Dark because the old harness clicked an off-screen scrollbar (y=783 while work area ended at 714), inherited unrelated real-user Last Tabs into its own copied profile, and left a test-owned Tip of the Day modal intercepting physical pointer clicks. The corrected synthetic-profile test now fits the actual monitor work area, loads exactly 65 test-owned folders, physically dismisses only its own modal, and guards process-owned foreground input. **Actual native Light and Dark GUI both PASS:** tree and list vertical/horizontal scroll, native thumb drag, track page-click and the expected dark-only overlay. Separate actual Light and Dark modal-scroll GUI both PASS; every run preserves the original six user profile hashes and exits normally. No actual high DPI/High Contrast/Narrator certification. The source branch's unique old renderer is intentionally superseded, NOT copied verbatim. See [UI-02 exact conflict resolution and tested outcome](UI02_SUPERSEDED_MERGE_ACCEPTANCE_20260929.md).


## Current 2026-09-29: UXH-06 recent search locations, merged candidate ACCEPTED in isolated worktree

On top of current `main` / UXH-07 revision `4507c1f`, the previously separate UXH-06 feature branch was integrated without source conflicts and the **current combined Release x64 Unicode** executable passed canonical local CI 17/0 `PASS_WITH_SKIPS` (user HKCU runtime smoke deliberately SKIPPED). Exact integrated binary SHA256: `1EDC8616E732B4E5DB277773A6D57D071960B2C74B2786EB5F01DB6778AFC8EE`. Real owned Windows 96-DPI search GUI confirmed a 182-character read-only full-scope view, a physically selected opt-in valid search persisting one recent directory through normal exit/restart, physical recent selection, Clear and empty restart, and a **second valid opt-out search remaining empty both immediately and after another restart**. All six original user-setting SHA256 hashes remained identical. Focused UXH-06 contracts 3/3 PASS after staging localized Korean.xml. Actual separately installed Korean pack, other physical DPI, OS High Contrast/Narrator remain unverified. Older "UXH-06 WIP" documents below describe the historical preintegration state. [Exact revision-scoped final UXH-06 acceptance](UXH06_MAIN_MERGE_ACCEPTANCE_20260929.md).


## Latest: UXH-07 branch publication verification (2026-09-29)

The older “LOCAL ONLY / UNCOMMITTED” evidence below describes its original prepublication test snapshot. The actual freshly rebuilt local Release-x64-Unicode binary at this checkpoint was `E3E29B6F79DE34CA57F6B0C817E0200D507911687DB4DAF90B1D56CFA077A086`. Current local CI 17/0 PASS_WITH_SKIPS; new owned Windows GUI reverified eight invalid workspace warnings, two distinct named preset restorations after a normal restart, native Korean menu and dark scrollbar physical-wheel behavior, and isolated orphan protection. Original six user settings SHA256 hashes stayed identical across the tests. This is feature-branch evidence only, not merge/release or all-DPI/HC certification. See [exact revalidation and ignored log paths](UXH07_PUSH_VERIFICATION_20260929.md). Check live Git refs for the actual remote branch state.


> Reviewed baseline: local and remote main
> cd96de0bc8fba13a7cfeee4e5f9da9a6dc30c7c5, before
> this UXH-06/07 review change. To identify the current
> commit, run git rev-parse main. Latest separately
> verified native UI product revision at review time:
> cd96de0bc8fba13a7cfeee4e5f9da9a6dc30c7c5
> (UXH-05 scoped accessibility and clean Release).
> Start with the [development index](README.md); the full prior
> 767-line status is [archived unchanged](CURRENT_STATUS_HISTORY_20260928.md).

## 1. Latest state, constraints and next work

### Local 2026-09-29 Korean menu, submenu arrow and native toolbar Dark UI: SCOPED PASS

LOCAL uncommitted branch only, not remote main. Canonical Korean Workspaces
menu/Save/Open translation placeholders fixed; owner-drawn submenu arrows
now use one high-contrast, larger, font-independent DPI-scaled chevron.
Native toolbar Customize (outside normal ModernDialog inheritance) now
enrolls both ListBoxes in the shared dark-scrollbar compositor and draws
parent/static/buttons with the common palette. Final x64 binary SHA256:
C0FF584E685E7DEEF6E3844AC7F0A55E2AA541DE0235B66F1BA7859826E64E79.
Local x64 CI exit 0, native 17/0, overall PASS_WITH_SKIPS (official runtime
smoke skipped due to existing HKCU state). Separate focused contract 3/3.
Two owned actual Windows 11 GUI runs verified corrected Korean submenu,
visible single arrows and both dark ListBox scrollbars; real mouse wheel
moved native LB_GETTOPINDEX 0 to 9. All six original config hashes remained
identical. Wider source audit inventoried 24 direct CWnd/CDialog bases but
does NOT claim they are all defective. Actual other DPI, OS High Contrast,
speech-reader and all other context/overflow menus remain NOT TESTED.
[Detailed local evidence and remaining audit](UI_LEGACY_MENU_TOOLBAR_AUDIT_20260929.md).


### Local UXH-07 named workspaces: scoped final acceptance (2026-09-29)

**LOCAL ONLY, UNMERGED, UNCOMMITTED:** branch
`fix/uxh07-named-workspaces-20260928` at HEAD `7cc0b46`
(branch base `main` tracking ref `463f6ffd`). The 2026-09-28
main review further below remains a HISTORICAL main-baseline
description, not this local named-workspace implementation.
Canonical detailed evidence:
[UXH-07 local named-workspace record](UI_PHASE6_UXH07_NAMED_WORKSPACE_WIP_20260929.md).

Final compiled and tested Release-x64-Unicode binary SHA256:
`0873F600E45DC26BEF98948BF2B6DADBC013C1DC11633B614EED5B75BA2F091C`.
One local `local_ci.bat x64` rebuilt the product, passed the
warning policy, source preflight, and native functional
17 passed / 0 failed; exit code 0, overall PASS_WITH_SKIPS.
The automatic runtime smoke SKIPPED to preserve existing
user HKCU/profile data; it is NOT a runtime-smoke PASS.
Only the remote command process received its missing
`ProgramFiles(x86)` and `TMP` environment variables;
no persistent machine setting was changed.

On that exact executable, owned Windows 11 GUI testing PASSED:
eight malformed native file-dialog rejections;
real keyboard menu Save/Open and a separate accepted
physical-pointer submenu Save/Open repeat (top-level
View opened with Alt+V), both named snapshots with
different 1x2/2/1-tab layouts; full normal parent
exit/restart, preserved Last Tabs, and reopening BOTH
named files into distinct private child windows; and
private 3-hex stale orphan reclamation with 4-hex locked
live marker and reparse/junction external sentinel protection.
All accepted tests preserved the six original user config
SHA256 hashes and owned processes exited 0.

Two previously open causes are now distinguished:
(a) real intermittent owner-dir refusal arose because
GetTempFileName sometimes yields 3-hex names but the
safety guard assumed EXACTLY four; validation/reaping now
accept strictly 1-4 hexadecimal digits with the same marker,
reparse, age and allowlist safety; (b) apparent failure
only after restart was a Python test defect checking
`"fxw" in argv` (argv is a list of full arguments).
The corrected test reads the exact `--conf_dir` argument
and passed against the final binary. Temporary product
diagnostic hooks were removed before final rebuild.

Artifact `bin/x64/build-revision.txt` records `7cc0b46`,
the current local HEAD, but source/document changes are
uncommitted; the marker alone is NOT an exact committed
source-content ID. Do not merge/push until a separate
review and revision-aligned checkpoint are authorized.
Full mouse-only top-level menu navigation, other real DPI,
OS High Contrast, spoken screen-reader acceptance, hosted
CI, clean-machine package/installer remain outside this
scoped verification and are NOT TESTED. UXH-06/WinUI 3
independent branches were not modified; GitHub Actions
were not run.

**UXH-05 residual direct UIA actions (2026-09-28):**
An isolated 96-DPI external client physically invoked
New and selected Close via actual UIA InvokePattern;
MSAA child count changed 5->6->5, the owned process
exited 0 and six original configuration hashes matched.
The prior direct UIA action gap is now tested.
Real High Contrast/other DPI, spoken Narrator and
full Tab/F6 multi-pane traversal remain NOT TESTED.
[UXH-05 additional evidence](UI_PHASE6_UXH05_TAB_ACCESSIBILITY_EVIDENCE_20260928.md).


**2026-09-28 UXH-06/07 review complete, no new feature:**
Existing Search provides saved named multi-location scopes,
current-folder selection, editable scope and query history.
An isolated actual 96-DPI native GUI retained all 165
characters typed into a 240px search-scope edit; the
owner-drawn group label and native visual scrolling
are NOT separately certified. An actual isolated 1x2
Last Tabs profile restored distinct owned folders,
accepted physical Ctrl+T and saved/restored its
2/1 pane tab counts in a second real process.
Original six user-config SHA256 hashes remained
unchanged. [UXH-06/07 feasibility](UI_PHASE6_UXH06_07_FEASIBILITY_20260928.md).
Duplicate saved scopes and redundant last-session
presets were not implemented. New recent scopes,
readable full-path presentation and multiple NAMED
workspaces remain potential separately scoped user
needs, not completed product features. No new
Release build is claimed for this assessment.
Next: isolated real UXH-05 spoken reader and
DPI/High Contrast, and separate Phase 5 productization.


**2026-09-28 UXH-05 scoped actual accessibility accepted:**
The custom drawn TabCtrl was actually unnamed/childless
in UIA and MSAA despite working native tab shortcuts.
A minimal native MFC IAccessible provider now supplies
full named/selected tabs and selected-close/new buttons,
accessible focus/geometry/default actions and native events.
Owned actual Dark and Light 96-DPI Ctrl+T/Ctrl+Tab/Ctrl+W,
MSAA select/new/close and focused Right/Home/End passed.
Final clean Release x64 SHA256 CCB5050EC1AE316CB3D6C4728A1DDF9A724D3319DA40305CC5880B4A422ABB10, source invariants
and native 17 PASS/0 FAIL; original six user settings
unchanged. Full [UXH-05 scoped evidence](UI_PHASE6_UXH05_TAB_ACCESSIBILITY_EVIDENCE_20260928.md).
Actual speech reader, High Contrast, other DPI, direct
UIA InvokePattern and wider Tab/F6 focus are NOT TESTED;
physical Tab/F6 did not move focus from a test-focused
tab in the owned single-pane profile. Treat this as
scoped native interface acceptance only, not full
accessibility certification. Next: UXH-06/07 feasibility
and independent isolated accessibility environment work.


**Phase 6 UXH-04 scoped acceptance (2026-09-28):** Explicit
reversible native Drive/Bookmark toolbar-row compaction is now
real-GUI verified at actual 96 DPI on the isolated Windows 11
test desktop. Saved four visual rows of height **141 px** become
**101 px** only after an explicit View > Tools command;
actual keyboard J and real pointer restore to 141. The prior
owner-drawn J failure was an absent deployed language key; a
single-command fallback now works with old packs and the source
Korean XML was fixed and staged. A private 12-item bookmark
fixture proved the existing MFC chevron can actually open its
owned folder. Actual keyboard-compact -> exit -> relaunch in
the *same owned copied settings* restored 141px and retained
the original coolbar bytes. Final clean Release SHA256
\`08D6B6D17713D4C258C4DEFFE4DBA02C66B449DD87E098164E2DDF1C666EA26E\`; source checks and native 17/0 PASS. Detailed
[UXH-04 final evidence](UI_PHASE6_UXH04_EVIDENCE_20260928.md).
All tests owned their process; original user config six hashes
unchanged. Native tooltip-popup accessibility was **not**
observed either before or after this change; a listening session
and actual other DPI / High Contrast remain NOT TESTED.
Next UX work: UXH-05 custom tab accessibility verification,
then UXH-06/07 capability-overlap review.


**Latest Phase 6 UXH-03 scoped acceptance (2026-09-28):** Existing
per-pane Explorer info sidebar now automatically becomes a compact
36-DIP horizontal folder summary only when a narrow pane would
leave under 280 scaled px for the file list. At actual 96 DPI
Dark/Light in a 750-px 1x2 window, each native file list gained
88 px (178/176 -> 266/264 px). A 750-px 2x2, restored 1100-px
1x2 and 1200-px 2x2, and 1-pane layout passed physical geometry
checks; actual Win+Up/Down and title-bar double-click
expanded/restored the original full sidebar. Preserved the
owned info-bar setting, bookmark child state and six original
user configuration hashes. Scoped x64 Release, source/scrollbar/
address checks and native 17/0 passed. See
[UXH-03 responsive pane evidence](UI_PHASE6_UXH03_RESPONSIVE_PANE_20260928.md).
UXH-04 was subsequently accepted with the narrow localization
fallback; next independently investigate UXH-05 tab accessibility. Actual higher DPI/High Contrast
remain NOT TESTED for this change.


**New Phase 6 UXH-02 verified handoff (2026-09-28):** Normal
Search completion no longer opens a duplicate light information
modal. Actual 96-DPI owned Dark/Light 0/1/3 and invalid-location
GUI, physically stopped real active content search, an owned file
result's native Open parent folder pointer flow, and an accessible
native Windows event/UIA-readable summary all PASS. Release x64
and native 17/0 PASS, original six user hashes unchanged.
Binary SHA256 22D0568AB047E4A08F690B7461FB7D63E2B90A23E447BE03650D8818B2559575.
[Full UXH-02 evidence](UI_PHASE6_SEARCH_NONMODAL_EVIDENCE_20260928.md).
The UXH-03 layout is now scoped accepted; subsequent UX
work now moves to UXH-05 tab accessibility after UXH-04 acceptance.
Real other DPI, OS High Contrast and live screen-reader listening
are not yet accepted.


**Phase 6 UXH-01 follow-up (2026-09-28):** Bookmark
CHotKeyCtrl's native bright client in explicit Dark was
confirmed and fixed through ModernUI's shared native hotkey
subclass, preserving actual Ctrl+2 keyboard semantics.
Actual owned 96-DPI Dark/Light GUI, incremental Release x64
and native functional 17/0 passed. Details:
[hotkey theme evidence](UI_PHASE6_HOTKEY_THEME_EVIDENCE_20260928.md).
The UXH-02 native Search work is now scoped accepted;
other hotkey-setting windows and real High Contrast are not
individually GUI-accepted yet. Prior snapshot facts below
refer to the earlier reviewed baseline.


**Current product:** \`main\` remains the native MFC/C++ multi-pane file
manager. The optional WinUI 3 same-process integration has NOT been
merged or made available to ordinary users. GitHub Actions require
explicit separate approval for each run.

**Latest native fixes and evidence:** common native list/tree/dialog
Dark scrollbar handling; lifecycle-aware address ComboBoxEx popup;
non-overlapping column selection modal; native Dark column header,
physical divider drag and an easier-to-read numeric field.
Newly entered widths for non-pinned columns are bounded, at
actual 96 DPI, to 24..4096px without silently migrating unchanged
historic settings. Scoped Release-x64-Unicode incremental build,
owned 96-DPI Dark/Light GUI, related source checks and native
functional regression **17 PASS / 0 FAIL** were observed at the
tested product revision. This is not an all-environments product
certification.

**Immediate UI backlog:** [seven evidence-labelled hands-on
items](UI_UX_HANDS_ON_BACKLOG_20260928.md). The native bookmark
shortcut field originally observed in UXH-01 is fixed and GUI-tested
at actual 96 DPI Dark/Light; individual other hotkey dialogs remain
unverified. UXH-02's duplicate Search completion is now fixed;
UXH-03 narrow panes are now improved; next review compact command
discoverability and custom TabCtrl accessibility need targeted
measurement/verification, not ungrounded implementation.

**Still open:** HANG-01 on its original Shell/loading conditions
was not cleared by synthetic sample folders. Existing UI-01/UI-09
require previously specified scenario retests. Actual 125%,
150%, 200% display DPI, Windows High Contrast and specific older
dialog scrollbars remain NOT TESTED. Clean-PC installer/uninstaller,
complete Help topic acceptance and third-party/GFL distribution
licensing are also open.

**Experimental UI status:** Separate branch
\`experiments/phase5-productization-20260928\`, worktree HEAD
\`7ceeab515bc90089d1220d608059d254c374a339\` at review time.
The historical cross-process strict-bridge teardown failure was
resolved in the TEST HARNESS, with repeated 96-DPI bridge passes.
Same-process MFC-host WinUI 3 with experimental TextBox, native
commands and owned host PRI staging is promising experimental
evidence, NOT a tested installer/runtime deployment contract.
IME, Shell virtual namespaces, other real DPI, High Contrast and
clean-PC runtime/redistribution gates remain open.
See [main's historical bridge report](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md)
and experiment-only
[PRI/address report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_ADDRESS_PRI_EVIDENCE.md)
and [MFC-island report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_MFC_ISLAND_EVIDENCE.md).
Do not merge or enable WinUI 3 from documentation maintenance.

**Next bounded tasks:** implement only a separately reproduced
native UX candidate; acquire a disposable Windows test environment
for outstanding actual DPI/High Contrast acceptance; and continue
formal PRI build/package plus active-pane synchronization on the
isolated WinUI 3 experiment only if specifically requested.

## 2. Area-specific state and evidence

| Area | Verified versus unverified | Read next |
| --- | --- | --- |
| Native engine and MFC controls | Latest scoped x64 native 17/0; owned 96-DPI Dark/Light GUI on listed controls, not other actual DPI/HC | [DPI/theme/input evidence](UI_WINDOWS11_DPI_CONTRAST_20260928_EVIDENCE.md), [native scrollbar inventory](UI_SCROLLBAR_MODAL_OVERLAP_AUDIT_20260928.md), [column header](UI_COLUMN_DETAILS_HEADER_EVIDENCE_20260928.md) |
| Native UI follow-up | Seven candidate items; only specifically observed effects are confirmed | [Hands-on backlog](UI_UX_HANDS_ON_BACKLOG_20260928.md), [UI design policy](UI_UX_DESIGN_GUIDE.md) |
| Historical instability | HANG-01, UI-01/09 full original-profile acceptance pending | [Error history](ERROR_HISTORY.md), [UI-09 cause](UI09_ROOT_CAUSE_20260926.md) |
| Cross-process WinUI 3 | Strict test harness teardown resolved, not product integration | [Bridge evidence](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md) |
| Same-process WinUI 3/PRI | Unmerged; owned test staging is not installer-ready | Experiment reports linked above and [framework decision gates](UI_FRAMEWORK_DECISION_POLICY.md) |
| Build/dependencies/licensing | VS2026, MSVC v145, recommended Release-x64-Unicode; full install and rights review pending | [Dependency audit](DEPENDENCY_ARCH_AUDIT_20260924.md), [license review](DISTRIBUTION_LICENSE_REVIEW.md), root [build README](../../README) |
| User help | Source/package structure previously checked, not a current-content or CHM runtime acceptance | [Help audit](HELP_CONTENT_AUDIT.md), [source topics](../htmlhelp/) |

A PASS is always scoped to the revision, test environment and
observed feature stated by its original evidence. Do not promote
source-only, Debug or simulated checks to missing actual-OS PASS.

## 3. Historical records and maintenance

**Additional UI-07 source checkpoint (2026-09-24):**
The existing custom tab control now reserves a DPI-scaled close target
for sufficiently wide tabs and paints a palette-backed close glyph on
the selected or hovered tab. Pointer release within the same tab uses
the existing tab-close command/confirmation path; the existing localized
close command string supplies its tooltip. Existing keyboard shortcuts,
tab indices, old profile options and high-contrast palette routing are
retained. This is source work only: compile, release-on-close behavior,
narrow layouts, hover/focus and actual final pixels are NOT TESTED.
UI-07 remains OPEN until Windows acceptance.

**Additional UI-08 source checkpoint (2026-09-24):**
The already-supported shared folder-tree mode becomes the default for
new profiles, avoiding duplicate trees when a user splits the view
vertically. Existing saved pane configurations, individual-tree mode,
folder-tree visibility controls, file lists, shortcuts and information
panels remain available. This is a limited initial-layout change, not
dynamic narrow-pane adaptation. A source guard confirms the existing
shared/per-view owner paths. Current-revision Windows build, clean-profile
first launch, split-pane resizing, layout persistence and visual evidence:
NOT TESTED. UI-08 remains OPEN for the broader acceptance case.

**Follow-up UI-08 source checkpoint (2026-09-24):**
Fixed the existing command-line split-column override: it had assigned
`sRowCount` instead of `sColumnCount`. The explorer-style Contents
sidebar now adapts to current pane width and DPI, reserving approximately
280 logical pixels for file columns where available; very narrow panes
share their remaining width without a negative list rectangle. The
Contents window, all displayed data, user-selected mode and individual
tree option remain intact. This is source/layout work only: the actual
Windows x64 build, command-line launch, splitter dragging, layout
persistence, light/dark/mixed-DPI and accessibility: **NOT TESTED**.
UI-08 remains **PARTIAL / RUNTIME RETEST OPEN**.

**UI-06 menu-height / client-background source checkpoint (2026-09-24):**
BCMenu app-owned popups and their pre-existing submenus now use the
documented `MENUINFO` max-height setting based on the popup monitor's
work area so Windows can provide native overflow scrolling without
dropping commands. In Dark/non-High-Contrast only, an elevated palette
brush covers the native client background; original menu settings
are restored and the transient brush is destroyed when tracking ends.
High Contrast and shell-owned context menus are not recolored.
**Native non-client outer menu frame color is still OS-owned** and
must not be claimed fixed from the client background alone.
Current-revision Windows compiler/runtime (small-monitor overflow,
keyboard/submenu, Light/Dark/HC screenshots): NOT TESTED. UI-06 remains
**PARTIAL / VISUAL RETEST OPEN**.

**UI-05 default command-band / settings spacing source checkpoint
(2026-09-24):** On a fresh profile the bookmark band no longer forces
a separate rebar row after the drive band. Both retain their chevrons,
normal narrow-window wrapping and explicit user-configurable multiline
modes. Previously persisted band order/BREAK settings still restore
from the existing coolbar file. Settings navigation row minimum rises
from 34 to 38 DPI-scaled units; separation between the description
and body rises from 12 to 16, without expanding overlapping controls
inside fixed legacy resources. A static contract guards the default
band flags, persistence and metrics. Other command grouping and
per-dialog control spacing require visual design/test; UI-05 is
**PARTIAL / WINDOWS VISUAL RETEST OPEN**.

**UI-06 chevron-popup position/paint follow-up (2026-09-24):**
The app-owned custom toolbar overflow popup now clamps to the anchor
monitor's *work area* (multi-monitor/taskbar aware) instead of the
entire desktop, and uses the correct left coordinate when choosing
horizontal placement around an excluded control rectangle. Its
`CWindowDC` now has one RAII release rather than an extra manual
`ReleaseDC`. A negative source regression guard covers both bugs.
Actual current-revision Windows build, large custom popups taller
than the available work area, keyboard/hover, taskbar on alternate
edges, multi-monitor DPI and final border pixels: **NOT TESTED**.
UI-06 remains **PARTIAL / RETEST OPEN**, and OS-owned native menu
outer border is intentionally untouched.

**UI-03 native location text inset (2026-09-24):**
The search dialog now sets a documented `EM_SETMARGINS` left inset
on its actual nested ComboBoxEx edit HWND, scaled to the current
dialog DPI. It reapplies the inset after the base dialog DPI-change
handler, leaving native location icons, right margin, text selection,
autocomplete and horizontal scrolling intact. A source wiring guard
checks init/DPI pathways. This is not proof that the Dark nested edit/
dropdown is visually correct; focus/hover/keyboard, location search,
OS High Contrast and mixed-DPI screenshots are **NOT TESTED**.
UI-03 remains **PARTIAL / RUNTIME VISUAL RETEST OPEN**.

**UI-01 one-page visibility reinforcement (2026-09-24):**
Settings navigation now hides every other *created* page rather than
only the previously selected index. Following synchronous theme/config
notification, it reasserts the selected-page visibility contract,
showing the selected page only if the HWND is unexpectedly hidden.
Own WS_VISIBLE flags are checked independently from ancestor visibility.
The existing theme transaction snapshot remains in place, and saved
settings, navigation IDs, modified flags and focus handling are not
intentionally changed. A negative source guard rejects the old
selection-only hide loop. The exact Windows sequence (General ->
Appearance -> Light -> Apply -> Filtering), focus preservation,
repeated switches and current-revision x64 compilation: NOT TESTED.
UI-01 remains CODE UPDATED / MATCHING RUNTIME RETEST OPEN.

**2026-09-24 user screenshot — bookmark-toolbar ghost icon/text
(UI-09, source candidate implemented, visual acceptance open):**
The supplied narrow Light-looking toolbar image shows clipped colored
strokes beneath Desktop/Libraries/Documents/media shortcut icons and
short black fragments beneath their Korean captions. The source had
a full-button postpaint owner for Dark but a text/dropdown-only
postpaint overlay for Light, leaving native icon and text pixels
outside the smaller overlay rectangle. The non-High-Contrast Light
path now reuses the existing complete owner for the entire button,
including palette fill, image-list icon, label, and dropdown.
Command IDs, bookmark data, native keyboard/tooltips/accessibility,
saved layout and High Contrast native rendering remain unchanged.
The original Dark full-item ownership guard now checks both Light
and Dark and forbids the former partial Light branch. This is an
inferred source root-cause candidate, not a revision-matched Windows
visual fix claim. Full validator, current x64 compiler and Light/
Dark/HC/DPI/hover toolbar pixel regression: **NOT TESTED**.
UI-09 is SOURCE UPDATED / VISUAL RETEST OPEN.

**2026-09-24 UI-09 repeat screenshot after 541cd0f3 — prior
postpaint candidate did NOT resolve the visible ghost:**
The user's repeat report supersedes the prior source-only hypothesis.
The remaining unguarded renderer was the bookmark toolbar's WM_PAINT
/ WM_PRINT / WM_PRINTCLIENT path: reflected NM_CUSTOMDRAW postpaint
is not a guarantee for the rebar print/composition route. The new
fix routes those final non-High-Contrast bookmark pixels directly
through one full client renderer, including image-list glyphs, labels,
button states and separators. It checks available icons before
taking ownership; otherwise it retains the native fallback.
High Contrast/native route, button commands, keyboard navigation,
drag/drop and saved layout are unchanged. A source regression guard
requires explicit direct paint and print ownership, not only
NM_CUSTOMDRAW postpaint. The actual source-revision Windows x64 build
and before/after screenshots (including hover, drag, DPI and
print/rebar) are **NOT TESTED**. UI-09 remains RUNTIME OPEN.

**2026-09-24 UI-09 second diagnostic track: idempotent bookmark buttons.**
Closer source review found an independent concrete data/layout defect:
BookmarkToolBar::setBookmark inserted every manager item via
TB_INSERTBUTTON without first deleting existing buttons. If this
initialization runs again with the old toolbar still populated, the
control holds duplicate commands and can expose a partly clipped
second row. A full update also deleted and recreated an image
list redundantly before calling setBookmark, which recreated it
again. The source now makes setBookmark the only full rebuild owner,
clears existing buttons first, inserts exactly one per manager item
and checks the final native button count in debug builds. Re-show
registers asynchronous icon updates only once per visible lifetime.
This complements the new bookmark-specific paint/print owner rather
than asserting which path caused the user's exact screenshot.
Source structure checks were constructed. Revision-matched Windows
compiler, actual toolbar count at reproduction, 100/125/150/200%
DPI, visibility toggling, wrap/chevron and final screenshots:
NOT TESTED. UI-09 remains OPEN.

**2026-09-24 follow-up after new user Light/Dark screenshots —
filtering list contrast and bookmark row layout (source checkpoint):**
The two settings screenshots confirm per-filter text is nearly
invisible on the Light elevated background; the Dark screenshot
also shows native bright scrollbar chrome that remains a separate
UI-02 issue. CfgAppearanceFilteringDlg previously corrected only
exact black on Dark; its user-configured pale/white filter colors
were drawn unchanged against the Light surface. The list custom
draw now evaluates WCAG relative luminance/contrast (4.5:1) for
each configured color against the current Light/Dark row background
and uses the active palette foreground only if inadequate.
Persisted filter RGB preferences and the actual filter semantics
are unchanged. The page reapplies native ListView text/background
and header invalidation after settings/theme/system-color change.

The repeated bookmark screenshot still shows colored icon and
caption fragments along the lower edge after earlier pixel-owner
and idempotent-button changes. A layout risk introduced by this
project's own UI-05 band compaction is now reversed: the bookmark
band again starts an independent rebar row and setWrapable also
corrects persisted same-row band styles that otherwise override
the fresh-profile change. Existing toolbar data and chevron/
multiline options remain available, but this correction does
override previously saved bookmark same-row positioning on launch;
users can rearrange bands during the session.

Source structure checks: constructed for these two owners. Full
source-invariants execution, current Windows compiler, exact
new Light/Dark screenshots, 100/125/150/200% DPI, keyboard and
High Contrast: NOT TESTED. Filtering UI-10 and bookmark UI-09
remain RUNTIME VISUAL RETEST OPEN; UI-02 scrollbar remains OPEN.

**2026-09-24 local x64 preflight regression on eebc68d (user log):**
The uploaded `local-ci(20260924-130832).log` stopped at the source
invariant preflight, before solution generation or compilation.
The old Win11 filter-list guard still demanded four code fragments
removed intentionally by the new Light/Dark contrast implementation:
the former `sListBackground` initializer assignments and the
black-only Dark fallback. This is a stale *validation contract*,
not evidence of a new Visual Studio compile error. The revised
guard checks the real `refreshFilteringListColors` and
`OnCustomDrawList` owners, preserves header, selection, and High
Contrast checks, and forbids the black-only regression. The dedicated
UI-10 contrast validator is unchanged. The log explicitly says
`bin/x64/fxfile.exe` was **not rebuilt** and still has revision
`468ee555`; therefore the newly reported screenshots cannot
validate the eebc68d executable without a successful new build.
The fix is source-reviewed only; rerun `local_ci.bat x64` on
the new revision before claiming build success or closing UI-09/10.

**2026-09-24 x64 compiler follow-up on `1a555ba`:**
The user's uploaded `local-ci(20260924-132251).log` confirms the
full source-invariant preflight **PASS**, solution generation **PASS**,
then MSBuild **FAIL** at `cfg_appearance_filtering_dlg.cpp:117,118`
with C2065 undeclared `sPalette`. The previous UI-10 edit moved
native list color setup into `refreshFilteringListColors` but
accidentally removed the *other* local `sPalette` declaration that
`OnInitDialog` still needs to choose Dark border style. Restore that
single local `ui::ModernUI::getPalette()` declaration immediately
before the border conditional without duplicating native list
background logic. The new targeted regression guard checks declaration
order inside `OnInitDialog`, not anywhere in the source file.
This checkpoint is SOURCE-CORRECTED only; a revision-matched x64
build, native tests and user-screen Light/Dark/HC acceptance
remain **NOT YET RETESTED**. UI-09/UI-10 are still runtime OPEN.

**2026-09-24 remaining Light filtering list issue (source-level
selected-row path):** The owner explicitly reports a successful latest
build yet still observes the same Light filtering screenshot. Stop
attributing the result to a stale executable. A second foreground
path in `CfgAppearanceFilteringDlg::OnCustomDrawList` bypassed the
previous per-filter contrast resolver: every `CDIS_SELECTED` item,
including when the list itself was UNFOCUSED, used
`mSelectionText` (usually white). An unfocused selection instead
uses `mInactiveSelection` (very pale blue on Light), so white
text remains invisible. Correct the pairing: active selection
foreground `mSelectionText`, inactive selection foreground
`mText`. No per-filter stored colors or filtering semantics
change; the WCAG resolver continues to handle normal rows.
Extend the regression guard for this independently observed
selected-state branch. This is source diagnosis/fix only:
revision-matched Windows execution, High Contrast/Light/Dark
screenshots and toolbar UI-09 remain OPEN. The separate bookmark
ghosting report is accepted as a current-binary failure; prior
renderer/band hypotheses are not runtime-proven.

**2026-09-25 UI-09 user-confirmed still failing on a built current revision:**
The user explicitly reports that they already built and ran the latest code
and the bookmark icon/text lower-row fragments remain. Do not request the
same source/executable-version check again or represent earlier custom
paint, idempotent rebuild, or default band placement changes as runtime
success. Inspecting the toolbar source reveals two additional native
layout vulnerabilities: the no-wrap transition clears
`TBSTYLE_WRAPABLE` but never clears retained per-button `TBSTATE_WRAP`,
and `onUpdatedToolbarSize` passes `RBBIM_CHILDSIZE` with
uninitialized `cyMaxChild` and `cyIntegral`. The nonwrapping bookmark
path now clears per-button wrap bits, initializes the entire
REBARBANDINFO, and constrains manual glyph/text painting to the first
native item row (after filling the entire client surface). The user's
multiline-enabled mode remains available. A dedicated negative source
guard checks the native wrap reset, zero-init and first-row pixel clip.
The repo main commit contains only source-level candidates: no Windows
compilation, actual `TB_GETITEMRECT` trace or final screenshot
acceptance was available in this environment. The user-reproduced
UI-09 remains **OPEN** until matching runtime evidence. The separate
unfocused-selected Light filter-row defect received its own
source adjustment at `ef48a29` and also awaits screenshot acceptance.

**2026-09-25 UI-09 source checkpoint after screenshot at `5a8fc7e`:**
The screenshot and displayed build revision match the previous source-only
repair, yet the bookmark icon/label fragments persist. A new *unverified*
candidate changes the bookmark-only non-High-Contrast paint gate: transient
asynchronous icon availability can no longer switch the whole toolbar back
to native painting, and nonwrapping drawing now skips any item not in the
first native button row (as well as preserving the existing row clip).
Static source inspection identified both paths; neither has been shown by
a Windows trace to cause the reproduced pixels. This main checkpoint is
CODE CHANGED / WINDOWS COMPILER, NATIVE RUNTIME AND VISUAL NOT TESTED;
the current user-reproduced UI-09 remains **OPEN**. Collect per-button
`TB_GETITEMRECT`, painting-route and same-screen screenshot evidence.
No GitHub Actions were run as part of this checkpoint.

**2026-09-25 UI-09 instrumentation-only checkpoint after external HWND trace:**
An owner-provided geometry snapshot of the previous `f18468a8` executable
records 8 bookmark items, exactly 1 row, no `TBSTATE_WRAP`, native item
rectangles with 22px height and a Rebar child with 40px client height.
This rules out an actual native second row in the captured state, but
does not establish whether the 18px gap creates the photographed slivers.
At the owner's request this main checkpoint first adds **opt-in internal
measurements, not another guessed render fix**: when launched with
`FXFILE_UI09_TRACE=1`, the bookmark-only code records before/after
ModernUI metrics, before/after native autosize, after parent Rebar
notification, and direct/native paint route and HDC clip geometry.
Only numeric HWND, button IDs, flags and rectangles are logged to
`%TEMP%\\fxfile-ui09-<PID>.log`; no bookmark targets or labels.
The default path neither writes this file nor changes render/sizing
behavior. This snapshot still needs a revision-matched Windows x64
compiler run and an actual user trace. UI-09 remains **OPEN**.
GitHub Actions was NOT RUN.

**2026-09-26 user Light/Dark main-window screenshot review — DOCUMENTED ONLY:**
Two owner screenshots of the same Documents main view show bright native-looking
file-list/tree scrollbars on Dark (additional UI-02 evidence), dense upper command
grouping and unused adjacent band space (UI-05 design review), truncated
single-pane modification dates despite wide unused right-side file-list space
(new UI-11), a narrow tree with cut-off long names/small expansion glyphs
(new UI-12), and dense folder information/bookmark-link wrapping (new UI-13).
File-list header spacing and a text-level focus cue need interactive assessment,
not a declared bug (UI-14 candidate). The old bookmark-sliver pattern is not
clearly discernible in these two images; this does NOT overturn the prior
revision-matched failure or close UI-09. See
`docs/development/UI_UX_AUDIT_20260924.md` for observed versus proposed
behaviors and exact acceptance tests. No build revision, DPI or interactive
sequence was visible in these screenshots. This documentation checkpoint made
no application code changes; Windows build/runtime/visual acceptance remains
NOT TESTED. GitHub Actions NOT RUN.

**2026-09-26 screenshot implementation checkpoint — UI-11/12/13 SOURCE CHANGED, RUNTIME OPEN:**
The default modified-time column was statically 140px; new FOLDER_DEFAULT
layouts and newly enabled date columns now use 225 logical px scaled to the
list HWND DPI. Saved user/per-folder column widths remain untouched.
FolderCtrl adds native TVS_INFOTIP full display-name callback while preserving
native horizontal scrolling and existing tree layout preferences. The adaptive
ContentsWnd renders header/bookmark text within its actual client instead
of fixed 200/198px bounds, chooses 224 logical px preferred width and 120px
conditional minimum, and shares a 5px bookmark link gap with scrolling.
An additional source invariant protects the linked behavior. This commit
does not change native non-client scrollbar painting (UI-02), force Rebar
regrouping (UI-05), or claim an unverified header defect is fixed (UI-14);
all remain OPEN/PARTIAL as tracked in the UI audit. Existing-profile
UI-11 behavior and native light/dark/UI-09 screenshot acceptance, current
Windows build, runtime and DPI verification: NOT TESTED. No Actions run.

2026-09-26 source checkpoint for remaining screenshot issues: UI-02 uses public GetScrollBarInfo-based list/tree Dark non-client scrollbar post-paint with native input preserved and High Contrast bypass. UI-05 only on new, unsaved, single-line profiles can combine drive/bookmark after measured native widths and 48-DIP slack fit the Rebar client; saved custom layout persists. UI-14 mixed owner/native header final painting and narrow sort glyph bounds are hardened, but the reported visual concern is unconfirmed. These are CODE UPDATED / WINDOWS COMPILE AND FINAL VISUAL NOT TESTED; do not close UI-02/05/14 yet. UI-09 still OPEN pending original-screen internal FXFILE_UI09_TRACE=1 ownership data. No GitHub Actions run.

## Outstanding near-term work

1. Address the reproduced settings-page visibility and Dark rendering issues
   in the UI audit. UI-01 and the UI-04 mojibake reorder-label path now have
   source fixes with runtime/visual retest still required. Current x64
   compile/regression has passed at `bee95d9`;
   regenerate and inspect the CHM and validate the installer in an isolated environment.
   Keep compiler, visual, runtime, installer and third-party licensing
   evidence separate. Non-default x86/release/full profiles need user
   scope expansion; hosted Actions need per-run explicit approval.
2. Source-check the legacy help detail pages against the actual
   application menus, language packs, settings tree, shortcuts and
   screenshots before claiming them current. No speculative remapping.
3. Automatic updates have been intentionally removed. For existing personal
   installations, manually check the legacy `fxfile-upchecker` startup entry
   and old installation directory if you want complete on-machine removal;
   no migration deletes existing Windows user startup entries automatically.
4. Audit exact GFL SDK redistribution permissions and all included
   third-party binary provenance/requirements before public packaging.
5. Decide whether old `dist/history.txt` belongs in future installers.
   Until changed, ship it with an explicit **historical releases only**
   header; do not transform or delete its original history.
6. Consider the remaining dependency ABI checks, optional x64-launcher
   feasibility study and VLD release staging only with direct build/package
   verification and the architecture limits in the dependency audit.
   The retired updater is not a migration candidate.

## Documentation ownership and history

| Owner document | Responsibility |
| --- | --- |
| `README`, `LOCAL_CI_MANUAL.txt` | Public-facing developer build, test and packaging procedures |
| `AGENTS.md`, vendored `.agent-policy/` core | Required agent rules; vendored policy core is not edited for project facts |
| `.agent-policy/PROJECT.md` | Project-specific facts, reviewed-path snapshot, individual work items and live handoff requirements |
| **This page** | Concise live summary of completed work, open decisions and evidence limits |
| `ERROR_HISTORY.md` | **Preserved, append-only historical evidence**, including context-specific test outcomes and errors |
| `DEPENDENCY_ARCH_AUDIT_20260924.md` | Current inventory summary followed by the immutable dated audit and cleanup checkpoints |
| `HELP_CONTENT_AUDIT.md` | Current help scope, legacy detailed-topic inventory and Windows user-help acceptance tasks |
| `UI_UX_AUDIT_20260924.md` | Revision-matched interactive observations, open UI findings, source-only OS compatibility candidates and reproduction/acceptance cases |
| `UI_UX_DESIGN_GUIDE.md` | **Required future UI/UX design and validation standards:** Windows 11 Explorer reference, Microsoft Fluent/Windows UI Kit/WinUI 3 Gallery, MFC preservation and optional isolated WinUI prototype |
| `DISTRIBUTION_LICENSE_REVIEW.md` | Observed license contradictions and unfinished third-party distribution checks |
| Root `LICENSE` and `CREDITS` | Existing application and third-party license notices; never rewrite on the basis of assumptions |

When source, build output or runtime evidence contradicts a summary,
correct this page and `PROJECT.md` during the same logical work unit.
Keep the historical evidence that led to earlier conclusions intact.


## 2026-09-28 native AddressBar drop-down Dark fix

The existing MFC address drop-down now draws its own dark list items and
uses the UI-02 click-through native scrollbar overlay with popup-scoped
z-order and hide-time cleanup. Verified at actual 96 DPI with synthetic
Dark and Light popup screenshots, scrollbar pointer clicks, unchanged
original six config hashes, incremental Release-x64-Unicode build and
native functional regression 17/0. Actual higher DPI and OS High Contrast
runtime acceptance remain untested. This is independent of the opt-in
WinUI 3 Phase 5 experiment; see
docs/development/UI_ADDRESS_DROPDOWN_DARK_EVIDENCE.md.


## 2026-09-28 Phase5 physical long-path input fix (EXPERIMENT ONLY)

On experiments/phase5-productization-20260928, the opt-in MFC-hosted
WinUI 3 InputSiteWindowClass was excluded from secondary MFC main-frame
accelerator preprocessing after the Windows App SDK pretranslation.
Repeated Release test-owned GUI runs physically typed all 119 synthetic
path characters including all nine backslashes, then used a real
keyboard Enter to navigate the existing native ExplorerCtrl.
The default release TextBlock-island baseline and original six config
hash checks passed. Release packaging-stage contracts have only
isolated tests; IME, actual higher DPI/High Contrast, dependency license
review, clean-machine install/uninstall and complete HKCU isolation
remain unverified. The feature is NOT merged into main.

### Imported mainline historical status references (2026-09-29)
The previous CURRENT_STATUS contents, including superseded
intermediate “latest” claims, are preserved **byte-for-byte**
in [CURRENT_STATUS_HISTORY_20260928.md](CURRENT_STATUS_HISTORY_20260928.md).
Treat old “next task” paragraphs as dated history, not live guidance.
Use [ERROR_HISTORY.md](ERROR_HISTORY.md) for the original
append-only diagnosis, [original UI audit](UI_UX_AUDIT_20260924.md)
for earlier screenshots and issues, and [the index](README.md)
to navigate the separate dated experiment/release evidence.
Update this short page when branch status, accepted tests or open
work changes; append detailed execution proof to an appropriate
dated evidence document, not to the top of this summary.
