# Agent efficiency and verification policy

This policy is mandatory for repository-changing work.

## Before tool calls

### Mandatory resume/current-state checkpoint

Before any new or resumed repository task, read current `main` HEAD,
about ten recent commits, current central CI status and
`docs/development/CURRENT_STATUS.md`. Historical Runner runs,
local checkouts and test snapshots are SHA-scoped evidence only.

The source-specific Runner and `control/remote-shell` control branch
were retired. Resolve all new Windows operations through
`tngkrwlsmd/personal-control-plane`. Read its live request slot, active
Remote Shell runs and registered central CI status before dispatch.
Always identify the exact target source SHA, target, scope, prerequisite
state and completion criterion. No stale request may overwrite active work.

### Zero-run preflight before central requests

Prepare the request before reserving Windows VM time:

- Verify the current `flyExplorer/main` SHA and whether earlier CI evidence
  already satisfies this logical unit.
- Check central Remote Shell and manual CI jobs for an active lease; never
  replace a queued/running request or launch duplicate work.
- For central CI, require registered project `desktop-a`, reviewed full
  40-character `main` SHA and an explicitly selected
  `health`/`source`/`release`/`gui`/`gui-probe` scope.
- For central Remote Shell, verify the exact target `windows-vm`,
  working directory, command quoting, relevant paths/refs and source
  preflight. Restore its single request file to idle after completion.
- Validate changed Python import paths/syntax, local source contracts,
  test-owned fixture paths, GUI automation APIs and semantic Markdown
  checks before consuming the VM queue.

Request-shape failures are agent preflight defects, not product acceptance.
Do not turn an invalid request into another Windows run. Work within a
sensible call budget without skipping essential correctness checks. The
retired source-side request validator and workflow are historical only.

## Reads and diagnosis

Read narrow-first. Do not repeatedly reread unchanged files/logs. Separate
static/source, compile, runtime, GUI-state and final-pixel evidence.

For prose/documentation source contracts, normalize whitespace before semantic
substring checks unless exact newlines/indentation are the behavior under test.
A Markdown line wrap must not create a validation run; newline-sensitive
assertions are appropriate only for structurally formatted content such as an
exact workflow/YAML block.

Do not retry the same product/test revision merely to see whether it passes.
Inspect the first relevant failure, classify it, and change the product,
harness, or execution condition that actually explains the failure before a
successor validation. Locale matching, UIA virtualization, request
serialization/encoding and screenshot harness failures are not product defects
by themselves. User-observed crashes/hangs/screens can outweigh stale comments
or old PASS logs.

## Builds and long operations

For the same revision/configuration, build once unless the first run was
inconclusive for an identified reason. Keep full output in ignored local logs;
surface only exit status plus the first relevant error or concise success.

Prefer one start plus one final/blocking read. This applies to GitHub Actions,
remote Windows tasks and local long-running commands, not only subprocesses.
Do not poll every few seconds, alternate status/log-tail probes, or repeatedly
read the same run while it is normally progressing.

For result-dependent GitHub Actions / Remote Windows Tasks, treat the run as a
**blocking dependency** and use a fixed bounded wait policy: record the Actions
start time, poll every **30 seconds**, and keep the same task open while the
run's Actions-reported execution time is under **three minutes**. An early queued/running read is not a reason to end the
response during that window. Consume completion immediately and continue the
dependent work. If the run is still active when its execution time reaches
three minutes, leave the exact run ID, candidate SHA and next action as the
resume checkpoint instead of waiting longer in that response.

Do not poll faster than every 30 seconds. If completion becomes independently
known between observations, inspect it immediately. The user does not need to
ask separately for active monitoring when the current request already depends
on the result. Do not create a scheduled/automation task merely to bridge the
wait. The 30-second observation cadence and 180-second same-turn ceiling are agent
policy; they are not duplicated as workflow environment variables.

For the central Actions path specifically, record the run ID,
source SHA, registered project/scope, Actions start time and conclusion.
Inspect completion when available. For a result-dependent active run,
observe at no more than a 30-second cadence and leave a precise resume
checkpoint if the action remains active at the three-minute execution
boundary. Do not perform duplicate validation solely because an old
conversation or request ended.

Remote validation chain discipline:
- every successor requires a completed predecessor, a material product/harness/
  execution-condition change, and a concrete new failure hypothesis or evidence
  need;
- never queue a successor while its predecessor is active;
- high-cost fixtures are final acceptance, not harness development. Their
  current project-specific profile lives in
  `docs/development/VERIFICATION_PROFILE.md`. Smoke the same lifecycle on the
  smallest useful fixture first and preserve unaffected PASS evidence.

Before repeating any expensive E2E, perform layered failure isolation on the
cheapest representative case. First decide whether the first relevant error is
a **product defect**, **harness/fixture defect**, or
**control-plane/environment defect**. For GUI behavior, trace the same
interaction through **input -> event -> model -> projection** on a small fixture
before returning to the high-cost fixture. Do not use the expensive fixture to
discover whether pywinauto/UIA input semantics, event delivery, stale wrappers,
fixture assumptions, command serialization, or runner orchestration are valid.
Fix the identified layer, preserve unaffected build/runtime PASS evidence, and
rerun only the invalidated stage. The expensive E2E is run after lower-cost
evidence has converged, as final acceptance.

