# flyExplorer current architecture

## Repository boundaries

- app/winui — canonical WinUI 3/C++/WinRT application and XAML.
- src/base — UI-independent native state, navigation, file operation,
  session/preferences and Shell-support code.
- tests/winui — source contracts, native fixtures, owned GUI automation and
  explicit manual gates.
- tools/winui — bounded build/test orchestration.
- out — ignored generated binaries/intermediates.
- .cache/nuget — ignored local package cache.
- logs — ignored local validation evidence.

Generated flyExplorer.vcxproj files are materialized from tracked project
templates. Edit the templates, not generated project files.

## UI/state ownership

    Window
    └── WindowTab[]
        ├── active pane + split state/ratio
        ├── LeftPane
        │   └── PaneTab[]
        │       ├── current Shell location
        │       ├── Back/Forward history
        │       └── view/sort/column state
        └── RightPane
            └── PaneTab[]

Theme/language are application preferences. Window geometry and active Window
Tab are session state. A pane owns its pane-local tab collection; a PaneTab owns
its navigation identity/history.

V8-A makes workspace ownership concrete in
app/winui/WindowWorkspaceController. The controller owns the WindowTab
collection, active WindowTab index, identity allocation and live workspace
state transitions.

V8-B makes private-session lifecycle ownership concrete in
app/winui/SessionCoordinator. The coordinator owns session epoch/revision,
serialized snapshot capture, save/load/clear workers, legacy-v1-to-live-state
restore preparation and close invalidation. MainWindow retains XAML-only window
size/split projection, status text, Shell/watcher route release and final
presentation refresh. Serialization format and validation remain UI-independent
in src/base/ui_session.

## SOLID rules for this codebase

SOLID is used to preserve change boundaries, not to maximize the number of
classes or interfaces.

### Single Responsibility Principle (primary rule)

A responsibility is a reason to change. Presentation, workspace-state
transition, persistence, Shell navigation, search, transfer/clipboard and
lifecycle coordination are separate reasons to change.

MainWindow is allowed to:
- receive XAML events;
- translate UI input into controller calls;
- project controller/native state back into XAML;
- participate in the top-level composition/lifetime boundary.

MainWindow should not gain a new independent state machine or persistence/
worker subsystem. Existing oversized MainWindow responsibilities should be
extracted behavior-preservingly when touched by substantial work.

A separate .cpp file containing MainWindow methods is still MainWindow
responsibility; physical file separation does not satisfy SRP.

### Open/Closed Principle

Prefer the simplest closed representation that matches the domain. Enums and
switches are acceptable for deliberately closed sets such as a small finite
theme or view-mode set.

Use a strategy/polymorphic seam when:
- new variants repeatedly modify multiple unrelated branches;
- each variant has substantial behavior/lifecycle of its own; or
- runtime substitution is a real product/test requirement.

Do not replace every switch with subclasses.

### Liskov Substitution Principle

The product intentionally favors composition, final classes and value objects.
Do not create inheritance hierarchies solely for reuse. Where a substitutable
base/interface exists, every implementation must preserve success/failure,
ownership, cancellation, lifetime and side-effect contracts expected by callers.

### Interface Segregation Principle

Subsystem seams should expose focused operations. Prefer small APIs such as
request/validate/execute, load/save/clear, or submit/forget/shutdown over a
catch-all application service. A caller should not receive file mutation,
session, search and Shell-provider operations through one wide interface.

### Dependency Inversion Principle

High-level workspace/UI policy must not depend on low-level Shell/COM process
details more than necessary. Stable seams are most valuable at:
- Shell/provider/process boundaries;
- persistence/storage boundaries;
- asynchronous worker/watcher boundaries;
- functionality that needs deterministic test substitution.

Do not create an interface around pure value transformations merely to satisfy
DIP. Composition roots may know concrete implementations; ordinary UI behavior
should not repeatedly construct and coordinate low-level infrastructure.

## Design-pattern map

Use patterns only where they clarify an existing responsibility.

### State / Coordinator — window workspace

WindowTab/Pane/PaneTab values represent state. Transition rules for create,
activate, close, split, active pane and tab ownership belong to one workspace
coordinator rather than being distributed across XAML handlers.

Preferred direction:

    MainWindow
        -> WindowWorkspaceController
             -> WindowTabState[]
             -> Pane/PaneTab state

State objects should remain mostly values; do not push XAML behavior into them.

### Memento — private session

ui_session is the serializable snapshot/store boundary. Session orchestration
should be separated into:
- origin state: workspace/controller state;
- memento: fxfile::uisession::Session and nested DTOs;
- caretaker/coordinator: capture, save/load, legacy v1 mapping, v2 restore,
  epoch/revision invalidation and close cancellation.

