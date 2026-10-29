# 2026-10-29 — EP05, EP01, PX11, PX13 네 순위 개발

## 우선순위 1 — EP05/PX01 명령 모음·컨텍스트 메뉴

상단 파일 명령 활성화가 `mFileOperations.busy()`만 검사하여, 충돌 확인 대화상자가 열려 있고 백그라운드 worker는 idle인 순간 일부 작업을 다시 활성화할 수 있었다. 파일 선택 메뉴의 기존 `pendingConfirmationToken()` 차단과 불일치했다.

- 상단 Create/Rename/Cut/Copy/Paste/Recycle/반대쪽 전송의 공통 `UpdateCommandAvailability()`를 파일 메뉴와 같은 대화상자 경계로 일치시켰다.
- 빈 배경 우클릭 메뉴의 준비/지연 클릭 경계에도 pending collision을 검사한다.
- 실제 파일 전송 `RunTransfer` 진입도 먼저 충돌 확인 진행 중 여부를 검사한다. 사용자 파일을 다루는 진입점의 방어를 GUI 버튼 상태와 별도로 유지한다.
- 보존: 다른 활성 패널·WindowTab/PaneTab·경로/선택 identity/route 검증, Windows 클립보드·휴지통 및 확인 UI 기존 정책. 사용자가 대화상자 응답을 완료하거나 취소하는 동작 자체는 변경하지 않았다.

## 우선순위 2 — EP01 탐색·주소 예외

- 기존 뒤로·앞으로 버튼은 탐색 중 비활성화됐지만 상위 폴더 버튼은 비활성화되지 않았다. 두 개의 UI 갱신 지점 모두 상위 버튼에 같은 `!pending` 조건을 적용했다.
- 버튼을 우회하는 키보드/직접 핸들러까지 뒤로·앞으로·상위 탐색을 `pane.pending`이 있는 동안 거절한다. 이 순간에도 주소 입력을 통한 새로운 명시적 탐색은 기존 요청 대체 정책을 따른다.
- 기존 실패 결과가 committed 경로/목록을 보존하는 ShellCompletion 분기와 PX12 주소 후보·선택은 변경하지 않았다.

## 우선순위 3 — PX11 저장 정책

- **기존 v4 혼합 소유 모델을 유지한다.** PaneTab별 정렬, WindowTab/패널별 보기·열 너비, 해당 v4 세션 상속 및 F14 한정 폴더 보기의 기존 우선순위를 임의로 뒤집지 않는다.
- 사용자가 각 탭의 보기·3개 열 너비를 별도로 저장할 필요성을 승인하지 않은 상태에서 v5 쓰기 형식/이전 버전 비호환 전환은 수행하지 않는다.
- [기존 v5 제안](PX11_TAB_PRESENTATION_PROPOSAL.md)을 구현 후보로 보존한다. 이 순위는 현재 설계 확인 및 보류 판정이고 *신규 기능 구현 완료*가 아니다.

## 우선순위 4 — PX13/G08 대량 폴더의 파일명 필터 + 정렬

- `FillFiles`가 모든 항목을 먼저 `stable_sort`한 뒤 숨김 항목·파일명 필터를 제거하던 구조를 **필터 먼저 → 살아남은 항목만 기존 비교자로 stable_sort**하는 순서로 개선했다.
- 정렬 전 필터 제거는 원래 인덱스 순서를 유지하는 안정적 부분 수열이다. 정렬 비교자/이름·유형·크기·날짜/폴더 우선/메타데이터 결측 규칙 및 논리적 아이템 ID는 변경하지 않아, 남은 항목의 정렬 결과는 동일해야 한다.
- 새 결정적 계약은 이름·유형·크기·날짜 등 8개 정렬 모드에 대해 8,000개 합성 항목의 **정렬 후 필터**와 **필터 후 정렬** 결과 ID를 비교한다. Windows 실제 `CompareStringOrdinal` 콜레이션이나 GUI 실측 타이밍이 아니라 순서 보존의 한정된 모델 검사다.
- 기존 8k Shell-pipe 이름 정렬 수용과 새로운 파일명 필터 정렬을 혼동하지 않으며, 벤치마크 속도 향상을 실측하지 않았다. 20,000/25,000 상한, Shell/provider 처리, 압축 형식/클라우드 기능은 변경하지 않았다.

## 집중 소스 검사 결과

- [Windows VM 소스 계약 #40844041193](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40844041193), 정확한 제품 `7e28366c10a365d9102e54aaf3460282b511b037`: 상단/메뉴 명령 계약 3/3, 탐색 크롬·경계 계약 13/13, 필터-정렬 안정 부분 수열과 8천 합성 항목 2/2로 **18/18 PASS**.
- 위 값은 Python 소스/결정적 모델 계약이다. 실제 C++ 컴파일, UI 행동, 사용자가 관찰하는 체감 성능 또는 시간 개선 증거가 아니다. 기존 Windows 검증 요청 슬롯은 완료 후 idle로 복원했다.

- Additional **26/26 dependent Python contracts PASS** under [central #40844503080](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40844503080): selected/external file context menu 8/8, metadata controller 8/8, large-folder streaming 10/10. Thus combined affected-source checks **44/44 PASS**. A predecessor [#40844372803](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40844372803) stopped before tests because the VM product checkout correctly remained on `7e28366c` while the request erroneously required documentation-only `2271b915`. Do not treat this as product failure or overwrite it with PASS. The corrected job verified exact product source `7e28366c`. No native build, GUI or measured speed gain.

## 검증·수용 경계

대상 변경은 `MainWindow.xaml.cpp`, `m22_transfers.cpp`, 집중 Python 소스 계약 및 이 문서로 한정한다. 현시점에서 **Windows Release 빌드, 실제 GUI, 키보드·메뉴 입력, 처리 속도 실측은 별도 검증 전까지 미검증**이다. 명시적으로 제외된 G03/G04/G05, 중단된 G07은 재개하지 않는다. 향후 집중 확인 시 소유 로컬 fixture에서 충돌 확인 중의 활성화·직접 작업 차단, pending 상태의 상위/뒤로/앞으로와 실패 후 경로 보존, 파일명 필터+복수 정렬의 실제 표시만 검증한다. 이미 수용된 M23 Copy 충돌 *완성 시나리오*나 기존 PX13 8k 이름 정렬은 다시 실행하지 않는다.
