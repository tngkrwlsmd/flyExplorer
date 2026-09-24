# 실행 기반 UI/UX 점검 — 2026-09-24

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
| UI-08 / P2 | 수직 듀얼 창에서 각 pane의 tree와 설명 영역이 반복되어 파일 목록 너비가 크게 줄고 열/수정 날짜가 잘린다. 주소는 현재 설정에서 마지막 폴더명 위주로 보인다. | 좁은 pane에서 정보 우선순위/최소 너비/설명 영역 크기 조절을 개선하고 활성 pane을 명확히 표시. 전체 경로 옵션과 고급 기능 보존; breadcrumb는 설계 후보. | `explorer_pane.cpp`, `explorer_view.cpp`, `splitter.cpp`, `address_bar.cpp` |

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

### UI-01의 진단 근거와 회귀 조건

**Observed source:** `ThemeRefreshSnapshot`은 hidden child를 포함한 HWND를 모으고, visibility 보존 없이 모두에게 `WM_SETREDRAW(FALSE)` 후 `WM_SETREDRAW(TRUE)`를 보낸다. `showCfg()`는 `mShowCfg`가 가리키는 기존 페이지만 숨긴다.

**Contract:** `DefWindowProc`가 처리하는 `WM_SETREDRAW(TRUE)`는 `WS_VISIBLE`을 추가할 수 있어 이전에 숨겨진 창을 표시할 수 있다. [Microsoft WM_SETREDRAW 문서](https://learn.microsoft.com/en-us/windows/win32/gdi/wm-setredraw).

**Inference:** theme refresh가 숨겨진 설정 페이지를 노출하여 선택/본문 불일치를 만드는 경로가 유력하다. 실제 HWND style 전후값/stack은 수집하지 않았으므로 단독 root cause 확정이나 해결 완료로 기록하지 않는다. 테마 적용 후 도구에 제목 없는 추가 app window가 노출된 것도 관찰됐지만 종류는 확인하지 않았다.

**후속 구현:** freeze 직전 각 HWND의 원래 visible 상태를 보존하는 설계를 검토한다. hidden window에 무조건 redraw-enable을 보내는 경로와 sibling refresh를 함께 조사한다. 기존 live-enumeration/re-entry 방지 snapshot 계약도 유지한다.

**회귀 case:** 일반·모양·필터링 페이지를 순회하여 여러 child를 만든 후 각 테마를 적용한다. 적용 직후 및 다음 페이지 전환 후 visible page 수, 선택 제목, 실제 본문, tab focus가 일치해야 한다. 닫기/재열기는 비교용이며 성공 조건을 대신하지 않는다. 안전 속성에 대한 native/static guard를 추가하고 최종 화면을 별도로 확인한다.

### 이전 검은 글자 신고의 현재 상태

`6b18c58f`의 modern OS routing 수정이 포함된 최신 binary에서 상단 메뉴, 툴바, 드라이브/북마크의 글자가 Dark 배경 위 밝게 표시됨을 직접 확인했다. **원래 신고된 main chrome 범위의 visual 재검증은 PASS**다. UI-03과 같은 다른 renderer의 Dark 결함이나 High Contrast/Windows 10까지 해결됐다는 뜻은 아니다.

## 코드로 확인한 현대 Windows 호환성 과제

아래는 source debt/설계 후보이며 이번 실행에서 해당 동작 실패를 재현한 목록이 아니다. API가 오래됐다는 이유만으로 전체 교체하지 않는다.

| ID / 우선순위 | Observed / Contract | 단계적 개선과 검증 기준 |
| --- | --- | --- |
| OS-01 / P2 | `file_operation_core.cpp`, `shell.cpp`, `shell_new.cpp`에 `SHFileOperation` 호출이 남아 있다. Microsoft는 Vista 이후 대체 API로 `IFileOperation`을 안내한다. | 기존 seam에서 COM apartment/lifetime, 충돌 처리, 취소·부분 성공·undo·진행 표시 의미를 먼저 정의. Unicode/space/다중 파일/동일 볼륨/권한 실패 회귀를 유지하고 새 adapter를 좁게 도입. [공식 API 문서](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shfileoperationw) |
| OS-02 / P2 | Windows `XPR_MAX_PATH`는 `MAX_PATH`; 주소/검색 등 고정 buffer와 입력 제한이 존재. 현재 manifest에 `longPathAware`는 없다. | path 생성→입력→Shell→file operation 전체 경로를 조사. Unicode, UNC, 260자 경계/초과, 취소/오류 표시 fixture 추가. manifest 하나만 추가하고 장경로 지원 완료라 하지 않음. 일부 Win32 API의 opt-in에는 OS 설정도 관계하며 이번 작업은 OS 설정을 변경하지 않음. [장경로 계약](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation) |
| OS-03 / P2 | `env_path.cpp`, `shell_new.cpp`의 `SHGetSpecialFolderPath`/CSIDL 및 고정 buffer. | `SHGetKnownFolderPath`/KNOWNFOLDERID 전환 후보를 caller별 검토. redirected Documents, OneDrive, template folder, 가상 Shell folder와 filesystem path의 차이를 보존. [Known Folders](https://learn.microsoft.com/en-us/windows/win32/shell/known-folders), [기존 API](https://learn.microsoft.com/en-us/windows/win32/api/shlobj_core/nf-shlobj_core-shgetspecialfolderpathw) |
| OS-04 / P2 | manifest의 PerMonitorV2/PerMonitor 및 `asInvoker`는 이미 존재한다. | DPI 기능 부재로 기록하지 않는다. 100/125/150/200%, 혼합 모니터 이동, 확대된 텍스트에서 icon/행 높이/dialog clipping을 실제 검증. High Contrast와 keyboard focus/스크린리더 name-role-state 검증은 별도 matrix로 남김. |

자동 업데이트는 최신 source에서 의도적으로 제거됐다. updater x64 전환을 현대화 과제로 되살리지 않는다. keyhook/launcher Win32 helper의 기존 mapping은 별도 증거 없이 변경하지 않는다.

## 다음 구현 순서와 인수 기준

1. UI-01 설정 페이지 무결성: 원래 visibility 보존과 회귀 guard, 같은 클릭 경로 runtime 재검증.
2. UI-02/03 Dark renderer 범위: client/non-client, ComboBoxEx 내부 HWND, legacy glyph 각각 owner를 정하고 동일 계열 sibling을 검사. undocumented Explorer API/theme string은 사용하지 않는다.
3. UI-04~08 command/탭/분할/대화상자 크기: Windows Explorer reference와 동일 배율에서 비교하고 command/shortcut 의미를 보존.
4. OS-01~04는 개별 변경 단위로 분리하여 기존 파일 처리 semantics와 fallback을 검증한 뒤 도입.

모든 수정은 Static PASS / Compile·Link PASS / Runtime PASS / Visual PASS를 따로 남긴다. 제품 코드가 바뀌면 현재 허용된 `local_ci.bat x64`를 수행하고 해당 UI case를 재실행한다. 확대 검증이 필요한 Windows 10/High Contrast/DPI/clean installer는 실제 수행 전까지 NOT TESTED를 유지한다.
