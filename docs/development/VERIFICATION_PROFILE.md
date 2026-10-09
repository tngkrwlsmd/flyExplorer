# flyExplorer verification profile

This document contains mutable project-specific verification values and the
canonical execution profile. General engineering principles stay in
\`AGENTS.md\`, \`.agent-policy/PROJECT.md\` and
\`docs/development/AGENT_EFFICIENCY.md\`.

## Remote Windows operational settings

The reusable workflow keeps only one repository-specific runtime setting:
`FLYEXPLORER_CANONICAL_CHECKOUT`, the canonical persistent Windows checkout.
Runner serialization is expressed directly by workflow concurrency rather than
duplicated tuning variables. Agent observation cadence and retry discipline are
policy, not workflow environment configuration.

The Remote Windows Task intentionally keeps `actions: write` and
`contents: write`. Request mode describes purpose and validation behavior; it
does not downgrade the workflow token. Repository-scoped maintenance such as
approved branch cleanup may therefore use the same control plane.

## Request modes

Remote requests have one purpose, not two declarations of the same purpose.

### Diagnostic

`request_mode: diagnostic` is for inspection, runner/environment diagnosis,
selector discovery and other exploratory work. It uses
`configuration: none`, an empty `validation_plan`, and may use a free-form
command. A moved `main` SHA is advisory for a non-mutating diagnostic. The
workflow token itself remains write-capable; request mode does not change token
permissions.

Diagnostic failures are infrastructure/diagnostic evidence. They are not
product acceptance failures.

### Validation

`request_mode: validation` requires `Debug` or `Release` and a non-empty
`validation_plan`. The plan names logical validation targets such as
`source`, `build`, `gui`, `visual` or
`high-contrast-gui`; it is not inferred back from command text.

The current request schema carries candidate SHA, configuration, logical unit
and validation plan directly. The workflow does not inspect previous Actions
results before execution. Deprecated fields from the older request schema are
rejected.

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

If baseline fails, candidate GUI remains \`NOT_RUN\`. Lower validation code
that already knows a failure category writes the small machine-readable
\`logs/remote-evidence/check-result.json\` result as well as the existing
\`FAILURE_CATEGORY=...\` marker. Final classification uses the structured
category first, then an explicit marker, then the legacy classifier as fallback.
Only failures that occur before lower validation can classify themselves use
the bounded request/static/runner fallback categories.

Remote command execution preserves the request source by writing
`REMOTE_COMMAND` verbatim to a per-run temporary `.ps1`, then launching a
fresh Windows PowerShell process with `-File`. This avoids native argv
re-tokenization of multi-line/quoted PowerShell source. The child process exit
code, not the parent shell's stale `$LASTEXITCODE`, determines command success;
the temporary script is removed in `finally`. A handled native nonzero used as
a condition therefore does not make an otherwise successful script fail, while
a bare failing native command or an uncaught PowerShell `throw` still fails the
task. Multi-step commands must continue to check native exit codes at the call
boundary when later successful statements could otherwise mask them.

## Retry policy

Do not use rerun as a development loop. Deterministic product assertions and
source-contract failures require a source or test revision before another
acceptance run.

There are no automatic or workflow-enforced result-based retries. After any
failure, classify the first relevant error as product, harness/fixture, or
control-plane/environment. A successor run is justified only after the code,
harness, or execution condition that explains the failure has materially
changed. Resume from the earliest invalidated boundary and do not rebuild or
repackage unchanged product merely because a later harness step failed.

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

Do not add a separate native compile preflight. On the self-hosted Windows
runner, selected/project compile experiments either failed to prove that the
changed translation unit reached the compiler or cost too close to the normal
build. The existing Release build is the trusted compile boundary: the measured
fresh build was about 150 seconds, a one-translation-unit incremental build was
about 46 seconds, and an injected `#error` was detected by the incremental
build in about 7 seconds. Use FAST -> Release build rather than adding a second
compile control path.

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

## Git-backed remote Windows evidence (2026-10-09)

Remote Windows Task archives sanitized evidence to the isolated
`evidence/remote-windows` branch at `runs/<run-id>/`, avoiding
account-limited Actions artifact storage. It commits the record from the
**same executing job** with the existing `contents: write` permission
and serialized execution lane.

`manifest.json` retains run URL, workflow SHA, candidate SHA and
pre-archive job state. The optional `remote-result.json` and
`check-result.json` contain strictly validated structured fields;
`markers.json` contains limited PASS/FAIL-like markers. Large, missing
or symlinked inputs are not copied. Full console logs remain in the
linked Actions run. Raw transcripts, private user data, binaries and
unreviewed screenshots are **not** committed to Git.

An archive PASS cannot override a failed product stage or independently
certify the UI's final pixels. Historic run `37912684233` is
reconstructed only from its surviving Actions log; its missing ZIP and
screenshot cannot be recovered.

## Remote workflow ownership

The full Remote Windows Task implementation is
\`.github/workflows/remote-windows-task.yml\` on \`main\`. The
\`control/remote-shell\` branch carries only request data and a thin push
trigger that calls the reusable implementation at \`@main\`. Operational logic
must not be duplicated into the control branch.
