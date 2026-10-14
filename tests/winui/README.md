# WinUI product tests

This directory is the canonical test surface for app/winui.

- test_*_contract.py: source/architecture/safety contracts.
- test_*_gui.py: test-owned UI automation against built WinUI processes.
- manual_*.py: explicitly human-gated probes.
- helper/: isolated Shell helper contracts.
- m19/ through m23/: retained native fixture directory names; the names are
  historical labels but the fixtures still validate current shared code.
- historical_mfc.py: read-only Git-object access to retired revision cbffb48;
  no MFC working-tree copy is retained.

Default source contracts:

    test.bat source

Source contracts use the Python standard library only. GUI automation additionally
uses exact versions from requirements-gui.txt:

    python -m pip install -r tests/winui/requirements-gui.txt
    python -X utf8 tools/winui/check_python_deps.py --gui

The pinned GUI dependencies were validated with Python 3.14.x on the now-retired
flyExplorer-specific self-hosted Windows runner. Since 2026-10-10, current
Windows jobs are managed through `tngkrwlsmd/personal-control-plane`.
GUI tests require a logged-in, unlocked interactive Windows user desktop;
the controlling SYSTEM service's Session 0 is not a GUI test desktop.
See `docs/operations/windows-runner-retirement.md`.

Legacy %APPDATA%\fxfile\conf files are optional read-only sentinels, not test
fixtures. Tests must work when none of them exist and must fail if they create,
remove or modify a real sentinel. Product processes receive test-owned
APPDATA/LOCALAPPDATA roots.

Default local full stage (Release build + functional GUI only):

    python -X utf8 tools\winui\run_checks.py full

Explicit local Debug + Release build/functional GUI sequence:

    python -X utf8 tools\winui\run_checks.py full --include-debug

Neither command certifies final-pixel visual acceptance or separate hardware,
installer and OS-global gates. Central registered CI with `scope=gui` covers
Release build + functional GUI only; it does not replace the Debug + Release
sequence. Request central acceptance for the exact reviewed `flyExplorer/main`
SHA and registered `project_id=desktop-a` instead of using retired
source-repository Windows Actions workflows.

Focused v7 Window Tab/session acceptance:

    python -X utf8 tools\winui\run_checks.py gui --configuration Release --v7-window-tabs-only

Global clipboard, physical drag and machine-wide install remain separate gates.
