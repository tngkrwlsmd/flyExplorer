# R03 내용 보기 8번째 모드 — 중복 XAML 부모 지정 해결 및 한정 수용 (2026-10-31)

## 사용자 가치와 변경
- Windows 11 기본 탐색기의 보기 8종과 동일한 범주의 **8번째 ‘내용 보기’**를 구현했다. `Ctrl+Shift+8`, 상단 보기 메뉴, 빈 배경 보기 메뉴에서 선택하며 현재 활성 패널만 변경한다. 행에는 32px 시스템 파일 아이콘과 이름/유형/크기/수정 날짜를 기존 bounded Shell 결과만으로 표시한다. 우측 패널의 자세히 보기는 유지된다.
- 기존 0~6(자세히, 목록, 작은/보통/큰/아주 큰 아이콘, 타일)을 재번호화하지 않고 `Content=7`을 추가했다. PaneTab별 정렬, 패널별 보기/열 너비, 두 단계 탭, v4 세션 버전/필드, 사용자 데이터/OS 설정은 그대로다. 컨텐츠 텍스트와 타일 배치는 별도이며 Ctrl+휠은 기존 아이콘 크기 단계 0~5에 남는다.
- 이전 제품 `d4a29ced8a1303db16225b2c84ed80214e58c434`는 Content 렌더링 중 `contentRow.Children().Append(cell)`과 `row.Content(contentRow)` 다음 무조건 `row.Content(cell)`을 재호출했다. 이것은 이미 다른 XAML Grid에 속한 아이콘 셀을 재부모화해 WinUI 런타임 예외·앱 종료를 유발하는 구체적인 결함이었다. 새 소스 `00673784a548c43e231a4e39d150a5e869974a36`에서는 **`if(!contentMode)row.Content(cell)`**로 내용 보기에서만 그 중복 할당을 제외했다. 관련 검사에 조건부 할당을 명시적으로 검증하고, 실패 소유 경로와 새 소유 경로를 분리했다.
- 기존 [실패/보류 근거](R03_CONTENT_RUNTIME_FAILURE_20261031.md)는 편집해 성공으로 바꾸지 않고 당시 자료와 충돌 없이 후속 성공을 연결했다. 신규 브랜치·PR·force-push는 사용하지 않았다.

## 실제 Windows 증거
- 초기 제품은 [Release #41163556405](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41163556405) 소스 24/24·빌드 PASS였으나 [GUI #41163844278](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41163844278) UIA COM 오류와 [#41164155299](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41164155299) 앱 프로세스 종료로 **FAIL**했다. 해당 실패 로그 및 runtime/cache는 보존한다.
- [수정 빌드 #41165798408](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41165798408): 신규 회귀 계약 포함 내용 보기 소스 3/3 PASS, 실제 Windows Release **PASS**. 변경 소스 `00673784a548c43e231a4e39d150a5e869974a36`, EXE SHA256 `c250a8f4611c4306e9010e34e5d5588068d5b2a0c725e126dd5e81a599327337`; helper SHA256 `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`. 증분 빌드가 유지 IPDB/IOBJ 부적합으로 25,718개 함수를 재컴파일. 기존 24개 중 변경되지 않은 세션·타일·아주 큰 아이콘 계약 결과는 이전 수용을 재사용했다. clean, 전체 GUI, package는 하지 않았다.
- [소유 GUI #41166008089](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41166008089): exact EXE로 왼쪽 `Ctrl+Shift+8` 전체 폭 내용 보기, 오른쪽 자세히 보기 유지, `Ctrl+Shift+6` 복귀 및 내용 재선택 PASS. UIA transient retries **0**. 소유 `.txt/.md/.log` 3개 파일 바이트, 기존 앱 설정 보존, 앱 정상 종료, 성공 fixture/profile/worker 제거, source clean, 앱·helper·worker 프로세스 없음 PASS.
- [화면 #41166133019](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41166133019): 종료된 앱의 테스트 소유 PNG `content`, `content-again`을 읽기 전용으로 가져와 직접 비교했다. **Dark·96 DPI·1160×640** 범위에서 좌측 `content-alpha.txt` 18 B, `content-beta.md` 17 B, `content-gamma.log` 18 B의 아이콘/파일명/유형/크기/수정 날짜가 표시되며, 오른쪽 자세히 목록은 유지되고 새 겹침·잘림 미관측. 두 PNG의 SHA256은 모두 `dbff94ea935581f847205612382b0f554020bdad6a446cae9ccc0288a3930e7d`. 캡처 두 장이 같다는 것은 해당 화면의 반복 결과만 뜻한다.
- Windows 제어 슬롯 `0cc2f28ec1e5b6c29572c9b3e6d9906a24e06ac3`을 **[skip ci] idle**로 복귀시켰다. 이전 실패 증거 및 재사용 실행 파일/빌드 캐시는 보존한다.

## 수용하지 않은 범위
실제 Windows 탐색기에서 모든 메타데이터와 동일하게 표시되는지, 바로 메뉴 항목을 마우스로 클릭한 경우, 앱 완전 종료 후 v4 Content 상태 복원, 다른 테마/창 크기/DPI/가상 공급자 등은 검증하지 않았다. 사용자가 제외한 G03 실제 고배율, G04 고대비·Narrator, G05 USB·SMB·UNC·매핑 드라이브 및 중단 G07 실제 IME는 재개하지 않았다. 실제 클립보드 읽기/쓰기, 휴지통, 외부 공유·전송, 공개 배포/서명과 사용자 파일 변경은 수행하지 않았다. 이 문서의 PASS는 **변경 소스와 위 실측 환경에 한정**된다.

## 다음 우선순위
새 기능 후보는 Windows 실제 직접 대조의 R04 ‘바로 가기 만들기’ 또는 R05 ‘현재 폴더에서 터미널 열기’다. 일반 사용자가 실행했을 때 얻는 가치와 기존 Shell 지원 범위를 비교해 하나를 고른다. R03 8종의 통과한 조건을 복제해 검사만 늘리지 않는다.
