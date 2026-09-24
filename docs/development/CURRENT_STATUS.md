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
| Build system | Visual Studio 2026/v145, GYP-generated solution; fresh `local_ci.bat x64` on product revision `bee95d9`: source preflight, Release x64 compile/link PASS; native functional regression 16 passed / 0 failed | PASS WITH SKIPS: automated runtime smoke skipped to preserve existing HKCU state; clean-profile startup NOT TESTED |
| Historical user-supplied x64 log (2026-09-24, `bc02a4a`) | Former native updater test compiled with a Windows `max` macro collision and that run FAILED. That entire updater feature/test is now removed by explicit owner choice. | Superseded for current compile evidence by the post-removal `bee95d9` x64 PASS. Preserve the old failure as historical evidence. |
| Earlier local x64 test | On the parent of product commit `6b18c58f` plus then-uncommitted OS-rendering fix: Release x64 compile/link PASS and native functional tests 17 passed / 0 failed | Overall PASS WITH SKIPS; startup smoke skipped for user HKCU preservation; not a revision-matched test of current `main` |
| Dark/Light/High Contrast UI | Actual Windows 11 inspection of `bee95d9`: original main-menu/toolbar/drive/bookmark Dark text now readable. UI-01 source now snapshots HWND visibility and only freezes/thaws windows that were visible before a theme transaction, preventing redraw-enable from exposing hidden settings pages. | UI-01 exact settings-page sequence on this source revision: NOT RETESTED. Bright Dark scrollbars, mixed search-dialog colors and the remaining UI/UX audit findings stay OPEN. Windows 10, High Contrast and mixed-DPI remain NOT TESTED. |
| Help / portable completeness | Canonical `docs/htmlhelp/` source remains the build input. Full packaging now validates 39 required runtime payloads across the three existing architectures before staged replacement, reserves the previous staged bin for rollback during activation, generates the installer before portable extras and clears partial/stale release outputs on failure; archives still carry fresh CHM and notices. | Static code/path inspection only; Windows directory-rename/rollback injection, HTML Help Workshop, NSIS/ZIP execution and installed/portable Help: NOT TESTED. |
| User guidance | `Html/current_development.htm` is the current source-grounded guide; old detailed reference pages are retained with prominent legacy entry-point labels | Full per-topic source/runtime rewrite still OPEN; track it in [`HELP_CONTENT_AUDIT.md`](HELP_CONTENT_AUDIT.md) |
| Distribution | Personal/local use only is the current owner's intent. Root GPL and third-party CREDITS notices remain unchanged and bundled; installer/portable paths now reject partially copied or missing release files. | No public redistribution permission is claimed. Third-party permissions (especially GFL) remain UNVERIFIED; Windows package generation on this revision NOT TESTED. |
| GitHub Actions | Manual workflow-only; each actual run requires a separate explicit user instruction with no expiry to this restriction | No Actions invoked in documentation/vendor/help cleanup |
| Automatic updates | **REMOVED FROM SOURCE AND NEW PACKAGE DEFINITIONS:** retired checker project/network dependency, application startup integration, update settings/About download, native updater regression and packaging payload. | Post-removal x64 compile/regression PASS at `bee95d9`; old-install migration and full packaging NOT TESTED. Existing startup values were preserved. |
| Prior repository cleanup | Removed unused `gtest` (41) and `libxslt` (52) files, 16 byte-identical zlib binaries, 113 non-build NSIS developer assets, 4 dead root HTML frameset inputs, plus the retired updater module, dedicated libcurl vendor tree and obsolete generated project files | Post-cleanup x64 compile/regression PASS at `bee95d9`; packaging and external manual consumer checks NOT TESTED |

**Do not call all runtime defects closed based on a build or a narrow visual
check.** Original main Dark text acceptance was visually rechecked on Windows
11; the separate settings/search/scrollbar findings remain OPEN. The dated
audit records the exact product revision, executable hash and untested cases.

**2026-09-24 follow-up source-only checkpoint:** UI-03 nested search
ComboBox Dark color forwarding, dropdown list retheming and a wider localized
current-folder button are now in source. UI-07 new-profile defaults expose the
existing single-tab strip and new-tab button without changing saved settings.
These are partial changes; Windows build, runtime/visual, DPI/HC, search
behavior and a newly added close-tab glyph still require revision-matched
Windows runtime/visual acceptance.
UI-02/UI-05/UI-06 remained unchanged in that checkpoint;
UI-08 receives a separate new-profile-only partial change below. Prior `bee95d9`
build evidence does not apply to this new revision.

**Additional UI-07 source checkpoint (2026-09-24):**
The existing custom tab control now reserves a DPI-scaled close target
for sufficiently wide tabs and paints a palette-backed close glyph on
the selected or hovered tab. Pointer release within the same tab uses
the existing tab-close command/confirmation path; the existing localized
close command string supplies its tooltip. Existing keyboard shortcuts,
tab indices, old profile options and high-contrast palette routing are
retained. This is source work only: compile, release-on-close behavior,
narrow layouts, hover/focus and actual final pixels are NOT TESTED.
UI-07 remains OPEN until Windows acceptance.

