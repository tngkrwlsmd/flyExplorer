# R11 선택 항목 메뉴 단축키 안내 — 실제 Windows 한정 수용 (2026-10-31)

Windows 11 탐색기와의 차이 중 선택 항목 메뉴에서 자주 쓰는 명령의 키보드 단축키를 찾기 쉬운 표시만 추가한다. 기존 메뉴의 세로 배치와 명령 처리 로직은 유지한다.

| 명령 | 표시 |
| --- | --- |
| 잘라내기 | Ctrl+X |
| 복사 | Ctrl+C |
| 경로 복사 | Ctrl+Shift+C |
| 이름 바꾸기 | F2 |
| 삭제 (휴지통) | Delete |

Windows App SDK에서 제공하는 MenuFlyoutItem.KeyboardAcceleratorTextOverride 속성으로 설명을 붙인다. 실제 단축키 등록이나 명령 실행·경로 확인·확인창·OS 클립보드·휴지통 정책은 변경하지 않는다. 사용 중인 듀얼 패널 고유 명령도 그대로 남긴다.

관련 소스 계약 테스트를 새로 추가해 기존 파일 목록 단축키와 표시값의 일치를 검사하도록 등록했다.

GUI 검사 `tests/winui/test_r11_menu_shortcut_hints_gui.py`는 사용자 데이터 대신 소유한 임시 파일 한 개를 선택하고 메뉴 명령 5개와 활성 상태를 확인한 뒤 앱 소유 창 이미지만 저장했다. [실제 Windows GUI #41199151346](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41199151346)의 GUI 작업자는 **exit code 0**으로 끝났고, 원본 파일 바이트·기존 설정 보존, 앱 정상 종료, 소유 fixture/profile 정리 PASS를 기록했다. 바깥 제어 스크립트는 테스트가 실제 저장한 `logs/r11-shortcut-hints-owned-gui-20261031/result.json` 대신 잘못된 경로를 조회하여 FAIL로 표시됐다. 이는 제품/GUI 테스트 실패가 아니다.

[보존 증거 재검증 #41199490778](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41199490778)에서 결과 JSON·실행 파일 SHA·정상 종료·원본 보존·스크린샷 PNG(1160×640) 존재 및 형식을 재확인하고, 작업자 폴더를 안전하게 정리했다. PNG를 JPEG로 변환해 앱 소유 화면을 직접 살펴본 결과 다크 테마/96 DPI/1160×640 한정으로 **잘라내기 Ctrl+X, 복사 Ctrl+C, 경로 복사 Ctrl+Shift+C, 이름 바꾸기 F2, 삭제 Delete**의 오른쪽 정렬 표시와 가독성을 확인했다. GUI 작업자 로그와 첫 제어 스크립트의 실패 기록은 삭제하지 않았다.

Microsoft의 [Windows App SDK 공식 설명](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.controls.menuflyoutitem.keyboardacceleratortextoverride)에 따르면, 해당 텍스트는 시스템이 연결된 키보드를 감지하지 못할 때 표시되지 않을 수 있다. 그러므로 VM에서 속성이 설정된 것과 **화면에 실제로 보이는 것**을 구분해 검사하고, 키보드가 없다고 판정된 환경의 화면 부재를 기능 오류나 성공으로 단정하지 않는다.

**수용 범위:** [Windows 소스 검사·증분 Release #41195478631](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41195478631) **26/26 PASS 및 Release PASS**. 정확한 빌드 소스 `c98bbfb17fe8966be88ec6f93ffe8dee2334d596`, EXE SHA256 `e10f4925b11a9152881fd1d4f2a76048ba31d2f27c4a27fc49d8ec98785521b4`. 기존 제품 main 기준으로 변경한 소스 파일은 `app/winui/m22_transfers.cpp` 한 곳이며, 함께 추가된 소스·GUI 계약과 문서 이외의 R12 코드는 포함하지 않는다. 사용자 클립보드·휴지통·파일 변경 명령은 GUI에서 누르지 않았고 실제 키보드 단축키 재실행 동등성 및 다른 환경은 본 작업에서 재검증하지 않았다. 라이트/고대비/125~200% 배율, 연결 키보드 없는 장치, Windows 11 가로 아이콘 행 전체 동등성은 미검증이다.

이후 Windows 11식 가로 아이콘 행 자체를 도입할지는 별도 화면·키보드·접근성 검증이 필요한 작업이다.
