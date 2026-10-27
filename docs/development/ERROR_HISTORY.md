# Error history

## 2026-10-27 — G01 public PDB valid through DBI age and actual DbgHelp loader; deferred callback stack resolved

- [Scoped Windows run #40453770619](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40453770619) on the retained 2.5.1 app-local DLL hash showed PDB Info Age=3 but **DBI Age=1** matching PE Age=1; DbgHelp accepted official PDB as `SymType=3`, `PdbAge=1`, `PdbUnmatched=False`. The earlier strict `resolve_local_rva.py` Info-stream-only GUID/Age comparison rejected this public PDB before calling the OS loader. This was a **diagnostic validation false negative**, not evidence that the downloaded PDB was unrelated.
- All 14 `CoreMessagingXP.dll` RVAs in the previously captured 15-address stack prefix now resolve to public symbols. The upper frame is `DispatcherQueue::DeferInvokeCallback+104`; further frames include `MessageSession::Callback_InvokeDeferInvoke`, deferred dispatch and `UserAdapter::WindowProc`. These are **candidate cross-build symbolic names**, not confirmation of a culprit user callback or a fixed app. The COMBASE stored origin/frame is not yet symbolized. Original crashing DLL was not archived; G01 OPEN.
- Cleanup: bounded probe scratch removed and exact control-plane request slot returned to `idle` [`bf578c358df0`](https://github.com/tngkrwlsmd/personal-control-plane/commit/bf578c358df01adb1f703b1439e78c40f9e6d061). No fresh Release build, GUI, source edit or dump produced.


## 2026-10-27 — G01 candidate CoreMessaging PDB identity obtained, app-local binary equivalence still unverified

- Installed X64 WindowsAppRuntime.2 `2.5.1.0` `CoreMessagingXP.dll` candidate PE probe **PASS** [#40450004069](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40450004069): PDB GUID `00d48158-b4de-ee9c-4f3d-e210b378d2b1` age `1`, PE timestamp `1CFF1018`, SHA-256 `049A1379592513D05BADA39D43A46124833C2E5F6EC2EEC299927339E12D57DF`. No match claim against the actual crash-time app-local CoreMessaging DLL.
- One exact-source isolated `build.bat Release` attempted to hash the app-local DLL [#40450249499](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40450249499) **FAIL** at NuGet restore; dependency packages were unavailable from `api.nuget.org`. No binary identity comparison performed, no GUI retest. Bounded owned scratch was removed and Windows Remote Shell request returned to `idle`. Retain prior central Release PASS evidence; retry this clean build only after concrete dependency restore recovery/preflight.
- Loaded module origin remains exactly app-local only from the last real G01 fatal GUI #40449178219. Root caller and G01 correction remain OPEN; L08 OPEN, G03–G05 excluded, G07 stopped.


## 2026-10-27 — G01 crash-time CoreMessagingXP.dll is app-local only; observed crash #8/12

- [Owned interactive Release diagnostic #40449178219](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40449178219) used exact source `f87ee07883313de28e8ecbf0534e97f732ec4ea5`: seven normal exits followed by eighth `full` crash `0xC000027B`, early stop, no App destructor entry. **All 8 verified test-owned processes** mapped precisely one `CoreMessagingXP.dll` from the app-local Release directory, **zero** from WindowsApps, System32 or other. This contradicts a simultaneous mixed app-local/framework CoreMessaging image explanation in the observed owned process, without ruling out distinct code or runtime ownership defects.
- Crash record again `HRESULT 0x800710DD`, `COMBASE+0x5CF34` origin and fifteen captured frame-module RVAs beginning `COMBASE+0x5DE97` / `CoreMessagingXP+0x97968` / `+0x42F8D`. The repaired central regex reports `WORDS_16`, `STACK_TRUNCATED`, `MAPPED_15` (cap of 16 retained words, not entire stack size). Root caller remains unknown, no `FLY` frame within retained prefix. No raw dump or process memory exported; G01 and L08 remain OPEN.
- Read-only OS preflight earlier [#40448525069](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40448525069) confirmed System32 has no CoreMessagingXP.dll; one installed WindowsAppRuntime.2 2.5.1 X64 framework package provides a **candidate**, not the exact loaded app-local binary. Continue with verified PE/PDB identity before attempting symbol resolution.


## 2026-10-27 — G01 first real stored module-RVA call prefix captured, 15 addresses, shutdown still fails

- [Interactive Release #40447398090](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40447398090): exact `4951369a8ff182e4ba7cf45e7acd6136daf7dd35`, Release build PASS. Owned matrix `plain/full/plain/full` ended `0x0/0x0/0x0/0xC000027B`, stopped at case 4 of maximum 12. One saved SE02 HRESULT `0x800710DD`, binary form, origin `combase.dll+0x5CF34`, captured first 15 allowlisted module-relative frame addresses: first `combase.dll+0x5DE97` then `CoreMessagingXP.dll+0x97968`, `+0x42F8D`, `+0x47096`, `+0x4E910` and additional CoreMessaging addresses. No app frame within this bounded prefix; this does not establish the responsible caller or source line. No raw dump, memory pointers or sensitive paths exported.
- Central output had a separate regex prefix bug (`WORDS_1`/`MAPPED_1` not valid full counters); repaired with a source-contained two-digit regression by [control commit `add0848146727395cdb06e22655ce9c57f1a0276`](https://github.com/tngkrwlsmd/personal-control-plane/commit/add0848146727395cdb06e22655ce9c57f1a0276), not yet fully quality-confirmed at this document checkpoint. Previous owned run [#40446485192](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40446485192) 4/4 clean is only intermittent clean evidence; G01 remains OPEN. A single test-owned, no-symbol-download preflight of Windows `CoreMessagingXP.dll`/`combase.dll` PE identities is queued. L08 remains OPEN; G03–G05 excluded; G07 paused.


## 2026-10-27 — G01 COMBASE origin RVA observed, invalid trace classification in older 16-frame-limited observer

- [Exact-source interactive Windows diagnostic #40443865784](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40443865784) produced `0x0/0x0/0x0/0xC000027B` after Release build PASS on `d97d50db24379bc4beb4bbc5778f3ce1e9186742`. The fourth case recorded `G01_DEBUG_STOWED_0_HRESULT_800710DD`, `FORM_BINARY`, `STACK_INVALID`, `ORIGIN_COMBASE_0005CF34`. The original backtrace still was not collected. COMBASE+RVA is not a symbolized call stack.
- **Confirmed diagnostic-code limitation:** the tested revision's `decode_v2` classifies any `StackTraceWords>16` as invalid; that conflates a safe read cap with invalid Windows data. Current main [`270eaa5b563394110c732ef408ca1af2818f0a00`](https://github.com/tngkrwlsmd/flyExplorer/commit/270eaa5b563394110c732ef408ca1af2818f0a00) clamps valid traces to the first 16 entries and marks truncation instead of dropping them. G01 targeted Windows contracts **7/7 PASS** plus syntax [#40446458254](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40446458254); source-limited GUI rerun [#40446485192](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40446485192) is not yet a completed result at this checkpoint.
- Installed Microsoft WinDbg remains available; not yet used to obtain the actual caller. G01 OPEN, L08 OPEN; G03–G05 excluded; G07 paused.


## 2026-10-27 — G01 stored WinRT error `0x800710DD` obtained under exact-owned external debugger

- [Interactive Release run #40442357459](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40442357459) built `fe95bc0ca8e33242b49b285de68117398e043b43` (exit 0), ran owned `plain/full/plain/full`, and ended `0x0/0x0/0x0/0xC000027B`. The last case's debugger recorded exactly one `C000027B` SE02 ResultCode **`0x800710DD`**, `HRESULT_FROM_WIN32(ERROR_INVALID_OPERATION)` (4317), with no allowlisted backtrace frames. Unlike the earlier vectored probe, the external debugger reached the fatal exception record. No causal function, WinUI task or application API can yet be inferred from the generic HRESULT.
- Installed Microsoft WinDbg `1.2610.1001.0` in the verified interactive Windows user via official WinGet; [installation verification #40443287834](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40443287834) PASS, one-shot task and scratch cleaned. No permanent global WER setting or dump. The follow-up `d97d50db24379bc4beb4bbc5778f3ce1e9186742` records SE02 form, declared stack-word count, allowlisted origin and frame mapping to discriminate an absent binary trace from a text-form exception; Windows source contracts 6/6 and Python syntax PASS [#40443505202](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40443505202). The new live matrix is requested but its result is not evidence at this time.
- G01 **OPEN** / L08 **OPEN**; G03–G05 excluded / G07 stopped.


## 2026-10-27 — G01 stowed Release crash reproduced despite vectored observer; native inner error remains unavailable

- At exact `flyExplorer/main` `3e0efd8ad4e4dbc74908c4fe0a079dacbdd1d69c`, the interactive central `gui-g01-shutdown` scope ([run #40438475916](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40438475916)) compiled Release once (PASS) and executed `plain/full/plain/full` on the same binary: native exits `0x0/0x0/0x0/0xC000027B`. The final `full` fixture completed, owned `WM_CLOSE` was posted and its profile/fixture guards passed; `WINDOW_CLOSED_EXIT` appeared, but `APP_DESTRUCTOR_ENTER` and all `NATIVE_STOWED_*` observer tokens were absent. The GitHub Actions green status reflects **diagnostic completion**, not product G01 acceptance.
- A distinct read-only Event 1000 check ([run #40440479370](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40440479370)) found one matching 2026-10-27 02:31:11 UTC `flyExplorer.exe` event: `CoreMessagingXP.dll`, `0xC000027B`, RVA `0x97976`. This agrees with one historical final crash signature but does not reveal the originating HRESULT or native stack.
- Microsoft documentation specifies that `RaiseFailFastException` bypasses vectored handlers. An unobserved `0xC000027B` therefore cannot disprove a real stowed WinRT failure; the exact fatal path is unconfirmed here. Future diagnosis should use an explicitly scoped crash-time debugger/stowed-array read rather than treating failed in-process observers as causal fixes. No debugger was attached, dump captured, OS setting changed or product code modified in this investigation. Central VM request slot restored to `idle`; G01 and L08 remain OPEN.


## 2026-10-26 — G01 parser stage ambiguity narrowed in source, no Windows validation

- The 2026-10-25 direct Windows run [#40240026806](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40240026806) finished with `LOCAL_SYMBOL_LOOKUP_FAILED / ValueError` after downloading the full public PDB and successfully removing its test-owned temporary folder. The exact failure stage **cannot** be retroactively recovered from the coarse error; do not attribute it to WinUI or assume the public PDB's GUID is incorrect.
- A source-only change to `tools/winui/resolve_local_rva.py` now identifies fixed, path-redacted failure categories for PE header, PE RSDS, PDB MSF7 parser and GUID/age checks. New synthetic portable `tests/winui/test_g01_symbol_preflight.py` covers six success/failure contracts, but those tests **have not been run** against the committed code. This protects subsequent investigations from needlessly redownloading a 293MB PDB just to classify an unrecognized `ValueError`.
- Source review of `inspect_release_symbols.py` identified a deliberate one-block PDB directory-map limit, consistent with the documented MSF7 block-map indirection. Whether that limit was encountered by the historical PDB is **unverified**. No speculative parser rewrite or renewed download was made.
- Prior blocked Windows probe remains a safety boundary; no substitute tooling, user-data access, registry changes, native dumps, unrelated GUI validation or product fix. G01 remains unresolved; continue only through a permitted, reviewed evidence path.

## 2026-10-26 — G01 public PDB download completed; pre-symbol ValueError, cleanup succeeded

- Resume checkpoint: exact prior [Windows Remote Shell Direct #40240026806](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40240026806) / control request commit `6fb10ea323984f13ca54553aa6f1a21350b2f665` actually **completed with failure**, not in progress. Microsoft public `Microsoft.UI.Xaml.pdb` download reached **292,835,328 bytes** (matching the previously returned HEAD Content-Length). The local RVA resolver returned `{"status":"LOCAL_SYMBOL_LOOKUP_FAILED","error":"ValueError"}`; it did not name a faulting function. The failure originated from a validation/parser ValueError before a successful function-name lookup; the sanitized error prevents identifying the specific rejected condition. Do not assume a wrong public PDB, an unsupported PE format, or an app defect from this result.
- The remote script's `finally` confirmed `G01_TEMP_SYMBOLS_CLEANED=YES`, before the runner reported the nonzero action result. The temporary 293MB symbol download was **not retained**; no memory dump, debugger install, registry edit, native app run or Windows GUI was performed. Retrying the same 293MB download without a preflight change is unjustified.
- Added diagnostic-only `--probe-module` to `tools/winui/resolve_local_rva.py` on product commit [`86aed2e878bc7da0d110614259fcccc6dd7ce4eb`](https://github.com/tngkrwlsmd/flyExplorer/commit/86aed2e878bc7da0d110614259fcccc6dd7ce4eb). It checks the local PE x64 header, expected COFF timestamp and CodeView identity independently of any PDB download, process attach or symbol-server access; without exact DLL preflight a 293MB download should not be repeated. The option has **not** been executed on Windows.
- A proposed bounded `windows-vm` read-only preflight request was **blocked by the tool safety inspection** before GitHub submission. No alternate execution path, policy bypass or second attempt was used. The previous completed request slot had already been restored to inert `idle` by control-plane [`8af572a15bec7f13ac3eaf874da8a0d6f084b989`](https://github.com/tngkrwlsmd/personal-control-plane/commit/8af572a15bec7f13ac3eaf874da8a0d6f084b989).
- **Evidence boundary:** G01 root cause, exact crash-time native caller stack, and original CI self-contained DLL identity are still unknown. The installed framework DLL with matching PE timestamp is only a **candidate**, not a verified byte-identical crash module. L08 remains separate OPEN; excluded G03–G05 and paused G07 remain untouched. Do not conceal `ValueError`, claim the symbol lookup passed, or retry blocked Windows work through a different route.

## 2026-10-25 — G01 public PDB located, native caller stack still unavailable

- Repeat owned Release crash WER: `Microsoft.UI.Xaml.dll`, `0xC0000005`, RVA `0xAB04B`, COFF timestamp `05FCB77A` ([#40190876464](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40190876464)). The original CI-loaded DLL was retired, and available text WER metadata has no exception-time stack.
- A registered Windows App Runtime 2.5.1 DLL's **PE COFF timestamp exactly matches** `05FCB77A` ([#40191885960](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40191885960)); its CodeView debug identity is **Microsoft.UI.Xaml.pdb / GUID `4ACDBE85-D668-192E-B8B6-A9334AC91B79` / age `1`** ([#40191726913](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40191726913)). File-version labeling differs (`3.2.3.2609` installed versus `3.2.3.0` WER); do not assert bytewise equality without a content hash.
- Microsoft public symbol endpoint returned **HTTP 200** to HEAD for that PDB (292,835,328 bytes; [#40192068135](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40192068135)); no file download, dump, debugger installation or GUI reenactment was performed. Symbolizing RVA alone cannot reveal the caller stack. A future explicitly authorized isolated native debugger run must obtain exception-time frames, with controlled data exposure, before C++ ownership changes. G01 remains unresolved.


## 2026-10-25 — precise G01 lifetime terminology and Release WinUI module identity

- Actual Windows Error 1000 read-only [remote run #40189509823](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40189509823) confirms the failing module is **Microsoft.UI.Xaml.dll 3.2.3.0**, native access violation **0xC0000005** at RVA **0xAB04B**. The tracked project-template source uses **Microsoft.WindowsAppSDK 2.5.1**, and `WindowsAppSDKSelfContained=true` for Release. Debug's self-contained setting differs, so a Debug-only outcome is not interchangeable with the recorded self-contained Release crash.
- Important distinction to prior shorthand: observed `MAINWINDOW_DESTRUCTOR_EXIT` is a marker **inside the user-written `MainWindow::~MainWindow()` destructor body**. C++ member subobjects and the generated WinUI `MainWindowT` base are destroyed **after** that marker. Likewise `APP_DESTRUCTOR_BODY_EXIT` is before automatic `App::window` member destruction. The event trace plus `0xC0000005` **does not establish that either complete class destruction or the projected Window release completed successfully**. Last actual Windows focused GUI, source SHA `f7bf2b72413e077b0892ea6b77951a7234e296a1`, remains [#40187978307](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40187978307); the source-only review did not run another build or GUI.
- Prior upstream focused TextBox shutdown bug [WinUI #11653](https://github.com/microsoft/microsoft-ui-xaml/issues/11653) concerns a known native crash family, but the flyExplorer exact GUI trace recorded `FOCUS_BEFORE_OTHER`, `FOCUS_TRANSFER_SUCCEEDED`, `FOCUS_AFTER_OTHER`; do not claim the TextBox-specific failure is reproduced. Other 3.2.3.0 reports with different exception code/offset are not an exact match either. Stopping extra timers or altering handler ownership based on this source audit without native exception-time stack would be speculative. The attempted Window-release witness was rolled back following a blocked protected test edit; don't circumvent the block.
- Next safe proof is a test-owned, approved exception-time stack for the matching Release module, keeping crash dumps/private process memory and global debugging/registry settings off by default. Until such evidence, **G01 clean exit** and **L08 native cursor oracle** remain OPEN.


## 2026-10-25 — G01 actual App destructor order and non-TextBox focus observed

- Exact trusted-main focused Windows [#40187978307](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40187978307), source `f7bf2b72413e077b0892ea6b77951a7234e296a1`: native Release build PASS; all three physical Details resize drags, rapid-tail and WindowTab restore PASS, original MFC settings unchanged, strict L08 OS cursor FAIL.
- Read-only preserved owned GUI trace [#40188449625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40188449625) captured `FOCUS_BEFORE_OTHER`, `FOCUS_TRANSFER_SUCCEEDED`, `FOCUS_AFTER_OTHER`, `APP_DESTRUCTOR_ENTER`, `APP_DESTRUCTOR_BODY_EXIT`, `MAINWINDOW_DESTRUCTOR_ENTER`, `MAINWINDOW_DESTRUCTOR_EXIT`, then process exit code **0xC0000005** after 3353ms. The owned main HWND was destroyed by 250ms after a successful normal `WM_CLOSE` post. This is *not* a focused-TextBox-at-close reproduction; App's projected Window-member release occurs after the App destructor body. It is still unknown whether Window-member release fully completed before the AV. No exception-time stack exists from this run.
- A proposed inert post-Window-member-release witness C++ diagnostic could not be completed because the required GUI-test allowlist edit was blocked by automated safety inspection; no workaround attempted. Both temporary C++ commits were reverted, and read-back verified unchanged pre-proposal App.xaml.cpp and App.xaml.h blobs. Product state and strict test remain consistent with the built source. **G01 remains OPEN**; do not claim fix or crash cause based on trace order alone.


## 2026-10-25 — repeated G01 access violation AFTER MainWindow destructor (post-XAML-close boundary)

- In source `a1f686c19d830bae9c5356b8a90805fe6ad78474`, bounded opt-in test-only native lifecycle trace was added. Source AST 2/2 and focused contracts 5/5 PASS ([#40180943309](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40180943309)), actual Windows Release build PASS in [#40181069199](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40181069199), physical three-column drag/tail/workspace-restore PASS, original MFC settings unchanged, but strict GUI L08 cursor FAIL. Avoid conflating independent functional GUI checks with full acceptance.
- The test sent normal owned `WM_CLOSE`, original HWND was gone by 250ms, and app exit after 3514ms was decimal 3221225477 (`0xC0000005`). Bounded archive log inspection [#40181481815](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40181481815) and targeted full phase-line retrieval [#40181572983](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40181572983) prove all 22 instrumented phases completed: AppWindow.Closing, focus transfer, XAML controls, session/controllers, ShellNavigation shutdown, Window.Closed, and crucially **`MAINWINDOW_DESTRUCTOR_EXIT`**, before the process crashed. Unlike a stuck WM_CLOSE handler, this run's crash occurs **after** all observed application window teardown callbacks returned.
- Scoped read-only Application Error event [#40181790568](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40181790568) matches `flyExplorer.exe` crashing in `Microsoft.UI.Xaml.dll`, exception `0xC0000005`, fault offset `0xAB04B` at 2026-10-25 18:37:27 KST — **same module, exception and exact offset** as previous run [#40178312147](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40178312147). The reproducible fault site does **not** establish an exception-time native call stack, UAF identity or causal code statement. Read-only [#40180452071](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40180452071) sampled owned archive and 12 app-specific WER report folders: no native dump found there, and the common debugger executables were not on PATH. Do not equate bounded search with a global proof of absence.
- Prevention: retain independent normal-exit, cursor-appearance and user-settings sentinels; keep trace disabled for ordinary use and scoped only to a unique owned temporary fixture. A future justified debugging investigation requires an exception-time stack or further post-destructor ownership evidence; do not keep rebuilding unchanged code, expand timeouts, rewrite WER fault offsets as causes, or disable other safety gates. G01 and L08 remain OPEN; user-excluded G03–G05 and paused G07 untouched.


## 2026-10-25 — G01 two-WindowTab close: HWND closes normally but WinUI XAML crashes after destruction

- One exact-trusted-main, focused Windows desktop GUI [#40177882230](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40177882230) at `64dea5f039304ce6fe29b2f0928ba15047048ffb`: native Release build PASS; all three Details width drags, rapid-tail, second WindowTab return and original MFC-settings identity independently observed PASS; strict L08 *global OS* cursor remained Arrow and overall GUI remained FAIL. TextBox cursor positive control also failed to show I-beam, so do not interpret this as proof that product visuals or a synthetic cursor assertion succeeded.
- Bounded failure log read from retained owned archive `e2d79ea1b06f4ebdb3be973f432b08b0` ([#40178200942](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40178200942)) shows `G01_OWNED_WM_CLOSE_POSTED True PRESTATE ('owned-hwnd','responsive')`; HWND destroyed by the 250ms checkpoint and stayed destroyed at 1s and 3s. Process exited at 3317ms with **`3221225477 / 0xC0000005`** rather than clean exit 0. The 2026-10-25 observation is post-HWND XAML access violation, **not** a generic blocked `WM_CLOSE` handler. The previous close timeout remains an independent observation and not evidence that both have the same cause.
- Read-only, local-time-bounded Application Error 1000 through [#40178312147](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40178312147) matched the exact execution window: `flyExplorer.exe`, faulting `Microsoft.UI.Xaml.dll`, exception `c0000005`, offset **`0xAB04B`**. Historical PX12 access violation in this module occurred at **`0xA0981`** and does not supply a native exception-time stack or a shared causal explanation.
- **Prevention/next boundary:** keep close, exit code, and unchanged profile-sentinel as independent gates. Report native faulting module distinctly from the original strict cursor failure; do not rewrite a genuine nonzero exit as a timeout or PASS. Require a same-case native exception-time call stack or bounded teardown-stage event evidence before modifying product lifetime handling; no speculative native timer/subclass/WinUI workaround. Preserve diagnostic archives and do not repeat a clean Release build without a new grounded source change. Excluded G03–G05/G07 remain excluded.


## 2026-10-23 — WinUI C++/WinRT micro-projection failure isolated (no new GUI)

- [Previous exact Windows run #39967597593](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39967597593) successfully verified all pinned NuGet component hashes, Authenticode signature on `cppwinrt.exe`, `Microsoft.UI.Xaml.Controls.h` generation and scratch cleanup, then failed native micro-compile: `C2338` mismatched generated-header vs Windows SDK `base.h`, `C1083` missing `winrt/Microsoft.UI.h`. This is a preflight/projection defect rather than evidence of product cursor behavior. Prior metadata inventory [#39966964422](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39966964422) located `Microsoft.UI.winmd`.
- Replaced the untracked ad-hoc request concept with a reusable, source-reviewed but **not Windows-verified** `tools/winui/l08_winui_projection_preflight.ps1`. It requires trusted package digests, a signed exact generator, matches generated platform/WinUI projections before MSVC `/Zs`, echoes native compiler errors and retires only owned scratch. It does not modify `DetailColumnHandle` or run UI. A matching generator platform `base.h` and the requested WinUI API compile **must still be verified**; don't claim this fixes `C2338`/ `C1083` until the script passes.
- Remote-shell request could not be reset to idle because update actions were blocked by a safety check; central run queue was empty. Do not overwrite an active request, work around the safeguard or repeat costly GUI builds. Inspect/clear the stale request through authorized control-plane procedures before the next exact-SHA focused preflight.


## 2026-10-23 — Preflight evidence path repaired for tiny WinRT compilation (not WinUI)

- Repeated native diagnostic failures on earlier exact sources were compounded by missing compiler error detail after the central CI's bounded logging and scratch retirement. This does **not** retroactively recover the third failed compile from [#39957644663](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39957644663).
- New, deliberately limited `tools/winui/l08_cppwinrt_core_preflight.ps1` at `88ef76418f5d3049f13f7bdc64352c55a915604c` compiles only a Windows SDK C++/WinRT `Windows.Foundation::IStringable` mock with the installed MSVC compiler, then verifies an intentional **C1189** compiler error is captured and echoed to the Actions job log while scratch still exists. [Committed-script VM execution #39960766793](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39960766793) **PASS**, exact checkout + compiler scratch safely retired. This is a negative-control proof of the **tiny unit** logging path, not a claim of full product compiler-error retention.
- No WinUI 3 `ProtectedCursor`/generated `DetailColumnHandle` API probe is compiled yet: pinned Windows App SDK projections were absent from inspected global cache locations. Before further product event instrumentation, obtain that SDK in a temporary, owned compiler-only fixture and prove compilation of the actual candidate call sequence. Do not launch the costly focused GUI on an uncompiled candidate.


## 2026-10-23 — L08 event instrumentation C++ compile failures; restoration and prevention

- Diagnostic-only edit to `DetailColumnHandle` exposed Loaded, pointer entry/exit counts and ProtectedCursor presence via a test-gated UIA HelpText. All focused **Python source contracts passed**, but this did **not** validate the generated C++/WinRT projection.
- Exact-source [central #39956401276](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39956401276) **Release FAIL** at `DetailColumnHandle.cpp:21` (braced `winrt::hstring{value}` parser error). Corrected explicit UTF-16 conversion. [#39957070274](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39957070274) **Release FAIL** at `DetailColumnHandle.cpp:20` because `this->as<DependencyObject>()` is absent on the implementation type. Changed to `get_strong().as<...>` but [#39957644663](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39957644663) still **Release FAIL** (error text unavailable in the bounded central log). **None of these three runs executed GUI**; do not mistake diagnostics for observed `PointerEntered`.
- Read-only retained archive [#39958334368](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39958334368) held only the source filename, not compiler errors. Exact third-run CI workspace no longer existed [#39958541750](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39958541750). Failed GitHub artifact uploads hit storage quota; do not invent a call stack or error code for the third compile.
- **Recovery:** reverted only the four new diagnostic/contract files to the exact GitHub blobs from accepted baseline `ae19755b47897dec298593cd4543c30a5e631ecd`, verified blob-for-blob at `7e086b4b00436aa5762abcc9495ac3b671caa949`. Previous [Windows GUI #39954174882](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39954174882) remains relevant for unchanged content, but the restore snapshot itself has **not been separately built/tested**. Prevent recurrence with an isolated C++/WinRT compile probe + complete compiler error preservation before another expensive scoped GUI; avoid guessed projection conversions.


## 2026-10-23 — L08 precise hover hit but native arrow persists through 600 ms

- Old focused GUI `98e9b283` was a **real drag PASS**, not a cursor PASS. Read-only inspection of its retained log ([#39953465234](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39953465234)) showed exact automation hit on each of the three resize thumb elements and actual +40/+28/+20-pixel boundary movement, but `GetCursorInfo` reported native arrow `HCURSOR=65539` while Win32 `IDC_SIZEWE=65553`.
- No new product cursor implementation was added. Narrow instrumentation in `dc0e5a826213b9e40e04eeeae4b7af1bc3dba311` enforces an owned-body-to-thumb pointer transition and logs `GetCursorInfo` and exact UIA peer at 70, 250 and 600 ms; a source contract in `e555051866868e4a7dc548a40b65d31edeccf552` guards this path. Windows preflight [#39954122328](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39954122328): syntax and 3/3 source tests PASS, isolated checkout removed.
- Exact-source [Windows scoped GUI #39954174882](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39954174882): Release and actual column-resize GUI **PASS**, process exit 0 (33.8 s), native user settings preserved, owned fixture removed. Bounded archived log inspection [#39955105078](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39955105078): nine of nine post-hover samples hit the matching resize Grid/Group peer but reported `CURSOR arrow`; three drag width deltas unchanged at +40/+28/+20. This rules against *only* an immediate-sampling delay within 600 ms under that automation, but **does not establish the WinUI root cause** or invalidate previous direct user observation of working cursor.
- Prevention: do not equate UIA hit or correct geometry with native cursor feedback; classify timed `GetCursorInfo` separately, and do not apply unproven cursor hacks or rerun accepted PX10/G01 features. Cursor-visual/pixel acceptance remains OPEN; G03–G05 excluded, G07 stopped.



## 2026-10-23 — PX10 physical column-resize focused GUI: verification and corrected preflight

- The legacy L08 owned GUI asserted `IDC_SIZEWE` on automation-driven hover although earlier Windows automation and user-physical input gave different cursor observations. It also ended the owned app with `terminate()`, which did not prove normal WinUI teardown. The focused test now checks actual header boundary movement for three columns, fast release-tail movement, original WindowTab boundary after workspace return, normal close exit 0, profile-sentinel equality and fixture cleanup. The cursor remains diagnostic only: **no cursor-shape or pixel-visual acceptance claimed**.
- Initial exact-source preflight [#39949635733](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39949635733) failed **one source contract** due to an outdated expected string `next_header.rectangle().left>=start+12` instead of the actual UIA re-query `element(next_header_id).rectangle().left>=start+12`. It was a test assertion mismatch, not a GUI or C++ failure. Corrected source at `4d6950dd`; exact-source [#39950085238](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39950085238) **3/3 contracts PASS**, with owned checkout removed.
- Central control-plane [Quality #39949400260](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39949400260) rejected the newly registered `gui-column-resize` because the old GUI dependency scope/order contract still expected the original scope list. The source guard and separate worker branch were corrected without enabling unrelated PX10 selection GUI. [Control-plane Quality #39950532626](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39950532626) **PASS**. Old failed/cancelled records remain historically failed/cancelled.
- Exact application `98e9b283998aa90c134ceacb1ec19be573841934` [scoped Windows #39951081963](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39951081963): **Release PASS, `functional-px10-column-resize` PASS, GUI process EXIT=0 in 29.3 seconds, central workflow success**. Positive GUI runner markers enforce owned resize results, tab-return, exit, user config checks and cleanup. The central diagnostic emits `NOT_FINAL_ACCEPTANCE=1`: this is not a full GUI suite, a native intermittent G01 root-cause resolution or a reviewed pixel comparison. Remote shell idle after dispatch; G03–G05 excluded; G07 stopped.


## 2026-10-23 — G01 focused Ctrl+W close PASS, central marker false negative (bounded)

- New focused test on `f5c327b40e53439b904a484c8a0d19b9d3dc2805` exercised startup plus address-focused Ctrl+W final-window close. First actual Windows run [#39941356463](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39941356463) had a **harness NameError** (new `send_keys` call lacked import), not a diagnosed native application failure. Fixed the import at `f3a29d3d640a13723e8bed5592c9613a0152cb3c`.
- Corrected exact-source [central Windows #39942415493](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39942415493) compiled Release **PASS** and executed `gui-startup-integrated-Release EXIT=0`, but was marked `G01_INTEGRATED_STARTUP_MARKER_MISSING`. Read-only retained log inspection [#39943122615](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39943122615) proved startup, focused editor, Ctrl+W exit 0, legacy settings unchanged, and owned-fixture cleanup markers all present. The actual legacy sentinel line ended with **`PRESENT 6`**; exact-line matching erroneously rejected it. The runner failure **must not be relabeled a CI PASS**.
- Fix `beb8b83cad232a2b7206571e4e6201098ba84b9b` checks the actual numeric suffix while requiring the remaining exact markers, and test fixture newline correction `2ba0da35c6144bc8d28c0d3949431ff9d598739e` covers positive, missing-marker, invalid-suffix and traceback cases. Exact-SHA Windows **source-only** [#39946409466](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39946409466): **3 tests PASS**, no GUI/build, isolated checkout retired and command slot idle. Do not rerun an otherwise successful GUI merely to change its reporter verdict; keep source, GUI and CI-verdict evidence distinct.
- G01 intermittent initial Shell navigation and shutdown reliability remain **OPEN**. Do not infer native exception-time stack, broad acceptance, or excluded G03–G05/G07 test coverage.


## 2026-10-23 — G01 focused TextBox close workaround: one bounded PX12 PASS

- Prior actual PX12 visual test `f0980b5...` / [central run #39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462) ended in `Microsoft.UI.Xaml.dll` access violation `0xC0000005`; its retained WER did not include an exception-time native dump. Microsoft [WinUI issue #11653](https://github.com/microsoft/microsoft-ui-xaml/issues/11653) reports a compatible focused-`TextBox` teardown bug, with focus relocation in `AppWindow.Closing` as a tested workaround. This is a plausible causal match, not independent native stack proof for flyExplorer.
- Code and the PX12 focus precondition were changed in [`0893ba12`](https://github.com/tngkrwlsmd/flyExplorer/commit/0893ba12c67b05ad4d5c9534261fc78f5b82e770). On exact-source [Windows focused run #39936268900](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39936268900), Release compiled and the actual scoped PX12 GUI exited successfully; the harness enforces exit code 0, unchanged user-profile sentinel and owned-fixture cleanup.
- Prevention: keep the pre-close focus assertion and real process-exit check; do not rely on `Window.Closed` alone for this workaround. Classify this as a single focused PASS, **not** evidence that all intermittent G01 shutdown or initial-navigation faults are resolved.


This is the append-only failure/root-cause/prevention ledger. Older entries may
refer to source or documentation paths that were later retired from the working
tree. Recover those exact artifacts from Git when needed; do not interpret old
milestone/current-state wording as the present product status. For current
product state use CURRENT_STATUS.md.
# flyExplorer Error Diagnosis / Prevention History

## 2026-10-23 — PX12 matched visual capture ended in XAML access violation

- Exact source `f0980b515f47288c14b6aded2d1829e2620d421e` [Windows #39911686462](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39911686462): actual native Release build and 3 matched synthetic-address screenshot captures succeeded, but on owned WinUI process close the exit was `3221225477` (`0xC0000005`) and visual acceptance correctly failed. Standalone focused PX12 functional navigation acceptance [#39907990501](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39907990501) remains a separate prior PASS.
- Read-only Windows Application Error 1000 [#39912873511](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39912873511) matched `flyExplorer.exe` PID 9492, `Microsoft.UI.Xaml.dll` exception `c0000005`, fault offset `0xA0981`, UTC 2026-10-23 06:32:05.673. This is a **crash site, not a proved root cause**. Do not attribute to PX12 change without a causal stack. Existing G01 intermittent-shutdown problem remains open/reproduction-deferred.
- The GUI harness raised before its original-profile sentinel or owned scratch deletion; neither unexecuted check can be claimed to have passed. Independently preserved the three screenshot PNGs/hashes in failed-run log, then cleaned the unique test-owned fixture [#39914030926](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39914030926) with exact ancestry, unique file markers, no reparse/protected files or live matching app. All user-owned paths were excluded from cleanup. Do not add speculative native teardown changes or repeat expensive builds to turn the run green. See `docs/development/PX12_VISUAL_COMPARISON_20261023.md`.


> **Chronological evidence archive (preserved):** Some entries describe past
> source snapshots and scoped test runs; they are not assertions that current
> `main` has passed the same tests. For active project status, evidence limits
> and currently outstanding work, read [`CURRENT_STATUS.md`](CURRENT_STATUS.md)
> and `.agent-policy/PROJECT.md`. Retain historical failures, diagnosis and
> test provenance when updating the live summary.

이 문서는 확정된 오류를 단순 수정으로 끝내지 않고, 다음 진단을 빠르게 하고 같은 계열의 결함을 사전에 막기 위한 프로젝트 기록이다.

## 2026-10-19 — R1 validation boundary and state-oracle repairs

- A SYSTEM-created owned checkout caused user-session historical Git contracts to
  return false despite the retired object being present. Confirm the object first,
  then use an exact-checkout **process-local** safe.directory setting; never a
  wildcard/global Git exception or ACL rewrite. Correct the canonical dependency
  helper path (`tools/winui/check_python_deps.py`) before scheduling.
- `Start-Process -Wait` remained blocked after native build commands had exited.
  Bounded owned-process inspection found only the waiting worker/console host.
  The obsolete owned task was cancelled with evidence retained, without claiming
  build acceptance. Capture the command process handle and `WaitForExit()` directly;
  keep stdout/stderr separate and observe its actual exit code.
- The new GUI fixture first omitted required polling `interval` arguments, then
  used the hidden legacy ComboBox's `selected_index()` as an oracle. A small real-key
  probe [39186572498](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39186572498)
  showed correct focus/check/file-order transitions while that getter returned None.
  Validate call signatures from the actual helper with stdlib AST/signature binding;
  assert visible Toggle state and durable file order instead of an unsupported getter.
- A folder-tab independence assertion was also broader than current product behavior.
  The unchanged old/new-binary comparison [39187495613](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39187495613)
  proved pane-shared sort in both. Record the architecture/implementation gap and
  preserve it in this display-only unit; do not silently add a persistence redesign.
- **Successor:** [39188197976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39188197976)
  passed the repaired focused GUI, normal exits, settings preservation and cleanup
  using the already-built `5a90c5de...` EXE. Four 96-DPI Light/Dark BEFORE/AFTER pairs
  were separately reviewed. Source 4+60 and Release PASS evidence was preserved;
  alternate DPI/HC/Narrator/full GUI and older failed runs were not relabelled PASS.

## 2026-10-18 — M26 owned GUI result transport obscured first failure

- On an exact previously accepted product binary (source `0d10b1b6`, exe SHA-256 `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17`), the optional 96-DPI owned accessibility GUI test was invoked through temporary user-session scheduled tasks. Runs [#39102240993](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102240993) and [#39102419752](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102419752) failed in the result-envelope handler (the second produced 236053 bytes where only bounded JSON was expected); [#39102607819](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39102607819) ended with user task exit 1 and no final evidence file. These runs do **not** prove any product UI defect.
- **Evidence limitation:** the old runner used Windows PowerShell native output redirection under terminating-error semantics and deleted its raw log even when result publication failed. The exact first GUI failure or wrapper failure from those runs cannot be recovered from the retained synthetic fixture. [Read-only inventory #39103271352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39103271352) found exactly one prior disposable fixture with test-owned source/config/temp dirs; the actual application and registered temporary task had already stopped.
- **Prevention:** The central control-plane tracked worker now launches the verified Python fixture using `Start-Process` with separate bounded stdout/stderr logs, produces an atomic small JSON result only after child exit, and retains diagnostic stdout/stderr on failure. It refuses unexpected source hash, product hash, user session, output paths, collisions and leftover task ownership. The previously inventoried fixture is preserved without recursive cleanup.
- **Successor evidence:** [Windows run #39103545858](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39103545858) **SUCCESS**, the same app binary and Python acceptance test (unchanged) produced all 7 expected markers and exit 0: 16 named controls at 960x634, 1100x680 and 1240x710; real Tab focus; 96 DPI/current High Contrast OFF; protected six user configurations unchanged. This supports **96-DPI M26 UIA/keyboard scoped PASS**, not a claim that the exact earlier failure's complete root cause was proven. 125/150/200% native scale, active F04/F05 High Contrast and spoken Narrator remain OPEN.

## 2026-10-17 — Isolated F05 build timeout caused by recursive ACL inheritance removal

- Exact candidate `32cb338c`, branch-only Windows Release
  [#39018110254](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39018110254)
  **FAILED** on outer `ISOLATED_RELEASE_RESULT_TIMEOUT`, before product
  compilation could be established. The temporary setup first created
  `.owner`, `worker.ps1`, `request.json`, and the isolated source
  checkout, then applied `icacls /inheritance:r /T` to the root. This
  recursively removed inherited read access from the child files,
  including the worker and Git source; the worker could not write a
  `ci.log` or `result.json`.
- Diagnosis: [#39021505482](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021505482)
  could not read the owner marker. [#39021592902](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021592902)
  found SYSTEM running with root SYSTEM/Admin/user ACL intact but
  `.owner` with **zero ACEs**. After exact owner-path repair,
  [#39021887711](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39021887711)
  proved both worker/request ACLs and sample source files had zero ACEs.
- Recovery was restricted to the unique verified test-owned root:
  restore inherited permissions to the marker, worker and request,
  then restore inherited rights within that root's isolated source
  subtree, preserving the restrictive root ACL; no broad
  `safe.directory` override, user data cleanup, or ownership takeover.
  [#39022006596](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022006596)
  verified that build/test scripts and `.git/HEAD` became readable.
  Successor [source #39022160319](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022160319),
  [Release #39022312037](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022312037),
  and [GUI #39022716919](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39022716919)
  all passed without repeating the broken recursive ACL command.
- **Prevention:** Set restrictive ACL only at the *owned root*, before
  creating children, with explicit SYSTEM, Administrators and exact
  interactive-user grants. Let descendants inherit. Never apply
  `/inheritance:r /T` to an existing test subtree, because it removes
  inheritance from individual files. Assert that `worker.ps1`,
  `request.json`, build scripts and `.git/HEAD` are readable
  before scheduling a long-running Release task.

---

## 2026-10-13 — F06 invalid UNC address chrome and last-request race

- Owned GUI run [38380137080](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38380137080)
  rejected a quoted nonexistent loopback UNC and retained the right-pane
  file list, but its address editor still exposed the rejected input.
- A proposed restore in `OnNativeResult::Failed` then caused the
  unrelated rapid invalid-then-valid navigation assertion to fail in
  [38380865307](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38380865307):
  a delayed failure handler may write over newer text before its newer
  request commits. The failed approach was removed, not carried into main.
- The correction restores the committed address immediately after
  submitting Enter input, leaving route-token checks and async commit
  ownership to the existing navigation controller. The first run
  [38381583006](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38381583006)
  found one stale exact-source assertion after the refactor. Updating that
  assertion (not weakening the behavioral requirement) led to full
  [38381812799](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38381812799)
  source, Release and owned GUI PASS, including the negative quoted UNC
  and rapid last-request test. Normal app shutdown and scratch cleanup passed.
- Prevention: do not mutate the address editor from stale asynchronous
  failures; let only the accepted complete Shell snapshot update committed
  navigation. Keep a negative UNC test and rapid opposite-order navigation
  gate together. No live SMB-share creation or credentials during probes.

---

## 2026-10-12 — Narrator Recap focus/visibility evidence is not speech evidence

- The first control-plane speech-recap script attempted
  `New-Item -LiteralPath` under Windows PowerShell 5.1; this cmdlet
  did not support that parameter. Correcting this command changed
  the request harness, not the flyExplorer product
  ([run 38232070285](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232070285)).
- Starting Narrator brought a Narrator window into the foreground.
  The synthetic owned Win32 editor was no longer focused. A limited,
  exact-owned foreground correction allowed a second probe to
  discover two visible Narrator Recap windows with 35 UIA nodes
  ([run 38232530406](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38232530406)).
  The previous `zero UIA nodes` diagnosis was a test discovery
  limitation, not a proven accessibility API failure.
- A controlled Win32 BUTTON with a verified accessible UIA Name and
  foreground focus gave a true reference-label prerequisite, but
  scanning Narrator's actual Recap UIA text/name/value patterns still
  found no matching phrase, and audio was not captured
  ([run 38233608351](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38233608351)).
  **No flyExplorer product failure** follows from the missing reference
  evidence; neither is actual spoken-text acceptance established.
- Test cleanup also requires its own explicit gate: after `Narrator+Esc`
  and `Windows+Ctrl+Enter` were injected, the test-originated
  Narrator process could remain running. An exact-PID termination
  sometimes caused a second Narrator instance, requiring strictly
  provenance-guarded bounded cleanup. Final exact-session/creation
  checks, two known test-originated PID stops, stable process-zero
  confirmation and safe owned-file removal completed
  ([run 38234299929](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38234299929)).
  Never terminate a preexisting real user's screen reader based only
  on the executable name.
- Prevention: stop using this shared session for unattended transcript
  guesses, require attended actual-audio or independently verified
  privacy-limited transcript capture, and retain separate source/UIA,
  speech-text, audio, process cleanup and OS-DPI acceptance labels.
  See `NARRATOR_SPEECH_VALIDATION.md`.

---

## 2026-10-12 — Narrator starts but actual speech remains unverified

- The Windows VM runs Windows 11 Pro build 26300 with a working audio
  endpoint and no preexisting Narrator process
  ([inventory 38229681112](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38229681112)).
- A non-elevated user test task starting `Narrator.exe` directly received
  WinError 740 (requires elevation). Retrying the same command or
  bypassing UAC is not a safe accessibility acceptance strategy
  ([run 38230127856](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230127856)).
- The documented Windows+Ctrl+Enter accessibility shortcut **did**
  launch Narrator from a test-owned desktop reference. Nevertheless,
  the limited UIA client observed zero Narrator-owned text nodes
  after Narrator+Alt+X Speech Recap; no spoken label or audio waveform
  was independently confirmed. The test worker then failed at
  `psutil.AccessDenied` on a higher-integrity Narrator process wait
  ([run 38230388533](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230388533)).
  These are *environment/automation permission* issues, not flyExplorer
  accessibility correctness failures.
- An independent process inventory confirmed zero remaining Narrator
  processes and zero test scheduled tasks after the failed wrapper
  ([run 38230563415](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/38230563415)).
- Prevention: first isolate actual spoken content in a synthetic
  reference, **do not** re-label a process-launch/UIA-name test as a
  voice test, use attended audible confirmation or independently
  trustworthy Speech Recap access, avoid machine-wide clipboard or
  unreviewed audio capture, and preserve/restored initial Narrator state.
  See `docs/development/NARRATOR_SPEECH_VALIDATION.md` for the explicit
  acceptance procedure.

---

## 2026-10-09 — indexed modified-date acceptance and local-time boundary

- Unlike traversal mode's local modified-day semantics, `SystemIndex`
  stores timestamp metadata that may be interpreted in UTC or local time.
  Using exact SQL midnight boundaries as the sole truth can exclude
  local-calendar dates around UTC offset and daylight-saving changes.
- The isolated helper uses intentionally expanded read-only
  `System.DateModified` candidate bounds for indexed queries, then
  re-reads each result's actual `ftLastWriteTime` and compares its
  exact local calendar date against the inclusive input boundaries.
  SQL is a prefilter, **not** authoritative acceptance.
- A shared strict Gregorian parser rejects invalid or reversed
  `YYYY-MM-DD` dates before indexing; SQL boundaries at year edges
  may be omitted (rather than overflow) while actual per-file local-day
  verification remains mandatory. No provider, filesystem, or index
  service configuration is modified by the test.
- Remote run `37934459707` on candidate
  `029ef1e5d8f186bfc5262d386576204b58fa47a9` completed
  **SUCCESS**, including Release native 72/72, Release app build,
  real SystemIndex date include/exclude, combined GUI filters, and
  protected profile/source unchanged. The separate matched-geometry
  visual run `37935505947` also completed SUCCESS: matched 956×711
  before/after app-owned screenshots, with 1,450 changed pixels
  confined to the one-line indexed-mode guidance text row
  `[446,200,664,214]`. Both actual previews were inspected for
  clipping and layout; targeted fixed Dark-theme/100% visual PASS.
  All checks are SHA-scoped pre-main and do not imply a separate
  post-merge full-suite verification.

---

## 2026-10-09 — indexed size acceptance stopped at native harness count

- Remote Windows Task `37923169399` on candidate
  `4efa1a59ecfa6c99a74cf0be6b1f53550276a492` passed change-scoped
  FAST, indexed-size source contracts, the canonical Release product build
  and a Release native fixture **build**. The Python acceptance driver then
  asserted `M19_NATIVE_SUMMARY 64 passed, 0 failed.` and failed.
- Fixture source changed from 57 expected completed assertions to 63
  (six net additional indexed-size bounds checks), but the Python driver
  expected 64. This is a test-harness count mismatch; the failed run did
  not print the actual native summary or reach live SystemIndex/GUI checks.
  Do not classify this as product runtime acceptance.
- Fix: assert 63 expected and include the actual native summary in future
  assertion failures. Run the native regression first; reuse the prior
  product build PASS as SHA-scoped evidence until a product binary is needed
  for SystemIndex/GUI acceptance. The temporary worktree from the old run
  was removed, so any necessary executable on the new candidate must be
  rebuilt, not assumed reusable.
- Resolved: corrected-run `37925547766` completed SUCCESS with 63/63
  native, Release, actual SystemIndex size include/exclude and GUI PASS.
  Initial visual run `37927022090` remained unequal geometry
  (944×510 / 944×677); not accepted as matched visual evidence.
  The fixed owned-window HWND fixture passed in run `37930662129`:
  matched 956×711 BEFORE/AFTER, 2,586 changed pixels only on the
  index-mode hint row. Both actual preview images were reviewed for
  layout, clipping and dual-pane visibility. These are SHA-scoped
  pre-main results, not independent post-merge certification.

---

## 2026-10-09 — Windows indexed search passed but Actions quota failed

- Run `37911818230` initially failed because a Release native fixture
  invoked the default Debug executable without building its native target.
  The candidate was corrected to build and run the Release fixture.
- Run `37912684233`: FAST, Release product/native build, 57 native
  tests, SystemIndex extension matching and GUI inclusion/exclusion all
  passed. The job subsequently failed during `actions/upload-artifact`
  with `Artifact storage quota has been hit`.
- Remediation: retain restricted structured results and bounded status
  markers directly in the `evidence/remote-windows` Git branch from
  the producing Remote Windows Task. The prior run's observed results
  were saved retrospectively; its missing binary ZIP and pixels were
  not recovered.
- Preserve separation: product PASS does not mean historical workflow
  PASS, and successful evidence persistence does not convert a
  failure into acceptance.

---

## 2026-10-09 — indexed Search visual comparison: unequal startup geometry

- First actual BEFORE/AFTER run `37918146605` passed old-main and
  candidate Release builds, both actual WinUI Search captures, and actual
  indexed extension filtering, but its screenshot comparator rejected
  different viewport sizes (BEFORE 944×677, AFTER 944×651).
  Git evidence archived the workflow failure correctly.
- The comparator was changed to preserve full, uncropped original
  dimensions, report overlap and uncovered pixels separately, and provide
  both image previews for direct inspection. A synthetic mismatched-size
  regression test now protects this behavior.
- Follow-up `37920530398` passed the updated comparator and all
  source/build/native GUI gates. Its screenshot dimensions were
  944×625 versus 944×599, again −26 pixels in height. The
  visual inspection found no new clipping or overlap in the modified
  index-mode explanation or surrounding controls; complete identical
  viewport pixel parity was not established.
- Prevention: a successful difference calculation is **not** automatic
  visual acceptance. Always record and inspect geometry mismatches,
  identify reviewed UI surface, and keep full-resolution/matched-screen
  evidence as an explicit separate gate if it was not exercised.

---

## 2026-10-09 — chained GUI harness regressions and recovery

**Failure boundaries and fixes**

- The combined suite's M22-owned 12,000-byte `큰.txt` also matched
  M19 Search v3's 10–13 KiB search condition. The test now expects
  two matches in the combined profile, retaining one in standalone
  search (PR #51). A restarted saved preset restores conditions but
  not folder scope, so its test re-enters the synthetic search folder.
- Theme restoration transiently invalidated the `LeftFiles` UIA peer.
  The owned harness now bounds reacquisition to 15 seconds for known
  transient errors while retaining the app-owner guard (PR #52).
- M19 left the Search/Workspace panels open during chained GUI; M20
  needed a visible file list. Only `area=all` now enables
  `FLY_M20_OWNED_COLLAPSE_M19_PANELS=YES` (PR #55).
- Failure-time evidence now captures only the test-owned app window,
  bounded pane UIA, synthetic folder listings and traceback before
  cleanup. It does not capture the user's desktop or mask the
  original GUI failure (PR #54).

**Acceptance and prevention**

Pre-main chained GUI run `37891171256` passed with normal exit 0 and
protected settings preserved, for its recorded candidate/runtime.
Post-merge central CI `37891854981` independently verified main
`7c23af1515fab0926fa409d277efd6e16b9d1f65`: Release build PASS,
`gui-all-Release` exit 0 (145.1 s) and
`central-ci/windows-gui=success`. Distinguish test fixture/UIA/
cross-suite lifecycle errors from product defects; reuse unaffected
build evidence after harness-only changes. These fixes do not imply
new visual, DPI, provider or release certification.

## 2026-10-08 — Windows Search indexed filename search

**원인과 경계**
- Traversal search was bounded at 20,000 visited entries and depth 32;
  it could not query Windows Search index contents.
- First indexed-search Release build exposed helper wire constant
  ambiguities; fully qualified the new `indexwire` symbols.
- The first visual harness used desktop screen capture, which failed on
  the interactive runner service desktop. Switched to app-owned XAML
  `RenderTargetBitmap` and separated visual evidence from functional GUI.
- Real Windows Search `System.ItemPathDisplay` did not reliably correspond to
  the canonical on-disk path. Native indexed `System.ItemUrl` was chosen and
  validated, with an independent SystemIndex oracle in GUI acceptance.
- Early GUI fixture queries assumed newly created or public test files were
  indexed immediately. They were not. Final acceptance used a verified
  pre-indexed read-only system path without modifying that source.

**검증 및 예방**
- Exact-owned, killable helper, 1,000 rows/1 MiB response, scope containment,
  explicit index-unavailable/timeout statuses, no fallback to traversal,
  search epoch cancellation and stale completion checks.
- Run `37712395449` on candidate
  `ef6618cd478a6cadad56eb3bdce026b7e9541d02`: focused GUI PASS,
  independent native oracle PASS, one real matching row, unsupported criteria
  rejected, original system file unchanged, process exit 0, protected legacy
  settings unchanged. Visual before/after pixel review remains separate.

**Focused visual acceptance follow-up (2026-10-08)**
- Run `37714905989` was a test-only diagnostic error: PowerShell command-line
  quoting removed Python's quotes around `RGB`, causing `NameError` before
  any pixel comparison. The subsequent diagnostic found captures from different
  fixtures/launch states; different dimensions cannot prove a regression.
- Later owned capture attempts exposed an early-startup/loaded-state race and
  a stale Release binary in one baseline run. Both problems were traced to
  fixture orchestration, not a new product search defect. Exact-main
  `387efa622f6a9ce6685e3bffb98299df0503de3c` was rebuilt before its
  final capture (`37718045551`); the accepted indexed candidate
  `ffc2466be51c32c1cf7454a2df80fe4f8c3f5f99` used the
  identical test-owned `display-folder` fixture (`37717788614`).
- Final fixed 972x720 HWND, Dark-theme, actual XAML `RenderTargetBitmap`
  pair was reviewed directly in `37718272601`: **956x711** images;
  **113,339 / 679,716** differing pixels (**16.6745%**). The added
  Windows-index mode row and expected downward flow of the search/pane
  sections explain the principal layout change; the sidebar, dual file panes,
  status footer and action chrome stayed legible without blocking overlap or
  clipping. Transient search-scope input and randomized test-owned path text
  differed at capture time and were explicitly excluded from any
  pixel-identical assertion. **VISUAL LAYOUT ACCEPTANCE: PASS**; additional
  DPI/selection/theme states: NOT SEPARATELY TESTED.
- Capture processes exited 0 with legacy settings and read-only system index
  fixture preserved. This closes the indexed mode's focused visual gate,
  without broadening indexed/provider/property scope.


## 2026-10-08 — bounded Windows Pictures Library provider Copy-in

**오류/위험 경계**
- Copy-out previously accepted only a filesystem destination. Blindly allowing
  arbitrary virtual Shell destinations would delegate an unbounded mutation to
  providers with different capabilities, collision semantics and storage rules.
- Display strings are insufficient authority for a provider write. Library
  write-through may resolve to a different physical default save location.
- Directory watcher status can replace a transient transfer-success message;
  success evidence must use the actual destination bytes and controller idle.

**원인 분석 및 처리**
- Added orthogonal `DestinationMode::ShellProvider` and private transfer wire
  v3; ordinary filesystem Copy/Move and provider Copy-out preserve their
  existing mode and validation.
- The UI sends bounded bytes copied from the accepted destination snapshot
  PIDL. The exact-owned `FlyShellIsolationHelper.exe --file-transfer` validates
  its framing and equality with `FOLDERID_PicturesLibrary`, loads the library
  and resolves its effective default save folder. It accepts only the safe
  non-reparse, supported-drive path equal to the user's `FOLDERID_Pictures`
  Known Folder. Other provider destinations/custom save locations fail closed.
- Collision checks use the resolved filesystem folder. `IFileOperation::CopyItem`
  handles only filesystem-source Copy; provider-to-provider Copy, Move,
  Recycle/Delete remain unsupported. Existing cancellation, process ownership,
  Job Object, progress and stale-route checks remain unchanged.

**재발 방지**
- Provider mutations require source and destination modes to be explicit in
  wire framing and checked again in the helper; navigation descriptions never
  grant mutation authority.
- The focused fixture refuses to overwrite existing Pictures entries, uses
  isolated test-owned source and sentinel files, verifies exact bytes plus source
  preservation, and removes all owned Pictures entries during cleanup.
- Do not claim general third-party provider writes from a built-in library's
  filesystem-backed default save-folder acceptance.

**검증 상태**
- Candidate `dfc8703394e8c750beaaaa7ee9cea9d81ddeba2c`, Remote Windows Task
  `37705656407`: request validation, change-scoped FAST, interactive GUI
  runner health, canonical Release build, source contract and focused actual
  two-pane Pictures Library GUI all PASS.
- Runtime: provider destination enumerated; provider target Move rejected;
  filesystem source copied into resolved Pictures location with exact bytes;
  source preserved; controller idle; application exit 0; both test-owned
  Pictures items and isolated fixture removed; protected legacy settings
  byte-identical.
- No new XAML/layout/icon changes; visual pixel acceptance was not required.
  Other provider destinations, custom library save locations and
  provider-to-provider/Move/Recycle/Delete remain NOT SUPPORTED.

## 2026-10-08 — virtual Shell/provider Copy-out acceptance

**오류 발생**
- The first focused fixture used a test-owned ZIP/Compressed Folder route. The
  app did not reliably enumerate that route in the self-hosted GUI session;
  AppsFolder also enumerated no usable items on this VM.
- After moving to the already accepted Pictures Library virtual root, several
  harness revisions exposed pane activation/destination-settlement assumptions.
  Once both panes were deterministic, run `37624180111` reached the product
  gate and showed `선택한 Shell provider 항목은 Windows에서 복사할 수 없습니다.`.
- Navigation snapshots do not request `SFGAO_CANCOPY`, so testing that bit in
  MainWindow falsely rejected an item which the Shell transfer helper could
  copy.
- After the UI capability gate was removed, run `37624726608` actually
  materialized the destination file but failed because the harness waited for a
  transient completion string that the destination watcher immediately replaced
  with `폴더 변경 알림을 반영했습니다.`.

**원인 진단**
- Provider mutation identity must come from the accepted Shell snapshot, not
  from reparsing a display/parsing name later. Some provider identities are not
  stable enough to treat string parsing as the mutation authority.
- Capability checks such as `SFGAO_CANCOPY` belong at the exact-owned helper
  boundary immediately before mutation. The navigation attribute set is a
  presentation/enumeration contract, not a transfer-capability contract.
- A watcher status is allowed to replace a transient success message after the
  controller has already completed successfully; status text is therefore not a
  durable transfer completion signal.

**해결 방법**
- Added `SourceMode::ShellProvider` for Copy-out only. Provider destination,
  Move and Recycle/Delete remain rejected.
- MainWindow copies the accepted parent/child PIDLs into bounded value blobs:
  32 KiB per PIDL and 1 MiB aggregate, in addition to the shared 1,024-item and
  1,048,576 UTF-16 source-identity bounds. No COM object crosses the process
  boundary.
- The exact-owned `--file-transfer` helper validates PIDL framing, immediate
  parent/child identity, duplicate selection, `SFGAO_CANCOPY`, materializable
  leaf names and destination collisions before `IFileOperation::CopyItem`.
- Removed the MainWindow `IndexedItem.attributes & SFGAO_CANCOPY` gate; the
  helper is the authority for selected provider capability.
- The focused acceptance starts directly in canonical Pictures Library, commits
  the opposite filesystem pane explicitly, verifies provider Move rejection and
  uses controller idle + destination bytes as durable Copy-out completion.

**재발 방지**
- Preserve accepted PIDL identity across helper boundaries when a Shell action
  depends on provider identity; parsing-name strings may remain diagnostics but
  must not become the sole mutation authority.
- Do not infer transfer capability from navigation attributes that were not
  explicitly requested.
- GUI transfer tests must verify durable state (destination bytes, controller
  idle, source preservation) rather than a transient status message when
  namespace/directory watchers can legitimately publish a later status.

**검증 상태**
- Canonical Pictures Library diagnostic `37623786873`: PASS; resolved
  `::{031E4825-7B94-4DC3-B131-E946B44C8DD5}\\Pictures.library-ms`.
- Product source last changed at
  `d95984203c41519235e36e276ba7f89adfa4e82c`.
- Run `37624726608`: FAST PASS, runner health PASS and canonical Release build
  PASS. Runtime reached destination materialization; only the stale transient
  status assertion failed.
- Final head `32648cfeb5e92594619b9ed24b2568b18d71a2e8`, run
  `37703633100`: FAST, runner health and focused GUI PASS. Provider
  enumeration and destination readiness passed; provider Move remained
  rejected; Copy-out materialized exact bytes; controller returned idle; source
  remained unchanged; app exited 0; test-owned source/fixture were removed; and
  protected legacy settings were byte-identical.
- No product pixel/layout code changed; no new visual acceptance was required.
- Arbitrary third-party providers and provider-only non-filesystem child types:
  NOT SEPARATELY CERTIFIED. Provider Copy-in, Move and Recycle/Delete:
  NOT IMPLEMENTED.
## 2026-10-07 — virtual Shell/provider thumbnail acceptance

**오류 발생**
- Provider thumbnail acceptance first needed a deterministic virtual-root image
  fixture. Diagnostic `37610405578` showed Pictures Library exposed the
  test-owned subfolder but not the image one level below it. Diagnostic
  `37610682928` moved only the synthetic PNG to the Pictures root and proved
  the image appears directly through `shell:PicturesLibrary`; cleanup removed
  it afterward.
- Baseline `37611127478` fixed the current-product frame with the registered
  PNG icon and no provider thumbnail.
- Product run `37611774958` stopped in FAST before build. The new source
  contract asserted that helper source must literally contain
  `thumbnailPixelBytes`, but the helper fills that ResultHeader member from
  `thumbnail.size()`.

**원인 진단**
- A virtual Shell root can expose filesystem-backed children while still
  requiring provider parsing-name handling at the root. Pictures Library gives
  a deterministic built-in acceptance seam without enabling provider mutation.
- Thumbnail work must stay bounded independently of the 1,200 type/icon item
  ceiling; requesting thumbnails for every provider entry would make provider
  latency and response size unbounded.
- The FAST failure was a test-string mistake, not product behavior.

**해결 방법**
- `shell_visual_wire` v2 adds per-item flags and separate thumbnail dimensions/
  byte counts. FileDetailController marks no more than four non-folder items in
  Medium/Large Icons and prefers known image extensions.
- The existing exact-owned `--shell-item-visuals` child handles both provider
  type/icon and flagged thumbnails. Only the child calls
  `SHCreateItemFromIDList` and `IShellItemImageFactory::GetImage` with
  `SIIGBF_THUMBNAILONLY|SIIGBF_BIGGERSIZEOK`; inherited handle restriction,
  one-process Job Object, cancellation and the 4.5-second inactivity watchdog
  are unchanged.
- Corrected only the stale source assertion after `37611774958`; product code
  did not change between that failed FAST candidate and the accepted successor.

**재발 방지**
- Provider visual protocols must carry explicit per-item work flags and hard
  thumbnail-count/size limits rather than infer expensive work from item count.
- Focused GUI fixtures that temporarily touch a user-facing Known Folder must
  use a unique test-owned filename, refuse overwrite, and delete it in a
  finally/cleanup path.
- Source contracts should assert the semantic initialization path rather than a
  field-name token that need not appear at the call site.

**검증 상태**
- BEFORE `37611127478`: FAST + runner health + focused Pictures Library GUI
  PASS; registered PNG icon present, provider thumbnail absent; process exit 0;
  settings unchanged; owned PNG removed; artifact `11477852307`, SHA-256
  `ce6ef976c28b0f513b008bfb0b763458a7742f6a89749e953261f521b3b36173`.
- Final `37612117791`: FAST + runner health + canonical Release build +
  focused Pictures Library GUI PASS; `SHELL_PROVIDER_THUMBNAIL_PASS=True`;
  process exit 0; settings unchanged; owned PNG removed; artifact
  `11478154054`, SHA-256
  `e54f994a299989de2fa41c2b9200c5fbd547a43544d3b83df5a96565d4cf03a7`.
- Matched 944x510 visual review: 6,996/481,440 pixels changed (1.4531%), only
  x=327..390 and 714..777, y=205..264, exactly the two pane copies of the owned
  image cell. VISUAL ACCEPTANCE: PASS.
- Provider Copy/Move/Recycle and arbitrary third-party provider behavior remain
  outside this unit.

## 2026-10-07 — virtual Shell/provider type-icon isolation and visual acceptance

**오류 발생**
- Initial baseline run `37590963762` built successfully but the GUI harness
  attempted physical `click_input` before entering This PC and failed in the
  service-desktop cursor path. A later mouse-independent revision still did not
  establish the virtual root reliably; the fixture was changed to launch
  directly at `shell:MyComputerFolder`.
- Baseline run `37591794512` then passed and fixed the current-product BEFORE
  frame.
- Product run `37592816719` stopped in FAST because a source contract still
  described the pre-change virtual-provider attribute boundary.
- Run `37593190964` passed FAST and runner health but the Release helper build
  failed: the new visual wire introduced `kMagic`, `kVersion` and
  `checksum` names alongside the navigation wire and several helper references
  were left unqualified.

**원인 진단**
- Baseline acquisition must not depend on synthetic mouse movement when typed
  Shell navigation or startup routing can establish the exact owned virtual
  root deterministically.
- The product extension intentionally separates provider visual identity from
  filesystem detail. Virtual-root requests carry parsing names and never enter
  filesystem attribute/thumbnail paths.
- Multiple private wire namespaces can coexist in one helper translation unit;
  unqualified protocol constants are therefore not a stable contract.

**해결 방법**
- The focused harness starts its isolated profile directly at the built-in This
  PC Shell root and uses the app-owned `RenderTargetBitmap` capture path.
- Added a bounded `shell_visual_wire` and exact-owned
  `--shell-item-visuals` helper route. The client restricts inherited handles,
  assigns a one-process kill-on-close Job Object and terminates that job on
  cancellation or 4.5 seconds without pipe progress.
- Only the helper parses provider names and calls
  `SHGetFileInfoW(...SHGFI_PIDL...)`. Protocol constants/checksum references
  are namespace-qualified. Provider thumbnails remain closed.

**재발 방지**
- Visual baselines on the self-hosted GUI runner should prefer deterministic
  owned navigation plus app-compositor capture over physical cursor movement
  when pointer behavior is not the feature under test.
- Cross-controller source contracts must be updated in the same logical unit
  when an intentionally closed route becomes supported.
- Shared helpers that include more than one private wire must qualify protocol
  symbols at each boundary.

**검증 상태**
- Baseline `37591794512`: FAST, runner health, focused This PC GUI, process
  exit 0 and protected legacy settings unchanged; artifact `11469400568`,
  BEFORE SHA-256
  `ac462537fd94437161c2033a927806b170045e18da5573bfdc8ca8f6c4a79005`.
- Final `37593453954`: FAST, runner health, canonical Release build and
  focused This PC GUI PASS; provider type/icon PASS, process exit 0, protected
  settings unchanged; artifact `11469965269`, AFTER SHA-256
  `42b3a53b26a209edd5ad5469f87fa0696509d9bc83e94f8e58fab5429ee97c1e`.
- Matched 944x510 visual review: 4,368/481,440 pixels changed (0.9072%), all in
  x=199..832, y=221..291, exactly the two visible item rows whose provider
  icon/type presentation changed. VISUAL ACCEPTANCE: PASS.
- Virtual/provider thumbnail and mutation semantics: NOT IMPLEMENTED in this
  unit. Arbitrary third-party provider implementation behavior: NOT SEPARATELY
  CERTIFIED.

## 2026-10-07 — removable Shell visual validation exposed stale contract and stale worktree

**오류 발생**
- Run `37587596698` stopped in change-scoped FAST before build because
  `test_file_metadata_controller_contract.py` still encoded the prior
  network-only visual isolation string.
- After updating only that stale expectation, run `37587832255` passed FAST
  and GUI runner health but the command deliberately stopped before build on
  `?? 965093aa9397b0e0419c94270e636d1d427a8948/` in the canonical checkout.

**원인 진단**
- The first failure was a source-contract fixture lagging the intended
  removable extension; metadata isolation itself remained unchanged and the
  visual detail path had moved to the generalized `isolatedPathAccess`
  contract.
- Read-only run `37588036456` proved the unexpected directory was not user
  data: it was a registered detached Git worktree created on 2026-10-05, with
  its `.git` file pointing into the canonical repository's worktree metadata.
  The nested worktree status was checked separately before any removal.

**해결 방법**
- Updated only the stale cross-controller source assertion after the first
  failure; no product retry was issued on the unchanged test revision.
- Cleanup run `37588225417` required the nested worktree to be clean, then
  removed it through normal `git worktree remove` and verified the outer
  canonical checkout was clean. No reset/clean/forced deletion was used.
- The product extension keeps removable/network path attribute probing out of
  FileDetailController by reusing snapshot folder hints and keeps image path,
  reparse, size and Shell thumbnail validation inside the exact-owned helper.

**재발 방지**
- Contracts that verify independent metadata/detail lifecycles should assert
  the semantic isolation boundary rather than freeze a network-only token when
  an additional filesystem drive class is intentionally enabled.
- A hash-named directory inside the canonical checkout must be identified with
  `git worktree list` and its own status before cleanup; do not assume it is
  disposable build output from its name alone.
- Environment residue that prevents a validation command from starting is not
  product evidence. Change the execution condition, preserve FAST/health
  evidence as appropriate, and resume from the earliest invalidated boundary.

**검증 상태**
- Run `37588369405`: request validation, FAST, runner health, canonical
  Release build and focused forced-removable GUI all PASS; thumbnail,
  registered icon, folder icon and Windows type label PASS; process exit 0;
  protected legacy settings unchanged.
- 944x510 visual comparison against run `37575384608`: 208/481,440 changed
  pixels (0.0432%), all in temporary path text at y=49..62; file-list/content
  pixels below y=80 identical. VISUAL ACCEPTANCE: PASS.
- Physical USB/removable execution: NOT TESTED — the runner reported no
  `DRIVE_REMOVABLE` volume.

## 2026-10-07 — network Shell visual acceptance required app-owned XAML capture

**오류 발생**
- UNC/network Shell visual/type/icon/thumbnail acceptance initially failed in
  the visual harness before product implementation was merged.
- Run `37569904209` passed the owned thumbnail/type/icon/folder-icon checks but
  Pillow `ImageGrab` failed with `OSError: screen grab failed` in the
  self-hosted service desktop.
- `PrintWindow(PW_RENDERFULLCONTENT)` runs `37570303708` and
  `37572625619` completed, but direct artifact review showed a black WinUI
  compositor client area, so those captures were explicitly rejected as visual
  evidence.
- Run `37573025841` then stopped before capture when the existing one-shot PNG
  thumbnail did not appear within the harness wait; run `37574565680`
  demonstrated that screen-DC `BitBlt` itself was unavailable in the runner.
- Later FAST runs `37576775870` and `37577140712` exposed stale source
  contracts that still encoded the old fixed-drive-only detail boundary and a
  namespace-escape token assumption.

**원인 진단**
- Desktop capture APIs are not a reliable evidence boundary for this
  self-hosted WinUI compositor/session.
- The thumbnail miss was a pre-existing one-shot scheduling/timing behavior in
  the baseline harness, not proof of a network-detail product defect.
- The source-contract failures were test expectations lagging the intentionally
  expanded network boundary; they occurred before Release runtime acceptance.

**해결 방법**
- Added a double-gated, test-owned XAML capture hook. After accepted
  FileDetailController completion, `RenderTargetBitmap` renders `RootShell`
  inside the app process and writes the owned BMP to the requested evidence
  path. No desktop capture or foreign foreground ownership is required.
- Network detail scheduling now accepts mapped `DRIVE_REMOTE` and ordinary
  direct UNC roots, carries snapshot folder/file hints so the parent worker
  avoids UNC attribute probes, and leaves actual thumbnail path validation and
  Shell image extraction in the bounded one-shot helper.
- Updated source contracts to scope the old fixed-drive-only assertions to the
  behavior that remains fixed-only and to assert the new network isolation
  boundary directly.

**재발 방지**
- WinUI visual acceptance on this runner should prefer app-owned
  `RenderTargetBitmap` evidence over `ImageGrab`, `PrintWindow` or screen
  `BitBlt`.
- A successful capture API return is not sufficient; the resulting image must
  be directly reviewed before it is accepted.
- Provider/network expansion contracts must distinguish parent-process path I/O
  from isolated-helper path I/O rather than forbidding `DRIVE_REMOTE` across a
  whole translation unit.

**검증 상태**
- Run `37575384608`: FAST + canonical Release build + fixed-path visual GUI
  PASS; accepted 944x510 BEFORE screenshot, process exit 0, legacy settings
  unchanged.
- Run `37577331163`: final candidate FAST + `git diff --check` PASS.
- Run `37577442125`: canonical Release build + forced-network visual GUI PASS
  for PNG thumbnail, registered file icon, folder icon and Windows type label;
  process exit 0 and protected settings unchanged.
- BEFORE/AFTER direct pixel review: file-list/content region identical; only
  random temporary-path text in the top chrome differs.
- Actual SMB/UNC or mapped-drive visual execution: NOT TESTED — no test-owned
  SMB share is available.
- **VISUAL ACCEPTANCE: PASS**.

**관련 candidate**
- `e4c95e1c2e7c1a3ca1f3530dac86f4477c1664a3`

---

## 2026-10-07 — UNC metadata-sort acceptance trusted hidden SortPicker UIA state

**오류 발생**
- 실행/프로필: UNC/network sortable-metadata pre-main acceptance.
- 초기 FAST runs `37558962391`, `37559264194`, `37559370802` exposed
  stale source-contract assumptions after `DRIVE_REMOTE` became valid only for
  sortable metadata. Run `37559533336` then reached Release compilation and
  failed in the helper on ambiguous unqualified `kMagic`/`kVersion`/
  `checksum` names. After qualification, run `37559970803` built both
  Release binaries successfully but the 1,305-file GUI stopped at
  `sort callback did not record 크기 내림차순 step 1`.

**최초 실제 오류**
- The compile failure was C2872/C2668 in `FlyShellIsolationHelper.cpp`: the
  new metadata wire reused symbol names already visible from the Shell
  isolation wire. Qualifying metadata-wire symbols removed the ambiguity.
- The later GUI failure was not a product sort failure. Small-fixture diagnostic
  run `37560547409` showed pywinauto `SortPicker.selected_index()` returning
  `None` both before and after Invoke, while the visible size header changed
  to `크기 ↑`, status changed to `파일 메타데이터 정렬을 적용했습니다.`,
  the first row changed according to the requested sort, and the process exited
  0.

**원인 진단**
- Some older source contracts were scoped to whole-file token absence instead
  of the behavior-owning block, so the legitimate metadata-only
  `DRIVE_REMOTE` token looked like a This-PC capacity-probe regression.
- The helper compile error was a namespace-collision defect in the new wire
  integration.
- The expensive GUI false negative was a harness defect: the hidden
  compatibility `SortPicker` is not a stable UIA state oracle in this runner.
  The visible sortable-column header is the product-owned projection of
  `PaneState::sortMode` and did update immediately.

**해결 방법**
- Scope the This-PC capacity contract to the capacity-card block and align the
  metadata-validity/source tokens with the actual owning expressions.
- Fully qualify `fxfile::metadatawire` symbols in the helper.
- Change `test_metadata_sort_gui.py` to validate each header Invoke from the
  visible ascending/descending arrow, then retain the existing stable
  postconditions: ordered first row, metadata-completion status, process exit
  and protected-settings checks. Remove the temporary diagnostic CLI after the
  failing layer was established.

**재발 방지**
- Source contracts that forbid a provider/drive token must slice the
  behavior-owning function/block instead of asserting token absence across an
  unrelated translation unit.
- Shared helper protocols with common names such as `kMagic`, `kVersion`
  and `checksum` must be namespace-qualified at integration points.
- GUI acceptance must use a visible/stable product projection or final model/
  filesystem postcondition, not a hidden compatibility control whose UIA
  property may be unavailable. Diagnose this on a small fixture before
  repeating a high-cost 1,000+ item fixture.

**검증 상태**
- Run `37560547409`: FAST + runner health + Release build + 25-item diagnostic
  PASS; visible header/status/row state proved the product callback path.
- Final run `37563774189`: FAST, runner health, `git diff --check`, canonical
  Release helper/app build and 1,305-item forced-isolated metadata GUI PASS for
  size/date/type; owned process exit 0 and protected legacy settings unchanged.
- Actual SMB/UNC or mapped-drive metadata execution: NOT TESTED — no test-owned
  SMB share is available on the runner.
- VISUAL ACCEPTANCE: NOT TESTED

**관련 commit**
- `f51edfdb40e066d063c85958601336c1854aeafc` — accepted product/test candidate; final integration adds
  documentation only.

---

## 2026-10-07 — UNC Copy/Move GUI acceptance confused transient status with completion

**오류 발생**
- 실행/프로필: UNC/network Copy·Move pre-main acceptance. Release/native
  semantics had already passed, but the broad file-operations GUI run
  `37553699165` failed before interaction because the runner had no
  app-owned foreground window. A later UIA-only focused harness then failed
  after the Copy file had already appeared at the destination.
- 사용자에게 보인 증상: repeated GUI failures looked like an isolated-transfer
  completion defect even though filesystem mutation and Release build/native
  evidence were already successful.

**최초 실제 오류**
- The broad physical-input harness first failed with
  `AssertionError: Refusing physical input: foreground belongs to a user window`.
  Diagnostic run `37554219584` observed no foreground HWND in the runner
  session, so changing product transfer code would not address that boundary.
- After switching to UIA-only interaction, the focused harness required
  `StatusText` to keep the exact transient string `복사를 완료했습니다.`.
  Direct diagnostic run `37555732127` instead observed the copied file on
  disk, `CopyButton=True`, `MoveButton=True`, `CancelButton=False` and
  `StatusText='폴더 변경 알림을 반영했습니다.'`.

**원인 진단**
- The first failure was a harness/environment mismatch: physical input was
  intentionally guarded when the runner could not prove an app-owned
  foreground target.
- The second failure was a harness lifecycle bug. On successful transfer,
  `OnTransferCompleted` briefly writes the success string and then queues a
  deterministic refresh for touched visible folders. The normal watcher/
  navigation completion is allowed to replace that transient string with the
  folder-change status before a polling test samples it.
- Product Copy/Move mutation, helper completion and FileOperationController
  busy-state settlement were therefore not the failing layer.

**해결 방법**
- Added a dedicated UIA-only UNC/Copy-Move acceptance path that uses Invoke and
  Selection patterns and never requires physical mouse/keyboard focus.
- The focused acceptance now waits for FileOperationController to leave the
  busy state (`CancelButton` disabled), verifies normal mutation controls are
  re-enabled, verifies the owned filesystem result, and rejects explicit
  transfer-failure status families instead of requiring a short-lived success
  sentence to remain visible.
- Product code was not changed for this harness correction.

**재발 방지**
- Async UI acceptance must validate the stable postcondition of the owning
  lifecycle (mutation result, busy/cancel state, failure disposition) rather
  than a presentation string that a downstream watcher/refresh is expected to
  supersede.
- When physical-input safety rejects a runner session, diagnose foreground/
  ownership once and move to a semantically equivalent UIA-only path if the
  feature does not require physical-pointer semantics.
- Preserve successful build/native evidence across harness-only revisions.

**검증 상태**
- Run `37553534009`: FAST + helper Debug + M22 Debug native 33/33 PASS.
- Run `37553699165`: M22 Release native 33/33 and canonical Release build
  PASS; later broad physical-input GUI boundary failed as described above.
- Run `37556148841`: final candidate
  `a08e32788bdcd5d33da31e0c413803f30e548b92` passed `git diff --check`,
  FAST, canonical Release build and focused UIA-only Copy/Move GUI.
- Actual SMB/UNC execution: NOT TESTED — no test-owned SMB share was available;
  the loopback admin-share probe was unavailable.

**관련 commit**
- `a08e32788bdcd5d33da31e0c413803f30e548b92` — watcher-aware focused
  transfer acceptance; product behavior unchanged from the previously built
  UNC Copy/Move implementation.

---

## 2026-10-04 — overlapping Remote Windows Task chain amplified one acceptance into seven runs

**오류 발생**
- 실행/프로필: Remote Windows Task #247-#253, large-folder 20k+ browse/tab-clipping acceptance.
- 사용자에게 보인 증상: one logical unit accumulated seven Actions runs, including queued speculative successors and repeated long 20.5k GUI probes. From Actions metadata the first-to-last wall interval was about 38 minutes and the summed run durations were about 53 minutes, creating roughly hour-scale perceived delay for one task.

**최초 실제 오류**
- #247 had already passed source 228/228, canonical Release build and the real helper over-20k offset regression before the expensive GUI harness failed on a stale UIA load-more wrapper.
- Later successors were submitted while earlier runs were still active. #251 ultimately passed the required 20k+ GUI/visual boundary. #252 then waited behind it and was rejected only after reaching the runner because its validation fingerprint duplicated #251.

**원인 진단**
- Observed: the workflow-side fingerprint guard prevents duplicate command execution but runs too late to prevent an already-created Actions run from occupying the queue.
- Observed: the three-minute guidance was treated as a status-polling cadence instead of a no-polling observation window.
- Observed: a 20,500-real-file final-acceptance fixture was also being used to debug UIA harness lifecycle/completion conditions.
- Root cause: the orchestration policy lacked a mandatory client-side active-run lease and a hard per-logical-unit successor budget before writing the control-branch request.

**해결 방법**
- `AGENTS.md`, `.agent-policy/PROJECT.md` and `AGENT_EFFICIENCY.md` now require a pre-dispatch lease: query recent `control/remote-shell` runs before writing `request.json`; any queued/pending/waiting/requested/in-progress run blocks a new request.
- The first routine read is no earlier than three minutes and a still-active result becomes a resume checkpoint instead of another same-turn polling loop.
- One logical unit gets one primary Windows validation run plus at most one focused successor after a diagnosed completed failure. A third run requires explicit user approval before any request commit.
- 8,000+/20,000+ real-file GUI fixtures are final acceptance only; harness lifecycle must first be proven on the smallest useful fixture.

**재발 방지**
- `test_remote_windows_task_contract.py` locks the pre-dispatch lease, no-polling interpretation, two-run budget and expensive-fixture rule into source contracts.
- Workflow-side validation fingerprint rejection remains a second line of defense, not a substitute for the pre-dispatch check.

**검증 상태**
- Static: PASS — policy language and source-contract assertions reviewed together.
- Compile/link: not applicable; no product/build input changed.
- Runtime/visual: not rerun. Existing #251 success evidence is reused; creating another Windows task solely to validate the anti-churn policy would violate the policy itself.

**관련 commit**
- this logical unit — remote-run lease policy hardening (squashed on merge).

---

## 2026-10-02 — transfer completion could skip the destination refresh

**Observed problem:** an owned multi-file copy completed on disk, but the
opposite pane sometimes did not publish the copied rows before the next
mutation. Full-suite failures moved between asynchronous UI boundaries while
the process still exited normally.

**Root cause:** `StartTransfer` refreshed the touched opposite pane only when
`other.pending[other.active]` was zero. A watcher/navigation refresh already
in flight therefore caused the deterministic post-transfer refresh to be
skipped. If watcher delivery was coalesced or consumed by that older request,
the destination UI could remain stale.

**Fix / prevention:** after a successful non-Recycle transfer, always queue a
Refresh for a currently visible opposite pane whose path is the source or
destination. `IsolatedShellSupervisor::submit` already supersedes the previous
same-pane request and `Model::completeRequest` rejects stale request IDs, so
this preserves the existing bounded/stale-result safety while guaranteeing a
post-mutation refresh.

## 기록 원칙

- 새 항목은 **오류 발생 → 최초 실제 오류 → 원인 진단 → 해결 방법 → 재발 방지 → 검증 상태 → 관련 commit** 순서로 작성한다.
- compiler/linker cascade는 최초 root cause와 파생 오류를 구분한다.
- Observed fact와 inference를 섞지 않는다. 원인이 확인되지 않은 경우 `미확정`으로 남긴다.
- 해결 후 동일 command/profile을 다시 실행하지 못했으면 `NOT TESTED`라고 기록한다.
- 반복 가능성이 있으면 문서만 추가하지 말고 source invariant, regression test, build preflight 또는 contract guard 중 가능한 가장 싼 deterministic 방어선을 추가한다.
- 제품 코드 오류와 build/CI orchestration 오류를 구분한다.
- 민감정보나 불필요한 개인 경로/계정 식별정보는 기록하지 않는다.

## 새 항목 템플릿

### YYYY-MM-DD — 짧은 오류 제목

**오류 발생**
- 실행/프로필:
- 사용자에게 보인 증상:

**최초 실제 오류**
- 첫 error/warning-policy failure:
- cascade/2차 증상:

**원인 진단**
- Observed:
- Root cause:

**해결 방법**
- 수정 파일:
- 수정 내용:

**재발 방지**
- 추가한 invariant/test/preflight:
- 앞으로 같은 계열 코드를 작성할 때 지킬 규칙:

**검증 상태**
- Static:
- Compile/link:
- Runtime/visual:

**관련 commit**
- `<sha>` — `<subject>`

---

## 2026-09-22 — local CI warning-policy 진단 추출 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64`
- 사용자에게 보인 증상: solution 생성과 source preflight 이후 `ERROR: Failed to extract warning-policy diagnostics.`로 CI 종료.

**최초 실제 오류**
- 제품 C++ compile/link error가 아니라 warning-policy diagnostic extraction 단계가 실패.
- MSBuild `BUILD_RESULT=0` 이후 warning 검사 분기로 들어간 상태였다.

**원인 진단**
- Observed: `local_ci.bat`의 quoted PowerShell `-Command` 내부 pipeline이 `$lines `| Where-Object ... `| ForEach-Object ...` 형태였다.
- Root cause: ``|`는 cmd.exe 바깥 문맥용 escape인데 이미 큰따옴표로 감싼 PowerShell command 안에서 사용되어 PowerShell parser에 잘못된 토큰으로 전달됐다.

**해결 방법**
- 수정 파일: `local_ci.bat`
- ``|`를 raw PowerShell pipe `|`로 변경했다.
- 영구 `local-ci.log`의 error-focused 정책과 shell의 일반 MSBuild 진행 출력은 그대로 유지했다.

**재발 방지**
- `build/validate_source_invariants.py`에 `validate_local_ci_warning_policy_wiring()`을 추가했다.
- quoted PowerShell `-Command` 안에서 warning extractor가 raw `|`를 사용하는지, error-only file logger와 temporary normal logger가 유지되는지 검사한다.

**검증 상태**
- Static: PASS — raw pipe 존재, caret-pipe 부재, logger/guard wiring 확인.
- Compile/link: NOT TESTED — 수정 후 Windows x64 재실행 evidence 없음.
- Runtime/visual: 해당 없음.

**관련 commit**
- `02347ca4` — `fix: repair warning-policy diagnostic extraction`
- `2537bf5b` — `test: guard local CI warning extraction`

---

## 2026-09-22 — functional test가 fxfile-crash.h를 찾지 못함

**오류 발생**
- 실행/프로필: Release x64 functional-test build.
- 사용자에게 보인 증상: functional-test translation unit이 `src/fxfile/stdafx.h`를 거치며 `fxfile-crash.h` include를 해석하지 못함.

**최초 실제 오류**
- functional-test target의 include/dependency wiring 누락.
- 같은 빌드에서 CP949 `C4819` 경고도 별도로 관찰됐다.

**원인 진단**
- Observed: product target은 crash module include/dependency를 갖고 있었지만 functional-test target은 해당 contract를 명시하지 않았다.
- Root cause: test target이 product PCH/header contract를 사용하면서 필요한 crash dependency/include path를 직접 선언하지 않았다.

**해결 방법**
- `src/fxfile-tests/fxfile-tests.gyp`에 `fxfile-crash` dependency와 include path를 추가했다.
- `updater_contract_tests.cpp`의 한글 path fixture는 code-page 안전한 `\x` escape로 변경했다.

**재발 방지**
- source invariant에 functional-test crash dependency/include wiring을 추가했다.
- standalone test translation unit은 product target의 우연한 include/PCH 상태에 기대지 않고 필요한 dependency를 직접 선언한다.

**검증 상태**
- Static: PASS — dependency/include/fixture wiring 확인.
- Compile/link: 이후 로컬 x64 CI에서 functional regression target build PASS evidence가 확보됨.
- Runtime/visual: 해당 없음.

---

## 2026-09-22 — functional test standalone compile에서 std container와 64-bit literal 오류

**오류 발생**
- 실행/프로필: `local_ci.bat x64` functional-test compile.
- 사용자에게 보인 증상: `conf_file.h`에서 `std::list`, `std::unordered_map` 미정의와 `XPR_INT64_LITERAL` 미정의가 연쇄적으로 발생.

**최초 실제 오류**
- `conf_file.h`가 사용하는 표준 container header를 직접 include하지 않음.
- test code가 존재하지 않는 `XPR_INT64_LITERAL` macro를 사용.

**원인 진단**
- Product build에서는 PCH/transitive include가 header dependency 누락을 가리고 있었다.
- XPR의 실제 signed 64-bit literal macro는 `XPR_SINT64_LITERAL`이었다.

**해결 방법**
- `src/base/conf_file.h`에 `<list>`, `<unordered_map>` 직접 include.
- `config_persistence_tests.cpp`의 macro를 `XPR_SINT64_LITERAL(...)`로 수정.

**재발 방지**
- public/common header는 자신이 사용하는 표준 타입의 header를 직접 include한다.
- test code에서 project macro를 사용할 때 실제 소유 header/definition을 확인하고 이름을 추측하지 않는다.
- `AGENTS.md`의 compile-readiness/dependency hygiene 원칙에 direct include 규칙을 유지한다.

**검증 상태**
- Static: PASS.
- Compile/link: 이후 functional-test build가 다음 단계까지 진행한 evidence가 확보됨.
- Runtime/visual: 해당 없음.

**관련 commit**
- `141424e7` — `fix: declare config container dependencies`
- `bbcf20a5` — `fix: use signed 64-bit XPR literal macro`

---

## 2026-09-22 — rename regression preflight의 qualified token 누락

**오류 발생**
- 실행/프로필: source invariant/regression preflight.
- 사용자에게 보인 증상: `functional_tests.cpp: missing regression token rename_core::splitBaseFileNameAndExt`.

**최초 실제 오류**
- 동작 테스트는 존재했지만 validator가 요구하는 qualified regression token이 source text에 없었다.

**원인 진단**
- 테스트가 `using namespace fxfile::cmd::rename_core;` 뒤 unqualified `splitBaseFileNameAndExt(...)`를 사용했다.
- static validator는 literal qualified token을 contract로 검사했다.

**해결 방법**
- 세 호출을 `fxfile::cmd::rename_core::splitBaseFileNameAndExt(...)`로 명시적으로 qualified 했다.

**재발 방지**
- static token guard가 의도된 contract라면 테스트 source도 해당 ownership이 명확히 보이도록 qualified symbol을 사용한다.
- 반대로 token guard가 지나치게 brittle한 경우에는 parser/behavior 기반 guard로 개선할지 검토한다.

**검증 상태**
- Static: 이후 source invariant preflight PASS.
- Compile/link: 해당 수정 자체는 behavior change 없음.

**관련 commit**
- `57c3db81` — `test: qualify rename core regression calls`

---

## 2026-09-22 — BCMenu popup width의 signed/unsigned warning-policy 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: Release x64 build가 warning-policy 단계에서 `BCMenu.cpp(1345,24): warning C4018`로 FAIL.

**최초 실제 오류**
- `MEASUREITEMSTRUCT::itemWidth`(`UINT`, unsigned)와 `ModernUI::scaleForWindow(...)`(`xpr_sint_t`, signed)을 `min()`에서 직접 비교했다.
- 같은 warning이 로그에 두 번 보였지만 하나의 root cause가 중복 출력된 것이며 독립 오류 두 개가 아니었다.

**원인 진단**
- Observed: `lpMIS->itemWidth = min(lpMIS->itemWidth, ModernUI::scaleForWindow(...))` 형태의 비교가 있었다.
- Root cause: Win32 구조체의 unsigned field와 내부 DPI helper의 signed 반환값을 같은 비교식에 섞어 MSVC C4018이 발생했다.
- CI는 warning을 정책 위반으로 승격하므로 compile 자체가 진행됐더라도 profile 결과는 FAIL이 된다.

**해결 방법**
- 수정 파일: `src/fxfile/gui/BCMenu.cpp`.
- DPI helper 결과를 먼저 `xpr_uint_t`로 명시적으로 정규화한 `sMaxItemWidth`를 만들고, `itemWidth`와 unsigned끼리 `min()` 비교하도록 수정했다.

**재발 방지**
- 기존 local CI warning-policy가 이 계열의 signed/unsigned mismatch를 자동으로 차단하는 가장 저렴한 방어선이므로 별도의 brittle source-token invariant는 추가하지 않는다.
- Win32/MFC 구조체의 unsigned size/count/index field와 project 내부 signed metric/helper를 `min/max/< />`에서 직접 섞지 않는다. 범위가 양수로 보장되는 값은 경계에서 명시적으로 동일 타입으로 정규화한다.
- 동일 warning이 여러 logger 경로에서 중복 출력되더라도 최초 source location과 warning code가 같으면 하나의 root cause인지 먼저 확인한다.

**검증 상태**
- Static: PASS — `itemWidth`와 최대폭이 동일한 unsigned 계열 타입으로 비교되도록 source 확인.
- Compile/link: NOT TESTED — 수정 후 Windows x64 profile 재실행 evidence 없음.
- Runtime/visual: NOT TESTED — popup menu width/visual regression은 실제 Windows 실행에서 확인 필요.

**관련 commit**
- `5c370470` — `fix: normalize popup width comparison types`

---

## 2026-09-22 — BCMenu rounded selection의 DPI window context 누락

**오류 발생**
- 작업 브랜치에서 popup selection을 rounded/DPI-aware하게 변경한 직후 static self-review 중 발견.
- 잠재 증상: `BCMenu::drawSelection()`이 선언되지 않은 `sMetricHwnd`를 참조하여 Windows/MSVC compile 단계에서 identifier 오류가 발생할 수 있는 상태였다.

**최초 실제 오류**
- 기존 `drawIcon()`/`drawText()`의 DPI metric pattern을 `drawSelection()`으로 옮기면서 metric 계산식만 추가하고 해당 함수 scope의 HWND context 초기화를 빠뜨렸다.

**원인 진단**
- Root cause: 다른 함수의 local setup을 암묵적으로 전제한 채 DPI-aware drawing fragment를 복사/확장했다.
- renderer helper마다 DPI 기준 HWND를 자체적으로 확보한다는 ownership 규칙이 코드에 명시되어 있지 않았다.

**해결 방법**
- `BCMenu::drawSelection()` 안에서 `AfxGetMainWnd()`를 기준으로 `sMetricHwnd`를 직접 초기화하고, main window가 없으면 desktop window로 fallback하도록 수정했다.
- `getControlCornerRadius()`와 inset scaling이 모두 동일한 local HWND context를 사용하도록 정리했다.

**재발 방지**
- DPI-aware drawing code를 함수 간 이동/복제할 때 scale expression만 옮기지 말고 metric context(HWND/DPI)의 선언과 fallback까지 하나의 단위로 검토한다.
- local renderer는 caller의 local variable이나 다른 renderer의 setup을 암묵적으로 기대하지 않는다.
- Windows compile 전 static self-review에서 새 identifier의 definition/use wiring을 확인한다.

**검증 상태**
- Static: PASS — `drawSelection()` 내부에 `sMetricHwnd` local initialization과 desktop fallback 존재 확인.
- Compile/link: NOT TESTED — connector 환경에서 Windows/MSVC 실행 불가.
- Runtime/visual: NOT TESTED — rounded popup selection은 실제 Windows Light/Dark/DPI에서 확인 필요.

**관련 commit**
- `db41ef71` — `fix: define popup selection DPI context`

---


## 2026-09-22 — command-surface validator가 최신 chrome palette를 거짓 실패로 판정

**오류 발생**
- 실행/프로필: `local_ci.bat x64`의 source invariant/regression preflight.
- 사용자에게 보인 증상: `ToolBarEx.cpp`와 `MenuBar.cpp`에서 `sPalette.mSurface` token이 없다는 이유로 solution 생성 전에 FAIL.

**최초 실제 오류**
- 제품 C++ compile/link 오류가 아니라 `build/validate_source_invariants.py`의 command-surface 정적 계약이 최신 UI 구현과 불일치했다.
- preflight 실패로 GYP/Visual Studio project generation 및 이후 compile/link/runtime 단계는 실행되지 않았다.

**원인 진단**
- Observed: 최신 `validate_soft_surface_contract()`와 실제 `ToolBarEx.cpp`/`MenuBar.cpp`는 Win11 layered palette의 command chrome에 `sPalette.mChrome`을 사용한다.
- Observed: 이전 `validate_command_surface_contract()`만 같은 두 파일에 `sPalette.mSurface` exact token을 계속 요구했다.
- Root cause: Win11 softness/rounding 단계에서 command surface ownership이 `mChrome`으로 승격됐지만 이전 flat-surface validator의 exact token이 함께 갱신되지 않아 validator 내부 계약이 서로 모순됐다.

**해결 방법**
- 수정 파일: `build/validate_source_invariants.py`.
- `ToolBarEx.cpp`와 `MenuBar.cpp`의 command-surface 요구 토큰만 `sPalette.mSurface`에서 `sPalette.mChrome`으로 변경했다.
- `SizableReBar.cpp`의 기존 `sPalette.mSurface` 계약은 별도 ownership이므로 변경하지 않았다.

**재발 방지**
- 동일 presentation 계층을 여러 validator가 중복 보호할 때 palette/metric ownership 변경 시 관련 guard 전체의 contract 정합성을 함께 확인한다.
- 실제 구현을 이전 palette 계층으로 되돌려 validator를 만족시키지 않고, 최신 canonical UI contract와 일치하도록 stale guard를 수정한다.
- exact-token invariant를 추가하거나 변경할 때 같은 symbol을 검사하는 다른 validator와 상충하지 않는지 self-check한다.

**검증 상태**
- Static: PARTIAL PASS — GitHub의 현재 source에서 command-surface validator와 soft-surface validator가 모두 toolbar/menu에 `sPalette.mChrome`을 요구하고, rebar의 `mSurface` 계약은 유지되는 것을 확인.
- Source invariant 실행: NOT TESTED — 이 환경에서는 Windows 로컬 checkout의 `python build/validate_source_invariants.py`를 실행하지 못함.
- Compile/link: NOT TESTED — 사용자 로컬 재실행 필요.
- Runtime/visual: 해당 없음.

**관련 commit**
- `53f66a7e` — `fix: align command surface invariant with chrome palette`

---


## 2026-09-22 — 설정 ModernUI subclass callback의 WPARAM/LPARAM 이름 누락

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: source invariant와 VS 2026 x64 solution 생성은 통과했지만 Release x64 compile에서 `cfg_dlg.cpp(129)`의 `aWParam`/`aLParam` C2065로 FAIL.

**최초 실제 오류**
- `ModernGroupBoxSubclassProc`가 callback signature에서 `WPARAM`/`LPARAM`의 변수 이름을 생략한 상태로 함수 끝의 `DefSubclassProc(..., aWParam, aLParam)`에서 해당 이름을 사용했다.
- 동일 구현 패턴의 `ModernCfgButtonSubclassProc`도 같은 누락을 가지고 있어 첫 오류 수정 후 같은 C2065가 이어질 가능성이 있는 상태였다.

**원인 진단**
- Observed: `cfg_dlg.cpp`와 `cfg_main_dlg.cpp`의 두 ModernUI subclass callback 모두 `WPARAM, LPARAM`으로 선언되어 있었고, 각각 원본 message parameter를 `DefSubclassProc`로 전달하려 했다.
- Root cause: settings softness/rounding subclass callback을 추가하면서 사용하지 않는 callback parameter처럼 이름을 생략했지만 forwarding path에서는 실제로 해당 parameter 이름이 필요했다.

**해결 방법**
- 수정 파일: `src/fxfile/cfg/cfg_dlg.cpp`, `src/fxfile/cfg/cfg_main_dlg.cpp`.
- 두 callback signature를 `WPARAM aWParam, LPARAM aLParam`으로 수정하여 기존 `DefSubclassProc` forwarding을 정상화했다.
- UI/message semantics는 변경하지 않았다.

**재발 방지**
- `build/validate_source_invariants.py`에 `validate_modern_subclass_forwarding()`을 추가했다.
- 두 settings ModernUI subclass callback이 WPARAM/LPARAM 이름을 선언하고 원본 message parameter를 `DefSubclassProc`에 전달하는 계약을 preflight에서 검사한다.

**검증 상태**
- Static: PASS — 두 callback signature와 forwarding, 새 source invariant wiring을 repository source에서 확인.
- 기존 사용자 로컬 evidence: source invariant PASS, VS 2026/v145 solution generation PASS, 수정 전 Release x64 compile FAIL.
- 수정 후 Source invariant / Compile/link / Functional regression / Runtime smoke: NOT TESTED — 사용자 로컬 `local_ci.bat x64` 재실행 필요.
- Runtime/visual: NOT TESTED.

**관련 commit**
- `0c67c91d` — `fix: forward config subclass message parameters`

---


## 2026-09-22 — Windows 11 Dark에서 command strip/북마크/설정 combo가 밝거나 과도한 대비로 남음

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 실행 스크린샷.
- 사용자에게 보인 증상: 파일 목록/트리/정보 영역은 Dark인데 상단 menu/rebar/toolbar가 밝게 남고, 정보 영역 bookmark는 순수 파랑으로 과도하게 튀며, 환경설정의 dropdown-list도 흰색 native control처럼 보였다.
- 추가 UX 문제: 테마 선택은 구현되어 있었지만 Korean 설정 tree의 '표시' 항목 아래에 있어 위치를 알아보기 어려웠다.

**최초 실제 오류**
- rebar/toolbar가 app Dark에서도 Explorer visual-style association을 유지한 채 transparent command control로 동작해 light-owned common-control background가 노출될 수 있었다.
- bookmark는 legacy default `RGB(0,0,255)`를 Dark에서도 그대로 사용했다.
- CfgDlg의 `CBS_DROPDOWNLIST` closed field/button은 palette WM_CTLCOLOR 경로만으로는 native light paint를 덮지 못했다.

**원인 진단**
- Observed: content/popup/settings shell의 ThemePalette Dark rendering은 활성화되어 있었으므로 전역 theme-mode 판정 실패가 아니라 control별 paint ownership 불일치였다.
- Root cause: documented Explorer common-control association은 flyExplorer app-dark palette ownership과 동일하지 않으며, legacy bookmark default 및 dropdown-list native paint가 별도 visual path로 남아 있었다.

**해결 방법**
- `SizableReBar.cpp` / `ToolBarEx.cpp`: Dark/non-HC에서 Explorer association을 reset하고 existing palette/custom-draw surface가 command chrome을 소유하도록 변경.
- `bookmark_wnd.cpp`: explicit custom color는 보존하되 legacy default blue만 Dark에서 ThemePalette text로 완화.
- `cfg_dlg.cpp`: dropdown-list의 native input/keyboard/dropdown 계약을 유지하면서 closed field/button만 native paint 후 Dark palette로 보정.
- `Languages/Korean.xml`: 설정 tree의 '표시'를 '모양 및 테마'로 명확화.

**재발 방지**
- `build/validate_source_invariants.py`에서 rebar/toolbar dark theme ownership, config combo adapter, bookmark default-dark readability contract를 보호한다.
- Dark mode에서 documented native theme association을 적용했다는 사실만으로 visual consistency를 가정하지 않고, 실제 control paint ownership을 확인한다.

**검증 상태**
- Static: PARTIAL PASS — repository diff/token wiring과 기존 keyboard/message forwarding 보존을 확인.
- Compile/link: NOT TESTED — Windows/MSVC 로컬 재실행 필요.
- Runtime/visual: 수정 후 NOT TESTED — Windows 11에서 상단 strip, bookmark, settings dropdown 및 Light/High Contrast를 다시 확인해야 한다.

**관련 commit**
- `715f7ec9` — `ui: give dark rebar palette ownership`
- `7f0f17cb` — `ui: keep dark toolbar off light explorer theme`
- `237a12ab` — `ui: soften default bookmark color in dark mode`
- `f4a3b301` — `ui: darken settings dropdown surfaces`

---


## 2026-09-22 — 실행 중 build output 점유로 local CI가 LNK1104까지 진행함

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: source invariant는 PASS했지만 runtime/language staging 중 `Sharing violation`이 반복되고, Release x64 link에서 `fxfile-crash.dll`과 `libxprw.dll`을 열 수 없다는 `LNK1104`로 FAIL.

**최초 실제 오류**
- static/source 오류가 아니라 repository `bin`의 기존 파일이 사용 중이거나 쓰기 불가능한 상태였다.
- staging의 `Sharing violation`은 같은 output tree가 사용 중이라는 선행 신호였고, 최종 fatal은 linker가 project-owned DLL을 교체하지 못한 `LNK1104`였다.
- 기존 local CI는 MSBuild 전에 build output lock을 검사하지 않아 원인이 명확한 환경 오류도 linker cascade까지 진행했다.

**원인 진단**
- Observed: GYP의 x64 OutputDirectory는 `bin/x64`이며 `libxprw.dll`과 `fxfile-crash.dll`도 같은 디렉터리에 linker output으로 생성된다.
- Observed: 실패 로그는 staging 단계의 sharing violation 뒤 같은 `bin/x64` linker output 두 개에 LNK1104를 기록했다.
- 제한: 기존 CI는 lock owner/PID를 기록하지 않았으므로 어떤 프로세스가 점유했는지는 해당 로그만으로 확정할 수 없다. 실행 중인 repository flyExplorer가 이 DLL들을 로드한 경우가 대표적인 재현 조건이다.
- Root cause: local Rebuild가 기존 output을 교체해야 하는데 build 전에 exclusive-write 가능성을 확인하는 preflight가 없었고, staging scripts도 unchanged bundled files를 매번 다시 복사하려 했다.

**해결 방법**
- `build/check_build_output_locks.ps1` 추가: 현재 configuration의 repository-owned EXE/DLL output을 MSBuild 직전 exclusive-open으로 검사하고, 잠긴 파일을 명시한 뒤 fail-fast한다.
- `local_ci.bat`: 모든 `:build_configuration` Rebuild 전에 output-lock preflight를 실행한다. 사용자 프로세스를 자동 종료하지 않는다.
- `copy_lib.bat`, `copy_languages.bat`: directory creation을 idempotent하게 만들고 `xcopy /d`로 unchanged 파일은 덮어쓰지 않는다. staging source가 없거나 실제 copy error가 발생하면 실패를 반환한다.

**재발 방지**
- `build/validate_source_invariants.py`가 lock-preflight wiring, MSBuild보다 앞선 실행 순서, `FileShare::None` 계약, non-destructive process policy, staging `/d`/error handling을 검사한다.
- local CI에서 LNK1104가 repository output 경로를 가리키면 compiler/linker source defect로 보기 전에 output lock을 먼저 진단한다.

**검증 상태**
- 기존 사용자 evidence: source invariant PASS 후 staging sharing violation + Release x64 LNK1104 FAIL.
- Static: PARTIAL PASS — repository source에서 lock preflight/local_ci/copy staging/validator wiring을 대조했다.
- 수정 후 source invariant: NOT TESTED — 사용자 Windows checkout에서 재실행 필요.
- 수정 후 compile/link/functional/runtime: NOT TESTED — repository `bin`을 사용하는 flyExplorer를 닫은 상태에서 `local_ci.bat x64` 재실행 필요.

**관련 commit**
- `275fc85e` — `build: detect locked local CI outputs`
- `4f8acef3` — `build: fail fast on locked outputs`
- `7a9ff045`, `ecd1e4e3` — `build: tolerate unchanged staged files`
- `30220ff2` — `test: guard local CI output lock handling`

---


## 2026-09-22 — Dark settings toggle text와 AddressBar visual-style ownership 불일치

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- 사용자에게 보인 증상: Dark 설정 페이지에서 checkbox/radio label이 어두운 색으로 표시되어 배경과 대비가 부족했고, AddressBar도 inner palette surface와 native-themed outer/child 영역이 섞여 반쪽짜리 Dark control처럼 보였다.

**최초 실제 오류**
- CfgDlg는 WM_CTLCOLOR에서 ThemePalette text를 공급하고 있었지만 themed Win32 Button의 checkbox/radio label paint를 해당 경로가 완전히 소유하지 않았다.
- AddressBar는 palette-backed edit/background/button adapter를 갖고 있으면서도 Dark에서 outer CComboBoxEx, child ComboBox/Edit/ListBox에 documented `Explorer` visual-style association을 계속 적용해 paint ownership이 혼재했다.

**원인 진단**
- Observed: settings page background/card는 Dark ThemePalette를 사용하지만 screenshot의 toggle labels는 dark text로 남았다.
- Observed: AddressBar child controls에는 `applyExplorerControlTheme`와 palette custom paint가 동시에 적용돼 있었다.
- Root cause: native visual-style association/WM_CTLCOLOR가 custom Dark surface 전체의 text/chrome ownership을 보장한다고 가정한 control별 paint ownership 오류였다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: Dark/non-HC checkbox/radio에만 paint subclass를 추가해 background, label, disabled text, check/radio/focus visual을 ThemePalette로 그린다. click/check/keyboard messages는 native Button에 계속 전달한다.
- `cfg/cfg_dlg.cpp`: Dark `CBS_DROPDOWNLIST`의 closed field/button은 기존 adapter가 그리며, `CB_SHOWDROPDOWN` 이후 실제 ListBox HWND의 Explorer association도 reset해 기존 CTLCOLOR palette path가 dropdown text/background를 소유한다. dropdown/keyboard/accessibility 동작은 native ComboBox/ListBox에 남긴다.
- `address_bar.cpp`: Dark/non-HC에서는 outer/ComboBox/Edit/lazy ListBox의 Explorer association을 reset하고 기존 AddressBar palette/subclass paint가 coherent surface를 소유한다. Light/High Contrast는 documented native association path를 유지한다.
- `gui/BCMenu.cpp`: app-owned submenu chevron은 Windows 11 system-provided Segoe Fluent Icons를 우선 사용하고 font 부재 시 geometry fallback을 사용한다. shell IContextMenu routing은 유지한다.
- `src/fxfile/res/fluent/`: Microsoft Fluent UI System Icons MIT license, representative command SVG set, 기존 toolbar frame/command mapping inventory를 추가했다. runtime bitmap strip은 아직 변경하지 않는다.

**재발 방지**
- `build/validate_source_invariants.py`가 settings toggle paint/native fallback wiring, settings ComboBox dropdown ListBox theme reset, AddressBar dark theme reset/native input tokens, popup Fluent chevron+fallback을 검사한다.
- Fluent source contract는 upstream MIT license/provenance, representative SVG existence, canonical GYP registration, main-toolbar frame/command mapping을 함께 검사하고 Windows font binary가 repository에 들어오지 않도록 guard한다.
- Dark UI 검토 시 visual-style association 또는 WM_CTLCOLOR 호출 존재만으로 완료로 판단하지 않고 실제 최종 paint owner를 확인한다.

**검증 상태**
- Static: PARTIAL PASS — repository source에서 paint ownership, native forwarding, asset provenance 및 validator wiring을 대조했다.
- Source invariant 실행: NOT TESTED — 현재 connector 환경에서는 Windows checkout command를 실행하지 못함.
- Compile/link / Functional regression / Runtime smoke: NOT TESTED.
- Visual/manual: 수정 후 NOT TESTED — Windows 11 Light/Dark/System/High Contrast 및 100/125/150/200% DPI에서 재확인 필요.

**관련 commit**
- `1e9d5477` — `ui: fix dark settings toggle contrast`
- `3e974a12` — `ui: give dark address bar full paint ownership`
- `20356129` — `ui: modernize popup chevrons and spacing`
- `962e0864` — `ui: tune popup metrics toward Explorer`
- `e2385e3e` — `ui: complete dark settings combo ownership`
- `b9c6c518` — `build: register Fluent source assets`
- `295be416` — `test: guard Fluent command asset foundation`

---


## 2026-09-22 — Dark settings surface clipping / mixed light controls / popup icon contrast 회귀

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- 사용자에게 보인 증상:
  - 환경 설정 페이지에 큰 검은 사각형 section surface가 생겨 Win11 설정 hierarchy와 어울리지 않음.
  - 일부 edit/combo/button에 밝은 native border/background가 남아 Dark page와 섞임.
  - page-local "모두 적용" 같은 pushbutton이 흰색 native button으로 남음.
  - child page 모서리 근처 control 일부가 잘리거나 위치가 부자연스러워 보임.
  - BCMenu popup의 legacy bitmap icon이 Dark surface에서 과도하게 밝거나 검은 부분이 배경에 묻혀 일부 icon이 사라진 것처럼 보임.

**최초 실제 오류**
- `ModernUI::resetControlTheme`가 `SetWindowTheme(hwnd, NULL, NULL)`을 사용하고 있었다. 이 호출은 themed rendering disable이 아니라 default visual-style association 복원이라 custom Dark paint와 native light chrome이 계속 혼재했다.
- `CfgDlg` child page 전체에 rounded window region을 적용했지만 canonical RC에는 x/y==0에서 시작하는 control이 다수 있어 page corner region이 실제 child control 영역을 잘랐다.
- `ModernGroupBoxSubclassProc`가 BS_GROUPBOX의 전체 rect를 `mElevated` rounded card로 채워 resource grouping box마다 큰 검은 island를 만들었다.
- CfgDlg의 page-local BS_PUSHBUTTON/BS_DEFPUSHBUTTON은 dark paint adapter 대상이 아니었다.
- BCMenu `drawIcon`은 legacy source icon을 `DrawIconEx(... DI_NORMAL)`로 그대로 그려 popup ThemePalette와 icon luminance/contrast ownership이 분리되어 있었다.

**원인 진단**
- Root cause: "native theme reset", "page rounding", "group card", "menu icon"을 각각 현대화 요소로 추가했지만 실제 Win32 paint/geometry ownership을 하나의 hierarchy로 검증하지 않았다.
- Observed: main settings/footer 일부는 custom dark paint인데 page-local buttons과 themed borders는 native light path가 남았다.
- Observed: resource-defined groupbox/page geometry는 legacy DLU 좌표를 그대로 사용하는데 window-region clipping과 larger visual layers를 추가해 control bounds와 충돌했다.
- Observed: legacy menu bitmap은 색상형 source이므로 Dark popup에서 원본 색을 유지하면 Fluent/Win11 command-menu icon weight와 맞지 않는다.

**해결 방법**
- `gui/ModernUI.cpp`: `resetControlTheme`이 documented `SetWindowTheme(hwnd, L"", L"")`을 사용해 실제 themed painting을 disable하도록 수정했다.
- `cfg/cfg_dlg.cpp`: Dark/non-HC Explorer-owned edit/list/combo 계열은 theme disable 후 palette path가 surface를 소유한다.
- `cfg/cfg_dlg.cpp`: groupbox를 전체 rounded card로 채우지 않고 page background + section label + subtle separator로 변경했다.
- `cfg/cfg_dlg.cpp`: BS_PUSHBUTTON/BS_DEFPUSHBUTTON용 Dark paint adapter를 추가해 page-local button도 같은 palette hierarchy를 사용한다.
- `cfg/cfg_dlg.cpp`, `cfg/cfg_main_dlg.cpp`: child page 자체 rounded window region을 제거해 x/y==0 resource control clipping을 방지했다.
- `gui/BCMenu.cpp`: non-HC menu icon을 documented `DrawState(... DST_ICON | DSS_MONO)`로 palette text/secondary-text color에 tint하고 High Contrast는 원본/system path로 fallback한다.
- 비집중 control border는 `mBorder`보다 약한 `mSeparator`를 사용해 흰 외곽선처럼 보이는 대비를 낮췄다.

**재발 방지**
- `build/validate_source_invariants.py`가 `SetWindowTheme(hwnd, L"", L"")` disable contract를 검사하고 `NULL,NULL` reset이 되돌아오는 것을 금지한다.
- settings guard가 page pushbutton adapter, page-region clearing, dark control theme ownership, flat groupbox hierarchy를 검사한다.
- popup guard가 `DrawState`, `DST_ICON | DSS_MONO`, disabled secondary-text tint를 검사한다.
- Win11 visual modernization에서 resource page 전체에 rounded window region을 적용하지 않는다. rounding은 control/surface 단위로만 적용하고 RC의 actual child bounds를 먼저 확인한다.

**검증 상태**
- 사용자 screenshot evidence: FAIL — 수정 전 검은 group card, white/mixed controls, clipped page details, overbright/hidden menu icons 확인.
- Static/source self-review: PASS — 수정 후 paint ownership/token/diff를 repository source에서 대조.
- `python build/validate_source_invariants.py`: NOT TESTED.
- Compile/link: NOT TESTED.
- Functional/runtime: NOT TESTED.
- 수정 후 Windows 11 Light/Dark/System/High Contrast 및 DPI visual: NOT TESTED.

**관련 commit**
- `b8ae8e3e` — `fix: actually disable native theme for owned dark controls`
- `c67ee1a6` — `ui: tint popup icons for dark menu contrast`
- `2131d37e` — `ui: unify dark settings control surfaces`
- `03f8ec1a` — `ui: stop clipping dark settings pages`
- `95f2eb98`, `46a85be4`, `4ddf1269` — settings border softening
- `a8dc5380` — `test: guard coherent dark settings and menu icons`

---


## 2026-09-23 — BCMenu DrawState 호출 인자 수 오류로 Release x64 compile 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64` → `Release-x64-Unicode | x64`.
- source invariant/regression preflight와 VS 2026/v145 solution 생성은 PASS했지만 `src/fxfile/gui/BCMenu.cpp(1185)`에서 C2660으로 compile이 중단됐다.
- 최초 실제 compiler error: `DrawState: 함수는 11개의 인수를 사용하지 않습니다.`

**최초 실제 오류**
- popup icon monochrome tint를 추가하면서 Win32 `DrawState` 호출을
  `HDC, NULL, HBRUSH, NULL, icon, ...` 순서로 작성해 11개 인자를 전달했다.
- Win32 signature는 `HDC, HBRUSH, DRAWSTATEPROC, LPARAM, WPARAM, x, y, cx, cy, flags`의 10개 인자다.

**원인 진단**
- Root cause: GDI API의 parameter ownership을 확인하지 않고 brush와 callback 사이에 불필요한 null placeholder를 추가했다.
- 기존 static guard는 `DrawState(` 및 `DST_ICON | DSS_MONO` token 존재만 검사해 실제 arity/order 오류를 잡지 못했다.

**해결 방법**
- `gui/BCMenu.cpp`: `DrawState(aDC->m_hDC, sBrush, XPR_NULL, reinterpret_cast<LPARAM>(sIcon), 0, ...)`의 documented 10-argument signature로 수정했다.
- menu icon의 ThemePalette monochrome tint semantics 자체는 유지했다.

**재발 방지**
- `build/validate_source_invariants.py`에 DrawState 호출의 첫 인자 순서를 regex로 검증하는 guard를 추가했다.
- `aDC->m_hDC, XPR_NULL, sBrush`의 과거 11-argument ordering이 돌아오면 preflight에서 실패한다.

**검증 상태**
- 사용자 로컬 evidence: source invariant PASS, VS 2026/v145 generation PASS, 수정 전 Release x64 compile FAIL.
- 수정 후 static/source self-review: PASS.
- 수정 후 `local_ci.bat x64` / compile/link/runtime: NOT TESTED.
- 현재 사용자 지시에 따라 CI 범위는 `Release-x64-Unicode | x64`로 한정한다. x86/Multibyte/release/full matrix는 별도 지시 전까지 실행하지 않는다.

**관련 commit**
- `c9fbb7d5` — `fix: use Win32 DrawState signature correctly`
- `7440a6a0` — `test: guard Win32 DrawState menu icon signature`
- `4ae5f7e6` — `docs: scope active CI to Release x64 Unicode`

---


## 2026-09-23 — Settings Style control 가림 / Dark Edit edge / Fluent menu icon gate 회귀

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- `환경 설정 > 모양 및 테마 > 레이아웃`의 `스타일` section은 제목/영역만 보이고 내부 Standard/Basic style 선택 항목이 보이지 않았다.
- `환경 설정 > 일반 > 시작 폴더`의 path Edit 주변에 Dark surface와 맞지 않는 밝은 native edge가 남았다.
- app-owned popup menu는 일부 command icon이 여전히 legacy 느낌이거나 아예 보이지 않는 상태였고, Main Toolbar도 9개 command만 Fluent runtime artwork를 사용해 기본 표시 command 대부분이 legacy였다.

**최초 실제 오류**
- `IDD_CFG_APPEARANCE_LAYOUT` resource에는 `IDC_CFG_LAYOUT_INFO_BAR_STANDARD_STYLE` / `IDC_CFG_LAYOUT_INFO_BAR_BASIC_STYLE`가 실제로 존재하고 init/enable logic도 정상이다. 하지만 `GROUPBOX`가 sibling control 뒤에 선언되어 있고 `ModernGroupBoxSubclassProc`가 전체 client rect를 불투명하게 owner-paint해 sibling radio/check control을 덮을 수 있었다.
- settings Edit는 native non-client border를 유지한 채 CTLCOLOR/client surface만 Dark palette로 바뀌어 multi-pixel `WS_BORDER` / themed edge가 일부 DPI에서 밝게 남을 수 있었다.
- BCMenu의 Fluent draw path가 legacy `menuIconNormal >= 0 && bitmap != NULL` 조건 뒤에 있어, Fluent registry에 command가 있어도 legacy bitmap이 없는 menu item은 Fluent icon을 그릴 기회가 없었다.
- Main Toolbar의 Fluent registry가 9개 command에만 한정되어 있었다.

**원인 진단**
- Root cause 1: legacy RC의 groupbox z-order와 opaque custom groupbox paint ownership을 함께 고려하지 않았다.
- Root cause 2: Dark Edit의 client background와 non-client border ownership을 분리해서 처리했다.
- Root cause 3: Fluent artwork source가 Main Toolbar private path에 묶여 있었고 BCMenu 표시 여부가 legacy bitmap 존재 여부에 종속되어 있었다.
- Root cause 4: 대표 command migration을 실제 default-visible command coverage로 확대하지 않아 한 화면 안에 Fluent/legacy artwork가 과도하게 혼재했다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: GROUPBOX를 transparent section-label container로 유지하고 `HWND_BOTTOM`에 배치한다. child traversal은 z-order 변경 전에 next sibling을 저장해 누락/반복을 방지한다.
- `cfg/cfg_dlg.cpp`: `ModernCfgEditSubclassProc`가 Dark/non-HC의 `WM_NCPAINT` 후 전체 native non-client band를 `mElevated`로 덮고 normal `mSeparator` / focus `mFocus` frame을 소유한다. native Edit input/caret/selection/IME/clipboard semantics는 그대로 둔다.
- `gui/FluentCommandIcons.*`: command-ID 기반 shared Fluent runtime adapter를 추가해 generated mask를 Main Toolbar와 BCMenu가 공유한다.
- `gui/BCMenu.cpp`: legacy bitmap이 없어도 shared registry에 command ID가 있으면 Fluent icon을 우선 그린다. check/radio item semantics와 legacy fallback은 유지한다.
- Main Toolbar manifest/runtime coverage를 23개 command로 확장했다. 이 중 기본 표시 21개 command는 전부 Fluent registry 대상이며 optional History/Settings도 포함한다.
- CfgMainDlg navigation은 33-frame legacy bitmap fallback을 유지하면서 의미가 명확한 17개 category image index를 non-High-Contrast에서 shared Fluent registry로 overlay한다.
- popup menu의 padding/shortcut gap/icon gutter와 accelerator/chevron text role을 조정해 primary text와 secondary metadata hierarchy를 분리했다.

**재발 방지**
- `build/validate_source_invariants.py`가 GROUPBOX transparency/z-order, stable child traversal, Dark Edit NC-frame ownership을 검사한다.
- Fluent validator는 `toolbar_manifest.json`을 canonical source로 파싱하고 23-command coverage, 기본 표시 21개 command mapping, SVG/GYP registration, generated-mask determinism, Main Toolbar/BCMenu shared registry wiring을 검사한다.
- settings navigation guard는 `config_tree.bmp` 33-frame fallback과 runtime Fluent overlay가 함께 유지되는지 검사한다.

**검증 상태**
- 사용자 screenshot evidence: FAIL — 수정 전 Layout Style 항목 가림, 밝은 folder Edit edge, legacy/missing popup icon 및 혼합 toolbar artwork 확인.
- Static/source self-review: PASS — resource/init logic과 paint/icon ownership을 latest main source에서 대조.
- `python build/validate_source_invariants.py`: NOT TESTED.
- `Release-x64-Unicode | x64` compile/link + functional regression + runtime smoke: NOT TESTED.
- 수정 후 Windows 11 visual/manual 및 DPI 100/125/150/200%: NOT TESTED.

**관련 commit**
- `59088311`, `daad8b57`, `78a34994` — settings group/edit ownership 수정
- `5882dc13`, `e1987bc8`, `654aac89`, `e2d87520` — shared Fluent command-icon path
- `27c2ea41` ~ `41f011b4` — 23-command manifest/mask/default-toolbar migration
- `7c395e6a`, `279ba426` — popup metric/text hierarchy 정리
- `6a0a986d` — settings navigation Fluent overlay
- `ad56d3dc`, `5d971fff` — manifest/settings regression guards

---

## 2026-09-23 — native functional regression harness의 XPR lifecycle 누락

**오류 발생**
- 확인 경로: 현재 native functional regression harness source/contract audit.
- `src/fxfile-tests/functional_tests.cpp`는 production `xpr::FileSys` / `xpr::FileIo`를 직접 사용하면서 product executable이 수행하는 XPR runtime initialize/finalize lifecycle을 명시적으로 갖고 있지 않았다.

**최초 실제 오류**
- 테스트 entry point가 fixture 생성과 production XPR API 호출 전에 `xpr::initialize()`를 호출하지 않았고, 종료 경로에도 `xpr::finalize()`가 없었다.
- 이는 테스트가 production runtime initialization contract를 우연한 process state에 의존하게 만드는 harness-level 결함이다.

**원인 진단**
- Observed: main application과 updater는 startup/exit에서 XPR lifecycle을 명시적으로 소유하지만 standalone functional-test executable은 동일 ownership을 빠뜨렸다.
- Root cause: product API를 직접 재사용하는 standalone test target을 추가하면서 library dependency/include wiring은 맞췄지만 process-level runtime lifecycle까지 test entry point 계약에 포함하지 않았다.

**해결 방법**
- `src/fxfile-tests/functional_tests.cpp`: `_tmain()` 시작에서 `xpr::initialize()` 성공을 확인한다.
- fixture setup 실패와 정상 test summary 종료 경로에서 `xpr::finalize()`를 호출한다.
- 실제 test result exit code는 finalize 전에 보존해 기존 PASS/FAIL semantics를 유지한다.

**재발 방지**
- `build/validate_source_invariants.py::validate_functional_test_wiring()`이 `xpr::initialize()` / `xpr::finalize()` token을 functional-test lifecycle contract로 검사한다.
- standalone executable test가 production runtime/library API를 직접 사용할 때 process initialization/finalization contract도 함께 확인한다.

**검증 상태**
- Static/source self-review: PASS — functional-test entry point와 invariant guard가 latest main에서 함께 존재함을 확인.
- `python build/validate_source_invariants.py`: NOT TESTED in this connector environment.
- `local_ci.bat x64` / `Release-x64-Unicode | x64` functional regression: NOT TESTED after this lifecycle fix.
- UI/runtime visual: 해당 없음.

**관련 commit**
- `1eb5ff24` — `test: initialize XPR runtime in functional regression`
- `7c9b69f4` — `test: guard functional XPR lifecycle`

---

## 2026-09-23 — build 성공 후에도 legacy toolbar 상태가 Win11 command-bar 변경을 덮어씀

**오류 발생**
- 실행/환경: 사용자 Windows 11 실제 실행. C++ build 자체는 성공했지만 상단 toolbar의 작은 icon/legacy-looking command surface와 text 대비 문제가 그대로 보였다.
- 새 기본값을 22px Fluent large icon으로 바꿔도 기존 사용자 화면이 즉시 달라지지 않았다.

**최초 실제 오류**
- `MainToolBar::Init()`은 기본 icon type을 `TBI_LARGE`로 설정하지만, `MainToolBar::load()`가 기존 `fxfile-toolbar.dat`의 persisted `TBI_SMALL` 값을 다시 적용했다.
- ToolbarWindow32 custom draw는 ThemePalette의 `clrText`를 채우고 있었지만 `TBCDRF_USECDCOLORS` 및 highlighted-text/background-mode contract가 없어 hot/selected state에서 system color가 다시 개입할 수 있었다.

**원인 진단**
- Observed: old toolbar state file format은 text type, icon type, command IDs만 저장하며 version/migration marker가 없었다.
- Root cause 1: source default 변경과 persisted user state migration을 동일한 것으로 취급했다.
- Root cause 2: ToolbarWindow32가 custom-draw color fields를 실제 text rendering에 사용하도록 명시하는 return flag/state color wiring이 불완전했다.

**해결 방법**
- `src/fxfile/main_toolbar.cpp`: legacy-format file에서만 historical `TBI_SMALL`을 `TBI_LARGE`로 1회 migration한다.
- 새 저장 파일에는 `kModernToolbarStateMarker`를 append한다. 기존 reader는 unknown command id로 무시하므로 layout format의 downgrade tolerance를 유지한다.
- marker가 있는 새 파일에서는 사용자가 이후 명시적으로 Small을 선택한 경우 그대로 보존한다.
- `ToolBarEx.cpp` / `MenuBar.cpp`: `TBCDRF_USECDCOLORS`, `clrTextHighlight`, transparent string background mode를 함께 설정해 normal/hot/selected text가 동일 ThemePalette를 사용하게 했다.

**재발 방지**
- `build/validate_source_invariants.py`가 one-time migration marker/read/write contract와 ToolbarWindow32 highlighted-text palette wiring을 검사한다.
- default UI 값 변경 시 persisted legacy state가 startup에서 다시 덮어쓰는지 함께 확인한다. migration은 user preference를 영구 무시하지 않도록 version/marker를 둔다.

**검증 상태**
- Targeted static audit: PASS — branch source에서 marker read/write, legacy-only migration, TBCDRF_USECDCOLORS, highlighted text/transparent background wiring 확인.
- `python build/validate_source_invariants.py`: NOT TESTED — connector 환경에는 repository checkout command 실행 경로가 없음.
- Compile/link / functional regression / runtime visual: NOT TESTED after these commits. 사용자 Windows에서 `local_ci.bat x64` 및 실제 화면 재확인 필요.

**관련 commit**
- `e97d0258` — `ui: migrate legacy small toolbar icons`
- `f01ddbea`, `e45778dd` — command/menu palette color ownership
- `de06e5ff` — `fix: migrate toolbar icon size only once`
- `fdfde0dd`, `4f6b51ec` — highlighted command/menu text palette
- `b25b70e3`, `af48a099` — regression guards

---

## 2026-09-23 — AddressBar nested legacy edge와 standard-user config path가 build 성공 뒤 runtime 증상으로 남음

**오류 발생**
- 실행/환경: 사용자 Windows 11 실제 실행에서 build는 성공했지만 AddressBar 내부 folder/path 영역에 별도 사각 edge가 남고, 일반 사용자 권한 실행 경로에 대한 문제가 계속 보고됐다.
- 이 항목은 두 runtime ownership 결함을 분리해 기록한다.

**최초 실제 오류**
- AddressBar outer ComboBoxEx는 palette-owned frame을 그리지만 child Edit의 legacy `WS_EX_CLIENTEDGE`가 그대로 남아 outer frame 안에 두 번째 native edge가 생길 수 있었다.
- `ConfDir::load()`은 persisted `conf_home`이 존재하는 directory인지 여부만 사실상 신뢰했고, Program Files 아래 `%fxfile%\\conf`처럼 읽기는 가능하지만 standard user에게 쓰기 불가능한 legacy portable path를 정상 save target처럼 유지할 수 있었다.
- `OptionManager::load()`은 configuration load 실패 시 즉시 default file을 저장하려 하므로 unwritable path에서는 startup/config initialization 흐름이 관리자 권한 여부에 따라 달라질 수 있었다.

**원인 진단**
- Root cause 1: AddressBar client/background paint와 child Edit non-client frame ownership을 분리해서 처리했다.
- Root cause 2: configuration directory의 "존재함"과 "현재 token으로 실제 writable함"을 동일하게 취급했다.
- 제한: 사용자의 실제 `.fxfile` 내용은 connector에서 읽지 않았으므로 해당 사용자의 persisted `conf_home` 값 자체는 미확인이다. 다만 위 경로 조건에서 발생하는 product defect는 source로 확인된다.

**해결 방법**
- `src/fxfile/address_bar.cpp`: non-High-Contrast에서 child Edit의 기존 `WS_EX_CLIENTEDGE` 상태를 기억한 뒤 제거하고, High Contrast에서만 원래 native edge를 복원한다. Combo/Edit background erase도 ThemePalette brush가 소유한다.
- `src/fxfile/conf_dir.cpp`: configured/default config directory에 실제 probe file create/delete를 수행해 writable 여부를 확인한다.
- 기존 persisted custom/portable path가 unwritable이면 `%AppData%\\fxfile\\conf`로 fallback하고, recovered path를 다시 descriptor에 저장해 다음 startup도 standard-user path를 사용하게 한다.

**재발 방지**
- source invariant가 AddressBar single-frame token, writable config probe/fallback/persist contract를 검사한다.
- 설치 위치가 Program Files일 수 있는 desktop app에서는 user config writeability를 directory existence만으로 판단하지 않는다.
- custom Dark frame을 소유하는 composite control은 child native non-client style까지 함께 audit한다.

**검증 상태**
- Targeted static audit: PASS — branch source에서 Edit edge removal/HC restore, writable probe, fallback/persist wiring 확인.
- Compile/link / runtime standard-user startup / visual AddressBar: NOT TESTED after these commits.
- settings theme refresh reentrancy guard도 branch에 포함되어 있으나 실제 crash stack evidence가 없어 별도 root cause로 확정하지 않는다.

**관련 commit**
- `6bd4ff31` — `fix: remove nested legacy address field frame`
- `1a2dfe1d`, `b5055009` — standard-user config fallback
- `673c2184` ~ `266603f2` — settings theme-refresh reentrancy guard
- `c81f37df` — runtime UI fix guards

---

## 2026-09-23 — 동일 control theme association 반복 적용이 settings/UI thread를 다시 막을 수 있었음

**오류 발생**
- 사용자 Windows 11 screenshot에서 `fxfile (응답 없음)` 상태가 다시 확인됐다.
- 이전 WER/cdb evidence에서는 `uxtheme!SetWindowTheme -> ModernUI::applyExplorerControlTheme -> WM_THEMECHANGED handler`가 반복되는 stack이 관찰됐다.
- 기존 수정은 `SetWindowTheme` 호출 중의 synchronous re-entry만 guard했기 때문에, 호출이 끝난 뒤 전달되는 후속 `WM_THEMECHANGED`가 동일 association을 다시 설정하는 경우를 막지 못했다.

**최초 실제 오류**
- `ModernUI::applyExplorerControlTheme()` / `resetControlTheme()`가 현재 HWND에 이미 같은 association이 적용돼 있는지를 기억하지 않았다.
- settings host/page의 `OnThemeChanged`가 다시 전체 child tree를 순회하며 control theme helper를 호출했다.

**원인 진단**
- Root cause: "현재 SetWindowTheme call 안에 있는가"와 "이 HWND가 이미 원하는 theme association 상태인가"를 같은 문제로 취급했다.
- synchronous call-stack recursion guard만으로는 message-queue를 거쳐 다시 발생하는 동일 association 적용 loop를 방지할 수 없다.

**해결 방법**
- `ModernUI.cpp`: HWND property에 Explorer/Default/Disabled association 상태를 기록하고 동일 association 요청은 `SetWindowTheme` 자체를 생략한다.
- 기존 call-stack guard는 nested synchronous notification 방어용으로 유지한다.
- `CfgMainDlg` / `CfgDlg`: `WM_THEMECHANGED`에서는 palette/font/frame repaint만 수행하고 child theme association을 다시 순회하지 않는다. 최초 생성/settings/system-color/DPI refresh에서는 기존 전체 적용 경로를 유지한다.

**재발 방지**
- source invariant가 theme-association state property, identical-request skip, settings의 `refreshModernAppearance(XPR_FALSE)` contract를 검사한다.
- `WM_THEMECHANGED` handler에서 `SetWindowTheme`를 다시 호출하는 경로는 call-stack guard뿐 아니라 desired-state idempotence까지 확인한다.

**검증 상태**
- 이전 WER/cdb stack evidence: CONFIRMED — `SetWindowTheme` / `WM_THEMECHANGED` 반복 경로가 관찰됨.
- Targeted static audit: PASS — desired association cache 및 settings paint-only notification 경로 확인.
- `python build/validate_source_invariants.py`: NOT TESTED in connector environment.
- Compile/link / Preferences 10회 open-close / runtime hang: NOT TESTED after this fix.

**관련 commit**
- `35594b5e` — `fix: make control theme changes idempotent`
- `b66b7d82` — association regression guard
- `b8bef073` ~ `deb887c1` — settings host/page paint-only theme notification
- `9a0666cc` — settings refresh regression guard

---

## 2026-09-23 — standard-user 경로에 machine-wide shell registration과 과도한 mutex access가 남아 있었음

**오류 발생**
- 사용자에게 관리자 권한 없이 실행/설정하는 경로가 정상 동작하지 않는 문제가 계속 보고됐다.
- manifest는 이미 `asInvoker`였고 configuration 기본 경로도 AppData였으므로, 남은 권한 의존 API를 추가 audit했다.

**최초 실제 오류**
- `ShellRegistry`가 `HKEY_CLASSES_ROOT\\Folder\\Shell`에 context-menu registration을 직접 쓰고 있었다.
- `SingleProcess::check()`가 단순한 named mutex 존재 확인에 `MUTEX_ALL_ACCESS`를 요청하고 있었다.

**원인 진단**
- HKCR write는 merged machine/user class view에 대한 legacy registration 방식이며 standard-user settings 적용에서 권한 차이를 만들 수 있다.
- named mutex 존재 확인에 all-access는 불필요하며, 기존 elevated instance와 standard-user instance 사이에서 access-denied를 "mutex가 없음"으로 오판할 수 있다.
- 제한: screenshot의 `관리자:` 표시는 실행된 process가 elevated라는 evidence지만, elevation이 shortcut/AppCompat 설정에서 강제됐는지는 repository source만으로 확인할 수 없다.

**해결 방법**
- shell context menu는 `HKCU\\Software\\Classes\\Folder\\Shell` 아래 per-user registration으로 이동했다. Explorer의 HKCR merged view에서는 동일하게 노출된다.
- single-process presence check는 `SYNCHRONIZE`만 요청하고, minimal open에서도 `ERROR_ACCESS_DENIED`이면 named object가 존재하는 것으로 처리한다.
- 기존 `asInvoker` manifest와 AppData configuration contract는 유지한다.

**재발 방지**
- source invariant가 shell registration에서 HKCR write를 금지하고 HKCU Classes path를 요구한다.
- mutex presence check에서 `MUTEX_ALL_ACCESS` 재도입을 금지한다.

**검증 상태**
- Targeted static audit: PASS — shell registry와 mutex access source contract 확인.
- standard-user clean launch / elevated-existing-instance interop: NOT TESTED after this fix.
- repository source에는 product manifest의 `requireAdministrator` / `highestAvailable` 설정이 없음.

**관련 commit**
- `253839b7` — `fix: register shell menu per user`
- `e03f5155` — per-user shell regression guard
- `1bdd46c2` — `fix: remove elevation-dependent mutex access`
- `c0c3fd55` — standard-user mutex regression guard

---

## 2026-09-23 — AddressBar와 coolbar legacy child geometry가 Win11 surface를 다시 덮어씀

**오류 발생**
- 기존 AddressBar 수정 뒤에도 사용자 보고에서 folder/path field의 별도 사각 frame과 command icon layout 문제가 남았다.

**최초 실제 오류**
- 이전 AddressBar fix는 child Edit의 `WS_EX_CLIENTEDGE`만 제거했다. 내부 ComboBox와 Edit의 `WS_BORDER` 및 ComboBox의 `WS_EX_CLIENTEDGE`는 그대로 남을 수 있었다.
- `MainCoolBar::loadStateFile()`은 Win11 command metrics가 계산된 뒤 legacy coolbar의 persisted `cx/cxMinChild` 값을 다시 적용했다. Main toolbar는 후속 load에서 자체 size refresh를 하지만 drive/bookmark band는 legacy geometry가 마지막 값이 될 수 있었다.

**원인 진단**
- composite address control에서 outer ComboBoxEx만 modern frame ownership을 가져야 하지만 nested child non-client styles를 완전히 제거하지 않았다.
- command button/icon 크기 migration과 rebar band geometry migration을 별개 persistence layer로 보지 않았다.

**해결 방법**
- non-High-Contrast AddressBar에서 nested ComboBox/Edit의 `WS_BORDER`와 `WS_EX_CLIENTEDGE`를 모두 제거하고 original state를 HWND property에 보관한다.
- High Contrast에서는 original native border state를 복원한다.
- legacy coolbar state restore가 끝난 뒤 main/drive/bookmark toolbar 모두 `UpdateToolbarSize()`를 다시 실행해 current command metrics가 최종 band child size를 결정하도록 했다.

**재발 방지**
- source invariant가 ComboBox/Edit 양쪽 border/client-edge 제거와 High Contrast restore에 필요한 state token을 검사한다.
- persisted rebar state restore 뒤 세 toolbar의 post-restore metric recalculation을 검사한다.

**검증 상태**
- Targeted static audit: PASS — nested border removal/restore 및 post-restore toolbar sizing source 확인.
- Windows 11 AddressBar visual / command-bar icon spacing: NOT TESTED after this fix.
- hung-window ghost screenshot의 회색/희미한 rendering은 정상-state palette evidence로 사용하지 않는다.

**관련 commit**
- `265161ab` — `fix: remove nested address control borders`
- `7bb4a027` — AddressBar single-frame regression guard
- `08186e67` — `ui: recalc command bars after legacy state restore`
- `678ef5a0` — post-restore command-bar metric guard

---

## 오류를 예방하기 위한 일반 개발 규칙

1. 새 header/API/macro는 소유 header를 직접 include한다. PCH/transitive include에 기대지 않는다.
2. generated project가 아니라 GYP/build canonical source에서 dependency와 configuration을 고친다.
3. 첫 실제 compiler/linker/CI orchestration error를 먼저 고친다. cascade 숫자를 결함 개수로 해석하지 않는다.
4. CI/build script 안에 다른 shell 언어를 embed할 때 cmd/PowerShell quoting과 escape 책임 경계를 분리한다.
5. static validator는 가능한 한 deterministic contract를 검사하되, 단순 문자열 token 때문에 정상 코드를 거짓 실패시키지 않도록 실제 syntax/format 변형을 고려한다.
6. 오류를 한 번 고친 후 반복 가능성이 있으면 가장 싼 자동 방어선을 같이 추가한다.
7. 제품 build PASS와 CI orchestration PASS, runtime PASS, visual PASS는 서로 다른 evidence로 기록한다.
8. Win32/MFC의 unsigned field와 signed DPI/metric/helper 값을 직접 비교하지 않는다. 값의 의미와 범위를 확인한 뒤 비교 경계에서 같은 타입으로 정규화한다.
9. DPI-aware draw/layout fragment를 함수 간 이동할 때 HWND/DPI metric context의 선언과 fallback도 함께 이동한다. renderer는 다른 함수의 local setup을 암묵적으로 전제하지 않는다.


## 2026-09-23 - Protected install-path migration and legacy owner-draw dark colors

### Standard-user migration path

**Occurrence**
- Source review of the standard-user startup/configuration path found two legacy migrations that still assumed the source directory was writable.
- This is relevant when an older portable profile or `accel.fac` is beside `fxfile.exe` under a protected installation directory such as Program Files.

**First actual source error**
- `ConfDir::moveToNewConfDir()` used a rename from the old configuration directory to the new per-user directory. Renaming requires delete/write access to the old directory.
- `MainFrame::loadAccelTable()` used a move of legacy `accel.fac` out of the executable directory, which has the same protected-source write/delete requirement.

**Cause**
- The migration logic treated a readable legacy install directory as if it were also writable.
- The current per-user destination was already designed to be writable, so requiring source deletion was unnecessary.

**Fix**
- Configuration migration now copies each existing file to the already validated destination and treats removal of the old source as best-effort cleanup.
- Legacy `accel.fac` migration now copies into `ConfDir::TypeAccel` instead of moving the install-directory file.
- The single-instance handoff also allows only the registered activation message through `ChangeWindowMessageFilterEx` when available, so a normal-integrity second launch does not need to elevate merely to wake an already elevated first instance.

**Prevention**
- `validate_source_invariants.py` checks that the legacy accel path uses `CopyFile`, configuration migration no longer uses `xpr::FileSys::rename`, and the cross-integrity handoff remains dynamically resolved for the legacy target headers.

**Validation**
- GitHub source review confirms the protected-source rename/move calls were replaced and the invariant contracts are present.
- `python build/validate_source_invariants.py`, MSVC compile/link, standard-user launch, elevated/non-elevated handoff, and Windows runtime smoke are **NOT TESTED** in the connector-only environment.

### Legacy owner-draw controls on Dark settings surfaces

**Occurrence**
- Source review found legacy owner-draw controls still selecting native light/system text and 3D colors while their parent settings surfaces were palette-owned Dark UI.
- Affected reviewed controls included `CButtonST`, `CDropMenuButton`, `CColourPickerXP`, the file-scrap pane, bookmark labels, and the search-location dialog.

**First actual source error**
- Split-button arrows and owner-draw button borders retained hard-coded black/light-system paths.
- The colour picker continued to use themed/light common-control painting and menu/system text colors in its owner-draw path.
- File-scrap/search-location paint paths could select native button/window text colors independently of the app Dark palette.

**Cause**
- These controls predate the shared `ModernUI::ThemePalette` ownership model and were not fully covered by parent `WM_CTLCOLOR` handling because they paint their own text, borders, arrows, or popup cells.

**Fix**
- Owner-draw text, disabled text, border, focus, hover/pressed, separator, and arrow colors now use `ThemePalette` outside High Contrast.
- The colour picker bypasses native light themed painting on app-owned Dark surfaces and uses the shared Windows UI font; its popup re-resolves that font after HWND creation so monitor DPI is available.
- File-scrap/bookmark labels use `ModernUI::getUIFont`, while High Contrast retains system-owned colors.

**Prevention**
- Source-invariant checks guard the palette-aware owner-draw paths, colour-picker popup font path, and file-scrap/bookmark typography contracts.

**Validation**
- Connector-side source inspection confirms the new palette/font branches and matching declarations are present.
- Windows 11 Light/Dark/System/High Contrast visual checks, 100/125/150/200% DPI checks, Korean text/IME checks, MSVC compile/link, and runtime behavior are **NOT TESTED** here.


### Dark filtered list text and menu state glyphs

**Occurrence**
- Continued source audit of the reported Dark-mode black-text inconsistency found two paint paths that were still able to select black/system-menu foreground colors independently of the Dark palette.

**First actual source error**
- When file-list text color mode was `COLOR_TYPE_FILTERING`, the historical general-file `*.*` filter supplied `RGB(0, 0, 0)` directly to list-view custom draw. That legacy default is readable on a light surface but can become black-on-dark.
- `BCMenu::Draw3DCheckmark()` always used `COLOR_MENUTEXT`, so app-owned checked/radio glyphs could remain dark even when the popup surface was Dark.

**Cause**
- Filter colors predate the app theme and encode the old light-surface general-file default as literal black rather than an automatic text semantic.
- The legacy menu-state helper bypassed the newer `ThemePalette` text/selection colors.

**Fix**
- The file-list filtering path treats only the historical general-file signature (`*.*` + pure black) and a missing filter as automatic text in app Dark/non-High-Contrast, using `ThemePalette.mText`. Other explicit filter colors and all background-filter colors remain unchanged.
- `BCMenu::Draw3DCheckmark()` now uses palette text/selection-text outside High Contrast and system menu/highlight text in High Contrast.
- Legacy owner-draw buttons/split buttons also resolve `ModernUI::getUIFont` when they do not already have a control font, and drag feedback uses the same shared Windows UI font.

**Prevention**
- Source invariants guard the legacy `*.*` black-text fallback, preserve background-filter routing, require palette-aware menu check/radio glyphs, and require shared Windows UI font fallback for reviewed owner-draw/transient text paths.

**Validation**
- Connector-side source inspection confirms the targeted paint/font branches and invariant tokens are present.
- `python build/validate_source_invariants.py`, MSVC compile/link, Windows 11 runtime Dark visual checks, user filtering-mode state, menu checked/radio rendering, DPI checks, and Korean text rendering are **NOT TESTED** in this connector-only environment.

**Related commits**
- `a45dbcb6` — `ui: keep legacy filtered text readable in dark mode`
- `be135783` — `ui: keep menu checkmarks readable in dark mode`
- `60ce7b8e`, `c3e6e8c8` — owner-draw Windows UI font fallbacks
- `188d1f6d` — drag-feedback Windows UI font
- `7d4e8a35`, `d96347de` — regression guards

---

## 2026-09-23 — 공용 dialog Dark theme와 elevated installer 자동 실행이 이전 수정 범위 밖에 남아 있었음

**오류 발생**
- 최근 runtime/UI 안정화 커밋들을 `main`에 통합한 뒤에도 사용자가 기존 오류가 그대로 재현된다고 보고했다.
- 이전 수정은 settings host/page의 theme 재진입과 제품 manifest/HKCU 권한 경로를 중심으로 닫았지만, 공용 dialog base와 실제 installer launch chain은 동일한 범위로 검증하지 않았다.

**최초 실제 오류**
- `CModernDialog`, `CResizingDialog`, `TitleDlg`의 child Edit/Combo/List/Tree/Tab 경로는 Dark/non-High-Contrast에서도 `applyExplorerControlTheme()`를 호출하고 있었다. 이 클래스들은 동시에 ThemePalette 기반 background/text를 직접 소유하므로 settings dialog에서 이미 제거한 native Explorer/light chrome 혼합이 다른 다이얼로그들에는 남아 있었다.
- `dist/setup.nsi`는 `RequestExecutionLevel admin`인 elevated installer이면서 finish page에서 `fxfile.exe`를 실행할 수 있었고, `.onInstSuccess`에서는 `fxfile-launcher.exe`를 자동 시작했다. launcher의 hotkey path는 다시 `ShellExecute`로 `fxfile.exe`를 시작하므로 설치 직후 elevated parent token이 launcher와 후속 fxfile 실행에 이어질 수 있었다.
- 기존 source invariant는 settings의 `refreshModernAppearance(XPR_FALSE)` 토큰과 product manifest의 `asInvoker`만 확인했고, 위 공용 dialog 3종의 Dark association 정책과 elevated installer auto-launch 부재는 검사하지 않았다.

**원인 진단**
- Root cause 1: 동일한 ModernUI 정책을 settings 전용 수정으로 닫고, 실제로 50개 이상의 command/resizable dialog가 공유하는 base class까지 확장하지 않았다.
- Root cause 2: executable manifest 권한과 "누가 executable을 시작하는가"를 별개로 보지 않았다. `asInvoker`는 이미 elevated인 parent에서 시작된 child를 강제로 de-elevate하지 않는다.
- Root cause 3: static regression guard가 수정된 파일의 token 존재만 확인해, 동일 증상을 만드는 다른 활성 경로를 탐지하지 못했다.

**해결 방법**
- `gui/ModernDialog.cpp`, `gui/ResizingDialog.cpp`, `cmd/title_dlg.cpp`: Explorer-theme 대상 child control은 Dark/non-High-Contrast에서 `resetControlTheme()`을 사용하고 Light/System/High Contrast에서는 기존 `applyExplorerControlTheme()` 경로를 유지한다. 기존 HWND association cache는 동일 요청 재적용을 계속 차단한다.
- `dist/setup.nsi`: elevated installer의 finish-page product run과 `.onInstSuccess` launcher 자동 실행을 제거한다. 설치된 fxfile/launcher는 이후 정상 사용자 shell/shortcut 또는 앱 설정 경로에서 시작한다.
- `build/validate_source_invariants.py`: 공용 dialog 3종에 Dark reset + HC fallback 계약을 추가하고, installer에서 finish-page run/`.onInstSuccess`/launcher ExecShell 재도입을 금지한다.
- `build/installer_smoke.ps1`: 동일 elevated auto-launch 부재를 installer smoke contract inspection에서 직접 검사한다.

**재발 방지**
- custom Dark paint를 소유하는 공용 base class는 개별 dialog와 별도로 theme association ownership을 검증한다.
- 권한 문제는 manifest만 보지 않고 installer/launcher/scheduled-startup 등 실제 parent launch chain까지 추적한다.
- "수정된 경로"만 토큰 검사하지 말고 동일 base/active path의 sibling 구현도 invariant 범위에 포함한다.

**검증 상태**
- Connector source audit: PASS — 공용 dialog base의 기존 Explorer-theme 호출, installer elevated auto-launch chain, 기존 invariant 누락을 현재 `main` source에서 확인했다.
- 변경 source self-check: PASS — 세 공용 base에 Dark reset/Light·HC Explorer fallback이 함께 존재하고 installer auto-launch token이 제거되도록 commit 전 검사했다.
- `python build/validate_source_invariants.py`: NOT TESTED — connector 환경에는 repository checkout command 실행 경로가 없다.
- MSVC compile/link, `local_ci.bat x64`, installer 실제 실행, 설치 직후 standard-user token 확인, Windows 11 Light/Dark/System/High Contrast 및 반복 dialog open/close runtime: NOT TESTED.

---

## 2026-09-23 — Preferences 무한 순회와 Dark menu text fallback

**오류 발생**
- 사용자 실제 Windows 11 screenshot에서 상단 menu bar가 Dark chrome 위에 검은 글자를 그려 가독성이 무너졌고, `도구 -> 환경설정`을 열면 여전히 응답없음이 재현됐다.
- screenshot title에는 `관리자: fxfile`도 남아 있어 실행 중인 기존 elevated instance/launcher 상태가 아직 정리되지 않았다는 evidence가 있었지만, 이번 hang 자체는 settings source에서 별도의 결정적 무한 순회 원인을 확인했다.

**최초 실제 오류**
- `CfgDlg::applyModernAppearanceToChild()`는 GROUPBOX를 owner-draw화한 뒤 `SetWindowPos(..., HWND_BOTTOM, ...)`으로 sibling z-order를 바꿨다.
- 동시에 같은 함수와 `applyModernAppearanceToChildren()`가 live sibling chain에서 `GetNextWindow()`를 계속 따라갔다. 두 개 이상의 GROUPBOX가 있으면 현재 항목을 bottom으로 옮길 때 이전 GROUPBOX가 다시 다음 sibling이 되어 A -> B -> A -> B 형태로 반복 방문할 수 있었다. 초기 `CfgGeneralDlg` 자체가 여러 GROUPBOX를 포함하므로 Preferences open 직후 hang과 직접 일치한다.
- `ListCtrlEx` / `TreeCtrlEx`의 Vista-enhanced 경로는 Dark 여부와 무관하게 Explorer theme association을 요구했다. settings parent는 Dark에서 같은 HWND를 `resetControlTheme()` 대상으로 취급하므로 control ownership도 서로 충돌했다.
- `CMenuBar::OnCustomDraw()`는 palette `clrText`를 채웠지만 최종 glyph/text drawing은 ToolbarWindow32 기본 renderer에 남겨두었다. 실제 screenshot에서 Win11 renderer가 dark chrome 위에 검은 `COLOR_BTNTEXT` 계열로 fallback하는 결과가 확인됐다.
- 기존 soft-surface invariant는 오히려 `CWnd *sNextChild = sChild->GetNextWindow()` token을 요구해 z-order 변경 중 live traversal 패턴을 보호하고 있었다.

**원인 진단**
- Root cause 1: paint/z-order mutation과 sibling enumeration을 같은 live list에서 수행했다.
- Root cause 2: `mVistaEnhanced`를 visual-style ownership과 동일시해 palette-owned Dark surface에서도 Explorer association을 복원했다.
- Root cause 3: custom draw color field 설정을 실제 text renderer ownership으로 오해했다. screenshot evidence는 field wiring만으로 최종 text color가 보장되지 않음을 보여줬다.
- Root cause 4: regression guard가 실제 안전 속성이 아니라 당시 구현 token 자체를 고정했다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: 각 parent의 direct child HWND를 `SnapshotChildWindows()`로 먼저 vector에 고정한 뒤 processing한다. GROUPBOX가 `HWND_BOTTOM`으로 이동해도 enumeration 순서는 더 이상 변하지 않는다.
- `gui/ListCtrlEx.cpp`: Vista-enhanced list도 Dark/non-High-Contrast에서는 `resetControlTheme()`을 유지한다. `WM_THEMECHANGED`에서는 `refreshModernAppearance(XPR_FALSE)`로 repaint/header refresh만 수행하고 association을 다시 바꾸지 않는다.
- `gui/TreeCtrlEx.cpp`: Vista-enhanced tree 역시 Dark/non-High-Contrast에서는 Explorer association을 강제하지 않는다.
- `gui/rebar/MenuBar.cpp`: non-High-Contrast Win11 path에서 menu text를 ThemePalette color로 직접 `DrawText`하고 `CDRF_SKIPDEFAULT`로 native toolbar text fallback을 차단한다. keyboard accelerator/focus cue는 `WM_QUERYUISTATE`를 존중한다.
- `build/validate_source_invariants.py`: stable child snapshot을 요구하고 live `GetNextWindow` traversal을 금지하며, List/Tree Dark ownership과 explicit menu text draw를 검사한다.

**재발 방지**
- child z-order/style을 바꾸는 traversal은 대상 HWND를 먼저 snapshot한다.
- behavioral enhancement flag와 visual theme association ownership을 분리한다.
- Dark owner-draw surface에서 native renderer의 color field만 설정한 경우 screenshot/runtime evidence 없이 readability PASS로 간주하지 않는다.
- invariant는 구현 모양보다 안전 속성(안정된 enumeration, notification 중 no-retime, explicit text ownership)을 검사한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — 상단 menu text contrast 실패, Preferences 응답없음 재현.
- Connector source audit: PASS — settings GROUPBOX live traversal cycle, List/Tree association conflict, menu native text ownership을 현재 `main`에서 확인했다.
- 변경 source self-check: PASS — stable HWND snapshot, no-retime `WM_THEMECHANGED`, Dark list/tree reset, explicit menu `DrawText` token을 commit 전 확인했다.
- `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`, Windows 11 Preferences 반복 open/close 및 screenshot visual: NOT TESTED in connector-only environment.

---

## 2026-09-23 — Filtering white surface, address selection box, disabled toolbar glyphs

**오류 발생**
- 사용자 최신 Windows 11 screenshot에서 Dark settings의 Filtering list/header가 흰색으로 남고 일부 기본 filter text가 검게 표시됐다.
- main window address field도 흰색 field와 현재 folder name 주위의 별도 검은 사각형을 보였고, Cut/Copy/Undo 등 실제 toolbar button은 존재하지만 disabled 상태에서 glyph가 보이지 않았다.
- top menu text도 일부 상태에서 여전히 native black fallback이 관찰됐다.

**최초 실제 오류**
- `CfgAppearanceFilteringDlg`는 item custom draw에서 `FilterItem::mColor`만 설정하고 list background/text-background/header renderer는 전혀 Dark palette로 전환하지 않았다. historical default black filter도 그대로 출력했다.
- `AddressBar`는 `CComboBoxEx`에 legacy `CBS_OWNERDRAWFIXED`를 설정했지만 대응 `DrawItem` owner가 없었다. 또한 child edit의 `WM_CTLCOLOREDIT`가 어느 parent HWND로 전달되는지에 따라 inner ComboBox subclass만으로는 palette brush routing이 보장되지 않았다.
- `CToolBarEx::SetIconType()`는 main toolbar에 disabled bitmap resource가 없을 때 disabled image list를 제공하지 않았다. Dark mode는 ToolbarWindow32 theme를 disable하므로 native disabled synthesis에 맡긴 Cut/Copy/Undo glyph가 dark chrome에서 사실상 사라질 수 있었다.
- `CMenuBar` explicit text path는 custom-draw `dwItemSpec`을 command id로만 해석했다. legacy/index-shaped notification에서는 item lookup이 실패해 native text renderer로 되돌아갈 수 있었다.

**원인 진단**
- Root cause 1: parent settings surface만 Dark를 소유하고 legacy child list/header의 final background renderer는 native light 상태로 남았다.
- Root cause 2: composite address control의 border만 제거하고 closed-field owner-draw/style 및 실제 CTLCOLOR message parent를 끝까지 정리하지 않았다.
- Root cause 3: enabled/hot icon overlay만 검증하고 disabled state의 image-list ownership을 검증하지 않았다.
- Root cause 4: menu text 직접 그리기 자체는 추가했지만 item resolution failure가 native fallback을 다시 허용했다.

**해결 방법**
- `cfg_appearance_filtering_dlg.*`: list body에 ThemePalette background/text-background를 적용하고 `FlatHeaderCtrl`로 header를 palette-owned rendering으로 전환한다. legacy pure-black filter text만 Dark에서 automatic `mText`로 처리하고 explicit user colors는 유지한다. Dark list의 legacy native border/client-edge도 제거한다.
- `address_bar.*`: unused `CBS_OWNERDRAWFIXED`를 제거하고 outer `AddressBar` 자체에 `WM_CTLCOLOR` handler를 추가해 Edit/ListBox/Static palette brush가 실제 message parent에서도 적용되도록 한다. 기존 child subclass routing은 fallback/inner-parent 경로로 유지한다.
- `ToolBarEx.cpp`: disabled resource가 없는 Dark toolbar는 cold image list를 duplicate해 explicit disabled image list를 만든다.
- `main_toolbar.cpp`: Fluent migrated frames의 disabled copy는 `ThemePalette.mSecondaryText` 색 glyph로 교체한다.
- `MenuBar.cpp`: custom-draw `dwItemSpec`이 command id로 해석되지 않을 때 유효한 zero-based button index fallback을 사용해 explicit Dark text drawing을 유지한다.
- `validate_source_invariants.py`: Filtering body/header palette, address no-owner-draw + outer CTLCOLOR, explicit disabled image list/Fluent disabled glyph, menu item fallback을 deterministic contract로 추가한다.

**재발 방지**
- Dark child control은 parent palette만 확인하지 말고 body/header/disabled/selection 등 각 최종 renderer state를 screenshot 기준으로 확인한다.
- owner-draw style은 실제 DrawItem/custom-draw owner가 없으면 사용하지 않는다.
- toolbar icon contract는 enabled/hot뿐 아니라 disabled/check/pressed state의 image source까지 포함한다.
- composite control의 CTLCOLOR는 추정 parent가 아니라 실제 outer/inner parent 경로 모두에서 palette routing을 보장한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — Filtering white surface/black text, white address field/black folder rectangle, missing disabled toolbar glyphs, remaining black menu text 확인.
- Connector source audit: PASS — 위 네 source ownership gap을 현재 `main`에서 확인했다.
- 변경 source self-check: PASS — palette list/header, no `CBS_OWNERDRAWFIXED`, outer `ON_WM_CTLCOLOR`, duplicated disabled image list + secondary Fluent glyph, menu index fallback을 commit 전 확인했다.
- `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`, 실제 Windows Light/Dark/System/High Contrast screenshot 및 toolbar enabled/disabled interaction: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Theme switch split-brain, menu native text, list-header clipping

**오류 발생**
- 사용자 최신 screenshot에서 main window는 Dark인데 이미 열린 Preferences는 Light 상태로 남아 한 번의 theme switch가 UI 전체에 원자적으로 적용되지 않았다.
- 같은 Dark main window의 top menu text는 계속 검정/짙은 native foreground로 보였고 file-list header의 `이름 / 크기 / 종류 / 수정한 날짜` 글자가 세로 방향으로 살짝 잘렸다.

**최초 실제 오류**
- `MainFrame::setOption()`은 theme mode 변경 시 `SendMessageToDescendants(WM_SETTINGCHANGE, ...)`만 호출했다. Preferences는 MainFrame child가 아니라 별도 top-level/owned window이므로 이 broadcast에서 구조적으로 제외됐다.
- `CMenuBar::OnCustomDraw()`는 custom-draw `dwItemSpec`을 command/index로 해석한 뒤에만 app-owned `DrawText`를 실행했다. runtime screenshot은 해당 resolution branch가 최종 text ownership을 확보하지 못하고 ToolbarWindow32 native text fallback이 남는다는 evidence다.
- `FlatHeaderCtrl::resizeWindow()`는 font가 바뀌어도 기존 header window height를 그대로 재사용했다. modern UI font/DPI가 legacy header height보다 큰 환경에서는 custom-drawn glyph의 상하가 clip될 수 있었다.

**원인 진단**
- Root cause 1: app theme mode는 process/global state인데 refresh scope는 MainFrame descendant tree로 제한했다.
- Root cause 2: final renderer ownership을 command/index inference 성공 여부에 의존했다.
- Root cause 3: typography를 modern font로 교체하면서 vertical control metric은 legacy window height에 남겼다.

**해결 방법**
- `main_frame.cpp`: current UI thread의 모든 top-level window를 `EnumThreadWindows`로 열거하고 frame theme, `WM_SETTINGCHANGE`, descendant refresh, full redraw를 한 theme-change transaction으로 적용한다. 이미 열린 Preferences/owned dialog도 같은 pass에 포함한다.
- `MenuBar.cpp`: `TB_GETBUTTONTEXT`로 custom-draw item command id의 실제 toolbar text를 직접 조회하고 ThemePalette foreground로 그린 뒤 `CDRF_SKIPDEFAULT`로 native black-text fallback을 차단한다. legacy sequential menu id fallback만 보조 경로로 유지한다.
- `FlatHeaderCtrl.cpp`: current UI font의 `TEXTMETRIC.tmHeight + tmExternalLeading`과 DPI-scaled vertical padding으로 header height를 매번 계산하고 font/theme/DPI refresh 시 재적용한다.
- `validate_source_invariants.py`: top-level theme broadcast, toolbar-id text ownership, font/DPI-derived header height를 safety contract로 추가하고 ambiguous `CommandToIndex(dwItemSpec)` 의존을 금지한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — split Light/Dark Preferences, Dark menu black text, header vertical clipping 확인.
- Connector source audit: PASS — 세 root cause를 현재 `main` source에서 확인했다.
- Source contract self-check: PASS — top-level enumeration, `TB_GETBUTTONTEXT` + `CDRF_SKIPDEFAULT`, TEXTMETRIC/DPI height contract를 commit 전 확인했다.
- Windows runtime theme switch, actual Dark menu foreground, header clipping screenshot, `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Legacy green active stripe and persistent address-field outline

**오류 발생**
- 사용자 최신 Windows 11 screenshot에서 탐색 pane 상단에 밝은 녹색 가로선이 계속 보였고, 현재 위치 `내 문서`를 표시하는 address field에는 포커스 여부와 무관한 밝은 사각 테두리가 남았다.
- 사용자가 제공한 Windows 11 File Explorer reference에는 동일한 full-width green stripe나 persistent white location-box outline이 없다.

**최초 실제 오류**
- `ActivateBar::applyModernAppearance()`는 non-High-Contrast에서도 active pane이면 `gOpt->mConfig.mActiveViewColor`를 그대로 사용했다. 기본값 `DEF_ACTIVED_VIEW_COLOR`는 `RGB(48,192,48)`이고, `ExplorerView::recalcLayout()`가 이 컨트롤에 `getActivePaneIndicatorThickness()` 높이를 항상 할당해 screenshot의 녹색 full-width stripe가 만들어졌다.
- `AddressBar::OnNcPaint()`는 non-High-Contrast idle 상태에서도 `ThemePalette.mBorder`로 전체 window `FrameRect`를 그렸다. nested native borders를 제거했더라도 이 app-owned frame 자체가 persistent white/bright outline으로 남았다.

**원인 진단**
- Root cause 1: legacy active-pane color option을 현대 tab/surface selection state와 중복해서 별도 horizontal accent로 계속 렌더링했다.
- Root cause 2: address-bar modernization이 native double-border 제거에 집중하면서 app-owned outer frame은 normal state에서도 항상 보이게 유지했다.

**해결 방법**
- `activate_bar.cpp`: non-High-Contrast에서는 legacy configured active color를 더 이상 그리지 않고 surrounding `ThemePalette.mWindow`를 사용한다. High Contrast active state는 system-selection palette를 유지한다.
- `explorer_view.cpp`: non-High-Contrast에서는 ActivateBar 높이를 0으로 collapse하고, High Contrast에서만 기존 active indicator thickness를 사용한다. TabCtrl의 pane-active selected surface는 그대로 유지한다.
- `address_bar.cpp`: idle non-client edge는 field surface인 `mElevated`와 같은 색으로 그려 persistent outline을 없애고, 실제 keyboard/mouse focus일 때만 `mFocus` frame을 표시한다.
- `validate_source_invariants.py`: non-HC active stripe collapse, legacy `mActiveViewColor` paint 금지, focus-only address border와 idle `mBorder` 금지를 regression contract로 추가한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — bright green full-width stripe와 persistent white `내 문서` outline 확인.
- Connector source audit: PASS — `DEF_ACTIVED_VIEW_COLOR -> ActivateBar -> ExplorerView layout`, `AddressBar::OnNcPaint -> mBorder` 경로를 확인했다.
- Source contract self-check: PASS — non-HC zero-height stripe, neutral ActivateBar paint, idle `mElevated`/focused `mFocus` address frame을 commit 전 확인했다.
- Windows runtime screenshot, keyboard-focus accessibility, High Contrast active-pane indication, `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Win11 source invariant preflight crashed on missing `header` registration

**오류 발생**
- 사용자 `local_ci.bat x64` 실행이 Visual Studio 2026 x64 solution 생성 전 source invariant/regression preflight에서 종료됐다.
- Python traceback은 `validate_win11_stability_regressions()`의 `contents["header"]` 접근에서 `KeyError: 'header'`를 보고했다. 따라서 이번 FAIL은 C++ compile/link 결과가 아니라 validator 자체의 integration 오류다.

**최초 실제 오류**
- 최근 file-list header clipping 회귀 guard가 `FlatHeaderCtrl.cpp`의 font/DPI metric token을 검사하도록 추가됐지만, 같은 함수의 `paths` map에는 `"header": FXFILE_SRC / "gui" / "FlatHeaderCtrl.cpp"` 등록이 빠져 있었다.
- 그 결과 source file read 단계에서는 오류가 없었고, 뒤쪽 direct dictionary access에서 Python exception이 발생해 정상적인 invariant error reporting도 건너뛰었다.

**원인 진단**
- Root cause 1: 새 regression assertion과 해당 assertion의 source-registration 변경을 하나의 invariant contract로 검토하지 않았다.
- Root cause 2: validator 내부 `contents`가 plain `dict`여서 source-registration 누락이 deterministic validation failure가 아니라 traceback으로 바뀌었다.
- Root cause 3: 직전 UI 논리 작업 종료 시 validator 자체의 source-key completeness를 정적 대조하지 않았다.

**해결 방법**
- `build/validate_source_invariants.py`: `validate_win11_stability_regressions()`의 `paths`에 `FlatHeaderCtrl.cpp`를 `header` key로 등록했다.
- 같은 함수의 contract contents map에 `__missing__` fallback을 추가해 향후 등록 누락이 발생하면 `missing source registration for contents[...] ` 오류를 누적하고 빈 source로 이어서 검사하도록 했다. 따라서 regression validator는 source integration 오류를 traceback이 아니라 일반 preflight failure로 보고한다.
- Connector-side static cross-check로 해당 함수의 모든 literal `contents["..."]` key와 `paths` key를 대조했고 누락이 0개임을 확인했다.

**재발 방지**
- regression guard가 새 source key를 참조하면 같은 논리 작업에서 source path registration까지 함께 검토한다.
- validator 내부 integration 실수는 Python exception으로 종료시키지 말고 deterministic validation error로 반환한다.
- invariant 변경 checkpoint에는 최소한 function-local source-key/reference completeness 대조를 포함한다.

**검증 상태**
- 사용자 local CI before fix: FAIL — source invariant/regression preflight에서 `KeyError: 'header'`; project generation/MSVC compile은 시작되지 않음.
- Connector source audit after fix: PASS — `header` source registration 존재, direct `contents["..."]` reference 대비 missing key 0개, defensive missing-key reporting 존재.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after this commit.
- `local_ci.bat x64`, VS 2026 project generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after this commit.

---

## 2026-09-23 — Rebar wrapper bypassed child toolbar/menu notification reflection

**오류 발생**
- 사용자 최신 screenshot에서도 Dark top menu text가 계속 검게 보였다.
- `CMenuBar::OnCustomDraw()`에는 이미 ThemePalette text, explicit `DrawText`, `CDRF_SKIPDEFAULT`가 있었으므로 단순 색상 값 문제로 설명되지 않았다.

**최초 실제 오류**
- `CMenuBar`와 `CToolBarEx`는 `ON_NOTIFY_REFLECT(NM_CUSTOMDRAW, ...)`에 의존한다.
- 그러나 부모 wrapper인 `CSizableReBar::OnNotify()`는 내부 rebar control의 id(`wParam == 1`)가 아니면 즉시 `return FALSE;`했다.
- 따라서 child toolbar/menu notification이 MFC 기본 `CControlBar::OnNotify()` routing/reflection으로 전달되지 않을 수 있었고, 이 경우 모든 child custom-draw 코드는 source에 존재해도 runtime에서 최종 renderer가 되지 않는다.

**원인 진단**
- Root cause: wrapper control이 내부 rebar notification과 child-band notification을 같은 방식으로 차단했다.
- 기존 regression guard는 child `NM_CUSTOMDRAW` handler token의 존재만 검사했고, 그 handler까지 notification이 실제로 도달하는 routing contract는 검사하지 않았다.

**해결 방법**
- `gui/rebar/SizableReBar.cpp`: `wParam != 1` child-band notification을 `CControlBar::OnNotify(wParam, lParam, pResult)`에 위임한다.
- 내부 rebar(id 1)의 `RBN_*` handling은 기존 구현을 유지한다.
- `build/validate_source_invariants.py`: command-surface contract가 base `OnNotify` delegation을 요구하고 해당 block의 `return FALSE;` 재도입을 금지한다.

**검증 상태**
- User screenshot before fix: FAIL — Dark menu text remains black.
- Connector source audit: PASS — reflection bypassing branch and child `ON_NOTIFY_REFLECT` dependency confirmed.
- Source contract after fix: PASS by connector inspection.
- Windows runtime screenshot after fix: **NOT RETESTED**.

---

## 2026-09-23 — AddressBar inner native edge repainted after outer-frame flattening

**오류 발생**
- 사용자 최신 screenshot에서도 current-folder `내 문서` row가 밝은 흰색 outline으로 둘러싸여 있었다.
- 이전 수정은 outer `AddressBar::OnNcPaint()`의 idle frame color만 바꿨지만 실제 화면은 변하지 않았다.

**최초 실제 오류**
- `AddressBar`는 outer `CComboBoxEx`, inner `ComboBox`, inner `Edit`의 복합 control이다.
- outer style에서 `WS_BORDER` / `WS_EX_CLIENTEDGE`를 제거해도 inner native ComboBox/Edit는 자신의 paint/non-client paint 단계에서 edge를 다시 그릴 수 있었다.
- 따라서 outer `OnNcPaint()`를 먼저 flatten해도 final renderer가 inner native control이면 screenshot에는 bright edge가 그대로 남는다.

**원인 진단**
- Root cause: composite control의 최종 paint ownership을 outer HWND만 기준으로 판단했다.
- 이전 invariant도 outer frame color contract만 검사했고 inner ComboBox/Edit post-paint edge ownership은 보호하지 않았다.

**해결 방법**
- `address_bar.cpp`: `PaintFlatAddressEdge(HWND, COLORREF)`를 추가해 현재 DPI 기준 2px edge를 palette `mElevated`로 덮는다.
- outer `AddressBar::OnNcPaint()`는 High Contrast 외에는 persistent focus/white outline을 그리지 않고 flat edge만 유지한다.
- inner ComboBox는 native `WM_PAINT` 뒤와 `WM_NCPAINT` 뒤에 flat edge를 다시 적용한다.
- inner Edit도 `WM_NCPAINT` 뒤에 flat edge를 적용해 native edge가 최종 renderer가 되지 않게 한다.
- invariant는 focus/border outline 재도입을 금지하고 outer/inner flat-edge tokens를 요구한다.

**검증 상태**
- User screenshot before fix: FAIL — bright outline still present.
- Connector source audit: PASS — outer-only ownership gap and inner native final-paint paths confirmed.
- Source contract after fix: PASS by connector inspection.
- Windows runtime screenshot after fix: **NOT RETESTED**.

---

## 2026-09-23 — AddressBar flat-edge implementation was rejected by stale invariant contracts

**오류 발생**
- 사용자 `local_ci.bat x64` 재실행은 source invariant/regression preflight까지 정상 진입했지만 `address: missing Win11 soft-surface token sPalette.mFocus`와 `palette-owned address frame painting is missing` 두 오류로 종료됐다.
- 이 시점에는 project generation/MSVC compile이 시작되지 않았으므로 제품 C++ compile failure가 아니라 validator contract drift였다.

**최초 실제 오류**
- `validate_soft_surface_contract()`의 AddressBar required token이 여전히 `("sPalette.mElevated", "sPalette.mFocus")`였다.
- `validate_win11_stability_regressions()`의 `AddressBar::OnNcPaint()` check는 `CWindowDC sDC(this);`가 함수 본문에 직접 존재해야 한다고 요구했다.
- 그러나 `62ab7978`은 Win11 Explorer reference에 맞춰 persistent focus/white outline을 제거했고, non-client edge painting을 reusable `PaintFlatAddressEdge()` helper로 이동했다. 따라서 두 old assertions는 최신 구현과 직접 모순됐다.

**원인 진단**
- Root cause 1: renderer implementation을 바꿀 때 동일 feature를 검사하는 여러 validator function을 한 번에 갱신하지 않았다.
- Root cause 2: safety property 대신 이전 구현의 local token(`sPalette.mFocus`, local `CWindowDC`)을 요구해 refactor-safe하지 않았다.
- Root cause 3: logical work unit 종료 시 validator 전체의 positive/negative AddressBar requirements 간 모순을 검색하지 않았다.

**해결 방법**
- soft-surface AddressBar contract는 `sPalette.mElevated`와 `PaintFlatAddressEdge`를 요구한다.
- Win11 AddressBar regression contract는 local DC variable 대신 `PaintFlatAddressEdge(m_hWnd, sPalette.mElevated)`를 요구한다.
- 기존 negative contract는 유지한다: `AddressBar::OnNcPaint()`에서 `sPalette.mFocus`, `sPalette.mBorder`, `sFocused`가 다시 나타나면 regression으로 실패한다.
- Connector static scan에서 validator의 `CWindowDC sDC(this)` requirement는 0개, `sPalette.mFocus` reference는 AddressBar `OnNcPaint()` forbidden check 1개만 남았음을 확인했다.

**재발 방지**
- UI renderer refactor 시 동일 component를 검사하는 모든 validator function을 검색해 positive/negative contract를 함께 갱신한다.
- invariant는 helper 위치나 local variable보다 최종 ownership/safety property를 검사한다.
- 서로 모순되는 required/forbidden token이 없는지 logical work unit checkpoint에서 component 단위로 재검색한다.

**검증 상태**
- User local CI before fix: FAIL — source invariant/regression preflight에서 두 stale AddressBar contract failure.
- Connector validator audit after fix: PASS — stale positive requirements 제거, current flat-edge tokens 요구, contradictory AddressBar focus requirement 없음.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after `63081b85`.
- `local_ci.bat x64`, VS 2026 project generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after `63081b85`.

---

## 2026-09-23 — Command-bar child custom draw now uses explicit MFC reflection

**오류 발생**
- 사용자가 최신 `main`을 pull/rebuild한 뒤에도 Dark top-menu text가 검게 보인다고 재현했다.
- `CMenuBar::OnCustomDraw()`에는 palette `DrawText` + `CDRF_SKIPDEFAULT`가 이미 존재했으므로, source token 존재만으로는 final renderer ownership을 설명하지 못했다.

**최초 실제 오류**
- `CSizableReBar::OnNotify()`는 child notification을 `CControlBar::OnNotify(...)`에 넘기도록 수정돼 있었지만, `CMenuBar` / `CToolBarEx`가 의존하는 `ON_NOTIFY_REFLECT`가 그 base path에서 반드시 실행된다는 것을 프로젝트 코드 수준에서 보장하지 않았다.
- 사용자 runtime evidence가 계속 FAIL인 이상 implicit framework routing을 acceptance 근거로 사용할 수 없었다.

**해결 방법**
- non-rebar child notification은 `NMHDR::hwndFrom`을 기준으로 `CWnd::ReflectLastMsg(hwndFrom, pResult)`를 먼저 호출한다.
- child가 reflected notification을 처리하면 즉시 TRUE를 반환한다.
- 처리되지 않은 notification만 기존 `CControlBar::OnNotify(...)` 경로로 넘긴다.
- invariant는 explicit `ReflectLastMsg` token을 요구하고 child-notification branch의 `return FALSE;`를 계속 금지한다.

**검증 상태**
- User rebuilt screenshot before this fix: FAIL — top menu text remains black.
- Connector source audit after fix: PASS — explicit reflection is in the active `CSizableReBar::OnNotify()` child path.
- Windows rebuilt screenshot after `aedb695c`: **NOT RETESTED**.

---

## 2026-09-23 — Replacement AddressBar frame itself remained visible

**오류 발생**
- 사용자가 최신 `main`을 pull/rebuild한 뒤에도 `내 문서` current-folder row의 rectangular outline이 그대로 보인다고 재현했다.
- 이전 `PaintFlatAddressEdge(..., mElevated)` 방식은 native white edge를 가리는 목적이었지만 실제 screenshot에서는 그 replacement edge 자체가 지속적인 box로 보였다.

**원인 진단**
- Root cause: Win11-style acceptance target은 "다른 색으로 frame을 다시 그리기"가 아니라 **persistent frame 없음**인데, 이전 수정은 outer/inner HWND 모두에 2px replacement frame을 명시적으로 그렸다.
- 즉 final renderer ownership은 앱이 가져왔지만 최종 시각 결과 자체가 요구사항과 달랐다.

**해결 방법**
- `PaintFlatAddressEdge()` helper와 모든 호출을 제거했다.
- outer `AddressBar::OnNcPaint()`는 High Contrast에서만 `Default()`를 호출하고 일반 Light/Dark에서는 아무 replacement frame도 그리지 않는다.
- inner ComboBox/Edit의 `WM_NCPAINT`는 non-High-Contrast에서 0을 반환해 legacy native edge를 억제한다.
- existing `WS_BORDER` / `WS_EX_CLIENTEDGE` removal + `SWP_FRAMECHANGED` contract는 유지한다.
- invariant는 `PaintFlatAddressEdge` 재도입을 금지하고 non-High-Contrast `WM_NCPAINT` suppression을 요구한다.

**검증 상태**
- User rebuilt screenshot before this fix: FAIL — current-folder row still boxed.
- Connector source/invariant audit after fix: PASS — replacement frame removed; remaining `PaintFlatAddressEdge` references are forbidden checks only.
- Windows rebuilt screenshot after `083de734`: **NOT RETESTED**.

---

## 2026-09-23 — Inactive frame policy dimmed enabled Dark menu commands

**오류 발생**
- 사용자 rebuilt `80ccaea9` screenshot에서 상단 메뉴 text가 여전히 지나치게 어둡게 보였다.
- screenshot에는 `build-revision.txt` 창이 foreground였으므로 fxfile frame은 inactive 상태였다.

**최초 실제 오류**
- modern `CMenuBar::OnCustomDraw()` text policy가 `(CDIS_DISABLED || !m_bFrameActive) ? mSecondaryText : mText`였다.
- 따라서 command 자체가 enabled여도 top-level frame이 inactive이면 모든 menu text가 secondary contrast로 내려갔다.

**원인 진단**
- Root cause: command availability(disabled)와 frame activation(inactive)을 같은 low-contrast visual state로 취급했다.
- 이 로직은 custom draw/reflection이 정상이어도 사용자 눈에는 "검은 메뉴 글자"처럼 보일 정도로 대비를 낮출 수 있었다.

**해결 방법**
- enabled menu item은 frame activation과 무관하게 `ThemePalette.mText`를 사용한다.
- `CDIS_DISABLED` item만 `mSecondaryText`를 사용한다.
- hover/pressed item은 기존대로 `mText`를 유지한다.
- invariant는 `disabled || !m_bFrameActive` modern text condition 재도입을 금지한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL — inactive fxfile menu labels too dark.
- Connector source audit after fix: PASS — enabled/disabled color split no longer depends on `m_bFrameActive`.
- Windows rebuilt screenshot after `e6c3e2c7`: **NOT RETESTED**.

---

## 2026-09-23 — Classic ComboBox client edge survived style and non-client suppression

**오류 발생**
- 사용자 rebuilt `80ccaea9` screenshot에서 current-folder row의 rectangular border가 계속 보였다.
- screenshot 자체가 current revision provenance를 포함하므로 stale build 가설은 배제했다.

**실제 픽셀 증거**
- 주소창 영역의 full-width edge는 위쪽 약 RGB 160/160/160 + 105/105/105 두 줄, 아래쪽 약 RGB 227/227/227 + 255/255/255 두 줄로 나타났다.
- 이는 app palette의 `mElevated` replacement frame이 아니라 classic sunken ComboBox 3-D client-edge 패턴이다.

**원인 진단**
- `WS_BORDER` / `WS_EX_CLIENTEDGE`를 outer/Combo/Edit에서 제거하고 `WM_NCPAINT`를 억제해도, ComboBoxEx/ComboBox native `WM_PAINT`가 client 영역 내부에 3-D edge를 그릴 수 있다.
- 따라서 non-client ownership만 검증한 이전 수정은 최종 client renderer를 놓쳤다.

**해결 방법**
- `AddressBar::OnPaint()`를 추가해 native/default paint를 먼저 완료한 뒤, non-High-Contrast에서 client rect의 2-DPI-pixel top/bottom/left/right strip만 `ThemePalette.mElevated`로 덮는다.
- nested ComboBox의 `WM_PAINT`도 native paint 뒤 동일 strip cover를 수행하고, 그 다음 modern dropdown button을 그린다.
- helper는 `GetClientRect` + 네 개의 `FillRect` strip만 사용한다. `FrameRect`나 contrasting replacement frame은 사용하지 않는다.
- High Contrast에서는 native painting을 그대로 유지한다.
- invariant는 outer `ON_WM_PAINT`, helper token, four-strip fill, inner ComboBox post-paint cover를 요구한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL — classic 3-D edge visibly present on revision `80ccaea9`.
- Connector source/diff audit after fix: PASS — outer and inner client-paint post-pass installed; stale PaintFlat/focus contracts absent.
- Windows rebuilt screenshot after `ea47b7b7`: **NOT RETESTED**.

---

## 2026-09-23 — Menu contrast invariant scanned legacy fallback and produced a false positive

**오류 발생**
- 사용자 `local_ci.bat x64`가 revision `277a64249c376d271a1684bf182cca1bfc9d25f6`에서 source invariant/regression preflight를 실행했고, `src/fxfile/gui/rebar/MenuBar.cpp: inactive frame must not dim enabled Dark menu text`로 종료됐다.
- 로그에는 프로젝트 생성/MSBuild 전 preflight FAIL과 함께 기존 x64 artifact가 이번 run에서 재빌드되지 않았다는 provenance warning도 정상적으로 기록됐다.

**최초 실제 오류**
- modern Dark custom-draw branch는 이미 `(uItemState & CDIS_DISABLED) ? mSecondaryText : mText`로 수정돼 있었다.
- 하지만 같은 `MenuBar.cpp`의 WinXP/system-color fallback branch에는 의도적으로 `!m_bFrameActive` 조건이 남아 있다.
- validator가 component 전체 문자열에 대해 `(CDIS_DISABLED || !m_bFrameActive)`를 검색해서 legacy fallback까지 modern regression으로 오인했다.

**원인 진단**
- Root cause: renderer-specific safety property를 file-global token absence로 표현했다.
- modern renderer와 legacy compatibility renderer가 한 함수에 공존하는데 validation scope를 구분하지 않았다.

**해결 방법**
- `validate_win11_stability_regressions()`에서 `CDDS_ITEMPREPAINT`의 modern non-High-Contrast branch 시작과 legacy `WinAppEx* pApp` fallback 시작을 찾아 `menu_modern_draw` block을 분리한다.
- inactive-frame dimming prohibition과 enabled/disabled text-color required token 검사는 해당 modern block에만 적용한다.
- modern block 자체를 찾지 못하면 별도의 deterministic invariant failure를 반환한다.
- Connector-side self-check에서 modern block 발견, forbidden condition absent, required contrast tokens present를 확인했다. legacy file-global `!m_bFrameActive`는 compatibility code로 허용한다.

**재발 방지**
- 동일 파일에 modern/legacy renderer가 공존하는 경우 safety invariant는 해당 renderer block으로 scope한다.
- legacy compatibility token의 존재 여부를 modern renderer regression 판단에 직접 사용하지 않는다.
- validator 변경 시 current source를 대상으로 block extraction 자체를 self-check한다.

**검증 상태**
- User local CI before fix: FAIL at source invariant/regression preflight.
- Connector scoped-validator self-check after fix: PASS.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after `53b2490a`.
- `local_ci.bat x64`, VS 2026 project generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after `53b2490a`.

---

## 2026-09-23 — MenuBar final text ownership moved to WM_PAINT post-pass

**오류 발생**
- 사용자가 `03bc40ce`로 실제 rebuild한 screenshot에서도 top menu labels가 어둡게 남아 있었다.
- custom draw source, explicit reflection, enabled/inactive color policy가 모두 최신 상태였으므로 `NM_CUSTOMDRAW`만으로 final pixel ownership을 보장할 수 없다는 runtime evidence가 됐다.

**원인 진단**
- ToolbarWindow32/native renderer가 custom-draw 결과 이후에도 최종 text pixels를 소유하거나, 일부 paint cycle에서 custom-draw 경로가 최종 draw가 아닐 수 있다.
- 따라서 "custom draw handler가 존재하고 올바른 색을 설정함"은 화면 결과의 충분조건이 아니었다.

**해결 방법**
- `CMenuBar::OnPaint()`를 추가한다.
- 먼저 `CToolBar::Default()`로 native layout/hit-testing/accessibility paint를 완료한다.
- non-High-Contrast modern path에서 textual toolbar button을 index로 순회하고 각 button rect를 `ThemePalette.mChrome`으로 다시 지워 native text를 제거한다.
- hot/pressed 상태는 ThemePalette hover/pressed surface로 다시 그린다.
- enabled label은 `mText`, 실제 disabled label만 `mSecondaryText`로 마지막에 `DrawText`한다.
- accelerator/focus cue를 `WM_QUERYUISTATE`와 기존 tracking state에 맞춰 유지한다.
- MDI caption buttons도 post-pass 끝에서 기존 `CMenuBarButton::DrawButton()`으로 다시 그린다.
- invariant는 `ON_WM_PAINT`, `CMenuBar::OnPaint`, native-default-first, per-button chrome erase, final `DrawText` ownership을 요구한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL on revision `03bc40ce`.
- Connector diff/source audit after fix: PASS — declaration/message map/implementation/final renderer guard all present.
- Windows rebuilt screenshot after `d48c9cb5`: **NOT RETESTED**.

---

## 2026-09-23 — ExplorerView legacy WS_BORDER framed the current-folder surface

**오류 발생**
- 사용자가 revision `03bc40ce`를 실제 rebuild한 screenshot에서도 `내 문서` current-folder row 위/주변에 full-width classic edge가 남아 있다고 재현했다.
- AddressBar의 outer/inner border style, non-client paint, client-edge paint를 이미 다뤘는데도 선이 남았으므로 AddressBar 자체가 아닌 상위 window hierarchy를 다시 추적했다.

**최초 실제 오류**
- `AddressBar`는 `ExplorerPane`의 직접 child이며 `ExplorerPane::OnPaint()`는 `ThemePalette.mWindow` 배경만 채운다.
- `MainFrame::onSplitterPaneCreate()`에서 `ExplorerView`와 `FolderView`를 모두 `WS_CHILD | WS_VISIBLE | WS_BORDER`로 생성하고 있었다.
- 이 outer `WS_BORDER`가 ExplorerView 전체를 감싸기 때문에 view의 첫 UI row인 current-folder 영역 바로 위/주변에 classic frame으로 나타났다.

**원인 진단**
- Root cause: AddressBar 내부 renderer만 계속 좁혀 봤고, 실제 classic edge ownership이 한 단계 상위 `ExplorerView` window style에 있다는 점을 늦게 확인했다.
- 기존 source invariant도 AddressBar/rebar의 border contract는 보호했지만 splitter가 생성하는 Explorer/Folder view의 unconditional `WS_BORDER`는 검사하지 않았다.

**해결 방법**
- modern Windows에서 `ExplorerView`와 `FolderView` 생성 style을 `WS_CHILD | WS_VISIBLE`로 변경한다.
- WinXP compatibility path에서만 `sStyle |= WS_BORDER`를 유지한다.
- invariant는 `onSplitterPaneCreate()` block을 scope하여 unconditional `WS_CHILD | WS_VISIBLE | WS_BORDER`를 금지하고, 두 modern borderless style과 두 XP guard를 요구한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL on revision `03bc40ce`.
- Connector source/diff self-check after fix: PASS — unconditional borders 0, modern borderless styles 2, XP guards 2, XP border additions 2.
- `python build/validate_source_invariants.py`: **NOT RETESTED** after `4004ac3d`.
- Windows Release-x64-Unicode build/runtime screenshot after `4004ac3d`: **NOT RETESTED**.

---

## 2026-09-23 — Final MenuBar WM_PAINT invariant required a nonexistent chained spelling

**오류 발생**
- 사용자 `local_ci.bat x64`가 revision `7decaadee4a75bcd31f820dd84d3a3679fe4bb6d`에서 source invariant/regression preflight를 실행했고, `final WM_PAINT text ownership missing token GetToolBarCtrl().GetButtonCount()`로 종료됐다.
- 로그상 이 failure는 프로젝트 생성/MSBuild 전에 발생했고 기존 x64 artifact가 이번 run에서 재빌드되지 않았다는 provenance warning도 정상적으로 출력됐다.

**최초 실제 오류**
- `CMenuBar::OnPaint()`의 실제 구현은 `CToolBarCtrl &sToolBarCtrl = GetToolBarCtrl();`로 control reference를 받은 뒤 `sToolBarCtrl.GetButtonCount()`를 호출한다.
- validator는 renderer contract가 아니라 `GetToolBarCtrl().GetButtonCount()`라는 exact source spelling을 요구했다.
- 기능적으로 동일하고 현재 source에 존재하는 구현을 validator가 잘못 거부한 false positive다.

**원인 진단**
- Root cause: safety property를 semantic operation sequence가 아니라 한 가지 C++ 표현식 spelling으로 고정했다.
- 최근 runtime regression 대응 과정에서 validator가 구현 세부 토큰에 다시 과적합됐다.

**해결 방법**
- validator가 `CMenuBar::OnPaint()` 시작부터 `OnButtonDown()` 직전까지의 paint block을 별도로 추출한다.
- 해당 block에서 native default paint, `CToolBarCtrl` acquisition, button count, per-button button/text/rect retrieval, chrome erase, enabled/disabled ThemePalette colors, final `DrawText`를 각각 검사한다.
- `ON_WM_PAINT()` message-map contract는 file-level에서 별도로 유지한다.
- nonexistent chained token `GetToolBarCtrl().GetButtonCount()` 요구는 제거했다.
- connector self-check로 current `MenuBar.cpp` paint block에 필요한 semantic steps가 모두 존재하고 missing token이 0개임을 확인했다.

**재발 방지**
- validator는 동일 semantics를 표현하는 합법적인 refactor를 막는 chained/local-variable spelling에 의존하지 않는다.
- renderer contract는 해당 function/block으로 scope하고 operation sequence를 확인한다.
- 신규 validator는 current source에 동일 extraction/check를 즉시 재현해 false positive 여부를 checkpoint에서 확인한다.

**검증 상태**
- User local CI before fix: FAIL at source invariant/regression preflight on revision `7decaade`. fileciteturn1029file0L14-L18
- Connector semantic-validator self-check after fix: PASS — paint block found, required steps missing 0, stale chained token absent.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after `97b42a8d`.
- `local_ci.bat x64`, VS 2026 generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after `97b42a8d`.

---

## 2026-09-23 — Final menu renderer needed a Dark contrast floor

**오류 발생**
- 사용자가 revision `02d3b404`를 실제 rebuild한 screenshot에서도 top menu label이 dark chrome과 거의 섞여 보인다고 재현했다.
- 최종 `CMenuBar::OnPaint()` post-pass가 이미 해당 revision에 포함돼 있었으므로 paint ownership만으로는 충분하지 않았다.

**실제 픽셀 증거**
- screenshot의 top command chrome은 약 RGB(43,43,43)이고 menu glyph의 dominant neutral pixels는 약 RGB(109,109,109)였다.
- 따라서 최종 text output 자체의 대비가 부족했다.

**원인 진단**
- final renderer가 `ThemePalette.mText` / `mSecondaryText`를 그대로 신뢰했다.
- system/UISettings-derived foreground가 app-owned Dark command surface에 비해 충분히 밝다는 별도 보장이 없었다.
- custom draw와 WM_PAINT가 같은 palette color를 공유하므로 renderer ownership을 여러 번 강화해도 color input이 어두우면 결과는 계속 어둡다.

**해결 방법**
- `MenuBar.cpp`에 perceived-luma helper와 `ResolveMenuTextColor()`를 추가한다.
- Light 또는 High Contrast에서는 기존 preferred palette text를 그대로 반환한다.
- Dark에서는 `mChrome` 대비 luma delta를 검사한다.
- enabled text는 delta가 부족하면 RGB(238,238,238), disabled text는 RGB(176,176,176)으로 보정한다.
- final `CMenuBar::OnPaint()`와 modern custom-draw path가 동일 resolver를 사용하도록 통합한다.
- invariant는 contrast helper, threshold/fallback colors, 두 renderer path의 resolver 사용을 요구한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL on revision `02d3b404`.
- Screenshot pixel analysis before fix: chrome ~RGB(43), neutral menu text ~RGB(109).
- Connector source/validator audit after fix: PASS — contrast-floor helper exists and both menu renderer paths use it.
- Windows rebuilt screenshot after `1ef8a78b`: **NOT RETESTED**.

---

## 2026-09-23 — Rebar print composition could overwrite the final MenuBar overlay

**오류 발생**
- 사용자가 revision `cf277791`를 실제 rebuild한 screenshot에서도 top menu text가 여전히 어둡다고 재현했다.
- 해당 revision에는 Dark contrast-floor fallback RGB(238,238,238) / RGB(176,176,176)이 포함돼 있었지만 screenshot menu region에는 두 fallback 색이 한 픽셀도 나타나지 않았고 foreground 최대 채널은 약 109였다.

**원인 진단**
- palette/contrast 계산이 잘못된 것이 아니라 새 foreground가 최종 visible renderer가 아니었다.
- `CMenuBar` toolbar는 rebar band child로 호스팅되며, normal `WM_PAINT` 이후에도 parent/rebar composition을 위한 `WM_PRINTCLIENT` 또는 client-inclusive `WM_PRINT` 경로가 native toolbar pixels를 다시 그릴 수 있다.
- 기존 final overlay는 `WM_PAINT`에만 있었으므로 이 후속 합성 경로를 소유하지 못했다.
- 동시에 top-level menu disabled 판정이 toolbar `TBSTATE_ENABLED`에 의존해 실제 `HMENU` state와 다를 여지도 있었다.

**해결 방법**
- `DrawFinalMenuOverlay(CDC &)`로 final text/background/state drawing을 단일화했다.
- `OnPaint()`는 native toolbar paint 후 해당 overlay를 호출한다.
- `CMenuBar::WindowProc()`는 base `CToolBar::WindowProc()`를 먼저 완료한 뒤 `WM_PRINTCLIENT`와 `WM_PRINT + PRF_CLIENT` HDC에도 동일 overlay를 마지막으로 적용한다.
- top-level enabled/disabled 상태는 `m_pMenu->GetMenuState(..., MF_BYPOSITION)`의 `MF_DISABLED | MF_GRAYED`를 기준으로 판단한다.
- `MenuBar.h`를 validator source map에 별도 등록해 header declaration과 cpp implementation contract를 분리했고, `LPARAM` print flags는 pointer-width를 유지한 채 검사한다.

**재발 방지**
- rebar/toolbar custom surfaces는 `WM_PAINT`만 final renderer로 가정하지 않고 `WM_PRINTCLIENT` / `WM_PRINT` composition contract도 함께 보호한다.
- top-level menu availability는 toolbar command-update state 대신 source-of-truth `HMENU` item state로 판단한다.
- validator에서 header token을 cpp source에서 찾지 않도록 source registration을 명시하고, function-local source-key completeness를 checkpoint에서 재검사한다.

**검증 상태**
- User rebuilt screenshot before fix: FAIL on revision `cf277791`.
- Connector static cross-check after fix: PASS — common overlay, normal-paint call, post-base print-client/print calls, HMENU disabled-state lookup and contrast resolver all present.
- Connector validator source-map cross-check: PASS — missing `contents["..."]` keys 0.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after `25856539`.
- `local_ci.bat x64`, VS 2026 build and rebuilt runtime screenshot: **NOT RETESTED** after `25856539`.



---

## 2026-09-24 — Dark command hover, text, tab and popup rendering remained inconsistent

**오류 발생**
- 실제 Windows Dark screenshot에서 About의 `License` / `Credits` tab text가 ellipsis로 잘렸다.
- main/file-scrap command toolbar의 icon hover가 밝은 legacy HOT bitmap으로 바뀌어 흰 box처럼 보이고 icon 대비가 사라졌다.
- `뒤로`, `이름변경` 등 ToolbarWindow32 text와 drop-down secondary glyph가 app-owned Dark surface에서 native gray/black renderer와 UI font를 계속 사용할 수 있었다.
- `위로 상자`와 Drive dialog는 dark dialog 안에 plain `CToolBar`를 유지해 toolbar strip/font/hot state가 공용 modern renderer와 달랐다.
- legacy standard-menu option이 켜진 경우 BCMenu의 일부 submenu/detail glyph/text가 system-color renderer로 돌아갈 수 있었다.

**원인 진단**
- dialog tab custom renderer가 native tab item 폭 위에 좌우 8 DPI pixel padding을 추가해 짧은 tab label 자체의 가용 폭을 과도하게 줄였다.
- `CToolBarEx::SetIconType()`가 Dark에서도 classic/light용 HOT bitmap strip을 그대로 load했다. Custom-draw hover background가 올바르더라도 hot image 자체의 밝은 artwork가 최종 pixel을 덮었다.
- toolbar custom draw는 prepaint color만 공급하고 native toolbar에 text/drop-down glyph 최종 painting을 맡겨, system text/arrow color와 toolbar font가 Dark surface에 다시 나타날 수 있었다.
- History/Drive/reusable dialog toolbar 경로가 공용 `CToolBarEx`를 우회했다.
- BCMenu의 legacy standard renderer 선택은 app-owned Dark popup에서도 허용되어 있었다.

**해결 방법**
- `ModernUI::drawDialogTab()`의 text side inset을 8에서 3 DPI pixel로 줄여 native tab sizing과 custom padding이 중복되지 않게 했다.
- Dark/non-High-Contrast에서 `CToolBarEx` hot image list는 cold image list를 duplicate하여 icon artwork를 바꾸지 않고 `ThemePalette.mHover/mPressed`만 상태 표시를 담당하게 했다.
- `CDRF_NOTIFYPOSTPAINT` / `CDDS_ITEMPOSTPAINT` final pass를 추가해 native image/layout/accessibility는 유지하되 text area와 drop-down chevron은 ThemePalette + 현재 toolbar UI font로 마지막에 다시 그린다.
- popup toolbar도 Dark에서 native Explorer theme association을 reset해 동일 custom renderer가 final surface를 소유하게 했다.
- `CToolBarEx::ApplyModernMetrics()`는 동일 LOGFONT이면 HFONT를 불필요하게 재생성하지 않는다.
- `HistoryDlg`, `DriveDlg`, `DlgToolBar`를 `CToolBarEx` 기반으로 통합했다. `DlgToolBar` 사용자인 batch rename도 같은 renderer를 자동으로 사용한다.
- Dark/non-High-Contrast BCMenu는 legacy standard-menu 설정과 무관하게 `DrawItemWindows8Style()` palette renderer를 사용한다.
- 기존 `DropMenuButton` / `ColourPickerXP`의 Dark arrow path는 ThemePalette text/secondary colors를 이미 사용하고 있음을 전수 확인했다.

**재발 방지**
- `build/validate_source_invariants.py`가 toolbar final post-paint ownership, cold→hot duplication, stable UI font, compact dialog-tab inset, visible dialog toolbar의 `CToolBarEx` inheritance, Dark BCMenu palette renderer를 검사한다.
- toolbar/menu의 상태 배경과 icon/text/glyph final renderer를 별개 ownership으로 취급한다. palette field 값만 맞는 것으로 visual PASS를 선언하지 않는다.
- 새로운 visible dialog toolbar는 plain `CToolBar`로 추가하지 않고 shared modern toolbar path를 사용한다.

**검증 상태**
- User runtime screenshots before fix: FAIL.
- Source/connector audit after fix: implemented; Release-x64-Unicode compile/link/runtime smoke **PENDING**.
- Matching Windows screenshot/runtime acceptance after fix: **NOT RETESTED**.


---

## 2026-09-24 — Dark toolbar post-paint used nonexistent TB_GETBITMAPSIZE

**오류 발생**
- 사용자 `local_ci.bat x64` 로그에서 revision `ec903d085d75f93fae7fead634d2c748ca88f765`의 source invariant/regression preflight는 PASS했지만 `Release-x64-Unicode | x64` MSVC compile이 `ToolBarEx.cpp`에서 C2065로 중단됐다.
- 실패 식별자는 `TB_GETBITMAPSIZE`였다.

**원인 진단**
- Dark toolbar final post-paint가 text 영역을 계산하려고 toolbar bitmap 크기를 조회하면서 실제 ToolbarWindow32 API에 없는 `TB_GETBITMAPSIZE` 메시지를 사용했다.
- 필요한 값은 toolbar의 현재 normal image list가 이미 소유하고 있으므로 별도 가상 toolbar message가 필요하지 않았다.

**해결 방법**
- `DrawFinalDarkToolbarItem()`에서 `TB_GETIMAGELIST`로 현재 normal image list를 얻고 `ImageList_GetIconSize()`로 icon width/height를 조회한다.
- image list가 없거나 size query가 실패하면 width/height를 0으로 유지해 text-only toolbar button 경로가 안전하게 계속 동작하도록 했다.
- 기존 list-style/non-list-style text rectangle 계산은 그대로 유지했다.

**재발 방지**
- `build/validate_source_invariants.py::validate_toolbar_custom_draw_regression()`의 unsupported toolbar-message 목록에 `TB_GETBITMAPSIZE`를 추가했다.
- 동일 validator가 `TB_GETIMAGELIST`와 `ImageList_GetIconSize` 존재를 요구해 지원되는 image-list contract가 사라지지 않게 한다.

**검증 상태**
- User local CI before fix: source invariant/regression preflight **PASS**, Release-x64-Unicode x64 compile **FAIL** with C2065 at `ToolBarEx.cpp(278,17)`.
- Connector source cross-check after fix: `ToolBarEx.cpp`에서 `TB_GETBITMAPSIZE` 없음, `TB_GETIMAGELIST` / `ImageList_GetIconSize` 있음.
- `python build/validate_source_invariants.py`: **NOT RETESTED** after this fix.
- User `local_ci.bat x64`: **NOT RETESTED** after this fix.


---

## 2026-09-24 — Dark top-level menu remained black after custom-draw/overlay fixes

**오류 발생**
- 사용자 재빌드 screenshot에서 Light 메뉴바는 정상이나 Dark 메뉴바의 `파일/편집/이동/보기/도구/창/도움말` 글자가 계속 검은색으로 표시됐다.
- 같은 창의 나머지 command/rebar surface는 Dark palette를 적용받고 있어 최상단 `CMenuBar`의 최종 text pixel ownership만 실패한 상태였다.

**원인 진단**
- `CMenuBar::OnCustomDraw()`와 `DrawFinalMenuOverlay()`는 ThemePalette text color를 사용하고 있었지만 `OnPaint()`가 먼저 `CToolBar::Default()`를 호출했다.
- 즉 Dark에서도 ToolbarWindow32 native renderer가 먼저 text를 그린 뒤 app overlay로 덮는 구조였다. rebar의 composition/print 경로에서는 native text pass가 다시 최종 surface에 노출될 여지가 있었고, 실제 screenshot의 검은 글씨가 그 증거였다.
- palette 값 자체는 정상이므로 색상 계산을 다시 조정하는 것으로는 해결되지 않는다. Dark 메뉴바에서 native text painter를 최종 경로에서 제거해야 한다.

**해결 방법**
- Dark/non-High-Contrast `CMenuBar::OnPaint()`는 `CToolBar::Default()`를 호출하지 않는다.
- `CPaintDC`로 WM_PAINT update region을 정상 소모하고 전체 client rect를 `ThemePalette.mChrome`으로 채운 뒤 `DrawFinalMenuOverlay()`만으로 menu text/hot/pressed/focus를 그린다.
- native paint를 건너뛰어도 MDI maximized child의 system-menu icon이 사라지지 않도록 `DrawFinalMenuOverlay()`가 `IDBUTTON_SYSMENU` icon까지 직접 그린다.
- `WM_PRINTCLIENT` / `WM_PRINT + PRF_CLIENT` 경로도 Dark에서는 전체 client surface를 chrome으로 다시 지운 뒤 같은 overlay를 적용한다.
- Light/High Contrast는 기존 native-first path를 유지한다.

**재발 방지**
- source invariant가 Dark `OnPaint()`의 `sOwnDarkSurface`, `CPaintDC`, full-client chrome fill, overlay 호출과 early return을 요구한다.
- final overlay contract에 `IDBUTTON_SYSMENU` / `DrawIconEx` ownership을 추가한다.
- rebar print/composition path가 Dark client rect 전체를 `mChrome`으로 지운 뒤 overlay하는지도 고정한다.
- Dark command surface에서 “native first + recolor later”를 최종 text ownership으로 인정하지 않는다.

**검증 상태**
- User runtime screenshot before fix: **FAIL** — Dark top-level menu text black.
- Connector source cross-check after fix: direct Dark WM_PAINT ownership, full print clear, MDI system icon ownership and invariant guards present.
- Rebuilt Windows runtime screenshot after fix: **NOT RETESTED**.


---

## 2026-09-24 — App theme switch exposed mixed Light/Dark intermediate surfaces

**오류 발생**
- 사용자 runtime screenshot에서 Light/Dark 전환 직후 환경설정 창이 먼저 검어지고 내부 page/control은 이전 상태로 남거나, main frame 일부 chrome/content가 서로 다른 theme phase로 보이는 전환 오류가 확인됐다.

**원인 진단**
- `MainFrame::setOption()`은 global theme mode를 먼저 변경했지만 `RefreshThemeForCurrentThread()`가 `EnumThreadWindows()` callback 안에서 각 top-level window를 즉시 `WM_SETTINGCHANGE` 처리하고 바로 `RedrawWindow()`했다.
- 따라서 Preferences, MainFrame, owned dialogs가 순차적으로 화면에 새 palette를 노출했다. 각 handler 내부의 `Invalidate()` / `UpdateWindow()`까지 실행될 수 있어 하나의 theme switch가 여러 visible repaint phase로 분리됐다.
- child window 집합도 사전에 고정하지 않았기 때문에 parent/child refresh 순서에 따라 이전 palette pixel이 잠시 남을 수 있었다.

**해결 방법**
- UI-thread top-level window와 모든 descendant HWND를 먼저 `ThemeRefreshSnapshot`에 수집한다.
- 어떤 theme notification도 보내기 전에 snapshot 전체에 `WM_SETREDRAW(FALSE)`를 적용한다.
- redraw가 잠긴 동안 top-level DWM frame theme를 적용하고, snapshot의 모든 HWND가 동일한 새 global theme mode를 기준으로 `WM_SETTINGCHANGE`를 처리하게 한다.
- child/descendant부터 reverse order로 `WM_SETREDRAW(TRUE)`를 복구한 뒤, 모든 state update가 끝난 후에만 top-level window를 `RDW_ALLCHILDREN`으로 invalidate한다.

**재발 방지**
- source invariant는 `ThemeRefreshSnapshot`, top-level/child snapshot, redraw freeze/thaw, reverse thaw, 새 theme frame 적용, descendant setting notification을 요구한다.
- 과거의 즉시 repaint callback `RefreshThemeTopLevelWindow` 및 top-level마다 `SendMessageToDescendants()`를 수행하는 sequential refresh pattern을 금지한다.

**검증 상태**
- User runtime screenshot before fix: **FAIL** — mixed Light/Dark transition visible.
- Connector source cross-check after fix: atomic snapshot/freeze/apply/thaw/invalidate contract present.
- Rebuilt Windows runtime theme-switch screenshot after fix: **NOT RETESTED**.


---

## 2026-09-24 — Rebar WM_PRINT path still restored black top-menu text

**오류 발생**
- revision `6fd81defc5f7bca63413a92507f21444cb84e044` runtime screenshot에서도 Dark 최상단 `파일/편집/이동/보기/도구/창/도움말` 글자가 어둡게 남았다.
- 같은 화면의 list/content text와 toolbar glyph는 Dark palette를 사용하고 있어 palette 자체의 `mText` 계산 문제는 아니었다.

**전수 조사**
- `src/fxfile`의 `SetTextColor()` 사용 파일 전체와 `COLOR_WINDOWTEXT`, `COLOR_BTNTEXT`, `COLOR_MENUTEXT`, `COLOR_GRAYTEXT`, direct black RGB 사용을 검색했다.
- `BtnST`, `DropMenuButton`, `ColourPickerXP`, `BCMenu`, `CustomizeDialog`, `SearchLocDlg`, list/tree/header/status/tab/address/content controls는 Dark에서 ThemePalette를 사용하고, system text color는 High Contrast/Light fallback 또는 사용자 색 기본값에 한정되어 있음을 확인했다.
- 실제 재현과 일치하는 미해결 경로는 `CMenuBar::WindowProc()`의 rebar print composition이었다.

**원인 진단**
- Dark `WM_PAINT`는 이미 native toolbar paint를 건너뛰었지만 `WindowProc()`은 `WM_PRINTCLIENT` / `WM_PRINT + PRF_CLIENT`에서 항상 먼저 `CToolBar::WindowProc()`를 호출했다.
- rebar는 자식 band를 합성할 때 이 print 경로를 사용하므로 ToolbarWindow32가 검은 native menu text를 먼저 그릴 수 있었다. 뒤 overlay 방식은 실제 runtime에서 최종 pixel ownership을 보장하지 못했다.

**해결 방법**
- print message 여부를 native 호출 전에 판정한다.
- Dark/non-High-Contrast에서는 target HDC 전체 client rect를 `ThemePalette.mChrome`으로 지우고 `DrawFinalMenuOverlay()`로 text/state/system-menu icon을 그린 뒤 즉시 `return 0`한다.
- 따라서 Dark rebar composition에서는 `CToolBar::WindowProc()`가 아예 실행되지 않는다.
- Light는 native print 후 shared overlay를 유지하고 High Contrast는 overlay가 즉시 빠져 system rendering을 그대로 사용한다.

**재발 방지**
- source invariant가 Dark print-owner branch의 위치와 early return 순서를 검사한다. `sOwnDarkSurface -> return 0 -> CToolBar::WindowProc` 순서가 깨지면 실패한다.
- direct `WM_PAINT`와 rebar `WM_PRINT*`를 별개의 final-pixel ownership 경로로 검증한다.

**검증 상태**
- User runtime screenshot before fix: **FAIL** — Dark top-level menu text still dark.
- Repository-wide source text-color audit: **PASS (static/source evidence)** for identified direct-draw call sites.
- Connector source cross-check after fix: Dark print path returns before native ToolbarWindow32 paint.
- Rebuilt Windows runtime screenshot after fix: **NOT RETESTED**.


---

## 2026-09-24 — DWM title bar could switch before frozen client controls

**오류 발생**
- theme-switch screenshot에서 fxfile 제목 표시줄은 이미 Dark인데 menu/toolbar/explorer content는 아직 Light이고, 동시에 Preferences frame/body만 먼저 Dark가 되는 비동기적인 전환 형태가 확인됐다.

**원인 진단**
- logical unit 17-A는 redraw를 freeze했지만 refresh transaction 안에서 top-level frame theme를 descendant setting refresh보다 먼저 적용했다.
- DWM non-client rendering은 child HWND의 `WM_SETREDRAW(FALSE)`와 별개로 즉시 반영될 수 있으므로 제목 표시줄만 먼저 새 theme로 보일 가능성이 남았다.
- 또한 top-level `WM_SETTINGCHANGE` handler 자체도 `applyWindowFrameTheme()`를 호출하므로 top-level notification을 descendant보다 먼저 보내면 같은 문제가 재발한다.

**해결 방법**
- snapshot에 `mChildWindows`를 별도로 유지한다.
- freeze 후 descendant HWND만 먼저 `WM_SETTINGCHANGE` 처리하여 새 palette/theme-association/font state를 준비한다.
- descendant state가 끝난 후 모든 top-level DWM frame theme를 적용한다.
- 그 다음 top-level HWND 자체의 `WM_SETTINGCHANGE`를 처리하고, reverse thaw와 final redraw를 수행한다.

**재발 방지**
- source invariant가 `mChildWindows` 존재와 `child refresh -> applyWindowFrameTheme -> top-level refresh` 순서를 위치 기반으로 검증한다.

**검증 상태**
- User runtime screenshot before fix: **FAIL** — title/frame theme changed before client surfaces.
- Connector source cross-check after fix: child-first/frame-second/top-level-last transaction ordering present.
- Rebuilt Windows runtime theme-switch screenshot: **NOT RETESTED**.


---

## 2026-09-24 — MenuBar still retained a native toolbar theme association

**추가 전수 조사**
- 공용 command toolbar인 `CToolBarEx`와 최상단 `CMenuBar`의 theme-association 처리 차이를 비교했다.
- `CToolBarEx`는 Dark/non-High-Contrast에서 `ModernUI::resetControlTheme()`로 ToolbarWindow32의 native themed painter를 끊고, Light/High Contrast에서는 Explorer/default association을 복구한다.
- `CMenuBar`는 같은 ToolbarWindow32 기반인데 이 처리가 전혀 없었고, `WM_PRINT`도 `PRF_CLIENT`가 있는 경우만 Dark ownership으로 분기했다.

**원인 위험**
- 최종 `WM_PAINT` / 일반 `WM_PRINTCLIENT`를 앱이 직접 그리더라도 CMenuBar HWND에 native visual-style association이 남으면 theme-change/custom-draw/print의 다른 변형에서 uxtheme가 다시 개입할 수 있다.
- rebar/toolbar의 내부 print 호출이 항상 `PRF_CLIENT`를 포함한다고 가정할 근거도 없으므로 일부 `WM_PRINT` 조합은 native `CToolBar::WindowProc()`로 빠질 수 있었다.

**해결 방법**
- `CMenuBar::ApplyModernAppearance()`를 추가해 `CToolBarEx`와 동일하게 Dark에서는 `resetControlTheme()`, Light/High Contrast에서는 `applyExplorerControlTheme()`를 적용한다.
- OnCreate, WM_SETTINGCHANGE, WM_SYSCOLORCHANGE, WM_THEMECHANGED에서 이 association을 갱신하고 tooltip도 Explorer theme를 재적용한다.
- modern Windows의 WM_THEMECHANGED에서는 legacy Window theme handle을 새로 열지 않고 app-owned renderer를 유지한다.
- Dark에서는 `WM_PRINTCLIENT`뿐 아니라 HDC가 제공된 모든 `WM_PRINT`를 native 호출 전에 직접 chrome + menu overlay로 그린 뒤 종료한다.

**재발 방지**
- source invariant가 MenuBar의 theme-association helper 선언/정의와 reset/restore 호출을 요구한다.
- Dark print ownership 검사는 `WM_PRINTCLIENT`와 모든 `WM_PRINT` variant를 포함한다.

**검증 상태**
- Connector source audit: MenuBar/ToolBarEx association parity and Dark all-print ownership implemented.
- Full local `python build/validate_source_invariants.py`: **NOT EXECUTED** in this session because the container could not resolve github.com to materialize a checkout.
- Rebuilt Windows runtime screenshot: **NOT RETESTED**.

---

## 2026-09-24 — Settings navigation hid root expand/collapse affordance

**오류 발생**
- 사용자 runtime screenshot에서 환경설정의 왼쪽 navigation이 사실상 한 단계 목록처럼 보였다.
- `일반`, `모양 및 테마`, `기능`, `고급`은 하위 page를 가진 parent이지만 펼치기/접기 가능 여부를 사용자가 알아차리기 어려웠다.

**첫 실제 source 오류**
- `IDD_CFG_MAIN`의 `IDC_CFG_TREE`에는 `TVS_HASBUTTONS`가 있었지만 root-level disclosure를 표시하는 `TVS_LINESATROOT`가 없었다.
- `TreeCtrlEx::enableVistaEnhanced()`는 full-row/track-select와 extended expando behavior를 설정하지만 root disclosure style 자체를 추가하지 않는다.

**원인**
- hierarchy 의미는 데이터 구조에 존재했지만 resource/runtime style contract에 root affordance가 빠져 있었다.
- borderless card + full-row selection으로 현대화하면서 root/leaf 구분을 보강하지 않아 정보 구조가 더 평평하게 보였다.

**해결 방법**
- `fxfile.rc`의 settings tree resource에 `TVS_LINESATROOT`를 추가했다.
- `CfgMainDlg::OnInitDialog()`에서도 `TVS_HASBUTTONS | TVS_LINESATROOT`를 명시해 Dark에서 Explorer theme association을 reset해도 disclosure contract가 유지되게 했다.
- child를 가진 root category에는 native `TVIS_BOLD`를 적용해 custom text renderer를 하나 더 만들지 않고 parent/leaf hierarchy를 강화했다.
- 기존 expand-all startup, selection, keyboard, icon mapping은 유지한다.

**재발 방지**
- validator는 실제 `IDC_CFG_TREE` resource line을 찾아 `TVS_HASBUTTONS`와 `TVS_LINESATROOT`를 검사한다.
- runtime hierarchy check는 `CfgMainDlg::OnInitDialog()` block에 범위를 제한하고 root disclosure와 parent emphasis를 확인한다.

**검증 상태**
- Connector/source audit: **PASS** — resource/runtime disclosure contract와 scoped invariant가 함께 변경됐다.
- `python build/validate_source_invariants.py`: **NOT TESTED** — 현재 세션에는 실행 가능한 Windows checkout이 없다.
- Release-x64-Unicode | x64 compile/link: **NOT TESTED**.
- Interactive/Visual Light/Dark/High Contrast/DPI: **NOT RETESTED**.
- 사용자 재현 항목이므로 matching runtime screenshot 전까지 CLOSED로 처리하지 않는다.

---

## 2026-09-24 — Shared hover/pressed palette overused the selection accent

**오류 발생**
- 사용자 runtime screenshot에서 Dark command toolbar의 active/hot icon 영역이 주변 chrome보다 지나치게 밝고 푸른 타일처럼 강조됐다.
- 강조 배경이 command icon보다 강해 Windows 11 계열의 중성 command surface와 이질적으로 보였다.

**전수 조사**
- `mHover`/`mPressed` 사용처를 toolbar, menubar, tab, settings, split/drop button, header, folder/content controls까지 확인했다.
- `CToolBarEx`는 이미 Dark에서 legacy HOT bitmap strip을 사용하지 않고 cold image list를 복제하므로, 남은 공통 tint source는 `ThemePalette`의 transient state 색이었다.

**첫 실제 source 오류 / 원인**
- non-High-Contrast `ModernUI::getPalette()`가 `mHover`와 `mPressed`를 `mElevated`와 `mSelection`의 blend로 만들었다.
- `mSelection`은 선택 의미의 system accent color이므로 같은 값을 transient hover/pressed에도 섞으면서 blue/accent tint가 여러 UI surface로 전파됐다.

**해결 방법**
- `mHover`와 `mPressed`를 `mElevated` + `mText`의 작은 Light/Dark-specific lift로 변경해 중성 command/control state로 분리했다.
- 실제 selection/focus는 기존 `mSelection`/`mFocus`를 유지한다.
- High Contrast는 기존대로 system selection colors가 최종 ownership을 가진다.

**재발 방지**
- validator는 `mHover`/`mPressed`의 실제 `blendColor()` assignment block을 추출하고 그 body가 `mSelection`에 의존하면 실패한다.
- 특정 RGB나 blend percentage 자체를 고정하지 않아 향후 palette tuning은 허용하면서 selection accent가 transient state로 다시 새는 known-bad property만 차단한다.

**검증 상태**
- Connector/source audit: **PASS** — shared palette와 property-level regression guard가 함께 변경됐다.
- `python build/validate_source_invariants.py`: **NOT TESTED** — 현재 세션에는 실행 가능한 Windows checkout이 없다.
- Release-x64-Unicode | x64 compile/link: **NOT TESTED**.
- Interactive/Visual Light/Dark/High Contrast/DPI: **NOT RETESTED**.
- 사용자 재현 visual issue이므로 matching runtime screenshot 전까지 CLOSED로 처리하지 않는다.

---

## 2026-09-24 — Transient-palette invariant regex was over-escaped

**오류 발견**
- logical unit 19의 post-commit diff review에서 새 `mHover`/`mPressed` regression guard가 Python raw regex 안에 이중 backslash를 기록한 것이 확인됐다.

**원인**
- GitHub blob 생성용 JavaScript 문자열과 Python raw string의 escaping 층을 혼동해 `\.`/`\s`가 아니라 소스에 `\\.`/`\\s`가 들어갔다.
- 이 상태에서는 정상 `sPalette.mHover = blendColor(...)` assignment를 찾지 못해 false failure가 날 수 있다.

**해결 / 예방**
- Python source regex를 `sPalette\.{state_name}\s*=\s*blendColor...` 형태의 단일 regex escape로 바로잡았다.
- post-commit source를 다시 fetch해 실제 저장된 문자열을 확인하는 절차를 이 logical unit에 적용했다.

**검증 상태**
- Sample regex match against the intended assignment shape: **PASS**.
- Repository `python build/validate_source_invariants.py`: **NOT TESTED** — 실행 가능한 Windows checkout 없음.

---

## 2026-09-24 — Legacy dependency and mixed-architecture audit

**조사 목적**
- 오래된 vendored library와 x64 + Win32 helper 구조를 '오래됐으니 교체' 방식으로 다루지 않고 실제 GYP/source/package dependency를 기준으로 분류했다.

**관찰 결과**
- GFL, libxml2, iconv, libcurl, MinGW runtime은 현재 source/link/runtime packaging에서 실제 사용된다.
- zlib은 crash component의 source-built target과 libxml2 계열 runtime DLL이라는 서로 다른 형태로 존재한다.
- VLD는 leak-detection용 개발 의존성이지만 release copy path도 남아 있어 별도 staging 검증이 필요하다.
- vendored gtest와 libxslt는 현재 flyExplorer GYP/production source consumer가 검색되지 않았지만, 동적/외부 수동 consumer 가능성을 확인하기 전에는 삭제 근거가 충분하지 않다.
- keyhook/launcher/upchecker의 Win32 유지에는 기존 helper/packaging 계약이 연결돼 있고, 특히 upchecker는 prebuilt network/XML/charset runtime과 결합돼 있다.

**결정**
- 이번 unit에서는 dependency 삭제/업그레이드나 helper x64 전환을 수행하지 않는다.
- 근거와 단계별 migration 후보를 `docs/development/DEPENDENCY_ARCH_AUDIT_20260924.md`에 기록했다.

**검증 상태**
- Repository source/GYP/package reference audit: **PASS (connector evidence)**.
- PE import/ABI inspection: **NOT TESTED**.
- Windows compile/runtime/package: **NOT TESTED**.

---

## 2026-09-24 — Final documentation reconciliation for UI/dependency audit

**논리적 작업 단위 / commit**
- Settings navigation disclosure + hierarchy: `608b166bf17d5847fcb14dfdfc4d4546d6770b86`.
- Neutral transient hover/pressed palette: `2f84caccfaff6d116a8e75d1377ccf90ddd9fbd5`.
- Transient-palette invariant regex correction found during post-commit review: `7c40d913163d84e90ec2b47cfcd0061d605f0958`.
- Dependency/mixed-architecture audit: `12aa5fd5d334f2fb5cabe420bdf4d80964449715`.

**최종 문서 대조**
- `AGENTS.md` / `.agent-policy/AGENTS.md`: tool choice, source-of-truth, Git safety, runtime-evidence rules remain current; no change required.
- `README.md`: build toolchain/default active build contract was not changed; no change required.
- `LOCAL_CI_MANUAL.txt`: active `Release-x64-Unicode | x64` scope and Actions pause policy were not changed; no change required.
- `.agent-policy/PROJECT.md`: user-reproduced settings/highlight items and dependency/architecture audit are current and keep runtime evidence open.
- `docs/development/ERROR_HISTORY.md`: each completed logical unit records cause/change/prevention/evidence without promoting NOT TESTED to PASS.
- `docs/development/DEPENDENCY_ARCH_AUDIT_20260924.md`: current dependency and mixed-architecture findings are recorded.

**최종 connector/source cross-check**
- `IDC_CFG_TREE` resource and runtime init both preserve root disclosure; expandable roots receive hierarchy emphasis: **PASS (source evidence)**.
- `ThemePalette.mHover/mPressed` derive from neutral text/elevated colors rather than `mSelection`: **PASS (source evidence)**.
- New validator guards are scoped to the settings init/resource contract and transient palette assignment property: **PASS (source inspection)**.
- Existing Dark `CMenuBar` direct paint/print ownership and text contrast floor remain present: **PASS (source evidence)**.

**미실행 검증**
- `python build/validate_source_invariants.py`: **NOT TESTED** in an executable repository checkout.
- Release-x64-Unicode | x64 compile/link, functional regression, runtime smoke: **NOT TESTED**.
- Interactive runtime / Visual Dark / Visual Light / High Contrast / DPI: **NOT RETESTED**.
- x86 / packaging / installer: **NOT TESTED** and outside the currently active scope.

**main 반영 전 상태**
- Work branch was compared against `main`: ahead 4, behind 0 at the reconciliation checkpoint.
- `main` was still `bce54ce2a274a3f27e86f5f5871c9e2964c4c2cc` at that checkpoint.
- Final branch/main fast-forward is performed only after this reconciliation commit is created.

---

## 2026-09-24 — Settings navigation disclosure was both required and forbidden by source invariants

**오류 발생**
- 사용자 `local_ci.bat x64` 실행이 revision `7558639752dccc2bafb4822d3152044a4cdc379f`에서 source invariant/regression preflight 단계에서 즉시 실패했다.
- 실제 오류: `src/fxfile/fxfile.rc: legacy configuration navigation token returned TVS_LINESATROOT`.
- preflight 실패 때문에 Visual Studio solution generation/build는 시작되지 않았고 기존 `bin\x64\fxfile.exe`는 이전 revision `bce54ce2a274a3f27e86f5f5871c9e2964c4c2cc` 산출물 그대로 남았다.

**첫 실제 원인**
- `validate_configuration_shell_contract()`의 과거 negative rule이 `TVS_HASLINES`, `TVS_LINESATROOT`, `WS_BORDER | WS_HSCROLL`를 모두 legacy token으로 금지하고 있었다.
- 반면 settings discoverability 수정에서는 `TVS_LINESATROOT`를 root expand/collapse affordance의 필수 contract로 도입했고, 새 invariant도 resource/runtime에서 이를 요구했다.
- 같은 source property를 한 validator에서는 금지하고 다른 validator에서는 요구하는 self-contradictory guard가 만들어졌다.

**해결 방법**
- 오래된 forbidden set에서 `TVS_LINESATROOT`만 제거했다.
- `TVS_HASLINES`와 classic `WS_BORDER | WS_HSCROLL` 금지는 그대로 유지한다.
- 신규 settings-navigation invariant의 `TVS_HASBUTTONS + TVS_LINESATROOT` positive requirement와 `OnInitDialog()` scoped runtime-style guard는 유지한다.

**재발 방지**
- negative rule 바로 위에 `TVS_LINESATROOT`의 현재 semantic ownership을 설명해, root disclosure가 legacy ornament와 다시 혼동되지 않도록 했다.
- 새 UI contract를 추가할 때 동일 property가 기존 forbidden/required rule 양쪽에 있는지 post-change validator audit 대상으로 본다.

**검증 상태**
- User local CI revision `7558639752dccc2bafb4822d3152044a4cdc379f`: **FAIL at source invariant preflight**.
- Connector source cross-check after fix: contradictory forbidden token removed; positive disclosure guards preserved: **PASS (source evidence)**.
- Rerun `local_ci.bat x64`: **NOT RETESTED**.
- Compile/link/functional/runtime/visual: **NOT TESTED** because the failing run stopped before project generation/build.

---

## 2026-09-24 — Fresh-build settings disclosure still invisible

**사용자 증거**
- `git pull` 후 다시 빌드한 설정 화면에도 root parent/leaf는 있지만 펼침·접힘 조작을 발견할 수 있는 화살표는 보이지 않는다. 과거 CI 실패 로그를 이 최신 runtime 증거의 stale-binary 근거로 사용한 것은 잘못이었다.

**첫 source 원인**
- `TreeCtrlEx::enableVistaEnhanced()`는 현대적인 borderless tree를 위해 `TVS_HASLINES`를 제거한다.
- 이전 fix는 `TVS_LINESATROOT`와 `TVIS_BOLD`만 추가했고 최종 표시 픽셀과 클릭 동작을 보장하지 않았다.

**수정**
- 설정 navigation의 `CDDS_POSTPAINT`에서 root parent마다 expanded/collapsed에 맞춘 화살표를 아이콘 앞 독립 gutter에 직접 그린다.
- custom glyph click에 `NM_CLICK`으로 collapse/expand를 연결한다. 원래 native button hit·텍스트 페이지 선택·keyboard 동작은 보존한다.
- High Contrast에서는 system text 색상을 사용하고 tree native item renderer를 보존한다.
- 스타일 token 존재만 검사하던 regression guard를 실제 postpaint/interaction 경로 확인으로 보완했다.

**검증**
- 사용자 제공 최신 설정 screenshot: 이전 구현에 대해 VISUAL FAIL.
- 소스 변경: CONNECTOR DIFF REVIEW 대기/이후 확인.
- `local_ci.bat x64`, interactive Dark/Light/HC/DPI: NOT TESTED. runtime screenshot 통과 전에는 CLOSED 금지.

---

## 2026-09-24 — Fresh-build dark toolbar kept native blue icon tile

**증거**
- 사용자는 pull 후 직접 빌드한 화면에서 밝은 청색 toolbar tile이 그대로 보임을 재현했다. 과거 stale-artifact 로그로 최신 runtime screenshot을 부정하지 않는다.

**원인**
- `ApplyDarkToolBarCustomDraw()`은 native toolbar item paint를 보존했고 `DrawFinalDarkToolbarItem()`은 text/dropdown만 다시 그렸다. 따라서 native hot/checked icon 배경은 그대로 노출될 수 있었다.

**수정/예방**
- Dark item postpaint에서 전체 item을 중성 배경으로 지우고 hot/pressed/checked state를 명시적으로 그리고 ImageList 아이콘, 기존 text/dropdown final draw를 수행한다.
- 아이콘 데이터가 없는 특수 경로는 원본 native 아이콘을 지우지 않고 유지한다. Light/HC는 기존 owner 유지.
- validator는 `DrawOwnedDarkToolbarItem`의 전체 배경/아이콘 redraw와 실제 postpaint 사용을 함수 범위에서 확인한다.

**검증**
- 이전 사용자 screenshot: VISUAL FAIL. 본 수정의 Release-x64-Unicode build/functional, interactive Dark/Light/HC/DPI: NOT TESTED. 현재 시각적 해결 완료로 기록 금지.

---

## 2026-09-24 — Fresh-build top-level Dark menu labels remain dim

**사용자 증거**
- 사용자가 git pull 후 직접 다시 빌드해 촬영한 Dark main window에서 상단 파일/편집/이동/보기/도구/창/도움말 label이 여전히 어둡다.
- 앞서 제출된 preflight 실패 로그를 새 runtime screenshot의 stale-binary 증거로 취급한 것은 오류였으며 이 이슈를 새 runtime failure로 기록한다.

**소스에서 발견된 추가 누출 가능 경로**
- `CMenuBar::OnCustomDraw()`이 item draw만 요구하고 `CDDS_POSTPAINT` 전체 final overlay는 요청하지 않아 notification-driven native 후속 pixel을 제어하지 못했다.
- toolbar text lookup 실패 시 item custom draw는 `CDRF_DODEFAULT`로 빠지고 `DrawFinalMenuOverlay()`는 빈 string을 건너뛰어 실제 HMENU title까지 확인하지 않았다.

**수정**
- modern menubar custom draw가 `CDRF_NOTIFYPOSTPAINT`를 요청하고 `CDDS_POSTPAINT`에서 Dark 전체 label overlay를 최종 출력하도록 했다.
- toolbar 문자열이 없거나 빈 경우 `m_pMenu->GetMenuString()`을 조회하여 app-owned label을 복원한다.
- Dark item 문자열 검색 실패는 black native text fallback 대신 neutral background + `CDRF_SKIPDEFAULT`로 안전하게 처리한다.
- 기존 `WM_PAINT`/`WM_PRINT*` 직접 ownership과 High Contrast native/system renderer는 유지한다.

**검증**
- 사용자 제공 이전 구현 screenshot: VISUAL FAIL.
- notification 경로가 사용자 화면의 직접 원인인지 Windows instrumented trace는 아직 없다. 신규 수정의 Release x64 compile/runtime/interactive/visual/HC/DPI: NOT TESTED. 실제 화면 확인 전 종결 금지.

---

## 2026-09-24 — Reconciliation of three fresh-build visual regressions

**논리 작업 단위별 commit**
- 설정 disclosure 실제 화살표/클릭: `4e8e8d63918ef73783b4b7f87a54e8469b73a122`.
- Dark toolbar 전체 버튼/아이콘 최종 그림: `164c016bcbc7587cc3e21908de72e91f00ac21f6`.
- Dark menubar notification 후속 repaint/문자열 fallback: `aa3c2d05b76c6ff2d6dece824992b80d88b17505`.

**추가 정적 검토와 마감 보완**
- 소스 교차검사에서 tree postpaint, 실제 chevron 클릭 handler/message map, toolbar 전체 item/icon redraw, menubar final custom postpaint/HMENU fallback 및 새 validator property guards가 모두 연결됨을 확인했다.
- CMenu의 `GetMenuItemCount()`와 signed item index 비교를 명시적 signed cast로 정리해 컴파일 경고 가능성을 낮추고, custom chevron 클릭 후 tree invalidation으로 화살표 방향 갱신을 명시했다.
- 과거 이슈 #16/#18/#19는 최신 사용자의 runtime screenshot과 모순되지 않도록 `PREVIOUS FIX VISUALLY FAILED`로 정정하고 새 이슈 #24/#22/#23에 연결했다.
- AGENTS/README/LOCAL_CI_MANUAL/GYP/architecture 계약은 이번 UI 렌더러 변경 범위에서 바뀌지 않아 수정하지 않았다.

**최종 검증 수준**
- GitHub source/diff/validator contract cross-check: PASS (static source inspection only).
- 전체 Python validator 실행 및 Release-x64-Unicode | x64 local CI, native functional/smoke: NOT TESTED.
- 실제 Windows Dark/Light/High Contrast/100%+high DPI/keyboard/interactive visual regression: NOT TESTED.
- 본 커밋 이후 main 반영 여부는 merge 결과 확인으로만 보고한다. 시각적 이슈는 matching runtime screenshot 통과 전 CLOSED 금지.

---

## 2026-09-24 — GitHub Actions storage reached 90% of included quota

**사용자 증거**
- GitHub 알림에서 account Actions storage 0.45 GB / 0.5 GB(90%) 사용 경고가 확인됐다.

**저장소 조사**
- flyExplorer에는 Actions run history가 198건 남아 있다.
- 현재 `.github/workflows/windows-build.yml`과 `policy-validation.yml`은 push/PR 자동 실행이 없고 explicit `workflow_dispatch`만 남아 있으며 현재 source에는 artifact upload step이 없다.
- 과거 Windows success run을 표본 조회한 결과 `flyExplorer-release-package`가 약 62–63 MB씩 미만료 상태로 반복 보관돼 있다. 일부 run의 runtime/upchecker artifacts는 이미 expired였지만 release package는 남아 있었다.
- 최근 one-off Release/Dark audit 두 run의 artifact list는 비어 있었다.

**원인/판단**
- 현재 workflow가 계속 새 storage를 생성하는 문제라기보다 과거 CI에서 반복 업로드한 release package의 retention이 누적된 것이 flyExplorer 측 주요 원인으로 보인다.
- 8개의 63 MB package만으로 약 0.49 GiB이므로 알림 규모와 일치하지만, GitHub billing 경고는 account 단위이므로 flyExplorer가 100% 원인이라고 단정하지 않는다.

**수정**
- `build/actions_storage_cleanup.py`를 추가했다. 기본은 dry-run, 동일 이름 artifact 중 최신 1개 보존, `--apply` 때만 과거 중복을 DELETE하고 선택적으로 repository artifact/log retention을 변경한다.
- cleanup 자체가 새 hosted run을 만들지 않도록 로컬 도구로 구현했다.
- source invariant가 hosted workflow의 `actions/upload-artifact`, `actions/cache`, `actions/upload-pages-artifact` 재도입을 금지한다.
- `LOCAL_CI_MANUAL.txt`에 dry-run/apply 및 token permission을 기록했다.

**검증 상태**
- GitHub connector repository/workflow/history/artifact sample audit: PASS.
- Connected GitHub tool does not expose artifact DELETE or repository retention write, so historical storage reclamation itself: NOT APPLIED.
- Cleanup script full live dry-run/apply with user token: NOT TESTED.
- GitHub billing usage after cleanup: NOT TESTED.

**Post-commit compatibility review**
- 첫 cleanup-tool draft에 Python 3.10의 PEP 604 `|` union annotation이 들어간 것을 발견했다. flyExplorer의 documented minimum은 Python 3.9+이므로 main 반영 전에 `typing.Optional`/`Tuple`/`Dict` 표기로 수정했다.
- validator가 cleanup script의 Python 3.9-compatible annotation contract도 확인하도록 보완했다.
- 이 보정 commit 전 live GitHub API 실행은 하지 않았다.

---

## 2026-09-24 — Actions storage prevention final reconciliation

**논리 작업 단위 commit**
- storage growth prevention + local cleanup tool + documentation: `be27fe0e886f88896cba9cb58df45367adf69e02`.
- Python 3.9 compatibility correction found during post-commit review: `57ac0fb07641d80ac1f8308d8586384944814a66`.

**현재 repository contract**
- hosted workflow는 explicit manual dispatch만 유지하고 `actions/upload-artifact`, `actions/cache`, `actions/upload-pages-artifact`를 사용하지 않는다.
- source invariant가 이 hosted storage producer 재도입을 차단한다.
- local cleanup은 기본 dry-run이며 `--apply` 없이는 삭제/retention 변경을 하지 않는다.
- 동일 이름 `flyExplorer-release-package`는 기본적으로 최신 1개를 보존한다.

**미완료 외부 작업**
- 현재 연결된 GitHub connector에는 artifact DELETE 및 repository retention WRITE operation이 노출되지 않아 이미 저장된 historical package의 실제 삭제는 수행하지 못했다.
- `build/actions_storage_cleanup.py`를 사용자 GitHub credential로 실행한 뒤 GitHub Billing/Usage가 감소했는지 확인해야 한다.
- account-level storage가 여전히 높으면 flyExplorer 외 repository가 원인인지 추가 조사한다.

---

## 2026-09-24 — Supported Windows was classified as XP, bypassing all modern command painters

**재현 / acceptance case**
- Windows 11에서 Dark 모드로 실행 → top menu, main command, drive 및 bookmark toolbar 이름이 검게 표시됨 → 각 이름이 Dark palette의 밝은 foreground로 읽혀야 한다. Light와 High Contrast의 기존 분기는 보존한다.
- 사용자 screenshot과 수정 전 `bin/x64/fxfile.exe`의 직접 실행 화면에서 동일 실패를 확인했다.

**최초 실제 오류 / 원인**
- `WinAppEx` 생성자가 지원 OS인 Windows 10/11을 `m_eOs = osWinXP`로 고정했다. `IsWinXP()`가 항상 true여서 `ApplyDarkToolBarCustomDraw`, menu paint/print/overlay 및 toolbar theme association의 modern 분기가 모두 실행되지 않았다.
- 기존 painter의 palette/notification/postpaint 코드가 존재해도 진입 조건에서 배제됐다. 같은 판정에 의존하는 rebar/splitter border와 popup 경로도 함께 확인했다.
- 이 고정값은 `5ac5cfe`의 legacy OS probing 제거에서 도입됐다. 실제 screenshot을 stale binary 또는 별도 renderer overwrite로 단정하지 않는다.

**해결 / 재발 방지**
- `osWinModern`을 추가해 지원 Windows와 XP-only presentation을 분리했다. `IsWin50`, `IsWinNT`, `IsWin2K`의 modern API capability는 true로 유지한다.
- flat-menu system parameter 조회/검증은 `IsWinXPOrLater()`로 분리해 초기화와 기존 menu capability를 유지한다. OS version API나 새 dependency는 추가하지 않는다.
- source preflight에 modern OS의 XP 오분류 금지, capability 유지 및 flat-menu 초기화 조건 검사를 추가했다. 수정 전 source에서 FAIL, 수정 후 PASS를 확인했다.

**검증 상태**
- 수정 전 Windows 11 Dark 시각 재현: FAIL (검은 menu/toolbar label 직접 관찰).
- Source invariant/regression preflight 및 policy bundle validation: PASS.
- policy development readiness: documented PASS / source-evidence FAIL — 기존 PROJECT.md reviewed revision 이후 reviewed paths가 변경된 상태. 이번 product 오류와 별개다.
- `local_ci.bat x64`: PASS WITH SKIPS — Release-x64-Unicode | x64 compile/link PASS, functional regression 17 passed / 0 failed. 기존 HKCU profile/startup 값 보호로 runtime smoke는 SKIPPED / NOT TESTED.
- 검증 환경 복구: 첫 sandbox 실행은 batch Python discovery 실패, 다음 실행은 실행 중인 검증용 앱의 output lock으로 compile 전에 중단됐다. Python 경로를 지정하고 사용자에게 창 종료를 받은 뒤 동일 profile을 재실행해 위 결과를 얻었다. 빌드는 `40ac0f2` + 이번 working-tree source 변경 기준이다.
- 수정 후 runtime/visual: NOT TESTED — 사용자가 Escape로 Computer Use를 중단하여 추가 UI 조작을 중지했다. 새 x64 binary에서 위 acceptance case와 Light/Dark 전환, menu/toolbar hover 및 High Contrast를 확인해야 한다.
- GitHub Actions: NOT RUN (실행별 명시적 지시 없음).

**관련 commit**
- 이 항목과 함께 반영하는 `fix: Windows 10/11의 XP 오분류로 누락된 다크 렌더링 복구` commit.

---

## 2026-09-24 — Documentation alignment after supported-Windows OS fix

**Scope and baseline**
- Product code remains at `6b18c58f`. Documentation-only source checkpoint:
  `5e3d8d4ad85e03b5cbe4db3d4457b0058c16687b` (README, Windows 11 UI reference, distribution README,
  legacy HTML system-requirements source, dependency audit follow-up).
- The accompanying PROJECT documentation checkpoint updates its source-review
  revision to the preceding documentation commit; no product source, GYP,
  build or GitHub Actions workflow is modified.

**Corrections**
- Replaced README's expired 2026-09-30 CI-pause/restart language with the
  permanent per-run user-approval restriction already enforced by AGENTS,
  LOCAL_CI_MANUAL and manual-only workflow definitions.
- Separated `6b18c58f` parent-plus-working-tree x64 build/functional
  evidence (PASS WITH SKIPS, launch SKIPPED) from unverified post-fix interactive
  Dark/Light/High Contrast visual results.
- Reconciled the Windows 11 UI reference's pre-generator roadmap with the
  standard-library deterministic 23-command Fluent pipeline and kept the
  historical 51-frame bitmap fallback distinction.
- Replaced outdated Win98/IE5/minimum-hardware claims in installer-facing
  readme and HTML requirements *source* with the documented active development
  and CI scope. Original product features and old history/credits were retained.
- Appended post-audit evidence without rewriting the dependency audit's
  original "NOT TESTED" results.

**Open limitation / evidence**
- The installer stages existing binary `dist/fxfile.chm`. That compiled
  legacy help was NOT REGENERATED; its included requirements may still be old.
  Regeneration and package/installer inspection require a separate, explicitly
  authorized Windows packaging validation unit.
- Static source/text consistency checks and source-path presence checks were
  performed through the repository connector. Policy/readiness CLI, C++ builds,
  product runtime, installer/package and visual tests were NOT RUN in this
  documentation-only synchronization. The historical local build results above
  are not new tests for this commit.

---

## 2026-09-24 — Reversible removal of unused vendored gtest/libxslt

**Observed:** 29 tracked build/GYP/packaging/validation entry points were
checked for direct references. None consume `lib/gtest/` or `lib/libxslt/`.
The product's native functional regression is an in-repository test executable.

**Change:** Dedicated cleanup removes 41 gtest files and 52 libxslt files;
removes the gtest-only block from `CREDITS`; records the result in
`PROJECT.md` and the dependency audit. Active `libxml2` and all other
bundled binary requirements remain unchanged. Old analysis remains
available through Git history.

**Verification:** Static manifest/script reference inspection: PASS.
External/manual consumption: NOT PROVEN. Windows x64 compile/test, x86,
runtime ABI, package/installer: NOT TESTED. No GitHub Actions run.

---

## 2026-09-24 — Identical zlib artifacts and unused NSIS SDK extras

**Observation:** `lib/zlib/bin/` contains 16 files with exact matching Git
blob IDs under `lib/zlib/lib/` (4,083,104 duplicate bytes). None of
29 first-party GYP/build/validation/packaging entry points refers to
`lib/zlib/bin/`. The active crash module compiles source from
`lib/zlib/src/` and the packaged XML zlib runtime comes from
`lib/libxml2/`.

**Scoped cleanup:** Remove only the duplicated zlib `bin/` directory
and non-build NSIS developer material (`Docs/`, `Examples/`, NSIS
developer HTML help and standalone/GUI executables). Keep CLI
`makensis.exe`, all compiler/runtime Includes/Contrib/Plugins/Stubs/Bin,
bundled NSIS COPYING and the current `dist/setup.nsi` installer input.

**Verification:** Static blob equality plus tracked first-party script
reference audit: PASS. Windows NSIS package generation, installer/smoke,
external developer scripts and Linux/Wine help regeneration: NOT TESTED.
No GitHub Actions run.

---

## 2026-09-24 — Installer-facing GPL notice versus legacy freeware EULA

**Observed conflict:** Root `LICENSE` states that the application source is
GPL version 3 or later. `dist/license.txt` and the legacy HTML help
previously asserted freeware terms forbidding modification and restricting
commercial redistribution. Both notices were presented as current, and
the installer did not separately expose the current `CREDITS` text.

**Scoped correction:** Replace both old application-facing notices with
references to the existing GPL license; do not invent new grant language.
Install the current `CREDITS` under `third_party_notices.txt` with
a Start Menu link and uninstall removal; update installer OS-selection
disclosure, distribution README and root README. Maintain historical
attributions and all active third-party license text.

**Unresolved distribution blocker:** The GFL SDK terms recorded in
`CREDITS` impose separate restrictions; legality/compatibility of the
combined product installer, source entitlement and binary provenance
are NOT VERIFIED. See the newly created
`docs/development/DISTRIBUTION_LICENSE_REVIEW.md` before public release.
The previous precompiled `dist/fxfile.chm` still contains old content at
this checkpoint until regenerated or excluded.

**Evidence:** Text and installer-script consistency inspection: PASS.
Legal/third-party rights, Windows installer, CHM binary, package and
runtime: NOT TESTED. Hosted Actions: NOT RUN.

---

## 2026-09-24 — Stale tracked CHM replaced with fail-closed help generation

**Observed error / requirement**
- The previous `docs/htmlhelp/flyExplorer.hhp` compiled to
  `flyExplorer.chm` while `dist/setup.nsi` and the running product
  required `fxfile.chm`. The tracked `dist/fxfile.chm` was a legacy,
  unregenerated binary despite updates to its requirements/license sources.
- The keyword index also contained two broken topic links:
  `html\\datetime.htm` and `html\\function\\using.htm`.

**Correction / prevention**
- Make the canonical HTML Help project output `fxfile.chm`, correct both
  index targets, update the opening page with the current development
  baseline and label the old feature/reference pages as historical.
- Introduce offline `build/rebuild_htmlhelp.py --check/--stage/--build`;
  stage source topics with corrected UTF-8 HTML charset metadata and
  Korean CP949 project/index text only in generated staging. Compile
  only with an existing Microsoft `hhc.exe`, validate the generated
  CHM signature and fail closed without reusing a prior CHM.
- Call the generator from every `dist/make_installer.bat` path and add
  its `--check` to the source-invariant preflight. Ignore generated
  CHM/staging and remove the old tracked `dist/fxfile.chm`.
- Synchronize README, AGENTS, LOCAL_CI_MANUAL and the install-facing
  README/licensing review; retain historical help source content.

**Evidence / unresolved**
- Generator Python syntax plus synthetic-source `--check`, `--stage`,
  invalid-index rejection and no-compiler fail-closed behavior: PASS
  (isolated disposable fixture only; not proof of real repository CHM).
- Repository static index/source and packaging contract inspection:
  source-level reviewed. Actual installed Windows `hhc.exe` run,
  generated CHM topic navigation, x64 product Help runtime and installer/
  package regression: NOT TESTED; historical feature pages remain
  intentionally identified as historical. GitHub Actions: NOT RUN.
- Third-party GFL SDK redistribution rights remain NOT VERIFIED; do
  not publish a combined installer based on this cleanup alone.

---

## 2026-09-24 — Reviewed-path metadata after help source generation checkpoint

After `f18503301b289eea504cfe07eb96c13b442e5748`, compared the earlier recorded review snapshot
`5e3d8d4ad85e03b5cbe4db3d4457b0058c16687b` with the current source
checkpoint (5 later commits, 243 changed files including intentional
vendor-file deletions). Existing reviewed paths touched by the cleanup:
AGENTS.md, LOCAL_CI_MANUAL.txt, README, source invariants, installer build
script and NSIS input, distribution README and dependency audit. Added
direct review-path coverage for the help generator, HHP/HHK/start and
license/about topics, CREDITS, root LICENSE and installer licensing
documentation. `PROJECT.md` now records `f18503301b289eea504cfe07eb96c13b442e5748` as the
source-review revision; this metadata/history-only commit is outside the
tracked review-source paths.

Verification: GitHub source-tree diff and changed-path inspection: PASS.
The vendored policy/readiness CLI and Windows/full release tests: NOT RUN.
The actual Microsoft HTML Help Workshop output and release rights:
NOT VERIFIED; do not elevate this metadata update to a runtime PASS.

---

## 2026-09-24 — Four unused root HTML frameset files retired

**Observed:** The root `docs/htmlhelp/index.htm`, `left.htm` and
`main.htm` implement a legacy browser frameset. The latter two refer
to an absolute former developer workstation path and the old
`flyExplorer.chm`; the root `style.css` is their unused companion.
All 79 other tracked HTML Help HTML/CSS/HHP/HHC/HHK files were inspected
for relative `href/src` links into the four proposed removals. No
surviving help source reference was found. The actual product calls the
Windows HTML Help API against generated `fxfile.chm` and the canonical
help project starts at `Html/start.htm`.

**Change:** Remove only the four obsolete frameset assets; retain
`docs/htmlhelp/Html/style.css` and `Html/config/style.css`.
Reject these obsolete root inputs in the read-only HTML Help
source preflight to avoid accidentally shipping them later.
The dependency audit now distinguishes 222 prior completed vendor-file
removals from historical recommendations and documents current active
third-party library dependencies.

**Verification:** Checked canonical help manifest/TOC/index,
79 remaining textual HTML Help sources and product Help command source.
No remaining tracked help source references the removed frameset assets.
External bookmarks/manual workflows cannot be ruled out. Fresh
Windows `hhc.exe`/CHM topic browsing, x64 compile/runtime and installer
checks: NOT TESTED. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Current-development user guide and historical-help labelling

**Observed:** Existing HTML Help covers many old menu, screenshot, keyboard,
feature and release-documentation topics, but the previous new landing page
only warned globally that they were historical. It did not provide an
actual current-version user-oriented guide. The old support topic still
made unverified website and future-support promises.

**Scoped changes:** Add `Html/current_development.htm` describing only
observed repository functionality and the active Windows x64 development
scope. Link it from `Html/start.htm`, `flyExplorer.hhc` and
`flyExplorer.hhk`, and validate the required page/index references
through `build/rebuild_htmlhelp.py --check`. Mark older menu, UI screenshot,
shortcut, overview, configuration, feature and prior-release index pages
as historical; preserve their detailed records. Replace stale support
promises with transparent contact-status guidance. Add the inventory and
acceptance plan to `docs/development/HELP_CONTENT_AUDIT.md`.

**Evidence:** Source implementations and README were cross-checked for
appearance modes, navigation, tab settings and runtime icon mappings;
textual cross-link and source-contract preflight can be inspected.
Windows HTML Help compiler, built CHM layout, per-page contemporary
user interactions, localized shortcuts and visual/accessibility
acceptance: NOT TESTED. GitHub Actions: NOT RUN. Remaining old detailed
pages are not represented as fully modernized.

---

## 2026-09-24 — Separate current status from preserved historical evidence

**Observed:** `ERROR_HISTORY.md` is an append-only evidence archive covering
multiple product and documentation revisions. The installer-visible
`dist/history.txt` begins with a 2010 release, so placing these records
next to live requirements without explicit scope risks confusing
historical evidence with a verified current build.

**Change:** Add `docs/development/CURRENT_STATUS.md` as the short live
status, open-work and evidence-level entry point; link it from README and
the head of this history without deleting or rewriting prior diagnosis.
Clearly label `dist/history.txt` as historical while preserving its
entire original release record and present installer wiring. Extend
`PROJECT.md` handoff instructions so each completed unit updates this
status summary whenever relevant, alongside its existing
PROJECT/ERROR_HISTORY obligation.

**Evidence:** Repository documentation cross-reference and original
history-body preservation: static inspected. New Windows compile, CHM
generation, installer/runtime, third-party licensing: NOT TESTED.
GitHub Actions: NOT RUN.

---

## 2026-09-24 — Reviewed paths refreshed after documentation maintenance

Following source-and-document snapshot `3e6a8914825c7527a0be1898a035a7004a598d60`, review metadata
now includes the preserved `dist/history.txt`, the new
`CURRENT_STATUS.md` and `HELP_CONTENT_AUDIT.md`, the newly authored
current user-help HTML topic, and the formerly misleading historical
help entry-point pages. The earlier baseline
`f18503301b289eea504cfe07eb96c13b442e5748` remains a dated
snapshot in prior entries, not the current review baseline.
The separate metadata commit changes only `PROJECT.md` and this
historical evidence document; neither is in the project's
`reviewed_paths` list.

Static Git tree/path coverage and internal CHM topic/index references:
source inspected. Windows policy/readiness CLI, HTML Help Workshop,
full product build/runtime, visual acceptance and installer:
NOT TESTED. Hosted GitHub Actions: NOT RUN.

---

## 2026-09-24 — Portable ZIP omitted product Help and licensing resources

**Error / evidence:** The old `dist/make_portable.bat` archived only each
`dist/bin/<architecture>` runtime tree. `dist/copy.bat` supplied runtime
DLLs and language packs but not `fxfile.chm`, root-level custom icon
bitmap resources or installer-facing application/third-party notices.
The product Help command calls Windows HtmlHelp with the generated
`fxfile.chm` path, and the NSIS installer explicitly includes these
non-runtime files. Consequently the existing portable package source
contract omitted resources available in the installer.

**Root cause:** Installer packaging and portable packaging owned separate
file-copy lists; only the installer invoked fresh HTML Help compilation.
The release validator checked binaries/architectures but not a portable
CHM or its user-facing notices.

**Fix / prevention:** Each direct `make_portable.bat` now regenerates CHM
from canonical source, fails closed, stages the CHM, 16/32px optional
file-list icon assets, application license, current `CREDITS` as
`third_party_notices.txt`, readme and preserved legacy history into
each architecture's ZIP root. The standalone installer retains its own
fresh rebuild. `validate_package.ps1` requires all assets in staging
and archives and checks the CHM ITSF signature. HTML Help static preflight
rejects missing portable and validator wiring.

**Evidence:** Repository source cross-check/structural contracts:
source inspected. Windows `hhc.exe`, batch/7zip/package validator on a
real three-architecture build, actual installed and portable product Help:
NOT TESTED. Neither updater server security nor GFL/public distribution
rights were changed. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Updater claimed successful writes despite disk failure

**Observed defect:** The Win32 update checker supplied libcurl a disk-writing
callback that returned `sBufferSize` regardless of the actual filesystem
write result. A missing/unwritable full metadata file or short write could
therefore be treated as an ordinary network transfer and fall through to
metadata parsing. No aggregate metadata byte limit or timeout was set.

**Root cause:** Curl callback return value used requested bytes, not the
written-byte count, and local transfer state did not accumulate payload size.

**Scoped fix:** Add the pure overflow-safe cumulative 256 KiB metadata budget;
initialize and update per-transfer written bytes, return only actual writes
from `UpdateChecker::downloadFile` and abort on oversized chunks. Add
15-second connect / 45-second total timeouts and `CURLOPT_FAILONERROR`.
Register the direct header in both updater and test GYP files, add native
boundary assertions and a source-invariant guard against restoring the
false success return path.

**Evidence:** Nine isolated cross-platform C++11 boundary cases passed
under g++ with warnings treated as errors. Windows native regression,
upchecker compile and actual curl network/disk-failure behavior: NOT TESTED.
The existing old HTTP update endpoint and unsigned metadata remain
untrusted and require independent server, TLS, provenance and release
integrity work. No GitHub Actions runs.

---

## 2026-09-24 — Source review checkpoint after portable and updater improvements

Reviewed implementation commits:
- `cb3cdafb2d4521f35fcfadcd2acee6c6fe822b6c`: stage regenerated
  help, user documents, custom icon assets and third-party notices into
  each portable ZIP; require them in package validation.
- `d594643e94002d6301a6720a83d4c56e888b5fd1`: make updater transfer budget overflow-safe and report
  actual disk-write length, with basic timeout/HTTP-error options,
  native test coverage and a source-invariant guard.

Updated the project source-review baseline from
`3e6a8914825c7527a0be1898a035a7004a598d60` to
`d594643e94002d6301a6720a83d4c56e888b5fd1` and registered five additional updater/contract GYP/test paths.
The final review-metadata/history-only commit does not alter those source
paths. Isolated Linux C++11 budget tests: 9 PASS; static source/build
wiring and negative contract mutations: PASS. Not executed: fresh
Windows x64 build, x86 updater build/test, help compiler,
portable ZIP production, installer/runtime UI or network/TLS
security verification. The existing HTTP endpoint and third-party
distribution/legal blockers remain OPEN. Hosted Actions: NOT RUN.

---

## 2026-09-24 — User-supplied Windows x64 compile failure: max macro in updater regression

**Input/revision:** `local-ci(20260924-074151).log`, started 2026-09-24
16:39:03 and finished 16:41:19 on `bc02a4a34df2ec5f6c20ccf76e80a24e5e6f67f5`.
`local_ci.bat x64` generated the VS2026 v145 x64 solution after source
invariant/regression preflight PASS. MSBuild Release-x64 FAIL followed.

**First real error:** `src/fxfile-tests/updater_contract_tests.cpp(196,9)`
C2589; later C2059 on the same macro-containing expression and C2143
at the following brace are parser cascades, not independent causes.
The log explicitly says the old `bin/x64/fxfile.exe` was NOT rebuilt;
its revision marker was `6621ae2d9c1d30204a8981306f178045f467bdf8`.
Do not use that stale artifact as a test of the current source.

**Cause:** The newly added transfer-budget boundary case contained
`std::numeric_limits<std::size_t>::max()` in a Windows translation
unit that includes `windows.h`. A function-like `max` macro can
expand that call before the C++ parser sees the namespace member.

**Fix / prevention:** Use
`(std::numeric_limits<std::size_t>::max)()` in the regression without
altering the actual transfer-budget behavior. Update
`validate_updater_download_budget()` to require the parenthesized
expression and reject the Windows-unsafe original. Preserve the full
nine-case native boundary suite.

**Evidence:** In an isolated `g++ -std=c++11 -Wall -Wextra -Werror -pedantic`
fixture with a Windows-style `max(a,b)` macro, the former spelling
fails compilation and the protected spelling compiles and runs.
The real Windows `local_ci.bat x64` profile on this new revision has
**NOT** been rerun; x86 updater, Windows runtime and packaging likewise
NOT TESTED. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Reviewed source snapshot after Windows max-macro fix

After the original user-supplied x64 log failed on `bc02a4a`, source
commit `752345b1bc76b7cf7601366e3548462c368d158e` replaced the macro-colliding updater regression call
and registered a source invariant against the original expression.
The review metadata now points to that exact code snapshot; no new
review paths were needed because both changed code and preflight were
already among the 66 reviewed paths. This subsequent metadata/history
commit changes only the project tracking and append-only evidence.
Independent C++11 Windows-style macro reproduction: expected unsafe
compile FAIL, protected spelling compile/run PASS.
The complete Windows `local_ci.bat x64` profile on the new revision
has NOT BEEN RE-RUN. Do not mark the defect/runtime closed or use the
prior unrebuilt executable as evidence. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Owner-directed retirement of auto updater and tracked build artifacts

**Observed problem / request:** Automatic updates were present in a
separate Win32 checker project, the app's startup/registry hooks, About
download/status dialog, advanced preference and saved default, bundled
libcurl, native regression, GYP graph and copied package payload. Earlier
x64 logs failed on the updater-only regression, now obsolete for the
owner's stated personal-use configuration. Five generated
`*.vcxproj.filters` files were nevertheless tracked despite the existing
`.gitignore`; two old vendored zlib VC project files were unused by GYP.

**Changes:** Remove all active updater implementation, supporting-only
libcurl, test and UI/translation/resource/GYP wiring. Keep the application's
ordinary version display and independent launcher/keyhook. Delete the
five generated filters and two old vendor projects from Git tracking;
keep the ignore rules. Preserve prior Windows user startup/profile state
and retain the uninstall-only legacy `upchecker/` directory cleanup
for earlier installations. Personal local use is the owner's intention;
existing GPL/GFL notices and unresolved public redistribution checks
remain unchanged.

**Prevention:** Read-only source-invariant check now rejects the retired
source/dependency and accidentally tracked generated project files.
Previously recorded updater fixes remain historical, not an outstanding
requirement to reintroduce the feature.

**Evidence:** Canonical source/GYP/resource references examined and
the proposed Git tree inspected. The owner reports their current
pre-removal build succeeds, but no revision-matched *post-retirement*
Windows compiler, runtime, installed cleanup or release-packaging result
has been provided. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Packaging silently ignored required copy errors and retained stale outputs

**Observed cause:** Former `dist/copy.bat` executed required xcopy
commands with the `/c` continue-after-errors flag and checked no copy
exit code. A partial three-architecture release stage could survive.
Previously generated installer/ZIP names could remain after a later
packaging failure. Portable-specific CHM/notices were also nested under
each architecture before the installer was generated, duplicating
installer input assets.

**Fix / prevention:** Check 39 remaining architecture-specific runtime
binaries and the Korean language source before staging. Stage into
`.package-stage`, verify every copy, promote only after full success.
Remove generated release file names before combined builds and on any
failure. Assemble installer before portable-only extras and leave the
standalone portable builder fail-closed. Validate main architecture,
normal notices and no retired updater in staged archives/installer smoke;
retain protected user-state snapshots.

**Evidence:** Static source and target-path contract review; actual
Windows CMD staging, multi-architecture compiler, hhc.exe, NSIS, ZIP,
installed payload and uninstall: NOT TESTED. Public redistribution
rights are not established by successful local packaging. GitHub
Actions: NOT RUN.

---

## 2026-09-24 — Reviewed implementation snapshot after updater retirement

Source implementation commit `3dfbf2daae22ba25820da888cea2ce09cc4bc4a1` retired the active Win32
updater and the updater-only libcurl, base helpers and native regression.
It also deleted the five tracked generated Visual Studio filter files
and the two obsolete vendored zlib project files and hardened release
staging. Scope: 48 tracked deletions and 43 active file modifications.
The root LICENSE/CREDITS notices, GFL image SDK, Win32 launcher/keyhook,
historical diagnostic entries and manual-only Actions controls remain.

Project review source baseline updated from
`752345b1bc76b7cf7601366e3548462c368d158e` to
`3dfbf2daae22ba25820da888cea2ce09cc4bc4a1` and reviewed paths expanded from 61 to 79, including new
product, source, UI and packaging inputs. This next metadata commit only
updates `PROJECT.md` and this historical evidence log; it does not
alter the reviewed source snapshot.

**Evidence:** Source-tree path checks and targeted source/build/package
contract inspection PASS. A revision-matched Windows Visual Studio build,
native functional run, real three-architecture staging, HTML Help compile,
portable ZIP generation, NSIS installer install/uninstall and actual UI
were NOT TESTED in this work unit. The owner reports their preceding
local build was working; the older user log's updater-only C++ error
no longer pertains to the retired test but is retained as history.
Old personal Windows HKCU updater startup entries are not modified by
a Git commit. Hosted GitHub Actions: NOT RUN.

---

## 2026-09-24 — Previous release staging lost if final rename failed

**Observed risk:** Following the updater-removal packaging changes,
`dist/copy.bat` validates the 39 required runtime files and creates
`dist/.package-stage`. Its former final step deleted the existing
`dist/bin` tree before attempting to move the newly prepared stage to
`bin`. A failed second operation (file lock, permissions, unexpected
directory collision) could lose the last known-good generated staging
tree while reporting a package failure.

**Root cause:** Input validation and copy failures were fail-closed,
but final staging activation lacked a retained backup and rollback.

**Change:** Fail if a prior `dist/.package-backup` remains (preserve
it for manual recovery), reserve the old `bin` with a same-directory
rename, activate `.package-stage` via rename, and attempt restoration
when that second rename fails and the old path remains available.
Remove the old backup only after successful activation. Ignore the
backup in Git and enforce the ordering and absence of eager `bin`
deletion through a negative source preflight. Original project/user
preferences, root GPL and third-party credits are unchanged.

**Verification:** Inspected the exact GitHub `main` batch source,
package orchestration and static guard contracts and exercised
negative mutation checks; no cmd.exe file-lock/permission injection,
full three-architecture package run or installer/runtime test was
performed. Full automatic updater code and obsolete generated VS
project files were already absent before this work unit. GitHub
Actions were NOT RUN.

---

## 2026-09-24 — Remove stale live updater migration recommendation

**Observed:** The current-status page still listed future `updater x86
isolation` despite the now-retired updater source and dependency
having been removed from the current repository. The dated dependency
audit deliberately preserves its earlier architecture observations
as historical evidence.

**Change:** Correct only the live near-term recommendation to cover
remaining runtime dependency ABI, optional launcher x64 feasibility,
and VLD release staging. Preserve dated dependency analysis and all
historical failure records. No product code or test scope changed.

**Verification:** Compared current `main` file inventory and the
live-status wording. Documentation consistency inspected; no
Windows build, generated CHM, ZIP or installer test performed.
GitHub Actions: NOT RUN.

---

## 2026-09-24 — Refreshed review snapshot for release-stage rollback

Source snapshot `3f7560a31f39080baaa5db275bf2186c1a4760a0` includes the follow-up safeguard for existing
`dist/bin` on package-stage activation failure, ignored backup storage,
negative source preflight and updated live status. Earlier retirement
snapshot `3dfbf2daae22ba25820da888cea2ce09cc4bc4a1` remains
historical review evidence. `PROJECT.md`'s machine-readable review
revision is now the new snapshot; the existing 79 paths cover every
new source/documentation edit. This metadata-only follow-up changes
only PROJECT.md and this append-only error-history document.

Evidence: Git tree/path inventory and staged recovery source contract
(including negative mutation scenarios) PASS. Real Windows cmd
rename/rollback under locks/permissions, x64 product build,
three-architecture package generation, HTML Help Workshop and
NSIS installer installation: NOT TESTED. No GitHub Actions ran.

---

## 2026-09-24 — Runtime audit: theme Apply exposes the wrong settings body (OPEN)

**Occurrence / first actual failure:** On a freshly built `bee95d9` x64
binary, open General, select Appearance/Theme, change System (Dark) to
Light and press Apply. Navigation and heading still identify Appearance,
but the body displays General controls. Selecting Filtering changes the
heading while General remains visible. Closing/reopening settings restores
the selected page. This is a settled-screen failure, not only a transient
theme paint frame. The same symptom observed before remote sync was
reproduced after the revision-matched rebuild.

**Diagnosis:** `RefreshThemeForCurrentThread` snapshots hidden descendants
as well as visible windows, then sends unconditional `WM_SETREDRAW(TRUE)`.
The documented DefWindowProc behavior can add `WS_VISIBLE` to hidden windows.
`CfgMainDlg::showCfg` hides only its tracked previous page. These source/API
facts form a plausible causal path; per-HWND style/stack evidence has not
been collected, so a sole root cause is not yet conclusively established.
See [Microsoft WM_SETREDRAW](https://learn.microsoft.com/en-us/windows/win32/gdi/wm-setredraw).

**Remedy / prevention:** Product fix NOT IMPLEMENTED in this audit.
Reopening settings is the observed workaround. Preserve original visibility
through theme refresh and check sibling owners before implementing a fix;
add a guard for hidden-page preservation and run the same Apply/next-page
case. Do not replace runtime acceptance with static implementation strings.

**Verification:** `local_ci.bat x64` on `bee95d9`: source preflight and
compile/link PASS; native functional regression 16 passed / 0 failed;
automated startup smoke SKIPPED for existing HKCU preservation. Actual
Windows 11 main launch/navigation/tab/pane interactions exercised, but this
settings acceptance case FAILS and remains OPEN. No Actions ran.

**Related commits / follow-up:** `6b18c58f` is the earlier modern OS routing
fix; this new runtime issue must not be labelled its same root cause.
Audit baseline `bee95d96a0150734ac247ed34e52ffe3bb1f4d92`;
the documentation commit containing this entry records the new finding.
Detailed steps, executable hash, other visual findings and untested scope:
`UI_UX_AUDIT_20260924.md` (UI_UX_AUDIT_20260924.md; historical, recover from Git).

**Additional post-fix evidence:** Original main-menu/toolbar/drive/bookmark
black text on Dark is now visibly readable on this Windows 11 binary.
That specific visual acceptance PASS does not close the remaining bright
scrollbars or the search dialog's white location edit/black legacy glyph.
Those observations and their owner candidates are OPEN in the audit.

---

## 2026-09-24 — UI-01 hidden settings page exposed by theme redraw transaction

**Observed:** The execution audit on the current Windows 11 x64 build showed
that after General was visited, applying a theme from Appearance/Theme could
leave the tree/title on the newly selected page while General content was
visible. Closing/reopening the configuration dialog restored the expected
page.

**First source-level cause:** `RefreshThemeForCurrentThread()` collected
hidden child HWNDs together with visible windows, sent `WM_SETREDRAW(FALSE)`
to all of them, and later sent `WM_SETREDRAW(TRUE)` to all. For the default
window procedure this message can change the `WS_VISIBLE` style. A hidden
configuration child therefore had a credible path to become visible during
the theme transaction.

**Fix:** Capture effective visibility for every HWND before the transaction.
Only HWNDs that were visible at snapshot time are frozen and thawed. Hidden
children still receive the palette/theme notifications so their future paint
state is current, but are not redraw-enabled. Preserve the prior snapshot
enumeration and descendant/frame/top-level ordering to avoid restoring the
earlier re-entrancy/flicker regressions.

**Prevention:** Source invariant now requires `ThemeRefreshWindowState`,
`mWasVisible`, the visibility capture, and a nearby visibility guard for
both `WM_SETREDRAW` calls; the former plain `std::vector<HWND> mWindows`
contract is forbidden.

**Verification:** Static source/invariant inspection: PASS. Windows compile,
the exact General → Appearance/Theme → Apply → Filtering runtime path,
visible-page count, focus and final pixels: NOT RETESTED. GitHub Actions:
NOT RUN.

---

## 2026-09-24 — UI-04 mojibake reorder button labels

**Observed:** The Windows UI audit showed the two filtering reorder buttons as
unreadable character-like labels. Source inspection found literal
`¡è`/`¡é` captions in that resource and the same pair on the sibling
program-association reorder page. Neither page replaced those captions from
the language table during initialization.

**Cause:** The resource depended on legacy encoded glyph bytes instead of
semantic localized text. Rendering therefore depended on resource encoding
and font interpretation, and the button name itself did not clearly express
its action.

**Fix:** Replace both resource pairs with readable `Up`/`Down` fallbacks,
widen the compact controls to 26 DLU, add Korean `위로`/`아래로` strings,
and set them explicitly in each page's `OnInitDialog`. No reorder behavior,
list data or command ID changed.

**Prevention:** Source invariant rejects either mojibake literal and requires
the four localization keys in both the language table and owning dialogs.

**Verification:** Static source/wiring inspection: PASS. Windows compile,
actual filtering/program-association dialog layout, DPI clipping, keyboard
focus and accessibility/visual result: NOT RETESTED. GitHub Actions: NOT RUN.

---

## 2026-09-24 — Reviewed snapshot after UI-01 and UI-04 source fixes

The project source-review baseline advances from `3f7560a31f39080baaa5db275bf2186c1a4760a0` to
`dce54c6678111d0252191ffc7e272339b94a95b7`. The reviewed-path set now includes
`src/fxfile/main_frame.cpp`,
`src/fxfile/cfg/cfg_appearance_filtering_dlg.cpp`,
`src/fxfile/cfg/cfg_func_program_ass_dlg.cpp` and
`docs/development/UI_UX_AUDIT_20260924.md` in addition to the existing
resource/language/invariant/status paths.

Source commits covered:
- `341f99c19f5730f41d1fb3726ce502457e93217b`: preserve hidden settings
  page visibility during the app-wide theme redraw transaction.
- `dce54c6678111d0252191ffc7e272339b94a95b7`: replace mojibake reorder labels in filtering and the sibling
  program-association page with localized semantic text.

Static tree/source-contract review: PASS. Windows compile after these two
changes, matching UI-01 runtime path, UI-04 dialog layout/accessibility,
DPI/High Contrast and final pixels: NOT RETESTED. GitHub Actions: NOT RUN.


---

## 2026-09-24 — UI-03 and UI-07 incremental source work

**Observed:** The Windows audit found a bright inner search ComboBox field,
a dark-on-dark current-location glyph, and hidden tab/+ affordances in a
default new profile.

**Cause identified in source:** SearchDlg uses ComboBoxEx with an internal
combo whose edit/list color messages do not reliably reach the dialog's
existing theme palette brush. The two tab display settings both defaulted
to false for new installations.

**Source change:** Subclass only the search location's nested combo,
forward its Dark edit/list color messages to the existing dialog brush,
and theme its native popup list on open. Replace the tiny legacy glyph
with a wider localized current-folder action and tooltip. New-profile
defaults show a single tab strip and the existing new-tab button;
previously saved preferences remain unchanged. Add a regression guard.

**Evidence:** Source-edit assertion and connector Git tree inspection only.
Full Python validator, current-revision Windows compile/link, functional
test, actual search/dialog and DPI/HC visual acceptance: NOT TESTED.
UI-03/UI-07 remain partially open; other audit items remain open.
GitHub Actions: NOT RUN; no per-run approval was given.


---

## 2026-09-24 — UI-07 visible tab-close glyph source follow-up

**Observed:** The existing custom tab strip did not show an obvious
close control, although Ctrl+F4, configurable double click and context
menus already supported tab closing.

**Source change:** Reuse the existing previously unused per-tab close
rectangle. Reserve space for a DPI-scaled 'X' within sufficiently wide
tabs; paint it for selected/hovered tabs using ThemePalette. Use a
separate press/release state so a close click cannot initiate tab drag
or activate an unrelated tab. Release over the same close target
dispatches through the existing `ID_WINDOW_TAB_CLOSE` command, including
existing close confirmation. The localized existing close command
supplies the tooltip. Narrow tab fallback and stored preferences are
unchanged.

**Prevention:** Added static wiring checks for paint/hit/observer/command
integration, not a claim of actual runtime acceptance.

**Evidence:** Connector-side source construction assertions and Git
tree/compare only. Python validator execution, Visual Studio x64
compile/link, real close interaction, tooltip and DPI/Light/Dark/High
Contrast screenshots: NOT TESTED. UI-07 remains OPEN. GitHub Actions:
NOT RUN because the individual run was not authorized.


---

## 2026-09-24 — UI-08 new-profile shared folder-tree initial layout

**Observed:** The Windows UI audit found repeated folder trees across
vertical split panes and reduced space for file columns. The product
already has a shared-tree mode and per-view tree controls, but its new
profile setting defaulted to individual trees.

**Source change:** Change only the new-profile default for
`main.folder_tree.mode` to select the existing shared tree. Existing
stored layout preferences still override the default, and switching
back to individual trees remains supported. No file manager features,
information panels or tree controls were removed. Add a source guard
for the shared/per-view routing contract.

**Verification boundary:** Source construction assertions only. The
Python preflight and VS2026 x64 build have not run for the new revision.
Windows clean-profile, pre-existing profile, vertical split/resize,
settings persistence, multi-monitor/DPI and UI visual interaction
remain NOT TESTED. UI-08 is partial and stays OPEN; no GitHub Actions
run was authorized.


---

## 2026-09-24 — UI-08 split column override and narrow Contents layout

**Observed in source:** MainFrame::OnCreateClient read both launch
split dimensions but incorrectly stored the column override into
`sRowCount`. ExplorerPane::recalcLayout unconditionally reserved the
same 200-unit explorer-style Contents width in narrow and wide panes,
which compounded the observed split-pane file column truncation.

**Changes:** Assign a valid command-line column override to
`sColumnCount` without modifying the row override. Reserve DPI-scaled
Contents space dynamically based on current pane width, leaving room
for list columns where possible and proportionally sharing very small
panes. No information panel, tree mode, file data or user preference
was removed; the previous new-profile shared tree remains the default.

**Regression prevention:** A source validator checks the column
assignment, adaptive margin owner and absence of the fixed subtraction.

**Evidence:** Source inspection and static change construction only.
Complete Python preflight, Release-x64-Unicode compilation, native
regression suite, command-line split, small-pane geometry, High
Contrast/DPI and Windows visual acceptance: NOT TESTED.
UI-08 remains partial. Hosted Actions: NOT RUN under per-run restriction.


---

## 2026-09-24 — UI-06 tall app-menu / Dark popup source work

**Observed:** The documented Windows UI audit recorded app-owned
Window/Tab menus taller than the main client, with a bright Dark
popup outline. The earlier BCMenu::TrackPopupMenu did not bound
menu height or explicitly set the native menu-client background.

**Source change:** Add scoped documented MENUINFO configuration for
each existing app-owned popup and submenu, limiting maximum height
to its monitor work area so the OS supplies overflow scrolling.
Dark/non-High-Contrast client background uses a temporary
ThemePalette elevated-color brush. Prior per-menu background/height
values are restored before the brush is destroyed; High Contrast
and shell-owned menus retain system behavior. The native outer popup
border is not changed and cannot be declared repaired on this evidence.

**Prevention:** A source guard checks monitor work area, the MIM flags,
submenu traversal, state restoration, brush lifetime and HC bypass.

**Evidence:** Reviewed supported Windows MENUINFO behavior and
repository source wiring. Full Python validator, x64 compiler,
actual work-area overflow/scroll, keyboard access, Light/Dark/HC
and outer-border screenshots: NOT TESTED. UI-06 partial and OPEN.
GitHub Actions: NOT RUN under the individual approval rule.


---

## 2026-09-24 — UI-05 fresh rebar packing and settings whitespace

**Observed:** Initial Windows 11 UI audit found dense main-command
glyphs alongside separate drive/bookmark bands with large unused
horizontal space, and comparatively tight configuration-page
description/navigation spacing.

**Source cause:** In MainCoolBar::createBands each of the three bands
explicitly set RBBS_BREAK; bookmark always started a third row even
when the previous Drive band had room. Settings navigation used
34 DPI-scaled rows and 12-unit section spacing.

**Change:** A fresh profile lets the bookmark band share the Drive row
when Windows rebar layout has enough width, retaining wrapping/
chevrons and all commands. Persisted rebar band breaks and user
multiline controls still override defaults. The shared ModernUI
navigation row and settings-section spacing become 38 and 16
DPI-scaled units; fixed-layout legacy child controls were left intact.

**Prevention:** A source regression guard checks the band BREAK
contract, the existing load/wrapping routes and shared spacing.

**Evidence:** Source-only construction checks. Actual Windows x64
compile, new and saved layout, 100/125/150/200% DPI, compact-window
overflow, keyboard accessibility and final visual presentation:
NOT TESTED. UI-05 remains partial; any remaining per-dialog spacing
work requires measured runtime geometry. GitHub Actions: NOT RUN.


---

## 2026-09-24 — UI-06 custom chevron popup monitor and DC fixes

**Observed in source:** The custom toolbar overflow popup previously
clamped its location against desktop bounds, including taskbar space
and potentially another monitor. Its horizontal popup exclusion
fallback compared a left coordinate to a top coordinate. The
nonclient painter constructed a scoped CWindowDC and also explicitly
called ReleaseDC on the same wrapper.

**Source change:** Derive the popup bounding rectangle from the
anchor monitor's documented work area with a desktop fallback,
correct the horizontal left-boundary comparison, and leave the
scoped CWindowDC to release its DC exactly once. No commands,
keyboard mapping or theme associations changed.

**Prevention:** Source validator checks anchor monitor placement,
forbids the wrong-coordinate condition and the manual double
release in the specific OnNcPaint owner.

**Evidence boundary:** Source inspection and construction assertions
only; full Python preflight, current VS2026 Release-x64-Unicode build,
real chevron popup/multi-monitor/taskbar placement, native keyboard,
High Contrast, DPI and screenshot tests: NOT TESTED. Custom popup
height beyond work-area remains an open design/test case; OS menu
nonclient border is still not considered repaired. GitHub Actions:
NOT RUN, as no execution-specific authorization was provided.


---

## 2026-09-24 — UI-03 ComboBoxEx location icon/text spacing

**Observed:** The interactive Windows audit reported the search
location icon pressed too close to the editable path text as well
as the distinct bright Dark field and unreadable legacy button.

**Source ownership:** SearchDlg uses a native ComboBoxEx image list
plus an inner editable HWND; changing its containing dialog spacing
cannot directly control text padding inside the native edit.

**Source change:** Use documented EM_SETMARGINS with EC_LEFTMARGIN
on the actual inner edit to introduce a small DPI-scaled icon/text
gap. Recalculate this gap after forwarding WM_DPICHANGED to the
existing CResizingDialog handler. Do not change the native icon
list, horizontal editing behavior, autocomplete or the right margin.

**Prevention:** Source validator now checks the init/DPI/declaration
chain and retains the native icon list contract.

**Evidence:** Source-construction assertions only. Full Python
source preflight, Windows x64 build, runtime typing/search,
Light/Dark/HC, keyboard/IME and DPI-final pixels: NOT TESTED.
UI-03 stays OPEN pending direct acceptance. GitHub Actions:
NOT RUN without run-specific authorization.


---

## 2026-09-24 — UI-01 settings single-page visibility reinforcement

**Original observed runtime symptom:** General -> Appearance ->
Light Apply -> Filtering could update navigation text while the
earlier General page body remained visible until settings was closed
and reopened. An earlier source checkpoint prevented theme redraw
from thawing previously hidden HWNDs; matching Windows runtime
evidence on the new revision was still missing.

**Further source risk:** showCfg hid only the previous mShowCfg
page. A stale visible third page would remain after navigation.
Option notification synchronously refreshes UI-thread windows,
including the currently open settings dialog.

**Source change:** Reconcile visibility across all created settings
pages during navigation using each page HWND's own WS_VISIBLE bit,
then reassert the invariant after config/theme notification. Show
the selected page only if unexpectedly hidden. No settings page,
stored preference or navigation command was removed.

**Prevention:** Add a negative source guard checking the new helper
and rejecting the old selection-only hiding path.

**Evidence:** Source structure only. Complete Python preflight,
VS2026 x64 compile, original user click sequence, Light/Dark/HC,
keyboard focus and DPI final screenshots: NOT TESTED. UI-01 is
NOT CLOSED. GitHub Actions: NOT RUN absent individual approval.


---

## 2026-09-24 — UI-09 bookmark strip icon/text baseline ghosts

**User evidence:** The user attached a close crop of the Windows
bookmark strip. Repeated short icon-colored underlines are visible
under Desktop/Libraries/Documents/Music/Pictures/Videos/Network,
with isolated dark fragments beneath their Korean captions.
The strip uses a Light-looking background. This is current user
visual evidence of a defect, not a successful acceptance screenshot.

**Source diagnosis candidate:** In ToolBarEx's custom-draw final
CDDS_ITEMPOSTPAINT, Dark previously called DrawOwnedDarkToolbarItem,
which fills the full item and redraws its ImageList icon, state,
caption and dropdown. Light took DrawFinalDarkToolbarItem only,
clearing/replacing the much smaller text/dropdown rectangles while
native rendering retained control of the remaining icon and/or
caption tail. Differing native/ModernUI text/icon positions could
produce the screenshot's two fragmented baselines. Pixel-trace
confirmation of this precise root cause has NOT been obtained.

**Source change:** Use the existing full-item owner for both
non-High-Contrast Light and Dark, renamed DrawOwnedToolbarItem to
reflect its responsibility. Native ToolbarWindow32 still manages
bookmark commands, hit-testing, focus/keyboard behavior, tooltips
and image-list data; the app owns only the final visual pixels.
High Contrast and legacy system branches retain native painting.
No icon/command mapping or stored profile data changed.

**Recurrence prevention:** Extend the scoped existing toolbar
source guard to require exactly one complete-item postpaint path
and explicitly reject the old conditional Light text-only pass;
keep the whole-item fill, ImageList redraw and text/glyph checks.

**Evidence state:** Connector-reviewed source construction only.
Full local Python source preflight, VS2026 Release-x64-Unicode build,
native functional suite, actual exact-user-strip rendering in
Light/Dark/HC with hover/press and 100/125/150/200 DPI:
NOT TESTED. The visual issue is OPEN pending reproduction
comparison; prior build evidence does not apply to this revision.
GitHub Actions: NOT RUN; per-run explicit approval remains required.


---

## 2026-09-24 — UI-09 repeated after Light full-item postpaint

**User evidence:** The user reports the exact bookmark icon/label
understrokes are still present after the previous full-item postpaint
change. This is a regression FAIL for the earlier hypothesis, not
evidence for a stale executable; the revised branch is not
considered fixed by source-string tests.

**Additional source path:** Existing CToolBarEx::WindowProc had no
WM_PAINT or WM_PRINT/WM_PRINTCLIENT owner; its custom-draw route
relied on postpaint reflected notifications. A rebar composes
child toolbars via WM_PRINT, which can use another native pixel
route. The duplicate glyph/label strokes at matching X positions
are consistent with more than one image/text paint pass, though
a Windows trace is still needed to establish exact root cause.

**New source change:** For the bookmark band only, when not in
High Contrast/legacy OS, intercept WM_PAINT and WM_PRINT* at the
CToolBarEx owner before native ToolbarWindow32 paints. Fill the
client clip and draw actual TB_GETITEMRECT/TB_GETBUTTON/
TB_GETBUTTONINFO icons, texts, states, separators and visible
keyboard focus using the existing ModernUI item painter. Before
ownership, check that all native toolbar images can be rendered;
otherwise preserve the existing native fallback. High Contrast,
other toolbar bands and their commands/tooltips/drag semantics
are untouched.

**Prevention:** New source guard requires native paint and print
interception in addition to the earlier Light/Dark unified
postpaint check.

**Evidence:** Source construction inspection only, NOT the actual
revision-matched Windows compile, native tests, same-strip
before/after Light/Dark/HC/DPI/focus/drag and rebar print pixel
acceptance. UI-09 remains OPEN until direct evidence.
GitHub Actions: NOT RUN without explicit approval for this run.


---

## 2026-09-24 — UI-09 native bookmark button accumulation found

**User evidence/context:** The previous Light full-item postpaint
did not remove the duplicated icon/label fragments. After adding
a separate WM_PAINT/WM_PRINT owner, further examination uncovered
a native *button lifecycle* bug that pure painting changes cannot
resolve when multiple rows contain duplicate real buttons.

**Source defect:** BookmarkToolBar::setBookmark used TB_INSERTBUTTON
at manager indices on every call without deleting prior native
items. If the method runs again while the toolbar is populated,
the native button count exceeds BookmarkMgr::getCount and a
wrapped/clipped extra row could carry the same shortcut icons and
labels. createBookmarkBar also registered async icon updates on
every invocation, and updateBookmarkButton(void) recreated its
image list before calling setBookmark, which recreated it again.
The call pattern on the actual user's machine is not observed;
this is a verified source-level accumulation vulnerability,
not proof that this specific screenshot was caused by it.

**Source change:** Make setBookmark an idempotent full rebuild:
disable redraw, remove all existing native buttons, recreate the
native icon list once, insert exactly one button per manager
bookmark and assert the final button count in debug builds.
Make updateBookmarkButton(void) delegate to that sole owner;
register the asynchronous observer only once per visible
lifetime. Keep per-index insert and shell path processing intact.

**Prevention:** Add a source guard checking delete-before-insert,
the single list owner, registration and final-count assertion.
This complements the separate WM_PRINT/WM_PAINT safeguard
without claiming a native runtime pass.

**Evidence:** Source inspection/construction only. Full source
invariant script, Visual Studio Release x64 build, toolbar button
count at observed failure, drag/click/visibility/wrap/DPI/HC and
final matching Windows screenshot: NOT TESTED. The user's visual
issue remains OPEN pending direct evidence. GitHub Actions:
NOT RUN without run-specific approval.


---

## 2026-09-24 — Reproduced Light filtering text and bookmark band fragments

**New user evidence:** The newly supplied Light/Dark Filtering-page
screenshots show near-white per-filter names/extensions on a pale
Light list; the Dark list is legible but still has a bright native
scrollbar in settings navigation. The bookmark strip crop shows
short icon-colored and text fragments below nearly every first-row
shortcut even after previously proposed toolbar painter/button
lifecycle changes. Do not treat those changes as proven visual fixes.

**Source finding, filtering:** CfgAppearanceFilteringDlg's list
item custom draw used each persisted FilterItem::mColor as a text
color, except only RGB(0,0,0) was replaced in Dark. White and
other pale configured colors could have insufficient contrast on
Light. Initialization applied ListView colors only once;
theme-refresh ownership lived in the parent dialog.

**Fix candidate, filtering:** Compare each per-filter color with
the current ThemePalette elevated list background using relative
luminance and WCAG 4.5:1 contrast. Only on-screen foreground uses
palette text when contrast fails; stored filter RGB remains
untouched. High Contrast always uses system palette foreground.
Synchronize ListView text/background and repaint header on
settings/theme/system-color messages; leave inherited dialog
theme re-entrancy protection intact.

**Source finding, bookmark:** Earlier UI-05 compaction defaulted
Bookmark to a shared Drive band row. Persisted REBARBANDINFO
fStyle is restored from disk and supersedes fresh defaults.
The combination is a plausible contributor to narrow toolbar
rows and clipped wrap/partial second-row fragments. No Windows
native geometry trace has proven this the sole cause.

**Fix candidate, bookmark:** Restore independent bookmark
RBBS_BREAK default, and enforce that break in the existing
setWrapable layout owner after saved state restoration.
This intentionally corrects old saved same-row Bookmark
layout on startup; current session still supports rebar
interaction. Keep bookmarks, button commands, wrap/chevron
setting, shared owner-draw and full rebuild intact. Extend
existing source guard's default bookmark-break expectation
and persisted layout check.

**Verification limits:** GitHub source/structure checks only.
Full Python invariant execution, Windows native build, exact
current Light/Dark/HC screenshot reproduction, bookmark
layout/wrap and saved-state interaction, multiple DPI and
keyboard/accessibility: NOT TESTED. Both are still runtime
OPEN. UI-02 bright native scrollbar is outside this fix.
GitHub Actions: NOT RUN pending individually requested approval.


---

## 2026-09-24 — Supplied local x64 log: obsolete filter validator blocks new UI fix

**Evidence:** User uploaded `local-ci(20260924-130832).log`,
revision `eebc68db3c5852bced3b0d04abc13dfba2a5e456`.
`build/validate_source_invariants.py` failed with four missing
legacy filtering statements: two list background assignments
using the removed local `sListBackground`, plus the explicit
black-only Dark condition and direct text-color substitution.
The run stopped before generating the VS2026 solution, so no
new compiler error was observed. It warns that `bin/x64/fxfile.exe`
was not rebuilt and its existing revision marker is `468ee555`.

**Why:** A prior Win11 stability regression guard asserted
obsolete implementation snippets instead of the current safety
contract. The actual UI-10 source moved native ListView color
updates into `refreshFilteringListColors` and replaced the
black-only special case with theme-independent contrast checking
inside `OnCustomDrawList`. Reintroducing the old snippets would
undo the visual fix and contradict the newer UI-10 validator.

**Correction:** Replace the old filtering token checks with
function-scoped assertions of the real theme-refresh owner,
subclassed header, retained High Contrast/default text, user
filter RGB input, contrast resolver, and selected/inactive row
colors. Add a negative assertion prohibiting the original
black-only Dark exception. Keep the dedicated newer UI-10
contrast regression guard intact.

**Limits:** Source construction/guard review is not a successful
local Windows test. Re-run `local_ci.bat x64` at the new SHA,
inspect its revision marker, and only then compare current
Light/Dark filtering and bookmark screenshots. CI, build and
UI-09/UI-10 runtime acceptance remain OPEN; GitHub Actions
not run because no separate per-run permission exists.


---

## 2026-09-24 — Follow-up local x64 compiler C2065 after preflight repair

**New evidence:** User uploaded `local-ci(20260924-132251).log`
from `1a555babc7f6c50dade669ee5ec3a55cdaa74532`.
Source-invariant/regression preflight reported PASS and the
VS 2026/v145 x64 solution was generated, then the native
Release x64 MSBuild FAILED at lines 117 and 118 of
`cfg_appearance_filtering_dlg.cpp` with undeclared `sPalette`.
This is a genuine compiler failure, distinct from the previous
stale source-guard failure.

**Source cause:** The earlier UI-10 change removed the local
palette initialization from OnInitDialog together with outdated
list background assignments, but left a Dark/non-High-Contrast
border-style conditional that still referenced `sPalette`.
The separate `refreshFilteringListColors` function's local
palette cannot satisfy OnInitDialog's C++ scope.

**Minimal correction:** Restore a local
`const ui::ThemePalette sPalette = ui::ModernUI::getPalette();`
immediately before the existing OnInitDialog border branch.
Retain shared native list color refresh, header, and Light/Dark
contrast-aware rendering as implemented; no settings migration.

**Regression guard:** The dedicated UI-10 validator now checks
the OnInitDialog function boundary and ensures the local palette
declaration precedes its Dark-border use, forbidding an equivalent
C2065 regression even if a palette declaration exists elsewhere.

**Evidence status:** User's previous Windows preflight PASS and
compiler C2065 FAIL are directly observed. Source correction and
guard checks are static only; NO new local x64 compile, native
tests, Light/Dark/HC screenshots or Actions run. Request a
new `local_ci.bat x64` log at the next revision before closure.


---

## 2026-09-24 — Owner confirms successful current rebuild, Light filtering persists

**Runtime evidence:** The owner specifically states the latest
source was built successfully and the same Light filtering
text and bookmark icon/text ghost screenshot persist. Reject
the prior suggestion that an old artifact alone explains
the report; do not demand another git pull/revision check
without separate reason.

**Source defect found:** The earlier 4.5:1 contrast-aware
filter-color path in `OnCustomDrawList` only executes for
nonselected rows. When `CDIS_SELECTED`, the implementation
always set `mSelectionText` (often white) even when the
filter list itself was unfocused; in that state the same
branch used pale `mInactiveSelection` as its background.
This yields white on pale blue in explicit Light mode even
with the resolver in place.

**Targeted change:** Pair focused selection with
mSelectionText/mSelection; unfocused selection with
mText/mInactiveSelection. No persisted per-filter RGB
changes or broader palette hacks. Extend the UI-10
negative regression check for this second paint path.

**Verification:** Source logic and conditional pairing
inspected. The user's persistent current-binary failure
is accepted as real. A Windows build with this new source
and actual Light/Dark/HC visual acceptance has NOT been
run by the agent. UI-10 remains RUNTIME OPEN; UI-09
bookmark ghosting remains OPEN until paint/geometry
trace or equivalent strong evidence. GitHub Actions
not run without explicit per-run approval.


---

## 2026-09-25 — User confirms latest build still has bookmark partial second row

**User runtime evidence:** The user rejects the stale-executable
explanation: they built and ran the latest version and the visible
colored icon/text fragments remain. Earlier source claims did not
establish actual Windows screenshot acceptance. Do not repeat old
build-version questions or mark UI-09 fixed without matching visual
evidence.

**New source review:** In nonwrapping Bookmark mode,
MainCoolBar::setWrapable removed window-level TBSTYLE_WRAPABLE but
left TBSTATE_WRAP on native toolbar buttons, permitting stale row
layout after earlier window resizing or mode switches.
MainCoolBar::onUpdatedToolbarSize constructed REBARBANDINFO
without initializing cyMaxChild/cyIntegral while passing
RBBIM_CHILDSIZE. The bookmark-specific WM_PAINT/WM_PRINT
owner painted across the entire client with no explicit
nonwrapping first-row clip, making partial lower-row glyphs
possible while the rebar child size is updated. The screenshot
alone cannot prove which of these pathways is active.

**Source corrections:** Clear retained native TBSTATE_WRAP only
when disabling bookmark multiline mode, zero-initialize all
REBARBANDINFO members and bound cyMaxChild, and clip owned
bookmark icon/text painting to the first native row while
still filling the full toolbar client background. Keep toolbar
commands, accessibility, saved bookmark data, chevrons and
intentional multiline setting. Add a regression source guard
that inspects each owner and mutation order, rather than
requiring arbitrary implementation snippets alone.

**Evidence limits:** This is a source-level repair candidate,
not a successful Windows test. No revision-matched Release
x64 compiler, native runtime toolbar geometry trace,
final identical screenshot or High Contrast/DPI acceptance
was available via the connector. UI-09 remains OPEN until
user-verified pixel result. Do not run GitHub Actions
without individual explicit authorization.
---

## 2026-09-25 — UI-09 subsequent source candidate committed at owner's request

**Problem/evidence:** The user provided a Windows screenshot with
`build-revision.txt=5a8fc7eedd45ac2da924a9ead13d914fbb8e5c78`; bookmark
icon/text fragments remain after the prior no-wrap state, rebar size and
first-row clipping changes. Prior source-only fixes cannot close UI-09.

**Source observations, not established runtime root cause:**
`CanPaintOwnedBookmarkToolbar` inspected asynchronously populated
image-list metadata before choosing the entire toolbar paint owner.
Unavailable image metadata could fall back to native whole-bar drawing
for one frame. Separately, `PaintOwnedBookmarkToolbar` clipped the
nonwrapping view to the first row's bottom but did not reject a second-row
button whose rectangle might partly overlap that clip.

**Narrow source candidate:** The bookmark-only paint eligibility check now
depends on valid HWND/command-bar ID rather than transient icon readiness;
the existing per-item renderer continues to handle missing icons.
Nonwrapping bookmark drawing records the first native item's row origin
and skips all off-row items before drawing, while preserving the
full-client background repaint and first-row clip. Existing multiline,
high-contrast native fallback, command routing and saved bookmarks are
not intentionally changed. This change does not establish that either
candidate explains the screenshot.

**Regression:** Updated `validate_bookmark_first_row_geometry` requires
the off-row rejection, and `validate_bookmark_toolbar_direct_paint_and_print_owner`
rejects metadata-dependent whole-toolbar eligibility. Earlier guards
remain in place.

**Evidence and limits:** Changes were reviewed against the exact inspected
source revision and targeted source/synthetic assertions were exercised
outside a Windows build. The complete repository preflight, Release
x64 compile/link, functional regression, actual toolbar HWND geometry/
WM_PAINT/WM_PRINT traces, identical screenshot and Light/Dark/High Contrast/
DPI acceptance were NOT TESTED in this environment. Icon-loading interim
appearance and ordinary multiline/chevron behavior still require runtime
checking. UI-09 stays OPEN. GitHub Actions were not invoked.
---

## 2026-09-25 — UI-09 user geometry evidence; optional internal trace

**New observed evidence:** The owner supplied `fxfile-ui09-geometry.txt`
collected on Windows: bookmark `ToolbarWindow32` ID 54 has eight visible
buttons, `TB_GETROWS=1`, no button `TBSTATE_WRAP`, and all eight
`TB_GETITEMRECT` rectangles are on the same y=0..22 row. Its client
rect is 1315x40 and Rebar allocates a 40px band. Drive items also
measure 22px inside a 40px child, while main-toolbar items are 28px
inside a 40px child. The 18px bookmark gap is a measurement, not yet a
proven cause of the icon/text fragments; previous native second-row
assumptions are contradicted by the captured state.

**Change:** On the owner's request, commit opt-in runtime
instrumentation before further speculative fixes. The bookmark-only
`ToolBarEx.cpp` helper writes numeric metrics, button rectangles,
style/wrap flags and paint/print route/clip state before/after
`ApplyModernMetrics`, `AutoSize` and the Rebar observer and on the
initial owned painting paths. It runs only when the process starts
with `FXFILE_UI09_TRACE=1` and writes to
`%TEMP%\\fxfile-ui09-<PID>.log`; no bookmark labels or destinations.
The instrumentation has a 700-line cap, does not change button geometry
or actual painting, and is not enabled for normal users.
A static source guard verifies the opt-in and stage placement.

**Evidence limits:** Static source property checks were performed
before the direct main checkpoint. This environment did NOT run the
complete repository preflight, Windows Release-x64-Unicode build,
native UI trace, real paint-order analysis, same-screen visual
acceptance or optional DPI/High Contrast checks. UI-09 stays OPEN.
No GitHub Actions dispatched.
---

## 2026-09-26 — Light/Dark screen review: initial UI-11/12/13 code corrections

**Observed report:** A matched-looking pair of user-provided Light/Dark
screenshots shows many truncated modification dates with unused list space,
clipped long tree labels and a densely wrapped optional folder information
sidebar. The images do not display build revision, actual DPI or the user
interaction sequence and alone cannot establish a header/focus defect.

**Source evidence:** `ExplorerCtrl::mDefColumnDefault` initializes the
modified-time width to 140px. Folder layouts store individual widths,
so widening an already saved column without permission would destroy
the user's preference. FolderCtrl did not implement native full-name
infotips. ContentsWnd rendered header, separator and bookmark-heading
pixels against fixed 200/198px coordinates despite its parent having
an adaptive narrow/split pane layout.

**Targeted changes:** First-use default modification dates now start at
225 DPI-scaled logical pixels and enabling that default date column uses
the same scaling. Existing per-folder and user-saved widths remain intact.
Enable `TVS_INFOTIP` and return the item's full displayed label while
retaining the native horizontal tree scroll. Draw folder title, separator
and bookmark heading using the actual information-pane client width;
increase preferred width to 224, conditional minimum to 120, and the
bookmarks' shared vertical/scrolling gap to 5px. Retain the original
narrow-pane one-third cap, list minimum-width budget and user settings.

**Regression:** `validate_light_dark_main_view_sizing` guards first-use
width, native tooltip wiring and client-relative panel geometry, and
checks link scrolling uses the same row separation.

**Limits:** Source inspection and targeted source safety checks, NOT a
confirmed runtime repair. Repository-wide preflight, native
Release-x64-Unicode compile/link, real Dark scrollbar painter, test of
previously saved 140px widths, actual tree tooltip, DPI, keyboard,
High Contrast and user screenshot acceptance: NOT TESTED. UI-02 remains
OPEN (native non-client scrollbar owner), UI-05 PARTIAL (saved Rebar
layout/chevron/multiline constraints), UI-14 unconfirmed, UI-09 OPEN.
No GitHub Actions were executed.
---

## 2026-09-26: UI-02/05/14 code candidates and UI-09 open verification

User evidence: Dark screenshot had white list/tree native scrollbars; toolbar command row dense against sparse drive/bookmark rows; header and focus concern was only provisional. Previous UI-09 user reproduction and native 8-item, 1-row geometry remain valid separate evidence.

Source candidates: UI-02 draws actual GetScrollBarInfo non-client rectangles/state after OS list/tree processing in Dark, bypasses High Contrast and preserves real Windows scrollbar scrolling/input/accessibility without private theming. UI-05 preserves user-saved Rebar grouping; new unsaved single-line drive/bookmark bands combine only after native AutoSize and a measured client fit with 48-DIP slack. UI-14 completes mixed native/owner-draw cells in the shared header paint path and bounds narrow sort arrows. UI-09 owns no new speculative renderer changes; the previous opt-in internal trace remains.

Regression: validate_remaining_main_window_source_candidates checks source ownership constraints, documented geometry, conditional grouping, no-wrap protection and final mixed-header palette. This check is NOT native Windows acceptance.

Not tested: full repository preflight, MSVC Release x64 compile/link, real scroll/drag/keyboard, saved/new CoolBar, actual header focus interaction, High Contrast, mixed DPI and UI-09 same-screen trace and screenshot. UI-02/05/14 = CODE UPDATED, NOT VISUALLY VERIFIED; UI-09 = OPEN. No Actions dispatched.

---

## 2026-09-26 — UI-09: MFC command update omits vacated toolbar pixels

- **발생 / 최초 실제 실패:** `dca62af` 기반 실제 Windows 실행에서 8개 북마크,
  1행, WRAP 없음에도 테마 적용 뒤 아이콘/텍스트 하단 잔상이 재현됐다.
  paint trace의 item 높이/DC clip은 `36/(0,0,1313,40)` 다음에
  `22/(0,0,572,22)`였으므로 이전 하단 픽셀이 다음 update region 밖에 있었다.
- **원인 진단:** MFC `CToolCmdUI::SetCheck(FALSE)`는 checkbox style을 추가하고
  `_SetButton`의 delete/reinsert를 거친다. native control이 높이를 재계산하지만
  MFC는 새 `TB_GETITEMRECT`만 invalidate한다. 계측한 `OnUpdateCmdUI` 직전
  36px, 직후 22px가 직접 증거다. 같은 실패의 native custom-draw 중복 호출은
  관찰되지 않았다. 이전 wrap/Rebar/first-row 수정으로는 이 damage 누락을 고칠 수 없다.
- **해결 방법:** bookmark에 한해 inherited command update 전후 native geometry를
  비교하고, 변경된 항목의 old/new footprint를 invalidate한다. 실제 drawing과
  command semantics, multiline/overflow/tooltip/drag/drop은 그대로 보존한다.
  별도 renderer, 전체 repaint, 강제 높이를 추가하지 않는다. 임시 trace는 제거한다.
- **재발 방지:** 공유 `ToolbarLayoutDamage.h`를 native functional suite에서
  축소/확장/이동/행 위치 변경/추가/삭제/동일 좌표로 검사한다. 변경 없는 먼 항목이
  damage를 넓히지 않는 것도 검사한다. 96/120/144/192 좌표 검사는 실제 DPI visual
  검증과 구분한다. preflight는 실제 command seam/test 연결과 direct include를
  보호하고 이 경계의 임의 repaint/resize 및 임시 trace 재도입을 금지한다.
- **검증 상태:** 진단 빌드의 x64 compile/link PASS, native regression 17/0,
  동일 Light→Dark 화면의 잔상 소멸 직접 확인. 최종 검증은
  UI-09 실행 보고서 (UI09_ROOT_CAUSE_20260926.md; historical, recover from Git)에 갱신한다.
  자동 smoke는 사용자 HKCU 보호로 SKIPPED이며 Actions는 실행하지 않았다.
- **관련 commit:** 이 항목과 제품 수정의 동일 checkpoint (`git log --grep="bookmark geometry damage"`).

## 2026-09-26 — UI-09와 최신 main의 통합 검증 경계

백업의 36→22px 영역 손상 수정과 별도 native
회귀 검사 및 기존 main의 UI-02·05·11·12·13·14
개선 코드를 함께 보존한다. 특히 UI-05의 조건부
새 프로필 드라이브·북마크 행 결합은 백업의
독립행 진단 환경과 다르므로 같은 Windows
실행에서 테마 변경/저장 배치/멀티라인/잔상
경로를 회귀 확인해야 한다.
이 병합 시점에는 새로운 Windows 빌드나
실행 화면 확인을 수행하지 않았다.
GitHub Actions는 실행하지 않았다.
---

## 2026-09-26 — HANG-01 새 사용자 화면: 내 문서에서 fxfile 응답 없음

- **발생/관찰:** 첨부한 Light 메인 화면의 창 제목에 `(응답 없음)`이
  표시되고 탐색 트리/파일 목록이 비어 있다. 이전의
  UI-09 북마크 색상 잔상과는 다른 **런타임 중단 신고**다.
  스크린샷만으로 빌드 리비전·DPI·마지막 입력·
  UI 스레드 호출 스택은 확인할 수 없다.
- **코드에서 확인된 신규 후보:** 앞서 Windows 실행 증거 없이
  합쳐진 UI-02는 ListCtrlEx/TreeCtrlEx 네이티브 처리 뒤
  `ModernUI::paintDarkNativeScrollbars`를 호출하며 이 경로에서
  `GetWindowDC`와 `GetScrollBarInfo`를 사용한다. UI-05는
  새 사용자 프로필에서 `MainCoolBar::OnSize` 안의
  `SetBandInfo` 및 부모 `RecalcLayout` 호출로 배치를 변경한다.
  두 경로 모두 메시지 재진입/레이아웃 연쇄 가능성 때문에
  조사 대상이지만, **어느 경로가 실제 중단을 만들었는지는
  스택/실행 로그가 없어 입증하지 못했다.**
- **안정화 변경:** 위 두 실험적인 UI 경로의 파일 7개를
  Windows x64 실행 이력이 있는 백업 `cd915a0`의
  바이트로 선택적으로 복원했다. 정상 운영에 필요한
  기존 리스트/트리 네이티브 메시지 처리와 기본
  독립 Rebar 행을 되살렸다. 다른 변경을 전부
  `git reset`하지 않았다. 특히 실제 Windows
  진단으로 뒷받침된 UI-09의 MFC
  `CToolBarEx::OnUpdateCmdUI` 이전/이후 damage
  계산·native 회귀 검사, UI-11/12/13 및
  별도의 UI-14 header 코드는 유지했다.
- **재발 방지:** `validate_main_window_hang_stabilization`은
  문제 후보였던 Dark non-client post-paint 재도입,
  `OnSize` 동기적 밴드 변경/부모 재레이아웃,
  UI-09 줄바꿈 및 UI-14 header 계약 보존을 검사한다.
  이 검사는 런타임 교착 원인 확정이나
  실제 화면 응답성 검사를 대체하지 않는다.
- **검증 경계:** 관련 GitHub 원격 blob 비교 및
  정적 속성/부정 테스트로 복원 범위를 검사할 수
  있으나 이번 환경에는 해당 프로젝트의 Windows
  빌드 실행 환경과 사용자 설정/재현 과정이 없다.
  `local_ci.bat x64`, 실제 프로그램 시작과 1분 이상
  내 문서 탐색/크기 변경/Light↔Dark, 기존 프로필과
  별도 새 프로필, UI-09 잔상 회귀는 **NOT TESTED**.
  같은 화면에서 중단이 계속된다면 프로세스
  덤프/스택을 확보해 최종 원인을 식별한다.
  관련 수정 커밋은 해당 안정화 체크포인트.
  GitHub Actions 미실행.



## 2026-09-26 — HANG-01: 시작 중 Shell COM 대기의 MFC paint pump starvation

- **오류 발생:** UI-02/05 경로를 격리한 `882030a`를 사용자가 빌드한 뒤에도
  시작 화면의 트리/목록이 비고 응답하지 않음. 기존 설정 그대로 실행하여 재현.
- **최초 실제 오류 / Observed:** 로컬 minidump와 여러 UI 스레드 샘플에서
  `WinApp::InitInstance/UpdateWindow → ListCtrlEx::WindowProc → native list/image
  rendering → SHDefExtractIconW → thumbcache → CoCreateInstance/COM wait →
  COleMessageFilter::OnMessagePending`이 지속됨. 마지막 함수 내부 PeekMessage와
  DispatchMessage 사이에서 CPU를 사용함. 프레임의 MSG.message는 WM_PAINT이고,
  MSG.hwnd는 같은 UI 스레드의 SysListView32임을 네이티브 클래스 조회로 확인.
  덤프·스택은 ignored logs에만 보관하며 사용자 경로/메모리를 저장소에 올리지 않음.
- **원인 진단:** 설치된 VS MFC `olemsgf.cpp`의 OnMessagePending은 WM_PAINT 큐가
  빌 때까지 순회한다. 이미 목록 paint 안에서 Shell COM을 기다리는데 같은 목록의
  paint가 계속 pending이면 이 루프는 COM에 제어를 돌려주지 않는다. 실제 스택이
  이 루프에 머무름을 확인했으며, 북마크/rebar/scrollbar 프레임은 해당 스택에 없다.
  native control 내부에서 update region을 유지하는 세부 분기와 Shell 서버 자체의
  별도 지연 여부는 미확정이다. 특정 아이콘/셸 확장 제품의 책임을 추정하지 않는다.
- **수정:** win_app.cpp의 앱 소유 COleMessageFilter 파생 클래스에서 paint를
  콜백당 최대 하나만 dispatch하고 scope guard로 재진입을 막는다. 그 후 COM이
  완료/대기 판단을 계속할 수 있다. 기존 필터를 revoke/delete한 뒤 새 필터를
  등록하며, 등록 실패는 OLE 초기화 실패로 처리한다. AfxOleTerm이 필터를 정리한다.
  busy/retry 정책, native painting/update region, 사용자 데이터, UI-09 수정은 보존.
- **재발 방지:** source preflight가 무제한 loop/base-pump 호출, 다중 dispatch,
  재진입 보호 누락, UI 생성 뒤 필터 등록을 거부한다. source mutation으로
  if→while, base-pump 호출 추가 및 설치 누락의 검출을 별도 확인한다.
- **검증 상태:** 수정 전 Windows 재현/스택 확보 완료. 수정 후 source preflight PASS,
  무제한 순회/base-pump 호출/설치 누락/재진입 보호 누락 4개 mutation 검출 PASS. 사용자 빌드 지시에 따라
  compile/link, native suite, 수정 바이너리 runtime/visual은 NOT TESTED.
  동일 시작 조건의 트리/목록/아이콘 로딩, 1분 이상 응답성, 탐색/종료, OLE
  drag/drop, Light/Dark 및 UI-09를 재검증하기 전 HANG-01은 OPEN이다.
- **관련 commit:** 진단 baseline 882030a. 이번 필터 수정·회귀 guard와 개발 상태 문서를 함께 main 반영하는 체크포인트.
  이 항목을 추가한 커밋이 해당 소스 기준이며 빌드/실행 PASS를 의미하지 않는다.

---

## 2026-09-26 — UI-02/05 후속 설계: 비동기 페인트와 첫 배치 한 번만 조정

- **배경:** 앞선 `a720dab4` 구현은 스크롤바를
  네이티브 `WM_NCPAINT` 처리 직후 그렸고,
  `MainCoolBar::OnSize` 내부에서
  `SetBandInfo` 및 부모 재배치를 실행했다.
  이후 HANG-01 신고로 두 변경을 격리했지만
  실제 Windows 덤프에서 확인된 HANG-01
  경로는 별도의 OLE paint starvation이었다.
  해당 OLE 필터 수정은 건드리지 않는다.
- **UI-02 코드:** 공개 native 스크롤바
  지오메트리는 계속 사용하지만 실제
  `GetWindowDC`는 별도 등록·예약 메시지에서만
  호출한다. NC/scroll native 메시지가
  정상 반환한 이후 1개만 `PostMessage`
  하며 그리는 도중 재예약을 막는다.
  사용자 입력과 High Contrast는 Windows
  기본 구현으로 유지한다.
- **UI-05 코드:** 초기 3개 행은 분리하고
  완성된 native `cxIdeal` 값을 기준으로
  예약 메시지에서 최초 한 차례만
  결합을 시도한다. 저장된 기존 배치,
  사용자 다중 행, 좁은 창 설정을
  자동 교체하지 않는다. `OnSize`
  본문에는 행 변경/부모 `RecalcLayout`
  경로를 넣지 않는다.
- **UI-11/12/13/14:** 기존 수정 코드를
  재검토하고 변경 없이 유지했다.
  특히 저장된 날짜 열 폭은 사용자
  설정이므로 225-DIP 기본값으로
  강제 이동시키지 않았다.
- **재발 방지:** `validate_main_window_hang_stabilization`
  검사는 제거된 구형 동기 경로 금지를
  유지하면서 새 지연 메시지,
  coalescing·재진입·고대비 보호,
  저장된 Rebar 상태 보존,
  이전 UI-09 및 UI-14 구현을
  확인하도록 변경했다.
- **검증 범위:** repo 소스 계약과
  제한적인 부정 테스트만 실행.
  통합 Release x64 컴파일/링크,
  `local_ci.bat x64` 전체, 실제
  화면 최종 픽셀, 스크롤 thumb drag,
  저장된 프로필/새 프로필, UI-09,
  DPI와 고대비는 **NOT TESTED**.
  이 커밋을 실제 화면 해결 완료로
  해석하지 않는다. GitHub Actions는
  실행하지 않았다.

---

## 2026-09-26 — 실사용 UI 재발: native drag 스크롤바·이름 열·필터 선택

**재현 보고:** 추가 Dark 파일 목록 화면과 Light/Dark
환경설정 필터링 캡처를 비교했다. 손잡이 드래그 도중
스크롤바가 다시 밝아지고, 파일 목록의 좁은 이름 열
오른쪽에 넓은 빈 공간이 남으며, 필터 목록에서 선택
영역이 과도하게 밝은 파란색이다. 사용자 캡처에는
실행 리비전 및 DPI가 표시되지 않았다.

**소스에서 확인한 내용:** 표준 비클라이언트 스크롤바의
최종 그리기 소유자는 Windows인데 제품은 별도 지연
메시지에서 native 바 위를 덮고 있다. drag에서
메시지가 실행되는 시점을 증명하지 못했으므로
UI-02는 미해결로 유지한다. 기본 새 목록의 이름
열은 150px이고 기존 프로필은 직접 저장한 폭을
재사용한다. 필터의 custom draw는 선택 배경색을
지정하지만 기본 Windows 선택 그리기를
`CDRF_DODEFAULT`로 그대로 실행한다.

**수정 범위:** 신규 기본 폴더 이름 폭을 280
DIP로 확대/DPI 대응하되 기존 저장값은 유지했다.
환경설정 필터의 Light/Dark 선택 항목만
최종 그리기를 직접 수행해 12%/6% 배경 강조,
원래 아이콘과 두 열·설정 색상 대비,
얇은 키보드 포커스를 보존했다.
고대비에서는 native 그리기로 돌아간다.
UI-02에는 검증되지 않은 덮어 그리기
임시방편을 추가하지 않았다.

**회귀/한계:** 새 소스 보호 검사,
기존 UI-09 및 OLE 응답 중단 수정 유지.
해당 Windows 빌드/실제 drag/키보드/
고대비·DPI/기존 프로필 시각 검증은
NOT TESTED다. GitHub Actions 미실행.


---

## 2026-09-27 — Windows PowerShell 5.1 runtime smoke ArgumentList 호환성 오류

**오류 발생**
- 사용자가 revision `ff0352957686a8895e885bc3103eed3a65d6702b`에서 `local_ci.bat x64` 실행.
- 빌드 도구와 x64 artifacts는 확인됐고 native functional regression은 17 passed / 0 failed.
- 그러나 Release x64 runtime smoke에서 PowerShell 예외가 발생해 전체 local CI는 exit 1로 종료됨.

**최초 실제 오류**
- `build/runtime_smoke.ps1`의 `ProcessStartInfo.ArgumentList` 접근에서
  `The property 'ArgumentList' cannot be found on this object`
  (`PropertyNotFoundStrict`)가 발생.
- 시작 코드 예외이므로 실제 제품의 main window 생성 또는 안정성 실패 증거가 아님.
  실행 단계는 이번 실패에서 **NOT TESTED**.

**원인 진단**
- `local_ci.bat`은 기본 `powershell.exe`로 smoke script를 실행하며 Windows
  PowerShell 5.1/.NET Framework의 `ProcessStartInfo`에는 `ArgumentList`
  속성이 없다. 별도로 cleanup에서 사용하던 `Process.Kill(bool)` 역시
  .NET Framework 경로에서 호출할 수 없으므로 후속 종료 오류 가능성이 있었다.

**해결 방법**
- `build/runtime_smoke.ps1`: 생성한 구성/합성 fixture 경로를 인용한
  `ProcessStartInfo.Arguments` 문자열로 시작 인자를 전달한다.
- 프로세스 종료는 .NET `Kill(bool)` overload가 실제 존재할 때만 사용하고,
  Windows PowerShell 5.1에서는 Windows 기본 `taskkill /T /F`로 자식까지
  종료한다. 시간 제한, 사용자 HKCU 상태 감지/거부, 합성 fixture 격리 및
  임시 파일 정리 경로를 유지한다.

**재발 방지**
- `build/validate_source_invariants.py::validate_runtime_smoke_ps51_contract`
  는 WinPS5.1에서 지원하지 않는 `ArgumentList`의 재도입을 거부하고
  인자 quoting/호환 cleanup/기존 사용자 프로필 보호를 점검한다.
- `build/test_runtime_smoke_ps51_contract.py`에 원래 source를 변형한
  compatibility regression 검사를 추가했다. PowerShell 7의 API 가용성을
  Windows PowerShell 5.1에서 동일하다고 가정하지 않는다.

**검증 상태**
- 사용자 수정 전 `ff035295`: source invariant PASS, x64 빌드/필수 artifact
  확인, functional regression 17/0 PASS, runtime smoke FAIL (orchestration).
- 이 수정 checkpoint: 스크립트/source contract 검토 및 신규 검증 코드 반영.
  사용자 Windows PowerShell 5.1에서 동일 `local_ci.bat x64` 재실행:
  **NOT RETESTED**. 새로운 수정 revision의 x64 compile/link 및 실제 프로그램
  launch/visual evidence도 **NOT TESTED**.
- 기존 사용자 데이터를 이용한 테스트를 위해 startup/profiles 보호를
  제거해서는 안 된다. GitHub Actions는 실행하지 않았다.

**관련 commit**
- `4e5bf4bc` — `fix(ci): support Windows PowerShell 5.1 runtime smoke process APIs`
- `90481d66` — `test(ci): reject .NET Core-only APIs in Windows PowerShell runtime smoke`
- `8b7fb5c1` — `test(ci): mutation-check Windows PowerShell runtime smoke regression contract`

---

## 2026-09-27 — UI-05 새 창 너비 증가 후 compact 미적용 및 북마크 chevron 밀림

**오류 발생**
- 실제 Windows 11 / 96 DPI / Dark, 격리된 신규 프로필·합성 파일 205개.
- 기존 e59aed97 창 800×600에서는 도구 모음 밴드가 분리되어 안전했으나 1920×1032로 최대화한 후에도 드라이브와 북마크가 개별 행으로 남음.
- 1차 패치 fe5e49d에서는 최대화 시 결합되지만 기존 전체 행 폭을 유지하던 드라이브 밴드가 북마크를 가려 오른쪽 chevron만 보임.

**최초 실제 오류**
- 초기 폭 한 차례만 확인하는 one-shot pending 플래그가 좁은 첫 프레임에서 꺼짐.
- 최초 결합안은 북마크 RBBS_BREAK만 해제하고 이미 전체 rebar 폭으로 계산된 드라이브 cx를 다시 배분하지 않음.
- 실제 screenshot과 WinApp UI 구조에서 문제 확인. 추측으로 PASS하지 않음.

**원인 진단**
- OnDeferredCompact에서 좁은 창의 미달 판정이 이후 넓어진 창 재시도를 영구히 차단.
- 결합 후 레이아웃은 rebar band별 현재 cx를 사용하므로 BREAK만 제거하면 북마크가 화면 오른쪽 밖으로 밀릴 수 있음.
- OnSize 안의 직접 SetBandInfo/RecalcLayout은 과거 rebar 재진입 중단 문제를 유발할 수 있으므로 사용하지 않음.

**해결 방법**
- src/fxfile/main_coolbar.cpp/.h: 저장된 레이아웃이 없는 신규 프로필에서만 크기 증가 watermark를 갱신하고 예약 메시지로 재측정.
- rebar ideal/header 폭에 DPI-scaled 여유를 더한 실제 드라이브/북마크 목표 폭으로 두 밴드의 cx를 각각 분배하고 나서 부모 레이아웃 갱신.
- native band mutation 직전에 pending을 해제하고 실패 시에만 재시도를 허용해 reentrant 반복 작업을 방지.
- RBN_BEGINDRAG 이후 자동 결합을 취소하여 사용자가 직접 재배치한 밴드를 다시 옮기지 않음.

**재발 방지**
- build/validate_source_invariants.py: 새 프로필 전용, 폭 증가 재시도, 밴드별 실제 폭 분배, 두 native mutation 실패 복구, OnSize의 동기적 레이아웃 금지.
- build/test_ui05_compaction_retry.py: 위 조건 중 하나씩 제거한 음성 변형 포함 11개 독립 회귀 검사.
- 좁은 최초 창과 큰 화면에서의 실제 캡처 및 저장 배치 재오픈 검증을 수행.

**검증 상태**
- 3aab666 후보: Windows Release x64 build PASS, source preflight PASS, 17/0 native functional PASS, 11/0 UI-05 전용 mutation PASS.
- Windows 격리 신규 프로필 800×600→1920×1032: 같은 행의 드라이브+북마크 직접 표시 확인, 응답 정상.
- 격리 저장 프로필 재오픈: 저장 rebar BREAK 플래그 보존, 1920×1032에서 같은 행으로 표시, 정상 종료.
- local_ci runtime smoke는 기존 사용자 HKCU 보호로 SKIPPED: PASS_WITH_SKIPS; 이 단계에 대해서는 자동 시작 검사 완료로 보고하지 않음.
- UI-02 별도 96 DPI Dark 한정 드래그 12+12 프레임 밝아짐 불관측. 다른 DPI/테마에서 UI-02는 OPEN.
- 125/150/200% DPI, Light/High Contrast, 모든 수동 설정 및 복잡한 기존 배치는 NOT TESTED.
- GitHub Actions NOT RUN; 이후 최종 documentation commit에서 전체 local_ci 재수행 결과는 CURRENT_STATUS.md에 갱신.

**관련 commit**
- 3aab666e — UI-05 듀얼 밴드 폭 보정 및 회귀 검사를 포함하는 실기 검증 후보.
- 전체 브랜치: ui/live-windows-ui05-20260927.

---

## 2026-09-27 — UI-02 user screenshot: native Dark scrollbar final-pixel ownership

**오류 발생**
- 사용자 화면: Dark 앱의 파일 목록 오른쪽이 native 밝은 scrollbar임.
- 비교 VM: Windows Dark 96 DPI이므로 기존 버전도 native scrollbar가
  Dark로 보여 원래 사용자 OS-밝음 증상을 완전히 복제하지 못함.
- 기존 probe bright_ratio=0이던 것만으로 사용자 버그를 닫은 것은 잘못됨.

**최초 실제 오류**
- 기존 UI02 implementation은 native NC scrollbar를 지연 GDI
  GetWindowDC로 덮어 그림. 별도 child layered popup으로 실험할 때도
  native thumb modal tracking 도중 덮개가 OS paint에 가려짐.
- OS ScrollBarInfo thumb는 이동하므로 문제는 범위/입력 소유권이 아니라
  OS가 attached nonclient scrollbar의 최종 paint를 다시 담당하는 것.

**원인 진단**
- 실기: GUI 스레드의 root-owned layered WS_POPUP에
  WS_EX_TRANSPARENT/NOACTIVATE를 지정하고 HTTRANSPARENT로 input을
  원래 리스트에 전달하면 OS의 drag modal loop 중에도 자체
  compositor 화면이 유지됨. 임시 opaque tint를 실제 mouse drag로
  8회 계측: 매 프레임 보인 popup thumb와 native xyThumbTop 오차
  약 1px, thumb 23→172 정상 이동. 외부 별도 프로세스 투명창은
  같은-thread pass-through 조건을 충족하지 않아 입력을 방해함.

**해결 방법**
- ModernUI에 list/tree별 native geometry 기반 layered pixel owner와
  documented thread WH_CALLWNDPROCRET + WH_MSGFILTER MSGF_SCROLLBAR
  tracking hook을 추가. 기존 native scroll input/wheel/accessibility는
  바꾸지 않고, 저장된 rebar/기존 HANG-01 OLE 코드는 변경하지 않음.
- popup 은 숨겨진 컨트롤에서 감추고 theme switch/destroy에서 제거.
- final source에서 임시 opaque tint/독립 diagnostic header 완전 삭제.
- visual_ui_probe는 popup을 독립 앱 창으로 찾지 않으며
  layered_windows를 포함해서 캡처하도록 보정.

**재발 방지**
- source invariant에서 GetWindowDC final-pixel overlay 재도입 거부,
  layered compositor/transparent native input/hooks/lifecycle 검사.
- UI02 negative mutation 테스트 15개 및 layered capture 테스트 포함
  visual collector 테스트 9개.
- 기존 OS Dark 한정 밝기 0 결과로 다른 사용자 Windows 문제를
  닫지 않으며 가능한 동일 환경 실기·원본 화면 retest 필수.

**검증 상태**
- 초기 candidate의 Windows x64 compile/link, native functional 17/0
  PASS, automatic runtime smoke SKIPPED (real existing HKCU protection).
- 격리 synthetic profile의 임시 tinted C++ 실제 8-frame
  thumb drag와 per-frame native geometry sync 직접 확인.
- 최종 source는 tint 제거 후 preflight 및 UI02 15 / collector 9 PASS.
  최종 commit revision의 local_ci/revision-matched clean GUI는
  별도 최종 빌드 로그 및 보고에서 확인; 이 기록만으로 PASS 아님.
- 사용자 OS와 동일한 Light-OS+Dark-app 대비, 다중 DPI, High Contrast,
  다양한 테마 전환/복수창은 별도 runtime 확인 전 RETEST OPEN.
- GitHub Actions NOT RUN.

**관련 branch**
- ui/ui02-final-pixel-20260927 (final commit는 브랜치 검증 후 생성)

## 2026-09-29: Independent WinUI3 shell event and UIA acceptance

LOCAL dedicated migration branch only, not production.

Initial C++/WinRT XAML build failed because the new shell declared a nonexistent TabViewSelectionChangedEventArgs and used an incompatible TabView sender. The generated WinUI TabView delegate requires an IInspectable sender and SelectionChangedEventArgs. Both signatures were corrected; independent Debug and Release x64 compilation/linking then passed.

The first real GUI test saw a new tab appear on the wrong pane. A delayed programmatic TabView SelectionChanged had selected the right pane after startup; the model now ignores programmatic selection equal to its own state and has explicit accessible pane-activation buttons. Tab creation now copies the old path before vector insertion. Initial UIA split-toggle testing also had a test-only false failure: a collapsed RightFiles control disappeared from the automation tree rather than returning IsVisible false. The test correctly asserts absence and restored presence.

Final standalone Release SHA256: 70080FECEA2AEDE6A545E5712CD2B6AD6E712BF0637D713C7FA661006D0C32C5. The exact compiled Release executable passed owned real 96-DPI WinUI3 GUI: two independent panes, per-pane local paths/listings, tab add/close, split toggle, real address Enter/Back and the direct native file_operation_core invalid-null API contract. Process exit 0, private fixture removed and six original user configuration SHA256 hashes identical. Source architecture contracts 3/3 passed. Detailed evidence: WINUI3_FULL_REPLACEMENT_20260929.md.

M1-M6 core extraction, virtual Shell enumeration, real mutation operations, profile/installer parity, multi-DPI and accessibility remain NOT ACCEPTED. No hosted GitHub Actions or remote push.

## 2026-09-29: M1 shared native Shell extraction, legacy PCH compatibility and GUI verification

Branch: LOCAL/unmerged migration/winui3-full-shell-20260929, forked from old Phase5 7ceeab5. The other UXH-07 and Phase5 worktrees were left untouched.

Observed coupling: native ExplorerCtrl inherits ListCtrlEx and owns MFC HWND/view state. Its real folder navigation resolves a Windows Shell folder and calls the existing base ShellEnumerator. ShellEnumerator mapped existing native folder/file and hidden/system options and directly called IShellFolder::EnumObjects with the original owner HWND.

Extraction: the old ShellEnumerator now calls the shared pure Win32 shellnav::openEnumeration implemented in src/base/shell_enum_bridge.cpp. The same module is compiled directly into the new independent WinUI3 executable. Higher-level src/base/shell_navigation_core.cpp adds typed absolute PIDL ownership, Shell parsing/binding including virtual This PC, real child enumeration, snapshot identity, per-tab Back/Forward/Up, deterministic error rollback and cooperative atomic cancellation between COM calls. The new WinUI pane/tab state consumes these real sessions and passes the original owned absolute child PIDL when opening an actual folder-list row. Its prior standalone std::filesystem-only NavigationModel was removed from the new project.

Compiler regression and correction: linking the entire new modern Shell session into the original MFC project initially failed. The original forced stdafx/PCH suppresses newer SHGetNameFromIDList, SHBindToObject and known-folder API declarations. No product-wide OS SDK defines were changed. The compatible low-level original EnumObjects bridge was split from the newer Session translation unit. The MFC product compiles ONLY the old-SDK-compatible bridge and the native functional test target compiles both modules; the separate new WinUI 3 project compiles both, independently of any MFC view.

Actual verified results: original MFC local_ci.bat x64 exit 0, source and warning policy PASS, Release x64 compile/link PASS, native 18 passed / 0 failed including new real test-owned local Shell folder/PIDL clone, invalid-path rollback, atomic cancellation without replacement and forward/back/up history. Official runtime smoke SKIPPED due existing real HKCU. Separate isolated real MFC GUI opened synthetic child and executed actual native Go Up / Back / Forward through MainFrame/ExplorerCtrl and the common enumeration bridge, normal exit 0, six original config SHA256 values unchanged. Original MFC binary SHA256 54C6F0C5584E957B8088670DB91414DB90A2D3BD3488B493D053177D5FD529D7.

New WinUI3 Debug/Release x64 compile and actual 96-DPI owned GUI PASS. Final new WinUI Release SHA256 12EE36CB7DC6758A824D4EAA669CFA24E0C81E497022FC36508BD0C973729F18. Its real owned GUI opened an actual Shell folder ListView row by absolute PIDL and navigated back; retained independent per-pane lists and history; opened shell:MyComputerFolder as a genuine virtual Shell PIDL and navigated back to the previously opened local folder. Owned exit 0 and fixture cleanup succeeded, original six SHA256 values unchanged. Static contract 4/4 PASS.

Evidence: docs/development/WINUI3_FULL_REPLACEMENT_20260929.md; logs/m1-shared-enum-legacy-native-local-ci-v2.log; logs/m1-real-legacy-explorer-shared-enum-gui-v2.log; logs/m1-native-shell-winui-release-build.log; logs/m1-native-shell-winui-release-real-gui.log; logs/m1-final-arch-contract.log.

Strictly incomplete: old ExplorerCtrl still owns MFC UI, view-specific filtering, file selection, change watchers, drag/drop and file-operation wiring. The new native Shell session currently enumerates at most 1200 entries SYNCHRONOUSLY on the current COM-initialized STA. Atomic cancellation does NOT interrupt an in-flight blocked Shell extension call. No async COM worker, production Windows Shell context menu/operation parity, advanced metadata or settings compatibility, other real DPI/HC/screen-reader certification or clean installer. Do not mark overall migration M1 complete or replace the user default app based on this bounded result.

## 2026-09-29: Shared Win32 watcher extraction and dedicated Shell STA; native test header and real GUI input fixes

Scoped to the local isolated WinUI3 migration worktree; not a production default replacement.

Implemented MFC-free Unicode/ANSI directory change primitives in src/base/directory_change_bridge.h/.cpp, reused by the old FileChangeWatcher and new WinUI COM STA worker. The dedicated worker creates and destroys its COM folder/enumerator interfaces on a private STA, pumps its queue, rejects stale per-tab results and forwards only owned PIDL snapshots via weak WinUI DispatcherQueue. Active filesystem folders rearm native change watchers and asynchronously refresh the real WinUI ListView.

First legacy native test compilation failed because the historical src/base/stdint.h shadowed the MSVC stdint.h but omitted INTMAX_MAX required by std::thread/ratio; the old native test compiler also rejected C++17 if-initializers. Corrected ONLY the new worker translation unit with a conditional Windows-appropriate LLONG_MAX fallback and C++14-compatible if syntax. The targeted suite and subsequent canonical local_ci.bat x64 both passed 20/0 native, Release build/link/source/warnings PASS; official HKCU-protecting smoke SKIPPED.

An initial new WinUI Release GUI run failed on a folder doubleclick despite passing file create/delete native auto-refresh. Failure-time capture proved an existing user Windows Explorer window was in the foreground and covered the test-owned WinUI. Added an owned foreground PID guard before every real pointer and physical Enter action; abort rather than click a user window when focus is unavailable. The SAME exact compiled WinUI Release EXE then passed the guarded full GUI, including file create/delete auto-refresh, native full-PIDL row doubleclick, cancel/reissue, fast tab close, independent panes and virtual This PC. Both separately owned MFC/WinUI GUI tests exited 0 and left SIX original user config SHA256 hashes unchanged.

Full binary SHAs, exact local logs, further architecture limitations and unverified OS environments: WINUI3_ASYNC_SHELL_CHANGE_WORKER_20260929.md. Nonblocking shutdown of a held TEST callback does not demonstrate forced interruption of a truly blocked third-party COM extension.


## 2026-09-29: C:\dev Phase5 cleanup exposed implicit cross-worktree NuGet dependency

While reducing duplicate worktrees, the migration WinUI build script was found to select the old historical Phase5 worktree's ignored pinned NuGet cache whenever that directory existed. Removing the old folder without correcting this would have introduced an external package-restore dependency and reduced offline reproducibility. The original old Phase5 branch was CLEAN, its source commit 7ceeab5 was retained on the real remote, and 394 unique historical log/sample evidence files were archived locally and verified with per-entry SHA256 plus ZIP CRC. Pinned NuGet packages (1,956 files) were atomically relocated and SHA-verified inside the current migration tree; the build script's cross-worktree fallback was removed. The old Phase5 worktree was then removed with the ordinary git worktree command (no force). A post-removal WinUI Debug x64 build passed using only the new local cache. No active dirty worktree, actual remote branch or running user program was deleted. Full rollback refs, archive hash, exact post-removal binary hash and status: LOCAL_GIT_WORKTREE_CLEANUP_20260929.md.

## 2026-09-29: M1.6 observed serial COM Shell risk; isolated-helper proof and Job exit-code test correction

Source inspection of the published M1.5 migration branch established a real architectural risk, NOT a previously reproduced user-visible crash: one detached, serialized COM STA processes both active pane navigation queues and up to two native directory-change handles. A third-party Shell extension blocking a single parse/bind/EnumObjects/Next/attribute/name call defeats in-flight atomic cancellation and prevents other panes and watcher signals from progressing; detach-on-shutdown avoids waiting but cannot reclaim the worker or contain in-process crashes. The preview also executes SHGetPathFromIDListEx on its WinUI UI thread. Do not claim full hang immunity for this revision.

Decision and scoped development: isolate eventually ALL untrusted read-only Shell parse/enum/metadata calls into up to two bounded, privately supervised helper processes for active panes; keep mutation commands and host configuration separate. Implemented a first independent read-only native helper compiled directly from the same MFC-free Shell source. Actual Debug and Release x64 Windows process tests proved local and virtual Shell results, bounded/corruption-checked IPC, two independent simultaneous processes, test-only owned blocking in one lane while the other progresses, finite exact-child Job-object termination/recovery and automatic job-handle-close reclamation. Original six user configuration hashes were unchanged.

An initial Release **test assertion** incorrectly required a nonzero exit code when KILL_ON_JOB_CLOSE ended a test-owned child; the platform can produce exit code zero for Job-handle closure. Corrected the test to assert timely process reaping before its 30-second synthetic sleep could finish and reject its natural exit code; the **same Release helper binary** then passed. This was not an actual Shell COM failure. Real hung third-party extensions, restricted-token security, native C++ host supervisor, production/preview WinUI integration and virtual Shell change events remain UNVERIFIED. See WINUI3_M16_SHELL_PROCESS_ISOLATION_20260929.md and ignored logs/m16.

## 2026-09-29: M1.7 real WinUI two-lane read-only Shell process integration and asynchronous GUI test races

This entry supersedes the earlier M1.6 helper-only architecture milestone, but does not replace or erase it. The isolated WinUI preview now routes real left/right Shell navigation through a native C++ two-lane process supervisor; private sibling-helper ownership, explicit inheritable handle allowlist, CREATE_SUSPENDED + pre-resume private KILL_ON_JOB_CLOSE Job assignment, per-lane finite timeout (4.5s), one restart and UI route/epoch rejection are enforced. A separate native COM-free filesystem watcher receives child-computed filesystem paths; SHGetPathFromIDListEx no longer runs on the preview's UI path. The old in-process AsyncShellWorker .cpp is no longer linked into the preview, though the unchanged legacy MFC regression retains it.

During real WinUI GUI migration testing, two TEST-HARNESS races were exposed (not product crashes): first, the newly faster helper replaced the constructor's transient initial status before the harness asserted the previous literal `native shell engine active`; fixed to recognize either the valid initial or helper-loaded state. Second, an edited right-pane TextBox echoed its new path before the out-of-process helper had delivered real right-pane ListView rows; the previous immediate assertion misinterpreted expected asynchronous display timing. The harness now **waits for actual independent right-pane rows**, not just the echoed address, and continues using owned-foreground-PID guards before physical input. The exact updated Debug GUI passed.

Exact final same-source WinUI Debug and Release x64 builds passed. A real test-owned Debug GUI deliberately blocked the left child for 30s and verified the right pane completed first, then observed the left private Job timeout/restart, real create/delete watcher refresh, independent panes, virtual This PC, own-process exit 0 and six original user-setting hashes identical. A real Release GUI verified normal left/right navigation, tabs, full PIDL open/back, virtual folder, create/delete watcher, own-process exit 0 and six original hashes identical. Standalone v2 helper and private-Job regression passed in Debug and Release; combined M1.5/M1.6/M1.7 source contracts 12/12 pass. Original MFC source/build/test graph unchanged; historical same-source M1.5 native 20/0 PASS_WITH_SKIPS was reused, NOT rerun.

This remains experimental preview fault containment and NOT a restricted-token sandbox, proof against an actually broken external Shell extension/UNC, virtual Shell-change subscription, a production MFC switch, completed full file operations or all-DPI/HC accessibility acceptance. Exact logs and paired executable hashes: WINUI3_M17_PANE_PROCESS_SUPERVISOR_20260929.md and ignored logs/m16/m17-*. No hosted Actions, push or merge occurred in this local implementation.

## 2026-09-29: M1.8 owned COM fault, invalid loopback UNC and independent Shell namespace notifications

The preceding M1.7 supervisor was extended without changing the default MFC product. The private helper now has an explicit test-only, UNREGISTERED COM IUnknown object whose QueryInterface delays 30 seconds on the owned child STA. Real WinUI Debug GUI passed independent right-pane progress, exact left-helper Job timeout and recovery, and a separate TWO-attempt exhaustion test with readable failure status and both previously accepted folders intact. An invalid local-only loopback UNC safely produced network-specific failure feedback. A separate private Shell namespace notification HWND/message thread subscribes to selected virtual PIDLs; its actual WinUI callback/refresh passed for SHChangeNotify on a strictly test-owned local folder. This is not proof of an actual installed faulty third-party extension, inaccessible real remote SMB environment or actual external virtual namespace provider event.

During acceptance the initial UNC Python harness inadvertently embedded a form-feed escape in place of the intended backslash. Its failure was TEST DATA, not a product failure. The corrected raw path was retested against the same built application and passed. The first new Debug compilation exposed a test-only command-line loop missing braces, causing a local variable to be referenced outside scope. It was corrected before final Debug/Release builds and GUI runs. Final current-source Debug and Release x64 build and actual owned GUI PASS; Debug COM/UNC/namespace combination PASS, separate two-exhausted-COM-attempt UI PASS, Release helper/Job PASS and 14/14 static PASS. All six original user profile hashes remained unchanged. Historical MFC native 20/0 PASS_WITH_SKIPS was reused, not executed in M1.8. Full logs and SHA256 evidence: WINUI3_M18_SHELL_STABILITY_20260929.md and ignored logs/m18. No hosted CI, push or merge.


## 2026-09-29: UXH-07 variable-width Windows TEMP directory names

**Observed failure:** Real second named-workspace Open
intermittently showed an isolated owner-marker protection
error (initially 1, later discriminated as code 14). An
apparent additional restart-only failure also occurred
during the extended automated GUI acceptance.

**First confirmed product error and root cause:**
The newly added `workspace_session::ownedDir` assumed
`GetTempFileName` always produced exactly four hex
digits in `fxw????.tmp`. 240 real Windows
`GetTempFileNameW` calls in an exclusively private
folder produced three-digit names including `fxw18F.tmp`.
The valid generated directory then failed its own
strict length check. The stale-orphan glob had the
same erroneous four-character assumption.

**Product correction:** Permit EXACT TEMP-root leaves
of `fxw` + 1-4 hex digits + `.tmp`; enumerate
`fxw*.tmp` for orphan candidates but retain the
marker magic, exact filename allowlist, no recursion,
24-hour age, exclusive active lock and reparse rejection.
An independent legacy-parser input problem was separately
bounded by rejecting odd-length/non-UTF-16-BOM named
snapshot data before `ConfFileEx::load`.

**Test-harness-only false failure:** The restart watcher
checked `"fxw" in argv` where `argv` was a
`psutil` command-token list. Real opt-in native
evidence instead proved IDOK from the dialog, successful
child CreateProcess and a living child. Replaced this
with exact `--conf_dir` extraction and strict owned
directory name validation. Removed temporary product
instrumentation before final compilation. Do not
attribute the old restart-only detection failure to
the application.

**Verification and prevention:** Final local x64 binary
SHA256 `0873F600E45DC26BEF98948BF2B6DADBC013C1DC11633B614EED5B75BA2F091C`;
canonical `local_ci.bat x64` exit 0, source checks and
native 17/0 PASS, official smoke SKIPPED due to existing
HKCU state. Eight real malformed GUI inputs PASS; two
named native GUI Save/Open and normal parent restart
with reopen of BOTH named files PASS; controlled
three-hex stale orphan, four-hex locked live marker
and reparse external-sentinel real-app safety PASS.
All accepted owned tests preserved the original six
configuration SHA256 values. Evidence and precise
log paths: `UI_PHASE6_UXH07_NAMED_WORKSPACE_WIP_20260929.md`.

**Build orchestration context:** The remote tool process
did not expose `ProgramFiles(x86)` or `TMP`; the
empty `TMP` triggered MSBuild MSB8029's temp-prefix
check, not an observed product code defect. Restoring
both variables ONLY for the local CI process eliminated
the prior strict warning-policy failure; the clean
full local CI result was PASS_WITH_SKIPS, not a
successful official runtime smoke.

**Scope remaining:** Real other DPI, OS High Contrast,
spoken accessibility, clean installer/package, hosted
CI, and fully mouse-only top-level menu routing were
not part of this acceptance. No GitHub Actions,
remote push, or merge was performed.
\n## 2026-09-29: Korean Workspaces placeholders and unthemed legacy native toolbar Customize

Observed: canonical Korean workspace labels contained literal question marks. Owner-drawn submenu chevrons were small/low contrast and native toolbar Customize appeared inconsistent with Dark mode, including legacy light ListBox scrollbars.

Root causes: three literal corrupted Korean XML values; font-dependent 12-DIP menu glyph and 1-pixel fallback; native Windows TB_CUSTOMIZE parent bypassed common CModernDialog control traversal and applied Explorer visual theme to ListBoxes without the common scrollbar compositor, parent palette or direct button theme.

Correction: repair all three labels retaining menu mnemonics, replace the glyph with a single native DPI-scaled two-stroke chevron and High Contrast system colors, and enroll native Customize parent and both ListBoxes in the existing shared ModernUI dark painting and scrollbar path. Canonical source invariant now requires this native glyph; three focused source contracts cover localization, glyph and Customize theme enrollment.

Acceptance (local, uncommitted branch only): x64 executable SHA256 C0FF584E685E7DEEF6E3844AC7F0A55E2AA541DE0235B66F1BA7859826E64E79. Canonical local_ci.bat x64 exit 0, native functional 17 passed / 0 failed; overall PASS_WITH_SKIPS due to protected original HKCU runtime smoke. Two separate test-owned Windows 11 GUI runs displayed correct Korean submenu and new chevrons; native Customize showed dark scrollbars on both ListBoxes, and real wheel moved top index 0 to 9. Six original user-setting hashes were identical and owned processes exited 0.

Wider source inventory found 24 direct CWnd/CDialog base declarations, many already themed or not actual dialogs. FolderPane, TabPane and CWindowScroller remain conditional GUI-review candidates, NOT diagnosed failures. Native popup overflow, other real DPI, OS High Contrast, spoken screen reader, additional app/UI routes and clean-machine deployment remain untested. Full logs, local screenshots and scope: UI_LEGACY_MENU_TOOLBAR_AUDIT_20260929.md. No GitHub Actions, remote push or branch merge.


## 2026-09-29: UXH-06 isolated main integration and final real search privacy acceptance

The original UXH-06 branch was merged without source conflicts into an isolated current-main/UXH-07 worktree. Canonical Release x64 Unicode local CI 17/0 PASS_WITH_SKIPS; its default HKCU runtime smoke was deliberately skipped because the user has an existing live profile. The actual owned 96-DPI GUI proved long full-scope text, opted-in single-directory search persistence after normal app restart, physical recent selection, Clear, restart empty and an additional **valid opt-out search** that was not recorded either immediately or after a further restart. All six original user's config SHA256 hashes were unchanged. An early pre-build UXH-06 contract test reported a missing generated `bin/x64/Languages/Korean.xml` because this brand-new worktree had no built binary/staged language files; the unchanged same focused contracts all passed after canonical build staged that file. This prebuild test setup error was NOT a product failure. Unrelated UI-02 dark/native scrollbar tests are being assessed separately because a tree-horizontal-pointer test reproduced the same direction discrepancy in BOTH Light and Dark, making the old extra dark renderer a questionable blind merge candidate. Exact UXH-06 acceptance and limits: UXH06_MAIN_MERGE_ACCEPTANCE_20260929.md.


## 2026-09-29: UI-02 superseded renderer and owned native pointer-test environment failures

The older unmerged UI-02 branch added a separate worker-thread DarkScrollbarLayer (560 C++ lines) on top of controls that current main had independently changed to use the already tested ModernUI per-HWND layered native overlay with modal WH_MSGFILTER/WH_CALLWNDPROCRET support and High Contrast escape. A direct merge had exactly two ListCtrlEx/TreeCtrlEx content conflicts. Rather than deploy two competing overlays, the integration intentionally resolves both controls to the known current ModernUI implementation, removes the old duplicate layer and its GYP entries from the resulting tree, and retains the old branch as a real merge parent for full historical provenance.

A 96-DPI owned primary-scroll GUI script initially failed native tree pointer tests identically in Light and Dark, indicating the old dark-only renderer was not the root cause. On-machine diagnostic screenshots/geometry revealed (1) the hardcoded 730px test window at y70 placed the tree horizontal scrollbar at global y783 below the actual work-area bottom 714, (2) copied live-user Last Tabs could override the fixture directory, and (3) the owned app's default Tip of the Day #32770 modal sometimes intercepted mouse clicks while scroll HWNDs underneath still reported visible. The test was CORRECTED to clamp its owned frame to SPI_GETWORKAREA, replace only copied PRIVATE tab layout with the known 65-folder fixture and await its real ListView rows, physically dismiss only the exact test-owned modal, and require a matching owned foreground process before pointer input. Diagnostic screenshots remain ignored and the FINAL tracked regression harness does NOT capture desktop pixels.

After these test-environment corrections the UNCHANGED current ModernUI product's actual Light and Dark primary GUI both passed native tree/list horizontal/vertical arrows, list thumb drag and track-click and dark-only overlay visuals. Its separate modal native-scroll GUI passed in both Light and Dark; original six user settings SHA256 unchanged, owned processes exited 0. Current ModernUI static source/negative contracts 19/19 plus three new harness-safety tests 3/3 PASS. Previously integrated UXH-06 Release-x64-Unicode source/binary hash and native 17/0 PASS_WITH_SKIPS remain applicable because UI-02 result modifies no production C++ source/GYP. This is not a claim of tested alternate physical DPI/HC/accessibility. See docs/development/UI02_SUPERSEDED_MERGE_ACCEPTANCE_20260929.md and ignored original/temporary logs/merge-20260929.

## 2026-09-29: M1.9 actual mainline source import, scoped WinUI UXH feature support and owned real GUI diagnostics

Latest native main 3a4d27c was actually merged into independent WinUI migration prior tip 34936ee, initially --no-commit with only three documentation conflicts in .agent-policy/PROJECT.md, docs/development/CURRENT_STATUS.md and this append-only ERROR_HISTORY.md; BOTH dated versions' historical content were preserved. Actual MFC sources auto-merged, canonical combined MFC Release x64 CI 20/0 PASS_WITH_SKIPS, real existing HKCU runtime smoke intentionally skipped. This is a migration-branch source merge, NOT a replacement for the protected native main.

New preview-only native UTF-16 MFC workspace schema1 bounded subset and isolated separate-window GUI, plus separate bounded read-only filesystem filename search and explicit opt-in private WinUI LOCALAPPDATA recent scopes were implemented. Real owned Debug and Release WinUI GUI proved workspace save/restored selected and inactive tabs, bad schema/no unexpected child, CREATE_NEW refusal to overwrite, default-opt-out search history absence, long path opt-in persistence, restart/select/clear across processes and six actual original user configs unchanged. Actual bidirectional MFC GUI file dialog opened WinUI-exported schema in a private MFC child preserving prior parent state and actual MFC GUI exported a second schema file imported back into WinUI. These test only supported one/two-pane subset, not complete old MFC tab-history/full search filter/regex/content fidelity.

Issues observed and corrected: separate M1.9 features translation unit originally omitted C++/WinRT XAML namespace imports (first Debug compile failed); after correction exact merged Debug/Release builds passed. Initial native recent reader reversed persistent history order by reinserting entries at the front; real compiled native contract exposed 11/12 and fix retained on-disk order, after which independently owned Debug/Release native bridge tests passed 12/12. Initial real GUI automation asserted TabView UIA rows too early and attempted to inspect WinUI ComboBox virtual popup children and item_texts placeholders as actual data; corrected to wait for real selected path/right pane, inspect model-backed recent count and verify full restored path and empty private UTF-16 file. Final actual scoped Debug/Release GUI and combined 20/20 source architecture checks passed.

Latest M1.9 full results, logs, compile hashes and limits: WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md and ignored logs/m19. Full old MFC search/layout/operations and physical higher DPI/OS HC/Narrator/real hostile extensions/SMB remain UNVERIFIED. Do not re-label old M1.8 per-revision results as proof on the new merged source without specific new re-run logs. Original main and real user settings remain protected.


## 2026-09-29: M1.9 resumed GUI assertion and owned virtual-folder diagnostic

During resumed acceptance the **first new test** wrongly expected a selected tab **inside** an empty test-owned Nested directory to itself contain a list row named Nested. The actual WinUI model had correctly restored the selected second tab; the test now verifies the XAML active full address and exact two tab headers. Final owned Debug and Release GUI passed.

A second preliminary TEST assertion searched collapsed WinUI ComboBox UIA descendants for loaded recent items. WinUI virtualizes its closed popup; real XAML `RecentCountText` and UIA `select(1)` showed the correct newest-first two item model, full prior scope restored without rewriting the file, and correctly persisted zero after Clear. One separate diagnostic Python synthetic file inadvertently expanded existing CRLF into a double-CR sequence on Windows, which made that **diagnostic-only** fixture invalid. A subsequent byte-exact UTF-16 BOM+CRLF synthetic fixture and full rebuilt GUI passed. No lost production history was demonstrated by those preliminary test errors.

Initial independent interoperability attempted to open the **actual MFC-generated second workspace** directly: its selected second tab is a Windows virtual Shell alias to the connected user's Documents. This caused one read-only WinUI Shell **metadata enumeration of that real Documents folder during diagnosis**; no file content was opened or modified, and the original six MFC user setting files remained unchanged. To avoid repeated unowned folder access, final tests open the original genuine MFC-generated 1+1 workspace unmodified, but substitute ONLY the second real MFC-generated file's Documents virtual-tab target with a **test-owned local directory** in a temporary copy before launching either WinUI build. All remaining native-authored workspace schema keys and original two-tab selection remain intact. Final Debug and Release owned GUI and original six configuration hashes PASS. Separate earlier, entirely synthetic, real bidirectional WinUI?MFC native dialog and MFC?WinUI GUI proof remains intact; this safer extra test must not be misrepresented as unchanged virtual-Documents interoperability.

Final compiled M1.9 WinUI Debug/Release actual owned GUI, merged native MFC x64 20/0 PASS_WITH_SKIPS (existing real HKCU smoke intentionally SKIPPED), own native UXH-07/UXH-06 and UI-02 Dark/Light primary/modal GUI, independent same-source M1.9 native 12/12 each config, combined source 56/56, Release native helper/Job and actual Debug M1.8 COM/namespace notification/local-loopback/two-timeout regression all passed. Two separate WinUI Release EXE hashes in historical M1.9 logs correspond to distinct actual builds; exact newer rebuilt hashes are in WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md. Default native main worktree and original untracked image were not modified.


## 2026-09-29: M2.0 actual WinUI state and GUI test-only corrections

- Initial shared C++ model compile hit the Win32 `max` macro expansion of `std::numeric_limits<uint64_t>::max()`; changed to the macro-safe `(std::numeric_limits<uint64_t>::max)()`. The final native and independent WinUI x64 Debug/Release builds then succeeded.
- Older static tests assumed that `PaneState` was declared only in the WinUI window, that direct `pane.tabs.emplace_back()` remained there, or that the historical main code merge parent had to equal the newer docs-only main tip. The source guards were corrected to assert the actual UI-independent native model, preserve the verified M1.9 imported code commit, and distinguish subsequent docs-only main updates. Combined current 64/64 static/source tests passed.
- Real GUI harness initially assumed WinUI's `ThemePicker` accessible item count was exactly three; its provider reported four peers for three actual options, so that incidental UIA count is not the runtime contract. Actual System/Light/Dark UIA selection and rendered Light/Dark pixel difference passed for both Debug and Release.
- The old test incorrectly assumed collapsed right-pane UIA elements remain queryable; actual WinUI removes that subtree from UIA when hidden, raising `ElementNotFoundError`. Corrected the test to check actual absence plus composited right-region pixel change; observed real owned pixel differences were 0.26 in Debug and 0.82 in Release.
- A new This PC GUI probe expected an unresolved `computerfolder` alias, whereas the same isolated Shell helper resolves it into native virtual `::{...}` PIDL parsing text. The updated test verifies the real resolved virtual PIDL and physically performs Back. Debug and Release completed these scenarios without touching original settings.


## 2026-09-29: M2.1 literal ?? runtime theme labels after partial UTF-8 repair

Initial remote Python writes from Windows PowerShell lost Hangul because the input pipe was not explicitly UTF-8. The main/source text was reconstructed with true Unicode and explicit UTF-8 transport, but three literal `??` strings remained in `ShellHeader.xaml.cpp::ShowChoice()`. The actual owned Debug WinUI GUI exposed `ThemeStateText` as ASCII `??: ???`: this was a **real runtime localization bug**, not only PowerShell console mojibake. Corrected all three genuine Korean strings, consolidated project-wide `/utf-8` compiler options for Debug/Release and created a static source check forbidding this exact bad runtime text. The rebuilt actual owned Debug GUI returned genuine Unicode Korean System, passed Dark/Light/Dark private theme persistence, real second process Korean Dark restoration and guarded Korean-folder create/rename/duplicate non-overwrite; original six MFC user settings unchanged. Earlier failed GUI logs are NOT pass proof. The initial GUI test also assumed non-exposed outer UserControl UIA wrappers and incorrectly called `child_window` on a UIA wrapper; both test-only assumptions were fixed. An owned child inadvertently left running by the preliminary test was identified using exact developer build exe AND exact synthetic owned folder argument, then safely terminated. The final harness now terminates only its own spawned child even when discovery fails.


## 2026-09-29: M2.2 소유 GUI 시험의 한글 파이프 및 다중 선택 하네스 오류

초기 79개 소스 검사의 1건 실패는 구현의 `state_.cancel.load`와 테스트의 잘못된 `progress.cancel.load` 기대가 달랐던 **테스트 오류**로 수정했다. 원격 PowerShell→Python의 비 UTF-8 파이프는 소유 GUI 시험용 한글 파일명을 `???.txt`로 치환했다. 입력에 UTF-8 `$OutputEncoding`을 명시하고 실제 유니코드 소스와 생성되는 파일명으로 검증했다. Python UIA 첫 시험에는 지원하지 않는 `click_input(key=...)` 인자를 사용했다. 다음 실행에서는 의도적으로 성공시킨 다중 선택 상태를 다음 단일 파일 이동에도 남겨 충돌을 발생시켰다. 실제 설치된 UIA의 `pressed="ctrl"` 및 `ListItem.select()`로 서로 다른 작업의 선택 범위를 명확히 분리하고 다시 검증했다. 이 실패는 하네스 오류로 기록하며 초기 실패 로그를 최종 제품 PASS라고 설명하지 않는다. 사전 GUI 실행 실패가 만든 정확히 식별된 한 개 임시 소유 폴더만 검사 후 정리했고 기존 사용자 파일/임의 창을 변경하지 않았다.


## 2026-09-29: M2.2 최종 통합 GUI 다중 선택 재현 및 해결

독립 집중 Debug GUI에서는 Ctrl 물리 클릭으로 다중 선택 복사가 성공했으나, M1.9~M2.1 GUI 테스트를 먼저 수행한 통합 환경에서는 UIA의 물리 클릭 보조 키 처리·이전 선택 상태가 달라 두 파일 동시 선택 테스트가 재현되지 않았다. 단순히 이전 선택을 지우는 것만으로는 해결되지 않았으므로 GUI 자동화의 두 번째 선택 명령을 UIA SelectionItem.AddToSelection()으로 변경하고 첫 번째 항목은 SelectionItem.Select()를 사용했다. 재현 가능한 실제 소유 Debug·Release 통합 GUI가 모두 통과해 이전 실패 로그와 구분했다. 공통 소스 계약에도 동일 UIA 선택 경로 확인을 포함했으며 **제품 코드의 별도 선택 상태 우회는 추가하지 않았다.** 해당 과정의 실제 선택 대상은 모두 자동 생성한 로컬 소유 파일로 제한했다.


## 2026-09-29: M2.3 중복 기본 언어·개인 세션 컴파일러 매크로·드래그 실기 미검증

1. 기존 WinUI MSBuild template은 ^DefaultLanguage=ko-KR^와 뒤쪽 ^DefaultLanguage=en-US^를 중복 지정했다. 마지막 영어 지정이 선행 한국어를 무력화할 수 있어 후자를 제거하고 한국어 기본 언어 하나만 남겼다. 정적 소스 계약에서 중복 등록을 거부한다.
2. 첫 개인 세션 WinUI C++ 컴파일에서 Win32 header의 ^max^ 매크로와 C++ 서로 다른 타입의 ^auto a,b^ 합병 선언 때문에 실제 C2589/C3538이 발생했다. ^(std::max)(...)^ 및 각각 타입 추론된 선언으로 수정하고 실 Debug 재빌드 후 실제 소유 GUI 세션 저장·두 번째 프로세스 복원·삭제를 확인했다. 최초 오류 로그는 로컬 무시된 ^logs/m23^의 별도 실제 파일로 보존한다.
3. 양쪽 WinUI 파일 목록의 XAML ^CanDragItems^ 및 리스트 항목의 ^CanDrag^와 Drop handler는 Debug에서 컴파일됐지만, 원격 테스트가 자체 소유 창 안의 한국어 파일을 자동 물리 마우스로 왼쪽→오른쪽으로 드래그해 복사하려던 실기 시험은 **기본 핸들러와 직접 ListViewItem 핸들러 모두 실패**했다. 마우스 좌표 및 StatusText UIA 진단을 보존했으며, WinUI DragStarting/Drop 이벤트가 실제 호출됐는지 코드 결함인지 자동화 한계인지 아직 판정할 자료가 부족하다. 미검증 상태의 물리 드래그는 별도 ^FLY_M23_OWNED_DRAG_TEST=YES^ 진단 플래그에서만 시행하고 공통 Shell/세션 수용 시험의 PASS에 섞지 않는다. 실제 Explorer→WinUI 및 WinUI→Explorer 상호 운용/외부 확장 역시 NOT TESTED다.
4. 전역 Windows 클립보드를 실제로 건드리면 사용자 클립보드 값과 형식을 잃을 위험이 있어, CF_HDROP in-memory wire 검증·합성 로컬 실제 Shell 복사만 기본 native 시험으로 삼고 실제 OS 명령은 별도 격리 Windows 사용자 컨텍스트가 확보될 때 검증한다. 전역 휴지통 실제 삭제·복원도 동일하게 미완료 게이트로 유지한다.

세부 구현 범위 및 검증 등급: M2.3 단계별 통합 (WINUI3_M23_CLIPBOARD_SESSION_DRAG_STAGING_20260929.md; historical, recover from Git).


## 2026-09-29: M2.3 한국어 문구 손실 및 드래그 자동화 미도달 기록

M2.3 후속 작업에서 `m23_drag.cpp`의 오류 문구 7개가 이전 원격 UTF-8 전달 문제로 손상된 사실을 확인해 한국어로 복구했다. 재발 방지를 위해 소스 검사에 해당 오류 문구와 리소스 연결 검사를 추가했다. 테스트 소유 Debug 창에서 네 단계 진단을 추가하여 포인터 입력을 시도했으나, 실제 DragStarting·DragOver·Drop 이벤트 발생을 관찰하지 못했다. 코드 결함 또는 입력 자동화 한계를 구분할 근거가 없으므로 드래그는 미검증 상태다. 별도로 Debug·Release 통합 소유 GUI와 소스 검사 102/102는 다른 검증 대상에서 통과했다. M2.3 후속 세부 기록 (WINUI3_M23_FOLLOWUP_KOREAN_RESOURCES_DRAG_DIAGNOSTICS_20260929.md; historical, recover from Git).


## 2026-09-29: 단계 간 패널 잔존 시 This PC 자동화 요소 미노출

**상태: OPEN / 원인 미확정.** 독립 WinUI 리팩터링 이후의 전체 M1.9~M2.3 소유 Debug GUI에서 M1.9의 작업 공간·검색 패널을 열어 둔 채 M2.0의 분할 창 숨김/복원을 실행하면, 실제 UIA에서 `ThisPCButton`을 찾지 못했다. 9초 동안 요소 재등장을 기다려도 미노출이 지속됐으며 테스트는 실패했다. 해당 실행의 다른 단계에서 원본 MFC 설정 6개는 보존됐고 소유 프로세스는 정상 종료했다. 반면 M2.0 단독 소유 Debug GUI와 M1.9 이후 두 패널을 명시적으로 닫은 M2.0 소유 Debug GUI에서는 동일 탐색·분할·This PC 조작을 통과했다. 따라서 단순 UIA 일시 지연으로 종결할 수 없고, 패널이 열린 상태의 실제 화면 배치/접근성 노출과 자동화 조건을 구분해야 한다. 이를 해결하지 않은 채 별도 패널 격리 시험 성공을 전체 UI 수용으로 승격하지 않는다. 상세 실패·비교 증거는 `logs/winui-scoped/20260929-222742-gui-Debug.log`, `isolated-m20-after-sidebar-failure.log` 및 `isolated-m19-m20-panels-closed.log`에 보존한다. 다음 담당자는 해당 상태의 실제 합성 화면과 접근성 트리 및 레이아웃 크기를 함께 확인한다.


## 2026-09-29: M2.3 세션 복원 후 부모 창 기억 삭제 버튼 UIA 재검색 실패

**상태: OPEN / 원인 미확정.** 동일한 개인 소유 폴더 및 별도 사용자 설정을 사용하는 WinUI Debug GUI에서 현재 세션을 실제 저장하고, 정확히 식별된 새 소유 프로세스가 좌우 두 폴더를 복원한 뒤 정상 종료할 때까지는 성공했다. 하지만 원래 부모 창의 `ClearSessionButton`을 자동화 도구가 클릭하려고 다시 검색하면 `pywinauto.timings.TimeoutError`와 `ElementNotFoundError`가 발생했다. M1.9/M2.0 패널을 제외하고 M2.1~M2.3만 시험했을 때와 M2.3 단독 집중 시험에서도 같은 현상을 관찰했으므로, M1.9 패널 잔존만이 원인이라고 해석할 수 없다. M2.3 집중 시험에서 원래 부모 창의 `WorkspacePanelButton`, `WorkspaceFileBox`, `SaveSessionButton`, `RestoreSessionButton`, `ClearSessionButton`는 모두 한 차례 UIA `exists()=True`로 관찰됐지만, 실제 `wrapper_object()` 재조회는 실패했다. 현재 증거만으로 화면 레이아웃, 포커스, UIA 래퍼 또는 제품 동작의 문제라고 단정할 수 없다. 모든 해당 소유 테스트에서는 원래 MFC 사용자 설정 6개가 보호되고 소유 프로세스가 정상 종료했다. 로컬 무시 로그: `logs/winui-scoped/20260929-223318-gui-Debug.log`, `isolated-m21-m22-m23-debug.log`, `isolated-m23-post-child-uia-diagnostic.log` 및 `isolated-m23-control-bounds.log`. 사람의 실제 소유 창 화면 및 UIA/컨트롤 실제 경계 측정을 결합한 단일 재현을 확보하기 전에는 해결 완료나 M2.3 통합 GUI PASS라고 보고하지 않는다.

## 2026-09-30: M2.3 후속 소형 화면 경계 오류 수용

**실제 오류:** M1.9의 검색 패널을 펼친 통합 소유 GUI에서 M2.0 분할 창 복원 후 내 PC 버튼의 UIA 요소가 노출되지 않았다. 실패 당시 창은 높이 519px, 파일 목록은 높이 44px이었고 원래 MFC 설정은 그대로 보존됐다.

**확인된 원인:** 실제 모니터의 작업 영역 하단 720px과 창 위치 y=78 기준 사용 가능 높이는 634px이지만, `EnsureExpandedPanelFits()`의 이전 조건 `desired>=640` 때문에 필요한 창 확장이 실행되지 않았다. 창 y=26에서는 초기 창이 686px로 확장된 기존 차별 시험도 있었다.

**수정:** 최소 560px의 사용 가능 높이가 있고 기존 창보다 40px 넘게 확장 가능하면 작업 영역 경계에 맞춰 확장한다. 검색 결과는 64px, 작업 공간 명령은 두 줄로 배치하고 사이드바는 스크롤 가능하게 했다. 기존 독립 Shell 작업·MFC 본 제품은 변경하지 않았다.

**검증:** 소유 HWND만 (78,78,960,519)로 배치한 집중 Debug GUI에서 실제 높이 634px, 내 PC 버튼 노출·실제 탐색 및 분할 화면 복원이 통과했다. 이어 같은 소유 소형 화면 조건의 통합 Debug 및 Release GUI가 모두 통과했다. 최초 실패 로그와 새 수용 로그를 구분해 `logs/winui-scoped/`에 보존한다. 이 결과는 실제 DPI 100%의 해당 PC/기능 한정이며 다른 DPI나 전 제품 인증은 아니다.

## 2026-09-30: 개인 세션 기억 삭제와 단일 파일 선택 하네스 후속 검증

**실제 과거 증상:** 별도 소유 프로세스의 개인 세션 복원 직후 부모 창의 `ClearSessionButton`을 자동화 도구가 다시 조회하는 과정이 실패했다. 작업 공간 버튼이 가로 한 줄에 길게 배치되어 있던 기존 UI는 작은 창에서 사용하기 불리했다. 별도로 통합 Debug 소유 시험에서 다중 선택 복사 뒤 `이동.txt`의 존재를 확인한 직후 두 번째 UIA 목록 조회에서는 해당 행을 찾지 못했다.

**변경:** 작업 공간 명령을 두 줄로 재배치하여 클리어 버튼의 화면 배치 문제를 개선했다. 다중 선택 이후 단일 파일 선택은 불안정한 별도 존재 검사 후 재검색하는 대신, 같은 제한된 재시도 안에서 새 UIA 행 검색, `Select()` 실행 및 실제 단일 선택 확인을 수행하게 변경했다. 일시적인 UIA 행 갱신은 가능한 원인이지만 실제 내부 스케줄을 직접 기록한 것은 아니므로 제품 파일 목록 결함으로 단정하지 않는다.

**검증:** 별도 소유 소형 화면에서 전체 Debug와 Release M1.9~M2.3 GUI가 모두 통과했다. 양쪽에서 파일 복사·이동·충돌 취소와 개인 세션 저장·별도 프로세스 두 폴더 복원·기억 삭제가 확인됐으며 원본 사용자 설정 6개는 각각 해시 동일했다. 증거: `logs/winui-scoped/20260930-065505-gui-Debug.log` 및 `logs/winui-scoped/20260930-065643-gui-Release.log`. 이전 실패 로그는 삭제하거나 PASS로 바꾸지 않는다. 실제 사람의 드래그/외부 Explorer 및 전역 클립보드·휴지통은 이 후속 검증에 포함하지 않았다.


## 2026-09-30: fast Shell-helper reply truncated at process exit (1,100 synthetic children)

A real owned WinUI Debug process failed to navigate into a 1,100-file synthetic folder; GUI status reported that it could not open the Shell folder and the file list was empty. The independent exact one-shot Shell helper on the same folder returned a valid 1,100-item, 1,038,279-byte reply in ~0.07 sec, ruling out child enumeration and the 1,200-entry protocol cap. The supervised host observed an exited child immediately after a partial pipe read and reported a broken reply even though unread valid pipe data remained. In migration `src/base/shell_isolated_supervisor.cpp`, the existing 4.5-second bounded reader now distinguishes child exit from stdout pipe EOF and continues only after positive bytes received, until a complete validated reply or a real truncated pipe/timeout. After Debug recompilation a fresh 1,100-file owned GUI opened the folder, displayed the first entry in 2.4sec, sorted descending to the last entry, and preserved the six real MFC settings. Initial failure fixture and the passing log `logs/m23/20260930-owned-1100-after-drain-fix.log` are retained. Pagination above 1,200 entries, unrelated SMB providers, and high DPI are not covered.


## 2026-09-30: UTF-8 test probe input and test-owned Release Assets staging

Two errors in this turn were specific to NEW Python automation, not independent evidence of product runtime defects. First, the fresh Release GUI accessibility audit contained a literally corrupted Korean filename `?.txt` after remote PowerShell-to-Python source transmission, making the test fail even though native registered type, adjustable width and file list were functional. The new test now constructs the Korean fixture name from an ASCII Unicode code point and a scoped source contract rejects that corrupted literal. Second, the initial private Release copy probe rejected the legitimate MSBuild `Assets` directory, and an intermediate probe patch accidentally imported `os` inside `main` after an earlier reference. The probe now recursively copies only the known Assets directory after reparse-point checks, validates individual file hashes and retains ordinary file packaging; `os` is imported at module scope only. The corrected private Release smoke copied 20 validated files and actually launched the owned WinUI preview with installed type text and original MFC config hashes intact. These unsuccessful probe logs remain locally ignored historical evidence, not product PASS evidence. Latest revised integrated Debug/Release GUI both pass, independent actual 1,100-item stress passes both, and original real Windows global clipboard remains untouched. See `WINUI3_M24_SCOPED_WINDOWS_INTEGRATION_20260930.md` for missing gates.

## 2026-09-30: sequential real clipboard settling and intermittent Release icon-label display

An initial test-owned real Windows Explorer and WinUI copy/cut four-direction single-session test had 3/4 completed when Explorer Cut -> WinUI Paste did not finish within the fixture timer. The fourth direction independently passed, and after the harness gated transitions on real native transfer completion and source watcher refresh the entire four-direction actual single-session retest passed, with global clipboard empty and original six MFC settings unchanged: logs/m24/20260930-four-directions-after-native-watcher-waits-debug.log. This does not independently prove a product defect. A later actual integrated Release GUI run intermittently missed the new Windows installed type label, even though both distinct Debug/Release native helper direct probes returned real TXT/PNG OS type+icon data and a copied actual Release GUI passed the registered type row. Exact cause unconfirmed. The implementation now bounds fallback to at most two individual extension lookups with a TXT priority after multi-extension batch failure. The revision-matched Release full GUI then passed in logs/winui-scoped/20260930-095439-gui-Release.log. Preserve both initial failure and eventual actual regression evidence; do not misattribute an automation timing issue or source-only check to product runtime success. Actual PNG thumbnail and isolated OS context full command execution retain independent coverage limits.

## 2026-09-30: M2.4 isolated Shell context-menu newer UIA harness (OPEN)

**Earlier successful evidence:** exact native helper enumerated 20 installed menu entries for a uniquely test-owned TXT file; a real Debug owned WinUI instance launched the isolated OS Shell popup in the matching helper PID, pressed ESC while that popup had the foreground, and left the original test file and six existing MFC settings untouched (see `logs/m24/20260930-test-owned-WinUI-native-context-popup-debug.log`).

**Later distinct failure:** the more restrictive current `test_owned_context_menu_gui.py` right-clicks inside the owned ListView's clipped viewport, then searches UIA descendants of windows belonging strictly to the owned WinUI PID for the explicit `Windows Shell isolated context menu` flyout entry. The lookup timed out even though the UIA diagnostic saw a native/system menu item: `logs/m24/20260930-final-owned-context-uiA-popup-diagnostic.log`. No reliable direct evidence distinguishes a missed app ContextFlyout activation from transient/incomplete pywinauto UIA enumeration. Retain both contradictory test observations; do not replace the failure with the earlier PASS.

**Disposition: OPEN / not a current release gate PASS.** Preserve the current exact-owned diagnostic script and failing log. Next investigation should check owned WinUI XAML flyout opening and UIA tree under the same ownership/foreground constraints, then rerun actual popup + ESC without mutating files. Do not use blind desktop coordinates or treat static source-contract PASS as a real GUI PASS.

## 2026-09-30: M2.5 lifecycle rerun stale profile and private helper file lock

**Observed harness failures:** the first M2.5 rerun stopped before mutation because fixed `isolated-*` profile folders from an earlier successful private lifecycle run still existed. After moving profile state to a new per-run directory, a second attempt completed v1 launch and v2 launch but Windows rejected the stage rename with `WinError 32`; an exact helper process launched from the private v2 directory could briefly retain a file handle after the top-level WinUI process exited.

**Correction:** every lifecycle run now owns one `lifecycle-run-owned-*` directory under the ignored evidence root. All mutable install/next/backup/fixture/profile paths are inside it. On successful completion the whole exact run directory is removed. Before an update/rollback rename, the harness waits only for processes whose executable resolves inside that exact private stage; if they do not exit within the bound, only those exact private processes are terminated. It never scans by generic process name for termination and never touches the installed product or MFC worktree.

**Retest:** prior Release-v1 ? freshly built M2.5 Release-v2 update ? exact v1 rollback ? owned uninstall PASS, with all six original MFC settings identical. This fixes test-repeatability and private-stage locking; it is not production installer certification.

## 2026-09-30: M2.5 context flyout historical miss reclassification

The M2.4 strict UIA right-click harness once timed out while looking for the app-owned Shell-menu flyout entry. No provider verb was invoked and source/settings remained unchanged. With current M2.5 layout changes and freshly compiled binaries, the same bounded row/ListView-intersection harness passed twice consecutively on Debug and once on Release, launching the exact sibling `--context-menu` helper, confirming the popup's foreground PID, and cancelling via ESC. The original failure is retained rather than deleted; direct evidence is insufficient to prove whether the earlier miss was WinUI flyout activation timing or UIA enumeration. Current launch/cancel smoke is accepted; arbitrary third-party verb execution remains outside the acceptance boundary.

## 2026-09-30: M2.6 friendly This PC literal text-pipeline corruption and UIA peer refresh

**Observed:** the first M2.6 friendly This PC address implementation compiled and displayed `? PC` instead of Korean because a long PowerShell-to-Python source-generation command had already replaced the non-ASCII source character before Python wrote the C++ file. A real full GUI run then correctly failed its new friendly-address expectation. Source inspection with `unicode_escape` proved the C++ file contained ASCII `?`, not a terminal-display artifact.

**Correction:** the C++ source now uses the ASCII-only universal character spelling `L"내 PC"` for both display and reverse address mapping. Debug and Release were rebuilt. A final owned Release visual probe read the UIA value as U+B0B4 + ` PC`, and full Debug/Release GUI subsequently passed native virtual This PC enumeration/history and existing regression suites.

**Separate bounded harness refinement:** one direct shell GUI retry also hit the known watcher/UIA replacement window after foreground acquisition. The test now reacquires the exact owned `Nested` ListViewItem immediately after focus is secured and before the physical double click. It does not retry blind desktop coordinates or weaken the native navigation assertion.

## 2026-09-30: canonical-main cutover validation races and one nonreproduced child shutdown

During final validation after relocating the accepted WinUI tree to `C:\dev\flyExplorer` / local `main`, the first source run correctly exposed a stale architecture test that still assumed `main` could only be the native baseline. The test was changed to verify ancestry of both the prior native-default `cbffb48` and accepted M2.6 `3476ecd` instead.

The first full Debug GUI timed out on the exact-owned M2.3 auto-restore child. The child/profile cleanup guards ran and the original six settings remained identical. A complete Debug rerun passed with no product-code change, so the event is retained as a nonreproduced timing anomaly rather than assigned a false single root cause.

The first Release validation reached the M2.1 duplicate-create assertion after the successful rename had already queued a native Refresh. In optimized timing, that previous Refresh could update the status after the duplicate command and hide the duplicate error string even though no overwrite occurred. The test now waits for the exact prior Refresh status before issuing the duplicate command; the real filesystem non-overwrite assertion remains mandatory.

A later Release attempt successfully restored the owned child Dark theme but that exact child returned Windows status `3221226107` during its immediate controlled shutdown. No product change was made; the final complete Release GUI rerun passed, including M2.1 create/rename/non-overwrite and M2.3 save/restore/clear. This shutdown code remains a recorded, nonreproduced anomaly rather than a claimed fixed defect.

## 2026-09-30: clean-checkout source contract depended on ignored legacy MFC staging

After the canonical-main cleanup removed ignored root `bin/` output, source validation failed because `build/test_ui_uxh06_recent_scope_contract.py` unconditionally opened `bin/x64/Languages/Korean.xml`. The file is generated legacy-MFC staging output and is not present on a clean checkout, so the source-only contract was incorrectly coupled to stale build artifacts.

The contract now always validates the tracked `src/fxfile/Languages/Korean.xml` source and its required UXH-06 keys, while validating the legacy staged copy only when that generated file exists. No production source behavior changed. Final post-cleanup source validation passed 141 tests with one environmental skip (`logs/winui-scoped/20260930-172330-source.log`).

## 2026-09-30: canonical WinUI repository move path assumptions

During the move from `experiments/phase6_winui_shell` to `app/winui` and
`tests/winui`, the first source run exposed path assumptions in the new runner
and several source contracts. The runner initially resolved its repository root
one level too shallow; after that was fixed, contracts still referred to GUI
harnesses/native fixtures as though they lived beside the app. A first fresh
compile also caught one remaining direct include of
`src/fxfile/file_operation_core.h` after that seam had moved to `src/base`.

These were repository-refactor defects, not accepted product-runtime failures.
The fixes make app/test/root paths explicit, add a canonical structure contract,
and build the shared file-operation seam only from `src/base`. Final canonical
source checks are 4/4 structure + 107/107 WinUI contracts, fresh Debug/Release
builds pass, and both full owned GUI configurations pass with original settings
unchanged.


## 2026-10-01: v6.1 validation re-observed the recorded CoreMessaging child-shutdown anomaly

During the first full Release GUI validation of the v6.1 icon-density presentation candidate, the owned M2.1 child successfully restored its Korean Dark preference and then returned Windows status `3221226107` during controlled shutdown. Windows Error Reporting identified `CoreMessagingXP.dll` with exception `0xC000027B` and underlying `0x800710DD`. This matches the shutdown anomaly already recorded on 2026-09-30; the v6.1 geometry work does not establish a new causal root.

No product patch or assertion weakening was made for this event. The same exact Release binary independently passed an owned stress gate with parent open plus three immediate child closes (child exits `0 / 0 / 0`, parent `0`, helper orphan `0`) and then passed one bounded full Release GUI rerun in 75.8 seconds, including normal owned exit and unchanged hashes for the original six user configuration files.

Therefore this recurrence is retained as a **nondeterministic unresolved lifecycle risk**, not reported as fixed and not attributed to the Medium/Small geometry change without stronger evidence.

## 2026-10-02: v7 close exposed late DispatcherQueue completion race

**Observed failure**
- The v7 owned multi-WindowTab restart/restore path completed its functional assertions, then the child or parent repeatedly exited with Windows status 3221226107 (0xC000027B).
- Windows Application Error named CoreMessagingXP.dll; WER reported combase.dll with 0x800710DD, which the installed Windows SDK defines as ERROR_INVALID_OPERATION.
- The failure became reproducible when v7 rapidly switched/restored WindowTabs and closed while file-detail/Shell work could still be finishing. It matched the signature of the earlier nondeterministic lifecycle anomaly, but this occurrence was treated as a new open defect until current-source evidence closed it.

**Cause diagnosis**
- Current source canceled detail/Shell/session work primarily from MainWindow destruction. The application keeps the window alive through shutdown, so destruction is not an early-enough boundary for dispatcher teardown.
- A detached file-detail worker did not re-check its cancellation flag immediately before DispatcherQueue::TryEnqueue; detached private-session workers also treated that enqueue as infallible.
- No persisted WER dump with a symbolic application stack was available. The causal conclusion is therefore based on the exact invalid-operation signature, the identified late-enqueue paths, and reproduction closure after changing those paths; it does not claim an internal Microsoft module root cause.

**Fix / prevention**
- Add idempotent PrepareForClose() on the WinUI Closed event so session revisions, file-detail work, transfers, Shell supervisor/watchers and search are canceled before dispatcher teardown; the destructor remains a fallback.
- Re-check file-detail cancellation immediately before enqueue and make private-session completion enqueue no-throw/best-effort when the DispatcherQueue is closing.
- Keep the v7 GUI gate asserting real process exit 0; do not convert the Windows crash code into an accepted test result.

**Integration-test follow-up**
- The first full Release reruns then failed M2.1 Korean folder creation although isolated M2.1 passed. Root cause was shared-test state: v7 returned WindowTab A at Left\Nested, and M2.1's substring address check falsely accepted that as the Left root.
- v7 now restores the initial owned folder before returning, and M2.1 requires exact normalized address equality. No product file-command workaround was added.

**Verification**
- Canonical structure: 4/4 PASS; source contracts: 125/125 PASS before final documentation checkpoint.
- Canonical Release build: PASS after the first build-runner timeout left MSBuild/link running to completion; the incremental canonical rerun completed normally.
- v7-only Release GUI: PASS, OWNED_WINUI_SHELL_EXIT 0, original six user config hashes identical.
- Isolated M2.1 Release GUI: PASS including Korean folder create/watcher and restart theme, exit 0.
- Final full Release GUI: PASS in 95.2 seconds, including v7 session restore and M2.3 private-session clear, exit 0, original six user config hashes identical.
- The failed build-wrapper run is retained as orchestration timeout evidence: it hit EXIT=124 while MSBuild/link continued and produced the candidate; it was not a compiler/linker failure.

## 2026-10-03: owned physical drag 재검증도 DragStarting 경계 미도달 — controller extraction 보류

**상태: OPEN / 자동화 경계 미확정.** 최신 main `7fdf3d4bdd222fff60c36dd9e2d19f5ac112c211`
기준으로 Release 바이너리를 다시 빌드하고, 테스트 소유 좌우 폴더와 한국어
`끌기.txt`만 사용하는 물리 마우스 drag 진단을 별도 remote Windows run으로
반복했다. 기본 재현 run `37098287271`에서는 실제 press/move/release 좌표를
전달했지만 DragStarting 진단 상태가 나타나지 않았고 파일 복사도 발생하지 않았다.

공통 GUI 단계의 일시적 실패와 진단 코드 자체의 잘못된
`pywinauto.mouse.move(..., duration=...)` 사용을 각각 제거한 뒤 isolated probe를
다시 실행했다. 최종 유효 run `37100390801` attempt 1에서는 source row가 실제
rectangle을 가졌고 `VISIBLE=True`, `ENABLED=True`, 명시적 selection이 성공했다.
그 상태에서 여러 실제 mouse move와 release를 수행했지만
`M23_DRAG_TRACE_AFTER_START`와 `M23_DRAG_TRACE_OVER_TARGET`의 StatusText는
계속 기존 `폴더를 불러왔습니다.`였고, row/ListView DragStarting 진단 문구는 한
번도 관찰되지 않았다. 16초 내 오른쪽 `끌기.txt` 복사도 발생하지 않았다.
요청에 따른 마지막 동일-SHA 재시도인 run `37100390801` attempt 2도 같은 결과를
재현했다. 두 유효 시도 모두 소유 flyExplorer 프로세스 exit 0과 원래 사용자 설정
6개 SHA256 동일을 확인했다.

이 증거는 DragOver/Drop 제품 로직의 실패를 입증하지 않는다. 해당 이벤트들까지
도달하지 못했기 때문이다. 또한 실제 사람 포인터에서도 DragStarting이 발생하지
않는다는 증거도 아니므로 제품 결함이라고 단정하지 않는다. 현재 결론은
**self-hosted pywinauto 입력으로 WinUI pointer→DragStarting gesture 경계를
인증할 수 없음**이다. 따라서 `mPrivateDragToken/mPrivateDragParent/
mPrivateDragSources/mPrivateDragRoute/mPrivateDragSide/mDropReading` ownership을
별도 controller/coordinator로 이동하는 refactor는 physical acceptance가 확보될
때까지 보류한다. 실제 사람 포인터 또는 별도 신뢰 가능한 WinUI 입력 경로로
DragStarting→DragOver→Drop 전체가 관찰되기 전에는 이 gate를 PASS로 승격하지
않는다.

## 2026-10-05: physical same-app drag gate closed after WinUI pointer-route diagnosis

**Prior state:** The 2026-10-03 entry above correctly recorded that the then-current
pywinauto gesture did not reach DragStarting and therefore could not certify the
product drag path. That OPEN result remains valid for its recorded revision and
harness.

**Resolved boundary:** Later focused diagnostics identified the WinUI gesture
boundary rather than changing FileOperationController ownership. ListViewItem
handled the press for selection, and subsequent pointer movement followed
control capture instead of the original row route. The product now observes the
handled press, polls held left-button/cursor movement at a bounded interval,
applies the Windows drag threshold, obtains the current PointerPoint by ID and
starts the documented WinUI drag path. The existing DragStarting handler still
owns DataPackage construction and source/route validation.

**Acceptance:** Remote Windows Task `37277431952` exercised real owned mouse
press/move/release in Release, reached DragOver, copied the owned Korean file
between panes, exited 0 and left all six protected user settings byte-identical.
Same-app physical drag is therefore accepted for the recorded/current product
path. External cross-application drag remains a separate interoperability gate.

## 2026-10-05: Remote Windows Task multi-line PowerShell source lost quoting through native argv

**Observed:** Remote Windows Task #422 (`37297422247`) received a multi-line
PowerShell request but child execution reported
`Stop : The term 'Stop' is not recognized` and treated a quoted
`("create-folder-shortcuts-" + $env:GITHUB_RUN_ID)` expression as an executable
token. Run #423 also showed the `Stop` corruption while later successful
statements allowed the task to finish green, demonstrating a false-green risk.

**Root cause:** The workflow passed the full `REMOTE_COMMAND` source directly as
a native `powershell.exe -Command` argument. Windows/native argument
re-tokenization did not preserve the original PowerShell quoting and multi-line
source. The child process exit-code logic itself was not the root cause.

**Fix / prevention:** The workflow now writes `REMOTE_COMMAND` verbatim to a
per-run temporary `.ps1` and invokes a fresh
`powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File` process.
The child process exit code remains authoritative, and the temporary script is
removed in `finally`. The existing workflow contract rejects a return to
`-Command $env:REMOTE_COMMAND` or `Invoke-Expression`.

**Verification:** Static/contract preflight passed 21 focused tests. The valid
candidate integration run #429 (`37302252972`) preserved
`$ErrorActionPreference="Stop"`, multi-line quoting, handled native nonzero and
product-like `try/finally` semantics, and recorded COMMAND=PASS with exit 0.
Run #428 is not acceptance evidence because its dispatch harness had already
removed quotes before the workflow received the command.

## 2026-10-05: fresh Release rebuild invalidated prior exact-build provenance

**Observed:** Remote Windows Task #434 (`37306118305`) passed request
validation, FAST preflight, runner health, packaging static checks and a fresh
Release build, then `packaging/provenance.py --check` rejected the tracked
snapshot with `tracked payload provenance does not match the current Release
runtime`.

**Diagnosis:** This was not a product/runtime defect. The previous snapshot had
been generated from a different Release build. The provenance contract hashes
the actual runtime bytes; linker/PE output from a later clean build is a new
byte set even when product behavior/source inputs are otherwise unchanged.
Therefore an older build digest must not be reused as a cross-build
reproducibility assertion.

**Correction / prevention:** The packaging instructions now make provenance
ownership explicit: after every fresh Release build, run
`packaging/provenance.py --write`, immediately run `--check`, and package
that same runtime. Do not rebuild between provenance generation and packaging.

**Verification:** Remote Windows Task #435 (`37306799266`) clean-built
candidate `1862231b271e9bb71d5adbf53439fe0d49b60af4`, generated and checked
the exact runtime snapshot, built a 326-file setup, and passed bounded
`/TESTROOT` clean install, repair, update, rollback and uninstall. The runtime
contains 305 files (17 product/generated, 288 exact NuGet byte matches) with
manifest SHA-256
`40f0f12797c6731f823dd3e438b09fc575a78a54f9962c14fb572e5d70dfdcc5`.
Clean-install, update and rollback shutdown observation all exited normally.
The accepted provenance commit is
`00f90c30800fb66f88184211442f6eeb05a950b7`.

## 2026-10-06: release-source acceptance failed after validation because evidence path variable was nonexistent

**Observed:** Remote Windows Task #439 (`37375579827`) completed clean Release
build, exact runtime provenance, setup packaging, deterministic source bundle
generation/check, release identity generation/check and the full bounded
installer lifecycle. It then failed in the acceptance harness at
`Join-Path $env:FLYEXPLORER_REMOTE_EVIDENCE_DIR ...` because that environment
variable is not part of the Remote Windows Task contract.

**Classification:** Control-harness defect, not product/package/source failure.
The workflow-owned evidence root is
`$env:FLYEXPLORER_CANONICAL_CHECKOUT\logs\remote-evidence`.

**Fix / prevention:** The successor request writes release-source evidence under
the workflow's canonical evidence root rather than inventing a second
environment variable. Future custom evidence producers should derive their path
from `FLYEXPLORER_CANONICAL_CHECKOUT\logs\remote-evidence` unless the
workflow explicitly exports another contract.

**Verification:** Remote Windows Task #440 (`37376305779`) changed only the
evidence destination and completed with REQUEST_VALIDATION, STATIC_PREFLIGHT,
RUNNER_HEALTH and COMMAND all PASS. The private artifact contains the concrete
setup, deterministic source ZIP, source manifest, runtime provenance and release
identity; the accepted record commit is
`28e361e8d9f3ed796abe7f69a4f301ae6e52a002`.

## 2026-10-06: outbound StorageItems drag accepted; same-app regression harness repaired

**Implementation boundary:** The accepted explicit row drag keeps
`FlyExplorer.M23.OwnedListDrag.v1` for same-app route/replay validation and
also projects filesystem selections to public Windows `StorageItems`
asynchronously under `DragStartingEventArgs.GetDeferral()`. The public
requested/allowed operation is Copy only. A public projection failure does not
invalidate the already-created private payload.

**External acceptance:** Remote Windows Task #464 (`37399608114`) on product
revision `0d23048d47b158b98c2aff0cf7f3ec5ffc8c5ebb` passed FAST and the
canonical Release build, opened one uniquely identified test-owned Windows
Explorer destination, then performed a real mouse drag from flyExplorer.
`REAL_OUTBOUND_STORAGEITEMS_EXPLORER_COPY=True`,
`REAL_OUTBOUND_DRAG_SOURCE_PRESERVED=True`, and
`OUTBOUND_DRAG_EXPLORER_ACCEPTANCE=PASS` were observed before the run later
failed in a separate same-app regression fixture.

**Regression-fixture boundary:** The first focused same-app successor #465
(`37400174960`) failed before drag because its synthetic pane routing did not
re-establish the owned source row
(`owned source row disappeared after pane routing`). Product code had not
changed after #464. The successor changed only the test harness to explicitly
route and verify both owned panes before physical input.

**Closure:** Remote Windows Task #466 (`37400834524`) kept the accepted P2
product code unchanged and passed Release build plus real private-token
cross-pane drag with
`REAL_SAME_APP_PRIVATE_DRAG_COPY_AFTER_OUTBOUND_SUPPORT=True` and
`SAME_APP_DRAG_REGRESSION_ACCEPTANCE=PASS`. This closes the concern that
adding public outbound StorageItems weakened the existing private same-app drag
path. Explorer is the concrete external acceptance target; Desktop and arbitrary
third-party targets are not separately claimed as GUI-certified.

## 2026-10-20: desktop-only Visual Studio installation passed WinUI preflight

Resuming G02/G06 on main `220e949f`, the first canonical local Release build
completed the Shell helper and NuGet restore, then failed with `MSB8036` in
`CppWinRTVerifyKitVersion`. SDK 10.0.26100.0 and the v145 compiler were present.
MSBuild evaluation instead reported `TargetPlatformVersion=7.0`, empty SDK
paths and no VC platform because the selected VS 18 installation lacked its
`Application Type/Windows Store/10.0` C++ imports. This was an environment
failure, not evidence of a keyboard or product defect.

The app build now calls the shared resolver with `--winui` before helper build
or restore. It checks the Store defaults, x64 platform and v145 toolset imports
within one VC root and names the missing Installer component. Native/helper
resolution keeps its existing desktop-only requirements. Six behavioral tests
cover desktop-only, complete, incomplete, old-toolset and split-root layouts,
plus the app-only opt-in. The 18 build-environment and six installer contracts
passed; Python static checks passed. Actual pre-install app preflight exited 3
with the correct component diagnostic. The user approved adding
`Microsoft.VisualStudio.ComponentGroup.UWP.VC`; the Installer required manual
UAC elevation, completed with logged exit 0, and real `--winui` preflight passed.
This does not establish G02/G06 GUI or visual acceptance.

## 2026-10-21: folder-tab activation destroyed keyboard focus

On the locally rebuilt `220e949f` baseline, PaneTab Left/Right+Enter called
`Refresh()`, whose `RefreshTabs()` cleared and recreated every item. WinUI
moved focus to the next control, the Name sort button, so the next Enter
sorted instead of selecting the adjacent folder tab. The BEFORE image and
settled second command distinguish this from the tool's stale FileNameBox
focus report. Reusing surviving TabViewItems and writing SelectedIndex only
when needed fixed the observed path. Release, 25 related source/harness tests,
actual two-workspace/four-pane keyboard traversal, matched Dark screenshots
and owned exit 0 passed. Full binary identity, scope and remaining G02/G01
limits are recorded at the top of CURRENT_STATUS.md. No startup focus hack
or shutdown workaround was added.

## 2026-10-21: private-session native gate still expected v3 after v4 migration

The current native session fixture compiled but returned 34 passed / 1 failed:
f01_private_session_v3_wire_written expected byte 8 to be 3 while the product
correctly wrote v4. The display-options source contract also referenced encodeV3.
Correct those expectations rather than reverting the v4 writer. Expand runtime
coverage with distinct per-tab sort round trips and independently composed v2/v3
streams, including sort inheritance, selected paths/history and display flags.
The Release native gate then passed 41/41; related display/session source checks
passed 15/15. Test-owned profiles and existing legacy settings were preserved.
This native result does not certify real legacy GUI restore or resolve G01's
intermittent shutdown risk. No product implementation change was required.

## 2026-10-21: installed tests package shadowed source contract execution

The standard harness used python -m unittest with tests/winui/... file selectors.
On this host an unrelated site-packages/tests/__init__.py won package resolution,
so every selected contract failed to import tests.winui before running. This is a
harness/environment collision, not a product failure. run_source_contracts.py now
loads each selected file explicitly with a distinct module identity and preserves
sibling import paths while tests run. Regressions cover the ambient tests package,
duplicate basenames, lazy imports, empty files, missing/outside paths and error
propagation. Standard harness 43/43 and related Shell/streaming 19/19 passed.
One new lazy-import fixture initially contained literal backslash-n instead of
line breaks; that fixture encoding was corrected before the final acceptance.
The existing real helper process/recovery regression also passed after its wire
client extraction. The new G08 benchmark is native IPC timing, not GUI acceptance.

## 2026-10-21: Windows minidump directory includes repeated unused slots

The first owned-helper dump collector wrote a native dump but its new validator
rejected duplicate UnusedStream directory slots as duplicate data. This was a
diagnostic parser defect, not a product or dump-writer failure. Ignore type-zero
placeholders while retaining real-stream uniqueness, directory bounds and required
thread context/stack checks. Add an explicit repeated-unused-slot regression.
The materially changed parser then validated an actual blocked helper: four
threads, contexts and stack buffers, target still alive, owned recovery and cleanup
PASS. Eight focused, 51 standard harness and 16 related source checks passed.
No real WinUI hang or symbolic root cause is claimed; the shortcut GUI timeout hook
awaits a real recurrence. Raw test dump removed; future raw dumps stay local/ignored.
