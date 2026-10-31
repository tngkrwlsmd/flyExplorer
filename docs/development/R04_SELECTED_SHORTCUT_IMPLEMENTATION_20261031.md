# R04 선택한 파일·폴더의 바로 가기 만들기 — 구현 및 검증 경계 (2026-10-31)

Windows 11 파일 탐색기의 R04 기능 차이 가운데, **선택한 파일·폴더 한 항목의 .lnk 생성**만 구현한 개발 후보입니다. 이것은 빈 배경의 ‘새로 만들기 → 바로 가기’ 대상 선택 마법사와 다릅니다.

- 선택 항목의 앱 우클릭 메뉴 ‘바로 가기 만들기’ → 기존 이름 편집에 기본 '.lnk' 이름 제시 → Enter에서만 파일 생성. Esc는 이름 입력 취소만 수행합니다.
- 현재 작업공간·패널·폴더 탭·경로·선택 항목의 기존 유효성 검사, 파일 작업 확인창 차단, 비동기 파일 작업과 결과 선택 경계를 유지합니다.
- 네이티브 생성은 일반 고정 로컬 드라이브의 재분석 지점 없는 부모와 같은 폴더의 일반 선택 파일/폴더로만 제한합니다. .lnk 확장자/예약 이름·원본 존재를 검사하고, Windows의 IShellLinkW/IPersistFile로 임시 소유 파일에 작성한 뒤 같은 폴더에 덮어쓰기 없이 공개합니다. 실패하면 해당 임시 파일만 삭제 시도합니다.
- 소스 계약과 Windows 네이티브 검사용 fixture를 추가했습니다. 기존 이름 바꾸기·빈 TXT/MD 생성 분기는 유지합니다.

**한정 기능 수용 완료:** 제품 코드와 계약을 `main`에 반영했다(`eebb633a3f1a21343e07743e1de49dbc1c779714`, 기존 계약 범위 조정 `df9b27cc867e457801c3f1d90e825add147a79fb`). [실제 Windows #41184095052](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41184095052): 소스 계약 PASS, M21 native 45/45 PASS(실제 .lnk 원본 경로 확인·동명 파일 보존), 증분 Release PASS, EXE SHA256 `b29061f1ca8d1c01feb0525d1b6f487f74595a8882dd517adabce52a4b09dae1`. [GUI #41184429700](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41184429700)은 Shift+F10 뒤 앱 소유 메뉴 조회 실패로 끝났으므로 FAIL 이력으로 보존한다. 수정된 마우스 직접 우클릭 검사 [#41184675172](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41184675172)는 같은 EXE에서 선택 메뉴→이름 편집→실제 .lnk 생성/목록 표시→원본 바이트·설정 보존→정상 종료·소유 fixture/profile/worker 정리 PASS. Python GUI 테스트는 `cd6f8f307a331c453a67ef87f7240733f14c1a08`. **픽셀 육안 검토 및 전체 Windows 11 동등성은 미실시**. R05도 별도 [#41182673672](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41182673672)에서 GUI 통과했다.

제외: 여러 항목 일괄 생성, 임의 대상 지정/마법사, 네트워크·이동식/가상 폴더, OS 전역 클립보드·휴지통·사용자 파일 테스트, 세션 v4 소유권 변경.
