# 실행 기반 UI/UX 점검 — 2026-09-24

## 2026-09-27 user screenshot follow-up: native list header and address chrome

- User-provided Dark and Light crops show a compressed-looking file-list header and an unnaturally contrasted full-width location box. These original screenshots have not been committed and the user's exact custom font/DPI/profile has not been reproduced.
- The clean baseline on the connected Windows 11 VM exposed a 24px native SysHeader32 and a 36px ComboBoxEx32. A manually resized header was not a sufficient long-term guarantee: native SysListView32 can renegotiate its header placement through HDM_LAYOUT.
- Scoped product source 03a68baff006f5d58cca304b7d0b36cc9ce28b49 adds a font/DPI-measured 28-DIP minimum through HDM_LAYOUT **and** adjusts the list content reservation by the exact increased header height. The existing header owner-draw, sort glyph bounds and High Contrast colors remain.
- The address field's outer ComboBoxEx32, nested ComboBox/edit brush, classic-edge cover and dark dropdown idle fill share the surrounding mChrome palette instead of drawing a full-width mElevated stripe. Native field input, autocomplete, dropdown, accessibility and High Contrast fallback stay owned by Windows.
- Native Windows Release-x64-Unicode compile/link passed and 17/0 functional tests passed; official HKCU-sensitive runtime smoke remained SKIPPED. New scoped invariant tests: 6 PASS; full preflight PASS.
- Isolated synthetic My Documents fixture, 1150px wide window, Dark and Light: actual header/window coordinates and mouse operations recorded by logs/header-address-retest/verify-gui.py; both after-theme screenshots and a narrow Dark capture are retained locally in ignored logs, not published. Original user custom settings, other DPI values and actual OS High Contrast remain NOT TESTED on this revision. Do not claim their exact screenshot is independently reproduced.
- Tested binary SHA: 03a68baff006f5d58cca304b7d0b36cc9ce28b49. Any following documentation-only commit does not require rebuilding the identical product C++ source but changes the overall git revision marker.


## 2026-09-27 UI-02 사용자 화면 재신고: native final pixel ownership 확인

- 사용자 화면: 앱 Dark임에도 파일 목록에 밝은 회색 native scrollbar 노출.
- 연결 VM: native OS Dark / 96 DPI. 원본 버전에서 사용자가 본
  OS-밝은 native track 현상은 해당 VM에서 직접 재현되지 않음.
- Win32 원인 검사: 기존 attached scrollbar의 GetWindowDC 지연 GDI
  덮어쓰기는 native scrollbar modal tracking의 최종 픽셀 소유권 없음.
  외부 Python의 child layered overlay는 drag 중 native NC paint에 가려짐.
- 동일 UI-thread owned transparent layered popup의 독립 diagnostic은
  8프레임 내내 track을 덮었으며 native thumb 이동이 유지됨.
- 중간 C++ test tint 빌드의 실제 native thumb 값과 overlay 위치가
  매 프레임 1px 차이로 추종했음(23→172). diagnostic tint는 release
  후보 source에서 완전히 제거. 최종 revision-specific binary retest는
  해당 git commit 후 별도 수행/로그 보관해야 함.
- UI-02 사용자의 원래 Windows/설정까지 COMPLETE로 간주하지 않음.
  High Contrast/DPI 차이 및 사용자 동일 화면 재검증 RETEST OPEN.
- 근거는 해당 Windows PC의 무추적 logs/ui02-*와 공식 local CI.
  제품 수정과 진단 이미지가 포함된 개인 자료는 저장소에 첨부하지 않음.

## 2026-09-27 실제 Windows UI-05 새 프로필 배치 검증 및 UI-02 부분 재현

- 장치: Win11 x64 VM, 96 DPI, Dark, 일치한 소스/바이너리 3aab666.
- fixture: 별도 --conf_dir와 합성 폴더 30개·파일 175개. 개인 폴더 검사 없음.
- 최초 e59aed97: 800×600 신규 창을 1920×1032로 키워도 드라이브와 북마크가 서로 다른 행에 남는 화면 확인.
- 중간 fe5e49d: 두 밴드는 합쳐지나 드라이브가 거의 전폭을 점유해 북마크가 오른쪽 넘침 메뉴 뒤로 숨는 화면 확인.
- 수정 3aab666: 다시 x64로 빌드한 뒤 좁은 창→1920×1032 최대화에서 둘째 행이 드라이브/북마크로 분할되고 북마크 단축 아이콘이 화면에 직접 표시됨. UIA에서 두 toolbar가 동일 y=84 행에 위치함을 재검증했고, 별도 테스트 프로세스 응답 정상.
- 사용자 저장 레이아웃 테스트: 합성 설정으로 닫은 뒤 rebar 저장 파일의 네 밴드와 BREAK 플래그를 확인하고 같은 설정을 재오픈했다. 1920×1032의 둘째 행 배치가 유지되고 앱이 정상 응답/종료함. 저장 설정이 최대화 창 크기를 복원하여 저장 상태의 800px 초기 배치 검사는 하지 못했음.
- UI-05 source invariant 전체 PASS, native x64 기능 테스트 17/0 PASS, 전용 mutation 회귀 11 PASS. 공식 runtime smoke는 기존 사용자 HKCU 데이터 보호로 SKIPPED이므로 PASS_WITH_SKIPS.
- 범위: UI-05의 이 특정 초기 창 크기 전환은 RUNTIME/VISUAL PASS. Light/High Contrast, 125/150/200% DPI, 사용자 수동 rebar 드래그, 다양한 기존 레이아웃은 RETEST OPEN.
- UI-02: 같은 후보 바이너리에서 실제 파일 목록 세로와 트리 가로의 native thumb를 각각 12프레임 드래그했고 좌표 이동 관측. 이 장치의 Dark 96 DPI에서 의심 밝기 0 프레임. 이전 다른 화면 실패를 반박하지 않으므로 UI-02 전역 OPEN.
- 근거 파일은 개인 정보가 없는 Windows 테스트 PC의 무추적 logs/visual-ui/ 및 logs/local-ci/ 아래 보관. GitHub Actions 미실행.
## 2026-09-27 추적: 실제 Windows UI 재검증 준비

[UI 시각적 재검증 절차](UI_VISUAL_RETEST.md)와 별도 로컬 수집기를
추가했다. UI-02는 네이티브 스크롤바 손잡이를 **누른 상태에서**
프레임·thumb 위치·영역별 밝은 픽셀 비율을 기록하도록 준비했지만,
현재 채팅에서 실제 Windows를 실행한 증거는 아직 없다.
제품 UI 소스를 변경하거나 원래 사용자 재현 실패를 종결하지 않았다.
기존 UI-01~14의 CODE UPDATED/OPEN 구분은 아래 실행 근거 그대로 유지한다.
검사 환경과 현재 실행 파일 리비전이 확인되기 전까지 모든 신규
시각적 결과는 **NOT TESTED**다. 밝기 탐지는 참고값일 뿐
사람/AI의 최종 화면 검토를 대신하지 않는다.

## 기준과 검증 범위

사용자 요청: 실제 프로그램을 조작하여 UI/UX 및 최신 Windows 호환성 개선 목록을 개발 지침에 남긴다. 최초 작성은 **조사·문서화**였으며, 이후 구현 시 각 항목에 CODE UPDATED / RETEST OPEN 같은 상태를 개별 기록한다.

- Source: 원격 `main`을 fast-forward한 `bee95d96a0150734ac247ed34e52ffe3bb1f4d92`.
- Binary: 해당 소스로 `local_ci.bat x64`를 실행한 `bin/x64/fxfile.exe`. `build-revision.txt` 일치 확인.
- SHA-256: `D716967A417EEFE3501BBAA8DFEBAA05805F9573FE0BDD8A7B70262064463FDC`.
- 환경: Windows 11, 보고된 OS version `10.0.26200.0`, 한국어 UI, 관찰된 main client 포함 창 약 1326×708. 정확한 모니터 DPI/텍스트 배율은 측정하지 않았다.
- 실행 도구: Computer Use로 실제 창을 관찰·조작. System(현재 OS에서는 Dark) → Light 적용 → System 복원. 마지막에는 단일 창으로 복원하고 추가한 탭을 닫았다.
- 비교: 같은 컴퓨터의 Windows 파일 탐색기 Dark 화면에서 탭/주소/명령 영역, 얇은 어두운 스크롤바와 여백을 관찰했다. OS Explorer의 구현 API를 추정하거나 복제하지 않는다.
- Evidence: 이번 세션의 창 캡처와 직접 입력 결과. 개인 파일명과 다른 앱이 포함된 원본 화면은 저장소에 첨부하지 않았다. 아래 재현 절차로 새 evidence를 남길 수 있다.
- 중단 전 구버전 실행의 관찰만으로 최신본 결함을 확정하지 않았다. 아래 UI-01~08의 화면 관찰은 위 binary로 재확인했다.

