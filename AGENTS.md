# flyExplorer repository instructions

## Current product override

The canonical product on main is the C++/WinRT WinUI 3 application under
app/winui. Shared UI-independent code is under src/base; tests are under
tests/winui; canonical orchestration is tools/winui/run_checks.py.

Higher-priority runtime/user instructions override this file. The vendored
.agent-policy core is upstream-managed generic policy from
tngkrwlsmd/universal-agent-docs; update that core atomically rather than
hand-editing individual generic files. Project facts belong in
.agent-policy/PROJECT.md, while flyExplorer-specific overrides belong here.

## User-directed validation boundary (2026-10-21)

The user explicitly directs: **do not perform build, GUI, or pixel/visual
verification unless the user requests that verification**. Continue scoped
development and preserve existing accepted evidence. Record any newly edited
product functionality as **not build/GUI/visual verified** until separately
authorized and actually checked. This changes when the acceptance gates run,
not what counts as accepted; do not claim those gates passed or silently run
them through another workflow. Do not restart user-stopped G07 or excluded
G03/G04/G05 checks.

## User-directed incremental validation rule (2026-10-22)

The user authorizes testing/builds when justified by the changed function, but **not unrelated reruns**. If E changes in accepted A/B/C/D/E, validate E and only genuine dependencies; reuse A-D evidence. No automatic all-source/full-GUI/clean package gate.

- Diff-classify first: documentation-only review; Python/harness changes use affected suite; one UI/feature change uses its product-source area and, when required, one focused owned GUI scenario.
- Build incrementally with verified compatible retained intermediates, compiling only affected targets and dependencies. Reuse unchanged exact runtime. A clean build requires identified missing/untrustworthy cache or cross-cutting impact.
- Central 'release' executes policy, all-source and Release build; 'gui' also runs all GUI. They are NOT focused validation and must not be the default for a one-feature change.
- Do not retest unchanged features or package, installer lifecycle, Debug+Release and unrelated system integration by default. Escalate only for evidence of shared ABI, dependency or integration impact, a focused failure or explicit user request; explain why.
- Always preserve safety/data-integrity gates, exact-SHA evidence, and distinguish *not re-tested* from PASS. G03/G04/G05 remain excluded; G07 remains stopped.

## Personal-use product direction (2026-10-22)

flyExplorer is now developed for **private personal use**, not public distribution.
Signing, marketplace submission, public releases, public-source delivery and
rightsholder clearance for publication are not active project goals.
Do not restore discontinued source or keep history-only utilities in the
active tree. Maintain the current application, its own contracts and actual
third-party NuGet and asset notices.

## Codex 작업 범위와 사용량 절약

Codex 사용량을 절약하면서 요청된 변경을 안전하게 완료한다. 이 절은
작업 범위와 검증 비용의 기본 원칙이며, 아래의 필수 현재 상태 확인,
Windows 검증, 데이터 보호 및 시각적 QA 요구사항을 생략하는 근거가 아니다.

### 탐색과 구현

- 요청과 직접 관련된 파일 및 필요한 의존 경계만 탐색하고 수정한다.
- 기존 사용자 변경사항과 프로젝트 규칙을 보존한다.
- ChatGPT 또는 사용자가 제공한 분석과 수정안은 현재 코드 및 규칙과
  비교한 뒤 우선 활용한다. 이미 제공된 분석을 이유 없이 반복하지 않으며,
  현재 코드에 맞지 않는 수정안은 무리하게 적용하지 않는다.
- 작고 독립적인 변경을 우선한다. 단순 작업에는 별도 에이전트나 장문
  계획을 사용하지 않는다.
- 요청하지 않은 리팩터링이나 기능 확대를 하지 않으며, 요청된 작업이
  끝나면 추가 개선을 시작하지 않는다.

### 영향에 맞는 검증

- 문서, 주석, 문구만 변경하면 일반적으로 테스트를 생략하고 변경 내용을
  검토한다. 실행 계약, 명령 예시 또는 UI에 영향을 주면 해당 영향에 필요한
  검증과 아래의 필수 게이트를 적용한다.
