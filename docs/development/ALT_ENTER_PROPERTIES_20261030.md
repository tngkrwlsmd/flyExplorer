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


## 2026-10-31 후속 소스 및 Work 클라우드 검사

- 후속 제품/검사 소스 `bd523bd080f471aa9683102883e0ba1d7b47a63a`는 direct-properties가 canonical verb를 찾은 뒤에도 초기 오류 코드 59를 유지하던 실제 결함을 수정했다. direct 분기에 `rc=0`을 먼저 설정하고, properties verb가 없으면 기존처럼 66으로 fail-closed한다.
- 기존 외부 메뉴 계약의 변경된 함수 서명·상태 문구를 현재 소스에 맞췄고, 소유 GUI harness와 실제 helper 분기 본문을 추출하는 모델 계약을 추가했다.
- Work 클라우드에서 `test_properties_verb_dispatch_contract.py`를 실제 g++/C++17로 컴파일·실행해 **1/1 PASS**했다. 대소문자 canonical properties 선택, properties 없음/빈 메뉴 거부, 앞 command 조회 실패 뒤 properties 복구를 확인했다. 두 변경 Python 파일의 `py_compile`도 PASS다.
- 중앙 요청 `6bbb4dbffdb5d5b52d5cfe6d1d8b0a6644591290`은 2026-10-30 11:27 UTC 만료 조건을 지난 뒤에도 workflow run이 생성되지 않았다. 명령·checkout·Windows 소스 검사·Release·GUI는 실행되지 않았다. 슬롯은 `8de43213bf4fc84312da0f6fc8d64bb6830dc7cd`에서 [skip ci] idle로 회수했다.

따라서 현재 판정은 **Work 클라우드 모델 1/1 PASS, Windows Release·GUI·화면 NOT TESTED**다. 다음 실행은 중앙 Actions 생성이 실제 복구됐다는 근거가 있을 때만 동일 소스의 최소 Windows 검증을 제출하며, 이전 요청을 중복 실행하지 않는다.


## 2026-10-31 선택 행 입력 경계 수정과 Windows runner 제한

- 실제 Windows run [#41046386664](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41046386664)는 제품 `bd523bd0`의 Release 빌드와 EXE `a5e7e7c212a8f20cce84b469f1af9eed21426404d98b56e99d237f9b8c37637a` 생성을 완료했지만, 선택 행에 포커스가 있을 때 Alt+Enter가 helper까지 도달하지 않아 GUI는 FAIL이었다.
- [#41087143290](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41087143290)에서 선택 행 입력이 실제 dispatch되지 않음을 확인했다. 첫 수정 `8dab27b3`은 ListView의 bare Enter 가로채기를 제한했지만, [#41087988459](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41087988459)의 소스 9개·Release PASS 뒤에도 행 기본 입력 경계에서 Alt+Enter가 상위 ListView로 전달되지 않았다. 이 실행의 EXE `ca8af2d5ecc1a948cd605204e0e0b9e69778576b1e8ff971be266eb0bcbf26b4`는 최종 소스의 증거가 아니다.
- 최종 제품 `30b36f8ac43c73ce76261a83a0ce882eff219508`는 동적 파일 행이 정확한 Alt-only+Enter를 기존 `ShowExternalWindowsContextMenu(side,true)`에 직접 전달하고, bare Enter와 다른 수정키 조합은 기존 동작을 유지한다. 최종 제품/검사 head는 `4abfa53f190bd05fd5d48fdfc04a14932b4bea8d`이며 Work 클라우드 source 계약·AST 검사는 PASS다.
- 후속 Windows 요청 [#41088699946](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41088699946)과 [#41089322834](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41089322834)은 시작/checkout SHA를 혼동한 request preflight 결함으로 제품 명령 전에 종료됐다. 교정된 [#41089952101](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41089952101)은 Windows runner가 가져가지 못한 채 2026-10-31 01:45 KST 만료 조건을 지났다. 늦게 시작돼도 첫 expiry guard에서 fail-closed하며, 슬롯은 control `48cf602a58e55a6f6f8e9d31782586c31c0a2779`에서 [skip ci] idle로 회수했다.

현재 최종 판정은 **최종 source 계약 PASS / 최종 Windows Release·GUI·실제 화면 NOT TESTED**다. runner 복구 전에는 같은 요청을 다시 만들지 않는다. 다음 실제 검증은 exact `4abfa53f`의 증분 Release, 단일·복수 소유 파일 속성 창, 주소 편집 보호, 정상 종료·바이트/설정 보존과 해당 화면 직접 검토만 수행한다.
