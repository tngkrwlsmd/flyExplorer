# R05 Terminal fallback: Release 및 실제 Windows GUI 한정 수용 (2026-10-31)

## 후속 해결 및 최종 수용
- 초기 [#41181754682](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41181754682)의 `UNEXPECTED_OR_DIRTY_R03_SOURCE`는 테스트가 이전 소스 HEAD를 요구하던 **검사 사전 조건 오류**다. 컨트롤 플레인 `a88594272c04ead91e351ba852c476bcc2bf8367`에서 그 조건과 문서 전용 main SHA 비교를 실제 소스에 맞게 수정했고, 기존 Release를 재빌드하지 않았다.
- [#41182673672](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41182673672) **GUI PASS**: 본 문서의 동일 실행 파일 SHA256 `e017cdd3e39949e1e30746330f05f983406312f36fe0979cb7391dc9ea4bfc2e`로 실제 앱 빈 배경 메뉴에서 `터미널에서 열기` 클릭, 새 Windows Terminal HWND/PID 관측·닫기, 원본 파일과 기존 설정 보존, 앱 정상 종료, 소유 fixture/profile/worker 정리를 확인했다. `R05_TERMINAL_OWNED_GUI=PASS; PIXELS_NOT_REVIEWED`. 특정 Windows VM·일반 로컬 폴더·Dark/96 DPI 한정 동작 검증이다.
- 이전 실패와 재개 가이드는 **해결 전 이력**이다. 성공 후 중앙 Windows 제어 요청 슬롯은 idle로 반환했다. 메뉴와 창의 픽셀 육안 평가, 다른 설치 환경/경로·별도 Windows 동등성은 미검증이다.

## 이전 조사·재개 기록 (해결 전 이력)

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
