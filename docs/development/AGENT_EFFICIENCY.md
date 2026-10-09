# Agent efficiency and verification policy

This policy is mandatory for repository-changing work.

## Before tool calls

### Mandatory resume/current-state checkpoint

On every new repository-changing task and every resumed/interrupted task, the
first repository read must establish **latest main + recent commits + recent
main CI** before any VM request, stale-run diagnosis or product implementation.
Normally one batched GitHub read should collect main HEAD, about 10 recent main
commits and the recent main Actions runs.

Compare that live snapshot with `CURRENT_STATUS.md` and the named logical
unit. If the work is already merged and accepted by CI, reuse that evidence and
advance; do not reopen the old unit. Runs from `control/remote-shell`,
temporary worktrees, dirty persistent checkouts and pre-main acceptance remain
SHA-scoped evidence only and must not override newer live main state.

Every control-branch request must carry `expected_main_sha` from that live
snapshot. The workflow must reject a stale request when current main no longer
matches, forcing the agent to refresh context instead of spending time on an
obsolete baseline.

Control-branch requests carry one machine-checkable purpose model in addition
to candidate SHA and stable logical unit. Diagnostic requests use
`request_mode: diagnostic`, `configuration: none` and an empty
`validation_plan`. Validation requests use `request_mode: validation`,
Debug/Release configuration and a non-empty logical plan.

Preflight that JSON **before the control-branch commit**. Validate the
mode/configuration/plan relationship and referenced SHAs/paths, but do not
regex-infer the command back into another stage declaration. Do not spend a
Remote Windows Task run discovering request-shape errors that the preflight can
catch locally.

### Zero-run preflight before Remote Windows Task

The request slot is the **last** step of preparation, not the first validation
tool. Before a control-branch push, catch cheap failures without consuming the
Windows queue:

- verify live main/candidate SHA, every referenced branch/ref/path and the
  pre-dispatch lease;
- validate request JSON mode/plan metadata;
- review PowerShell/JSON quoting and reuse a known-good command template rather
  than debugging fresh shell serialization on the runner;
- for changed Python tests/harnesses, perform syntax/import-path sanity and
  verify referenced scripts/modules exist;
- for changed source/documentation contracts, run or mechanically evaluate the
  narrowest affected assertion first, with whitespace-normalized prose checks;
- for GUI harness changes, verify fixture paths, automation IDs and UIA/helper
  API names against checked-in code or an already working harness before
  spending a physical GUI run.

A failure at this layer is a **preflight defect**. Fix it before dispatch and do
not count it as product validation. Do not create a Remote Windows Task merely
to learn that JSON metadata is invalid, a module cannot import, a branch does
not exist, a Markdown sentence wrapped, or an automation method name was
invented.

Use `tools/winui/validate_remote_request.py` as the canonical request-shape
validator and keep `tests/winui/test_gui_harness_contract.py` in the source
contract set for Python/pywinauto harness sanity. Run those checks locally when
a checkout/interpreter is available; otherwise mechanically evaluate the same
assertions from repository content before the request commit. This preflight is
not a reason to introduce GitHub-hosted/cloud compute, and it must not be
deferred into a Windows VM task. The self-hosted workflow checks are only a
fallback guard after the zero-run preflight already passed.

The request workflow deliberately does not maintain a second fingerprint or
prior-run reuse protocol. The request schema states the candidate, logical unit,
configuration and validation plan; the agent decides the smallest invalidated
boundary before dispatch.

Define the completion condition, reusable evidence, minimum required
verification and expected call budget.

Default ceilings per user request:
- documentation/status task: 12 calls;
- general source modification plus build: 20 calls;
- real GUI/debug task: 30 calls.

Periodically audit recorded logical units, request modes, validation plans and
failure classes. The target is zero diagnosis-free repeated validation and zero
unchanged-product build repeats after harness-only corrections.

These are safety ceilings, not targets. At 75% of a ceiling, re-evaluate the
plan. Essential verification must not be skipped merely to hit a budget.
Typical targets are 4-6 calls for docs/status, 8-12 for source plus one build,
and 16-24 for GUI/debug work.

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

