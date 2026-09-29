# flyExplorer development documentation index

**CURRENT OWNER-APPROVED UI DIRECTIVE:** [Full WinUI 3 product destination, protected native C++ reuse, temporary MFC fallback, stepwise delivery and release gates](WINUI3_FULL_MIGRATION_DIRECTIVE_20260929.md). Older framework-neutral comparisons are historical; use this decision to prioritize subsequent UI work.

**CURRENT ACTUAL M1.9 SOURCE IMPORT:** [Latest native main merged into separate WinUI with bounded workspace/search interoperability and exact limits](WINUI3_M19_MAINLINE_FEATURE_INTEGRATION_20260929.md). Prior M1.8 no-import plans below remain historical. Native default main is unchanged.


**CURRENT branch/release readiness (2026-09-29):** [Merged UXH-07/UXH-06/UI-02 native main, separate WinUI 3 M1.8, exact artifact hashes, retained evidence and open acceptance gates](BRANCH_AND_RELEASE_STATUS_20260929.md). Read this and [CURRENT_STATUS](CURRENT_STATUS.md) before interpreting the historical feature-only links below.


**UI-02 branch-resolution evidence:** [Current ModernUI replaces obsolete dual-renderer branch; actual Light/Dark native controls, drag and modal GUI accepted](UI02_SUPERSEDED_MERGE_ACCEPTANCE_20260929.md). Corrected test-owned desktop clipping, old Last Tabs and a modal startup tip without modifying the real user profile.


**Latest scoped legacy MFC integration:** [UXH-06 saved/recent search scopes ? real owned GUI and merged Release x64 acceptance](UXH06_MAIN_MERGE_ACCEPTANCE_20260929.md). Includes explicit opt-in persistence and opt-out privacy after restart; separate legacy scrollbar GUI work is reviewed independently.


> Current branch snapshot *before* this documentation-only update: `main` `f074a6b` and WinUI M1.8 `eb7ee1a`. For later revisions use `git rev-parse`, not the older `f2958d7` review baseline retained in historical reports. [Current consolidation record](BRANCH_AND_RELEASE_STATUS_20260929.md) is the primary entry point.

## 1. Required instructions and active work

| When | Document and responsibility |
| --- | --- |
| Every repository-changing task | [Root AGENTS](../../AGENTS.md), then [vendored policy](../../.agent-policy/AGENTS.md); preserve the vendor core. |
| Managing build/log/GUI tool calls | [Agent efficiency](AGENT_EFFICIENCY.md), including budgets, minimum validation and final-only build log capture. |
| Reviewing architecture and project facts | [Editable project facts](../../.agent-policy/PROJECT.md). |
| Finding live branch, verified work and open tasks | [Concise CURRENT_STATUS](CURRENT_STATUS.md); authoritative entry point. |
| Choosing native UX work | [Evidence-labelled hands-on backlog](UI_UX_HANDS_ON_BACKLOG_20260928.md) and [design/acceptance policy](UI_UX_DESIGN_GUIDE.md). |
| Diagnosing known failures | [Append-only error history](ERROR_HISTORY.md), including the original failed checkpoints. |

## 2. Native MFC UI, visual review and regression evidence

- [UXH-07 branch publication revalidation (2026-09-29)](UXH07_PUSH_VERIFICATION_20260929.md): fresh latest Release x64 binary hash, canonical native 17/0 with protected smoke SKIP, actual GUI eight malformed fixtures, two named presets across restart, orphan safety, Korean menus and physical dark-scrollbar wheel. This is a feature-branch checkpoint, not a production release or whole-OS acceptance.


- [Local Korean popup and legacy Customize dark/scrollbar audit (2026-09-29)](UI_LEGACY_MENU_TOOLBAR_AUDIT_20260929.md):
  corrected real menu strings and scalable single chevrons; native toolbar
  Dark list scrollbars physically exercised in owned GUI, source audit of
  other legacy class candidates, exact binary and remaining OS limits.
  LOCAL/unmerged, not evidence that every popup is fixed.


