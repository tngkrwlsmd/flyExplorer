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

## GitHub 및 개발 기록 한국어 우선 원칙 (2026-11-05, 사용자 지시)

flyExplorer의 GitHub 저장소를 사용자가 한국어로 쉽게 확인할 수 있도록,
**앞으로 새로 만들거나 수정하는 사용자에게 보이는 개발·운영 기록은 한국어를 기본 언어로 사용한다.**
이 규칙은 새 작업·후속 작업·자동 실행 요청에도 적용한다.

- **저장소 소개:** GitHub About의 설명, README와 사용자용 안내, 릴리스 설명,
  프로젝트 작업 현황과 개발 문서는 기본적으로 자연스러운 한국어로 작성한다.
- **이슈 및 PR:** 제목·본문·체크리스트·검증 결과·진행 상황·댓글을 한국어로 작성한다.
  새로 만드는 이슈/PR 라벨의 사용자용 이름과 설명도 가능한 범위에서 한국어로 한다.
  안전한 `main` 직접 반영을 기본으로 하되, 2026-11-06 조건부 PR 허용 지침을 적용한다.
- **커밋:** 커밋 제목과 본문을 한국어로 작성하여 GitHub 커밋 목록과
  해당 커밋으로 표시되는 Actions 실행 제목도 한국어로 읽히게 한다.
  필요한 경우 `feat:`, `fix:`, `test:`, `docs:`, `ci:` 같은
  기존 기술적 분류 접두사는 유지하되 뒤의 설명은 한국어로 쓴다.
- **GitHub Actions:** 새로 작성하거나 관련 작업에서 수정하는 워크플로의
  표시 이름(`name`), 실행 제목(`run-name`), 잡과 단계의 표시 이름,
  실행 결과 요약·검증 보고 문구를 한국어로 작성한다.
  flyExplorer 작업을 대신 수행하는 `personal-control-plane`의 실행 요청
  커밋 제목과 사람이 읽는 결과 설명에도 한국어를 사용한다.
  다만 그 저장소의 자체 지침과 기존 실행 체계·권한·검증 안전 규칙을 우선 보호한다.
- **예외:** 소스 코드 식별자, GitHub API 필드·이벤트명, 고정 상태값,
  파일 경로, 명령어, 기계 판독용 로그 표식, 외부 제품·라이브러리 명칭 등은
  정확성과 호환성이 중요한 경우 원문을 유지한다. 사용자에게 보이는 설명은
  그 의미를 한국어로 풀어 쓴다. 테스트·CI에서 비교하는 고정 문자열을
  번역해 동작을 깨뜨리지 않는다.
- **범위:** 이 지침은 **향후 작성·수정되는 항목**에 우선 적용한다.
  이미 종료된 이슈, 과거 커밋/Actions 로그, 기존 워크플로 전체를
  언어 변경만을 위해 일괄 수정하거나 재실행하지 않는다.
  기존 항목을 별도로 정리할 때에도 이 한국어 원칙을 적용한다.

## New-chat infrastructure checkpoint (2026-11-04)

Start development from live `flyExplorer/main`, current instructions, relevant status and accepted evidence; never treat an earlier conversation as a live status check. For runner/device, remote CI, GitHub administration or external release tasks, **also read current `tngkrwlsmd/personal-control-plane/AGENTS.md` and `docs/TARGETS.md` first**, including their new-chat preflight. The old `windows-vm-control` repository name redirects to `personal-control-plane`; it is not an independent active control plane.

- A **GitHub Actions self-hosted runner** and an **RDC device** are different. Read live runner inventory before saying online/offline; one queued job, old successful job or offline runner does not establish that all runners are offline.
- Before declaring a GitHub task impossible, check the connector's precise capabilities **and** available approved control-plane Remote Shell/`gh` paths, including actual authentication. RDC is not the default fallback; do not prematurely delegate executable Git steps to the user.
- For a requested GitHub Release, verify exact source SHA, required CI, the **target repository's** tag-triggered release flow, published assets and final post-release verification. Keep this separate from a flyExplorer product Release build.
- Report `NOT CHECKED`/`QUEUED`/`OFFLINE`/`PUBLISHED`/`VERIFIED` accurately; cancel stale queued probes and restore their slots. This preflight does **not** authorize additional product build/GUI checks, data changes or tools the user has excluded.

## ChatGPT 전담 개발과 이벤트 전달 역할 분리 (2026-11-06 사용자 채택)

