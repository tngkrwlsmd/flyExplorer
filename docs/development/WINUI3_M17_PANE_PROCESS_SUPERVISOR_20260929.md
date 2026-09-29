# M1.7: real WinUI 3 per-pane Shell process supervision and standalone filesystem watches

**Later M1.8 milestone:** See [owned COM and loopback-network failure UX plus separate Shell namespace subscriptions](WINUI3_M18_SHELL_STABILITY_20260929.md). The following M1.7 record is revision-scoped and predates the notification implementation. Real third-party extension and external virtual-provider events remain unverified.

Date: 2026-09-29. Worktree: `C:\dev\flyExplorer-winui3-migration`; base HEAD `a829fd1`. This is a scoped **experimental WinUI preview integration**. The production MFC file manager, profile, registry, DPI and user windows were not changed.

## Implemented (actual source)

1. `src/base/shell_isolated_supervisor.h/.cpp` replaces the WinUI preview's old shared serial COM worker with a native **two-lane supervisor** (one independent execution lane per pane). Each outstanding request launches an exact, test-preview-owned **sibling executable**, bounded to two simultaneous helpers. The supervisor obtains the helper's absolute path from its own preview EXE, creates private stdin/stdout and NUL stderr handles using an explicit process attribute handle allowlist, launches the child **suspended**, assigns it to its own private Windows Job Object with `KILL_ON_JOB_CLOSE` and one-process limit, then resumes only that child.
2. Each lane checks for newer requests at most every 20ms during read, uses a **4,500ms deadline** and at most **two attempts** per selected navigation request. On timeout it terminates only the exact lane-owned Job, reaps and closes the child, and launches one fresh helper. Further timeout yields a failed navigation without modifying the last accepted folder. A new same-pane request cancels the previous helper; the other pane's child is unaffected. Tab-specific route/request tokens and the weak WinUI DispatcherQueue recipient reject stale results.
3. `src/base/shell_isolation_wire.h` and `experiments/phase6_winui_shell/isolation/FlyShellIsolationHelper.cpp` share version 2 of a bounded protocol. Requests contain either a UTF-16 Shell parsing name or **copied absolute PIDL bytes**; responses have bounded/count-validated owned PIDL bytes, display names, checksum, truncation flag and an optional actual filesystem path computed **inside the helper** using `SHGetPathFromIDListEx`. The host checks each PIDL structure and validates the entire response before atomically committing a prepared snapshot. No COM interface pointer crosses the pipe. The helper exposes **read-only enumeration only**.
4. `src/base/directory_watcher.h/.cpp` is an independent native Win32-only watcher thread, shared by the two selected **filesystem** pane routes. Unlike the previous arrangement, a stuck Shell helper does not share its work queue or COM apartment. WinUI `UpdateWatch` now reads the helper-returned filesystem path instead of calling `SHGetPathFromIDListEx` itself. This retains asynchronous synthetic file creation/deletion refresh and route-token protection.
5. `experiments/phase6_winui_shell/build.cmd` builds the helper from its **tracked** project template for the same Debug/Release x64 configuration, then stages only the matching helper next to its separately named WinUI preview EXE. The WinUI project no longer links the old in-process `shell_async_worker.cpp`, though the unchanged original native code and its 20-test MFC suite still retain that implementation. No UI file copy/move/delete, context menu execution, product associations or config migration was enabled.

**Process-per-request design:** The two independent lanes do *not* keep two persistent helpers alive while idle; they launch a new read-only child per navigation/refresh attempt and reclaim its private Job after completion. This limits the concurrency and isolates hangs/crashes at the cost of child-launch overhead. The helper is a **fault-containment boundary, not a security sandbox**; it inherits the current user's token. A hostile OS/kernel driver or other system-level fault cannot be contained by this design.

## Actual revision-scoped Windows tests and evidence

