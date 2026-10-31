# R01 — 선택 항목·현재 폴더 속성 메뉴 (2026-10-31)

## 변경과 지원 범위

실제 Windows 탐색기 대조에서 확인한 R01의 직접 속성 진입을 추가했다.

- 선택 항목 메뉴의 **속성**은 기존 Alt+Enter의 격리된 Windows Properties 경로를 사용한다.
- 빈 배경의 **속성**은 선택된 자식 파일 대신 현재 확정된 폴더 하나를 대상으로 한다.
- 메뉴 생성/실행의 WindowTab·PaneTab·폴더·route·pending·파일 작업/확인창 검증을 유지한다.
  현재 폴더 요청은 디렉터리 여부도 재확인한다. 선택 속성의 늦은 응답은 선택 변경 시
  버리며, 폴더 속성 응답은 현재 폴더 상태로 검증하고 자식 선택에는 의존하지 않는다.
- helper의 경로 정규화·같은 부모·최대 32개/총 16K·고정 로컬 디스크·reparse 거부를
  재사용한다. 다른 Shell verb·파일 작업·전송·클립보드를 자동 실행하지 않는다.
- **일반 고정 로컬 폴더 범위**다. 기존 helper의 최소 경로 길이를 유지해 드라이브
  루트의 배경 속성은 비활성화한다. 가상/네트워크/이동식·연결 지점 지원을 확대하지 않았다.
- 듀얼 패널/두 단계 탭·v4 및 정렬/보기/열 소유권은 바꾸지 않았다.

제품 소스 `b10bc7a6c2a0f65b6f6f0c22e86efe4772585102`. 후속 `0f89ce38`과
`03f778de868feaf989b58a69040715b817578803`은 GUI 검사 코드만 변경했다.
검토한 immutable commit을 정확한 SHA로 가져와 검증했고 새 PR이나 검증용 branch는 만들지 않았다.

## 검증과 재사용

| 경계 | 실제 결과 |
| --- | --- |
| 관련 코드 | 외부 메뉴/속성 대상·보호 및 실제 의존 파일 작업 계약 **25/25 PASS**, 변경 Python AST 2/2·diff PASS. Windows 상태 전 범위의 수용은 아니다. |
| Release | [#41156457660](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41156457660) PASS. MainWindow 선언 변경에 따라 관련 WinUI 소스들이 재컴파일됐다. 유지 캐시 증분 명령은 IPDB/IOBJ 불일치로 **25,637개 함수 전체 코드 생성**으로 전환됐다. clean/package는 실행하지 않았다. |
| 선택 파일 메뉴 | [#41156724867](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41156724867)의 선택 단계 PASS. 실제 메뉴의 속성→정확한 r01-item.txt 창→닫기/helper exit0·선택 유지·정상 앱 종료/원래 설정 보존. 뒤 오른쪽 준비 실패 때문에 전체 run은 FAIL로 보존한다. |
| 현재 폴더 메뉴 | [#41157260116](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41157260116) SUCCESS. 처음부터 확정된 SecondMenu 폴더의 빈 배경→속성→정확한 파일 폴더 창→닫기/helper exit0, 경로·바이트/원래 설정 보존·정상 종료·성공 fixture/profile/worker 정리. 앞 선택 파일 성공은 반복하지 않았다. |
| 화면 | [#41157342360](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41157342360)의 실제 PNG4장을 직접 검토했다. Dark/96 DPI/1160×640의 두 앱 메뉴에 속성이 표시되고 잘림/겹침 없이 접근된다. native 파일 시트는 r01-item.txt/28바이트, 폴더 시트는 SecondMenu/29바이트/파일1·폴더0으로 대상이 다름을 확인했다. 이 run의 뒤 바이트 기대값 검사 FAIL은 별도 보존한다. |
| 이전 소유 파일·최종 상태 | [#41157490567](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41157490567) SUCCESS. 앞 기대값은 실제로 원소1개/길이58로 구성됐음을 확인했다. 두 literal base64 기대값으로 이전 fixture의 실제 28/29바이트 보존을 확인했다. source03f778de clean·앱0/helper0/worker0. |

EXE SHA256 `9d7624fa191928e9bcaef1fc1bb93482fa8f1d079f6d9431bd1acb26456a317c`.
Helper SHA256 `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`.
GUI 후속과 화면 읽기는 전부 같은 실행 파일을 사용했으며 재빌드하지 않았다.

## 실패 분류와 한정 수용

- 첫 GUI는 새 현재 폴더 명령 전에 오른쪽 폴더 준비가 완료되지 않았다. 숨겨진 패널
  활성화 Invoke가 실제 키보드 소유까지 보장하지 않는 사전 조건을 소스에서 확인했다.
- 검사만 바꾼 [#41157015441](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41157015441)도
  Right input owner 확인에서 중단됐다. 오른쪽 탐색이나 포커스의 제품 결함/해결을
  확정하지 않는다. 이미 수용된 오른쪽 탐색 전체를 재검사하지 않고 새 폴더 명령
  자체의 최소 시작 폴더 시나리오로 분리했다. 두 전체 FAIL은 유지한다.
- 화면 읽기 run은 네 PNG 출력 뒤 잘못 구성한 PowerShell 바이트 기대값에서 중단됐다.
  GUI/이미지는 재실행하지 않고 literal base64 두 기대값으로 바이트 읽기만 교정했다.

선택 파일·현재 일반 로컬 폴더 메뉴의 위 기능과 실제 화면을 한정 수용한다.
다른 패널/개수·모든 테마·늦은 탐색 전환·드라이브 루트·전체 Explorer 동등성은
이번 새 GUI로 인증하지 않았다. 기존 Alt+Enter/공통 helper 성공은 해당 기록으로 재사용한다.
성공한 소유 자료는 정리하고 실패 fixture/profile/로그 및 재사용 cache/runtime는 보존한다.
정상 사용·변경 검증을 통과한 이 논리 단위를 사용자 지시대로 main에 직접 반영한다.

## 화면 지문

| 화면 | SHA256 |
| --- | --- |
| 선택 메뉴 | c68d60592c654da7bf374bf0f295c93bf168bae1f4e68a41ddd22182248e0fc1 |
| 파일 속성 | a21e021626cbbe9052e79fa1e0abf47916adc9ca2a598531dc0a9b792328de8a |
| 배경 메뉴 | b6aaad8eb509f848d113ba16727d799a625810145fe2f280cc4157bffcdb8ece |
| 폴더 속성 | 0a4e229cead4db141180bb2f7ccfc4f27f08e2da91fe9af01d5d31d2a18ddb2d |

이미지는 VM ignored logs의 r01-properties-menus-20261031 및
r01-properties-menus-folder-only-20261031에 보존하며 Git에는 원시 화면을 넣지 않는다.
