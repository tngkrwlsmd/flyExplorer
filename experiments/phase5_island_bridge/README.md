# Phase 5 same-process MFC / WinUI 3 island experiment

This experiment is opt-in and test-only. The real flyExplorer MFC MainFrame loads
FlyExplorerIslandBridge.dll only when FLYEXP_PHASE5_TEST_ISLAND_DLL names that exact
DLL. Normal product startup is unchanged when the variable is absent.

The DLL initializes the pinned Windows App SDK runtime, creates a real
DesktopWindowXamlSource on the existing MainFrame UI thread, and exposes WinUI 3
Back, Forward, and Up buttons. Those buttons send the existing native WM_COMMAND
IDs directly to the same-process MainFrame, so routing continues through the
product's real CommandContext and ExplorerCtrl.

test_owned_product.py uses a private copy of six user UI configuration files,
disables cloned side effects, starts a test-owned product process, validates that
the XAML controls live in the same PID, invokes navigation, resizes the real MFC
window, checks clean shutdown, and verifies original config hashes are unchanged.

This is not production integration. The temporary island is an overlay and does
not yet implement full focus traversal, editable address state, active-pane state,
Shell drag/drop, DPI/High Contrast coverage, packaging, or installer behavior.