- 목표 구조: `personal-control-plane`이 작업 요청·완료 이벤트·실행 상태·중복 방지를 관리하고, 일반 ChatGPT 개발 실행이 최신 `flyExplorer/main`, `AGENTS.md`, 개발 계획 및 실제 검증 근거를 읽어 다음 미완료 단위의 분석·구현·검증 판단·GitHub 반영을 직접 수행한다. 개발 연속성은 이전 대화의 존재가 아니라 저장소 상태와 명시적 작업 ID/근거로 유지한다.
- Work 또는 Codex를 이벤트 전달에 사용하더라도 **전달 전용**이다. 수신한 작업 요청/결과의 원문과 식별자·정확한 SHA·출처 링크를 변경하거나 개발 지시를 새로 만들어내지 않고 ChatGPT 개발 실행으로 넘기는 역할만 허용한다. Work·Codex에 개발 단위 선정, 소스 수정, 코드 리뷰, 빌드·테스트, Git 커밋·병합을 위임하지 않는다. 이 조항은 `chatgpt-codex-connector`의 사용 승인으로 해석할 수 없다.
- **현재 기술적 미검증 경계:** 지원되는 GitHub PR 이벤트가 Work 작업을 시작하는 공식 경로는 존재하지만, Work/Codex가 내용을 전달하여 **일반 ChatGPT의 새 개발 실행을 자동 시작**하는 공식·실동작 경로는 아직 확인되지 않았다. 이 전달 경로가 실제 왕복 시험으로 검증되기 전에는 자동 재개가 가동 중이라고 보고하거나, 미검증 이벤트/PR을 반복 생성하거나, 개발을 Work/Codex로 대신 수행하지 않는다. 실패 시에는 해당 경계를 BLOCKED/NOT VERIFIED로 기록한다.
- 개발 실행이 실제로 시작된 경우에는 기존 최신 HEAD·중복 작업·승인된 Windows VM 검증·사용자 데이터 보호·정확한 SHA 수용 및 임시 브랜치 정리 규칙을 모두 적용한다. 이벤트만으로 새로운 검증·배포 권한이 생기지 않는다.

## PR 조건부 허용과 chatgpt-codex-connector 금지 (2026-11-06 사용자 지시)

- PR 자체는 금지하지 않는다. 독립 검토, 격리 통합, 실제로 필요한 GitHub 이벤트 전달 등 구체적인 목적이 있을 때 조건부로 생성·사용할 수 있다. 기존처럼 안전성과 필요한 검증을 확인한 독립 변경은 PR을 기다리지 않고 `main`에 직접 반영할 수 있다. 의례적으로 PR을 생성하거나 별도 PR 대기를 필수 관문으로 만들지 않는다.
- PR 생성·수정·댓글 등으로 이벤트를 발생시키기 전에 해당 저장소의 자동 Codex 리뷰 및 `chatgpt-codex-connector` 개입 가능성을 확인한다. 자동 개입을 차단했거나 해당 PR에 개입하지 않음이 확인되지 않으면 이벤트 전달용 PR을 생성·작동시키지 않는다. 저장소 지침을 기록하는 것만으로 GitHub 앱·자동 리뷰 설정이 비활성화됐다고 간주하지 않는다.
- `chatgpt-codex-connector`는 개발, 코드 검토, 테스트, GitHub/PR 작업, 작업 재개 및 자동화에 사용하지 않는다. 해당 작업에서 사용자가 이 제한을 명시적으로 해제하지 않는 한 일반적인 PR 허용·GitHub 작업 지시를 사용 승인으로 해석하지 않는다. 일반 GitHub 연결 도구, GitHub API, 승인된 `personal-control-plane` 실행 경로는 이 금지의 대상이 아니다.
- PR은 개발·검증·이벤트 전달 수단일 뿐, 이벤트를 통해 이 ChatGPT 대화가 자동으로 깨어난다고 가정하지 않는다. 실제 지원 트리거와 실행 결과를 별도로 확인하고, 완료 후 불필요한 임시 PR·브랜치는 기존 보존·정리 원칙을 따른다.

## Git 브랜치·태그 정리 규칙 (2026-11-07 사용자 지시)

