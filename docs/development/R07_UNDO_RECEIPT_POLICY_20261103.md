# R07 실행 취소·다시 실행: 안전한 작업 영수증 기준 (2026-11-03)

## 현행 사실과 위험

- 현재 flyExplorer의 파일 전송은 `IFileOperation`이며 여러 항목을 개별로 처리할 수 있다. 실패·취소 보고에도 앞 항목의 실제 변경이 남을 수 있다. `Report.queued`는 성공 개수나 각각의 결과가 아니다.
- `RenameSelected`는 `MoveFileW`가 기존 이름을 덮어쓰지 않는 방식으로 실행하고, 성공 시 결과에 실제 새 대상 경로(`Result.target`)가 남는다. 하지만 완료 구조체에는 원래 경로가 없어 성공 이후 별도 재구성해야 했다.
- Windows Shell의 `FOF_ALLOWUNDO`와 `FOFX_ADDUNDORECORD`는 Windows Explorer 세션의 Undo 기록과 관련되지만, 앱에서 특정 항목만 안전하게 되돌리는 자체 작업 영수증을 제공하는 API가 아니다. 현재 `shell_transfer_core.cpp`는 Recycle에만 `FOF_ALLOWUNDO|FOFX_RECYCLEONDELETE`를 사용한다. 다른 Windows 응용프로그램의 전역 실행 취소 기록을 Ctrl+Z로 임의 실행하지 않는다.
- Microsoft 공식 근거: https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags

## R07-1 구현: 성공한 이름 변경의 원래 경로만 임시 전달

`FileOperationController::FileCommandCompletion.originalRenameSource`를 추가했다. 파일 명령 worker는 **RenameSelected 요청의 정확한 `request.source`를 실행 전에 값으로 보존**하고, **실제 `execute(request)`가 성공한 경우에만** 원본 경로를 완료 값으로 전달한다. 기존 완료의 `ticket`, `Context`, `result.target`, 상태 판정, UI·디스크 작업과 세션 저장 형식은 변경하지 않는다. 성공 영수증에 필요한 첫 데이터일 뿐, **실행 취소 가능 판정이나 파일 쓰기 허가가 아니다.** 다른 생성/바로 가기 작업이나 실패/취소 결과에는 원래 이름을 제공하지 않는다.

## R07-2 구현: 이름 변경 전후 파일 ID 읽기 전용 증거 (2026-11-03)

단일 로컬 일반 파일의 `RenameSelected` 작업에 **읽기 전용 identity probe**를 추가했다. 기존 이름 변경 엔진(`MoveFileW`, 대상 덮어쓰기 금지)과 작업 완료의 ticket/창·패널·탭·route 바인딩, UI·세션 v4에는 변경이 없다.

- 증거 대상은 고정 로컬 드라이브(`DRIVE_FIXED`)이며 파일과 모든 부모 폴더가 **재분석 지점이 아닌 일반 파일 시스템 경로**여야 한다. 폴더 이름 변경, 재분석 지점, 네트워크·이동식 볼륨, 하드 링크 수가 1이 아닌 파일, 지원되지 않는 파일 ID 조회는 **영수증 미발급**으로 종료한다. **기존 파일 이름 변경 요청은 그대로 수행**되며, 읽기 전용 조회 실패를 작업 실패로 바꾸지 않는다.
- Windows `CreateFileW(FILE_READ_ATTRIBUTES, OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT)`로 기존 파일의 속성만 조회하고 `GetFileInformationByHandleEx(FileIdInfo)`에서 **볼륨 일련번호 + 128비트 파일 ID**를 수집한다. 파일 크기·마지막 수정 시각도 함께 기록하며 이름 변경 전후 **모두 같을 때만** `Result.renameEvidence.verified=true`로 만든다. 탐색 중 접근만 하며 파일에 쓰지 않는다. Microsoft 근거: https://learn.microsoft.com/en-us/windows/desktop/api/winbase/ns-winbase-file_id_info 와 https://learn.microsoft.com/en-us/windows/desktop/api/winbase/nf-winbase-getfileinformationbyhandleex .
- 기존 `originalRenameSource`와 새 `Result.renameEvidence`는 작업 완료에 전달되는 **관측 데이터**일 뿐이며 **실행 취소 가능 판정이나 파일 쓰기 허가가 아니다**. Rename이 완료된 후 외부 프로그램이 수정하거나 원본 이름을 다시 점유할 수 있고, 현재 구현에는 원자적 열린 핸들 기반의 안전한 복원, 충돌/만료 확인, Undo·Redo 명령/단축키가 없다. 복원 전 재검증이 완료되기 전에는 사용자가 누를 수 있는 실행 취소를 만들지 않는다.
- 전용 `test_r07_rename_identity_contract.py`와 기존 `m21_native_fixture.cpp`에 파일 ID의 독립 조회 비교, 폴더 이름 변경의 영수증 미발급, 기존 대상 이름 충돌 시 영수증 미발급/파일 보존 검사를 추가했다. **Windows 단위 네이티브 검증은 후속 #41657292869에서 48/48 PASS**, GUI·픽셀·실제 파일 되돌리기 명령은 NOT TESTED/NOT IMPLEMENTED이며 제품 전체 Release 빌드는 별도 확인 대상이다.

