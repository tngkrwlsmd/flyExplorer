# flyExplorer 작업 인계 — 2026-10-19 L08 커서 OPEN, G01 코드·빌드 PASS


## 2026-10-21 EP06/L10 구현 — 빌드·GUI·시각 검증 보류 (사용자 지시)

- 기준 main은 직전 `5ba90042`. 제품 코드 변경 `612e2fdc`(EP06),
  `05175d29`(L10) 및 회귀 계약 추가 `9ff69c2f`, `88f4a446`을
  순차적으로 main에 반영했다. 기존 비동기 파일 작업, Windows
  Shell 보조 프로세스, 복사·이동·휴지통 안전 정책은 그대로다.
- EP06: 휴지통·동명 파일 확인 단계에서 사용자가 취소할 때
  `StartStatus::Cancelled` 안내를 표시한다. 실제 전송 도중 취소
  (`report.aborted`/`ERROR_CANCELLED`)와 다른 오류를 구분하며,
  일괄 전송은 트랜잭션이 아니므로 이전 항목이 이미 처리됐을 수 있다는
  경고와 닿은 폴더의 갱신 로직을 보존한다.
- L10: 기존의 격리된 외부 Windows 메뉴와 다중 선택 시 속성만 허용하는
  정책을 유지하면서, 메뉴 시작 안내와 금지 명령 결과(`code==65`),
  속성 창 종료 미확인(`code==69`)을 구별해 안내한다.
  앱 자체 우클릭 메뉴의 시각·레이아웃 전면 교체는 수행하지 않았다.
- **2026-10-21 명시적 사용자 지시:** 빌드, GUI 및 시각 검증은
  사용자가 따로 지시할 때만 수행한다. 프로젝트별 `AGENTS.md`
  지침 `fca36be8`에 기록했다. 수정 내용을 읽어 보존 범위를 점검했으나,
  회귀 계약의 실행, Release 빌드, 실제 GUI·화면 비교는
  **전부 NOT TESTED**이며 신규 제품 기능 수용 PASS를 주장하지 않는다.
- 다음 개발 후보: 요구된 L10 앱 자체 공통 명령과 외부 메뉴의 사용성
  구분, EP06 건너뛰기·부분 작업 정책, EP11 기본 앱 연결 실패·중복 요청.
  사용자 제외 G03~G05, 중단 G07 및 원인 미확정인 G01 종료 잔류는 보존한다.



## 2026-10-21 EP01/L01·L03·L09 기본 사용성 개발 (검증 최소화)

- 기준: 제품 `main` `8402d318`, 변경 순서 `8f86f587` → `1ce0daba` → `25cb91ce`.
  G01 종료 잔류는 별도 OPEN이며 2026-10-21 덤프 수집 준비 결과를 보존한다.
- EP04/L03: `file_detail_controller.cpp`에서 등록된 Windows 파일 유형 이름을
  확장자 설명 뒤에 다시 붙이지 않고, 유형 열에 등록 이름만 표시한다.
  등록 유형이 없으면 기존 확장자 대체 문구를 유지하고 Shell 항목의
  제공자 유형·아이콘·미리보기 처리 경로는 변경하지 않았다.
- EP01/L01: `MainWindow.xaml.cpp`의 기존 PreviewKeyDown 경로에
  Alt+Left/Right/Up을 추가했다. 현재 활성 패널의 기존 뒤로/앞으로/
  상위 이동 핸들러를 재사용한다. 편집기·메뉴·대화 상자의 키 입력 경로,
  Ctrl/Shift 조합은 건드리지 않는다.
- EP06/L09: `m21_commands.cpp`에서 이름 변경 시작 및 확정 시
  파일 또는 폴더 하나만 선택하도록 검사하고, 상태 표시줄에 편집
  대상 이름과 Enter/Esc 안내를 표시한다. 기존 F2 확장자 제외
  선택·비동기 파일 작업·사용자 데이터 보호 처리는 변경하지 않았다.
