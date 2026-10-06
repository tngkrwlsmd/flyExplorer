# flyExplorer project facts

This file contains current project-specific facts only. Generic policy remains
in the vendored .agent-policy core.

Vendored generic policy provenance: tngkrwlsmd/universal-agent-docs commit
bafb40f55dcb6aa15f432b391ba5487b87759e0e. Upstream-managed .agent-policy files are synchronized as one
consumer core; this PROJECT.md remains project-owned across bundle refreshes.

<!-- project-facts:start -->
```json
{
  "profile": "consumer",
  "facts": {
    "repository_root": {"value": ".", "status": "Confirmed", "evidence": "path:."},
    "primary_source": {"value": "app/winui", "status": "Confirmed", "evidence": "path:app/winui"},
    "build_command": {"value": "build.bat Release", "status": "Confirmed", "evidence": "command-source:.github/workflows/windows-build.yml::build.bat Release"},
    "test_command": {"value": "test.bat source", "status": "Confirmed", "evidence": "command-source:.github/workflows/windows-build.yml::test.bat source"},
    "runtime": {"value": "Windows 11 / Visual Studio 18.x / Python 3.14.x", "status": "Confirmed", "evidence": "manual:project self-hosted Windows runner preflight and current build policy"},
    "deploy_command": {"value": "", "status": "Unknown", "evidence": "manual:public deployment/signing remains an open gate"},
    "deploy_target": {"value": "", "status": "Unknown", "evidence": "manual:public deployment target is not certified"}
  },
  "components": [
    {"name": "winui-app", "path": "app/winui", "responsibility": "C++/WinRT WinUI 3 application"},
    {"name": "base", "path": "src/base", "responsibility": "UI-independent native values and services"},
    {"name": "winui-tests", "path": "tests/winui", "responsibility": "source, native and owned GUI contracts"}
  ],
  "review": {
    "reviewed_revision": "36b46b96973ef4777f96dffc64413e3c9d548ca5",
    "reviewed_at": "2026-10-06",
    "reviewed_paths": [
      "app/winui",
      "src/base",
      "build.bat",
      "test.bat",
      ".github/workflows/windows-build.yml",
      ".github/workflows/remote-windows-task.yml",
      "tools/winui/run_checks.py",
      "packaging",
      "tests/winui"
    ]
  }
}
```
<!-- project-facts:end -->

## Canonical product

- Repository: tngkrwlsmd/flyExplorer.
- Canonical branch/worktree: main / workflow-configured canonical persistent checkout.
- Product: C++/WinRT Windows App SDK WinUI 3 file manager.
- Product source: app/winui.
- Shared UI-independent native code: src/base.
- Tests: tests/winui.
- Orchestration: tools/winui/run_checks.py.
- Generated output: ignored out/; package cache: ignored .cache/nuget/;
  local evidence: ignored logs/.
- Retired MFC product is absent from the working tree; exact historical recovery
  starts from Git revision cbffb48.

## Current product checkpoint

Current main includes V8-A WindowWorkspaceController, V8-B SessionCoordinator,
V8-C ShellNavigationController, V8-D FileOperationController and V8-E
SearchController responsibility extraction. Live Git refs take priority.

Current accepted UI/state includes functional top-level Window Tabs, dual panes
with pane-local tabs, Explorer-like navigation/chrome, private session schema v2
restore, WindowWorkspaceController ownership of top-level workspace state,
ShellNavigationController ownership of isolated Shell navigation/watcher
orchestration, FileOperationController ownership of transfer/file-command
worker lifecycle, cancellation, stale completion and collision/recycle
continuations, and SearchController ownership of bounded search request
identity, cooperative cancellation, stale completion rejection and recent-scope
state/persistence. The V8-A through V8-E extraction cycle is complete. The
post-extraction MainWindow responsibility audit is also complete and extracted
one additional coherent lifecycle boundary: FileDetailController now owns
pane-local detail cancellation, detached metadata/icon/thumbnail workers and
bounded Shell visual orchestration. A second responsibility audit then selected
preferences persistence over drag/drop and workspace restore sequencing:
PreferencesCoordinator owns the Preferences value, write mutex, revision
ordering and detached atomic-save worker. A later restore-lifecycle audit
identified an independent request/settlement boundary, so
WorkspaceRestoreCoordinator now owns pane-local restore queues, awaited
navigation request identity and settle/reset/cancel semantics. MainWindow
retains theme/view presentation, persistence triggering, workspace/model
application, Shell submission, DispatcherQueue handoff and status projection.
Large Icons is now an accepted fifth view mode (stable value 4) with private
preference/session persistence, a 64 px Shell visual path and bounded image
thumbnail use. Pre-main owned GUI evidence measured fully visible items at
112x128 with 120x132 pitch against the controlled Explorer Large Icons
baseline of 105x131 with 118x132 pitch; owned thumbnails were visible,
the GUI exited 0 and protected user settings remained unchanged.
File-list Known Folder artwork now resolves Desktop, Documents, Downloads,
Pictures, Music and Videos through a fixed-key, disposable Shell helper path.
The detail worker matches OS Known Folder paths off the UI thread, the helper
returns bounded pixels, and generic folder artwork remains the fallback.
Pre-main before/after evidence changed all six targeted rows from generic
folder icons to their native Windows artwork with process exit 0.
NavigationSidebar now reuses the same six fixed Known Folder keys on a
background worker and applies 16 px native pixels on the UI dispatcher.
Home and This PC retain their existing Fluent glyphs, while each Known Folder
button keeps its prior glyph as a failure fallback. Controlled 972x720 Dark
visual acceptance showed all six sidebar artwork images visible at 16x16,
aligned with the Windows 11 Explorer navigation motifs, with before/after
process exit 0.

