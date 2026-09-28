# flyExplorer 전체 제품 직접 사용 UX 감사와 개발 백로그 — 2026-09-28

이 문서는 실제 MFC 제품을 조작하여 기능 수정, UI/UX 개선, 새 기능의 **후보**를 수집한 후속 개발 지침이다. 구현 완료·버그 확정 보고서가 아니다. 기존 이력은 [2026-09-24 UI 감사](UI_UX_AUDIT_20260924.md), 최신 DPI·테마 근거는 [2026-09-28 환경 검증](UI_WINDOWS11_DPI_CONTRAST_20260928_EVIDENCE.md)을 따른다.

**검증 환경:** 연결된 Windows 11 빌드 26200, 1280×1024 단일 모니터, 실제 96 DPI, High Contrast OFF. main 4f1a407cca0162080a5449f2d7772b69b3ca32c5의 Release-x64-Unicode 실행 파일 SHA256: 137DDA525F0D1FDAE62475DE4FA2A5C1E38A916FAA76C63479BB6B3235AC828C.

**증거 위치:** 개발 컴퓨터의 무시되는 logs/ui-ux-* 실행 로그와 logs/ui02-modal-owned-*/ux-* 화면 캡처. 일부 분할 pane에는 복사된 기존 프로필의 초기 폴더명이 표시될 수 있으므로 개인 정보 노출 가능성이 있는 원본 캡처는 공개 저장소에 넣지 않는다.

## 1. 상태 분류 및 실제로 조작한 범위

- **OBSERVED:** 별도 소유 테스트 프로세스의 실제 GUI·Windows HWND·파일 시스템 결과로 관찰.
- **SOURCE ONLY:** 소스에서 구조 또는 후보 원인만 확인. 실행·외관·접근성 성공을 의미하지 않는다.
- **PROPOSED:** 새 기능 또는 설계 아이디어. 기존 기능 여부와 사용자 필요부터 조사.
- **NOT TESTED:** 이번 실행으로 판단할 수 없으며, 과거 테스트 결과와도 명확히 분리.

| 직접 조작한 기능 | 실제 관찰 | 이번에 단정할 수 없는 부분 |
| --- | --- | --- |
| 메인 화면 | 메뉴, 네 줄 명령 도구 모음, 드라이브·북마크 바, 탭, 주소, 트리, 정보 패널, 목록, 상태줄 확인 | 모든 세부 메뉴와 설정의 기능 검증 |
| 탭과 탐색 | 새 탭 명령 후 탭 영역 시각 변화, 주소에 임시 절대 경로 입력 후 뒤로·앞으로·상위 이동 | 커스텀 탭의 화면낭독기 호환, 대규모 탭 복원 |
| 다중 pane | 실제 ExplorerPane HWND 수 1 → 2 → 1; 분할 화면 캡처 | 빠른 pane 전환, 저장된 전체 레이아웃 복원 |
| 설정·북마크·신규 폴더 | 실제 대화상자 개방과 취소, 별도 실행에서 임시 폴더 실제 생성 | 모든 설정 페이지와 중복 이름·권한 오류 |
| 파일 검색 | 테스트 소유 임시 폴더의 README sample.txt 검색 결과 **정확히 1개** 화면 확인 | 검색 결과에서 이동·대량 검색·취소·네트워크 검색 |
| 파일 목록 우클릭 | **빈 영역의** 실제 네이티브 팝업 확인 | 선택한 파일 전용 Shell 컨텍스트 메뉴 |
| 작은 창 | 실제 750×540 창, 도구 모음 4줄·48개 노출 버튼·더보기 영역 관찰 | 모든 아이콘의 사용성·단축키 발견성 정량 평가 |

테스트 시작 전에 원본 사용자 설정 6개의 SHA256을 기록했다. 수정된 최종 탐색 검사 및 독립 검색·새 폴더 실행에서 6개 모두 변경되지 않았고 테스트 소유 프로세스도 정상 종료했다. 전역 클립보드·휴지통·네트워크 환경·실행 중인 사용자 프로세스는 건드리지 않았다.

## 2. 재현된 시각·사용성 개선 항목

