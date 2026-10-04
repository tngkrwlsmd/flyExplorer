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
    "reviewed_revision": "44305357394c8eed76eaaa31614ecaddaca7f4c3",
    "reviewed_at": "2026-10-04",
    "reviewed_paths": [
      "app/winui",
      "src/base",
      "build.bat",
      "tests/winui/requirements-gui.txt"
    ]
  }
}
```
<!-- project-facts:end -->

## Canonical product

- Repository: tngkrwlsmd/flyExplorer.
- Canonical branch/worktree: main / C:\dev\flyExplorer.
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
ordering and detached atomic-save worker. MainWindow retains theme/view
presentation, persistence triggering, DispatcherQueue handoff and status
projection.
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

Local filesystem Shell enumeration now uses a bounded 6,000-entry isolated
helper ceiling while retaining the 8 MiB wire-body limit and 160-item
progressive UI rendering. This extends the previously exercised 2,300-item
path without introducing unbounded enumeration or changing the Shell fault
boundary.

Search v2 extends the existing bounded name-search model without changing its
worker/lifecycle owner. The default remains file-only, case-insensitive literal
name search. Users may opt into ECMAScript regular expressions, case-sensitive
matching, file/folder/both targeting and a single extension condition. Invalid
regular expressions and extensions are rejected before a worker starts. The
existing depth-5, 2,500-entry walk and 100-result bounds, cancellation,
stale-result rejection and opt-in recent-scope persistence remain in force.

## Current verification

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
  against persistent checkout `C:\dev\flyExplorer` by default. Request
  commits are operational history and must never merge into main; main remains
  the history of verified logical units. Manual workflow_dispatch is the
  human-operated equivalent. RDC is supplementary for interactions that shell/
  UIA/screenshot evidence cannot exercise. Use
  `tngkrwlsmd/personal-control-plane` primarily for runner/machine recovery and
  maintenance, especially when this repository's runner path is broken.
  The control branch is a minimal control-plane tree containing only the
  remote-shell workflow and request slot; it does not mirror product source.
  The persistent checkout fetches live main for every product command. No
  `remote/**` command-branch fallback is maintained. Temporary `work/*`
  branches are deleted once their accepted final tree is on main.
- The persistent remote-shell checkout is the primary Windows development and
  diagnosis surface. Batch investigate/edit/build/focused-test/GUI-evidence
  commands there. Windows build Actions are never triggered merely by a push
  and never receive a same-revision rerun. A deliberately dispatched failure is
  diagnosed once, fixed in the remote-shell loop, and only a new revision may
  justify a later manual gate.
  For normal builds/remote tasks expected to finish within a few minutes, allow
  up to three minutes of runtime before declaring them still running; use one
  final read rather than short-interval polling.
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

## Open gates

Not certified:
- actual 125/150/200% OS scaling;
- High Contrast ON;
- human Narrator/Korean IME;
- physical drag;
- signed clean-machine machine-wide install/update/rollback;
- public redistribution/source-delivery/rightsholder/legal clearance.

The tracked installer/provenance snapshot predates v7 and must be rebuilt before
it can represent the current product.

## Documentation

Current maintained engineering docs are indexed by
docs/development/README.md. Dated MFC/Phase5/migration checkpoint documents and
legacy HTML Help were removed from the current tree; Git history is the recovery
source for those records.
