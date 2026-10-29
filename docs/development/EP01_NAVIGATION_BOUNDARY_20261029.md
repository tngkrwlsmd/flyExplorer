# 최신 후속 결과 — 2026-10-29

이 문서의 미관측/pending 서술은 이전 checkpoint다. [소스 갱신 누락 수정과 실제 한정 수용](EP01_NAVIGATION_CHROME_ACCEPTANCE_20261029.md)이 최신이다. source 25/25, Release, 후보 세 버튼/실제 이력 입력 억제·복구, 진행 중 새 주소와 Light 픽셀을 유한 범위에서 확인했다. 아래 과거 실패와 당시 원인 미확정 기록은 보존한다.

# 2026-10-29 — EP01 실제 탐색 검증의 확인 범위와 남은 공백

## 제품과 실행 파일

main `ad86618f1a7d31408014fd10649a216668085e62`, EXE SHA256 `bf2de6ba515c072cf30bb075052e7380b0a74479bd2d5dc23b42f348492929a2`. Back/Forward/Up pending 거절 코드는 제품 `7e28366c`와 같고, 이후 제품 변경은 별도 EP05 취소 복구뿐이다. 이 작업에서 C++를 다시 빌드/수정하지 않았다.

## 실패 원인 분리

[중앙 #40859732626](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40859732626)의 navigation 실패는 변경 전 runtime의 반대쪽 첫 행 문자열이 달라졌다는 assertion이었다. 그 시점에는 실제 예상/관측 행을 저장하지 않아 제품 결함으로 확정할 수 없었다. native와 필터 단계 PASS는 별개로 보존한다.

[집중 진단 #40862156427](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40862156427)은 변경 전/후 모두 확정 주소와 왼쪽 첫 행이 같음을 기록했다. 반대쪽 파일 이름·크기·시각은 그대로이고 `txt 파일`이 늦게 도착한 Windows 등록 유형 `텍스트 문서`로 바뀌었다. **비동기 유형 메타데이터까지 파일 identity와 동일하게 비교한 harness 결함**이다. 파일명/경로 보존 실패나 소스 회귀가 아니다. 두 앱 모두 정상 종료 0, 원래 설정과 소유 바이트 보존. job 자체는 해당 assertion으로 FAIL을 유지한다.

## 미관측 pending 경계 — 미검증으로 유지

동기 UIA 관측을 독립 COM MTA 관측으로 바꾼 #40859732626, 이후 history 요청을 실제 Alt+Right 입력으로 시작하고 단일 Back 상태를 관측한 #40862156427 모두 진행 중 비활성 상태를 포착하지 못했다. 후자는 이전/후보 각각 31/28회 조회, 단일 호출 최고 50.135/40.336ms였다. 이를 버튼이 항상 활성이라는 제품 결함이나 모든 입력 차단 PASS로 해석하지 않는다. 현재 관측의 시간 경계·제공자 지연 원인은 확정하지 못했다.

기존 관련 소스 계약 13/13과 전체 영향 계약 44/44는 유지하지만 **실제 pending Back/Forward/Up와 Alt+Left 거절, 진행 중 새 주소 대체 및 그 상태 픽셀은 미검증**이다. 임의 Release 지연 주입, 사용자 경로 접근이나 같은 8k GUI 재실행으로 통과를 만들지 않는다. 두 관측 방식으로 남은 공백은 다음에 결정적 관측 경계가 마련되거나 새 실제 증상이 있을 때만 해당 단위를 재개한다. 이 한계를 없애기 위한 전체 GUI/제외 DPI/IME 시험은 하지 않는다.

## 실패한 새 주소의 보존 화면

[최종 #40863066296](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40863066296), 같은 main/EXE, 1160×640, 96 DPI, Light. 소유 A/B 폴더 각 .txt 1개에서 B 이동 후 존재하지 않는 소유 경로를 제출했다. Shell 실패 안내, 확정 B 주소·왼쪽 owned-b·오른쪽 owned-a 보존, Up 재활성·정상 종료 0·원래 설정 보존을 실제 확인했다. 성공/실패 상태 PNG를 직접 검토해 두 목록·주소가 유지되고 실패 문구가 보이는 것을 확인했다. **이 한정 실패 경로 기능 GUI와 화면은 PASS**다.

- 실패 전 상태 PNG SHA256 `b2ff7fdb43a0a0990c00630d804247f49301ebf46f58b73ce7bfc7f9f079ff8f`.
- 실패 후 PNG SHA256 `35c29e8a5de1717a7dc3927244855358e86f7cabca2c7bf04ab0e2946eeef63c`.

전체 job은 종료 후 test fixture 경로를 Windows 역슬래시 문자열과 슬래시 기대값으로 비교한 harness 오류 때문에 **FAIL**이다. 실제 GUI 검증 뒤의 오류이며 제품 실패가 아니다. 이어 실행된 별도 cleanup 단계가 정확한 A/B 이름과 원래 바이트를 독립 확인하고 fixture를 제거했다. 테스트는 `relative_to(...).as_posix()`로 수정하고 PureWindowsPath의 같은 두 경로로 구분자 변환을 확인했다. Python 구문 PASS. 이미 통과한 GUI를 이 한 줄의 출력 경로 정규화 때문에 다시 실행하지 않았다. 수정 후 전체 GUI job PASS를 주장하지 않는다.

같은 실행의 cleanup은 이전 실패 profile·fixture·305개 manifest/hash가 일치한 비교용 runtime 등 소유 디렉터리 14개, 123,968,260 bytes (118.225 MiB)를 제거했다. 오류 0, 현재 Release와 호환 캐시는 유지했다. 원래 stash 목록을 보존하며 VM 제품 소스는 ad86618f로 동기화됐다. 최종 문서/도구 반영 후에는 제품 변경 없이 fast-forward와 idle 복원만 수행한다.

진행 중 버튼/단축키 경계는 여전히 위의 미검증 상태다. 실패 주소 수용으로 확대하지 않는다.
