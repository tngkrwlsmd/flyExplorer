# R11 선택 항목 메뉴 단축키 안내 — 개발 후보 (2026-10-31)

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

GUI 검사 후보 `tests/winui/test_r11_menu_shortcut_hints_gui.py`는 사용자 데이터 대신 소유한 임시 파일을 선택하고 메뉴 명령 5개와 활성 상태를 확인한 뒤 앱 소유 창 이미지만 저장하도록 작성했다. **아직 실행 전**이며, 텍스트 오버라이드가 실제로 화면에 나타나는지는 저장된 이미지의 별도 시각 검토가 필요하다.

Microsoft의 [Windows App SDK 공식 설명](https://learn.microsoft.com/en-us/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.controls.menuflyoutitem.keyboardacceleratortextoverride)에 따르면, 해당 텍스트는 시스템이 연결된 키보드를 감지하지 못할 때 표시되지 않을 수 있다. 그러므로 VM에서 속성이 설정된 것과 **화면에 실제로 보이는 것**을 구분해 검사하고, 키보드가 없다고 판정된 환경의 화면 부재를 기능 오류나 성공으로 단정하지 않는다.

**상태:** 소스 구현과 계약 테스트 작성까지 진행했다. 실제 Windows Release 컴파일, 메뉴 GUI 및 화면 배치 검토는 미실행이다. R12 개발 후보 위에 쌓인 별도 브랜치이므로 R12 검증과 정식 반영 전에는 제품 main에 반영하지 않는다.

이후 Windows 11식 가로 아이콘 행 자체를 도입할지는 별도 화면·키보드·접근성 검증이 필요한 작업이다.
