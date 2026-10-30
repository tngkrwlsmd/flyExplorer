# 2026-10-30 — Alt+Enter 선택 항목 속성 구현, Windows 검증 대기

## 사용자 가치와 비교 근거

Microsoft 공식 [Windows 바로 가기](https://support.microsoft.com/ko-kr/accessibility/windows/keyboard-shortcuts-in-windows)는 파일 탐색기의 `Alt+Enter`를 선택 항목의 속성 표시로 정의한다. flyExplorer는 안전한 “추가 옵션 표시” 메뉴 안에서 속성을 열 수 있었지만 파일 목록의 직접 단축키가 없었다.

## 구현

- 제품/계약 소스: `c7e8f39f2305685a772d8c94ef1061abfb6c5c34`.
- 파일 목록이 입력을 소유하고 하나 이상 선택됐을 때만 Alt+Enter를 처리한다.
- 기존 `ShowExternalWindowsContextMenu`의 선택·WindowTab·PaneTab·route·visible route·busy/pending 검증과 로컬 고정 디스크/reparse/32개/16K 경계를 그대로 재사용한다.
- 격리된 `FlyShellIsolationHelper.exe`가 Shell의 canonical verb 목록에서 정확히 `properties`만 찾아 직접 실행한다. delete/rename/copy/cut/paste/move 차단과 속성 창 수명 대기는 유지한다.
- 일반 우클릭·Shift+F10의 메뉴 경로는 변경하지 않았다. 세션 v4, 패널별 보기/열, PaneTab별 정렬 및 파일 바이트에는 새 상태나 변경이 없다.

## 현재 검증

- 커밋 diff를 재검토해 변경 파일은 MainWindow 선언/입력 연결, 기존 Shell context core/helper, 관련 계약 테스트 6개뿐임을 확인했다.
- 변경된 Python 계약 테스트는 `py_compile` 문법 PASS. 저장소 전체 파일을 필요로 하는 실제 계약 실행은 아직 하지 않았다.
- 중앙 Windows 읽기 전용 사전 점검 요청 커밋 `656e38a80cb066d8221ee1ddd9008760c12bb88d`에는 workflow run이 생성되지 않았다. VM 명령, checkout, 빌드, GUI는 시작되지 않았다.
- 지연 실행을 막기 위해 슬롯을 `20ca06a59e20ecc9e7f12f788c47135db410d76b`에서 `[skip ci]` idle로 되돌렸다.

## 다음 최소 검증

중앙 실행이 다시 생성되는 다음 실행에서 먼저 VM의 정확한 clean HEAD/기존 runtime/앱0/대화형 desktop을 확인한다. 조건이 맞으면 이 소스의 `test_external_context_contract.py`와 실제 의존 계약만 실행하고, 영향 프로젝트 증분 Release를 빌드한다. 소유 파일과 소유 프로필에서 단일/복수 선택 Alt+Enter 속성 창, Escape 또는 WM_CLOSE 종료, 선택/파일 바이트/설정 보존과 정상 앱 종료를 확인한다. 실제 속성 창 화면은 기능 GUI와 별도로 직접 검토한다.

**Windows Release·GUI·실제 화면 미검증 — 중앙 Remote Shell 실행이 생성되지 않음.** 이전 실행 파일을 새 코드 증거로 사용하지 않으며 main 병합·공개 배포·전역 클립보드·실제 휴지통·외부 전송은 수행하지 않는다.
