# flyExplorer verification profile

This document contains mutable project-specific verification values and the
canonical execution profile. General engineering principles stay in
\`AGENTS.md\`, \`.agent-policy/PROJECT.md\` and
\`docs/development/AGENT_EFFICIENCY.md\`.

## Central Windows execution settings

The dedicated flyExplorer Windows Runner and source-repository Windows
workflows were retired on 2026-10-10. There is no active
`FLYEXPLORER_CANONICAL_CHECKOUT` setting owned by this repository's
GitHub Actions workflow. The central Windows service and source checkout
are controlled by `tngkrwlsmd/personal-control-plane`.

## Central request profiles

**Registered CI:** Explicit manual request to
`personal-control-plane/.github/workflows/central-flyexplorer-ci.yml`.
The project ID is `desktop-a`; pass a verified 40-character commit SHA
reachable from flyExplorer/main and one scope:

- `health`: runner and environment health; **not** product acceptance.
- `source`: policy and source contracts.
- `release`: policy/source and Release build.
- `gui`: policy/source, Release build and functional GUI.
- `gui-probe`: focused diagnostic; **not** final acceptance.

There is no exact current central equivalent for the retired
Debug+Release `full` scope. If it is required, plan and run its gates
explicitly using central Remote Shell, and retain scope-specific evidence.

**Ad hoc Windows shell:** Use central `requests/remote-shell/request.json`
with target `windows-vm`, not the retired source `control/remote-shell`
branch. Verify the live source revision, target, working directory,
request lease and preflight before submission; restore the slot to idle
when complete. It has a different request schema from the historical
`request_mode`/`validation_plan` protocol.

## Failure taxonomy

Distinguish a product defect, GUI fixture/harness error and VM/control
environment failure from the first relevant log. Central run status is
authoritative only for the exact source SHA, scope and environment
recorded. A functional GUI PASS does not certify visual pixel review.
The former remote-request sidecar stages remain historical Git evidence,
not a current live workflow contract.

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

## Focused verification override — 2026-10-22

Validation has been authorized with a strict **feature-local** budget.

| Changed material | Minimal default proof | Unrelated work to omit |
| --- | --- | --- |
| Documents or roadmap | Review modified text and links | Builds, GUI, all-source |
| Python/CI/harness | Syntax and affected contract only | Product suite/native builds |
| Independent feature behavior | Its product-source area plus one targeted native/GUI test if needed | A/B/C/D regressions for E-only edit |
| Compiled code or XAML | Relevant contracts and one incremental impacted target build using compatible intermediates | Clean all-target build or installer |
| Shared ABI/dependency/stale build cache | Identified affected graph only | Arbitrary full retests |

Use existing exact-source/runtime acceptance if compiled inputs are unchanged.
An isolated fresh checkout without usable build cache cannot provide a true
incremental binary build; require at most one justified new build and document
the limitation. The registered central 'release' and 'gui' scopes include broad
source tests and/or full GUI; do not use them for E-only acceptance by default.
GUI is not implicit in build permission. Never reactivate excluded G03-G05 or
stopped G07.

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

Do not add a separate native compile preflight. Historical measurements on
the retired flyExplorer-specific self-hosted Windows runner found that
selected/project compile experiments either failed to prove that the
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

## Archived remote Windows evidence

The historical `evidence/remote-windows` branch stores sanitized
results under `runs/<run-id>/`. `manifest.json` identifies run and
source revision; optional `remote-result.json`, `check-result.json`
and `markers.json` contain bounded, allowlisted fields. Private
transcripts, user profile data, binaries and unreviewed screenshots
were never approved Git evidence and remain excluded.

This branch is retained as an independent audit/archive source.
The current central CI instead uploads bounded private GUI-failure
artifacts with one-day retention. See
`docs/operations/windows-runner-retirement.md` for archived runner
inventory, request commands and exact capability differences.
