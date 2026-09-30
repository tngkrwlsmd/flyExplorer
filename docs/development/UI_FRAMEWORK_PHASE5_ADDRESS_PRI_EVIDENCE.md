# Phase 5 — native-host PRI deployment and editable address adapter (experiment)

> **Historical evidence notice (2026-09-30):** Local Phase5 PoC source/runtime hooks were retired from the active WinUI migration branch. This report is intentionally preserved as evidence of the prior experiment. Recreate source from the retained `experiments/phase5-productization-20260928` branch if needed; do not treat the old local path as a current dependency. See [Phase5 retirement record](WINUI3_PHASE5_RETIREMENT_20260930.md).


Date: 2026-09-28. Branch: `experiments/phase5-address-pri-20260928`.
The experiment is **opt-in only**, not a shipping-product UI migration.

## Scope and implementation

The separately built WinUI 3 Debug-x64 DLL produces
`FlyExplorerIslandBridge.pri`. The reproducible experiment-only
`stage_test_host.py` copies the separately built native flyExplorer
executable, its app-local native DLLs and Languages folder to a fresh
test-owned directory, then puts the generated PRI beside that copied
executable as `resources.pri`. No file is staged in the normal product's
`bin/x64`, an existing PRI is never overwritten, and the test asserts
the staged PRI's SHA256 matches the compiled source. The generated WinUI
App is created only in the explicitly opt-in `app` diagnostic mode.
This proves the previously observed native-host resource discovery layout
in an isolated **unpackaged experimental host**. It does **not** prove
installer/MSIX/portable production resource packaging or fresh-PC deployment.

The experimental DLL exposes `FlyIslandBindAdapter` callbacks. The real
MFC `MainFrame` supplies read-only active-folder retrieval through
`getExplorerCtrl(-1)->getCurPath()` and local-directory navigation through
the same existing active `ExplorerCtrl::explore` and shell PIDL ownership
contract. Both callbacks run synchronously on the existing UI thread,
reject wrong-thread calls, and the navigate callback checks that the
target is an existing local directory. This directly reuses the actual
native navigation engine without rewriting it. It is **not** a complete
shell namespace/address bar adapter or continuous pane-change observer.

The opt-in editable WinUI 3 TextBox initially displays the native
active-folder path, refreshes following island navigation, cancels edits
on Escape and submits the current value on keyboard Enter. A targeted
test-only `FlyIslandPreTranslate` handler selects all when Ctrl+A
arrives with the diagnostic editable TextBox focused. Without this native
host interception, XAML TextBox KeyDown did not receive Ctrl+A and the
initial replacement attempt failed. The handler does not act on normal
non-island startup or unfocused/read-only controls.

## Actual connected-Windows validation

- Experiment DLL: Debug x64 incremental build **PASS**.
- Experimental native product: Release-x64-Unicode | x64 incremental
  build **PASS**. A first attempt wrongly called protected
  `ExplorerView::openFolder`; this was corrected to the public
  `ExplorerCtrl::explore` path. The missing direct C++/WinRT Input
  header, which first caused a linker error, was also corrected before
  the successful DLL build.
- THREE successful full, isolated app-mode GUI regressions at actual
  96 DPI, each checking: generated PRI in copied native host; actual
  editable XAML TextBox; current active-pane folder display; physical
  keyboard Ctrl+A followed by actual short text entry and Escape restore;
  existing real-product Up/Back/Forward, keyboard Tab/Enter, and resize;
  long synthetic absolute target path inserted through UI Automation
  ValuePattern followed by **physical keyboard Enter**, which navigated
  the existing native ExplorerCtrl to the actual target; normal exit
  code 0; SHA256 of all SIX original user settings files unchanged; and
  normal product output directory unmodified by PRI staging.
- Default TextBlock (no diagnostic App/PRI) integration regression:
  **PASS**, exit 0.
- Native functional regressions: **17 passed, 0 failed**.
- Source invariants, Python syntax and diff check: **PASS**.
- GitHub Actions and full installer/clean-PC smoke: **NOT RUN**.

A long (119-character) path sent entirely using the existing
pywinauto keyboard helper previously yielded only 110 characters in
one actual trial. That does **not** establish a product TextBox defect
or complete long-path keyboard reliability. The final passing test
deliberately separates (a) real physical short-string keyboard editing,
Ctrl+A and Escape from (b) exact long-path UIA ValuePattern input plus
a physical Enter command. Do not misreport (b) as full physical
keyboard entry of a long path.

## Main merge gate

**Decision: retain the opt-in test code in the experiment branch.**
The copied-host PRI placement is a repeatable test deployment, not a
normal installer/package deployment contract. The native address
adapter is deliberately limited to existing local directories and
refreshes only when the island drives the tested navigation; continuous
native multi-pane/tab selection updates, Ctrl+A in other focus/context
states, IME, Shell virtual namespaces, drag/drop, actual 125/150/200%
DPI, OS High Contrast, full HKCU isolation, release WinUI DLL and
fresh-machine packaging remain unverified. These are separate gates
before any product-wide or framework decision.

All personal settings used during tests were cloned into ignored,
test-owned fixtures. Original files were hash-compared; those six
hash checks alone are not proof of complete system-state isolation.
