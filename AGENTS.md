# flyExplorer repository instructions

## Current product override

The canonical product on main is the C++/WinRT WinUI 3 application under
app/winui. Shared UI-independent code is under src/base; tests are under
tests/winui; canonical orchestration is tools/winui/run_checks.py.

The former MFC product is retired from the current checkout and recoverable
only from Git revision cbffb48. Do not recreate a persistent MFC/Phase5 tree on
main.

Higher-priority runtime/user instructions override this file. The vendored
.agent-policy core is upstream-managed generic policy from
tngkrwlsmd/universal-agent-docs; update that core atomically rather than
hand-editing individual generic files. Project facts belong in
.agent-policy/PROJECT.md, while flyExplorer-specific overrides belong here.

## Required current references

Before substantial work, use:
- docs/development/CURRENT_STATUS.md
- docs/development/ARCHITECTURE.md
- docs/development/AGENT_EFFICIENCY.md
- docs/development/ERROR_HISTORY.md for known/repeated failures.

Deleted dated migration reports are historical Git evidence, not current
instructions.

## Mandatory resume/current-state checkpoint

Before substantial work, and before continuing any interrupted or resumed task,
establish a fresh live repository snapshot **before touching the Windows VM or
re-reading an old run as if it were current**:

- read current `main` HEAD;
- read the recent main commit list (normally the latest 10 is enough);
- read recent main Windows CI runs and conclusions;
- compare the requested logical unit with those commits plus
  `docs/development/CURRENT_STATUS.md`.

If the target logical unit is already on main and has successful acceptance
evidence for that revision, treat it as complete and move to the next current
open item. Do not re-run or re-debug an already accepted unit merely because a
previous chat turn ended earlier. A stale control-branch run, temporary
worktree, local dirty checkout or pre-main acceptance run is evidence only for
its recorded SHA; it is never the repository baseline when live main has moved.

Only after this checkpoint may an old run be inspected in detail, and only when
the fresh snapshot shows that the run still belongs to unfinished current work.
This "latest main + recent commits + recent main CI" checkpoint is mandatory on
every resume.

## Build and verification

Supported root entry points:

    build.bat Debug|Release
    run.bat Debug|Release [path]
    test.bat source
    test.bat policy
    clean.bat build|all
    python -X utf8 tools\winui\run_checks.py full

Edit tracked project templates, not generated .vcxproj files. Keep build output
under ignored out/, NuGet cache under .cache/nuget/, and evidence under logs/.

Static/source, compile, runtime, GUI-state and visual evidence are distinct.
Do not claim unrun gates. Follow AGENT_EFFICIENCY.md call budgets and bounded
log rules.

When source tests assert prose/documentation meaning, compare a whitespace-
normalized form (for example `" ".join(text.split())`) unless exact line
breaks/indentation are themselves the contract. Do not make semantic guidance
tests fail merely because Markdown wrapped a sentence differently. Reserve raw
newline-sensitive assertions for formats where layout is structurally
significant, such as exact YAML/workflow blocks.

Canonical Windows full builds require Visual Studio/MSBuild 18.x, MSVC v145 x64
tools and Windows SDK 10.0.26100.0. Do not claim VS 2022/v143 full-build support
without a separately verified compatibility change. Product source-only Python
contracts are stdlib-only. The separate policy gate uses the hash-locked
.agent-policy/requirements.lock in a repo-local ignored .cache directory. GUI
automation additionally requires the exact pins in tests/winui/requirements-gui.txt
and an interactive Windows desktop.

Debug is Windows App SDK framework-dependent. Release is self-contained, but the
Release executable is not standalone: keep the complete out/winui/Release
runtime set, including helper, PRI/XBF and dependent DLLs.

## Architecture and safety

Potentially blocking Shell/provider calls must not run synchronously on the
XAML UI thread. Preserve isolated helper/supervisor behavior, route-token stale
result rejection, owned process boundaries and early-close cancellation.

