# Phase 5 — same-process MFC / actual WinUI 3 island evidence (2026-09-28)

## Scope and implementation boundary

This is a **test-only**, explicitly enabled experiment on the connected Windows
11 development PC. The existing flyExplorer C++ engine remains unchanged.
An opt-in DLL is loaded into the **actual product process** and creates real
WinUI 3 XAML controls in a DesktopWindowXamlSource owned by its existing MFC
MainFrame on the same UI thread. Button handlers send allowlisted, scalar
WM_COMMAND IDs 32004 (Up), 32006 (Back), 32007 (Forward) to that actual HWND.
MainFrame::OnCmdMsg dispatches them through the existing command system to
ExplorerCtrl. This verifies native **command reuse**, not a direct ExplorerCtrl
C++ library link or complete active-pane state integration.

The test DLL uses the pinned Windows App SDK 2.5.1 framework, native NuGet
restore, isolated build cache and an explicit opt-in environment variable.
The real application has no normal-startup dependency on the experiment DLL.
Its temporary island is an overlay, not a replacement for production panes,
tabs, saved toolbar geometry or the existing address editor.

## Actual verification on the connected Windows 11 PC

| Check | Result and boundary |
| --- | --- |
| Experimental DLL Debug x64 / actual product Release-x64-Unicode x64 | Both compiled and linked; existing MSB8029 build directory warnings remain |
| Same PID, same UI-thread-hosted MFC child / actual XAML UIA buttons | PASS in an explicitly test-owned real product |
| Existing product Up / Back / Forward navigation | PASS via pointer activation and native command return/title trace |
| WinUI button focus, native MFC resize and responsiveness | PASS at actual 96 DPI using UIA-derived button bounds |
| Product exit and XAML resource teardown | PASS, exit 0, no forced process stop in corrected tests |
| Original six personal UI config files (SHA256) | Identical before and after each isolated run |
| Source invariant preflight | PASS |
| Actual product native functional regressions | 17 PASS, 0 FAIL |
| Full default local CI / installer / fresh machine | NOT RUN |

An initial strict same-process integration PASS was followed by three
consecutive additional PASS runs. After removing unused prototype sources
and rebuilding the experiment DLL, a strict PASS was obtained again;
the last updated UIA-geometry test also passed. These successful runs
span minor test-harness/source cleanup revisions. The latest test directly
checked actual WinUI UIA button identities and real pointer click positions;
its real host DPI was 96. Separate native-only and island-enabled processes
also exited 0 in three additional *paired* isolated sampling runs.
All checks used cloned private settings and synthetic filesystem fixtures.
Matching six SHA256 hashes do not prove complete HKCU or system-state isolation.

## Failure isolation and lifecycle correction

The earlier prototype created a real island child HWND but did not load the
expected XAML control tree; closing it produced access violation 0xC0000005.
A separately compiled *plain Win32* host reproduced the fault using the same
DLL without flyExplorer or MFC. Controlled trials showed that a TextBlock
alone, then a TextBlock with a Button, both loaded and exited 0, whereas
adding even a fresh read-only TextBox prevented XAML loading and crashed
during cleanup. The read-only current-folder display was therefore replaced
with a TextBlock. The underlying TextBox activation cause is **unresolved**;
this is not a claim that WinUI 3 TextBox is universally defective.

A second, independent failure remained after native navigation worked:
destroying the SDK DispatcherQueue from MainFrame's destructor stalled
process exit. The island is now detached before the native owner closes;
the Windows App SDK dispatcher, bootstrap and owned runtime references
are released from WinApp::ExitInstance **after the MFC message loop exits**.
The observed real product and plain Win32 test both then exited cleanly.
The experiment still retains the opt-in DLL mapped until process exit.

## Bounded local startup and memory comparison

Two independent batches of three paired sequential runs each used the
**same experimentally rebuilt native product binary**, first with no island,
then with the Debug-x64 DLL enabled.
Each ran with fresh cloned settings, private APPDATA and a synthetic folder.
First visible, correctly titled product MainFrame was the startup endpoint.
RSS and private bytes were sampled about 0.8 seconds after window readiness.
Each batch reports the median of only three runs, not representative
production benchmarks, and the extra island DLL was **Debug**, not Release.

Batch A (initial three paired runs):

| Measurement | Native only | Native + WinUI 3 island |
| --- | ---: | ---: |
| First visible product frame | 0.570 s | 0.649 s |
| Process working set (RSS) | 42.01 MiB | 77.93 MiB |
| Process private memory | 9.86 MiB | 20.11 MiB |
| Island XAML root loaded | n/a | 0.730 s |

Batch B (portable rerun of the checked-in benchmark script, three more pairs):

| Measurement | Native only | Native + WinUI 3 island |
| --- | ---: | ---: |
| First visible product frame | 0.650 s | 0.655 s |
| Process working set (RSS) | 42.16 MiB | 78.20 MiB |
| Process private memory | 9.79 MiB | 20.30 MiB |
| Island XAML root loaded | n/a | 0.739 s |

The island used 35.92 / 36.04 MiB more RSS and 10.25 / 10.51 MiB
more private memory in batches A / B, respectively. The frame-visible
median difference changed substantially between batches (+0.079 s
versus +0.005 s), so no stable startup slowdown has been established.
OS caching, process startup variability, the Debug DLL, selected user layout
and runtime installation limit comparison.
Do not extrapolate to shipping memory usage, responsiveness or total lifetime
cost. DPI was 96 and all six original UI-config hashes stayed unchanged.
Local test evidence is under ignored logs/phase5; user layout screenshots and
private configuration data were not committed.

## Framework viability: evidence versus remaining risk

| Approach | Established by this phase | Missing before a decision |
| --- | --- | --- |
| Incrementally improve MFC | Original command system and functional regression suite remain reusable; no additional WinUI runtime in the native-only baseline | Full Windows 11 visual, drag/drop, DPI/HC and long-term MFC painting cost comparison |
| MFC with selective WinUI islands | Actual same-process UI, real command reuse, focus, resize and scoped clean lifecycle work at 96 DPI | TextBox/address editing, real active-pane bidirectional state, native Shell, theme, actual other DPIs/HC, runtime packaging and lifecycle/update costs |
| Full UI migration | Separate independent WinUI navigation prototype exists in Phase 5 history | Real ExplorerCtrl embedding, full tabs/panes/file operations, settings conversion, deployment, rollback and measured engineering effort |

There is **no evidence-based framework migration verdict** yet. The minimum
next experiment is to isolate the DLL's TextBox fault with valid WinUI
resource/PRI initialization, then validate editable address and real active-
pane read-only state without changing the proven native engine. Keyboard
Tab traversal, pointer edge cases, DPI/HC, drag/drop and packaged deployment
need their own tests before selective integration reaches production.

Validated commands, for the **experiment branch only**:
- `experiments/phase5_island_bridge/build.cmd` (Debug x64 DLL)
- existing VS2026 solution Build, Release-x64-Unicode / x64 (actual product)
- `python build/validate_source_invariants.py`
- `bin/x64/fxfile-functional-tests.exe` (17/0)
- `python experiments/phase5_island_bridge/test_owned_product.py`
- optional: `python experiments/phase5_island_bridge/benchmark_runtime.py`
  (requires locally installed `psutil`; three paired private-profile samples)
GitHub Actions were **not** dispatched. The full `local_ci.bat x64` profile,
installer, clean PC, complete HKCU, 125/150/200% DPI and actual OS High
Contrast remain unverified.
