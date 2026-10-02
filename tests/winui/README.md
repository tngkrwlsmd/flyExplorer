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

The pinned GUI set was validated on the project self-hosted Windows runner with
Python 3.14.x. GUI tests require an interactive Windows desktop/session.

Legacy %APPDATA%\fxfile\conf files are optional read-only sentinels, not test
fixtures. Tests must work when none of them exist and must fail if they create,
remove or modify a real sentinel. Product processes receive test-owned
APPDATA/LOCALAPPDATA roots.

Full owned Debug + Release sequence:

    python -X utf8 tools\winui\run_checks.py full

Focused v7 Window Tab/session acceptance:

    python -X utf8 tools\winui\run_checks.py gui --configuration Release --v7-window-tabs-only

Global clipboard, physical drag and machine-wide install remain separate gates.
