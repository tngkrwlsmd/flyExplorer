# WinUI 3 M1.5 — shared directory changes and asynchronous COM STA

Local-only migration worktree: `C:\dev\flyExplorer-winui3-migration`, branch `migration/winui3-full-shell-20260929`. M0/M1 staged work is preserved; this is not a production default swap.

## Shared change-detection extraction

`src/base/directory_change_bridge.h/.cpp` implements MFC-free Win32 wrappers for directory watching: `FindFirstChangeNotificationW/A`, rearm, and close. Unicode and ANSI overloads retain the legacy x86 multibyte source contract. The original `FileChangeWatcher` now invokes these primitives while retaining its existing options, xpr thread, debounce, and HWND notification flow. Legacy `AdvFileChangeWatcher` and `ShellChangeNotify` are unchanged.

The independent WinUI Shell worker uses the SAME shared bridge for up to two selected visible filesystem panes, one watch per pane. Each watch carries a unique tab route and token. On real native invalidation the worker rearms the handle and sends route/token-only notification. WinUI queues background Shell refresh and discards old-tab or old-folder invalidations. No user configuration or system-wide watcher is installed.

## Private native COM STA worker

`src/base/shell_async_worker.h/.cpp` owns a dedicated native thread with `COINIT_APARTMENTTHREADED`, a message pump and serialized native Shell requests. Shell COM interfaces are created, used and released ONLY in the private worker apartment. The worker accepts a cloned absolute Shell PIDL or parsing name and returns a complete value-only `shellnav::Snapshot`.

WinUI uses `DispatcherQueue::TryEnqueue` with a weak UI reference. Every pane/tab has a distinct persistent route, each navigation a request token; obsolete and canceled route results are rejected by BOTH worker and UI before display. `Session::accept` commits prepared snapshots and history without any UI-thread `EnumObjects` call. File operations remain disabled, except the existing safe invalid-null native contract check.
## Lifetime and safety limits

- `shutdown()` cancels pending work and clears callbacks without synchronously joining potentially stuck third-party Shell COM calls. A detached worker retains a private shared state and native resources until COM eventually returns or the process exits; it has no raw UI pointer.
- An in-flight blocking `EnumObjects` or `Next` call CANNOT be interrupted by the atomic flag; cancellation is cooperative between blocking COM calls. One stuck extension can delay requests for other tabs on this one worker. A watchdog, bounded slow-folder handling, or an isolated worker process remains necessary before shipping.
- Native filesystem directory changes are observed for selected tabs only. Windows virtual Shell namespace change notifications are NOT implemented; manual navigation to virtual This PC is supported. A permission failure while re-opening a filesystem watch is not auto-retried until a new snapshot.
- Current snapshots stop after 1200 entries. Existing selection/scroll position is not preserved across full-list refresh; remote/large folders, OS High Contrast, actual alternate DPI, IME, spoken accessibility, installer and configuration/workspace compatibility still require separate acceptance.

## Scope-specific tests and logs

This phase must separately verify original MFC Release x64 compilation and regression, actual MFC GUI navigation, and NEW WinUI Release x64 compilation plus real GUI. Native async tests must demonstrate callback execution on another thread, superseding same-route requests, and real test-owned directory-change signal. The GUI must show automatic create/delete refresh without manual input, rapid invalid-to-valid navigation consistency, correct virtual Shell/back history, normal process exit, and unchanged SHA256 for six original user configuration files.

The original user's running product is never killed, global registry/theme/DPI are never changed and synthetic files are confined to owned fixtures. Hosted GitHub Actions, remote push, merge and installer release need separate approval.

## Final revision-scoped verification (2026-09-29)

**Original MFC product:** Final migration-worktree `local_ci.bat x64` exit 0 with Release-x64-Unicode compilation/link, source and compiler-warning gates passing. The expanded native functional suite finished **20 passed / 0 failed** (previous 18 plus worker/watch request test and test-owned blocked-callback shutdown test). The native worker callback was observed on a different thread; same-route supersession and actual synthetic directory change events passed. The deliberate shutdown test blocks ONLY its private callback and demonstrates that the caller does not synchronously wait for that callback; it is NOT proof of interrupting blocked third-party Shell COM. The standard runtime smoke was **SKIPPED** because real user HKCU existed; exact CI verdict **PASS WITH SKIPS**. Final MFC x64 EXE SHA256: `B35F7ADC0768436851F8F485A70C0D042B5C70FBE9EDFF2E333C8CAE221CC835`.

An independent test-owned real MFC process on that binary successfully executed native ExplorerCtrl Go Up / Back / Forward on synthetic folders and exited normally. Its isolated APPDATA/TEMP/config were cleaned up. All SIX original real-user config SHA256 values remained unchanged.

**New WinUI 3:** Final C++/WinRT Release x64 build PASS. Exact final EXE SHA256: `5944CB8DBAA4BB730F5E0D43DB3C7FA463B4701556644329192B95BBFA41D694`. On this binary an actual test-owned Windows 11 96-DPI GUI run proved async native folder enumeration and original native core linkage; test-owned file CREATE and DELETE both auto-refreshed the native WinUI ListView without manual refresh; real owned full-PIDL row doubleclick and Back worked; 1→2→1 tab add/close, rapid close without resurrecting a stale tab, split toggle, physical address Enter, invalid→valid rapid request supersession, independent left/right sessions and genuine virtual Shell This PC plus Back all passed. The owned WinUI process exited 0, private fixtures were removed and the same original SIX user-config SHA256 values were unchanged. Static architecture/source tests: **5/5 PASS**.

**Important initial Release GUI failure and correction:** The first Release pointer test failed after successful watcher create/delete. Its failure-time screenshot showed a separate, already-existing Windows Explorer window over the test-owned WinUI list, so the uncontrolled pointer did not reach the intended item. This was a **test input ownership fault**, not evidence of a native Shell engine failure. The harness now focuses its own window and validates foreground PID BEFORE all 16 pointer-button inputs and five physical Enter inputs; it refuses physical input if another user's window retains focus. The SAME compiled Release executable passed the subsequent guarded full GUI test. Do not dismiss subsequent genuine product failures as automation faults without comparable evidence.

Local ignored logs: `logs/m15-final-shared-watch-legacy-x64-local-ci.log`, `logs/m15-final-legacy-old-explorer-owned-gui.log`, `logs/m15-final-winui-sta-release-x64-build.log`, `logs/m15-release-guarded-owned-input-gui.log`, `logs/m15-final-native-20-direct-run.log`, and `logs/m15-static-contract-five-final.log`. Diagnostic evidence: `logs/phase6-winui/m15-failed-row-input-diagnostic.png`; successful owned GUI capture: `logs/phase6-winui/migration-first-shell-real-gui.png`. Generated source/binary/evidence hashes are recorded separately under ignored migration logs.
