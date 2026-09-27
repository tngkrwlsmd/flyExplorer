# Phase5 WinUI 3 template build and runtime checkpoint, 2026-09-28

This is an INCOMPLETE experiment, NOT a navigation implementation or product integration. Official Windows App SDK 2.5.1, C++/WinRT, BuildTools, WIL and transitive dependencies (17 package folders) were restored using official nuget.org into the ignored worktree-local logs cache. The authentic installed VS2026 C++/WinUI 3 XAML template compiled and linked. A real WinUIDesktopWin32WindowClass top-level window appeared in the development PC and its isolated process closed with exit 0. No extra Visual Studio workload or global Windows runtime was installed.

Build instructions: run build.cmd. Package versions are pinned in this project; official NuGet.Config source is local to this directory. WARNING: VS2026 MSBuild 18 currently fails its ResolveNuGetPackageAssets target because the build selects UAP v10.0 while the C++ PackageReference graph restores native v0.0. TargetFramework uap10.0 did not change the restored graph. The experiment compiled only when using its already generated package imports and temporarily disabling the separate NuGet asset resolution target with /p:ResolveNuGetPackages=false. This is NOT a production-grade build fix. Investigate and repair proper reproducible NuGet resolution before any integration or deployment decision.

The current true WinUI 3 template contains a BLANK XAML Grid. WinUI Back/Forward/Up buttons, path edit, input tests, real ExplorerCtrl/CommandContext adapter, comparative cost measurements, 125/150/200% DPI and actual OS High Contrast are not tested. Use a separate next bounded task to implement and validate these. Existing flyExplorer product code, user settings, SDK installation and GitHub main remain untouched.

# Phase 5: true WinUI 3 navigation prototype

Experimental project created from the already-installed Visual Studio 2026 C++/WinRT single-project template. Unlike the Phase4 native Win32 proof, this project references the **real Microsoft.WindowsAppSDK 2.5.1 / WinUI 3 XAML runtime**. Target: x64, unpackaged, framework-dependent. It has no flyExplorer product project reference and must not be treated as production integration.

Dependencies: official NuGet packages pinned in the vcxproj and scoped official nuget.org source in NuGet.Config. All downloads and builds in this experiment should set NUGET_PACKAGES and NUGET_HTTP_CACHE_PATH to ignored local logs/phase5; no Visual Studio components or machine runtimes are installed by restore. A framework-dependent unpackaged app requires a compatible preinstalled Windows App Runtime.

Status: build and live GUI checks must be recorded, not assumed. Later revisions implement the navigation controls and explicitly separate the independent in-memory state proof from any real product ExplorerCtrl/CommandContext adapter.

Do not use this experiment to alter user's global DPI, High Contrast, HKCU, private flyExplorer settings or the real product UI.