- **검증 상태:** 해당 파일의 수정 코드와 `main` 반영은 읽기 전용으로
  대조했다. 사용자 요청에 따라 Windows Release/GUI/픽셀 비교 및
  전체 테스트는 **실행하지 않았다**. 따라서 기능·시각 수용은 NOT TESTED이고
  마지막으로 수용된 이전 바이너리의 결과를 신규 변경의 PASS로 확대하지 않는다.
  다음 추가 작업은 이 세 항목을 다시 설계하기보다 사용 중 재현되는 문제를
  기준으로 최소 수정한다.
- 사용자 제외 G03/G04/G05, 사용자 중단 G07은 재개하지 않는다.
  L08의 사용자 수동 커서 정상 보고와 자동화 실패도 각각 보존한다.


## 2026-10-21 최신 인계 — G01 소유 덤프 수집 경로 준비

- tests/winui/owned_process_dump.py를 추가하고 shortcut GUI 종료 타임아웃에
  연결했다. 원래 Popen 핸들/PID/실행 파일을 검증하고 읽기 전용에 가까운 제한된
  핸들만 별도 수집기에 상속한다. 수집 제한 10초; 원래 종료 실패를 PASS로 바꾸지 않는다.
- 실제 합성 helper 정지 시험에서 4개 thread/context/stack 수집, 대상 생존,
  기존 소유 복구·정리·설정 보존을 확인했다. 최초 unused-slot 파서 오류를 수정했고
  표준 하네스 51개·관련 소스 16개·정적 검사 PASS. 제품 구현/빌드/UI 변경 없음.
- 실제 WinUI 종료 실패 훅 실행·심볼 스택 분석은 아직 없다. G01 원인/해결을
  주장하지 않는다. 다른 소유 프로브는 다음 필요한 신규 실행 전에 같은 수집기를
  연결할 수 있다. 이미 수용한 GUI를 동일 조건으로 재실행하지 않는다.
- 원시 덤프는 ignored logs/의 소유 증거에만 보존하고 commit/upload하지 않는다.
  합성 시험 덤프는 정리했다. 전역 WER·보안 설정·디버거 설치를 바꾸지 않았다.
- 전체 해시·증거·한계는 CURRENT_STATUS.md 최신 G01 절과 tools/winui/README.md.
  G07 사용자 중단과 G03~G05 제외, G02/G06·세션·G08 수용을 보존한다.
- 사용자가 요청한 대로 이 완료 단위도 검토 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G08 helper 계측 도구·표준 검증 복구

- 로컬 합성 폴더의 native helper 페이지 계측 도구를 추가했다. 200개 사전 시험 후
  8,000개/8페이지를 읽어 항목·내용·설정 보존과 정리 PASS. 첫 페이지 169.320 ms,
  페이지 합계 1,458.497 ms. GUI/정렬/색인/20k·25k 성능으로 확대하지 않는다.
- 설치된 tests 패키지 때문에 표준 unittest 경로가 실패하는 문제를 명시 파일
  로더로 복구했다. 표준 하네스 43개·관련 Shell/streaming 19개·실제 helper 복구/
  정리 회귀 및 정적 검사 PASS. 제품 구현/바이너리는 바꾸거나 다시 빌드하지 않았다.
- 재현 명령과 전체 SHA/측정 범위는 tools/winui/README.md 및 CURRENT_STATUS.md.
  동일한 측정을 성공 확인 목적으로 반복하거나 지원 상한을 임의로 높이지 않는다.
- 사용자는 G07 실제 IME 시험을 중단했다. 자동 재개하지 않는다. 중단 정리 당시
  PID 15472 창 없는 프로세스 잔류와 소유-only 종료를 기록했다. 스택 미확보,
  원인 미확정이며 G01 종료 위험은 여전히 열려 있다. 실제 재발 시 스택을 확보한다.
