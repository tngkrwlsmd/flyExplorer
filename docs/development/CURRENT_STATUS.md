# PX01 owned Properties GUI oracle exit/privacy accuracy — 2026-10-23

- **Test-harness-only hardening:** in `tests/winui/test_owned_context_properties_gui.py`, the owned GUI oracle now requires an actual WinUI process **exit code 0** for its final PASS and successful test-fixture retirement. A forced termination or abnormal exit can no longer be misreported as accepted. The same guard is asserted in the narrow source regression `test_late_selection_gui_oracle_is_owned_and_observable`.
- Removed `ImageGrab.grab(bbox=...)` from this **functional** oracle because a rectangle screen capture can include unrelated overlapping desktop content. The dialog is still verified by test-owned window/process identity, UIA visibility and geometry; no visual/pixel PASS is claimed.
- Exact test/source SHA `3c87b82ae114e1a053480fdbda618314f9fabe11`: [central Windows one-off #39885610745](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39885610745) **1/1 focused source contract PASS**, **3/3 Python syntax files PASS**, owned temporary checkout retirement PASS; no native Release build, interactive GUI or pixel verification was run. Remote Shell request slot was restored to idle after completion.
- **Pending:** run only the approved isolated `context-selection` interactive GUI area when such an authorized route exists. The current central registered scopes do not execute that area, and broad `gui`/`gui-probe` must not be mislabeled or substituted. The earlier PX01 product-source selection guard still lacks native-build/GUI acceptance; G01 remains unresolved and reproduction-deferred, G03–G05 excluded and G07 stopped.

---

# PX01 owned Properties selection-lifetime GUI oracle — 2026-10-23

- Added one **test-only** GUI oracle in
  `tests/winui/test_owned_context_properties_gui.py`: invoke only the
  positively identified built-in Properties verb for disposable files A+B,
  change the test-owned WinUI selection to A+C while the exact owned
  Properties window is still open (same count, different item set), close
  only that verified owned window, and ensure the delayed Shell response
  does not replace the new selection's status. Includes exact-process
  checks, original file hash preservation, bounded UIA polling and cleanup.
- Registered the `context-selection` area in
  `tools/winui/run_checks.py` for an eventual **single focused GUI run**.
  This does not claim that central CI's existing `gui-probe` profile
  executes this case.
- Added `test_late_selection_gui_oracle_is_owned_and_observable` to the
  source contract; Windows [#39882780540](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39882780540)
  at source `42400ccec2b0720a3d965921db5193852130a11c`:
  **1/1 PASS**, three Python files compiled without syntax errors and
  isolated temporary checkout retirement PASS. An earlier
  [#39882611485](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39882611485)
  attempt failed *before* test collection owing to PowerShell
  single-entry array unwrapping; corrected without re-running unrelated
  methods.
- **Native Release build and actual interactive GUI acceptance for this
  revision remain UNVERIFIED.** Adding a new central GUI validation scope
  was not authorized by the control-plane tool safety gate, so no
  broad/incorrect GUI profile was substituted and the project was not
  reported as accepted. The existing external-menu ownership guard has
  3/3 targeted **source-contract** PASS at `c8dbfe9009...`.
  The new probe can be run only through an approved isolated interactive
  path, and only for synthetic test-owned files; do not run unrelated suites.
- G01 remains open/reproduction-deferred by user instruction; excluded
  G03–G05 and stopped G07 remain outside the test scope.

---

# PX01 external Windows context menu selection-ownership guard — 2026-10-23

- **Scope:** changed only the delayed external Windows Shell context-menu
  completion status guard in `app/winui/m22_transfers.cpp`; retained the
  accepted multi-selection right-click preservation, explicit Explorer
  fallback, helper isolation, no automatic external command invocation
  and the existing context-menu 32-item/16K UTF-16 budget.
- **Observed code gap:** completion previously verified active WindowTab,
  PaneTab, route and visible folder, but not whether the user had since
  changed the selected files *within that same tab/folder*. A delayed
  native popup could overwrite the current selection's status.
- **Fix:** snapshot the bounded original selected filesystem path set,
  sort for order independence and keep it with the worker completion.
  Before applying delayed UI feedback, revalidate the currently selected
  item count and resolve current selected entries through the same active
  PaneTab model; suppress feedback if identities/paths differ or the
  tab has begun a new pending navigation.
- **Focused source contracts:** exact code/test SHA
  `c8dbfe90099b2c12bf550ff600575f25346f31bd`,
  [Windows #39878343686](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39878343686)
  — **3/3 PASS**: isolated native menu process boundary, distinct
  workspace/route guard and original selection membership guard.
  Scoped scratch clone retired. **No new WinUI native build, binary,
  GUI or pixel test was performed** for this product code revision;
  those gates remain **unverified**, not failed or passed.
- **UX boundary:** this is status ownership protection, not claim of
  full Windows 11 context-menu command/extension parity. Existing L06
  multi-select preservation remains based on prior accepted evidence.

---

# G01 all-profile startup-only Windows diagnosis — 2026-10-23

- Reproduced the **original integrated suite's pre-start test conditions**
  (same owned M19/M20/M21/M22/M23/V7 fixtures and feature flags), but stopped
  after one existing 18-second startup predicate had seen **both** the owned
  folder path and the actual `Nested` entry in the **left** WinUI file list.
  No later tab/search/file-operation GUI interactions, G03–G05 or G07 tests
  were replayed.
- Exact product source `63c61237aa3c184ef534d83383b1be36cfe859a7`.
  The focused Windows source [#39873451885](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873451885)
  passed 3/3 G01 startup harness/private-redaction tests and the AST syntax
  of the three edited Python files; no binary build/GUI was run there.
  Central [Quality #39873299998](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873299998)
  passed after updating the exact-tip-only Git checkout contract.
- One real targeted Windows [`gui-startup` run #39873813652](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39873813652)
  **PASS**: `runner-health` 647 ms; GUI dependencies 173 ms;
  Release build 184,302 ms; `gui-startup-integrated-Release` exit 0 in
  approximately 3.6 s; `functional-g01-startup-diagnostic` PASS in
  3,981 ms; `NOT_FINAL_ACCEPTANCE=1`. A positive fixture-visibility
  marker is required by the harness before it can succeed.
- This **did not reproduce the intermittent G01 failure**. The run does not
  reproduce the historical *sequence* of earlier unrelated GUI test processes,
  nor certify full integration, user-visible visual fidelity or installer.
  Treat G01 as **OPEN**, do not patch native Shell logic without failure
  evidence and do not raise helper/GUI deadlines.
- A separate central maintenance correction was required because the
  newly registered `gui-startup` scope was initially unrecognized by the
  workspace retirement metadata allowlist. Its bounded, exact-target
  retirement is a separate operational step, not a product GUI regression.

---

# G01 exact-main Windows Release + focused GUI probe — 2026-10-23

- User authorized scoped live Windows verification. Ran **one** registered
  `desktop-a` central `scope=gui-probe` at exact product SHA
  `871caab7fb4729da0dffb1b08b56da2cae6b0250`:
  [central run #39871105711](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39871105711).
- Direct Windows job evidence: runner-health **PASS** (1,003 ms),
  GUI dependencies **PASS** (240 ms), Release build **PASS**
  (197,545 ms), targeted `gui-core-Release` **PASS**
  (37.1 s, exit 0); `functional-gui-diagnostic` **PASS**
  (37,547 ms). The central job concluded success, with
  `NOT_FINAL_ACCEPTANCE=1`.
- The initial Shell route failure **did not recur in this one focused**
  startup observation. This is not an integrated `gui-all` acceptance:
  the historical failing full-profile run used additional owned GUI
  feature flags. No new failing `Startup/sampled_transitions` exists,
  and no root cause or intermittent recovery resolution was shown.
- The central cleanup archived bounded owned evidence, then retired the
  verified ~3,236,461,965-byte scratch workspace. No current product
  code or user settings were changed by the probe.
- Do **not** repeat all GUI scopes merely to seek a green G01 result.
  If the original startup failure is observed again in an authorized,
  exact-SHA test-owned integrated scenario, use redacted bounded
  startup transitions to locate the failed stage. G01 **OPEN**.
  G03/G04/G05 remain excluded; G07 remains stopped.

---

# G01 startup failure-only route sampling — 2026-10-23

- **Purpose:** classify an intermittent startup-left-pane failure without
  guessing at a Shell implementation fix, adding retries, or increasing
  the native helper 4.5-second-per-attempt and GUI 18-second deadlines.
- **Changed only the G01-owned GUI test/evidence harness:**
  `tests/winui/test_shell_gui.py` samples only bounded
  `elapsed_bucket` (2-second bins), address route
  `empty/owned-left/other` and fixed Shell status category while the
  **existing** startup condition is polled. It keeps 16 transitions at
  most (first three plus recent ones) in memory.
  `tests/winui/gui_failure_evidence.py` serializes only allowlisted
  fixed codes into `panes.json/Startup/sampled_transitions` when that
  **exact** startup assertion fails. Other failures never receive the
  timeline. Arbitrary status strings, user paths and raw UIA text are
  not logged by this feature.
- **Exact source test SHA:**
  `5c1eec5428121b4a8d1655222ead6ce616dbbd1a`.
  [Windows run #39870020233](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39870020233)
  showed **3/3 focused evidence source-contract methods PASS**.
  Its final AST check command failed because a Windows PowerShell
  command-line quoting bug stripped the Python encoding string.
  Corrected **AST-only** invocation
  [Windows run #39870209119](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39870209119)
  showed `FLY_G01_STARTUP_POLL_AST=PASS`, correct exact checkout, no
  native build or GUI and clean scoped scratch checkout retirement.
- **State:** G01 remains **OPEN**: the original failed
  [integrated run #39732505243](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39732505243)
  predates the timeline and cannot retroactively be classified.
  No actual recurring left-pane failure or shutdown hang was
  reproduced, and no new binary has been built. On a genuinely
  justified same-scenario recurrence, compare the new categorical
  state transitions to the active native request route before changing
  implementation. Avoid blanket GUI loops. G03/G04/G05 excluded;
  G07 stopped.

---

# flyExplorer current development status — 2026-10-23

## Product and source boundary

- The active application is the C++/WinRT WinUI 3 dual-pane Windows file
  manager in `app/winui/`, with shared native code in `src/base/`,
  an owned isolated Shell helper, and tests in `tests/winui/`.
- Build/project inventory: all **55 current native C/C++ translation units**
  under the active app and native-core scopes are registered in at least one
  active app/helper/native-test compilation project. The **32 native-core
  headers** have recorded includes or explicit project references.
  This is a source-reference audit, not an assertion that every potential
  runtime code path executed in a fresh binary.
- History-only Python Git-object access and its associated source-inventory
  contract have been removed. Structural checks now inspect the current
  app and the active `src/base` files without requiring old Git commits.
- Personal-use private installer continues to use runtime provenance,
  precise manifest ownership, safe uninstall and actual NuGet/package
  license and NOTICE inputs. The independently bundled policy library and
  actively used Fluent icon attribution remain. No public publication,
  signing or redistribution objective is active.

## Latest focused verification

- Product changes: current-only structural tests, shell architecture
  assertions, isolation helper and neutral installer identity; no
  unrelated function or full application suites were re-run.
- Exact product source `8e01ddc1971ab6639a78ae0b0204784a20bff5e5`.
- [Windows source test #39864992776](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39864992776):
  **7/7 affected source contracts PASS**; execution then stopped because a
  scoped runner pointed unittest discovery at the wrong helper-test folder.
  The owned temporary clone was retired.
- [Windows source test #39865469684](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39865469684):
  the **remaining 3/3 tests PASS** after distinguishing native Python
  stderr from process failure. Exact source revision matched; scratch
  checkout retired. **Total changed-contract evidence: 10/10 PASS.**
- Prior Windows [Release #39779111032](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39779111032)
  at `5cf79f56b27e7d86a1fd82cc6ae171d75e04d98e` passed its then-current
  Release build; that is **not** a build of the latest code.
- Prior integrated [GUI #39739943824](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39739943824)
  applied to `74bd0f3376d34b934f059b093c014fa469447606`, **not** the
  current latest source. No current revision full GUI/pixel validation
  or installer lifecycle has been claimed.

## Product gaps and verification limits

- Full Windows 11 File Explorer behavioral/UX equivalence is **not**
  established. Refer to `WIN11_PARITY_REAUDIT_20261022.md` PX01–PX18
  and `EXPLORER_PARITY_REQUIREMENTS.md` for the existing categorized
  requirements and current evidence boundary.
- G01 intermittent initial navigation/shutdown cause remains **OPEN**.
  It must not be described as permanently solved by one functional PASS.
- G03 real DPI 125/150/200, G04 spoken Narrator/high contrast,
  G05 real USB/SMB/UNC are user-excluded; G07 real IME work is stopped.
  Their earlier unverified status is not permission to rerun them.
- Only test the changed feature and transitive dependencies; re-use
  exact-source evidence for unaffected behavior. New builds, full GUI,
  visual matching and installer/package operations require a justified
  scope and their own acceptance; do not silently include them.

## Technical information sources

- `AGENTS.md`, `docs/development/VERIFICATION_PROFILE.md`,
  `docs/development/AGENT_EFFICIENCY.md` — validation instructions
- `docs/development/NEXT_DEVELOPMENT_GOALS.md` — prioritized open goals
- `docs/development/EXPLORER_PARITY_REQUIREMENTS.md`,
  `docs/development/WIN11_PARITY_REAUDIT_20261022.md` — parity gaps
- `docs/development/UI_UX_AUDIT.md` and `ERROR_HISTORY.md` —
  targeted experience findings and failure diagnostic context
- `docs/development/PRIVATE_PACKAGING_VERIFICATION_20261023.md` —
  exact-source private installer input checks

Historical development evidence is not a substitute for acceptance of the
latest source or binaries; active requirements and the actual owned tests
always control.
