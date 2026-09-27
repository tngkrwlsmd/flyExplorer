# Phase 4: real-DPI UI validation and framework experiment

Date: 2026-09-27. Unchanged production binary: 6d1f76388b0b8326568478ce35814aba1eb69a0e. Main guidelines at start: 792d91e507d2bf049ab35c143be3876c48588d51. Isolated experiment: [Phase4 native navigation proof](https://github.com/tngkrwlsmd/flyExplorer/tree/experiments/phase4-ui-tech-20260927/experiments/ui_phase4_navigation), commit ad561271a08cd493ad477059f306e5cbfd22f4ac. The proof was not merged into the product.

## Real validation and untested cases

The connected Windows 11 system reports build 26200, one primary 1920x1080 display and **actual system DPI 96 (100%)**. The unchanged product binary was launched with a read-only partial copy of four actual saved user UI files (fxfile.conf, fxfile-main.conf, fxfile-toolbar.dat, fxfile-coolbar.dat), with global hotkey/startup, shell registration and single-instance routing disabled **only inside that copy** and separate APPDATA. The test used a synthetic fixture, exited normally, and original source-file SHA256 hashes matched before and after. Three native toolbar bands remained 1175x40 pixels and one 1175x21, matching the prior Phase3 measurements; list header measured 28 pixels and address bar 36 pixels. The private capture remains under ignored local logs/phase4 and is not in Git.

For the **same, unchanged product revision**, Phase3 already validated synthetic Dark, Light and System themes, native header/address geometry, editable address focus and narrow Dark responsiveness. These valid previous results are reused, NOT presented as new Phase4 runs. The prior production x64 build and 17/0 native functional checks passed; protected-user HKCU-sensitive official runtime smoke was SKIPPED, not PASS. No actual new product UI defect was established in the narrow Phase4 validation, so the existing production UI and binary were not changed.

**NOT TESTED:** real 125%, 150% and 200% system DPI; actual operating-system High Contrast (system accessibility registry state was read but not changed); equivalent new Windows Explorer same-fixture side-by-side capture; complete user profile and HKCU isolation; full UI-02/UI-05/UI-09/HANG-01 interactive matrix. Do not count screenshot magnification as real DPI testing or partial settings copy as full isolation. Independent DPI/High Contrast test account or provisioned VM is needed before further claims; do not change the user's active system settings.

## Architecture actually inspected

The product statically links MFC in src/fxfile/fxfile.vcxproj. Reusable native functionality also exists under src/base and src/xpr, but no complete core was independently linked into the experimental binary. src/fxfile/cmd/router/cmd_command_map.cpp binds Back/Forward/Up IDs to GoDirect command objects. In src/fxfile/cmd/cmd_history.cpp, the actual Back/Forward handlers query ExplorerCtrl and call goBackward/goForward; src/fxfile/cmd/cmd_go_path.cpp delegates Up to ExplorerCtrl::goUp. A replacement UI therefore needs a verified small CommandContext/ExplorerCtrl adapter preserving the active pane, native Shell objects, history and UI thread; an unrelated standalone path history is insufficient. Existing multi-pane, tabs, saved toolbar layout, file operations, Shell context menus, drag/drop, accelerators and user settings remain product acceptance requirements.

## Compared implementation paths and evidence limits

| Approach | Actual observations | Remaining uncertainty |
| --- | --- | --- |
| Maintain and improve current MFC/Win32 | Production build/function tests and prior real Dark/Light/System synthetic UI verified. New Phase4 clone at actual 96 DPI preserves stored toolbar/header/address geometry. No extra framework development dependency needed for the current features. | Remaining real DPI/High Contrast tests, cost of continued custom painting, future changes and long-term maintenance. |
| Native Win32 host with C++/WinRT Foundation | Separate C++20 experiment built using installed VS2026/Windows SDK without downloading packages. An actual 96-DPI GUI launched and Up/Back/Forward/Up mouse operations, initially disabled Back, responsiveness, and clean shutdown passed. Windows.Foundation URI initialization completed. Source, build instructions, limitations and portable synthetic GUI test are on the experiment branch. | **Not actual WinUI 3.** The experiment does not use flyExplorer's ExplorerCtrl/CommandContext. Does not prove Fluent UI quality, mixed-framework hosting, production feature parity, installer implications or lower lifetime cost. |
| Actual WinUI 3 island or staged UI replacement | Windows App Runtime installations are present on the connected machine. | WinUI 3 C++ development workload/project template and SDK NuGet development package were not confirmed. No WinUI 3 XAML control built, hosted or tested; no representative cost/performance/accessibility/deployment measurements exist. |

The simple isolated proof cannot be compared numerically with the mature MFC product on development cost, code size or runtime performance. No estimated savings or winner should be inferred. Windows App Runtime installed on the PC does not itself establish a usable WinUI 3 C++ development environment.

## Bounded next steps and decision gates

1. Ask permission before installing or changing any missing WinUI 3 SDK/development components or provisioning an independent Windows test environment. Prefer an isolated development VM; do not install packages or change system accessibility settings unilaterally.
2. With minimum necessary tooling, implement an actual WinUI 3 navigation control proof on the same synthetic fixture. Record real setup/implementation/test/deployment effort, Light/Dark, focus/keyboard/IME, screen-reader behavior and, when safely available, High Contrast and actual additional DPIs.
3. Separately prototype a thin adapter to actual product command state and the owning UI thread. Verify Back/Forward/Up, current-pane history, native shell folders, tabs, drag/drop, accelerators and persisted toolbar data under a copied profile. Do not merge an in-memory imitation into the real app.
4. Provision actual 125%, 150%, 200% and High Contrast test environments to compare the current production implementation and candidate under identical actual conditions, including launch and rollback.
5. Decide per screen only after comparable observed setup, integration, maintenance and compatibility evidence exists. The current evidence supports continuing the working product while running a limited additional experiment; **it does not establish that an MFC-to-WinUI migration would reduce costs**.

No new SDK was installed. No personal settings, system DPI or OS High Contrast were modified. GitHub Actions were not dispatched.
