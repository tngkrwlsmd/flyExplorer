# flyExplorer — current project status (2026-09-28 baseline; 2026-09-29 migration-branch addendum)

## Latest 2026-09-29: M1.6 investigation and owned process-isolation proof — scoped only

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



**Later Phase5 native NuGet checkpoint, 2026-09-28:** The isolated WinUI3 Debug|x64 build now PASSES normal NuGet native asset resolution (native,Version=v0.0) and full compile/link WITHOUT bypass, superseding earlier mismatch/bypass reports. The actual 96-DPI standalone UI pointer/keyboard regression PASSES with clean exit. An explicitly test-owned WinUI3 UIA InvokePattern bridge sent real product Up/Back/Forward commands and original six config hashes matched, but its strict cleanup regression currently FAILS because the owned WinUI3 helper sometimes times out and must be terminated. Prior pointer automation also intermittently missed a Back event. Product source/executable unchanged; same-process XAML Islands, full integration, fresh-machine deployment and actual higher DPI/OS High Contrast remain untested. Experiment commit ddff6a3397e3c2ade38f1a173a6567366ec9ac84; details UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md.


**2026-09-28 Phase5 continued: real product command bridge tested; product unchanged.** An isolated, explicitly test-owned WinUI 3 XAML prototype now forwards allowlisted scalar Up/Back/Forward commands from actual UI Automation clicks to a private-profile real product MainFrame through existing CommandContext/ExplorerCtrl routing, without editing the product. Native real-product and real WinUI GUI tests plus experiment x64 compilation passed at 96 DPI; both test-owned processes exited 0 and original six config hashes matched. The experiment is e845eb45f3bd3cf978bbecaecf7984dc6f0d22a0 on experiments/phase5-real-winui3-20260928 ONLY. This is cross-process proof, NOT same-process integration or active-pane state/address parity. Ordinary VS18 NuGet UAP/native asset resolution remains unresolved; prototype-only build bypass still required. Higher real DPIs, actual OS High Contrast, complete profile/HKCU, Shell/multi-pane parity and lifecycle-cost comparison remain NOT TESTED. See UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md.


**2026-09-27 Phase4 partial evidence (actual 96 DPI pass; migration undecided):** Revalidated unchanged production executable 6d1f763 with an isolated four-file user UI copy, synthetic folder and real 96 DPI: preserved three 1175x40 and one 1175x21 toolbar bands, 28px native header, 36px address; original settings hashes equal and isolated exit 0. Phase3 same-revision synthetic Dark/Light/System evidence reused; other real DPIs, actual OS High Contrast and complete HKCU/profile isolation remain NOT TESTED, protected-user runtime smoke SKIPPED. No new confirmed product defect, no speculative product edit or rebuild. Isolated experiment branch ad561271 compiled and live-tested C++/WinRT Foundation + Win32 navigation controls, NOT WinUI 3 and NOT product engine integration. Actual WinUI 3 development tools and equal-feature UI comparison require a later approved bounded experiment. Details: UI_FRAMEWORK_PHASE4_EVALUATION.md and UI_UX_AUDIT_20260924.md.


**2026-09-27 UI/UX Phase 3 — primary native navigation (synthetic and guarded saved-layout replica):** Built and visually exercised product revision 6d1f76388b0b8326568478ce35814aba1eb69a0e on connected Windows 11 x64. Back/Forward/Up keep their native commands and user-saved toolbar layout while gaining a scoped, DPI-scaled icon/hover target and independent history-arrow hover. Local compile/link and 17/0 functional checks PASS, focused source tests and preflight PASS; protected-HKCU smoke SKIPPED. Real synthetic mouse navigation/hover and Dark/Light/System GUI checks PASS. A partial copy of the saved user profile four saved UI files preserved measured native toolbar/header/address geometry with unmodified originals, but complete live personal profile/HKCU, High Contrast and other DPI conditions remain RETEST OPEN. See UI_UX_AUDIT_20260924.md for scoped evidence and limitations.


**2026-09-27 UI/UX Phase2 synthetic GUI PASS (real user profile RETEST OPEN):** The ComboBoxEx address surface is rounded using the existing Fluent metric while retaining native focus, editing, autocomplete, dropdown and High Contrast fallback. Product executable eb958777a7cb182606b4511672abf08f852a9daf passed Windows x64 compile/link, native 17/0 functional, source preflight and 8 focused tests. Isolated Dark/Light/System header and address keyboard focus, narrow Dark response and actual Light dropdown/Escape passed; official HKCU smoke skipped. Read-only real user config selects Light, but the saved personal layout and other DPI/High Contrast have not been tested. Local-only evidence is recorded in UI_UX_AUDIT_20260924.md.

