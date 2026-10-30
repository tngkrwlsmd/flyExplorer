# 2026-10-30 계속 개발 기록

앞서 사용자는 별도로 멈추라고 지시할 때까지 개발을 이어가도록 요청했다.
현재는 2026-10-30의 후속 지시에 따라 진행 중 작업 정리 후 **일시중지**한다. 재개 지시 전 새 작업/예약 실행을 시작하지 않는다.
야간·06:00 종료 조건은 해제됐다. 이번 실행은 예약 변경만 하지 않고 실제
제품 소스를 변경했다. 사용자의 VM 가동 알림 후 변경 기능의 한정 Windows 검증을 진행하며, 필수 Windows 검증 전 main 병합 금지는 유지한다.
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

## 최신 후속 수용: 61624b66

앞선 '후속 XAML 재빌드/재검토 전' 상태는 이 절로 대체한다. 관련 검사
17/17 후 [증분 Release #40964770658](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40964770658)가 PASS했다.
실행 파일 SHA256은 `1ace409882ae68e353a0897f64001adb1d76937799dc280b30be81acfda841ba`다.
[#40965095829](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40965095829)에서 첫 결과 행이 검색 뷰포트 안에 온전히 들어오는 것을 확인했고 정상 종료·원본 보존·소유 fixture/profile 제거도 통과했다. 동일 실행에서 Windows 인덱스의 직접 자식 포함, 재귀 부모 포함, 얕은 부모 제외 및 잘못된 깊이 인수 거부를 실제 helper로 확인했다.
[#40965276002](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40965276002)의 수정 PNG를 직접 검토했다. 앞선 같은 크기의 결과 밀림이 사라졌고 기존 검색 방식 행 안의 체크박스·문구·양쪽 파일 목록은 겹치지 않는다. **Light/96 DPI/1160x692 한정 시각 수용**이다. 앞선 source ad71a5f6의 성공한 검색/선택/주소 후보 로직과 GUI 증거는 XAML 배치만 바뀌어 재사용한다. Dark·모든 창 크기·전체 제품·실제 Explorer 동등성으로 확대하지 않는다.

기존 야간 일곱 기능의 Windows 입력/실제 생성/클립보드 수용은 남아 있다. 사용자 파일·설정·클립보드·실제 휴지통은 이번 검증에서 변경하지 않았으며 main에 병합하지 않는다.

## Alt+P 새 패널의 포커스 실패: 조사와 수정 후보

#40965819688에서 검색/주소 별칭과 5개 보기 키/메뉴 체크는 실제 통과했지만
Alt+P 뒤 버튼 포커스 관측에서 중단됐다. 정상 종료와 원본 설정 보존은 유지했다.
#40966280100은 ListView 컨테이너 자체가 포커스를 소유해야 한다는 과도한
검사 때문에 실제 Alt+P 전에 중단된 harness 실패다. 이때 제품 결함을 단정하지 않았다.
실제 소유 행 클릭과 UIA focused element로 바꾼 #40966605541에서는 Alt+P가
패널을 열었으나 켜기 버튼은 unfocused였다. 이미 열린 패널에서 Reveal 명령을
실행하자 버튼 포커스가 정상 이동했다. 뒤의 close 판정은 숨겨진 Border가 UIA에서
사라질 때 ElementNotFound를 닫힘으로 처리하지 못한 harness 실패이며 close 제품 실패로 확정하지 않는다.

수정 후보는 Alt+P의 첫 포커스가 실패했을 때만 낮은 우선순위로 1회 다시
기존 Reveal을 호출한다. 약한 UI/focus 참조, 같은 WindowTab/패널/포커스와 열린
상태, 종료/확인창 검사를 통해 새 사용자 입력의 포커스를 빼앗지 않도록 한다.
자동 읽기를 켜거나 반복 타이머/작업자를 추가하지 않는다. 공식 DispatcherQueue
[우선순위 API](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.dispatching.dispatcherqueue.tryenqueue)를 사용한다.
관련 source 25/25와 diff 검사 PASS. 이 새 후보의 Windows 빌드/실제 포커스/픽셀은 아직 검증 전이다.


## Alt+P 후속: 지연 재시도 실패와 동기 배치 완료로 한정 수용

- 지연 재시도 후보 `0a7823d34fd139378e244d0eada7db09923f7706`는
  [증분 Release #40967100455](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40967100455)를 통과했지만,
  [실제 입력 #40967403181](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40967403181)에서 버튼 포커스가 실패했다. 해결로 수용하지 않는다.
- [#40968062339](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968062339)는 양쪽 시작 로딩이 끝난 뒤 실제 행 클릭의 포커스를 확인했다.
  Alt+P 뒤 Alt 누름 중 4회/해제 뒤 4회 모두 오른쪽 폴더 탭에 포커스가 있었고, 이미 열린 Reveal 명령은 버튼을 정상 포커스했다.
  따라서 단순 시작 로딩/Alt 해제만의 문제로 확정하지 않는다. 패널 토글은 소스에서 목록 행을 다시 구성할 수 있다.
- 제품 `2053c6750f606a652d91fa9a320bf0da23c683f2`는 실패한 queued retry를 제거하고,
  토글 직후 한 번 `RootShell().UpdateLayout()`한 다음 기존 포커스 명령을 호출한다.
  [공식 API](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.uielement.updatelayout)의 명시적 배치 완료를
  이 키 명령 한 곳에서만 사용한다. 타이머/새 상태/지연 포커스 작업은 없다. 관련 소스 계약 **17/17 PASS**, diff 검사 PASS.
- [증분 Release #40968263254](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968263254) PASS.
  EXE SHA256 `e0769ea5f70385c0afc8b24a3f5cc735f6e23cd450c2b970599b4bf4089c18d8`.
- [집중 GUI #40968522464](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968522464)에서 실제 Alt+P 열기→켜기 버튼 포커스,
  자동 읽기 OFF/본문 비어 있음, Alt+P 닫기→원래 파일 행 포커스, 재열기 직후 F3 검색 포커스 보존이 PASS했다.
  정상 종료·원본 설정/소유 바이트 보존 및 성공한 fixture/profile 제거도 확인했다.
- [#40968746919](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968746919)에서 이 GUI의 실제 PNG 두 장을 읽어 직접 검토했다.
  앞선 같은 Light/96 DPI/1160x640 창과 비교해 켜기 버튼이 스크롤 안에 온전히 보이고 키보드 포커스 테두리가 명확하며,
  이어지는 F3는 검색 입력에 포커스가 있고 버튼 테두리는 해제됐다. 양쪽 파일 목록과 상세 정보가 겹치지 않는다.
  **Alt+P 변경의 이 조건 한정 기능·시각 수용**이며 전체 제품/다른 테마/실제 Explorer 동등성을 뜻하지 않는다.

## Markdown Windows native 한정 결과

[#40968746919](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968746919)에서 제품 `file_command_core.cpp`와
소유 폴더만 쓰는 작은 native fixture를 MSVC로 컴파일·실행해 **5/5 PASS**했다.
한글·공백 이름의 빈 .md 생성 및 실제 경로, 충돌 시 기존 sentinel 바이트 보존,
대문자 .MD, 잘못된 이름/다른 확장자의 파일 미생성, 기존 텍스트 명령의 .txt 전용 제한을 확인했다.
성공한 native 소유 fixture/컴파일 결과는 같은 실행에서 제거하고 작은 로그/결과만 보존했다.
GUI 메뉴/편집/선택/취소 수용이나 클립보드 검증을 이 native 결과로 대신하지 않는다.

## 남은 동작 GUI의 검사 경계

[#40968622374](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40968622374)는 F11 입력 전에
목록의 일시적 재구성 중 빈 rows를 즉시 인덱싱해 IndexError로 중단한 **harness 실패**다.
정상 종료와 원본 설정 보존은 확인했지만 F11/선택/Markdown은 이 실행에서 PASS가 아니다.
후속은 각 입력 직전 실제 행을 기다리도록 바꾸며 같은 제품 binary를 재사용한다.


[#40976493866](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40976493866)의 수정 harness는
F11 실제 최대화/복원·누른 키 반복 방지와 표시된 두 파일의 선택 반전/해제를 **PASS**했다.
이 성공 단계는 재실행하지 않는다. 이어지는 Markdown 메뉴 UIA Invoke 뒤 이름 입력란 포커스가
확인되지 않아 전체 실행은 **FAIL**이다. 편집 값·물리 클릭·수동 포커스 positive control을
구분하는 후속 진단으로 원인을 좁히며, 아직 자동 이름 편집/GUI 생성/취소 수용으로 확대하지 않는다.


## Markdown 이름 입력: 메뉴 닫힘 뒤 포커스와 최종 일시중지

[#40976728424](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40976728424)에서
실제 메뉴 클릭 뒤 이름 값은 준비됐지만 포커스가 MoreButton에 남았다. 수동으로 입력란을
포커스하면 빈 .md 생성과 정확한 생성 항목 선택은 성공했다. 자동 입력 포커스의 제품 문제로 범위를 좁혔다.

제품 `4206b8f0a2468352978e8aa88e6d6f915e742b1e`는 More 메뉴가 열린 동안 시작한
이름 편집에만 닫힘 후 포커스를 마무리한다. 표식은 즉시 소비하고 취소 때도 제거하며,
현재 포커스가 More 버튼인 경우에만 이동한다. 편집/파일 명령의 소유 경로·탭·세션 정책은 유지한다.
관련 source **13/13 PASS**와 diff 검사 PASS.
[증분 Release #40977193585](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40977193585) PASS,
EXE SHA256 `7af209e944df53ea1f2d30104c9f2555746361e9a0695a0168830e731aab2ff3`.
이전 정확한 runtime은 `logs/parity-20261030-ad71/before-name-focus-runtime`에 해시 대조 후 보존했다.

- [#40977470562](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40977470562): 첫 물리 메뉴 클릭 뒤 입력란 포커스,
  실제 키 타이핑으로 .md 확장자를 남긴 이름 교체, Enter로 0바이트 파일 생성과 UIA의 정확한 항목 선택은 PASS다.
  생성 직후 두 번째 포인터 메뉴의 포커스에서 전체 실행은 FAIL했다. 정상 종료/원본 설정 보존은 확인했다.
  그 실패를 PASS로 바꾸거나 원인을 단정하지 않는다.
- [#40977745029](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40977745029): 독립 실행에서 첫 물리 메뉴 포커스,
  실제 이름 입력 후 Esc 취소·파일 미생성, 키보드 메뉴 재열기 포커스와 두 번째 Esc가 PASS했다.
  정상 종료, 원본 설정/소유 바이트 보존, 성공한 fixture/profile 제거도 PASS다.
  이 결과는 파일 생성 직후 포인터 재열기를 검증한 것이 아니다.
- [#40977840422](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40977840422): 실제 이름 입력/재열기 PNG를
  앞선 같은 Light/96 DPI/1160x640 화면과 직접 비교했다. 선택된 이름 줄기의 파란 강조와 입력 포커스 밑줄이 보이며
  확장자 보존은 실제 타이핑 값으로 확인했다. 표준 입력란 내부의 가로 스크롤/지우기 버튼 외에 도구 모음이나 양쪽 목록의 겹침은 없다.
  **이름 입력 포커스의 이 조건 한정 시각 수용**이다. 생성 직후 PNG는 footer가 불러오는 중이며 이전 목록 프레임이므로
  새 파일 행의 최종 픽셀 수용으로 사용하지 않는다. 이는 두 번째 포인터 검사의 readiness 경계를 좁힐 근거지만 정확한 실패 원인의 확정은 아니다.

사용자의 '지금까지 하던 것만 하고 일시중지' 지시를 적용했다. 개발 예약
`6ae347e8d21c819197a07a08b7eb6e74`는 비활성화했고 새 기능은 착수하지 않았다.
최종 Windows 확인에서 source4206b8f0 clean, 해당 앱 프로세스 0개다. GUI worker task는 각각 finally에서 제거됐다.
[제어 슬롯 idle 정리 커밋](https://github.com/tngkrwlsmd/personal-control-plane/commit/346a8234778c990c098dc004d694b51d2455061a)은
skip-ci로 저장했으며 새 Windows 작업을 예약하지 않는다. 재사용 cache/runtime과 실패 진단 자료는 보존한다.

PR #70은 draft/미병합, main은 `c563a0e004fac25be1c92a4765e31223a9af7c10`다.
재개 후 필요할 때만 생성 완료/탐색 readiness와 두 번째 포인터 메뉴를 구분한다.
빈 배경 메뉴의 실제 이름 편집, 클립보드, 다른 테마/전체 제품/Explorer 동등성은 미검증으로 보존한다.
