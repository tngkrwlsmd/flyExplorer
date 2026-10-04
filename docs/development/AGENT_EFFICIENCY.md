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

Control-branch requests also carry machine-checkable validation metadata:
`candidate_sha`, stable `logical_unit`, `configuration`,
`validation_kind`, and `invalidated_evidence`. The stage array is the exact
evidence frontier the request is allowed to exercise. A normal inspection or
Git-only request uses `validation_kind: ["none"]`; a validation request names
only the source/build/native/gui/visual stages invalidated by the current diff
and gives one concrete reason per stage.

The request workflow fingerprints validation as
`candidate_sha + configuration + sorted(validation_kind)` and rejects an
already-requested fingerprint before the remote command executes. Do not evade
this by making another control commit with an equivalent command. A materially
different retry is allowed only with both `retry_reason` and a changed
`retry_revision` for the harness/environment condition that invalidated the
prior attempt. The workflow also checks recognizable expensive commands against
the declared stage list. GitHub rerun attempts are skipped at the job boundary
in both Windows workflows.

Define the completion condition, reusable evidence, minimum required
verification and expected call budget.

Default ceilings per user request:
- documentation/status task: 12 calls;
- general source modification plus build: 20 calls;
- real GUI/debug task: 30 calls.

For the first 30-50 Remote Windows Task runs after the mechanical guard lands,
audit the recorded `logical_unit`, `validation_kind` and validation
fingerprints. Target normally <=2 validation runs per logical unit, zero
unchanged-product build repeats after a harness-only correction, and zero
duplicate same-candidate fingerprints without a changed retry revision.

These are safety ceilings, not targets. At 75% of a ceiling, re-evaluate the
plan. Essential verification must not be skipped merely to hit a budget.
Typical targets are 4-6 calls for docs/status, 8-12 for source plus one build,
and 16-24 for GUI/debug work.

## Reads and diagnosis

Read narrow-first. Do not repeatedly reread unchanged files/logs. Separate
static/source, compile, runtime, GUI-state and final-pixel evidence.

Do not retry a completed GitHub Actions run on the same revision. Zero
same-revision Actions retries is the default and required development policy.
Inspect the first relevant failure, classify it, fix the identified cause in
the persistent remote checkout, and only then create a new revision whose
single final run can provide new evidence. Locale matching, UIA virtualization,
request serialization/encoding and screenshot harness failures are not product
defects by themselves. User-observed crashes/hangs/screens can outweigh stale
comments or old PASS logs.

## Builds and long operations

For the same revision/configuration, build once unless the first run was
inconclusive for an identified reason. Keep full output in ignored local logs;
surface only exit status plus the first relevant error or concise success.

Prefer one start plus one final/blocking read. This applies to GitHub Actions,
remote Windows tasks and local long-running commands, not only subprocesses.
Do not poll every few seconds, alternate status/log-tail probes, or repeatedly
read the same run while it is normally progressing.

For builds/remote tasks whose expected runtime is within a few minutes, the
default first active GitHub status read is no earlier than three minutes after
submission unless completion is independently known. This is an anti-polling
floor, not a sleep requirement: establish the run once and make one
final/blocking read when the default observation point is reached. Completion
observed earlier may be consumed immediately. If the user explicitly requests
active monitoring for the current run, that request overrides the default
three-minute floor for that task only; poll no more frequently than every
30 seconds, stop immediately on completion, and do not create a scheduled or
automation task merely to bridge the observation window.

For Actions specifically:
- **before writing `requests/remote-shell/request.json` or pushing
  `control/remote-shell`, query the recent Remote Windows Task runs.** If any
  run is `queued`, `pending`, `waiting`, `requested` or
  `in_progress`, the request slot is leased by that run: do not submit,
  replace or pre-stage a successor request. This pre-dispatch check is required
  because workflow-side duplicate/fingerprint rejection still consumes queue
  time on the single self-hosted runner;
- after triggering or observing a long run, record run ID, target SHA, scope and
  start/current state;
- by default, do not issue short-interval status reads while the normal runtime
  has not plausibly elapsed. The first routine active status read is no earlier
  than three minutes after submission unless completion is independently known;
- when the user explicitly asks for active monitoring of the current run,
  30-second polling is allowed for that task only. Do not poll more frequently,
  stop as soon as completion is observed, and do not replace this with an
  unsolicited scheduled/automation task;
- without that explicit active-monitoring request, the three-minute rule is an
  anti-polling floor rather than a polling interval. If the first post-floor
  read still says queued/running, end the response with the exact resume
  checkpoint. Do not keep the same turn alive with repeated status reads;
- a second same-turn read is allowed only when a tool has produced a genuine
  completion signal, the user explicitly asks for current status, or a distinct
  failure hypothesis requires one bounded log read;
- if that read still shows queued/running, end the response with the resume
  checkpoint rather than holding the chat turn open indefinitely;
- on resume, query current main/ref, the recorded run, artifacts and cleanup
  state first, then continue from completed evidence;
- never restart a completed build/test merely because the previous ChatGPT turn
  disconnected;
- for the same apparent failure, inspect the first relevant error and change
  the hypothesis before rerunning.

Remote validation chain budget:
- one logical unit normally gets one primary Windows validation run;
- after that run completes with an identified failure, one focused successor is
  allowed after the relevant product/harness/environment change is committed;
- a third Windows validation run for the same logical unit requires explicit
  user approval before any control-branch request commit;
- never queue a successor while its predecessor is active, even if a harness
  fix has already been prepared;
- expensive 8,000+ or 20,000+ real-file GUI fixtures are final acceptance, not
  harness development. Smoke the same UI/control lifecycle on the smallest
  useful fixture first. If the expensive run reveals a harness-only defect,
  preserve product build/native PASS evidence and rerun only GUI/visual in the
  single focused successor.

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
VM and runs in `C:\dev\flyExplorer` by default. Never merge request commits
into main. Product main continues to record only verified logical units, while
the control branch records command history separately. Manual
`workflow_dispatch` remains available for human-operated commands. The
`control/remote-shell` branch is intentionally a minimal control-plane tree:
it carries the remote-shell workflow plus request slot, not a copy of product
source. The persistent checkout fetches live `main` for product work. Do not
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
against Windows 11 Explorer. RDC/desktop-control is supplementary; use it only
for interactions that shell, UIA or screenshot evidence cannot exercise or
when the repository dispatch path is unavailable.

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

Use `personal-control-plane` for runner health, Windows process/service/
task-scheduler checks, recovery and machine maintenance, especially when this
repository's runner/workflow path is broken. The committed-script `remote/**` task remains a fallback for
project-specific commands when the request-slot/dispatch path is unavailable or
unsuitable, or isolated branch execution is materially useful.

After normal push, fetch and verify HEAD == origin/main and ahead/behind 0/0.
Force push is prohibited. If origin/main moved unexpectedly, analyze rather
than overwrite.

## Final report

Report actual changes, verification performed, untested/open gates and necessary
follow-up. Never claim a test or certification that was not run.
