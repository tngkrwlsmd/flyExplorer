# flyExplorer — current development state (2026-09-28)

> Reviewed baseline: local and remote main
> \`f2958d70b6a2714b061bc5215ecce3a9f707d0b3\`, **before this
> docs-only change**. To identify the new current commit, run
> \`git rev-parse main\`. Last separately tested native product change:
> \`4f1a407cca0162080a5449f2d7772b69b3ca32c5\`.
> Start with the [development index](README.md); the full prior
> 767-line status is [archived unchanged](CURRENT_STATUS_HISTORY_20260928.md).

## 1. Latest state, constraints and next work

**New Phase 6 UXH-02 verified handoff (2026-09-28):** Normal
Search completion no longer opens a duplicate light information
modal. Actual 96-DPI owned Dark/Light 0/1/3 and invalid-location
GUI, physically stopped real active content search, an owned file
result's native Open parent folder pointer flow, and an accessible
native Windows event/UIA-readable summary all PASS. Release x64
and native 17/0 PASS, original six user hashes unchanged.
Binary SHA256 22D0568AB047E4A08F690B7461FB7D63E2B90A23E447BE03650D8818B2559575.
[Full UXH-02 evidence](UI_PHASE6_SEARCH_NONMODAL_EVIDENCE_20260928.md).
The next MFC UX implementation/verification sequence starts at
UXH-03 (split-pane information density), UXH-04 (compact command
surface), and UXH-05 (actual tab accessibility investigation).
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
next measure split-pane layouts and compact command
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