- G02/G06·구형 세션 수용과 G03~G05 제외를 보존한다. 새 GUI/시각 수용 없음.
  완료 단위마다 바로 push하라는 사용자 지시를 유지한다.

## 2026-10-21 최신 인계 — G01 구형 세션 호환 확인

- ebe26cf9로 v4 저장기를 v3으로 오판하던 회귀 검사를 복구·push했다.
  실제 Release 네이티브 41개와 관련 소스 15개 PASS. 제품 구현 변경 없음.
- 같은 EXE 78fb331f...로 실제 구형 v1/v2/v3 기본 실행 복원과 작업 공간의 명시
  v4 저장을 확인했다. 좌우 탭·선택·정렬, 버전별 표시 옵션과 Back 히스토리를
  저장 결과의 독립 디코딩으로 확인했고 세 실행 모두 정상 종료 0·원본 불변이었다.
- 구형 세션 실측 공백은 위 범위에서 닫는다. 이전의 구형 세션 미검증 문구는
  이 수용 전 기록이다. 정확한 전체 해시·범위는 CURRENT_STATUS.md 최신 G01 절.
- G01 간헐 종료 위험은 여전히 원인 미확정이다. 실제 재발 때 네이티브 스택을
  확보한다. 정상 실행을 반복하거나 추측한 종료 코드를 추가하지 않는다.
- G02/G06 완료 기준선과 G03~G05 제외는 유지한다. 제품 픽셀 변경 없이 Dark
  복원 화면만 검토했으며 전체 시각 PASS를 주장하지 않는다. 소유 앱 잔류 없음.
- 이번 결과 문서도 사용자 지시에 따라 완료 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G02 남은 로컬 검증 완료

- main `44d770ee`와 origin/main 일치를 확인했고 중앙 최신 CI는 이전 `7ac35a06`의
  source PASS임을 구분했다. 현재 수용은 실제 로컬 Computer Use 결과다.
- 제품 변경·재빌드 없이 EXE `78fb331f...`로 새 격리 PID 20760을 실행했다.
  시작 포커스부터 Tab 39회 순환, 역순 이동·F6·주소/검색·정렬 메뉴 복귀 및 재열기,
  정상 Alt+F4 exit 0·사용자 설정과 합성 파일 12개 불변을 확인했다.
- G02 시작/메뉴의 미완료 게이트를 해당 로컬 범위에서 완료했다. 아래 G02 순회 대기
  내용은 과거 기록이며 다시 실행할 지시가 아니다. G06 완료 증거도 그대로 보존한다.
- 현재 상태·시각 범위·전체 해시는 CURRENT_STATUS.md와 UI_UX_AUDIT.md 최신 절.
  문서만 갱신하며 추가 소스 검사·빌드나 새 기능을 자동 시작하지 않는다.
- G01 간헐 종료 위험은 해결 주장 없이 유지한다. 실제 재발 때만 네이티브 스택을
  확보하고 동일 조건 반복/추측 수정은 피한다. G03~G05 제외는 유지. 소유 앱 잔류 없음.
- 사용자 지시에 따라 이 완료 기록도 검토 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G06 포커스 회귀 검증 완료

- 빌드 사전 점검은 `b02c51a6`으로 main에 push 완료. 사용자는 이후에도 검증된
  논리 작업 단위가 끝나면 바로 커밋·push하도록 승인했다.
- G06: `RefreshTabs()`의 Clear/recreate를 기존 TabViewItem 재사용으로 수정했다.
  제품 blob `f5ae9266...`, EXE `78fb331f...`; Release·관련 소스 25개와
  실제 두 작업 공간×좌우×두 탭 방향키+Enter·Dark 전후 검토·exit 0 확인.
  사용자 설정과 12개 합성 파일 불변. 자동 GUI 회귀 확장은 정적 검사만 완료했다.
