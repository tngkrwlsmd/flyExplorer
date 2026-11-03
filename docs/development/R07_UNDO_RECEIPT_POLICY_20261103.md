# R07 실행 취소·다시 실행: 안전한 작업 영수증 기준 (2026-11-03)

## 현행 사실과 위험

- 현재 flyExplorer의 파일 전송은 `IFileOperation`이며 여러 항목을 개별로 처리할 수 있다. 실패·취소 보고에도 앞 항목의 실제 변경이 남을 수 있다. `Report.queued`는 성공 개수나 각각의 결과가 아니다.
- `RenameSelected`는 `MoveFileW`가 기존 이름을 덮어쓰지 않는 방식으로 실행하고, 성공 시 결과에 실제 새 대상 경로(`Result.target`)가 남는다. 하지만 완료 구조체에는 원래 경로가 없어 성공 이후 별도 재구성해야 했다.
- Windows Shell의 `FOF_ALLOWUNDO`와 `FOFX_ADDUNDORECORD`는 Windows Explorer 세션의 Undo 기록과 관련되지만, 앱에서 특정 항목만 안전하게 되돌리는 자체 작업 영수증을 제공하는 API가 아니다. 현재 `shell_transfer_core.cpp`는 Recycle에만 `FOF_ALLOWUNDO|FOFX_RECYCLEONDELETE`를 사용한다. 다른 Windows 응용프로그램의 전역 실행 취소 기록을 Ctrl+Z로 임의 실행하지 않는다.
- Microsoft 공식 근거: https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-ifileoperation-setoperationflags

## R07-1 구현: 성공한 이름 변경의 원래 경로만 임시 전달

`FileOperationController::FileCommandCompletion.originalRenameSource`를 추가했다. 파일 명령 worker는 **RenameSelected 요청의 정확한 `request.source`를 실행 전에 값으로 보존**하고, **실제 `execute(request)`가 성공한 경우에만** 원본 경로를 완료 값으로 전달한다. 기존 완료의 `ticket`, `Context`, `result.target`, 상태 판정, UI·디스크 작업과 세션 저장 형식은 변경하지 않는다. 성공 영수증에 필요한 첫 데이터일 뿐, **실행 취소 가능 판정이나 파일 쓰기 허가가 아니다.** 다른 생성/바로 가기 작업이나 실패/취소 결과에는 원래 이름을 제공하지 않는다.

## 후속 필수 단계 (순서 변경 금지)

1. **개별 변경 증거:** 원본·결과의 정확한 단일 항목 식별자(볼륨 식별자와 파일 ID), 재분석 지점 제외, 최종 파일 상태, 실제 생성/이동/복구 성공 정보 등을 worker의 신뢰된 범위에서 수집한다. 이름이나 경로만으로 동일한 파일이라고 간주하지 않는다. 일괄 Copy/Move의 aggregate 완료 수치만으로는 영수증을 발행할 수 없다.
2. **복원 전 재검증:** 원본 경로가 비어 있고 되돌릴 대상이 현재도 같은 파일 식별자이며, 외부 변경·충돌·권한 오류가 없는지 재확인한다. 확인과 실행 사이의 경합은 열린 파일 핸들 등 별도 원자적 보호가 필요하다. 미해결이면 **차단**, 임의 덮어쓰기나 원본 삭제 금지.
3. **정확한 소유권:** 창/패널/탭/route와 사용자 작업 ticket에 바인딩한다. 완료가 오래되었거나 작업 중 다른 앱이 내용을 바꾼 경우 거부한다. 세션 v4·기존 Windows/Explorer Undo 스택에 자동 기록하거나 다른 작업을 지우지 않는다.
4. **Redo 별도:** 안전하게 Undo된 개별 영수증에만 새로운 상태 신원을 검증하여 허용한다. 다중 항목·휴지통 복구·프로바이더·타 드라이브 이동·재시작 후 복구는 R07-1 범위 밖이다.

## 검증과 현재 상태

- 이번 변경에는 **실제 실행 취소/다시 실행 명령·단축키·삭제/이동/복원 파일 I/O를 추가하지 않았다.**
- 전용 `tests/winui/test_r07_rename_receipt_contract.py`는 성공 전용 원래 경로 전달, 기존 ticket/컨텍스트 보존 및 파일 쓰기 로직 불변을 검사한다.
- Windows Release, 실제 Ctrl+Z/파일 복원/충돌/픽셀: **NOT TESTED**. 이 단계는 **R07-1 영수증 기초 데이터 구현**, R07 전체 수용이 아니다.
