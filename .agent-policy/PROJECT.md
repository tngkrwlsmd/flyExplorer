# PROJECT.md — flyExplorer project facts, architecture, readiness

이 파일은 universal-agent-docs의 PROJECT template을 flyExplorer에 맞게 채운 Validated-profile 프로젝트 지도다.
상세 제품 명세를 복제하지 않고 실제 Source of Truth 위치와 현재 확인된 build/runtime 사실을 기록한다.

<!-- project-facts:start -->
```json
{
  "profile": "flyexplorer-validated",
  "facts": {
    "repository_root": {
      "value": ".",
      "status": "Confirmed",
      "evidence": "path:."
    },
    "primary_source": {
      "value": "src",
      "status": "Confirmed",
      "evidence": "path:src"
    },
    "build_command": {
      "value": "build.bat",
      "status": "Confirmed",
      "evidence": "command-source:README::build.bat"
    },
    "test_command": {
      "value": "",
      "status": "N/A",
      "evidence": "manual:no single unit/integration test command is defined; source preflight, Windows Product Build CI, hosted runtime smoke, and package validation are automated, while clean Windows Sandbox/VM checks remain manual"
    },
    "runtime": {
      "value": "Visual Studio 2026",
      "status": "Confirmed",
      "evidence": "value-source:README::Visual Studio 2026"
    },
    "deploy_command": {
      "value": "",
      "status": "N/A",
      "evidence": "manual:desktop application repository has packaging scripts but no deployment target"
    },
    "deploy_target": {
      "value": "",
      "status": "N/A",
      "evidence": "manual:no production deployment environment is defined"
    }
  },
  "components": [
    {
      "name": "fxfile",
      "path": "src/fxfile",
      "responsibility": "Main MFC file-manager application"
    },
    {
      "name": "xpr",
      "path": "src/xpr",
      "responsibility": "Shared portability/runtime library used by the application"
    },
    {
      "name": "fxfile-crash",
      "path": "src/fxfile-crash",
      "responsibility": "Crash-handling module"
    },
    {
      "name": "fxfile-keyhook",
      "path": "src/fxfile-keyhook",
      "responsibility": "Win32 keyboard-hook helper"
    },
    {
      "name": "fxfile-launcher",
      "path": "src/fxfile-launcher",
      "responsibility": "Win32 launcher/tray helper"
    },
    {
      "name": "fxfile-upchecker",
      "path": "src/fxfile-upchecker",
      "responsibility": "Legacy Win32 update-check helper; built separately for packaging"
    }
  ],
  "review": {
    "reviewed_revision": "52499667c0adaa8ce0ef012195fd9a0d5d68379e",
    "reviewed_at": "2026-09-21",
    "reviewed_paths": [
      "README",
      "build.bat",
      "build/common.gypi",
      "build/fix_solution_configs.py",
      "build/validate_source_invariants.py",
      ".github/workflows/windows-build.yml",
      "build/runtime_smoke.ps1",
      "build/validate_package.ps1",
      "dist/package.bat",
      "dist/copy.bat",
      "dist/make_portable.bat",
      "dist/make_installer.bat",
      "dist/setup.nsi",
      "fxfile.gyp",
      "src/fxfile",
      "src/xpr",
      "src/fxfile-crash",
      "src/fxfile-keyhook",
      "src/fxfile-launcher",
      "src/fxfile-upchecker"
    ]
  }
}
```
<!-- project-facts:end -->

## 시스템 개요

- 제품 목적: Windows용 고기능 multi-pane file manager
- 주요 사용 환경: Windows 10/11 desktop
- 현재 개발 toolchain: Visual Studio 2026, MSVC v145, Windows 10/11 SDK, Python 3.9+, gyp-next 0.22.2
- 주요 use case: multi-pane/tab file browsing, file operations, search, rename, sync, preview, shell integration
- 비기능 우선순위: 기존 기능/shortcut 호환성, 안정적인 file operation, modern Windows UI 적응, x86/x64 helper compatibility

## Components / entry points

| Component | Path | Architecture / role |
|---|---|---|
| Main application | `src/fxfile` | x64 Unicode 권장, MFC desktop executable |
| XPR | `src/xpr` | x64 shared runtime for main application |
| Crash handler | `src/fxfile-crash` | x64 DLL |
| Key hook | `src/fxfile-keyhook` | Win32 helper |
| Launcher | `src/fxfile-launcher` | Win32 helper |
| Update checker | `src/fxfile-upchecker` | Win32 helper; x64 solution build에서는 제외 |

## Source of Truth

