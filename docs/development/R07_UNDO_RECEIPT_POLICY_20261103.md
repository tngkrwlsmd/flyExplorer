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

## R07-23A: 창별 비동기 시작 소유권과 완료 콜백 단회 전달 (2026-11-06)

R07-20의 `startTakenRenameRestoreAsync`는 작업 시작 전 후보의 원래 `Context`와 호출자의 `liveContext`를 비교한다. WindowTab 식별자·패널·PaneTab·route·파일시스템 및 Shell 폴더 중 한 필드라도 다르면 `StaleConfirmation`을 반환하고 네이티브 파일 변경을 시작하지 않는다. 이 판단은 UI 전용 상태 표시를 허용하는 것과 구별된다. R07-23A에서는 잘못된 owner 여섯 종류와 서로 다른 두 창에서의 실제 복원 실행 및 대기열 분리를 **테스트 소유 파일**로 검증했다.

또한 완료 `UiTask`는 대기열을 제공하는 `Post`가 같은 작업을 복사해 다시 실행하는 경우에도 안전하도록 공유 `atomic_bool` 표식을 소비한다. 첫 실행만 기존 창 종료·ticket/epoch·탐색 세대 재확인을 진행하고 원래 결과 콜백을 전달할 수 있으며, 이후 호출은 즉시 폐기한다. 이는 네이티브 파일 변경의 재시도가 아니라 **완료 이벤트 중복 전달 방어**다. 오래된 창 소유권이 되살아나지 않으며, 실행 불명 결과를 확인된 성공 또는 무변경으로 바꾸지도 않는다.