Use test-owned directories/processes. Do not arbitrarily reset, discard,
overwrite or mutate user files/settings. Global clipboard, real Recycle Bin,
machine-wide install and similar OS-global effects are separate explicit gates.

ko-KR is the default for new app-owned UI. Preserve true UTF-8 Unicode and
validate real GUI behavior when relevant.

## SOLID and design-pattern policy

Architecture work must improve responsibility boundaries without introducing
ceremonial abstractions. Apply SOLID as a design test, not as a requirement to
create an interface/class for every function.

- **SRP first:** one owner for one reason to change. MainWindow is the XAML
  composition/presentation boundary; do not add new independent persistence,
  search, transfer, navigation or workspace state machines directly to it.
  File splitting alone is not responsibility splitting when methods still
  belong to one oversized owner.
- **OCP pragmatically:** stable closed sets such as small enums may use switch
  statements. Introduce Strategy/polymorphism only when behavior families
  genuinely vary or extension repeatedly requires editing unrelated code.
- **LSP through simple composition:** prefer final/value types and composition
  over inheritance hierarchies. A subtype must preserve the complete observable
  contract of its base; do not add inheritance merely to claim reuse.
- **ISP at subsystem boundaries:** keep native APIs small and purpose-specific.
  UI code should depend on only the operations it needs, not a catch-all file
  manager/service interface.
- **DIP where volatility warrants it:** isolate OS/Shell/async/persistence
  boundaries behind stable controller/facade/store seams when substitution,
  lifecycle control or testability benefits. Do not wrap deterministic value
  helpers in one-method interfaces without a real variation point.

Preferred project patterns:
- Window workspace state -> State/Coordinator ownership.
- Private session capture/restore -> Memento-style snapshot plus a caretaker/
  coordinator; serialization remains in src/base.
- Shell navigation/provider isolation -> Facade/Proxy plus Adapter from native
  results to presentation state.
- Watchers/async completion -> Observer/callback with weak UI ownership,
  cancellation and stale-route rejection.
- File operations -> request/command objects plus a coordinating controller;
  do not create one command class per button unless undo/queue/macro behavior
  requires it.
- View/render modes -> Strategy only after mode-specific behavior becomes large
  enough that switch-based closed-set handling is no longer simpler.
- Object creation -> keep a small explicit composition root. Add factories only
  when construction genuinely varies or tests need substitution.

For new or refactored UI behavior, prefer this ownership direction:

    MainWindow (XAML events/presentation)
        -> WindowWorkspaceController
        -> SessionCoordinator
        -> ShellNavigationController
        -> FileOperationController
        -> SearchController
        -> focused src/base values/services

These controller names describe responsibility boundaries, not a requirement to
create all of them before needed. Extract behavior-preservingly, one coherent
responsibility at a time.

Prohibited architecture shortcuts:
- growing MainWindow into a God Object;
- renaming/splitting files while retaining the same oversized owner;
- service locator/global mutable singleton state;
- interface-per-class/factory-per-class pattern inflation;
- deep inheritance for WinUI or Shell orchestration;
- moving WinUI/XAML types into src/base;
- broad rewrites that mix architecture extraction with unrelated feature
  behavior changes.

See docs/development/ARCHITECTURE.md for the detailed mapping and extraction
criteria.

## UI direction

Windows 11 File Explorer is the primary visual/interaction reference using
public WinUI/Windows APIs only. Preserve flyExplorer's dual-pane model. See
docs/development/UI_UX_DESIGN_GUIDE.md and
docs/development/WIN11_EXPLORER_UI_REFERENCE.md.

### Mandatory visual acceptance gate for user-visible UI changes

Any change that alters user-visible XAML/layout, spacing, typography, colors,
icons, command/navigation chrome, pane/list presentation, focus/selection/
hover/disabled states, dialogs, menus or other composited pixels requires the
visual QA loop in docs/development/UI_VISUAL_RETEST.md. Functional/UIA GUI PASS
alone is not sufficient acceptance for such a change.

