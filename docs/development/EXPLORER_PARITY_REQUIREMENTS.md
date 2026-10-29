# Windows 11 탐색기 기능 호환 개발 지침

최초 작성 기준일: 2026-10-19. 당시 소스 기준: `main`
`e3c5275dad98b9f890197b53ceaca333d362b4f9`.
사용자 요청에 따라 탐색기에 최대한 가까운 기능·사용성을 개발 목표로 정리한다.
이 문서는 요구사항이며, 아래 기능의 구현 완료나 새로운 GUI 수용을 뜻하지 않는다.
기존 `NEXT_DEVELOPMENT_GOALS.md`의 G01~G08 및 F01~F18 비교 ID를 재사용한다.

## 2026-10-29 현행 수용과 작업 선정 기준

대조 기준은 `main@3cb5b7691a11910b2d71f5a7b0e112205f341baf`다.
작업 순서·상태·중단 조건의 기준은
[NEXT_DEVELOPMENT_GOALS.md](NEXT_DEVELOPMENT_GOALS.md)의 **앞으로 진행할 작업**이며,
[CURRENT_STATUS.md](CURRENT_STATUS.md)와 기능별 정확한 소스/실행 파일 증거를 함께 본다.

기존 PX02/PX06/PX10/PX12/M23/G01의 수용에 더해 Home 축소, 로컬 대량 폴더
병목, Light 캡션, PX17 로컬 새 항목 메뉴, 검색 패널 축소, F03 문자 경계와
축소 후 포커스 표시가 각 기록된 범위에서 완료됐다. 아래의 넓은 Explorer
요구사항은 이 완료 범위를 다시 열거나 전체 동일성을 주장하는 근거가 아니다.

현재 최우선은 `7e28366c`의 충돌 확인/탐색 차단과 필터 후 정렬 변경의
Release·집중 GUI·해당 픽셀·실제 성능 검증이다. 관련 44/44는 소스/모델 검사다.
그 뒤 PX15 잔여 공백 한 건, PX11 결정, 미채택 PX17/PX08 후보를 검토한다.
자세한 순서와 기존 L03/M24/검색 가로 스크롤 수용은 위 작업 목록을 따른다.
새 필터/정렬 게이트 이후의 성능 재개는 새 증상/근거가 있을 때로 제한한다.
후보 채택과 실제 외부 전송은 별도 결정이다. G03~G05 제외/G07 중단,
Windows 기능 우선 재사용과 현재 탭 상태 소유 규칙을 유지한다.
이 문서 정리는 제품 코드/정책 변경이나 새 Windows 검증이 아니다.
아래 날짜별 비교·실행과 과거 우선순위는 당시 이력이다.

## 2026-10-22 Windows 11 Explorer 재비교 — 완전 동일성 불인정

정식 Windows 11 파일 탐색기의 홈·클라우드 검색·빠른 액세스·공유·메뉴·표시
옵션을 Microsoft 공식 설명과 현재 소스/기존 수용 기록에 대조했다.
별도 Explorer 실행을 통한 Shell 기능은 flyExplorer 자체 동일 기능과 구별한다.
**기능/화면/상호작용의 전체 동등성은 현재 성립하지 않는다.**

[WIN11_PARITY_REAUDIT_20261022.md](WIN11_PARITY_REAUDIT_20261022.md)는
PX01~PX18의 차이를 DIFFERENT/PARTIAL/CANDIDATE/OPEN/INTENTIONAL로
분류하고 기능별 최소 수용 조건을 정한다. 기존 EP01~EP15 / F01~F18과
연결되므로 완료한 항목을 초기 상태로 되돌리거나 새로 전체 검증하지 않는다.

신규 명시 요구: 자체 메뉴와 외부 Explorer 위임 차이(PX01), 로컬 Home·최근
항목 대 클라우드 추천(PX02), 내장/위임 압축 구분(PX03), Gallery(PX04),
클라우드 동기화/오프라인 표시(PX05), Windows Search 범위 차이(PX06),
외부 Windows Share(PX08), 되돌리기 트랜잭션(PX09), 탭 계층 및 보기 설정
소유 범위(PX11), 실제 Explorer 대조 화면 증거(PX15), New-item 템플릿(PX17).
완료 판정은 해당 변경 영역의 증거로만 내리고, G03~G05 제외/G07 중단을 유지한다.



