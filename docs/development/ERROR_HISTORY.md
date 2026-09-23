# flyExplorer Error Diagnosis / Prevention History

이 문서는 확정된 오류를 단순 수정으로 끝내지 않고, 다음 진단을 빠르게 하고 같은 계열의 결함을 사전에 막기 위한 프로젝트 기록이다.

## 기록 원칙

- 새 항목은 **오류 발생 → 최초 실제 오류 → 원인 진단 → 해결 방법 → 재발 방지 → 검증 상태 → 관련 commit** 순서로 작성한다.
- compiler/linker cascade는 최초 root cause와 파생 오류를 구분한다.
- Observed fact와 inference를 섞지 않는다. 원인이 확인되지 않은 경우 `미확정`으로 남긴다.
- 해결 후 동일 command/profile을 다시 실행하지 못했으면 `NOT TESTED`라고 기록한다.
- 반복 가능성이 있으면 문서만 추가하지 말고 source invariant, regression test, build preflight 또는 contract guard 중 가능한 가장 싼 deterministic 방어선을 추가한다.
- 제품 코드 오류와 build/CI orchestration 오류를 구분한다.
- 민감정보나 불필요한 개인 경로/계정 식별정보는 기록하지 않는다.

## 새 항목 템플릿

### YYYY-MM-DD — 짧은 오류 제목

**오류 발생**
- 실행/프로필:
- 사용자에게 보인 증상:

**최초 실제 오류**
- 첫 error/warning-policy failure:
- cascade/2차 증상:

**원인 진단**
- Observed:
- Root cause:

**해결 방법**
- 수정 파일:
- 수정 내용:

**재발 방지**
- 추가한 invariant/test/preflight:
- 앞으로 같은 계열 코드를 작성할 때 지킬 규칙:

**검증 상태**
- Static:
- Compile/link:
- Runtime/visual:

**관련 commit**
- `<sha>` — `<subject>`

---

## 2026-09-22 — local CI warning-policy 진단 추출 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64`
- 사용자에게 보인 증상: solution 생성과 source preflight 이후 `ERROR: Failed to extract warning-policy diagnostics.`로 CI 종료.

**최초 실제 오류**
- 제품 C++ compile/link error가 아니라 warning-policy diagnostic extraction 단계가 실패.
- MSBuild `BUILD_RESULT=0` 이후 warning 검사 분기로 들어간 상태였다.

**원인 진단**
- Observed: `local_ci.bat`의 quoted PowerShell `-Command` 내부 pipeline이 `$lines ^| Where-Object ... ^| ForEach-Object ...` 형태였다.
- Root cause: `^|`는 cmd.exe 바깥 문맥용 escape인데 이미 큰따옴표로 감싼 PowerShell command 안에서 사용되어 PowerShell parser에 잘못된 토큰으로 전달됐다.

**해결 방법**
- 수정 파일: `local_ci.bat`
- `^|`를 raw PowerShell pipe `|`로 변경했다.
- 영구 `local-ci.log`의 error-focused 정책과 shell의 일반 MSBuild 진행 출력은 그대로 유지했다.

**재발 방지**
- `build/validate_source_invariants.py`에 `validate_local_ci_warning_policy_wiring()`을 추가했다.
- quoted PowerShell `-Command` 안에서 warning extractor가 raw `|`를 사용하는지, error-only file logger와 temporary normal logger가 유지되는지 검사한다.

**검증 상태**
- Static: PASS — raw pipe 존재, caret-pipe 부재, logger/guard wiring 확인.
- Compile/link: NOT TESTED — 수정 후 Windows x64 재실행 evidence 없음.
- Runtime/visual: 해당 없음.

**관련 commit**
- `02347ca4` — `fix: repair warning-policy diagnostic extraction`
- `2537bf5b` — `test: guard local CI warning extraction`

---

## 2026-09-22 — functional test가 fxfile-crash.h를 찾지 못함

**오류 발생**
- 실행/프로필: Release x64 functional-test build.
- 사용자에게 보인 증상: functional-test translation unit이 `src/fxfile/stdafx.h`를 거치며 `fxfile-crash.h` include를 해석하지 못함.

**최초 실제 오류**
- functional-test target의 include/dependency wiring 누락.
- 같은 빌드에서 CP949 `C4819` 경고도 별도로 관찰됐다.

**원인 진단**
- Observed: product target은 crash module include/dependency를 갖고 있었지만 functional-test target은 해당 contract를 명시하지 않았다.
- Root cause: test target이 product PCH/header contract를 사용하면서 필요한 crash dependency/include path를 직접 선언하지 않았다.

**해결 방법**
- `src/fxfile-tests/fxfile-tests.gyp`에 `fxfile-crash` dependency와 include path를 추가했다.
- `updater_contract_tests.cpp`의 한글 path fixture는 code-page 안전한 `\x` escape로 변경했다.

**재발 방지**
- source invariant에 functional-test crash dependency/include wiring을 추가했다.
- standalone test translation unit은 product target의 우연한 include/PCH 상태에 기대지 않고 필요한 dependency를 직접 선언한다.

**검증 상태**
- Static: PASS — dependency/include/fixture wiring 확인.
- Compile/link: 이후 로컬 x64 CI에서 functional regression target build PASS evidence가 확보됨.
- Runtime/visual: 해당 없음.

---

## 2026-09-22 — functional test standalone compile에서 std container와 64-bit literal 오류

**오류 발생**
- 실행/프로필: `local_ci.bat x64` functional-test compile.
- 사용자에게 보인 증상: `conf_file.h`에서 `std::list`, `std::unordered_map` 미정의와 `XPR_INT64_LITERAL` 미정의가 연쇄적으로 발생.

**최초 실제 오류**
- `conf_file.h`가 사용하는 표준 container header를 직접 include하지 않음.
- test code가 존재하지 않는 `XPR_INT64_LITERAL` macro를 사용.

**원인 진단**
- Product build에서는 PCH/transitive include가 header dependency 누락을 가리고 있었다.
- XPR의 실제 signed 64-bit literal macro는 `XPR_SINT64_LITERAL`이었다.

**해결 방법**
- `src/base/conf_file.h`에 `<list>`, `<unordered_map>` 직접 include.
- `config_persistence_tests.cpp`의 macro를 `XPR_SINT64_LITERAL(...)`로 수정.

**재발 방지**
- public/common header는 자신이 사용하는 표준 타입의 header를 직접 include한다.
- test code에서 project macro를 사용할 때 실제 소유 header/definition을 확인하고 이름을 추측하지 않는다.
- `AGENTS.md`의 compile-readiness/dependency hygiene 원칙에 direct include 규칙을 유지한다.

**검증 상태**
- Static: PASS.
- Compile/link: 이후 functional-test build가 다음 단계까지 진행한 evidence가 확보됨.
- Runtime/visual: 해당 없음.

**관련 commit**
- `141424e7` — `fix: declare config container dependencies`
- `bbcf20a5` — `fix: use signed 64-bit XPR literal macro`

---

## 2026-09-22 — rename regression preflight의 qualified token 누락

**오류 발생**
- 실행/프로필: source invariant/regression preflight.
- 사용자에게 보인 증상: `functional_tests.cpp: missing regression token rename_core::splitBaseFileNameAndExt`.

**최초 실제 오류**
- 동작 테스트는 존재했지만 validator가 요구하는 qualified regression token이 source text에 없었다.

**원인 진단**
- 테스트가 `using namespace fxfile::cmd::rename_core;` 뒤 unqualified `splitBaseFileNameAndExt(...)`를 사용했다.
- static validator는 literal qualified token을 contract로 검사했다.

**해결 방법**
- 세 호출을 `fxfile::cmd::rename_core::splitBaseFileNameAndExt(...)`로 명시적으로 qualified 했다.

**재발 방지**
- static token guard가 의도된 contract라면 테스트 source도 해당 ownership이 명확히 보이도록 qualified symbol을 사용한다.
- 반대로 token guard가 지나치게 brittle한 경우에는 parser/behavior 기반 guard로 개선할지 검토한다.

**검증 상태**
- Static: 이후 source invariant preflight PASS.
- Compile/link: 해당 수정 자체는 behavior change 없음.

**관련 commit**
- `57c3db81` — `test: qualify rename core regression calls`

---

## 2026-09-22 — BCMenu popup width의 signed/unsigned warning-policy 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: Release x64 build가 warning-policy 단계에서 `BCMenu.cpp(1345,24): warning C4018`로 FAIL.

**최초 실제 오류**
- `MEASUREITEMSTRUCT::itemWidth`(`UINT`, unsigned)와 `ModernUI::scaleForWindow(...)`(`xpr_sint_t`, signed)을 `min()`에서 직접 비교했다.
- 같은 warning이 로그에 두 번 보였지만 하나의 root cause가 중복 출력된 것이며 독립 오류 두 개가 아니었다.

**원인 진단**
- Observed: `lpMIS->itemWidth = min(lpMIS->itemWidth, ModernUI::scaleForWindow(...))` 형태의 비교가 있었다.
- Root cause: Win32 구조체의 unsigned field와 내부 DPI helper의 signed 반환값을 같은 비교식에 섞어 MSVC C4018이 발생했다.
- CI는 warning을 정책 위반으로 승격하므로 compile 자체가 진행됐더라도 profile 결과는 FAIL이 된다.

**해결 방법**
- 수정 파일: `src/fxfile/gui/BCMenu.cpp`.
- DPI helper 결과를 먼저 `xpr_uint_t`로 명시적으로 정규화한 `sMaxItemWidth`를 만들고, `itemWidth`와 unsigned끼리 `min()` 비교하도록 수정했다.

**재발 방지**
- 기존 local CI warning-policy가 이 계열의 signed/unsigned mismatch를 자동으로 차단하는 가장 저렴한 방어선이므로 별도의 brittle source-token invariant는 추가하지 않는다.
- Win32/MFC 구조체의 unsigned size/count/index field와 project 내부 signed metric/helper를 `min/max/< />`에서 직접 섞지 않는다. 범위가 양수로 보장되는 값은 경계에서 명시적으로 동일 타입으로 정규화한다.
- 동일 warning이 여러 logger 경로에서 중복 출력되더라도 최초 source location과 warning code가 같으면 하나의 root cause인지 먼저 확인한다.

**검증 상태**
- Static: PASS — `itemWidth`와 최대폭이 동일한 unsigned 계열 타입으로 비교되도록 source 확인.
- Compile/link: NOT TESTED — 수정 후 Windows x64 profile 재실행 evidence 없음.
- Runtime/visual: NOT TESTED — popup menu width/visual regression은 실제 Windows 실행에서 확인 필요.

**관련 commit**
- `5c370470` — `fix: normalize popup width comparison types`

---

## 2026-09-22 — BCMenu rounded selection의 DPI window context 누락

**오류 발생**
- 작업 브랜치에서 popup selection을 rounded/DPI-aware하게 변경한 직후 static self-review 중 발견.
- 잠재 증상: `BCMenu::drawSelection()`이 선언되지 않은 `sMetricHwnd`를 참조하여 Windows/MSVC compile 단계에서 identifier 오류가 발생할 수 있는 상태였다.

**최초 실제 오류**
- 기존 `drawIcon()`/`drawText()`의 DPI metric pattern을 `drawSelection()`으로 옮기면서 metric 계산식만 추가하고 해당 함수 scope의 HWND context 초기화를 빠뜨렸다.

**원인 진단**
- Root cause: 다른 함수의 local setup을 암묵적으로 전제한 채 DPI-aware drawing fragment를 복사/확장했다.
- renderer helper마다 DPI 기준 HWND를 자체적으로 확보한다는 ownership 규칙이 코드에 명시되어 있지 않았다.

**해결 방법**
- `BCMenu::drawSelection()` 안에서 `AfxGetMainWnd()`를 기준으로 `sMetricHwnd`를 직접 초기화하고, main window가 없으면 desktop window로 fallback하도록 수정했다.
- `getControlCornerRadius()`와 inset scaling이 모두 동일한 local HWND context를 사용하도록 정리했다.

**재발 방지**
- DPI-aware drawing code를 함수 간 이동/복제할 때 scale expression만 옮기지 말고 metric context(HWND/DPI)의 선언과 fallback까지 하나의 단위로 검토한다.
- local renderer는 caller의 local variable이나 다른 renderer의 setup을 암묵적으로 기대하지 않는다.
- Windows compile 전 static self-review에서 새 identifier의 definition/use wiring을 확인한다.