**2026-09-27 user screenshot follow-up — list header/address: TESTED on synthetic VM, original user profile RETEST OPEN.** At product commit 03a68baff006f5d58cca304b7d0b36cc9ce28b49, native HDM_LAYOUT adjusts both the measured header height and file-list content reservation so the native header cannot shrink below 28 DIP during reflow; the address field shares command chrome rather than a visibly raised full-width background. Connected Windows Release-x64-Unicode compile/link and 17/0 native functional checks PASS; official startup smoke SKIPPED to avoid user HKCU. Six new targeted static tests and full source preflight PASS. Synthetic Dark and Light UI geometry, header click, editable location focus, responsive narrow Dark resizing and normal test-process shutdown were checked with local-only captures. The uploaded user's custom profile/DPI and OS High Contrast remain NOT TESTED. Detailed evidence: UI_UX_AUDIT_20260924.md. The product executable corresponds to 03a68baff006f5d58cca304b7d0b36cc9ce28b49, not the subsequent docs-only final commit.



**2026-09-27 UI/UX Phase 1 verified tab title improvement:** Same-PC Windows Explorer comparison confirmed that the old 150-DIP flyExplorer tab truncated FXUI_Synthetic_Root at 1240 x 790 while Explorer showed the full title. At tested product source/binary revision 5db3f92b46bf38c2cea2ed0e12f06d199ecc86de, a scoped 232-DIP default and bounded narrow/multitab allocation built and linked on Windows VS 2026 x64, native functional regressions 17/0 PASS, source invariants PASS, 5 targeted source mutation tests PASS; official runtime smoke SKIPPED to protect the existing user HKCU. In an isolated synthetic GUI profile, the full original tab title was visibly readable, mouse-clicking New Tab opened a second tab, narrow resizing stayed responsive, and our test process exited normally. Keyboard-only input, Light/High Contrast and other DPI environments were not verified. Screenshots are retained locally (logs/phase1, ignored), not committed. The tested product commit is 5db3f92b46bf38c2cea2ed0e12f06d199ecc86de; any subsequent documentation-only final merge revision is not a separate rebuilt product executable. See UI_UX_AUDIT_20260924.md.

**Purpose:** Fast, current-state entry point for maintainers and development
agents. This is an evidence-labelled summary, not a replacement for source,
build scripts, the project policy, or an independently executed test.
Update this page after each logical work unit that changes its facts.
For the chronological diagnosis and original evidence, retain and use
[`ERROR_HISTORY.md`](ERROR_HISTORY.md) rather than moving/deleting entries.

**2026-09-27 UI-02 final-pixel redesign — Windows Dark 96-DPI
DIAGNOSTIC PASS / FINAL REVISION AND USER ENVIRONMENT RETEST OPEN:**
사용자의 원래 Dark 파일 목록에는 밝은 native scrollbar가 여전히 노출된다.
기존 GetWindowDC/지연 PostMessage 방식은 native thumb modal tracking 동안
OS의 최종 픽셀 소유권을 확보하지 못한다. 연결된 VM은 OS도 Dark이므로
원래 OS-밝음 증상 자체가 이 VM의 기존 바이너리에서는 재현되지 않았다.
다만 격리 VM 실험에서 별도 child layered overlay는 drag 때 OS에 가려졌고,
**동일 UI thread의 root-owned/비활성/HTTRANSPARENT layered popup**은
native thumb drag 입력을 방해하지 않고 8프레임 내내 덮개가 유지됐다.

같은 Windows VM에서 중간 C++ 구현을 x64 compile/link하고 native regression
17 PASS/0 FAIL, local_ci 결과 PASS_WITH_SKIPS(HKCU 보호에 따른 runtime smoke
SKIP)를 얻었다. 일시적 diagnostic RGB tint를 넣은 테스트 빌드는
실제 8프레임 thumb drag에서 popup 자체의 track이 항상 7420 픽셀,
각 프레임 native xyThumbTop과 popup thumb 위치가 1px 이내로 일치했고
native thumb가 23→172로 이동했다. 이 test tint는 source에서 **삭제**했다.
따라서 이는 검증 당시 source snapshot의 원인 진단 evidence이며,
이후 최종 commit을 대상으로 한 별도 full CI/UI 재검증 없이
최종 release visual PASS라고 승격하지 않는다.

