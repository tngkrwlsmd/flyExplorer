# R06b Windows 공유 시트 직접 진입 (2026-11-03)

## 제한된 구현

Windows 11 파일 탐색기와 차이를 줄이기 위해 파일 한 개를 직접 선택한 뒤 메뉴의 `Windows 공유 창 열기 (파일 1개)`를 누르면 Windows 공유 UI 열기를 요청한다. 데스크톱 WinUI 3 앱에 맞는 공식 `IDataTransferManagerInterop.GetForWindow / ShowShareUIForWindow`를 사용한다. Microsoft 문서: https://learn.microsoft.com/en-us/windows/apps/develop/ui/display-ui-objects , https://learn.microsoft.com/en-us/windows/apps/develop/windows-integration/integrate-sharesheet-send

- **지원 후보:** 일반 파일시스템 파일 정확히 1개. 폴더·가상 Shell 항목·복수 선택은 기존 R06a `Windows 탐색기에서 선택`에 위임한다. 비패키지 환경에서 Windows 공유 시트 지원은 실제 실행으로 확인해야 한다.
- **데이터:** `StorageFile.GetFileFromPathAsync`로 사용자 선택한 한 파일만 준비한다. `DataRequested`에서 `DataPackage.SetStorageItems`에 파일 한 개를 담는다. 앱은 수신인·계정을 선택하지 않고 전송도 실행하지 않는다. 사용자가 공유 대상 앱을 선택해야만 그 앱이 공유 콘텐츠를 받는다.
- **소유권:** 전용 코루틴이 준비하기 전/후 WindowTab 식별자, PaneTab, route, 원본 폴더, 파일 논리 ID·실제 경로와 선택 1개를 확인한다. `DataRequested` 때 다시 확인하여 이동·선택 변경·닫기 이후에는 실패 안내로 종료한다. 새 공유를 시작하면 이전 비동기 작업의 revision을 무효화한다.
- **수명:** 이벤트는 창이 소유하며 `PrepareForClose`에서 해제한다. Windows 공유 시트와 시스템 사용자 데이터는 테스트 목적이라도 자동 조작·전송·취소하지 않는다.
- **안전한 대안:** Windows 공유 API를 사용할 수 없으면 R06a 탐색기 위임을 계속 제공한다. 자동 전송, 클립보드 변경, 파일 이동/삭제, 세션 v4 변경은 없다.

## 후속 검증 상태 (2026-11-03)

- 기존 소스 구현과 안전 경계는 유지했으며, 이번 후속 검증에서 제품 C++/XAML·전송 엔진은 변경하지 않았다. [Windows 신규 메뉴 계약 #41647512565](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41647512565) **3/3 PASS**와 [수정된 입력 경로 소스 계약 #41649149905](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41649149905) **3/3 PASS**를 기록했다.
- [중앙 x64 Release + 앱 소유 메뉴 #41649330703](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41649330703)은 정확한 소스 `dee652f1fe47d8bb6db05fee92ae83f704c89d74`에서 **SUCCESS**. 단일 파일 우클릭은 R06b 직접 공유·R06a 탐색기 대안 **둘 다 활성화**, 폴더와 복수 선택의 `Shift+F10`에서는 R06b 직접 공유 **비활성화**, R06a **활성화**, 원본 바이트·사용자 기존 설정 보존과 테스트 앱 정상 종료·소유 fixture 정리까지 한정 PASS했다. [앞선 물리 폴더 우클릭 중단 #41647705586](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41647705586)은 해당 입력 경로의 실패 이력으로 보존한다.
- **Windows 공유 시트 자체 실행/수동 취소·비패키지 OS 연동·수신 대상·외부 전송·화면 픽셀 검증은 여전히 NOT TESTED**. 자동 공유 시트 조작·자동 전송은 현재 검증에도 포함되지 않았다. 소스의 `ShowShareUIForWindow` 요청이 실제 Windows OS에서 시트를 표시하는지는 별도 사용자 주도 확인이 필요하다. R06a Explorer 위임 메뉴의 활성 여부는 검증했으나, 이번에는 해당 메뉴를 눌러 새로운 Explorer 창을 띄우지도 않았다.

## R07 경계

Undo/Redo는 별도의 데이터 복구 기능이다. 복사·이동·이름 변경·휴지통 처리의 작업 영수증, 대상 파일이 다른 프로그램에 의해 변경된 경우, 충돌, 취소 후 부분 작업, 재시작/만료 정책을 먼저 정의해야 한다. 현재 파일 작업에 파일 삭제 기반의 즉석 Undo를 붙이지 않는다.
