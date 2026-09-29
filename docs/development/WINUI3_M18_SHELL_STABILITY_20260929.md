# WinUI 3 M1.8 — scoped Shell fault handling, network errors and namespace-change subscriptions

Date: 2026-09-29. Isolated migration worktree only: `C:\dev\flyExplorer-winui3-migration`, based on local M1.7 `d5d09b7`. No production MFC GUI source was changed, no global Windows settings or Shell-extension registration was written, and no hosted CI, merge, push or installer release was performed.

## 1. Actual implementation

- The native two-lane `IsolatedShellSupervisor` now retains the reason for an exhausted helper timeout, recognizes a requested UNC path, and tracks the completed attempt count. The WinUI preview shows distinct, actionable status text after **both** 4.5-second Shell-helper attempts time out, or when a UNC request fails. In either case the last accepted folder, tab history and file list remain intact. Requests are still route/generation-checked and terminate only their exact owned helper Job.
- Added an **unregistered, test-only COM interface object** inside the existing private Shell helper. Its real `IUnknown::QueryInterface` method sleeps for 30 seconds in the helper's COM STA. Only the matching Debug GUI test command **and** explicit environment opt-in can request the behavior. This tests an actual blocking COM method call and private helper termination/recovery **without installing or invoking a known bad third-party Shell extension**; it is not proof of recovery from every real extension, network provider or kernel fault.
- Added an opt-in second COM test mode that blocks **both** attempts *after* a real test-owned local folder has successfully loaded. The actual WinUI GUI displays the exhausted-timeout explanation while preserving the last good left and right folders. No normal navigation path triggers this test-only mode.
- Added `src/base/shell_namespace_watcher.h/.cpp`: an independent Shell notification subscription thread with a private message-only HWND/message pump. It registers `SHChangeNotifyRegister` subscriptions for a maximum of two selected virtual-folder absolute PIDLs, verifies route, generation and PIDL identity before forwarding `SHChangeNotification_Lock/Unlock` events through the existing weak UI dispatcher, and deregisters on selection change/exit. The older, **separate** COM-free `DirectoryWatcher` continues to observe selected normal filesystem paths. Neither watcher uses the Shell enumeration helper's STA.
- The current WinUI preview now registers its actual virtual This PC folder using this namespace watcher when the helper reports no filesystem path. To prove the actual notification route without emitting fake global changes to This PC or user folders, an **isolated Debug-only** test registers that same watcher on a synthetic, test-owned local folder and delivers `SHChangeNotify(SHCNE_UPDATEDIR)` for that exact owned folder. Its real GUI list refresh and status update passed. **A genuine device/third-party virtual namespace event has not been reproduced** and remains a separate acceptance item.

## 2. Build, native contracts and real Windows GUI

All files under `logs/m18` are locally ignored test evidence; original real user settings are read-only hash sentinels.

| Test / binary | Verified result |
| --- | --- |
| Current WinUI Debug x64 + matched read-only helper | **PASS**: `m18-fixed-exhaustion-final-debug-build.log`; WinUI EXE SHA256 `E846A17E3EC06B5EDFCBC3B2E093EE75EE8D47D765D96783272845488D686523` |
| Real WinUI Debug, two test-owned blocked COM calls | **PASS**: both native helpers timed out, actual actionable two-attempt status appeared, previous left/right folder lists retained, ordinary remaining navigation/watch/virtual Shell regression PASS, owned host exit 0, SIX original setting hashes unchanged. `m18-exhausted-two-com-attempts-fixed-owned-gui.log` |
| Same final Debug binary: blocked COM + isolated namespace event + invalid loopback UNC | **PASS**: right pane continued while left COM call blocked, left recovered after private Job timeout/restart, test-owned Shell notification delivered to real WinUI; native filesystem create/delete refresh and virtual This PC exploration continued; nonexistent `\\127.0.0.1\flyexplorer-m18-owned-no-share` safely failed with a network-specific message and previous folder intact; owned host exit 0, SIX original hashes unchanged. `m18-final-latest-debug-owned-com-shell-notify-and-loopback-unc-gui.log` |
| Current WinUI Release x64 + matched child | **PASS**: `m18-final-release-x64-build.log`; WinUI EXE SHA256 `9BF898985A9E1E7A7A2F0D86CD4AF43037A968A0CA729182454539EED4EB306D`; child SHA256 `71C49FF74BA986F1FAF523159F473DC2D0989217F476F8BD145D57DDEB6EBC16` |
| Release native child protocol/owned Job tests | **PASS**, `m18-final-release-helper-protocol-owned-job.log` |
| Real owned Release WinUI GUI | **PASS**: normal independent pane/tab/native PIDL/virtual folder and physical filesystem creation/deletion notification, normal exit 0, original SIX hashes identical. `m18-final-release-real-owned-gui.log` |
| Current static integration and regression checks | **14/14 PASS**, `m18-final-source-contracts.log` |
| Existing MFC native 20 tests | Legacy sources/build graph **unchanged**. Earlier M1.5 20/0 `PASS WITH SKIPS` is revision-scoped historical evidence; **NOT RERUN** in this M1.8 slice. |

A failed preliminary **test**, not evidence of a product network failure, embedded a form-feed escape instead of a backslash in a Python UNC test path. The test harness path was corrected and the same compiled Debug application subsequently passed the actual inaccessible-loopback request. A separate initial compile error in a **Debug-only CLI argument loop** (`i` outside its loop scope) was fixed before the exact final Debug/Release builds and GUI runs. Preserve both initial failures in the append-only error history.

## 3. Explicitly NOT verified / next acceptance

- No existing genuinely faulty or malicious **third-party** Shell extension was installed or invoked. The bounded 30-second test-owned COM-vtable call demonstrates private-process containment and useful UI feedback, not blanket real-extension tolerance.
- `\\127.0.0.1` accessed only a **nonexistent loopback** share. It did not change shares, firewall, drive maps or use a remote computer. Real slow/offline UNC, authentication failures and permission-denied live servers require an authorized disposable SMB fixture and owner-provided failure scenario.
- The notification component subscribes to virtual This PC, and its change-delivery path passed for an **owned local Shell notification**. Actual change emissions from virtual This PC, removable media or third-party Shell namespace providers, rapid event bursts and registration retry after failure are **NOT ACCEPTED**.
- The helper is a fault-isolation boundary, **not** a restricted-token security sandbox. A blocked OS-level child creation, system kernel I/O, runaway namespace notification flood, unsupported high DPI/High Contrast/Narrator and full production file-operation parity remain outside this scoped test.
- Keep the two active-pane limit, bounded process retry, route/token checks, private Job ownership and original user settings protection. Do not replace the production MFC app based on this experiment.

Exact revision/source/hash/log cross-checks are stored separately in the ignored `logs/m18/evidence-manifest.json`.