| 검증 종류 | 실제 결과와 한계 |
| --- | --- |
| Source preflight / x64 compile·link | PASS (`logs/local-ci/local-ci.log`) |
| Native functional regression | 16 passed / 0 failed; fixture cleanup PASS |
| 자동 runtime smoke | SKIPPED: 기존 HKCU profile/startup 값 보호. clean-profile startup는 NOT TESTED |
| 직접 실행 | main 창 표시, 주소로 프로젝트 폴더 이동, 설정 열기/재열기, 테마 적용, 설정 tree 스크롤, 검색 창 열기, 수직 듀얼/단일 창 전환, 새 탭/`Ctrl+F4` 닫기 확인 |
| 제한 | 검색 실행·결과/취소, 파일 복사·이동·삭제, shell context menu, drag/drop, installer/CHM, Windows 10, High Contrast, mixed-DPI, 화면 읽기 프로그램: NOT TESTED |
| GitHub Actions | NOT RUN; 실행별 사용자 명시적 지시 규칙 유지 |

## 사용자 제공 추가 화면 — UI-09 (북마크 도구 모음 잔상)

**2026-09-26 병합 시점 최신 확인:** 아래 과거 가설보다
실제 Windows에서 계측된 36px→22px 명령 UI 갱신
이전 영역 무효화 누락을 현재 원인 근거로 적용한다.
수정한 진단 빌드에서 동일 테마 전환 경로의 잔상이
사라졌으나 새 main과 UI-05 행 결합을 포함한
병합 바이너리는 아직 실행 검증되지 않았다.
임시 추적 코드도 최종 백업 소스에서 제거되었다.

**2026-09-26 후속 실행 진단:** 테마 적용 후 36px로 그린 버튼을 MFC command
update가 22px로 축소하면서 새 영역만 invalidate하는 경로가 확인됐다.
진단 빌드에서 이전/새 영역을 함께 무효화하자 동일 화면의 잔상이 사라졌다.
최종 빌드 검증 상태와 항목별 evidence는
[UI09_ROOT_CAUSE_20260926.md](UI09_ROOT_CAUSE_20260926.md)를 따른다.
아래 기록은 이전 시점의 가설/검증 한계를 보존한 역사이며 현재 결론을 대신하지 않는다.

- 2026-09-24 사용자 스크린샷에서 Light처럼 보이는
  바탕 화면·라이브러리·내 문서·음악·사진·동영상·네트워크
  바로가기 아이콘 아래에 짧은 색상 줄, 한국어 레이블
  아래에는 검은 잔상 조각이 각각 반복된다.
  이 화면은 이전 x64 PASS 기록의 이미지가 아니며,
  본문과 하단 잔상은 실제 사용자 화면 근거이다.