새 C++ 구현은 ListCtrlEx/TreeCtrlEx별 overlay lifecycle을 ModernUI에 두고
SCROLLBARINFO geometry, WS_EX_LAYERED|WS_EX_TRANSPARENT,
WH_CALLWNDPROCRET와 native MSGF_SCROLLBAR thread hook으로 기존 input을
보존하면서 layered 최종 색상을 추적한다. 동기적 NC 그리기와 timer는 없다.
새 source mutation 회귀 15개 및 layer 캡처를 포함한 visual collector
9개 테스트는 PASS, 전체 static preflight PASS. 모든 새 overlay window는
destroy/theme/visibility lifecycle에서 정리되도록 보호한다.

다음 검증은 최종 git SHA와 x64 executable marker가 일치하는 상태에서
Dark 96-DPI list/tree drag, wheel/keyboard, Light/System, UI-05/UI-09 및
종료/재실행을 반복 검사한다. 원래 사용자 OS/monitor 설정에서 동일
스크린샷 재검증, High Contrast와 125/150/200% DPI는 여전히 OPEN이다.
코드가 같은 증상을 수정했다고 전역 사용자 환경에서 단정하지 않는다.
GitHub Actions는 별도 개별 승인 없이 실행하지 않는다.

**2026-09-27 실제 Windows UI-05 새 프로필 후속 — 96 DPI DARK RUNTIME/VISUAL PASS, 기타 DPI RETEST OPEN:**
Remote Desktop Commander/WinApp CLI가 연결된 Windows에서 격리된 합성
프로필과 합성 폴더·파일 205개만 사용하여 실기 화면을 검사했다.
최초 e59aed97의 800×600 신규 창은 세 rebar 밴드가 따로 존재하고,
1920×1032로 최대화해도 드라이브와 북마크가 계속 별도 행으로 남았다.
최초 UI-05 리사이즈 재시도 수정 fe5e49d의 화면에서는 동일 행으로
합쳐졌으나 드라이브 밴드가 거의 전폭을 유지해 북마크가 오른쪽
chevron에 숨겨졌다. 이는 실제 화면에서 확인한 두 번째 결함이다.

후속 3aab666 소스는 저장된 레이아웃/사용자 밴드 드래그를 존중하면서
**더 넓어진 신규 프로필 창에서만**, 예약 메시지로 실제 rebar ideal/header
폭을 측정하고 각각의 밴드에 폭을 배분한다. WM_SIZE에서는
SetBandInfo/부모 RecalcLayout을 직접 호출하지 않는다.
실제 3aab666 x64 Windows 빌드 후 800×600→1920×1032에서 드라이브와
북마크가 정상적인 하나의 둘째 행에 직접 표시되며 프로그램 응답 상태가
정상인 것을 screenshot·WinApp UI 트리로 확인했다.
정적 전체 preflight PASS, 신규 UI-05 mutation 검사는 **11 PASS**,
local_ci.bat x64 빌드와 native 기능 검사는 **17 PASS / 0 FAIL**다.
단 **runtime smoke는 기존 HKCU 사용자 상태 보호 때문에 SKIPPED**;
실기 UI 실행은 별도 격리 프로필로 확인했다. 125/150/200% DPI,
Light/High Contrast, 기존의 복잡한 사용자 저장 밴드와 도구 모음 드래그
상호작용은 **RETEST OPEN**이다. 이 범위 밖의 UI-01/03~14 및 다른
설치 환경의 문제를 완료로 승격하지 않는다.

동일 후보 바이너리의 **96 DPI Dark 합성 fixture**에서 UI-02 파일 목록
세로/트리 가로 스크롤바를 각각 12프레임 실제 드래그했다. 손잡이
위치는 이동했고 해당 캡처의 밝은 중성 픽셀 비율은 전 프레임 **0.0**;
원격 테스트 시스템에서 밝아짐은 재현되지 않았다. 다른 배율/Windows
시각 스타일과 사용자가 과거 제공한 실패 화면은 아직 설명되지 않아
**UI-02 전체 OPEN / 해당 한정 재현 NOT OBSERVED**로 유지한다.
캡처·manifest는 개인 설정을 포함하지 않고 검사 PC의 무추적
logs/visual-ui/에 보관했으며, 기존 사용자의 main-window.png와
HKCU 설정은 건드리지 않았다. GitHub Actions는 실행하지 않았다.