**2026-09-28 scoped implementation status:** UXH-01's originally
observed bookmark hotkey Dark field was fixed and accepted on
the actual owned 96-DPI Dark/Light GUI with native Ctrl+2;
Release build and 17/0 native regressions PASS.
[Dedicated evidence](UI_PHASE6_HOTKEY_THEME_EVIDENCE_20260928.md).
Other hotkey-setting screens, actual High Contrast and higher
real DPI were not individually exercised and remain OPEN.

### UXH-01 · P1 · 북마크 단축키 입력 컨트롤의 다크 모드 불일치

**OBSERVED:** 다크 모드 북마크 항목 편집 창에서 일반 입력란은 어둡지만 **단축키 입력 칸 하나가 흰색**으로 표시된다. 실제 캡처 ux-bookmark.png에서 확인했다. bookmark_item_edit_dlg.h는 CHotKeyCtrl을 사용하고, ModernUI의 공통 대화상자 테마 처리에는 해당 네이티브 클래스의 명시적 처리가 없다(**SOURCE ONLY** 후보 원인).

**개발 지시:** 먼저 북마크 창에서 정확한 컨트롤 HWND·클래스·테마 소유권을 확인한다. 같은 CHotKeyCtrl을 사용하는 전역 단축키 설정, 단축키 테이블, 바로가기 생성 창은 개별 실행해 재현 여부를 기록한다. 공통 처리를 검토하되 네이티브 조합키 수집·선택·포커스·사용자 지정 색·High Contrast를 훼손하지 않는다. 다른 단축키 화면의 같은 오류는 아직 **미확인**이다.

**인수 조건:** 다크/라이트와 실제 High Contrast에서 배경·글자·포커스의 가독성 확보, 조합키 입력과 해제 및 기존 설정 보존. 실행하지 못한 테마는 NOT TESTED.

**2026-09-28 scoped UXH-02 accepted:** Actual owned 96-DPI
Dark/Light zero/one/three-result and invalid-location GUI passed,
along with real pointer Stop during active content search,
native Open parent folder for an owned result, readable UIA
completion status and an actual Windows name-change event.
Scoped Release, source and native 17/0 passed; all six original
user configuration hashes were preserved.
See [UXH-02 final evidence](UI_PHASE6_SEARCH_NONMODAL_EVIDENCE_20260928.md).
High Contrast, other real DPI and physical screen-reader listening
remain separately NOT TESTED.

### UXH-02 · P2 · 파일 검색 완료 알림의 불필요한 모달 및 테마 차이

**OBSERVED:** 임시 폴더에서 파일 한 개를 즉시 찾았고, 검색 창 하단에도 결과 건수와 시간이 나오지만, 위에 **밝은 Windows 정보 MessageBox**가 추가 표시돼 확인 클릭을 요구한다. 실제 캡처 ux-private-search-result.png와 search_dlg.cpp의 완료 메시지 호출을 각각 확인했다.

**개발 지시:** 정상 완료를 상태줄·검색 결과 화면의 접근 가능한 비모달 알림으로 표시할 수 있는지 검토한다. 취소·실패·중요한 확인은 별도로 설계한다. 즉시 성공한 작은 검색에 중복 확인 절차를 남기지 않는 것이 목표이며, 시스템 MessageBox를 유지한다면 다크 경계도 검토한다.

**인수 조건:** 0/1/다수 결과, 긴 검색·중단·오류를 구분하고 결과 접근성, 키보드 포커스 및 스크린리더 알림을 확인한다. 검색 엔진·검색 위치의 의미를 변경하지 않는다.

**2026-09-28 UXH-03 scoped ACCEPTED:** Actual owned 96-DPI
Dark/Light GUI measured 750-px 1x2 file-list width improving
from 178/176 to 266/264 px with automatic 36-DIP horizontal
folder summaries, wide-mode sidebar/bookmark restoration,
750-px 2x2, actual keyboard Win+Up/Down and pointer title-bar
double-click resizing. Original user settings and the saved
per-pane information choice stayed intact; x64 Release,
source and native 17/0 passed. See
[actual UXH-03 acceptance](UI_PHASE6_UXH03_RESPONSIVE_PANE_20260928.md).
Other real DPI/High Contrast remain separate NOT TESTED gates.
Next native implementation is UXH-04; UXH-05 is a
separate real-accessibility investigation.

