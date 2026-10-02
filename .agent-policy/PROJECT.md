# flyExplorer project facts

This file contains current project-specific facts only. Generic policy remains
in the vendored .agent-policy core.

## Canonical product

- Repository: tngkrwlsmd/flyExplorer.
- Canonical branch/worktree: main / C:\dev\flyExplorer.
- Product: C++/WinRT Windows App SDK WinUI 3 file manager.
- Product source: app/winui.
- Shared UI-independent native code: src/base.
- Tests: tests/winui.
- Orchestration: tools/winui/run_checks.py.
- Generated output: ignored out/; package cache: ignored .cache/nuget/;
  local evidence: ignored logs/.
- Retired MFC product is absent from the working tree; exact historical recovery
  starts from Git revision cbffb48.

## Current product checkpoint

The latest product-code checkpoint before the 2026-10-02 documentation cleanup
is eb76c37 (feat: persist window tab sessions). Live Git refs take priority.

Current accepted UI/state includes functional top-level Window Tabs, dual panes
with pane-local tabs, Explorer-like navigation/chrome and private session schema
v2 that restores Window Tab/pane/tab/view/sort/column/history state.

## Current verification

Latest accepted 2026-10-02 evidence:
- canonical structure 4/4 PASS;
- source contracts 125/125 PASS;
- Release build PASS;
- v7-only Release GUI PASS with normal exit 0;
- isolated Korean create/watcher/restart GUI PASS;
- final full Release GUI PASS in 95.2 seconds;
- protected six user-config hashes identical.

The v7 close-race fix moved cancellation/shutdown to the window Closed boundary
and prevents late DispatcherQueue completions from turning teardown into
0xC000027B.

## Build/runtime facts

- Root wrappers are the supported build/run/test entry points.
- Release is Windows App SDK self-contained; Debug is framework-dependent.
- The tracked project template is the project-file source of truth.
- flyExplorer.exe cannot be distributed alone; sibling resources and
  FlyShellIsolationHelper.exe are required.
- Potentially blocking Shell/provider behavior stays off the XAML UI thread and
  behind bounded isolation.
- Project CI runs on the repository-scoped interactive self-hosted Windows x64
  runner; pushes to main use the Release + GUI validation scope automatically.
- GitHub-hosted runners are not part of the active flyExplorer CI path.

## Open gates

Not certified:
- actual 125/150/200% OS scaling;
- High Contrast ON;
- human Narrator/Korean IME;
- physical drag;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance;
- Large Icons and optional Known Folder-specific artwork.

The tracked installer/provenance snapshot predates v7 and must be rebuilt before
it can represent the current product.

## Documentation

Current maintained engineering docs are indexed by
docs/development/README.md. Dated MFC/Phase5/migration checkpoint documents and
legacy HTML Help were removed from the current tree; Git history is the recovery
source for those records.
