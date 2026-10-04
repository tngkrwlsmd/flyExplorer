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
workflow-side fingerprint rejection is too late to prevent queue/runner waste.
This serialization rule is based on the current
`FLYEXPLORER_REMOTE_RUNNER_CAPACITY` workflow setting representing a single
interactive Windows execution lane. If runner capacity changes, re-evaluate the
global lease/concurrency rule instead of preserving single-runner serialization
by habit.

After starting a build or remote task, record its run ID, target commit and
scope. The governing principle is **no short-interval routine polling**.
The workflow-level settings `FLYEXPLORER_ROUTINE_OBSERVATION_SECONDS` and
`FLYEXPLORER_ACTIVE_MONITOR_SECONDS` define the current observation cadence;
do not duplicate their literal values in guidance. If completion becomes
independently known — for example the user reports completion/failure or a tool
returns a genuine completion signal — inspect the run immediately. Otherwise,
routine status reads wait for the configured routine observation interval. When
the user explicitly requests active monitoring, use the configured active
monitor interval, stop as soon as completion is observed, and never replace
that monitoring with a scheduled/automation task unless the user separately
asks for one. If a permitted read still shows the run active, leave the exact
run ID as the resume checkpoint instead of tight-loop polling. On a later
"continue the interrupted work" request, first read current main/ref state, the
recorded run, relevant artifacts and cleanup state; reuse completed evidence
for the same revision/configuration rather than rerunning it.

For one logical unit, use the workflow-configured
`FLYEXPLORER_DEFAULT_VALIDATION_RUN_BUDGET` as the normal planning budget, not
as an arbitrary correctness limit. Its purpose is to prevent
**diagnosis-free repeated execution**. Every successor run must follow a
completed predecessor, a concrete new revision or execution-condition change,
and a stated new failure hypothesis or evidence need. A run beyond the default
budget is allowed only when that additional hypothesis/evidence need is
explicitly justified; ordinal run number alone is neither a reason to run nor a
reason to stop. Never queue a speculative successor while its predecessor is
active.

High-cost fixtures are final acceptance tools, not harness-debug loops.
The current project-specific fixture profile and thresholds live in
`docs/development/VERIFICATION_PROFILE.md`; guidance must not duplicate those
numbers. Prove the harness/control lifecycle first with the smallest fixture
that exercises the same interaction, then spend the high-cost fixture only when
its evidence is actually required. If it exposes a harness bug after product
build/native evidence has passed, preserve those PASS stages and rerun only the
invalidated boundary after diagnosis.

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

Do **not** rerun the same GitHub Actions revision to see whether it passes on a
second attempt. Same-revision Actions reruns are prohibited for normal
development. A follow-up Actions run must correspond to a real new revision
that addresses an identified cause; it is a new acceptance run, not a retry.

### Mechanical validation-churn guard

Every `control/remote-shell` request must classify itself before the Windows
runner executes anything. In addition to `request_id`, `expected_main_sha`,
`working_directory` and `command`, the request JSON must provide:
`candidate_sha`, a stable `logical_unit`, `configuration`,
`validation_kind` as an array drawn from `source/build/native/gui/visual`
(or exactly `none`), and `invalidated_evidence` with one non-empty reason
for every declared validation stage. Routine non-validation shell/inspection
requests use `candidate_sha == expected_main_sha`, `configuration: none`,
`validation_kind: ["none"]` and an empty evidence object.

Before committing the request slot, perform a **request-metadata preflight in
the agent/tooling layer** instead of relying on the workflow to reject a bad
request after it consumes queue time. Check these invariants as one unit:

- `validation_kind == ["none"]` -> `configuration == "none"`,
  `candidate_sha == expected_main_sha`, and `invalidated_evidence == {}`;
- any validation stage (`source/build/native/gui/visual`) ->
  `configuration` is exactly `Debug` or `Release`, `candidate_sha` is
  the intended 40-hex revision, and `invalidated_evidence` contains exactly
  the declared stages with non-empty reasons;
- the command's recognizable source/build/native/gui/visual work matches the
  declared `validation_kind`;
- request ID/logical unit are non-empty and the pre-dispatch lease is clear.

Treat a workflow rejection of these request-shape rules as an **agent preflight
defect**, not as product evidence. Correct the metadata before doing any product
diagnosis.

Before any control-branch push, complete a **zero-run preflight** for avoidable
agent/control-plane errors. A Remote Windows Task must not be created until all
applicable checks below pass:

1. **Request shape:** validate the metadata invariants above, exact
   `expected_main_sha`/`candidate_sha`, evidence keys and stage/command
   agreement.
2. **Lease/ref existence:** confirm no active Remote Windows Task owns the
   request slot; verify every branch/ref/SHA/path the command will use actually
   exists before dispatch.
3. **Command sanity:** inspect quoting/escaping and PowerShell/JSON boundaries;
   keep request commands small and composed from previously working forms.
   Never use the Windows runner as the first parser for a newly invented
   multi-line quoting construct when it can be checked statically.
4. **Source/test sanity:** when tests/contracts changed, run or mechanically
   evaluate the narrowest affected contract before dispatch. Python harnesses
   must at least pass syntax compilation; `python -m` targets/import paths must
   resolve to tracked modules rather than being discovered by the runner.
5. **Harness/API sanity:** validate fixture paths, automation IDs and helper/API
   calls against the checked-in code or an established harness pattern. Do not
   invent pywinauto/UIA wrapper methods or assume a control API exists without a
   static/source check.
6. **Prose-contract hygiene:** semantic documentation assertions use normalized
   whitespace; raw line-sensitive matching is reserved for genuinely
   line-structured formats.

If one of these checks fails, fix it locally/in the agent layer and **do not
create a workflow run**. Classify failures caught here as request/contract/
harness preflight defects, not product defects. Windows-only behavior that
cannot be established statically belongs in the remote run, but the request
that reaches Windows should already be syntactically and structurally valid.

The request-slot workflow derives a validation fingerprint from
`candidate_sha + configuration + sorted(validation_kind)`. A fingerprint
already present in the control-branch request history is rejected before the
remote command runs. An exceptional repeat requires both a concrete
`retry_reason` and a changed `retry_revision` identifying the harness or
environment revision that makes the new attempt materially different; the same
retry revision cannot be reused for the same fingerprint. Common source/build/
native/GUI/visual commands are also checked against the declared stage set so
expensive work cannot be hidden behind `validation_kind: ["none"]`.

Both Windows workflows reject GitHub rerun attempts at the job boundary with
`github.run_attempt == '1'`; do not use the UI rerun button as a development
mechanism. Manual `workflow_dispatch` remains a human fallback and therefore
does not use request-history fingerprinting, but it remains subject to the
same no-rerun policy and must not replace the normal request-slot discipline.

Periodically review the recorded logical unit, validation kind and fingerprint
data. The target is zero diagnosis-free repeated validation, zero product-build
repeats after a harness-only fix, and zero duplicate same-candidate
fingerprints without a materially changed retry revision.

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