| Focus | Document / use |
| --- | --- |
| Historical UI issue IDs and old screenshots | [2026-09-24 UI audit](UI_UX_AUDIT_20260924.md): dated observations, not today's open-work list. |
| How to validate actual Windows UI | [Visual retest workflow](UI_VISUAL_RETEST.md): owned processes, screenshots and evidence levels. |
| External Windows 11 design references | [Explorer reference policy](WIN11_EXPLORER_UI_REFERENCE.md): UI sources and adoption limits. |
| Address dropdown original Dark defect | [Dropdown-specific evidence](UI_ADDRESS_DROPDOWN_DARK_EVIDENCE.md): original narrow popup fix. |
| Native scrollbar source inventory and modal overlap | [Scroll/modal audit](UI_SCROLLBAR_MODAL_OVERLAP_AUDIT_20260928.md): control coverage, popup ownership and lifecycle. |
| Column header, divider and numeric field | [Column GUI evidence](UI_COLUMN_DETAILS_HEADER_EVIDENCE_20260928.md): dedicated native dialog acceptance. |
| Latest actual DPI/theming and width bounds | [MFC 96-DPI Windows regression](UI_WINDOWS11_DPI_CONTRAST_20260928_EVIDENCE.md): real 120/144/192 DPI and OS High Contrast explicitly NOT TESTED. |
| Previous bookmark toolbar redraw defect | [UI-09 root-cause evidence](UI09_ROOT_CAUSE_20260926.md): not a full original-user retest. |

These are separate, revision-scoped evidence documents. Do not
combine historic Debug/source-only or different-DPI results into
a single unsupported release qualification.

- [Phase 6 native hotkey Dark fix](UI_PHASE6_HOTKEY_THEME_EVIDENCE_20260928.md):
  actual 96-DPI bookmark dialog, native Ctrl+2 and light fallback;
  other hotkey screens and real High Contrast remain open.

- [Phase 6 accepted native Search completion](UI_PHASE6_SEARCH_NONMODAL_EVIDENCE_20260928.md):
  real Dark/Light count/error, physical active Stop, actual
  parent-folder navigation and a readable Windows event/UIA summary.

- [Phase 6 responsive narrow per-pane info](UI_PHASE6_UXH03_RESPONSIVE_PANE_20260928.md):
  actual 96-DPI Dark/Light 1x2/2x2 and 750-px file-width measurement,
  keyboard/pointer restoration, saved layout protection; higher
  actual DPI/High Contrast remain untested.

- [UXH-06 explicit recent scopes and full-path preview, WIP](UI_PHASE6_UXH06_NEW_FEATURE_WIP_20260928.md):
  built scoped product change with initial isolated real GUI
  proof; normal-restart persistence/clear and Dark/Light
  acceptance pending active input desktop. NOT MERGED.

- [Phase 6 UXH-06/07 native feature-overlap review](UI_PHASE6_UXH06_07_FEASIBILITY_20260928.md):
  owned 96-DPI long search path retention and
  real 1x2 Last Tabs exit/relaunch proof at the historical
  main baseline; this is NOT the optional named-workspace feature.

- [Local UXH-07 named workspace scoped acceptance](UI_PHASE6_UXH07_NAMED_WORKSPACE_WIP_20260929.md):
  UNMERGED local branch only. After a verified variable-width
  temporary-name fix and restart-test correction, the final locally
  rebuilt x64 executable passed eight real invalid GUI inputs,
  two named save/restore/restart GUI, isolated 3-hex orphan and
  live-lock/reparse safety, and local CI PASS_WITH_SKIPS.
  Real other DPI, OS High Contrast and spoken reader remain separate.

- [Phase 6 custom tab native UIA/MSAA accessibility](UI_PHASE6_UXH05_TAB_ACCESSIBILITY_EVIDENCE_20260928.md):
  scoped actual 96-DPI Dark/Light named tab/close/new
  semantic actions and keyboard acceptance; separate
  spoken reader, other DPI, High Contrast and broader
  Tab/F6 focus routes remain open.

