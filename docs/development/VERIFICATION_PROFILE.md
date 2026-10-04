# flyExplorer verification profile

This document holds mutable project-specific verification values that should not
be duplicated in policy/guidance text. Behavioral principles live in
`AGENTS.md`, `.agent-policy/PROJECT.md` and
`docs/development/AGENT_EFFICIENCY.md`.

## Remote Windows operational settings

The single source for current remote-shell operational tunables is the top-level
`env` block in `.github/workflows/remote-windows-task.yml`:

- `FLYEXPLORER_CANONICAL_CHECKOUT` — canonical persistent Windows checkout.
- `FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS` — default routine observation interval.
- `FLYEXPLORER_ACTIVE_MONITOR_SECONDS` — explicit active-monitor interval.
- `FLYEXPLORER_REMOTE_RUNNER_CAPACITY` — current interactive Windows execution capacity.
- `FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET` — normal validation planning budget.

Guidance references these setting names and their purpose, not their literal
values. When runner capacity changes, revisit request-slot serialization and the
workflow concurrency group.

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