Serialization remains UI-independent in src/base.

### Facade / Proxy / Adapter — Shell integration

IsolatedShellSupervisor is a bounded proxy/facade over helper processes and
Shell calls. ShellNavigationController is the focused owner that coordinates
supervisor/watcher requests and adapts IsolatedResult/Snapshot values into
workspace state.

The implemented controller owns the supervisor, filesystem watcher, Shell
namespace watcher, watch route/token state, request submission, stale
route/request completion checks and route release/suspend/shutdown lifecycle.
MainWindow retains the DispatcherQueue/weak-UI handoff plus status and XAML
projection only; pipe, Job object and COM extension details stay outside XAML
handlers.

### Observer — watchers and asynchronous completion

Directory/Shell watchers and worker callbacks use observer-style completion.
Callbacks must preserve:
- weak/no-use-after-close UI ownership;
- cancellation before dispatcher teardown;
- route/request/epoch stale-result rejection;
- no synchronous provider work on the XAML thread.

### Command/request object — file operations

File mutation/transfer behavior should be represented by bounded request data
and coordinated execution. Current Kind/Request/Report forms are preferred over
one heap-allocated command subclass per toolbar button.

Introduce richer Command objects only when undo/redo, durable queues,
composition/macros or independently schedulable commands become real
requirements.

### Strategy — variable behavior families

Use Strategy for behavior families only after variants own meaningful distinct
logic. Candidate examples are future complex file-view rendering modes or
provider policies. Current small closed-set switches are acceptable until that
threshold is reached.

### Composition root / Factory

Concrete supervisor/watcher/store construction belongs at a small explicit
composition boundary. A dedicated factory is warranted only when implementation
selection varies by configuration/environment or deterministic tests need
replacement. Avoid factory-per-class architecture.

## Target controller boundaries

The current/evolutionary direction is:

    MainWindow
      |-- WindowWorkspaceController  : IMPLEMENTED V8-A state/transition owner
      |-- SessionCoordinator          : IMPLEMENTED V8-B session caretaker/lifetime
      |-- ShellNavigationController   : IMPLEMENTED V8-C navigation/supervisor/watchers
      |-- FileOperationController     : IMPLEMENTED V8-D transfer/file-command lifecycle
      '-- SearchController            : search request/cancel/recent state

WindowWorkspaceController, SessionCoordinator, ShellNavigationController and
FileOperationController are implemented. SearchController remains the next
future extraction candidate, not a mandate for a big-bang rewrite. Create the
next controller only when a coherent responsibility is being changed or
extraction materially reduces coupling/race risk.

Controllers under app/winui may depend on WinUI only when presentation/
DispatcherQueue coordination requires it. Move a component to src/base only
when its public contract is genuinely WinUI-independent.

## Refactor acceptance rules

Architecture refactors must normally be behavior-preserving:
- do not combine responsibility extraction with unrelated UX/feature changes;
- keep session schema compatibility unless migration is the explicit task;
- preserve Shell process/watcher/cancellation safety boundaries;
- retain real exit-0 requirements and protected user-settings invariants;
- add focused source contracts for new ownership seams;
- run targeted GUI acceptance for any moved lifecycle/state behavior, then the
  smallest required regression.

Avoid these anti-patterns:
- God Object/MainWindow accumulation;
- Service Locator or mutable global singleton state;
- interface/factory/class proliferation without a variation point;
- deep inheritance for orchestration;
- XAML/WinRT leakage into UI-independent src/base code;
- pattern names used as justification without a measurable change boundary.

## Shell isolation

No third-party Shell provider or potentially blocking Shell extension call may
be introduced synchronously on the XAML UI thread.

The app uses a bounded two-lane native Shell supervisor,
FlyShellIsolationHelper.exe as a disposable process boundary, independent
filesystem and Shell namespace watchers, route/request tokens to reject stale
results, weak UI references with DispatcherQueue handoff, and cancellation
before window dispatcher teardown.

The helper is a bounded fault/isolation boundary, not a security sandbox.

## Session persistence

Private session schema v2 stores only bounded validated state. Persisted
filesystem history is converted to safe path values rather than retaining COM
interfaces. Existing v1 sessions remain readable. Source is authoritative for
the exact numeric limits.

## Build/runtime

Canonical root entry points:

    build.bat Release
    run.bat Release
    test.bat source
    python -X utf8 tools\winui\run_checks.py full

Release is Windows App SDK self-contained; Debug is framework-dependent. Do not
distribute flyExplorer.exe alone: sibling resources and
FlyShellIsolationHelper.exe are required.

## Change placement

Put reusable non-UI behavior in src/base when it has no WinUI dependency. Keep
presentation/UI orchestration in app/winui. Do not recreate the retired MFC
tree or a permanent hybrid UI.
