# flyExplorer 작업 인계 — 2026-10-19 L08 커서 OPEN, G01 코드·빌드 PASS

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