For those changes:
- capture a BEFORE screenshot from the actual current product under a controlled
  test-owned fixture before the visual change;
- capture AFTER screenshot(s) from the changed actual product under like-for-like
  conditions (revision/binary, window size, theme, DPI/scale and fixture recorded);
- inspect the pixels for alignment, spacing, hierarchy, clipping/wrapping,
  density, focus/selection readability, theme/contrast and narrow-window/
  dual-pane behavior;
- compare BEFORE vs AFTER and classify intended vs unintended changes;
- if a material visual defect is found, fix it, recapture and review again;
- report functional GUI acceptance and visual acceptance separately.

Do not claim a user-visible UI task fully accepted if the screenshot review was
not performed. Report `VISUAL ACCEPTANCE: NOT TESTED` (or the precise blocked
state) instead. Pure behavior-preserving architecture/refactor work with no
composited-pixel change does not require new visual screenshots, but existing
GUI regression requirements still apply. Screenshots must use test-owned data
and must not expose or commit personal/private desktop content.

## External tools and CI

Do not use chatgpt-codex-connector unless the user explicitly requests or
permits it for the task. Normal GitHub connector/API access is allowed when
appropriate.

If the available GitHub connector/API does not expose a repository operation
needed for the current task, **do not stop at the connector gap and do not hunt
for an unrelated control path first**. Use this repository's
`control/remote-shell` request slot and persistent
`workflow-configured canonical persistent checkout` checkout as the next fallback for repository-scoped Git,
private Actions/run/artifact inspection, branch cleanup and other shell-capable
operations. Only move to RDC/desktop-control or another control plane when the
remote-shell path itself cannot perform the operation or the repository runner
is unavailable. A missing connector method is not, by itself, a reason to leave
a required repository action undone.

The repository-scoped self-hosted Windows runner is **not triggered by normal
main pushes**. `.github/workflows/windows-build.yml` is manual
`workflow_dispatch` only. Use `control/remote-shell` as the normal Windows
development surface for compilation, focused tests, runtime diagnosis and GUI/
visual evidence. Dispatch Windows VM Build only when the user explicitly asks
for it or a deliberate release/checkpoint gate materially needs an independent
one-off build. Its default manual scope is `release`; `release-gui` and
`full` are exceptional explicit choices.

Do not keep one ChatGPT response alive by repeatedly polling a long Actions
run. A Remote Windows Task has a **pre-dispatch lease**: before writing
`requests/remote-shell/request.json` or pushing the control branch, query the
recent `control/remote-shell` Actions runs. If any Remote Windows Task is
`queued`, `pending`, `waiting`, `requested` or `in_progress`, do not
modify the request slot and do not create a successor request. Record that run
ID and either wait for the normal observation point or leave a resume
checkpoint. This check must happen before the request commit because
workflow-side request validation is too late to prevent queue/runner waste.
The workflow concurrency group currently represents one interactive Windows
execution lane. If runner capacity changes, re-evaluate the global lease and
concurrency rule instead of preserving single-runner serialization by habit.

After starting a GitHub Actions build or Remote Windows Task, record its run
ID, target commit, scope, and Actions-reported start time. If the current user
request depends on that run's result, treat it as a blocking dependency and
**poll every 30 seconds while the Actions execution time is under three
minutes**. Do not end the response merely because the first read still says
queued/running during that window. As soon as completion is observed, consume
the result immediately and continue the dependent action in the same task.

The three-minute ceiling is measured from the Actions run's execution/start
time, not from when ChatGPT happened to notice the run. Once the run has been
executing for three minutes and is still active, stop waiting in that response
and leave the exact run ID, candidate SHA, and next action as the resume
checkpoint. If completion becomes independently known before the next scheduled
30-second observation — for example the user reports it or a tool returns a
genuine completion signal — inspect it immediately instead of waiting out the
interval. Do not poll faster than every 30 seconds, do not create a
scheduled/automation task merely to bridge the wait, and do not require the
user to separately ask for active monitoring when the current request already
depends on the run.

