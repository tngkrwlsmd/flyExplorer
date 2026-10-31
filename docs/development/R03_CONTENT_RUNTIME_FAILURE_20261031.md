# R03 내용 보기(8번째 보기) — 당시 Windows 프로세스 종료 실패 이력 (2026-10-31)

**후속 해결:** 아래는 당시의 실패 분석/보류 근거이며 현재 미완료 상태가 아닙니다. 새 제품 커밋 `00673784a548c43e231a4e39d150a5e869974a36`에서 같은 아이콘 셀을 두 UI 부모에 중복 지정하던 결함을 고쳤습니다. [#41165798408](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41165798408) Release, [#41166008089](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41166008089) 정상 GUI, [#41166133019](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41166133019) Dark 실제 화면 통과. [후속 수용 문서](R03_CONTENT_ACCEPTANCE_20261031.md)를 우선 참조하고 아래 실패 로그·소유 자료를 보존합니다.

## 구현 범위
- 최신 수용 제품 기준: `ebaf8afcc87fcb8396520b2739db9430689a62d8` (7개 보기).
- 제품 `d4a29ced8a1303db16225b2c84ed80214e58c434`: `FileViewMode::Content=7`을 기존 0~6 뒤에 추가하고 `Ctrl+Shift+8`과 상단/빈 배경 메뉴, 가변 폭 파일 행의 32px 아이콘과 파일명, cached 유형·크기·수정 날짜를 연결했다. 새 파일 I/O, 새로운 외부 전송/OS 권한, 세션 버전 변경은 도입하지 않았다. 기존 PaneTab별 정렬·패널별 보기/열 및 v4 세션의 허용 값만 확장한다.
- `312423120c481c1325623d0aa6da8798aee44b10`은 `tests/winui/test_r03_content_gui.py` **한 파일만** 수정한 뒤의 소스다. 첫 GUI 오류에 따라 UIA row 스냅샷 수를 줄이고, 특정 COM 오류만 한정 재시도하며 앱 종료를 구별했다. 제품 C++와 실행 파일은 d4a와 같다.

## 정확한 실행과 실패
1. [Windows Release #41163556405](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41163556405): 24/24 관련 source 계약 PASS, Release PASS. 새 EXE SHA256 `3f57c7b4ada9a8a66f21a3f6d0b095529d090aa7c788a874329898789dd97f8c`, helper `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`. 이전 IPDB/IOBJ 캐시 부적합으로 25,718 함수 컴파일. GUI/픽셀은 이 시점 미실행.
2. [첫 소유 GUI #41163844278](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41163844278): **FAIL**. 왼쪽 `Ctrl+Shift+8` 직후 UIA `ElementFromHandle` 접근에서 `_ctypes.COMError(-2147220991)`. 테스트의 `all_rows`는 동일 UIA ListView를 여러 번 조회하고 있었다. 이는 UIA 실패 지점일 뿐 앱 생존 여부까지는 확인되지 않았다.
3. 검사만 수정한 후속 [GUI #41164155299](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41164155299): **FAIL**. 위 COM 오류에서 프로세스 생존 여부를 점검하자 `owned app exited during UIA provider change`가 나왔다. **앱 프로세스가 내용 보기 전환 중 이미 종료**된 현상은 확인됐지만 첫 원인(예외, 종료 코드, UI 측 위반)은 아직 확보하지 못했다. 테스트 소유자 외 파일·설정의 변화, 화면 배치, 정상 종료, 성공 소유 fixture/profile 정리는 통과로 표시하지 않는다.

## 결정과 정확한 재개 경계
- 제품 종료 가능성을 단순한 자동화 검사 오류로 반복 취급하지 않는다. 실패 GUI 및 그 재시도는 별도 보존 경로 `logs/r03-content-20261031`, `logs/r03-content-uia-snapshot-20261031`과 각각의 worker 자료를 사용했다. 실패 데이터와 Release runtime/cache는 보존한다.
- 실패 원인 확인용 Windows 읽기 전용 작업 스크립트 등록 시도는 작업 도구의 안전 검사에서 차단됐고 실행되지 않았다. 임의 우회·개인 PC·RDC·Codex 커넥터는 사용하지 않는다. Windows VM의 로컬 HEAD, 잔류 프로세스 및 실패 소유 데이터 상태는 마지막 실패 이후 직접 점검하지 못했다.
- [보류 복구 `7d3bc25d2100595872140db30dced6892d89bd70`](https://github.com/tngkrwlsmd/flyExplorer/commit/7d3bc25d2100595872140db30dced6892d89bd70): 수용된 7종 제품 코드로 정상 비강제 main 업데이트. 구현/검사 교정은 Git 이력으로 보존하되 main 정식 기능으로 채택하지 않는다. Windows 제어 요청 파일은 [skip ci] `bcbb0ebe035a476174b3f0a74f56fefe5dec7755` idle. 새 PR/브랜치는 만들지 않았다.
- 다음 실행은 최신 `main`/10커밋/제어 슬롯/Windows 활성 작업을 확인하고 이전 실패 소유 증거·승인된 충돌 없는 진단 수단을 재검토한다. 최초 제품 종료 원인을 설명하는 **실제 소스 변경**이 확인된 경우에만 새로운 Windows 증분 빌드/소유 GUI/픽셀을 검증한다. 기수용 R03 타일·ExtraLarge의 GUI나 전체/클린/포장 빌드를 반복하지 않는다.
- 제외 범위: G03 고배율, G04 고대비/Narrator, G05 USB/SMB/UNC/매핑드라이브, 중단 G07 실제 IME, 전역 클립보드·실제 휴지통·외부 전송·공개 배포/서명. 세션 v4·두 단계 탭·듀얼 패널 소유권은 유지한다.
