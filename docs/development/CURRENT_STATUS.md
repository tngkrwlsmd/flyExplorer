# flyExplorer — current development state (2026-09-28)

> Reviewed baseline: local and remote main
> \`f2958d70b6a2714b061bc5215ecce3a9f707d0b3\`, **before this
> docs-only change**. To identify the new current commit, run
> \`git rev-parse main\`. Last separately tested native product change:
> \`4f1a407cca0162080a5449f2d7772b69b3ca32c5\`.
> Start with the [development index](README.md); the full prior
> 767-line status is [archived unchanged](CURRENT_STATUS_HISTORY_20260928.md).

## 1. Latest state, constraints and next work

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
items](UI_UX_HANDS_ON_BACKLOG_20260928.md). First reproduce and scope
the bright native bookmark shortcut field under Dark (UXH-01);
separately review the redundant bright success message during
Search (UXH-02). Narrow split-pane layouts, compact command
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