**2026-09-27 사용자 x64 빌드 보고 — COMPILE/FUNCTIONAL PASS, SMOKE SCRIPT RETEST OPEN:**
사용자가 `ff0352957686a8895e885bc3103eed3a65d6702b`에서 `local_ci.bat x64`
실행 결과를 공유했다. VS 2026/v145 솔루션 생성·소스 정적 검사 및
필수 x64 산출물 확인은 PASS이며 native functional regression은
**17 passed / 0 failed**다. 그러나 이어진 runtime smoke는 제품 창 생성
검사 전에 Windows PowerShell 5.1/.NET Framework에서 지원되지 않는
`ProcessStartInfo.ArgumentList` 속성 접근으로 즉시 종료되어
전체 local CI 결과는 **FAIL (CI 실행 스크립트 호환성)**이었다.

`build/runtime_smoke.ps1`을 WinPS5.1에서 사용 가능한 인자 API와
프로세스 트리 종료 방식으로 변경하고 호환성 source guard 및 회귀
검사를 추가했다. 최종 수정본에 대한 사용자 Windows 재실행과
최신 revision 일치 x64 재빌드, 실제 창 표시/안정성은 여전히
**NOT RETESTED**다. 앞선 `ff035295`의 compile/functional PASS를
새 commit의 실행 검증으로 자동 승격하지 않는다. UI-02 등
시각적 결함은 그대로 OPEN/RETEST OPEN이며 GitHub Actions는
실행하지 않는다. 진단과 변경 범위는
[오류 이력](ERROR_HISTORY.md)의 2026-09-27 PowerShell smoke 항목 참조.

**2026-09-27 Native UI evidence preparation — TOOLING ADDED / PRODUCT VISUAL NOT TESTED:**
채팅에서 실제 Windows UI를 검증하는 반복 작업을 준비하기 위해 별도
`build/visual_ui_probe.py` 및 순수 `build/test_visual_ui_probe.py` 테스트와
[실행 및 검증 절차](UI_VISUAL_RETEST.md)를 추가했다. 사용자의 개인 설정과
데이터를 수정하지 않도록 격리된 합성 fixture를 요구하고,
`build-revision.txt`와 Git HEAD가 일치하지 않으면 스크린샷 수집을
거부한다. 스크롤바 대상은 공개 `GetScrollBarInfo`로 좌표를 얻어
실제 마우스 드래그 중 12개 프레임과 thumb 위치를 기록한다. 밝은
네이티브 스크롤바 의심 프레임은 탐지 후보로 표시하되,
픽셀 차이만으로 UI 결함의 해결이나 실패를 단정하지 않는다.
정적 source preflight에 해당 안전 계약도 연결했다.

**해당 UI 수집기 체크포인트는 제품 C++ 렌더링을 변경하지 않았다.** 당시 채팅에는
연결된 Windows 테스트 기기가 없으므로 신규 소스의 Windows x64
컴파일·최신 바이너리 실행·실제 화면 관찰은 **NOT TESTED**다.
기존 UI-02는 여전히 **OPEN**, UI-09 및 UI-01/03~14의 해당 항목은
각기 종전 근거 수준의 **RUNTIME/VISUAL RETEST OPEN**으로 유지한다.
자동 GitHub Actions를 실행하거나 제한된 x86/배포 범위를 확장하지
않았다. 전체 UI 해결 완료로 보고하지 않는다.

**2026-09-26 UI-02·05 후속 코드 — 비동기 방식으로 재설계 / WINDOWS RUNTIME NOT TESTED:**
사용자는 HANG-01 문제가 해결됐다고 보고하며 이전 UI 점검 목록의
처리를 요청했다. 현재 소스의 HANG-01 OLE paint starvation
수정은 그대로 보존했다. 과거 UI-02/05 자동 처리의
동기적 비클라이언트 그리기 및 OnSize 중 부모
RecalcLayout 경로를 재도입하지 않았다.

