# WinUI development tools

`run_checks.py` is the canonical bounded local orchestrator for the current
WinUI product. It knows the repository layout explicitly:

- product: `app/winui`
- tests: `tests/winui`
- logs: `logs/winui-scoped`

It does not dispatch CI or publish releases. Global clipboard and destructive
user-state scenarios remain separate explicit tests.

The app build runs `resolve_msbuild.py --winui` before helper compilation or
NuGet restore. In addition to MSBuild 18.x, MSVC v145 and SDK 10.0.26100.0,
this verifies the Windows Store C++ x64 platform/toolset imports from the same
VC root. A desktop-only installation needs the Visual Studio Installer
component `Microsoft.VisualStudio.ComponentGroup.UWP.VC`. The resolver's default
mode remains available to helper and native-only builds.

## Owned helper page measurements

From the repository root, run:

    python tests/winui/helper/benchmark_pages.py --items 8000 --configuration Release

The default is 200 files. The 8000 and 20000 choices always pass the same
200-file lifecycle first. It creates only disposable fixtures under
logs/helper-page-benchmark on a fixed local drive, reads them through the
canonical runtime's helper, checks every page/count/continuation flag and the
complete unique inventory/content, then removes its owned fixture. Existing
legacy and WinUI profiles are read-only guarded. Inherited FLY_ fault/test flags
are removed. Each fresh helper process has a bounded timeout; Python reaps that
exact child on timeout.

The JSON report records source revision, helper binary hash, environment, fixture
creation time, first/per-page/total/max latency and data guards. Page timing includes
process startup, Shell binding/enumeration and IPC; it excludes fixture creation,
Python reply validation and cleanup. OS caches are uncontrolled. These measurements
do not certify GUI rendering/responsiveness, supervisor scheduling, sorting or
indexed metadata/search latency. No OS settings or global clipboard are used.

run_checks.py loads selected contract files through run_source_contracts.py.
It does not import them as tests.winui modules, which could resolve to an
unrelated installed tests package. Empty selections/files and import/assertion
failures remain errors; test files with identical basenames load independently.
