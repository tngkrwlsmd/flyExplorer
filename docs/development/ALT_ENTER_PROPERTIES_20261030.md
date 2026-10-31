# Alt+Enter 선택 항목 속성 — 2026-10-31 한정 수용

## 구현과 범위

Windows 기본 탐색기의 Alt+Enter 동작처럼 선택 파일의 속성을 연다. 기존 분리된 Shell 작업자에서 canonical `properties` 명령만 직접 실행한다. 로컬 고정 디스크·같은 폴더·reparse 거부·최대 32개·총 경로 16K와 기존 선택/탭/route/pending 검증을 재사용한다. 세션 v4와 패널별 보기/열, PaneTab별 정렬은 바꾸지 않는다.

- 최초 구현: `c7e8f39f2305685a772d8c94ef1061abfb6c5c34`.
- 후속 `bd523bd0`는 명령을 찾고도 초기 오류 코드 59가 남던 실제 결함을 수정했다. `properties`가 없으면 66으로 거부한다.
- 최종 제품 `30b36f8ac43c73ce76261a83a0ce882eff219508`은 선택된 행의 Alt-only+Enter를 기본 행 입력보다 먼저 직접 처리한다. 일반 Enter와 다른 수정키 조합, 기존 우클릭/Shift+F10 경로는 유지한다.
- 빌드 소스: `4abfa53f190bd05fd5d48fdfc04a14932b4bea8d`. 검사만 수정한 최종 `51e1e69d03a5f1bc3e045c1e631bb48d75996326`까지 제품 변경이 없음을 VM의 app/winui·src/base diff와 실행 파일 해시로 확인했다.
- 실제 클립보드·휴지통·외부 전송, 제외 G03~G05와 중단 G07은 범위 밖이다.

## 현재 검증