- 다음 미완료 범위는 G02의 시작부터 연속 순회·메뉴 복귀를 정상 종료까지 확인하는
  좁은 검증이다. 이미 수용한 G06 네 영역이나 빌드를 이유 없이 반복하지 않는다.
- G01: 기준 바이너리 첫 종료의 0xC0000005와 후속 정상 종료를 모두 보존한다.
  이번 탭 수정이 종료 위험을 해결했다고 주장하지 않는다. 새 제품 기능을 섞지 않는다.
- 캡처가 검게 나왔던 도구 문제는 사용자 바탕 화면 복귀 및 JS 캡처 세션 재연결로
  복구했다. 검은 화면 구간은 기능/시각 판정에서 제외했다. 남은 소유 앱은 없다.

## 2026-10-20 G02/G06 후속 — 확인된 GUI 범위 보존

- main `db10ef42`, 동일 기존 EXE `eb89f47d...`로 소유 실행 1회, exit 0.
  두 작업 공간×좌우×두 폴더 탭 이름과 추가 대상, B의 닫기 대상 및 A 보존을 확인했다.
  F6/실제 파일 선택, 목록 Tab·Shift+Tab, 주소→검색, 정렬 메뉴 Escape 후 복귀·
  Enter 재열기, A 왼쪽 폴더 탭 방향키+Enter 왕복도 정상이다. 사용자 설정·파일 불변.
- 전체 G02/G06 PASS는 아니다. 다음에는 초기부터 연속 키보드 순회와 네 영역 전체의
  포커스만 확인한다. 도구 focused_element 값은 화면과 불일치하므로 단독 판정 금지.
  입력 간섭·가림이 있던 시도는 제외했다. 이미 확인한 행렬이나 빌드는 반복하지 않는다.
- 제품 코드·새 빌드 없음. 전체 시각 수용과 기존 간헐적 종료 위험은 별도 보존한다.

## 2026-10-20 G01 후속 진단 — 종료 잔류 재현 안 됨

- 최신 main `08e066a1`, 기존 EXE `eb89f47d...`와 같은 소유 v4 세션을 재사용했다.
  UIA 텍스트만 확인한 복원 실행과 화면 캡처·두 번째 탭 전환을 추가한 실행이
  모두 exit 0, 원본 사용자 설정 불변이었다. 새 빌드·제품 수정·전체 GUI 실행 없음.
- 이전 종료 잔류 원인은 미확정이다. 해결 완료나 G01 전체 PASS로 바꾸지 않는다.
  동일 조건 반복 대신 실제 재발 시 소유 PID의 네이티브 호출 스택을 확보한다.
  현재 남은 테스트 앱은 없다. 추측한 강제 종료 코드를 추가하지 않는다.
- 다음 별도 기능 과제는 G02/G06의 좁은 키보드·UIA 점검이다.

## 2026-10-20 G01 최신 재개 결과 — 정상 종료 게이트 보류

- `4bdde290` 로컬 Release 한 번 빌드 후 실제 소유 GUI에서 폴더 탭 추가·전환·
  닫기, 좌우/WindowTab 독립 정렬, v4 저장·재시작 후 두 탭 정렬 복원을 확인했다.
- 최초 실행 exit 0. 복원 실행은 창이 닫힌 뒤에도 60초 이상 프로세스가 남았다.
  대기 체인은 `csrss.exe` 방향 ALPC wait이며 cycle은 보고되지 않았다.
  소유 PID만 정리한 최종 exit는 -1. 사용자 설정·합성 파일은 불변이다.
- G01 최종 GUI PASS로 승격하지 않는다. 다음 작업은 저장 세션 복원 후 종료의
  OS/앱 생명주기 경계를 좁히는 것이다. 이미 확인한 정렬 시나리오와 전체 GUI를
  반복하거나 근거 없이 Application.Exit/강제 종료를 제품 해결책으로 넣지 않는다.
