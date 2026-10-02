# flyExplorer current WinUI GUI and visual retest workflow

Use the canonical current product and test-owned fixtures only.

## Automated owned checks

From the repository root:

    python -X utf8 tools\winui\run_checks.py source
    python -X utf8 tools\winui\run_checks.py build --configuration Release
    python -X utf8 tools\winui\run_checks.py gui --configuration Release

For the v7 Window Tab/session slice:

    python -X utf8 tools\winui\run_checks.py gui --configuration Release --v7-window-tabs-only

A GUI PASS must include a normal owned process exit. Do not accept a functional
sentinel followed by a crash exit code.

## Visual comparisons

Use the same revision/binary, Windows build, DPI/scaling, theme, window
dimensions and folder/view fixture.

Capture only synthetic/test-owned paths. Never commit screenshots containing
personal filenames or private desktop content.

## Manual gates

Actual 125/150/200% display scaling, High Contrast ON, human Narrator/Korean
IME behavior and physical pointer drag are separate manual/environment gates.
RDP restrictions or code-level RasterizationScale behavior do not certify them.

## Evidence language

Use PASS, FAIL, NOT TESTED, ENVIRONMENT BLOCKED, or similarly explicit states.
Keep source/compile/runtime/GUI/visual evidence distinct.