Persistent WinUI filesystem bookmarks are now part of the accepted product
surface. Bookmarks use the private %LOCALAPPDATA%\flyExplorer\bookmarks-v1.txt
profile with atomic replacement, case-insensitive path deduplication and a
bounded 100-item model. The active pane's filesystem folder can be added from
the always-visible bookmark bar, reopened from the bar, renamed or deleted from
the management surface and restored after process restart. Legacy MFC bookmark
configuration is never read automatically; explicit import reads only
name/path entries and skips malformed, duplicate or unsupported items.

Local filesystem Shell enumeration now uses protocol-v3 page transport with at
most 1,024 entries and 8 MiB per helper response. The first page is accepted
immediately, normal browsing keeps a 2,048-entry resident window, and UI rows
remain progressively rendered in 160-row increments. Complete-model operations
remain bounded by 20,000 entries, while sequential resident-window browsing has
a separate 100,000-entry safety ceiling. Current owned GUI evidence reaches
20,500 entries; the 100,000 value is not a performance/certification claim.

Search remains owned by the bounded asynchronous SearchController lifecycle.
The default is file-only, case-insensitive literal name search; optional
criteria include ECMAScript regex, case sensitivity, file/folder/both targeting,
single extension, minimum/maximum file size, inclusive local modified-date and
bounded literal file-content matching. Up to 20 private condition sets may be
saved. Content decoding supports deterministic Auto UTF plus explicit CP949 and
Windows-1252 fallbacks, with 1 MiB per file and 16 MiB per search. The depth-5,
2,500-entry walk and 100-result bounds, cancellation and stale-result rejection
remain in force; content regex, indexed/provider/property search and unrestricted
deep content scanning are not implemented.

Physical same-app file drag is accepted through the existing private drag/drop
path and hands transfer work to FileOperationController after source/destination
revalidation. The explicit row StartDragAsync path also exposes public Windows
StorageItems asynchronously under the DragStarting deferral, with Copy-only
requested/allowed operation; the private same-app token remains present and is
still checked first on flyExplorer drops. Owned physical acceptance copied a
Korean test file from flyExplorer into a fresh test-owned Windows Explorer
window, and a focused successor re-proved same-app private-token cross-pane drag
without product changes. File transfer entry points share one bounded native
budget: at most 1,024 source items and 1,048,576 aggregate UTF-16 source-path
units. This replaces the historical 32-item copy/move/recycle/clipboard/drag cap
while remaining fail-closed above the shared bounds; owned evidence includes a
real 64-item IFileOperation copy, 64-item CF_HDROP round-trip and 64-item WinUI
cross-pane copy. Explorer-compatible `Ctrl+Shift+N` is also accepted for
create-folder and routes through the existing
`fxfile::filecommand::Kind::CreateFolder` command path for the active pane/tab;
historical F11 is intentionally not restored because it conflicts with current
Windows/File Explorer behavior.

## Development loop and verification budget

flyExplorer uses a deliberately narrow development loop. The goal is the
smallest evidence set that proves the changed behavior, not maximum repeated
confidence. This project is stricter than the generic retry allowance where the
rules below differ.

### Plan the verification frontier before running the VM

- Define one logical implementation unit and its concrete acceptance claims
  before editing. Map each unresolved claim to the lowest layer that can prove
  it: static/source contract, compile, native/runtime, focused GUI, or visual.
- Before every remote run, compare the current candidate with the last revision
  that already has valid evidence. Explicitly identify which prior evidence was
  invalidated by the new diff. Do not rerun a stage whose relevant product,
  build input, runtime path, or presentation did not change.
- Test-only, harness-only, documentation-only and control-plane-only revisions
  do not invalidate an already successful product build or product runtime
  result unless they alter how that evidence was produced or interpreted.
  Reuse the existing binary and prior PASS evidence when valid.
- Catch obvious compile/test-fixture mistakes through diff/static review before
  paying for a Windows VM run. A remote run should answer a remaining product
  question, not be the first syntax review of a test harness.

### Machine-enforced remote validation metadata

The fixed `control/remote-shell` request slot now records the validation
frontier in data rather than relying only on prose. Every request includes
`candidate_sha`, stable `logical_unit`, `configuration`,
`request_mode` and `validation_plan`. Diagnostic requests use mode
`diagnostic`, configuration `none` and an empty plan. Validation requests
use mode `validation`, Debug/Release configuration and a non-empty logical
plan. The workflow does not regex-infer the command back into a second stage
declaration.

