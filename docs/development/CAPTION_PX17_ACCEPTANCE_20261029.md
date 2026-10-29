# Light 제목 표시줄과 PX17 새 항목 메뉴 — 2026-10-29

## 구현과 사용자 변화

Light 테마의 최소화·최대화·닫기 아이콘을 앱의 실제 테마에 맞춘다.
Windows 기본 버튼/동작을 유지하며 최초 설정과 `ActualThemeChanged`에서
공개 AppWindowTitleBar 색상 API만 적용한다. 고대비/조회 실패 시 지정 색을
해제해 Windows에 맡긴다. 고대비 환경 시험을 수행한 것은 아니다.

폴더/텍스트 파일 생성 엔진과 배경 메뉴는 이미 있으므로 재구현하지 않았다.
**더 보기 → 새로 만들기 → 폴더 / 텍스트 문서 (.txt)**를 추가했다.
기존 새 폴더 버튼과 단축키는 유지한다. 기존 이름 편집 명령에 연결하며
Enter/Escape·작업 문맥·충돌·로컬 경로·덮어쓰기 금지 처리를 재사용한다.

## 실제 검증

Windows VM, Windows 11 build 26300, x64 Release, 960×519 픽셀, 96 DPI.
같은 소유 fixture 형태와 격리 프로필을 사용했다. 원래 바탕 화면·사용자
파일·클립보드·휴지통을 조작하지 않았다.

| 범위 | 결과 |
| --- | --- |
| 관련 소스 | Fluent 17/17, 파일 명령·가용성 17/17 PASS. UIA 이름 계약 보강 후 파일 명령 15/15 PASS |
| Release | 종료 0. 기존 산출물은 유지했으나 LTCG에서 IPDB/IOBJ 불일치로 전체 함수 컴파일에 폴백 |
| Light 전후 픽셀 | 수정 전 흰 캡션 아이콘이 밝은 배경에 묻힘. 수정 후 검은 아이콘 3개 식별, 잘림·배치 변화 없음 |
| Dark 전후 픽셀 | 기존 흰 아이콘 식별 유지. 의도하지 않은 색·배치 변화 관찰 없음 |
| 메뉴 픽셀 | 별도 popup에서 '폴더', '텍스트 문서 (.txt)'를 읽을 수 있음. 앱 창 캡처와 별도로 소유 하위 메뉴 영역을 직접 확인 |
| 실제 생성 | 왼쪽 현재 폴더에 .txt 생성, 내용 0바이트 |
| 충돌 | 기존 파일 오류 안내, 원래 27바이트 보존 |
| 잘못된 이름 | `../escape.txt` 거부, 소유 폴더 밖 파일 미생성 |
| 취소 | 이름 입력 후 Escape, 해당 파일 미생성 |
| 활성 패널 | 오른쪽 활성 패널의 소유 하위 폴더에 생성, 오른쪽 목록·실제 경로 일치, 부모 폴더에 미생성 |
| 창 동작·종료 | 소유 HWND에 Windows 표준 최소화/최대화/복원 명령 성공, 닫기 후 종료 0 |
| 보존·정리 | 기존 설정 존재/해시와 원래 소유 파일 보존. 성공 fixture/프로필 및 스케줄러 작업 제거 |

기능 GUI와 실제 픽셀 검토는 각각 수행했다. 두 테마의 캡션 비교와 제한된
메뉴 표시만 시각 수용한다. 모든 크기·hover/pressed·비활성 상태, Snap
Layouts, 전체 PX15, 임의 Shell New 템플릿과 모든 PaneTab 전환 경합은
별도 미검증이다. G03~G05 제외와 G07 중단은 유지한다.

## 정확한 소스·실행 파일·실패 이력

기준 `693410792e029f3a026a0deba192acba4b496580`에 검토한 성능/캡션/메뉴
변경을 더한 다음 여섯 product blob으로 빌드했다. 통합 후 같은 blob인지
대조하며, 문서 편집 때문에 같은 빌드를 반복하지 않는다.

| 파일 (`app/winui/`) | 검증한 blob |
| --- | --- |
| MainWindow.xaml.cpp | cf691f9415cd03de458e38c8e650cd020841ccd3 |
| MainWindow.xaml.h | 2a7937efe3e519079c8f530e7669d515a0246d75 |
| m20_shell.cpp | 910ce9cc12eb7199baa85b2cf00969542ff6286e |
| FileToolbar.xaml | 030c0e78c552893ce59bc77cd5718f1f8f6ed0e3 |
| FileToolbar.xaml.cpp | 0cea6dd62f66f9f89cfae3b55c112449c87ee50f |
| FileToolbar.xaml.h | 959f1d7a99155bf0be16654bbde0a1085c3236c2 |

- 변경 전 EXE SHA-256: `05d09dece705cfda56f0842f8dc43ecdeb3f07b63daa8a2163a111882f46c99a`.
- 변경 후 EXE SHA-256: `bed5a148ec4dc10ded3787d019ab7fda45089e73e1e7664fc8999e8e0cc0c131`.
- 최종 GUI 스크립트 SHA-256: `c8a5228a767c254d96fee7551ff713f0b1c63e404a74a852ee552a3123258f20`.
- [#40803819387](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40803819387): **빌드 PASS, 전체 시험 FAIL**. 최초 생성 후 메뉴 재열기 시험 실패. 이 실행을 GUI PASS로 변경하지 않는다.
- [#40816557383](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40816557383): **FAIL**. UIA 접근성 이름을 화면의 Text와 혼동한 시험 결함이다.
- [#40816798955](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40816798955): **집중 GUI PASS**. 같은 빌드 재사용. 생성/충돌/잘못된 이름/취소/오른쪽 패널, 기본 창 명령, 종료 및 보존·정리 marker 확인.

원본 이미지 픽셀을 직접 읽어 Light/Dark 전후와 하위 메뉴를 검토했다.
이미지는 테스트 소유 앱/메뉴 영역만 캡처했으며 Git에 커밋하지 않는다.
공식 근거: [Microsoft 제목 표시줄 색상/기본 캡션 동작](https://learn.microsoft.com/en-us/windows/apps/develop/title-bar).
