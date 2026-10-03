# Agent efficiency and verification policy

This policy is mandatory for repository-changing work.

## Before tool calls

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
hypothesis. User-observed crashes/hangs/screens can outweigh stale comments or
old PASS logs.

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
- source-contract-only tests or tools/policy: source/policy scope;
- WinUI/src product code, GUI/runtime tests, build/toolchain/package or workflow
  changes: Release + GUI scope;
- full Debug + Release remains explicit workflow_dispatch or a task-specific
  acceptance gate.

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
flyExplorer product/runtime validation. Do not expand GitHub-hosted runners
into a substitute product build/GUI path. Do not run untrusted fork/PR code
automatically on the privileged self-hosted runner.

Treat runner/machine maintenance as a different operational responsibility from
flyExplorer validation. Prefer tngkrwlsmd/personal-control-plane for runner
health, Windows process/service/task-scheduler checks, recovery and machine
maintenance when available/authorized. Use flyExplorer's bounded remote task
only for project-specific commands that belong with this repository.

After normal push, fetch and verify HEAD == origin/main and ahead/behind 0/0.
Force push is prohibited. If origin/main moved unexpectedly, analyze rather
than overwrite.

## Final report

Report actual changes, verification performed, untested/open gates and necessary
follow-up. Never claim a test or certification that was not run.