- 소스 진단 후보: ToolBarEx의 \`CDDS_ITEMPOSTPAINT\`는
  Dark에서만 버튼 전체를 지우고 다시 그렸고,
  Light에서는 \`DrawFinalDarkToolbarItem\`으로 text/dropdown
  사각형만 지워 그려 native 아이콘·글자 일부가 남을 수 있었다.
- 해당 비고대비 Light도 Dark와 동일한 버튼 전체
  최종 렌더러를 사용하도록 연결했다.
  앱 테마 팔레트로 배경·hover/pressed·아이콘·레이블·화살표를
  완전히 그리며 기능·이미지 목록·키보드·tooltip·고대비는
  유지한다. 정적 검사에서는 이전 Light 부분 오버레이로
  돌아가지 못하게 한다.
- 이는 일관된 소스 수정으로, 원인 확정이나 완료 판정은
  재빌드한 Windows 11의 정확히 같은 바로가기 밴드
  Light/Dark/고대비, 100/125/150/200%와 hover/pressed
  스크린샷 비교가 필요하다.
  **UI-09: SOURCE UPDATED / VISUAL RETEST OPEN.**

## UI-09 재신고 — 사후 그리기 변경 후에도 잔상 유지

사용자가 기존 \`541cd0f3\` 수정 후 동일한 잔상을 다시
보고했다. 따라서 이전 Light 후처리 변경은 문제 해결
증거가 아니며, 기존 가설만 반복하지 않는다.

추가 소스 진단에서 \`CToolBarEx\`는
\`NM_CUSTOMDRAW/CDDS_ITEMPOSTPAINT\`만 덮었으며
native \`WM_PAINT\`와 rebar 합성용 \`WM_PRINT*\`를
가로채지 않았다. 화면에는 전체 아이콘/글자 아래 같은
X 좌표로 추가 표시 흔적이 있으므로, 독립 그리기
경로를 제어해야 한다.

이번 후보 변경은 북마크 밴드에 한정하여 WM_PAINT,
WM_PRINT와 WM_PRINTCLIENT에서 공식 이미지 목록,
toolbar item rect, 실제 상태를 읽어 전체 클라이언트
영역을 직접 그린다. 아이콘 정보가 불완전하면 native
경로로 되돌아가며, High Contrast는 처음부터 시스템
그리기를 유지한다. 툴팁·버튼 명령·드래그 동작은
그리기 경로 밖에 그대로 둔다.

해당 재발 방지 검사는 사후 item paint뿐 아니라
독립적인 print 경로까지 확인한다. 이는 이전
재현 결과에 대응한 후속 소스 후보이며
정확한 Win11 현재 빌드에서 동일 캡처를
얻기 전까지 **UI-09 OPEN**이다.

## UI-09 추가 근본 원인 후보 — 버튼 자체의 중복 생성

재신고를 계기로 그리기 처리 외에 북마크 밴드의 버튼
생명주기를 확인했다. \`setBookmark\`는 기존 native
버튼을 비우지 않고 \`TB_INSERTBUTTON\`으로
\`BookmarkMgr\`의 전체 항목을 다시 삽입했다.
한 번 이상 초기화되는 경로에서는 같은 명령/아이콘
버튼들이 중복될 수 있고, 줄바꿈/좁은 rebar일 때
두 번째 줄 일부가 아래쪽 잘린 흔적으로 표시되는
양상과도 부합한다. 기존 \`updateBookmarkButton()\`은
\`setBookmark\` 직전에 이미지 목록까지 이중 생성했다.

\`setBookmark\` 시작 시 버튼을 비운 뒤 최신 목록
개수만큼 다시 넣는 단일 재생성 경로로 합쳤다.
완료 후 실제 버튼 수와 manager 항목 수를 debug
assert로 비교한다. 비동기 아이콘 observer도 이미
등록된 경우 이중 등록하지 않는다.
중복 버튼 여부가 이 사용자의 실행 과정에서
실제로 확인된 것은 아니므로 전체 그리기 경로
수정과 함께 source-level 복구 후보로 기록하며
Windows 실행/버튼 수/스크린샷 확인 전에는
UI-09를 완료 처리하지 않는다.

## 재신고 후속 소스 변경 — Light 필터 목록 / 북마크 두 번째 줄

사용자가 올린 Light/Dark 필터링 페이지를 비교하면
Light 상태에서 필터 이름·확장자 텍스트 대부분이
아주 옅은 색으로 표시되어 읽기 어렵다.
기존 custom draw는 Dark 화면의 완전 검정
\`RGB(0,0,0)\`만 예외 처리하고,
저장된 밝은 색의 필터 값은 Light 화면에 그대로
그렸다. 이번 수정에서는 저장된 RGB와 필터
의미를 바꾸지 않고 각 행의 실제 배경과
WCAG 상대휘도 대비 4.5:1 이상인지 판단한다.
대비가 부족한 경우 현재 팔레트 기본 글자색으로
화면에만 대체한다. 고대비에서는 사용자 시스템
문자색을 사용한다. 테마/설정/시스템색 이벤트에
ListView 기본색을 동기화하고 헤더를 다시 그린다.
Dark의 밝은 기본 스크롤바(UI-02)는 별도 미해결이다.

세 번째 북마크 화면은 이전 렌더러·중복 버튼
수정에도 반복 잔상이 남는다. 따라서 이전
"드라이브와 북마크 밴드를 한 행으로 합친"
UI-05 변경을 되돌려, 신규 기본 배치뿐 아니라
기존 저장된 같은 행 배치도 시작할 때 북마크
독립 행으로 교정한다. 단일행에서는 chevron,
사용자가 선택한 다중행에서는 native wrapping
기능을 그대로 유지한다. 기존에 북마크를
드라이브와 한 행으로 저장한 사용자의 배치는
이 문제 해결을 위해 재시작 시 독립 행으로
다시 놓인다.

두 소스 경로를 정적 검사로 보호하지만,
실제 Windows 11 최종 화면/명령 기능을 같은
리비전으로 다시 확인하지 못했으므로 UI-09와
UI-10을 완료 처리하지 않는다.

## 실제 관찰된 개선 목록

P1은 기능 오인 또는 읽기 어려움, P2는 사용성/시각 일관성 개선이다. 기대 결과는 Intended이며 관찰 결과와 구분한다. CODE UPDATED는 소스 수정만 뜻하며 matching runtime/visual evidence 전에는 CLOSED가 아니다.

| ID / 우선순위 | 사용자 행동 → 관찰된 결과 | 기대 결과 / 완료 기준 | 우선 조사할 owner |
| --- | --- | --- | --- |
| UI-01 / P1 — **CODE UPDATED / RETEST OPEN** | 설정에서 일반을 본 뒤 모양 및 테마 → Light → 적용. 제목/선택은 모양 및 테마지만 본문이 일반 페이지로 바뀐다. 필터링을 클릭해도 제목만 바뀌고 일반 본문이 남는다. 창을 닫았다 재열면 필터링 본문이 정상 표시된다. | 2026-09-24 source fix: theme transaction 시작 시 HWND의 visible 상태를 snapshot하고 당시 visible이었던 HWND만 `WM_SETREDRAW(FALSE/TRUE)`로 freeze/thaw한다. 재시작/재열기 없이 선택된 페이지 하나만 표시되는지 동일 경로 runtime/visual 재검증이 남아 있다. | `main_frame.cpp::RefreshThemeForCurrentThread`, `cfg/cfg_main_dlg.cpp::showCfg/OnApply` |
| UI-02 / P1 | System→Dark에서 긴 파일 목록, 폴더 tree, 설정 tree를 표시/스크롤하면 흰 바탕의 고전 스크롤바와 검은 화살표가 남는다. | thumb/track/화살표/교차 모서리까지 Dark와 조화. 휠·키보드·thumb drag·High Contrast 동작 보존. | `gui/ListCtrlEx.cpp::refreshModernAppearance`, folder tree 및 settings tree의 non-client rendering |
| UI-03 / P1 — **SOURCE PARTIAL / RETEST OPEN** | Dark에서 툴바 검색을 열면 찾는 위치 입력부는 흰 바탕/검은 글자이고 옆의 작은 `>>` 모양 버튼은 어두운 배경 위 검게 표시된다. 입력칸 앞쪽 아이콘도 경로와 매우 가깝다. | ComboBoxEx의 내부 edit/list, browse/current-location icon까지 읽을 수 있는 최종 색상과 여백. 정상·hover·focus·disabled 상태 각각 확인. | `search_dlg.cpp`의 `mLocComboBox`, `mCurLocButton` (`IDI_EXPAND`), 공통 dialog/combobox/button renderer |
| UI-04 / P2 — **CODE UPDATED / VISUAL RETEST OPEN** | Light 설정 → 필터링에서 목록 아래의 두 작은 버튼이 정상적인 위/아래 화살표로 읽히지 않는 문자열처럼 보인다. 동일한 mojibake literal이 프로그램 연동 순서 버튼에도 있었다. | 2026-09-24 source fix: 두 페이지의 resource fallback을 `Up`/`Down`으로 바꾸고 버튼 폭을 26 DLU로 확장, runtime Korean label은 `위로`/`아래로`로 명시한다. 실제 DPI별 clipping/focus/accessibility name과 최종 미감은 재검증이 남아 있다. | `fxfile.rc`, `cfg_appearance_filtering_dlg.cpp`, `cfg_func_program_ass_dlg.cpp` |
| UI-05 / P2 | main 상단은 좁은 명령 아이콘들이 밀집하고 드라이브/북마크 band에는 넓은 빈 공간이 남는다. 설정의 checkbox/radio/combobox 내부 간격은 다른 영역보다 좁다. | Windows 11 Explorer를 기준으로 font/행 높이/hit target/섹션 간격을 함께 조정. 기존 command, bitmap index, 정보 밀도 선택권 보존. | main toolbar/rebar, `ModernUI`, dialog resource/layout metrics |
| UI-06 / P2 | Dark의 창/탭 popup 메뉴에 밝고 두꺼운 외곽선이 보인다. 창 메뉴는 현재 main 창 높이보다 길다. | 중립색 경계와 일관된 hover/disabled 상태. 짧은 화면에서도 모든 명령을 키보드/스크롤로 접근 가능. 기능을 삭제해 메뉴를 줄이지 않음. | app-owned `BCMenu`, command grouping/placement |
| UI-07 / P2 — **SOURCE UPDATED / VISUAL RETEST OPEN** | 단일 창에는 탭 추가/닫기 affordance가 보이지 않는다. 창 → 탭 → 새 탭으로 열면 탭 strip이 나타나지만 상시 `+`/닫기 표시가 눈에 띄지 않는다. `Ctrl+F4`로 테스트 탭은 정상 닫힌다. | 새 사용자도 탭 기능을 발견 가능. 선택/hover/focus/닫기 target을 구분하며 기존 shortcut과 single-tab 숨김 설정 의미 보존. | `tab_pane.cpp`, tab control, 창/탭 command UI |
| UI-08 / P2 — **SOURCE PARTIAL / VISUAL RETEST OPEN** | 수직 듀얼 창에서 각 pane의 tree와 설명 영역이 반복되어 파일 목록 너비가 크게 줄고 열/수정 날짜가 잘린다. 주소는 현재 설정에서 마지막 폴더명 위주로 보인다. | 좁은 pane에서 정보 우선순위/최소 너비/설명 영역 크기 조절을 개선하고 활성 pane을 명확히 표시. 전체 경로 옵션과 고급 기능 보존; breadcrumb는 설계 후보. | `explorer_pane.cpp`, `explorer_view.cpp`, `splitter.cpp`, `address_bar.cpp` |

UI-04의 원래 `¡è`/`¡é` literal은 filtering과 sibling program-association resource에서 제거했다. 두 페이지 모두 runtime localization으로 의미 있는 이동 방향 text를 설정한다. CODE UPDATED는 visual/accessibility PASS가 아니므로 실제 DPI/keyboard/screen-reader 확인은 남아 있다.

필터 목록의 모든 채워진 행이 파랗게 보이는 현상도 관찰했다. 항목별 색상 표시인지 selection renderer 문제인지 확인하지 않았으므로 **추가 조사 후보**로만 둔다. 전부 선택됐다고 단정하지 않는다.

### 후속 UI-03 / UI-07 소스 개선

- UI-03: 검색 위치 ComboBoxEx의 실제 내부 edit/list 색상을 기존
  CResizingDialog 다크 팔레트로 전달하고 드롭다운 list의 테마 연결을
  열 때 갱신한다. 작은 검은 아이콘 대신 더 넓은 현재 폴더 텍스트
  버튼을 사용한다. 실행·검색·시각·배율·고대비 재검증은 남아 있다.
- UI-07: 새 설정 파일의 단일 탭과 '+' 버튼 기본 표시를 활성화한다.
  기존 사용자 저장값은 변경하지 않는다. 닫기 버튼 추가와 실제 화면
  검증은 미완료이므로 해당 항목을 완료 처리하지 않는다.

### UI-07 후속 소스 개선: 닫기 발견성

- 선택한 탭이나 마우스를 올린 탭에서 DPI 배율에 따른 'X' 닫기
  표시를 추가했다. 탭 안에 충분한 폭이 있을 때만 그리며 좁은
  탭에서는 기존 키보드·상황별 메뉴로 닫을 수 있다.
- 닫기 누름과 놓음을 구분하고 같은 탭의 X 영역에서 놓았을 때만
  기존 `ID_WINDOW_TAB_CLOSE` 명령을 실행해 확인 설정과 동작을
  재사용한다. Tooltip은 기존 현지화된 닫기 명령 문자열을 쓴다.
- 이 변경이 실제 Windows에서 올바르게 빌드되는지, 한 개·여러 개
  탭, 탭 드래그, 탭 축소, 닫기 취소, Light/Dark/High Contrast,
  100/125/150/200% 배율 및 접근성 이름을 만족하는지는
  **NOT TESTED / RETEST OPEN**이다.

### UI-08 후속 source checkpoint: 새 프로필 공유 폴더 트리

신규 프로필에서 이미 구현된 '공유 폴더 트리' 모드를 기본값으로
선택하도록 바꾸었다. 수직 분할 시 각 pane에 반복되는 폴더 트리
대신 공용 트리를 사용하는 초기 배치 개선이다. 저장된 기존 사용자
설정, 개별 트리 모드와 표시 설정은 그대로 유지한다. 파일 목록이나
정보 영역을 임의로 삭제하지 않는다.

이 변경은 화면 폭에 따른 자동 적응, 최소 너비, 정보 영역 크기,
활성 pane 식별 또는 전체 경로/브레드크럼 설계를 구현하지 않는다.
새 설정과 기존 설정 각각에서 단일/수직/수평 분할·창 크기 변경·
탭 전환·설정 저장/복구를 실제 Windows에서 점검하기 전에는
UI-08 완료로 판단하지 않는다.

### UI-08 추가 후속 소스 수정 — 분할 열과 좁은 창

- `main_frame.cpp::OnCreateClient`의 실행 인자 열 분할 값이
  행 분할 변수에 잘못 저장되는 오류를 열 분할 변수로 수정했다.
  저장된 분할 설정 또는 사용자가 지정한 행 수는 변경하지 않는다.
- `ExplorerPane::recalcLayout`에서 설명 영역이 기본 200 DLU에
  고정되지 않고 현재 pane 너비와 DPI에 따라 너비를 조정한다.
  설명 영역과 파일 목록 모두 유지하고, 좁은 창에서는 설명 영역
  너비를 최대 약 1/3 수준으로 제한한다. 기본/개별/공용 폴더
  트리 옵션과 콘텐츠 스타일 설정은 유지한다.
- 실제 Windows 분할 인자, 좁은 두 개 창, 설정 복원, 내용 가독성,
  100/125/150/200% 배율 및 화면 판독기 증거는 아직 없다.
  UI-08은 **SOURCE IMPROVED / RUNTIME RETEST OPEN**이다.

### UI-06 후속 소스 변경 — 화면 높이 내 메뉴 접근

- app-owned `BCMenu::TrackPopupMenu`는 Win32 공식 `MENUINFO`의
  최대 높이를 표시 위치의 모니터 작업 영역에 맞게 임시 지정한다.
  기존 하위 메뉴에도 적용하고, 메뉴를 닫으면 종전 설정으로
  복원한다. 메뉴 항목을 제거하지 않으며 초과 부분의 표시/스크롤은
  Windows 기본 팝업 메뉴에 위임한다.
- Dark·비고대비 상태에서는 메뉴 내부 배경 브러시를 기존 팔레트
  색상으로 임시 지정한다. 브러시 수명은 팝업 추적 구간에 묶고,
  고대비·외부 셸 메뉴는 변경하지 않는다.
- 외곽선은 Win32 기본 비클라이언트 렌더러 소유이므로 배경 수정
  자체를 밝은 테두리 문제의 완전한 해결로 기록하지 않는다.
  Windows 실제 화면·작은 모니터·하위 메뉴·키보드·고대비
  검증이 남아 있다. UI-06은 **SOURCE PARTIAL / RETEST OPEN**.

### UI-05 후속 소스 변경 — 초기 명령 밴드와 설정 여백

- 신규 기본 배치에서 북마크와 드라이브 밴드가 가능한 경우
  동일한 두 번째 줄의 빈 공간을 나눠 쓰게 한다. 기존 메인
  명령 바와 드라이브의 줄 구분은 유지한다. 작은 화면에서는
  공식 rebar wrapping/chevron이 동작하고, 북마크·드라이브의
  사용자 멀티라인 선택권은 그대로다.
- 저장된 coolbar 배치가 있으면 기존 `loadStateFile` 경로가
  사용자 band 순서/줄 구분을 우선 적용한다.
- 설정 탐색 tree의 기본 행 높이는 34→38 DPI-scaled 단위,
  설명과 설정 본문 사이 공간은 12→16으로 조정한다.
  legacy child dialog 안의 checkbox/combobox를 무작정 키워
  겹치게 만들지는 않는다.
- 실제 현재 source Windows x64 컴파일, 신규/기존 저장
  레이아웃·작은 창·배율별 커맨드 도달성·접근성·스크린샷
  은 아직 미수행. UI-05는 **SOURCE PARTIAL / RETEST OPEN**.

### UI-06 추가 소스 수정 — 자체 도구 모음의 넘침 팝업

- `CToolBarPopup::SetPosition`은 가상 바탕 화면이 아니라
  팝업이 열린 모니터의 작업 영역을 공식
  `MonitorFromPoint`/`GetMonitorInfo`로 조회해 위치를 조정한다.
  조회 실패 시 기존 바탕 화면 크기를 사용한다.
- 좌/우 대안 위치의 유효성을 확인할 때 사용되던
  `rcLeft.left >= rcDesktop.top` 오타를
  `rcDesktop.left`와 비교하도록 수정했다.
- `OnNcPaint`에서 `CWindowDC` 자동 수명 해제에
  `ReleaseDC`를 추가로 수행하던 부분도 제거했다.
- 이는 자체 chevron 팝업 수정이다. 기본 Windows 메뉴
  테두리나 화면보다 큰 자체 팝업의 스크롤 지원까지
  완료했다는 의미는 아니다. 실행·다중 모니터·고대비
  검증 전까지 **UI-06 PARTIAL / RETEST OPEN**이다.

### UI-03 후속 소스 변경 — 검색 위치 아이콘과 글자 간격

- `SearchDlg`의 ComboBoxEx 내부 편집 HWND에 공식
  `EM_SETMARGINS / EC_LEFTMARGIN`을 적용해, 현재 DPI에서
  아이콘 뒤의 입력 글자가 붙어 보이지 않도록 여유를 준다.
  기존 이미지 목록, 경로 자동 완성, 텍스트 선택, 스크롤은
  변경하지 않는다.
- 설정한 물리 여백은 `WM_DPICHANGED`에서 기본 dialog
  처리 후 다시 계산한다. 오른쪽 기본 마진은 변경하지 않는다.
- 이는 검색 창 UI-03의 추가 소스 개선일 뿐, 실제 Dark
  콤보·드롭다운 전체의 최종 표시 문제를 완료 처리한 것이
  아니다. 여러 DPI·고대비·포커스·실제 검색은 여전히
  **NOT TESTED / RETEST OPEN**이다.

### UI-01 추가 수정: 한 번에 하나의 설정 페이지만 표시

기존 코드는 이전 선택 페이지 하나만 숨겼으므로, 테마 갱신
과정에서 다른 페이지가 잘못 보이게 된 경우 다음 탐색에서도
겹친 페이지를 정리하지 못할 수 있었다. 이제 선택 변경 시
이미 생성된 다른 설정 페이지의 직접 WS_VISIBLE 상태를 확인해
모두 숨긴다. 옵션 적용의 동기식 테마 갱신 직후에도 같은 계약을
재확인하고 선택 페이지가 실제로 숨겨졌을 때만 다시 표시한다.

이전 WM_SETREDRAW 가시성 snapshot 수정은 유지하며, 저장된
설정·단축키·기존 페이지 ID는 변경하지 않는다. 이 조치는
독립적인 소스 방어선이며 원래 사용자 재현 경로의 Windows
실행과 최종 화면 확인 전에는 완료 처리하지 않는다.

### UI-01의 진단 근거와 회귀 조건

**Observed source:** `ThemeRefreshSnapshot`은 hidden child를 포함한 HWND를 모으고, visibility 보존 없이 모두에게 `WM_SETREDRAW(FALSE)` 후 `WM_SETREDRAW(TRUE)`를 보낸다. `showCfg()`는 `mShowCfg`가 가리키는 기존 페이지만 숨긴다.

**Contract:** `DefWindowProc`가 처리하는 `WM_SETREDRAW(TRUE)`는 `WS_VISIBLE`을 추가할 수 있어 이전에 숨겨진 창을 표시할 수 있다. [Microsoft WM_SETREDRAW 문서](https://learn.microsoft.com/en-us/windows/win32/gdi/wm-setredraw).

**Inference:** theme refresh가 숨겨진 설정 페이지를 노출하여 선택/본문 불일치를 만드는 경로가 유력하다. 실제 HWND style 전후값/stack은 수집하지 않았으므로 단독 root cause 확정이나 해결 완료로 기록하지 않는다. 테마 적용 후 도구에 제목 없는 추가 app window가 노출된 것도 관찰됐지만 종류는 확인하지 않았다.

**후속 구현:** freeze 직전 각 HWND의 원래 visible 상태를 보존하는 설계를 검토한다. hidden window에 무조건 redraw-enable을 보내는 경로와 sibling refresh를 함께 조사한다. 기존 live-enumeration/re-entry 방지 snapshot 계약도 유지한다.

**회귀 case:** 일반·모양·필터링 페이지를 순회하여 여러 child를 만든 후 각 테마를 적용한다. 적용 직후 및 다음 페이지 전환 후 visible page 수, 선택 제목, 실제 본문, tab focus가 일치해야 한다. 닫기/재열기는 비교용이며 성공 조건을 대신하지 않는다. 안전 속성에 대한 native/static guard를 추가하고 최종 화면을 별도로 확인한다.

### 이전 검은 글자 신고의 현재 상태

`6b18c58f`의 modern OS routing 수정이 포함된 최신 binary에서 상단 메뉴, 툴바, 드라이브/북마크의 글자가 Dark 배경 위 밝게 표시됨을 직접 확인했다. **원래 신고된 main chrome 범위의 visual 재검증은 PASS**다. UI-03과 같은 다른 renderer의 Dark 결함이나 High Contrast/Windows 10까지 해결됐다는 뜻은 아니다.

### 2026-09-26 HANG-01: 내 문서 화면의 새로운 `응답 없음` 신고

**관찰:** 추가 사용자 캡처에서 flyExplorer 제목 표시줄에
`(응답 없음)`이 표시되며 폴더 트리와 파일 목록이 비어 있다.
따라서 이전 UI-02/05 소스 개선 성공을 가정하지 않고,
UI-09와 별개인 실행 중단 문제로 우선순위를 높였다.
초기 캡처만으로는 원인을 확정하지 않았으나, 후속 `882030a` 사용자 빌드의
동일 실행을 재현하고 로컬 덤프/반복 스택을 확보했다.

**실행 근거와 수정 상태:** native 목록 아이콘 그리기에서 Shell/thumbcache
COM 대기에 진입한 뒤 MFC `OnMessagePending`이 같은 UI 스레드의
SysListView32 WM_PAINT를 반복 처리했다. 앱 소유 OLE 필터로 콜백당
paint 하나만 처리하고 중첩 dispatch를 막도록 수정했다. 추가 Shell 서버
지연 여부는 미확정이다. source preflight와 실패 패턴 검사 4개는 PASS이나
사용자가 빌드를 담당하므로 수정 후 compile/runtime/visual은 NOT TESTED다.
상세 호출 경로와 소유권은 ERROR_HISTORY의 HANG-01 후속 항목에 기록한다.

앞서 UI-02/05를 격리한 뒤에도 멈춤이 재현됐으므로 해당 격리를 해결로
간주하지 않는다. 격리 상태, 사용자 설정, UI-09 damage fix,
UI-11/12/13/14는 유지한다. **HANG-01은 후속 실행 검증 전 OPEN**이다.

**수용 조건:** 허용된 Release x64 빌드와 기존 프로필의
동일 `내 문서` 화면에서 메뉴·트리·목록·스크롤·
툴바가 로드되고 창이 1분 이상 응답해야 한다.
창 크기·최소화/복원·Light/Dark/System을 반복하고,
별도 테스트 프로필에서 첫 실행도 확인한다.
재현하면 UI 스레드 덤프를 확보한다. 이전
UI-09 테마 전환의 색상 잔상도 동일 빌드에서
별도로 확인한다. **이번 체크포인트는
Windows 빌드/런타임/시각 검증 NOT TESTED.**
UI-02 스크롤바 외형 및 UI-05 자동 행 결합은 OPEN으로
재분류하고, 부작용이 없는 대체 설계는
행동 재현 이후 별도 진행한다.

## 사용자 제공 Light/Dark 메인 화면 비교 — 2026-09-26 (화면 관찰만)

**입력 증거:** 사용자가 동일한 "내 문서" 파일 목록을 표시한 Light 및 Dark 메인 창 캡처 두 장을 제공했다. 이 기록은 첨부 화면의 **정적 시각 관찰**이다. 화면에 `build-revision.txt` 또는 실제 DPI 값이 없으므로 최신 `main` 바이너리인지, 동일 픽셀 크기/배율인지, 특정 컨트롤의 hover/focus가 무엇인지 단정하지 않는다. 개인 폴더명 등이 보이는 원본 이미지는 저장소에 추가하지 않는다. 기존 2026-09-24 직접 실행 점검 및 2026-09-25 UI-09 HWND 진단 결과와 이번 이미지의 검증 수준은 별개다.

**비교 시 확인한 화면 요소:**
- 공통: 메뉴, 주 명령 바, 드라이브 바, 북마크 바가 수직으로 쌓여 있다. 촘촘한 명령 아이콘·구분선과 비교해 드라이브/북마크 행 오른쪽에는 넓은 빈 공간이 남는다. 이는 현재 배치에 대한 사용성 검토 대상이며 곧바로 기능 결함이라고 해석하지 않는다.
- 공통: 단일 파일 목록에서도 "수정한 날짜" 열의 날짜·시간 문자열이 여러 행에서 줄임표로 끝나지만 목록 오른쪽에는 넓은 빈 영역이 남는다. 저장된 사용자 열 너비와 컨트롤 자체의 가용 폭 중 어느 것이 원인인지는 확인되지 않았다.
- 공통: 왼쪽 탐색 트리의 긴 폴더명이 가시 폭을 벗어나고 일부 확장 표식은 작다. Dark 화면에서는 표식 대비도 낮아 보인다. 옆 정보 영역에서는 설명이 좁게 줄바꿈되고 북마크 링크들이 조밀하게 세로 배치된다. 의도적인 사용자 설정·표시 기능과 실제 가독성 결함을 구분해야 한다.
- Dark에서 뚜렷함: 파일 목록 오른쪽 세로 스크롤바가 본문과 달리 밝은 흰색이며, 좌측 탐색 트리 하단 가로 스크롤바도 밝은 표면으로 남는다. Light에서는 같은 요소가 밝은 화면에 자연스럽게 섞인다. 이는 기존 UI-02의 **새 사용자 캡처 근거**이며 기본 OS 스크롤바의 비클라이언트 그리기 문제 가능성을 시사할 뿐 최종 소유자는 아직 미확인이다.
- 검증 후보: 파일 목록 헤더 글자와 하단 선이 근접하며 Dark의 항목 포커스/선택 표시가 작은 텍스트 영역에 나타난다. **글자 잘림이나 선택 상태 오류가 확정된 것은 아니다.** 동일 폰트/DPI/선택 행동으로 이전 헤더 수정의 실제 효과를 확인한다.
- UI-09: 이번 두 이미지의 상단 북마크 행에서는 이전에 보고된 아래쪽 색상/문자 잔상을 뚜렷하게 판별할 수 없다. 새 화면만으로 기존 재현 증거를 반박하거나 UI-09를 닫지 않는다. 기존 `f18468a8` Windows HWND 로그의 8개 버튼/1행/비줄바꿈, 22px 버튼/40px 자식 높이는 당시 측정값으로만 유지한다.

| 추적 ID / 구분 | 화면에서 관찰한 사실 | 개발 시 검토할 요구사항(아직 확정 원인 아님) | 재현·완료 판정 |
| --- | --- | --- | --- |
| **UI-02 / P1 — 기존 OPEN** | Dark 파일 목록 세로 및 탐색 트리 가로 스크롤바가 주변 어두운 면과 대비되는 밝은 네이티브 외형을 보인다. | 실제 scrollbar/교차 영역의 최종 렌더러와 시스템 테마 대응을 분리 조사한다. 기존 동작 및 High Contrast 유지. | 동일 화면에서 실제 스크롤/드래그·키보드 조작 후 Dark/System/Light/High Contrast 결과를 비교. 밝은 스크롤바가 남으면 OPEN. |
| **UI-05 / P2 — 기존 부분 개선/재검증** | 상단 명령이 밀집했지만 드라이브·북마크 행 오른쪽은 비어 있다. | 아이콘/글자 혼합 표현, 그룹 구분 및 클릭 면적을 검토하되 빈 공간만으로 강제 재배치하지 않는다. 기존 rebar 저장 설정과 멀티라인·chevron·단축키 유지. | 새 프로필과 기존 저장 배치, 좁은 창, DPI 변경에서 명령 가시성·키보드·설정 복원을 별도 평가. |
| **UI-11 / P2 — 신규 단일 창 열 배분 검토** | 날짜·시간 값 다수가 잘리고 파일 목록 우측에는 가용 공간이 크게 남는다. | 단일 창의 기본 너비 배분/저장된 열 설정/실제 가용 폭을 조사한다. 사용자 지정 열 너비·정렬을 강제로 덮어쓰지 않는다. 분할 창 UI-08과 재현 조건을 구분한다. | 기본/기존 프로필, 넓은/좁은 창, 긴 한국어 날짜와 파일명, 열 수동 조정/재실행을 비교. 사용 가능한 폭이 있는데 기본 날짜가 불필요하게 잘리지 않는지 확인. |
| **UI-12 / P2 — 신규 트리 가독성 검토** | 긴 항목명이 트리 폭 밖으로 잘리고 확장 표식이 작거나 Dark에서 옅게 보인다. | tree 표시/말줄임·수평 탐색/툴팁, 확장 및 선택·hover·focus 대비, DPI를 함께 검토한다. 사용자 트리 너비·레이아웃 설정을 임의 초기화하지 않는다. | 긴 한글/영문 폴더, Light/Dark/High Contrast, 100/125/150/200% DPI, 마우스·키보드로 전체 대상에 접근 가능해야 한다. |
| **UI-13 / P2 — 신규 정보 영역 밀도 검토** | 현재 폴더 설명과 북마크 목록이 좁은 정보 영역에 촘촘히 나타나 파일 목록의 가로 공간도 차지한다. | 최소 너비, 사용자 조정 가능 영역, 긴 한국어 문장 줄바꿈 및 링크 간격을 검토한다. 북마크/설명 자체를 임의 제거하지 않는다. | 일반/좁은 창과 분할 UI-08에서 텍스트 잘림·링크 클릭·탭 탐색·저장된 표시 설정을 비교한다. |
| **UI-14 / 조사 후보, 오류 미확정** | 헤더 글자·구분선 간격이 좁아 보이며 Dark의 텍스트 영역 포커스 테두리가 도드라진다. | 이전 파일 목록 헤더 세로 잘림 수정의 적용 여부와 selection/focus/hover의 실제 렌더링을 측정한다. 현재 사진만으로 재발 판정하지 않는다. | 동일 리비전과 DPI에서 헤더 높이·글꼴 metrics·키보드 선택 동작·Light/Dark 캡처가 있어야 결함 확정. |

**검증 매트릭스:** 같은 리비전의 프로그램·같은 폴더·동일한 창/패널 크기에서 두 테마를 비교하고, Light/Dark/System·High Contrast 및 100/125/150/200% DPI를 각각 *실행한 범위만* PASS로 기록한다. 기본 사용자 설정과 기존 설정 파일의 결과를 나누며 긴 폴더명/한국어 날짜/북마크 항목을 포함한다. Windows 컴파일, interactive UX, 선택/hover/focus, 스크롤 조작 및 동일 조건 최종 화면은 이 문서 변경으로 실행되지 않았다: **NOT TESTED**. UI-09 및 기존 항목의 상태는 위 화면만으로 종료하지 않는다.

### 2026-09-26 UI-11 / UI-12 / UI-13 first source correction (runtime acceptance pending)

**UI-11:** The original default `ExplorerCtrl` modified-date column width was 140 physical pixels. A new default FOLDER_DEFAULT layout and the re-enabled default modified-date column now use a 225 logical-pixel base scaled to that list HWND's current DPI. Already loaded/persisted column widths, user order, per-folder layouts and manual resizing are intentionally not migrated. A former user profile showing the screenshot may still have its original narrow column, so absence of ellipsis on an existing profile is NOT TESTED.

**UI-12:** The tree now enables documented native `TVS_INFOTIP` and answers `TVN_GETINFOTIP` with the full displayed tree-item label. Existing horizontal scrolling, saved tree width, folder selection, keyboard, native expand glyphs, drag/drop and item editing are otherwise unchanged. Actual tooltip visibility, timing, clipping and high-contrast behavior require Windows verification.

**UI-13:** The optional Explorer-style folder information pane paints its title, dividers and bookmark heading within its actual client width instead of to fixed 200/198px coordinates. Its preferred width grows from 200 to 224 logical px; the narrow-layout minimum budget increases from 96 to 120 logical px only when space permits. The original one-third pane cap and 280 logical-px list budget remain. Bookmark links use 5px vertical separation (previously 2) through their shared position/scroll-height constant. It is still possible for very long names and narrow windows to require user resizing or scrolling: no blanket guarantee of zero truncation is made.

`validate_light_dark_main_view_sizing` checks that these source-level contracts stay connected. Actual Windows Release-x64-Unicode compilation, real Light/Dark/System/High Contrast screenshots, 100/125/150/200% DPI, existing-user settings, live tooltip/hit regions and pane resize behavior have **NOT BEEN TESTED** by this source checkpoint.

**Other screenshot items:** UI-02 remains OPEN: OS-owned native list/tree scrollbar painting cannot safely be declared fixed from a client palette change, and no unsupported Windows private theme strings or behavior-breaking overlay are added here. UI-05 remains PARTIAL: separate Rebar rows were introduced while diagnosing UI-09 and saved user positioning/chevron and multiline must be inspected before regrouping to reduce unused width. UI-14 remains an unconfirmed focus/header appearance candidate because font-metric header sizing already exists. UI-09 remains OPEN despite the lack of clear slivers in the later pair of photographs; compare with the old reproduced screenshot using the opt-in trace where needed. GitHub Actions were NOT RUN.

### 2026-09-26 remaining issues: UI-02/05/14 source improvements, UI-09 unchanged

UI-02: The list/tree palette does not own standard non-client scrollbar pixels. A Dark-only and High-Contrast-safe ModernUI helper now uses documented GetScrollBarInfo to obtain the actual native vertical/horizontal scrollbar, arrow states, thumb and intersection rectangles, then draws only those pixels through GetWindowDC *after* the native control processes non-client and scroll events. The OS still owns hit tests, accessibility, mouse drag, keyboard and scroll range. No undocumented Windows dark theme names or exports were used. The native event ordering, speed of thumb drag, Theme transitions and actual Light/Dark/High Contrast screenshot have NOT BEEN TESTED.

UI-05: The three independent initial bands remain until native AutoSize completes. For *new profiles without a saved CoolBar file only*, single-line visible adjacent drive and bookmark bands may share their row when measured cxIdeal widths fit the Rebar client with 48 DPI-scaled logical pixels of extra room. The pending flag is cleared before mutation to prevent layout re-entry. Loaded manual band position/row choices are authoritative, and explicit multiline bookmarks still occupy a separate row. These are scoped code changes; saved/new/multiline/resize visual behavior is NOT TESTED.

UI-14: The global header mCallDrawItem flag previously assumed every header cell was owner-draw if at least one sent DrawItem. Mixed owner/native headers could leave a native light cell in Dark. After native paint, the final painter now colors only the remaining non-owner-draw cells; the manual path includes hover and sort glyphs are suppressed when a user-resized column is too narrow. The screenshot's specific header/focus concern itself remains UNCONFIRMED pending interaction.

UI-09 remains OPEN: prior screenshot showed slivers at a revision that was actually built. The native Windows geometry was one 22px item row within a 40px child, not a native second row. The current FXFILE_UI09_TRACE=1 internal paint/size tracing still needs a revision-matched run to identify the final owner; new rebar grouping is delayed and slack-guarded but is NOT a verified remedy.

A source invariant validate_remaining_main_window_source_candidates now checks documented native geometry, accessibility-preserving owner order, new-profile-only rebar layout and mixed header safeguards. No Windows local_ci.bat x64, same-screen UI-02/05/09/14 runtime, 100/125/150/200% DPI or High Contrast execution has been performed. GitHub Actions was not executed.

**참고:** 위에 기록된 과거 단계의
`FXFILE_UI09_TRACE=1` 수집 지시는 현재
통합 소스에 해당하지 않는다. 제품 임시 추적
writer는 백업에서 원인 확인 후 제거되었다.

## 코드로 확인한 현대 Windows 호환성 과제

아래는 source debt/설계 후보이며 이번 실행에서 해당 동작 실패를 재현한 목록이 아니다. API가 오래됐다는 이유만으로 전체 교체하지 않는다.

| ID / 우선순위 | Observed / Contract | 단계적 개선과 검증 기준 |
| --- | --- | --- |
| OS-01 / P2 | `file_operation_core.cpp`, `shell.cpp`, `shell_new.cpp`에 `SHFileOperation` 호출이 남아 있다. Microsoft는 Vista 이후 대체 API로 `IFileOperation`을 안내한다. | 기존 seam에서 COM apartment/lifetime, 충돌 처리, 취소·부분 성공·undo·진행 표시 의미를 먼저 정의. Unicode/space/다중 파일/동일 볼륨/권한 실패 회귀를 유지하고 새 adapter를 좁게 도입. [공식 API 문서](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shfileoperationw) |
| OS-02 / P2 | Windows `XPR_MAX_PATH`는 `MAX_PATH`; 주소/검색 등 고정 buffer와 입력 제한이 존재. 현재 manifest에 `longPathAware`는 없다. | path 생성→입력→Shell→file operation 전체 경로를 조사. Unicode, UNC, 260자 경계/초과, 취소/오류 표시 fixture 추가. manifest 하나만 추가하고 장경로 지원 완료라 하지 않음. 일부 Win32 API의 opt-in에는 OS 설정도 관계하며 이번 작업은 OS 설정을 변경하지 않음. [장경로 계약](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation) |
| OS-03 / P2 | `env_path.cpp`, `shell_new.cpp`의 `SHGetSpecialFolderPath`/CSIDL 및 고정 buffer. | `SHGetKnownFolderPath`/KNOWNFOLDERID 전환 후보를 caller별 검토. redirected Documents, OneDrive, template folder, 가상 Shell folder와 filesystem path의 차이를 보존. [Known Folders](https://learn.microsoft.com/en-us/windows/win32/shell/known-folders), [기존 API](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shgetspecialfolderpathw) |
| OS-04 / P2 | manifest의 PerMonitorV2/PerMonitor 및 `asInvoker`는 이미 존재한다. | DPI 기능 부재로 기록하지 않는다. 100/125/150/200%, 혼합 모니터 이동, 확대된 텍스트에서 icon/행 높이/dialog clipping을 실제 검증. High Contrast와 keyboard focus/스크린리더 name-role-state 검증은 별도 matrix로 남김. |

자동 업데이트는 최신 source에서 의도적으로 제거됐다. updater x64 전환을 현대화 과제로 되살리지 않는다. keyhook/launcher Win32 helper의 기존 mapping은 별도 증거 없이 변경하지 않는다.

### 2026-09-26 UI-02~05/11~14 재작업: 동기 호출을 배제한 코드 적용

사용자 요청을 기준으로 기존 구현을 다시 확인했으며
현재 `main`에 남아 있는 UI-11/12/13
(새 기본 날짜 열/툴팁/정보 패널)과 UI-14
(혼합 헤더 그리기) 코드는 기존 상태를 보존한다.
실제 Windows 화면 검증 증거가 새로 확보된 것은 아니다.

**UI-02:** OS 기본 스크롤바는 ListCtrl/TreeCtrl의
client 색상만으로 어두워지지 않는다. 이번
구현은 `GetScrollBarInfo`의 실제 thumb,
화살표, track 및 두 스크롤바가 만나는 영역을
Dark 팔레트로 다시 그리되, 기존에 제거한
`WM_NCPAINT` 내부 직접 `GetWindowDC` 호출을
반복하지 않는다. 네이티브 처리 완료 후
`PostMessage`로 단일 지연 작업을 예약하고
중복 이벤트를 합친다. 그리는 중 들어오는
추가 비클라이언트 알림은 새 작업을 예약하지
않으며 Light/High Contrast는 기본 OS
렌더러만 사용한다. 스크롤 hit-test·드래그·
휠·접근성 계층은 Windows 소유 그대로다.
완료 조건: Dark에서 실제 수직/수평 bar와
thumb·arrow·junction 최종 픽셀이 일치하고
빠른 drag와 마우스 휠, Light 전환,
고대비가 정상이어야 한다.

**UI-05:** 최초 Rebar 생성 동안은 북마크
행을 독립시켜 UI-09의 초기 높이 문제에
영향을 주지 않는다. 저장된 배치 없는
새 프로필에서만 기본 드라이브/북마크가
한 행에 들어갈 수 있는지 확인하며,
`OnSize`는 실제 크기 계산 이후 예약 메시지만
전송한다. 예약 핸들러에서 실제
`cxIdeal`과 Rebar의 넓이를 측정하고
48-DIP 여유가 존재할 때 한 차례만 합친다.
저장한 사용자 행 순서와 다중 행 설정을
자동 변경하지 않는다. 완료 조건:
신규 넓은 화면의 공간 배분 개선,
기존 설정의 행·순서 유지, 좁은 창
chevron, UI-09 동시 재발 부재다.

**UI-11:** 새 기본 폴더의 날짜 열을
225 DIP로 초기화하는 기존 코드는 유지한다.
저장된 사용자 폭은 강제 변경하지 않는다.
**UI-12:** 기존 `TVS_INFOTIP`를
유지해 잘린 폴더명 전체를 볼 수 있게 한다.
확장 표식의 실제 DPI/대비는 별도 실행
확인이 필요하다.
**UI-13:** 클라이언트 너비 기반
제목/북마크 배치와 가변 패널 폭을 유지한다.
**UI-14:** 이미 소스에 반영된
혼합 그리기/좁은 정렬 화살표 보호를
유지한다. 잘못된 포커스 상태는 원래
정적 사진만으로 확정되지 않았다.

**검증 경계:** 소스코드와 기존 테스트
등록 여부, 새 지연 메시지 계약을
별도로 점검했다. 전체 저장소 Python
preflight 실행, Windows 컴파일 및
실제 최종 픽셀/스크롤·배치·DPI·고대비
시험은 아직 수행하지 않았다. 실행 전
모든 항목을 시각 해결 완료로 닫지 않는다.
GitHub Actions는 실행하지 않았다.

### 2026-09-26 실사용 후속 캡처: 스크롤바 drag / 짧은 이름 열 / 필터 강조

- **UI-02 — 여전히 OPEN:** 사용자는 손잡이 드래그 도중
  밝은 기본 스크롤바를 다시 확인했다. 현재 지연된
  `GetWindowDC` 재그리기는 OS 네이티브 손잡이 추적 중
  최종 프레임이 되지 않는 구조적 한계가 있다.
  임의로 재도색 빈도만 늘리거나 사용자 입력을
  가로채지 않는다. 정확한 Windows 메시지·그리기
  순서 및 원본 실행 리비전을 기록하고, 네이티브
  입력·접근성·Light/System/High Contrast를
  유지하는 실질적 렌더링 소유 방식을 설계해야 한다.
- **이름 열 — CODE UPDATED / RETEST OPEN:** 기본 새
  목록의 이름 열 150px은 실제 사용자 화면에서
  불필요한 말줄임을 일으켰다. 신규 기본 폭을
  280 논리 픽셀로 바꾸고 DPI를 적용했다.
  기존 수동·저장 너비는 임의 변경하지 않는다.
  이전 사용자는 기본 제공 자동 열 너비 옵션이나
  수동 열 조절로 변경할 수 있다.
- **필터 설정 선택 — CODE UPDATED / RETEST OPEN:**
  여러 선택 행 전체가 선명한 시스템 파란색으로
  칠해져 미리보기의 가독성을 저해한다.
  Light/Dark의 선택 행만 `CDRF_SKIPDEFAULT`로
  직접 소유하여 12%·6%의 부드러운 강조로
  변경하되, 네이티브 선택/키보드·원래 아이콘,
  이름·확장자·저장된 필터 RGB, 미세한
  포커스 표시를 유지한다. 고대비에서는
  원래 Windows 선택 표시를 사용한다.

회귀 소스 검사는 선택 상태 비변경, 두 열/아이콘
유지, 고대비 우회, 신규 이름 너비와 저장값
보존 경계를 다룬다. 전체 Windows 빌드와
실제 100/125/150/200% DPI,
같은 환경의 Light/Dark/고대비 및
손잡이 드래그 결과는 이번 환경에서
NOT TESTED다. 세 항목 모두 동일 화면의
최종 실행 검증 없이는 전체 해결로 닫지 않는다.

## 다음 구현 순서와 인수 기준

1. UI-01 설정 페이지 무결성: 원래 visibility 보존과 회귀 guard, 같은 클릭 경로 runtime 재검증.
2. UI-02/03 Dark renderer 범위: client/non-client, ComboBoxEx 내부 HWND, legacy glyph 각각 owner를 정하고 동일 계열 sibling을 검사. undocumented Explorer API/theme string은 사용하지 않는다.
3. UI-04~08 command/탭/분할/대화상자 크기: Windows Explorer reference와 동일 배율에서 비교하고 command/shortcut 의미를 보존.
4. OS-01~04는 개별 변경 단위로 분리하여 기존 파일 처리 semantics와 fallback을 검증한 뒤 도입.

모든 수정은 Static PASS / Compile·Link PASS / Runtime PASS / Visual PASS를 따로 남긴다. 제품 코드가 바뀌면 현재 허용된 `local_ci.bat x64`를 수행하고 해당 UI case를 재실행한다. 확대 검증이 필요한 Windows 10/High Contrast/DPI/clean installer는 실제 수행 전까지 NOT TESTED를 유지한다.


## 2026-09-27 Phase 1: Explorer-reference tab title readability

- Observed on connected Windows 11 at identical 1240 x 790 geometry and current Dark mode using the same synthetic fixture (30 folders and 175 files): Explorer displays the complete FXUI_Synthetic_Root title; baseline flyExplorer's 150-DIP tab truncates it. Local captures: logs/phase1/ in isolated worktree.
- Scoped product change: default tab size to 232 logical pixels; cap the active tab by remaining width after the new-tab button; distribute nonnegative remaining fixed-width among other tabs. Do not change file operations, main toolbar bands, tab IDs or saved user settings.
- Acceptance: complete synthetic folder title, usable close/new-tab controls at wide width, narrow and multitab window layout without hangs. Revision-matched Windows x64 compile/link PASS, native functional 17/0 PASS, targeted source checks 5/5 PASS; official runtime smoke SKIPPED to preserve existing user HKCU. Direct isolated runtime/visual PASS at 5db3f92b46bf38c2cea2ed0e12f06d199ecc86de: complete original tab title; New Tab mouse click opened a second tab; 470px narrow window remained responsive and retained tab controls; test process exited normally. Keyboard-only input, Light/High Contrast and other DPI modes NOT TESTED. Other top command area gaps remain a future task.


## 2026-09-27 Phase 2: native rounded address field

- The same-PC Windows 11 Explorer reference (ignored local logs/phase1/windows-explorer-reference.png) has a rounded navigation field. The tested Phase1 flyExplorer synthetic Dark/Light screens still had square address corners. These captures used different fixtures/window sizes, so this is a qualitative shape reference, not a pixel-exact Explorer match.
- Product commit eb958777a7cb182606b4511672abf08f852a9daf leaves the MFC ComboBoxEx, native inner ComboBox/Edit, autocompletion and command IDs intact. After native outer/inner painting, it masks only square address corner pixels and draws a one-pixel outline using the existing six-DIP Fluent corner metric. High Contrast retains native control painting.
- Windows VS2026/v145 Release x64 compilation and linking PASS; native functional regression 17/0 PASS; full source preflight PASS; focused header/address source tests 8/8 PASS. HKCU-sensitive official runtime smoke SKIPPED to preserve actual saved user settings.
- Revision-matched synthetic GUI PASS: Dark, Light and System have 28px native list headers, header click and address edit mouse/keyboard focus (HOME/END), and clean process shutdown; the narrow Dark window retains 28px header and stays responsive. The actual native Light-mode address dropdown opened by click and closed via Escape.
- Old and new Dark/Light/System screens remain under ignored local logs/header-address-retest and were visually compared. Read-only real user config records Light mode, but the entire personal saved layout/font/profile was not used or altered. Actual personal screen, OS High Contrast, 125/150/200% DPI and complete UI-02/UI-05/UI-09/HANG-01 interactive matrix remain RETEST OPEN; do not upgrade the synthetic PASS to those environments.
- Tested executable revision is eb958777a7cb182606b4511672abf08f852a9daf; the subsequent docs-only commit is not a separate C++ build.


## 2026-09-27 UI/UX Phase 3 — primary native navigation target

- Compared the existing same-PC native Windows 11 Explorer reference (local-only logs/phase1) with the Phase2 flyExplorer UI, and performed same-fixture Phase2-vs-Phase3 flyExplorer comparison at the same 1150x765 window geometry. Native Explorer has a compact icon-oriented navigation row, whereas flyExplorer must retain its configurable multi-band MFC toolbar; this phase alters only the visual Back/Forward/Up icon targets instead of restructuring or overwriting user-saved bands.
- The live user profile has six local files under AppData/fxfile/conf. Only fxfile.conf, fxfile-main.conf, fxfile-toolbar.dat and fxfile-coolbar.dat were copied to ignored local logs/phase3 for layout verification; in the copy alone, single-process routing, global hotkeys/startup and shell context registration were disabled. An isolated APPDATA was set for the test process and a read-only --conf_dir was passed. No user config or HKCU keys were intentionally mutated. Four original config file hashes matched before/after baseline and after source-change tests; saved toolbar geometry was compared numerically, while personal saved names/screenshots were never uploaded or committed. This is a partial visual profile replica, NOT a claim of complete HKCU or personal-profile isolation.
- Product source 6d1f76388b0b8326568478ce35814aba1eb69a0e keeps native ToolbarWindow32 command ID, hit test, configured image size, order, below-icon user text and history dropdown. Only ID_GO_BACK, ID_GO_FORWARD, ID_GO_UP in AFX_IDW_TOOLBAR get a bounded DPI-scaled 36-DIP icon/hot tile; the rest of the toolbar, including bookmarks/drive, is unchanged. Back label optional text-right label starts beyond the navigation tile; dropdown hover is independent of the main tile.
- Full source invariant preflight and focused Phase3 source regression suite PASS. Windows VS2026/v145 Release x64 native compile/link and 17/0 functional regression PASS; official HKCU-sensitive runtime smoke SKIPPED. Actual mouse navigation in an isolated synthetic nested fixture: Up, Back, Forward, and Up commands verified by observed current folder title; Back hover tile produces changed composited pixels. Synthetic Dark, Light and System GUI, 28px native header, address Edit keyboard focus and HOME/END, narrow Dark responsiveness, and clean test-process shutdown PASS. Partial saved-user-profile copy reproduced toolbar/header/address geometry with original files unchanged.
- Private copied-profile screenshot and before/after synthetic captures remain only under ignored logs/phase3, never in GitHub. Actual personal file paths, full HKCU state, OS High Contrast, different DPI, live pre-existing flyExplorer process, and the full UI-02/UI-05/UI-09/HANG-01 interaction matrix remain NOT TESTED. The preceding suite does not establish pixel-identical Windows Explorer appearance. Final docs-only merge revision may differ from executable build 6d1f76388b0b8326568478ce35814aba1eb69a0e.


## 2026-09-27 Phase 4 — guarded DPI validation and separate C++/WinRT feasibility

- Actual connected-PC system DPI 96. At unchanged compiled product revision 6d1f76388b0b8326568478ce35814aba1eb69a0e, safely launched a read-only partial clone of four saved UI files with separate APPDATA and disabled test-only side effects; recorded prior-matching native three 1175x40 plus one 1175x21 toolbar bands, 28px header and 36px address; original config hashes unchanged and test process exit 0. No confirmed new UI defect in the tested subset, so production code was not modified.
- Existing valid same-revision Phase3 Dark/Light/System synthetic verification reused, not rerun. Other real DPI values (125/150/200%), actual OS High Contrast, fresh equivalent Explorer capture, full user HKCU isolation and full interactive regression matrix remain NOT TESTED. Official HKCU-sensitive runtime smoke SKIPPED.
- Isolated experimental branch experiments/phase4-ui-tech-20260927 at ad561271a08cd493ad477059f306e5cbfd22f4ac contains a small compiled C++/WinRT Foundation + native Win32 navigation proof. Actual 96-DPI real GUI Up/Back/Forward/Up and exit passed; this is explicitly NOT a WinUI 3 prototype and is NOT connected to product navigation. No migration conclusion is justified from this proof.
- Detailed architecture observations, alternative comparison, missing evidence and safe next gates: [Phase4 framework evidence](UI_FRAMEWORK_PHASE4_EVALUATION.md). No SDK installation or GitHub Actions dispatch.

## 2026-09-28 Phase5 continued — real product command bridge via isolated WinUI 3 GUI

- Confirmed native MainFrame command route ID_GO_UP/BACK/FORWARD to existing GoDirect*Command and ExplorerCtrl. An isolated test-owned fxfile.exe with six private copied UI files and separate APPDATA responded to scalar, timeout-bound WM_COMMAND and updated actual synthetic folder history. Original six user settings SHA256 hashes identical; two owned child processes closed with exit 0. Initial incorrect HWND selection targeted a dark overlay and was discarded as test-harness error, not a product bug.
- Actual WinUI 3 XAML buttons, on an explicit **test-owned PID+MainFrame HWND** proof-only mode, sent commands to the real unchanged product. UI Automation mouse tests verified Up/Back/Forward, actual real-product titles and WinUI mirror/status at real system DPI 96. Original independent WinUI 3 navigation GUI regression and x64 proof build passed; product source unchanged. Commit: e845eb45f3bd3cf978bbecaecf7984dc6f0d22a0 on experiments/phase5-real-winui3-20260928, NOT on main.
- Still NOT TESTED: same-process WinUI host, actual active-pane enabled-state/address adapter, full Shell/multi-pane functionality, real 125/150/200% DPI, actual Windows High Contrast and lifecycle-cost superiority. The VS18 native/UAP NuGet target mismatch remains and the private experiment-only ResolveNuGetPackages=false bypass is not production-approved. Full evidence: [Phase5 bridge evidence](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md).

## Later 2026-09-28 Phase5: standard NuGet asset resolution PASS, strict bridge shutdown FAIL

- The isolated actual WinUI 3 C++ Debug|x64 build now PASSES normal ResolveNuGetPackageAssets and linking after matching native,Version=v0.0, clearing mismatched VS18 UAP fallback and implicit NuGet runtime ID; prior skip-target workaround removed. Existing standalone real 96-DPI mouse/keyboard GUI regression PASSED with clean exit.
- The explicitly test-owned product bridge delivered all three actual product commands when real WinUI 3 XAML buttons were invoked using UI Automation InvokePattern and original six user setting hashes were unchanged. Repeated shared-desktop pointer automation sometimes missed the Back event; after Invoke, the WinUI 3 helper sometimes timed out on shutdown and was forcibly closed. Strict bridge test currently FAIL, not a production product defect. No same-process host, higher real DPI/High Contrast or production feature/cost parity was tested. Experiment commit ddff6a3397e3c2ade38f1a173a6567366ec9ac84; see UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md.

## 2026-09-28 product-wide hands-on UX follow-up

For additional isolated real-product observations, source-supported
candidate causes, priorities and explicit NOT TESTED boundaries, see
[the new product-wide UX development backlog](UI_UX_HANDS_ON_BACKLOG_20260928.md).
The earlier screen-reproduction history and its original status remain above.

## 2026-09-28 Phase 5 correction: strict bridge harness shutdown

The earlier Phase 5 strict shutdown failure was later traced to
test-harness HWND selection, NOT independently shown to be a
WinUI 3 product shutdown defect. The corrected owned strict
bridge then passed repeated actual 96-DPI Up/Back/Forward
and clean child-process exits. See the later
[main bridge evidence](UI_FRAMEWORK_PHASE5_COMMAND_BRIDGE_EVIDENCE.md)
for precise revisions and boundaries. Same-process product
shipping and PRI installer redistribution are separate,
unfinished experiment-only tasks linked from
[the current status](CURRENT_STATUS.md).