- 일반 코드 변경은 영향받는 최소 검증부터 수행한다. 전체 테스트, 전체
  빌드, E2E, 광범위한 보안 검사는 변경 위험, 명시적 요구 또는 프로젝트의
  필수 게이트가 요구할 때 수행한다.
- 인증, 권한, 결제, 데이터 삭제, DB 마이그레이션, 외부 API 계약 변경에는
  필요한 검증을 생략하지 않는다.
- 동일한 검증을 이유 없이 반복하지 않는다. 실패 시 원인을 좁히고 실제로
  무효화된 관련 범위만 재실행한다.
- 검증하지 않은 내용을 성공했다고 보고하지 않는다. 기능 GUI 검증과
  시각적 검증은 아래 규칙에 따라 별도로 보고한다.

### 작업 종료와 인계

- 변경 파일, 변경 내용, 검증 결과 및 미검증 위험을 간결하게 보고한다.
- 허가되지 않은 커밋, 푸시, 배포는 수행하지 않는다.
- 중요한 미완료 작업이 남아 다음 세션의 구체적 인계가 필요한 경우에만
  `docs/HANDOFF.md`를 생성하거나 갱신한다. 완료된 작업에는 만들지 않는다.
  인계 문서는 현재 상태 확인을 대신하지 않으며, 재개 시 아래 체크포인트와
  `docs/development/CURRENT_STATUS.md`에 대조한다. 기존 인계의 무관한 작업은
  보존하고 비밀정보, 개인 데이터 및 원시 머신 로그는 기록하지 않는다.
- 인계 문서에는 다음 항목을 포함한다:
  - 현재 목표: 진행 중인 기능 또는 수정 목적.
  - 완료된 작업: 완료 항목과 관련 파일.
  - 중요한 결정: 선택한 구현 방식과 이유, 실패한 시도와 확인된 원인.
  - 남은 작업: 다음에 수행할 구체적인 변경과 영향받는 파일.
  - 검증 상태: 실행한 검증과 결과, 실행하지 않은 검증과 남은 위험.
  - 다음 작업 지침: 우선 처리할 사항과 건드리면 안 되는 파일이나 기능.

## Required current references

Before substantial work, use:
- docs/development/CURRENT_STATUS.md
- docs/development/ARCHITECTURE.md
- docs/development/AGENT_EFFICIENCY.md
- docs/development/ERROR_HISTORY.md for known/repeated failures.
- docs/development/NEXT_DEVELOPMENT_GOALS.md when selecting or resuming an
  unfinished feature, usability audit, accessibility check or release gate;
  reconcile each goal with live main and exact-SHA acceptance first.

Deleted dated migration reports are historical Git evidence, not current
instructions.

## Future development goals and scope

The maintained, prioritized incomplete-work register is
docs/development/NEXT_DEVELOPMENT_GOALS.md. It distinguishes verified
architecture/behavior gaps from untested environments, deliberate safety
limits, optional Explorer parity and publication gates. Use its dated current
summary before older historical OPEN/next-step labels. The accepted ownership
contract is independent PaneTab sort with v4 persistence; view/display options
and column widths remain per pane within each WindowTab, and grouping uses a
transient route/tab cache. Per-tab view/column persistence is a separate product
choice, not an unresolved defect in the accepted sort behavior.
Previously accepted F01-F06 and R1 sort-menu work must not be reopened from
older historical plans without new evidence.

The register is a planning and resumption aid, **not** permission to implement
unrequested items, run privileged Windows tests, publish, change global OS
settings, or create a PR. Preserve the dual-pane plus two-level tab model,
source/binary/environment-scoped acceptance, and the existing project/user
approval boundaries. Update goal status only when its actual completion
criteria and evidence have been checked.

### Explicit user exclusions (2026-10-19)

Do **not** pursue, schedule, perform, re-propose or treat as release blockers
any of these previously proposed P1 checks:
- Real Windows 125%, 150% and 200% OS DPI tests (former goal G03).
- F04/F05 actual High Contrast visual checks and Narrator spoken-audio tests
  (former goal G04).