| Test | Result and exact evidence |
| --- | --- |
| WinUI Debug x64 + matching helper | PASS, `logs/m16/m17-final-debug-after-removing-old-worker-build.log` |
| Actual owned WinUI Debug GUI with left **test-only** 30s blocked child | PASS: **right pane loaded while left blocked**, left timed out and automatically restarted, real native auto-refresh after owned file create/delete, independent pane navigation and virtual This PC; owned process exit 0, six original user settings SHA256 identical. `logs/m16/m17-final-debug-exact-owned-timeout-recovery-gui.log` |
| WinUI Release x64 + matching helper | PASS, `logs/m16/m17-final-winui-release-x64-build.log` |
| Actual owned WinUI Release x64 GUI | PASS: both real filesystem panes, independent tab/history, virtual This PC, native PIDL row open, native create **and** delete watcher refresh, process exit 0 and six original user settings SHA256 identical. `logs/m16/m17-final-release-owned-winui-real-gui.log` |
| Read-only helper protocol/Job regression | PASS in standalone Debug and final Release, including actual ordinary/virtual absolute PIDL round-trip, corrupt/oversize/truncated IPC rejection, selective Job termination, automatic private Job-close reaping and unchanged real settings. `logs/m16/m17-helper-version2-debug-protocol.log`, `logs/m16/m17-final-release-standalone-v2-wire-and-job.log` |
| M1.5 + M1.6 + new M1.7 focused architecture contracts | **12/12 PASS**, `logs/m16/m17-final-all-source-contracts.log` |
| Original MFC product / tests | Original production/native tests/build graphs unchanged in this slice; existing exact M1.5 `20/0 PASS WITH SKIPS` record reusable but **not rerun now**. |

SHA256 of final paired binary sets:

| Binary | SHA256 |
| --- | --- |
| WinUI Debug EXE | `D5A3E4D44A7278BC0B3CF338A4D31F6D5DD29F0D8D8801CFC86932E4D420A8EC` |
| Its matching Debug helper | `5370EE4B78E578ADB57A9F07BDD2D8538C38DA76A11DDE5F691E6EABB4592645` |
| WinUI Release EXE | `B4CCB956FD886CC72DF9CAE78A0BCFD484972A9882D5B9DD75032F6FC779EF93` |
| Its matching Release helper | `B76BFC297D562E91BF7208670CCE2BD156901B066CAD164A2CFD32D1CAC3B6EC` |

Complete source/binary/log hash manifest: ignored local `logs/m16/m17-exact-source-binary-evidence-manifest.json`. No remote push, hosted CI, merge or release in this implementation slice.

## Known limitations and explicit next gates

- **Synthetic test only**, not an actual hung/malicious third-party Shell extension or inaccessible UNC path. `CreateProcess` itself and certain OS/kernel I/O can also block; a child-per-request Job is not a guaranteed timeout on every kernel-level failure. The bound applies to the actively monitored helper, not an absolute guarantee about all system interactions.
- At most two selected filesystem paths are watched; no virtual Shell namespace change notifications. Win32 filesystem watcher creation can itself block on some remote/network folders; its own separate thread prevents that from blocking Shell lanes but does not guarantee every watch remains healthy. Watcher retry/debounce and selection/scroll restoration after complete re-enumeration need separate product work.
- Truncation at 1200 entries, 4MiB response bound, 16K UTF-16 parsing path and 64KiB individual absolute PIDL bounds are explicit. No streaming large-directory UI, shared icon/thumbnail caches, all Shell namespaces, physical alternate DPI/OS High Contrast/Narrator, real network-failure performance or clean-machine deployment certification.
- Failure feedback currently retains the previous folder and reports a generic Shell operation failure; distinguish exhausted deadline from other failures and add bounded diagnostics in a separate small UI polish slice. Do not use a real user profile for crash/kill probes.
- The shared `shell_navigation_core.cpp` still contains legacy synchronous `Session` helpers in the WinUI binary to retain its session type; only the actual WinUI navigation path is redirected to the isolated supervisor. A later source split can eliminate unreachable in-process enum functions.
- Existing `M1.6` design document records the *earlier* helper-only experiment and is historical after this revision. This `M1.7` file describes actual subsequent WinUI host integration. Other MFC product UI parity and isolated file mutations remain unimplemented.