**검증 상태**
- Static: PASS — `drawSelection()` 내부에 `sMetricHwnd` local initialization과 desktop fallback 존재 확인.
- Compile/link: NOT TESTED — connector 환경에서 Windows/MSVC 실행 불가.
- Runtime/visual: NOT TESTED — rounded popup selection은 실제 Windows Light/Dark/DPI에서 확인 필요.

**관련 commit**
- `db41ef71` — `fix: define popup selection DPI context`

---


## 2026-09-22 — command-surface validator가 최신 chrome palette를 거짓 실패로 판정

**오류 발생**
- 실행/프로필: `local_ci.bat x64`의 source invariant/regression preflight.
- 사용자에게 보인 증상: `ToolBarEx.cpp`와 `MenuBar.cpp`에서 `sPalette.mSurface` token이 없다는 이유로 solution 생성 전에 FAIL.

**최초 실제 오류**
- 제품 C++ compile/link 오류가 아니라 `build/validate_source_invariants.py`의 command-surface 정적 계약이 최신 UI 구현과 불일치했다.
- preflight 실패로 GYP/Visual Studio project generation 및 이후 compile/link/runtime 단계는 실행되지 않았다.

**원인 진단**
- Observed: 최신 `validate_soft_surface_contract()`와 실제 `ToolBarEx.cpp`/`MenuBar.cpp`는 Win11 layered palette의 command chrome에 `sPalette.mChrome`을 사용한다.
- Observed: 이전 `validate_command_surface_contract()`만 같은 두 파일에 `sPalette.mSurface` exact token을 계속 요구했다.
- Root cause: Win11 softness/rounding 단계에서 command surface ownership이 `mChrome`으로 승격됐지만 이전 flat-surface validator의 exact token이 함께 갱신되지 않아 validator 내부 계약이 서로 모순됐다.

**해결 방법**
- 수정 파일: `build/validate_source_invariants.py`.
- `ToolBarEx.cpp`와 `MenuBar.cpp`의 command-surface 요구 토큰만 `sPalette.mSurface`에서 `sPalette.mChrome`으로 변경했다.
- `SizableReBar.cpp`의 기존 `sPalette.mSurface` 계약은 별도 ownership이므로 변경하지 않았다.

**재발 방지**
- 동일 presentation 계층을 여러 validator가 중복 보호할 때 palette/metric ownership 변경 시 관련 guard 전체의 contract 정합성을 함께 확인한다.
- 실제 구현을 이전 palette 계층으로 되돌려 validator를 만족시키지 않고, 최신 canonical UI contract와 일치하도록 stale guard를 수정한다.
- exact-token invariant를 추가하거나 변경할 때 같은 symbol을 검사하는 다른 validator와 상충하지 않는지 self-check한다.

**검증 상태**
- Static: PARTIAL PASS — GitHub의 현재 source에서 command-surface validator와 soft-surface validator가 모두 toolbar/menu에 `sPalette.mChrome`을 요구하고, rebar의 `mSurface` 계약은 유지되는 것을 확인.
- Source invariant 실행: NOT TESTED — 이 환경에서는 Windows 로컬 checkout의 `python build/validate_source_invariants.py`를 실행하지 못함.
- Compile/link: NOT TESTED — 사용자 로컬 재실행 필요.
- Runtime/visual: 해당 없음.

**관련 commit**
- `53f66a7e` — `fix: align command surface invariant with chrome palette`

---


## 2026-09-22 — 설정 ModernUI subclass callback의 WPARAM/LPARAM 이름 누락

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: source invariant와 VS 2026 x64 solution 생성은 통과했지만 Release x64 compile에서 `cfg_dlg.cpp(129)`의 `aWParam`/`aLParam` C2065로 FAIL.

**최초 실제 오류**
- `ModernGroupBoxSubclassProc`가 callback signature에서 `WPARAM`/`LPARAM`의 변수 이름을 생략한 상태로 함수 끝의 `DefSubclassProc(..., aWParam, aLParam)`에서 해당 이름을 사용했다.
- 동일 구현 패턴의 `ModernCfgButtonSubclassProc`도 같은 누락을 가지고 있어 첫 오류 수정 후 같은 C2065가 이어질 가능성이 있는 상태였다.

**원인 진단**
- Observed: `cfg_dlg.cpp`와 `cfg_main_dlg.cpp`의 두 ModernUI subclass callback 모두 `WPARAM, LPARAM`으로 선언되어 있었고, 각각 원본 message parameter를 `DefSubclassProc`로 전달하려 했다.
- Root cause: settings softness/rounding subclass callback을 추가하면서 사용하지 않는 callback parameter처럼 이름을 생략했지만 forwarding path에서는 실제로 해당 parameter 이름이 필요했다.

**해결 방법**
- 수정 파일: `src/fxfile/cfg/cfg_dlg.cpp`, `src/fxfile/cfg/cfg_main_dlg.cpp`.
- 두 callback signature를 `WPARAM aWParam, LPARAM aLParam`으로 수정하여 기존 `DefSubclassProc` forwarding을 정상화했다.
- UI/message semantics는 변경하지 않았다.

**재발 방지**
- `build/validate_source_invariants.py`에 `validate_modern_subclass_forwarding()`을 추가했다.
- 두 settings ModernUI subclass callback이 WPARAM/LPARAM 이름을 선언하고 원본 message parameter를 `DefSubclassProc`에 전달하는 계약을 preflight에서 검사한다.

**검증 상태**
- Static: PASS — 두 callback signature와 forwarding, 새 source invariant wiring을 repository source에서 확인.
- 기존 사용자 로컬 evidence: source invariant PASS, VS 2026/v145 solution generation PASS, 수정 전 Release x64 compile FAIL.
- 수정 후 Source invariant / Compile/link / Functional regression / Runtime smoke: NOT TESTED — 사용자 로컬 `local_ci.bat x64` 재실행 필요.
- Runtime/visual: NOT TESTED.

**관련 commit**
- `0c67c91d` — `fix: forward config subclass message parameters`

---


## 2026-09-22 — Windows 11 Dark에서 command strip/북마크/설정 combo가 밝거나 과도한 대비로 남음

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 실행 스크린샷.
- 사용자에게 보인 증상: 파일 목록/트리/정보 영역은 Dark인데 상단 menu/rebar/toolbar가 밝게 남고, 정보 영역 bookmark는 순수 파랑으로 과도하게 튀며, 환경설정의 dropdown-list도 흰색 native control처럼 보였다.
- 추가 UX 문제: 테마 선택은 구현되어 있었지만 Korean 설정 tree의 '표시' 항목 아래에 있어 위치를 알아보기 어려웠다.

**최초 실제 오류**
- rebar/toolbar가 app Dark에서도 Explorer visual-style association을 유지한 채 transparent command control로 동작해 light-owned common-control background가 노출될 수 있었다.
- bookmark는 legacy default `RGB(0,0,255)`를 Dark에서도 그대로 사용했다.
- CfgDlg의 `CBS_DROPDOWNLIST` closed field/button은 palette WM_CTLCOLOR 경로만으로는 native light paint를 덮지 못했다.

**원인 진단**
- Observed: content/popup/settings shell의 ThemePalette Dark rendering은 활성화되어 있었으므로 전역 theme-mode 판정 실패가 아니라 control별 paint ownership 불일치였다.
- Root cause: documented Explorer common-control association은 flyExplorer app-dark palette ownership과 동일하지 않으며, legacy bookmark default 및 dropdown-list native paint가 별도 visual path로 남아 있었다.

**해결 방법**
- `SizableReBar.cpp` / `ToolBarEx.cpp`: Dark/non-HC에서 Explorer association을 reset하고 existing palette/custom-draw surface가 command chrome을 소유하도록 변경.
- `bookmark_wnd.cpp`: explicit custom color는 보존하되 legacy default blue만 Dark에서 ThemePalette text로 완화.
- `cfg_dlg.cpp`: dropdown-list의 native input/keyboard/dropdown 계약을 유지하면서 closed field/button만 native paint 후 Dark palette로 보정.
- `Languages/Korean.xml`: 설정 tree의 '표시'를 '모양 및 테마'로 명확화.

**재발 방지**
- `build/validate_source_invariants.py`에서 rebar/toolbar dark theme ownership, config combo adapter, bookmark default-dark readability contract를 보호한다.
- Dark mode에서 documented native theme association을 적용했다는 사실만으로 visual consistency를 가정하지 않고, 실제 control paint ownership을 확인한다.

**검증 상태**
- Static: PARTIAL PASS — repository diff/token wiring과 기존 keyboard/message forwarding 보존을 확인.
- Compile/link: NOT TESTED — Windows/MSVC 로컬 재실행 필요.
- Runtime/visual: 수정 후 NOT TESTED — Windows 11에서 상단 strip, bookmark, settings dropdown 및 Light/High Contrast를 다시 확인해야 한다.

**관련 commit**
- `715f7ec9` — `ui: give dark rebar palette ownership`
- `7f0f17cb` — `ui: keep dark toolbar off light explorer theme`
- `237a12ab` — `ui: soften default bookmark color in dark mode`
- `f4a3b301` — `ui: darken settings dropdown surfaces`

---


## 2026-09-22 — 실행 중 build output 점유로 local CI가 LNK1104까지 진행함

**오류 발생**
- 실행/프로필: `local_ci.bat x64`.
- 사용자에게 보인 증상: source invariant는 PASS했지만 runtime/language staging 중 `Sharing violation`이 반복되고, Release x64 link에서 `fxfile-crash.dll`과 `libxprw.dll`을 열 수 없다는 `LNK1104`로 FAIL.

**최초 실제 오류**
- static/source 오류가 아니라 repository `bin`의 기존 파일이 사용 중이거나 쓰기 불가능한 상태였다.
- staging의 `Sharing violation`은 같은 output tree가 사용 중이라는 선행 신호였고, 최종 fatal은 linker가 project-owned DLL을 교체하지 못한 `LNK1104`였다.
- 기존 local CI는 MSBuild 전에 build output lock을 검사하지 않아 원인이 명확한 환경 오류도 linker cascade까지 진행했다.

**원인 진단**
- Observed: GYP의 x64 OutputDirectory는 `bin/x64`이며 `libxprw.dll`과 `fxfile-crash.dll`도 같은 디렉터리에 linker output으로 생성된다.
- Observed: 실패 로그는 staging 단계의 sharing violation 뒤 같은 `bin/x64` linker output 두 개에 LNK1104를 기록했다.
- 제한: 기존 CI는 lock owner/PID를 기록하지 않았으므로 어떤 프로세스가 점유했는지는 해당 로그만으로 확정할 수 없다. 실행 중인 repository flyExplorer가 이 DLL들을 로드한 경우가 대표적인 재현 조건이다.
- Root cause: local Rebuild가 기존 output을 교체해야 하는데 build 전에 exclusive-write 가능성을 확인하는 preflight가 없었고, staging scripts도 unchanged bundled files를 매번 다시 복사하려 했다.

**해결 방법**
- `build/check_build_output_locks.ps1` 추가: 현재 configuration의 repository-owned EXE/DLL output을 MSBuild 직전 exclusive-open으로 검사하고, 잠긴 파일을 명시한 뒤 fail-fast한다.
- `local_ci.bat`: 모든 `:build_configuration` Rebuild 전에 output-lock preflight를 실행한다. 사용자 프로세스를 자동 종료하지 않는다.
- `copy_lib.bat`, `copy_languages.bat`: directory creation을 idempotent하게 만들고 `xcopy /d`로 unchanged 파일은 덮어쓰지 않는다. staging source가 없거나 실제 copy error가 발생하면 실패를 반환한다.

**재발 방지**
- `build/validate_source_invariants.py`가 lock-preflight wiring, MSBuild보다 앞선 실행 순서, `FileShare::None` 계약, non-destructive process policy, staging `/d`/error handling을 검사한다.
- local CI에서 LNK1104가 repository output 경로를 가리키면 compiler/linker source defect로 보기 전에 output lock을 먼저 진단한다.

**검증 상태**
- 기존 사용자 evidence: source invariant PASS 후 staging sharing violation + Release x64 LNK1104 FAIL.
- Static: PARTIAL PASS — repository source에서 lock preflight/local_ci/copy staging/validator wiring을 대조했다.
- 수정 후 source invariant: NOT TESTED — 사용자 Windows checkout에서 재실행 필요.
- 수정 후 compile/link/functional/runtime: NOT TESTED — repository `bin`을 사용하는 flyExplorer를 닫은 상태에서 `local_ci.bat x64` 재실행 필요.

