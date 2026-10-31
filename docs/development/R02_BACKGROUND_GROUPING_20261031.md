# R02 — 빈 배경 분류 방법 4종 한정 수용 (2026-10-31)

## 목적 및 구현
Windows 11 탐색기와의 직접 비교에서 빠져 있던 빈 배경 **분류 방법** 메뉴를 보강했다. 기존 상단 보기 메뉴의 유형·이름·크기·수정 월 그룹화 명령을 재사용한다. `app/winui/m22_transfers.cpp`의 빈 배경 MenuFlyout에서 현재 활성 패널의 그룹 상태로 체크 표시를 구성하고, 기존 WindowTab/PaneTab·route·폴더·pending/확인창 보호 콜백을 거쳐 `ToggleGroupMode`를 호출한다.

- 제품 SHA: `43588b57ae56766dcdf7e995841df4e943132155`
- 마지막 검사용 SHA: `eb73f964f51624c93f7c99007fb3e63321e4c671` (제품 코드 변경 없음)
- Windows Release [#41158157518](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41158157518) PASS, EXE `61fd80511560f6ada59debff527dbd4c6c7a8a65bfaae0b2810cc2a5d313a006`, helper `3cc8f2e489c9229c8e419199d8b5b63bc512e1c6e503d1943f35984084c08487`. IPDB/IOBJ 불일치로 25,657 함수 전체 코드 생성으로 전환.

## 최초 실패와 교정
- [#41158470446](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41158470446): 마우스 hover로 자식 항목 노출 실패. 테스트 구동 경계 미확정, 전체 FAIL 유지.
- [#41158860708](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41158860708): 앱 소유 메뉴의 물리 클릭으로 '유형' 검색은 통과했으나 검사 도구에 없는 `get_toggle_state()` 호출로 FAIL. 기존 `iface_toggle.CurrentToggleState`로 교정.
- 실패 후 테스트 폴더를 새로 분리하여 기존 진단 로그/fixture를 덮어쓰지 않았다. 변경된 검사용 Python 파일 이외 제품 코드는 변경하지 않았다.

## 실제 검증
- [#41159003202](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41159003202) PASS: 빈 배경 우클릭/분류 방법/유형 적용, .txt·.md·.log 그룹 머리글, 다시 열 때 체크와 유형 재클릭 해제, 파일 원본 바이트·설정 보존, 앱 정상 종료와 성공 fixture/profile 제거.
- [#41159142286](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41159142286) PASS: 동일 제품·소유 폴더에서 생성한 두 PNG 읽기 전용 확인, 원본 1160×640/96 DPI. 실제 화면 직접 검토 결과 네 메뉴 항목, 적용 후 유형 체크, 좌측 그룹 머리글, 우측 파일 목록 유지, 메뉴의 창 내부 배치가 확인됐다. 전체 Windows 11 Explorer 픽셀 동등성은 주장하지 않는다.
- 화면 SHA256: 최초 메뉴 `a55856f4040129c4aed05a83011f66fb097da0e1f32691d41929199ffa7abd72`, 적용 후 체크 `3b790da6ab9ddfd630d409fc30a6aee315b37a758ba61f12f89c24aa35043254`.
- VM 종료 시 source clean, 앱/격리 helper/예약 worker 0; 성공 fixture/profile 제거, 실패 로그와 유효 runtime/cache 보존. VM 슬롯은 `605e67795cd093cac05aaca4d212ba70cffa9065`에서 [skip ci] idle.

## 수용 한계 및 다음 작업
Dark/96 DPI/1160×640, 테스트 소유 로컬 파일 폴더에서의 적용·체크·해제와 화면만 한정 수용한다. 다른 모드·제공자·테마/해상도·모든 창 크기·실제 Explorer 완전 동등성, 사용자 파일/설정·클립보드·실제 휴지통 조작은 미검증이며 수행하지 않는다. 사용자 제외 G03~G05 및 중단 G07 유지. 다음 후보는 R03의 추가 보기 모드이며, 기존 다섯 모드 번호 및 세션 v4 호환 설계부터 수행한다.