The request schema is intentionally small. Candidate SHA, configuration,
logical unit and validation plan state the check directly; the workflow does
not maintain a second fingerprint/reuse protocol or inspect previous Actions
runs before execution. A moved main SHA is advisory for read-only diagnostics
but fail-closed for validation, write/destructive work and final acceptance.

Do not rerun the same product/test revision merely to see whether it passes.
After a failure, classify the first relevant error and change the product,
harness, or execution condition that explains it before a successor
validation. Resume from the earliest invalidated boundary and preserve
unaffected successful evidence without encoding it into remote request
metadata.

### Default verification ladder

Use only the rows required by the change:

1. **Docs/policy/test-only change:** static diff/review and the narrowest
   relevant source/contract check if one exists. Do not run a Windows build
   merely because the repository is a Windows application.
2. **Windows C++/project/XAML compile input changed:** perform static/source
   checks first, then one canonical Release build. A second build requires a
   product/build-input change that invalidated the first build.
3. **Runtime semantics changed:** after a valid build, run one focused native
   or runtime scenario that directly exercises the changed behavior. Prefer an
   established focused fixture over a broad regression harness.
4. **GUI interaction semantics changed:** run one focused owned-GUI scenario
   only when the behavior cannot be established at a lower layer. Do not append
   unrelated GUI flows after the relevant acceptance boundary.
5. **Visual/layout/artwork changed:** perform matched visual acceptance once,
   after functional evidence passes. If pixels/layout/artwork did not change,
   do not create visual evidence unless the user explicitly asks for it.
6. **Cross-cutting protocol/schema/shared-build change:** a broader source
   suite or helper regression is justified only when no narrower trustworthy
   contract covers the affected boundary. It is still run once per invalidated
   revision, not as a default companion to every build.

For a normal logical unit, the default Windows-VM verification budget is
**one canonical Release build plus one focused runtime or GUI acceptance**.
Expensive fixtures such as multi-thousand-file folders, broad GUI walks,
Explorer benchmark capture, DPI/visual sessions or full runtime matrices are
final-acceptance gates, not iteration loops. Exercise each expensive fixture at
most once after cheaper evidence has converged, unless a later product change
directly invalidates that fixture's result.

### Failure and retry rules

- Stop at the **first relevant failure** and classify it as product,
  test-harness, or environment/control-plane before changing anything.
- **Never rerun the same product/test revision.** This includes a same-SHA
  Actions rerun and an equivalent remote-shell command issued only to see
  whether it passes the second time.
- flyExplorer permits **zero automatic result-based retries**, including a
  speculative "one more try" for apparently transient failures. A later run is
  justified only after the cause has been identified and the code, harness, or
  execution condition has materially changed.
- After a new revision, resume at the **earliest invalidated failure boundary**
  and run only dependent downstream stages. Do not replay the entire
  source -> native -> build -> GUI -> visual chain by default.
- A harness-only correction does not justify rebuilding unchanged product
  binaries. A visual-only/XAML correction does not justify repeating unrelated
  native semantics. A product algorithm change does invalidate the relevant
  build/runtime evidence and should restart from that specific boundary.
- If the requested focused behavior already passed and a later unrelated broad
  harness tail fails, preserve the focused PASS evidence, diagnose the unrelated
  tail separately, and do not rerun the broad harness as a condition of the
  focused feature's acceptance.
- Once the required evidence is successful, stop. Do not add another run,
  screenshot, fixture size, or harness solely for additional confidence.

### Remote-shell and CI discipline

- The persistent `control/remote-shell` checkout is the normal Windows
  development surface. Batch only the stages that are currently required; do
  not include earlier PASS stages "for completeness".
- Before every request-slot commit, preflight the current request schema locally/
  in the agent layer. A diagnostic request uses
  `request_mode: "diagnostic"`, `configuration: "none"` and an empty
  `validation_plan`. A validation request uses
  `request_mode: "validation"`, configuration exactly `Debug` or
  `Release`, a non-empty logical `validation_plan`, the intended
  `candidate_sha` and the live `expected_main_sha`. Do not infer a second
  stage declaration from free-form command text. Workflow rejection for these
  invariants is an agent preflight defect and should never be used as
  product-failure evidence.
- The request-slot commit is allowed only after a **zero-run preflight** has
  cleared avoidable control/harness errors: referenced refs/SHAs/paths exist,
  command quoting is structurally valid, changed Python harnesses have syntax
  and import-path sanity, changed prose/source contracts have the narrowest
  local/static check, and new GUI automation IDs/API calls are verified against
  checked-in code or an established harness. If any of those checks fail, fix
  them before dispatch; do not create a Remote Windows Task to discover them.
- The canonical local/static request validator is
  `tools/winui/validate_remote_request.py`; GUI harness API/syntax traps are
  guarded by `tests/winui/test_gui_harness_contract.py`. Apply those checks,
  or mechanically reproduce the same assertions from repository content, before
  the request-slot commit. Do not add GitHub-hosted/cloud compute for this
  preflight and do not substitute a Windows VM run for a missing local/static
  check. The remote workflow remains only a second-line guard.