**관련 commit**
- `275fc85e` — `build: detect locked local CI outputs`
- `4f8acef3` — `build: fail fast on locked outputs`
- `7a9ff045`, `ecd1e4e3` — `build: tolerate unchanged staged files`
- `30220ff2` — `test: guard local CI output lock handling`

---


## 2026-09-22 — Dark settings toggle text와 AddressBar visual-style ownership 불일치

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- 사용자에게 보인 증상: Dark 설정 페이지에서 checkbox/radio label이 어두운 색으로 표시되어 배경과 대비가 부족했고, AddressBar도 inner palette surface와 native-themed outer/child 영역이 섞여 반쪽짜리 Dark control처럼 보였다.

**최초 실제 오류**
- CfgDlg는 WM_CTLCOLOR에서 ThemePalette text를 공급하고 있었지만 themed Win32 Button의 checkbox/radio label paint를 해당 경로가 완전히 소유하지 않았다.
- AddressBar는 palette-backed edit/background/button adapter를 갖고 있으면서도 Dark에서 outer CComboBoxEx, child ComboBox/Edit/ListBox에 documented `Explorer` visual-style association을 계속 적용해 paint ownership이 혼재했다.

**원인 진단**
- Observed: settings page background/card는 Dark ThemePalette를 사용하지만 screenshot의 toggle labels는 dark text로 남았다.
- Observed: AddressBar child controls에는 `applyExplorerControlTheme`와 palette custom paint가 동시에 적용돼 있었다.
- Root cause: native visual-style association/WM_CTLCOLOR가 custom Dark surface 전체의 text/chrome ownership을 보장한다고 가정한 control별 paint ownership 오류였다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: Dark/non-HC checkbox/radio에만 paint subclass를 추가해 background, label, disabled text, check/radio/focus visual을 ThemePalette로 그린다. click/check/keyboard messages는 native Button에 계속 전달한다.
- `cfg/cfg_dlg.cpp`: Dark `CBS_DROPDOWNLIST`의 closed field/button은 기존 adapter가 그리며, `CB_SHOWDROPDOWN` 이후 실제 ListBox HWND의 Explorer association도 reset해 기존 CTLCOLOR palette path가 dropdown text/background를 소유한다. dropdown/keyboard/accessibility 동작은 native ComboBox/ListBox에 남긴다.
- `address_bar.cpp`: Dark/non-HC에서는 outer/ComboBox/Edit/lazy ListBox의 Explorer association을 reset하고 기존 AddressBar palette/subclass paint가 coherent surface를 소유한다. Light/High Contrast는 documented native association path를 유지한다.
- `gui/BCMenu.cpp`: app-owned submenu chevron은 Windows 11 system-provided Segoe Fluent Icons를 우선 사용하고 font 부재 시 geometry fallback을 사용한다. shell IContextMenu routing은 유지한다.
- `src/fxfile/res/fluent/`: Microsoft Fluent UI System Icons MIT license, representative command SVG set, 기존 toolbar frame/command mapping inventory를 추가했다. runtime bitmap strip은 아직 변경하지 않는다.

**재발 방지**
- `build/validate_source_invariants.py`가 settings toggle paint/native fallback wiring, settings ComboBox dropdown ListBox theme reset, AddressBar dark theme reset/native input tokens, popup Fluent chevron+fallback을 검사한다.
- Fluent source contract는 upstream MIT license/provenance, representative SVG existence, canonical GYP registration, main-toolbar frame/command mapping을 함께 검사하고 Windows font binary가 repository에 들어오지 않도록 guard한다.
- Dark UI 검토 시 visual-style association 또는 WM_CTLCOLOR 호출 존재만으로 완료로 판단하지 않고 실제 최종 paint owner를 확인한다.

**검증 상태**
- Static: PARTIAL PASS — repository source에서 paint ownership, native forwarding, asset provenance 및 validator wiring을 대조했다.
- Source invariant 실행: NOT TESTED — 현재 connector 환경에서는 Windows checkout command를 실행하지 못함.
- Compile/link / Functional regression / Runtime smoke: NOT TESTED.
- Visual/manual: 수정 후 NOT TESTED — Windows 11 Light/Dark/System/High Contrast 및 100/125/150/200% DPI에서 재확인 필요.

**관련 commit**
- `1e9d5477` — `ui: fix dark settings toggle contrast`
- `3e974a12` — `ui: give dark address bar full paint ownership`
- `20356129` — `ui: modernize popup chevrons and spacing`
- `962e0864` — `ui: tune popup metrics toward Explorer`
- `e2385e3e` — `ui: complete dark settings combo ownership`
- `b9c6c518` — `build: register Fluent source assets`
- `295be416` — `test: guard Fluent command asset foundation`

---


## 2026-09-22 — Dark settings surface clipping / mixed light controls / popup icon contrast 회귀

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- 사용자에게 보인 증상:
  - 환경 설정 페이지에 큰 검은 사각형 section surface가 생겨 Win11 설정 hierarchy와 어울리지 않음.
  - 일부 edit/combo/button에 밝은 native border/background가 남아 Dark page와 섞임.
  - page-local "모두 적용" 같은 pushbutton이 흰색 native button으로 남음.
  - child page 모서리 근처 control 일부가 잘리거나 위치가 부자연스러워 보임.
  - BCMenu popup의 legacy bitmap icon이 Dark surface에서 과도하게 밝거나 검은 부분이 배경에 묻혀 일부 icon이 사라진 것처럼 보임.

**최초 실제 오류**
- `ModernUI::resetControlTheme`가 `SetWindowTheme(hwnd, NULL, NULL)`을 사용하고 있었다. 이 호출은 themed rendering disable이 아니라 default visual-style association 복원이라 custom Dark paint와 native light chrome이 계속 혼재했다.
- `CfgDlg` child page 전체에 rounded window region을 적용했지만 canonical RC에는 x/y==0에서 시작하는 control이 다수 있어 page corner region이 실제 child control 영역을 잘랐다.
- `ModernGroupBoxSubclassProc`가 BS_GROUPBOX의 전체 rect를 `mElevated` rounded card로 채워 resource grouping box마다 큰 검은 island를 만들었다.
- CfgDlg의 page-local BS_PUSHBUTTON/BS_DEFPUSHBUTTON은 dark paint adapter 대상이 아니었다.
- BCMenu `drawIcon`은 legacy source icon을 `DrawIconEx(... DI_NORMAL)`로 그대로 그려 popup ThemePalette와 icon luminance/contrast ownership이 분리되어 있었다.

**원인 진단**
- Root cause: "native theme reset", "page rounding", "group card", "menu icon"을 각각 현대화 요소로 추가했지만 실제 Win32 paint/geometry ownership을 하나의 hierarchy로 검증하지 않았다.
- Observed: main settings/footer 일부는 custom dark paint인데 page-local buttons과 themed borders는 native light path가 남았다.
- Observed: resource-defined groupbox/page geometry는 legacy DLU 좌표를 그대로 사용하는데 window-region clipping과 larger visual layers를 추가해 control bounds와 충돌했다.
- Observed: legacy menu bitmap은 색상형 source이므로 Dark popup에서 원본 색을 유지하면 Fluent/Win11 command-menu icon weight와 맞지 않는다.

**해결 방법**
- `gui/ModernUI.cpp`: `resetControlTheme`이 documented `SetWindowTheme(hwnd, L"", L"")`을 사용해 실제 themed painting을 disable하도록 수정했다.
- `cfg/cfg_dlg.cpp`: Dark/non-HC Explorer-owned edit/list/combo 계열은 theme disable 후 palette path가 surface를 소유한다.
- `cfg/cfg_dlg.cpp`: groupbox를 전체 rounded card로 채우지 않고 page background + section label + subtle separator로 변경했다.
- `cfg/cfg_dlg.cpp`: BS_PUSHBUTTON/BS_DEFPUSHBUTTON용 Dark paint adapter를 추가해 page-local button도 같은 palette hierarchy를 사용한다.
- `cfg/cfg_dlg.cpp`, `cfg/cfg_main_dlg.cpp`: child page 자체 rounded window region을 제거해 x/y==0 resource control clipping을 방지했다.
- `gui/BCMenu.cpp`: non-HC menu icon을 documented `DrawState(... DST_ICON | DSS_MONO)`로 palette text/secondary-text color에 tint하고 High Contrast는 원본/system path로 fallback한다.
- 비집중 control border는 `mBorder`보다 약한 `mSeparator`를 사용해 흰 외곽선처럼 보이는 대비를 낮췄다.

**재발 방지**
- `build/validate_source_invariants.py`가 `SetWindowTheme(hwnd, L"", L"")` disable contract를 검사하고 `NULL,NULL` reset이 되돌아오는 것을 금지한다.
- settings guard가 page pushbutton adapter, page-region clearing, dark control theme ownership, flat groupbox hierarchy를 검사한다.
- popup guard가 `DrawState`, `DST_ICON | DSS_MONO`, disabled secondary-text tint를 검사한다.
- Win11 visual modernization에서 resource page 전체에 rounded window region을 적용하지 않는다. rounding은 control/surface 단위로만 적용하고 RC의 actual child bounds를 먼저 확인한다.

**검증 상태**
- 사용자 screenshot evidence: FAIL — 수정 전 검은 group card, white/mixed controls, clipped page details, overbright/hidden menu icons 확인.
- Static/source self-review: PASS — 수정 후 paint ownership/token/diff를 repository source에서 대조.
- `python build/validate_source_invariants.py`: NOT TESTED.
- Compile/link: NOT TESTED.
- Functional/runtime: NOT TESTED.
- 수정 후 Windows 11 Light/Dark/System/High Contrast 및 DPI visual: NOT TESTED.

**관련 commit**
- `b8ae8e3e` — `fix: actually disable native theme for owned dark controls`
- `c67ee1a6` — `ui: tint popup icons for dark menu contrast`
- `2131d37e` — `ui: unify dark settings control surfaces`
- `03f8ec1a` — `ui: stop clipping dark settings pages`
- `95f2eb98`, `46a85be4`, `4ddf1269` — settings border softening
- `a8dc5380` — `test: guard coherent dark settings and menu icons`

---


## 2026-09-23 — BCMenu DrawState 호출 인자 수 오류로 Release x64 compile 실패

**오류 발생**
- 실행/프로필: `local_ci.bat x64` → `Release-x64-Unicode | x64`.
- source invariant/regression preflight와 VS 2026/v145 solution 생성은 PASS했지만 `src/fxfile/gui/BCMenu.cpp(1185)`에서 C2660으로 compile이 중단됐다.
- 최초 실제 compiler error: `DrawState: 함수는 11개의 인수를 사용하지 않습니다.`

**최초 실제 오류**
- popup icon monochrome tint를 추가하면서 Win32 `DrawState` 호출을
  `HDC, NULL, HBRUSH, NULL, icon, ...` 순서로 작성해 11개 인자를 전달했다.
- Win32 signature는 `HDC, HBRUSH, DRAWSTATEPROC, LPARAM, WPARAM, x, y, cx, cy, flags`의 10개 인자다.

**원인 진단**
- Root cause: GDI API의 parameter ownership을 확인하지 않고 brush와 callback 사이에 불필요한 null placeholder를 추가했다.
- 기존 static guard는 `DrawState(` 및 `DST_ICON | DSS_MONO` token 존재만 검사해 실제 arity/order 오류를 잡지 못했다.

**해결 방법**
- `gui/BCMenu.cpp`: `DrawState(aDC->m_hDC, sBrush, XPR_NULL, reinterpret_cast<LPARAM>(sIcon), 0, ...)`의 documented 10-argument signature로 수정했다.
- menu icon의 ThemePalette monochrome tint semantics 자체는 유지했다.

**재발 방지**
- `build/validate_source_invariants.py`에 DrawState 호출의 첫 인자 순서를 regex로 검증하는 guard를 추가했다.
- `aDC->m_hDC, XPR_NULL, sBrush`의 과거 11-argument ordering이 돌아오면 preflight에서 실패한다.

**검증 상태**
- 사용자 로컬 evidence: source invariant PASS, VS 2026/v145 generation PASS, 수정 전 Release x64 compile FAIL.
- 수정 후 static/source self-review: PASS.
- 수정 후 `local_ci.bat x64` / compile/link/runtime: NOT TESTED.
- 현재 사용자 지시에 따라 CI 범위는 `Release-x64-Unicode | x64`로 한정한다. x86/Multibyte/release/full matrix는 별도 지시 전까지 실행하지 않는다.

