# flyExplorer current architecture

## Repository boundaries

- app/winui — canonical WinUI 3/C++/WinRT application and XAML.
- src/base — UI-independent native state, navigation, file operation,
  session/preferences and Shell-support code.
- tests/winui — source contracts, native fixtures, owned GUI automation and
  explicit manual gates.
- tools/winui — bounded build/test orchestration.
- out — ignored generated binaries/intermediates.
- .cache/nuget — ignored local package cache.
- logs — ignored local validation evidence.

Generated flyExplorer.vcxproj files are materialized from tracked project
templates. Edit the templates, not generated project files.

## UI/state ownership

    Window
    └── WindowTab[]
        ├── active pane + split state/ratio
        ├── LeftPane
        │   └── PaneTab[]
        │       ├── current Shell location
        │       ├── Back/Forward history
        │       └── view/sort/column state
        └── RightPane
            └── PaneTab[]

Theme/language are application preferences. Window geometry and active Window
Tab are session state. A pane owns its pane-local tab collection; a PaneTab owns
its navigation identity/history.

## Shell isolation

No third-party Shell provider or potentially blocking Shell extension call may
be introduced synchronously on the XAML UI thread.

The app uses a bounded two-lane native Shell supervisor,
FlyShellIsolationHelper.exe as a disposable process boundary, independent
filesystem and Shell namespace watchers, route/request tokens to reject stale
results, weak UI references with DispatcherQueue handoff, and cancellation
before window dispatcher teardown.

The helper is a bounded fault/isolation boundary, not a security sandbox.

## Session persistence

Private session schema v2 stores only bounded validated state. Persisted
filesystem history is converted to safe path values rather than retaining COM
interfaces. Existing v1 sessions remain readable. Source is authoritative for
the exact numeric limits.

## Build/runtime

Canonical root entry points:

    build.bat Release
    run.bat Release
    test.bat source
    python -X utf8 tools\winui\run_checks.py full

Release is Windows App SDK self-contained; Debug is framework-dependent. Do not
distribute flyExplorer.exe alone: sibling resources and
FlyShellIsolationHelper.exe are required.

## Change placement

Put reusable non-UI behavior in src/base when it has no WinUI dependency. Keep
presentation/UI orchestration in app/winui. Do not recreate the retired MFC
tree or a permanent hybrid UI.
