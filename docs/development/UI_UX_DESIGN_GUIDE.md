# flyExplorer 필수 UI/UX 디자인·구현·검증 지침

> **적용:** flyExplorer의 화면 설계·실제 UI 구현·컨트롤/테마 수정·디자인 평가·WinUI 전환 검토 모두.
> **지침 소유:** root [AGENTS.md](../../AGENTS.md)의 필수 Windows 11 UI 원칙을 구체화한다. 실제 증상/검증 상태는 [UI 실행 감사](UI_UX_AUDIT_20260924.md)와 [현재 상태](CURRENT_STATUS.md)에 별도로 기록한다.
> **상태:** 향후 개발의 의도된 디자인 기준이다. 이 문서만 추가했다고 제품 UI가 수정되거나 Windows 실행 검증을 통과한 것은 아니다.

## 1. 최종 화면 기준과 공식 참고 자료

**설치되어 실행 중인 실제 Windows 11 파일 탐색기**가 최종 비교 화면이다. Fluent 자료는 스타일 규칙이고, Figma kit은 컴포넌트 설계 참고이며, WinUI 3 Gallery는 실제 컨트롤의 상태·작동 참고다. 이 자료 어느 것도 현재 OS의 파일 탐색기 전체 완성 도면이라고 가정하지 않는다.

