# R05 Terminal fallback: 소스·Release 성공과 GUI 요청 스크립트의 HEAD 오류 (2026-10-31)

## 변경된 실제 제품
- 제품 `e452fe990d6798ac3292f5eded79d4d634abedb0`; 선행 `16e6986e2c46dc5c9e6d16eedc82b491f45c1ed5`가 ‘터미널에서 열기’ 메뉴, 활성 패널/현재 폴더·경로의 안정성 검증 및 안전한 로컬 경로로 `wt.exe`를 여는 기능을 도입했다.
- 후속은 per-user 실행 별칭 `%LOCALAPPDATA%\\Microsoft\\WindowsApps\\wt.exe`가 없을 때 Store 설치 패키지의 `Microsoft.WindowsTerminal_8wekyb3d8bbwe!App`을 `IApplicationActivationManager::ActivateApplication`으로 실행하려는 fallback이다. 대상 폴더는 최대 1024자, fixed drive/일반 로컬 폴더로 한정된다. GUI 테스트는 선택한 새 HWND/PID만 대상으로 창을 닫으며 터미널에 명령을 입력하지 않는다.

## 정확한 실행 증거
- [#41179006927](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41179006927): `test_r05_terminal_contract.py` **3/3 PASS**, 실제 Windows Release **PASS**, 소스 `e452fe990d6798ac3292f5eded79d4d634abedb0`; EXE SHA256 `e017cdd3e39949e1e30746330f05f983406312f36fe0979cb7391dc9ea4bfc2e`; helper SHA256 `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`. 증분 빌드의 함수 25,788개 재컴파일도 보존한다.
- [#41181754682](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41181754682): 검사·환경 선행 조건 **FAIL**, `Invoke-FlyExplorerR05TerminalFallbackGUI.ps1`의 `UNEXPECTED_OR_DIRTY_R03_SOURCE`. 기존 GUI 템플릿의 이전 커밋 `6f3c805f...`를 요구했으나 새 빌드가 checkout을 `e452fe990...`로 이동시켰다. 해당 PowerShell 예외는 프로세스/테스트 파일 생성 이전에 발생했다. **새 Terminal 창은 관측 시도조차 시작하지 않았다.**
- 요청 파일 `requests/remote-shell/windows-vm.json`은 [skip ci] `01ca8b43097ff8c7b74b939776bc67ce1c6e0bf4` idle로 복구. 잘못된 source preflight 하나를 고치려는 GitHub 파일 갱신은 도구 안전 검사에서 차단되어 저장되지 않았다. 임의 우회는 시도하지 않았다.

## 재개 가이드
1. 최신 main 10커밋, Control Plane main/slot/활성 작업을 다시 읽어 다른 소유자 요청을 건드리지 않는다.
2. 통제된 기존 GUI 스크립트에서 `git rev-parse HEAD`의 기대값만 현재 소스 `e452fe990...`로 맞춘 뒤, Git diff 허용 파일 세 개(`shell_terminal_delegate.h`, R05 source contract, R05 GUI)·정확한 Release EXE hash/desktop/작업 폴더 원본·근거를 그대로 검증한다. 안전 검사가 허용하지 않으면 무리하게 제출하지 않는다.
3. 이미 PASS한 Release를 재빌드하지 않는다. 승인된 GUI가 실행되어 새 창을 실제로 관측하고 소유 파일·설정이 보존되면 관련 실제 화면만 확인한다. GUI 실패라면 첫 오류의 제품/검사/환경 귀속을 명시한다.
4. R04 바로 가기 생성, 전역 클립보드, 실제 휴지통·외부 전송, 개인 PC/RDC/Codex 연결, 제외 G03~G05·중단 G07 및 세션 v4 정책은 무단 확장하지 않는다.
