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
