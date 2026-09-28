# flyExplorer — current development state (2026-09-28)

> Reviewed baseline: local and remote main
> cd96de0bc8fba13a7cfeee4e5f9da9a6dc30c7c5, before
> this UXH-06/07 review change. To identify the current
> commit, run git rev-parse main. Latest separately
> verified native UI product revision at review time:
> cd96de0bc8fba13a7cfeee4e5f9da9a6dc30c7c5
> (UXH-05 scoped accessibility and clean Release).
> Start with the [development index](README.md); the full prior
> 767-line status is [archived unchanged](CURRENT_STATUS_HISTORY_20260928.md).

## 1. Latest state, constraints and next work

**UXH-05 residual direct UIA actions (2026-09-28):**
An isolated 96-DPI external client physically invoked
New and selected Close via actual UIA InvokePattern;
MSAA child count changed 5->6->5, the owned process
exited 0 and six original configuration hashes matched.
The prior direct UIA action gap is now tested.
Real High Contrast/other DPI, spoken Narrator and
full Tab/F6 multi-pane traversal remain NOT TESTED.
[UXH-05 additional evidence](UI_PHASE6_UXH05_TAB_ACCESSIBILITY_EVIDENCE_20260928.md).


**2026-09-28 UXH-06/07 review complete, no new feature:**
Existing Search provides saved named multi-location scopes,
current-folder selection, editable scope and query history.
An isolated actual 96-DPI native GUI retained all 165
characters typed into a 240px search-scope edit; the
owner-drawn group label and native visual scrolling
are NOT separately certified. An actual isolated 1x2
Last Tabs profile restored distinct owned folders,
accepted physical Ctrl+T and saved/restored its
2/1 pane tab counts in a second real process.
Original six user-config SHA256 hashes remained
unchanged. [UXH-06/07 feasibility](UI_PHASE6_UXH06_07_FEASIBILITY_20260928.md).
Duplicate saved scopes and redundant last-session
presets were not implemented. New recent scopes,
readable full-path presentation and multiple NAMED
workspaces remain potential separately scoped user
needs, not completed product features. No new
Release build is claimed for this assessment.
Next: isolated real UXH-05 spoken reader and
DPI/High Contrast, and separate Phase 5 productization.


**2026-09-28 UXH-05 scoped actual accessibility accepted:**
The custom drawn TabCtrl was actually unnamed/childless
in UIA and MSAA despite working native tab shortcuts.
A minimal native MFC IAccessible provider now supplies
full named/selected tabs and selected-close/new buttons,
accessible focus/geometry/default actions and native events.
Owned actual Dark and Light 96-DPI Ctrl+T/Ctrl+Tab/Ctrl+W,
MSAA select/new/close and focused Right/Home/End passed.
Final clean Release x64 SHA256 CCB5050EC1AE316CB3D6C4728A1DDF9A724D3319DA40305CC5880B4A422ABB10, source invariants
and native 17 PASS/0 FAIL; original six user settings
unchanged. Full [UXH-05 scoped evidence](UI_PHASE6_UXH05_TAB_ACCESSIBILITY_EVIDENCE_20260928.md).
Actual speech reader, High Contrast, other DPI, direct
UIA InvokePattern and wider Tab/F6 focus are NOT TESTED;
physical Tab/F6 did not move focus from a test-focused
tab in the owned single-pane profile. Treat this as
scoped native interface acceptance only, not full
accessibility certification. Next: UXH-06/07 feasibility
and independent isolated accessibility environment work.