- 개발은 안전한 경우 `main` 직접 반영을 기본으로 한다. 분리된 검증이나 충돌 방지에 실제로 필요한 경우에만 임시 브랜치를 생성한다. 작업이 수용되어 `main`에 반영된 뒤에는 해당 브랜치의 정확한 SHA와 반영 여부를 확인하고 즉시 삭제한다.
- **사용자가 그 태그 또는 릴리스를 명시적으로 요청하지 않으면 태그를 생성하지 않는다.** 특히 `branch-archive-*`, 백업·브랜치 은퇴용 경량 태그를 만들지 않는다. 브랜치 삭제 요청은 보관 태그 생성 승인이 아니며 일반 정책의 릴리스 태그 예시보다 이 프로젝트 규칙을 우선한다.
- 브랜치를 삭제하기 전 열린 PR, 미통합 고유 변경, 실제 진행 중인 작업을 확인한다. 완료되지 않은 작업이나 소유 증거를 임의로 폐기하지 않으며 `main`과 다른 저장소는 보호한다.
- 참조 정리 시 삭제 전 SHA와 삭제 후 브랜치·태그 수를 확인한다. 정리용 브랜치·태그·형식적인 PR을 새로 만들지 않는다.

## User-directed direct-main and live comparison rule (2026-10-31)

The user explicitly directs: when scoped review and actual use show no material
problem, integrate directly into main without a PR. Do not keep accepted work
waiting for a PR, create new PRs by default, or ask again for an already authorized
safe main update. Verify the exact target, changed-function checks, existing
accepted evidence and working tree, then use a normal non-force update. Isolate
only changes with an actual unresolved problem; user data and existing work stay
protected. Retire superseded work branches/PRs after their accepted content is on
main. This supersedes older PR #70/draft/unmerged continuation notes.

The user also requests a direct Windows 11 File Explorer comparison to revise
requirements and the development backlog. Use the approved windows-vm path, the
same disposable fixture, observed OS/Explorer version/theme/DPI and real input/
pixels. Separate observed differences, source-confirmed limits and unobserved
areas. Do not replace this live comparison with a documentation-only audit.
Keep the dual-pane/two-level-tab/v4 ownership and existing exclusions. Opening
and closing the new owned Explorer window is authorized; do not inspect or alter
preexisting Explorer windows or personal history/settings.

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

## ChatGPT 개발 작업 범위와 검증 비용 절약

불필요한 탐색과 검증 사용량을 줄이면서 요청된 변경을 안전하게 완료한다. 이 절은
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

### Current continuation rule (2026-10-29)

Use the **앞으로 진행할 작업** section in
`docs/development/NEXT_DEVELOPMENT_GOALS.md` as the single current queue.
Keep scoped completions outside that queue. Complete the pending validation
for already changed product code before selecting a new feature or visual unit;
the register owns the exact targets, source identities and verification states.
Reuse successful evidence and select at most one important uncovered PX15 action.
Do not invent accepted-case variants or whole-product test matrices merely to
continue working. PX11's proposal is complete; retain v4 unless its unadopted
per-tab presentation extension is explicitly chosen. Additional PX17 templates,
PX08 Share and later candidates are not automatically adopted by a generic
continue request. After a changed performance unit is accepted, reopen its older
acceptance only for new symptoms or a new evidenced bottleneck. If no justified
executable unit remains, **do not declare development complete yet**. First apply the
Windows 11 Explorer re-comparison gate below. That gate identifies evidence-based
new requirements; it does not waive any approval, data-safety or test exclusions.
The register defines completion and stop conditions after this gate.

Use normal ChatGPT development execution and the approved central `windows-vm`
path; Work/Codex are relay-only under the user-adopted role split above. Do not
access personal PCs/local desktops, use RDC, or use `chatgpt-codex-connector`.
Documentation-only planning does not require Windows execution/build/GUI.
Preserve existing exclusions, user-data protections and separate GUI/pixel gates.

### 미완료 작업 소진 시 Windows 11 탐색기 실기 재대조 (2026-11-07 사용자 지시)

