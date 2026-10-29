# 2026-10-30 계속 개발 기록

사용자는 별도로 멈추라고 지시할 때까지 개발을 이어가도록 요청했다.
야간·06:00 종료 조건은 해제됐다. 이번 실행은 예약 변경만 하지 않고 실제
제품 소스를 변경했다. VM 금지·필수 Windows 검증 전 main 병합 금지는 유지한다.
기존 일곱 기능은 [야간 기록](NIGHT_DEVELOPMENT_20261029.md)의 증거로 보존한다.

## EP08: 현재 폴더만 또는 하위 폴더 포함 검색

- 시작 main: `c563a0e004fac25be1c92a4765e31223a9af7c10`.
- 시작 PR #70 head: `eea651ecf3ec4d869cdb93f9613c52ccf1f20d23`.
- 검색 패널의 `하위 폴더 포함`은 기본 ON이다. 해제하면 입력한 폴더 바로
  안의 항목만 검색한다. 실행 중/완료 안내에 선택한 범위와 폴더를 표시한다.
- 직접 탐색은 기존 이름/확장자/크기/날짜/내용 조건을 유지하면서 하위 폴더를
  대기열에 넣지 않는다. 바로 안의 폴더 자체는 폴더 검색 결과가 될 수 있다.
- Windows 인덱스는 기존 SCOPE 대신 얕은 DIRECTORY 조건을 사용하고 반환된
  경로도 재검사한다. 보조 프로세스의 마지막 인수 0/1만 허용한다. 이전 인수
  형식은 재귀 동작을 유지하며 응답 형식/버전과 기존 취소·시간·결과 상한은 같다.
- 범위 선택을 검색 조건 일치 검사에 포함해, 실행 중 범위가 바뀌면 이전 결과와
  그 결과의 폴더 이동을 거부한다. 범위는 폴더 경로/검색 방식처럼 이번 검색의
  설정이며 저장된 검색 조건 템플릿과 세션 v4에 추가하지 않는다.

### 비교 근거