선택 항목 우클릭은 공식 Shell PIDL API로 해당 항목을
Explorer에서 선택해 열고, 폴더 목록의 **빈 배경 우클릭**은
`ShellExecuteExW(explore)`로 현재 폴더를 열 수 있도록
확장했다. 파일 생성/압축/해제와 확장 Shell 동작은 열린
Windows Explorer에서 사용자가 추가 선택한다. Windows 11
메뉴를 WinUI 안으로 그대로 복제하는 것은 아니며,
실제 Windows 소유 픽스처에서 선택 파일과 현재 폴더를 각각 새 Explorer
창으로 넘기는 동작은 `1a5aece2`의 [실측 증거 #39721385267](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39721385267)로 확인했다.
후속 ZIP 소스 정리 `79b03945`도 [소스·Release·GUI #39728188652](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39728188652)
PASS다. 다른 Windows 빌드/타사 제공자의 동작 및 별도 시각 수용은 미검증이다.

## Windows 기본 기능 우선 재사용 원칙 (2026-10-21)

- Explorer/Windows Shell에 이미 있는 압축·해제·연결 프로그램·
  공유·속성·기본 파일 동작은 **공식 공개 API나 Explorer
  자체 UI로 위임**하는 방식을 먼저 선택한다.
  기능을 새로 구현하는 것은 Windows가 지원하지 않는
  flyExplorer 전용 사용자 시나리오에 한정한다.
- Shell의 일부 컨텍스트 메뉴 API만으로 Windows 11의 모든
  최신 탐색기 메뉴를 flyExplorer 프로세스 안에 그대로
  표시할 수 있다고 가정하지 않는다. 필요하면 사용자가
  명시적으로 선택한 항목을 별도 Explorer 창에 전달한다.
- 이미 있는 flyExplorer 고유 기능(듀얼 패널/WindowTab/
  PaneTab/상태와 작업 문맥, 두 패널 간 명시적 전송)은 보존한다.
  자체 ZIP 엔진·배포 의존성의 제거는 Windows 기본 경로의
  실제 검증 이후 별도 변경으로 취급한다.
- 최신 `79b03945`는 WinUI 위임과 자체 ZIP 메뉴 비노출,
  F08 엔진·전용 테스트 29개 파일 제거를 반영했다.
  전체 소스 계약·Release·기능 GUI는 [중앙 CI #39728188652](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39728188652)
  PASS다. 이 기록은 새로운 전체 화면 픽셀 검토나 공개 배포 승인 아님.

## 적용 원칙

- Windows 11 정식 배포판의 사용자가 관찰할 수 있는 동작을 기준으로 한다.
  Windows/Explorer 빌드·채널과 기능 제공 여부를 먼저 기록한다. 현재 로컬 OS의
  `10.0.26300.0` 문자열만으로 정식 배포 기능 또는 채널을 확정하지 않는다.
- 최대한의 기능 호환이 목표다. Explorer의 비공개 API, DLL 주입, 리소스 추출,
  임의 Shell 확장의 프로세스 내 로딩으로 외형·기능을 복제하지 않는다.
- 두 패널과 WindowTab→PaneTab 구조는 유지한다. Explorer와 다른 단축키·상태
  소유 범위는 명시적인 제품 결정으로 남긴다. 기존 동작을 조용히 바꾸지 않는다.
- G03(실제 고배율), G04(F04/F05 고대비·Narrator), G05(실제 USB·SMB·UNC·
  매핑 드라이브 시험)는 **USER-EXCLUDED**다. 이 문서의 포괄적 호환 목표로
  재활성화하거나 출시 차단 조건으로 만들지 않는다.
- 사용자 설정, 전역 클립보드, 실제 휴지통, OS 설정은 이번 점검에서 변경하지 않는다.
  향후 해당 부작용이 필요한 기능 시험은 별도 명시 범위와 소유 데이터가 필요하다.
- 아래의 '차이 후보'는 현재 미구현을 단정하지 않는다. 관련 코드와 최신 수용을
  먼저 대조하고, 재현된 결함 / 개선 요구 / 검증 공백 / 의도적 제약을 구분한다.

## 공통 완료 기준

각 작업은 요구사항 ID, 사용 시나리오, 관련 파일, 상태 소유자, 실패·취소 동작,
필요한 검증 및 실제 증거를 남긴다. 소스 존재만으로 완료 처리하지 않는다.

1. 소유 fixture에 일반/빈/한글/긴 이름/같은 이름/여러 선택 조건을 필요한 만큼 만든다.
2. 명령 전후의 활성 패널·탭·경로·선택·포커스와 실제 파일 결과를 확인한다.
   비활성 패널과 다른 작업공간의 상태가 오염되지 않아야 한다.
3. 비동기 작업은 늦은 결과 거부, 취소, 창 닫기, 부분 실패와 복구까지 정의한다.
   상태 표시 메시지 대신 안정된 모델·파일 결과를 판정 근거로 삼는다.
4. 영향 범위의 소스/네이티브/GUI 검증을 선택한다. 사용자가 요청하지 않은
   전체 빌드·전체 E2E 반복을 자동 요구하지 않는다.
5. 픽셀이 바뀌면 `UI_VISUAL_RETEST.md`의 실제 BEFORE/AFTER 검토를 수행한다.
   기능 GUI와 시각 수용을 별도 기록하며 제외된 환경 시험을 끼워 넣지 않는다.

## 기능 요구사항과 완료 조건

P1은 우선 설계·검증할 항목, P2는 후속 구현 후보, P3는 별도 채택 결정 대상이다.
이 우선순위는 전체 구현·외부 연동·전역 부작용의 자동 승인이 아니다.

| ID / 우선순위 | 목표와 현재 근거 | 관련 파일·경계 | 완료 조건 / 필요한 검증 |
| --- | --- | --- | --- |
| EP01 / P1 | 뒤로·앞으로·상위, breadcrumb, 경로 편집, 새로고침이 일관되게 동작한다. F04/F06 기존 수용 재사용. 풍부한 임의 폴더 자동완성은 차이 후보다. | `app/winui/MainWindow.xaml.cpp`, `app/winui/shell_navigation_controller.cpp` | 소유 로컬 폴더에서 클릭/Enter/Alt+방향키의 지원 계약, 잘못된 경로·취소·연속 요청을 확인. 실패 시 committed 경로/목록 보존, 늦은 응답 무시. 자동완성 입력만으로 디스크 전체 탐색 금지. |
| EP02 / P1 (G01) | 폴더 탭의 정렬·보기·열·그룹 상태 소유 범위를 명확히 한다. 정렬은 현재 PaneTab별 독립이며 v4 세션에 저장한다. 보기·표시 옵션·열 너비는 WindowTab 안의 패널별 소유다. R1 체크 표시는 완료 상태다. | `app/winui/window_tab_state.h`, `app/winui/window_workspace_controller.cpp`, `app/winui/session_coordinator.cpp`, `src/base/ui_session.cpp` | **2026-10-23 계약 확정:** 정렬은 PaneTab별 독립(v4 저장, v1~v3 상속 호환), 보기·표시 옵션·열 너비는 WindowTab 안의 패널별 상태이며, 그룹은 경로/탭 단위 임시 캐시다. F14의 명시적 폴더별 보기 기억은 현재 세션에만 적용한다. 이미 수용한 탭 정렬은 재검증하지 않는다. 탭별 보기/열의 별도 영속화는 미래 기능으로 남긴다. |
| EP03 / P1 (G02/G06) | WindowTab와 폴더 탭의 명령·도움말·키보드 범위를 구별한다. 기존 Ctrl+T/W/Tab은 WindowTab 계약이다. | `app/winui/MainWindow.xaml`, `app/winui/MainWindow.xaml.cpp`, `tests/winui/test_owned_accessibility_layout_gui.py` | 두 작업공간×두 패널×두 폴더 탭에서 실제 Tab/Shift+Tab·방향키·메뉴 열기/닫기 후 포커스 복귀. 숨은 컨트롤로 강제 포커스하지 않은 시작 경로를 검증. 도움말과 실제 동작 일치. |
| EP04 / P1 | 선택·다중 선택·범위 선택·빈 영역·열 머리글·아이콘/상세 보기 동작을 일관되게 한다. F01/F02/F05 및 R1 기존 범위 보존. | `app/winui/file_list_state.h`, `app/winui/FileToolbar.xaml`, `app/winui/MainWindow.xaml.cpp` | Ctrl/Shift 선택, 정렬/그룹/필터 전환 후 선택·스크롤·포커스 정책 명시. 표시 체크와 실제 모델 일치. 상세 열 너비·순서·가로 스크롤 및 좁은 두 패널의 잘림 검토. |
| EP05 / P1 | 명령 모음과 우클릭 메뉴에 선택/위치별 유효한 작업만 표시·활성화한다. 메뉴 개선은 F10 후보이며 기존 Shell 메뉴 경계를 먼저 조사한다. | `app/winui/FileToolbar.xaml`, `src/base/shell_context_core.cpp`, `tests/winui/test_owned_context_menu_gui.py` | 선택 없음/하나/여러 개/폴더/읽기 전용 조건에서 라벨·툴팁·비활성 사유·작업 대상 일치. 키보드 메뉴와 Escape·포커스 복귀, 좁은 창 overflow 확인. 기존 확장 메뉴를 무조건 호환한다고 주장하지 않음. |
| EP06 / P1 | 복사·이동·이름 변경·폴더 생성·삭제의 충돌/진행/취소/실패를 명확하게 한다. 기존 파일 작업 수용과 지원 범위부터 재사용한다. | `app/winui/file_operation_controller.cpp`, `src/base/shell_transfer_core.cpp`, `src/base/shell_clipboard_core.cpp` | 소유 로컬 데이터에서 충돌의 덮어쓰기/건너뛰기/취소 정책, 부분 완료 내역, 파일 무결성과 창 닫기를 검증. undo/redo는 지원 여부·가역 범위를 별도 설계하며 완료 전 버튼으로 약속하지 않음. 전역 클립보드·실제 휴지통 시험은 이번 범위 밖. |
| EP07 / P1 (G07) | 주소·검색·이름 변경에서 한글/Unicode와 조합 Enter/Esc를 보존한다. 필터 IME의 기존 PASS는 전체 입력란 수용이 아니다. | `app/winui/MainWindow.xaml.cpp`, `app/winui/FileToolbar.xaml.cpp`, `app/winui/m19_features.cpp` | 승인된 실제 IME 환경에서 조합/확정/취소를 구별하고 오탐색·이중 명령·글자 손실 없음 확인. 실제 fixture 파일명·경로와 입력 결과 대조. 소스 검사만으로 IME PASS 금지. |
| EP08 / P2 (F11) | 현재 폴더/하위 폴더 검색 범위, 진행·취소·결과 없음·실패를 이해할 수 있게 한다. 제안과 '포함 폴더 열기'는 개선 후보. | `app/winui/m19_search.cpp`, `app/winui/m19_features.cpp`, `tests/winui/test_indexed_search_gui.py` | 검색 모드·루트·상한과 잘림 알림 명시, 연속 쿼리의 늦은 결과 거부, 결과 위치 이동과 원래 작업공간 보존. 색인 실패 시 다른 모드로 몰래 전환하지 않음. |
| EP09 / P2 (F07/F14) | 홈/빠른 접근/즐겨찾기/최근 항목 및 위치별 보기 기억을 앱 소유 데이터로 제공한다. 현재 통합 Home은 즐겨찾기·옵트인 세션 최근 파일·자주 방문한 폴더를 모으며 제한된 GUI 범위가 수용됐다. Explorer/클라우드 Home 전체와 동등하다는 근거는 아니다. | `app/winui/NavigationSidebar.xaml`, `app/winui/MainWindow.xaml.cpp`, `src/base/ui_preferences.cpp`, `src/base/ui_session.cpp` | 사용자 선택으로만 기록·삭제·초기화하고 저장 범위·상한·없는 경로 처리를 정의. OS Explorer 기록을 변경하지 않음. 최근 검색 이력과 최근 파일 목록을 구분. 위치별 저장과 세션 복원을 혼동하지 않음. |
| EP10 / P2 (F08) | 압축 관련 동작은 수용된 외부 Windows Explorer 위임을 우선 재사용한다. 자체 ZIP 엔진은 제거됐으며 내장 압축은 별도 채택 후보다. 형식별 지원은 실제 OS/위임 범위로 명시한다. | `app/winui/file_operation_controller.cpp`, `src/base`의 별도 압축 경계(채택 시), 관련 신규 소유 fixture | 경로 탈출/절대 경로/링크/중복 이름/손상/과도한 해제량 차단, 충돌·취소·부분 출력 정책. 형식/OS/API/라이선스 확인. zip 지원으로 다른 모든 형식 호환을 주장하지 않음. |
| EP11 / P2 (F09/F13) | 연결 프로그램으로 열기·속성·새 폴더·새 텍스트 파일의 기존 구현과 정확한 수용 범위를 먼저 재사용한다. 일반화된 새 항목 템플릿과 Windows Share는 별도 후보이며 전체 GUI 수용으로 확대하지 않는다. | `src/base/shell_context_core.cpp`, `src/base/shell_assoc_type_core.cpp`, `app/winui/FileToolbar.xaml`, `tests/winui/test_owned_context_properties_gui.py` | 공개 OS 계약과 인수 경계를 사용. 연결 없음·실패·취소 처리, 새 파일 충돌 시 덮어쓰기 금지. 기본 앱 등록 변경 금지. 공유는 전송 없는 UI 확인과 실제 외부 전송 승인을 구별. |
| EP12 / P2 (F03/F16) | 미리보기/세부 정보/썸네일의 크기·메타데이터·선택 전환을 일관되게 한다. F03 제한된 안전 포맷은 의도된 지원 경계다. | `src/base/file_preview_supervisor.cpp`, `src/base/file_preview_reader.cpp`, `src/base/shell_thumbnail_core.cpp` | 손상/큰 파일/미지원 포맷 안내, 제한 시간·메모리·worker 정리, 선택 변경 시 stale 미리보기 없음. PDF 등 추가 포맷은 별도 공개 API·격리·의존성 검토 후 채택. |
| EP13 / P1 (G08) | 로컬 대량 폴더에서 스크롤·정렬·검색·취소 응답을 유지한다. 20,000 모델/25,000 색인 상한은 성능 PASS가 아니다. | `app/winui/MainWindow.xaml.cpp`, `app/winui/m19_search.cpp`, `src/base/shell_isolated_supervisor.cpp` | 동일 로컬 fixture와 측정 환경에서 첫 목록/완료/입력 지연·메모리·취소 시간을 기록하고 개선 전 목표 수치를 정함. 상한에서 완전/부분 결과를 구분. G05 시험으로 확대하지 않음. |
| EP14 / P1 | Explorer를 참고해 주소·검색·명령·목록의 정보 계층과 피드백을 통일한다. 현재 Light/Dark·96 DPI 수용 재사용. | `app/winui/MainWindow.xaml`, `app/winui/FileToolbar.xaml`, `docs/development/UI_VISUAL_RETEST.md` | 사용 가능한 동일 DPI·창 크기·합성 fixture에서 실제 화면 비교. 활성/비활성 패널, 선택/포커스/hover/disabled, 메뉴·대화 상자·빈/오류/진행 상태 검토. 앱과 Explorer 비교가 없으면 비교 미검증, 원본 픽셀 미검토면 시각 미검증. |
| EP15 / P3 (F12/F15/F17/F18) | 갤러리·클라우드 상태·새 Insider 메뉴·AI 동작은 별도 채택 후보로 유지한다. | `WIN11_EXPLORER_FEATURE_BENCHMARK_20261012.md` 및 채택 후 지정할 컨트롤러 | 사용자 가치·정식 제공 여부·공개 API·개인정보·의존성·라이선스를 먼저 결정. 자격 없는 환경의 기능은 허위 표시하지 않음. G05 제외를 해제하거나 클라우드 계정/업로드를 자동 승인하지 않음. |

## 2026-10-19 당시 로컬 실행 기록 (이력)

- 시작 시 로컬 `HEAD/main/origin/main`과 GitHub main이 모두 위 SHA였다.
  최근 10개 main 커밋을 확인했다. 제품 소스는 R1 이후 문서 변경뿐이다.
- 중앙 최근 네 CI는 SUCCESS였다. 재사용 가능한 최신 기록
  [39188826255](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39188826255)는
  `7ac35a06`의 **source** 검증이며 이번 로컬 빌드나 현재 SHA의 GUI PASS가 아니다.
- 기존 사용자 변경은 `build.bat` EOF 줄바꿈 차이이며 보존했다.
- 요청받은 `fly.bat build Release`를 로컬에서 실행했다. 최초 실행은 exit **7**:
  `LINK : fatal error LNK1101: MSPDB140.DLL 버전이 잘못되었습니다`.
  바로 앞의 IPDB/IOBJ 전체 코드 생성 안내 자체와는 다른 실제 링크 실패다.
  로그: ignored `logs/explorer-parity-local/build-release.log`.
- MSVC 14.51.36260.0의 `mspdb140.dll`/`mspdbcore.dll`/`mspdbsrv.exe` 버전은
  일치했다. 실행 권한 경계만 바꿔 동일한 정식 명령을 재실행한 결과 **exit 0**으로
  성공했다. 첫 실패는 환경 의존이며 DLL 설치 손상으로 확정하지 않는다.
  후속 로그 `logs/explorer-parity-local/build-release-native.log`에는
  21,808개 중 223개 함수 코드 생성, 나머지 재사용이 기록됐다. 코드·설치 변경 없음.
- 생성 EXE SHA-256:
  `5a2fdab8c1915cc2e647102bd3ced38cb9039dd2301e03e36bd195c0ae08854a`.
  sibling helper SHA-256:
  `924363fd4120b5bd91d2509ff58b60dc2ca7d6ee9ff15e5943c4a57e2060b0d1`.
- `fly.bat run Release <owned fixture>`로 실제 로컬 앱 실행을 확인했다.
  소유 fixture의 두 텍스트 파일과 Nested 폴더, 별도 자식 환경의
  APPDATA/LOCALAPPDATA/TEMP/TMP/USERPROFILE을 사용했다. PID `47548`,
  실제 창 핸들 `4262940`, `Responding=True`를 확인하고 앱을 열어 두었다.
  이 프로세스 관찰은 기능 조작이나 픽셀 검토 PASS가 아니다.
- 실행 래퍼의 `capture_output` 파이프가 GUI에 상속되어 종료 코드는 관찰하지 못했다.
  소유 Python의 경로·인수를 확인하고 해당 래퍼만 종료했다. 별도 앱은 유지했다.
  후속 래퍼는 GUI에 상속되지 않는 로그 파일/DEVNULL과 bounded wait를 사용해야 한다.
  ignored `logs/explorer-parity-local/owned-run/launch-evidence.json`에 근거를 남겼다.
- Computer Use 초기화 후 창 목록 읽기는 두 번 모두 자동 승인 검토 서비스의
  `Selected model is at capacity`로 실행되지 않았다. 제품 GUI 실패로 분류하지 않는다.
  승인 경로를 우회해 다른 화면 자동화를 실행하지 않는다.
- **기능 GUI: NOT TESTED. 시각 수용: BLOCKED (승인 검토 서비스).**
  이번 소스 검토로 Explorer와의 기능/픽셀 완전 호환을 주장하지 않는다.

## 2026-10-19 당시 우선순위와 후속 이력

현재 작업 선정은 상단의 2026-10-29 절과 현행 목표 목록을 따른다.
아래의 다음 작업·제안은 작성 당시의 순서이며 이후 수용된 기능을 다시 열지 않는다.

**세 번째 구현 수용:** L07 상세 보기의 긴 이름 열 침범을 유한 폭 Grid와
말줄임으로 수정했다. 로컬 Release·관련 소스 29개·Dark 비교 및 Light 추가 검토,
UIA 열 너비 변경·정상 종료를 확인했다. 다음은 아직 미검증인 L08의 실제
열 경계 조절 커서·hit 영역이다. 전체 15개 범주가 완료됐다는 뜻은 아니다.

**두 번째 구현 수용:** L06의 선택된 멤버 우클릭 선택 손실을 수정했다.
소유 네 항목 선택/취소 보존과 미선택 행 전환, Release·정상 종료·Dark 화면을
로컬에서 확인했다. 다중 외부 메뉴 실행 제한은 유지하며 자동 GUI 회귀의 새
assertion은 문법 검사만 완료했다. 다음 변경은 L07이다.

**첫 구현 수용:** L05/EP11 중 일반 파일시스템 문서의 기본 앱 열기는 로컬
Release·실제 더블클릭/Enter·폴더 회귀·정상 종료 및 scoped Dark 시각 검토를
완료했다. 실행 파일/스크립트·가상 항목은 지원 범위 밖이며 전체 EP11 완료가 아니다.
정확한 증거와 미검증 경합은 `UI_UX_AUDIT.md` 최신 절을 따른다. 다음은 L06,
그 다음 L07을 독립된 변경 단위로 처리한다.

사용자가 기본 파일 작업의 불편을 추가 지적한 후 실제 관찰한 L05~L10은
[UI_UX_AUDIT.md](UI_UX_AUDIT.md)의 최신 절에 있다. **일반 파일 더블클릭 열기
(EP11), 다중 선택 후 우클릭 보존(EP04/EP05), 긴 이름의 이웃 열 침범 방지
(EP04/EP14)**를 먼저 처리할 세 기본 동작으로 제안한다. 이는 구현 완료나 코드
수정 승인이 아니다. 열 조절 커서/hover 실측 공백, F2 편집 위치·확장자 선택,
외부 Shell 메뉴의 테마 차이도 별도 완료 조건을 남겼다.

2026-10-19 후속 로컬 관찰에서 승인 서비스 차단이 해소됐다. 실제 관찰 결과는
[UI_UX_AUDIT.md](UI_UX_AUDIT.md)의 맨 위 후속 절을 따른다. 기본 폴더 탐색·
뒤로 버튼·Ctrl+L→Tab 및 Dark 화면의 제한적 검토를 완료했으며 전체 기능 GUI나
동일 창 크기 시각 비교를 수용한 것은 아니다. 아래는 최초 설계 우선순위다.
추가로 확인한 L01(Alt 탐색), L02(선택별 명령 활성 정책), L03(유형 문구)은
각각 EP01/EP05/EP04의 구체적 후속 요구다. 제품 코드는 변경하지 않았다.

1. **EP02/G01:** 정렬의 PaneTab 소유 계약부터 결정하고 기존 세션과의 호환 범위를 확정.
2. **EP03/G02·G06:** 시작부터 실제 키보드 순회와 두 수준 탭 명령의 발견 가능성을 확인.
3. **EP05·EP06:** 소유 로컬 fixture에서 선택별 명령과 충돌·취소·실패 결과를 검증하고
   그 근거에 따라 필요한 메뉴/작업 피드백 개선만 선정.

이번 로컬 빌드 및 프로세스/창 생성 확인은 완료했다. 실제 기능·시각 점검의
승인 서비스 차단은 위 기능 결함 목록과 구분해 해소한다.
새 기능 구현은 이번 문서화 요청에 포함하지 않는다.

## 비교 출처

- [Microsoft: File Explorer in Windows](https://support.microsoft.com/en-us/windows/experience/fileexplorer/file-explorer-in-windows)
  — 홈/빠른 접근, 명령 메뉴 및 보기 옵션의 공개 사용 기준.
- [Microsoft: Keyboard shortcuts in Windows](https://support.microsoft.com/en-au/windows/keyboard-shortcuts-in-windows-dcc61a57-8ff0-cffe-9796-cb9706c75eec)
  — 지원할 탐색기 키 동작을 대조할 기준. 앱의 두 수준 탭 예외는 별도로 명시.
- 프로젝트의 `WIN11_EXPLORER_FEATURE_BENCHMARK_20261012.md`, `UI_UX_AUDIT.md`,
  `NEXT_DEVELOPMENT_GOALS.md` — 과거 비교와 현재 수용·제외 결정을 먼저 재사용.