**관련 commit**
- `c9fbb7d5` — `fix: use Win32 DrawState signature correctly`
- `7440a6a0` — `test: guard Win32 DrawState menu icon signature`
- `4ae5f7e6` — `docs: scope active CI to Release x64 Unicode`

---


## 2026-09-23 — Settings Style control 가림 / Dark Edit edge / Fluent menu icon gate 회귀

**오류 발생**
- 실행/환경: Windows 11 실제 사용자 스크린샷.
- `환경 설정 > 모양 및 테마 > 레이아웃`의 `스타일` section은 제목/영역만 보이고 내부 Standard/Basic style 선택 항목이 보이지 않았다.
- `환경 설정 > 일반 > 시작 폴더`의 path Edit 주변에 Dark surface와 맞지 않는 밝은 native edge가 남았다.
- app-owned popup menu는 일부 command icon이 여전히 legacy 느낌이거나 아예 보이지 않는 상태였고, Main Toolbar도 9개 command만 Fluent runtime artwork를 사용해 기본 표시 command 대부분이 legacy였다.

**최초 실제 오류**
- `IDD_CFG_APPEARANCE_LAYOUT` resource에는 `IDC_CFG_LAYOUT_INFO_BAR_STANDARD_STYLE` / `IDC_CFG_LAYOUT_INFO_BAR_BASIC_STYLE`가 실제로 존재하고 init/enable logic도 정상이다. 하지만 `GROUPBOX`가 sibling control 뒤에 선언되어 있고 `ModernGroupBoxSubclassProc`가 전체 client rect를 불투명하게 owner-paint해 sibling radio/check control을 덮을 수 있었다.
- settings Edit는 native non-client border를 유지한 채 CTLCOLOR/client surface만 Dark palette로 바뀌어 multi-pixel `WS_BORDER` / themed edge가 일부 DPI에서 밝게 남을 수 있었다.
- BCMenu의 Fluent draw path가 legacy `menuIconNormal >= 0 && bitmap != NULL` 조건 뒤에 있어, Fluent registry에 command가 있어도 legacy bitmap이 없는 menu item은 Fluent icon을 그릴 기회가 없었다.
- Main Toolbar의 Fluent registry가 9개 command에만 한정되어 있었다.

**원인 진단**
- Root cause 1: legacy RC의 groupbox z-order와 opaque custom groupbox paint ownership을 함께 고려하지 않았다.
- Root cause 2: Dark Edit의 client background와 non-client border ownership을 분리해서 처리했다.
- Root cause 3: Fluent artwork source가 Main Toolbar private path에 묶여 있었고 BCMenu 표시 여부가 legacy bitmap 존재 여부에 종속되어 있었다.
- Root cause 4: 대표 command migration을 실제 default-visible command coverage로 확대하지 않아 한 화면 안에 Fluent/legacy artwork가 과도하게 혼재했다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: GROUPBOX를 transparent section-label container로 유지하고 `HWND_BOTTOM`에 배치한다. child traversal은 z-order 변경 전에 next sibling을 저장해 누락/반복을 방지한다.
- `cfg/cfg_dlg.cpp`: `ModernCfgEditSubclassProc`가 Dark/non-HC의 `WM_NCPAINT` 후 전체 native non-client band를 `mElevated`로 덮고 normal `mSeparator` / focus `mFocus` frame을 소유한다. native Edit input/caret/selection/IME/clipboard semantics는 그대로 둔다.
- `gui/FluentCommandIcons.*`: command-ID 기반 shared Fluent runtime adapter를 추가해 generated mask를 Main Toolbar와 BCMenu가 공유한다.
- `gui/BCMenu.cpp`: legacy bitmap이 없어도 shared registry에 command ID가 있으면 Fluent icon을 우선 그린다. check/radio item semantics와 legacy fallback은 유지한다.
- Main Toolbar manifest/runtime coverage를 23개 command로 확장했다. 이 중 기본 표시 21개 command는 전부 Fluent registry 대상이며 optional History/Settings도 포함한다.
- CfgMainDlg navigation은 33-frame legacy bitmap fallback을 유지하면서 의미가 명확한 17개 category image index를 non-High-Contrast에서 shared Fluent registry로 overlay한다.
- popup menu의 padding/shortcut gap/icon gutter와 accelerator/chevron text role을 조정해 primary text와 secondary metadata hierarchy를 분리했다.

**재발 방지**
- `build/validate_source_invariants.py`가 GROUPBOX transparency/z-order, stable child traversal, Dark Edit NC-frame ownership을 검사한다.
- Fluent validator는 `toolbar_manifest.json`을 canonical source로 파싱하고 23-command coverage, 기본 표시 21개 command mapping, SVG/GYP registration, generated-mask determinism, Main Toolbar/BCMenu shared registry wiring을 검사한다.
- settings navigation guard는 `config_tree.bmp` 33-frame fallback과 runtime Fluent overlay가 함께 유지되는지 검사한다.

**검증 상태**
- 사용자 screenshot evidence: FAIL — 수정 전 Layout Style 항목 가림, 밝은 folder Edit edge, legacy/missing popup icon 및 혼합 toolbar artwork 확인.
- Static/source self-review: PASS — resource/init logic과 paint/icon ownership을 latest main source에서 대조.
- `python build/validate_source_invariants.py`: NOT TESTED.
- `Release-x64-Unicode | x64` compile/link + functional regression + runtime smoke: NOT TESTED.
- 수정 후 Windows 11 visual/manual 및 DPI 100/125/150/200%: NOT TESTED.

**관련 commit**
- `59088311`, `daad8b57`, `78a34994` — settings group/edit ownership 수정
- `5882dc13`, `e1987bc8`, `654aac89`, `e2d87520` — shared Fluent command-icon path
- `27c2ea41` ~ `41f011b4` — 23-command manifest/mask/default-toolbar migration
- `7c395e6a`, `279ba426` — popup metric/text hierarchy 정리
- `6a0a986d` — settings navigation Fluent overlay
- `ad56d3dc`, `5d971fff` — manifest/settings regression guards

---

## 2026-09-23 — native functional regression harness의 XPR lifecycle 누락

**오류 발생**
- 확인 경로: 현재 native functional regression harness source/contract audit.
- `src/fxfile-tests/functional_tests.cpp`는 production `xpr::FileSys` / `xpr::FileIo`를 직접 사용하면서 product executable이 수행하는 XPR runtime initialize/finalize lifecycle을 명시적으로 갖고 있지 않았다.

**최초 실제 오류**
- 테스트 entry point가 fixture 생성과 production XPR API 호출 전에 `xpr::initialize()`를 호출하지 않았고, 종료 경로에도 `xpr::finalize()`가 없었다.
- 이는 테스트가 production runtime initialization contract를 우연한 process state에 의존하게 만드는 harness-level 결함이다.

**원인 진단**
- Observed: main application과 updater는 startup/exit에서 XPR lifecycle을 명시적으로 소유하지만 standalone functional-test executable은 동일 ownership을 빠뜨렸다.
- Root cause: product API를 직접 재사용하는 standalone test target을 추가하면서 library dependency/include wiring은 맞췄지만 process-level runtime lifecycle까지 test entry point 계약에 포함하지 않았다.

**해결 방법**
- `src/fxfile-tests/functional_tests.cpp`: `_tmain()` 시작에서 `xpr::initialize()` 성공을 확인한다.
- fixture setup 실패와 정상 test summary 종료 경로에서 `xpr::finalize()`를 호출한다.
- 실제 test result exit code는 finalize 전에 보존해 기존 PASS/FAIL semantics를 유지한다.

**재발 방지**
- `build/validate_source_invariants.py::validate_functional_test_wiring()`이 `xpr::initialize()` / `xpr::finalize()` token을 functional-test lifecycle contract로 검사한다.
- standalone executable test가 production runtime/library API를 직접 사용할 때 process initialization/finalization contract도 함께 확인한다.

**검증 상태**
- Static/source self-review: PASS — functional-test entry point와 invariant guard가 latest main에서 함께 존재함을 확인.
- `python build/validate_source_invariants.py`: NOT TESTED in this connector environment.
- `local_ci.bat x64` / `Release-x64-Unicode | x64` functional regression: NOT TESTED after this lifecycle fix.
- UI/runtime visual: 해당 없음.

**관련 commit**
- `1eb5ff24` — `test: initialize XPR runtime in functional regression`
- `7c9b69f4` — `test: guard functional XPR lifecycle`

---

## 2026-09-23 — build 성공 후에도 legacy toolbar 상태가 Win11 command-bar 변경을 덮어씀

**오류 발생**
- 실행/환경: 사용자 Windows 11 실제 실행. C++ build 자체는 성공했지만 상단 toolbar의 작은 icon/legacy-looking command surface와 text 대비 문제가 그대로 보였다.
- 새 기본값을 22px Fluent large icon으로 바꿔도 기존 사용자 화면이 즉시 달라지지 않았다.

**최초 실제 오류**
- `MainToolBar::Init()`은 기본 icon type을 `TBI_LARGE`로 설정하지만, `MainToolBar::load()`가 기존 `fxfile-toolbar.dat`의 persisted `TBI_SMALL` 값을 다시 적용했다.
- ToolbarWindow32 custom draw는 ThemePalette의 `clrText`를 채우고 있었지만 `TBCDRF_USECDCOLORS` 및 highlighted-text/background-mode contract가 없어 hot/selected state에서 system color가 다시 개입할 수 있었다.

**원인 진단**
- Observed: old toolbar state file format은 text type, icon type, command IDs만 저장하며 version/migration marker가 없었다.
- Root cause 1: source default 변경과 persisted user state migration을 동일한 것으로 취급했다.
- Root cause 2: ToolbarWindow32가 custom-draw color fields를 실제 text rendering에 사용하도록 명시하는 return flag/state color wiring이 불완전했다.

**해결 방법**
- `src/fxfile/main_toolbar.cpp`: legacy-format file에서만 historical `TBI_SMALL`을 `TBI_LARGE`로 1회 migration한다.
- 새 저장 파일에는 `kModernToolbarStateMarker`를 append한다. 기존 reader는 unknown command id로 무시하므로 layout format의 downgrade tolerance를 유지한다.
- marker가 있는 새 파일에서는 사용자가 이후 명시적으로 Small을 선택한 경우 그대로 보존한다.
- `ToolBarEx.cpp` / `MenuBar.cpp`: `TBCDRF_USECDCOLORS`, `clrTextHighlight`, transparent string background mode를 함께 설정해 normal/hot/selected text가 동일 ThemePalette를 사용하게 했다.

**재발 방지**
- `build/validate_source_invariants.py`가 one-time migration marker/read/write contract와 ToolbarWindow32 highlighted-text palette wiring을 검사한다.
- default UI 값 변경 시 persisted legacy state가 startup에서 다시 덮어쓰는지 함께 확인한다. migration은 user preference를 영구 무시하지 않도록 version/marker를 둔다.

**검증 상태**
- Targeted static audit: PASS — branch source에서 marker read/write, legacy-only migration, TBCDRF_USECDCOLORS, highlighted text/transparent background wiring 확인.
- `python build/validate_source_invariants.py`: NOT TESTED — connector 환경에는 repository checkout command 실행 경로가 없음.
- Compile/link / functional regression / runtime visual: NOT TESTED after these commits. 사용자 Windows에서 `local_ci.bat x64` 및 실제 화면 재확인 필요.

**관련 commit**
- `e97d0258` — `ui: migrate legacy small toolbar icons`
- `f01ddbea`, `e45778dd` — command/menu palette color ownership
- `de06e5ff` — `fix: migrate toolbar icon size only once`
- `fdfde0dd`, `4f6b51ec` — highlighted command/menu text palette
- `b25b70e3`, `af48a099` — regression guards

---

## 2026-09-23 — AddressBar nested legacy edge와 standard-user config path가 build 성공 뒤 runtime 증상으로 남음

**오류 발생**
- 실행/환경: 사용자 Windows 11 실제 실행에서 build는 성공했지만 AddressBar 내부 folder/path 영역에 별도 사각 edge가 남고, 일반 사용자 권한 실행 경로에 대한 문제가 계속 보고됐다.
- 이 항목은 두 runtime ownership 결함을 분리해 기록한다.