- Treat missing modules, nonexistent branches, invalid request metadata,
  PowerShell/JSON serialization mistakes, brittle Markdown line-wrap
  assertions and nonexistent UIA/pywinauto methods as **preflight defects** by
  default. They are not product failures unless independent product evidence
  proves otherwise.
- If the available GitHub connector/API does not expose a repository operation
  needed for the task, use `control/remote-shell` as the immediate
  repository-scoped fallback when the operation is shell-capable. This includes
  Git/branch cleanup and private run/artifact inspection when practical. Do not
  declare the task blocked, leave required cleanup undone, or switch to
  RDC/another control path merely because a connector method is missing.
- **Pre-dispatch lease:** before writing `requests/remote-shell/request.json`
  or pushing the control branch, query recent Remote Windows Task runs for
  `control/remote-shell`. If any run is `queued`, `pending`, `waiting`,
  `requested` or `in_progress`, do not touch the request slot and do not
  create a successor request. Record the active run ID and wait/resume from it.
  Workflow-side request validation is only a second line of defense because it
  occurs after scheduling and cannot recover queue time already consumed.
  The workflow concurrency group currently represents a single interactive
  execution lane. If capacity changes, re-evaluate the lease and concurrency
  policy instead of carrying the single-runner assumption forward.
- If the current user request depends on a GitHub Actions / Remote Windows
  Task result, that run is a blocking dependency. Record the Actions start time
  and poll every **30 seconds** while its reported execution time is under
  **three minutes**. Do not end the response after an early queued/running read
  during that window. Consume completion immediately and continue the dependent
  action in the same task. If the run is still active once its Actions
  execution time reaches three minutes, stop waiting in that response and leave
  the exact run ID, candidate SHA and next action as the resume checkpoint.
  Independently known completion is inspected immediately; never poll faster
  than 30 seconds or create an automation merely to bridge this wait. The user
  does not need to separately request active monitoring for a result-dependent
  run. The 30-second observation cadence and 180-second same-turn ceiling are
  agent policy, not workflow environment settings.
- Do not use a numeric retry token or workflow-side run budget. Every successor
  must have a completed predecessor, a material product/harness/execution-
  condition change, and a concrete new failure hypothesis or evidence need.
- For an unexplained GUI/input failure, the first diagnostic successor must
  establish the failing layer before the interaction mechanism is changed.
  Prefer environment-gated test diagnostics that capture event entry, hit
  target/geometry, drag or button/capture state, pointer/cursor coordinates and
  deltas, and the resulting model/UI boundary in one run. Do not burn Windows
  runs on competing event-routing hypotheses until that boundary is proven.
- High-cost fixtures are final acceptance only. Their current project-specific
  sizes/thresholds live in `docs/development/VERIFICATION_PROFILE.md`, not in
  policy text. First prove the harness/control lifecycle on the smallest
  fixture that exercises the same path, and preserve unaffected PASS evidence
  if a high-cost fixture later exposes a harness defect.
- Before any high-cost E2E successor, classify the first relevant failure as
  **product**, **harness/fixture**, or **control-plane/environment**, then
  isolate the broken boundary on the smallest fixture that preserves the same
  lifecycle. For GUI paths, prove **input -> event -> model -> projection** in
  order before using the expensive fixture again. High-cost E2E is final
  acceptance, not discovery for UIA/automation semantics, stale wrappers,
  fixture assumptions, request serialization, runner routing or other
  orchestration defects. Fix only the identified layer and rerun only the
  invalidated boundary; repeat the expensive fixture only when its acceptance
  evidence was genuinely invalidated.
- For a result-dependent Actions run, the normal same-response observation
  window is bounded: check every 30 seconds until completion or until the run's
  Actions execution time reaches three minutes, whichever comes first. Only
  after that three-minute ceiling may an unfinished required run be left as a
  resume checkpoint. A run that is not required for the current request may be
  checkpointed immediately. Do not replace either case with an unsolicited
  scheduled task.
- Main-branch pushes do not trigger Windows validation automatically. After a
  logical unit is already accepted and moved to main, do not dispatch another
  Windows CI run just to reconfirm it. A post-main manual gate requires a
  distinct release/deployment requirement, a newly invalidated risk, or an
  explicit user request.
- Keep only `main`, the minimal `control/remote-shell` branch, and at most
  the temporary work branch required by the current isolated integration.
  Delete an accepted `work/*` branch immediately after its final tree is on
  main.
- Operational control-branch commits and remote evidence are never product
  history. Product main should contain one clean logical product commit (plus a
  necessary acceptance/docs commit when appropriate), not iterative WIP or
  verification churn.

### Source-contract hygiene

- Documentation/guidance tests compare whitespace-normalized prose for semantic
  requirements unless exact line breaks or indentation are themselves part of
  the format contract. Markdown reflow must not fail a semantic source gate.
