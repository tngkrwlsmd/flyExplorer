# R12 보기 메뉴: 두 번째 물리 클릭 실패와 체크형 메뉴 후보 — 2026-11-02

## 관측과 원인 경계

- 제품 기준: R19의 `7229144f3566d08e39f13a9ec42c93ef645d1a20`, Release EXE SHA256 `f600f7658b1e703d291ed21dff27bfeceb8dea9d1129f67834b6cf35dafd0a93`.
- [Windows GUI #41373394728](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41373394728) **전체 FAIL**: 독립 입력 화면에서 테스트 앱 소유 보기 버튼과 메뉴 항목 좌표가 실제로 확보됐다. 첫 실제 메뉴 클릭은 세부 정보 창 열기, 자동 본문 읽기 방지, 첫 메뉴 닫기까지 성공. 800ms 안정화 후 두 번째 실제 클릭은 같은 앱 소유 `ViewFileInfoPaneItem`의 `MenuItem`을 정확히 가리켰으나 메뉴가 닫히지 않고 세부 정보 창도 닫히지 않았다. 바로 아래 `ViewDetailsItem`을 실제 클릭했을 때 메뉴가 닫힌 것은 관측했다(해당 행의 명령 전체 동작까지 수용하지 않음). 이 증거로는 외부 창의 입력 가림·단순 대기 부족을 실패 원인으로 볼 수 없으며, 두 항목의 **메뉴 행 유형 차이 또는 포인터 생명주기**를 분리해야 한다.
- 검사 소스 `60c88410d984bd106391243bc108391339d3f650`는 표시·활성·좌표 소유권의 진단 항목을 각각 기록한다. 이번에는 첫 소유 배치에서 클릭 좌표가 확인돼 최상위 전환 자체는 필요하지 않았다. 기존 설정과 테스트 원본은 보존되고 테스트 앱 정상 종료, 임시 GUI 스케줄러 제거가 기록됐으나 **실패 시 생성한 진단 fixture/profile/evidence는 보존**했다. 성공으로 재분류하지 않는다.

## 새 후보와 수용 조건

- R19의 `MenuFlyoutItem`을 같은 뷰 메뉴의 `ToggleMenuFlyoutItem`으로 교체한다. 이 컨트롤은 체크/해제 상태를 가진 메뉴 항목이고, 바로 아래 보기 모드의 체크형 항목은 실제 물리 입력으로 메뉴를 닫았다. 다만 이 차이가 근본 원인이라고 아직 단정하지 않는다.
- `SetFileInfoPaneState(bool)`는 **모델의 현재 상태만 캐시**하고, WinUI `MenuFlyout.Opening`에서만 체크 상태를 동기화한다. 즉, 메뉴가 표시되거나 클릭/닫기 중인 동안 프로그램이 해당 메뉴 항목을 재구성하지 않는다. 사용자 클릭은 기존 `OnViewFileInfoPane` → `Closed` → UI 큐 → `OnToggleFileInfoPane` 경로를 재사용한다. 파일 작업 중 확인창 차단과 미리보기 명시 동의 정책, 패널·탭/v4 소유권은 변경하지 않는다.
- 실제 최신 `main`의 검색 우클릭 보호 등 수용 코드가 유지되는지 대조 후 통합 후보를 만들며, R12 외 관련 소스나 전체 파일 작업은 수정하지 않는다.
- **후속 검증 대기:** 관련 R12 소스 계약, 변경된 XAML·C++를 포함한 정확한 Windows x64 Release, 같은 테스트 소유 폴더의 **실제 메뉴 두 번 클릭(열기/닫기)**, 기존 Alt+Shift+P 및 미리보기 자동 읽기 방지, 원본/설정 보존·정상 종료·성공 fixture 및 작업자 정리. 실제 GUI 두 번째 클릭이 통과하기 전까지 `main`에 제품 코드를 반영하지 않는다. 픽셀 검토는 별개.
- API 근거: [ToggleMenuFlyoutItem](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.controls.togglemenuflyoutitem), [FlyoutBase.Opening](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.controls.primitives.flyoutbase.opening). 문서는 API 동작 근거일 뿐 flyExplorer의 실제 두 번째 클릭 성공 증거가 아니다.

## R12 선택적 포인터 단계 계측 — 2026-11-02 (미수용)

- **개발 브랜치 한정:** `diag/r12-flyout-event-order-20261102`의 코드 `4df050a93cd7077601da8c2b1d6d792da2fac034`에서는 진단용 `R12_UI_TRACE=1`이 설정된 테스트 앱에 한해 메뉴 항목의 **이미 처리된(handled) 포인터 누름/뗌 이벤트도** 기록한다. 세부 정보 창 항목 `details_press/details_release`와 정상 작동 비교용 보기 항목 `other_press/other_release`를 기존 `details_click/flyout_closed/action23_dispatch` 기록과 분리한다. 이로써 두 번째 시도에서 포인터 단계가 도달하지 않은 것인지, 도달했지만 `Click`이 발생하지 않은 것인지, `Click` 이후 닫힘/큐 전달에서 막힌 것인지 추후 로그로 비교할 수 있다. 비진단 모드에서는 추가 이벤트 핸들러를 설치하지 않고, 실제 패널 명령·검색·파일 데이터는 변경하지 않는다.
- **검증:** 정확한 커밋 `4df050a93...`에 대한 [원격 R12a 소스 계약 5/5 PASS 및 XAML/XML·GUI 테스트 스크립트 문법 PASS #41402534082](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41402534082). 이 검사는 R12 진단용 C++ WinUI 앱의 컴파일/GUI 클릭 재현이 아니다. **두 번째 실제 포인터 클릭 실패의 원인은 여전히 미확정**이며 새 계측을 성공으로 수용하거나 `main`에 합치지 않는다. 남겨 둔 기존 실패 증거와 소유 테스트 fixture/profile을 삭제하지 않는다.
- **실패 직후 로그 분리 (2026-11-02):** 진단 스크립트/검사 커밋 `7c126bcaf6980d2661ea9fa6635fb7c3c6423b5e`는 두 번째 클릭 후 상세 창 닫기 대기 실패가 발생하면, 다른 보기 항목 물리 클릭 또는 UIA Invoke를 시도하기 **전에** 앱 소유 임시 프로필의 제한된 이벤트 로그를 읽고, 두 번째 `flyout_open` 이후 `details_press/details_release/details_click/flyout_closed/queue_added/action23_dispatch`의 도달 여부와 순서를 별도 결과에 보존한다. 이후의 비교 진단과 종료 시 전체 로그는 종전대로 남긴다. 심볼릭 링크·미허용 필드·16KiB 초과 로그는 추론 없이 오류로 구분한다. [원격 소스 계약 **6/6 PASS** 및 GUI 스크립트/XAML 문법 PASS #41403170045](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41403170045). **Windows 빌드·실제 두 번째 물리 클릭·픽셀 검증은 수행하지 않았다.**
- **후속 경계:** 별도로 승인된 정확한 Windows 빌드와 소유 GUI 입력 시에만 위 네 가지 포인터 단계와 `Click`/Flyout `Closed`의 이벤트 시각 순서를 비교하고, 확인된 실패 위치의 최소 수정만 채택한다. 이미 실패한 클릭 경로를 같은 증거 없이 반복하지 않는다.

## R30 Windows 실제 포인터 이벤트 도달 지점 — 2026-11-02

- **실제 실행·빌드 소유권:** `DESKTOP-FJM09OG-vm-control` Windows 소유 러너에서 진단 후보 `bad5fe35c7363127ffc9ba3c21406103d3613582`의 실제 x64 Release 빌드 **종료 코드 0 PASS** ([#41405640392](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41405640392)). 실행 EXE SHA256 `400c3e35be8d61bfc82c33b4bca35feba215b1e870e7425b319bdda0bb11b036`. [R30 실제 GUI #41407858096](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41407858096)에서는 같은 EXE로 소유 폴더 첫 마우스 클릭의 상세 창 열기·첫 메뉴 닫기·자동 본문 미리보기 차단 **PASS**, 800ms 정착 뒤 두 번째 실제 클릭의 상세 창 닫기 **FAIL**. 비교용 일반 보기 항목 클릭은 메뉴 닫기 확인. 테스트 원본 보존 및 전용 GUI 스케줄러 제거가 기록됐고 실패 fixture/profile/증거는 유지했다.
- **진단 로그 수집 경로 교정:** GUI 진단 스크립트는 소유 프로필의 `temp`를 조회했으나 실제 로그는 `tmp/flyExplorer-r12-events.log`에 생성돼 첫 실행 결과에는 `missing_owned_temp_trace`가 찍혔다. 이는 **이벤트 미발생 증거가 아니라 로그 경로 가정 오류**다. 기존 실패 증거를 삭제·변경하지 않고 해당 소유 프로필의 `tmp`만 읽어 [Windows 읽기 전용 이벤트 추출 #41408562597](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41408562597) **PASS**. 초기에 이벤트명 숫자를 허용하지 않은 정규식 실패[#41408150781](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41408150781)와 PowerShell 인용 구문 실패[#41408348364](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41408348364)는 읽기 작업 오류로 구분한다.
- **실제 이벤트 시퀀스 (GetTickCount64 기준, ms):** 첫 `flyout_open(16327140)` → `details_press(16327656)` → `details_click(16327656)` → `flyout_closed(16327671)` → `queue_added(16327671)` → `action23_dispatch(16327671)` → `pane_state=1(16327671)`. 두 번째 `flyout_open(16329062)` → `details_press(16329593)` → `details_release(16329593)`까지만 기록됐다. 이후 `details_click`, 두 번째 메뉴의 `flyout_closed`, `queue_added`, `action23_dispatch`가 **모두 없었다**. 12.5초 후 비교용 일반 보기 항목의 `other_press/other_view_click(16342093)`와 `flyout_closed(16342109)`는 별도로 기록됐다. 두 번째 시도는 앱 소유 항목의 pointer press/release까지 도달했고 이후 **Pointer→Click 단계에서 멈췄다**. 실제 모델 명령 처리·큐·세부 정보 레이아웃 단계까지 진입했다는 증거는 없다.
- **정확한 판단 경계:** 실제 두 번째 입력의 `Click` 미발생과 메뉴 미닫힘은 확인됐지만 **어떤 내부 조건이 Click을 억제했는지**(컨트롤 상태, 포인터 캡처, 메뉴 입력 처리 등)는 아직 입증하지 않았다. 첫 클릭의 `details_release`는 기록되지 않았으므로 릴리스 기록이 없는 것을 실제 릴리스 입력 자체의 부재라고 단정하지 않는다. GUI 케이스의 전체 결과는 계속 FAIL이며, R12 제품 미수용 및 `main` 미반영을 유지한다.
- **후속 최소 조사:** 실패가 발생하는 선택형 메뉴 항목의 `PointerCaptureLost`·`PointerCanceled`, 두 번째 `IsEnabled`·`IsChecked` 및 히트테스트 상태를 앱 소유·고정 필드로 제한해 비교하는 것이 다음 원인 구분 후보이다. 실제 구현/재실행 전에 기존 R30 원본 증거를 보존하고, unrelated 기능이나 파일 작업을 수정하지 않는다.

## R31-R32 follow-up, 2026-11-02

R31 Windows x64 Release source d8f6df2b: build PASS (run 41412224914), GUI second click FAIL (run 41414650616). First click opened and dismissed the menu, without automatic preview. During second click the Details item was enabled, checked and hit-test visible (state=7). Pointer press/release arrived, while cancel/capture-lost, Click, menu Closed and command dispatch did not occur. This narrows the failure to click recognition but does not establish that checked state causes it. Existing failure fixture remains retained.

R32 source 1900897e adds opt-in Tap and pointer enter/exit diagnostics without changing commands. Rocky8 focused source tests 6/6 PASS, plus XAML and script syntax PASS (run 41418178742). Windows build, GUI and pixel acceptance of R32 remain NOT TESTED. The R12 feature is still unaccepted and not on main.

## R32 Windows 실제 Tapped 이벤트 결과 — 2026-11-02

- **실제 Windows 빌드:** 독립 작업공간의 정확한 소스 `dc8a8ff9326eccda5e19bd9c20b225db058cb8c7`로 x64 Release [#41435761491](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41435761491) 종료 코드 0 PASS. EXE SHA256 `b34fc0cca7c207c3423d2379aeb5ef571ded96d71e613bb7866dab1700bf09a4`, helper SHA256 `899f46d67452b0d7d22ad2168b4fd5a237097b697401034704856a3f883d209c`. 원본과 이전 R30/R31 EXE 해시 보존 검사 통과. 별도 작업공간·실행 파일·로그는 기존 경로와 분리했다.
- **소유 GUI [#41438665612](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41438665612):** 정확한 위 EXE의 첫 물리 클릭 상세 창 열림·첫 메뉴 닫힘·자동 본문 미리보기 차단 PASS. **두 번째 실제 물리 클릭은 상세 창 닫기 FAIL** (`R32_GUI_WORKER_EXIT=1`); 해당 Actions 요청 자체는 실패 진단 정보 수집에 성공하여 success로 종료했다. 비교용 일반 보기 항목 실제 클릭은 메뉴 닫힘 확인. 실패 증거 보존, 앱 소유 테스트 원본 불변 및 GUI 작업 스케줄러 제거를 확인했다.
- **두 번째 시도 이벤트 시퀀스:** `flyout_open(1593546)` → `details_ostate=7(1593546)` → `details_enter(1594109)` → `details_press(1594109)` → `details_pstate=7(1594109)` → `details_release(1594109)` → `details_rstate=7(1594109)` → **`details_tap(1594109)`**. 두 번째 시도에서 `details_exit`/취소/캡처 상실, `details_click`, 두 번째 메뉴 `flyout_closed`, `queue_added`, `action23_dispatch`는 없었다. 비교용 항목의 `other_press/other_view_click`과 메뉴 `flyout_closed`는 12초 뒤 별도 기록됐다.
- **원인 경계:** 두 번째 항목의 포인터는 항목 영역에 진입하여 누름·뗌과 `Tapped`까지 전달됐음이 확인됐다. 그럼에도 실제 메뉴 명령 `Click`은 생성되지 않았다. 첫 클릭은 `details_press`와 `details_click`이 기록되고 `Tapped`는 기록되지 않아, 두 이벤트가 무조건 같은 순서로 생성된다고 단정하지 않는다. **WinUI 메뉴 항목의 입력/Click 활성화 상태 전환 문제로 범위가 더 좁혀졌지만**, 그 내부 원인과 제품 해결책은 미확정이다. 체크된 상태 자체가 원인이라는 실험 증거도 아직 없다.
- **수용 상태 및 후속:** R12 제품은 **미수용**, `main` 미반영. `Tapped`를 실제 명령으로 우회하는 제품 변경은 아직 하지 않았다. 다음 변경은 중복 실행 방지·키보드 클릭 보존·메뉴 닫힘 후 큐 처리·파일 작업/미리보기 차단을 함께 보장하는 최소 후보로 분리하고, 정확한 후보 Windows 빌드와 두 번의 실제 클릭을 다시 수용해야 한다. R30/R31/R32 실패 fixture·profile·로그 및 기존 사용자 파일·설정은 삭제하지 않는다.

## R33 Tapped 보완 후보 — 2026-11-02 (제품 미수용)

- R32 실제 소유 Windows 로그에서 두 번째 메뉴 클릭은 마우스 press/release 및 Tapped까지 도달했으나 Click/Closed/명령 23이 발생하지 않았다. 따라서 새 입력 진단을 반복하지 않고 R12 진단 브랜치의 해당 메뉴 항목에 한정해 Tapped의 handled 이벤트까지 받는 보완 처리기를 추가했다.
- 기존 Click은 키보드/접근성/정상 포인터 명령의 우선 경로로 유지한다. Tapped는 마우스 유형에만 적용하고, 한 UI 큐 뒤에도 Click이 없는 경우에만 메뉴의 IsOpen·항목 활성/히트테스트·열림 세대를 확인한 뒤 한 번만 요청을 선점하고 Hide한다. 명령 23은 반드시 Flyout Closed 이후 기존 DispatcherQueue와 MainWindow의 파일 작업 busy/confirmation 차단을 경유한다. 메뉴가 취소되거나 다시 열리면 오래된 Tapped/명령을 거부한다.
- 변경 범위: FileToolbar.xaml.cpp/.h, R12 관련 소스 계약 및 이 문서. 파일 작업·미리보기·세션 v4·전역 클립보드·Windows 설정 경로는 수정하지 않았다. 다른 메뉴의 Tapped를 일반화하지 않는다.
- **검증 상태:** 정확한 제품·검사 커밋 `4b0dd538e86ca067742fa51ceec42f7c4fa1f058`의 R12 소스 계약 7/7 PASS. 단, Windows C++/XAML 컴파일, 새 Release·실제 마우스 두 번 열기/닫기 GUI, 키보드/UIA·중복 호출·Esc·원본 보존은 별도 검증 전이다. R12가 실제로 통과하기 전까지 main으로 통합하지 않으며 이전 R30~R32 실패 원본은 보존한다.

- 지연 실행이 다른 최상위 탭으로 넘어가지 않도록 메뉴를 열 당시 `WindowTab.identity`를 저장하고, Tapped 보완 예약 및 Closed 이후 명령 실행 직전에 동일 식별자를 재확인한다. 종료 중에는 0을 반환해 차단한다. 기존 `command==23` 파일 작업 확인 조건은 그대로 유지한다.

## R33 소스 검증 실행과 정확한 수용 한계 — 2026-11-02

- R33 소스 확인은 등록된 `windows-vm` 경로의 별도 테스트 소유 체크아웃으로만 수행했다. 정확한 제품·검사 소스 `4b0dd538e86ca067742fa51ceec42f7c4fa1f058`의 [Windows 작업 #41455852406](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41455852406)에서 **R12 관련 소스 계약 7/7 PASS**를 확인했다. 성공 항목에는 정상 Click 경로 보존, 처리된 마우스 Tapped 보완 구독, 한 번만 실행하는 상태, 메뉴 Closed 뒤 큐 호출, 탭 식별자 보호, 파일 작업 확인창 차단과 미리보기 명시 동의 보존 검사가 포함된다. 이것은 코드의 문자열·구조 계약 검사이며 실제 WinUI 이벤트 동작 증거가 아니다.
- **작업 전체는 FAIL:** 위 7/7 PASS 후 GUI 검사 스크립트/XAML 문법 파싱을 위한 `python -c` 인수가 PowerShell에서 잘못 인용돼 `NameError: name 'tests' is not defined`가 발생했다. 이 보조 문법 단계는 완료되지 않았으며 제품 오류·메뉴 클릭 실패로 취급하지 않는다. 해당 GUI 검사 스크립트와 XAML은 앞선 R32 문법 PASS 당시와 동일하고 R33에서 수정하지 않았으므로 이전 성공 근거를 재사용한다.
- 앞선 [#41455163201](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41455163201)은 검사의 오래된 문자열 기대값 두 건, [#41455573126](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41455573126)은 신규 소스 검사에서 `main` 변수를 초기화 전에 참조한 테스트 코드 오류로 각각 FAIL이다. 해당 문제를 변경한 후보 후속 커밋을 사용해 최종 7/7 PASS를 얻었으며 과거 실패를 PASS로 재분류하지 않는다.
- 기존 수용 제품 `main`은 변경하지 않았고, 미수용 R12 후보는 이 브랜치에만 남겼다. Windows VM 요청 슬롯은 [idle 복원](https://github.com/tngkrwlsmd/personal-control-plane/commit/0aba4b8bab59ae7be68111a63e903ea77931cbfc)됐다. 세 번의 원격 실패 실행의 소유 폴더와 오류 근거는 별도 보존하여 임의 정리하지 않았다.
- **다음 수용 경계:** 변경된 WinUI C++ 실제 컴파일과 이 후보의 기존 테스트 소유 폴더 두 번 물리 클릭, 키보드/접근성 정상 경로, 본문 미리보기 자동 읽기 방지, 파일 원본·설정 보존 및 성공 시 소유 자원 정리를 먼저 확인한다. 새 제품 GUI PASS 없이는 `main` 반영·R12 완료 처리·관련 진단 브랜치 삭제를 하지 않는다. 단일 소스 계약은 이미 통과했으므로 재실행하지 않는다.

## R34 Windows 첫 Release 컴파일 오류와 정확한 최소 수정 — 2026-11-02

- [Windows x64 Release #41456856186](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41456856186)는 정확한 후보 `ccca046537acc5cbb98069f7c46295b665c98400`를 새 소유 작업공간에서 빌드했으나 **FAIL**. 첫 관련 오류는 `FileToolbar.xaml.cpp(232,29) error C2676`: `TappedRoutedEventArgs::PointerDeviceType()`가 반환하는 `Microsoft.UI.Input.PointerDeviceType`을 `Windows.Devices.Input.PointerDeviceType` enum과 직접 비교한 타입 불일치다. 이 빌드는 GUI나 변경 기능을 실행하지 않았다. 기존 R30~R32 실패 증거·EXE와 사용자의 설정·파일을 임의 삭제하거나 수정하지 않았다.
- 보완 후보에서 파일의 장치 유형 include와 비교식만 WinUI3의 `Microsoft.UI.Input.PointerDeviceType::Mouse`로 교체하고 소스 계약에 정확한 네임스페이스 검사를 추가한다. 메뉴 상태·명령 순서·파일 작업 경로 자체는 변경하지 않는다. 원격 VM의 실패 작업공간은 컴파일 재사용 가능성을 위해 보존하며 새 증분 빌드 전에 기존 산출물·소유권/작업 상태를 점검한다. **새 후보 컴파일과 실제 물리 두 번 클릭은 아직 별도 검증 전**이다.

## R39–R43 최종 R12 Windows 수용 — 2026-11-03

- [R39 x64 Release #41469825133](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41469825133): source contract PASS, native Release build exit 0. C++ 코드 `a5a721f21ceab812ea9894d15d08184e35062296`, EXE SHA256 `5a1098cdd77cee4f7a33cedb55e1573e73f97219d921fc1d828c6d407db8c202`. `WindowWorkspaceController`의 첫 탭 식별자 `0`을 유효하게 보존하고 종료/미존재 상태는 `std::nullopt`로 구별하여 지연 `action23` 차단 오류를 수정했다.
- [R40 #41547423989](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41547423989)는 실제 메뉴 행 마우스 열기·닫기와 exactly-once 동작은 PASS였으나 닫힌 패널에서 사라진 UIA 자식을 읽는 검사기 오류로 전체 실패했다. 이 증거는 폐기하거나 제품 FAIL로 대체하지 않았다.
- [R41 #41547907684](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41547907684): 닫힌 패널 검사기를 수정하여 keyboard-opened View flyout + 실제 두 번의 Details 행 클릭, command 2회/보완 tap 1회/stale 0회, 자동 본문 읽기 없음, 독립 파일·설정 보존, 정상 종료/fixture 삭제 **전부 PASS**.
- [R42 #41548314025](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41548314025): **완전 물리 마우스 검증 PASS**. 보기 버튼 자체를 실제 마우스로 열고 세부 정보 창 항목을 실제로 두 번 클릭해 열기·닫기와 메뉴 닫힘 모두 PASS, action 23 정확히 2회, 보완 `Tapped` 1회, stale 0회. 독립 파일/기존 설정/자동 미리보기 정책 및 종료·테스트 프로필 삭제 모두 PASS.
- [R43 #41548691840](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41548691840): 같은 고정 EXE의 Alt+Shift+P와 Alt+P 각각 열기/닫기 및 기존 파일·설정 보존, 정상 종료/프로필 삭제 전부 PASS. 최종 GUI 검사 커밋 `8d2fc11136ec885b8e9561aac867b1fe534cd010`은 빌드 커밋에서 Python GUI 검사기만 변경한다. 픽셀 단위 시각 비교 및 컨텍스트 메뉴 독립 입력은 이번 수용 범위가 아니다.
- R12 기능은 이 검증 경계에서 **수용**한다. 역사적 R25–R38 FAIL은 당시 결함과 검사기 실패를 구분하는 참고 증거로 보존하고, 기존 소스·바이너리·사용자 데이터를 임의 삭제하지 않는다.
