# WinUI product tests

This directory is the canonical test surface for `app/winui`.

- `test_*_contract.py`: source/architecture/safety contracts
- `test_*_gui.py`: test-owned UI automation against the built WinUI process
- `manual_*.py`: explicitly human-gated probes
- `helper/`: contracts for the isolated Shell helper
- `m19/` ... `m23/`: retained native fixture names from migration milestones;
  they are tests, not application source

Run the default source contracts from the repository root with:

    test.bat source

The full owned Debug + Release integration sequence is:

    python -X utf8 tools\winui\run_checks.py full