| 경계 | 실제 결과 |
| --- | --- |
| 관련 코드 계약 | Work 클라우드 9/9 PASS. 실제 helper 분기를 추출한 C++17 모델을 포함한다. 이전 c7e8f39f의 rc=59 결함도 같은 검사로 재현했다. 변경 Python 문법과 diff 공백 검사 PASS. |
| Windows Release | [#41151817072](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41151817072)의 빌드 단계 PASS. `MainWindow.xaml.cpp` 컴파일. 유지한 캐시로 증분 명령을 실행했지만 IPDB/IOBJ 불일치로 25,600개 함수 전체 코드 생성으로 전환됐다. clean/package 빌드는 하지 않았다. |
| 단일 선택 GUI | [#41152158131](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41152158131)의 첫 단계에서 실제 Alt+Enter, 정확한 helper 속성 창, 창 닫기/helper exit 0/선택 유지 PASS. 뒤 복수 선택 준비 실패 때문에 전체 run의 FAIL은 유지한다. |
| 복수 선택 GUI | [#41152708059](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41152708059)에서 실제 Ctrl+클릭으로 두 파일 선택→Alt+Enter→속성 창→닫기/helper exit 0/선택 유지 PASS. 뒤 주소창의 잘못된 기대값 때문에 전체 run의 FAIL은 유지한다. 단일 성공은 재실행하지 않았다. |
| 주소·수명·정리 | [#41152885137](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41152885137) SUCCESS. 이미 성공한 속성 창 두 사례를 건너뛰고 주소창의 기존 Enter 경로/속성 helper 미생성, 파일 바이트·원래 설정 보존, 정상 종료와 성공 fixture/profile/worker 정리만 확인했다. |
| 실제 화면·기존 소유 바이트 | [#41152943320](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41152943320) SUCCESS. 보존된 두 실제 PNG를 직접 검토했다. Light/96 DPI에서 단일 파일명·21바이트와 복수 파일 2/폴더 0·42바이트, 창 제목·내용·버튼을 확인했다. 두 이전 fixture의 정확한 파일 2개와 바이트를 재확인했고 clean source51e1/앱0/helper0/worker0을 확인했다. |

EXE SHA256: `27a73d6b8a2a24562aa83d4d920d8aeceebccf8837e8915af89b118c80850b04`.
Helper SHA256: `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`.

## 이전 실행과 정정

- 사전 점검 `656e38a8`은 처음에는 미생성으로 기록했지만, 후속 조회로 #41045060061의 읽기 전용 점검 성공을 확인했다. checkout/빌드/GUI 실행은 아니었다.
- 요청 `6bbb4dbf`도 처음에는 미관측이었으나 #41046386664에서 bd523bd0 Release 성공과 GUI helper 미도달 실패가 확인됐다. “실행되지 않았다”는 당시 판단을 정정한다.
- #41087143290은 행 입력 미dispatch를 확인했다. 첫 수정 8dab27b3은 #41087988459의 소스 9개·Release PASS 뒤에도 행 기본 입력 경계가 남았다. 이 두 이전 바이너리를 최종 제품의 증거로 쓰지 않는다.
- #41088699946/#41089322834는 요청의 시작/checkout SHA 혼동으로 제품 검증 전에 종료됐다.
- #41089952101은 처음 대기·만료로 기록했지만 실제 2026-10-31 09:33 KST 로그의 첫 오류는 `prior failure evidence missing`이었다. 기존 실패 경로 목록에 아직 생성하지 않은 새 출력 경로를 넣은 요청 결함이다. 만료 guard가 실제 종료 원인이었다는 판단을 정정한다.
- 복구 점검 [#41151720752](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41151720752)은 clean 8dab27b3, 앱/작업자 0, desktop 1, 이전 실패 경로 존재와 새 출력 경로 부재를 확인했다. 이후 기존 실패 경로와 새 출력 경로를 구분해 최종 빌드 요청을 진행했다.

## 실패 분류와 최종 경계

- #41151817072의 첫 GUI 실패는 목록 재생성 중 없는 행을 is_selected로 읽은 검사 결함이다. Release 성공은 재사용했다.
- #41152158131/#41152355539의 복수 선택 준비는 UIA AddToSelection 뒤 행 포커스를 확인하지 못했다. 첫 번째 행만 요구하던 조건을 선택된 행 중 하나로 바로잡은 뒤에도 관측되지 않아, 이미 검증된 실제 Ctrl+클릭 입력으로 바꿨다. 이를 제품 Alt+Enter 실패로 확정하지 않는다.
- #41152539835는 창 foreground 전환 뒤 행을 재조회하는 지점의 None 클릭으로 종료됐다. 완전한 행 스냅샷을 다시 기다리도록 검사만 수정했다.
- #41152708059의 마지막 실패는 주소창 초안 보존 기대가 기존 제품 동작과 달랐기 때문이다. main c563a0e0와 현재 OnAddressKeyDown 전체 본문이 같고, 수정키 구분 없이 Enter를 경로 제출로 처리함을 소스로 확인했다. 새 초안 보존 기능을 주장하거나 제품 정책을 바꾸지 않았다.

모든 GUI 후속은 위 동일 EXE/helper를 재사용했다. 성공한 새 fixture/profile/worker는 즉시 정리했고, 전체 FAIL이 남은 소유 fixture/profile과 재사용 runtime/cache는 증거로 보존한다. 각 통과 단계와 최종 읽기 전용 확인을 합쳐 **선택된 로컬 .txt 단일/복수 속성 열기의 기능·Light/96 DPI 화면을 한정 수용**한다. 중간 run의 전체 FAIL을 SUCCESS로 바꾸지 않는다. 다른 테마·제공자·모든 개수·전체 제품/Explorer 동등성은 미검증이다. control `711ac2cf7511d88c698fa05755d3ec29e5489792`에서 사용 슬롯을 [skip ci] idle로 복귀했다. PR #70은 draft/미병합이며 main은 c563a0e0다.

PNG SHA256:
- 단일 `b5d6924a21afd0bb4bd7047529295ca4635f3fe97a0e234a42a60f8dc8749516`
- 복수 `f570d135494d8e53fbfae3e2327dee5f54895c3b2367c8815629aeada0887d6c`

이미지/실패 fixture는 VM의 무시된 logs 아래 해당 run별 경로에 보존한다. 실제 속성 창 및 빌드 성공을 다시 실행하지 않고 다음 유용한 미완료 기능 또는 새로운 실제 결함으로 진행한다.
