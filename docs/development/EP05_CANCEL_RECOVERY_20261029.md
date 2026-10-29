# 2026-10-29 — EP05 충돌 확인 취소 후 명령 복구

## 정확한 소스와 실행 파일

- 시작 main: `6eaa6384649240f0145e8e952b0324c7bef96cb2`; 제품 소스는 `7e28366c10a365d9102e54aaf3460282b511b037`과 동일했다.
- 기존 수용 runtime: 소스 `ddd340694fa98442ea8e2bfcde6139901aac94c9`, EXE SHA256 `5fef82d04f58a9640a4bab2db4b64cd496e2675d64ffe3ce5315c6353e0f4fb4`.
- 위 main의 최초 Release: EXE `d178c4e14b54ba18923149bf0db4f04ba58bd26ffacab8d9b34617bc907a8d96`, [중앙 #40853467641](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40853467641), build exit 0, 75.212초. 호환 캐시를 재사용했으나 LTCG IPDB/IOBJ 불일치로 전체 함수 컴파일 fallback이 있었다. clean/package는 실행하지 않았다.
- 취소 복구 수정: 위 main + `app/winui/m22_transfers.cpp` blob `0c8e8cd7db3bb1a27579a3c56b562fab4db3c725`. Release EXE `bf2de6ba515c072cf30bb075052e7380b0a74479bd2d5dc23b42f348492929a2`.
- helper는 `88017a2c25ed70a7cd0a615aa75f2a7a3632bb9f4085fb82089b718454c744fd`로 유지됐다. 증거는 이 소스/blob/실행 파일에만 해당한다.

## 실제 결함과 최소 수정

`7e28366c`는 pending collision 동안 명령을 차단했으나, 취소는 worker 완료 콜백 없이 pending token을 해제했다. 이 경로에서 toolbar readiness를 다시 계산하지 않아 취소 후에도 버튼이 비활성으로 남았다. [#40856964667](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40856964667)에서 재현됐다.

`ApplyTransferStartStatus`의 terminal 상태 처리 뒤 `UpdateCommandAvailability()`를 호출한다. Cancelled/AllSkipped 및 worker 시작 실패 이후에도 현재 선택·활성 패널·busy/token에 따라 재계산하며 버튼을 강제로 활성화하지 않는다. Controller·파일 처리·세션 정책은 바꾸지 않았다. 관련 소스 계약 12/12 PASS (`test_command_availability_contract.py`, `test_transfer_confirmation_identity_contract.py`). AllSkipped의 실제 GUI 실행은 이번 범위 밖이다.

## 기능 GUI와 독립 픽셀 검토

[중앙 #40857952150](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40857952150)의 **Release, collision-light, collision-dark 단계 PASS**. 전체 job은 뒤의 native/navigation harness 실패로 **FAIL**이며 성공으로 바꾸지 않는다.

Windows VM 대화형 사용자, x64 Release, 96 DPI, 1160×640, 테스트 소유 Left/Right 각각 같은 이름의 .txt 1개. 앱 내부 Copy의 충돌창을 열고 **취소만** 수행했다. 전역 클립보드·휴지통·사용자 파일을 조작하지 않았다.

- CreateFolder/Rename/WindowsCut/WindowsCopy/WindowsPaste/Recycle/Copy/Move 8개: 준비 시 모두 true → 확인 중 모두 false → 취소 후 모두 true (Light/Dark).
- Left 주소·선택과 양쪽 1개 목록, 소스/대상 원래 바이트 보존. 양쪽 정상 종료 0, 기존 설정 6개 presence/hash 보존, 통과한 fixture/프로필 제거.
- 실제 HWND PNG 6장(변경 전 Light 2장, 변경 후 Light/Dark 4장)을 직접 검토했다. 확인창의 문구·취소 버튼과 비활성 명령, 취소 후 두 파일 목록·명령 복구를 확인했다. 한정 기능 GUI와 이 화면의 픽셀은 PASS다. Light에서도 어두운 충돌 대화상자는 기존과 같으며 테마 전체 정합성 수용은 아니다.
- Shift+F10 동안 관측한 메뉴는 ThemePicker의 `시스템`뿐이다. `mutating_menu_observed=false`: **빈 배경 메뉴의 실제 표시/실행과 직접 backend 호출의 GUI 수용으로 확대하지 않는다.** 이 방어는 기존 44/44 소스/모델 증거와 이번 관련 소스 검사 범위다.

| 원본 PNG | SHA256 |
| --- | --- |
| before-light-pending | c4509d77c464d810a1c1f1d49e1bf5633a697950a8e5c50996c4406e94ba42ef |
| before-light-recovered | 35b42a34198dff4ed61238fd722cbe5ce83c7c4437a94df8a97724a0111c7cb2 |
| after-light-pending | bc1ebd6835aa609feeebc877d4850ec65b7258d591227fe3de6e7fabea67a485 |
| after-light-recovered | 8b3288db9d238033c903a97c527fc531523168b65292262368b0bb4927738378 |
| after-dark-pending | bfc1e972c8f1afd819a33ddd48feec6c47b872314c1f788da30911554c101517 |
| after-dark-recovered | 4878c6d29c6a3ac1999ae708c7e5fb499de7532594dabc5e459778bc92eb2bdc |

변경 전 Light는 [#40855739604](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40855739604)의 유효한 앞 단계에서 얻었다. 이 job 자체는 뒤의 메뉴 판정 오류로 FAIL을 유지한다.

## 실패 분류와 남은 실행

- #40854679833: 입력 데스크톱의 SetCursorPos 사용 불가. 이후는 앱 실행 전 GetCursorPos를 확인한다. 사용자 마우스 입력 가능 보고 후 GUI는 위 범위에서 통과했다.
- #40855739604: modal 중 MenuItem이 하나도 없어야 한다는 잘못된 harness 조건. 테마 항목과 실제 변경 명령 관측을 분리했다.
- #40856288037: 초기 행 대기 전 소유 창 focus 부족. focus를 먼저 설정하고 진단을 추가했다. G01 전체 실패/해결로 판정하지 않는다.
- #40856964667: 위의 실제 제품 취소 복구 결함.
- #40857952150: native는 vcvars64.bat의 cmd quoting 오류로 C++ 실행 전 실패. navigation은 동기 관측 시 pending이 이미 끝나 관측 실패. filter는 앞 단계 fixture 잔존으로 미실행. 성능/제품 회귀로 판정하지 않는다.

### 계속할 체크포인트 (미완료)

[중앙 #40859732626](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40859732626), request commit `05e56c6cf014af87a0312078e535fa5386ecfaa5`. 이 기록 시점에 실행 중이다. 대상은 main `6eaa6384` + 위 복구 blob, EXE `bf2de6ba…`. 충돌 Light/Dark를 반복하지 않고 batch 파일로 native compile, 독립 COM MTA의 pending 관측, 별도 fixture-navigation / fixture-filter로 남은 검증을 수행한다.

8,000개 실파일→keep-* 80개, 실제 앱 이름 오름/내림차순 각3회 시간·RSS와 순서, native 비교자 8모드, 후보 Light/Dark 0개 화면 및 필터 해제 복구가 대상이다. **후속 결과를 아직 받지 않았으므로 PASS/개선값을 주장하지 않는다.** 새 test/benchmark 스크립트는 검증 완료 전이므로 main에 넣지 않는다.

다음에는 최신 main과 이 실행 완료 결과를 먼저 대조하고, 성공한 충돌 시험이나 빌드를 반복하지 않는다. 이미지를 독립 검토하고 미완료 영역만 수정한다. 종료 후 소유 fixture/실패 profile과 비교용 runtime의 소유권·hash·비 reparse·앱 부재를 확인해 정리하고, VM의 이번에 확인한 patch만 main에 동기화하고 request slot을 idle로 돌린다. 실행 중 슬롯은 덮어쓰지 않는다. 전체 5개 항목·성능·전체 PX15 완료는 아직 선언하지 않는다.
