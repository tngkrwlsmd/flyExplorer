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
