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
