# R03 — 아주 큰 아이콘 추가 및 v4 보기 호환 (2026-10-31)

## 사용자 가치와 설계
기존 flyExplorer 보기 모드는 Details=0, List=1, SmallIcons=2, MediumIcons=3, LargeIcons=4다. Windows 11 탐색기의 8종과 비교해 부족한 아주 큰 아이콘 모드를 **ExtraLargeIcons=5**로 뒤에 추가했다. 기존 값 0~4나 v4 이진 세션 스키마의 필드 순서/버전, WindowTab→PaneTab 정렬 소유권·패널별 보기/열 너비 규칙은 변경하지 않는다.

상단 보기 메뉴·빈 배경 우클릭 메뉴에서 5를 선택하고, Ctrl+Shift+1 또는 Ctrl+휠 확대 단계에서도 같은 UpdateView 경로를 실행한다. 새 XAML ItemsWrapGrid는 항목 176×196 단위, 실제 행 168×190이며 이미지 표시 목표 112px, 파일 이름 두 줄(폭 152px)이다. Shell 시각 아이콘 요청 상한 64px과 파일 썸네일 상한 128px, 기존 항목별 썸네일 예산·취소/route 제한을 그대로 사용한다. 기존 큰/중간/작은 아이콘·자세히·목록은 다른 모드 번호를 갖지 않는다.

- 제품·검사 SHA: `213f3566809950160118d14ee5737e9c1dd4f62c`.
- 수정: 보기 열거형·패널 XAML/렌더링·기존 FileToolbar/빈 배경 진입점·이미지 스케줄러·폴더 임시 보기·개인 설정 읽기/쓰기·v4 세션 유효성 검사와 관련 소스/소유 GUI 계약.
- 새 v4 값 5의 소스 저장·읽기 규칙은 검사했으나 **앱 종료 후 세션 저장을 직접 복원하는 GUI는 이번에 실행하지 않았다**. 이것을 재시작 동작 전체 수용으로 표시하지 않는다.

## 영향 경계 검증
[Windows #41160263141](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41160263141): 변경한 R03 계약 3/3, 기존 폴더 보기 4/4, 세션 소유 계약 7/7, 설정 계약 4/4 = **관련 소스 18/18 PASS**; 변경 C++ 및 XAML 포함 Release **PASS**. EXE SHA256 `1cd018b35ebd8ffe9915a7ae56fdb613c146b99425e1e7995259fa0b43ad4ec4`; helper SHA256 `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`. IPDB/IOBJ 중간 파일 불일치로 25,676 함수 전체 코드 생성으로 전환했다. 별도 clean/package/전체 GUI는 하지 않았다.

[실제 소유 GUI #41160542458](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41160542458): 파일 3개가 있는 임시 일반 로컬 폴더에서 **왼쪽 Ctrl+Shift+1 아주 큰 아이콘**, 오른쪽 자세히 보기 무변경, 기존 Ctrl+Shift+2 큰 아이콘, 다시 Ctrl+Shift+1을 실제 입력해 각 행 크기와 원본 파일 바이트를 검증했다. 기존 프로필 보존, 정상 종료, 성공 fixture/profile 제거 및 worker 등록 해제를 확인했다. 전체 Windows 탐색기와의 기능 동등성 주장은 하지 않는다.

[실제 화면 #41160630412](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41160630412) 읽기 전용 SUCCESS: Dark/96 DPI/1160×640 PNG 2장 직접 검토. 아주 큰 모드의 2열, 기존 큰 모드의 3열 배치 및 파일명·오른쪽 상세 목록의 유지, 창 안의 행 배치와 새 겹침/잘림 없음 확인. SHA256은 각각 `13759848c20e4078b7d1d487819ed62aa29f12f1c8362c314c7c1de2b575961b` / `68712a04b2c07cd1168501851e63238f9275ed4337c95289a269d19e9047866f`.

## 남은 범위
R03는 8종 전체 중 **6종 구현**이다. 타일/내용 보기, 새 모드의 명시적인 세션 재시작 복원 GUI, 메뉴 포인터 선택의 직접 입력 검증, 다른 DPI/테마/제공자, 파일별 실썸네일 유형, 실제 기본 탐색기와 픽셀 동등성 비교는 미검증이다. 실제 클립보드·휴지통·사용자 파일이나 설정/OS 설정은 조작하지 않았다. 사용자 제외 G03~G05, 중단 G07을 다시 열지 않는다.

완료 후 소유 fixture/profile 정리, source clean, 앱/helper/worker 0 확인; Windows 슬롯은 [skip ci] `ec11df764a677920ea3b6ee05198c60a3b123edc`로 idle 복귀. 다음 R03 하위 항목은 타일 또는 내용 보기 한 종류를 별도 설계·구현하는 것이며, 기존 0~5 모드와 소유/세션 정책을 유지해야 한다.