Normal `flyExplorer/main` pushes do **not** start Windows validation.
The old local `windows-build.yml` and `remote-windows-task.yml`
workflows were retired with their dedicated Runner. Independent Windows
acceptance is requested manually from
`personal-control-plane` Central Registered Projects CI and is
specific to the exact source commit. Its `gui` scope does not prove
the old Debug+Release `full` profile.
The remaining `tools/winui/resolve_validation_scope.py` helper is
advisory and does not trigger CI.
Use `tools/winui/run_checks.py` for local product orchestration;
do not return to obsolete phase6/experimental paths.

## GUI acceptance

Use test-owned folders/processes and validate the requested behavior. Distinguish
input delivery, state change and final composited pixels.
For asynchronous work, verify durable outputs and settled state, not transient watcher/toast/status messages as the sole success signal.

For any user-visible UI change, final-pixel review is mandatory rather than
optional:
1. capture a controlled BEFORE screenshot from the actual current product;
2. implement the change and run targeted functional GUI acceptance;
3. capture like-for-like AFTER screenshot(s);
4. visually review alignment, spacing, hierarchy, clipping/wrapping, density,
   focus/selection/disabled readability, contrast/theme and relevant
   narrow-window/dual-pane states;
5. if the review finds a material regression, fix it and repeat capture/review;
6. only then run the smallest required regression.

Record revision/binary, theme, DPI/scale, window dimensions and fixture with the
visual evidence. Keep screenshots in ignored evidence or CI artifacts unless a
tracked fixture is explicitly required; never capture personal filenames or
private desktop content.

Functional GUI acceptance and visual acceptance are separate gates. A
functional/UIA PASS with no screenshot review must be reported as
`VISUAL ACCEPTANCE: NOT TESTED`, not as complete UI acceptance. Actual
125/150/200% scaling, High Contrast, human Narrator/Korean IME and other
environment-specific gates remain NOT TESTED unless they were really exercised.

Behavior-preserving refactors that do not alter composited pixels do not require
fresh screenshots; they still require the relevant GUI regression and normal
process-exit evidence.

## Evidence reuse

Reuse evidence only when binary/source revision, configuration, environment and
tested condition are unchanged. Do not relabel an older binary or different
DPI/environment as current acceptance.

## Architecture/refactor discipline

For SOLID/design-pattern refactors:
- start from a concrete oversized responsibility or volatile dependency, not a
  pattern name;
- extract one coherent owner at a time and preserve behavior;
- prefer composition and small value/request APIs over inheritance;
- do not add abstraction layers unless they reduce coupling, isolate an OS/
  async boundary, or enable a real substitution/test seam;
- require a focused contract for the new ownership boundary;
- do not combine architectural extraction with unrelated visual/feature work;
- after state/lifecycle extraction, run targeted GUI acceptance including
  normal process exit before deciding whether a full GUI regression is needed.

A smaller architecture with fewer unnecessary abstractions is preferred over a
textbook pattern graph that increases call depth and debugging cost.

## Git logical units

Commit and push only independently explainable, verified logical units.
Check `git diff --check`, staged scope, required policy review and
applicable source/Windows gates before publication. Do not include debug
instrumentation, generated files or known broken acceptance results.
Prefer direct `main` for normal nonconcurrent work, or an isolated
short-lived branch/PR when concurrent edits or validation risk warrants it.
Do not force push or overwrite unexpected work.

### Central Windows development and acceptance

For focused debugging, use `personal-control-plane` Remote Shell
and a verified source checkout. Fetch and inspect HEAD, origin/main and
`git status` before modifying anything. Keep tasks bounded, reuse
unaffected evidence, and inspect native/UIA failures from the first
relevant error. A follow-up requires a changed product/test/execution
condition and a stated new hypothesis.

For independent acceptance, manually request
`central-flyexplorer-ci.yml` in `personal-control-plane` with
`desktop-a`, the exact trusted source `main` SHA and an intentional
scope. Central `source`, `release` and `gui` replace the respective
old source-scoped CI purposes, not the old Debug+Release `full` profile.
The central SYSTEM service controls jobs; GUI tests use a separate
logged-in and unlocked interactive user desktop.

Keep `evidence/remote-windows` as the historical allowlisted Git
archive; current central failures generate private short-retention
artifacts. Never upload user profile files, credentials, raw traces or
unreviewed desktop images. No separate per-repository Runner or
`control/remote-shell` branch should be recreated.

For machine service, task scheduler or runner recovery, use
`personal-control-plane` first. RDC is a fallback only when central
control or the shell/UIA evidence cannot satisfy the task. No new
`remote/**` task branches. After push, fetch and verify HEAD and
origin/main agree; resolve unexpected movement without force pushing.

## Final report

Report actual changes, verification performed, untested/open gates and necessary
follow-up. Never claim a test or certification that was not run.