**최초 실제 오류**
- AddressBar outer ComboBoxEx는 palette-owned frame을 그리지만 child Edit의 legacy `WS_EX_CLIENTEDGE`가 그대로 남아 outer frame 안에 두 번째 native edge가 생길 수 있었다.
- `ConfDir::load()`은 persisted `conf_home`이 존재하는 directory인지 여부만 사실상 신뢰했고, Program Files 아래 `%fxfile%\\conf`처럼 읽기는 가능하지만 standard user에게 쓰기 불가능한 legacy portable path를 정상 save target처럼 유지할 수 있었다.
- `OptionManager::load()`은 configuration load 실패 시 즉시 default file을 저장하려 하므로 unwritable path에서는 startup/config initialization 흐름이 관리자 권한 여부에 따라 달라질 수 있었다.

**원인 진단**
- Root cause 1: AddressBar client/background paint와 child Edit non-client frame ownership을 분리해서 처리했다.
- Root cause 2: configuration directory의 "존재함"과 "현재 token으로 실제 writable함"을 동일하게 취급했다.
- 제한: 사용자의 실제 `.fxfile` 내용은 connector에서 읽지 않았으므로 해당 사용자의 persisted `conf_home` 값 자체는 미확인이다. 다만 위 경로 조건에서 발생하는 product defect는 source로 확인된다.

**해결 방법**
- `src/fxfile/address_bar.cpp`: non-High-Contrast에서 child Edit의 기존 `WS_EX_CLIENTEDGE` 상태를 기억한 뒤 제거하고, High Contrast에서만 원래 native edge를 복원한다. Combo/Edit background erase도 ThemePalette brush가 소유한다.
- `src/fxfile/conf_dir.cpp`: configured/default config directory에 실제 probe file create/delete를 수행해 writable 여부를 확인한다.
- 기존 persisted custom/portable path가 unwritable이면 `%AppData%\\fxfile\\conf`로 fallback하고, recovered path를 다시 descriptor에 저장해 다음 startup도 standard-user path를 사용하게 한다.

**재발 방지**
- source invariant가 AddressBar single-frame token, writable config probe/fallback/persist contract를 검사한다.
- 설치 위치가 Program Files일 수 있는 desktop app에서는 user config writeability를 directory existence만으로 판단하지 않는다.
- custom Dark frame을 소유하는 composite control은 child native non-client style까지 함께 audit한다.

**검증 상태**
- Targeted static audit: PASS — branch source에서 Edit edge removal/HC restore, writable probe, fallback/persist wiring 확인.
- Compile/link / runtime standard-user startup / visual AddressBar: NOT TESTED after these commits.
- settings theme refresh reentrancy guard도 branch에 포함되어 있으나 실제 crash stack evidence가 없어 별도 root cause로 확정하지 않는다.

**관련 commit**
- `6bd4ff31` — `fix: remove nested legacy address field frame`
- `1a2dfe1d`, `b5055009` — standard-user config fallback
- `673c2184` ~ `266603f2` — settings theme-refresh reentrancy guard
- `c81f37df` — runtime UI fix guards

---

## 2026-09-23 — 동일 control theme association 반복 적용이 settings/UI thread를 다시 막을 수 있었음

**오류 발생**
- 사용자 Windows 11 screenshot에서 `fxfile (응답 없음)` 상태가 다시 확인됐다.
- 이전 WER/cdb evidence에서는 `uxtheme!SetWindowTheme -> ModernUI::applyExplorerControlTheme -> WM_THEMECHANGED handler`가 반복되는 stack이 관찰됐다.
- 기존 수정은 `SetWindowTheme` 호출 중의 synchronous re-entry만 guard했기 때문에, 호출이 끝난 뒤 전달되는 후속 `WM_THEMECHANGED`가 동일 association을 다시 설정하는 경우를 막지 못했다.

**최초 실제 오류**
- `ModernUI::applyExplorerControlTheme()` / `resetControlTheme()`가 현재 HWND에 이미 같은 association이 적용돼 있는지를 기억하지 않았다.
- settings host/page의 `OnThemeChanged`가 다시 전체 child tree를 순회하며 control theme helper를 호출했다.

**원인 진단**
- Root cause: "현재 SetWindowTheme call 안에 있는가"와 "이 HWND가 이미 원하는 theme association 상태인가"를 같은 문제로 취급했다.
- synchronous call-stack recursion guard만으로는 message-queue를 거쳐 다시 발생하는 동일 association 적용 loop를 방지할 수 없다.

**해결 방법**
- `ModernUI.cpp`: HWND property에 Explorer/Default/Disabled association 상태를 기록하고 동일 association 요청은 `SetWindowTheme` 자체를 생략한다.
- 기존 call-stack guard는 nested synchronous notification 방어용으로 유지한다.
- `CfgMainDlg` / `CfgDlg`: `WM_THEMECHANGED`에서는 palette/font/frame repaint만 수행하고 child theme association을 다시 순회하지 않는다. 최초 생성/settings/system-color/DPI refresh에서는 기존 전체 적용 경로를 유지한다.

**재발 방지**
- source invariant가 theme-association state property, identical-request skip, settings의 `refreshModernAppearance(XPR_FALSE)` contract를 검사한다.
- `WM_THEMECHANGED` handler에서 `SetWindowTheme`를 다시 호출하는 경로는 call-stack guard뿐 아니라 desired-state idempotence까지 확인한다.

**검증 상태**
- 이전 WER/cdb stack evidence: CONFIRMED — `SetWindowTheme` / `WM_THEMECHANGED` 반복 경로가 관찰됨.
- Targeted static audit: PASS — desired association cache 및 settings paint-only notification 경로 확인.
- `python build/validate_source_invariants.py`: NOT TESTED in connector environment.
- Compile/link / Preferences 10회 open-close / runtime hang: NOT TESTED after this fix.

**관련 commit**
- `35594b5e` — `fix: make control theme changes idempotent`
- `b66b7d82` — association regression guard
- `b8bef073` ~ `deb887c1` — settings host/page paint-only theme notification
- `9a0666cc` — settings refresh regression guard

---

## 2026-09-23 — standard-user 경로에 machine-wide shell registration과 과도한 mutex access가 남아 있었음

**오류 발생**
- 사용자에게 관리자 권한 없이 실행/설정하는 경로가 정상 동작하지 않는 문제가 계속 보고됐다.
- manifest는 이미 `asInvoker`였고 configuration 기본 경로도 AppData였으므로, 남은 권한 의존 API를 추가 audit했다.

**최초 실제 오류**
- `ShellRegistry`가 `HKEY_CLASSES_ROOT\\Folder\\Shell`에 context-menu registration을 직접 쓰고 있었다.
- `SingleProcess::check()`가 단순한 named mutex 존재 확인에 `MUTEX_ALL_ACCESS`를 요청하고 있었다.

**원인 진단**
- HKCR write는 merged machine/user class view에 대한 legacy registration 방식이며 standard-user settings 적용에서 권한 차이를 만들 수 있다.
- named mutex 존재 확인에 all-access는 불필요하며, 기존 elevated instance와 standard-user instance 사이에서 access-denied를 "mutex가 없음"으로 오판할 수 있다.
- 제한: screenshot의 `관리자:` 표시는 실행된 process가 elevated라는 evidence지만, elevation이 shortcut/AppCompat 설정에서 강제됐는지는 repository source만으로 확인할 수 없다.

**해결 방법**
- shell context menu는 `HKCU\\Software\\Classes\\Folder\\Shell` 아래 per-user registration으로 이동했다. Explorer의 HKCR merged view에서는 동일하게 노출된다.
- single-process presence check는 `SYNCHRONIZE`만 요청하고, minimal open에서도 `ERROR_ACCESS_DENIED`이면 named object가 존재하는 것으로 처리한다.
- 기존 `asInvoker` manifest와 AppData configuration contract는 유지한다.

**재발 방지**
- source invariant가 shell registration에서 HKCR write를 금지하고 HKCU Classes path를 요구한다.
- mutex presence check에서 `MUTEX_ALL_ACCESS` 재도입을 금지한다.

**검증 상태**
- Targeted static audit: PASS — shell registry와 mutex access source contract 확인.
- standard-user clean launch / elevated-existing-instance interop: NOT TESTED after this fix.
- repository source에는 product manifest의 `requireAdministrator` / `highestAvailable` 설정이 없음.

**관련 commit**
- `253839b7` — `fix: register shell menu per user`
- `e03f5155` — per-user shell regression guard
- `1bdd46c2` — `fix: remove elevation-dependent mutex access`
- `c0c3fd55` — standard-user mutex regression guard

---

## 2026-09-23 — AddressBar와 coolbar legacy child geometry가 Win11 surface를 다시 덮어씀

**오류 발생**
- 기존 AddressBar 수정 뒤에도 사용자 보고에서 folder/path field의 별도 사각 frame과 command icon layout 문제가 남았다.

**최초 실제 오류**
- 이전 AddressBar fix는 child Edit의 `WS_EX_CLIENTEDGE`만 제거했다. 내부 ComboBox와 Edit의 `WS_BORDER` 및 ComboBox의 `WS_EX_CLIENTEDGE`는 그대로 남을 수 있었다.
- `MainCoolBar::loadStateFile()`은 Win11 command metrics가 계산된 뒤 legacy coolbar의 persisted `cx/cxMinChild` 값을 다시 적용했다. Main toolbar는 후속 load에서 자체 size refresh를 하지만 drive/bookmark band는 legacy geometry가 마지막 값이 될 수 있었다.

**원인 진단**
- composite address control에서 outer ComboBoxEx만 modern frame ownership을 가져야 하지만 nested child non-client styles를 완전히 제거하지 않았다.
- command button/icon 크기 migration과 rebar band geometry migration을 별개 persistence layer로 보지 않았다.

**해결 방법**
- non-High-Contrast AddressBar에서 nested ComboBox/Edit의 `WS_BORDER`와 `WS_EX_CLIENTEDGE`를 모두 제거하고 original state를 HWND property에 보관한다.
- High Contrast에서는 original native border state를 복원한다.
- legacy coolbar state restore가 끝난 뒤 main/drive/bookmark toolbar 모두 `UpdateToolbarSize()`를 다시 실행해 current command metrics가 최종 band child size를 결정하도록 했다.

**재발 방지**
- source invariant가 ComboBox/Edit 양쪽 border/client-edge 제거와 High Contrast restore에 필요한 state token을 검사한다.
- persisted rebar state restore 뒤 세 toolbar의 post-restore metric recalculation을 검사한다.

**검증 상태**
- Targeted static audit: PASS — nested border removal/restore 및 post-restore toolbar sizing source 확인.
- Windows 11 AddressBar visual / command-bar icon spacing: NOT TESTED after this fix.
- hung-window ghost screenshot의 회색/희미한 rendering은 정상-state palette evidence로 사용하지 않는다.

**관련 commit**
- `265161ab` — `fix: remove nested address control borders`
- `7bb4a027` — AddressBar single-frame regression guard
- `08186e67` — `ui: recalc command bars after legacy state restore`
- `678ef5a0` — post-restore command-bar metric guard

---

## 오류를 예방하기 위한 일반 개발 규칙

1. 새 header/API/macro는 소유 header를 직접 include한다. PCH/transitive include에 기대지 않는다.
2. generated project가 아니라 GYP/build canonical source에서 dependency와 configuration을 고친다.
3. 첫 실제 compiler/linker/CI orchestration error를 먼저 고친다. cascade 숫자를 결함 개수로 해석하지 않는다.
4. CI/build script 안에 다른 shell 언어를 embed할 때 cmd/PowerShell quoting과 escape 책임 경계를 분리한다.
5. static validator는 가능한 한 deterministic contract를 검사하되, 단순 문자열 token 때문에 정상 코드를 거짓 실패시키지 않도록 실제 syntax/format 변형을 고려한다.
6. 오류를 한 번 고친 후 반복 가능성이 있으면 가장 싼 자동 방어선을 같이 추가한다.
7. 제품 build PASS와 CI orchestration PASS, runtime PASS, visual PASS는 서로 다른 evidence로 기록한다.
8. Win32/MFC의 unsigned field와 signed DPI/metric/helper 값을 직접 비교하지 않는다. 값의 의미와 범위를 확인한 뒤 비교 경계에서 같은 타입으로 정규화한다.
9. DPI-aware draw/layout fragment를 함수 간 이동할 때 HWND/DPI metric context의 선언과 fallback도 함께 이동한다. renderer는 다른 함수의 local setup을 암묵적으로 전제하지 않는다.


## 2026-09-23 - Protected install-path migration and legacy owner-draw dark colors

### Standard-user migration path

