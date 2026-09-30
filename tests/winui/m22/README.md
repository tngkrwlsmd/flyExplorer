# M2.2 안전한 네이티브 Shell 파일 작업 격리 시험

`build.cmd Debug` 또는 `build.cmd Release`로 별도의 MFC/WinRT 독립 네이티브 시험 파일을 빌드한다. 같은 구성으로 `FLY_M22_CONFIG`를 설정하고 `python -u test_native.py`를 실행한다.

시험은 `logs/m22` 아래에 만든 임시 소유 폴더와 별도 APPDATA·LOCALAPPDATA만 쓴다. 실제 한글 파일 복사·이동·다중 선택·이름 충돌 시 거부/둘 다 유지·휴지통 동의 거부 및 사전 취소를 검사하고, 기존 여섯 MFC 설정은 해시만 검사한다. **자동 시험에서는 전역 Windows 휴지통을 변경하지 않는다.** 실제 GUI 검증은 같은 개발 빌드에서 `FLY_M22_OWNED_FEATURES=YES`를 설정한 `test_shell_gui.py`가 소유한 창만 대상으로 수행한다.
