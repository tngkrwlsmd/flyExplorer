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

The optional F07 activity model is owned by
`app/winui/recent_activity_controller.h` as a bounded, in-memory value
controller. It holds no XAML references and does not persist, scan, or fetch
Explorer history. MainWindow forwards only successful accepted file-open and
active folder navigation events after user opt-in.

F14 in-session folder view overrides belong to
`app/winui/folder_view_controller.h`. It holds at most 64 explicit
normalized local folder→view entries and has no filesystem/persistence/UI
dependencies. The existing pane/session model retains the actual active view
mode, and asynchronous navigation only projects an override after accepted
navigation outside of workspace restoration.

F08 read-only ZIP metadata preflight is in `src/base/zip_inspection.h`.
It is a bounded parser without write/decompression APIs; the WinUI
context action owns an opt-in worker and suppresses stale WindowTab/PaneTab
results. A preflight acceptance does not certify data integrity or authorize
archive extraction.

The first F08 writer is `src/base/zip_store_writer.h`: a one-file,
bounded ZIP/Store-only creator. It owns CRC/header generation and
same-folder staged publishing without overwrite. Strict Store/Deflate
extraction and single-file Deflate creation live in separate F08 modules. `MainWindow::CreateSelectedZip` only dispatches
validated selection into a short-lived worker and applies UI refresh to the
origin WindowTab/PaneTab. Do not treat unexecuted code contracts as native
ZIP acceptance.

The next F08 native extractor is `src/base/zip_store_extractor.h`:
one in-memory, single-handle ZIP Store snapshot with strict one-file
header/offset/name verification and actual CRC32 calculation before output.
It uses the ZIP writer's owned staging and flush helper to publish one
flat extracted file without replacing existing content. The WinUI
`ExtractSelectedZip` action dispatches it off the UI thread and gates
feedback/refresh by exact workspace origin. The single-member action
has no cancellation guarantee and is not a general ZIP extractor.

Additional F08 flat multi-file Store creation is implemented in
`src/base/zip_store_batch_writer.h`. It takes only 2-8 explicitly selected
ordinary fixed-drive sibling files (total <=8 MiB), checks each file before
publishing a deterministic `flyExplorer-selection.zip` through owned
temporary staging without overwrite. Its ZIP headers carry one CRC32/name
and local offset per file. The WinUI dispatcher owns an exact WindowTab/
PaneTab/route origin and separate in-flight flag. The single-member
extractor intentionally rejects its multi-entry output. The batch
writer still emits only Store files and cannot archive directories.

F08 bounded multi-file extraction lives in `src/base/zip_store_batch_extractor.h`.
It checks every flat Store entry's local and central record and CRC32
against a single read-only snapshot before any file is written. An owned
staging directory holds only the new files; the whole directory is
published once without replacement as `flyExplorer-selection-unpacked`.
Failed staging cleans only known staging entries; no recursive directory
delete, no rollback of a user destination, and no general ZIP support
beyond strict Store/Deflate entries. MainWindow gates the background completion on the origin
WindowTab/PaneTab/route and has a separate ZIP-batch-extraction busy bit.

F08 batch ZIP Store creation/extraction now accept an optional
per-worker atomic cancellation token, owned by the UI and captured
by a detached worker. The existing toolbar Cancel command requests it
while retaining Shell cancellation. The native writers poll at bounded
I/O and before non-replace publication, returning Cancelled on a
pre-commit stop and using RAII staging cleanup. A rename already
committed cannot be undone. Single-file ZIP operations remain unchanged.

The F08 Store metadata compatibility policy lives in
`src/base/zip_store_compat.h`, reused by the one-file and batch
Store extractors. It permits DOS version 1.0/2.0 and matching DOS
timestamps and strict UTF-8 or unflagged ASCII-only names while
continuing to reject all extra/comment/data-descriptor/ZIP64/encryption
features. Pinned miniz 3.1.2 tinfl/tdefl codecs are now bundled,
while Windows MSZIP must not be treated as ZIP method-8 raw Deflate.

