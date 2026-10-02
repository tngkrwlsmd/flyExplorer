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

Prefer one start plus one final/blocking read. Do not poll every few seconds or
alternate log-tail/process probes. Use one status probe only for a genuine
timeout/stall question.

Canonical orchestration is tools/winui/run_checks.py. Obsolete
experiments/phase6 paths must not be used.

## GUI acceptance

Use test-owned folders/processes and validate the requested behavior. For UI
work distinguish input delivery, state change, and final composited pixels when
visual acceptance matters. Use targeted acceptance first, then the smallest
required regression.

## Evidence reuse

Reuse evidence only when binary/source revision, configuration, environment and
tested condition are unchanged. Do not relabel an older binary or different
DPI/environment as current acceptance.

## Git logical units

When commit/push is approved for the task, commit and normal-push each
independently explainable verified logical unit. Before commit:
- git diff --check;
- inspect staged scope;
- run the verification required by the change.

Do not commit/push known failing required acceptance, temporary diagnostics,
generated artifacts or a known correctness defect.

After normal push, fetch and verify HEAD == origin/main and ahead/behind 0/0.
Force push is prohibited. If origin/main moved unexpectedly, analyze rather
than overwrite.

## Final report

Report actual changes, verification performed, untested/open gates and necessary
follow-up. Never claim a test or certification that was not run.
