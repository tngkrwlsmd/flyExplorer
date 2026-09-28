# Phase 5 product integration: opt-in resource packaging and native pane synchronization

Date: 2026-09-28.
Experimental branch: experiments/phase5-productization-20260928.
Starting experiment: 8aafb7791685ff9b387d8d073af77a696d34b814.
The independent native AddressBar Dark fix on main is a separate change.

## Implemented in this experiment

1. The native ExplorerView navigation and active-tab callbacks notify MainFrame
   on actual native state changes. Native splitter activation also triggers a
   posted address refresh after pane state settles; there is no polling timer.
   The WinUI bridge reads the selected native ExplorerCtrl and invokes its
   existing C++ navigation engine for validated local directories.
2. The editable WinUI TextBox distinguishes pristine focus from genuinely
   modified text. Clean focused addresses follow external native navigation.
   Dirty drafts survive native folder changes; Escape restores the latest
   actual native path. An explicit native-text reference protects against
   delayed programmatic TextChanged notifications being mistaken for edits.
3. TextBox and button callbacks capturing the native bridge object are revoked
   before XAML content detach, preventing callbacks after object destruction.
   The observed earlier 0xC0000005 on shutdown did not recur in the passing
   post-revocation tests; no unique crash root cause was independently proven.
4. For a non-filesystem/Shell virtual location, the new WinUI local-only edit
   is cleared rather than displaying a stale previous filesystem path.
   The original MFC address bar remains available. This fallback has source
   validation, NOT an end-to-end virtual-folder runtime test.
5. build.cmd now supports both Debug and Release x64 WinUI bridge builds.
   The protected owned-host test stage copies the exact built bridge DLL,
   generated resources.pri and the matching WindowsAppRuntime bootstrap and
   WebView2 native companion DLLs into a fresh disposable host. No ordinary
   product binary directory, user profile or existing resource index is
   overwritten.
6. dist/copy.bat has an explicit experimental x64-only opt-in flag
   FLYEXP_PHASE5_INCLUDE_WINUI=1. It preflights generated Release outputs
   BEFORE staging, rejects an existing host resources.pri, and transactionally
   adds the bridge, PRI and two native companions only to x64. By default it
   continues to omit WinUI files. The ordinary product itself activates its
   test bridge only under its separate explicit DLL environment flag.

## Executed evidence on the connected Windows 11 machine, actual 96 DPI

- Release-x64-Unicode native product incremental build: PASS.
- Debug x64 and Release x64 WinUI bridge builds with compiled PRI: PASS.
- Pre-refinement real test-owned GUI: THREE consecutive Debug app-mode
  native-event and in-progress-draft tests PASS, plus a separate default
  TextBlock island regression PASS. Original six settings hashes remained
  unchanged; each test-owned child exited 0.
- Pre-refinement real Release app-mode: THREE consecutive synthetic local
  directory tests passed native tabs, a 1x2 multi-pane split and pane
  previous/next switching, invalid local path rejection, active path display,
  native folder callbacks, Ctrl+A, Escape, pointer/keyboard navigation,
  native address Enter and clean shutdown. The release bridge and PRI loaded
  from a disposable native-host directory with its native dependencies.
- After refining pristine-focus handling and delayed TextChanged logic:
  PASS after the final native-text-reference refinement: the Debug opt-in
  app-mode real-product GUI passed focused-but-clean native refresh, dirty
  draft preservation, Escape/latest-path handling and clean owned shutdown.
  The Release app-mode GUI also passed those paths, invalid-path rejection,
  original/native tab switching and split multi-pane navigation; two further
  independently verified full Release runs passed the same conditions and
  original six SHA256 settings checks. The default Release TextBlock island
  passed its separate regression with normal exit 0.
- Release performance: THREE paired native/WinUI runs against equivalent
  disposable Release host contents (same compiled executable, stage and DPI).
  Median native: 43.04 MiB RSS, 9.82 MiB private, 1.043s to visible frame.
  Median WinUI App/TextBox: 88.30 MiB RSS, 27.20 MiB private, 1.115s to
  visible frame. Observed median differences: +45.26 MiB RSS, +17.38 MiB
  private, +0.072s to visible frame. This is a six-process local sample,
  not a formal system-wide performance guarantee; XAML root became ready
  after the main frame in island mode.
- The isolated Windows batch-package contract runs passed FOUR cases:
  default native stage unchanged; opted-in x64 Release DLL, PRI and
  companion staged; existing native PRI refused without destroying the
  prior package stage; and missing opt-in dependency refused before
  destroying prior stage.
- Final native functional suite: 17 passed / 0 failed.
- Python syntax, source invariants, native address/callback source
  contracts, and the FOUR isolated package-stage scenarios: PASS.
  Original test-owned app-mode product exits were 0, all original
  six user-setting hashes remained unchanged and the regular native
  source bin/x64 directory received no test PRI or bridge DLL.

## Important open issues and deployment boundaries

Long absolute-path key injection is NOT VERIFIED: in an isolated 119-char
synthetic path both default Unicode-packet and rate-limited native-key
pywinauto injection yielded 110 characters. A diff showed precisely the
nine backslash separators missing. The tool's key parser itself represents
each separator as an event, but tests have not determined whether the
failure occurs in automation, native MFC message routing or XAML text
translation. A comparative normal MFC Edit automation probe was inconclusive
because its Win32 automation attach failed; it does not establish a root
cause. Earlier short-string keyboard editing and UIA ValuePattern setting
of the exact long path plus physical-key simulation of Enter did pass.
Do not treat UIA ValuePattern as proof of a physically typed long path.

Clipboard paste with exact global user-state preservation, Korean IME
composition, Shell virtual-folder GUI fallback, High Contrast on the OS,
actual 125%/150%/200% DPI, drag and drop, missing-WindowsAppSDK-runtime
machines, complete HKCU side-effect isolation, dependency redistribution
license review and clean-machine installer/uninstaller tests are NOT TESTED.
The opt-in batch package script has only isolated transaction tests, not
a real signed NSIS installer or an end-to-end installed-app smoke.

## main merge decision

B (user-enabled WinUI feature): HOLD because long keyboard path entry,
real installer/runtime prerequisites and cross-environment GUI integration
gates remain open. A (test-only default-disabled source): also HOLD for
now rather than adding unfinished diagnostics and extra ABI/deployment
obligations to the canonical native product. Preserve proven changes
on the named experimental branch, keep independently validated MFC UI
improvements on main, and revisit only after the required gates are tested.
Neither GitHub Actions nor a production package installation was triggered.