- Use raw newline-sensitive assertions only for structurally significant blocks
  such as exact workflow/YAML syntax or another deliberately line-oriented
  format.

### Evidence reuse examples

- Product build PASS -> test assertion fixed only: reuse the product build;
  rerun the failed focused test only.
- Native/runtime PASS -> XAML label/layout changed only: rebuild the UI once if
  required, then run the visual/UI boundary only; do not rerun the native gate.
- Focused GUI PASS -> unrelated later broad-GUI step fails: do not replay the
  focused GUI. Fix or retire the unrelated harness path separately.
- Large-folder/native algorithm iterating: use cheap source/native fixtures
  while developing; reserve the configured high-cost real-file GUI fixture for
  final acceptance.
- Successful matched visual evidence remains valid across docs/test/control-only
  commits that do not change the rendered product tree.

## Current verification

Model-level large-folder page streaming is accepted on product revision
`f7f3674e5271c17652a865cf2ed499185983d1eb`. The isolated Shell helper still returns one bounded protocol-v3
page at a time (maximum 1,024 entries and 8 MiB per response), but the
supervisor no longer aggregates all continuation pages before reporting
navigation. The first page is accepted into the active Shell session and
rendered immediately; later pages are requested through a continuation action
and appended only when route, request identity, folder PIDL and expected child
offset still match.

WinUI keeps the existing 160-row render window. A truncated model is exposed
with a `+` suffix such as `160/1024+`. View-page requests can request another
Shell page when the currently loaded model is exhausted. Operations that require
a complete bounded model, including global sort and non-empty pane filtering,
set a completion intent and pull continuation pages until the folder ends or
the existing 20,000-entry aggregate safety bound is reached. Optional metadata,
thumbnail and Shell-visual detail work remains deferred while the snapshot is
truncated.

Resident-window acceptance extends that streaming baseline. Product work revision
`37d4cc023777c67a963710efd2e17ee7125a7cae` implements the 2,048-entry normal-browse
window, exact previous/known-forward rehydration and full-model rebuild before
sort/filter. Run `37182310190` passed source contracts 227/227, the canonical
Release build and helper process regression, then proved all target 2,300-file
resident-window markers before an unrelated focused-harness tail assertion
failed. Harness-only revision `1c5779448a8cb194ff1a506ccfdd7cf0239f8222` changed no product file;
resume run `37182611109` reran only GUI/visual acceptance and passed eviction,
backward/forward rehydration and complete 2,300-item global sort.

The next accepted scale step is product work revision
`924a035e244fb547662bedb7094f45b543396a36`. It separates the 20,000-entry
complete-model ceiling from a 100,000-entry bounded sequential-browse ceiling.
Run `37183718932` passed source contracts 228/228, the canonical Release build
and real helper offset-over-20k regression before a GUI-harness-only failure.
Final harness-only run `37184906352` changed no product file and proved owned
20,500-file browsing past the complete-model boundary at logical progress
`20480`, preserved previous-window access and refused incomplete global sort.
The 100,000 ceiling is not itself certified.

The same unit raises each pane folder `TabView` from 28 to 36 px. Matched
956x521 Dark-theme review shows the previously clipped folder-tab caption fully
visible without moving or clipping the Name/Type/Size header row.
`VISUAL ACCEPTANCE: PASS`.

Remote run `37177222154` passed canonical structure 4/4, source contracts
223/223, the canonical Release build, the real helper protocol-v3 process
regression including offset/limit paging, and an owned Release folder containing
8,000 files. The actual WinUI first rendered the initial 1,024-item model in
2.71 seconds, showed the initial streamed-page marker, then completed the
remaining pages for global name-descending sort and reached `bench-7999.txt`.
The GUI also proved the completed `8000` model before the post-stream view page,
kept protected legacy settings unchanged and exited normally. `git diff
--check` passed.

This closes the prior "model waits for the full aggregated transport snapshot"
gap. It does not make enumeration unbounded. Ordinary resident-window browsing
is bounded by `kMaxBrowseEntries=100000`, while complete-model global
sort/filter remains bounded by `kMaxCompleteModelEntries=20000`. Do not claim
100,000-item acceptance from the constant alone: current owned GUI evidence
proves 20,500-file browsing only. Network/virtual provider behavior and
sustained thumbnail-cache behavior remain separate open gates.

Paged isolated Shell enumeration beyond the former 6,000-entry single-frame
ceiling was first accepted on product revision `fb92b9dd03c90ce3e3434270bff3cc5be8714cad`. That revision introduced
private wire protocol v3 with at most 1,024 entries and 8 MiB per helper
response. Its supervisor-side aggregation behavior is historical evidence, not
the current architecture.

Current main follows the later model-level page-streaming revision
`f7f3674e5271c17652a865cf2ed499185983d1eb`: the first helper page is committed immediately and later
pages append only after route/request/folder/offset validation. Cancellation,
route supersession, per-page watchdog/retry, PIDL validation, checksum
validation and exact-owned child job boundaries remain in force. The WinUI list
still renders 160 rows initially and exposes controlled 160-row increments.