- Real USB/removable-media, SMB, UNC or mapped-drive file-operation tests
  (former goal G05).

These are **USER-EXCLUDED**, not PASS and not product defects. Leave the
historical acceptance/untested evidence intact. Other feature or release
tasks must not silently reintroduce these tests as subchecks or prerequisites.
Do not change this exclusion unless the user expressly requests that scope
again. Continue ordinary available-environment visual QA for separately
authorized UI changes without interpreting it as permission for excluded tests.

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

Unified developer entry point (root), with legacy wrappers retained:

    fly.bat help
    fly.bat check
    fly.bat build [Debug|Release]
    fly.bat run [Debug|Release] [path]
    fly.bat test [stage] [Debug|Release]
    fly.bat package
    fly.bat clean [build|cache|all]

Root run.bat with no arguments is also a double-click Release launcher; it
never implicitly builds and displays a persistent missing-build error when
opened by double-click. A user may directly double-click the built
out/winui/Release/flyExplorer.exe if its full sibling runtime is present.
Root build.bat, run.bat, test.bat, clean.bat, package.bat remain supported
for compatibility; do not bypass their actual build/test implementations.
fly.bat package deliberately deletes only ignored out/ build output, runs
one Release build, then writes/checks exact-runtime provenance before
package.bat Release. Fail closed on cleanup, build, provenance or packaging
errors. This explicit packaging path updates tracked
packaging/licenses/PAYLOAD_PROVENANCE.* and is never an automatic retry.
The full stage defaults to Release build + functional GUI, not all source,
native, Debug, packaging or pixel-visual acceptance.

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

For Windows 11 Explorer feature-parity planning and implementation, follow
docs/development/EXPLORER_PARITY_REQUIREMENTS.md. It defines scoped feature
contracts, existing evidence, completion criteria and verification boundaries;
it does not authorize implementing the entire backlog or override explicit
user exclusions in NEXT_DEVELOPMENT_GOALS.md. Record functional and visual
acceptance separately and preserve the dual-pane/two-level-tab model.

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

Do not use chatgpt-codex-connector unless explicitly requested/authorized for
this task. Ordinary GitHub connector/API operations are permitted. For missing
GitHub write operations, prefer the approved `personal-control-plane` Remote
Shell running under its SYSTEM Windows VM service, not RDC. Use RDC only if
that control plane fails or a desktop interaction is truly required.

**Current ownership (since 2026-10-10):** `flyExplorer` no longer has a
self-hosted GitHub Runner or a source-repository Windows Actions execution
path. The former `control/remote-shell` and `windows-build.yml`/
`remote-windows-task.yml` interfaces are retired. Do not re-create the old
Runner, enable a privileged source PR trigger, or queue a job targeting
`[self-hosted, Windows, X64]` in this source repository.

Use `tngkrwlsmd/personal-control-plane` as the sole Windows VM control path:

- **Development/diagnosis/one-off Git operations:** request through its
  `requests/remote-shell/request.json` slot (target `windows-vm`) or the
  explicit central Remote Shell manual dispatch. Before submission read
  current `main`, check active central Remote Shell/CI jobs and inspect
  the request slot. Never overwrite an active request. Restore the slot
  to its documented idle command after completion.
- **Independent acceptance:** manually dispatch the central
  `central-flyexplorer-ci.yml` workflow with registered `project_id=desktop-a`,
  exact verified SHA reachable from `flyExplorer/main`, and an explicit
  `scope=health|source|release|gui|gui-probe`. Its default `health` does
  **not** imply a Release or GUI acceptance. Only the central producing
  workflow's completion, logs and exact-SHA status are evidence.
- The previous `release-gui` intent maps to `gui`, which performs central
  policy/source, Release build and GUI. The previous `full` Debug+Release
  scope has **no exact automatic central replacement**; arrange a bounded,
  explicitly scoped central Remote Shell validation when truly required,
  and never report `full` acceptance based on a `gui` PASS.
