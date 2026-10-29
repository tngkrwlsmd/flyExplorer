# 2026-10-29 — 충돌 확인창 중 F6 패널 전환 우회 수정

## 실제 문제와 최소 수정

확인창이 열린 동안 파일 작업 버튼은 차단됐지만, RootShell의 공통 키 처리는 계속 실행됐다. 실제 F6 입력으로 확인창 뒤의 활성 패널이 Left에서 Right로 바뀌었다. 파일 변경은 없었지만 사용자가 확인 중인 작업 문맥을 움직이는 우회 경로였다.

`MainWindow.xaml.cpp`의 RootShell PreviewKeyDown 맨 앞에서 파일 작업의 확인 token이 남아 있으면 앱 공통 단축키 처리를 중단한다. 이벤트를 handled로 소비하지 않아 확인창 자체의 Enter/Escape/Tab 처리를 보존한다. 4줄 수정이며 Controller·파일 엔진·세션 형식은 변경하지 않았다. source상 공통 키의 새 진입을 막으며, 실제 GUI 수용은 아래 F6/Escape 범위로 한정한다.

## 정확한 소스와 실행 파일

- 시작 main: `18ffecc75840b89e42e1f9ef7b86f82fc14f8379`.
- 이전 EXE SHA256: `bf2de6ba515c072cf30bb075052e7380b0a74479bd2d5dc23b42f348492929a2`.
- 수정 제품: 위 main + `app/winui/MainWindow.xaml.cpp` blob `600c69c7b74a5ab43822d21722e369873b09f307`.
- 이후 EXE SHA256: `0d8fa7d377ac6a13aefa043a0abb39c1ce320fe27f82a3b786c2ce6a94ef9bd4`.
- helper 유지: `88017a2c25ed70a7cd0a615aa75f2a7a3632bb9f4085fb82089b718454c744fd`.
- 관련 명령/탐색 source 계약 **18/18 PASS**. 같은 제품의 이전 전체 계약이나 GUI를 다시 실행하지 않았다.

## 실제 GUI와 화면

[변경 전 진단 #40867279736](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40867279736): Light, 1160×640, 96 DPI. 테스트 소유 Left/Right 각각 OwnedModal.txt 1개에서 내부 Copy 충돌 확인창을 열고 F6를 입력했다. 주소가 Left→Right, 활성 패널의 파란 표시도 오른쪽으로 이동했다. 확인창은 계속 표시됐으며 파일 바이트와 기존 설정은 보존, 종료 0이었다.

이 job은 취소 후 Copy 버튼이 항상 활성이라는 잘못된 시험 조건 때문에 **FAIL**이다. F6가 활성 패널을 바꾼 상태에서는 선택에 따라 Copy 비활성이 정상일 수 있으므로 이 조건으로 새 취소 장애를 판정하지 않는다. F6 우회 관측과 원본 PNG는 유효한 앞 단계 증거로 보존한다. 후속 시험은 확인창 닫힘/Up 복구를 확인하고, 왼쪽 목록으로 포커스를 되돌려 비모달 F6를 확인한다.

[수정 후 #40867842183](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40867842183): **Release + 집중 GUI PASS, job SUCCESS**.

- canonical Release build exit 0, 101.390초. 기존 산출물·호환 캐시를 재사용했으나 LTCG IPDB/IOBJ 불일치로 25,356 함수 전체 컴파일 fallback. clean/package는 실행하지 않았다.
- 확인창 중 F6: 주소 Left→Left, 확인창 유지, 활성 패널 이동 없음.
- 실제 Escape: 확인창 닫힘. 이후 같은 키 입력 경로의 F6: Left→Right 정상 전환. 차단이 키 입력 실패 때문이 아님을 확인했다.
- 앱 정상 종료 0, 원래 설정 6개 존재/hash 보존, 소유 두 파일 이름·바이트 보존. 새 fixture/profile 제거, 실패한 이전 fixture/profile도 non-reparse·소유 경로·정확한 파일 이름/바이트 확인 후 제거했다. 현재 runtime/cache는 보존했다.
- 변경 전/후 각각 F6 입력 전후의 실제 소유 HWND PNG, 총 4장을 직접 검토했다. 변경 전 오른쪽으로 이동했던 주소·활성 표시가 변경 후 왼쪽에 유지되고, 대화상자 문구·버튼·양쪽 목록 배치가 보존됐다. 이후 두 PNG는 동일 hash다. **이 유한 GUI와 Light 픽셀 검토 PASS**.

| PNG | SHA256 |
| --- | --- |
| before-f6 / 입력 전 | 498a67866880c45c94f87478022bccd65cf30d214247b030945693e15d87bb61 |
| before-f6 / 입력 후 | 795dcd5729f723251824cab4c0fa01b019da032d0d5b00609e58bd91a012246a |
| after-f6 / 입력 전 | e02f78fd9210c1c85ee5d556a6f75942c3c33515b8ee431c9dadaa98650b0a4a |
| after-f6 / 입력 후 | e02f78fd9210c1c85ee5d556a6f75942c3c33515b8ee431c9dadaa98650b0a4a |

전역 클립보드·휴지통·사용자 파일·외부 전송은 사용하지 않았다. Copy를 확정하지 않고 취소만 했다. 별도 Dark/모든 단축키/모든 메뉴/backend 직접 진입 수용으로 확대하지 않는다. 기존 Dark 충돌 수용은 재사용하며 새 Dark 실행으로 주장하지 않는다. EP01의 진행 중 폴더 탐색 상태와도 별개다.

## 사용자가 지정한 나머지 조건부 항목

| 항목 | 이번 판정 |
| --- | --- |
| 충돌창 중 다른 작업 진입 | 실제 F6 우회를 발견해 수정·한정 수용. 다른 미관측 메뉴/직접 호출은 소스 증거 한정 |
| 추가 성능 개선 | 기존 필터 정렬 실측을 재사용. 이번 키 처리 결함과 별개의 새 제품 병목은 확정하지 않아 목록 코드를 수정하거나 8k 계측을 반복하지 않음 |
| 탭별 보기·열 너비 저장 | 기존 PX11 제안 검토. 현행 v4 혼합 소유 유지; 새 저장 정책/마이그레이션 채택 없음 |
| 새 항목 템플릿·Windows 공유 | 기존 폴더·빈 .txt 메뉴는 수용 완료. 다음 구체적 권고 후보는 기존 엔진으로 빈 Markdown(.md) 생성 메뉴 한 가지. 아직 제안이며 미채택·미구현. Windows 공유와 동시에 추가하지 않음 |

다음 작업은 남은 실제 증상/검증 경계 또는 구체적 기능 채택을 기준으로 선정한다. 통과한 F6/충돌/성능/빈 결과 조합을 늘리지 않는다. 제외 G03~G05·중단 G07, 듀얼 패널·두 수준 탭과 v4 정책을 유지한다.