정확한 코드·테스트 `457b9f11a803202528eb766524ed78d17261b3a1`, [Windows VM #42058086853](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42058086853): 관련 소스 계약 **14/14 PASS**, 제품 컨트롤러와 네이티브 파일 명령을 실제 컴파일한 테스트 **38/38 PASS**, WinUI x64 Release 빌드 **PASS**, 기존 프로필 불변·소유 작업공간 정리 PASS. **실제 WinUI `FileOperationRestoreCallback`과 비동기 시작 호출을 서로 연결한 것은 아니다.** 사용자용 Undo/Redo·Ctrl+Z, 실제 GUI 탭·창 이벤트, 개인 파일 복원 및 외부 파일 경합은 여전히 NOT CONNECTED / NOT TESTED다.

## R07-22: 복원 완료 알림의 원래 탭 귀속 경계 (2026-11-06)

`FileOperationRestoreCallback`은 창을 강하게 보유하지 않고 UI 대기열에서 약한 참조를 해석한다. `OnRenameRestoreCompleted`는 완료값의 WindowTab identity·패널·PaneTab·route·표시 파일시스템/셸 폴더와 로딩 상태를 다시 확인한 뒤에만 원래 작업공간 알림을 갱신한다. 성공·불확실·미실행 결과를 분리하며 다른 활성 탭의 상태줄을 바꾸지 않는다. 이 콜백은 아직 `startTakenRenameRestoreAsync` 또는 사용자 명령에 연결되지 않았다.

정확한 제품 `80309ab9ae2c7f92b2fd95c6a226e674a51b011a`, [Windows VM #42055501856](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42055501856): 관련 소스 10/10, WinUI x64 Release, 소유 작업공간 정리 PASS. EXE SHA-256 `a3c6aa40f42af4818caa732f706c818333ad15e9a34685aa91afe6c082da259e`. 선행 #42054946021의 반환형 범위 컴파일 실패는 보존한다. 실제 GUI/픽셀·사용자 파일·Ctrl+Z·Undo/Redo는 미검증·미연결이다.

## R07-21A: 실제 WinUI 작업 대기열에서 닫힌 창 콜백 폐기 (2026-11-05)

`MainWindow::FileOperationUiPost()`는 실제 WinUI `DispatcherQueue`를 통해 `FileOperationController::UiTask`를 등록하되, worker가 `MainWindow`의 COM 객체를 직접 해석하거나 강하게 붙잡지 않는다. 큐에 등록된 함수가 UI 스레드에서 실행될 때 `get_weak()`로 받은 창 참조를 해석하고 `mClosing`을 확인하여 유효할 때에만 UI 완료 콜백을 호출한다. `TryEnqueue` 실패는 false로 보고한다. 이 안전 전달은 기존 M21 파일 작업에 실제 적용됐으며, 복원 API에는 **향후 안전한 `Post` 인수로 사용 가능하도록 준비된 단계**일 뿐 실제 Undo 명령 연결은 아니다.

정확한 코드 `50d2e7f87fa8e27d949aae7440b78d30149be203`, [Windows VM #42052008690](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42052008690): 관련 소스 **7/7 PASS**, WinUI x64 Release 컴파일·실행 파일 생성 **PASS**. 선행 [#42051238274](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42051238274)는 반환형 네임스페이스 표기 오류(C2143/C4430)로 Release FAIL이었고, 수정 후 재검증했다. 실제 GUI에서 창을 닫아보는 동작, 화면 갱신·프레임, `RestoreCompletion`의 개별 창/탭 귀속, 사용자용 Ctrl+Z·Undo/Redo는 **NOT TESTED / NOT CONNECTED**다. R07-20의 컨트롤러 작업 번호·탐색 세대 2단계 검사는 그대로 유지하며, 이 UI 약한 참조 검사만으로 복원 소유권을 승인하지 않는다.

## R07-20: 비동기 복원 완료 알림의 창 수명 보호 (2026-11-05)

`startTakenRenameRestoreAsync`는 기존 단회 복원 실행을 **공유 내부 상태만 포획한 별도 스레드**에서 수행한다. 컨트롤러 객체가 파괴돼도 이미 시작된 네이티브 복원을 취소하거나 재시도하지 않는다. 완료 결과는 원래 `status`·`nativeCallAttempted`와 보수적 결과 분류를 그대로 보존한다.

알림은 **UI 대기열 등록 직전과 실제 실행 직전** 두 차례 창 종료 여부·작업 번호·탐색 변경 세대를 확인한다. 소유권을 잃었다면 파일 변경 사실을 바꾸지 않고 사용자에게 보낼 알림만 폐기한다. 호출자가 제공하는 `Post`는 종료된 UI 객체를 안전하게 다뤄야 한다. 이 함수는 아직 실제 WinUI/Undo에 연결되지 않았다.

정확한 소스 `26b8aaad1922dfde044fc64ea2d68859a9c7c23a`의 [Windows VM #42044879231](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42044879231)에서 소스 **24/24**, 실제 네이티브 파일 복원과 완료 전달 **30/30**, WinUI x64 Release 빌드 모두 PASS. 사용자 설정 보존·작업공간 정리 PASS. **실제 DispatcherQueue/GUI 응답성·사용자 파일 Undo·외부 프로세스 파일 경합은 NOT TESTED**다.

## R07-19: 복원 중 UI 소유권 알림 비차단·완료 통지 재수용 차단 (2026-11-05)

기존 R07-18은 컨트롤러의 동일 잠금을 네이티브 파일 변경 전체에 걸쳐 보유했기 때문에 운영체제 I/O가 지연되면 **탭·폴더 탐색 무효화와 창 종료를 알리는 컨트롤러 메서드도 대기**할 수 있었다. R07-19의 현행 `executeTakenRenameRestore`는 원본의 ticket/epoch·창/패널/폴더 탭/route·원본/대상·파일 ID·수정 시각을 **잠금 안에서 대조하고 일회용 소유권을 영구 소비**, 호출용 경로·증거를 **자체 값으로 복사**한다. 그 자리에서 `busy=true`와 별도의 `restoreInFlight=true`를 설정하고 잠금을 해제한 **후** 안전한 `restoreRenameNoReplace`를 실행한다. 실제 네이티브 작업이 끝난 뒤에는 잠금 안에서 현재 epoch·닫기 상태를 확인하고 실행 중 표시를 정리한다.

이 계약에서 **복원이 시작되기 전**의 탐색·닫기 알림은 후보를 거부한다. 반면 **복원 소유권을 이미 소비하여 네이티브 호출이 시작된 뒤**의 탐색 변경이나 닫기는 더 이상 컨트롤러 잠금에 막히지 않지만, 시작된 운영체제의 복원은 취소하거나 롤백하지 않는다. 새 파일/전송 작업은 진행 중 `Busy`를 반환하고, 동일 epoch의 과거 파일/전송 완료 통지를 다시 수용하지 않도록 `restoreInFlight`를 확인한다. 결과적으로 “화면에서 떠났으므로 파일 변경이 없었다”는 판단은 허용되지 않는다.

미래 UI 표시를 위한 순수 분류 `classifyRestoreOutcome`는 `status`와 `nativeCallAttempted`를 함께 확인하여 **`NotAttempted`(네이티브 호출 전에 거부)**, **`VerifiedCommitted`(네이티브 호출 및 사후 복원 검증 확인)**, **`UncertainAfterAttempt`(네이티브 시도 뒤 실패·사후 미검증·모순된 상태)**로 구분한다. 네이티브 호출이 있었거나 상태가 모순되는 경우를 무변경/실패로 확정하지 않고, 무조건 재시도하지 않는다. 이 분류는 아직 사용자용 메시지나 Undo/Redo·Ctrl+Z로 연결되지 않았다.

**검증:** 정확한 소스 `3a2f99674e2c7747d22014e84f19259a636e319d`의 [Windows VM #42040643673](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42040643673)에서 관련 소스 계약 **21/21 PASS**, 실제 제품 컨트롤러·네이티브 파일 변경 코드의 테스트 소유 파일 **22/22 PASS**, WinUI **x64 Release 빌드 PASS**, 사용자 설정 불변·작업공간 정리 PASS를 확인했다. 테스트 전용 지연점은 실제 NT 이름 변경 직전에만 설치됐고, 호출을 중단한 동안 탐색 변경·닫기·busy 조회·중복 완료 통지 거부와 복원 결과를 확인했다. 앞선 [#42039485831](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42039485831)은 20/20 동작·제품 Release PASS였지만 완료 통지 중복 방어 이전 소스이므로 최종 수용 근거는 후속 실행이다.

**남은 검증 경계:** 테스트는 GUI의 실제 입력·렌더링·프레임 속도를 측정하지 않았으며, 창/작업 스레드 수명과 결과 디스패치가 사용자 인터페이스에 연결된 것도 아니다. 컨트롤러 잠금 해제는 OS 파일 경합 전체를 제거하지 않는다. 부모 폴더 이동/삭제, 외부 프로세스에 의한 이름 재점유, 장기 장애·전원 중단, 사용자 파일 Undo 및 반환 상태 메시지는 여전히 **NOT TESTED**이다.

## R07-18: 단회 소유권을 네이티브 복원에 연결한 격리 실행 경계 (2026-11-05)

`FileOperationController::executeTakenRenameRestore(candidate,liveContext)`는 **새로운 worker 전용 API**다. 인출한 Rename 후보를 원본 작업의 ticket/epoch, 창·패널·폴더 탭·route·가시 폴더, 대상 파일 ID·볼륨·크기·수정 시각과 비교한 뒤 **컨트롤러 잠금 아래에서 영구 소비**한다. 일치한 경우에만 `filecommand::restoreRenameNoReplace`를 호출하고, 잠금은 반환 때까지 유지한다. 같은 컨트롤러에 대한 새 작업·탭 탐색 무효화·창 닫기는 이 호출과 직렬화되며, 한 후보의 중복 네이티브 호출은 허용되지 않는다. 읽기 전용 재확인 `recheckAndRetireRenameRestoreCandidate`와 해당 실행 API는 같은 후보를 중복 사용할 수 없다. **OS 파일 I/O 동안 컨트롤러 잠금을 보유하므로 반드시 UI 스레드 밖에서만 호출**해야 하며, GUI Undo/Redo·Ctrl+Z·세션 v4·사용자 작업에 아직 연결하지 않았다.

정확한 소스 `37f566dca823dae13f9cb54ea48f289433d4761c`, [Windows VM #42036519845](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42036519845): 관련 소스/안전 계약 **24/24 PASS**, 실제 테스트 소유 파일에서 수행된 컨트롤러+네이티브 **13/13 PASS**, WinUI x64 Release 제품 빌드 **PASS**. 실제 RenameSelected 성공 작업에서 영수증을 받고 이를 복원까지 전달한 뒤 바이트와 128비트 파일 ID를 확인했다. 재사용, 읽기 전용 소비 뒤 실행, ticket/원본/대상/파일 ID 위조, 다른 route, 탐색 왕복, 창 종료, 원래 경로 충돌, 두 실행자의 동시 요청을 거부했다. 사용자 설정 불변과 자체 테스트 공간 정리 PASS. 처음 [#42036224625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42036224625)은 이전 계약에서 컨트롤러의 격리 호출까지 금지한 탓에 23/24로 중단됐으며 테스트 계약을 수정한 후속 실행만 수용한다.

**안전 제한:** 이 잠금은 **프로세스 내부 컨트롤러 상태**만 보호한다. UI 모델의 변경과 그 알림 사이에는 간격이 있을 수 있고, 외부 프로세스의 파일·부모 경로 변경은 여전히 운영체제 파일 공유·무덮어쓰기 호출·재검증에 의존한다. 특히 네이티브 호출 **진행 중** UI 탐색/종료 알림이 지연되는 실사용 경합 및 UI가 올바르게 반응하는지는 테스트하지 않았다. native-call 실패의 상태 불확실성을 임의로 성공/무변경으로 축소하거나, 반환이 확인되지 않은 호출을 무조건 재시도하지 않는다. 사용자에게 실행 취소를 표시하는 별도의 승인으로 해석하지 않는다.

## R07-17: 복원 네이티브 호출 직전의 결정적 경합 주입 (2026-11-05)

`restoreRenameNoReplace`는 열린 부모 및 대상 파일 핸들을 유지하면서 네이티브 단일 무덮어쓰기 호출 직전에 부모 디렉터리의 **현재 경로 동일성·안전 경로·원본 이름의 부재를 추가 재확인**한다. `FLY_R07_RESTORE_RACE_NATIVE_TEST`를 정의한 **격리 네이티브 테스트 빌드**에서만 최종 검증 전과 직후에 파일 시스템 개입을 주입하고, 실제 WinUI 제품에서는 해당 개입 경로가 컴파일되지 않는다.

정확한 제품·테스트 소스 `06d6c6097c97278b672695ab40c67f3dec3db832`의 [Windows VM #42032411343](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42032411343)에서 관련 소스 계약 **13/13**, 테스트 전용 C++ 경합 **8/8**, WinUI x64 Release 빌드, 사용자 프로필 보존·소유 임시 작업공간 정리가 모두 **PASS**였다. 원래 이름을 마지막 검사 전에 선점한 경우 호출 전에 거부했고, 검사 직후 선점한 경우 Windows의 무덮어쓰기 네이티브 호출이 실패하며 선점 파일 및 원래 대상의 ID·바이트를 보존했다. 네이티브 실패는 여전히 `NativeCallFailedUnknownState`이며, 한 테스트의 파일 보존 확인을 모든 호출 실패의 무변경 보장으로 확대하지 않는다.

**명시적 한계:** 부모 이동 시도는 실제로 `moved=0, rebound=0, error=32`(공유 위반)로 **차단됐다**. 따라서 부모 디렉터리가 보유 중인 핸들 아래에서 실제로 이동하거나 경로가 재점유되는 경합은 검증되지 않았다. 동기식 테스트 주입은 독립 외부 프로세스의 모든 경쟁 시점을 대표하지 않으며, 최종 검사와 NT 호출 사이의 간극도 완전히 제거하지 못한다. UI Ctrl+Z·Undo/Redo, 실제 사용자 파일 복원 및 GUI/픽셀 검증은 미연결·미실행 상태를 유지한다.

## R07-15: 실제 컨트롤러 네이티브 단위 실행 검증 (2026-11-05)

전용 `tests/winui/r07_owner_native/` 테스트 실행 파일은 제품 `app/winui/file_operation_controller.cpp`의 **실제 구현**과 `src/base/file_command_core.cpp`를 직접 컴파일한다. 사용자 파일이나 기존 GUI는 열지 않는다. 작업 번호를 만드는 사전 파일 요청은 유효하지 않은 파일명으로 즉시 거부되며, 비동기 결과는 폐기한다. 이후 **합성된 검증 성공 영수증**을 컨트롤러에 제공하여 일반적인 후보 인출·실행 직전 재확인·무효화를 실제 C++ 메서드로 검증한다. Shell 전송 함수는 실수로 실행되면 중단하도록 대체했다. 프로덕션 코드에서는 WinUI 사전 컴파일 헤더 포함만 테스트 매크로로 분기했고 실제 컨트롤러 로직은 그대로다.

[중앙 Windows VM #42017316589](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42017316589), 정확한 소스 `ee39c31ea928b31bccabbae6425ac75de583bdd9`: 소스/보호 계약 **3/3 PASS**, C++ 네이티브 x64 Release 컴파일 PASS, 소유권 상태 검사 **23/23 PASS**, 사용자 프로필 불변·임시 작업공간 정리 PASS. WinUI 애플리케이션 전체 빌드·GUI·파일 변경은 이 소스에서 **NOT TESTED**다. 이 결과는 실제 파일을 복원할 수 있다는 승인이 아니다.

**남은 위험:** 컨트롤러로 탐색 변경 이벤트가 연결되지 않아 이탈했다가 동일 컨텍스트로 돌아올 때 `sameContext`의 단순 값 비교를 통과할 수 있다. 완료 직전의 소유권 검사와 네이티브 파일 이름 변경 사이의 동시 경합도 아직 닫히지 않았다. 사용자용 Undo/Redo·Ctrl+Z는 계속 활성화하지 않는다.

## R07-14: 인출 후 일회성 소유권 재확인 (2026-11-05)

R07-7의 `takeRenameRestoreCandidate`는 기존 후보를 원본 저장소에서 제거하며, 인출한 복사본은 이후 자동으로 유효해지지 않는다. 새 `recheckAndRetireRenameRestoreCandidate(taken,liveContext)`는 별도로 보관한 기대 영수증과 파일 ID·볼륨·크기·시간, 정확한 경로, 창·패널·탭·route·ticket를 다시 대조한다. **일치 여부와 관계없이 잠금 안에서 기대값을 폐기**하므로 동일 후보의 후속 재검사는 실패한다. 새 파일 작업과 전송, 창 종료도 인출된 대기 후보를 폐기한다. 파일 I/O나 실제 이름 복원은 이 단계에 없다.

정확한 소스 `3b055ce1a76924c399e91c6ae266caf823c81717`에서 [소유권 소스 계약 #42003245497](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42003245497) **7/7 PASS**, [x64 Release 빌드 #42004028953](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42004028953) **PASS**. 첫 시도 [#42003728525](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/42003728525)의 긴 작업 경로 NuGet 복원 FAIL은 소스 C++ 미컴파일로 분류했고 짧은 소유 경로에서 재검증했다. 독립 컨트롤러 런타임/GUI/픽셀 및 복원 실행은 **NOT TESTED**.

이 검사는 파일 복원 권한이 아니다. 실제 UI에서 사용하려면 탭/route 변경의 전달, 재확인에서 실제 네이티브 호출까지의 원자성·동시 경합, 한 번만 실행되는 작업 수명 계약이 추가로 필요하다. 사용자용 Undo/Redo·Ctrl+Z/세션 영속화를 아직 활성화하지 않는다.

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

### R07-12 네이티브 클래스 10의 부모 핸들 기준 복원 경계 (2026-11-05)

이전 `SetFileInformationByHandle(FileRenameInfo/Ex)`의 동일 부모 핸들 입력은 오류 87을 반환했고 `RootDirectory=NULL`은 임시 파일을 프로세스 실행 폴더로 이동시켰다. 별도 테스트 소유 경로에서 실제 `NtSetInformationFile`의 정보 클래스 **10(FileRenameInformation)**을 동적 로딩한 [Windows VM #41992215529](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41992215529)은 **status=0, same_parent=1**, 원본 이름 점유시 **0xC0000035** 거부 및 **collision_preserved=1**을 기록했다. 별도 fixture의 결과로서 **제품 복원 함수가 통과했다는 뜻은 아니다**. 기존 M21 전체 검사에는 여전히 이전 실패 2건이 있었다.

`restoreRenameNoReplace`는 기존 보호 조건과 부모 디렉터리/대상 파일의 유지 핸들을 그대로 사용하며, 오직 이름변경 실행 부분만 같은 네이티브 ABI로 교체했다. `FILE_RENAME_INFO` 버퍼를 정렬하고 레이아웃을 컴파일 시 검사한다. `ReplaceIfExists=FALSE` 및 flags=0만 지정하며, 유지된 디렉터리 핸들을 `RootDirectory`에 넣고 상대 **단일 파일명**만 전달한다. 이 함수가 리턴한 NT 상태가 성공이 아니거나 완료 확인이 실패하면 네이티브 호출 시도와 실패를 구분해서 보고하고, 절대 경로 fallback/무조건 재시도/덮어쓰기/롤백은 수행하지 않는다. 성공한 호출에도 실제 부모 동일성·파일 ID·원본 이름과 대상 이름의 사후 증거를 따로 확인해야 한다. 네이티브 ABI 또는 OS 버전별 지원 차이는 아직 제품 수용 근거가 없다.

변경된 제품 소스 `ff3ef1b4d3584744b1b6096f10b7e459c3d09cc1`의 [Windows VM #41992876059](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41992876059)에서 **R07-8 소스 계약 9/9 PASS**만 확인했으며, **제품 C++ 컴파일/77건 실제 파일 복원 검사·GUI는 NOT TESTED**다. 이번 네이티브 함수는 **독립적이고 UI 미연결**이므로, 일회성 ticket·창/패널/탭/route가 실제 쓰기 시점에 유효함을 별도 증명하기 전까지 사용자용 Undo/Redo를 노출하지 않는다.

### R07-12 정확한 소스 Windows 네이티브 수용 (2026-11-05 추가)

이전의 부모 핸들 Win32 오류 87과 NULL 루트 파일 오이동은 이력으로 보존한다. 네이티브 클래스 10을 사용하는 **실제 독립 제품 함수**가 포함된 정확한 소스 `fa1771934c744e60eec9e53c950f40dc0909477f`의 [Windows VM #41995665162](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41995665162)에서 **M21 x64 Release 컴파일 PASS, 전용 파일 네이티브 77/77 PASS**, 기존 사용자 프로필 센티넬 불변·전용 체크아웃 정리 PASS를 확인했다. R07-8 테스트의 정상 복원, 원래 이름 충돌 거부와 바이트 보존, 파일 ID/내용 일치, 사전 열린 쓰기 핸들 거부, 위조/누락된 영수증 및 중복 복원 거부 조건이 포함된다.

**수용은 테스트 전용 단일 로컬 파일과 해당 Windows VM/정확한 소스 SHA에 한정**한다. 부모 폴더 외부 이동·삭제 타이밍, 원본명 경합의 모든 경우, 다른 Windows 버전, 복원 실행 시점의 창/패널/탭/route/ticket 재확인, WinUI 앱 전체 빌드·GUI는 검증하지 않았다. 따라서 사용자용 Undo/Redo·Ctrl+Z 연결은 계속 금지하고, 기존 R07-7 인출 영수증을 실제 실행 권한으로 간주하지 않는다. 이전 시점에 작성된 아래/위의 NOT TESTED 기록은 해당 시점의 이력이고, 이 후속 증거가 이번 테스트 범위의 상태를 갱신한다.

## 후속 필수 단계 (순서 변경 금지)

1. **개별 변경 증거 (R07-2 일부 구현):** 원본·결과의 정확한 단일 항목 식별자(볼륨 식별자와 파일 ID), 재분석 지점 제외, 최종 파일 상태, 실제 생성/이동/복구 성공 정보 등을 worker의 신뢰된 범위에서 수집한다. 이름이나 경로만으로 동일한 파일이라고 간주하지 않는다. 일괄 Copy/Move의 aggregate 완료 수치만으로는 영수증을 발행할 수 없다.
2. **복원 전 재검증 (R07-3 현재 시점 관측만 구현):** 원본 경로가 비어 있고 되돌릴 대상이 현재도 같은 파일 식별자이며, 외부 변경·충돌·권한 오류가 없는지 재확인한다. 확인과 실행 사이의 경합은 열린 파일 핸들 등 별도 원자적 보호가 필요하다. 미해결이면 **차단**, 임의 덮어쓰기나 원본 삭제 금지.
3. **정확한 소유권:** 창/패널/탭/route와 사용자 작업 ticket에 바인딩한다. 완료가 오래되었거나 작업 중 다른 앱이 내용을 바꾼 경우 거부한다. 세션 v4·기존 Windows/Explorer Undo 스택에 자동 기록하거나 다른 작업을 지우지 않는다.
4. **Redo 별도:** 안전하게 Undo된 개별 영수증에만 새로운 상태 신원을 검증하여 허용한다. 다중 항목·휴지통 복구·프로바이더·타 드라이브 이동·재시작 후 복구는 R07-1 범위 밖이다.

## 검증과 현재 상태

- R07-1 당시에는 **실제 실행 취소/다시 실행 명령·단축키·삭제/이동/복원 파일 I/O를 추가하지 않았다.** 이후 R07-8에는 위의 격리된 파일 이름 복원 원시 함수가 추가됐지만, 사용자 UI·작업 제어기에서 호출하는 경로는 아직 없다.
- 전용 `tests/winui/test_r07_rename_receipt_contract.py`는 성공 전용 원래 경로 전달, 기존 ticket/컨텍스트 보존 및 파일 쓰기 로직 불변을 검사한다.
- Windows Release, 실제 Ctrl+Z/파일 복원/충돌/픽셀: **NOT TESTED**. 이 단계는 **R07-1 영수증 기초 데이터 구현**, R07 전체 수용이 아니다.