F08 single-member raw DEFLATE decoder is
`src/base/zip_raw_deflate.cpp` (paired `.h`). The native project
template compiles this as a separate no-PCH translation unit. Pinned
miniz v3.1.2 `tinfl` and `tdefl` are vendored under
`src/base/third_party/miniz_3_1_2`, with upstream copyright/license
and an explicit include adaptation. The decoder has NO filesystem or
ZIP path authority; it has a bounded allocation and validates exact
input consumption/output count. both ZIP extractors own
method 8 ZIP metadata, CRC32, path restrictions and non-replace staging.
The bounded batch extractor also permits a flat 2-8-member mix
of Store (0) and raw Deflate (8) using the same pinned native
`zip_raw_deflate` decoder. It gates each decompression on declared
output size, compression ratio, exact input/output count and CRC
before constructing the owned staging directory; the original
whole-directory non-replace publish and cancellation policy remains.
The batch ZIP writer still emits only Store files. A one-shot tinfl
call is not preemptible mid-call. All new code is NOT TESTED.

The first F08 **writer-side** raw DEFLATE codec is
`src/base/zip_raw_deflate_compress.cpp`/header, using miniz 3.1.2
tdefl compiled as an independent C source. A tightly scoped
`miniz_tdef_compat.h` fills only the monolithic miniz.h constants
and checksum helpers needed by tdefl. The single-file
`zip_deflate_writer.h` writes method-8 ZIP or falls back to method 0
when compression enlarges data or our own extractor would reject a
ratio above 100:1. Compressed output is round-trip verified through
the existing bounded raw inflater before staging. It uses a distinct
`<source>.deflate.zip` destination, no-overwrite publication, and
has no single-file cancellation UI. Unbuilt/unexecuted: NOT TESTED.

Regular-document activation belongs to `app/winui/file_open_controller.h`.
It owns one asynchronous Windows StorageFile/Launcher request, deadline and
close cancellation. MainWindow supplies weak presentation callbacks and checks
the active pane/tab/route/folder before launch and completion. This brokered
document path does not replace the isolated native navigation/context helpers
or implement unrestricted executable/virtual-Shell activation.

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

## Windows Search indexed filename boundary (Search v3)

`SearchController` retains epoch/cancel/route acceptance and dispatches
`SearchMode::WindowsIndex` to `scanIndexedFiles`, leaving traversal the
default. Only a bounded case-insensitive literal filename query on a local
non-reparse fixed-drive filesystem directory is eligible; other Search v2
criteria are rejected before starting the worker. The detached search worker
launches exact-owned `FlyShellIsolationHelper.exe --indexed-filename-search`
with restricted inherited handles, one-process kill-on-close Job Object and
a 12-second deadline. The helper alone executes the read-only Windows Search
`Search.CollatorDSO.1` `SystemIndex` OLE DB query, bounds return rows to
1,000 and serialized body to 1 MiB, verifies the scope and actual files, and
returns an explicit wire status. Query service errors and timeouts are
reported, never rewritten as traversal results. The isolated child uses the
current user token; the process boundary is fault isolation, not a sandbox.
The native oracle plus focused GUI task `37712395449` validated one real
indexed path. Property and virtual provider index searches are outside scope.

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

FileOperationController remains the transfer lifecycle owner, while the
filesystem/Shell mutation implementation stays in `src/base/shell_transfer_core`.
Copy and Move now cross an additional fault boundary: the controller's detached
worker invokes `shelltransfer::executeIsolated`, which starts the exact
`FlyShellIsolationHelper.exe --file-transfer` staged beside the app. The
parent passes only the bounded private transfer frame plus restricted inherited
stdin/stdout/error/cancel handles, assigns the child to a one-process
kill-on-close Job Object, streams progress and signals cancellation before a
bounded grace-period termination of that exact owned job. This is a
hang/cancellation boundary, not a security sandbox; the helper inherits the
user token.

Recycle deliberately does not use the Copy/Move helper mutation path. It
continues through `shelltransfer::execute` on the FileOperationController
worker and accepts only local fixed/removable roots with explicit recycle
confirmation.