Normal unsorted, unfiltered large-folder browsing uses a 2,048-entry
resident window. Logical `baseOffset` and `nextOffset` remain independent of
resident child count, exact previous/known-forward ranges can be rehydrated, and
file-list rows retain logical identities across a nonzero resident base.
Sequential browsing may now advance beyond 20,000 up to the bounded 100,000
browse ceiling, while global sort and non-empty pane filtering retain the
20,000 complete-model ceiling. Above that complete-model boundary those
operations must be refused rather than applied to a partial window. Do not
describe current main as unbounded or as 100,000-item certified; owned GUI
acceptance currently reaches 20,500 items.

The first pre-main run `37174851727` stopped at source contracts because one
old contract asserted the pre-paging local variable name
`result.timedOut=outcome.timeout`. No product code changed for that failure.
Work revision `40f126fdc3225c41e6a3a5fbc7534f0d36522d11`
updated only that source assertion. Remote run `37174929070` then passed
canonical structure 4/4, source contracts 218/218, the canonical Release build,
the real helper protocol-v3 process-isolation regression (including
offset/limit paging), and an owned Release folder containing 8,000 files.
The GUI verified first render, name-descending sort to the final owned file,
the existing 160->320 controlled render-page path, protected legacy settings
unchanged, and emitted
`OWNED_LARGE_FOLDER_OVER_6000_PAGED_TRANSPORT True`.
First render in that owned fixture was 6.17 seconds. `git diff --check`
also passed.

Explicit legacy text encodings for bounded content search are accepted on
product revision `44305357394c8eed76eaaa31614ecaddaca7f4c3`. The default mode remains deterministic:
UTF-8/ASCII plus BOM-tagged UTF-16 LE/BE. Users can explicitly choose Korean
CP949 or Western Windows-1252 for BOM-less legacy text; BOM detection always
wins over the selected fallback. The existing 1 MiB/file, 16 MiB/search and
64 KiB cancellation boundaries remain unchanged. Invalid encoding enum values
are rejected before worker start.

Saved search-condition presets now write schema 3 with the selected content
encoding while retaining read compatibility with schema 1 and schema 2. Scope
remains intentionally excluded.

Remote run `37173754944` passed canonical structure 4/4, source contracts
218/218, the Release M19 native content-encoding gate at 47/47, canonical
Release build and the focused existing M1.9 owned GUI boundary. The GUI proved
that Auto UTF rejects BOM-less CP949 input, explicit CP949 matches Korean legacy
text, explicit Windows-1252 matches Western legacy text, switching back to Auto
UTF restores UTF-16 behavior, and the selected CP949 encoding survives private
preset save/restart/apply by successfully executing the restored query. The
owned WinUI process exited 0, protected legacy-profile checks passed, and
`git diff --check` passed.

Matched Dark-theme visual evidence uses 956x689. The first AFTER capture taken
immediately after an automation-driven CP949 selection was not accepted because
the closed ComboBox had not visually repainted its selected label. A separate
visual-only run `37174155301` captured the ordinary default state and shows
`자동 UTF`, the encoding selector and the I/O guidance without clipping or
overlap, with both file panes still usable. The functional CP949/1252 selection
itself is covered by the focused GUI run above.

Content regex remains intentionally unimplemented: this project currently has
no regex engine with a match limit/callout mechanism that would preserve the
accepted cancellation contract for up-to-1-MiB decoded text. Do not add
unbounded `std::wregex` content matching as a shortcut.

Bounded literal file-content search is accepted on product revision
`eb612e6ef81e168e95cc5c00284eaf890157497b`. It reuses the existing SearchController worker and composes
an optional literal content term with existing name/regex, extension, size,
modified-date and entry-kind criteria. Content matching supports UTF-8/ASCII
and BOM-tagged UTF-16 LE/BE text. Unmarked NUL-containing files are treated as
binary and skipped. Reading is bounded to 1 MiB per file and 16 MiB per search,
with cancellation checked every 64 KiB. Folder-only content queries are rejected
before worker start. The existing depth-5, 2,500-entry and 100-result search
bounds remain unchanged.

Saved search-condition sets now persist the content term using schema 2 while
retaining read compatibility with schema 1. Scope remains intentionally
excluded from saved presets.

Remote run `37172317827` passed canonical structure 4/4 and source contracts
212/212, then isolated one native-fixture token mismatch after 39/40 checks;
the product code was not changed for that failure. New work revision
`651ee13c8edfbdd91cb28f34234fcfb610b53df2` corrected only the fixture token.
Remote run `37172446492` then passed the Release M19 native contract gate at
40/40, the canonical Release build, UTF-8 and UTF-16 real owned-GUI content
search, folder-only pre-start rejection, schema-2 preset save/restart/apply/
delete, protected legacy-profile checks and normal owned WinUI exit 0. That run
later failed in a broader unrelated test-shell tail while resolving
`LeftFiles` after the owned content-search section had already completed; it
was not treated as a content-search product failure.