### R07-2 Windows 한정 실행 증거

[Windows VM #41657292869](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41657292869)에서 정확한 제품·시험 소스 `c3486e1b247a22ecec388168eb23166650b59b9c`의 소스 5/5 PASS, M21 네이티브 x64 Release 빌드 PASS, **48/48 실제 테스트용 파일 명령 PASS**, 원본 사용자 설정 불변(`PRESENT 0`), 소유 임시 공간 정리를 확인했다. 처음 [#41656448397](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41656448397)은 Remote Shell의 잘못된 PowerShell 인자로 실행 전 중단, [#41656844843](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41656844843)은 실제 네이티브 48/48 PASS에도 오래된 Python 예상 테스트 수가 37이라 검증기에서 중단됐다. 원인을 수정한 후속 실행만 성공으로 수용한다.

[제품 x64 Release 컴파일 #41657641687](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41657641687)은 **정확한 소스 SHA `c3486e1b247a22ecec388168eb23166650b59b9c`에서 최종 SUCCESS**, `runner-health` 및 `release-build` **EXIT=0 PASS**다. 빌드 전용 범위이므로 **전체 소스/GUI 최종 수용은 아니며**, GUI·픽셀·파일 복원/Undo는 NOT TESTED다.

## R07-3 구현: 파일 복원 전 상태의 읽기 전용 재확인 (2026-11-04)

`filecommand::inspectRenameRestore(originalPath, renamedResult)`는 **복원 명령이 아닌 현재 시점의 관측 함수**다. R07-2 이름 변경 결과에 성공 표시와 확인된 파일 ID가 있어야 하며, 원래 경로와 결과 경로가 같은 안전한 고정 로컬 드라이브/부모 아래의 서로 다른 일반 파일명이어야 한다. 일반 파일·부모 폴더의 재분석 지점이나 불확실한 경로는 거부한다.

- 원래 이름의 `GetFileAttributesW` 조회가 **정확하게 `ERROR_FILE_NOT_FOUND`일 때만** 원래 이름이 비어 있다고 관측한다. 이미 점유되었거나 접근 거부·다른 오류가 발생하면 모두 거부한다. 이 검사는 기존 파일을 열거나 덮어쓰지 않는다.
- 대상 경로의 단일 일반 파일을 **읽기 속성 전용**으로 다시 조회하고, R07-2에서 기록한 볼륨 일련번호·128비트 ID·크기·수정 시각과 전부 비교한다. 불일치하거나 확인 불가능하면 거부한다. `MatchingSnapshotOnly`는 함수 호출 시점에만 두 관측값이 일치했다는 뜻이며 **실제 Undo/Redo 가능 승인, 이름 예약, 외부 수정 방지, 파일 쓰기 허가가 아니다**.
- `FileOperationController`·MainWindow 명령·Ctrl+Z·파일 시스템 변경·세션 v4 및 Windows Explorer 전역 Undo 기록은 수정하지 않았다. 검사 사이와 실제 복원 사이에 다른 프로세스가 원래 이름을 만들거나 대상 파일을 교체할 수 있다. **열린 핸들 기반 경합 방지와 원자적 복원 방식은 아직 미구현**이며, 그전에는 Undo·Redo를 노출하지 않는다.
- `m21_native_fixture.cpp`의 테스트 소유 폴더에서 현재 상태 일치, 유효하지 않은 영수증, 다른 부모/동일 이름, 원래 이름의 재점유, 바뀐 파일 ID, 대상 누락, 파일 내용 변경을 각각 확인한다. 이 과정의 파일 생성·변경·제거는 임시 테스트 소유 공간에만 한정한다. **실제 파일 복원은 전혀 실행하지 않는다.** 별도 Windows 빌드·실행 결과는 정확한 대상 SHA와 함께 후속으로 기록한다.

### R07-3 한정 Windows 실행 증거

[Windows VM #41662348650](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41662348650)는 정확한 변경 소스 `cd3c83d604ac5da4704cfba240a60ef1f6152683`에 대해 R07-1/2/3 소스 계약 **14/14 PASS**, M21 네이티브 x64 Release 빌드 PASS, 일회용 폴더에서의 실제 파일 명령 **55/55 PASS**, 변경 공백 검사 및 소유 임시 체크아웃 정리 PASS로 종료됐다. 사용자 기존 설정도 변경되지 않았다. 추가 7건은 원래 경로 비어 있음·이름 재점유·잘못된 영수증·부모 경로 불일치·파일 ID 불일치·대상 소실·외부 내용 변경의 순간 관측만 검증한다.

공통 `src/base` 연결을 확인하는 [제품 Release 빌드 #41662666694](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41662666694)는 **정확한 R07-3 SHA에서 최종 SUCCESS**로 확인됐다. 이 결과는 후속 R07-4의 전체 제품 빌드를 대신하지 않는다. Release와 독립적으로 실제 Undo/Redo·GUI·시각 검증은 NOT TESTED/NOT IMPLEMENTED이다.

## R07-4 구현 후보: 대상 파일 핸들 보호 및 재검증 (2026-11-04)

`RenameTargetLease`는 기존 R07-2/3의 성공한 이름 변경 결과에만 결합할 수 있는 짧은 수명의 C++ 객체다. `begin`은 먼저 원래 경로의 빈 상태와 128비트 대상 파일 ID를 관측하고, 이어서 대상 파일을 **`FILE_READ_DATA|FILE_READ_ATTRIBUTES`, `FILE_SHARE_READ`, `OPEN_EXISTING`**으로 열어 핸들을 유지한다. 손상되거나 일치하지 않는 파일·다른 부모 경로·재분석 경로·경합으로 열기 실패한 파일은 거부한다. `recheck`는 유지된 핸들의 볼륨·128비트 ID와 대상 경로의 최신 ID·크기·수정 시각, 원래 이름의 비점유를 다시 확인한다. 객체가 소멸하거나 `reset`이 호출되면 `CloseHandle`로 닫는다. 구조체는 복사할 수 없으며 WinUI/작업 큐·세션 저장과 연동하지 않았다.

- 이 핸들의 공유 옵션은 **열린 동안** 대상 파일에 대한 새로운 쓰기·이름 변경·삭제 접근을 제한한다. 기존 쓰기 핸들이 있는 경우 보호 획득 자체가 실패하는지 확인한다. <https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew>
- **원래 이름을 예약하지 않는다.** 타 프로세스가 그 이름으로 새 파일을 만들 수 있어 `recheck`가 다시 거부할 수 있다. 핸들이 닫히면 대상 보호도 해제되므로 이 관측을 파일 복원이나 Undo 허가로 사용하면 안 된다. 기존 매핑, 부모 디렉터리 경합, 공유 모드·파일시스템 차이 등을 감안해 결과를 영구적인 안전 보증으로 간주하지 않는다.
- 비교 API `CompareStringOrdinal`은 실패할 경우 0을 반환한다. R07-3 경로 판단뿐 아니라 기존 이름 변경 경계에서도 **`CSTR_LESS_THAN` 또는 `CSTR_GREATER_THAN`만 서로 다른 경로로 인정**, 0은 실패 폐쇄 처리한다. 같은 이름의 충돌 결과는 계속 `ERROR_ALREADY_EXISTS`, 잘못된 비교는 `ERROR_INVALID_NAME`을 사용한다. <https://learn.microsoft.com/en-us/windows/win32/api/stringapiset/nf-stringapiset-comparestringordinal>
- 소유 테스트 파일에서 보호 중 다른 쓰기·삭제 핸들 열기 거부, 원래 이름 재점유의 재검증, 선행 쓰기 핸들 존재 시 획득 거부와 해제 후 재획득을 실험한다. `RenameTargetLease`는 **파일을 생성·이동·삭제·복원하지 않으며** `DELETE` 접근 권한도 요청하지 않는다. 실제 Undo/Redo·Ctrl+Z·경합 없는 최종 이름 예약/복원은 여전히 **미구현**이다.
- [첫 Windows #41781410527](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41781410527)은 R07 소스 계약 21/21 PASS지만 잘못 사용한 `std::equal_n` 때문에 네이티브 컴파일 FAIL. 이를 표준 `std::equal`로 수정한 뒤 [Windows #41781670269](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41781670269)에서 정확한 제품·테스트 SHA `ec44b50dccc12dc2eb0d48af71ff3262bf7cabf5`의 **R07 계약 21/21, M21 네이티브 Release 빌드, 테스트 소유 파일 작업 60/60, 원본 설정 보존, 소유 체크아웃 정리 PASS**를 확인했다. [전체 제품 x64 Release #41781872051](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41781872051)은 작성 당시 진행 중이며 **별도 최종 확인 대상**이다. GUI·화면 픽셀·실제 Undo/Redo는 미실행이다.

## R07-5 구현: 원본 부모 디렉터리 동일성 유지 (2026-11-05)

`RenameTargetLease`는 대상 파일과 더불어 **원본 이름 및 결과 파일의 공통 부모 디렉터리 핸들**을 유지한다. 부모 디렉터리를 `FILE_READ_ATTRIBUTES`, `FILE_SHARE_READ|FILE_SHARE_WRITE`, `FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT`로 열고 비재분석 디렉터리와 볼륨/128비트 파일 ID를 확인한다. 부모 디렉터리의 삭제/이름 변경에 대한 배타적 차단은 이 핸들만으로 보장되지 않는다. 실제 Windows 네이티브 검사에서는 DELETE 접근이 열릴 수 있어, 기존 DELETE 핸들을 반드시 거부한다는 가정도 폐기한다. 따라서 부모 핸들은 현재 디렉터리의 동일성 재관측용이며 원본 이름·상위 경로의 경합 방지 권한이 아니다. `recheck`에서 유지된 부모 핸들과 최신 경로의 디렉터리 ID가 일치하는지 다시 검사하고, `reset` 및 소멸자에서 두 핸들을 해제한다.

- **원래 파일명은 원자적으로 예약하지 않는다.** 동일 부모에 새 파일을 만드는 경합은 가능하므로 복원 실행을 승인하지 않는다. 조상 디렉터리 경합은 재검증 시 발견할 수 있어도 모든 경합을 차단하는 것은 아니다.
- UI·Undo/Redo·Ctrl+Z·세션 v4·실제 파일 복원 또는 데이터 변경 명령은 연결하지 않는다.
- 소유 Windows 네이티브 검증 69건 중 최초 실행은 **67 PASS / 2 FAIL**이었다([#41951610572](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41951610572)). 두 실패는 부모 DELETE 접근이 언제나 차단된다는 부정확한 가정을 드러냈다. 이후 테스트는 파일 보존·현재 동일성 재확인과 비승인 원칙을 요구하도록 수정했다. 수정본은 후속 [Windows VM #41955278343](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41955278343)에서 정확한 소스 `33c7d1d0625a2b653c63f87159bbd59b050e924b`로 **R07 소스 22/22, 네이티브 컴파일 및 테스트 소유 파일 69/69 PASS**를 확인했다. 과거 실패 기록은 보존하며 원자적 Undo 안전성으로 확대하지 않는다.

### R07-5 보완: 유지 중인 대상 파일 메타데이터 재확인 (2026-11-05)

`RenameTargetLease::recheck`는 저장된 파일 ID와 열린 핸들의 ID만 비교하던 단계에서, 유지 중인 **동일 대상 핸들**의 `FileAttributeTagInfo`·`FileIdInfo`·`FileStandardInfo`·`FileBasicInfo`를 통해 파일 유형, 128비트 ID, 삭제 대기, 하드 링크 수, 파일 크기, 마지막 수정 시각을 다시 검사하도록 강화했다. 그다음 현재 경로로 읽은 파일 정보도 기존 R07-2 증거와 비교하며 원래 이름의 비점유를 따로 관측한다. 서로 다른 시점의 조회가 원자적 파일 복원 권한을 만들지는 않는다.

기존 부모 DELETE 공유 차단 가정을 완화한 테스트와 이번 메타데이터 보강은 [Windows VM #41955278343](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41955278343)에서 정확한 소스의 **22/22 소스 계약·M21 x64 Release 네이티브 컴파일·69/69 소유 파일 검사 PASS**로 확인됐다. 기존 [#41951610572](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41951610572)의 **67/69** 실패 이력은 그대로 보존한다. 앱 전체 WinUI 빌드·GUI·픽셀은 이번에는 검증하지 않았다. 파일 복원용 DELETE 권한 획득, 경합 없는 원본 이름 예약, `SetFileInformationByHandle` 기반 복원, 작업 소유권·Ctrl+Z·Redo는 구현하지 않았다.


## R07-6 구현: 수용된 이름 변경의 임시 작업 소유권 후보 (2026-11-05)

`FileOperationController`는 한 번에 하나의 실제 **수용된 성공 Rename 완료**가 정확한 ticket·현재 창 탭 ID·활성 패널/폴더 탭·route·표시 경로와 일치하고 128비트 파일 ID 영수증이 `verified`일 때만 메모리 후보를 보관한다. 결과를 무조건 Undo 가능으로 표시하지 않으며 복사·이동·폴더 작업·실패·오래된 완료의 결과는 후보가 아니다. 새로운 파일 작업·전송 요청, 창 종료, 조회 시 소유권 불일치는 후보를 무효화하고 ticket 최대값 재사용을 거부한다.

후보 조회는 **파일시스템 작업이 없는 데이터 조회**다. 실제 Undo 실행과 원본 경로 예약을 허용하지 않는다. UI에서 탭 이동을 즉시 알려 후보를 무효화하는 통지는 **아직 연결되지 않았으며**, 미조회 사이의 탭 이동·재진입을 감지할 수 있다고 주장하지 않는다. 향후 복원 작업은 *파일 자체의 열린 DELETE 권한 핸들과 실제 128비트 식별자 재확인, 동일 부모 식별자 재확인, 현재 이름 충돌 원자적 거부, 외부 변경 시 거부, 성공 후 재검증*의 별도 안전 계약을 갖추어야 한다. 기존 R07-5 `RenameTargetLease`의 읽기 전용 핸들은 이름 복원을 수행할 수 없고 부모 DELETE 공유 방식도 원본 이름을 예약하지 않는다.

새 `tests/winui/test_r07_rename_owner_contract.py`는 자료 발급 조건과 거절·무효화 계약을 소스로 검사한다. [Windows VM #41958774791](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41958774791)의 정확한 소스 `67d9ba35be3fb10d1ed466fa8a854772453be26f`에서 R07 Python 소스 계약 **26/26 PASS**(신규 R07-6 4건 포함)와 소유 체크아웃 정리를 확인했다. C++/WinUI 빌드, GUI, 실제 파일 복원은 **NOT TESTED / NOT IMPLEMENTED**이다. 이전 R07-5의 [69/69 네이티브 수용](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41955278343)을 이 새 코드의 수용으로 확대하지 않는다.

## R07-7 구현: 소유권 후보의 단일 인출 (2026-11-05)

`FileOperationController::takeRenameRestoreCandidate`는 성공한 Rename에서 남긴 임시 후보를 요청한 현재 컨텍스트·ticket과 비교하고, mutex를 유지한 채 **후보를 반환하기 전에 컨트롤러의 원본 저장분을 즉시 폐기한다**. 별개 호출이 같은 소유권 후보를 두 번 획득하지 않도록 한다. 메모리 이동 중 오류가 발생해도 후보를 폐기하며, 소유권 불일치가 있으면 값을 반환하지 않는다. 외부 호출자가 이미 받은 값을 별도로 복사하거나 소유권이 바뀐 뒤 재사용하는 일까지 이 메서드로 봉쇄하는 것은 아니다.

이것은 단지 **일회성 메모리 인출 계약**이다. `RenameTargetLease`의 R07-5 읽기 핸들 및 `inspectRenameRestore` 순간 관측과 마찬가지로 원래 이름의 원자적 무덮어쓰기·파일 변경 보호·실제 작업 소유권의 미래 유효성을 증명하지 않는다. 파일을 복원하는 API, 삭제 권한 핸들, `SetFileInformationByHandle`, 복원 승인, GUI Ctrl+Z/Redo는 추가하지 않는다.

새 R07-7 소스 계약은 `tests/winui/test_r07_rename_owner_contract.py`에서 한번 인출·mutex 범위·반환 전 폐기·파일 변이 미도입을 검사한다. 정확한 소스 SHA `15251587b3e22b655a3bd0b67ad7dd76584ad925`의 [Windows VM #41959646943](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41959646943)에서 **신규 R07-7 Python 소스 계약 5/5 PASS**, 전용 체크아웃 정리 PASS를 확인했다. C++/WinUI 빌드·GUI·실제 Undo는 **NOT TESTED**다. 기존 R07-6 26/26 통과는 별도의 이전 SHA에서 검증한 결과다.

## R07-8 구현: UI와 격리된 원본 이름 무덮어쓰기 네이티브 함수 (2026-11-05)

Microsoft `FILE_RENAME_INFO` 문서에 따르면 `SetFileInformationByHandle(FileRenameInfo)`에서 `ReplaceIfExists=FALSE`는 새 이름이 이미 사용 중인 경우 오류로 거부하며 `RootDirectory`는 상대 이름을 해석할 기준 디렉터리 핸들이다. 공식 참조: https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info

`restoreRenameNoReplace`는 원래 이름의 공백을 단순 검사만으로 보증하지 않고, **열린 `DELETE` 권한 대상 핸들에서 실제 파일 동일성/변경 여부를 검증**한 다음 `FileRenameInfo`의 이 원자적 무덮어쓰기 조건을 사용한다. 대상 핸들은 R07-5의 `FILE_READ_DATA|FILE_READ_ATTRIBUTES` 읽기 전용 핸들과 독립적이며, 부모 디렉터리 핸들의 식별자를 유지하고 복원 대상 이름을 이 핸들에 상대적으로 전달한다. 이때 부모 디렉터리의 외부 DELETE 접근은 완전히 차단되지 않는다. 따라서 완료 뒤 경로 동일성이 실패하면 `CommittedUnverified`로 반환하고 자동 롤백하지 않는다. 호출 자체가 실패하면 `NativeCallFailedUnknownState`를 반환해 '아무 파일도 바뀌지 않았다'고 단정하지 않는다.

**R07-8은 독립 원시 함수 소스만 추가된 상태**다. 호출자가 정확한 R07-7 ticket/창/패널/탭/route 소유권을 확인해 인출했는지 이 함수에서 검증하는 것은 아니며, 앱과 연결된 Undo/Redo 승인 권한도 아니다. 새 소스 계약 `tests/winui/test_r07_no_replace_restore_contract.py`는 비연결·부모/파일 동일성·DELETE 권한·원자적 비덮어쓰기·불확실한 완료 상태를 검사한다. [Windows VM #41962356186](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41962356186)에서 정확한 소스 `9cfba11ba63e0daeba3a84702d106991f6ed4f73`의 **R07 소스 32/32, 신규 R07-8 5/5 PASS**, 소유 체크아웃 정리 PASS를 확인했다. 첫 [#41962094352](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41962094352)은 기존 검사 범위가 새 주석까지 포함해 **31/32 FAIL**이었고, 금지 플래그 이름이 들어간 주석만 정리한 후 PASS했다. **C++ 빌드, 테스트 소유 파일의 실제 복원/경합 및 GUI는 NOT TESTED**다. 독립 테스트에서 안전/실패 사례가 수용되기 전 사용자 데이터로 실험하거나 UI에 연결하지 않는다.

### R07-8 테스트 전용 Windows 네이티브 복원 사례 추가 (2026-11-05)

`tests/winui/m21/m21_native_fixture.cpp`에 **테스트 소유 로컬 파일에서만** 실행할 정상 복원·원래 이름 충돌/바이트 보호·위조/누락된 영수증·기존 쓰기 핸들 거부·복원 뒤 파일 ID/바이트 보존·중복 복원 거부를 8건 추가했다. M21 네이티브 예상 건수는 **69 → 77건**이다. 사용자 프로필 보호와 임시 작업공간 정리는 기존 테스트 실행 래퍼 계약을 유지한다. 현재 이것은 *실행될 테스트 시나리오*를 만든 것이지, 파일 복원이 성공했다고 관측한 결과가 아니다.

정확한 SHA `608404a7c9f1cf83cd557f7260259af7e5212bbf`의 [Windows VM #41977843188](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41977843188)에서 **Python R07 소스 계약 34/34 PASS**와 소유 체크아웃 정리만 확인했다. [첫 #41977661567](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41977661567)은 이전 예상 건수(69)를 사용한 소스 검사로 **33/34 FAIL**이었고, 해당 검사 값을 바로잡아 재검사했다. **M21 네이티브 컴파일, 테스트용 파일의 실제 복원 77건, WinUI 앱 빌드, GUI 및 실제 Undo/Redo는 NOT TESTED**다. 원본 파일을 다시 변경하는 함수는 컨트롤러와 UI에 여전히 연결하지 않는다.

### R07-9 네이티브 복원 실제 실패와 현재 금지 조건 (2026-11-05)

복원 함수는 Windows x64 Release 네이티브로 **컴파일 가능**하지만, 실제 소유 파일 이름 복원에서 아직 실패한다. 원본 `FileRenameInfo` 구현의 정확한 [Windows VM #41981398953](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41981398953)은 **75/77 PASS, 2 FAIL**(정상 복원·중복 복원), 진단을 추가한 [#41981791738](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41981791738)은 네이티브 결과 `NativeCallFailedUnknownState`, `ERROR_INVALID_PARAMETER=87`, 호출 시도 1, 원본 이름 부재/변경된 이름 존재를 출력했다. 이어 같은 디렉터리 핸들과 상대 이름을 유지하고 **확장 이름변경 `FileRenameInfoEx`, 플래그 0**만 바꾼 정확한 소스 `9065d22c1c0aeb4436efdd411ca8b7dc64cc4352`의 [#41982303138](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41982303138)은 Python 소스 34/34와 C++ 컴파일은 PASS지만 **네이티브 75/77 FAIL, 동일 오류 87**이었다.

Microsoft 문서가 `RootDirectory`의 상대 이름을 허용하더라도 이번 오류 87이 반드시 그 필드만의 결함임을 입증한 것은 아니다. 원본 이름을 덮지 않는 원자적 변경과 바뀌지 않은 실제 부모 디렉터리의 식별자를 **동시에 보장할 수 있는 방식이 실행 증거로 수용되기 전까지 사용자용 Undo/Redo/단축키에 연결하지 않는다**. 단순 절대 경로 대체, 덮어쓰기 플래그 추가, 호출 실패 뒤 무조건 재시도·롤백, 77건의 정상복원 기대값 완화는 안전 해결책이 아니다. 제품 전체 앱 빌드/GUI/픽셀은 이번에 하지 않았다.

### R07-10 NULL 루트와 단순 파일명의 작업 폴더 오이동 (2026-11-05)

Windows 드라이버 자료는 단순 파일명을 `RootDirectory=NULL`과 사용하는 동일 폴더 이름 변경 형태를 설명하지만, 이 프로젝트가 실제 사용하는 **Win32 `SetFileInformationByHandle(FileRenameInfoEx)`**에서는 그 조합이 의도한 동일 폴더 동작을 제공하지 않았다. Microsoft Win32 문서도 NULL 루트를 기본값으로 설명하면서 FileName에 현재 작업 폴더 상대 이름을 허용한다. 따라서 각 인터페이스의 설명을 섞어 안전을 추정하지 않는다. 문서: https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info 및 https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information

정확한 소스 `c1ab5b2cbbaa554afa621e4e6cdf1fb663e44a9e`의 [Windows VM #41987547104](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41987547104)에서 **R07 소스 35/35·네이티브 x64 Release 컴파일 PASS**, 테스트용 파일 네이티브 **75/77 FAIL**, 복원 호출 자체는 성공이었으나 `CommittedUnverified`·원래 파일명과 대상 파일명 모두 미관측으로 끝났다. 현재 작업 폴더 내 후보 파일의 **볼륨/128비트 파일 ID가 복원 직전 파일과 동일**한지를 조사한 정확한 진단 SHA `5b42e633b643da0df186df3be21530735bc48df1`의 [#41988089601](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41988089601)에서 `cwd_id_match=1`이었다. 즉, **복원할 파일을 원래 부모가 아닌 실행 폴더로 이동**시킨 위험한 동작이었다. 두 폴더 모두 임시 소유 체크아웃이며 사용자 파일·설정은 대상이 아니었다. 호출의 0 오류 코드만으로 안전한 복원이라고 판정하는 것은 금지한다.

제품 함수에서는 `RootDirectory=nullptr`를 되돌려 `RootDirectory=parent.h`를 유지하고, `test_r07_no_replace_restore_contract.py`에 NULL 루트 금지와 부모 ID 재검증을 명시했다. 이 변경 소스 `43dcef7c020cec0fd235fd3988b5fc402954a36b`에서 [Windows VM #41988475539](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41988475539)의 **R07 관련 Python 8/8 PASS**가 확인됐다. 이후 이름만 정리한 테스트 함수 자체는 Windows 재실행하지 않았다. 부모 핸들을 지정한 실행은 기존 **오류 87**을 내므로, 안전한 네이티브 복원 기능 자체는 여전히 **미수용**이다. 파일 내용을 보호한다는 사전 확인과 파일의 **최종 저장 경로**를 보호한다는 사실은 서로 다르다.

사용자용 Undo/Redo 또는 작업 소유권 후보와 연결하기 전, 정확한 **원본 파일 핸들 + 실제 부모 디렉터리 동일성 + 목적지 이름 무덮어쓰기 + 최종 경로/파일 ID 확인**을 같은 테스트에서 검증한다. 루트 핸들을 없애거나 절대 경로로 바꾸는 우회, 오류 이후 자동 재시도·롤백, 검증 없는 GUI 노출은 하지 않는다.

## 후속 필수 단계 (순서 변경 금지)

1. **개별 변경 증거 (R07-2 일부 구현):** 원본·결과의 정확한 단일 항목 식별자(볼륨 식별자와 파일 ID), 재분석 지점 제외, 최종 파일 상태, 실제 생성/이동/복구 성공 정보 등을 worker의 신뢰된 범위에서 수집한다. 이름이나 경로만으로 동일한 파일이라고 간주하지 않는다. 일괄 Copy/Move의 aggregate 완료 수치만으로는 영수증을 발행할 수 없다.
2. **복원 전 재검증 (R07-3 현재 시점 관측만 구현):** 원본 경로가 비어 있고 되돌릴 대상이 현재도 같은 파일 식별자이며, 외부 변경·충돌·권한 오류가 없는지 재확인한다. 확인과 실행 사이의 경합은 열린 파일 핸들 등 별도 원자적 보호가 필요하다. 미해결이면 **차단**, 임의 덮어쓰기나 원본 삭제 금지.
3. **정확한 소유권:** 창/패널/탭/route와 사용자 작업 ticket에 바인딩한다. 완료가 오래되었거나 작업 중 다른 앱이 내용을 바꾼 경우 거부한다. 세션 v4·기존 Windows/Explorer Undo 스택에 자동 기록하거나 다른 작업을 지우지 않는다.
4. **Redo 별도:** 안전하게 Undo된 개별 영수증에만 새로운 상태 신원을 검증하여 허용한다. 다중 항목·휴지통 복구·프로바이더·타 드라이브 이동·재시작 후 복구는 R07-1 범위 밖이다.

## 검증과 현재 상태

- R07-1 당시에는 **실제 실행 취소/다시 실행 명령·단축키·삭제/이동/복원 파일 I/O를 추가하지 않았다.** 이후 R07-8에는 위의 격리된 파일 이름 복원 원시 함수가 추가됐지만, 사용자 UI·작업 제어기에서 호출하는 경로는 아직 없다.
- 전용 `tests/winui/test_r07_rename_receipt_contract.py`는 성공 전용 원래 경로 전달, 기존 ticket/컨텍스트 보존 및 파일 쓰기 로직 불변을 검사한다.
- Windows Release, 실제 Ctrl+Z/파일 복원/충돌/픽셀: **NOT TESTED**. 이 단계는 **R07-1 영수증 기초 데이터 구현**, R07 전체 수용이 아니다.