- **발동 조건:** `flyExplorer/main`의 최신 코드, 최근 커밋, `CURRENT_STATUS.md`, `NEXT_DEVELOPMENT_GOALS.md`, 기존 수용 증거를 대조한 뒤 **실행 가능한 미완료 개발·결함 수정·필수 검증 단위가 정말로 없다고 판단한 경우**에만 시행한다. 현재 진행 중인 작업이나 이미 명시된 미완료 단위가 있으면 먼저 이어서 처리한다. 과거 대화의 '할 일 없음' 판단만으로 발동하지 않는다.
- **종료 판단 전 필수 단계:** 문서만 재검토하거나 2026-10-31 대조 결과만 재사용해 Windows 11 탐색기와 동등하다고 선언하지 않는다. 승인된 `personal-control-plane` Windows VM에서 **그 시점의 실제 Windows 11 파일 탐색기와 최신 flyExplorer 제품을 직접 실행**하여 동일한 테스트 소유 폴더·파일로 비교한다. OS/Explorer 버전, flyExplorer의 정확한 소스 SHA·실행 파일, 테마·DPI·창 크기와 입력/화면 근거를 남긴다. 실행 환경이 없거나 실기 조작이 불가능하면 `BLOCKED / NOT TESTED`를 명시하고 기능 동등성을 주장하지 않는다.
- **비교 범위:** 탐색·주소창·뒤로/앞으로·탭·파일 선택, 보기/정렬/그룹, 검색, 컨텍스트 메뉴/키보드 진입, 파일 명령·속성, 주요 보조 창·상태 표시 및 관련 사용성 등 **기존 프로젝트에서 허용된 영역**을 우선 확인한다. 기존 듀얼 패널/2단계 탭의 의도된 차이는 보존하고, G03/G04/G05 제외·G07 중단 및 사용자 데이터/OS 설정/외부 전송 제한은 그대로 지킨다. 무관한 전체 GUI·빌드 회귀를 의례적으로 재실행하거나 개인 Explorer 창·최근 항목·설정을 건드리지 않는다.
- **차이 판정:** 각 관측을 (1) 실제 누락/오작동, (2) 기존 기능의 다른 진입점·표현, (3) 의도된 제품 차이 또는 승인 제외, (4) Windows 설치·확장·계정 의존, (5) 미관측/미검증으로 구분한다. 소스에서만 추정한 기능, 문서상 구현, 화면만 본 사례를 실동작 PASS로 승격하지 않는다. 이미 수용된 기능은 새로운 실패 증거 없이 반복 개발 과제로 만들지 않는다.
- **개발 지침 갱신:** 새로 확인된 차이는 정확한 재현 단계·근거·영향·수용 기준과 함께 날짜가 있는 직접 비교 보고서에 기록하고, `docs/development/NEXT_DEVELOPMENT_GOALS.md`의 **앞으로 진행할 작업**에 우선순위와 다음 한 단위로 반영한다. 기존 `EXPLORER_PARITY_REQUIREMENTS.md`, `CURRENT_STATUS.md` 또는 이 `AGENTS.md`의 요구·구현 지침이 최신 실측과 충돌하면 필요한 범위만 수정한다. 기능 하나를 끝내면 최신 `main`과 근거를 다시 대조하여 다음 미완료 단위를 선택한다.
- **정말로 차이가 없는 경우:** 실제로 비교한 **범위·환경·미관측 부분**과 '추가 실행 가능한 작업 없음' 판단 근거를 기록한 후에만 그 범위에서 종료 보고한다. 모든 Windows 11 Explorer 버전·환경에 대한 완전한 기능 동등성을 주장하지 않는다. 새 비교 항목의 발견은 무제한 기능 구현, 중단된 자동 릴레이 재개 또는 별도의 승인·검증이 필요한 동작에 대한 포괄 허가가 아니다.

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

## Mandatory cross-repository branch cleanup at development completion (2026-11-03)

The user explicitly requires **all non-main development, integration, test and
instrumentation branches to be removed when the accepted development unit
finishes**, in **both** `tngkrwlsmd/flyExplorer` and
`tngkrwlsmd/personal-control-plane` (the central Windows control repository).
This is a required completion gate, not an optional later housekeeping item.
Before deleting any branch, confirm its work is accepted on the appropriate
`main` or its unique evidence/code is safely preserved without needing that
branch. Confirm no queued/active request, test or pull request references it.
Do not delete an unfinished candidate or the only copy of unaccepted work;
finish, integrate or explicitly report the blocker before claiming completion.
After acceptance, enumerate **all** branches in both repositories, delete all
superseded non-main refs via exact-name, non-force operations, verify each
repository contains only `main`, and report any unresolved ref by name. Keep
historical failures in committed docs and Actions evidence rather than leaving
`work/*`, `fix/*`, `diag/*`, or `integrate/*` branches as archives.

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