Final focused remote run `37172732023` succeeded with `git diff --check` and
matched 956x689 Dark-theme BEFORE/AFTER evidence. Direct review shows the added
file-content row, encoding/I/O-budget guidance and existing search criteria
without clipping or overlap, while both file panes remain usable.

Search v3 compound metadata criteria are accepted on product revision
`b7e6873407016e8a3e9cceb3e397a81d71b7e0c5`. The existing bounded worker now supports optional minimum/
maximum file size in integer KB and inclusive local modified-date bounds in
`YYYY-MM-DD`, AND-composed with the existing name/regex, case, entry-kind and
single-extension criteria. An empty name term is valid when another criterion
is present. Size criteria intentionally exclude folders. The depth-5,
2,500-entry walk, 100-result retention, reparse-point avoidance, cancellation
and stale-context rejection remain unchanged.

Up to 20 named query-condition sets persist privately under
`%LOCALAPPDATA%\flyExplorer\search-presets-v1.txt` using atomic replacement.
The search scope is deliberately not part of a preset, so saved criteria can be
reused against another folder.

Remote run `37170399569` passed canonical structure 4/4, source contracts
205/205, the Release M19 native Search v3 fixture at 29/29, canonical Release
build and the established M1.9 owned GUI harness. The GUI passed name +
extension + size + date AND matching, size-only search with an empty name term,
invalid size/date pre-start rejection, private preset save, restart/apply/
delete, protected legacy-profile checks, normal exit and `git diff --check`.

The first functional AFTER screenshot was not accepted as matched visual
evidence because its window height differed from BEFORE. A fixed-size review at
956x689 then exposed clipped date placeholder text; that visual-only XAML issue
was corrected before acceptance. Final remote run `37171067880` passed the
focused Search v3 source contract (6/6), canonical Release build and a new
956x689 capture. Direct review on the same Windows VM and Dark presentation
shows complete date labels, no control overlap/clipping, and both file panes
remaining usable at that size.

Persistent pane filter presets are accepted on product revision
`a7490083000ac8faeb6c4fbe2cf54fecd6b00cf8`. The private store is bounded to 20 named rules and persists
only under `%LOCALAPPDATA%\flyExplorer\filter-rules-v1.txt` using atomic
same-directory replacement. Existing case-insensitive substring filtering is
preserved; expressions containing `*`, `?` or `;` use case-insensitive
wildcard-mask semantics.

Remote run `37168744531` passed canonical source contracts, the Release M20
native fixture at 48/48 and the canonical Release build, and captured the
controlled BEFORE frame. The first GUI assertion failures were isolated to
pywinauto visibility/index assumptions for WinUI container controls and did not
change product code. Final focused run `37169304880` passed durable preset
save, wildcard application, legacy substring compatibility, restart
persistence, delete, protected legacy-profile sentinel checks, normal process
exit and `git diff --check`.

Visual evidence was exported by remote run `37169509814`. The reviewed
BEFORE/AFTER frames were both 1060x760, 96-DPI VM, Dark theme and the same owned
fixture. The AFTER frame shows the two-row preset manager without clipping or
overlap; navigation, address/search chrome and both file panes remain usable.
The AFTER capture was intentionally taken after the harness re-applied the
legacy substring `note` filter, matching the functional evidence.

The accepted Search v2 product revision is
`1fc808f91fa2236890a0025a555ccbd0d922319c`. Focused source contracts passed before build. Remote run
`37166780382` then passed the Release M19 native fixture at 19/19, including
regex case-sensitive/insensitive matching, extension filtering, folder-only and
files+folders targeting, invalid-regex rejection, Unicode filename matching,
cancellation and recent-scope persistence; the canonical Release app build also
passed. Its standalone SearchPanel fixture was rejected as a UIA harness path
after repeating panel-discovery failures and was not used as product evidence.

The evidence path was switched rather than retried. Remote run
`37167164976` used the established M1.9 owned GUI harness and passed default
file-only literal search, case-sensitive regex, Korean filename plus extension,
folder-only targeting, invalid-regex pre-start rejection, existing opt-in
recent-scope save/restart/clear behavior, normal process exit and protected
legacy-profile sentinel checks. `git diff --check` also passed.

The previously accepted large-folder revision remains
`51182fed05e32dfbd90ee320a4a259b1b884d0df`; its 6,000-entry wire bound and
owned 5,000-item navigation/sort/progressive-paging evidence are unchanged.

## Build/runtime facts

- Root wrappers are the supported build/run/test entry points.
- Canonical Windows full builds require Visual Studio/MSBuild 18.x, MSVC v145
  x64 tools and Windows SDK 10.0.26100.0; v143 is not a claimed full-build
  target.
- Release is Windows App SDK self-contained; Debug is framework-dependent.
- The tracked project template is the project-file source of truth.
- flyExplorer.exe cannot be distributed alone; sibling resources and
  FlyShellIsolationHelper.exe are required.
- Potentially blocking Shell/provider behavior stays off the XAML UI thread and
  behind bounded isolation.
