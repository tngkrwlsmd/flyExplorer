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
    "reviewed_revision": "c20192916fba7af536411810defc6ac2439b28fa",
    "reviewed_at": "2026-09-22",
    "reviewed_paths": [
      "AGENTS.md",
      "README",
      "LOCAL_CI_MANUAL.txt",
      "build.bat",
      "local_ci.bat",
      "build/common.gypi",
      "build/fix_solution_configs.py",
      "build/validate_source_invariants.py",
      ".github/workflows/policy-validation.yml",
      ".github/workflows/windows-build.yml",
      "build/runtime_smoke.ps1",
      "build/installer_smoke.ps1",
      "build/validate_package.ps1",
      "dist/package.bat",
      "dist/copy.bat",
      "dist/make_portable.bat",
      "dist/make_installer.bat",
      "dist/setup.nsi",
      "fxfile.gyp",
      "src/base",
      "src/fxfile",
      "src/fxfile-tests",
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
| 로컬 CI orchestration | `local_ci.bat`, `LOCAL_CI_MANUAL.txt` | Contract / Evidence | quick/test/install/policy/x64/x86/release/full profiles; 실행 로그는 `logs/local-ci/local-ci.log` 하나로 통합, manual은 실행/skip 계약 제공 |
| 프로그램 구현 | `src/` | Observed | C++/MFC |
| third-party | `lib/`, `CREDITS` | Contract / Observed | ABI/license 검토 필요 |
| 패키징 | `dist/package.bat`, `dist/copy.bat`, `dist/make_portable.bat`, `dist/make_installer.bat`, `dist/setup.nsi` | Contract / Observed | x64/x86 staging, portable ZIP 3종, vendored NSIS installer |
| 개발 환경 문서 | `README` | Intended / Observed | 실제 build evidence와 함께 해석 |
| 제품 빌드 CI | `.github/workflows/windows-build.yml` | Contract / Evidence | automatic trigger 중지; explicit `run_ci`에서 Release x64 build/warning/artifact/native functional regression/x64 smoke 실행, `run_x86_compat`에서 x86 Unicode/Multibyte compile/artifact/native functional regression 추가 |
| native functional regression | `src/fxfile-tests/fxfile-tests.gyp`, `src/fxfile-tests/*.cpp` | Contract / Evidence | OS temp fixture에서 xpr FileSys/FileIo/SHFileOperation, rename transform, fnmatch/FilePath, UTF-8 ConfFileEx persistence, updater version/metadata/command quoting, CRC32/MD5, ShellRegistry command/key contract 검증 |
| runtime smoke | `build/runtime_smoke.ps1` | Contract / Evidence | 임시 staged runtime + isolated conf_dir에서 process/main-window/stability 검증 |
| installer smoke | `build/installer_smoke.ps1`, `dist/setup.nsi` | Contract / Evidence | 기본 safety-contract inspection; elevated + FXFILE_INSTALLER_SMOKE=1에서 temp install/runtime/uninstall, main/upchecker architecture, protected Registry/shortcut/startup/profile snapshot 비변경, 기존 fxfile process/sibling sentinel 보존 검증 |
| package validation | `build/validate_package.ps1` | Contract / Evidence | staging/portable payload, main/upchecker PE architecture, XPR runtime/architecture staging, stale updater, ZIP traversal/duplicate/casing/development-artifact, installer output + installer-smoke wiring 검증 |
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
- native product functional regression suite가 존재한다. `src/fxfile-tests/fxfile-tests.gyp`의 executable은 production xpr FileSys/FileIo, SHFileOperation seam, CRC32/MD5, ShellRegistry command/key core를 직접 사용하고 fixture는 OS temp 아래에서 생성/정리한다.
- GitHub Actions budget 보호를 위해 2026-09-22부터 2026-09-30까지 `Source Validation`과 `Windows Product Build`의 automatic push/PR trigger를 중지했다. 수동 dispatch도 `run_ci` explicit override 없이는 job이 실행되지 않는다. Windows는 Release x64만 기본 실행하며 x86 compatibility는 추가 `run_x86_compat` 입력이 필요하다; Debug x64와 package/upload job은 Actions에서 제거했다.
- budget pause 기간에는 branch/main CI PASS를 완료 조건으로 요구하지 않는다. `local_ci.bat`을 로컬 검증 진입점으로 사용하고 실제 수행한 profile의 결과만 Evidence로 기록한다. 수행하지 않은 compile/runtime/package/visual 검증은 `NOT TESTED`로 남긴다. 검증 스크립트는 삭제하지 않고 재개 시점까지 보존한다.
- `local_ci.bat`은 redirected Python stdout을 UTF-8로 강제한다. Windows ANSI code page가 CP949 등일 때 policy/readiness/conformance 출력의 Unicode 문장부호로 `UnicodeEncodeError`가 발생하지 않도록 하기 위한 로컬 검증 contract다.
- 로컬 CI의 영구 로그는 `logs/local-ci/local-ci.log` 하나만 사용한다. 실행 시작 시 이전 local CI `.log`를 정리하고 단계별 임시 capture 파일은 종료 시 삭제한다. 간단한 프로필 사용법은 루트 `LOCAL_CI_MANUAL.txt`를 Source of Truth로 둔다.
- 로컬 C++ CI profile(`x64`, `x86`, `release`, `full`)은 MSBuild `Rebuild`를 사용해 stale `obj`/CRT configuration 재사용을 방지한다. console은 MSBuild minimal verbosity를 사용해 Visual Studio 일반 빌드처럼 `.cpp` 파일명과 핵심 결과만 표시한다. file logger는 normal verbosity를 유지하며 localized MSBuild output은 Windows ANSI code page에서 BOM-less UTF-8로 변환한 뒤 통합 `local-ci.log`에 저장한다.
- policy conformance의 `distribution-duplicate-entry` negative fixture는 같은 ZIP entry를 의도적으로 두 번 생성한다. 로컬 CI는 이 검증을 유지하면서 Python `zipfile`의 expected duplicate-name warning만 국소적으로 숨긴다. `dist/copy.bat`은 staging `bin`이 존재할 때만 삭제해 정상 package build에서 불필요한 `The system cannot find the file specified.` 메시지를 내지 않는다.
- `.agent-policy/PROJECT.md`의 `reviewed_at`은 validator의 UTC date 기준으로 기록한다. 한국 등 UTC+ 시차 지역의 로컬 날짜를 그대로 기록하면 UTC 자정 전에는 미래 날짜로 판정될 수 있다.
- 로컬 runtime smoke는 기존 `HKCU\...\Run`의 flyExplorer startup 값이나 `HKCU\Software\fxfile` profile data를 발견하면 해당 사용자 상태를 수정하지 않고 exit code 3으로 skip한다. `local_ci.bat`은 이를 `PASS_WITH_SKIPS`로 기록하고 runtime evidence를 `NOT TESTED`로 남기며 나머지 build/package 검증을 계속한다. GitHub-hosted smoke는 이 opt-in skip switch를 사용하지 않아 기존 strict failure contract를 유지한다.
- 현재 slimmed Windows Product Build는 기본적으로 `Release-x64-Unicode | x64` compile/link, warning, 핵심 산출물, native functional regression, hosted x64 launch smoke를 검증한다. x86 Unicode/Multibyte는 명시적 `run_x86_compat` 입력에서 compile/link, 핵심 산출물, native functional regression을 추가한다. Debug x64와 package build/upload는 Actions에서 제거했다.
- x86 Unicode는 `libxprw.dll/.lib`, x86 Multibyte는 `libxpr.dll/.lib` 계약을 유지한다. `fxfile-upchecker`는 Unicode/x64 Build Solution에서 제외되고 x86 Multibyte에서 빌드된다. Actions의 optional x86 compatibility job은 두 구성의 compile/link와 핵심 updater 산출물만 확인하며 x86 hosted launch smoke는 더 이상 실행하지 않는다.
- xpr의 logical target 이름은 `xpr`로 유지하면서 generated MSBuild `TargetName`을 configuration별 physical product 이름(`libxprw` / `libxpr` 계열)과 정렬해 MSB8012를 제거했다.
- crash module은 vendored zlib 1.2.3 source를 현재 MSVC로 직접 빌드하며 legacy `zlibS-x64.lib`를 링크하지 않는다.
- crash/network resolver 경로는 deprecated `gethostbyname`/`inet_ntoa`/`inet_addr` 대신 modern Winsock address API를 사용한다.
- distribution 입력 이름은 현재 제품 계약에 맞춰 Unicode/x64 `libxprw.dll`과 `upchecker/fxfile-upchecker.exe`를 사용한다. Actions의 package job과 artifact upload는 비용 절감을 위해 제거했으며, release packaging은 로컬에서 `dist/package.bat`과 `build/validate_package.ps1`로 수행한다.
- 패키징은 vendored `dist/7zip/7za.exe`와 `dist/nsis/makensis.exe`를 사용하며 외부 NSIS 다운로드를 요구하지 않는다. Actions package upload는 제거되어 현재 installer/portable 결과는 로컬 `dist/`에서 생성·검증하며, 필요 시 별도 release 절차에서 보존한다.
- installer는 `/FXFILE_SMOKE=<temp-dir>` 격리 mode와 `build/installer_smoke.ps1`을 갖는다. 기본 `local_ci.bat install`은 생성 installer 없이도 source safety-contract inspection을 수행한 뒤 actual install을 SKIP한다. 관리자 권한 + `FXFILE_INSTALLER_SMOKE=1` opt-in에서는 temp install/runtime/uninstall과 selected Registry/shell/startup snapshot 비변경을 자동 검증한다. 이 smoke는 실제 제품 Registry/Start Menu/Desktop/shell-context registration을 의도적으로 수행하지 않으므로 clean Windows Sandbox/VM의 real install/uninstall/shell integration evidence와 구분한다.
- GitHub-hosted Windows runner의 기본 remote runtime evidence는 x64 Unicode launch smoke 하나만 유지한다. smoke는 staged runtime을 임시 디렉터리에 복사하고 isolated `--conf_dir`로 `fxfile.exe`를 시작한 뒤 top-level main window와 short stability window를 확인한다. x86 launch smoke는 Actions 비용 절감을 위해 제거했다.
- hosted runner에는 Visual Studio와 여러 system runtime이 이미 설치되어 있으므로 이 결과는 clean Windows Sandbox/VM evidence가 아니다. Windows Sandbox/clean VM, interactive functional smoke, visual regression은 아직 자동화하지 않는다.
- `build/validate_source_invariants.py`가 C++ cross-cutting dependency와 ModernUI integration의 빠른 static preflight를 제공하며, 알려진 product regression도 함께 차단한다. 현재 ToolbarWindow32에 존재하지 않는 `TB_SETBKCOLOR`/`TB_SETTEXTCOLOR` 재도입을 거부하고 `NM_CUSTOMDRAW`/`NMTBCUSTOMDRAW` 기반 dark-state color wiring이 유지되는지 검사한다.
- `.agent-policy/`에는 upstream `universal-agent-docs` revision `cc250a63994f1d9d4fcfdbb2bab9b622230bf8c6`의 validated policy bundle을 vendor한다. GitHub Actions의 Source Validation은 source invariant + known regression preflight만 실행하도록 유지하며, bundle/readiness/conformance 전체 검증은 `local_ci.bat policy` 또는 `local_ci.bat full`에서 수행한다. 2026-09-30까지 Actions 자동 trigger는 계속 중지되어 있고 수동 실행도 explicit budget override 없이는 실행하지 않는다.
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
- file list/header dark-specific styling은 완료되었다.
- Folder Tree 1-D2 dark-specific styling을 완료했다. TreeCtrlEx는 기존 enableVistaEnhanced semantics를 유지하면서 theme/High Contrast 전환 때 Explorer association을 재적용하는 generic refresh helper를 제공한다. FolderCtrl은 기존 NM_CUSTOMDRAW ownership을 유지하고 dark mode에서만 ThemePalette의 mSelection/mSelectionText/mHover/mText로 focused selection, inactive selection, hot/default item colors를 보정한다. Light와 High Contrast는 native TreeView state rendering을 유지하며 glyph, tree line geometry, keyboard focus rectangle은 custom drawing하지 않는다.
- FolderCtrl은 High Contrast 동안 background/text/line을 system palette/CLR_DEFAULT로 강제하고 HC 해제 후 기존 custom folder-tree color 설정으로 복귀한다. 기존 inactive-highlight user option은 Light/Dark에서 유지하고 High Contrast에서는 custom outline을 억제한다.
- Folder Tree image-list background는 attach 시점과 theme/settings refresh 시 실제 TreeView background와 동기화하며, focus gain/loss 시 selected row를 다시 그려 focused/unfocused dark selection 상태가 즉시 갱신되도록 했다. theme/settings/system-color/DPI 변경은 existing applyModernAppearance 경로에서 theme association -> palette/color/metrics -> image-list -> redraw 순서로 갱신된다.
- 1-D2 변경 범위 정적 대조는 PASS: 변경 파일은 src/fxfile/gui/TreeCtrlEx.h/.cpp와 src/fxfile/folder_ctrl.cpp뿐이며 ModernUI direct include/helper contract, direct SetWindowTheme 금지, native glyph preservation, image-list sync, theme/settings/DPI refresh tokens를 확인했다. 이 실행 환경은 Windows/MSVC와 repository clone network가 없어 local_ci.bat quick 및 local_ci.bat x64는 실행하지 못했으므로 NOT TESTED다.
- 1-D2 실제 Windows visual/interactive 검증은 NOT TESTED: Light/Dark/High Contrast, 100/125/150/200% DPI, focused/unfocused selection, hover, native expand/collapse glyph, tree line, icon halo, rename/navigation/drag-drop/context-menu 동작을 실제 화면에서 확인해야 한다.
- 1-D3 AddressBar/Edit/Combo dark-specific styling을 완료했다. AddressBar는 기존 CComboBoxEx + child ComboBox/Edit + native drop-down ListBox 구조와 기존 CBS_OWNERDRAWFIXED 계약을 유지하며, 새로운 owner-draw/custom Edit로 교체하지 않았다.
- AddressBar는 child ComboBox를 SetWindowSubclass로 관찰하고 dark/non-HC에서 WM_CTLCOLOREDIT / WM_CTLCOLORLISTBOX / WM_CTLCOLORSTATIC의 text/background를 ThemePalette mText/mSecondaryText/mWindow와 재사용 CBrush로 공급한다. text selection, caret, focus cue, drop-down button/arrow는 Windows native rendering에 맡긴다.
- AddressBar/ComboBox/Edit/ListBox에는 ModernUI::applyExplorerControlTheme를 재적용하며 drop-down ListBox는 CBN_DROPDOWN 시 COMBOBOXINFO로 다시 조회해 lazily created HWND에도 theme association을 갱신한다. Light/High Contrast는 custom brush/color 경로를 사용하지 않고 native/system rendering으로 fallback한다.
- AddressBar는 기존 system UI font, child font synchronization, font/icon 기반 item-height 계산, SHAutoComplete, Enter/Tab/Escape navigation 경로를 유지한다. WM_SETTINGCHANGE / WM_SYSCOLORCHANGE / WM_THEMECHANGED / WM_DPICHANGED에서 theme/color/font/metric/redraw를 갱신한다.
- 1-D3 정적 범위 검토는 PASS: 구현 변경은 src/fxfile/address_bar.h/.cpp에 한정되고 ModernUI direct include, existing owner-draw preservation, native arrow/focus handling, High Contrast fallback, child HWND refresh, autocomplete/font/DPI contract 보존을 확인했다. build/validate_source_invariants.py 및 ModernUI palette 구조는 변경하지 않았다.
- 이 실행 환경에서는 Windows/MSVC local_ci.bat quick 및 local_ci.bat x64를 실행하지 못했으므로 둘 다 NOT TESTED다. 실제 Windows Light/Dark/High Contrast, 100/125/150/200% DPI, focused/unfocused, edit selection/caret, drop-down selected item/arrow, Korean IME, autocomplete, Enter/path navigation은 NOT TESTED다.
- auxiliary common controls inventory를 정리했다. main explorer shell에서 TabCtrl은 이미 ThemePalette 기반 selected/hover/background/separator rendering과 settings/theme/DPI refresh를 갖고 있어 재작업하지 않았고, PathBar 계열도 별도 대규모 recolor 대상으로 잡지 않았다. dialog 전용 CButton/CStatic/CProgressCtrl/CListBox/CComboBox/CEdit 등은 broader dialog modernization 범위로 남겼다.
- 이번 auxiliary dark styling의 실제 수정 대상은 main ExplorerView의 ActivateBar와 optional ContentsWnd 정보 영역(ContentsWnd + BookmarkSetWnd + BookmarkWnd)이다. MenuBar/Rebar/Toolbar, File List/Header, Folder Tree, AddressBar, StatusBar는 수정하지 않았다.
- ActivateBar는 기존 custom paint ownership과 사용자 active-pane color 설정을 유지하면서 ThemePalette의 window/surface를 inactive/last-active 배경 계산에 사용한다. High Contrast에서는 사용자 색을 강제하지 않고 mSelection/mSurface/mWindow system-derived palette로 fallback하며 WM_SETTINGCHANGE / WM_SYSCOLORCHANGE / WM_THEMECHANGED에서 즉시 갱신한다.
- ContentsWnd는 기존 custom paint ownership을 유지하고 hard-coded white/gray/black surface, infotip, icon-box, drive-space legend/progress 색을 ThemePalette mWindow/mSurface/mText/mBorder/mSeparator로 교체했다. High Contrast infotip text/background는 COLOR_INFOTEXT/COLOR_INFOBK를 유지한다. BookmarkSetWnd 배경은 ThemePalette mWindow로 전환하고 documented Explorer theme helper를 settings/syscolor/theme refresh 때 재적용한다.
- BookmarkWnd는 기존 CStatic + WM_CTLCOLOR_REFLECT 동작을 유지하고 WHITE_BRUSH를 제거했다. ThemePalette mWindow 기반 reusable CBrush를 멤버로 관리하여 paint/message마다 GDI brush를 생성하지 않으며, High Contrast에서는 bookmark custom text color 대신 system-derived palette text를 사용한다. Tooltip theme association도 기존 ModernUI helper로 갱신한다.
- auxiliary 구현 정적 범위 검토는 PASS: 변경 파일은 activate_bar.h/.cpp, contents_wnd.h/.cpp, bookmark_set_wnd.h/.cpp, bookmark_wnd.h/.cpp뿐이며 generated project, MenuBar/Rebar/Toolbar, TabCtrl, source invariant, ModernUI palette 구조는 변경하지 않았다. 새 ModernUI 사용 cpp는 모두 ModernUI.h를 직접 include하며 hard-coded RGB(255,255,255)/WHITE_BRUSH light-only 경로 제거, theme/syscolor/settings handlers, High Contrast fallback, reusable bookmark brush를 확인했다.
- 이 실행 환경에서는 Windows/MSVC local_ci.bat quick 및 local_ci.bat x64를 실행하지 못했으므로 둘 다 NOT TESTED다. 실제 Windows Light/Dark/High Contrast, 100/125/150/200% DPI, ActivateBar active/last-active 상태, ContentsWnd infotip/drive-space/bookmark rendering, native scrollbar/tooltip, mouse/keyboard/scroll/bookmark interaction은 NOT TESTED다.
- MenuBar / Rebar / Toolbar dark rendering을 완료했다. CMenuBar는 기존 CToolBar + NM_CUSTOMDRAW ownership을 유지하고 dark/non-HC에서 normal/disabled/hot/selected text/background를 ThemePalette mText/mSecondaryText/mHover/mSelection/mSelectionText로 보정한다. 기존 system-menu icon, MDI caption-button 동작, keyboard/menu tracking은 변경하지 않았다.
- CToolBarEx는 기존 native ToolbarWindow32 구조, image-list/button command semantics, DPI/system-font metrics를 유지하면서 reflected NM_CUSTOMDRAW를 추가했다. dark/non-HC에서 normal/disabled/hot/selected/checked 상태 색상은 NMTBCUSTOMDRAW의 clrBtnFace/clrText/clrHighlightHotTrack으로 처리하며 Light/High Contrast는 default/native path를 유지한다. toolbar 및 tooltip HWND에는 documented ModernUI Explorer theme helper를 재적용한다. Toolbar control에 존재하지 않는 TB_SETBKCOLOR/TB_SETTEXTCOLOR 사용은 제거했다.
- CToolBarPopup chevron menu도 동일 toolbar palette contract를 사용한다. exact Windows XP에서만 기존 SetWindowThemeXP(..., L"", L"") legacy path를 유지하고 그 외에는 ModernUI helper를 사용한다. popup border는 dark에서 mBorder, High Contrast에서는 COLOR_3DSHADOW를 사용한다.
- CSizableReBar는 FrameWndEx menu rebar와 MainCoolBar toolbar rebar가 공유하는 실제 host이므로 공통 dark styling ownership을 맡는다. internal CReBarCtrl에 documented Explorer association을 적용하고 RB_SETBKCOLOR/RB_SETTEXTCOLOR를 ThemePalette/System color로 갱신하며, dark non-client sizing edge는 mBorder로 그린다. WM_SETTINGCHANGE / WM_SYSCOLORCHANGE / WM_THEMECHANGED에서 즉시 refresh한다.
- BCMenu owner-draw popup의 실제 활성 경로인 Windows8/Standard style만 ThemePalette-aware하게 변경했다. dark/non-HC에서 background/separator/normal text/disabled text/selection을 mSurface/mSeparator/mText/mSecondaryText/mSelection/mSelectionText로 처리하며 Light/High Contrast는 기존 system-color 경로를 유지한다. 사용되지 않는 legacy Office/Vista drawing path는 건드리지 않았다.
- Menu/Rebar/Toolbar 구현 정적 범위 검토는 PASS: 변경 파일은 gui/rebar/MenuBar.h/.cpp, ToolBarEx.h/.cpp, SizableReBar.h/.cpp, gui/BCMenu.cpp에 한정되고 각 ModernUI 사용 translation unit의 direct include, handler declaration/definition/message-map 일치, toolbar/popup/rebar High Contrast fallback, active BCMenu draw path와 dark separator를 확인했다. generated project, ModernUI palette 구조, build/validate_source_invariants.py는 변경하지 않았다.
- 2026-09-22 사용자 로컬 full CI에서 발견된 ToolBarEx.cpp의 `TB_SETBKCOLOR`/`TB_SETTEXTCOLOR` C2065 compile regression은 제거되었고, 동일 식별자 재도입과 toolbar custom-draw wiring 손실을 `build/validate_source_invariants.py`가 정적으로 차단하도록 보강했다. 이후 업로드된 full 로그는 수정 전 Toolbar 소스를 계속 컴파일한 stale local checkout 결과였으므로 현재 `main`의 post-fix compile/runtime/package PASS evidence로 사용하지 않는다. 현재 `main`에 대한 fresh Windows `local_ci.bat x64`/`full`은 아직 NOT TESTED이며, 실제 Windows visual/interactive evidence도 별도다.
- broader dialog modernization의 공통 기반을 완료했다. CResizingDialog는 검색/히스토리/드라이브/파일 작업/CRC/배치/동기화 등 다수 modeless/resizable command dialog가 공유하는 base로서 system UI font, ThemePalette surface/window background, WM_CTLCOLOR 기반 edit/list/static/button 색 보정, documented Explorer common-control association, settings/syscolor/theme/DPI refresh를 공통 제공한다. Light/High Contrast는 native/system rendering으로 fallback하며 기존 resize/layout, command routing, per-dialog custom font를 보존한다.
- TitleDlg 기반(create/rename/shortcut/file-list 계열)은 기존 custom header ownership을 유지하면서 header background/text/separator를 ThemePalette로 전환하고 32 logical-pixel description icon을 current-DPI 크기로 로드/그린다. resource-ID icon은 HWND 생성 이후 ModernUI::loadIconResource로 로드하고 DPI 변경 시 다시 로드하며, caller가 전달한 shell/external HICON은 기존 ownership 계약을 유지한다.
- 설정 UI는 CfgDlg 공통 page base와 CfgMainDlg host를 현대화했다. 약 30개의 CfgDlg-derived page는 공통 system font/dark surface/edit-list color/theme refresh를 상속하고, CfgMainDlg는 window-frame theme, palette-backed host surface, config TreeCtrl background/text/line 및 image-list background를 갱신한다. 기존 config tree 구조, apply/default semantics, dynamically-created page lifecycle은 변경하지 않았다.
- ModernUI::applyWindowFrameTheme는 이제 실제 ThemePalette mDark 값을 따라 DWMWA_USE_IMMERSIVE_DARK_MODE를 true/false로 설정하여 Light mode에서 dark title bar를 강제하지 않는다. ModernUI::loadIconResource는 logical icon size를 current window DPI로 scale해서 LoadImage(IMAGE_ICON)로 로드하는 공통 helper다.
- 기존 IDR_MAINFRAME title icon을 소유하던 CResizingDialog 계열 18개 command dialog는 constructor-time LoadIcon 대신 OnInitDialog 시점의 DPI-aware ModernUI::loadIconResource 경로로 전환했다. icon handle ownership/DestroyIcon 계약은 유지한다.
- icon/resource modernization은 DPI-aware loading/scaling을 유지하면서 application `fxfile.ico`의 기존 16/32/48 프레임을 보존하고 32-bit 256px 프레임을 추가했다. `tip.ico`/`shortcut.ico`는 32/40/48/64px, `goup.ico`는 기존 16/32px 변형을 보존하면서 40/48/64px 32-bit 프레임을 추가했고 ExplorerCtrl parent-folder icon도 fixed-size LoadIcon 대신 ModernUI DPI loader/scale 경로를 사용한다. main toolbar small/large hot/cold strip과 config-tree strip은 command/image index에 강하게 결합된 legacy artwork이므로 프레임 순서를 재디자인하지 않고 frame count/cell geometry/16bpp mask format/RC/GYP wiring을 source-invariant가 고정한다. 최종 artwork 미감은 automated PASS로 주장하지 않는다.
- standard non-resizing direct `CDialog` outlier modernization을 완료했다. 새 `CModernDialog` base는 system UI font, ThemePalette surface/window brush, Explorer common-control association, top-level frame theme, settings/syscolor/theme/DPI refresh를 공통 소유한다. Bookmark/Wait/About/설정 보조/선택·변환·검색/file-scrap 계열과 PictureViewer/COptionsDialog가 이 기반으로 이동했고, `CResizingDialog`, `TitleDlg`, `CfgDlg`/`CfgMainDlg`, `DriveDetailDlg`는 기존 전문 ModernUI owner로 allowlist한다. AboutDlg/TipDlg/PictureViewer의 custom paint 및 toolbar customize owner-draw는 ThemePalette/DPI 경로로 별도 보정했다.
- `build/validate_source_invariants.py`는 ModernDialog 등록/direct include/direct-CDialog allowlist, About/Tip/PictureViewer custom-paint wiring, toolbar invalid-message/custom-draw wiring, toolbar/config-tree bitmap frame geometry, app/tip/shortcut/go-up icon frame 계약과 go-up DPI loader, rename/pattern-path/config/updater native functional-test wiring, shared updater metadata/version/command core, isolated installer-smoke wiring을 검사한다. validator는 Python 3.9+ 계약을 유지한다.
- native functional regression은 filesystem/hash/shell contract에서 확장되어 batch-rename transform core, `fnmatch`/`xpr::FilePath`, UTF-8 `ConfFileEx` round-trip/default/corrupt input, updater strict version 비교/metadata parser/conf-dir+startup quoting을 production implementation으로 검증하도록 구성됐다. 이 과정에서 `ConfFile::mFlags` constructor 초기화, version compare ordering, malformed updater version 처리, updater metadata 필수 필드, conf-dir quoting, rename boundary input을 수정하고 회귀를 추가했다.
- package validation은 main executable과 모든 package의 Win32 upchecker PE machine을 확인하고 wrong XPR runtime, stale `fxfile-updater.exe`, nested architecture staging, unsafe ZIP path, duplicate/case-colliding entry, 개발 산출물 혼입을 차단한다. isolated installer smoke는 install/uninstall 전후 Registry뿐 아니라 shortcut/startup/profile snapshot, pre-existing fxfile process, sibling sentinel과 installed architecture를 보호한다.
- 이번 범위의 자동화 가능한 product functional regression, updater/release/package/installer hardening, shell-command contract, direct-dialog/DPI icon/resource regression 보강은 구현 완료했다. toolbar/config-tree strip은 기능 index를 보존하기 위해 구조를 유지하며 실제 시각 재디자인과 최종 visual acceptance는 별도 manual/design evidence로 남는다.
- 이 실행 환경에서는 Windows/MSVC `local_ci.bat quick`/`test`/`install`/`x64`/`x86`/`release`/`full`을 실제 실행하지 못했으므로 현재 `main`의 compile/link/functional/runtime/package/install evidence는 NOT TESTED다. 실제 제품 Registry shell registration, clean Windows install/uninstall, Light/Dark/High Contrast/DPI/interactive 검증도 별도 Manual / NOT TESTED evidence다.

## Recommended verification

0. `local_ci.bat x64` (일상적인 기본 로컬 CI)
1. static 확인은 `local_ci.bat quick`; product 기능만은 `local_ci.bat test`; installer contract/격리 설치는 `local_ci.bat install`; 릴리스 준비는 `local_ci.bat release`; 전체 회귀는 `local_ci.bat full`
2. `python build/validate_source_invariants.py` (source invariant + dialog/resource/DPI-icon + rename/pattern/config/updater functional + installer wiring + known regression guards)
3. `build.bat`
4. 새로 생성된 `fxfile.sln`을 Visual Studio 2026에서 열기
5. `Release-x64-Unicode | x64` Build Solution
6. `build.bat 2026 x86` 후 `Release-x86-Unicode | Win32` 및 `Release-x86-Multibyte | Win32` Build Solution
7. x64/x86 제품 산출물과 x86 Multibyte `fxfile-upchecker` 산출물 확인
8. `build/runtime_smoke.ps1` 또는 GitHub Actions hosted-runner launch smoke 결과 확인
9. `dist/package.bat`으로 portable ZIP 3종과 NSIS installer 생성
10. `build/validate_package.ps1 -DistDir dist`로 package payload + installer-smoke wiring 검증
11. `local_ci.bat install`로 installer safety contract 검사; 격리 temp install/uninstall evidence가 필요하면 elevated shell에서 `FXFILE_INSTALLER_SMOKE=1` opt-in
12. **2026-09-30까지는 GitHub Actions를 실행하지 않는다.** pause 해제 후에만 Windows Product Build와 로컬 evidence를 비교
13. Windows Sandbox 또는 clean VM에서 실제 product Registry/shell registration을 포함한 clean install/runtime/uninstall 검증
14. interactive 기능 및 UI 변경이면 visual 결과를 별도로 확인

## Maintenance

build command, toolchain, component architecture, generated-file 규칙, packaging 구조가 바뀌면 이 문서와 root `AGENTS.md`를 함께 갱신한다.
실제 코드/빌드 evidence와 충돌하면 이 문서를 무조건 믿지 말고 evidence를 다시 확인한다.
