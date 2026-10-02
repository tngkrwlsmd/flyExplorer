# flyExplorer repository instructions

## Current product override

The canonical product on main is the C++/WinRT WinUI 3 application under
app/winui. Shared UI-independent code is under src/base; tests are under
tests/winui; canonical orchestration is tools/winui/run_checks.py.

The former MFC product is retired from the current checkout and recoverable
only from Git revision cbffb48. Do not recreate a persistent MFC/Phase5 tree on
main.

Higher-priority runtime/user instructions override this file. The vendored
.agent-policy core remains authoritative for generic policy; project facts
belong in .agent-policy/PROJECT.md.

## Required current references

Before substantial work, use:
- docs/development/CURRENT_STATUS.md
- docs/development/ARCHITECTURE.md
- docs/development/AGENT_EFFICIENCY.md
- docs/development/ERROR_HISTORY.md for known/repeated failures.

Deleted dated migration reports are historical Git evidence, not current
instructions.

## Build and verification

Supported root entry points:

    build.bat Debug|Release
    run.bat Debug|Release [path]
    test.bat source
    clean.bat build|all
    python -X utf8 tools\winui\run_checks.py full

Edit tracked project templates, not generated .vcxproj files. Keep build output
under ignored out/, NuGet cache under .cache/nuget/, and evidence under logs/.

Static/source, compile, runtime, GUI-state and visual evidence are distinct.
Do not claim unrun gates. Follow AGENT_EFFICIENCY.md call budgets and bounded
log rules.

## Architecture and safety

Potentially blocking Shell/provider calls must not run synchronously on the
XAML UI thread. Preserve isolated helper/supervisor behavior, route-token stale
result rejection, owned process boundaries and early-close cancellation.

Use test-owned directories/processes. Do not arbitrarily reset, discard,
overwrite or mutate user files/settings. Global clipboard, real Recycle Bin,
machine-wide install and similar OS-global effects are separate explicit gates.

ko-KR is the default for new app-owned UI. Preserve true UTF-8 Unicode and
validate real GUI behavior when relevant.

## UI direction

Windows 11 File Explorer is the primary visual/interaction reference using
public WinUI/Windows APIs only. Preserve flyExplorer's dual-pane model. See
docs/development/UI_UX_DESIGN_GUIDE.md and
docs/development/WIN11_EXPLORER_UI_REFERENCE.md.

## External tools and CI

Do not use chatgpt-codex-connector unless the user explicitly requests or
permits it for the task. Normal GitHub connector/API access is allowed when
appropriate.

GitHub Actions workflows are manual-only by project policy. Do not dispatch
hosted CI without explicit user approval.

## Git logical units

If commit/push is approved for the task, complete a verified logical unit, run
git diff --check, inspect staged scope, commit, normal-push, fetch, and verify
HEAD == origin/main with ahead/behind 0/0. Never force-push.

Do not push a state with a known required acceptance failure, temporary debug
instrumentation or generated artifacts.
