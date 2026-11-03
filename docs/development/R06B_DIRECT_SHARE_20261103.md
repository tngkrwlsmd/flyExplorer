# R06b Windows 공유 시트 직접 진입 (2026-11-03)

## 제한된 구현

Windows 11 파일 탐색기와 차이를 줄이기 위해 파일 한 개를 직접 선택한 뒤 메뉴의 `Windows 공유 창 열기 (파일 1개)`를 누르면 Windows 공유 UI 열기를 요청한다. 데스크톱 WinUI 3 앱에 맞는 공식 `IDataTransferManagerInterop.GetForWindow / ShowShareUIForWindow`를 사용한다. Microsoft 문서: https://learn.microsoft.com/en-us/windows/apps/develop/ui/display-ui-objects , https://learn.microsoft.com/en-us/windows/apps/develop/windows-integration/integrate-sharesheet-send

- **지원 후보:** 일반 파일시스템 파일 정확히 1개. 폴더·가상 Shell 항목·복수 선택은 기존 R06a `Windows 탐색기에서 선택`에 위임한다. 비패키지 환경에서 Windows 공유 시트 지원은 실제 실행으로 확인해야 한다.
- **데이터:** `StorageFile.GetFileFromPathAsync`로 사용자 선택한 한 파일만 준비한다. `DataRequested`에서 `DataPackage.SetStorageItems`에 파일 한 개를 담는다. 앱은 수신인·계정을 선택하지 않고 전송도 실행하지 않는다. 사용자가 공유 대상 앱을 선택해야만 그 앱이 공유 콘텐츠를 받는다.
- **소유권:** 전용 코루틴이 준비하기 전/후 WindowTab 식별자, PaneTab, route, 원본 폴더, 파일 논리 ID·실제 경로와 선택 1개를 확인한다. `DataRequested` 때 다시 확인하여 이동·선택 변경·닫기 이후에는 실패 안내로 종료한다. 새 공유를 시작하면 이전 비동기 작업의 revision을 무효화한다.
- **수명:** 이벤트는 창이 소유하며 `PrepareForClose`에서 해제한다. Windows 공유 시트와 시스템 사용자 데이터는 테스트 목적이라도 자동 조작·전송·취소하지 않는다.
- **안전한 대안:** Windows 공유 API를 사용할 수 없으면 R06a 탐색기 위임을 계속 제공한다. 자동 전송, 클립보드 변경, 파일 이동/삭제, 세션 v4 변경은 없다.

## 남은 검증

이번 단위는 **소스 구현 후보**이며 C++ Release 컴파일·실제 WinUI 메뉴·Windows 공유 시트 실행/취소·시각 QA는 **NOT TESTED**. 자동 전송은 이 제품의 요구사항이 아니다. Windows 공유 창 자체의 지원·OS 버전과 실제 수신 대상은 추가 확인이 필요하다.

## R07 경계

Undo/Redo는 별도의 데이터 복구 기능이다. 복사·이동·이름 변경·휴지통 처리의 작업 영수증, 대상 파일이 다른 프로그램에 의해 변경된 경우, 충돌, 취소 후 부분 작업, 재시작/만료 정책을 먼저 정의해야 한다. 현재 파일 작업에 파일 삭제 기반의 즉석 Undo를 붙이지 않는다.
