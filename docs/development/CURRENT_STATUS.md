# flyExplorer — current project status (2026-09-24)

**Purpose:** Fast, current-state entry point for maintainers and development
agents. This is an evidence-labelled summary, not a replacement for source,
build scripts, the project policy, or an independently executed test.
Update this page after each logical work unit that changes its facts.
For the chronological diagnosis and original evidence, retain and use
[`ERROR_HISTORY.md`](ERROR_HISTORY.md) rather than moving/deleting entries.

## Active baseline and verified scope

| Subject | Current observed state | Evidence limit |
| --- | --- | --- |
| Product | fxfile/flyExplorer 2.0.4-dev; Windows 10/11 active development; native Release-x64-Unicode is the default build path | Not a formal minimum-OS or general release compatibility guarantee |
| Build system | Visual Studio 2026/v145, GYP-generated solution, repo-local build/preflight scripts | No fresh x64 compile of this current documentation/cleanup revision |
| Earlier local x64 test | On the parent of product commit `6b18c58f` plus then-uncommitted OS-rendering fix: Release x64 compile/link PASS and native functional tests 17 passed / 0 failed | Overall PASS WITH SKIPS; startup smoke skipped for user HKCU preservation; not a revision-matched test of current `main` |
| Dark/Light/High Contrast UI | Theme selection and `osWinModern` rendering route implemented in source | Post-fix actual Windows 10/11 visual/screenshots and interaction acceptance remain NOT TESTED |
| Help / portable completeness | Canonical `docs/htmlhelp/` source and `build/rebuild_htmlhelp.py`; both direct portable and installer entrypoints now rebuild CHM. All three portable variants stage CHM, application/third-party license notices, readme, legacy history and available custom icon bitmaps. Package validator requires and checks CHM signatures in each ZIP and staging tree. | Static script-contract inspection only; Windows HTML Help Workshop compilation, package/ZIP generation, installed/portable Help commands: NOT TESTED |
| User guidance | `Html/current_development.htm` is the current source-grounded guide; old detailed reference pages are retained with prominent legacy entry-point labels | Full per-topic source/runtime rewrite still OPEN; track it in [`HELP_CONTENT_AUDIT.md`](HELP_CONTENT_AUDIT.md) |
| Distribution | Installer now distinguishes application GPL notice and separately installs current `CREDITS` as third-party notices | Bundled third-party permissions, particularly GFL SDK, and public redistribution compatibility: NOT VERIFIED; see [`DISTRIBUTION_LICENSE_REVIEW.md`](DISTRIBUTION_LICENSE_REVIEW.md) |
| GitHub Actions | Manual workflow-only; each actual run requires a separate explicit user instruction with no expiry to this restriction | No Actions invoked in documentation/vendor/help cleanup |
| Updater metadata transfer | A new 256 KiB overflow-safe transfer budget and truthful disk-write callback result prevent oversized/partially written metadata from being reported as a successful libcurl transfer. Basic connect/total timeouts and HTTP error reporting are configured. | Pure helper's 9 boundary cases passed an isolated Linux C++11 compile; Windows x86 updater build/real server/disk-failure integration: NOT TESTED. Existing hard-coded HTTP endpoint and unsigned metadata remain security blockers. |
| Prior repository cleanup | Removed unused `gtest` (41) and `libxslt` (52) files, 16 byte-identical zlib binaries, 113 non-build NSIS developer assets, plus 4 dead root HTML frameset inputs | Source and Git tree inspection only; fresh Windows compile/package and external manual consumer checks NOT TESTED |

**Do not call the application/runtime defect closed based solely on source or
static checks.** The last product code OS-routing fix remains
`CODE FIXED / POST-FIX VISUAL RETEST REQUIRED` until the reported Windows
Light/Dark/High Contrast acceptance scenarios are reproduced successfully.

## Outstanding near-term work

1. In a Windows development environment, run the authorized local static
   preflight and current x64 compile/regression, regenerate and inspect
   the CHM, and validate the current installer in an isolated environment.
   Keep compiler, visual, runtime, installer and third-party licensing
   evidence separate. Non-default x86/release/full profiles need user
   scope expansion; hosted Actions need per-run explicit approval.
2. Source-check the legacy help detail pages against the actual
   application menus, language packs, settings tree, shortcuts and
   screenshots before claiming them current. No speculative remapping.
3. Verify/update the updater's hard-coded cleartext HTTP endpoint, installed libcurl TLS capabilities, signed release-metadata/download integrity and actual deployed server before enabling a release-grade update trust chain. The bounded-transfer fix alone does not authenticate metadata.
4. Audit exact GFL SDK redistribution permissions and all included
   third-party binary provenance/requirements before public packaging.
5. Decide whether old `dist/history.txt` belongs in future installers.
   Until changed, ship it with an explicit **historical releases only**
   header; do not transform or delete its original history.
6. Consider dependency ABI, updater x86 isolation and VLD release
   staging only with direct build/package verification and
   the architecture limits in the dependency audit.

## Documentation ownership and history

| Owner document | Responsibility |
| --- | --- |
| `README`, `LOCAL_CI_MANUAL.txt` | Public-facing developer build, test and packaging procedures |
| `AGENTS.md`, vendored `.agent-policy/` core | Required agent rules; vendored policy core is not edited for project facts |
| `.agent-policy/PROJECT.md` | Project-specific facts, reviewed-path snapshot, individual work items and live handoff requirements |
| **This page** | Concise live summary of completed work, open decisions and evidence limits |
| `ERROR_HISTORY.md` | **Preserved, append-only historical evidence**, including context-specific test outcomes and errors |
| `DEPENDENCY_ARCH_AUDIT_20260924.md` | Current inventory summary followed by the immutable dated audit and cleanup checkpoints |
| `HELP_CONTENT_AUDIT.md` | Current help scope, legacy detailed-topic inventory and Windows user-help acceptance tasks |
| `DISTRIBUTION_LICENSE_REVIEW.md` | Observed license contradictions and unfinished third-party distribution checks |
| Root `LICENSE` and `CREDITS` | Existing application and third-party license notices; never rewrite on the basis of assumptions |

When source, build output or runtime evidence contradicts a summary,
correct this page and `PROJECT.md` during the same logical work unit.
Keep the historical evidence that led to earlier conclusions intact.