Filesystem Copy/Move keeps direct-child/reparse/path-budget/collision
validation and additionally accepts mapped `DRIVE_REMOTE` roots and ordinary
direct UNC shares. Virtual Shell/provider sources use a distinct
`SourceMode::ShellProvider` that is **Copy-only** and requires a filesystem
destination. MainWindow serializes no COM interface: it copies the accepted
snapshot's parent and selected child desktop-absolute PIDLs into bounded value
blobs (32 KiB each, 1 MiB total) while retaining the common 1,024-item and
1,048,576 UTF-16 source-identity budget. Inside the exact-owned transfer helper,
the core validates PIDL framing, immediate parent/child relationship and
duplicate identity, creates `IShellItem` values from the PIDLs, queries
`SFGAO_CANCOPY`, obtains a materializable parent-relative leaf for collision
checking and queues `IFileOperation::CopyItem`. Provider Move and
Recycle/Delete remain fail-closed, as does provider-to-provider Copy. Extended/
device namespaces remain fail-closed for filesystem paths.

A separate `DestinationMode::ShellProvider` now supports **Copy-in from a
filesystem source to Windows' built-in Pictures Library only**. MainWindow
copies the currently accepted destination snapshot's absolute PIDL bytes
(no COM interface crosses the process boundary); private transfer wire v3
keeps source and destination modes independent. Inside the exact-owned
`--file-transfer` COM STA helper, the destination PIDL must equal
`FOLDERID_PicturesLibrary`. The helper then loads `IShellLibrary`, resolves
the effective default save folder and requires its safe, non-reparse filesystem
path to equal `FOLDERID_Pictures`. Only that concrete, revalidated destination
receives `IFileOperation::CopyItem` after leaf collision checks. Existing
source path/direct-child checks, Reject/explicit KeepBoth handling, 1,024-source
and 1 Mi UTF-16 identity bounds, 32 KiB PIDL bound, inherited-handle allowlist,
one-process Job Object, cancellation, progress and stale-route rejection
remain in force. Other provider destinations, custom library save folders,
provider Move/Recycle/Delete and provider-to-provider Copy are unsupported.
Focused real two-pane Pictures Library Copy-in acceptance passed on product/
test SHA `dfc8703394e8c750beaaaa7ee9cea9d81ddeba2c`, run `37705656407`;
arbitrary third-party provider writes are not certified.

The subsequent MainWindow post-extraction responsibility audit is also complete.
Most remaining MainWindow work is presentation/composition. The audit first
identified one coherent leftover file-detail lifecycle, which is now split by
change reason. FileMetadataController owns pane-local sortable type-key/size/
last-write collection, cancellation and stale-ticket lifecycle. Local fixed/
removable roots use its bounded detached filesystem worker; mapped
`DRIVE_REMOTE` and ordinary direct-UNC roots set `isolatedNetwork` and route
only sortable metadata through the exact-owned
`FlyShellIsolationHelper.exe --file-metadata` child. That path uses a bounded
private wire, restricted inherited handles, a one-process kill-on-close Job
Object, an inherited cancellation event, a 5-second inactivity watchdog and a
bounded cooperative-cancel grace before owned-job termination.

FileDetailController separately owns Windows type/icon/known-folder/thumbnail
visual enrichment and retains the 1,200-item bound. MainWindow accepts local
fixed/removable roots plus mapped `DRIVE_REMOTE`, ordinary direct-UNC
filesystem roots and virtual Shell/provider roots for type/icon detail; direct
UNC is classified as network before a parent-side drive probe. Removable and
network filesystem requests carry folder/file hints from the already accepted
navigation snapshot, so FileDetailController does not call
`GetFileAttributesExW` on those paths in the flyExplorer process.

Virtual-root requests keep filesystem paths empty and instead carry the
snapshot's desktop-absolute Shell parsing names over bounded private
`shell_visual_wire` v2. `shell_assoc_type_core` launches the exact-owned
`FlyShellIsolationHelper.exe --shell-item-visuals` child with an inherited
handle allowlist and one-process kill-on-close Job Object. Only that child calls
`SHParseDisplayName` and `SHGetFileInfoW(...SHGFI_PIDL...)` for provider
type/icon data. In Medium/Large Icons, FileDetailController flags at most four
non-folder records for provider thumbnails, preferring known image extensions;
for those records only the same helper calls
`IShellItemImageFactory::GetImage(SIIGBF_THUMBNAILONLY|SIIGBF_BIGGERSIZEOK)`.
The response frame separately bounds icon and thumbnail payloads. Cancellation
or 4.5 seconds without pipe progress terminates only the owned job. Provider
roots never enter filesystem attribute probing or the filesystem thumbnail
path.