The 30-second observation cadence and 180-second same-turn ceiling are agent
policy and are not duplicated as workflow environment variables. A run whose
result is **not required to satisfy the current user request** may still be left
as a resume checkpoint without waiting through this window. On a later "continue the interrupted work" request, first read current
main/ref state, the recorded run, relevant artifacts and cleanup state; reuse
completed evidence for the same revision/configuration rather than rerunning
it.

For one logical unit, do not use a numeric retry token or workflow-side run
budget. Every successor run must follow a completed predecessor, a concrete
product/harness/execution-condition change, and a stated new failure hypothesis
or evidence need. Never queue a speculative successor while its predecessor is
active.

High-cost fixtures are final acceptance tools, not harness-debug loops.
The current project-specific fixture profile and thresholds live in
`docs/development/VERIFICATION_PROFILE.md`; guidance must not duplicate those
numbers. Prove the harness/control lifecycle first with the smallest fixture
that exercises the same interaction, then spend the high-cost fixture only when
its evidence is actually required. If it exposes a harness bug after product
build/native evidence has passed, preserve those PASS stages and rerun only the
invalidated boundary after diagnosis.

Before any high-cost E2E retry, isolate the failing layer with the cheapest
representative path. Classify the failure as **product**, **harness/fixture**, or
**control-plane/environment** from the first relevant evidence; do not let an
automation or orchestration defect masquerade as a product defect. For GUI
flows, validate the chain **input -> event -> model -> projection** explicitly,
using the smallest fixture that preserves the same interaction/lifecycle. A
high-cost E2E is the final acceptance gate after those lower-cost boundaries
converge, not the tool for discovering whether a UIA method, event route,
fixture, or control-plane command works. If a lower layer fails, fix that layer
and rerun only the invalidated boundary; rebuild or repeat the expensive E2E
only when a product/build change or a still-required final acceptance genuinely
invalidates its prior evidence.

For iterative Windows development, GUI work and Windows 11 benchmarking,
prefer this repository's fixed `control/remote-shell` request slot. Update
only `requests/remote-shell/request.json` on that control branch; every
request must include `expected_main_sha` equal to the live main SHA observed
by the mandatory resume/current-state checkpoint. The workflow rejects the
request before executing its command if main has moved. Its push triggers
`Remote Windows Task` on the repository-scoped interactive Windows VM and
executes against the workflow-configured canonical persistent checkout. Request commits are operational history and must never
be merged into main. This keeps product main limited to verified logical units
while still allowing GitHub tooling to command the development PC directly.
Manual `workflow_dispatch` remains the equivalent human-operated shell entry
point. The persistent checkout is the development state boundary; each Actions
invocation is a bounded command job rather than a persistent terminal process,
so batch the normal `investigate -> edit -> focused tests -> incremental build
-> owned GUI/evidence` loop into one request when practical, or at most two
requests when the first result genuinely determines the second. Do not create a
new remote job merely to rediscover facts already available from live main,
CURRENT_STATUS or completed run logs.

Classify each failure once from its first relevant error: product defect,
environment limit, or fixture/harness defect. For an unexplained GUI/input
failure, the **first diagnostic successor must locate the broken layer before
changing the interaction strategy**. Prefer a minimal environment-gated,
test-only diagnostic that records in one run: event entry/exit, resolved hit
target or geometry, drag/button/capture state, pointer or cursor coordinates and
deltas, and the observable UI result. Use that evidence to prove whether the
break is in event delivery, hit testing, drag-state transport, coordinate
conversion, model mutation, or rendering. Do not spend successive Windows runs
on alternative event/capture implementations while that boundary is still
unknown. Diagnostics must be inert in normal product runs and should be removed
or kept strictly gated once the cause is known.

