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
