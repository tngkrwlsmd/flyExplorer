# flyExplorer WinUI 3 application

This directory contains the canonical Windows application on `main`.

## Build

Build output is intentionally outside this source directory (`../../out`).

From the repository root:

    build.bat Release
    build.bat Debug

Direct app build is also supported:

    app\winui\build.cmd Release

## Run

Use the repository root wrapper:

    run.bat Release
    run.bat Release D:\

The executable is generated at:

    out\winui\Release\flyExplorer.exe

Do not copy only the EXE. The sibling resources and
`FlyShellIsolationHelper.exe` are required runtime files.

## Structure

- XAML/C++ files in this directory are the application presentation/controller.
- `helper/` is the isolated Shell helper process.
- `Assets/` and `Strings/` are app resources.
- shared UI-independent native code lives in `../../src/base`.
- product tests live in `../../tests/winui`.
- local orchestration lives in `../../tools/winui/run_checks.py`.

Historical milestone evidence is kept under `docs/development`; milestone labels
in a few source filenames are retained only to avoid unrelated churn.
