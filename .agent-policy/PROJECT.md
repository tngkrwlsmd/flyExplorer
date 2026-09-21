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
      "value": "local_ci.bat x64",
      "status": "Confirmed",
      "evidence": "command-source:README::local_ci.bat x64"
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
    "reviewed_revision": "b6ed8a9d55757ca90a1340ea001718628c25b1d2",
    "reviewed_at": "2026-09-21",
    "reviewed_paths": [
      "README",
      "LOCAL_CI_MANUAL.txt",
      "build.bat",
      "local_ci.bat",
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
| 로컬 CI orchestration | `local_ci.bat`, `LOCAL_CI_MANUAL.txt` | Contract / Evidence | quick/policy/x64/x86/release/full profiles; 실행 로그는 `logs/local-ci/local-ci.log` 하나로 통합, manual은 프로필별 한 줄 사용법 제공 |
| 프로그램 구현 | `src/` | Observed | C++/MFC |
| third-party | `lib/`, `CREDITS` | Contract / Observed | ABI/license 검토 필요 |
| 패키징 | `dist/package.bat`, `dist/copy.bat`, `dist/make_portable.bat`, `dist/make_installer.bat`, `dist/setup.nsi` | Contract / Observed | x64/x86 staging, portable ZIP 3종, vendored NSIS installer |
| 개발 환경 문서 | `README` | Intended / Observed | 실제 build evidence와 함께 해석 |
| 제품 빌드 CI | `.github/workflows/windows-build.yml` | Contract / Evidence | automatic trigger 중지; explicit `run_ci`에서 Release x64 build/warning/artifact/x64 smoke만 기본 실행, `run_x86_compat`에서만 x86 Unicode/Multibyte compile/artifact 확인 |
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
- GitHub Actions budget 보호를 위해 2026-09-22부터 2026-09-30까지 `Source Validation`과 `Windows Product Build`의 automatic push/PR trigger를 중지했다. 수동 dispatch도 `run_ci` explicit override 없이는 job이 실행되지 않는다. Windows는 Release x64만 기본 실행하며 x86 compatibility는 추가 `run_x86_compat` 입력이 필요하다; Debug x64와 package/upload job은 Actions에서 제거했다.
- budget pause 기간에는 branch/main CI PASS를 완료 조건으로 요구하지 않는다. `local_ci.bat`을 로컬 검증 진입점으로 사용하고 실제 수행한 profile의 결과만 Evidence로 기록한다. 수행하지 않은 compile/runtime/package/visual 검증은 `NOT TESTED`로 남긴다. 검증 스크립트는 삭제하지 않고 재개 시점까지 보존한다.
- `local_ci.bat`은 redirected Python stdout을 UTF-8로 강제한다. Windows ANSI code page가 CP949 등일 때 policy/readiness/conformance 출력의 Unicode 문장부호로 `UnicodeEncodeError`가 발생하지 않도록 하기 위한 로컬 검증 contract다.
- 로컬 CI의 영구 로그는 `logs/local-ci/local-ci.log` 하나만 사용한다. 실행 시작 시 이전 local CI `.log`를 정리하고 단계별 임시 capture 파일은 종료 시 삭제한다. 간단한 프로필 사용법은 루트 `LOCAL_CI_MANUAL.txt`를 Source of Truth로 둔다.
- 로컬 C++ CI profile(`x64`, `x86`, `release`, `full`)은 MSBuild `Rebuild`를 사용해 stale `obj`/CRT configuration 재사용을 방지한다. file logger는 normal verbosity로 실제 `.cpp` compile 내역을 남기며, localized MSBuild output은 Windows ANSI code page에서 BOM-less UTF-8로 변환한 뒤 통합 `local-ci.log`와 콘솔에 출력한다.
- policy conformance의 `distribution-duplicate-entry` negative fixture는 같은 ZIP entry를 의도적으로 두 번 생성한다. 로컬 CI는 이 검증을 유지하면서 Python `zipfile`의 expected duplicate-name warning만 국소적으로 숨긴다. `dist/copy.bat`은 staging `bin`이 존재할 때만 삭제해 정상 package build에서 불필요한 `The system cannot find the file specified.` 메시지를 내지 않는다.
- `.agent-policy/PROJECT.md`의 `reviewed_at`은 validator의 UTC date 기준으로 기록한다. 한국 등 UTC+ 시차 지역의 로컬 날짜를 그대로 기록하면 UTC 자정 전에는 미래 날짜로 판정될 수 있다.
- 로컬 runtime smoke는 기존 `HKCU\...\Run`의 flyExplorer startup 값이나 `HKCU\Software\fxfile` profile data를 발견하면 해당 사용자 상태를 수정하지 않고 exit code 3으로 skip한다. `local_ci.bat`은 이를 `PASS_WITH_SKIPS`로 기록하고 runtime evidence를 `NOT TESTED`로 남기며 나머지 build/package 검증을 계속한다. GitHub-hosted smoke는 이 opt-in skip switch를 사용하지 않아 기존 strict failure contract를 유지한다.
- 현재 slimmed Windows Product Build는 기본적으로 `Release-x64-Unicode | x64`만 compile/link하고 warning, 핵심 산출물, hosted x64 launch smoke를 검증한다. x86 Unicode/Multibyte는 명시적 `run_x86_compat` 입력에서만 compile/link와 핵심 산출물을 확인한다. Debug x64와 package build/upload는 Actions에서 제거했다.
- x86 Unicode는 `libxprw.dll/.lib`, x86 Multibyte는 `libxpr.dll/.lib` 계약을 유지한다. `fxfile-upchecker`는 Unicode/x64 Build Solution에서 제외되고 x86 Multibyte에서 빌드된다. Actions의 optional x86 compatibility job은 두 구성의 compile/link와 핵심 updater 산출물만 확인하며 x86 hosted launch smoke는 더 이상 실행하지 않는다.
- xpr의 logical target 이름은 `xpr`로 유지하면서 generated MSBuild `TargetName`을 configuration별 physical product 이름(`libxprw` / `libxpr` 계열)과 정렬해 MSB8012를 제거했다.
- crash module은 vendored zlib 1.2.3 source를 현재 MSVC로 직접 빌드하며 legacy `zlibS-x64.lib`를 링크하지 않는다.
- crash/network resolver 경로는 deprecated `gethostbyname`/`inet_ntoa`/`inet_addr` 대신 modern Winsock address API를 사용한다.
- distribution 입력 이름은 현재 제품 계약에 맞춰 Unicode/x64 `libxprw.dll`과 `upchecker/fxfile-upchecker.exe`를 사용한다. Actions의 package job과 artifact upload는 비용 절감을 위해 제거했으며, release packaging은 로컬에서 `dist/package.bat`과 `build/validate_package.ps1`로 수행한다.
- 패키징은 vendored `dist/7zip/7za.exe`와 `dist/nsis/makensis.exe`를 사용하며 외부 NSIS 다운로드를 요구하지 않는다. Actions package upload는 제거되어 현재 installer/portable 결과는 로컬 `dist/`에서 생성·검증하며, 필요 시 별도 release 절차에서 보존한다.
- installer 실제 설치/제거, shell integration install/remove, clean Windows Sandbox/VM install은 아직 자동화하지 않으며 Package Build/Payload PASS와 구분한다.
- GitHub-hosted Windows runner의 기본 remote runtime evidence는 x64 Unicode launch smoke 하나만 유지한다. smoke는 staged runtime을 임시 디렉터리에 복사하고 isolated `--conf_dir`로 `fxfile.exe`를 시작한 뒤 top-level main window와 short stability window를 확인한다. x86 launch smoke는 Actions 비용 절감을 위해 제거했다.
- hosted runner에는 Visual Studio와 여러 system runtime이 이미 설치되어 있으므로 이 결과는 clean Windows Sandbox/VM evidence가 아니다. Windows Sandbox/clean VM, interactive functional smoke, visual regression은 아직 자동화하지 않는다.
- `build/validate_source_invariants.py`가 C++ cross-cutting dependency와 ModernUI integration의 빠른 static preflight를 제공한다.
- `.agent-policy/`에는 upstream `universal-agent-docs` revision `cc250a63994f1d9d4fcfdbb2bab9b622230bf8c6`의 validated policy bundle을 vendor한다. GitHub Actions의 Source Validation은 현재 source invariant만 실행하고, bundle/readiness/conformance 전체 검증은 `local_ci.bat policy` 또는 `local_ci.bat full`에서 수행한다.
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
- ModernUI는 documented `SetWindowTheme`를 `uxtheme.dll`에서 동적으로 해석해 common control에 Windows Explorer visual-style association을 적용하고 High Contrast에서는 association을 제거하는 `applyExplorerControlTheme` helper를 제공한다. explicit theme disable은 `resetControlTheme`가 소유하며, ListCtrlEx/TreeCtrlEx의 기존 `enableVistaEnhanced` enable/disable semantics는 유지한 채 direct `SetWindowTheme` 호출을 이 helper pair로 이관했다.
- Explorer list/tree theme migration은 source-invariant, Debug/Release x64, x86 Unicode/Multibyte compile/link, warning 0, hosted launch smoke, package regression을 통과했다. 실제 light/dark/High Contrast visual과 interactive list/tree behavior는 아직 수동 검증하지 않았다.
- MainFrame은 settings/theme change에서 top-level frame theme를 재적용하고 child 전체를 redraw하며, MenuBar는 `WM_THEMECHANGED`에서 theme handle을 다시 열고 ToolBarEx는 DPI/settings/theme change에서 modern metrics를 갱신한다. rebar MenuBar/ToolBarEx의 `SetWindowThemeXP(..., L"", L"")`는 WinXP 전용 legacy empty-theme association으로 Explorer sub-app theme와 의미가 달라 그대로 유지했다.
- ListCtrlEx/TreeCtrlEx의 direct common-control call-site 이관은 완료되었다.
- Explorer file list/header dark-styling 단위에서 ModernUI ThemePalette는 Windows Runtime UISettings의 documented foreground/background color signal을 사용해 사용자 app light/dark preference를 반영한다. High Contrast에서는 기존 system-color palette를 유지하고, WinRT activation/color query가 실패하면 기존 system-color 기반 palette로 fallback한다.
- ExplorerCtrl의 thumbnail/custom-draw 경로는 selection, inactive selection, surface, border, text를 ThemePalette에서 가져오며, image-list background는 실제 list background와 동기화한다. FlatHeaderCtrl은 기존 ThemePalette custom draw를 유지해 list/header가 동일 palette contract를 공유한다.
- Explorer file list/header dark-styling은 source-invariant, Debug/Release x64, x86 Unicode/Multibyte compile/link, warning rejection, hosted launch smoke, package regression을 branch CI에서 통과했다. 실제 Windows light/dark 전환 visual, selection/focus contrast, High Contrast visual, 100/125/150/200% DPI visual은 아직 수동 검증하지 않았다.
- file list/header dark-specific styling은 완료되었다. folder tree dark styling, AddressBar/edit/combo dark styling, auxiliary common controls, menu/rebar dark rendering, 나머지 dialog/icon asset 현대화는 후속 phase 범위다.

## Recommended verification

0. `local_ci.bat x64` (일상적인 기본 로컬 CI)
1. 더 좁은 static 확인은 `local_ci.bat quick`; 릴리스 준비는 `local_ci.bat release`; 전체 회귀는 `local_ci.bat full`
2. `python build/validate_source_invariants.py`
3. `build.bat`
4. 새로 생성된 `fxfile.sln`을 Visual Studio 2026에서 열기
5. `Release-x64-Unicode | x64` Build Solution
6. `build.bat 2026 x86` 후 `Release-x86-Unicode | Win32` 및 `Release-x86-Multibyte | Win32` Build Solution
7. x64/x86 제품 산출물과 x86 Multibyte `fxfile-upchecker` 산출물 확인
8. `build/runtime_smoke.ps1` 또는 GitHub Actions hosted-runner launch smoke 결과 확인
9. `dist/package.bat`으로 portable ZIP 3종과 NSIS installer 생성
10. `build/validate_package.ps1 -DistDir dist`로 package payload 검증
11. **2026-09-30까지는 GitHub Actions를 실행하지 않는다.** pause 해제 후에만 Windows Product Build와 로컬 evidence를 비교
12. Windows Sandbox 또는 clean VM에서 clean install/runtime smoke test
13. interactive 기능 및 UI 변경이면 visual 결과를 별도로 확인

## Maintenance

build command, toolchain, component architecture, generated-file 규칙, packaging 구조가 바뀌면 이 문서와 root `AGENTS.md`를 함께 갱신한다.
실제 코드/빌드 evidence와 충돌하면 이 문서를 무조건 믿지 말고 evidence를 다시 확인한다.