Extension-based Windows type/icon lookup continues through the disposable
visual helper. Filesystem thumbnail client validation is lexical and rejects
`\\?\` / `\\.\`; the one-shot `--file-thumbnail` helper accepts fixed,
removable and remote filesystem roots and owns drive-type, component/reparse,
file-size and `IShellItemImageFactory` path access, while the client enforces
the existing bounded timeout with exact child termination. MainWindow retains request
preparation, current route/tab/ticket acceptance, DispatcherQueue/weak-UI
handoff and final XAML projection.

A second MainWindow responsibility audit compared three concrete candidates:
preference-persistence async revision/mutex state, private drag/drop
state/async deferral and the workspace restore queue. Preferences persistence
had the strongest independent change/lifetime boundary and deterministic
acceptance seam, so PreferencesCoordinator now owns the Preferences value,
write mutex, latest-revision ordering and detached atomic-save worker.
MainWindow retains theme/view UI application, persistence triggering,
DispatcherQueue handoff and user-visible failure status.

Private drag/drop remains in MainWindow because the gesture, active pane/route
identity, selected rendered rows, DataPackage deferral and transfer handoff are
one short-lived UI interaction rather than an independent lifetime owner.
Physical pointer acceptance is now established: ListViewItem handled-event
routing is observed on press, cursor/button movement is polled across control
capture, and the Windows drag threshold feeds the current PointerPoint into
StartDragAsync. The existing DragStarting path then creates the private data
package and the drop path revalidates source/destination context before handing
off to FileOperationController. Remote Windows Task `37277431952` proved the
owned Release two-pane Korean-file drag-copy with normal process exit.

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
and 8 MiB. The first page is committed immediately. `Snapshot::nextOffset`
tracks the furthest validated enumeration frontier independently from the
resident range `[baseOffset, residentEndOffset())`.

Normal unsorted, unfiltered browsing uses a 2,048-entry resident window.
Forward page acceptance can trim the oldest prefix. Backward navigation requests
an exact range ending at the current `baseOffset`, prepends it, then trims the
tail. Forward navigation from an older resident window can request a known range
below `nextOffset` without incorrectly advancing the frontier. Route/request/
folder identity and exact offset/range checks still reject stale or overlapping
results.

Global operations must not treat a partial resident window as a complete
folder. Name sort and name/mask filtering now use a bounded lightweight
`ShellNavigationSession::nameIndex_` outside the 2,048-entry resident
window. An owned 20,500-file GUI/visual scenario passed indexed name
sort and filtering in run `37211942616` (merged product revision
`582560f89afe8c9c53bbc23791cdbd5d3335c014`).

The complete resident sortable metadata model stays capped by
`kMaxCompleteModelEntries=20000`. A separate **local fixed-drive-only**
indexed metadata mode now permits type/size/modified-date sorting
beyond that bound without storing all Shell rows in the resident model.
`FileMetadataController` requires complete, valid indexed metadata
and bounds the request to `kMaxIndexedMetadataEntries=25000` and
`kMaxIndexedMetadataPathUnits=12*1024*1024`. Indexed logical item
identities, route/ticket freshness, cancellation and fail-closed
metadata collection protect against partial/stale global ordering.
Removable/UNC/mapped-network and arbitrary Shell providers still refuse
global metadata sorting above 20,000.

The actual owned fixed-drive 20,500-entry GUI test passed indexed
size/date/type sorting in `38055029443`. A 960x519 Dark matched
app-window before/after screenshot review (`38056349169`) showed
a correct first type-sort item, total count and preserved pane layout.
The 25,000 ceiling is an implementation bound, not a 25,000-item
performance or correctness acceptance.

Sequential browsing retains the independent
`kMaxBrowseEntries=100000` safety limit, 1,024-entry/8 MiB Shell
transport pages and the 2,048-entry resident window. No general
100,000-item sorted-folder throughput is certified.

File-list rows carry logical `uint64` item indices, not resident-vector
positions. Consumers translate them through `Snapshot::residentIndex()`
before open, rename, transfer, clipboard, context-menu or private-drag actions.
`PaneState::renderedBaseOffset` keeps selection restoration tied to the window
that rendered the row. Rows remaining resident can restore selection by parsing
path; an evicted row is intentionally not kept as a hidden cross-window
selection.


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
