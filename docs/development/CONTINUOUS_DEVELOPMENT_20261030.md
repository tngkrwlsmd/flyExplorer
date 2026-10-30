# 2026-10-30 계속 개발 기록

앞서 사용자는 별도로 멈추라고 지시할 때까지 개발을 이어가도록 요청했다.
2026-10-30 진행 중 작업 정리 후 일시중지했으며, 후속 사용자 지시로 **개발을 재개**했다. 아래의 일시중지 기록은 당시 이력이다. 매시간 개발 예약을 다시 활성화했으며 최신 물리 메뉴 재열기 결과는 이 문서의 후속 수용 및 [재개 기록](RESUME_20261030_1351.md)을 따른다.
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

## 2026-10-30 재개: Markdown 생성 후 물리 메뉴 재열기

사용자의 일시중지 해제 지시에 따라 최종 제품 `4206b8f0a2468352978e8aa88e6d6f915e742b1e`와
EXE SHA256 `7af209e944df53ea1f2d30104c9f2555746361e9a0695a0168830e731aab2ff3`를 그대로 사용해
남아 있던 생성 직후 포인터 재열기 경계를 좁혔다.

- [#41005850759](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41005850759):
  새 파일 생성 전 단일 메뉴에서 물리 포인터와 키보드 모두 기본 이름·입력 포커스를 안정적으로 준비했다.
- [#41005967857](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41005967857):
  생성 결과와 두 행 투영·명령 준비를 안정화한 뒤 UIA Expand로 하위 메뉴를 연 경우 포인터 선택은 편집을 시작하지 않았고,
  키보드 선택은 정상 작동했다. 제품 성공으로 판정하지 않았다.
- [#41006132284](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41006132284):
  보이는 Markdown 항목과 포인터 중앙의 Text→NewMarkdownFileMenuItem 조상까지 확인했으나 UIA Expand 경로는 같은 실패를 보였다.
- [#41006296625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41006296625):
  실제 사용자 경로처럼 More를 클릭하고 상위 새 항목 메뉴를 물리 마우스로 가리켜 하위 메뉴를 연 뒤 Markdown을 클릭했다.
  첫 생성, 생성 결과 두 행·선택·명령 준비 안정화, 두 번째 같은 물리 메뉴 재열기, 기본 이름과 FileNameBox 포커스,
  이름 줄기 입력, Esc 취소·추가 파일 미생성이 모두 PASS했다. 정상 종료·원본 설정·소유 바이트 보존·fixture/profile 제거도 PASS다.

따라서 생성 직후 **실제 물리 메뉴 재열기 동작은 이 Light/96 DPI/1180×660 소유 fixture 범위에서 수용**한다.
앞선 실패는 UIA Expand로 연 하위 메뉴의 자동화 입력 경계로 분류하며 제품 결함 근거로 사용하지 않는다.
제품 코드는 추가 변경하지 않았다. PNG는 기능 진단용으로 생성했으며 새 파일 행의 별도 픽셀 수용으로 확대하지 않는다.
빈 배경 메뉴 이름 편집, 전역 클립보드, 다른 테마·전체 제품 및 실제 Explorer 동등성은 계속 미검증이다.

Windows 작업 후 앱 프로세스와 성공 fixture/profile·worker task를 정리했고,
[제어 슬롯 idle 커밋](https://github.com/tngkrwlsmd/personal-control-plane/commit/c2163be95a09428881c02ff74acbcf433c66b88c)으로
Remote Shell 요청을 비활성 명령에 복귀시켰다. 개발은 다음 독립 단위에서 이어간다.

## 빈 배경 새 항목 이름 편집 포커스

[#41006512594](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41006512594)에서 소유 fixture의 빈 왼쪽 목록 배경을 실제 우클릭하고
새로 만들기→Markdown을 물리 hover/click한 결과, 기본 이름 값은 준비됐지만 FileNameBox 포커스가 없었다.
0초·0.2초·0.7초 모두 같은 상태였고 Esc도 편집을 닫지 못해 제품 결함으로 확인했다.

제품 `a4333748719316763faccee27542c0365d65f159`는 빈 배경 동적 MenuFlyout에서 시작한 폴더·텍스트·Markdown 이름 편집만
메뉴 Closed 때 한 번 포커스한다. 편집이 유효하고 FileNameBox가 표시·탭 가능하며 도구 모음이 로드된 경우에만 적용하고,
표식은 즉시 소비한다. 파일 명령과 세션/탭/열 소유 정책은 바꾸지 않았다.

- [#41006845613](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41006845613): 소스 계약 **2/2 PASS**, diff 검사와 증분 Release 빌드 PASS.
  EXE SHA256 `7a4e15a1e5da7c614222a1ae13480e0c1712b94dbd0e8dab88f3a18839f83089`.
  뒤 GUI는 harness의 존재하지 않는 `app.exe_hash` 접근으로 제품 입력 전에 중단해 전체 실행은 FAIL로 보존한다.
- [#41007167335](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41007167335): 동일 소스·동일 EXE로 GUI만 재시도했다.
  빈 목록 배경 물리 우클릭, 새로 만들기 물리 hover, Markdown 클릭 후 기본 이름·키보드 포커스,
  이름 줄기 타이핑의 .md 유지, Enter 0바이트 파일 생성과 생성 행 선택이 모두 PASS했다.
  정상 종료·원본 설정/소유 바이트 보존 및 성공 fixture/profile 제거도 PASS다.

이 변경은 **Light/96 DPI/1160×640의 소유 fixture 실제 입력 범위에서 기능 수용**한다.
PNG는 생성했지만 이번 실행에서 직접 픽셀 비교하지 않았으므로 시각 수용은 주장하지 않는다.
다른 테마·전체 제품·실제 Explorer 동등성, 전역 클립보드는 미검증이다.

## 파일 목록 Backspace와 직전 이름 포커스 화면 확인

제품 a6174aee는 Backspace를 파일 목록의 기존 이력 뒤로 가기에 연결했다.
관련 소스34/34, 증분 Release/왼쪽 GUI 단계는 #41008802577에서 통과했지만
왼쪽 전용 보조 함수를 오른쪽 준비에 사용한 전체 FAIL은 보존했다. 테스트만
수정한 후속 #41009193684는 같은 EXE로 오른쪽 이력과 편집 보존·정상 종료·
원본/성공 소유 정리를 확인했다. #41009358308에서 네 실제 PNG와 최종 clean/
앱0/worker 제거를 확인했다. 정확한 소스/해시·재사용 경계는
[Backspace 수용 기록](KEYBOARD_BACKSPACE_20261030.md)을 따른다.

앞 절의 빈 배경 이름 편집 PNG 미검토 상태는 #41008296066의 실제 전후 검토로
이름 입력 포커스의 Light 한정 범위만 갱신했다. 생성 직후 loading 캡처와 다른
테마/전체 제품·Explorer 동등성, 전역 클립보드까지 수용한 것은 아니다.

## EP05/EP06: 파일 목록 Ctrl+D 휴지통 단축키 (2026-10-30)

- 사용자 동작: 활성 파일 목록에서 Ctrl+D → 기존 RunTransfer(Kind::Recycle)의 파일 선택 검증 및 휴지통 이동 확인창. 새 엔진, 전역 클립보드, 세션 v4/PaneTab 소유권, 일반 Delete 동작은 변경하지 않았다.
- 마지막 C++ 제품 변경: 0801c978dd71663780ef0930bacd81f41b4e4ce0 (app/winui/m22_transfers.cpp). 검사용 Alt+D/ Ctrl+D 충돌 주장 수정 0020e4a9bba6840db3112b1feea8c9113217f9dd부터 마지막 GUI 전용 코드 08e5580b1c5cb2ded9711fbdb01f0aa13b5e3773까지 추가 제품 변경은 없다.
- [Windows source/Release #41022673884](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41022673884): 소스 검사 15/15 PASS, Windows Release PASS. IPDB/IOBJ 불일치로 LTCG 전체 함수 재컴파일로 전환된 사실을 보존한다. EXE SHA256 fd65469dc401a3655de012fb1f29b837a8c2feb6c50b66f696594c2945ca04c8 (소스 0020e4a9bba6840db3112b1feea8c9113217f9dd).
- 실패 기록: [#41022545205](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41022545205)는 이전 문서 변경까지 검사해 제품 검사 전에 FAIL. [#41023016364](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41023016364)는 입력 후 확인창 미관측 FAIL. [#41023272560](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41023272560)는 선택 준비 상태에서 FAIL, [#41023381491](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41023381491)는 지원하지 않는 UIA 속성 사용 때문에 FAIL. 이력과 실제 원인을 삭제하거나 제품 결함으로 단정하지 않는다. fixture 선택 안정화와 진단을 수정했다.
- [최종 실제 Windows GUI #41023477151](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41023477151): 동일 EXE 재사용, 테스트 파일 행 포커스 → Ctrl+D → 앱 확인창 PASS; Cancel과 다음 확인창에서 Escape PASS. 테스트 파일 바이트·원래 프로필 보존, 정상 종료, 성공 fixture 정리, 앱 프로세스 0 및 소스 clean PASS.
- 실제 휴지통으로 보내기 승인, 전역 클립보드, 원본 픽셀 직접 비교, Windows 11 Explorer 병렬 비교는 수행하지 않았다. 제외 G03~G05/중단 G07 그대로. PR #70 draft·미병합, main c563a0e004fac25be1c92a4765e31223a9af7c10 유지. Windows VM 제어 슬롯은 dd92bb7325a15ab15559ffb4198d66b40637f270에서 idle로 반환했다.


## EP01: Ctrl+마우스 휠 보기 크기 전환 (2026-10-30)

Microsoft의 Windows 바로 가기 안내에서 파일 탐색기의 Ctrl+마우스 휠은 파일·폴더 아이콘의 크기와 모양을 바꾸는 기본 조작이다. flyExplorer에는 Details/List/Small/Medium/Large의 기존 5단계 보기와 패널별 저장 소유권은 있었지만 이 포인터 입력 연결이 없었다.

- 제품 `6a1c0e59afac7f8cfbc4cced588e20e94969fcf2`에서 양쪽 파일 목록의 PointerWheelChanged를 기존 UpdateView에 연결했다. 정확히 Ctrl만 눌린 경우에만 휠 방향으로 한 단계 이동하고 0~4 범위에서 고정한다. 가리킨 비활성 패널을 활성화하며 Shift/Alt 조합과 일반 휠은 소비하지 않는다.
- 최초 Windows 컴파일에서 생성자 뒤쪽의 nativeWeak를 앞에서 캡처한 선언 순서 결함을 발견했다. 최종 제품 `0c30de4c19edd5f6f839867874e072f207eceac0`은 이 핸들러 전용 약한 참조를 선언해 해결했다. 세션 v4, PaneTab별 정렬, 패널별 보기/열 소유 계약은 바꾸지 않았다.
- 소스 계약 **16/16 PASS**. [Windows 증분 Release·집중 GUI #41038432274](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41038432274) PASS. EXE SHA256 `0dec1fb3a012319311335a5f5abf8aa9cb90e392063f3234f0a9760f25be14b5`.
- 실제 소유 fixture에서 양쪽을 Details로 준비한 뒤 일반 휠이 보기를 바꾸지 않음을 확인했다. 왼쪽 Ctrl+휠은 List, 오른쪽 Ctrl+휠 두 번은 Small icons로 바뀌며 오른쪽이 활성화됐다. 다시 왼쪽을 활성화해도 왼쪽 List가 유지돼 패널별 보존을 확인했다. 정상 종료, 원본 설정·소유 파일 바이트 보존, 성공 fixture/profile/캡처 정리, 앱 프로세스 0, 소스 clean도 PASS다.
- 같은 실행에 보존된 실제 전후 캡처를 직접 검토했다. Light/96 DPI/1160×640에서 왼쪽 List와 오른쪽 Small icons의 배치가 명확하고 패널 경계·파일명·도구 모음의 겹침이나 잘림이 없다. **이 조건 한정 시각 수용**이다.

실패 이력은 보존한다. #41037912837과 #41038064654는 각각 검사 본문 추출 범위와 `::GetKeyState` 토큰의 harness 결함으로 제품 실행 전 중단했다. #41038216768은 소스 16/16 뒤 실제 Release 컴파일에서 위 선언 순서 제품 결함을 찾았고 GUI는 시작하지 않았다. 설명하는 변경 뒤에만 최종 실행했다.

근거는 Microsoft 공식 [Windows 바로 가기 키](https://support.microsoft.com/ko-kr/windows/windows%EC%9D%98-%EB%B0%94%EB%A1%9C-%EA%B0%80%EA%B8%B0-%ED%82%A4-dcc61a57-8ff0-cffe-9796-cb9706c75eec) 안내다. 실제 Windows 11 탐색기를 나란히 자동 조작한 동등성 검사, Dark/다른 DPI·창 크기, 고대비·Narrator 및 전체 제품 수용은 수행하지 않았다.

## Ctrl+1~9 상단 작업공간 번호 선택

제품 a3ab6ce6는 번호 단축키를 기존 WindowTab 활성화에 연결한다. 관련 소스
53/53·AST/diff PASS 뒤 #41040999662에서 Release/소유 GUI를 통과했다.
두 작업공간의 양쪽 경로 복원, 없는 번호/같은 번호 무동작, 주소 편집 보호,
정상 종료·원본 보존/성공 정리를 확인했다. IPDB/IOBJ 불일치로 빌드는 전체 함수
코드 생성에 전환됐으며 캐시를 완전히 재사용했다고 주장하지 않는다.
#41041344251에서 실제 Light 화면 세 장과 최종 clean/앱0/worker 제거를 확인했다.
[정확한 소스·화면·검사 경계](NUMBER_TABS_20261030.md)를 따른다. 상단 작업공간
계층과 폴더 탭 계층은 구분하고 세션 정책은 유지한다. main 병합은 하지 않았다.
