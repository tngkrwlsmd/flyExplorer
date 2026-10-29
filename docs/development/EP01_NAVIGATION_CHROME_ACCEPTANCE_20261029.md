# 2026-10-29 — EP01 탐색 시작·완료의 버튼 상태: 한정 수용

## 확인한 원인과 수정

시작 main `d78cdaee42fe751558305d0f31191535342323d4`의 Controller는 요청을 수락하면 Model.markPending을 호출했다. 하지만 MainWindow의 QueuePath/QueuePidl/추가·이전 페이지 요청 시작에서는 UpdateNavigationChrome을 호출하지 않았다. 상태 판정 함수와 완료 갱신은 있어도 시작 갱신이 빠져 이전 Back/Forward/Up 표시가 남을 수 있었다. 앞선 분석에서 이 연결을 놓쳤으며, 미관측 원인을 짧은 전이/도구 지연으로 확정하지 않는다.

활성 패널의 요청이 수락된 직후 버튼을 재계산하고, 추가 페이지 완료가 pending을 해제할 때도 갱신한다. Controller·요청 ID/route·이력 거절·주소 요청 대체·파일 목록/정렬·두 수준 탭·세션 v4는 그대로다. Release 지연 주입이나 제품 진단 코드는 추가하지 않았다.

## 정확한 소스·빌드