- UI-02: 공개 `GetScrollBarInfo`로 실제 네이티브
  스크롤바의 위치·thumb·화살표 상태를 읽어
  Dark에서만 그리는 코드가 있다. 리스트/트리
  `WM_NCPAINT`·스크롤 이벤트에서는 그리지 않고,
  기존 Windows 메시지를 처리한 후 등록된 별도
  `PostMessage` 하나로 작업을 합쳐 실행한다.
  그리는 중 재진입 요청을 거부하고 Light 및
  High Contrast에서는 OS 출력을 유지한다.
  사용자 스크롤 위치·hit-test·드래그를 바꾸지 않는다.
- UI-05: 초기에 세 도구 모음을 독립 행으로
  생성하고 native 크기 계산이 끝난 후,
  저장된 배치가 없는 첫 실행·단일행·가시 상태에서
  두 이상 폭과 48-DIP 여유가 실제로 맞는 경우만
  드라이브/북마크 행 결합을 한 차례 시도한다.
  `OnSize`에서는 메시지 예약만 하며 실제
  `SetBandInfo`·`RecalcLayout` 호출은 별도
  예약 메시지로 분리했다. 기존 배치 파일·
  다중 행·사용자 조작과 UI-09 변경은 보존한다.
- UI-11/12/13: 앞선 새 기본 열 너비,
  트리 전체명 툴팁, 가변 정보창 배치 수정은
  현재 `main`에서 확인됐고 중복 수정하지 않았다.
  저장된 기존 140px 열 너비는 임의 변경하지 않는다.
- UI-14: 혼합 방식의 헤더 그리기/좁은 정렬 표시
  기존 개선을 유지한다. 당시 화면만으로
  포커스 표시 문제는 확정되지 않았다.

정적 계약은 동기 그리기·OnSize 내부 재배치
재도입을 금지하고 기존 UI-09 및 UI-11~14
회귀 검사를 유지한다. **새로 결합한 소스의
Windows Release x64 컴파일/링크, 실제 Dark
스크롤바 마지막 픽셀, 기존/새 프로필 UI-05
배치, 100/125/150/200% DPI·High Contrast,
같은 사용자 화면의 전체 UI 수용 검증은
이 작업 환경에서 NOT TESTED**다.
사용자 설정을 초기화하거나 GitHub Actions를
실행하지 않았다.

**2026-09-26 추가 사용자 화면 재현 — UI-02 OPEN, 이름/필터 선택 소스 수정, 전체 Windows 재검증 대기:**
사용자 캡처는 Dark 스크롤바 손잡이를 드래그하면 여전히 밝은
네이티브 색상이 나타나며, 목록 이름 열(기존 기본값 150px)이
우측 빈 공간과 비교해 좁고, 필터링 설정 선택 항목이 Light/Dark에서
과도하게 선명한 파란색이라고 보여 준다. 리비전과 DPI는 화면에서
확인되지 않는다.

UI-02의 현재 코드는 표준 Windows 비클라이언트 스크롤바를
뒤늦게 덮어 그리는 방식이므로 네이티브 손잡이 추적 중
최종 픽셀 소유권을 보장할 수 없다. **UI-02는 미해결**이다.
다시 무조건 덮어 그리거나 반복 타이머·비공개 OS API를
추가하지 않았다. 동일 바이너리의 드래그 중 WM_NCPAINT /
WM_VSCROLL / WM_HSCROLL / 등록 지연 메시지 발생 순서를
Windows에서 수집한 뒤 스크롤바 렌더링 소유 구조를
재설계해야 한다.

기본 새 폴더 레이아웃의 이름 너비를 150→280 논리 픽셀로
넓히고 HWND DPI를 적용했다. 이미 저장된 열 너비와 열 순서,
자동 열 너비 사용자 설정은 변경하지 않았다. 기존 사용자
프로필의 좁은 열은 열 경계를 드래그하거나 파일 목록의
기존 자동 열 너비 옵션을 사용해야 한다.

필터 설정의 선택 표시에서는 일반 Light/Dark에서
선택된 행의 최종 픽셀만 직접 그린다. 현재 팔레트 선택색
12%(활성)·6%(비활성)와 기존 배경을 혼합하여 은은하게
표시한다. 원래 아이콘·이름·확장자·설정된 글자 색의 대비,
얇은 키보드 포커스를 보존하고 네이티브 선택 상태나
사용자 필터 정의는 건드리지 않는다. High Contrast는
기존 Windows 선택 렌더러를 그대로 사용한다.