### UXH-03 · P2 · 다중 탐색 영역의 중복 정보 패널과 가로 공간 부족

**OBSERVED:** 1×2 pane 분할에서 폴더 설명·북마크 정보 패널이 양쪽에 반복돼 실제 파일 목록 폭이 좁고 긴 파일명·설명 텍스트가 잘린다. 750px 창에서도 밀도가 높다. 기존 UI-08 및 UI-11과 연계하며 이미 해결된 다른 UI-02 항목으로 혼동하지 않는다.

**개발 지시:** 이미 제공되는 pane별 패널 표시·폭·저장 설정부터 확인한다. 없는 기능이 입증되면 pane별 빠른 접기, 최소 폭과 적응형 정보 배치 또는 명시적 공유 패널을 작은 시제품으로 비교한다. 기본 열 폭과 저장된 사용자 폭을 강제 초기화하지 않는다.

**인수 조건:** 1×2·2×2·750px·일반 창에서 실제 파일명 가용 폭 개선, 활성 pane에 대응하는 정보 표시, 레이아웃·탭·설정 보존, 키보드 및 마우스로 복원 가능.

### UXH-04 · P2 · 작은 창의 명령 도구 모음 발견성

**OBSERVED:** 750×540 실제 창에서 네 줄 명령/드라이브/북마크 영역과 많은 아이콘 명령, 오른쪽 더보기 표시가 존재한다. 조사 당시 UI 자동화에서 가시 버튼 48개를 찾았으며 실제 창 밖으로 벗어난 버튼은 관찰하지 못했다. 따라서 버튼 유실 결함으로 단정하지 않는다. 과거 UI-05의 사용성 후속 검토이다.

**개발 지시:** 명령 빈도와 도구 팁·레이블·접근 키를 직접 검사하고, 기본/고급 명령 그룹 또는 선택형 압축·명령 검색의 가치를 사용자 시나리오와 비교한다. 기존 사용자 지정 도구 모음·드라이브·북마크 배치의 저장값은 보존한다.

**인수 조건:** 작은 창에서도 자주 쓰는 명령을 찾고 더보기 메뉴의 전체 명령에 키보드/마우스로 도달할 수 있어야 한다. 단순히 기능을 숨기거나 삭제하지 않는다.

### UXH-05 · P2 조사 · 커스텀 탭 접근성 정보

**OBSERVED:** 새 탭 명령 이후 실제 탭 영역의 픽셀 변화가 있었지만, 이번 UIA 자동화 호출에서 커스텀 TabCtrl의 하위 TabItem 목록은 비어 있었다. 네이티브 TCM_GETITEMCOUNT도 이 커스텀 컨트롤의 항목 수를 알려주지 않았다. **화면낭독기가 실제로 사용 불가하다고 판단할 증거는 아니다.**

**개발 지시:** UI Automation 외에도 MSAA/IAccessible, 실제 키보드 Tab·Ctrl+Tab·F6, 선택·닫기·재정렬, 고대비 포커스를 확인한 뒤 결함 여부를 결정한다. 문제가 확인되면 현재 컨트롤의 접근성 어댑터를 우선 검토한다.

**인수 조건:** 각 탭의 이름·선택 상태·추가/닫기 의미가 접근 가능한 API를 통해 노출되고 키보드로 동일 업무를 수행할 수 있다. 접근성 검사 없이 소스만 고쳐 PASS 처리하지 않는다.

### UXH-06 · P3 제안 · 긴 검색 범위의 위치 확인 및 재사용

**OBSERVED:** 실제 파일 검색의 초기 검색 위치는 활성 테스트용 폴더와 일치했으며, 긴 절대 경로는 현재 콤보의 폭 때문에 일부만 표시됐다. 검색 위치가 잘못됐다는 증거는 없다.

**PROPOSED:** 경로 전체를 확인할 수 있는 툴팁/표시와 자주 쓰는 검색 범위의 빠른 재사용을 검토한다. 이미 존재하는 사용자 정의 검색 위치·최근 검색 기능부터 조사해 중복 구현하지 않는다.

### UXH-07 · P3 제안 · 다중 pane 작업 공간 프리셋

**OBSERVED:** pane 분할·복원은 정상 동작했고 새 pane이 별도 시작 위치를 보여줬다. 세션별 pane/탭/경로 복원 정책은 이번에 검증하지 않았다.

