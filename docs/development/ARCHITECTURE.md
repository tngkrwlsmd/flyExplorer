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
      |-- SearchController            : IMPLEMENTED V8-E search/cancel/recent lifecycle
      |-- FileDetailController        : POST-AUDIT worker/cancel/Shell-visual lifecycle
      |-- PreferencesCoordinator      : POST-AUDIT-2 preference/write-order lifecycle
      '-- WorkspaceRestoreCoordinator : POST-AUDIT-3 restore request/settlement lifecycle

WindowWorkspaceController, SessionCoordinator, ShellNavigationController,
FileOperationController and SearchController are implemented, and the V8-A
through V8-E controller-extraction cycle is complete.

The subsequent MainWindow post-extraction responsibility audit is also complete.
Most remaining MainWindow work is presentation/composition. The audit found one
coherent leftover lifecycle subsystem: file-detail metadata/icon/thumbnail work.
FileDetailController now owns its pane-local cancellation tokens, detached
worker lifecycle and bounded Shell visual/thumbnail orchestration. MainWindow
retains DPI/request preparation, current route/tab/ticket acceptance,
DispatcherQueue/weak-UI handoff and final XAML projection.

A second MainWindow responsibility audit compared three concrete candidates:
preference-persistence async revision/mutex state, private drag/drop
state/async deferral and the workspace restore queue. Preferences persistence
had the strongest independent change/lifetime boundary and deterministic
acceptance seam, so PreferencesCoordinator now owns the Preferences value,
write mutex, latest-revision ordering and detached atomic-save worker.
MainWindow retains theme/view UI application, persistence triggering,
DispatcherQueue handoff and user-visible failure status.

Private drag/drop was not extracted because its physical pointer acceptance is
still a separate open gate. A focused Release probe confirmed that the
test-owned source ListViewItem is visible, enabled and selectable and that real
mouse coordinates are delivered, but neither the row nor ListView DragStarting
diagnostic status is reached; an identical final retry reproduced that result.
Because DragOver/Drop therefore remain unexercised, current evidence cannot
distinguish a product gesture defect from an automation/input limitation.
Changing drag ownership now would outpace the available runtime evidence.

A later workspace-restore lifecycle audit produced stronger evidence than the
earlier deferral. The old raw per-pane queue depended on ShellNavigation pending
state but did not own the identity of the request whose settlement should
advance that queue. A failed, rejected or no-change restore completion could
therefore clear model pending state and return before QueueNextWorkspaceTab(),
stalling later tabs. WorkspaceRestoreCoordinator now owns the per-pane restore
task queue, awaited navigation request id, settle matching and lane reset/cancel
semantics. MainWindow applies the validated workspace/model, submits Shell
navigation and projects UI; ShellNavigationController continues to own the
actual navigation worker/supervisor/watchers. Only the matching restore request
may advance a lane, and user navigation, tab/window context changes and close
reset restore state so stale completions cannot advance it.

Do not create another controller by default. Introduce a new boundary only when
concrete mutable-state, lifetime, change-reason or deterministic-test evidence
justifies it.

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

Large-folder navigation uses protocol-v3 helper pages of at most 1,024 entries
and 8 MiB. The first page is committed to the active Session immediately and
continuations are accepted only for the same route/request/folder and expected
logical offset. Snapshot logical coordinates (`baseOffset`/`nextOffset`) are
kept separate from `children.size()`. Current main still retains every accepted
child and enforces the 20,000-entry navigation safety ceiling, but continuation
identity no longer depends on resident vector length. This is the seam required
for a later bounded resident window. Do not raise or remove the 20,000 ceiling
until that window/index also defines backward access, selection identity and
the behavior of operations that require a complete folder such as global
sort/filter.


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