새 정적 회귀 검사를 추가했으며 OLE 응답 중단 수정 및
UI-09 북마크 damage 수정은 변경하지 않았다.
**이번 변경본의 Windows Release x64 컴파일, 실제
다중 선택·드래그·고대비·DPI·기존 프로필 화면 확인은
NOT TESTED**다. GitHub Actions 미실행.

## Active baseline and verified scope

**2026-09-26 HANG-01 실행 진단 후 수정 후보 — BUILD / RUNTIME NOT TESTED:**
사용자가 빌드한 `882030a` 실행 파일로 동일한 시작 화면의 빈 트리/목록과
응답 중단을 재현했다. UI-02/05 격리 이후에도 재현되므로 이전 격리를
해결로 취급하지 않는다. 로컬 덤프와 반복 UI 스레드 스택에서
`WinApp::InitInstance → UpdateWindow → ListCtrlEx::WindowProc → native
image list → SHDefExtractIconW → thumbcache/CoCreateInstance → COM wait →
COleMessageFilter::OnMessagePending`을 확인했다. 메시지 필터의 프레임에서
`WM_PAINT` 대상이 동일 UI 스레드의 `SysListView32`임을 확인했다.
MFC 기본 구현은 `PeekMessage(WM_PAINT)`가 빌 때까지 무제한 순회한다.
이 반복이 COM 대기로 복귀하지 못하는 starvation 경로를 수정하기 위해
앱 소유 OLE 필터가 콜백당 paint 하나만 처리하고 중첩 paint dispatch를
막도록 했다. native update region을 강제로 지우거나 아이콘을 생략하지 않는다.
OLE 필터의 나머지 busy/retry 정책과 CWinThread/AfxOleTerm 소유권은 유지한다.
Shell 서버 자체의 별도 지연/장애 유무와 수정 후 응답성은 아직 미검증이다.

사용자 요청에 따라 **이번 변경의 빌드·새 바이너리 실행은 하지 않는다**.
source preflight PASS, 무제한 순회/base-pump 호출/설치 누락/재진입 보호 누락의
4개 mutation 검출 PASS. 이 정적 evidence는 빌드/실행 검증과 별개다. 사용자가 빌드한 후
동일 폴더/설정에서 목록·트리·아이콘 로딩, 1분 이상 응답성, 폴더 이동,
종료, UI-09 북마크 잔상, Light/Dark 및 OLE 드래그 앤 드롭을 재검증해야 한다.
UI-02/05 격리 및 기존 UI-09 damage fix는 유지한다. 사용자 설정은 변경하지
않았으며 GitHub Actions는 실행하지 않는다. 상세 근거는 ERROR_HISTORY 참조.

**최신 UI-09 실행 근거 및 병합 상태 (2026-09-26):**
백업 브랜치의 실제 Windows 진단은 설정에서 테마를
변경할 때 MFC 명령 UI 갱신으로 버튼 높이가
36px에서 22px로 축소되면서 변경 후의 사각형만
무효화되어 기존 아이콘/텍스트 하단이 남는 것을
계측했다. 명령 갱신 이전/이후의 버튼 좌표를
비교하여 이전·새 영역 모두 무효화하는 수정으로
**진단 빌드에서는 동일 화면의 잔상이 사라졌다.**
백업 브랜치에 기록된 진단 빌드의 Windows
Release-x64 컴파일/링크 PASS 및 native regression
17 passed / 0 failed는 그 당시 증거다.
최종 백업 소스에서는 임시
`FXFILE_UI09_TRACE=1` 기록 코드가 제거됐다.
현재 UI-02/05의 미검증 후처리·자동 행 결합은 격리되어 있고,
UI-09 damage fix와 UI-11/12/13/14는 유지한다. HANG-01 필터 변경을
포함한 새 소스의 전체 Windows 빌드·응답성·테마 전환 회귀는 NOT TESTED다.
아래 임시 추적기 추가 관련 내용은 당시 작업 기록이며
현행 소스 사용 지침이 아니다.
근거: [실제 UI-09 원인 진단](UI09_ROOT_CAUSE_20260926.md).