Do not rerun the same product/test revision merely to see whether it passes.
Classify the first relevant failure and change the product, harness, or
execution condition that explains it before a successor validation.

### Mechanical validation-churn guard

Every `control/remote-shell` request must classify itself before the Windows
runner executes anything. In addition to `request_id`,
`expected_main_sha`, `candidate_sha`, stable `logical_unit`,
`working_directory` and `command`, new requests use exactly one purpose
model:

- diagnostic: `request_mode: "diagnostic"`, `configuration: "none"` and
  `validation_plan: []`;
- validation: `request_mode: "validation"`, configuration exactly Debug or
  Release, and a non-empty logical `validation_plan`.

Retry/reuse metadata is intentionally not part of the request schema. The
workflow does not inspect previous Actions runs or infer a second validation
plan from the free-form command. Read-only diagnostic work may continue when
main moved, but validation, write/destructive work and final acceptance remain
fail-closed against stale main.

Before committing the request slot, run the canonical request preflight and
confirm the pre-dispatch lease. Treat request-shape rejection as an agent
preflight defect, not product evidence.

Before any control-branch push, complete a **zero-run preflight** for avoidable
agent/control-plane errors. A Remote Windows Task must not be created until all
applicable checks below pass:

1. **Request shape:** validate mode/configuration/plan invariants, exact
   `expected_main_sha`/`candidate_sha`, request ID and logical unit.
2. **Lease/ref existence:** confirm no active Remote Windows Task owns the
   request slot; verify every branch/ref/SHA/path the command will use exists.
3. **Command sanity:** inspect quoting/escaping and PowerShell/JSON boundaries;
   keep request commands small and composed from previously working forms.
4. **Source/test sanity:** when tests/contracts changed, run or mechanically
   evaluate the narrowest affected contract before dispatch. Python harnesses
   must at least pass syntax/import-path checks.
5. **Harness/API sanity:** validate fixture paths, automation IDs and helper/API
   calls against checked-in code or an established harness pattern.
6. **Prose-contract hygiene:** semantic documentation assertions use normalized
   whitespace; raw line-sensitive matching is reserved for genuinely
   line-structured formats.

If one of these checks fails, fix it in the agent layer and **do not create a
workflow run**. Windows-only behavior that cannot be established statically
belongs in the remote run, but the request that reaches Windows should already
be syntactically and structurally valid.

The canonical zero-run request validator is
`tools/winui/validate_remote_request.py`. For GUI harness changes, the
canonical static guard is `tests/winui/test_gui_harness_contract.py`. Use
these checks locally or mechanically reproduce their assertions through
repository reads before writing the request slot. The Windows workflow's own
validation is only a second line of defense.

Do not use Actions rerun as the development loop. A successor validation exists
only after the identified product, harness, or execution condition has changed,
and it resumes from the earliest invalidated boundary.

### Remote development and final-CI anti-thrashing rule

Use `control/remote-shell` and the workflow-configured canonical persistent checkout
as the primary Windows development/debug surface. Compile errors, link errors,
native fixture failures, runtime diagnostics, focused UIA checks and controlled
screenshots should be investigated there before main is pushed. Batch related
commands in the remote shell instead of creating a sequence of one-observation
diagnostic workflows.

Windows VM Build is a **manual-only build/acceptance gate**, not a debugging
environment. Normal main pushes must not start it. When an independent gate is
actually needed, dispatch it once with the smallest intentional scope:
`source`, `release`, `release-gui` or `full`. The normal choice is
`release`; GUI/full are exceptional.

For user-visible UI work, complete targeted functional GUI and required
BEFORE/AFTER pixel review through the remote shell before the main push. Once that evidence is accepted, push one logical unit without automatically
starting a Windows workflow. If a deliberate manual build/checkpoint is needed,
dispatch it once after the push. If it fails, read the first relevant error,
return to the remote shell, make a concrete fix, and push a new revision.
Never press rerun and never create a validation-only commit whose only purpose
is to obtain another attempt.

