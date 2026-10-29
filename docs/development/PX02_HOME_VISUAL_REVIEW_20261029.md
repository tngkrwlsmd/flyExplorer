# PX02 Home / PX15 화면 검토 — 2026-10-29

## 발견한 결함과 수정

홈을 연 넓은 창을 기본 크기(화면상 약 945×511)로 복원하면, 기존 고정
MaxHeight=280이 파일 패널을 밀어내 제목과 열 머리글만 남았다.
이는 이전 PX02 기능 GUI 수용으로 확인하지 못한 실제 화면 결함이다.

RootShell 및 Home의 크기 변경 시 나머지 행의 실제 높이를 제외하고 홈의
MaxHeight를 0~280 범위로 다시 계산한다. 파일 패널에 160 XAML 단위의
공간을 먼저 남기며, 나머지 홈 내용은 기존 세로 스크롤로 접근한다.
새 창 크기 강제 변경, 파일 작업, 기록 활성화 또는 탐색 동작은 추가하지 않는다.

## 실제 검토 결과

Windows 11 build 26300의 기존 표시 설정에서 같은 테스트 소유 fixture
(폴더 1개와 텍스트 파일 2개), 기본 기록 OFF, 북마크 1개를 사용했다.
VM 연결 화면은 1282×875, 게스트 바탕 화면은 1280×768이었다.
OS 배율은 변경하지 않았으며 이 기록은 별도 DPI 수용이 아니다.

| 범위 | 관찰 결과 |
| --- | --- |
| 변경 전 | Light 기본 크기 복원 후 양쪽 파일 행이 잘려 보이지 않음 |
| 변경 후 Dark | 넓은 창과 기본 크기에서 홈 및 양쪽 파일 목록 표시, 기본 크기에서 3개 항목 모두 보임 |
| 변경 후 Light | 넓은 창과 약 945×511로 줄인 창에서 양쪽 파일 목록의 3개 항목 모두 보임 |
| 홈 세로 스크롤 | 작은 Light/Dark 창에서 기록 OFF 설명의 끝까지 접근, 파일 목록 공간 유지 |
| 키보드 포커스 | Dark 홈 북마크에 Shift+Tab으로 이동했을 때 흰 포커스 테두리 식별 |
| 종료와 보존 | 변경 전후 앱 종료 0, 기존 설정 6개 보존, 소유 파일 바이트 보존, 임시 프로필·fixture 정리 |

화면은 Computer Use로 실제 표시를 읽고 조작해 검토했다. 자동 UIA 기능
시험을 화면 검토로 간주하지 않았으며, worker의
`visual_verdict=requires_actual_pixel_review`는 화면 검토 전 대기 표식이다.
위 표는 이후 실제 화면 관찰의 한정된 수용 결과다.

Light 제목 표시줄의 최소화/최대화/닫기 아이콘 대비가 낮은 현상도 관찰했다.
이는 이번 홈 높이 수정 밖의 남은 화면 개선 후보이며, 전체 앱 화면 수용을
완료했다고 판정하지 않는다.

## 소스·실행 파일·검증 근거

빌드 기준은 main `b5f09e6d71e9b4b986473a62b3847da55abe04e5`에
아래 검토한 4개 파일 변경을 더한 내용이다. 통합 커밋의 해당 blob과
일치 여부를 확인하며, 뒤따른 문서 편집 때문에 같은 빌드를 반복하지 않는다.

| 변경 파일 | 검증한 Git blob |
| --- | --- |
| app/winui/MainWindow.xaml | b55ac508ecc3feb814a20ebf89f46746f49b041d |
| app/winui/MainWindow.xaml.cpp | 3946f90d3cafd5b5e7e9f9b4cf685844ec88aae7 |
| app/winui/MainWindow.xaml.h | 1dc075bcb07e9ab725024d59d607a7dff81f8a9c |
| tests/winui/test_home_overview_contract.py | 273dbfe95bad397d854add8af3dd631a427b932a |

- 로컬 및 VM의 Home/최근 활동 집중 소스 계약: 각각 **11/11 PASS**.
- 기존 호환 중간 산출물을 재사용한 증분 x64 Release 빌드: **종료 0**.
- [변경 전 준비 #40798056527](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40798056527): 기준 소스의 증분 Release와 격리 프로필 실행.
- [변경 후 준비 #40799832282](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40799832282): 4개 blob 일치, 집중 소스 계약 및 증분 Release 성공.
- [종료·보존 확인 #40800979406](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40800979406): 전후 종료 0, 기존 설정·소유 파일 보존, 임시 fixture/프로필 제거, 소유 예약 작업 해제.
- 변경 전 EXE SHA-256: `6044fc503d26347ae1e606894b0aa81751723484957f798aea564332338aa4b5`.
- 변경 후 EXE SHA-256: `7526f673ebb2559a9cb924a029766037fc36b102fc1b5afb4aa0b5e898c9a1eb`.
- 공통 helper SHA-256: `88017a2c25ed70a7cd0a615aa75f2a7a3632bb9f4085fb82089b718454c744fd`.
- 전후 화면 파일은 작업 공간의 `home-visual-review/`에 보존했다.
  화면 파일과 개인 머신의 원시 로그는 제품 저장소에 넣지 않는다.

## 수용 경계와 다음 작업

**홈의 복원·축소 시 파일 패널 공간 보존과 위 표의 화면 범위는 수용 완료**다.
[기존 PX02 기능 수용](PX02_HOME_OVERVIEW_ACCEPTANCE.md)은 그대로 재사용한다.
활동이 채워진 홈, 긴 북마크 타일, Light 키보드 포커스, 다른 표시 환경,
전체 PX15, 전체 기능 GUI 또는 패키지 수용으로 확대하지 않는다.
G03~G05는 제외, G07은 중단 상태를 유지한다.

같은 홈 검사를 반복하기보다 다음 현행 항목인 PX13/G08의 로컬 대량 폴더
응답성 측정 범위를 먼저 정한다. 위 제목 표시줄 대비 문제는 별도의 작은
화면 개선 항목으로 남긴다.
