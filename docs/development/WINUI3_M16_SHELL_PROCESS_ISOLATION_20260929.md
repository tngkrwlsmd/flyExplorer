# M1.6 — Shell process isolation: verified risks and implementation boundary

**SUPERSEDED BY ACTUAL M1.7 WINUI GUI INTEGRATION:** This file documents the earlier helper-only state at commit `a829fd1`. A subsequent local revision *does* connect a native two-lane C++ supervisor and standalone Win32 change watcher to the actual WinUI preview. Use [M1.7 real Debug/Release and owned GUI evidence](WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md) for current status, while retaining this M1.6 record as historical investigation/test evidence.

Date: 2026-09-29. Source revision at investigation: `65a618837eddfd88a850477ba8023baa8d6a847a`, `migration/winui3-full-shell-20260929`. This document records *source-observed* findings, the chosen architecture and separate experiment acceptance. Do not treat a process experiment as production WinUI integration.

## Current implementation: source-observed risks

1. `AsyncShellWorker` has **one** background COM STA, serial queue and up to two native directory watch handles on that same STA. `SHParseDisplayName`, `SHBindToObject`, `IShellFolder::EnumObjects`, `IEnumIDList::Next`, `IShellFolder::GetAttributesOf`, and Shell display-name retrieval can execute third-party handlers. A single indefinitely blocking COM call therefore delays **both** panes and change notifications. Cooperative atomic cancellation only runs between those calls.
2. `shutdown()` cancels queued requests, clears callbacks and detaches the worker without a join. It avoids a synchronous UI shutdown wait; it **cannot** reclaim an in-flight hung thread, COM apartment or loaded in-process extension. An extension crash in the same process could also terminate the preview application.
3. Per-route generations and weak WinUI dispatcher references already reject stale UI results correctly after ordinary cancellation and tab closure. Preserve them when the execution boundary changes. Do not move native COM interfaces or raw in-process pointers across a process boundary.
4. The WinUI `UpdateWatch` method still calls `SHGetPathFromIDListEx` directly on the UI thread. Even though the main enumeration is off-thread, this conversion still needs removal or a safe worker-derived filesystem path before promising that *all* potentially blocking Shell operations are off the UI thread.
5. The 20 passing native tests include a deliberately blocked **callback**, not an unresponsive Shell extension. Existing owned GUI proves local/virtual navigation and automatic filesystem create/delete, **not** COM timeout recovery or crash containment. Shell virtual-folder change notifications remain unimplemented.

## Isolation decision

The eventual product boundary is ALL untrusted namespace parsing and enumeration (local, UNC/network, unknown and virtual Shell folders), including item metadata and Shell name/attribute calls. Arbitrary local folders may load third-party extensions, so a local-path allowlist alone is insufficient as a strict crash-containment guarantee.

Start with **one supervised helper per active pane** (two bounded independent lanes); each lane serializes its own selected tab's Shell requests. When a lane stalls, a supervisor must report a recoverable error, reject old-generation replies, terminate **only the exact helper it created** and restart a fresh helper without resetting the unaffected pane. Lazy/hidden tabs have no permanently reserved processes. Avoid one helper per tab and unbounded child-process creation. Newer same-tab requests supersede older ones; a stalled previous request requires helper replacement rather than relying on an atomic cancel flag.

Production host policy: own each helper process handle and private job object (KILL_ON_JOB_CLOSE), restrict child handles to exact request/response IPC, version and bound every frame and PIDL, never pass raw pointers/COM interfaces, and apply finite timeouts, bounded restart budget/backoff and separate UI feedback. Do **not** terminate `explorer.exe`, a user's original flyExplorer process, or any unverified process by image name. The process is a fault boundary, **not** a security sandbox: it initially inherits the same user's token; future handling of malicious code needs a separate Windows token/AppContainer/privilege review.

Keep UI/tab/history and final accepted owned snapshots in the main WinUI host. Keep filesystem-only watcher handles in a separate lightweight host thread (or a bounded watcher service) so Shell stalls cannot silence them. Do not move mutating file operations, drag/drop or Shell context-menu command execution into the read-only enumeration helper. Those require a distinct authorization and recovery design.

## This slice's executable experiment scope

Build a **separately named read-only native helper** that compiles the exact shared `shell_navigation_core.cpp` and `shell_enum_bridge.cpp`. It reads a bounded UTF-16 request from an inherited private stdin pipe, performs native Shell enumeration on its own COM STA and writes a versioned, bounded binary snapshot to stdout. Results contain copied absolute PIDLs, names, attributes, flags and checksums; no WinUI or MFC DLLs are loaded. Tests must use test-owned local directories and a standard virtual Shell namespace folder.