- Central `winui-gui` launches test-owned UI under a logged-in, unlocked
  Windows user desktop; SYSTEM Session 0 is the controlling service,
  **not** the desktop where GUI assertions run. If the desktop is absent,
  report the environment limitation rather than treating it as a product
  failure. A functional UIA PASS alone does not satisfy pixel/visual QA.
- The central CI service is privileged. Only reviewed, trusted main
  ancestry and allowed registered project profiles may be executed;
  untrusted pull requests, arbitrary remote source refs and unexpected
  filesystem paths are not authorized by a general CI request.

Every remote execution needs zero-run preflight: exact ref and working directory,
command escaping/syntax, relevant test/fixture contracts, runner/service state,
lease and stable logical unit. Do not create speculative retries or rerun the
same SHA to seek a different result. Classify the first failure as product,
fixture/harness, or control-plane/environment and change the invalidated
boundary before a successor run. Prefer the smallest source/native/UIA diagnostic
before expensive full GUI fixtures. Do not push partially validated product
changes, debug instrumentation or generated artifacts.

Use the persistent canonical source checkout only after verifying the actual
origin, `HEAD`, `origin/main` and `git status --short`. Do not reset,
clean, overwrite or delete unexpected user work. Keep evidence revision-
and configuration-scoped. Historical, bounded non-secret run metadata remains
in Git branch `evidence/remote-windows`; active central GUI failures use
private short-retention Actions artifacts. Never commit credentials, profile
data, raw machine logs, unreviewed desktop screenshots, or large binaries.

For exact request examples, archive locations, deprecated workflow mappings
and capability limitations see
`docs/operations/windows-runner-retirement.md`. This current contract
supersedes earlier repository-scoped Remote Windows Task instructions.

## Windows CI disk-space maintenance

Treat `C:\ProgramData` as protected machine/application state, not as a
disposable directory. The Windows control-plane owns CI storage, under
`C:\ProgramData\personal-control-plane`. Never recursively delete all
of `ProgramData`, user profile data, Windows Update/installer caches,
unknown files, staged transfer `.partial` outputs or receipt journals.
These may be recovery evidence and require separate ownership validation.

Use the control repository's documented capacity workflow and
`scripts/maintenance/AutoTrim-CIStorage.ps1` (installed through a
checksum-pinned SYSTEM task), which delegates to
`Manage-CIStorage.ps1` for exact-workspace provenance validation,
active-process guards, `.keep`, no reparse traversal and
archive-before-deletion. Preview first unless an approved, configured
scheduled task is applying its strictly bounded policy: **72h minimum age,
30 GiB free-space threshold or 8 GiB recoverable CI backlog, maximum
three old clean owned CI workspaces per run**. Protect unfinished work,
unique native/debugging evidence and dirty checkouts. Schedule execution
and inspect postconditions rather than assuming that committed policy
files automatically installed a maintenance task.

Reference: `tngkrwlsmd/personal-control-plane/docs/CI_CAPACITY_GUARD.md`.
Any expansion to `scratch`, orphan copy stages, `ci-evidence` or
system/installer folders needs a separate verified ownership and retention
decision; do not automatically extend the allowed root.

## Git logical units

flyExplorer intentionally overrides the generic branch-first integration
default in the vendored policy. If commit/push is approved for the task, prefer
a verified logical unit directly on main. Use a separate work branch only when repository protection requires
it, the user requests it, concurrent work would make direct-main unsafe, or the
change needs isolated integration testing. Delete temporary work branches as
soon as their verified final tree is accepted on main; do not keep stale
work/* branches as historical checkpoints.

Before push, run `git diff --check`, inspect staged scope, and execute
the narrowest source/static checks and any required central Windows acceptance.
Normal `flyExplorer/main` pushes do not run Windows validation automatically.
Use reviewed `personal-control-plane` requests for source/Release/GUI
evidence against the exact main revision as required; check GUI and visual
acceptance separately. After push, fetch and verify HEAD == origin/main with
ahead/behind 0/0. Never force-push.

Do not push a state with a known required acceptance failure, temporary debug
instrumentation or generated artifacts.
