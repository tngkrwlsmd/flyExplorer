# WinUI 3 full UI migration — M1.8 isolated Shell stability

**M2.3 ?? ???/?? ??:** ?? ??? ??? 19?? ???? ?? ??? ??? ?? 7?? ??, ??? ?? ??? ?? ?? ??? ??? ??. ?? ?? Debug?Release ?? PASS; ??? ?? ?? ?? ???? ??/?? ???? ???? ?? ?? FAIL/???. [??? ??](../../docs/development/WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md).


**M2.3 단계별 통합 (2026-09-29):** M2.3에서 한국어 기본 WinUI의 Windows CF_HDROP/Preferred DropEffect 읽기·쓰기 사용자 명령과 제한된 개인 세션 저장·시작 시 복원·삭제를 연결했다. 전역 클립보드는 별도 테스트에서 건드리지 않는다. Native fixture는 m23/build.cmd Debug|Release 및 FLY_M23_CONFIG=... m23/test_native.py를 사용한다. FLY_M23_OWNED_FEATURES=YES는 합성 폴더·별도 사설 프로필의 실제 WinUI 세션 UIA를 검사하고, FLY_M23_OWNED_DRAG_TEST=YES 물리 드래그 진단은 현재 **실패/미검증**으로 별도 유지한다. [M2.3 범위](../../docs/development/WINUI3_M23_CLIPBOARD_SESSION_DRAG_STAGING_20260929.md).


**M2.2 acceptance:** 기본 언어 ko-KR의 분리된 파일 도구 모음/상태 화면, 초기 .resw, 네이티브 Shell 복사·이동·명시적 휴지통 확인 및 비동기 로컬 메타데이터/다중 선택/정렬 구현. 소유 환경의 Debug·Release M1.9~M2.2 통합 실기 GUI와 Debug 통제 장애 재현 PASS, 독립 네이티브 각 18/18 및 소스 79/79 PASS. 실제 휴지통 삭제·외부 확장/네트워크·완전한 MFC 동등성 검증은 남아 있음. [M2.2 독립 증거](../../docs/development/WINUI3_M22_SHELL_OPERATIONS_KOREAN_20260929.md).


**M2.1 KOREAN DEFAULT REUSABLE WINUI PREVIEW:** The independent full-window preview now actually compiles reusable ShellHeader/NavigationSidebar XAML controls, Korean text and a real runtime theme label, and uses MFC-/WinRT-independent native preview_preferences/file_command_core. The new controls report intents to the existing M2.0 model/window; default ko-KR/System preference is stored ONLY in the private WinUI3Preview local-appdata directory. Guarded actual native operations are create-folder and rename-selected, never delete or overwrite. Run a matching Debug/Release build with build.cmd, then separate M2.1 owned native contracts (m21/build.cmd and m21/test_native.py with FLY_M21_CONFIG) and GUI test_shell_gui.py with FLY_M21_OWNED_FEATURES=YES and matching FLY_MIGRATION_CONFIGURATION. Additional M1.9 and M2.0 owned checks are independent optional flags. [M2.1 exact acceptance and remaining scope](../../docs/development/WINUI3_M21_KOREAN_NATIVE_UI_COMPONENTS_20260929.md).

**ACTIVE M2.0 WINUI-ONLY FULL-WINDOW SHELL:**
The existing independent WinUI 3 XAML window consumes `src/base/explorer_ui_state` for actual two-pane native tab/route/request commands, and now has System/Light/Dark controls plus This PC through private supervised Shell navigation. Build with `build.cmd Debug` or `Release`; actual owned `test_shell_gui.py` with `FLY_M20_OWNED_SHELL=YES` validates rendered light/dark pixels and native commands; adding `FLY_M19_OWNED_FEATURES=YES` also retests the existing private workspace/search GUI. These modes are for test-owned processes only. [M2.0 detailed scope](../../docs/development/WINUI3_M20_FULL_WINDOW_NATIVE_COMMAND_MODEL_20260929.md).


