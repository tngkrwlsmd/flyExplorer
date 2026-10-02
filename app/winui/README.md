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

Do not copy flyExplorer.exe alone. Sibling WinUI resources and
FlyShellIsolationHelper.exe are required runtime files.

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
