# 2026-10-30 파일 목록 Backspace 뒤로 가기

Windows 탐색기 기본 조작과 현재 구현을 대조해, 파일 목록의 일반 Backspace를
기존 뒤로 가기 명령에 연결했다. 상위 폴더 이동이 아니라 현재 폴더 탭의
방문 이력을 사용한다. Ctrl/Shift/Alt 조합과 텍스트 편집 입력은 대상이 아니다.
파일 확인창 또는 종료 중에는 새 명령을 실행하지 않는다. 탐색 중 요청 거부,
이력 없음, 늦은 결과 처리와 패널 소유권은 기존 OnBackClicked 경로를 재사용한다.

기준 PR head는 `e5e6f2aa939a3ad965bf6ab7c30c8ff53c9e5b3b`다.
Microsoft 공식 [Windows 단축키](https://support.microsoft.com/en-us/accessibility/windows/keyboard-shortcuts-in-windows)의
File Explorer Backspace 동작을 2026-10-30 확인했다. 새 제어 요소나 저장 형식,
파일 조작·클립보드 동작은 추가하지 않는다.

## 현재 검사

- 관련 단축키/탐색/명령 가용성 소스 계약 **34/34 PASS**.
- `git diff --check` PASS, 준비한 소유 GUI 스크립트 Python AST 검사 PASS.
- 이 커밋 시점의 Windows 증분 Release·실제 키 입력은 **검증 대기**다.
  아침의 이전 성공 바이너리를 새 C++ 변경의 증거로 사용하지 않는다.
- 최소 실제 검사는 양쪽 패널에서 서로 이웃인 두 폴더 사이의 이력 복귀,
  반대 패널 보존, 주소·검색·이름 편집에서 글자 삭제 유지와 원본/정상 종료다.
  새 전체 GUI·클린 빌드·포장 검사를 실행하지 않는다.

## 직전 빈 배경 메뉴의 화면 검토 완료

이 기능을 시작하기 전 기존 제품 a4333748의 보존된 전후 PNG를
[41008296066](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41008296066)에서 읽어 직접 검토했다.
Light/96 DPI/1160x640 조건에서 수정 후 이름 줄기의 파란 선택 강조와 포커스
밑줄을 확인했고 도구 모음·양쪽 목록의 새 겹침은 없었다. 긴 이름의 일부는
고정 폭 입력란 내부 스크롤로 처리된다. 이 이름 입력 포커스 범위만 시각 수용한다.

- 이전 PNG SHA256: `0fe3b2f877efa9ea065b398edcb230b37776601c6d078d487b70e0f7c89061dc`.
- 이후 PNG SHA256: `d2b9ca4b0088bd602a0a705b143997d65a313d1ae4d29afe9c53e063bd37a888`.
- 생성 직후 PNG `bd6193b29021628b7b17eb432c7da091566b4a2631d5d04f59469c54dbc3e1ba`는
  불러오는 중인 이전 목록 프레임이므로 생성 행의 최종 픽셀 수용으로 사용하지 않는다.
- 기존 실제 파일 생성·선택·정상 종료/보존·정리는 #41007167335의 한정 증거를 재사용한다.
