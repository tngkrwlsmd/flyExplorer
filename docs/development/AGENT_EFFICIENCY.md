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

Define the completion condition, reusable evidence, minimum required
verification and expected call budget.

Default ceilings per user request:
- documentation/status task: 12 calls;
- general source modification plus build: 20 calls;
- real GUI/debug task: 30 calls.

These are safety ceilings, not targets. At 75% of a ceiling, re-evaluate the
plan. Essential verification must not be skipped merely to hit a budget.
Typical targets are 4-6 calls for docs/status, 8-12 for source plus one build,
and 16-24 for GUI/debug work.

## Reads and diagnosis

Read narrow-first. Do not repeatedly reread unchanged files/logs. Separate
static/source, compile, runtime, GUI-state and final-pixel evidence.

For the same apparent failure cause, retry at most twice before changing the
hypothesis. For GUI fixtures/harnesses, two consecutive failures without
independent product-defect evidence are a circuit breaker: stop debugging the
fixture and switch to a different bounded evidence path. Locale matching, UIA
virtualization, request serialization/encoding and screenshot harness failures
are not product defects by themselves. User-observed crashes/hangs/screens can
outweigh stale comments or old PASS logs.

## Builds and long operations

For the same revision/configuration, build once unless the first run was
inconclusive for an identified reason. Keep full output in ignored local logs;
surface only exit status plus the first relevant error or concise success.

Prefer one start plus one final/blocking read. This applies to GitHub Actions,
remote Windows tasks and local long-running commands, not only subprocesses.
Do not poll every few seconds, alternate status/log-tail probes, or repeatedly
read the same run while it is normally progressing.

For Actions specifically:
- after triggering or observing a long run, record run ID, target SHA, scope and
  start/current state;
- do not issue short-interval status reads while the normal runtime has not
  plausibly elapsed;
- make at most one later final/blocking status/log read unless new evidence
  indicates an actual stall or a distinct failure hypothesis;
- if that read still shows queued/running, end the response with the resume
  checkpoint rather than holding the chat turn open indefinitely;
- on resume, query current main/ref, the recorded run, artifacts and cleanup
  state first, then continue from completed evidence;
- never restart a completed build/test merely because the previous ChatGPT turn
  disconnected;
- for the same apparent failure, inspect the first relevant error and change
  the hypothesis before rerunning.

Typical CI scope on direct-main pushes:
- docs/status/agent-operation-only: no Windows VM workflow;
- source-contract-only tests or tools/policy: `source`;
- `src/base`, native fixtures, build/package/toolchain and other UI-independent
  changes: `release`;
- hard GUI paths (XAML, visual assets, owned GUI harness) and ordinary WinUI/
  runtime behavior changes: `release-gui`;
- nonvisual behavior-preserving `app/winui` work may use `release` when the
  logical-unit subject starts with `refactor:` or carries
  `CI-Scope: release`; hard GUI paths always override this and remain
  `release-gui`;
- `CI-Scope: release-gui` may promote any applicable push when stronger GUI
  evidence is desired;
- full Debug + Release remains explicit workflow_dispatch or a task-specific
  acceptance gate.

The automatic classifier is `tools/winui/resolve_validation_scope.py` and is
covered by source contracts. The `release` gate means policy + source +
Release native state fixture + canonical Release build + runtime-set check,
without the owned GUI suite. Do not label a functional/visual change as a
refactor merely to reduce CI cost.

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
`workflow_dispatch` remains available for human-operated commands. Use the
persistent checkout to preserve incremental build state and a stable
interactive desktop between iterations. Each job is not a persistent terminal
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
integrate safely rather than overwriting it. After push, use flyExplorer Actions
as the independent final acceptance gate. If that final gate fails, diagnose
the first relevant failure and return to the remote checkout for the next fix;
do not make repeated temporary task branches/commits the normal development
loop.

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
