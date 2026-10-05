# flyExplorer verification profile

This document holds mutable project-specific verification values that should not
be duplicated in policy/guidance text. Behavioral principles live in
`AGENTS.md`, `.agent-policy/PROJECT.md` and
`docs/development/AGENT_EFFICIENCY.md`.

## Remote Windows operational settings

The top-level `env` block in `.github/workflows/remote-windows-task.yml`
mirrors the current remote-shell operational policy:

- `FLYEXPLORER_CANONICAL_CHECKOUT` — canonical persistent Windows checkout.
- `FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS` — 30-second dependent-run observation interval.
- `FLYEXPLORER_ACTIVE_MONITOR_SECONDS` — 30-second explicit active-monitor interval.
- `FLYEXPLORER_RESULT_DEPENDENT_MAX_WAIT_SECONDS` — 180-second / three-minute same-turn wait ceiling for result-dependent Actions runs.
- `FLYEXPLORER_REMOTE_RUNNER_CAPACITY` — current interactive Windows execution capacity.
- `FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET` — normal validation planning budget.

The 30-second observation interval and three-minute ceiling are deliberate
repository policy and are intentionally repeated in the maintained guidance so
future conversations do not reinterpret them away. When runner capacity changes,
revisit request-slot serialization and the workflow concurrency group.

## Current high-cost fixture profile

These are current project facts, not generic policy:

- The owned large-folder GUI acceptance fixture at 8,000 files is high-cost and
  should be reserved for final acceptance after cheaper lifecycle checks pass.
- The 20,000-entry aggregate/model safety boundary can make boundary probes
  high-cost. That number is also a product safety bound where encoded by product
  contracts; it is not a generic validation-run threshold.

Change this profile when the project fixture strategy changes. Do not copy these
numbers back into the general development rules.

## Remote workflow ownership

The full Remote Windows Task implementation is
`.github/workflows/remote-windows-task.yml` on `main`. The
`control/remote-shell` branch carries only request data and a thin push
trigger that calls the reusable implementation at `@main`. Operational logic
must not be duplicated into the control branch.
