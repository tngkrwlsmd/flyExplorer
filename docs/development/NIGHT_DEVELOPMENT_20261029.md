# 2026-10-29 야간 기능 개발

사용자는 Windows 11 기본 탐색기와 현재 구현을 비교해 부족한 기능을 계속
추가·개선하도록 요청했다. 종료 시각은 한국 시간 2026-10-30 06:00이다.
수면 중 VM 종료로 Windows 작업은 수행하지 않는다. 기존 듀얼 패널,
두 단계 탭, 세션 v4와 상태 소유 정책 및 제외된 환경 검사는 유지한다.
이 기록은 이번 야간 변경의 인계이며 기존 수용 증거를 대체하지 않는다.

## 첫 구현: 탐색기 키보드 별칭

- 기준 main: `c563a0e004fac25be1c92a4765e31223a9af7c10`.
- 제품 파일: `app/winui/MainWindow.xaml.cpp`.
- F3은 기존 빠른 검색 입력란에 포커스를 주고 입력값을 선택한다. 검색을
  자동 실행하지 않는다.
- F4와 Alt+D는 기존 주소 편집 동작을 호출한다. 폴더를 자동 탐색하지 않는다.
- Ctrl+R은 기존 F5의 활성 패널 새로고침 경로를 재사용한다.
- 기존 사용자 지정 Ctrl 포커스 단축키는 그대로 유지한다.
- 새 별칭은 파일 충돌 확인 중 작동하지 않는다. 대화상자·메뉴·콤보박스·
  파일명 등 다른 텍스트 편집 중에는 입력을 가로채지 않는다. 주소/검색
  입력란 사이의 포커스 별칭은 허용하고 Ctrl+R은 모든 텍스트 편집에서 제외한다.
- Microsoft 공식 기준: [Windows 바로 가기 키](https://support.microsoft.com/en-us/accessibility/windows/keyboard-shortcuts-in-windows),
  2026-10-29 확인. F3/F4/Alt+D 및 Ctrl+R 동작 설명을 사용했다.

### 실제 실행한 검사

다음 파일을 기존 `tools/winui/run_source_contracts.py`로 함께 실행했다.
**31/31 PASS**, `git diff --check` PASS다. 소스 구조 검사이며 실제 입력이나
Windows C++ 컴파일 성공을 증명하지 않는다.

- `test_shortcut_semantics_contract.py`: 새 별칭과 입력 보호 및 기존 단축키.
- `test_command_availability_contract.py`: 충돌 확인 중 입력 소유권.
- `test_window_tab_navigation_chrome_contract.py`: 기존 탐색 상태 경계.
- `test_f06_address_candidate_label_contract.py`: 주소 후보 입력 경계.
- `test_navigation_submit_chrome_contract.py`: 기존 탐색 제출·완료 갱신.

**Windows 빌드·GUI·실제 화면 검증 미수행 — 사용자 수면 중 VM 종료.**
`VISUAL ACCEPTANCE: NOT TESTED`. 검토용 브랜치에 보존하고 main에 병합하지 않는다.
정확한 커밋 SHA는 PR의 head와 커밋 목록을 기준으로 확인한다.

### 아침의 최소 후속 검증

1. 변경한 번역 단위와 의존성만 기존 캐시로 증분 Release 빌드한다.
2. 소유 로컬 fixture에서 F3의 검색 포커스/선택, F4·Alt+D의 주소 포커스/선택,
   Ctrl+R의 활성 패널 새로고침과 반대 패널 경로 보존을 확인한다.
3. 파일명 편집·콤보·파일 확인창에서 새 별칭이 입력을 가로채지 않는지 확인한다.
   Alt+F4 등 다른 조합은 별칭으로 처리하지 않아야 한다.
4. 필요한 포커스/선택 화면만 같은 조건으로 전후 비교하고 정상 종료와
   소유 파일·원본 설정 보존을 확인한다. 기존 기능 전체 검증은 반복하지 않는다.

## 다음 실행

최신 main과 열린 PR, 이번 작업 브랜치의 실제 내용을 먼저 대조한다.
이미 이 별칭이 구현됐으면 반복하지 않는다. 다음 후보는 기존 기능으로
연결 가능한 탐색기 기본 조작(선택 항목 속성 키보드 진입, 보기 전환 키보드
조작 등) 중 실제 빠진 한 가지다. 현재 소스에서 지원 여부와 입력/안전 경계를
확인한 뒤 작은 단위로 구현한다. 저장 형식·상태 소유권 변경, 외부 공유,
클라우드 기능이나 임의 성능 검사를 이 후보에 끼워 넣지 않는다.