| 종류 | 위치 | 분류 | 비고 |
|---|---|---|---|
| 빌드/프로젝트 정의 | `fxfile.gyp`, `src/**/*.gyp`, `build/common.gypi` | Contract | 생성된 vcxproj보다 우선 |
| VS 2026 생성/보정 | `build.bat`, `build/fix_solution_configs.py` | Observed / Contract | v145, mixed architecture mapping |
| 프로그램 구현 | `src/` | Observed | C++/MFC |
| third-party | `lib/`, `CREDITS` | Contract / Observed | ABI/license 검토 필요 |
| 패키징 | `dist/package.bat`, `dist/copy.bat`, `dist/make_portable.bat`, `dist/make_installer.bat`, `dist/setup.nsi` | Contract / Observed | x64/x86 staging, portable ZIP 3종, vendored NSIS installer |
| 개발 환경 문서 | `README` | Intended / Observed | 실제 build evidence와 함께 해석 |
| 제품 빌드 CI | `.github/workflows/windows-build.yml` | Contract / Evidence | VS 2026 x64 Unicode + x86 Unicode/Multibyte compile/link, warning, 산출물 및 hosted-runner launch smoke 검증 |
| runtime smoke | `build/runtime_smoke.ps1` | Contract / Evidence | 임시 staged runtime + isolated conf_dir에서 process/main-window/stability 검증 |
| package validation | `build/validate_package.ps1` | Contract / Evidence | staging/portable payload, updater runtime, installer output 검증 |
| build/runtime 결과 | GitHub Actions build log, Visual Studio build log, hosted-runner launch smoke, Windows Sandbox/VM smoke | Evidence | compile/link, hosted runtime, clean-runtime evidence를 분리 |

## Generated artifacts

다음은 canonical source가 아니다.

- `fxfile.sln`
- `*.vcxproj*`
- `bin/`
- `obj/`
- `tools/`
- generated installer / portable archives

이들은 `build.bat` 또는 packaging script에서 다시 만들 수 있어야 한다.

## Known constraints

