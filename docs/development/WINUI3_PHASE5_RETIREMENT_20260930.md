# Phase5 local code retirement (2026-09-30)

Scope: `migration/winui3-full-shell-20260929` only. The protected original MFC `main` worktree is not modified.

## Retired local source and runtime dependencies

The migration worktree no longer carries the obsolete Phase5 proof-of-concept implementations:

- `experiments/phase5_winui3`
- `experiments/phase5_island_bridge`
- the Phase5-only address/island contract and optional-package test
- `dist/copy.bat`'s `FLYEXP_PHASE5_INCLUDE_WINUI` opt-in and all `FlyExplorerIslandBridge`/PRI/WebView2/WindowsAppRuntime staging
- the opt-in `FLYEXP_PHASE5_TEST_ISLAND_DLL` loader, adapter callbacks, message hook, resize/input forwarding and WinApp shutdown hook previously present only in the migration copy of the legacy MFC sources

The five legacy MFC files touched by that island experiment were restored byte-for-byte from the protected MFC `main` worktree because comparison showed their migration-only differences were the retired Phase5 adapter: `main_frame.cpp`, `main_frame.h`, `win_app.cpp`, `explorer_view.cpp`, and `explorer_view_observer.h`. This does **not** edit the real `C:\devlyExplorer` worktree.

The current independent Phase6 preview manifest identity is `FlyExplorerWinUIShell.app`; the obsolete `FlyExplorerWinUI3NavPoC.app` identity is no longer used by Phase6.

## What is deliberately retained

Historical Phase5 design/evidence documents remain tracked. They describe experiments that actually happened and should not be rewritten as current implementation. The remote historical branch `experiments/phase5-productization-20260928` and the previously verified local evidence archive documented in `LOCAL_GIT_WORKTREE_CLEANUP_20260929.md` remain recovery sources. No remote branch is deleted by this retirement.

A new `build/test_phase5_retirement_contract.py` proves that the old local directories and runtime/package hooks are absent and that a stale `FLYEXP_PHASE5_INCLUDE_WINUI=1` environment variable no longer changes native `dist/copy.bat` output. It also keeps a sandboxed transactional native-package smoke test.

## Packaging boundary after retirement

Removing the Phase5 island option does **not** mean that legacy `dist/copy.bat` now packages the new WinUI shell. It returns to native MFC packaging only. The active WinUI implementation remains `experiments/phase6_winui_shell`, whose private copied-Release/lifecycle tests are separate from a signed production installer. A future default-product cutover must introduce an explicit Phase6/production packaging path instead of resurrecting Phase5.

## Acceptance

Before checkpointing this retirement, run the official source preflight, scoped source contracts, native distribution sandbox contract, and independent Phase6 Debug/Release build + owned GUI regression. The protected MFC main worktree must remain clean.

## Verified checkpoint evidence

- Official source preflight PASS. Scoped source contracts: **134 run, OK, 1 environmental skip** (`logs/winui-scoped/20260930-120052-source.log`); this includes the five-test retirement/native-package sandbox contract.
- Fresh independent Phase6 x64 builds after retirement: Debug PASS (`20260930-115423-build-Debug.log`), Release PASS (`20260930-115530-build-Release.log`).
- Fresh full test-owned Phase6 GUI after retirement: Debug PASS (`20260930-115720-gui-Debug.log`), Release PASS (`20260930-115829-gui-Release.log`), including original six user-config SHA256 equality.
- The restored five migration-side MFC files were SHA256/byte compared against the protected `C:\devlyExplorer` copies and all five match exactly. Protected main remains at `cbffb48` with no tracked changes.
- Both local Phase5 source directories are absent. A non-historical source/runtime grep finds no remaining `FLYEXP_PHASE5`, `TestIsland`, `WM_TEST_ISLAND`, `FlyIsland`, or `FlyExplorerIslandBridge` dependency outside retirement guards.