**Occurrence**
- Source review of the standard-user startup/configuration path found two legacy migrations that still assumed the source directory was writable.
- This is relevant when an older portable profile or `accel.fac` is beside `fxfile.exe` under a protected installation directory such as Program Files.

**First actual source error**
- `ConfDir::moveToNewConfDir()` used a rename from the old configuration directory to the new per-user directory. Renaming requires delete/write access to the old directory.
- `MainFrame::loadAccelTable()` used a move of legacy `accel.fac` out of the executable directory, which has the same protected-source write/delete requirement.

**Cause**
- The migration logic treated a readable legacy install directory as if it were also writable.
- The current per-user destination was already designed to be writable, so requiring source deletion was unnecessary.

**Fix**
- Configuration migration now copies each existing file to the already validated destination and treats removal of the old source as best-effort cleanup.
- Legacy `accel.fac` migration now copies into `ConfDir::TypeAccel` instead of moving the install-directory file.
- The single-instance handoff also allows only the registered activation message through `ChangeWindowMessageFilterEx` when available, so a normal-integrity second launch does not need to elevate merely to wake an already elevated first instance.

**Prevention**
- `validate_source_invariants.py` checks that the legacy accel path uses `CopyFile`, configuration migration no longer uses `xpr::FileSys::rename`, and the cross-integrity handoff remains dynamically resolved for the legacy target headers.

**Validation**
- GitHub source review confirms the protected-source rename/move calls were replaced and the invariant contracts are present.
- `python build/validate_source_invariants.py`, MSVC compile/link, standard-user launch, elevated/non-elevated handoff, and Windows runtime smoke are **NOT TESTED** in the connector-only environment.

### Legacy owner-draw controls on Dark settings surfaces

**Occurrence**
- Source review found legacy owner-draw controls still selecting native light/system text and 3D colors while their parent settings surfaces were palette-owned Dark UI.
- Affected reviewed controls included `CButtonST`, `CDropMenuButton`, `CColourPickerXP`, the file-scrap pane, bookmark labels, and the search-location dialog.

**First actual source error**
- Split-button arrows and owner-draw button borders retained hard-coded black/light-system paths.
- The colour picker continued to use themed/light common-control painting and menu/system text colors in its owner-draw path.
- File-scrap/search-location paint paths could select native button/window text colors independently of the app Dark palette.

**Cause**
- These controls predate the shared `ModernUI::ThemePalette` ownership model and were not fully covered by parent `WM_CTLCOLOR` handling because they paint their own text, borders, arrows, or popup cells.

**Fix**
- Owner-draw text, disabled text, border, focus, hover/pressed, separator, and arrow colors now use `ThemePalette` outside High Contrast.
- The colour picker bypasses native light themed painting on app-owned Dark surfaces and uses the shared Windows UI font; its popup re-resolves that font after HWND creation so monitor DPI is available.
- File-scrap/bookmark labels use `ModernUI::getUIFont`, while High Contrast retains system-owned colors.

**Prevention**
- Source-invariant checks guard the palette-aware owner-draw paths, colour-picker popup font path, and file-scrap/bookmark typography contracts.

**Validation**
- Connector-side source inspection confirms the new palette/font branches and matching declarations are present.
- Windows 11 Light/Dark/System/High Contrast visual checks, 100/125/150/200% DPI checks, Korean text/IME checks, MSVC compile/link, and runtime behavior are **NOT TESTED** here.


### Dark filtered list text and menu state glyphs

**Occurrence**
- Continued source audit of the reported Dark-mode black-text inconsistency found two paint paths that were still able to select black/system-menu foreground colors independently of the Dark palette.

**First actual source error**
- When file-list text color mode was `COLOR_TYPE_FILTERING`, the historical general-file `*.*` filter supplied `RGB(0, 0, 0)` directly to list-view custom draw. That legacy default is readable on a light surface but can become black-on-dark.
- `BCMenu::Draw3DCheckmark()` always used `COLOR_MENUTEXT`, so app-owned checked/radio glyphs could remain dark even when the popup surface was Dark.

**Cause**
- Filter colors predate the app theme and encode the old light-surface general-file default as literal black rather than an automatic text semantic.
- The legacy menu-state helper bypassed the newer `ThemePalette` text/selection colors.

**Fix**
- The file-list filtering path treats only the historical general-file signature (`*.*` + pure black) and a missing filter as automatic text in app Dark/non-High-Contrast, using `ThemePalette.mText`. Other explicit filter colors and all background-filter colors remain unchanged.
- `BCMenu::Draw3DCheckmark()` now uses palette text/selection-text outside High Contrast and system menu/highlight text in High Contrast.
- Legacy owner-draw buttons/split buttons also resolve `ModernUI::getUIFont` when they do not already have a control font, and drag feedback uses the same shared Windows UI font.

**Prevention**
- Source invariants guard the legacy `*.*` black-text fallback, preserve background-filter routing, require palette-aware menu check/radio glyphs, and require shared Windows UI font fallback for reviewed owner-draw/transient text paths.

**Validation**
- Connector-side source inspection confirms the targeted paint/font branches and invariant tokens are present.
- `python build/validate_source_invariants.py`, MSVC compile/link, Windows 11 runtime Dark visual checks, user filtering-mode state, menu checked/radio rendering, DPI checks, and Korean text rendering are **NOT TESTED** in this connector-only environment.

**Related commits**
- `a45dbcb6` — `ui: keep legacy filtered text readable in dark mode`
- `be135783` — `ui: keep menu checkmarks readable in dark mode`
- `60ce7b8e`, `c3e6e8c8` — owner-draw Windows UI font fallbacks
- `188d1f6d` — drag-feedback Windows UI font
- `7d4e8a35`, `d96347de` — regression guards

---

## 2026-09-23 — 공용 dialog Dark theme와 elevated installer 자동 실행이 이전 수정 범위 밖에 남아 있었음

**오류 발생**
- 최근 runtime/UI 안정화 커밋들을 `main`에 통합한 뒤에도 사용자가 기존 오류가 그대로 재현된다고 보고했다.
- 이전 수정은 settings host/page의 theme 재진입과 제품 manifest/HKCU 권한 경로를 중심으로 닫았지만, 공용 dialog base와 실제 installer launch chain은 동일한 범위로 검증하지 않았다.

**최초 실제 오류**
- `CModernDialog`, `CResizingDialog`, `TitleDlg`의 child Edit/Combo/List/Tree/Tab 경로는 Dark/non-High-Contrast에서도 `applyExplorerControlTheme()`를 호출하고 있었다. 이 클래스들은 동시에 ThemePalette 기반 background/text를 직접 소유하므로 settings dialog에서 이미 제거한 native Explorer/light chrome 혼합이 다른 다이얼로그들에는 남아 있었다.
- `dist/setup.nsi`는 `RequestExecutionLevel admin`인 elevated installer이면서 finish page에서 `fxfile.exe`를 실행할 수 있었고, `.onInstSuccess`에서는 `fxfile-launcher.exe`를 자동 시작했다. launcher의 hotkey path는 다시 `ShellExecute`로 `fxfile.exe`를 시작하므로 설치 직후 elevated parent token이 launcher와 후속 fxfile 실행에 이어질 수 있었다.
- 기존 source invariant는 settings의 `refreshModernAppearance(XPR_FALSE)` 토큰과 product manifest의 `asInvoker`만 확인했고, 위 공용 dialog 3종의 Dark association 정책과 elevated installer auto-launch 부재는 검사하지 않았다.

**원인 진단**
- Root cause 1: 동일한 ModernUI 정책을 settings 전용 수정으로 닫고, 실제로 50개 이상의 command/resizable dialog가 공유하는 base class까지 확장하지 않았다.
- Root cause 2: executable manifest 권한과 "누가 executable을 시작하는가"를 별개로 보지 않았다. `asInvoker`는 이미 elevated인 parent에서 시작된 child를 강제로 de-elevate하지 않는다.
- Root cause 3: static regression guard가 수정된 파일의 token 존재만 확인해, 동일 증상을 만드는 다른 활성 경로를 탐지하지 못했다.

**해결 방법**
- `gui/ModernDialog.cpp`, `gui/ResizingDialog.cpp`, `cmd/title_dlg.cpp`: Explorer-theme 대상 child control은 Dark/non-High-Contrast에서 `resetControlTheme()`을 사용하고 Light/System/High Contrast에서는 기존 `applyExplorerControlTheme()` 경로를 유지한다. 기존 HWND association cache는 동일 요청 재적용을 계속 차단한다.
- `dist/setup.nsi`: elevated installer의 finish-page product run과 `.onInstSuccess` launcher 자동 실행을 제거한다. 설치된 fxfile/launcher는 이후 정상 사용자 shell/shortcut 또는 앱 설정 경로에서 시작한다.
- `build/validate_source_invariants.py`: 공용 dialog 3종에 Dark reset + HC fallback 계약을 추가하고, installer에서 finish-page run/`.onInstSuccess`/launcher ExecShell 재도입을 금지한다.
- `build/installer_smoke.ps1`: 동일 elevated auto-launch 부재를 installer smoke contract inspection에서 직접 검사한다.

**재발 방지**
- custom Dark paint를 소유하는 공용 base class는 개별 dialog와 별도로 theme association ownership을 검증한다.
- 권한 문제는 manifest만 보지 않고 installer/launcher/scheduled-startup 등 실제 parent launch chain까지 추적한다.
- "수정된 경로"만 토큰 검사하지 말고 동일 base/active path의 sibling 구현도 invariant 범위에 포함한다.

**검증 상태**
- Connector source audit: PASS — 공용 dialog base의 기존 Explorer-theme 호출, installer elevated auto-launch chain, 기존 invariant 누락을 현재 `main` source에서 확인했다.
- 변경 source self-check: PASS — 세 공용 base에 Dark reset/Light·HC Explorer fallback이 함께 존재하고 installer auto-launch token이 제거되도록 commit 전 검사했다.
- `python build/validate_source_invariants.py`: NOT TESTED — connector 환경에는 repository checkout command 실행 경로가 없다.
- MSVC compile/link, `local_ci.bat x64`, installer 실제 실행, 설치 직후 standard-user token 확인, Windows 11 Light/Dark/System/High Contrast 및 반복 dialog open/close runtime: NOT TESTED.

---

## 2026-09-23 — Preferences 무한 순회와 Dark menu text fallback

**오류 발생**
- 사용자 실제 Windows 11 screenshot에서 상단 menu bar가 Dark chrome 위에 검은 글자를 그려 가독성이 무너졌고, `도구 -> 환경설정`을 열면 여전히 응답없음이 재현됐다.
- screenshot title에는 `관리자: fxfile`도 남아 있어 실행 중인 기존 elevated instance/launcher 상태가 아직 정리되지 않았다는 evidence가 있었지만, 이번 hang 자체는 settings source에서 별도의 결정적 무한 순회 원인을 확인했다.

**최초 실제 오류**
- `CfgDlg::applyModernAppearanceToChild()`는 GROUPBOX를 owner-draw화한 뒤 `SetWindowPos(..., HWND_BOTTOM, ...)`으로 sibling z-order를 바꿨다.
- 동시에 같은 함수와 `applyModernAppearanceToChildren()`가 live sibling chain에서 `GetNextWindow()`를 계속 따라갔다. 두 개 이상의 GROUPBOX가 있으면 현재 항목을 bottom으로 옮길 때 이전 GROUPBOX가 다시 다음 sibling이 되어 A -> B -> A -> B 형태로 반복 방문할 수 있었다. 초기 `CfgGeneralDlg` 자체가 여러 GROUPBOX를 포함하므로 Preferences open 직후 hang과 직접 일치한다.
- `ListCtrlEx` / `TreeCtrlEx`의 Vista-enhanced 경로는 Dark 여부와 무관하게 Explorer theme association을 요구했다. settings parent는 Dark에서 같은 HWND를 `resetControlTheme()` 대상으로 취급하므로 control ownership도 서로 충돌했다.
- `CMenuBar::OnCustomDraw()`는 palette `clrText`를 채웠지만 최종 glyph/text drawing은 ToolbarWindow32 기본 renderer에 남겨두었다. 실제 screenshot에서 Win11 renderer가 dark chrome 위에 검은 `COLOR_BTNTEXT` 계열로 fallback하는 결과가 확인됐다.
- 기존 soft-surface invariant는 오히려 `CWnd *sNextChild = sChild->GetNextWindow()` token을 요구해 z-order 변경 중 live traversal 패턴을 보호하고 있었다.

