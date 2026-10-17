# F04 — expandable local folder tree (incremental implementation)

## F04-A path/identity foundation — 2026-10-17

F04 is not yet a user-visible TreeView. This first isolated logical unit
adds only the reusable, UI-independent lexical path and stale-result guards
in app/winui/folder_tree_path.h, a native executable regression, and a
source contract registered with the existing shell source suite.

- Accepted lexical shape: normalized absolute drive-letter paths, including
  the exact root, with bounded length (1,024 UTF-16 units), nesting (12 levels)
  and a documented future sibling budget (128). Reject UNC, device prefixes,
  drive-relative paths, empty/dot/dotdot segments, reserved Win32 device
  names, dangerous leaf characters and trailing dots/spaces.
- Child construction changes the output only on a valid path; Korean names
  and ordinary spaces are preserved.
- A future async expansion result must match active side, tab, navigation
  route and expansion generation. The pure identity guard rejects stale
  answers after pane/tab/route/expansion changes.
- The lexical guard proves neither volume type nor path containment against
  junctions/reparse/hardlinks. Real fixed-drive inspection and no-reparse
  decisions belong in a bounded isolated worker off the WinUI thread.
- No directory enumeration, read of personal files, global Windows-setting
  change, filesystem mutation, UI pixel change or new navigation command
  is introduced in F04-A.

## Next isolated unit — F04-B (not implemented / not accepted)

Add an explicit opt-in expandable TreeView in NavigationSidebar, local fixed
drive roots first; enumerate each expanded folder lazily with at most 128
child folders and a test-owned, cancellable isolated worker. Reject reparse,
UNC, provider and removable roots until individually reviewed. Resolve a
selected tree node to the existing active-pane OpenFolder route only, never
silently switch pane or tab. Verify keyboard/UIA focus, two-pane/tab route
changes, collapse/re-expand stale answers, empty/access-denied cases and the
mandatory actual light/dark before/after screenshot/pixel comparison.

## Acceptance boundaries

For F04-A, run the three registered stdlib source contracts and compile/run
the dedicated native fixture (C++17). Linux compiler execution checks only
portable path logic; it is not a Windows Release/GUI or visual acceptance.
F04-B remains open until exact-source Windows build, functional GUI and
independent pixel inspection are complete. Keep F03/F05/legacy paths unchanged.
