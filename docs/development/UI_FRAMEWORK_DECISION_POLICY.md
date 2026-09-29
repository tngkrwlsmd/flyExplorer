# flyExplorer UI technology selection and migration decision

OWNER DECISION (2026-09-29): The final flyExplorer app-owned UI will be fully WinUI 3 / Windows App SDK with C++/WinRT. The MFC interface is the protected existing product until the new UI passes release gates; no permanent MFC or hybrid UI is a target. Keep the existing proven native C++ functionality and user data. See [full UI migration directive](WINUI3_FULL_MIGRATION_DIRECTIVE_20260929.md).

## Historical alternatives and current implementation options

- Keep MFC/Win32 only for temporary baseline, safe maintenance, essential security and compatibility fixes; do not create new MFC-only cosmetic or dark-theme work as the long-term UI solution.
- Continue the separate WinUI 3/C++/WinRT application with reusable C++ file-management services. Use any MFC-hosted XAML Island only as a time-bounded integration or fallback experiment when actual evidence shows a need.
- Gradually replace all remaining app-owned MFC presentation with WinUI 3 while proving each feature and preserving tested fallback and rollback until release acceptance.

Earlier framework comparisons remain historical research; do not reopen the destination choice per screen. A documented blocking constraint and explicit renewed owner decision are required to change the final UI framework. Do not rewrite a tested file-management engine merely to replace the presentation.

## Comparable decision evidence

For equivalent, small, representative address/navigation/tab workflows, collect observed evidence for:

1. Initial implementation and integration time, refactoring effort, training and tooling.
2. Expected maintenance, customization, theme/DPI/accessibility and SDK update burden.
3. Actual Windows 11 appearance, keyboard and pointer behavior, High Contrast and localization.
4. Startup time, memory footprint, responsiveness, failure behavior and native Shell/COM interactions.
5. Target Windows version coverage, runtime/installer/packaging requirements and deployment complexity.
6. Preservation of multi-pane/tab workflows, saved user preferences, shell menus, drag/drop, shortcuts and other existing features.
7. Gradual rollout feasibility, isolated fallback and rollback cost.

Do not invent measurements or claim a technology is always cheaper. Record the scope, dates and limitations of every comparison. Avoid creating a large prototype before a small proof of concept resolves the key uncertainty.

## Implementation gates

The target technology is decided: implement full WinUI 3. Compare only architecture and incremental implementation techniques using evidence unless the owner explicitly revises the destination. Keep tested C++ core behavior reusable. Make architecture boundaries explicit, prevent regressions and stage changes in small reversible increments.

A proof of concept is not production readiness. Before integrating a migrated UI, demonstrate representative Windows build, native file operations, actual GUI input/focus, theme/DPI/accessibility behavior, saved settings compatibility and a rollback route. Cross-framework hosting additionally needs real checks of HWND ownership, UI-thread dispatch, keyboard focus, drag/drop, COM/Shell lifecycle, runtime dependencies and install/update behavior.

If an individual migration step lacks evidence, keep the MFC default temporarily, identify the next smallest validating experiment and record any blocker; do not revert to an undecided MFC-versus-WinUI strategy.

Respect repository-level tool-call budgets, protected user settings, source-to-binary revision verification and the prohibition on unapproved hosted GitHub Actions.
