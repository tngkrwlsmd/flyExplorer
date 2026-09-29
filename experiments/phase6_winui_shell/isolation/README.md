# M1.7 — isolated native Shell helper (actual WinUI preview integration)

The current M1.7 WinUI preview **now really launches this helper** through a native two-lane C++ supervisor, with same-config sibling staging in the tracked preview `build.cmd`, finite deadlines/private Jobs and one automatic restart. It also uses a separate, COM-free filesystem watcher. Actual owned WinUI Debug timeout/restart and ordinary Release GUI tests passed. This is still **not** the production MFC default or a restricted-token security sandbox. The earlier helper-only text below is historical; see [M1.7 live integration and real GUI evidence](../../../docs/development/WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md).

## Historical M1.6 helper-only experiment

This directory contains a **read-only, out-of-process experimental helper**, not a replacement for the current WinUI 3 navigation worker. The current WinUI executable still uses the existing single `AsyncShellWorker`. No production GUI, existing MFC binary, system association, or user setting is modified by the experiment.

The tracked `FlyShellIsolationHelper.project-template.xml` (materialized by `build.cmd` into an ignored generated `FlyShellIsolationHelper.vcxproj`) compiles the **same** MFC-free `src/base/shell_navigation_core.cpp` and `shell_enum_bridge.cpp` used by the previously verified WinUI experiment. It reads a bounded UTF-16 request over its privately inherited standard input pipe and writes a versioned, length-checked binary snapshot with owned absolute PIDL copies over standard output. It has no file-operation or mutation API and no UI dependencies. This is a process fault boundary, **not** a restricted-token security sandbox.

Build from the tracked project template using the local Windows 11 / VS2026 environment:

`build.cmd Debug` or `build.cmd Release`. Never edit the generated/ignored `.vcxproj`.

On the connected Windows computer, run `python test_process_isolation.py` from the repository (it locates the binary itself). Set `FLY_M16_CONFIG=Release` in the test process for Release. The test harness creates only its own disposable directories and helpers, uses exact owned process handles and individual Windows Job objects, and verifies an owned synthetic 30-second delay is stopped after a finite timeout without affecting the other process. It also checks KILL_ON_JOB_CLOSE by closing the **test-owned** job handle. It deliberately does **not** inject or terminate a real third-party Shell extension. Run `python -m unittest test_contract.py` for focused source/protocol/architectural guardrails.

Limits: The test's Python host is a validation tool, **not** a production C++ supervisor. At the historical M1.6 stage, before the subsequent M1.7 integration, the actual WinUI host needed two bounded native process lanes with owned Job objects, authenticated executable path/handle ownership, strict request/response decoding, resource/restart budgets and status feedback. Filesystem watchers must be independent of hung Shell calls, and `SHGetPathFromIDListEx` must be moved off the UI thread. See `docs/development/WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md` for the risk assessment, scope decision and exact result.
