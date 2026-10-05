# flyExplorer verification profile

This document contains mutable project-specific verification values and the
canonical execution profile. General engineering principles stay in
\`AGENTS.md\`, \`.agent-policy/PROJECT.md\` and
\`docs/development/AGENT_EFFICIENCY.md\`.

## Remote Windows operational settings

The top-level \`env\` block in
\`.github/workflows/remote-windows-task.yml\` owns these values:

- \`FLYEXPLORER_CANONICAL_CHECKOUT\` - canonical persistent Windows checkout.
- \`FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS\` - 30-second dependent-run observation interval.
- \`FLYEXPLORER_ACTIVE_MONITOR_SECONDS\` - 30-second explicit active-monitor interval.
- \`FLYEXPLORER_RESULT_DEPENDENT_MAX_WAIT_SECONDS\` - 180-second / three-minute same-turn wait ceiling.
- \`FLYEXPLORER_REMOTE_RUNNER_CAPACITY\` - current interactive Windows execution capacity.
- \`FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET\` - normal planning budget, not a retry token budget.

When runner capacity changes, revisit request-slot serialization and workflow
concurrency.

## Request modes

Remote requests have one purpose, not two declarations of the same purpose.

### Diagnostic

\`request_mode: diagnostic\` is for inspection, runner/environment diagnosis,
selector discovery and other exploratory work. It uses
\`configuration: none\`, an empty \`validation_plan\`, and may use a free-form
command. A moved \`main\` SHA is reported as advisory rather than invalidating a
read-only diagnostic.

Diagnostic failures are infrastructure/diagnostic evidence. They are not
product acceptance failures and do not participate in validation deduplication.

### Validation

\`request_mode: validation\` requires \`Debug\` or \`Release\` and a non-empty
\`validation_plan\`. The plan names logical validation targets such as
\`source\`, \`build\`, \`gui\`, \`visual\` or
\`high-contrast-gui\`; it is not inferred back from command text.

The validation fingerprint includes candidate SHA, configuration, logical unit,
normalized validation plan, normalized command hash and harness revision. The
fingerprint is evidence identity, not a hard duplicate rejection gate.
Previously successful evidence may be reused when all identities match.
Harness or infrastructure changes naturally produce a different identity.

Legacy \`validation_kind\` requests remain readable only for migration. New
requests must not declare both schemas.

## Failure taxonomy

Remote workflow evidence records these control-plane stages:

- \`REQUEST_VALIDATION\`
- \`STATIC_PREFLIGHT\`
- \`RUNNER_HEALTH\`
- \`COMMAND\`

Each stage is \`PASS\`, \`FAIL\` or \`NOT_RUN\`. The High Contrast acceptance
orchestrator additionally records:

- \`RUNNER_SETUP\`
- \`BASELINE\`
- \`CANDIDATE_GUI\`
- \`VISUAL\`
- \`CLEANUP\`

If baseline fails, candidate GUI remains \`NOT_RUN\`. A failure before the
product command is classified as request/static/runner infrastructure rather
than as a product regression.

## Retry policy

Do not use rerun as a development loop. Deterministic product assertions and
source-contract failures require a source or test revision before another
acceptance run.

A same-revision rerun may be used once when the previous evidence clearly shows
an infrastructure/transient class such as runner session loss, transient UIA
availability, network fetch, Windows Settings automation, infrastructure
timeout or artifact upload failure. The workflow no longer blocks all reruns at
the job boundary because that hid this distinction.

The workflow now reads the prior Actions result/log for the same logical unit
before an expensive retry. A still-unclassified prior failure blocks validation
until it can be classified by the current failure classifier or a focused
diagnostic. A harness/automation/shutdown-boundary failure requires
`retry_scope: focused-reuse`: the request names the prior run/candidate and
the successful targets it reuses, the workflow verifies canonical success
markers plus a harness/infra-only diff, and the focused command is forbidden
from invoking the normal build/package entry points again. Repeated full
validation after such a classified focused failure is invalid evidence.

## Verification profiles

### FAST

Use for every relevant change before expensive Windows work:

- request/schema validation when applicable;
- \`git diff --check\`;
- changed-Python syntax and undefined-global static checks;
- the narrowest product, harness or infrastructure contract suite invalidated
  by the diff.

Goal: catch cheap deterministic defects before build or GUI execution.

### STANDARD

FAST plus the minimum build/native/targeted GUI smoke required by the changed
product behavior. Do not repeat a deterministic FAST assertion here merely
because the profile is broader.

### FINAL ACCEPTANCE

STANDARD plus only the environment/global-state/high-cost evidence required for
merge or release, including High Contrast, matched baseline/candidate visual
evidence or large fixtures when those risks are actually invalidated.

Diagnostic work is outside FAST/STANDARD/FINAL.

## Source contract ownership

\`tools/winui/run_checks.py\` exposes three independently runnable source
families:

- \`product-source\` - product/API/architecture invariants;
- \`harness\` - test harness, cleanup, fixture and validation-helper safety;
- \`infra\` - workflow/request/orchestration policy.

The umbrella \`source\` stage runs all three. Change-scoped preflight should run
only the affected family instead of making every product edit depend on
workflow/document wording.

Exact prose and implementation-string assertions are reserved for structural or
safety markers that genuinely require exact representation. Behavior checks are
preferred otherwise.

## Runner health and High Contrast

Before a GUI validation plan, run the low-cost runner health check. It verifies
the interactive Windows/UIA/Python/High Contrast-query capability without
walking the complete Windows Settings tree.

High Contrast global-state control is runner setup/cleanup:

1. query and remember the original state;
2. use \`tools/winui/high_contrast_runner_setup.py\` to reach the target;
3. run product acceptance;
4. restore and verify the original state in cleanup.

\`tools/winui/high_contrast_acceptance.py\` orchestrates this lifecycle and
writes structured stage evidence. Product acceptance remains in
\`tests/winui/test_high_contrast_gui.py\`.

Runtime PowerShell here-strings must not contain reusable Python acceptance or
runner-state helpers. Those helpers belong in repository files so syntax,
undefined-name checks and source review apply before a Windows run.

## Current high-cost fixture profile

These are current project facts, not generic policy:

- The owned large-folder GUI acceptance fixture at 8,000 files is high-cost and
  is reserved for final acceptance after cheaper lifecycle checks pass.
- The 20,000-entry aggregate/model safety boundary can make boundary probes
  high-cost. It is a product safety bound, not a generic validation-run
  threshold.

## Remote workflow ownership

The full Remote Windows Task implementation is
\`.github/workflows/remote-windows-task.yml\` on \`main\`. The
\`control/remote-shell\` branch carries only request data and a thin push
trigger that calls the reusable implementation at \`@main\`. Operational logic
must not be duplicated into the control branch.
