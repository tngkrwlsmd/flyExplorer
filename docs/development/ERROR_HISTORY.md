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

## 오류를 예방하기 위한 일반 개발 규칙

1. 새 header/API/macro는 소유 header를 직접 include한다. PCH/transitive include에 기대지 않는다.
2. generated project가 아니라 GYP/build canonical source에서 dependency와 configuration을 고친다.
3. 첫 실제 compiler/linker/CI orchestration error를 먼저 고친다. cascade 숫자를 결함 개수로 해석하지 않는다.
4. CI/build script 안에 다른 shell 언어를 embed할 때 cmd/PowerShell quoting과 escape 책임 경계를 분리한다.
5. static validator는 가능한 한 deterministic contract를 검사하되, 단순 문자열 token 때문에 정상 코드를 거짓 실패시키지 않도록 실제 syntax/format 변형을 고려한다.
6. 오류를 한 번 고친 후 반복 가능성이 있으면 가장 싼 자동 방어선을 같이 추가한다.
7. 제품 build PASS와 CI orchestration PASS, runtime PASS, visual PASS는 서로 다른 evidence로 기록한다.
