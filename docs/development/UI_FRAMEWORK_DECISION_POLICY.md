# flyExplorer UI technology selection and migration decision

This project prioritizes low total development and maintenance cost and a high-quality Windows 11 user experience. MFC retention is optional. WinUI 3 adoption is optional. This document authorizes evidence-based selection, not an untested automatic full rewrite.

## Alternatives to evaluate

- Keep and modernize MFC/Win32 where it delivers the required experience with acceptable ongoing cost.
- Introduce carefully isolated WinUI 3/C++/WinRT UI surfaces while reusing proven existing C++ file-management functionality.
- Gradually replace more presentation screens with a new UI framework when representative experiments justify the cost and regression risk.

Other viable frameworks may be evaluated using the same criteria. Do not rewrite a tested file-management engine merely to change UI technology.

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

The agent may choose a different UI technology when verified total-cost and product-quality gains justify it. Keep tested C++ core behavior reusable. Make architecture boundaries explicit, prevent regressions and stage changes in small reversible increments.

A proof of concept is not production readiness. Before integrating a migrated UI, demonstrate representative Windows build, native file operations, actual GUI input/focus, theme/DPI/accessibility behavior, saved settings compatibility and a rollback route. Cross-framework hosting additionally needs real checks of HWND ownership, UI-thread dispatch, keyboard focus, drag/drop, COM/Shell lifecycle, runtime dependencies and install/update behavior.

If the evidence is insufficient, retain the working approach for the current task and record the next minimum experiment. This does not permanently mandate MFC.

Respect repository-level tool-call budgets, protected user settings, source-to-binary revision verification and the prohibition on unapproved hosted GitHub Actions.
