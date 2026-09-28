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

## Verified 2026-09-28 continuation (actual Windows 11, 96 DPI)

The opt-in island now visibly loads its actual WinUI 3 Back, Forward and Up
buttons **inside the real product's MFC MainFrame, in the same process and UI
thread**. Real XAML pointer clicks plus Back→Forward Tab traversal and Enter activation
dispatch the original WM_COMMAND IDs through the unchanged native CommandContext/ExplorerCtrl path.
The native MainFrame remains responsible for the file engine and history.
The child island responds to MFC resizing. Its current folder display is a
TextBlock, NOT an editable path control.

Two failures were isolated experimentally. Attaching a read-only WinUI TextBox
caused XAML load failure and exit access violations even in a plain Win32
diagnostic host; the TextBox was replaced by a read-only TextBlock for the
narrow navigation prototype. Shutting down the Windows App SDK dispatcher
inside the MainFrame destructor stalled the product; the native host now
destroys the island on close and shuts the SDK down from WinApp::ExitInstance,
after MFC's message pump returns. No production navigation engine was changed.

The corrected integration passed an initial strict real-product run and three
more consecutive strict runs; subsequent post-cleanup and UIA-geometry runs
also passed. The original six user-config file hashes matched and the test-owned
process exited 0 on each successful run. Source invariants and native regression
(17/0) passed. Two separate three-pair local benchmark batches sampled native-only versus
native-plus-Debug-WinUI-island startup and memory at 96 DPI; see the evidence
document for scope and measured medians.

Run `build.cmd` here for the isolated Debug|x64 bridge, build the real product
Release-x64-Unicode|x64 separately, then run `python test_owned_product.py`
in an interactive Windows 11 session with the expected private-profile test
prerequisites. The only in-product activation is the explicit
`FLYEXP_PHASE5_TEST_ISLAND_DLL` environment variable set by that test.
Do not use this DLL as a general-purpose component or ship this experiment.

For optional three-pair startup/memory sampling, install `psutil` in the
local Python environment and run `python benchmark_runtime.py`. It also
uses cloned private settings, verifies clean shutdown and never reports a
production-grade performance figure.

Evidence and remaining limitations:
[Phase 5 same-process MFC island evidence](../../docs/development/UI_FRAMEWORK_PHASE5_MFC_ISLAND_EVIDENCE.md).

## Opt-in TextBox isolation (experimental source; runtime NOT YET verified)

The ordinary same-process island still uses a TextBlock and never constructs the
diagnostic TextBox. The new `FLYEXP_PHASE5_DIAG_TEXTBOX` environment variable is
only meaningful together with the existing, explicit test-only DLL activation:
- Unset: original production test path, unchanged.
- `plain`: create a read-only TextBox without additional island resources to
  capture the existing failure under identical initialization and teardown.
- `resources`: merge an explicit `XamlControlsResources` dictionary into the
  island root before constructing the same read-only TextBox. Compare with
  `plain` to isolate whether missing effective WinUI styles/resources matter.

On the connected Windows 11 test PC, incrementally build this experimental DLL
using `build.cmd`, retaining logs locally and inspecting only exit/error summary.
Then, using the existing private-profile test-owned harness:

```powershell
Remove-Item Env:FLYEXP_PHASE5_DIAG_TEXTBOX -ErrorAction SilentlyContinue
python test_owned_product.py
$env:FLYEXP_PHASE5_DIAG_TEXTBOX = 'resources'
python test_owned_product.py
# Only if distinguishing the resource hypothesis is still necessary:
$env:FLYEXP_PHASE5_DIAG_TEXTBOX = 'plain'
python test_owned_product.py
Remove-Item Env:FLYEXP_PHASE5_DIAG_TEXTBOX -ErrorAction SilentlyContinue
```

Both diagnostic modes trace control creation, root/individual Loaded events and
XAML detach. A successful diagnostic must show the TextBox's actual UIA Edit
identity, navigate via existing Up/Back/Forward and Tab/Enter, resize, cleanly
exit 0, and leave the original six configuration hashes unchanged. A mode
that fails must remain **FAIL**; an exception, missing UIA tree, incomplete
cleanup or forced termination cannot be counted as success. Re-run the passing
configuration if the first sample passes to establish stability.

Microsoft's host and control-resource guidance motivates this **hypothesis**,
not a confirmed fix. If `resources` still fails, next inspect the first real
HRESULT/faulting native stack and effective resource/PRI and XAML metadata
availability. Avoid speculative rewrites of the product. No experimental
TextBox code belongs in `main` until the test-owned Windows runtime gate passes.
