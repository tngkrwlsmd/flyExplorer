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

## Evidence

For visual claims record binary/revision, theme, DPI, window size and fixture.
Compare like-for-like conditions. Do not turn one screenshot into a
product-wide PASS.
