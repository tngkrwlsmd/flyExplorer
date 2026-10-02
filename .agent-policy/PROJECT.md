# flyExplorer project facts

This file contains current project-specific facts only. Generic policy remains
in the vendored .agent-policy core.

Vendored generic policy provenance: tngkrwlsmd/universal-agent-docs commit
bafb40f55dcb6aa15f432b391ba5487b87759e0e. Upstream-managed .agent-policy files are synchronized as one
consumer core; this PROJECT.md remains project-owned across bundle refreshes.

<!-- project-facts:start -->
```json
{
  "profile": "consumer",
  "facts": {
    "repository_root": {"value": ".", "status": "Confirmed", "evidence": "path:."},
    "primary_source": {"value": "app/winui", "status": "Confirmed", "evidence": "path:app/winui"},
    "build_command": {"value": "build.bat Release", "status": "Confirmed", "evidence": "command-source:.github/workflows/windows-build.yml::build.bat Release"},
    "test_command": {"value": "test.bat source", "status": "Confirmed", "evidence": "command-source:.github/workflows/windows-build.yml::test.bat source"},
    "runtime": {"value": "Windows 11 / Visual Studio 18.x / Python 3.14.x", "status": "Confirmed", "evidence": "manual:project self-hosted Windows runner preflight and current build policy"},
    "deploy_command": {"value": "", "status": "Unknown", "evidence": "manual:public deployment/signing remains an open gate"},
    "deploy_target": {"value": "", "status": "Unknown", "evidence": "manual:public deployment target is not certified"}
  },
  "components": [
    {"name": "winui-app", "path": "app/winui", "responsibility": "C++/WinRT WinUI 3 application"},
    {"name": "base", "path": "src/base", "responsibility": "UI-independent native values and services"},
    {"name": "winui-tests", "path": "tests/winui", "responsibility": "source, native and owned GUI contracts"}
  ],
  "review": {
    "reviewed_revision": "20e56e9f7cb25162fbe53d446e3102ef23ad2f87",
    "reviewed_at": "2026-10-02",
    "reviewed_paths": [
      "app/winui",
      "src/base",
      "build.bat",
      "tests/winui/requirements-gui.txt"
    ]
  }
}
```
<!-- project-facts:end -->

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

Current main includes V8-A WindowWorkspaceController and V8-B
SessionCoordinator responsibility extraction through 6c2a677. Live Git refs
take priority.

Current accepted UI/state includes functional top-level Window Tabs, dual panes
with pane-local tabs, Explorer-like navigation/chrome, private session schema v2
restore, and WindowWorkspaceController ownership of top-level workspace state.

## Current verification

Latest accepted product evidence before this policy-gate correction:
- canonical structure 4/4 PASS;
- source contracts 138/138 PASS;
- canonical Release build PASS;
- owned Release GUI PASS with OWNED_WINUI_SHELL_EXIT 0;
- private-session clear/revoke PASS;
- protected six user-config hashes identical.

The later CI-only remote-task workflow commit does not modify product code.
Its first automatic GUI run exposed a history-readiness timing failure that is
tracked separately from this policy-gate correction.

The v7 close-race fix moved cancellation/shutdown to the window Closed boundary
and prevents late DispatcherQueue completions from turning teardown into
0xC000027B.

## Build/runtime facts

- Root wrappers are the supported build/run/test entry points.
- Canonical Windows full builds require Visual Studio/MSBuild 18.x, MSVC v145
  x64 tools and Windows SDK 10.0.26100.0; v143 is not a claimed full-build
  target.
- Release is Windows App SDK self-contained; Debug is framework-dependent.
- The tracked project template is the project-file source of truth.
- flyExplorer.exe cannot be distributed alone; sibling resources and
  FlyShellIsolationHelper.exe are required.
- Potentially blocking Shell/provider behavior stays off the XAML UI thread and
  behind bounded isolation.
- Project CI runs on the repository-scoped interactive self-hosted Windows x64
  runner; pushes to main use the Release + GUI validation scope automatically.
- GitHub-hosted runners require explicit user approval and are not part of the
  active flyExplorer CI path by default.
- The privileged self-hosted runner must not execute untrusted fork/PR code
  automatically.
- Normal repository work intentionally overrides the generic branch-first
  default: prefer verified direct-main logical units; use a work branch only
  when repository protection, explicit user direction, concurrent work, or
  isolated integration testing makes one necessary.
- Vendored generic policy is validated as Profile B-style bundle/readiness/
  conformance evidence in self-hosted CI. This does not claim Profile C runtime
  enforcement.

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