- The self-hosted Windows build workflow is manual `workflow_dispatch` only;
  normal main pushes do not queue it. The default manual scope is `release`,
  which includes policy/source contracts, the Release M20 native state fixture,
  canonical Release build and runtime-set verification. `release-gui` and
  `full` remain explicit exceptional manual choices. Windows development,
  focused tests, runtime diagnosis and GUI/visual evidence use the persistent
  `control/remote-shell` path instead.
- Every resumed/interrupted task starts by reading live main HEAD, recent main
  commits and recent main CI together. If the named logical unit is already
  merged and accepted, advance instead of reopening old control-branch or
  pre-main evidence.
- Iterative Windows development, Win11 benchmarking and GUI refinement should
  prefer the fixed `control/remote-shell` branch request slot. Every request
  includes `expected_main_sha` from that live checkpoint; the workflow rejects
  stale requests if main has moved. Updating
  `requests/remote-shell/request.json` on that branch triggers this
  repository's `Remote Windows Task` on the interactive Windows VM and runs
  against workflow-configured canonical persistent checkout by default. Request
  commits are operational history and must never merge into main; main remains
  the history of verified logical units. Manual workflow_dispatch is the
  human-operated equivalent. RDC is supplementary for interactions that shell/
  UIA/screenshot evidence cannot exercise. Use
  `tngkrwlsmd/personal-control-plane` primarily for runner/machine recovery and
  maintenance, especially when this repository's runner path is broken.
  The control branch is a minimal control-plane tree containing only the
  request slot and a thin push trigger. The full Remote Windows Task
  implementation lives on `main` as a reusable workflow, and the control
  trigger calls that `@main` implementation instead of carrying a second copy
  of validation/path/artifact/execution logic.
  The persistent checkout fetches live main for every product command. No
  `remote/**` command-branch fallback is maintained. Temporary `work/*`
  branches are deleted once their accepted final tree is on main.
- The persistent remote-shell checkout is the primary Windows development and
  diagnosis surface. Verification scope, failure handling, evidence
  preservation, retry prohibition and polling behavior follow the
  project-specific **Development loop and verification budget** above. Windows
  build Actions are never triggered merely by a push and never receive a
  diagnosis-free same-revision rerun.
- Remote Windows Task preserves multi-line PowerShell source by writing
  `REMOTE_COMMAND` verbatim to a per-run temporary `.ps1` and launching a
  fresh `powershell.exe -File` process. The child process exit code determines
  command success/failure; the temporary script is removed in `finally`.
- GitHub-hosted runners require explicit user approval and are not part of the
  active flyExplorer CI path by default.
- The privileged self-hosted runner must not execute untrusted fork/PR code
  automatically.
- Normal repository work intentionally overrides the generic branch-first
  default: prefer verified direct-main logical units; use a work branch only
  when repository protection, explicit user direction, concurrent work, or
  isolated integration testing makes one necessary.
- Vendored generic policy is validated as Profile B-style bundle/readiness/
  conformance evidence in self-hosted CI. This does not claim Profile C runtime
  enforcement.

High Contrast ON is accepted on merged product revision
`eaa1b368a677f57c15183c5e6851f0598ed25878`. Actual Windows High Contrast
GUI/visual acceptance passed in Remote Windows Task `37252987127`, including
selected-row UIA state, search controls, protected user settings and restoration
of the original High Contrast OFF state.

## Open gates

Not certified:
- actual 125/150/200% OS scaling;
- human Narrator/Korean IME;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance.

The latest unsigned package + exact binary/source identity acceptance is Remote
Windows Task #440 (`37376305779`). Binary source revision
`bc63c8b48e466d1275cc6dcffb0c50e02d39db60` produced a 305-file Release
runtime (17 product/generated, 288 exact NuGet byte matches), a 326-file setup,
and a deterministic 382-file source bundle. Runtime manifest SHA-256 is
`61572e65c4a593e01607147596195041ce9d530e5f9fc21c9f9517f615b26c1d`;
source bundle SHA-256 is
`5a263a42ecced3384be9a8ab131024ce309e4eb96b249bad1f8adc91f065ce1d`;
unsigned setup SHA-256 is
`825a644a8170acdaae43135604d6998ce517f882b3f8f228fa54cb30c1298a91`.
The setup, source ZIP, source manifest, runtime provenance and release identity
were preserved together in the private #440 evidence artifact. This closes the
technical exact binary/source identity gate.

The public conveyance policy is now fixed to GPLv3 section 6(d): matching binary
and source assets on the same public GitHub Release page, without authentication
or extra source charge. `v1.0.0.0` is reserved but intentionally not pre-created;
repository Immutable Releases was enabled in run #446 (`37379026246`) so the
fully assembled published release locks its tag/assets. Corresponding Source
must remain available while the binary is offered and for at least 1095 days
after withdrawal under the project's stronger retention policy. Production
signing, clean-machine machine-wide deployment, activation of the public
release surface and rightsholder/legal clearance remain open.

## Documentation

Current maintained engineering docs are indexed by
docs/development/README.md. Dated MFC/Phase5/migration checkpoint documents and
legacy HTML Help were removed from the current tree; Git history is the recovery
source for those records.