- 제품 변경 없음. 정확한 EXE/범위/한계는 CURRENT_STATUS.md 최신 G01 절 및
  ignored `logs/g01-local-20261020/result.json`에 기록했다. 구버전 세션 실측은 별도 미검증.

## 2026-10-20 최신 사용자 관찰 — 이후 재개 시 우선 적용

- 사용자가 직접 열 경계에 마우스를 올렸을 때 조절 커서가 정상 표시됨을
  보고했다. 아래 자동 입력 실패를 제품 전체의 커서 미동작으로 일반화하지 않는다.
- 사용자 관찰의 정확한 바이너리·열/패널·환경은 기록되지 않았다. 사용자 실측
  근거와 기존 exact-SHA 자동 실패를 함께 보존하며 전체 L08 PASS로 확대하지 않는다.
- 커서 제품 수정은 중단한다. 자동 입력과 실제 입력의 차이를 먼저 분류하고,
  이미 실패한 후보를 다시 빌드하거나 엄격한 커서 assertion을 약화하지 않는다.
- 이번 로컬 재개에서 추가했던 이벤트 대상 임시 진단은 소스에서 제거했다.
  그 진단을 위한 로컬 빌드 출력은 제품 수용/배포 증거로 사용하지 않는다.
- 다음 제품 작업은 이미 구현된 G01 및 G02/G06의 남은 GUI 수용을 마무리하는
  순서다. 아래 원격 요청 슬롯의 복원/승인 경계와 사용자 제외 조건을 유지한다.

## 기준과 사용자 범위

- G01 제품 변경은 [`5c5298a3`](https://github.com/tngkrwlsmd/flyExplorer/commit/5c5298a3e126542b0118c5a670ac982cd5ed1718)에 반영됐다.
  L08 커서 검증의 당시 제품 코드는 `099cfb7125f9`였다. 재개할 때 최신 `main`,
  최근 10개 커밋, 중앙 CI 및 `CURRENT_STATUS.md`를 다시 확인한다.
- 작업 순서: **1) L08 커서/드래그 검증 → 2) G01 정렬 상태 독립화
  → 3) 일상 파일 사용성 개선**. 완료되지 않은 앞 단계를 PASS로 처리하거나
  다음 단계의 코드를 섞지 않는다.
- 실 OS 125/150/200% DPI, F04/F05 High Contrast/Narrator 음성,
  실제 USB/SMB/UNC 시험은 **USER-EXCLUDED**. 실행·권유·출시 차단 금지.
  사용자의 기존 앱·설정·파일을 건드리지 않는다. PR 생성 금지.

## 1. L08 진행: Build PASS, GUI/커서 FAIL