- [Phase 6 opt-in compact native toolbar rows](UI_PHASE6_UXH04_EVIDENCE_20260928.md):
  actual 96-DPI pointer/J keyboard, old/new Korean-language
  fallback, owned bookmark overflow, preserved serialized custom
  layout and physical restart proof; tooltip screen-reader
  acceptance and other actual DPI/High Contrast remain open.

## 3. UI framework decision and optional experimental work

| Stage | Source / restriction |
| --- | --- |
| Choosing MFC, hybrid or staged replacement | [Framework migration decision gates](UI_FRAMEWORK_DECISION_POLICY.md); WinUI 3 adoption is not mandatory. |
| Previous DPI/WinRT technical feasibility | [Phase 4 evaluation](UI_FRAMEWORK_PHASE4_EVALUATION.md). |
| Historical separate-process strict command bridge | [Phase 5 bridge report](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md); the original shutdown failure was subsequently fixed in the test harness. |
| Unmerged MFC-host WinUI 3 island | [Experiment-only island report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_MFC_ISLAND_EVIDENCE.md), branch \`experiments/phase5-productization-20260928\` (reviewed \`7ceeab515bc90089d1220d608059d254c374a339\`). |
| Experimental TextBox/address/PRI staging | [Experiment-only PRI/address report](https://github.com/tngkrwlsmd/flyExplorer/blob/experiments/phase5-productization-20260928/docs/development/UI_FRAMEWORK_PHASE5_ADDRESS_PRI_EVIDENCE.md). Temporary host PRI placement is NOT formal installer or clean-PC readiness. |

The two experiment-only reports are intentionally NOT copied
into \`main\`, because their opt-in productization code remains
unmerged and the required installer/runtime/IME/DPI acceptance
is incomplete.

## 4. Build, distribution and user help

| Purpose | Owner |
| --- | --- |
| Building the native product and running local CI | Root [build README](../../README), \`LOCAL_CI_MANUAL.txt\` and mandatory AGENTS; recommended VS2026 v145 Release-x64-Unicode / x64. |
| Dependency architecture and ABI | [Dependency audit](DEPENDENCY_ARCH_AUDIT_20260924.md). |
| Packaging and third-party redistribution | [Distribution/license review](DISTRIBUTION_LICENSE_REVIEW.md) and root LICENSE/CREDITS; GFL/third-party authorization remains an open review. |
| User help maintenance and acceptance | [Help content audit](HELP_CONTENT_AUDIT.md) and [HTML Help source tree](../htmlhelp/); passing the source inventory does not establish current content or installed CHM usability. |

## 5. Historical retention and update rules

- The old 767-line status, including superseded 'latest' claims
  and intermediate failures, is archived as a **byte-exact copy**:
  [CURRENT_STATUS_HISTORY_20260928.md](CURRENT_STATUS_HISTORY_20260928.md).
  The new [current status](CURRENT_STATUS.md) alone owns live tasks.
- [ERROR_HISTORY](ERROR_HISTORY.md), the early
  [UI audit](UI_UX_AUDIT_20260924.md), original targeted evidence
  and unmerged WinUI experiments retain unique facts. No original
  development document was proven safely redundant; **0 deletions**.
- Keep [AGENTS](../../AGENTS.md) and [efficiency policy](AGENT_EFFICIENCY.md)
  for mandatory workflow, [.agent-policy/PROJECT.md](../../.agent-policy/PROJECT.md)
  for project facts, [hands-on backlog](UI_UX_HANDS_ON_BACKLOG_20260928.md)
  for upcoming UI tasks, and individual evidence files for
  revision-specific tests. Append failures to ERROR_HISTORY.
  Do not edit the upstream-pinned \`.agent-policy\` core.
- Update this index when files move/appear. Before any future
  deletion, prove that all substantive facts and consumers
  have an authoritative replacement and fix every inbound link.