2026-10-30 확인한 Microsoft 공식
[탐색기 검색 범위 안내](https://support.microsoft.com/en-us/office/foundations-experiences/find-what-you-need-with-microsoft-search)는
현재 폴더와 하위 폴더 포함 범위를 설명한다.
[Windows Search SCOPE/DIRECTORY](https://learn.microsoft.com/en-us/windows/win32/search/-search-sql-folderdepth)는
깊은/얕은 범위를 구분한다. 이번 구현은 이 공개 계약과 현재 소스의 차이를
근거로 했다. **실제 Windows 11 탐색기를 조작하거나 화면을 대조하지 않았다.**

### 실제 검사

`tools/winui/run_source_contracts.py`로 아래 세 파일을 실행해 **20/20 PASS**다.

- `test_search_scope_contract.py`: 새 범위 UI/엔진/보조 프로세스 연결과 기존 상한.
- `test_search_controller_contract.py`: 기존 검색 컨텍스트/취소/결과 위치/조건 계약.
- `test_indexed_search_contract.py`: 기존 인덱스 격리·요청·크기/날짜 조건 계약.

첫 파일 중 1개는 제품의 순수 `insideScope`, `sameSearchQuery`, `sameContext`
본문을 추출해 g++ C++17, Wall/Wextra/Werror/pedantic으로 컴파일·실행했다.
현재 폴더/하위 폴더, 비슷한 접두사의 다른 폴더, 드라이브 루트, 끝 구분자,
슬래시, 한글 파일명 및 두 모드의 범위 변경 컨텍스트를 확인했다. Windows
ordinal 비교는 ASCII용 shim이며 실제 Windows API나 앱 전체 컴파일이 아니다.
XAML은 XML로 파싱됐고 변경 Python 문법 및 `git diff --check`도 통과했다.

Windows M19 소유 fixture에는 재귀 3개/현재 폴더 2개 및 바로 안의 폴더 반환
사례를 추가했다. 인덱스 native 검사에는 기존 읽기 전용 표본의 부모/자식 범위와
잘못된 깊이 인수 사례를 준비했다. **이 Windows 사례는 실행하지 않았다.**

### 남은 최소 검증

1. 변경 WinUI/검색 코어 및 보조 프로세스만 호환 캐시로 증분 Release 빌드한다.
2. 소유 부모/하위 폴더의 동일 검색어에서 포함 ON/OFF 결과와 폴더 검색을 확인한다.
3. 이미 인덱싱된 읽기 전용 표본에서 DIRECTORY/SCOPE 차이와 잘못된 인수 거부를 확인한다.
   인덱스를 사용할 수 없다면 그대로 보고하며 직접 탐색으로 자동 대체하지 않는다.
4. 검색 중 범위 변경 후 늦은 결과 거부, 결과 폴더 이동 거부 및 재검색 복구를 확인한다.
5. 변경 범위 행/안내의 작은 창 표시와 기존 양쪽 파일 목록, 정상 종료/원본 보존을 확인한다.

**Windows 빌드·실제 파일 검색·GUI·화면·Explorer 실물 대조 미검증.**
`VISUAL ACCEPTANCE: NOT TESTED`. VM 접근·클립보드 조작·main 병합은 하지 않았다.
정확한 최종 커밋은 PR #70의 이번 기능 커밋과 최신 head를 기준으로 확인한다.

## EP08: 검색 결과의 원본 항목 선택

- 시작 head: `7022817b21bb701f31015bf3bfae8d76a1a10fcf`.
- 기존 `선택한 결과의 폴더로 이동`에서 폴더가 열린 뒤 해당 파일/폴더의 실제
  경로를 가진 행을 선택하고 스크롤한다. 새 파일 실행이나 Shell 동기 호출은 없다.
- 생성/이름 변경의 기존 일회성 선택 상태를 재사용한다. 검색 결과에는 정확한
  탐색 요청 ID를 추가하고 route·폴더 탭·대상 폴더와 성공 여부를 함께 확인한다.
- 이미 열린 폴더로의 Open은 Session::accept에서 S_FALSE/NoChange다. 이 경우에도
  이력/스냅샷을 바꾸지 않고 일치하는 결과의 선택만 갱신한다.
- 새 경로 요청, 폴더 탭 변경, WindowTab 전환, 탐색 실패·다른 결과는 요청을
  폐기한다. 생성/이름 변경은 검색의 이전 요청 ID를 물려받지 않는다.
- 파일 작업/충돌 확인 중에는 결과 이동을 시작하지 않는다. 검색 범위나 입력·
  작업공간이 바뀐 결과는 기존 검색 컨텍스트 검사에서 계속 거부한다.
- 기존 표시 정책은 유지한다. 숨김/필터/접힌 그룹/아직 화면에 펼치지 않은
  페이지에 있으면 폴더만 열고 대체 항목을 선택하지 않는다. 자동으로 필터를
  지우거나 숨김을 켜거나 전체 폴더를 추가 탐색하지 않는다.

### 실제 검사

아래 다섯 소스 계약 **46/46 PASS**, diff 공백 검사 PASS다.

- `test_search_reveal_contract.py`
- `test_search_controller_contract.py`
- `test_file_command_feedback_contract.py`
- `test_navigation_submit_chrome_contract.py`
- `test_window_tab_navigation_chrome_contract.py`

새 검사 중 1개는 제품의 실제 FileCommandReveal 구조체 본문을 추출해 호스트
g++ C++17, Wall/Wextra/Werror/pedantic으로 컴파일·실행했다. 성공 후 일회성
준비, clear, 다른 요청/route/탭, 실패·폴더 불일치·빈 대상·없는 요청 거부를
확인했다. 이는 WinUI callback이나 실제 탐색/스크롤 성공을 입증하지 않는다.

검토 중 메타데이터 무효화가 완료 판정과 목록 표시 사이에 실행되는 것을
확인했다. 일반 invalidate에 선택 상태 clear를 넣지 않고, 실제 탐색/탭 전환과
소비 지점에서만 폐기해 성공한 선택 요청이 중간에 사라지지 않도록 했다.

### 남은 최소 검증

1. 변경 WinUI 번역 단위와 상태 헤더의 의존성만 증분 Release 빌드한다.
2. 소유 fixture의 현재 폴더와 다른 하위 폴더 결과를 각각 선택·이동하고,
   정확한 경로 행의 선택/스크롤과 반대 패널 경로 보존을 확인한다.
3. 대기 중 다른 경로/폴더 탭/WindowTab 전환과 실패 경로에서 늦은 선택을 거부한다.
4. 숨김/필터/접힌 그룹/비표시 페이지는 정책을 자동 변경하지 않으며 임의 대체 선택이 없다.
5. 기존 생성·이름 변경 선택은 실제 의존성만 함께 확인하고 변경 선택/포커스의
   필요한 화면 및 정상 종료·원본 보존을 검토한다.

**Windows 빌드·실제 동작·GUI·픽셀·Explorer 실물 비교는 미검증**이다.
VM 금지와 main 병합 금지는 그대로다. 정확한 소스는 이번 PR 커밋을 따른다.

## EP01/F06: 다른 폴더 탭의 캐시를 주소 후보에 활용

- 시작 head: `8b66c104296231fbc65fdbe9eed6197298da77bd`.
- 이전 후보 수집은 열린 탭의 폴더 경로와 활성 폴더 한 곳의 이름 인덱스였다.
  이제 같은 WindowTab 안의 다른 폴더 탭/반대 패널에 이미 불러온 하위 폴더도
  후보로 활용한다. 활성 폴더를 먼저 확인하고 대소문자 중복 제거는 재사용한다.
- 입력 접두사가 캐시의 폴더와 겹치지 않으면 그 캐시를 건너뛴다. `C:\Foo`를
  `C:\Foobar`의 부모로 잘못 판단하지 않도록 경로 구분자 경계를 확인한다.
- 탐색 중인 탭과 단일 패널 모드의 숨겨진 오른쪽 패널은 검사하지 않는다.
  전체 캐시 검사량 2,048개와 표시 후보 8개를 공유해 탭마다 작업량이 늘지 않는다.
- 입력 중 디스크/네트워크/Shell 조회나 새 비동기 작업을 추가하지 않는다.
  실제 폴더 존재/접근 여부는 사용자가 후보를 실행할 때 기존 탐색 경계가 판단한다.
- 후보의 전체 경로 Tag, 꼬리 이름 표시, 키보드 이동/Escape와 성공한 주소만
  커밋하는 기존 동작은 유지한다. 아직 읽지 않은 임의 경로의 자동완성은 아니다.

### 실제 검사

`test_address_cached_tabs_contract.py`, `test_f06_address_candidate_label_contract.py`,
`test_window_tab_navigation_chrome_contract.py`,
`test_navigation_submit_chrome_contract.py`를 함께 실행해 **21/21 PASS**다.

새 검사 중 1개는 실제 제품의 후보 수집 본문을 추출해 가짜 모델과 ASCII
ordinal shim으로 g++ C++17, Wall/Wextra/Werror/pedantic 컴파일·실행했다.
반대 패널/형제 탭에서 후보 찾기, 활성 캐시 우선, 대소문자 중복, pending/split,
2,048개 공유 검사 예산과 8개 후보 상한, 비슷한 접두사의 다른 폴더를 확인했다.
실제 Windows 경로 비교 API·XAML UI·입력 이벤트의 성공을 입증하지 않는다.

### 남은 최소 검증

1. MainWindow 번역 단위와 실제 의존성만 증분 Release 빌드한다.
2. 소유 폴더의 반대 패널/비활성 폴더 탭에만 알려진 하위 폴더가 주소 후보로
   나타나는지 확인한다. 후보의 전체 경로와 실제 이동 결과를 대조한다.
3. pending 탭, split OFF, 중복 후보와 활성 폴더 우선 및 기존 Up/Down/Escape를
   새 동작의 의존성 범위에서만 확인한다. 임의 디스크 전체 자동완성으로 확대하지 않는다.
4. 추가 후보의 좁은 창 표시와 정상 종료/원본 보존을 확인한다.

**Windows 빌드·실제 입력·GUI·픽셀·Explorer 실물 대조는 미검증**이다.
기존 PX12의 수용 범위를 소급 변경하지 않으며 main 병합은 하지 않는다.

## 세 변경의 연결 검토

검색 범위, 결과 항목 선택, 다른 폴더 탭 주소 후보를 함께 적용한 최종 소스에서
위 관련 계약 9개 파일을 한 번에 실행해 **60/60 PASS**다. 여기에는 실제 제품의
순수 로직 본문/상태/후보 수집을 호스트 C++17로 컴파일·실행한 3개 검사가
포함된다. 나머지는 소스 연결/구조 검사다. Windows API는 실제 실행하지 않았다.
변경 Python 문법과 `git diff --check`도 통과했다. 기존 야간 일곱 기능 전체나
전체 제품 수용을 다시 실행·선언한 것이 아니다. Windows/GUI/픽셀 미검증은 유지한다.

## VM 가동 후 한정 검증과 검색 화면 후속 수정

사용자가 VM 가동을 알린 뒤 기존 제어 경로로 실행했다. 상태 확인
#40963601008에서 clean main, 실행 앱 없음, 로그인 화면 1개와 기존 runtime을
확인했다. 기존 runtime은 logs/parity-20261030-ad71/baseline-runtime에 보존했다.

- 소스 `ad71a5f623e76a8a586db62d7199ef02b744aa36`의 증분 Release
  [#40963818178](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40963818178) PASS.
  EXE SHA256 `a8ee38d33876244782d7a91c59268b8181f0cd8a58f1d8e920677d142c95d953`,
  helper `a0c979ae9af50de741137674dd30afaec21e42191677aee6e61a3f34099b0218`.
- 소유 fixture의 이전/이후 실행
  [#40964235043](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40964235043) PASS.
  직접 탐색 재귀 2개/얕은 1개, 다른 폴더 및 같은 폴더의 정확한 항목 선택,
  반대 패널의 캐시 주소 후보와 이동을 관측했다. 이전/이후 정상 종료,
  원본 설정/소유 바이트 보존과 fixture/profile 제거도 확인했다.
- Light/96 DPI/실제 HWND 1160x692의 소유 PNG 5장을
  [#40964418895](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40964418895)에서
  읽어 직접 검토했다. 선택 행과 주소 후보는 확인했지만 별도 범위 행이 검색
  결과를 뷰포트 아래로 더 밀어낸 시각 회귀를 발견했다. **이 화면은 수용하지 않았다.**
- 후속 변경은 체크박스를 기존 검색 방식 행으로 옮기고 설명을 툴팁으로
  제공한다. 추가 세로 행을 없애며 검색 엔진/조건/선택 로직은 변경하지 않는다.
  관련 검사 17/17 PASS, diff 검사 PASS. **이 후속 XAML은 아직 재빌드/화면 재검토 전**이다.

Windows 인덱스의 실제 DIRECTORY 검색, 이전 야간 일곱 기능의 실제 입력/파일
생성/클립보드, Dark/작은 창 전체 및 실제 Windows Explorer 동등성은 이번 GUI
범위 밖이다. 앞 절의 모든 미검증을 일괄 PASS로 바꾸지 않으며 main에는 병합하지 않는다.
