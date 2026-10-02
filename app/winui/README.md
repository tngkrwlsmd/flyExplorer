# flyExplorer WinUI 3 application

This directory contains the canonical Windows application on main.

## Build and run

From the repository root:

    build.bat Release
    build.bat Debug
    run.bat Release
    run.bat Release D:\

Direct app build is also supported through app\winui\build.cmd.
Generated output stays under ../../out.

Canonical full-build toolchain:
- Visual Studio/MSBuild 18.x;
- MSVC v145 x64 tools;
- Windows SDK 10.0.26100.0.

VS 2022/v143 is not a supported full-build claim. The app, Shell helper, native
fixtures and installer template intentionally use the same v145/SDK contract.

The app restores these direct NuGet inputs:
- Microsoft.WindowsAppSDK 2.5.1
- Microsoft.Windows.CppWinRT 2.0.250303.1
- Microsoft.Windows.SDK.BuildTools 10.0.26100.9169
- Microsoft.Windows.ImplementationLibrary 1.0.260126.7

app\winui\build.cmd verifies the actual restore assets, including the
transitive WinUI/XAML targets, before compiling. No standalone .NET SDK version
is declared by this repository; do not invent one as a prerequisite.

Debug is framework-dependent and therefore needs the matching Windows App
Runtime on the machine. Release is self-contained.

Do not copy flyExplorer.exe alone. The complete out\winui\Release runtime
set is required, including FlyShellIsolationHelper.exe, PRI/XBF resources and
dependent DLLs.

## Current structure

- MainWindow and reusable XAML controls own presentation/orchestration.
- Window Tabs own independent dual-pane workspace state.
- Each pane retains its own folder tabs.
- m19_*.cpp through m23_*.cpp names are retained only to avoid unrelated churn;
  they are current product source, not separate migration products.
- helper/ is the current isolated Shell helper process.
- Assets/ and Strings/ contain app resources.
- shared UI-independent native code lives in ../../src/base.
- tests live in ../../tests/winui and orchestration in ../../tools/winui.

Current architecture and status are documented under docs/development.