- 검증 소스: 위 main + MainWindow.xaml.cpp blob `b2cd9c729879f01cc270d265914a3c2f55cc5d56`.
- 이전 EXE SHA256: `0d8fa7d377ac6a13aefa043a0abb39c1ce320fe27f82a3b786c2ce6a94ef9bd4`.
- 후보 EXE SHA256: `47a8c28286769ed11db582f3513e8b800eab650daa529e65847efd1d6788129b`.
- helper 유지: `88017a2c25ed70a7cd0a615aa75f2a7a3632bb9f4085fb82089b718454c744fd`.
- 새 source 계약 2개는 이전 소스에서 누락을 검출했다. 수정 뒤 기존 navigation chrome/large-folder streaming과 함께 **25/25 로컬 소스 검사 PASS**.
- [Release #40871091665](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40871091665): exit 0, 115.755초. 호환 산출물/캐시를 재사용했으나 LTCG IPDB/IOBJ 불일치로 25,356 함수 전체 컴파일 fallback. clean/package와 GUI 동반 실행은 하지 않았다. 이후 GUI에서 이 EXE를 그대로 재사용했다.
- 이전 runtime 305개 파일 / 123,731,718 bytes를 manifest/hash로 보존해 정확한 전후 실행에 사용했다. 비교 후 해당 소유 복사본만 정리한다.

## 실제 GUI — 진행 중 이력 입력과 새 주소

Windows VM, x64 Release, Light, 1160×640, 96 DPI. 같은 소유 A/B/Big 경로, Big은 entry-00000.txt~entry-07999.txt 8,000개, A/B는 각각 1개다. 파일 이름/바이트는 실행 전후 그대로다. 성능 수치를 재수용하거나 기존 8k 순서 시험을 늘리는 작업이 아니다.

[진행 상태 관측 #40874030229](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40874030229)의 후보 앞 단계에서 Back/Forward/Up을 모두 false로 읽었다. 그 구간에 실제 Alt+Left를 보낸 뒤 Big 경로가 유지됐고, 완료 후 같은 실제 키는 B로 이동했다. 이어 Alt+Right로 Big 복귀도 확인했다. 이 제한된 이력 입력의 억제·완료 후 복구는 유효한 앞 단계 증거다. 즉시 거절 안내 문자열은 UIA에서 관측되지 않았으므로 핸들러 내부 분기 실행 기록으로 주장하지 않는다. 전체 job은 뒤의 주소 시험에서 정렬 popup이 열린 채 입력한 harness 실패로 **FAIL**을 유지한다.

[최종 비교 #40877218273](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40877218273): **before/after/cleanup 3단계 PASS, job SUCCESS**.

- 이전 runtime에서 8k 전체 이름 내림차순 로딩의 원본 HWND 프레임을 6장으로 한정해 캡처했다. 로딩 문구가 보이는데 Back/Up 표시가 활성으로 남는 상태를 직접 확인했다. Forward는 이 장면에서 다음 이력이 없어 원래 비활성이므로 그 전후 차이를 주장하지 않는다.
- 후보는 같은 Big의 전체 정렬 로딩에서 popup을 닫고 파일 목록으로 포커스를 돌린 뒤 관측했다. Back/Forward/Up 세 개가 false였다. 실제 Ctrl+L로 주소 편집에 포커스가 온 것을 확인하고 A를 입력했다. Enter 직전 Up=false를 다시 확인한 `enter_while_pending=true`를 기록했다.
- A 주소/owned-a.txt로 이동하고 Up이 복구됐다. 추가 관측 뒤에도 A를 유지하고 반대쪽 B/owned-b.txt가 그대로였다. `explicit_address_replaced_pending=true`.
- 두 앱 정상 종료 0, 기존 6개 설정의 존재 상태/hash 보존, 각 private profile 제거. 8,002개 소유 파일 이름/바이트를 독립 재확인한 뒤 공유 fixture 제거, 실패 profile 잔존 없음.

이 증거로 **활성 왼쪽 로컬 탐색/페이지 로딩의 세 버튼 표시, 실제 Alt+Left의 대상 보존과 완료 후 정상 동작, 진행 중 새 주소 대체의 유한 GUI 범위를 수용**한다. 진행 중 Alt+Right/Alt+Up 각 키, 모든 페이지 역방향/오른쪽/제공자/장기 경합을 따로 실행한 것은 아니다. 그들을 자동 후속 매트릭스로 만들지 않는다. 실패 주소 보존은 기존 별도 수용을 재사용했다.

## 실제 픽셀 검토

전후 같은 Big·내림차순·오른쪽 B·Light/창 크기/DPI에서 로딩 상태를 직접 비교했다. 이전의 Back/Up 활성 표시가 후보에서 비활성으로 바뀌었고, 양쪽 목록·주소·열·상태 문구 배치는 유지됐다. 메뉴가 닫힌 후보 로딩과 A로 완료된 화면도 검토했다. #40874030229의 후보 이력 로딩 화면은 별도 앞 단계 이미지다. **이 선택된 Light 진행/완료 화면의 픽셀 PASS**이며 Dark/전체 PX15 수용은 아니다.

| 대표 원본 PNG | SHA256 |
| --- | --- |
| #40877218273 이전 정렬 로딩 frame-2 | 8d28757f4d81e54d48607e7b524e25511d8973cdd684319449dcd7577adaaadc |
| 같은 실행 후보 정렬 로딩 | be3b1efbce957510d318c1aeb854fc7afc32e52e2000fad61e03a76490c4c03f |
| 같은 실행 후보 A 완료 | ac63937f05089bce5f19929ac24a36cf5e7372c9ba61f926d832d01df8f1c04f |
| #40874030229 후보 이력 로딩 | 8bc571d5494e3dc6258cfd4eebb12463251f00308855adc92db6f5d331ce22ec |

## 실패 기록과 바뀐 시험 경계

| 실행 | 실제 경계/판정 |
| --- | --- |
| #40870257109 | 입력 desktop 불가, 앱 시작 전 중단. 환경 FAIL. 처음 생성한 fixture는 빌드 작업에서 이름/바이트 확인 후 정리. 이후 입력 preflight를 파일 생성 앞으로 이동 |
| #40871921081 | 사용자 접근 복구 보고 후 입력 가능. 속성 알림 등록 뒤 실제 수신이 없어 이전 단계 중단. 알림 미수신 원인은 확정하지 않음. 제품 변경으로 삼지 않고 알림 의존을 제거 |
| #40873197002 | 이전 앱 오른쪽 초기 목록 준비 조건에서 중단. pending 시험 전이며 새 제품의 실패로 확대하지 않음 |
| #40874030229 | 후보 세 버튼 false/이력 억제·복구는 유효. 이후 정렬 popup 중 주소 입력으로 실패한 harness. 전체 FAIL 유지 |
| #40875986788 | 오른쪽에 B를 연 뒤 왼쪽만 검사하는 App.navigate helper를 재사용한 harness 오류. 해당 단계가 양쪽 버전에서 실패. 오른쪽 주소/RightFiles를 명시적으로 대기하도록 수정 |
| #40877218273 | 정렬 popup 닫힘, 주소 실제 포커스 및 Enter 직전 pending을 확인한 비교·정리 PASS |

모든 시도에서 사용자 PC/RDC/금지 connector·전역 클립보드·휴지통·외부 전송을 사용하지 않았다. G03~G05 제외·G07 중단 유지. 성공 뒤 이 로컬 시나리오를 다른 검사 이름으로 반복하지 않는다. 추가 기능/탭 저장 정책은 별도 채택 대상이다.