Before pushing a verified logical unit to main, run or inspect the policy
readiness gate whenever a reviewed product path changed. Update
`.agent-policy/PROJECT.md` review metadata in the same logical unit when
required, so main CI is not spent rediscovering a known stale review revision.
Do not create separate publish/copy-only evidence workflows; the producing
remote-shell job should retain or report the evidence directly.

At the start of a remote development loop, fetch origin and inspect the current
branch, HEAD, `origin/main` and `git status --short`. Do not reset, clean,
discard or overwrite unexpected local work. If the checkout is clean and main
can be advanced normally, synchronize it with a fast-forward-only update.
Before push, fetch again and stop to analyze any unexpected movement of
`origin/main`; never force-push.

Use that persistent Windows checkout for the fast inner loop: edit files,
run the smallest meaningful source/native checks, perform incremental builds,
launch the test-owned GUI, capture/inspect controlled visual evidence and
repeat locally until the logical unit is ready. This is especially preferred
for Explorer/Win11 visual benchmarking and other tasks where keeping the same
interactive desktop, DPI, window geometry and fixture materially improves the
comparison. RDC or another desktop-control path is a supplementary tool, not
the default development transport: use it only when shell/UIA/screenshot
evidence cannot exercise the required interaction or when the repository
dispatch path is unavailable.

Direct-main remains the normal Git integration policy, but do not interpret it
as "push every intermediate edit." Commit/push only a verified logical unit.
A push by itself must not start Windows build/GUI validation. Use the persistent
remote checkout for the development loop; invoke the manual Windows build
workflow only for a deliberately requested one-off gate.

Runner health, process/service/task-scheduler inspection, runner recovery and
machine maintenance belong in `personal-control-plane`, especially when this
repository's runner path itself is broken. Do not create `remote/**` task
branches. The repository has one Git-backed Windows command channel:
`control/remote-shell`, plus manual `workflow_dispatch` as a human fallback.
The control branch is a minimal control-plane tree, not a product mirror. It
carries only the request slot plus a thin push-trigger workflow. The complete
Remote Windows Task implementation lives only on `main` as the reusable
`.github/workflows/remote-windows-task.yml`; the control trigger calls that
implementation explicitly at `@main`. Do not copy validation, path, artifact
or execution logic back into the control branch. Product source is always read
from or fetched into the workflow-configured canonical persistent checkout from
live `main`.

GitHub-hosted runners require explicit user approval and are not part of the
active flyExplorer CI path unless the user explicitly requests them. Do not add
a pull_request trigger that executes untrusted fork code on the privileged
self-hosted runner; use a separately isolated/unprivileged runner path if
untrusted PR validation is ever required.

## Git logical units

flyExplorer intentionally overrides the generic branch-first integration
default in the vendored policy. If commit/push is approved for the task, prefer
a verified logical unit directly on main. Use a separate work branch only when repository protection requires
it, the user requests it, concurrent work would make direct-main unsafe, or the
change needs isolated integration testing. Delete temporary work branches as
soon as their verified final tree is accepted on main; do not keep stale
work/* branches as historical checkpoints.

Before push, run git diff --check, inspect staged scope, and run the verification
required by the change. Normal main pushes do not trigger Windows VM Build at all. The workflow is
manual `workflow_dispatch` only, with `release` as its default. Use
`source` for an intentionally requested source/policy-only check,
`release` for a one-off native/Release build/runtime gate, and
`release-gui`/`full` only when explicitly needed. GUI and visual acceptance
for changed UI normally belongs to the pre-main remote-shell development loop. After normal push, fetch and verify HEAD == origin/main with
ahead/behind 0/0. Never force-push.

Do not push a state with a known required acceptance failure, temporary debug
instrumentation or generated artifacts.