**LATEST M1.9 SOURCE AND GUI REPRODUCIBILITY:** Combined default `main` native source and independent WinUI preview passed real Debug+Release UXH-07 supported subset named-workspace/new process restoration, UXH-06 default-off bounded read-only filename search/opt-in private recent locations, actual merged MFC 20 native tests PASS_WITH_SKIPS and native UXH-07/UXH-06/UI-02 Dark/Light owned GUI. Independently build the same preview-only Win32 cores using `experiments/phase6_winui_shell/m19/build.cmd Debug` or `Release`, then run `m19/test_native.py` with `FLY_M19_CONFIG` for the matching build; both passed 12/12 using synthetic owned data. Source architecture and native feature checks combined 56/56 PASS. To test genuinely MFC-produced workspaces, run the original test-owned MFC UXH-07 generator first and point `M19_NATIVE_WORKSPACE_OWNER` ONLY at its exact generated `logs/uxh07-named-owned-*` directory before running `test_m19_real_mfc_interop.py`. The second generated virtual Documents tab is substituted only in a temporary copy with a synthetic local folder to prevent unowned user-document enumeration. No test flag, test-only profile or generated fixture is part of normal WinUI startup. [Current exact scoped evidence and missing full product parity](../../docs/development/WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md).


**M1.9 CURRENT ACTUAL SOURCE IMPORT:** Independent experimental WinUI 3 preview now includes latest native main MFC source, bounded native XAML UXH-07 UTF-16 named-workspace Save new/Open separate process (tested bidirectional MFC?WinUI 2-pane subset), and user-explicit privacy-default-off WinUI-only bounded read-only filename search+8 recent filesystem scopes (not full MFC regex/content/filter). Actual owned Debug/Release feature GUI, MFC imported native 20/0 PASS_WITH_SKIPS, exact standalone bridge Debug/Release 12/12 and 20/20 source checks PASS. Original M1.8 dual isolated Shell helpers maintained. Not a default product replacement or full UI/accessibility parity. [M1.9 integration report](../../docs/development/WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md). Old pre-M1.9 no-main-source passages below are historical.

---



**CURRENT branch context:** This is a non-default M1.8 WinUI experimental preview at `eb7ee1a`, not a substitute for the now-merged native product `main` `f074a6b` (UXH-07 named workspaces, UXH-06 opt-in recent search locations, current ModernUI UI-02). These codebases are **not source-reconciled**, so neither shared feature parity nor a new combined build is claimed. Branch details and next integration gates: [migration/mainline alignment](../../docs/development/MIGRATION_MAINLINE_ALIGNMENT_20260929.md). Historical M1.8 test evidence below remains exact for this older migration revision.

The preview retains its native two-lane private helper Jobs and independent filesystem watcher. M1.8 adds distinct exhausted-timeout and invalid UNC error messages without discarding the active folder, plus an independent hidden-window Shell notification subscription for selected virtual PIDLs. Actual owned GUI tests passed a test-only blocked COM method, both exhausted retries, an invalid localhost UNC, and a Shell event confined to a synthetic owned folder. Actual external third-party provider and virtual-folder changes remain unverified. See [M1.8 scoped verification](../../docs/development/WINUI3_M18_SHELL_STABILITY_20260929.md).

## Historical M1.7 integration

# WinUI 3 full UI migration — M1.7 actual isolated-process Shell preview

**Latest, revision-scoped:** The real WinUI navigation path now uses a native **two-lane C++ supervisor**, one test-preview-owned read-only Shell child per active-pane request (at most two simultaneous children), with bounded timeout/private Windows Job termination and one restart. A standalone **COM-free Win32 watcher thread** handles selected filesystem-pane changes independently of hung Shell helpers; paths are computed in the child, never by UI-thread SHGetPathFromIDListEx. The Debug GUI successfully tested a blocked owned LEFT child while RIGHT continued and LEFT recovered; ordinary Release GUI and native create/delete watching passed, unchanged six user hashes, static 12/12. This preview is still not the default MFC product and is not a restricted-token security sandbox. [M1.7 verification and known limits](../../docs/development/WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md).

## Historical M1.5 design and tests (the old in-process worker is no longer linked to this preview)

This is an independent **local, non-default** C++/WinRT executable in the separate migration worktree. The existing MFC product remains the safe fallback, and advanced file mutations are not enabled here.

## Native components already connected

