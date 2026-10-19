# flyExplorer 작업 인계 — 2026-10-19 L08 커서 OPEN, G01 코드·빌드 PASS

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
