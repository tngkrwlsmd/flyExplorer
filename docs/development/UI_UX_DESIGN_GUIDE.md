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

- **기본 경로:** 현재 MFC 제품을 유지한 채 필요한 presentation/control 경계에서 단계적으로 고친다. UI 변경 중 기본 파일 작업, Shell context menu, 다중 창·pane·tab, 주소·검색, 북마크, 설정·단축키, 드래그 앤 드롭을 보존한다.
- **WinUI 3은 실험 후 결정:** 사용자가 전환을 별도로 지시하지 않는 한 기존 제품의 MFC root window를 WinUI 3으로 대체하지 않는다. 새로운 기능을 무조건 WinUI로 구현하도록 강제하지 않는다.
- **작은 C++/WinRT 독립 시제품:** 별도 실험 브랜치/프로젝트에서 **메인 화면의 탭·주소창·명령 모음·탐색 영역·파일 목록**을 먼저 구현하고, 기존 C++ 기능과 UI 이벤트를 연결할 수 있는 좁은 경계 하나를 검증한다. 영구 추가되는 build system/외부 의존성은 사전에 영향·배포 비용을 설명한다.
- **비교 후 도입 판단:** 동일 fixture와 UI acceptance case에서 외형, 반응성·대용량 목록, keyboard/accessibility, Shell context menu, drag/drop, 탭·다중 pane, 기존 설정 이전, DPI/High Contrast, 설치·배포 런타임의 동등성 또는 제한을 기록한다. 근거가 부족하면 MFC 개선을 계속한다.
- **부분 통합 대안:** 기존 Win32에 XAML/WinUI를 호스팅하는 방식(XAML Islands 등)은 Windows App SDK 버전별 실제 지원·스레드/메시지 루프·키보드 포커스·DPI·배포 제약을 먼저 확인하는 **선택적 feasibility 항목**이다. WinUI 3이 항상 기존 MFC에 그대로 임베드된다는 전제를 두지 않는다.

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
