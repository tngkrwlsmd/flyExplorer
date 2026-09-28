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
| WinUI button pointer focus, Back→Forward Tab traversal, Enter activation, native MFC resize and responsiveness | PASS at actual 96 DPI using UIA-derived button bounds |
| Product exit and XAML resource teardown | PASS, exit 0, no forced process stop in corrected tests |
| Original six personal UI config files (SHA256) | Identical before and after each isolated run |
| Source invariant preflight | PASS |
| Actual product native functional regressions | 17 PASS, 0 FAIL |
| Full default local CI / installer / fresh machine | NOT RUN |

An initial strict same-process integration PASS was followed by three
consecutive additional PASS runs. After removing unused prototype sources
and rebuilding the experiment DLL, a strict PASS was obtained again;
the last updated UIA-geometry test also passed. These successful runs
span minor test-harness/source cleanup revisions. The latest test directly checked actual WinUI UIA button identities, real
pointer click positions, Back→Forward Tab traversal and Enter activation;
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

## Initial TextBox failure isolation (historical, before host PRI staging)

The dedicated `experiments/phase5-textbox-isolation-20260928` branch adds
explicitly opt-in `plain`, `resources` and `app` diagnostic modes. Ordinary
startup leaves the proven read-only TextBlock island unchanged.

On the connected Windows 11 machine, the diagnostic DLL's incremental Debug x64
build passed. A normal same-process MFC/WinUI 3 baseline passed with native
navigation, keyboard Tab/Enter, clean exit 0 and all six original config SHA256
hashes intact after the diagnostic changes. Three distinct opt-in trials showed:

| Trial | Direct runtime result | Interpretation |
| --- | --- | --- |
| Plain read-only TextBox | Child HWND visible but real XAML buttons/UIA tree missing; product exited `0xC0000005` in teardown | Reproduced earlier failed load/cleanup; not a pass |
| Direct root `XamlControlsResources` | Fails before TextBox construction, `0x80004005` / `AcrylicBackgroundFillColorDefaultBrush` missing; product itself exits 0 | Root-local resource merge alone is insufficient |
| Generated WinUI App + `InitializeComponent()` | Fails before island creation with `0x802B000A` XAML parse error; product itself exits 0 | Generated app resource activation also fails in existing host |

Every diagnostic returned **test FAIL**; original six configuration hashes
remained unchanged even when the owned product crashed. Generated project
outputs contain `FlyExplorerIslandBridge.pri` beside the DLL, while the
generated App code requests `ms-appx:///FlyExplorerIslandBridge/App.xaml`.
The current DLL host does not provide demonstrated working application-level
resource/metadata registration for WinUI controls with richer templates.
Missing effective XAML resources/metadata is the leading integration boundary,
**not yet a proven complete root cause**. It is not evidence that TextBox is
universally broken in WinUI 3. See the Windows App SDK
[islands sample](https://github.com/microsoft/WindowsAppSDK-Samples/tree/main/Samples/Islands)
and [hosting guidance](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/host-controls-existing-desktop-apps).

**Merge decision:** no experimental TextBox changes to `main`. Keep the
independently validated normal island baseline and the crash-isolation modes
on experimental branches. A subsequent focused experiment must establish
proper generated XAML/PRI resource registration in a native host before
rerunning read-only/editable TextBox, UIA input, repeated clean shutdown and
user settings preservation. Do not infer other-DPI or installer readiness.

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
pane read-only state without changing the proven native engine. Broader keyboard traversal/accelerators, pointer edge cases, DPI/HC, drag/drop
and packaged deployment need their own tests before selective integration
reaches production.

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

## Verified opt-in native-host PRI staging (2026-09-28)

Following the initial failure modes above, makepri dump confirmed the
bridge's DLL-output FlyExplorerIslandBridge.pri embeds App.xbf under the
FlyExplorerIslandBridge resource map, while generated App.xaml.g.h requests
ms-appx:///FlyExplorerIslandBridge/App.xaml. Direct root-local resources
and generated App initialization WITHOUT native-host PRI both failed.
By contrast, temporarily staging that same compiled PRI as resources.pri
beside the experimental native host executable BEFORE constructing its
generated WinUI App made the same read-only TextBox load and exit cleanly.

The experiment subsequently made only the app-mode test TextBox editable
and equipped test_owned_product.py to stage the PRI with pre-existing-file
refusal, matching SHA256 verification and guaranteed verified-copy cleanup.
No default product path stages a PRI or loads the diagnostic App.

The incremental Debug-x64 DLL build passed. THREE consecutive full
test-owned app-mode runs passed at actual 96 DPI: a real WinUI TextBox UIA
Edit control; UIA-clearing the synthetic initial text followed by real
keyboard typing and exact UIA value Phase5-Input-20260928; existing
Up/Back/Forward pointer navigation and Back/Tab/Forward/Enter keyboard
path; MFC island resize; product exit zero with no forced termination;
unchanged hashes of all six original user config files; and complete
removal of the temporarily staged host PRI after EACH test. The separate
normal TextBlock-island regression also passed. Python syntax and source
invariants passed. The native product engine and executable were
unchanged during this focused experiment.

This is direct evidence that the observed native-host resource-location
gap plus generated XAML App initialization caused the previously blocked
control-load path in the tested environment. The historical plain and
direct-resource modes still fail without that combination. This does
not prove that simply shipping a DLL-private PRI works on other hosts.

A separate initial Ctrl+A attempt did not replace the original TextBox
content, so full keyboard editing and shortcut routing remain OPEN;
the passing physical typing check intentionally clears a synthetic field
with UIA first. Editable native address commit/cancel, live active-pane
state, formal shipping resource deployment, full HKCU isolation,
higher DPI/OS High Contrast and clean-machine reproducibility remain
NOT TESTED. Merge decision: retain experimental product integration
and diagnostic code off main. This evidence may inform a future
safe resource-packaging and native address-adapter implementation.