| Subject | Current observed state | Evidence limit |
| --- | --- | --- |
| Product | fxfile/flyExplorer 2.0.4-dev; Windows 10/11 active development; native Release-x64-Unicode is the default build path | Not a formal minimum-OS or general release compatibility guarantee |
| Build system | Visual Studio 2026/v145, GYP-generated solution; fresh `local_ci.bat x64` on product revision `bee95d9`: source preflight, Release x64 compile/link PASS; native functional regression 16 passed / 0 failed | PASS WITH SKIPS: automated runtime smoke skipped to preserve existing HKCU state; clean-profile startup NOT TESTED |
| Historical user-supplied x64 log (2026-09-24, `bc02a4a`) | Former native updater test compiled with a Windows `max` macro collision and that run FAILED. That entire updater feature/test is now removed by explicit owner choice. | Superseded for current compile evidence by the post-removal `bee95d9` x64 PASS. Preserve the old failure as historical evidence. |
| Earlier local x64 test | On the parent of product commit `6b18c58f` plus then-uncommitted OS-rendering fix: Release x64 compile/link PASS and native functional tests 17 passed / 0 failed | Overall PASS WITH SKIPS; startup smoke skipped for user HKCU preservation; not a revision-matched test of current `main` |
| Dark/Light/High Contrast UI | Actual Windows 11 inspection of `bee95d9`: original main-menu/toolbar/drive/bookmark Dark text now readable. UI-01 source now snapshots HWND visibility and only freezes/thaws windows that were visible before a theme transaction, preventing redraw-enable from exposing hidden settings pages. | UI-01 exact settings-page sequence on this source revision: NOT RETESTED. Bright Dark scrollbars, mixed search-dialog colors and the remaining UI/UX audit findings stay OPEN. Windows 10, High Contrast and mixed-DPI remain NOT TESTED. |
| Help / portable completeness | Canonical `docs/htmlhelp/` source remains the build input. Full packaging now validates 39 required runtime payloads across the three existing architectures before staged replacement, reserves the previous staged bin for rollback during activation, generates the installer before portable extras and clears partial/stale release outputs on failure; archives still carry fresh CHM and notices. | Static code/path inspection only; Windows directory-rename/rollback injection, HTML Help Workshop, NSIS/ZIP execution and installed/portable Help: NOT TESTED. |
| User guidance | `Html/current_development.htm` is the current source-grounded guide; old detailed reference pages are retained with prominent legacy entry-point labels | Full per-topic source/runtime rewrite still OPEN; track it in [`HELP_CONTENT_AUDIT.md`](HELP_CONTENT_AUDIT.md) |
| Distribution | Personal/local use only is the current owner's intent. Root GPL and third-party CREDITS notices remain unchanged and bundled; installer/portable paths now reject partially copied or missing release files. | No public redistribution permission is claimed. Third-party permissions (especially GFL) remain UNVERIFIED; Windows package generation on this revision NOT TESTED. |
| GitHub Actions | Manual workflow-only; each actual run requires a separate explicit user instruction with no expiry to this restriction | No Actions invoked in documentation/vendor/help cleanup |
| Automatic updates | **REMOVED FROM SOURCE AND NEW PACKAGE DEFINITIONS:** retired checker project/network dependency, application startup integration, update settings/About download, native updater regression and packaging payload. | Post-removal x64 compile/regression PASS at `bee95d9`; old-install migration and full packaging NOT TESTED. Existing startup values were preserved. |
| Prior repository cleanup | Removed unused `gtest` (41) and `libxslt` (52) files, 16 byte-identical zlib binaries, 113 non-build NSIS developer assets, 4 dead root HTML frameset inputs, plus the retired updater module, dedicated libcurl vendor tree and obsolete generated project files | Post-cleanup x64 compile/regression PASS at `bee95d9`; packaging and external manual consumer checks NOT TESTED |

**Do not call all runtime defects closed based on a build or a narrow visual
check.** Original main Dark text acceptance was visually rechecked on Windows
11; the separate settings/search/scrollbar findings remain OPEN. The dated
audit records the exact product revision, executable hash and untested cases.

**2026-09-24 follow-up source-only checkpoint:** UI-03 nested search
ComboBox Dark color forwarding, dropdown list retheming and a wider localized
current-folder button are now in source. UI-07 new-profile defaults expose the
existing single-tab strip and new-tab button without changing saved settings.
These are partial changes; Windows build, runtime/visual, DPI/HC, search
behavior and a newly added close-tab glyph still require revision-matched
Windows runtime/visual acceptance.
UI-02/UI-05/UI-06 remained unchanged in that checkpoint;
UI-08 receives a separate new-profile-only partial change below. Prior `bee95d9`
build evidence does not apply to this new revision.

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
