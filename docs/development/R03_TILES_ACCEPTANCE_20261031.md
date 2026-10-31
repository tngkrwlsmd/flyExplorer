# R03 — 타일 보기 7번째 모드 한정 Windows 수용 (2026-10-31)

## 구현과 기존 계약
- 기준 제품은 기존 6종(Detailed=0, List=1, Small=2, Medium=3, Large=4, ExtraLarge=5)을 유지하고 `FileViewMode::Tiles=6`을 추가했다. 사용자가 타일 모드에서 보는 것은 48px 파일 아이콘과 오른쪽 파일명·유형·크기다. XAML 포장 타일은 264×84, 실제 파일 행은 256×80이며 텍스트 폭 176을 사용한다.
- 상단 보기 메뉴·파일 목록 빈 배경 보기 메뉴·Ctrl+Shift+7은 기존 `UpdateView` 소유 경로를 호출한다. Ctrl+휠의 아이콘 크기 순서 0~5는 변경하지 않았다. WindowTab 안 좌우 패널별 보기·열 너비와 PaneTab별 정렬, 폴더별 세션 내 기억, v4 저장 형식·필드 순서를 보존하고 새 허용 값 6만 추가했다.
- 실제 C++/XAML과 계약 검사 15개 파일은 `16908b4554f81703c0400c61453d2d7d3f29e77e`에서 빌드·테스트했다. 이전 main은 보류 상태 문서만 추가한 `f8589173abc33fcf2a68bd6f900cf4f275686d99`였다. 후보의 **15개 파일 Git blob SHA를 그대로 사용**해 일반 비강제 업데이트 `1cc598b600192bc9fdc1dd2ebc6e54b6fec9327f`로 main에 통합했으므로 기존 문서/사용자 변경과 수용된 0~5 동작은 덮지 않았다.

## 실제 Windows 소스 및 증분 Release
- 최초 [#41161710785](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41161710785)는 신규 타일 계약 3/3 PASS 뒤 구 ExtraLarge 정확 문자열 검증 2건에서 FAIL했고 Release는 시작하지 못했다. 검사만 수정한 `16908b45…` 이후 승인된 `scripts/tasks` 작업으로 변경 부분만 검증했다.
- [#41162326981](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41162326981): Tiles 3/3, 기존 ExtraLarge 3/3, 폴더 보기 4/4, 세션 7/7, 개인 설정 4/4 = **총 21/21 PASS**; Windows Release **PASS**. EXE SHA256 `8c86a402158af7eb80854bc8c1681625549a566810e291b7056039677255c306`. 증분 명령이 유효 IPDB/IOBJ 부재로 25,697개 함수 코드 생성으로 전환됐음을 기록하며 clean/package/전반적 GUI는 실행하지 않았다.

## 소유 Windows GUI 및 실제 화면
- [#41162627911](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41162627911): 동일 EXE/정확한 후보 소스로 테스트 소유 로컬 `.txt`·`.md`·`.log` 3개 파일에서 왼쪽 Ctrl+Shift+7 타일, 오른쪽 자세히 보기 유지, Ctrl+Shift+6 기존 자세히 복원, 타일 재선택 **PASS**. 원본 파일 바이트, 원래 프로필 설정 보존, 정상 종료, 성공 fixture/profile/worker 제거 및 source clean/앱 프로세스 없음 확인.
- [#41162756780](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41162756780): 앱 종료 후 생성한 **Dark/96 DPI/1160×640** 소유 PNG 2장만 읽기 전용으로 가져와 직접 검토했다. 왼쪽 타일에 `tile-alpha.txt` 16 B, `tile-beta.md` 15 B, `tile-gamma.log` 16 B 및 파일명·유형이 보였다. 오른쪽 자세히 목록과 경계가 유지됐고 관측 화면에 새 겹침·잘림은 없다. 첫 PNG의 잠깐 열린 폴더 툴팁은 두 번째에서 사라진 상태다. 유형명은 비동기 등록 정보 해석에 따라 기본 확장자 문구와 Shell 명칭이 다를 수 있어 완전한 표시 동등성으로 단정하지 않는다.
- PNG SHA256: 최초 `21be8b4ffb1fb28ce07f8ad10294e3e8af394f29c27594e844ee72be61917cf1`, 타일 재선택 `9ba5f1d213dd5307b9fc7f44499e79bd9fcd7a5f02270c6ee1baaa4145f7ea73`.
- Windows VM 작업 슬롯은 유효 성공 실행 후 `4bb6158eccbb6cc925b250e3ca3edcf9e87127c7` [skip ci] idle로 반환했다. 실패 증거와 재사용 Release/cache는 보존했다.

## 수용 범위와 남은 실제 가치
현재 flyExplorer의 보기 모드는 **7종**이며, R03의 남은 **내용 보기(Content)**는 별도 구현 대상이다. 실제 타일 보기 메뉴 포인터 클릭, 다른 DPI·Light 테마·대용량/네트워크/가상 공급자, 실제 앱 종료 후 v4 타일 복원, 다른 OS 빌드, 기본 탐색기와 픽셀 단위 동등성은 이번에 검사하지 않았다. 사용자가 제외한 G03 고배율, G04 고대비·Narrator, G05 USB/SMB/UNC/매핑 드라이브 및 중단 G07 실제 IME는 그대로 유지한다. 사용자 파일/원래 설정, Windows 전역 클립보드, 실제 휴지통, 외부 전송, 서명·공개 배포는 건드리지 않았다. 과거 PR #70은 통합 완료이며 새 PR을 생성하지 않았다.