Test supervisor starts **two actual independent helper processes** using private pipes. Simulate a hung helper using an explicit test-only delay entrypoint; terminate/reap only that Popen-owned child after a finite deadline, verify the other helper can still complete and a new helper can recover. Test a failed path, malformed protocol bounds and process exit. The test delay is NOT proof that a real third-party Shell extension can be terminated safely in every Windows configuration. Do not redirect the shipped WinUI UI to this helper until a native C++ supervisor with job-object ownership, robust IPC parsing and actual owned-GUI regression is implemented and verified.

## Explicit gates before default UI switch

1. Actual independent helper Debug and Release x64 build and synthetic/virtual Shell IPC tests.
2. Two simultaneous helpers, owned synthetic hang timeout and selective restart; no existing user process is touched.
3. **Next integration task**: native per-pane host supervisor with job objects, request epochs, bounded IPC, heartbeat/timeouts and real WinUI GUI tests. Move `SHGetPathFromIDListEx` off the UI thread and split filesystem watchers from the legacy serial COM worker.
4. Existing MFC `local_ci.bat x64`, native 20/0 regression and old owned GUI must remain unchanged. Actual product parity, extension crash tests, real slow UNC/third-party providers and accessibility/high-DPI remain separate acceptance gates.

No hosted GitHub Actions, remote push, merge or release without separate user instruction.

## Actual executable proof results — same local revision (2026-09-29)

The helper is compiled as a separate native x64 console executable without MFC/WinUI dependencies. Tracked sources: `experiments/phase6_winui_shell/isolation/FlyShellIsolationHelper.cpp`, `FlyShellIsolationHelper.project-template.xml` and `build.cmd`. The ignored generated `.vcxproj` is copied from its tracked template on each build. It uses the exact original shared `shell_navigation_core.cpp` and `shell_enum_bridge.cpp`; NO existing product build graph, original `ExplorerCtrl`, `MainWindow` or `AsyncShellWorker` was changed.

- Debug x64 build **PASS**; compiled helper SHA256 `1009F2D0836EAB103B128FC4A3B7B4E1073B2D4C257FD9C42EE431205A982F34`.
- Release x64 build **PASS**, no C++ or linker warnings in the focused build log; compiled helper SHA256 `7003CACF224ACAA0F9E29575B9D476C5B9B42939C979D8EFA4BCCE7805C36251`.
- On the actual Windows 11 machine **BOTH Debug and Release** passed owned real-process tests: typed test-local Shell listing including separate folder and file, real virtual `shell:MyComputerFolder` enumeration, absolute PIDL wire payload integrity/structure, invalid folder error without a partial snapshot, rejected oversize/truncated requests and corrupted/truncated/overlong replies.
- TWO independent helper processes were actually running: the left lane performed an explicitly authorized test-only 30-second sleep; the right lane completed real Shell enumeration while the left still existed. The test applied its 0.8-second watchdog deadline and used `TerminateJobObject` on **only its own left child**, waited for that child to be reaped, launched a fresh helper and successfully re-enumerated the original left folder. Separately, closing an independently owned private Windows job HANDLE automatically reaped an explicitly delayed owned helper well before 30 seconds.
- The six original Windows user's existing flyExplorer settings SHA256 values remained **identical** across both runs. All synthetic directories/processes were reclaimed. New focused source/architecture contracts **3/3 PASS**; prior source/architecture contracts **5/5 PASS**.
- An initial Release test assertion failed because it required a nonzero exit status from KILL_ON_JOB_CLOSE, which Windows does not guarantee. The test was corrected to require actual early process reaping (and not the natural test-delay exit 42); the same Release binary then passed. Do not misrepresent this test-only assertion failure as an underlying Shell enumeration crash.

Local, ignored evidence: `logs/m16/helper-debug-build.log`, `helper-release-build.log`, `helper-debug-final-owned-tests.log`, `helper-release-final-owned-tests.log`, `static-contract.log` and `prior-phase-source-contract.log`. Exact binary and source hashes belong in a separate local evidence manifest. This is **not** a claim that the production WinUI UI now uses the helper: `MainWindow` still uses the earlier in-process `AsyncShellWorker`, and blocked real third-party Shell extensions, real UNC/network failures, full crash-handler behavior and clean installation have **not** been tested.

**Next engineering slice:** Implement a native C++ supervisor in the existing experimental WinUI host with two bounded active-pane lanes, safely scoped Job ownership and deadline/restart budgets, strict decoding of this provisional wire protocol and PIDLs, route epoch validation, and opt-in isolated GUI tests. Move UI-side `SHGetPathFromIDListEx` and native filesystem watching to safe non-Shell UI-independent workers. Only after comparing actual GUI behavior and previous M1.5 regression may isolated navigation become the preview default; the existing MFC application remains unchanged.