**Additional UI-08 source checkpoint (2026-09-24):**
The already-supported shared folder-tree mode becomes the default for
new profiles, avoiding duplicate trees when a user splits the view
vertically. Existing saved pane configurations, individual-tree mode,
folder-tree visibility controls, file lists, shortcuts and information
panels remain available. This is a limited initial-layout change, not
dynamic narrow-pane adaptation. A source guard confirms the existing
shared/per-view owner paths. Current-revision Windows build, clean-profile
first launch, split-pane resizing, layout persistence and visual evidence:
NOT TESTED. UI-08 remains OPEN for the broader acceptance case.

**Follow-up UI-08 source checkpoint (2026-09-24):**
Fixed the existing command-line split-column override: it had assigned
`sRowCount` instead of `sColumnCount`. The explorer-style Contents
sidebar now adapts to current pane width and DPI, reserving approximately
280 logical pixels for file columns where available; very narrow panes
share their remaining width without a negative list rectangle. The
Contents window, all displayed data, user-selected mode and individual
tree option remain intact. This is source/layout work only: the actual
Windows x64 build, command-line launch, splitter dragging, layout
persistence, light/dark/mixed-DPI and accessibility: **NOT TESTED**.
UI-08 remains **PARTIAL / RUNTIME RETEST OPEN**.

**UI-06 menu-height / client-background source checkpoint (2026-09-24):**
BCMenu app-owned popups and their pre-existing submenus now use the
documented `MENUINFO` max-height setting based on the popup monitor's
work area so Windows can provide native overflow scrolling without
dropping commands. In Dark/non-High-Contrast only, an elevated palette
brush covers the native client background; original menu settings
are restored and the transient brush is destroyed when tracking ends.
High Contrast and shell-owned context menus are not recolored.
**Native non-client outer menu frame color is still OS-owned** and
must not be claimed fixed from the client background alone.
Current-revision Windows compiler/runtime (small-monitor overflow,
keyboard/submenu, Light/Dark/HC screenshots): NOT TESTED. UI-06 remains
**PARTIAL / VISUAL RETEST OPEN**.

**UI-05 default command-band / settings spacing source checkpoint
(2026-09-24):** On a fresh profile the bookmark band no longer forces
a separate rebar row after the drive band. Both retain their chevrons,
normal narrow-window wrapping and explicit user-configurable multiline
modes. Previously persisted band order/BREAK settings still restore
from the existing coolbar file. Settings navigation row minimum rises
from 34 to 38 DPI-scaled units; separation between the description
and body rises from 12 to 16, without expanding overlapping controls
inside fixed legacy resources. A static contract guards the default
band flags, persistence and metrics. Other command grouping and
per-dialog control spacing require visual design/test; UI-05 is
**PARTIAL / WINDOWS VISUAL RETEST OPEN**.

**UI-06 chevron-popup position/paint follow-up (2026-09-24):**
The app-owned custom toolbar overflow popup now clamps to the anchor
monitor's *work area* (multi-monitor/taskbar aware) instead of the
entire desktop, and uses the correct left coordinate when choosing
horizontal placement around an excluded control rectangle. Its
`CWindowDC` now has one RAII release rather than an extra manual
`ReleaseDC`. A negative source regression guard covers both bugs.
Actual current-revision Windows build, large custom popups taller
than the available work area, keyboard/hover, taskbar on alternate
edges, multi-monitor DPI and final border pixels: **NOT TESTED**.
UI-06 remains **PARTIAL / RETEST OPEN**, and OS-owned native menu
outer border is intentionally untouched.

**UI-03 native location text inset (2026-09-24):**
The search dialog now sets a documented `EM_SETMARGINS` left inset
on its actual nested ComboBoxEx edit HWND, scaled to the current
dialog DPI. It reapplies the inset after the base dialog DPI-change
handler, leaving native location icons, right margin, text selection,
autocomplete and horizontal scrolling intact. A source wiring guard
checks init/DPI pathways. This is not proof that the Dark nested edit/
dropdown is visually correct; focus/hover/keyboard, location search,
OS High Contrast and mixed-DPI screenshots are **NOT TESTED**.
UI-03 remains **PARTIAL / RUNTIME VISUAL RETEST OPEN**.

**UI-01 one-page visibility reinforcement (2026-09-24):**
Settings navigation now hides every other *created* page rather than
only the previously selected index. Following synchronous theme/config
notification, it reasserts the selected-page visibility contract,
showing the selected page only if the HWND is unexpectedly hidden.
Own WS_VISIBLE flags are checked independently from ancestor visibility.
The existing theme transaction snapshot remains in place, and saved
settings, navigation IDs, modified flags and focus handling are not
intentionally changed. A negative source guard rejects the old
selection-only hide loop. The exact Windows sequence (General ->
Appearance -> Light -> Apply -> Filtering), focus preservation,
repeated switches and current-revision x64 compilation: NOT TESTED.
UI-01 remains CODE UPDATED / MATCHING RUNTIME RETEST OPEN.

