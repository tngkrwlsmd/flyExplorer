# PX15 검색 패널 가로 접근 — 2026-10-29 한정 Windows 수용

## 변경과 정확한 범위

- 제품 코드: [fe84769b](https://github.com/tngkrwlsmd/flyExplorer/commit/fe84769bdae72f890d4edc4d9f3e3c773348e147). 기존 검색 ScrollViewer의 `HorizontalScrollBarVisibility`만 `Disabled`에서 `Auto`로 변경. 기존 세로 스크롤, 최대 높이 400, 파일 패널에 남기는 높이 160, 검색 Controller/탭 상태/데이터 변경 없는 정책은 유지.
- 시험 전용: [8732358a](https://github.com/tngkrwlsmd/flyExplorer/commit/8732358aeaae4d7ebbe141afcb30d71683cb68ad) 새 소유 GUI fixture, [004ad288](https://github.com/tngkrwlsmd/flyExplorer/commit/004ad28887f8f872026f32728bebb7c13165145b)에서는 초기 왼쪽 패널 준비만 요구하던 fixture를 시험 소유 파일이 좌·우 어느 패널에 있든 진행하도록 조정하고 검색 범위를 시험 소유 폴더로 명시. 두 번째 커밋은 제품 C++/XAML 변경 없음.
- 환경: 중앙 관리 Windows 11 build 26300, x64 Release, 96 DPI, 격리된 대화형 사용자 프로필, 테스트 소유 파일 2개. 기존 실행 파일 SHA-256 `ab3109a78d9cba63c3f24f29c75b9ad83be2b38466b014f02c0e167fe67a79e3`를 Light/Dark 모두 사용했다.

## 실행 결과와 실패 분리

| 단계 | 정확한 근거 | 판정 |
| --- | --- | --- |
| 검색 소스 계약 / Python 구문 | [중앙 #40831510904](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40831510904) | 각 exit 0 |
| 실제 Windows Release 빌드 | 같은 #40831510904 | exit 0, 위 EXE 해시 |
| Light 800×519 / 960×519 | 같은 #40831510904 | 집중 GUI exit 0 |
| 최초 Dark 시작 | 같은 #40831510904 | **FAIL**: 왼쪽 파일 행을 20초 기다리다 종료, 가로 스크롤 검사 이전 |
| 수정된 테스트 전용 Dark 실행 | [중앙 #40832073857](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40832073857) | Python 구문 exit 0, **Dark GUI exit 0**, 동일 Release EXE 재사용 |
| 독립 화면 파일 읽기와 해시 확인 | [중앙 #40832267762](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40832267762) | 소유 PNG 6장 SHA-256 일치, 실제 이미지 검토 완료 |

첫 Dark 실패를 성공으로 소급하지 않는다. 당시 `owned file rows not displayed`는 검색 가로 스크롤 로직 검사 전의 시작 조건 실패이며 원인(실제 Shell 시작 실패인지 UIA 준비 지연인지)을 특정하지 않았다. 후속 Dark 실행은 검색 패널 자체의 독립 검증을 위해 시험 폴더를 명시하고 어느 패널의 시험 파일이든 준비되면 진행했다. 별도 G01 시작 탐색의 완전 해결이나 초기 표시의 무결함을 주장하지 않으며 기존 #68/#69 수용 범위도 다시 열지 않는다.

## 실제 GUI 상태

- Light/Dark 각각 800×519에서 검색 패널을 가로 0% → 100%로 움직여 맨 오른쪽 **파일 찾기/검색 취소** 행 끝의 접근 가능한 영역을 확인했다. 이전에 잘리던 긴 조건 줄은 화면 안에서 좌·우로 이동해 읽을 수 있다. UIA `HorizontalScrollPercent=100.0`, 우측 취소 버튼의 실제 사각형이 패널 내부, 동시에 양쪽 파일 목록은 화면에 남는다.
- 960×519에서는 패널 세로 결과 영역으로 이동해 시험 소유 파일 한 개의 결과 선택, 폴더 이동 버튼 활성화 및 양쪽 파일 목록의 높이 80px 이상을 확인했다. 두 파일 항목이 양쪽 목록에 보이는 실제 화면을 검토했다.
- 정확한 소유 앱 HWND만 캡처한 Light/Dark 화면 6장을 해시 대조 후 직접 검토했다. 800px의 스크롤 위치 양 끝에서 의도된 수평 잘림은 있으나 스크롤로 접근 가능하고 새 겹침/대비 저하는 확인되지 않았다. 960px의 검색 결과와 두 파일 패널/상태줄도 가독성이 유지됐다.
- Light/Dark 각각 앱 정상 종료 0, 원래 사용자 설정과 시험 소유 파일 해시 불변, 성공 시 격리 프로필/시험 파일 제거 확인. 시각 증거는 중앙 VM의 무시되는 프로젝트 로그에 보존했고 외부 개인 파일/데스크톱 이미지는 수집하지 않았다.

## 캡처별 SHA-256 (원본 PNG)

| 이미지 | SHA-256 |
| --- | --- |
| Light 800 왼쪽 | `8c5df690c107cb2ea6c2eca3de36ad2011635ed20674f2f437ebd776c8d09da3` |
| Light 800 오른쪽 | `54d1fcaaba9f7382d1f626acdbc9bc4399858acbc1ec5750fd94c6afdfdef77a` |
| Light 960 결과 | `61ae68b60ad7cba5a31a0ce906e2aa1ca0f980b63e475e5264be8dcc940b6e12` |
| Dark 800 왼쪽 | `33783304262e240059af861c391662d7cc04dc684f051820f4a443b3abde3c2b` |
| Dark 800 오른쪽 | `4df61f9b15503c98768f31be21736d65f5baee616cd5700dc526e6b36c670dbe` |
| Dark 960 결과 | `9cbc5bdce61740e9cb548b40a286ca849689972ae68b71bf4baaba97e7a58fff` |

## 한계와 다음 작업

본 수용은 **PX15 검색 가로 접근의 해당 Light/Dark 두 창 크기, 한 시험 검색 결과, UIA 가로/세로 스크롤, 화면 검사** 범위다. 실제 마우스 휠·키보드의 수평 이동, 모든 검색 조건/창 너비, 접근성 음성, 다른 탐색 Shell/provider, 전체 Windows 탐색기 UI 호환, 전체 애플리케이션 GUI를 수용한 것은 아니다. G03~G05 사용자 제외, G07 중단, PX11의 기존 저장 정책을 그대로 보존한다. 이미 완료된 이번 스크롤 변형을 자동 재검증하지 않고, 다음에 별도로 선정된 미완료 기능으로 이동한다.