- **2026-10-19 후속 실제 GUI 결과:** 중앙 Windows
  [#39247119043](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39247119043)에서
  소유 앱의 UIA hit 대상은 `LeftNameColumnResizeThumb` (`Group`)였지만
  실제 커서 `65539`는 기본 arrow `65539`였으며 좌우 조절용 커서 `65553`와 달랐다.
  GUI assertion은 **FAIL**이다. 실행 래퍼가 `gui-pass/exit_code=0`을
  잘못 기록했지만 Python traceback과 필수 마커 누락으로 이를 거부했다.
- **후속 격리 후보:** 기존 앱을 중단하거나 소스 `main`을 수정하지 않고
  `MainWindow.xaml.cpp/.h` 두 파일의 `WM_SETCURSOR` 보정 후보를 별도
  Windows 테스트 작업공간에 적용했다. 중앙
  [#39248666199](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39248666199)에서
  source-contract와 Release 빌드는 **PASS**, GUI는 동일한 기본 arrow 커서로
  **FAIL**이었다. 이 후보를 제품 코드에 도입하지 않는다.
- **검증 도구 정비:** `ffd9027c`에서 L08 Python GUI 예외를 명시적으로
  `OWNED_DETAIL_COLUMN_RESULT FAIL`로 출력하도록 변경했다.
  `3b308357`에서 `python tools/winui/run_checks.py gui --area column-resize
  --configuration Release` 집중 경로를 추가했고, `81cab8b6`에서 관련
  소스 계약을 보강했다. 이후 `ed68a40a`와 `1f7ad3ca`에서는
  전용 실행 결과에 정상 종료 코드가 있더라도 명시적 PASS, 세 열의
  실제 변경 마커, 원본 설정 불변 마커가 모두 존재하고 traceback/FAIL이
  없어야만 통과시키도록 강화했다. 이 변경은 테스트 실행기의 안전 판정
  개선이지 커서 문제 해결은 아니다. 기존 엄격한 커서 assertion과 세 열 드래그,
  기존 사용자 설정 불변 조건은 그대로다. **이 새 경로의 실제 Windows 실행은
  아직 NOT TESTED**다. 전체 GUI 통과로 승격하지 않는다.
- **제어 상태:** 마지막 조회 시 `personal-control-plane`의
  `requests/remote-shell/windows-vm.json`에 완료된 과거 후보 요청이 남아 있었다.
  실행은 모두 종료됐지만 해당 슬롯의 idle 복원 GitHub 쓰기는 안전 검사에서
  차단됐다. 다른 수단으로 우회하거나 그 슬롯을 덮어쓰지 않는다.
  승인된 정상 복원 가능 상태가 확인된 뒤에만 Windows 작업을 재개한다.
  이후의 cursor 수정은 실제 XAML 입력 전달·네이티브 창 경계의 증거가 있을 때만 선택한다.


- **2026-10-19 후속 진단 준비:** [`552fe9c5`](https://github.com/tngkrwlsmd/flyExplorer/commit/552fe9c58787a64aebf3f126a11f933acb50b07d)에서
  `tests/winui/test_owned_column_resize_gui.py`의 엄격한 커서 assertion 직전에
  소유 앱 위치의 UIA hit 정보와 native active/arrow/sizewe 커서 핸들을
  `COLUMN_RESIZE_HOVER_PROBE`로 출력하게 했다. 실패를 성공으로 바꾸거나
  기존 커서 assertion/드래그 조건을 우회하지 않는다.
- 독립 중앙 Windows [#39244437409](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39244437409)는
  정확한 위 `main` SHA의 신선한 clone에서 **Python `py_compile` PASS**
  (`L08_PRECHECK_PYTHON_SYNTAX_PASS`)를 기록했다. GUI를 실행하지 않았고
  **제품 커서 동작/기능 GUI/시각 수용은 여전히 FAIL/NOT TESTED 범위 그대로**다.
  단일 Remote Shell 요청 슬롯은 완료 후 idle로 복원했다.
- [`0d3f5f4`](https://github.com/tngkrwlsmd/flyExplorer/commit/0d3f5f455af7342349f9dca8bda3142af1aef607)는
  hover 대상이 소유 앱 프로세스와 다를 경우 외부 창 제목을 수집하지 않도록
  로그를 제한한다. 이 **최신 테스트 Blob**의 정확한 Windows Python 구문 검사는
  [#39245014398](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39245014398)에서
  `L08_CURRENT_SYNTAX_PASS`를 확인했다. GUI 및 제품 변경은 없음.
  Remote Shell 요청 슬롯은 검증 후 다시 idle로 복원했다.
- 다음 단계는 **허용된 실제 로그인 GUI 경로**에서 새 probe의 UIA hit target과
  실제 cursor 핸들 출력을 확인해, WinUI `ProtectedCursor`가 수평 핸들에
  적용되지 않는 원인이 hit-test 또는 메시지 전달 중 어디에 있는지 먼저
  분류하는 것이다. 승인 차단이 지속되면 우회하지 않는다. 기존 드래그
  경계·실패 검증을 유지하고 원인 확인 전 HWND subclass 등의 변경은 금지한다.

- 새 `main`의 `DetailColumnHandle`과 드래그 코드 자체는 이미 구현됐다.
  정식 테스트 소유 Release 빌드 [#39221721375](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39221721375)
  PASS; EXE `9a9056d94c18d6f662a7b8991f2704d877ae0bee746b9ece6b4e037bbdb9eaf6`.
- 첫 실제 GUI [#39222335628](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39222335628):
  `test_owned_column_resize_gui.py`의 첫 hover 수평 커서 assertion에서
  Python Traceback이 발생했다. 외부 Actions SUCCESS/worker exit=0만 보고
  PASS라고 판단하면 안 된다. 필수 GUI 통과 마커는 없었다.
- [#39223067075](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223067075)
  진단에서 **커서 assertion을 의도적으로 우회한 경우에만** 세 개 열 경계의
  실제 물리 마우스 이동과 너비 증가, `RESIZE_MOVE`를 관찰했다.
  이 실행은 수용 근거가 아니다.
- [#39223454976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223454976):
  호버 위치가 `LeftNameColumnResizeThumb`인 상황에서 커서 `65539`는
  stock IDC_ARROW와 같고 IDC_SIZEWE `65553`와 달랐다.
  **현행 L08 cursor 동작은 수용 실패.**
- 임시 `DetailColumnHandle.cpp` PointerEntered/Moved+Win32 SetCursor 후보는
  헤더 수정 후 격리 Release [#39224349062](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224349062)
  PASS (EXE `df5e964b8e60a064843f9251642711c5c067ca232e5c688b406ec7bcb52b076c`)
  였으나 엄격한 실제 GUI [#39224659050](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224659050)
  에서 같은 cursor assertion **FAIL**. 본 후보는 `flyExplorer/main`에
  푸시하지 않았다. 반복만 하는 빌드·테스트는 금지.
- 표준 WinUI `ProtectedCursor`가 포인터 over 상태에서 적용되는지,
  실제 이벤트 전달·캡처 경계 및 native WM_SETCURSOR 경계를 추가로
  분석하고 최소 수정 후보를 결정한다. 프로세스·시스템 전역 커서나
  복잡한 HWND subclass를 검증 없이 추가하지 않는다.
- 수용 기준: 테스트 소유 앱에서 실제 3개 열의 hover 수평 커서,
  드래그→최종 너비, release, body 이동 시 기본 커서 복귀, 좌우 패널
  영향 범위, 정상 종료·사용자 설정 불변을 기록한다. GUI 판정은
  명시적 통과 마커+오류 출력 부재로 한다. 픽셀 시각 검토는 별도.

## 2. G01 진행: 코드 및 Release PASS, 실제 GUI 수용 대기

- [`5c5298a3`](https://github.com/tngkrwlsmd/flyExplorer/commit/5c5298a3e126542b0118c5a670ac982cd5ed1718)
  에서 WindowTab당 좌우 각 PaneTab의 정렬 스냅샷을 도입했다.
  새 PaneTab 기본 이름 오름차순, 탭 선택/닫기 시 정렬 복원,
  private session schema v4 기록 및 v1~v3 읽기 호환을 구현했다.
  R1 정렬 체크와 기존 F05 그룹 상태를 변경하지 않았다.
- 7개 패치 Git Blob의 동일성을 격리 Windows 소스에서 확인한 뒤,
  `test_session_coordinator_contract.py`와 GUI 스크립트 문법 검사,
  정식 Release 빌드를 [#39230031402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39230031402)
  에서 PASS했다. 바이너리 해시
  `368cc3c2b74f17845ec06e4db3cfc31687040eef78f878c8faba6b7b32df6fa1`.
- GUI 시험의 Windows 실행 승인 단계가 안전 제어로 **차단됐다**.
  다른 경로로 우회하지 않았고, **실제 GUI·시각·세션 복원은 NOT TESTED**다.
  승인 가능한 정식 수용 경로가 명확해지기 전까지 PASS로 승격하지 않는다.
- 해당 변경의 상세 원인·테스트 범위는 최신 `CURRENT_STATUS.md`,
  `NEXT_DEVELOPMENT_GOALS.md`를 따른다.

## 3. 일상 파일 사용성 — G02/G06 소스 개선 반영, GUI 미검증

- 최근 `main`의 F2 파일명 기본 이름 선택(`b1cddbbb`), 선택별 명령
  활성 정책(`81b8bc26`), stale-context 파일 작업 결과 안내
  (`0dfbd31a`)는 **이미 코드에 반영**되어 있다. 이번 재개에서 중복
  변경하지 않았으며 실제 GUI 수용은 별도로 필요하다.
- G02 F6 포커스 결과 분기 `1c768b3` 및 소스 계약 `05266a4` 반영:
  반대 패널 파일 목록의 `Focus()` 실패 시 성공한 것처럼 알리지 않는다.
- G06 접근성 이름 `8480403`, `c290ff6`, 소스 계약 `de2c687`
  반영: 제목 표시줄 작업 공간(WindowTab)과 활성 패널의 폴더 탭
  생성·닫기(PaneTab)를 사용자에게 구별한다. 레이아웃과 단축키 불변.
- 이어서 `1a024da`에서 좌우 PaneTab **항목별** UIA 이름,
  `d19c359`에서 활성 패널별 생성·닫기 버튼 이름을 적용했다.
  `e34b95b`, `ea2d08b`에 해당 계약을 추가했다.
- 정확한 소스 `11915f42bd6d85d2001653dba0a2aa30e0141532`로
  새로운 test-owned Windows checkout의 단축키 소스 계약·탭 소스 계약
  및 실제 Release 빌드 [#39239758606](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39239758606)
  **모두 PASS** (`exit=0/0/0`). EXE SHA-256
  `967db8f70dce972274786c177753de1030d10c2908fb1fe6758fcd5f0292943b`.
  범위는 **컴파일과 source 계약**이며 실제 GUI/UIA·시각 픽셀 수용 아님.
  Remote Shell 요청 파일은 검사 후 idle로 복원했다.
- 현재 Desktop Commander 호스트는 offline. 기존 GUI 실행 승인
  차단의 우회는 하지 않았으므로 G02/G06 기능 GUI는 미검증으로 유지한다.
- 추가 키보드 처음-끝 왕복(G02), F2 실제 선택 범위 및 명령 활성·파일
  작업 결과 GUI 검증, L08 커서와 G01 실제 수용은 계속 열린 상태다.
  이전 사용자 제외 항목 3종은 이 작업의 하위 시험으로 다시 등록 금지.



## 통제/증거 정리

- Windows 검사는 중앙 `personal-control-plane`의
  `windows-vm` 전용 Remote Shell을 이용했다. 해당 요청 파일은
  검사 뒤 idle 명령으로 복원했다.
- SYSTEM 전용 테스트 소유 작업 폴더
  `C:\ProgramData\personal-control-plane\central-ci\f67e51c3f71a47e39f02390c3a395013`
  에 후보 바이너리/로그/일부 실패 fixture가 증거로 남아 있을 수 있다.
  이것은 `main` 기준 소스·실행 파일이 아니다. 임의 전체 정리 금지.
  필요 시 소유 마커·정확한 경로·내용을 확인한 뒤 별도 정리한다.
- 이번 재개에서 G01 제품 변경 7개 파일을 `main`에 반영했다. L08 제품
  코드는 변경하지 않았고, 사용자 제외 시험과 신규 PR을 수행하지 않았다.
  중앙 `windows-vm` 요청 파일은 idle 명령으로 복원했다. 성공한 Actions
  run도 내부 Traceback 또는 PASS 마커 누락을 덮어쓰지 못한다.
