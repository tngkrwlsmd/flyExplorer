# flyExplorer 저장소 종합 검토 — 2026-11-11

## 판정 범위와 기준

- **기준:** [flyExplorer/main `6f7fd9e7fcc058400399f4a3b9b104bb469ace97`](https://github.com/tngkrwlsmd/flyExplorer/commit/6f7fd9e7fcc058400399f4a3b9b104bb469ace97), 2026-11-11 조회. 최근 15개 커밋, main 파일 트리, 비기본 브랜치 3개, 공개된 코드·문서·설정·테스트 대표 지점, 중앙 제어 저장소의 당시 `AGENTS.md`/`docs/TARGETS.md`/실제 `central-flyexplorer-ci.yml`을 대조했다.
- **검토 방식:** GitHub 원격 파일/커밋을 읽은 정적·계약·운영 문서 감사다. 모든 파일의 모든 함수에 대한 전수 정적 분석이나 CVE 감사가 **아니다**. Windows x64 빌드, 기존 테스트 재실행, 실기 GUI·키보드·접근성·DPI·성능 측정, 설치/제거, 실제 Runner `busy` 상태 및 사용자 파일 작업은 **이번 작업에서 실행·확인하지 않았다**. 기존 PASS는 각 당시 소스 SHA/실행의 제한된 이력 증거로만 취급한다.
- **읽기·수정 경계:** 본 감사에 따른 직접 변경은 개발 지침 및 관련 Markdown 문서뿐이다. 제품 소스·테스트·패키징·원격 요청·운영 머신은 변경하지 않는다.

## 1. 목적과 실제 구성

**제품 방향:** Windows 11 기본 파일 탐색기를 참고하는 **개인용** 파일 관리자. 일반 Windows Shell 기능을 재사용하되 고유의 듀얼 패널 및 2단계 탭을 유지한다. 공용 배포, 자체 ZIP 엔진 재도입, 모든 탐색기 기능의 동등 구현은 현재 목표가 아니다. 데이터 안전·검증 경계가 기능 수보다 우선한다.

| 영역 | 확인한 실제 경계 |
| --- | --- |
| UI/제품 | `app/winui`의 C++/WinRT + WinUI 3/XAML, `MainWindow`, FileToolbar 등; `app/winui/flyExplorer.project-template.xml`이 생성 프로젝트의 원본 |
| 상태/수명 | `WindowWorkspaceController`, `SessionCoordinator`, `ShellNavigationController`, `FileOperationController`, `SearchController`; WindowTab → 좌/우 Pane → PaneTab 별 소유권 |
| 네이티브 핵심 | `src/base`에 Shell 탐색·검색·전송·파일 명령, 이름 변경 복원 영수증, 세션 v1–v4 호환, 프리뷰 안전 열기/시간·크기 제한, 설정 저장 |
| 외부 호출 | 별도 `FlyShellIsolationHelper.exe` 자식 프로세스와 버전·크기 제한을 둔 IPC. **장애 격리이지 보안 샌드박스가 아니며** 사용자 토큰을 상속 |
| 테스트 | `tests/winui`의 Python 표준 라이브러리 소스 계약, 네이티브 C++ fixture, 실제 소유 폴더/프로세스 기반 GUI 검사, 별도 수동 안전 게이트 |
| 실행 도구 | `fly.bat`/기존 배치 래퍼와 `tools/winui/run_checks.py`; Release 출력과 NuGet 캐시는 무시되는 `out/` 및 `.cache/` |
| 패키징 | 개인용 무서명 설치기, `packaging/provenance.py`가 실제 Release 파일·NuGet 복원 자산/해시 확인. 새 빌드 후 기존 manifest를 그대로 재사용하면 안 됨 |
| 정책/운영 | 저장소 루트 `AGENTS.md` 우선, 프로젝트 정보는 `.agent-policy/PROJECT.md`. `.agent-policy` 일반 코어 v0.6.6은 상류 관리이므로 개별 수정 금지. Windows VM 실제 실행은 `personal-control-plane`이 소유 |

**기술 환경:** MSBuild/Visual Studio 18.x, MSVC v145 x64, Windows SDK 10.0.26100.0; Windows App SDK 2.5.1, CppWinRT 2.0.250303.1, SDK BuildTools 10.0.26100.9169, ImplementationLibrary 1.0.260126.7. Python GUI 도구는 `pywinauto==0.6.9`, `Pillow==13.0.0`, `psutil==7.2.2`로 고정. 정책 검증의 Python 환경은 별도 해시 잠금 `.agent-policy/requirements.lock`; 일반 GUI 의존성은 버전 고정만 되어 있다. `app/winui/NuGet.Config`는 공식 nuget.org 공급원으로 명시된다.

**대략적인 규모(트리 값):** 추적 파일 **684개**, 표시된 Blob 합계 **7,877,788바이트**(Git 이력 및 로컬 빌드/캐시 크기 제외). `tests/winui` 325개, `app/winui` 95개, `src/base` 59개, `docs/development` 68개. 제품 `MainWindow.xaml.cpp` 약 **5,129줄**, `CURRENT_STATUS.md` 약 **485KB**, `ERROR_HISTORY.md` 약 **471KB**, `NEXT_DEVELOPMENT_GOALS.md` 약 **129KB**. 이 수치는 구조적 규모를 설명할 뿐 결함의 증거는 아니다.

## 2. 중요도별 발견과 조치

| 순위 | 판정 | 근거·영향 | 권장 조치와 완료 기준 |
| --- | --- | --- | --- |
| **P0 — 문서/운영 정합성** | **확인된 지침 오류** | 루트 `AGENTS.md`, `.agent-policy/PROJECT.md`, `AGENT_EFFICIENCY.md`, `VERIFICATION_PROFILE.md`, `windows-runner-retirement.md`의 Remote Shell 안내가 오래된 단일 `requests/remote-shell/request.json` 및 `windows-vm` 대상을 가리킴. 반면 [제어 저장소의 실제 `docs/TARGETS.md`](https://github.com/tngkrwlsmd/personal-control-plane/blob/main/docs/TARGETS.md)와 워크플로는 Windows VM 전용 `vm-control-fjm09og`, per-target 슬롯을 사용. 예전 명령 재사용 시 잘못된 요청·운영 혼란 위험. | 해당 지침의 현재 경로/대상을 정정하고, **실행 직전 live 상태로 재확인**하도록 명시. 구조화된 Windows 요청의 `windows-vm` target과 혼동 금지. **이번 문서 변경 대상.** |
| **P1 — 비동기 UI 소유권** | **코드에서 확인한 위험, GUI 미재현** | `app/winui/m19_features.cpp`의 `OpenRecentActivityFilePath`는 요청 시작 전 검사에서 WindowTab/패널/route를 확인하지만, `[weak,path]` 완료 콜백에서는 재검사 없이 최근 활동 패널/홈/상태줄을 갱신함. 기다리는 동안 다른 탭으로 전환하면 옛 결과가 현재 화면에 나타날 가능성. | 기존 소유권 컨텍스트를 완료 콜백에서도 검사하고, 성공한 실제 열기 이력만 유지하는 최소 변경. `work/f07-recent-open-stale-completion-20261107`에 독립 후보가 존재하므로 중복 구현 전에 비교. 소스 계약 후 필요 시 승인된 소유 GUI로 실제 시나리오 확인. **기능 코드는 이번에 수정하지 않음.** |
| **P1 — R07 파일 복원** | **한정 수용 + 미검증 경계** | `CURRENT_STATUS.md` 2026-11-07 상단과 중앙 [#42366071785](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42366071785)는 테스트 소유 WinUI F2 Rename→private 복원 정상 경로를 한정 PASS로 기록. 실제 사용자 Undo/Redo·Ctrl+Z는 미연결. 최신 소스에서 사용자 진입 권한을 확대했다는 증거 없음. | 이미 수용된 정상 경로 재실행 금지. 일반 Release의 테스트용 진입/문자열 부재, 창 종료·탭/패널/route 변경 경합, `Post=false`·실패 복원 분기 등 남은 **서로 다른 위험**은 별도 승인·정확한 소스/런타임 증거에 따라 검토. |
| **P1 — 변경 보존/통합** | **확인된 미통합 브랜치** | `main` 외 `automation/search-scope-quoted-recursive-20261107`, `work/f07-recent-open-stale-completion-20261107`, `work/gui-failure-bounded-directory-20261107` 각각 `main` 대비 **ahead 1 / behind 15**, 고유 변경 있음(비교 시점). 열린 PR은 조회 당시 0건. | 첫째는 재귀 색인 검색 작은따옴표 소스 계약 2줄, 둘째는 비동기 완료 UI 소유권 보강과 검사, 셋째는 GUI 실패 증거 수집 개선. 정확한 diff/수용 근거를 비교하고 각 변경의 영향 범위만 검증한 후 통합 여부 결정; **자동 삭제·임의 병합 금지**. |
| **P2 — 증거 수집 효율** | **확인된 코드 비효율** | `tests/winui/gui_failure_evidence.py::_disk_rows`는 `sorted(directory.iterdir())`로 전체 디렉터리 정렬·메모리 적재한 뒤 최대 70개만 사용하고, `len(list(directory.iterdir()))`로 전부 재수집해 절단 여부를 계산함. 대형 소유 실패 폴더에서 O(N) 메모리와 중복 순회가 발생. 제품 핵심 탐색의 병목이라는 근거는 **없음**. | 테스트 전용 제한 크기 상위 71개 수집으로 메모리 상한을 두고 정렬·절단 의미 보존. 기존 비기본 브랜치 구현 비교 후 영향 테스트 한정 실행. |
| **P2 — 문서 내 시점 충돌** | **확인된 기록 불일치** | `NEXT_DEVELOPMENT_GOALS.md` 앞부분은 R07-23E G25 한정 PASS로 적으면서 아래에는 동일 전달 경계를 현재 미완료라고 적음. 이전 수용 시점의 세부 근거가 현행 지침처럼 읽힘. | 현 시점 요약을 최상단에 놓고 충돌 문장을 정정; 이전 작업 기록·실패는 역사적 근거로 유지. 완료 항목과 미검증 항목을 구분. **이번 문서 변경 대상.** |
| **P2 — 유지보수성** | **구조적 부담, 즉시 리팩터링 사유 아님** | `MainWindow.xaml.cpp` 5천여 줄이고 `m19_*`~`m24_*` 파일도 MainWindow 메서드와 컨트롤러 호출이 혼합됨. 분할 파일 자체가 독립적인 책임 추출을 뜻하지 않음. 반면 workspace/session/navigation/file operation/search 컨트롤러는 이미 분리되어 있음. | 이슈가 발생한 소유권 경계부터 동작 보존 방식으로 한 번에 한 책임만 추출; 새 인터페이스·팩토리 일괄 도입 금지. 이미 존재하는 컨트롤러/가치 타입을 우선 사용. |
| **P2 — 공급망·검증 범위** | **관리 필요 위험, 확인된 취약점 아님** | GUI Python 의존성은 버전만 고정, NuGet 패키지 버전 고정과 공식 공급원은 확인. 2026-11-03 문서에는 Pillow 관련 과거 Dependabot 41건 해소 이력이 있으나 **2026-11-11 활성 경보를 직접 조회한 것은 아님**. 이번 현재 설치 바이너리·전이 의존성 CVE/서명 검사는 미실행. | 보안 이슈가 실제 발생했을 때 패키지/간접 의존성·인증 해시·아티팩트 출처를 별도 점검. 신규 배포·매번 전체 재설치·구현 리라이트로 확대하지 말 것. |
| **P3 — 플랫폼/UX 범위** | **기존 미검증·의도된 범위** | Windows Shell 공급자별 동작, 다중 DPI/고대비/Narrator, 외부 공유/전역 클립보드, 별도 Explorer 창과의 완전 동등성은 하나의 과거 GUI PASS로 보증할 수 없음. 듀얼 패널/2단계 탭·Shell 위임은 설계 의도. | 변경이 실제 영향을 준 경우에만 동일 소유 fixture와 관측 환경을 명시해 기능/시각/접근성을 각각 검증. 전체 탐색기 모방을 목표화하지 않음. |

P0/P1/P2/P3는 **후속 조치의 중요도**이며, P1이 곧 검증된 악용 취약점이나 사용자 데이터 사고라는 뜻은 아니다. P0의 운영 경로는 문서 오류가 확정된 것으로 이번 범위에서 먼저 바로잡았다.

## 3. 잘 설계된 부분 및 보존할 불변조건

1. **파일 무결성 우선:** `src/base/file_command_core.cpp`에 이름 복원 영수증·파일 ID·부모 경로 재확인·기존 이름 무덮어쓰기 조건이 있다. `shell_transfer_core.cpp`에는 충돌·취소·스테이징 경계가 있다. 완료되지 않은 위험 분기를 성공으로 표현하지 않고 기존 사용자 파일은 건드리지 않는다.
2. **격리와 제한:** `src/base/shell_isolation_wire.h`는 요청/응답 버전, 경로·PIDL·본문·페이지 상한(예: 본문 8MiB, 모델 2만 항목)을 정의한다. 프리뷰는 `file_preview_safe_open.cpp`의 안전한 핸들/재파싱 검사와 제한을 활용한다. 격리 helper가 보안 샌드박스라는 주장은 금지한다.
3. **상태 수명:** 세션 v4는 이전 v1–v3 읽기 호환성을 유지하며, 현재 패널별 보기와 PaneTab별 정렬/탐색 이력을 혼동하지 않는다. 비동기 작업은 창/탭/패널/route/ticket의 사용 시점 소유권을 지킨다.
4. **실행 비용·안전:** `tools/winui/run_checks.py`에는 영향 범위 중심 FAST/GUI 경계가 있고, 시스템 전역·사용자 데이터 시나리오는 별도 승인이다. 테스트 소유 프로세스·파일·프로필 정리, 정확한 SHA·실행 결과·화면 증거 분리는 유지한다.

## 4. 실행할 개발 목표

**단기(최초 1~3 독립 단위):** (a) P0 문서 경로·시점 정정(이번 문서 작업), (b) 고유 브랜치 3개 diff/현재 테스트 계약을 정확히 대조하고, P1 최근 파일 열기 소유권 문제를 최우선 기능 수정 후보로 분리, (c) GUI 실패 증거 수집의 확정된 메모리 비효율을 작은 테스트 전용 변경으로 해결. 어떤 기능 코드도 이 문서 감사에서 자동 병합하지 않는다.

**중기:** R07 복원 **미검증 위험 시나리오**를 독립적으로 계획·승인·소스/네이티브/실기 환경에서 좁게 수용한다. 실제 결함이 재현된 MainWindow 책임에 한해서만 컨트롤러 경계로 이동한다. 지표가 확인된 검색·대량 폴더·helper IPC 성능만 최적화하며, 데이터 규모·실행 바이너리·측정 조건과 회귀 기준을 기록한다.

**장기/선택:** 실제 Windows 11 탐색기와의 새 실기 대조는 기존 중요 미완료 단위 소진 후 사용자/프로젝트 게이트에 맞춰 수행한다. 보존해야 하는 듀얼 패널·2단계 탭·개인용 제품 범위는 유지한다. 전체 UX 재설계, 공개 배포, 자동 Undo 활성화, 대규모 아키텍처 교체, 포괄적 테스트 재실행은 현 감사만으로 채택하지 않는다.

## 5. 향후 개발 지침 적용 체크

- **착수:** `main`의 최신 SHA/최근 커밋, 비기본 브랜치의 고유 변경·열린 PR·실제 진행 상태를 읽고, 해당 항목의 수용 근거와 차이를 분류한다.
- **안전:** 파일 I/O·복원·외부 앱·프리뷰·Shell 경계에 대해 사용자 입력/경로/리파스·소유권/취소/기한/단회 완료/실패 결과를 책임별로 검토한다. 자식 helper를 신뢰 경계로 오인하지 않는다.
- **검증:** 실제 변경된 의미와 최소 의존 계약을 정하고 정적 → 필요한 컴파일 → 필요한 네이티브/GUI → 실제 픽셀 순으로 선택한다. 동일 SHA의 불필요한 재검사·전체 제품 수용 주장을 금지한다. 날짜·OS·정확한 소스 SHA/EXE/fixture/입력/단계별 PASS/FAIL/NOT TESTED를 기록한다.
- **운영:** Windows VM은 제어 저장소의 **그 순간** 대상·워크플로·승인/상태로 호출한다. 단순 request 파일 내용이나 과거 온라인 기록으로 Runner 점유를 판정하지 않는다. GitHub source repo의 Actions run이 0건이어도 **중앙 Runner 검증 없음**을 뜻하지 않는다.
- **종료:** 기능 변경·문서 변경·배포 여부, 검증 단계, 원래 사용 데이터/설정 보존, 열린 고유 변경, 후속 과제/명시 제외를 분리하여 보고한다. 허가 없이 새 기능·공개 작업·추가 플랫폼 검증을 확대하지 않는다.

## 6. 이번 문서 반영과 한계

**반영:** 루트 `AGENTS.md`의 코드/증거 분류·시점 관리 기준과 실제 Remote Shell 대상을 보완하고, 프로젝트 소유 `.agent-policy/PROJECT.md`, `AGENT_EFFICIENCY.md`, `VERIFICATION_PROFILE.md`, `windows-runner-retirement.md`의 오래된 실행 안내를 현재 계약으로 수정한다. `NEXT_DEVELOPMENT_GOALS.md`의 앞부분에 최신 수용·미검증·브랜치 후보를 분리하고, 개발 문서 인덱스에 본 보고서를 추가한다.

**미반영:** 제품 C++/XAML/테스트·종속성·빌드 설정·패키징·중앙 제어 저장소·범용 정책 코어는 그대로 둔다. Runner 현재 busy, 중앙 최신 실행 결론, 모든 파일의 전체 코드 의미, 진짜 CVE/성능 회귀/GUI 재현은 이번 정적 감사에서 증명하지 않았다. 구현/실행 단위는 별도 후속 검증·승인과 비교가 필요하다.