- legacy MFC code와 deprecated Windows API가 남아 있다.
- 일부 third-party binary는 오래되었고 architecture가 제한될 수 있다.
- x64 solution은 mixed-architecture helper mapping을 사용한다.
- updater는 x64 Build Solution에서 의도적으로 제외한다.
- product unit/integration test suite는 아직 확인되지 않았다.
- Windows Product Build CI가 `Release-x64-Unicode | x64`, `Release-x86-Unicode | Win32`, `Release-x86-Multibyte | Win32`의 실제 compile/link와 핵심 산출물을 검증하며, 각 MSBuild file log에서 compiler/linker/MSBuild warning이 발견되면 실패한다. reviewed revision 기준 세 제품 빌드는 모두 warning 0건이다.
- x86 Unicode는 `libxprw.dll/.lib`, x86 Multibyte는 `libxpr.dll/.lib` 계약을 검증한다. `fxfile-upchecker`는 Unicode/x64 Build Solution에서 제외되고 x86 Multibyte에서 실제 compile/link 및 runtime staging 산출물을 검증한다.
- xpr의 logical target 이름은 `xpr`로 유지하면서 generated MSBuild `TargetName`을 configuration별 physical product 이름(`libxprw` / `libxpr` 계열)과 정렬해 MSB8012를 제거했다.
- crash module은 vendored zlib 1.2.3 source를 현재 MSVC로 직접 빌드하며 legacy `zlibS-x64.lib`를 링크하지 않는다.
- crash/network resolver 경로는 deprecated `gethostbyname`/`inet_ntoa`/`inet_addr` 대신 modern Winsock address API를 사용한다.
- distribution 입력 이름은 현재 제품 계약에 맞춰 Unicode/x64 `libxprw.dll`과 `upchecker/fxfile-upchecker.exe`를 사용한다. Windows Product Build CI는 세 release runtime을 모아 `dist/package.bat`을 실제 실행하고 portable ZIP 3종과 NSIS installer를 생성한 뒤 `build/validate_package.ps1`로 staging/ZIP/installer output을 검증한다.
- 패키징은 vendored `dist/7zip/7za.exe`와 `dist/nsis/makensis.exe`를 사용하며 외부 NSIS 다운로드를 요구하지 않는다. 검증된 installer/portable 3종과 `SHA256SUMS.txt`는 `flyExplorer-release-package` Actions artifact로 보존한다.
- installer 실제 설치/제거, shell integration install/remove, clean Windows Sandbox/VM install은 아직 자동화하지 않으며 Package Build/Payload PASS와 구분한다.
- GitHub-hosted Windows runner에서 x64 Unicode, x86 Unicode, x86 Multibyte의 launch smoke를 자동화한다. smoke는 staged runtime을 임시 디렉터리에 복사하고 isolated `--conf_dir`로 `fxfile.exe`를 시작한 뒤 top-level main window와 short stability window를 확인한다.
- hosted runner에는 Visual Studio와 여러 system runtime이 이미 설치되어 있으므로 이 결과는 clean Windows Sandbox/VM evidence가 아니다. Windows Sandbox/clean VM, interactive functional smoke, visual regression은 아직 자동화하지 않는다.
- `build/validate_source_invariants.py`가 C++ cross-cutting dependency와 ModernUI integration의 빠른 static preflight를 제공한다.
- `.agent-policy/`에는 upstream `universal-agent-docs` revision `cc250a63994f1d9d4fcfdbb2bab9b622230bf8c6`의 validated policy bundle을 vendor하며 root CI에서 bundle/readiness/conformance를 검사한다.
- Profile C runtime enforcement는 설치되어 있지 않다.
- Windows 11 UI 현대화 Phase 1에서 Per-Monitor V2 DPI, system typography, theme palette foundation을 추가했다.
- Phase 2에서 toolbar padding/system typography/double buffering과 flat theme-aware tab rendering, DPI-scaled tab metrics를 추가했다.
- Phase 3에서 file list/header를 system font/theme palette 기반으로 정리하고, folder tree에 DPI-aware row/indent/system typography를 적용했으며 explorer pane/splitter 배경을 flat separator 기반으로 정리했다.
- Phase 4의 첫 단위로 AddressBar에 system UI font fallback, ComboBox/edit font 동기화, font/icon 기반 DPI-aware item metrics, settings/DPI 변경 시 font refresh를 적용했다.
- Phase 4의 다음 단위로 StatusBar 공통 기반에 system UI font, 96-DPI logical pane metrics, ThemePalette 기반 flat background/text/separator, settings/theme/DPI refresh를 적용하고, ExplorerStatusBar의 4-pane 정보 구조와 drive-properties double-click 계약을 유지한 채 drive usage progress를 palette/DPI-aware rendering으로 정리했다.
- StatusBar/TextProgressCtrl 현대화는 Windows Product Build에서 x64/x86 compile/link, warning 0, hosted launch smoke, package regression을 통과했지만 100/125/150/200% DPI visual, High Contrast visual, interactive status-bar 동작은 별도 수동 evidence가 아직 없다.
- Dialog 현대화의 첫 reference로 DriveDetailDlg에 ModernUI system UI font와 explicit child-font 동기화, settings/theme/DPI refresh를 적용했다. 기존 bold TextProgressCtrl percentage contract는 유지하며, DrivePieCtrl은 ThemePalette 기반 used/free colors와 DPI-scaled margin/legend metric을 사용한다.
- DriveDetailDlg 현대화는 Debug/Release x64, x86 Unicode/Multibyte compile/link, warning 0, hosted launch smoke, package regression을 통과했다. 실제 dialog open/close, keyboard navigation, 100/125/150/200% DPI visual, High Contrast visual은 아직 수동 검증하지 않았다.
- top-level MainFrame title bar는 documented `DWMWA_USE_IMMERSIVE_DARK_MODE` DWM attribute를 동적 로딩하는 ModernUI helper로 opt-in하며 create/settings/theme change 시 재적용한다. High Contrast에서는 dark frame 요청을 끄고, 미지원 Windows/DWM 실패는 기존 frame 동작으로 fallback한다.
- MainFrame title-bar foundation은 source-invariant, Debug/Release x64, x86 Unicode/Multibyte compile/link, warning 0, hosted launch smoke, package regression을 통과했다. 실제 Windows 11 light/dark 전환 시 title-bar visual, High Contrast visual은 아직 수동 검증하지 않았다.
- common-control/dialog dark theming과 나머지 dialog/icon asset 현대화는 후속 phase 범위다.

## Recommended verification

0. `python build/validate_source_invariants.py`
1. `build.bat`
2. 새로 생성된 `fxfile.sln`을 Visual Studio 2026에서 열기
3. `Release-x64-Unicode | x64` Build Solution
4. `build.bat 2026 x86` 후 `Release-x86-Unicode | Win32` 및 `Release-x86-Multibyte | Win32` Build Solution
5. x64/x86 제품 산출물과 x86 Multibyte `fxfile-upchecker` 산출물 확인
6. `build/runtime_smoke.ps1` 또는 GitHub Actions hosted-runner launch smoke 결과 확인
7. `dist/package.bat`으로 portable ZIP 3종과 NSIS installer 생성
8. `build/validate_package.ps1 -DistDir dist`로 package payload 검증
9. GitHub Actions의 Windows Product Build 결과와 로컬 build/runtime/package evidence를 비교
10. Windows Sandbox 또는 clean VM에서 clean install/runtime smoke test
11. interactive 기능 및 UI 변경이면 visual 결과를 별도로 확인

## Maintenance

build command, toolchain, component architecture, generated-file 규칙, packaging 구조가 바뀌면 이 문서와 root `AGENTS.md`를 함께 갱신한다.
실제 코드/빌드 evidence와 충돌하면 이 문서를 무조건 믿지 말고 evidence를 다시 확인한다.