**2026-09-24 user screenshot — bookmark-toolbar ghost icon/text
(UI-09, source candidate implemented, visual acceptance open):**
The supplied narrow Light-looking toolbar image shows clipped colored
strokes beneath Desktop/Libraries/Documents/media shortcut icons and
short black fragments beneath their Korean captions. The source had
a full-button postpaint owner for Dark but a text/dropdown-only
postpaint overlay for Light, leaving native icon and text pixels
outside the smaller overlay rectangle. The non-High-Contrast Light
path now reuses the existing complete owner for the entire button,
including palette fill, image-list icon, label, and dropdown.
Command IDs, bookmark data, native keyboard/tooltips/accessibility,
saved layout and High Contrast native rendering remain unchanged.
The original Dark full-item ownership guard now checks both Light
and Dark and forbids the former partial Light branch. This is an
inferred source root-cause candidate, not a revision-matched Windows
visual fix claim. Full validator, current x64 compiler and Light/
Dark/HC/DPI/hover toolbar pixel regression: **NOT TESTED**.
UI-09 is SOURCE UPDATED / VISUAL RETEST OPEN.

**2026-09-24 UI-09 repeat screenshot after 541cd0f3 — prior
postpaint candidate did NOT resolve the visible ghost:**
The user's repeat report supersedes the prior source-only hypothesis.
The remaining unguarded renderer was the bookmark toolbar's WM_PAINT
/ WM_PRINT / WM_PRINTCLIENT path: reflected NM_CUSTOMDRAW postpaint
is not a guarantee for the rebar print/composition route. The new
fix routes those final non-High-Contrast bookmark pixels directly
through one full client renderer, including image-list glyphs, labels,
button states and separators. It checks available icons before
taking ownership; otherwise it retains the native fallback.
High Contrast/native route, button commands, keyboard navigation,
drag/drop and saved layout are unchanged. A source regression guard
requires explicit direct paint and print ownership, not only
NM_CUSTOMDRAW postpaint. The actual source-revision Windows x64 build
and before/after screenshots (including hover, drag, DPI and
print/rebar) are **NOT TESTED**. UI-09 remains RUNTIME OPEN.

**2026-09-24 UI-09 second diagnostic track: idempotent bookmark buttons.**
Closer source review found an independent concrete data/layout defect:
BookmarkToolBar::setBookmark inserted every manager item via
TB_INSERTBUTTON without first deleting existing buttons. If this
initialization runs again with the old toolbar still populated, the
control holds duplicate commands and can expose a partly clipped
second row. A full update also deleted and recreated an image
list redundantly before calling setBookmark, which recreated it
again. The source now makes setBookmark the only full rebuild owner,
clears existing buttons first, inserts exactly one per manager item
and checks the final native button count in debug builds. Re-show
registers asynchronous icon updates only once per visible lifetime.
This complements the new bookmark-specific paint/print owner rather
than asserting which path caused the user's exact screenshot.
Source structure checks were constructed. Revision-matched Windows
compiler, actual toolbar count at reproduction, 100/125/150/200%
DPI, visibility toggling, wrap/chevron and final screenshots:
NOT TESTED. UI-09 remains OPEN.

## Outstanding near-term work

1. Address the reproduced settings-page visibility and Dark rendering issues
   in the UI audit. UI-01 and the UI-04 mojibake reorder-label path now have
   source fixes with runtime/visual retest still required. Current x64
   compile/regression has passed at `bee95d9`;
   regenerate and inspect the CHM and validate the installer in an isolated environment.
   Keep compiler, visual, runtime, installer and third-party licensing
   evidence separate. Non-default x86/release/full profiles need user
   scope expansion; hosted Actions need per-run explicit approval.
2. Source-check the legacy help detail pages against the actual
   application menus, language packs, settings tree, shortcuts and
   screenshots before claiming them current. No speculative remapping.
3. Automatic updates have been intentionally removed. For existing personal
   installations, manually check the legacy `fxfile-upchecker` startup entry
   and old installation directory if you want complete on-machine removal;
   no migration deletes existing Windows user startup entries automatically.
4. Audit exact GFL SDK redistribution permissions and all included
   third-party binary provenance/requirements before public packaging.
5. Decide whether old `dist/history.txt` belongs in future installers.
   Until changed, ship it with an explicit **historical releases only**
   header; do not transform or delete its original history.
6. Consider the remaining dependency ABI checks, optional x64-launcher
   feasibility study and VLD release staging only with direct build/package
   verification and the architecture limits in the dependency audit.
   The retired updater is not a migration candidate.

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
| `UI_UX_AUDIT_20260924.md` | Revision-matched interactive observations, open UI findings, source-only OS compatibility candidates and reproduction/acceptance cases |
| `DISTRIBUTION_LICENSE_REVIEW.md` | Observed license contradictions and unfinished third-party distribution checks |
| Root `LICENSE` and `CREDITS` | Existing application and third-party license notices; never rewrite on the basis of assumptions |

When source, build output or runtime evidence contradicts a summary,
correct this page and `PROJECT.md` during the same logical work unit.
Keep the historical evidence that led to earlier conclusions intact.