For Actions specifically:
- **before writing `requests/remote-shell/request.json` or pushing
  `control/remote-shell`, query the recent Remote Windows Task runs.** If any
  run is `queued`, `pending`, `waiting`, `requested` or
  `in_progress`, the request slot is leased by that run: do not submit,
  replace or pre-stage a successor request. This pre-dispatch check is required
  because any workflow-side validation occurs only after scheduling and cannot
  recover queue time already consumed. The workflow concurrency group currently
  represents a single interactive execution lane; if runner capacity changes,
  re-evaluate the lease/concurrency policy;
- after triggering or observing a long run, record run ID, target SHA, scope and
  start/current state;
- if the current user request depends on the run result, use the Actions run
  start/execution time as the clock: poll every 30 seconds while elapsed
  execution is under three minutes, consume completion immediately, and
  continue the dependent action in the same task;
- do not end the response merely because an early read still says
  queued/running before the three-minute ceiling;
- once a still-active dependent run reaches three minutes of Actions execution,
  stop waiting in that response and leave the exact run ID, candidate SHA and
  next action as the resume checkpoint;
- never poll faster than every 30 seconds. Independently known completion may
  be inspected immediately;
- explicit active monitoring is not required for a run the current request
  already depends on, and it does not remove the three-minute same-response
  ceiling unless the user explicitly asks for a longer watch;
- when the run result is not required for the current request, it may be left
  as a resume checkpoint without waiting through the three-minute window;
- on resume, query current main/ref, the recorded run, artifacts and cleanup
  state first, then continue from completed evidence;
- never restart a completed build/test merely because the previous ChatGPT turn
  disconnected;
- for the same apparent failure, inspect the first relevant error and change
  the hypothesis before rerunning.

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

Normal direct-main pushes do **not** trigger the Windows VM workflow.
`.github/workflows/windows-build.yml` is manual `workflow_dispatch` only.
Use the persistent remote shell for ordinary Windows build/debug/test iteration.
When an independent one-off gate is materially useful, dispatch the smallest
scope deliberately: `source`, `release` (default), `release-gui` or
`full`. Do not dispatch merely because a commit was pushed.

`tools/winui/resolve_validation_scope.py` is retained only as an advisory
classification helper/source contract; it is not wired to a push trigger.
Targeted GUI/visual acceptance is normally completed pre-main through remote
shell.

Canonical orchestration is tools/winui/run_checks.py. Obsolete
experiments/phase6 paths must not be used.

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

When commit/push is approved for the task, commit and normal-push each
independently explainable verified logical unit. Before commit:
- git diff --check;
- inspect staged scope;
- run the verification required by the change.

Do not commit/push known failing required acceptance, temporary diagnostics,
generated artifacts or a known correctness defect.

Prefer direct-main logical units for normal repository work. Create a separate
work branch only when repository protection requires it, the user requests it,
concurrent work makes direct-main unsafe, or isolated integration testing is
materially useful.

The repository-scoped self-hosted runner remains the default for trusted
flyExplorer final product/runtime acceptance. Do not expand GitHub-hosted
runners into a substitute product build/GUI path. Do not run untrusted fork/PR
code automatically on the privileged self-hosted runner.

### Remote Windows development loop

For iterative Windows development, Win11 benchmarking and GUI refinement,
prefer the fixed `control/remote-shell` request slot. Write
`requests/remote-shell/request.json` only on that branch and include the
mandatory `expected_main_sha` from the current-state checkpoint. The workflow
rejects the request if live main has moved before execution. The request commit
triggers `Remote Windows Task` on the repository-scoped interactive Windows
VM and runs in the workflow-configured canonical persistent checkout by default. Never merge request commits
into main. Product main continues to record only verified logical units, while
the control branch records command history separately. Manual
`workflow_dispatch` remains available for human-operated commands. The
`control/remote-shell` branch is intentionally a minimal control-plane tree:
it carries the request slot plus a thin push trigger only. The full Remote
Windows Task implementation is reusable workflow code on `main`; the control
trigger calls it at `@main` and must not duplicate validation, path, artifact
or execution logic. The persistent checkout fetches live `main` for product
work. Do not
create `remote/**` command branches, and delete temporary `work/*` branches
after their accepted tree lands on main. Use the persistent checkout to
preserve incremental build state and a stable interactive desktop between
iterations. Each job is not a persistent terminal
session, so default to one batched request containing investigation, edit,
focused tests, incremental build and owned GUI/evidence when practical. Use a
second request only when the first result materially determines the next step;
avoid chains of diagnostic-only requests.