**원인 진단**
- Root cause 1: paint/z-order mutation과 sibling enumeration을 같은 live list에서 수행했다.
- Root cause 2: `mVistaEnhanced`를 visual-style ownership과 동일시해 palette-owned Dark surface에서도 Explorer association을 복원했다.
- Root cause 3: custom draw color field 설정을 실제 text renderer ownership으로 오해했다. screenshot evidence는 field wiring만으로 최종 text color가 보장되지 않음을 보여줬다.
- Root cause 4: regression guard가 실제 안전 속성이 아니라 당시 구현 token 자체를 고정했다.

**해결 방법**
- `cfg/cfg_dlg.cpp`: 각 parent의 direct child HWND를 `SnapshotChildWindows()`로 먼저 vector에 고정한 뒤 processing한다. GROUPBOX가 `HWND_BOTTOM`으로 이동해도 enumeration 순서는 더 이상 변하지 않는다.
- `gui/ListCtrlEx.cpp`: Vista-enhanced list도 Dark/non-High-Contrast에서는 `resetControlTheme()`을 유지한다. `WM_THEMECHANGED`에서는 `refreshModernAppearance(XPR_FALSE)`로 repaint/header refresh만 수행하고 association을 다시 바꾸지 않는다.
- `gui/TreeCtrlEx.cpp`: Vista-enhanced tree 역시 Dark/non-High-Contrast에서는 Explorer association을 강제하지 않는다.
- `gui/rebar/MenuBar.cpp`: non-High-Contrast Win11 path에서 menu text를 ThemePalette color로 직접 `DrawText`하고 `CDRF_SKIPDEFAULT`로 native toolbar text fallback을 차단한다. keyboard accelerator/focus cue는 `WM_QUERYUISTATE`를 존중한다.
- `build/validate_source_invariants.py`: stable child snapshot을 요구하고 live `GetNextWindow` traversal을 금지하며, List/Tree Dark ownership과 explicit menu text draw를 검사한다.

**재발 방지**
- child z-order/style을 바꾸는 traversal은 대상 HWND를 먼저 snapshot한다.
- behavioral enhancement flag와 visual theme association ownership을 분리한다.
- Dark owner-draw surface에서 native renderer의 color field만 설정한 경우 screenshot/runtime evidence 없이 readability PASS로 간주하지 않는다.
- invariant는 구현 모양보다 안전 속성(안정된 enumeration, notification 중 no-retime, explicit text ownership)을 검사한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — 상단 menu text contrast 실패, Preferences 응답없음 재현.
- Connector source audit: PASS — settings GROUPBOX live traversal cycle, List/Tree association conflict, menu native text ownership을 현재 `main`에서 확인했다.
- 변경 source self-check: PASS — stable HWND snapshot, no-retime `WM_THEMECHANGED`, Dark list/tree reset, explicit menu `DrawText` token을 commit 전 확인했다.
- `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`, Windows 11 Preferences 반복 open/close 및 screenshot visual: NOT TESTED in connector-only environment.

---

## 2026-09-23 — Filtering white surface, address selection box, disabled toolbar glyphs

**오류 발생**
- 사용자 최신 Windows 11 screenshot에서 Dark settings의 Filtering list/header가 흰색으로 남고 일부 기본 filter text가 검게 표시됐다.
- main window address field도 흰색 field와 현재 folder name 주위의 별도 검은 사각형을 보였고, Cut/Copy/Undo 등 실제 toolbar button은 존재하지만 disabled 상태에서 glyph가 보이지 않았다.
- top menu text도 일부 상태에서 여전히 native black fallback이 관찰됐다.

**최초 실제 오류**
- `CfgAppearanceFilteringDlg`는 item custom draw에서 `FilterItem::mColor`만 설정하고 list background/text-background/header renderer는 전혀 Dark palette로 전환하지 않았다. historical default black filter도 그대로 출력했다.
- `AddressBar`는 `CComboBoxEx`에 legacy `CBS_OWNERDRAWFIXED`를 설정했지만 대응 `DrawItem` owner가 없었다. 또한 child edit의 `WM_CTLCOLOREDIT`가 어느 parent HWND로 전달되는지에 따라 inner ComboBox subclass만으로는 palette brush routing이 보장되지 않았다.
- `CToolBarEx::SetIconType()`는 main toolbar에 disabled bitmap resource가 없을 때 disabled image list를 제공하지 않았다. Dark mode는 ToolbarWindow32 theme를 disable하므로 native disabled synthesis에 맡긴 Cut/Copy/Undo glyph가 dark chrome에서 사실상 사라질 수 있었다.
- `CMenuBar` explicit text path는 custom-draw `dwItemSpec`을 command id로만 해석했다. legacy/index-shaped notification에서는 item lookup이 실패해 native text renderer로 되돌아갈 수 있었다.

**원인 진단**
- Root cause 1: parent settings surface만 Dark를 소유하고 legacy child list/header의 final background renderer는 native light 상태로 남았다.
- Root cause 2: composite address control의 border만 제거하고 closed-field owner-draw/style 및 실제 CTLCOLOR message parent를 끝까지 정리하지 않았다.
- Root cause 3: enabled/hot icon overlay만 검증하고 disabled state의 image-list ownership을 검증하지 않았다.
- Root cause 4: menu text 직접 그리기 자체는 추가했지만 item resolution failure가 native fallback을 다시 허용했다.

**해결 방법**
- `cfg_appearance_filtering_dlg.*`: list body에 ThemePalette background/text-background를 적용하고 `FlatHeaderCtrl`로 header를 palette-owned rendering으로 전환한다. legacy pure-black filter text만 Dark에서 automatic `mText`로 처리하고 explicit user colors는 유지한다. Dark list의 legacy native border/client-edge도 제거한다.
- `address_bar.*`: unused `CBS_OWNERDRAWFIXED`를 제거하고 outer `AddressBar` 자체에 `WM_CTLCOLOR` handler를 추가해 Edit/ListBox/Static palette brush가 실제 message parent에서도 적용되도록 한다. 기존 child subclass routing은 fallback/inner-parent 경로로 유지한다.
- `ToolBarEx.cpp`: disabled resource가 없는 Dark toolbar는 cold image list를 duplicate해 explicit disabled image list를 만든다.
- `main_toolbar.cpp`: Fluent migrated frames의 disabled copy는 `ThemePalette.mSecondaryText` 색 glyph로 교체한다.
- `MenuBar.cpp`: custom-draw `dwItemSpec`이 command id로 해석되지 않을 때 유효한 zero-based button index fallback을 사용해 explicit Dark text drawing을 유지한다.
- `validate_source_invariants.py`: Filtering body/header palette, address no-owner-draw + outer CTLCOLOR, explicit disabled image list/Fluent disabled glyph, menu item fallback을 deterministic contract로 추가한다.

**재발 방지**
- Dark child control은 parent palette만 확인하지 말고 body/header/disabled/selection 등 각 최종 renderer state를 screenshot 기준으로 확인한다.
- owner-draw style은 실제 DrawItem/custom-draw owner가 없으면 사용하지 않는다.
- toolbar icon contract는 enabled/hot뿐 아니라 disabled/check/pressed state의 image source까지 포함한다.
- composite control의 CTLCOLOR는 추정 parent가 아니라 실제 outer/inner parent 경로 모두에서 palette routing을 보장한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — Filtering white surface/black text, white address field/black folder rectangle, missing disabled toolbar glyphs, remaining black menu text 확인.
- Connector source audit: PASS — 위 네 source ownership gap을 현재 `main`에서 확인했다.
- 변경 source self-check: PASS — palette list/header, no `CBS_OWNERDRAWFIXED`, outer `ON_WM_CTLCOLOR`, duplicated disabled image list + secondary Fluent glyph, menu index fallback을 commit 전 확인했다.
- `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`, 실제 Windows Light/Dark/System/High Contrast screenshot 및 toolbar enabled/disabled interaction: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Theme switch split-brain, menu native text, list-header clipping

**오류 발생**
- 사용자 최신 screenshot에서 main window는 Dark인데 이미 열린 Preferences는 Light 상태로 남아 한 번의 theme switch가 UI 전체에 원자적으로 적용되지 않았다.
- 같은 Dark main window의 top menu text는 계속 검정/짙은 native foreground로 보였고 file-list header의 `이름 / 크기 / 종류 / 수정한 날짜` 글자가 세로 방향으로 살짝 잘렸다.

**최초 실제 오류**
- `MainFrame::setOption()`은 theme mode 변경 시 `SendMessageToDescendants(WM_SETTINGCHANGE, ...)`만 호출했다. Preferences는 MainFrame child가 아니라 별도 top-level/owned window이므로 이 broadcast에서 구조적으로 제외됐다.
- `CMenuBar::OnCustomDraw()`는 custom-draw `dwItemSpec`을 command/index로 해석한 뒤에만 app-owned `DrawText`를 실행했다. runtime screenshot은 해당 resolution branch가 최종 text ownership을 확보하지 못하고 ToolbarWindow32 native text fallback이 남는다는 evidence다.
- `FlatHeaderCtrl::resizeWindow()`는 font가 바뀌어도 기존 header window height를 그대로 재사용했다. modern UI font/DPI가 legacy header height보다 큰 환경에서는 custom-drawn glyph의 상하가 clip될 수 있었다.

**원인 진단**
- Root cause 1: app theme mode는 process/global state인데 refresh scope는 MainFrame descendant tree로 제한했다.
- Root cause 2: final renderer ownership을 command/index inference 성공 여부에 의존했다.
- Root cause 3: typography를 modern font로 교체하면서 vertical control metric은 legacy window height에 남겼다.

