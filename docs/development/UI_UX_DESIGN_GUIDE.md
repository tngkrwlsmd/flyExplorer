# flyExplorer UI/UX design guide

## Product direction

flyExplorer is a native WinUI 3 Windows file manager. Windows 11 File Explorer
is the primary visual/interaction reference, not a pixel-clone target.
flyExplorer keeps its defining dual-pane workflow.

## Structural rules

- Top-level Window Tabs represent independent workspaces.
- Each Window Tab owns two pane states and its split state.
- Each pane keeps its own folder tabs.
- Navigation/history/view/sort state belongs to the pane tab that uses it.
- Do not flatten the dual-pane model merely to imitate Explorer's single-pane
  hierarchy.

## Visual rules

Prefer public WinUI/Windows App SDK controls, Fluent spacing/state conventions,
system typography/theme resources and documented Windows APIs. Avoid private
Explorer APIs, extracted system resources and undocumented theme strings.

The current icon-view density may be denser than Explorer when that improves
dual-pane readability. Visual similarity never overrides functional ownership
or information density.

## Language and accessibility

ko-KR is the default for new app-owned labels, accessible names, feedback and
actual Hangul filename tests. Keep source UTF-8 and verify real Unicode UI.

New/changed controls need usable UI Automation names, keyboard reachability,
focus behavior and theme readability. Source-level accessibility support is not
a substitute for human Narrator, High Contrast or alternate-DPI acceptance.

## Mandatory screenshot and visual-review loop

A user-visible UI change is not complete merely because source contracts, build
or UI Automation pass. The actual WinUI product must be visually reviewed.

For every change that alters composited pixels:

1. **BEFORE** — capture the current product before the visual change using a
   test-owned fixture. Record revision/binary, theme, DPI/scale, window size and
   relevant pane/view state.
2. **AFTER** — capture the changed product under the same conditions. Add
   screenshots for relevant interactive states such as active/inactive pane,
   focus/selection, expanded/collapsed UI, dialog/menu, busy/error/empty state or
   narrow split-pane layout when the change affects them.
3. **Review** — inspect alignment, spacing, padding, visual hierarchy,
   typography, clipping/truncation/wrapping, overlap, icon alignment, focus and
   selection visibility, disabled-state readability, status/progress
   visibility, contrast/theme consistency and dual-pane density.
4. **Compare** — identify intended changes separately from unintended visual
   regressions. Windows 11 File Explorer is the primary interaction/chrome
   reference, not a pixel-clone target.
5. **Iterate** — any material visual defect requires a code fix followed by a
   new screenshot and another visual review. Merely taking a screenshot is not
   acceptance.
6. **Report separately** — functional GUI acceptance and visual acceptance are
   independent. If final-pixel review was not performed, report
   `VISUAL ACCEPTANCE: NOT TESTED` and do not call the UI task fully accepted.

Do not manufacture certification for an untested theme, DPI, accessibility or
input condition. For layout/theme/scale-sensitive work, exercise every
environment that is actually available and list the rest as NOT TESTED or
ENVIRONMENT BLOCKED. Current 125/150/200% DPI, High Contrast, human Narrator
and Korean IME remain separate explicit gates until actually exercised.

Pure behavior-preserving refactors with no composited-pixel change do not need a
new BEFORE/AFTER screenshot pair, though their required functional GUI
regressions still apply.

## Evidence

For visual claims record binary/revision, theme, DPI, window size and fixture.
Compare like-for-like conditions. Keep evidence on test-owned paths or CI
artifacts and do not commit screenshots containing personal filenames/private
desktop content. Do not turn one screenshot into a product-wide PASS.