**Phase 6 UXH-04 scoped acceptance (2026-09-28):** Explicit
reversible native Drive/Bookmark toolbar-row compaction is now
real-GUI verified at actual 96 DPI on the isolated Windows 11
test desktop. Saved four visual rows of height **141 px** become
**101 px** only after an explicit View > Tools command;
actual keyboard J and real pointer restore to 141. The prior
owner-drawn J failure was an absent deployed language key; a
single-command fallback now works with old packs and the source
Korean XML was fixed and staged. A private 12-item bookmark
fixture proved the existing MFC chevron can actually open its
owned folder. Actual keyboard-compact -> exit -> relaunch in
the *same owned copied settings* restored 141px and retained
the original coolbar bytes. Final clean Release SHA256
\`08D6B6D17713D4C258C4DEFFE4DBA02C66B449DD87E098164E2DDF1C666EA26E\`; source checks and native 17/0 PASS. Detailed
[UXH-04 final evidence](UI_PHASE6_UXH04_EVIDENCE_20260928.md).
All tests owned their process; original user config six hashes
unchanged. Native tooltip-popup accessibility was **not**
observed either before or after this change; a listening session
and actual other DPI / High Contrast remain NOT TESTED.
Next UX work: UXH-05 custom tab accessibility verification,
then UXH-06/07 capability-overlap review.


**Latest Phase 6 UXH-03 scoped acceptance (2026-09-28):** Existing
per-pane Explorer info sidebar now automatically becomes a compact
36-DIP horizontal folder summary only when a narrow pane would
leave under 280 scaled px for the file list. At actual 96 DPI
Dark/Light in a 750-px 1x2 window, each native file list gained
88 px (178/176 -> 266/264 px). A 750-px 2x2, restored 1100-px
1x2 and 1200-px 2x2, and 1-pane layout passed physical geometry
checks; actual Win+Up/Down and title-bar double-click
expanded/restored the original full sidebar. Preserved the
owned info-bar setting, bookmark child state and six original
user configuration hashes. Scoped x64 Release, source/scrollbar/
address checks and native 17/0 passed. See
[UXH-03 responsive pane evidence](UI_PHASE6_UXH03_RESPONSIVE_PANE_20260928.md).
UXH-04 was subsequently accepted with the narrow localization
fallback; next independently investigate UXH-05 tab accessibility. Actual higher DPI/High Contrast
remain NOT TESTED for this change.


**New Phase 6 UXH-02 verified handoff (2026-09-28):** Normal
Search completion no longer opens a duplicate light information
modal. Actual 96-DPI owned Dark/Light 0/1/3 and invalid-location
GUI, physically stopped real active content search, an owned file
result's native Open parent folder pointer flow, and an accessible
native Windows event/UIA-readable summary all PASS. Release x64
and native 17/0 PASS, original six user hashes unchanged.
Binary SHA256 22D0568AB047E4A08F690B7461FB7D63E2B90A23E447BE03650D8818B2559575.
[Full UXH-02 evidence](UI_PHASE6_SEARCH_NONMODAL_EVIDENCE_20260928.md).
The UXH-03 layout is now scoped accepted; subsequent UX
work now moves to UXH-05 tab accessibility after UXH-04 acceptance.
Real other DPI, OS High Contrast and live screen-reader listening
are not yet accepted.


**Phase 6 UXH-01 follow-up (2026-09-28):** Bookmark
CHotKeyCtrl's native bright client in explicit Dark was
confirmed and fixed through ModernUI's shared native hotkey
subclass, preserving actual Ctrl+2 keyboard semantics.
Actual owned 96-DPI Dark/Light GUI, incremental Release x64
and native functional 17/0 passed. Details:
[hotkey theme evidence](UI_PHASE6_HOTKEY_THEME_EVIDENCE_20260928.md).
The UXH-02 native Search work is now scoped accepted;
other hotkey-setting windows and real High Contrast are not
individually GUI-accepted yet. Prior snapshot facts below
refer to the earlier reviewed baseline.


**Current product:** \`main\` remains the native MFC/C++ multi-pane file
manager. The optional WinUI 3 same-process integration has NOT been
merged or made available to ordinary users. GitHub Actions require
explicit separate approval for each run.

**Latest native fixes and evidence:** common native list/tree/dialog
Dark scrollbar handling; lifecycle-aware address ComboBoxEx popup;
non-overlapping column selection modal; native Dark column header,
physical divider drag and an easier-to-read numeric field.
Newly entered widths for non-pinned columns are bounded, at
actual 96 DPI, to 24..4096px without silently migrating unchanged
historic settings. Scoped Release-x64-Unicode incremental build,
owned 96-DPI Dark/Light GUI, related source checks and native
functional regression **17 PASS / 0 FAIL** were observed at the
tested product revision. This is not an all-environments product
certification.

**Immediate UI backlog:** [seven evidence-labelled hands-on
items](UI_UX_HANDS_ON_BACKLOG_20260928.md). The native bookmark
shortcut field originally observed in UXH-01 is fixed and GUI-tested
at actual 96 DPI Dark/Light; individual other hotkey dialogs remain
unverified. UXH-02's duplicate Search completion is now fixed;
UXH-03 narrow panes are now improved; next review compact command
discoverability and custom TabCtrl accessibility need targeted
measurement/verification, not ungrounded implementation.

**Still open:** HANG-01 on its original Shell/loading conditions
was not cleared by synthetic sample folders. Existing UI-01/UI-09
require previously specified scenario retests. Actual 125%,
150%, 200% display DPI, Windows High Contrast and specific older
dialog scrollbars remain NOT TESTED. Clean-PC installer/uninstaller,
complete Help topic acceptance and third-party/GFL distribution
licensing are also open.

**Experimental UI status:** Separate branch
\`experiments/phase5-productization-20260928\`, worktree HEAD
\`7ceeab515bc90089d1220d608059d254c374a339\` at review time.
The historical cross-process strict-bridge teardown failure was
resolved in the TEST HARNESS, with repeated 96-DPI bridge passes.
Same-process MFC-host WinUI 3 with experimental TextBox, native
commands and owned host PRI staging is promising experimental
evidence, NOT a tested installer/runtime deployment contract.
IME, Shell virtual namespaces, other real DPI, High Contrast and
clean-PC runtime/redistribution gates remain open.
See [main's historical bridge report](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md)
and experiment-only
[PRI/address report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_ADDRESS_PRI_EVIDENCE.md)
and [MFC-island report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_MFC_ISLAND_EVIDENCE.md).
Do not merge or enable WinUI 3 from documentation maintenance.

**Next bounded tasks:** implement only a separately reproduced
native UX candidate; acquire a disposable Windows test environment
for outstanding actual DPI/High Contrast acceptance; and continue
formal PRI build/package plus active-pane synchronization on the
isolated WinUI 3 experiment only if specifically requested.

## 2. Area-specific state and evidence

| Area | Verified versus unverified | Read next |
| --- | --- | --- |
| Native engine and MFC controls | Latest scoped x64 native 17/0; owned 96-DPI Dark/Light GUI on listed controls, not other actual DPI/HC | [DPI/theme/input evidence](UI_WINDOWS11_DPI_CONTRAST_20260928_EVIDENCE.md), [native scrollbar inventory](UI_SCROLLBAR_MODAL_OVERLAP_AUDIT_20260928.md), [column header](UI_COLUMN_DETAILS_HEADER_EVIDENCE_20260928.md) |
| Native UI follow-up | Seven candidate items; only specifically observed effects are confirmed | [Hands-on backlog](UI_UX_HANDS_ON_BACKLOG_20260928.md), [UI design policy](UI_UX_DESIGN_GUIDE.md) |
| Historical instability | HANG-01, UI-01/09 full original-profile acceptance pending | [Error history](ERROR_HISTORY.md), [UI-09 cause](UI09_ROOT_CAUSE_20260926.md) |
| Cross-process WinUI 3 | Strict test harness teardown resolved, not product integration | [Bridge evidence](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md) |
| Same-process WinUI 3/PRI | Unmerged; owned test staging is not installer-ready | Experiment reports linked above and [framework decision gates](UI_FRAMEWORK_DECISION_POLICY.md) |
| Build/dependencies/licensing | VS2026, MSVC v145, recommended Release-x64-Unicode; full install and rights review pending | [Dependency audit](DEPENDENCY_ARCH_AUDIT_20260924.md), [license review](DISTRIBUTION_LICENSE_REVIEW.md), root [build README](../../README) |
| User help | Source/package structure previously checked, not a current-content or CHM runtime acceptance | [Help audit](HELP_CONTENT_AUDIT.md), [source topics](../htmlhelp/) |

A PASS is always scoped to the revision, test environment and
observed feature stated by its original evidence. Do not promote
source-only, Debug or simulated checks to missing actual-OS PASS.

## 3. Historical records and maintenance

The previous CURRENT_STATUS contents, including superseded
intermediate “latest” claims, are preserved **byte-for-byte**
in [CURRENT_STATUS_HISTORY_20260928.md](CURRENT_STATUS_HISTORY_20260928.md).
Treat old “next task” paragraphs as dated history, not live guidance.
Use [ERROR_HISTORY.md](ERROR_HISTORY.md) for the original
append-only diagnosis, [original UI audit](UI_UX_AUDIT_20260924.md)
for earlier screenshots and issues, and [the index](README.md)
to navigate the separate dated experiment/release evidence.
Update this short page when branch status, accepted tests or open
work changes; append detailed execution proof to an appropriate
dated evidence document, not to the top of this summary.