**PROPOSED:** 이미 제공되는 시작 폴더·레이아웃·북마크 및 작업 폴더 기능부터 조사한다. 사용자 수요가 확인되면 탭·pane 경로·분할 비율의 명시적 작업 공간 프리셋을 비교한다. 연결이 해제된 경로의 안전한 fallback과 원본 세션 유지가 필수다.

## 3. 별도 품질 게이트와 미검증 기능

| 항목 | 이번 상태 | 다음 안전한 검증 |
| --- | --- | --- |
| 복사·이동·이름 변경·삭제·충돌 확인·되돌리기 | **NOT TESTED**. GUI 새 폴더 생성만 실제 PASS. | 복사된 합성 파일에서 충돌·권한·취소를 별도 검증. 사용자 클립보드·휴지통을 훼손하는 실험 금지. 기존 네이티브 기능 회귀 결과와 GUI 증거는 구별. |
| 선택한 파일의 Shell 컨텍스트 메뉴·드래그 앤 드롭 | **NOT TESTED**. 실제 검사한 메뉴는 파일 목록 **빈 영역** 메뉴. | 격리된 테스트 확장/연결 프로그램과 파일 선택 상태를 준비해 검증. |
| 실제 오래 걸리는 탐색·Shell 확장·클라우드 지연 | **NOT TESTED**. 소규모 합성 폴더 실행에서 과거 HANG-01은 재현되지 않음. | 기존 HANG-01 독립 재현 시나리오대로 1분 이상 응답성 및 스레드 덤프 확보. 해결된 것으로 간주하지 않음. |
| UI-01 설정 페이지·UI-09 북마크 잔상 | 화면 접근은 확인했으나 **기존 재현 조건 전체는 NOT TESTED**. | 이전 사용자 화면과 같은 설정 프로필·전환 순서·비동기 redraw를 사용해 별도 검사. |
| 실제 DPI 120/144/192 및 High Contrast | 이번 점검에서는 **NOT TESTED**. | 격리된 Windows 환경에서 실제 HWND DPI와 High Contrast 플래그 검증. 96 DPI 이미지 확대나 소스 검사로 대체하지 않음. |
| 타 단축키 대화상자 | **SOURCE ONLY**, 공통 CHotKeyCtrl 사용처 확인. | 실제 각 대화상자에서 밝은 필드가 재현되는지 독립 확인. |

## 4. 구현 순서와 개발 팀 공통 수용 조건

1. UXH-01의 북마크 단축키 테마 문제부터 동일 계열 컨트롤의 재현 범위를 확인한다. 그 후 UXH-02의 완료 알림을 오류·취소의 의미와 분리해 개선한다.
2. UXH-03·UXH-04는 실제 정보 패널/명령 영역의 좌표와 파일 목록 가용 폭을 측정하고, 서로 다른 옵션을 작은 시제품으로 비교한다. 사용자 레이아웃 저장값은 그대로 보존한다.
3. UXH-05는 접근성 사실 확인 후에만 구현 과제로 전환한다. UXH-06·UXH-07은 기존 기능 중복 조사와 실제 사용자 시나리오 확보 이후 검토한다.
4. 기존 HANG-01, UI-01, UI-09, 격리된 파일 작업 회귀 및 다른 실제 DPI/High Contrast는 각각 독립 게이트다. 소규모 합성 폴더에서 정상 작동했다는 이유로 해결 처리하지 않는다.
5. 각 과제마다 **관찰 또는 재현 조건 → 예상 사용자 이익 → 기존 기능 중복 조사 → 최소 변경 → 실제 GUI 입력/키보드/화면 인수 기준 → 관련 네이티브 회귀 → 설정·시스템 상태 보호 → 문서화**를 기록한다. 소스·빌드·실행·화면·접근성의 PASS를 혼용하지 않는다.

**이번 요청의 작업 범위:** 개발 후보 문서화만 진행한다. 제품 실행 코드와 별도의 WinUI 3 실험 브랜치는 수정하지 않는다. 구현 단계에서 AGENT_EFFICIENCY.md의 호출 예산과 빌드 로그 제한을 적용하고, 개별 승인 없는 GitHub Actions 실행은 금지한다.
