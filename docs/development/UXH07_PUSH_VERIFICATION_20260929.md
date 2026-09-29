# UXH-07 feature-branch publication verification — 2026-09-29

This document records the **latest compiled source and owned GUI** verification before publication of `fix/uxh07-named-workspaces-20260928` to its own remote feature branch. It is NOT a merge into `main`, a product release, or certification of untested Windows environments. Earlier status/evidence documents may describe their historical **prepublication** local/uncommitted state; use live Git refs to determine current publication status.

## Exact rebuilt binary and accepted checks

The current `bin/x64/fxfile.exe` at publication-check time has SHA256:
`E3E29B6F79DE34CA57F6B0C817E0200D507911687DB4DAF90B1D56CFA077A086`.

- Re-executed `python build/validate_source_invariants.py` **PASS** and targeted legacy menu/toolbar contract tests **3/3 PASS**.
- Re-executed `local_ci.bat x64` **exit 0**, Release-x64-Unicode compile/link and warning policy PASS; native functional **17 passed / 0 failed**. The default runtime smoke was **SKIPPED** because an existing user HKCU profile must not be modified: exact result **PASS WITH SKIPS**.
- Re-executed **real Windows 11 GUI against this freshly built binary**, with a synthetic profile and owned processes: `test_ui_uxh07_named_workspace_runtime.py --negative --multiple --restart` **exit 0**. Eight malformed workspace fixtures were correctly rejected by native dialogs; two separate named presets were restored independently with different tab layouts; the owned product was closed and restarted and both named workspaces remained independent of Last Tabs. All six original user configuration SHA256 hashes remained identical and the test parent exited 0.
- Additional owned actual GUI `test_ui_uxh07_named_workspace_runtime.py` default Save/Open **exit 0**; `test_ui_legacy_menu_skin_runtime.py` **exit 0** verified Korean Workspaces menu, larger native chevron, dark native toolbar Customize ListBox scrollbars, and real physical wheel top-index movement from 0 to 9. Both checks preserved all six original user-setting hashes.
- Test-owned orphan safety `test_ui_uxh07_orphan_isolated_runtime.py` **exit 0**: stale owner-only temp cleanup, live locked marker protection, external junction/reparse sentinel protection, owned process exit 0, original six SHA256 hashes identical and all owned fixtures deleted.

Ignored local evidence is under `logs/push-verification-20260929`: latest canonical local CI, deep workspace GUI, native legacy menu GUI, owned orphan probe, targeted invariants and appearance contracts. This publication should include **source, test and development documents only**. The untracked `main-window.png` is user-supplied visual evidence and is deliberately **not committed or uploaded**.

## Known limits and branch policy

The scoped UXH-07 functionality and corrected legacy menu/theme were tested in the actual local Windows 11 configuration, not on separate physical 125/150/200 DPI machines, OS High Contrast, full spoken Narrator or all Windows-managed popup paths. Those remain unverified. The old MFC product is not replaced by this feature branch, and the separate WinUI3 prototype lives on another independent branch. Do not merge, trigger GitHub Actions, create a release or change any user's profile from this branch-publication checkpoint.
