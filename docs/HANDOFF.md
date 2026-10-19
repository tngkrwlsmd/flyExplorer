# flyExplorer 작업 인계 — 2026-10-19 L08 실제 커서 검증

## 기준과 사용자 범위

- 기준 제품 코드: `099cfb7125f98ca57df977861dba2a8bd0c27c77`.
  이후 문서 커밋은 제품 코드 변경이 아니다. 재개할 때 최신 `main`,
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

## 2. G01 결정 (코드 변경 이전)

- **PaneTab별 독립 정렬**을 유지하기로 선택한다. 현재 UI 설계 문서
  `ARCHITECTURE.md`와 `UI_UX_DESIGN_GUIDE.md`의 원칙을 보존한다.
  현재 `fileLists[side].sortMode`는 패널 공유이며 기존 동작이라는
  근거 [#39187495613](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39187495613)
  를 보존한다. **G01 코드 구현/세션 마이그레이션은 미착수.**
- 다음 독립 단위는 탭 정렬 스냅샷 저장·복원, 새 탭 기본값, 탭 닫기,
  WindowTab 전환, 기존 private session 스키마 마이그레이션과 실제
  목록·메뉴 일치 회귀를 다뤄야 한다. 현재 수용된 R1 체크 표시와
  F05 접힘 상태를 훼손하지 않는다.

## 3. 일상 파일 사용성 개선

- G02 키보드 전체 탐색·포커스 복귀, G06 두 수준 탭 범위 안내,
  L09 F2 이름 변경, EP05/EP06 명령 활성화/충돌·취소 피드백은
  1, 2단계 뒤에 개별 변경 단위로 진행한다. **이번 세션에서 새
  구현·수용을 하지 않았다.**
- 기존 L05 기본 연결 파일 열기, L06 우클릭 다중 선택 보존,
  L07 긴 이름 말줄임은 기존 수용으로 유지한다.

## 통제/증거 정리

- Windows 검사는 중앙 `personal-control-plane`의
  `windows-vm` 전용 Remote Shell을 이용했다. 해당 요청 파일은
  검사 뒤 idle 명령으로 복원했다.
- SYSTEM 전용 테스트 소유 작업 폴더
  `C:\ProgramData\personal-control-plane\central-ci\f67e51c3f71a47e39f02390c3a395013`
  에 후보 바이너리/로그/일부 실패 fixture가 증거로 남아 있을 수 있다.
  이것은 `main` 기준 소스·실행 파일이 아니다. 임의 전체 정리 금지.
  필요 시 소유 마커·정확한 경로·내용을 확인한 뒤 별도 정리한다.
- 이번 제품 변경 없음, 신규 PR 없음. 성공한 Actions run도 내부
  Traceback 또는 PASS 마커 누락을 덮어쓰지 못한다.