Begin by fetching and inspecting HEAD/origin/main and the worktree. Never use
reset/clean/checkout-overwrite to erase unexpected local changes. Fast-forward
a clean checkout when appropriate. During the inner loop, prefer the smallest
meaningful checks first, then incremental build and targeted owned GUI/visual
acceptance. Keep the same controlled fixture/DPI/window geometry when comparing
against Windows 11 Explorer.

If the available GitHub connector/API does not expose a repository operation
needed to continue the task, treat that as a tooling gap, not a task blocker.
Use `control/remote-shell` next for shell-capable repository operations,
including Git/branch cleanup and private run/artifact inspection when practical.
Do not spend tool calls searching unrelated APIs or switch to desktop control
while the repository remote shell can perform the operation. RDC/desktop-control
is supplementary; use it only for interactions that shell, UIA or screenshot
evidence cannot exercise or when the repository dispatch path is unavailable.

Do not push each intermediate edit merely because direct-main is the normal Git
policy. Finish and verify the logical unit in the remote checkout first. Fetch
again immediately before push; if origin/main moved unexpectedly, analyze and
integrate safely rather than overwriting it. A normal push does not launch Windows Actions. If an independent build gate is
deliberately requested, invoke the dispatch-only Windows workflow once; on
failure diagnose the first relevant error and return to the remote checkout.
Do not make repeated task commits or Actions runs the development loop.

### Remote shell first; Actions once

The Windows VM is not a CI debugger. Use the persistent remote-shell checkout
for normal Windows iteration: investigate, edit, compile, run focused native
tests, inspect runtime output, exercise targeted UIA and capture/review owned
screenshots there. Batch related diagnostics so one remote-shell request answers
the current hypothesis instead of spawning many micro-workflows.

For the first unexplained GUI/input failure, make the next focused diagnostic
answer **where the signal stops** before trying another interaction mechanism.
Prefer environment-gated diagnostics that expose event entry, hit target or
geometry, drag/button/capture state, cursor/pointer coordinates and deltas, and
the resulting UI/model boundary in the same run. Do not iterate
`Thumb -> capture -> root route -> another route`-style hypotheses one run at a
time without first proving which layer failed. Once the layer is known, make
one concrete fix and invalidate only the evidence affected by that fix.

For a given Git revision, do not rerun a failed job or workflow on that same
SHA. Windows Actions are not automatically started by pushes. If a deliberate
manual run fails, reuse its successful earlier steps, inspect the first relevant
error, fix the cause through the remote-shell development loop, and push a new
revision before any later manual gate.

Required GUI/visual acceptance is normally pre-main remote-shell evidence.
Windows VM Build is dispatch-only and should be used only when an independent
one-off build/acceptance gate is actually requested. Do not create a separate remote workflow
solely to publish, copy or rename evidence that the producing command could
retain or report. Before a main push that changes any path covered by project
policy review metadata, perform the policy readiness/preflight check and update
the review metadata in the same logical unit.

For Windows computer status, process/service/task-scheduler
inspection, runner recovery and maintenance, inspect `windows-vm-control`
first and use its existing capabilities or tracked `scripts/tasks/`
tasks when accessible and suitable. The verified
`personal-control-plane` central-CI/status-relay and runner-recovery
path remains the fallback when that project cannot perform the operation.
RDC is a last resort, not the normal control surface. Do not create
`remote/**` task branches.

After normal push, fetch and verify HEAD == origin/main and ahead/behind 0/0.
Force push is prohibited. If origin/main moved unexpectedly, analyze rather
than overwrite.

## Final report

Report actual changes, verification performed, untested/open gates and necessary
follow-up. Never claim a test or certification that was not run.