| 참고 자료 | 필수 활용 범위 | 한계 |
| --- | --- | --- |
| [Microsoft Fluent Design / Windows 앱 디자인](https://learn.microsoft.com/en-us/windows/apps/design/) | 색상 토큰, 타이포그래피, 계층·여백, 아이콘, 대비, 터치 대상, motion, 상태 표현 및 접근성 | 실제 Explorer의 사유 구현이나 현재 OS 빌드의 정확한 픽셀 수치를 자동 제공하지 않는다. |
| [Windows UI Kit for Figma 등 Microsoft 디자인 리소스](https://learn.microsoft.com/en-us/windows/apps/design/downloads/) | 화면 배치·컨트롤 상태·간격·색상 등 디자인 시안과 측정의 출발점 | optional. 추가 유료 디자인 도구 구매를 필수 조건으로 만들지 않는다. |
| [Microsoft WinUI 3 Gallery](https://github.com/microsoft/WinUI-Gallery) | 실제 WinUI 3 컨트롤의 시각 상태·동작·예제 코드 확인 | Gallery의 컨트롤이 MFC 안에 곧바로 이식되거나 Explorer의 모든 셸 기능을 제공한다고 가정하지 않는다. |
| 같은 PC의 Windows 11 파일 탐색기 | 탭, 주소·탐색, 명령 모음, 목록/헤더, 트리, 상태·정보 영역, 팝업의 최종 시각 및 동작 비교 | OS 빌드·테마·배율·접근성 설정에 따라 달라진다. OS 자산과 비공개 구현을 복제하지 않는다. |

## 2. 제품 현대화의 경계

- **선택 원칙:** MFC는 필수 유지 대상이 아니며, WinUI 3도 필수 전환 대상이 아니다. 사용자 경험을 향상시키면서 총 개발·검증·운영·장기 유지보수 비용을 낮추는 쪽을 근거로 결정한다. 상세 의사결정 기준은 [UI 기술 선택 지침](UI_FRAMEWORK_DECISION_POLICY.md)을 따른다.
- **보존할 대상:** 검증된 C++ 파일 관리 엔진과 다중 창/패널/탭, Windows Shell 연동, 컨텍스트 메뉴, 드래그 앤 드롭, 북마크, 단축키 및 사용자 데이터·설정을 보존한다. 엔진과 교체 가능한 프레젠테이션 계층의 경계를 먼저 식별한다.
- **비교 가능한 대안:** 현행 MFC 개선, MFC/Win32와 WinUI의 점진적 혼합, WinUI 3 및 C++/WinRT 기반 UI 전환을 동등하게 검토한다. 다른 기술도 실증 가능한 비용·품질 이점이 있으면 비교할 수 있다.
- **작은 실험:** 결과를 예측만 하지 말고 동일한 주소/탐색/탭 흐름을 격리된 실험 브랜치에서 비교한다. 실제 개발 소요, native 기능 연결, 키보드·접근성, 테마/DPI, 성능, 설치 및 Windows 버전 호환성을 기록한다.
- **전환 판단:** 대표 시제품과 실기 회귀 검증에서 장기적으로 유리한 영역은 기존 MFC 화면이라도 교체할 수 있다. 근거 없는 전면 재작성은 금지하며, 단계별 롤백 및 사용자 설정 마이그레이션 계획을 확보한다. 자료가 부족하면 현재 동작하는 구현을 임시 유지하고 최소 후속 검증 과제를 남긴다.
- **기술 혼합:** XAML Islands 등은 가능성을 자동 호환성으로 간주하지 않는다. 메시지/스레드/COM/HWND/포커스/드래그·드롭/DPI/배포 의존성을 실제 환경에서 확인한다.

## 3. 화면 설계 우선순위

1. Main frame chrome과 command surface: 탭·제목줄 경계·명령 간격·아이콘·접근 가능한 hit target.
2. Navigation: 주소 breadcrumb, 뒤로·앞으로·상위 이동, 검색, 탐색 트리, popup/flyout.
3. Content: list/header, 다중 pane, 선택·hover·focus·sort 및 실제 native scrollbar 최종 픽셀.
4. 정보·상태·설정: 정보 패널, 상태 표시, 설정 dialog와 언어별 텍스트 잘림.

실제 Windows 11과 같은 어두운 단일 평면을 강제하지 않고 표면 계층(window/surface/separator)을 구분한다. Fluent 자료를 참고하되 flyExplorer의 고유 정보 밀도와 추가 기능을 보존한다. 사용자 저장 열 너비, 도구 모음 멀티라인·배치, 북마크를 디자인 기본값으로 강제로 덮지 않는다.

## 4. 직접 비교 및 인수 검사

UI 수정 또는 시제품 승인 전에 **단 하나의 정의된 acceptance case**부터 시작한다.

1. **비교 조건 고정:** Windows OS 빌드, 제품 git SHA와 bin/x64/build-revision.txt, 화면 해상도·DPI(우선 100%), 텍스트 배율, System/Light/Dark·High Contrast, 창 크기, 동일 합성 폴더·선택·pane/tab 상태를 기록한다. 실제 Explorer와 flyExplorer를 같은 조건으로 촬영한다.
2. **측정:** 탭·주소·명령 영역·navigation·list/header·정보 패널의 bounding box, 표면/선/텍스트 대비, 아이콘 크기와 간격, 글꼴과 말줄임, 스크롤 영역을 비교한다. 스크린샷을 단순 평균 픽셀 차이로만 채점하지 않는다.
3. **상호작용:** hover, pressed, selection, focus, 키보드·휠·마우스 드래그, 크기 변경을 상태 변화와 최종 화면으로 확인한다. UI-02처럼 OS native 마지막 그리기 주체가 문제라면 단순 정지 화면 또는 픽셀 0.0 휴리스틱만으로 PASS하지 않는다.
4. **접근성/회귀:** 키보드 이동, 충분한 상태 대비, 컨트롤 접근성 이름·포커스 표시, Light/System/Dark/High Contrast, 가능한 경우 125/150/200% DPI를 해당 변경과 연관된 범위에서 확인한다. UI-05 기본 프로필과 기존 저장 배치, UI-09 command damage, HANG-01 응답성을 관련 변경에서 회귀 확인한다.
5. **증거와 상태:** 동일 revision의 정적 검사, compile/link, native functional, 실제 runtime, visual PASS를 별도로 표시한다. 검증하지 못한 환경은 RETEST OPEN/NOT TESTED로 유지한다. 개인 파일명·사용자 설정·비공개 정보가 보이는 screenshot은 커밋하지 않는다.

[기존 시각 증거 수집기](UI_VISUAL_RETEST.md)와 [실행 기반 UI 감사](UI_UX_AUDIT_20260924.md)를 재사용한다. 새로운 진단 도구·반복 녹화는 기존 도구로 검증할 수 없는 단일한 질문이 있을 때만 만든다.

## 5. 작업 단위와 완료 판단

- 모든 UI 작업은 **현상/목표 → 기준 화면 → 가장 작은 구현 변경 → 해당 regression → 일치 revision 실기 화면** 순서로 수행한다. 문서 시안만 만든 뒤 제품 구현이 끝났다고 보고하지 않는다.
- WinUI 3 시제품이 Windows 11 Explorer를 닮았다는 사실만으로 기존 기능 호환, 제품 배포 준비 또는 전면 전환 승인을 뜻하지 않는다. 기존 MFC 제품/별도 시제품의 결과를 구분해 보고한다.
- 기존 [에이전트 개발 효율 규칙](AGENT_EFFICIENCY.md)의 도구 호출 예산, 기존 증거 재사용, 무의미한 로그/화면 반복 금지와 중단 기준을 그대로 적용한다.
- 코드/리소스/GYP를 변경한 실제 제품 UI 작업에만 해당 로컬 Windows 빌드와 범위에 맞춘 런타임 검증을 요구한다. 이 지침만 편집하는 문서 작업에는 불필요한 제품 재빌드를 하지 않는다.
- GitHub Actions는 해당 개별 실행에 대한 사용자 명시 지시 없이는 **수동·자동 모두 실행하지 않는다**. 이전 성공이나 main 반영 요청만으로 허용하지 않는다.

## 6. 제품 전체 직접 사용 감사 및 개발 후보 관리 (2026-09-28)

최신 실제 사용 관찰·기능 수정 후보·제안의 우선순위는 [2026-09-28 제품 직접 사용 백로그](UI_UX_HANDS_ON_BACKLOG_20260928.md)에서 관리한다. 과거 UI-01~UI-14 재현 기록은 [기존 UI 감사](UI_UX_AUDIT_20260924.md)에 보존하고, 동일 현상을 신규 결함처럼 다시 등록하지 않는다.

- **증거 분리:** 실제 조작으로 관찰된 버그, 화면 밀도·작업 흐름의 사용성 마찰, 새로운 기능 제안, 소스에서만 추정한 후보, 실행하지 않은 검사를 다른 상태로 기록한다. GUI 접근성을 UIA 하위 항목 미검출 하나만으로 확정하지 말고 MSAA·실제 키보드·보조기술을 확인한다.
- **사용 시나리오 우선:** 단일·분할 pane, 탭 추가와 닫기, 주소 탐색, 검색 완료·취소, 북마크/설정, 파일 생성, 선택/포커스와 실제 메뉴를 사용자 작업 순서로 묶어 확인한다. 성공 메시지의 추가 클릭이나 결과 중복 표시도 사용자 비용으로 평가한다.
- **컨트롤 소유권:** 다크 모드에서 한 대화상자의 배경색만 확인하지 말고 CHotKeyCtrl 등 네이티브 예외, Shell/MessageBox의 별도 테마, ComboBoxEx 팝업과 스크롤바, 실제 High Contrast 회귀를 구분한다. 코드의 클래스 공통성은 다른 화면에서 결함이 관찰됐다는 증거가 아니다.
- **좁은 화면과 분할 구성:** 도구 모음의 발견성, 정보 패널의 실제 점유 폭, 열 제목과 긴 파일명의 가용 폭을 함께 측정한다. 기존 저장된 사용자 열 폭·레이아웃·북마크·단축키를 무단 초기화하지 않는다. 기존 설정이 제공하는 기능을 조사한 다음 기능 추가를 결정한다.
- **파일 작업의 안전:** 소유한 합성 테스트 폴더와 격리 설정을 사용한다. 전역 클립보드·휴지통·사용자 Shell 설정과 충돌하는 실험은 안전한 스냅샷/복구 절차가 준비되지 않으면 NOT TESTED로 유지한다.
- **완료 규칙:** 해당 과제의 재현 조건, 예상 사용자 이익, 최소 수정 범위, 실제 조작 및 시각·접근성 인수 조건, Release 빌드/관련 네이티브 회귀와 설정 보존을 명시한다. 문서에 제안으로 등록했다는 이유만으로 제품 결함을 수정 완료로 처리하지 않는다.

AGENT_EFFICIENCY.md의 기존 호출 예산과 빌드 출력 제한을 유지한다. GitHub Actions는 개별 실행에 대한 명시적 승인 없이 실행하지 않는다.

## 7. Custom native StatusBar accessibility (2026-09-28)

Our gui/StatusBar intercepts WM_SETTEXT as a command to update
*visible pane 0*. For completion announcements, use
StatusBar::announceAccessibleStatus rather than ordinary
SetWindowText, to preserve the visual panes and publish a
separate readable native window name with an OS name-change
event. Test visible status text, real external WinEvent delivery,
UIA Name and keyboard/pointer flow as separate gates.
Do not claim live screen-reader listening without testing it.

## 8. Responsive native per-pane information (UXH-03, 2026-09-28)

Preserve a user's saved global Explorer info-bar style and
individual pane folder/bookmark data. Only while the available
**native file-list width** would fall under 280 DPI-scaled pixels,
draw the *same per-pane ContentsWnd* as the existing 36-DIP
Basic-like horizontal folder summary; hide off-screen bookmark
controls from keyboard focus instead of destroying them. Restore
the full Explorer vertical sidebar and bookmark controls
automatically on resize. Do not mutate global settings, forcibly
reset custom file-list columns, or share one pane's folder summary
with another pane. The 750-px 1x2 result is measured, not a
guarantee about real 120/144/192-DPI or High Contrast acceptance.
[Measured UXH-03 acceptance](UI_PHASE6_UXH03_RESPONSIVE_PANE_20260928.md).
At 750-px 2x2 the height of file-list rows remains constrained;
treat UXH-04 global toolbar density as an independent improvement.