- `src/base/shell_navigation_core.h/.cpp`: real Windows Shell absolute PIDL snapshots, virtual parsing names and transactional per-tab navigation history. The old MFC ExplorerCtrl retains its higher-level GUI/controller.
- `src/base/shell_enum_bridge.cpp`: shared low-level native Shell enumeration entry used by the old MFC ShellEnumerator and this independent WinUI preview.
- `src/base/directory_change_bridge.h/.cpp`: new MFC-free Unicode/ANSI Win32 directory watch primitives, reused by the old MFC FileChangeWatcher and this preview.
- `src/base/shell_async_worker.h/.cpp`: private COM STA, message pump, serialized Shell requests, request/route cancellation, native filesystem invalidation and nonblocking UI teardown.

Real WinUI 3 TabView/ListView panes now queue their Shell work away from the XAML UI thread. Owned native snapshots are delivered via the WinUI DispatcherQueue through weak window references. Each tab retains independent history; changing a synthetic file in the selected filesystem folder triggers asynchronous refresh. Actual Windows Shell virtual folders can be navigated but their change notifications are not yet implemented.

The old, UI-independent `fxfile::fileop::execute` is linked only for its safe invalid-null contract. Copy/move/delete are deliberately not exposed.

## Local build and tests

Run `build.cmd Debug` or `build.cmd Release` in this directory. Generated projects and x64 artifacts remain ignored and confined to the separate migration worktree. No local installer or system/user setting is changed.

Run `python -m unittest test_arch_contract.py` for focused shared-core and no-MFC source checks; run `python test_shell_gui.py` for actual test-owned UIA and physical input GUI acceptance. Set `FLY_MIGRATION_CONFIGURATION=Release` in the current process to test the Release EXE. The GUI harness checks the foreground process owns the WinUI window before each actual pointer/keyboard action; if it cannot safely acquire focus, it must abort rather than click a user's existing window.

`python test_legacy_enum_gui.py` independently starts the compiled original MFC program with private config and synthetic folders and proves its real Go Up / Back / Forward route. The local `local_ci.bat x64` in the migration worktree checks native Release x64 plus the expanded regression suite. It may SKIP the normal runtime smoke to preserve existing user HKCU; do not claim smoke PASS when that happens.

## Incomplete and unsafe for production

A hostile third-party Shell extension can still block the **single worker STA** in one `EnumObjects` or `Next`. Newer route cancellation discards obsolete results but cannot interrupt an already-running COM call; detached shutdown only prevents UI window closure from synchronously waiting, not worker resource leakage until the blocked call finishes or the process exits. Dedicated process isolation or timeout recovery is still needed for a production guarantee.

Only selected filesystem folders get native auto-change watches (up to two). The old advanced watcher and CWnd ShellChangeNotify, virtual Shell change events, sorting/metadata/thumbnails, native file operations, named workspace settings parity, IME, actual alternate DPI/high contrast, screen reader and clean-machine installer require later integration and tests.

Exact M1.5 source/build/GUI acceptance, known limitations, log paths and first Release pointer-test diagnosis: `docs/development/WINUI3_ASYNC_SHELL_CHANGE_WORKER_20260929.md`. Do not ship this preview as the default file manager or run hosted CI without an explicit per-run approval.

## M1.6 bounded process-helper experiment (not yet wired to this GUI)

The risk audit identified one serialized in-process Shell STA serving **both** panes plus filesystem watches; a genuinely stuck Shell COM call defeats cooperative cancellation. A **separate read-only native process helper** and test-owned Windows Job-object watchdog are now implemented under `isolation/`. That helper's Debug/Release x64 builds and direct two-process Windows tests passed local and virtual Shell enumeration, strict IPC/PIDL decoding, independent helper progress when the other is artificially blocked, targeted termination/restart and automatic private-job close reclamation.

This **does not** change the runtime `MainWindow`: it still uses `AsyncShellWorker`. Do not report process isolation or true third-party Shell extension recovery in the GUI until a new native per-pane supervisor and owned WinUI GUI regression are implemented and verified. Run `python -m unittest isolation/test_contract.py` for isolated source checks and see `isolation/README.md` and `docs/development/WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md` for exact test commands, risks and boundaries.
