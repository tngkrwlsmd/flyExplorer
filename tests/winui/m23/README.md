# M2.3 비전역 클립보드 및 WinUI 전용 개인 세션 격리 시험

Debug 또는 Release `build.cmd`로 MFC/WinRT 독립 native 계약 바이너리를 빌드한다. 같은 구성으로 `FLY_M23_CONFIG=Debug|Release`를 지정하고 `python -u test_native.py`를 실행한다. 한글 파일 CF_HDROP 인코딩/디코딩, 잘못된 데이터·너무 많은 파일 거부, 테스트가 소유한 로컬 Shell 복사, 클립보드를 직접 건드리지 않는 테스트, 유효한 개인 세션 라운드트립·저장/삭제 및 원본 MFC 사용자 설정 해시를 검사한다.

실제 저장·재실행 복원은 GUI `FLY_M23_OWNED_FEATURES=YES`로 원본 테스트 하네스 `test_shell_gui.py`의 자체 합성 폴더만 사용한다. 소유 두 번째 WinUI 프로세스는 `FLY_M23_OWNED_SESSION=YES`와 `--m23-owned-auto-restore`의 명시 테스트 가드에 결박되며 소유 PID/정확한 EXE/시작 인자가 일치할 때만 닫는다. **운영체제 전체 클립보드에 대한 읽기·쓰기를 자동 테스트에서 시행하지 않는다.**

물리 마우스 내부/외부 드래그는 아직 PASS가 아니다. `FLY_M23_OWNED_DRAG_TEST=YES`의 별도 현재 실패 진단을 제품 정상 동작 증거로 사용하지 않는다. 네이티브 파일 작업 계층의 검증도 실제 사용자의 전역 휴지통 삭제/복원을 수반하지 않는다.
