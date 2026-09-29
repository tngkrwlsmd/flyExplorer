# flyExplorer product UI directive — full WinUI 3 replacement (2026-09-29)

**Decision status: owner-directed product goal. Implementation status: in progress, NOT production complete.**
This decision supersedes earlier technology-neutral comparisons and earlier suggestions that a permanent MFC-hosted XAML Islands hybrid could be the product end state. MFC remains the supported existing product until release gates pass.

## 1. Product destination and reason

The intended final Windows UI is **100% WinUI 3 / Windows App SDK with C++/WinRT**, including the main window and all app-owned visual surfaces. The owner identified the current MFC interface as visually dated and inadequately compatible with modern dark-mode expectations. Treat modern Windows 11 visual design, consistent System/Light/Dark behavior, accessibility, DPI and localization as first-class product acceptance criteria, not a cosmetic add-on.

**Replace the presentation layer, not the proven file-management core.** Retain or extract existing native C++ Shell/navigation logic, operations, settings/schema compatibility and tested independent Shell process supervision/watchers. WinUI screens issue explicit commands against shared native state/contracts; neither WinUI UI threads nor an MFC window may become the sole owner of long-running Shell enumeration.

## 2. Mandatory development rules

- New end-user UI development goes first into the separate WinUI migration branch. Use real WinUI 3 controls, theme resources, keyboard/pointer focus and accessibility semantics; do not develop new MFC-only visual features or invest in long-term MFC dark-scrollbar/theme architecture.
- Maintain the current MFC `main` while migration is incomplete. Security fixes, blocking compatibility fixes and narrowly necessary regression maintenance in MFC remain allowed. Do not remove existing features simply because they are expensive to migrate.
- A temporary MFC/WinUI bridge, XAML Island or MFC fallback may be used for bounded migration experiments, contract extraction or safe rollout **only**. It is **not** the target architecture, not a permanent dual-UI product and not a prerequisite if the independent WinUI executable offers a simpler migration path.
- Keep full parity requirements visible: multi-pane/tabs, workspace formats, searches and privacy choices, native Shell virtual folders, menus, context actions, drag/drop, clipboard, file mutations, history, bookmarks, shortcuts, dialogs, settings and localization.
- The owner has chosen the final UI technology; do not reopen an equal-choice MFC-versus-WinUI framework selection process for each screen. Evaluate **how** to migrate and measure technical risks. Revisit the technology direction only for a documented blocking constraint and explicit new owner decision.
- Preserve the private Job-isolated left/right native Shell helpers, finite deadlines/recovery, separate filesystem and namespace change subscriptions, per-route stale-result suppression and nonblocking UI dispatch. Preserve existing user files and source-to-binary proof.
- Never equate Windows App SDK controls with automatically correct dark mode, High Contrast or accessibility. The **final rendered app** must be tested under System/Light/Dark, OS High Contrast, varied DPI, keyboard/IME, screen reader and installed localization.

## 3. Sequenced implementation roadmap

1. **M2.0 — native core/UI boundary:** inventory the current native `main` and M1.9 WinUI contracts; introduce an explicit shared state and command/event boundary so the independent WinUI app does not depend on MFC widgets. Extend the existing independent WinUI main window rather than treating an MFC XAML host as the permanent architecture.
2. **M2.1 — full WinUI application chrome:** implement the WinUI main frame, responsive command surface, address/breadcrumb, tabs, primary/secondary panes, file list/tree, status and settings shell using reusable WinUI controls. Define shared theme resources and theme persistence; maintain the feature-for-feature MFC parity matrix.
3. **M2.2 — full interaction and data parity:** migrate native MFC file operations and error feedback, Shell menus, drag/drop/clipboard, keyboard commands, filters/advanced search, workspace and session formats, bookmarks and all remaining dialogs. Keep advanced native work in reusable C++ services, not UI code.
4. **M2.3 — reliability and accessibility hardening:** verify helper crash/hang recovery, real fault fixtures where authorized, rapid tab/pane changes, large folders, System/Light/Dark, High Contrast, 100/125/150/200% DPI, keyboard/IME, Narrator, installed Korean/other language packs, startup/shutdown and installer/update/rollback.
5. **M2.4 — controlled cutover:** ship the independent WinUI build through an explicit opted-in or staged migration with tested profile import/rollback, no destructive automatic overwrite; promote WinUI to default **only after** functional, visual and reliability gates pass; retire the user-facing MFC UI only after proven migration and a recovery route.
## 4. Acceptance gates and traceability

For each migrated screen or behavior, record its MFC reference behavior, new shared contract, compiled Git revision, test-owned GUI evidence, feature/data compatibility and known deficits. Static tests, successful builds, a screenshot and actual runtime interaction are separate forms of evidence.

Before any default-product cutover: supported feature parity or explicitly owner-approved documented omissions; successful native helper and WinUI x64 Debug/Release builds; physical pointer/keyboard/IME, actual themed screenshots, stress and error-recovery runs; real user-setting safety verified through read-only hashes and test-owned profile copies; clean-install, update and rollback validation. Do not silently change the existing `main` binary or the real six user config files during preview tests.

The last independently accepted code baseline when this directive was adopted was native `main` `3a4d27c` and independently merged M1.9 WinUI preview `e84741a`. M1.9 has scoped native/GUI/interop/fault evidence but **does not yet satisfy full MFC product feature parity or UI/accessibility certification**. Later documentation-only commits may advance branch tips without implying a new product build.

**Historical scope:** `UI_FRAMEWORK_DECISION_POLICY.md` and prior Phase 4/5 MFC-versus-WinUI comparisons remain valuable for their dated measurements, not an active mandate to treat the technology destination as undecided. This directive controls future UI implementation priorities until the owner revises it.
