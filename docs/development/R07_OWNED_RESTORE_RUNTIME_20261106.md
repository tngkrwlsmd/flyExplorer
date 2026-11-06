# R07-23E 소유 WinUI Rename → private 복원 런타임 경계 (2026-11-06)

## 목적과 안전 경계

실제 WinUI F2 Rename이 만든 검증 영수증을 기존 private 복원 경계로 한 번만 넘기고 DispatcherQueue 완료까지 확인하려는 테스트 전용 단위다. `FlyExplorerR07OwnedRuntimeTest=true`인 명시적 빌드에서만 컴파일되며, 세 환경 경로가 모두 프로세스 로컬 `%TEMP%` 아래이고 실제 원본·대상과 일치할 때만 동작한다. 일반 제품 빌드, XAML/키보드/메뉴, Ctrl+Z, Undo/Redo, 세션 v4에는 진입점이 없다.

## 소스

- 일반 제품과 격리된 런타임 경계: `87267e12be47b782f781671c45d5b69ef7f32736`
- 최초 거절 단계 및 실패 상태 진단: `5b6eecc62add9847ec60f7446e73a0b047d2e96d`
- 기존 경로 계약 형식 유지: `ba0e51eaaf49dbbddad4f3d0f9d6975684f88acc`
- completion disposition 한정 계측: `52631e9ab9612146961e1abb312a157b3e292e96`

## 통과한 검사

- [#42141076080](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42141076080): 관련 소스 21/21, GUI Python 컴파일, 일반 WinUI x64 Release, 일반 EXE에 전용 표식 없음, EXE SHA-256 `ded808c8409eb8ac9810833e7fc9757e32d60c1c5b34e5872e9daac92804a665`, 소유 정리 PASS.
- [#42144517962](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42144517962), [#42145287796](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42145287796): 변경 소스 계약 PASS.
- 세 중앙 실행 모두 테스트 전용 WinUI x64 Release PASS. IPDB/IOBJ가 없어 27,323함수를 전체 생성했다.

## 실제 GUI 결과와 실패 분류

| 실행 | 확인 결과 | 판정 |
| --- | --- | --- |
| [#42143079176](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42143079176) | 실제 F2 Rename 뒤 완료 trace 없음 | private 복원 완료 미도달 |
| [#42144555422](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42144555422) | `original=False; target=True; trace=<missing>` | Rename 성공, 복원 진입 전 실패 |
| [#42145343421](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42145343421) | disposition 계측도 없음, 원본 없음/대상 있음 | `acceptFileCommand` 이후 분기보다 앞선 전달 경계 |

모든 실패 실행에서 테스트 소유 fixture 정리와 레거시 설정 불변은 PASS였다. 실제 사용자 파일·클립보드·휴지통·외부 전송은 사용하지 않았다.

## 현재 판정과 재개점

R07-23E는 **미수용**이다. 자동 복원, 완료 콜백 단회성, 원본 바이트/파일 ID 보존은 실제 GUI에서 입증되지 않았다. watcher에 의한 stale 또는 private 복원 함수 실패로 단정하지 않는다. 다음은 테스트 전용 빌드에서 worker `Post` 반환과 UI task 진입을 계측해 `FileOperationUiPost` 호출 실패와 DispatcherQueue 미실행을 분리한다. 동일 바이너리·동일 GUI 반복은 금지한다.
