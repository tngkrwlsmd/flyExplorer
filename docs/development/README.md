# flyExplorer development documentation

This directory contains documentation relevant to the canonical WinUI 3
application and its current engineering requirements.

## Current documents

- CURRENT_STATUS.md — accepted product state, latest evidence and open gates.
- NEXT_DEVELOPMENT_GOALS.md — current dated work queue, scoped completed items,
  unverified gaps and product choices; historical plans remain below the current
  summary and do not reopen accepted work. Planning, not authorization.
- ARCHITECTURE.md — current WinUI/native-core/Shell-isolation architecture.
- AGENT_EFFICIENCY.md — mandatory bounded tool/build/test strategy.
- VERIFICATION_PROFILE.md — central CI scopes, failure taxonomy, FAST/STANDARD/FINAL profiles and high-cost fixture policy.
- PRE_DISTRIBUTION_FUNCTIONAL_GATES.md — verified pre-installation functional
  gates, hardware blocks and remaining user-facing/large-folder work.
- ERROR_HISTORY.md — append-only failure/root-cause/prevention ledger.
- UI_UX_DESIGN_GUIDE.md — current product UI/UX rules.
- WIN11_EXPLORER_UI_REFERENCE.md — Windows 11 Explorer comparison policy.
- EXPLORER_PARITY_REQUIREMENTS.md — feature-parity development contracts,
  acceptance criteria, priorities and scoped local build/run evidence.
- WINUI_EXPLORER_VISUAL_BENCHMARK_20261001.md — measured Explorer baseline.
- WIN11_EXPLORER_FEATURE_BENCHMARK_20261012.md — sourced feature-gap matrix, priorities and acceptance boundaries.
- WIN11_PARITY_REAUDIT_20261022.md — original dated Explorer comparison with a
  2026-10-29 evidence reconciliation; use NEXT_DEVELOPMENT_GOALS.md for the live
  work queue, not the historical OPEN labels. No blanket equivalence claim.
- PX02_HOME_OVERVIEW_ACCEPTANCE.md, PX06_SEARCH_CANCEL_STATUS.md,
  PX12_KEYBOARD_CANDIDATE_ACCEPTANCE.md and M23_ACCEPTANCE_BOUNDARY.md — finite
  feature acceptance records; preserve their explicit runtime/visual limits.
- UI_VISUAL_RETEST.md — current owned GUI/visual verification workflow.

The root README, AGENTS.md and editable .agent-policy/PROJECT.md are also
current sources of truth. Current Windows request ownership is documented in
docs/operations/windows-runner-retirement.md; older task examples in
historical acceptance sections are not live commands. Packaging-specific
obligations live under packaging/.

## Source-of-truth order

1. Higher-level runtime/user instructions.
2. Root AGENTS.md and applicable path instructions.
3. Current source and tests on the checked-out revision.
4. CURRENT_STATUS.md and ARCHITECTURE.md.
5. Historical Git objects and old logs as revision-specific evidence only.

Root AGENTS.md overrides the vendored generic branch-first Git workflow
for flyExplorer. Prefer verified direct-main logical units when safe and
permitted; otherwise use a short-lived work branch when required. Preserve
evidence/remote-windows as a historical archive, not an active work branch.

Evidence is always tied to source SHA, configuration/binary, tested
environment, producing workflow/run, exact scope and result. Historical
Release, GUI and visual PASS claims are not automatically transferable
to later main commits. Compare live main and central CI before deciding
that a logical unit is accepted.

Do not recreate deleted historical documentation merely to preserve old links.
Recover an old report from Git only for a specific historical investigation.