**해결 방법**
- `main_frame.cpp`: current UI thread의 모든 top-level window를 `EnumThreadWindows`로 열거하고 frame theme, `WM_SETTINGCHANGE`, descendant refresh, full redraw를 한 theme-change transaction으로 적용한다. 이미 열린 Preferences/owned dialog도 같은 pass에 포함한다.
- `MenuBar.cpp`: `TB_GETBUTTONTEXT`로 custom-draw item command id의 실제 toolbar text를 직접 조회하고 ThemePalette foreground로 그린 뒤 `CDRF_SKIPDEFAULT`로 native black-text fallback을 차단한다. legacy sequential menu id fallback만 보조 경로로 유지한다.
- `FlatHeaderCtrl.cpp`: current UI font의 `TEXTMETRIC.tmHeight + tmExternalLeading`과 DPI-scaled vertical padding으로 header height를 매번 계산하고 font/theme/DPI refresh 시 재적용한다.
- `validate_source_invariants.py`: top-level theme broadcast, toolbar-id text ownership, font/DPI-derived header height를 safety contract로 추가하고 ambiguous `CommandToIndex(dwItemSpec)` 의존을 금지한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — split Light/Dark Preferences, Dark menu black text, header vertical clipping 확인.
- Connector source audit: PASS — 세 root cause를 현재 `main` source에서 확인했다.
- Source contract self-check: PASS — top-level enumeration, `TB_GETBUTTONTEXT` + `CDRF_SKIPDEFAULT`, TEXTMETRIC/DPI height contract를 commit 전 확인했다.
- Windows runtime theme switch, actual Dark menu foreground, header clipping screenshot, `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Legacy green active stripe and persistent address-field outline

**오류 발생**
- 사용자 최신 Windows 11 screenshot에서 탐색 pane 상단에 밝은 녹색 가로선이 계속 보였고, 현재 위치 `내 문서`를 표시하는 address field에는 포커스 여부와 무관한 밝은 사각 테두리가 남았다.
- 사용자가 제공한 Windows 11 File Explorer reference에는 동일한 full-width green stripe나 persistent white location-box outline이 없다.

**최초 실제 오류**
- `ActivateBar::applyModernAppearance()`는 non-High-Contrast에서도 active pane이면 `gOpt->mConfig.mActiveViewColor`를 그대로 사용했다. 기본값 `DEF_ACTIVED_VIEW_COLOR`는 `RGB(48,192,48)`이고, `ExplorerView::recalcLayout()`가 이 컨트롤에 `getActivePaneIndicatorThickness()` 높이를 항상 할당해 screenshot의 녹색 full-width stripe가 만들어졌다.
- `AddressBar::OnNcPaint()`는 non-High-Contrast idle 상태에서도 `ThemePalette.mBorder`로 전체 window `FrameRect`를 그렸다. nested native borders를 제거했더라도 이 app-owned frame 자체가 persistent white/bright outline으로 남았다.

**원인 진단**
- Root cause 1: legacy active-pane color option을 현대 tab/surface selection state와 중복해서 별도 horizontal accent로 계속 렌더링했다.
- Root cause 2: address-bar modernization이 native double-border 제거에 집중하면서 app-owned outer frame은 normal state에서도 항상 보이게 유지했다.

**해결 방법**
- `activate_bar.cpp`: non-High-Contrast에서는 legacy configured active color를 더 이상 그리지 않고 surrounding `ThemePalette.mWindow`를 사용한다. High Contrast active state는 system-selection palette를 유지한다.
- `explorer_view.cpp`: non-High-Contrast에서는 ActivateBar 높이를 0으로 collapse하고, High Contrast에서만 기존 active indicator thickness를 사용한다. TabCtrl의 pane-active selected surface는 그대로 유지한다.
- `address_bar.cpp`: idle non-client edge는 field surface인 `mElevated`와 같은 색으로 그려 persistent outline을 없애고, 실제 keyboard/mouse focus일 때만 `mFocus` frame을 표시한다.
- `validate_source_invariants.py`: non-HC active stripe collapse, legacy `mActiveViewColor` paint 금지, focus-only address border와 idle `mBorder` 금지를 regression contract로 추가한다.

**검증 상태**
- 사용자 screenshot: FAIL before fix — bright green full-width stripe와 persistent white `내 문서` outline 확인.
- Connector source audit: PASS — `DEF_ACTIVED_VIEW_COLOR -> ActivateBar -> ExplorerView layout`, `AddressBar::OnNcPaint -> mBorder` 경로를 확인했다.
- Source contract self-check: PASS — non-HC zero-height stripe, neutral ActivateBar paint, idle `mElevated`/focused `mFocus` address frame을 commit 전 확인했다.
- Windows runtime screenshot, keyboard-focus accessibility, High Contrast active-pane indication, `python build/validate_source_invariants.py`, MSVC compile/link, `local_ci.bat x64`: **NOT TESTED** in connector-only environment.

---

## 2026-09-23 — Win11 source invariant preflight crashed on missing `header` registration

**오류 발생**
- 사용자 `local_ci.bat x64` 실행이 Visual Studio 2026 x64 solution 생성 전 source invariant/regression preflight에서 종료됐다.
- Python traceback은 `validate_win11_stability_regressions()`의 `contents["header"]` 접근에서 `KeyError: 'header'`를 보고했다. 따라서 이번 FAIL은 C++ compile/link 결과가 아니라 validator 자체의 integration 오류다.

**최초 실제 오류**
- 최근 file-list header clipping 회귀 guard가 `FlatHeaderCtrl.cpp`의 font/DPI metric token을 검사하도록 추가됐지만, 같은 함수의 `paths` map에는 `"header": FXFILE_SRC / "gui" / "FlatHeaderCtrl.cpp"` 등록이 빠져 있었다.
- 그 결과 source file read 단계에서는 오류가 없었고, 뒤쪽 direct dictionary access에서 Python exception이 발생해 정상적인 invariant error reporting도 건너뛰었다.

**원인 진단**
- Root cause 1: 새 regression assertion과 해당 assertion의 source-registration 변경을 하나의 invariant contract로 검토하지 않았다.
- Root cause 2: validator 내부 `contents`가 plain `dict`여서 source-registration 누락이 deterministic validation failure가 아니라 traceback으로 바뀌었다.
- Root cause 3: 직전 UI 논리 작업 종료 시 validator 자체의 source-key completeness를 정적 대조하지 않았다.

**해결 방법**
- `build/validate_source_invariants.py`: `validate_win11_stability_regressions()`의 `paths`에 `FlatHeaderCtrl.cpp`를 `header` key로 등록했다.
- 같은 함수의 contract contents map에 `__missing__` fallback을 추가해 향후 등록 누락이 발생하면 `missing source registration for contents[...] ` 오류를 누적하고 빈 source로 이어서 검사하도록 했다. 따라서 regression validator는 source integration 오류를 traceback이 아니라 일반 preflight failure로 보고한다.
- Connector-side static cross-check로 해당 함수의 모든 literal `contents["..."]` key와 `paths` key를 대조했고 누락이 0개임을 확인했다.

**재발 방지**
- regression guard가 새 source key를 참조하면 같은 논리 작업에서 source path registration까지 함께 검토한다.
- validator 내부 integration 실수는 Python exception으로 종료시키지 말고 deterministic validation error로 반환한다.
- invariant 변경 checkpoint에는 최소한 function-local source-key/reference completeness 대조를 포함한다.

**검증 상태**
- 사용자 local CI before fix: FAIL — source invariant/regression preflight에서 `KeyError: 'header'`; project generation/MSVC compile은 시작되지 않음.
- Connector source audit after fix: PASS — `header` source registration 존재, direct `contents["..."]` reference 대비 missing key 0개, defensive missing-key reporting 존재.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after this commit.
- `local_ci.bat x64`, VS 2026 project generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after this commit.

---

## 2026-09-23 — Rebar wrapper bypassed child toolbar/menu notification reflection

**오류 발생**
- 사용자 최신 screenshot에서도 Dark top menu text가 계속 검게 보였다.
- `CMenuBar::OnCustomDraw()`에는 이미 ThemePalette text, explicit `DrawText`, `CDRF_SKIPDEFAULT`가 있었으므로 단순 색상 값 문제로 설명되지 않았다.

**최초 실제 오류**
- `CMenuBar`와 `CToolBarEx`는 `ON_NOTIFY_REFLECT(NM_CUSTOMDRAW, ...)`에 의존한다.
- 그러나 부모 wrapper인 `CSizableReBar::OnNotify()`는 내부 rebar control의 id(`wParam == 1`)가 아니면 즉시 `return FALSE;`했다.
- 따라서 child toolbar/menu notification이 MFC 기본 `CControlBar::OnNotify()` routing/reflection으로 전달되지 않을 수 있었고, 이 경우 모든 child custom-draw 코드는 source에 존재해도 runtime에서 최종 renderer가 되지 않는다.

**원인 진단**
- Root cause: wrapper control이 내부 rebar notification과 child-band notification을 같은 방식으로 차단했다.
- 기존 regression guard는 child `NM_CUSTOMDRAW` handler token의 존재만 검사했고, 그 handler까지 notification이 실제로 도달하는 routing contract는 검사하지 않았다.

**해결 방법**
- `gui/rebar/SizableReBar.cpp`: `wParam != 1` child-band notification을 `CControlBar::OnNotify(wParam, lParam, pResult)`에 위임한다.
- 내부 rebar(id 1)의 `RBN_*` handling은 기존 구현을 유지한다.
- `build/validate_source_invariants.py`: command-surface contract가 base `OnNotify` delegation을 요구하고 해당 block의 `return FALSE;` 재도입을 금지한다.

**검증 상태**
- User screenshot before fix: FAIL — Dark menu text remains black.
- Connector source audit: PASS — reflection bypassing branch and child `ON_NOTIFY_REFLECT` dependency confirmed.
- Source contract after fix: PASS by connector inspection.
- Windows runtime screenshot after fix: **NOT RETESTED**.

---

## 2026-09-23 — AddressBar inner native edge repainted after outer-frame flattening

**오류 발생**
- 사용자 최신 screenshot에서도 current-folder `내 문서` row가 밝은 흰색 outline으로 둘러싸여 있었다.
- 이전 수정은 outer `AddressBar::OnNcPaint()`의 idle frame color만 바꿨지만 실제 화면은 변하지 않았다.

**최초 실제 오류**
- `AddressBar`는 outer `CComboBoxEx`, inner `ComboBox`, inner `Edit`의 복합 control이다.
- outer style에서 `WS_BORDER` / `WS_EX_CLIENTEDGE`를 제거해도 inner native ComboBox/Edit는 자신의 paint/non-client paint 단계에서 edge를 다시 그릴 수 있었다.
- 따라서 outer `OnNcPaint()`를 먼저 flatten해도 final renderer가 inner native control이면 screenshot에는 bright edge가 그대로 남는다.

**원인 진단**
- Root cause: composite control의 최종 paint ownership을 outer HWND만 기준으로 판단했다.
- 이전 invariant도 outer frame color contract만 검사했고 inner ComboBox/Edit post-paint edge ownership은 보호하지 않았다.

**해결 방법**
- `address_bar.cpp`: `PaintFlatAddressEdge(HWND, COLORREF)`를 추가해 현재 DPI 기준 2px edge를 palette `mElevated`로 덮는다.
- outer `AddressBar::OnNcPaint()`는 High Contrast 외에는 persistent focus/white outline을 그리지 않고 flat edge만 유지한다.
- inner ComboBox는 native `WM_PAINT` 뒤와 `WM_NCPAINT` 뒤에 flat edge를 다시 적용한다.
- inner Edit도 `WM_NCPAINT` 뒤에 flat edge를 적용해 native edge가 최종 renderer가 되지 않게 한다.
- invariant는 focus/border outline 재도입을 금지하고 outer/inner flat-edge tokens를 요구한다.

**검증 상태**
- User screenshot before fix: FAIL — bright outline still present.
- Connector source audit: PASS — outer-only ownership gap and inner native final-paint paths confirmed.
- Source contract after fix: PASS by connector inspection.
- Windows runtime screenshot after fix: **NOT RETESTED**.

---

## 2026-09-23 — AddressBar flat-edge implementation was rejected by stale invariant contracts

**오류 발생**
- 사용자 `local_ci.bat x64` 재실행은 source invariant/regression preflight까지 정상 진입했지만 `address: missing Win11 soft-surface token sPalette.mFocus`와 `palette-owned address frame painting is missing` 두 오류로 종료됐다.
- 이 시점에는 project generation/MSVC compile이 시작되지 않았으므로 제품 C++ compile failure가 아니라 validator contract drift였다.

**최초 실제 오류**
- `validate_soft_surface_contract()`의 AddressBar required token이 여전히 `("sPalette.mElevated", "sPalette.mFocus")`였다.
- `validate_win11_stability_regressions()`의 `AddressBar::OnNcPaint()` check는 `CWindowDC sDC(this);`가 함수 본문에 직접 존재해야 한다고 요구했다.
- 그러나 `62ab7978`은 Win11 Explorer reference에 맞춰 persistent focus/white outline을 제거했고, non-client edge painting을 reusable `PaintFlatAddressEdge()` helper로 이동했다. 따라서 두 old assertions는 최신 구현과 직접 모순됐다.

**원인 진단**
- Root cause 1: renderer implementation을 바꿀 때 동일 feature를 검사하는 여러 validator function을 한 번에 갱신하지 않았다.
- Root cause 2: safety property 대신 이전 구현의 local token(`sPalette.mFocus`, local `CWindowDC`)을 요구해 refactor-safe하지 않았다.
- Root cause 3: logical work unit 종료 시 validator 전체의 positive/negative AddressBar requirements 간 모순을 검색하지 않았다.

**해결 방법**
- soft-surface AddressBar contract는 `sPalette.mElevated`와 `PaintFlatAddressEdge`를 요구한다.
- Win11 AddressBar regression contract는 local DC variable 대신 `PaintFlatAddressEdge(m_hWnd, sPalette.mElevated)`를 요구한다.
- 기존 negative contract는 유지한다: `AddressBar::OnNcPaint()`에서 `sPalette.mFocus`, `sPalette.mBorder`, `sFocused`가 다시 나타나면 regression으로 실패한다.
- Connector static scan에서 validator의 `CWindowDC sDC(this)` requirement는 0개, `sPalette.mFocus` reference는 AddressBar `OnNcPaint()` forbidden check 1개만 남았음을 확인했다.

**재발 방지**
- UI renderer refactor 시 동일 component를 검사하는 모든 validator function을 검색해 positive/negative contract를 함께 갱신한다.
- invariant는 helper 위치나 local variable보다 최종 ownership/safety property를 검사한다.
- 서로 모순되는 required/forbidden token이 없는지 logical work unit checkpoint에서 component 단위로 재검색한다.

**검증 상태**
- User local CI before fix: FAIL — source invariant/regression preflight에서 두 stale AddressBar contract failure.
- Connector validator audit after fix: PASS — stale positive requirements 제거, current flat-edge tokens 요구, contradictory AddressBar focus requirement 없음.
- `python build/validate_source_invariants.py`: **NOT RETESTED** on the user's Windows checkout after `63081b85`.
- `local_ci.bat x64`, VS 2026 project generation, Release-x64-Unicode compile/link/runtime smoke: **NOT RETESTED** after `63081b85`.

