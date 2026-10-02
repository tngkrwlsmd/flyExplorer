# flyExplorer development documentation

This directory contains only documentation that is still useful for the
canonical WinUI 3 product on main. Dated migration, MFC, Phase5 and early
M1.x-M2.x checkpoint reports were removed from the working tree on 2026-10-02.
Their exact content remains available through Git history.

## Current documents

- CURRENT_STATUS.md — accepted product state, latest evidence and open gates.
- ARCHITECTURE.md — current WinUI/native-core/Shell-isolation architecture.
- AGENT_EFFICIENCY.md — mandatory bounded tool/build/test strategy.
- ERROR_HISTORY.md — append-only failure/root-cause/prevention ledger.
- UI_UX_DESIGN_GUIDE.md — current product UI/UX rules.
- WIN11_EXPLORER_UI_REFERENCE.md — Windows 11 Explorer comparison policy.
- WINUI_EXPLORER_VISUAL_BENCHMARK_20261001.md — measured Explorer baseline.
- UI_VISUAL_RETEST.md — current owned GUI/visual verification workflow.
- DISTRIBUTION_LICENSE_REVIEW.md — current public-distribution/legal gates.

The root README, AGENTS.md and editable .agent-policy/PROJECT.md are also
current sources of truth. Packaging-specific obligations live under packaging/.

## Source-of-truth order

1. Higher-level runtime/user instructions.
2. Root AGENTS.md and applicable path instructions.
3. Current source and tests on the checked-out revision.
4. CURRENT_STATUS.md and ARCHITECTURE.md.
5. Historical Git objects and old logs as revision-specific evidence only.

Do not recreate deleted historical documentation merely to preserve old links.
Recover an old report from Git only for a specific historical investigation.
