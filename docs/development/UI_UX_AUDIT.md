# flyExplorer Windows 11 벤치마킹 및 UI/UX 점검

## 2026-10-20 G02/G06 — 탭 이름·명령 대상 및 주요 키보드 경로

- 조건: main `db10ef42`, 변경 없는 `4bdde290` 제품 소스의 EXE `eb89f47d...`
  (CURRENT_STATUS.md 전체 해시), 로컬 Release 소유 실행 1회. 작업 공간 A는
  합성 fixture, B는 기본 내 PC 경로이며 파일 작업 없이 탭만 추가·전환·닫았다.
- **기능 GUI 관찰 PASS:** 두 작업 공간×좌우×두 폴더 탭의 수준/패널 이름,
  네 영역의 새 탭 명령 대상, B의 좌우 닫기 범위, WindowTab 전환·닫기 및 A 보존.
  F6 후 실제 파일 방향키 선택, 목록 Tab/Shift+Tab 왕복, Ctrl+L→Tab 검색 진입,
  정렬 메뉴 방향키·Escape·Enter 재열기, A 왼쪽 폴더 탭 방향키+Enter 왕복도 확인했다.
- **검증 공백:** 초기부터 모든 컨트롤을 통과하는 연속 순회와 네 영역 전체의
  키보드 포커스 검증은 미완료다. 관련 파일은 `MainWindow.xaml.cpp`,
  `MainWindow.xaml`, `ShellHeader.xaml`, `FileToolbar.xaml`이다. 완료 조건은
  강제 포커스 없이 해당 경로를 순회하고 화면 포커스·실제 명령 대상이 일치하는 것.
  다음 검증은 이 남은 범위만 수행하며 확인된 탭 생성 행렬이나 빌드는 반복하지 않는다.
- 도구의 `focused_element`는 실제 포커스와 달리 FileNameBox로 고정됐다.
  실제 화면/입력 결과로 판정했으며 입력 간섭·가림이 있던 시도는 수용에서 제외했다.
  이 도구 한계를 제품 결함으로 분류하거나 제품 코드를 추측해 바꾸지 않았다.
- **시각 검토:** fixture 화면의 Dark/96 DPI/1906×1016에서 파일·작업 공간 탭·
  폴더 탭·메뉴 버튼의 포커스 표시를 확인했다. 전체 시각 수용은 NOT TESTED다.
- 앱 exit 0, 사용자 설정·합성 파일 불변. 제품 수정·새 빌드 없음.

## 2026-10-20 G01 종료 후속 — 간헐적 위험, 원인 미확정

- main `08e066a1`에서 제품 소스가 동일한 기존 EXE(`eb89f47d...`, 아래 전체 해시)를
  재사용했다. 같은 소유 v4 세션의 UIA 텍스트 확인 실행과 실제 캡처·두 번째 탭 전환
  실행 모두 정상 exit 0 및 원본 설정 불변이었다. 후자는 오름차순 목록도 확인했다.
- 앞선 종료 잔류는 재현되지 않았다. **간헐적 종료 위험**을 보존하며 원인·수정
  완료 및 G01 최종 수용을 주장하지 않는다. 아래 관련 파일 경계를 유지하되,
  다음 진단은 실제 잔류 시 네이티브 호출 스택 확보다. 동일 실행 반복은 하지 않는다.
- 이번 기능 관찰은 정상 종료했고 전체 시각 수용은 **NOT TESTED**다.
  새 제품 코드·빌드·테스트 의존성 설치는 없다.

## 2026-10-20 G01 — 탭별 정렬·v4 복원 관찰 및 종료 차단

- 소스 `4bdde290`, EXE `eb89f47db33d2d12ff6abb1e6b7eb4f47c1e79adabfae3be27e8a54f9e35456d`.
  소유 fixture의 alpha.txt(10 B), beta.md(30 B), 한글 파일.txt(20 B)로 실제 UI를 조작했다.
- **기능 관찰:** 왼쪽 이름 내림차순/오른쪽 오름차순 보존, 새 폴더 탭 기본 오름차순,
  탭 왕복 및 닫기 복원, 두 WindowTab의 이름/크기 정렬 분리, v4 저장·재시작 후
  두 폴더 탭의 서로 다른 이름 정렬 복원이 모두 관찰됐다. 메뉴 체크와 행 순서도 일치했다.
- **수용 차단:** 최초 실행 exit 0, 복원 후에는 창이 닫혔지만 소유 프로세스가 60초 이상
  남았다. top-level 창/helper는 없었고 ALPC wait 대상은 csrss.exe였다. 앱/환경 원인은
  미확정이다. 소유 PID만 정리한 exit -1을 정상 종료로 취급하지 않는다.
- 관련 경계: `m23_session.cpp` 복원, `MainWindow.xaml.cpp::PrepareForClose`,
  앱/XAML/Windows 종료. 완료 조건은 동일 소유 v4 복원 후 정상 exit 0 및 설정 불변이다.
  재검증은 이 종료 경계부터 수행하고, 정렬 엔진 변경이나 전체 GUI 반복은 하지 않는다.
- **시각:** 실제 Dark/96 DPI/1906×1016 화면에서 좌우 행·탭·정렬 화살표와 내림차순
  메뉴 체크를 읽었다. 원래 구현 전/후 비교를 새로 확보한 것은 아니므로 전체 시각
  수용으로 확대하지 않는다. Light/좁은 창과 v1~v3 실제 복원도 미검증이다.
- 제품 코드 수정 없음. 기존 pywinauto GUI 스크립트는 실행하지 않았다. 사용자 설정과
  세 합성 파일 해시는 불변이며, 이번 실행만으로 G01 최종 GUI PASS를 주장하지 않는다.

## 2026-10-20 L08 — 실제 마우스 정상 표시 사용자 보고

- 사용자가 직접 열 경계에 마우스를 올려 조절 커서가 정상 표시됨을 확인했다.
  정확한 바이너리·열/패널·환경은 미기록이다. 사용자 실측 근거로 보존한다.
- 기존 자동 입력에서 arrow가 관찰된 결과는 해당 조건의 실패로 유지한다.
  실제 입력과의 차이 원인은 아직 미확정이며, 제품 전반의 미동작으로 확대하지 않는다.
- 제품 커서 수정은 중단하고 임시 이벤트 진단도 제거했다. 기존 엄격한 자동 검사와
  기능 GUI/시각 수용의 분리는 유지한다. 이 보고만으로 모든 열·드래그·종료 또는
  exact-SHA 시각 수용을 PASS로 표시하지 않는다.

## 2026-10-19 L07 세 번째 구현 — 상세 보기 이름 셀 말줄임

- `d4fff1b0` 기준. Details 이름 셀의 가로 StackPanel을 Auto(아이콘·필터 배지)
  + Star(이름) Grid로 바꿔 유한 폭에서 CharacterEllipsis가 동작하게 했다.
  이웃 유형 열과 6px 여백을 두고 전체 표시 이름 tooltip을 연결했다.
  드라이브의 진행 표시도 남은 이름 폭에 맞도록 MaxWidth/Stretch를 사용하고
  용량 설명에는 말줄임을 적용했다. 다른 보기의 렌더링·정렬 엔진은 바꾸지 않았다.
- 정식 로컬 Release exit 0. EXE SHA-256
  `6e6c9e37f258fd7f25a038216693af1fc746bcc1e5928367416611885fb3b0dd`.
  근거: ignored `logs/file-open/build-name-cell.log`, `name-cell-identity.json`.
  관련 source contracts architecture 9 + display 8 + detail controller 6 +
  registered type 3 + known-folder artwork 3 = **29 PASS**.
- **실제 GUI/시각:** 변경 전 `c7bf9663...`와 같은 네 합성 항목,
  Dark/1906×1016에서 양쪽 긴 한글 파일명이 이름 열 끝에서 `…`로 표시되고
  유형·크기 열과 겹치지 않음을 직접 확인했다. UIA 항목 이름에는 전체 이름이
  유지된다. 기존 L03 유형 설명 자체의 길이는 그대로이며 별도 개선 과제다.
- 왼쪽 기존 UIA 너비 컨트롤로 120→320→168을 설정하고 안정된 실제 화면을
  읽었다. 이름이 각 열 폭에 맞게 다시 말줄임되며 오른쪽 168은 유지됐다.
  첫 즉시 캡처는 재배치 중간 상태여서 최종 판정에서 제외했다.
  컨트롤의 공개 Max=320을 확인하기 전 360을 입력한 시도는
  E_INVALIDARG로 거절됐다. 시험 값 오류이며 제품의 드래그 상한 실패가 아니다.
  이 검증은 **UIA 값 변경**이며 실제 경계 마우스 드래그/커서 검증이 아니다.
- 별도 소유 LOCALAPPDATA의 Light 기본 설정으로 같은 바이너리·네 항목·
  1906×1016도 직접 검토했다. Light는 추가 AFTER 검토이며 Light BEFORE 비교
  수용은 아니다. Dark/Light 실행 모두 앱 exit **0**, fixture 파일 해시 불변.
  사용자·OS 테마/배율은 변경하지 않았다.
- **한계:** tooltip 연결은 소스 확인이며 실제 hover 표시는 미검증. 실제 좁은
  창, 드라이브 용량 행과 필터 배지의 새 픽셀 수용, 다른 보기 전체 GUI 및 중앙
  exact-SHA 수용을 주장하지 않는다. 기존 사용자 제외 항목은 실행하지 않았다.

우선 세 항목 중 문서 열기(L05 제한 범위), 다중 선택 보존(L06), 상세 이름
침범(L07)이 각각 독립 변경으로 수용됐다. 다음 사용성 점검/수정은 **L08 열 경계
조절 커서·hit 영역**이며, 아직 해결된 것으로 처리하지 않는다.

---

## 2026-10-19 L06 두 번째 구현 — 우클릭 선택 보존

- `33cc2e8a` 위에서 `OnFileRightTapped`가 **미선택 행을 우클릭할 때만** 기존
  선택을 교체하도록 수정했다. 이미 선택된 멤버는 전체 선택을 유지한다.
  helper의 같은 부모/최대 32항목 및 다중 항목 properties-only 실행 제한은 보존했다.
  외부 메뉴의 모든 표시 명령이 실행 가능해졌다는 뜻은 아니다.
- 정식 로컬 Release 빌드 exit 0. EXE SHA-256
  `c7bf96633a24297fd207a9dee7e843a6388238595f4989dc5e1b0cd62db0cec3`.
  ignored `logs/file-open/build-selection.log`, `selection-identity.json`에 근거 보존.
- **실제 기능 GUI:** 왼쪽 소유 네 항목 Ctrl+A→선택된 alpha.txt 우클릭→
  네 항목 하이라이트/하단 '4개 선택됨'과 다중 대상 Shell 메뉴 확인.
  Escape 후에도 네 항목 선택 유지. 이어 alpha 단일 선택→미선택 한글 파일
  우클릭은 한글 파일 한 항목만 선택됨을 확인했다. 메뉴 명령은 실행하지 않았다.
  소유 파일 해시 불변, 앱 정상 종료 exit 0.
- **시각 수용:** 같은 네 항목/Dark/1906×1016의 BEFORE/AFTER를 직접 읽었다.
  이전에는 우클릭 후 1개, 변경 후 4개 선택 표시가 남는 것이 의도된 차이다.
  패널/헤더/행 기하에 추가 변형은 없었다. 기존 긴 이름 문제와 흰 외부 메뉴는
  별도 L07/L10으로 유지한다. Light·오른쪽 패널의 새 실측 수용은 주장하지 않는다.
- 기존 `test_owned_context_menu_gui.py`에 두 소유 형제 파일을 선택한 채 직접
  우클릭하고 메뉴 취소 후에도 선택을 assert하는 회귀를 추가했다. AST 문법 검증과
  관련 source contract 3개 PASS. 로컬 pywinauto 의존성이 없어 이 **스크립트 자체는
  실행하지 않았으며**, 위 Computer Use 실제 관찰과 혼동하지 않는다.
  다음 정상 중앙 GUI 범위에서 해당 회귀를 실행할 수 있다.

다음 구현 단위는 **L07 긴 파일명과 유형 열 침범 방지**다.

---

## 2026-10-19 L05 첫 구현 — 기본 연결 문서 열기 수용

- 기준 `c6ac450408d97e3d8dd4304f64f2059f4d60036e`에 이번 변경을 적용한
  로컬 Release를 정식 `fly.bat build Release`로 빌드했다(exit 0).
  EXE SHA-256 `27a848d9e1356f7d7ec71033570532f43e669d6a4fe34bebd72eeefa96f60c3e`.
  소스/바이너리/fixture 해시는 ignored `logs/file-open/identity.json`,
  전체 빌드 출력은 `logs/file-open/build-release.log`에 있다.
- `MainWindow::OpenSelectedFolder`의 기존 폴더 탐색은 보존하고, 단일 일반
  파일에 대해서 `file_open_controller.h`의 비동기 StorageFile/Launcher 경로로
  분기했다. 행/목록 Enter와 DoubleTapped 모두 이 진입점을 사용한다.
  UI에서 동기 Shell/provider 호출이나 셸 명령 문자열 실행을 추가하지 않았다.
- 컨트롤러는 동시 요청 하나, 15초 제한, weak UI callback, route/tab/폴더
  재확인과 close cancellation을 소유한다. lookup 후 탭 문맥이 바뀌면 파일을
  열지 않고, 늦은 completion은 현재 상태를 덮어쓰지 않는다.

**기능 GUI — 제한된 로컬 수용:**

1. 합성 alpha.txt 이름을 실제 더블클릭 → 기존 메모장 창 제목이
   `alpha.txt - 메모장`으로 바뀌고 앱에 성공 안내가 나타났다.
2. `한글 파일.txt`를 실제 클릭→Enter → `한글 파일.txt - 메모장`과 성공
   안내 확인. 파일명·공백 전달을 확인했으며 편집기 본문 UIA는 읽히지 않아
   내용 표시의 독립 검증으로 확대하지 않는다. 기존 사용자 문서는 수정/닫지 않았다.
3. 실행 코드가 아닌 합성 텍스트를 담은 blocked-launch.exe → 실패 안내 확인.
   이 파일이 실행되거나 executable 지원이 수용됐다는 뜻이 아니다.
4. 이후 Nested 폴더 두 번 클릭 → 왼쪽 경로 변경/빈 목록, 오른쪽 기존
   목록 보존. 뒤로 버튼으로 원래 fixture 복귀. 실제 앱 정상 종료 exit **0**.
5. 파일 내용 해시는 전후 일치했다. 거절 확인용 합성 파일 하나만 내용과
   소유 경로를 확인해 제거했다. 기존 네 항목은 유지했다.

관련 소스 계약은 architecture 9 + shortcut 6 + external context 3 +
file-operation 14 = **32 PASS**. 로컬 실제 GUI는 Computer Use로 수동 관찰한
위 범위이며 전체 자동 GUI, Debug 또는 중앙 exact-SHA acceptance가 아니다.
중복·timeout·lookup 중 탭 이동·close 경합은 코드 검토 범위이며 결정적 지연을
만든 별도 런타임 시험은 하지 않았다. 연결 없음의 OS 선택 UI도 미검증이다.

**시각 수용 — scoped Dark/96 DPI:** 이전 `5a2fdab8...`와 새 제품에서 같은
네 항목 fixture·1906×1016·Dark 화면을 직접 비교했다. 성공/실패 상태 안내가
읽히고 주소·명령·두 패널 배치는 유지됐다. 시험 중 추가됐던 거절 파일은 최종
비교 전에 제거했으며 해당 5행 화면은 동일 fixture 비교 쌍으로 사용하지 않았다.
이름/유형 열의 기존 L07 문제는 그대로이며 이번 회귀로 분류하지 않는다.
Light/다른 창 크기 수용이나 L07 해결을 주장하지 않는다.

**지원 경계:** 이 구현은 기본 연결 앱이 있는 일반 문서의 파일시스템 경로다.
가상 Shell 파일은 안내 후 거절한다. Windows Launcher 자체가 exe/msi/일부
스크립트의 실행을 제한하므로 Explorer의 실행 파일/바로가기 전체 실행 호환은
별도 미완료 요구로 남긴다. 우회 실행을 자동 추가하지 않는다.
[Microsoft 공개 API 기준](https://learn.microsoft.com/en-us/windows/apps/develop/launch/launch-the-default-app-for-a-file).

다음 구현 단위는 **L06 다중 선택 보존 및 다중 대상 메뉴 계약**이다.
아래 L05의 기존 재현 기록은 수정 전 증거이며 이 절이 최신 문서 파일 수용이다.

---

## 2026-10-19 기본 파일 작업 사용성 추가 점검

앞선 구조·탐색 위주 점검을 보완하여 사용자 제보의 더블클릭/열 조절/긴 이름과
F2·다중 선택·우클릭을 직접 확인했다. 기준 main은
`e01f552fd6d7858f0e9e8151ff3cc890ed93de62`이며 원격/로컬 일치, 최근 10개 커밋,
최근 중앙 CI SUCCESS와 실제 scope를 재확인했다. 제품 소스가 같은 기존 로컬
Release(`5a2fdab8...8854a`)를 재사용했다. 새 빌드·제품 수정·전체 E2E는 하지 않았다.

### 재현 환경과 안전 범위

- 이전 소유 fixture에 합성 긴 이름
  `회의자료_2026년_10월_최종검토_수정사항을_반영한_매우긴파일이름_원본보존용.txt`만
  추가했다. 기존 일반/한글 txt와 Nested를 합쳐 네 항목이다.
- 격리된 자식 설정으로 정식 런처 exit 0 후 실제 앱에서 조작했다.
  Dark 상세 보기, 좌우 패널, 이름 열 기본값 168. 기존 사용자/OS 설정을 바꾸지 않았다.
- F2는 편집 진입/선택만 관찰하고 Escape로 취소했다. 우클릭 메뉴의 어떤 작업도
  실행하지 않았다. 실제 파일 저장/이름 변경/삭제/클립보드·휴지통 작업 없음.
- 기능 GUI와 실제 픽셀을 구분했다. 아래 '재현'은 해당 한정 조건에서의 관찰이며
  모든 형식·보기·테마에서 재현된다는 뜻이 아니다. 도구 geometry 실패는 새 화면의
  확인된 좌표로 재관찰해 첫 클릭 실패와 실제 제품 결과를 구분했다.

### 추가 확인 결과와 개발 요구

| ID / 우선순위·분류 | 실제 재현·근거 | 관련 파일 / 원인 경계 | 완료 조건·필요한 검증 |
| --- | --- | --- | --- |
| L05 / P1 기능 공백 재현 | alpha.txt 이름을 좌표로 실제 두 번 클릭해도 파일 선택만 되고 편집기/연결 프로그램 창이 생기지 않았다. 오류 안내도 없었다. | `app/winui/MainWindow.xaml.cpp`: DoubleTapped→OpenSelectedFolder에서 `!indexed->isFolder()`이면 즉시 return. Enter도 소스상 같은 경로지만 이번 Enter 실행은 미검증. | 폴더 탐색과 일반 파일의 기본 연결 프로그램 열기를 구별해 공개 Windows 경계로 구현. 소유 txt/한글/공백 경로, 연결 없음·실패 안내, 활성 탭 보존 및 중복 실행 방지를 실제 검증. 임의 Shell 명령 문자열 조합이나 확장자 연결 변경 금지. |
| L06 / P1 다중 선택 손실 재현 | 파일 행 클릭→Ctrl+A로 네 항목 하이라이트와 하단 '4개 선택됨' 확인→이미 선택된 alpha.txt 우클릭→한 행만 선택되고 '1개 선택됨'. 메뉴도 단일 파일 대상으로 열린다. | `app/winui/m22_transfers.cpp`: OnFileRightTapped가 `SelectedItems().Size()!=1`일 때 항상 Clear하고 clicked 하나만 선택. 이후 ShowExternalWindowsContextMenu의 단일/다중 지원 계약도 확인 필요. | 선택된 멤버 우클릭 시 선택 집합 보존. 미선택 행/빈 공간 우클릭 정책과 다중 대상 메뉴 지원을 명시하고 미지원 작업을 조용히 단일 파일로 바꾸지 않음. 1개/여러 개, 좌우 패널 및 키보드 메뉴를 소유 fixture에서 검증. |
| L07 / P1 시각 결함 재현 | 긴 한글 파일명을 추가하면 양 패널에서 이름이 유형 열과 붙어/겹쳐 보인다. 파일명의 끝·확장자와 유형의 구분이 어려우며 정상적인 셀 경계 안의 말줄임으로 보이지 않는다. | `app/winui/MainWindow.xaml.cpp`: Details 행의 가로 StackPanel nameCell과 filename TextBlock, Grid 열 제약. TextTrimming 설정만으로 실제 유한 폭 배치가 보장되는지 확인. | 아이콘+이름을 열 안에 제한하고 이웃 열 침범 없이 말줄임. 긴 한글/영문/공백·복합 확장자, 열 최소/기본/최대 너비, 두 패널·다른 보기의 실제 BEFORE/AFTER 검토. 전체 이름을 확인할 tooltip/상세 정보 경로도 제공할지 결정. |
| L08 / P2 코드 근거 있는 조절 피드백 공백·실제 hover 미검증 | 헤더 경계 드래그를 한 번 시도했으나 이름 너비 168이 유지됐다. 이 시도만으로 resize 기능 실패를 확정하지 않는다. 이번 도구에는 직접 hover API가 없고 정확한 hit/지연을 검증하지 못해 커서 전환 누락을 실측 완료로 쓰지 않는다. | `app/winui/MainWindow.xaml`의 IsHitTestVisible=False Thumb; `MainWindow.xaml.cpp`의 root pointer hit/16ms drag timer. 현재 app/winui에서 resize cursor 지정·PointerEntered/Exited 처리 발견 못함. | 실제 경계 hit에서 수평 조절 커서, hover/drag 표시와 충분한 hit 영역을 확인하고 필요한 피드백 구현. 클릭 정렬과 드래그 충돌, 좌우·각 열·범위 상한·release/capture-loss를 실제 마우스로 검증. 커서 포함 여부가 확인된 관찰 수단으로 기록. |
| L09 / P2 상호작용 개선 제안·재현 | alpha.txt 선택 후 F2를 누르면 행 안이 아니라 상단 오른쪽 180px 입력칸에 편집기가 생기고 명령 버튼 위치가 밀린다. `alpha.txt` 전체가 선택돼 확장자도 즉시 덮어쓸 수 있다. Escape 취소는 됐다. | `app/winui/FileToolbar.xaml.cpp`: BeginNameEdit의 Width(180), Focus, SelectAll; MainWindow의 이름 명령 연결 | 행 근처 편집/명확한 대상 안내 중 계약 선택, 파일은 기본 이름만 선택하고 확장자 변경은 의식적으로 수행하도록 설계. 폴더·점으로 시작하는 이름·복합 확장자·긴 이름·F2/Enter/Esc·파일 불변을 검증. 레이아웃 변경은 픽셀 QA 필수. |
| L10 / P2 시각적 차이·격리 경계 보존할 개선 후보 | Dark 앱에서 우클릭 시 흰 배경의 긴 고전 Shell 메뉴가 열린다. 다수 외부 확장 명령으로 목록이 길며 앱 내 flyout과 밀도·테마가 다르다. 첫 입력 직후에는 안 보이고 후속 캡처에서 보였다. 시간 측정 없이 지연 수치를 주장하지 않는다. | `app/winui/m22_transfers.cpp`: ShowExternalWindowsContextMenu, 격리 helper의 공개 Shell 메뉴 경계 | 직접 그린 Win11 메뉴를 무조건 요구하지 않음. 앱 소유 공통 명령과 명시적 외부 Windows 메뉴 진입을 나눌지 결정. helper 격리를 유지하고 공개 API로 가능한 테마/배치·포커스 복귀·외부 메뉴 대기 안내를 검증. 타사 확장에 대한 완전 호환 주장은 하지 않음. |

**기능 GUI:** L05/L06과 F2 진입·취소를 위 조건에서 관찰. 실제 파일 열기는
실패/미지원 결과이며 PASS로 기록하지 않는다. **시각 검토:** L07의 긴 이름 문제,
L09의 편집 위치·레이아웃 이동, L10의 Dark/흰 메뉴 차이를 실제 화면에서 확인했다.
열 조절 hover·전체 이름 tooltip은 실측 미검증이다. 기존 데이터 변경이나 픽셀 수정은 없다.

기본 파일 관리자 사용성을 기준으로 다음 구현 우선순위는 최대 세 가지:
**L05 일반 파일 열기 → L06 다중 선택 보존/메뉴 계약 → L07 긴 이름 셀 제약**.
L01~L04 및 기존 G01은 유지하되, 이 기본 동작의 공백을 화면 구조 개선보다 먼저 검토한다.

---

## 2026-10-19 로컬 후속 관찰 — 기능 일부 확인 / Dark 화면 직접 검토

이 절이 아래 최초 점검의 실행 금지 문구보다 최신인 후속 기록이다. 이번에는
제품 코드를 바꾸지 않고 실제 로컬 앱·Explorer를 관찰했으며 새 빌드는 하지 않았다.

### 기준과 관찰 조건

- 재개 시 GitHub main, 로컬 HEAD/main/origin/main 모두
  `cdbe716c6d370b2969c5c66d790ae24dcdfb73b0`. 최근 10개 커밋과 중앙 최근
  4개 CI SUCCESS를 확인했다. 최신 중앙 `39188826255`의 source PASS는
  `7ac35a06` 범위로 보존하며 이번 SHA의 GUI 인증으로 확대하지 않는다.
- 이전 로컬 Release EXE SHA-256 `5a2fdab8c1915cc2e647102bd3ced38cb9039dd2301e03e36bd195c0ae08854a`
  재확인. `git diff e3c5275d HEAD -- app/winui src/base` 차이 없음.
  기존 `build.bat` 사용자 변경 보존. 이전 빌드 성공을 재사용했다.
- 기존 프로세스는 초기 창 목록 뒤 사라져 재선택할 수 없었다. 종료 원인/코드를
  확보하지 못했으므로 정상 종료나 제품 충돌로 판정하지 않는다. 동일 바이너리를
  정식 `fly.bat run Release <fixture>`로 다시 실행했고 launcher exit 0을 확인했다.
  파이프 상속 대기를 피하기 위해 stdout/stderr는 DEVNULL을 사용했다.
- `logs/explorer-parity-local/owned-run/fixture`의 Nested, alpha.txt,
  한글 파일.txt만 사용했다. 자식 APPDATA/LOCALAPPDATA/TEMP/TMP/USERPROFILE은
  기존 소유 디렉터리로 격리했다. 파일 변경·삭제, 클립보드·휴지통·OS 설정 조작 없음.
- Windows Explorer 파일 버전 `10.0.26100.8875`, OS `10.0.26300.0`.
  두 앱은 Dark로 표시됐다. 실제 앱 캡처 1906×1016, Explorer 1125×622로
  창 크기가 다르므로 동일 기하의 픽셀 우열·간격 수치 비교로 해석하지 않는다.
  DPI를 새로 측정하거나 배율을 바꾸지 않았다. 사용자 제외 시험도 실행하지 않았다.

### 기능 GUI 결과

| 관찰 | 결과와 한계 |
| --- | --- |
| 소유 폴더 표시 | 두 패널에 Nested 및 일반/한글 파일이 표시됐다. 한글 파일명을 직접 읽었다. |
| 하위 폴더 열기 | 왼쪽 Nested를 두 번 클릭한 뒤 비동기 완료 상태를 다시 읽어 주소가 Nested, 왼쪽 목록이 비어 있고 오른쪽의 원래 세 항목이 유지됨을 확인했다. |
| 뒤로 버튼 | 버튼으로 fixture 복귀, 뒤로 비활성/앞으로 활성, 왼쪽 세 항목 복원을 확인했다. |
| Alt+왼쪽 | Nested에서 입력 후 재관찰해도 위치가 유지됐다. 같은 조건의 뒤로 버튼은 동작했다. RootShell의 현재 키 처리에도 Alt 탐색 연결을 찾지 못했다. 아래 L01의 기능 차이다. |
| Ctrl+L → Tab | 실제 화면에서 주소 문자열 선택/편집 진입, 다음 Tab에 검색 입력란의 포커스 선·캐럿을 확인했다. 전체 키보드 순회 PASS는 아니다. |
| 정렬 메뉴 | 실제 화면에서 이름 오름차순 체크와 다른 항목을 직접 읽었다. 기존 R1의 8모드 수용을 재사용하며 다시 전체 정렬 회귀를 실행하지 않았다. |
| 새 폴더 탭 | 새 탭 버튼 접근 시 도구가 `coordinate input geometry is unavailable`을 반환해 실제 추가 결과를 판정하지 않았다. G02/G06 전체 수용은 여전히 미완료다. |

### 확인된 차이·개선 제안·검증 공백

| ID / 분류 | 근거와 재현 조건 | 관련 파일 | 완료 조건 / 필요한 검증 |
| --- | --- | --- | --- |
| L01 / 확인된 기능 차이, 개선 요구 | 소유 하위 폴더에서 Alt+왼쪽이 이동하지 않지만 뒤로 버튼은 이동한다. Ctrl+L은 화면에서 동작하여 키 입력 전체 불능과 구분했다. 이미 약속한 기능의 회귀로 단정하지 않는다. | `app/winui/MainWindow.xaml.cpp`의 RootShell PreviewKeyDown 및 OnBackClicked/OnForwardClicked/OnUpClicked | Alt+왼쪽/오른쪽/위쪽의 지원 계약을 명시하고 기존 탐색 경계를 재사용. 텍스트 편집·메뉴·대화 상자·이동 중 처리와 활성 탭만 변경됨을 실제 입력으로 확인. UI 변경 시 픽셀 게이트도 적용. |
| L02 / 의도적 기존 정책과 Explorer 차이, 설계 개선 제안 | 선택 없는 Explorer는 잘라내기/복사/이름 변경/삭제 비활성, flyExplorer는 활성. `UpdateCommandAvailability`는 선택 대신 busy 여부만 검사하며 키보드/UIA 접근을 유지하려는 주석이 있다. 무선택 실제 파일 작업은 수행하지 않았다. | `app/winui/MainWindow.xaml.cpp`의 UpdateCommandAvailability, `app/winui/FileToolbar.xaml` | 선택 기반 비활성화 또는 유효한 안내 정책을 결정. 변경한다면 키보드/UIA 선택 경로가 막히지 않게 유지하고 선택 없음/하나/여러 개·busy·패널 전환을 검증. 안전성 결함이나 데이터 손실로 분류하지 않음. |
| L03 / 시각·문구 개선 제안 | 동일 txt 파일에서 Explorer는 '텍스트 문서', 앱은 'txt 파일 (Windows 유형: 텍스트 문서)'로 표시. 앱의 기본 유형 열에서 설명이 잘린다. 전체 창은 더 넓어도 패널별 열 폭은 고정이므로 창 전체 크기만으로 공간 충분을 판단하지 않음. | `app/winui/file_detail_controller.cpp`의 typeLabel 조합, 상세 열 표시 경계 | 목록에는 등록된 Windows 유형을 우선해 간결하게 표시하고 미등록 형식 fallback·상세 설명 위치를 정함. 일반/미등록/긴 형식명, 두 패널·좁은 창·정렬에 영향 없는지 검사. 실제 BEFORE/AFTER 캡처 검토 필수. |
| L04 / 도구·검증 공백 | 도구 focused_element는 FileNameBox로 유지됐지만 실제 화면의 Ctrl+L/Tab 포커스는 주소/검색으로 이동했다. 화면 미검토 시 이 값만으로 제품 포커스 결함을 판정할 수 없다. | 기존 `tests/winui/test_owned_accessibility_layout_gui.py`, 이번 Computer Use 관찰 경계 | 새 전용 시험은 실제 focused control/PID·키 전달·모델·픽셀을 교차 확인. 시작부터 모든 주요 영역을 왕복하는 경로와 두 수준 탭은 별도 소유 fixture에서 수용. |

### 시각 검토 결과 (기능 GUI와 별도)

실제 Dark 앱의 기본 목록, 빈 하위 폴더, 정렬 flyout, 주소 편집·검색 포커스와
Dark Explorer의 동일 fixture 화면을 직접 읽었다. 기본 헤더/주소/명령 계층,
두 패널 구분, 한글 표시와 정렬 체크는 읽을 수 있었다. L03의 유형 문구 잘림은
개선 후보로 남겼다. 창 크기가 달라 정량적인 동일 조건 비교는 **미검증**이다.
Light, 메뉴 전체·오류 대화 상자·전체 키보드 경로를 새로 수용하지 않는다.
제품 변경이 없으므로 변경 전후 시각 수용을 주장하지 않는다.

한 Explorer 캡처는 다른 창에 가려져 비교 근거에서 제외했다. 대상 창을 다시
선택·활성화한 올바른 Explorer 화면만 검토했다. 원시 화면·UIA 로그는 Git에
저장하지 않았다. 이전 승인 서비스 차단은 이번에 해소됐지만 초기 창 소실,
포커스 필드 불일치와 geometry 오류는 서로 별개의 미확정 도구/환경 한계다.

다음 최대 세 항목은 L01 탐색 단축키, L02 명령 활성 정책 결정, L03 유형 문구
간결화다. 기존 G01 정렬 소유권의 설계 결정 과제는 그대로 유지한다.

---

점검일: 2026-10-19 (KST). 첨부 명세의 NAV/CMD/LIST/SORT/GROUP/TAB/KEY/VIS
39개 항목을 대상으로 한 소스·기존 증거 검토 및 제한적 실제 Windows 관찰이다.
제품 코드 수정, 새 빌드, 전체 GUI/E2E, 커밋·푸시·PR 생성은 수행하지 않는다.

위 범위와 아래 39개 표는 최초 점검 당시의 기록이다. 사용자가 이후 승인한
R1 구현·검증은 문서 끝의 후속 작업 절에서 별도로 기록한다.

## 기준과 증거 수준

- GitHub에서 확인한 최신 `flyExplorer/main` 및 로컬 HEAD:
  `3dd17f614caaf7a41b5d90a4f345e5a1e1ff61a9`.
  이전 main `ba3a16cc` 이후 변경은 AGENTS.md 작업 정책뿐이다.
- 기존 사용자 변경: 루트 `build.bat`의 EOF 줄바꿈 제거. 보존하고 실행하지 않았다.
- 중앙 제어 저장소 main: `454a1e4a16b0d2689eaff19f8de77435ab39c716`.
  활성 작업 없음, Windows VM runner online/idle, 공용·windows-vm 요청 슬롯 idle을
  확인하고 기존 `remote-shell.yml`의 수동 dispatch를 사용했다. 요청 파일은 수정하지 않았다.
- 최신 중앙 검증 [39105558139](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105558139):
  `desktop-a`, **source** 범위, `ba3a16cc81d55360aa20f2bdba16d3a443e76c4c` PASS.
  현재 HEAD의 새 Release/GUI PASS로 표현하지 않는다. 현재 HEAD에 status가 없다는 사실도
  제품 실패를 뜻하지 않는다.
- 재사용 Release 소스: `0d10b1b600c854a2cfbb3b425bf7b2d616e9af77`.
  EXE SHA-256: `300eeb16f86bba4dd47f92bd36ee073116f4bce371e4d3f6da54e5a86589db17`.
  VM의 기존 테스트 소유 체크아웃에서 origin·HEAD·clean 상태·EXE 해시·동봉 helper를 확인했다.
  `git diff 0d10b1b6 HEAD -- app/winui src/base`는 차이가 없다.
  따라서 제품 소스의 동일성에 근거해 기존 바이너리를 재사용한다. 현재 HEAD를 새로 빌드했다는
  주장이나 전체 런타임 파일의 재검증 주장은 아니다.
- VM의 `C:\dev\flyExplorer`는 깨끗하지만 `387efa62`의 오래된 체크아웃이었다.
  최신 제품 기준으로 사용하거나 갱신하지 않았다.
- 원본 첨부 문서는 점검 기준이다. 코드 존재는 기능 GUI PASS가 아니며,
  UIA 이름/좌표는 시각적 PASS나 Narrator 발화 PASS가 아니다.

**기존 부분 증거**는 특정 조건에 대한 과거 수용을 보존한다는 뜻이다.
해당 행의 모든 완료 조건이나 모든 DPI·테마·입력 조합이 통과했다는 뜻은 아니다.
과거 오류가 해결된 항목을 새 결함으로 다시 열지 않는다.

## 비교 기준과 의도적인 차이

Windows 11 탐색기는 탐색·명령·키보드·정보 계층의 기준이다. 듀얼 패널,
WindowTab 아래의 PaneTab, 제한된 Shell/provider 지원과 더 조밀한 아이콘 배치는
제품의 의도된 차이이며 결함이 아니다. 공개 WinUI/Windows API만 사용한다.

이번에 Microsoft 공식 문서에서 확인한 기준:

- [Keyboard interactions](https://learn.microsoft.com/en-us/windows/apps/develop/input/keyboard-interactions):
  예측 가능한 Tab 순서, 방향키의 컨트롤 내부 이동, 보이는 포커스,
  F6의 주요 영역 순회. flyExplorer F6의 반대 패널 이동은 의도적 차이로 기록한다.
- [Windows keyboard shortcuts](https://support.microsoft.com/en-us/accessibility/windows/keyboard-shortcuts-in-windows):
  탐색기 단축키 비교 자료. flyExplorer의 기본 주소 입력은 Ctrl+L,
  검색은 Ctrl+F이며 제한된 사용자 지정이 가능하다. Alt+D 미구현만으로 결함 판정하지 않는다.
- [Accessible text requirements](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessible-text-requirements):
  텍스트 대비·배율·테마 검토 기준. 실제 픽셀 측정 없이 대비 수치를 통과했다고 쓰지 않는다.

기존 Explorer 비교 캡처는 `WINUI_EXPLORER_VISUAL_BENCHMARK_20261001.md`의
972×720 / 96 DPI / Dark 기준이다. 이번 앱 관찰과 같은 조건으로 새 Explorer 창을
촬영한 비교 쌍은 없다. 따라서 새로운 Explorer 대비 픽셀 우열을 판정하지 않는다.
첨부 명세의 Release Preview 신규 기능은 이번 작업의 요구사항으로 승격하지 않았다.

## 재사용한 수용과 코드 경계

| 근거 ID | 수용 범위와 한계 |
| --- | --- |
| E1 | `CURRENT_STATUS.md`의 2026-10-18 F04 narrow TreeView 최종 수용: 정확한 `0d10b1b6` Release, focused F04 및 전체 GUI exit 0, 960×519/96 DPI Light·Dark 원본 PNG 검토. 이전 root 경로 잘림은 수정된 상태다. 고배율·HC·Narrator는 포함하지 않는다. |
| E2 | F05 실제 키보드 [39105142373](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105142373), [39105289485](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39105289485): 네 그룹 모드, 접기·펼치기, 탭 상태 복원 PASS. UIA로 최초 컨트롤 포커스를 설정했으므로 시작부터 독립적인 키보드 순회를 인증하지 않는다. |
| E3 | M26 [39103545858](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39103545858): 16개 UIA 이름, 960×634·1100×680·1240×710 기하 및 실제 Tab 입력, 96 DPI/HC OFF. 소스의 루프는 주소에 보조 포커스를 준 뒤 Tab 네 번을 보낼 뿐 각 단계 도달 컨트롤을 assert하지 않는다. 전체 키보드 접근성·픽셀 PASS로 확대하지 않는다. |
| E4 | F01: 숨김/확장자/선택 확인란/간격, pane 상태와 private session 수용 기록. `38353716100`은 통합 main 중앙 GUI PASS. `38359677323`의 내부 restart marker가 PASS여도 외부 Actions FAILURE는 그대로 보존한다. |
| E5 | F02/F03: Details 좁은 창 스크롤·포커스 원본 PNG 검토, bounded Preview 실제 마우스·키보드·선택 전환 수용. 미지원 포맷 placeholder는 의도된 제한이다. 세부 범위는 CURRENT_STATUS의 2026-10-14/15 최신 항목을 따른다. |
| E6 | F06: 따옴표 경로, pane-local 중간 클릭, 실패 UNC 이후 committed path 보존과 경합 수용. `38491527835`의 940/800px, 96 DPI Light·Dark 후보 표시 원본 PNG 검토. 실패 UNC는 정상 SMB 공유 연결 수용이 아니다. |
| E7 | 기존 파일 작업·창 탭·다중 선택·아이콘/썸네일 수용 및 2026-10-01/03 Explorer 비교. `CURRENT_STATUS.md`의 각 SHA/조건을 넘어서 재인증하지 않는다. |
| E8 | 96 DPI scoped 필터 HC 및 실제 한글 두벌식 조합·필터 저장 수용. 주소·검색·이름 변경 IME나 F04/F05 HC 전체 수용을 뜻하지 않는다. |

소스 검토에서 확인한 연결:

- `MainWindow.xaml.cpp`의 `RootShell().PreviewKeyDown`: Ctrl+T/W/Tab은 WindowTab,
  F5는 활성 pane/tab refresh, F6는 split 상태에서 반대 pane으로 이동한다.
  `NewTabButton`/`CloseTabButton`의 폴더 탭 동작과 적용 범위가 다르다.
- `window_workspace_controller.*`, `window_tab_state.h`: WindowTab마다 workspace를 소유한다.
  `SessionCoordinator`와 `src/base/ui_session.*`가 세션 수명·직렬화를 분리한다.
- `ShellNavigationController`: supervisor·watcher 경계, route/request와 활성 탭 검증,
  forget/suspend/shutdown이 존재한다. UI에서 동기 provider 작업을 새로 실행하지 않았다.
- `file_group_tab_cache.h`: route/tab/side 키의 live cache와 complete metadata 조건을 둔다.
  live 탭 복원과 앱 재시작 영속성은 서로 다른 요구사항이다.
- `MainWindow::OnAddressKeyDown`: Enter 뒤에는 새 요청 경로가 아닌 committed 위치를 표시한다.
  `OnQuickSearchKeyDown`, `FileToolbar::OnNameKeyDown`과 함께 IME Enter 경계는 별도 실제 검증이 필요하다.

## 이번 실제 Windows 관찰

새 관찰은 기존 바이너리, 별도 APPDATA/LOCALAPPDATA/TEMP/TMP와 합성 파일만 사용한다.
실제 사용자 설정은 읽기 전용 hash로 전후 비교하며 OS 설정·clipboard·Recycle을 조작하지 않는다.

키보드 관찰 [39182554102](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182554102):

- 대화형 session 1, Windows version 문자열 `10.0.26300`, 실제 앱 96 DPI, HC OFF.
  일반 배포 채널 여부나 실제 고배율 시험 가능성을 이 버전 문자열만으로 확정하지 않는다.
- 앱 창 활성화 보조 후 **컨트롤 강제 포커스 없이** startup AddButton에서 Tab 32회.
  매 입력 후 소유 PID와 실제 focused element의 ID/name/type/rectangle을 기록했다.
  CreateFolder → Cut/Copy/Paste → Rename/Recycle → 반대편 Copy/Move → Sort/View/More →
  Up/Address/Search → 폴더 탭 버튼 → 보조 패널 버튼 → sidebar까지 도달했다.
  버튼에는 Tab으로 포커스만 주었고 파일 명령은 실행하지 않았다.
- Ctrl+L 후 `AddressBox`, F6 후 오른쪽 파일 목록의 test-owned `Nested` ListItem을 관찰했다.
  이 제한된 경로는 관찰 완료다. Shift+Tab 역순·모든 pane/tab/dialog와 시작부터 무보조
  window activation은 검증하지 않았으므로 KEY-01 전체 PASS로 확대하지 않는다.
- 기하 순서에서 command row 뒤에 그보다 위의 address row로 포커스가 이동했다.
  실행 불가능이나 함정은 이 부분 관찰에서 확인하지 않았다. 상하 시각 순서와의 일치성은
  R3의 검토 후보이며 즉시 제품 결함으로 분류하지 않는다.
- 이후 잘못된 `move_window` 호출로 화면 캡처 전에 harness가 중단됐다.
  **외부 Actions는 FAILURE**다. 정상 앱 종료 0, 사용자 설정 hash/HC 불변,
  test-owned fixture 제거 및 task/process 잔류 0은 별도로 확인했다.
  위 키보드 부분 증거는 `logs/ui-ux-audit/keyboard-observations.json`에 보존했다.

기능 GUI 전체 acceptance와 이 부분 관찰, 실제 화면 픽셀 검토는 각각 별도로 판정한다.

화면·정렬 메뉴 후속 관찰
[39182719028](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182719028)는
**SUCCESS**다. 앞서 관찰한 32회 Tab·Ctrl+L·F6는 재실행하지 않았다.

- 같은 binary/source, session 1, 96 DPI, HC OFF, 기본 System 테마가 실제 Dark로 표시됐다.
  각각 960×634와 800×634 창, 합성 `source/Nested`, alpha.txt/beta.md/긴 한글 txt,
  좌우 같은 폴더의 Details/이름 오름차순 상태를 캡처했다.
- 960px: 두 pane의 이름·유형·크기 열과 header 화살표, 한글 파일명, footer가 읽힌다.
  긴 유형명은 말줄임으로 처리된다. 현재 상태에서 material overlap/clipping은 관찰하지 않았다.
- 800px: 유형 열을 숨기고 이름·크기를 남기는 반응형 배치다. 한글 이름과 양 pane 목록이
  읽히고 command/address 영역의 뚜렷한 겹침은 관찰하지 않았다. 폭이 더 작은 상태,
  전체 overflow 명령 도달성, 모든 hover/disabled/focus 상태는 이 이미지로 수용하지 않는다.
- 상단 작업 공간 탭과 각 pane 폴더 탭은 별도 행에 있고, 활성 pane 상단선과 상단 AddButton
  focus 테두리는 구분된다. 구조가 다르다는 이유로 결함 판정하지 않았다.
- 이후 UIA Invoke로 Sort 메뉴를 열어 이름 내림차순 항목을 실행하고 메뉴를 다시 열었다.
  정렬 항목 8개 모두 Toggle/SelectionItem 패턴이 unsupported였다.
  소스의 일반 MenuFlyoutItem과 일치한다. 모든 MenuItem을 process 범위로 열거한 결과에는
  정렬과 무관한 시스템 메뉴 항목도 있으므로 정렬 8개와 구분한다.
  이 실행은 실제 파일 순서나 메뉴 픽셀의 checkmark를 별도로 assert/촬영하지 않았다.
  UIA 상태 부재와 소스 근거에 기반한 R1 개선 제안이며 정렬 알고리즘 실패가 아니다.
- 앱 정상 종료 0, 사용자 app/legacy 설정 hash 및 HC 불변, synthetic fixture 제거,
  임시 Scheduled Task 0개와 제품 프로세스 0개를 확인했다.
  VM 원본 evidence는 `logs/ui-ux-audit-d8b7c4e4216c494396be1a357b3d5552/`에 보존했다.
  원격·로컬 이미지 해시가 일치하며 로컬 파일은 ignored `logs/ui-ux-audit/`에 있다.

| 로컬 화면 증거 | SHA-256 |
| --- | --- |
| `logs/ui-ux-audit/window-960.png` | `d6505c6b805d38f7212c1496c084ad032e652ca96bc95a6359cdc9eb2a083ec4` |
| `logs/ui-ux-audit/window-800.png` | `a111e205f7c0df479927e898b1f77e81f12fe850acc92c7776632795fc0dcb77` |

**기능 GUI:** 기존 기능 acceptance를 재사용하고 위 제한적 동작만 새로 관찰했다.
전체 GUI 재실행은 NOT TESTED. 키보드 부분 관찰의 외부 실패를 PASS로 바꾸지 않는다.
**시각적 검토:** 위 2개 실제 96 DPI Dark PNG의 기본 화면은 scoped PASS.
이번 Light·HC·고배율·menu/focus 전체 상태는 NOT TESTED 또는 환경 차단.
제품 화면을 변경하지 않았으므로 이번 BEFORE/AFTER 비교는 N/A이며,
기존 E1/E5/E6의 실제 비교 수용은 그 조건에 한해 보존한다.

최초 점검에서 새로 확정한 제품 동작 결함은 **0개**였다. 이는 미검증 조건에 결함이 없다는 뜻이 아니다.
구현 후보는 R1/R2의 2개, 우선 검증 후보는 R3의 1개이며 아래 상세 기준을 따른다.

## 39개 항목별 검토 결과

| ID | 판정 / 관찰 근거 | 남은 완료 조건·필요 검증 |
| --- | --- | --- |
| NAV-01 | 기존 부분 증거 E1/E7; 활성 pane/tab controller 경계 확인 | 각 입력 수단의 반대 pane history 불변 매트릭스는 새로 실행하지 않음 |
| NAV-02 | 기존 부분 증거 E6, breadcrumb/event 연결 | 모든 긴 경로·폭의 실제 표시·클릭 결과 |
| NAV-03 | 기존 부분 증거 E6, committed path 처리 소스 확인 | 한글·공백·따옴표 입력의 현재 IME 조합 포함 전 조합 |
| NAV-04 | 기존 부분 증거 E6 | 후보 전체 키보드 취소·포커스 조합 및 다른 DPI |
| NAV-05 | 기존 부분 증거 E1 | 현재 폴더의 제한된 로컬 트리이며 전체 Explorer 드라이브 트리가 아님; provider 확장은 별도 요구 |
| CMD-01 | 기존 부분 증거 E7 | 이번 clipboard/Recycle은 사용자 제외 조건으로 NOT TESTED; 새 안전성 인증 아님 |
| CMD-02 | 기존 부분 증거 E3, FileToolbar의 label/name/tooltip 확인 | 모든 command 상태·음성 안내·색상 대비 |
| CMD-03 | 기존 부분 증거 E3 | 좁은 창의 실제 command overflow 접근성과 전체 핵심 명령 가시성 |
| CMD-04 | 기존 부분 증거 E7 | 취소·실패의 전체 파일 결과 매트릭스; 이번 파일 전송은 실행하지 않음 |
| CMD-05 | 기존 부분 증거 E7, isolated allowlist 설계 | 선택·미지원 provider별 메뉴 동작 전체 |
| LIST-01 | 기존 부분 증거 E7, 다섯 보기 handler 확인 | 모든 보기 전환의 selection/focus 조합 |
| LIST-02 | 기존 부분 증거 E4, 메뉴 check-state 동기화 소스 | 다른 DPI·전체 session 조합으로 확대하지 않음 |
| LIST-03 | 기존 부분 증거 E5/E7, 열 배치 코드 | 모든 열 크기·정렬·탭 복원 조합 |
| LIST-04 | 기존 부분 증거 E5/E7 | Ctrl/Shift/확인란/보기 조합 전체 선택 불변 |
| LIST-05 | 기존 부분 증거 E7 | 느린 provider·실패·다른 DPI의 실제 fallback 픽셀 |
| LIST-06 | 기존 부분 증거 E5 | 빠른 연속 선택·닫기 경합의 전체 포맷/provider 조합 |
| SORT-01 | 기존 부분 증거 E7; 8개 sort index와 pane 갱신 연결 | 부분 목록·metadata 조건을 포함한 전체 실제 정렬 결과 |
| SORT-02 | 개선 후보 확인 / source+새 UIA 관찰; 메뉴 8개에 선택·체크 패턴 없음, details header에는 화살표 표시 | 실제 정렬 결과·메뉴 픽셀 전체는 미검증; R1 |
| GROUP-01 | 기존 부분 증거 E2 및 F05 기존 모드 수용 | 전체 폴더/provider가 아니라 complete metadata 조건 범위 |
| GROUP-02 | 기존 부분 증거 E2 | 전체 키보드 시작 경로·Narrator 발화 |
| GROUP-03 | 기존 부분 증거 F05 contract/native와 complete-model 소스 | 현재 source 검토를 신규 incomplete-provider 실제 실행 PASS로 확대하지 않음 |
| GROUP-04 | 기존 부분 증거 E2와 route/tab cache | live 탭 수용이며 재시작 group 영속성 요구를 추가하지 않음 |
| TAB-01 | 기존 부분 증거 E1/E7, workspace 소유 코드 | 모든 복원·오류 경합의 새 시험은 아님 |
| TAB-02 | 기존 부분 증거 E2/E4/E7 | 보기·그룹·history 전체 조합 |
| TAB-03 | 기존 부분 증거 E1/E2/E7 | 모든 pointer/key/menu에서 명령 대상과 focus 일치 |
| TAB-04 | 기존 부분 증거 E2/E7, WindowTab 단축키 연결 | 창 탭/폴더 탭의 사용자 구분성; R2 |
| TAB-05 | 기존 부분 증거 E3/E7 | 최소 지원 폭의 실제 사용 가능성과 숨긴 pane 복원 전체 |
| TAB-06 | 기존 부분 증거 E7 | 이번 전송·drag는 미실행; clipboard·Recycle 전역 효과 제외 |
| KEY-01 | 확인 필요 / 새 부분 관찰; 32회 Tab별 실제 focus와 Ctrl+L/F6 기록, 전체 도달·복귀는 미확인 | 처음부터 키보드만으로 각 핵심 영역 도달·복귀 assert; R3 |
| KEY-02 | 기존 부분 증거 E7, Ctrl+L/F·F5/F6·WindowTab 소스 | Explorer와 의도된 차이 안내, 사용자 지정 조합 전체 |
| KEY-03 | 기존 부분 증거 E1/E8의 제한된 96 DPI 상태 | 모든 영역·테마의 selection/focus 실제 픽셀 |
| KEY-04 | 환경 차단 / 기존 부분 증거 E3 | UIA는 발화 증거가 아님; Narrator 설정 변경 없이 이번 실제 음성 확인 불가 |
| KEY-05 | 확인 필요; E8은 필터 저장만 수용 | 주소·빠른 검색·이름 변경의 조합 중 Enter/Esc, 문자 보존 |
| KEY-06 | 확인 필요; 탭별 소유 소스·기존 경로만 확인 | 전환·dialog 닫기 이후 포커스 도달값의 실제 연속 관찰 |
| VIS-01 | 기존 부분 증거 E1/E5/E6 | 앱 전체 모든 surface/theme contrast 수용 아님 |
| VIS-02 | 환경 차단 / 기존 부분 증거 E8 | F04/F05 포함 실제 HC 화면; 이번 OS 설정 변경 금지 |
| VIS-03 | 환경 차단 | 실제 125/150/200% 데스크톱; 모사 resize는 대체 증거가 아님 |
| VIS-04 | 기존 부분 증거 E1/E3/E5/E6 + 새 960/800px Dark 기본 화면 scoped PASS | 각 panel/확장 UI와 최소 폭의 전체 새 화면 조합 |
| VIS-05 | 기존 부분 증거 E1/E5/E6 | 모든 hover/disabled/long-name 상태와 정량 대비는 미검증 |

39개 항목의 주요 분류는 기존 부분 증거 32개, 확인 필요 3개,
개선 후보 확인 1개, 환경 차단 3개다. VIS-04 등에는 새 부분 관찰을 추가했다.
39개 전체 완료 조건에 대한 신규 PASS/FAIL 집계가 아니다.
환경 차단과 검증 부재는 재현된 P0 결함이나 자동 배포 차단으로 바꾸지 않는다.

## 개선 요구사항과 검증 공백

### R1 — 현재 정렬 모드의 메뉴 표시 (SORT-02, 개선 제안, P1)

- 근거: `app/winui/FileToolbar.xaml`의 Sort 메뉴는 일반 `MenuFlyoutItem` 8개다.
  `FileToolbar::SetSortIndex/ChooseSort`는 숨긴 `SortPicker.SelectedIndex`만 갱신한다.
  보기·그룹 메뉴의 `IsChecked` 동기화와 차이가 있다. details header의 정렬 화살표는
  별도 표시이므로 앱 어디에도 정렬 표시가 없다고 주장하지 않는다.
  새 실제 UIA 관찰에서도 이름 내림차순 실행 후 8개 정렬 항목의 Toggle/SelectionItem
  패턴이 모두 unsupported였다. 이 범위는 확인했으며 메뉴 픽셀은 별도 캡처하지 않았다.
- 재현 조건: 테스트 폴더에서 이름 내림차순 선택 후 Sort 메뉴를 다시 연다.
  현재 선택 표시/UIA 선택 상태, 실제 파일 순서, details header를 함께 관찰한다.
- 기대 동작: 활성 pane/tab의 기준과 방향을 메뉴에서 명확히 식별한다.
- 관련 파일: `FileToolbar.xaml`, `FileToolbar.xaml.cpp/.h`,
  `MainWindow.xaml.cpp`의 `SetSortIndex` 호출·`UpdateSortPresentation`.
- 최소 구현 후보: 기존 sort index를 메뉴 check-state에 투영한다. 새 정렬 엔진이나
  전역 설정을 만들지 않는다. 실제 구현은 이번 범위가 아니다.
- 완료 조건: 8개 모드 중 올바른 하나만 표시되고 pane/tab 전환 후 갱신되며
  실제 순서·header와 일치한다. 키보드 선택·UIA 상태, 96 DPI Light/Dark 및 좁은 창
  BEFORE/AFTER 시각 검토가 필요하다.

### R2 — 두 수준 탭의 명령 범위 안내 (TAB-04/KEY-02, 개선 제안, P2)

- 근거: Ctrl+T/W/Tab은 WindowTab을 조작하지만 주소 옆 `NewTabButton`의 tooltip은
  단순 “새 탭”, Close는 “탭 닫기”다. 상단 WindowTabs의 접근성 이름은 “창 작업 공간 탭”이다.
  명령 범위가 다르다는 것은 소스로 확인했으나 실제 사용자의 혼동이나 잘못된 조작은 미확인이다.
- 재현 조건: 두 WindowTab에 좌우 PaneTab을 각각 두 개 열고 버튼과 단축키의 대상 비교.
- 기대 동작: 사용자가 “창 작업 공간 탭”과 “현재 패널의 폴더 탭”을 구분한다.
- 관련 파일: `MainWindow.xaml`, `ShellHeader.xaml`, `MainWindow.xaml.cpp`의
  `PreviewKeyDown`, `OnNewTabClicked/OnCloseTabClicked`.
- 최소 구현 후보: tooltip·접근성 이름·도움말의 적용 범위 명시. 구조/단축키 재설계는 하지 않는다.
- 완료 조건: 두 수준의 생성·전환·닫기 대상이 안내와 일치하고 실제 키보드/UIA로 확인된다.
  문구가 화면 픽셀에 영향을 주면 기존 시각적 QA 규칙을 적용한다.

### R3 — 키보드 도달·복귀 증거 완결 (KEY-01/06, 검증 공백, P1)

- 근거: E3의 네 번 Tab 입력은 각 focus target assertion이 없고 E2는 보조 포커스로 시작한다.
  기존 F05 기능 PASS를 취소하지 않으면서 전체 앱의 독립적인 키보드 경로를 따로 검증해야 한다.
  이번 32회 Tab 관찰은 단계별 실제 값을 보완했지만 전체 영역 왕복을 assertion하지는 않았다.
- 재현 조건: 깨끗한 private fixture로 앱 활성화 후 컨트롤 강제 포커스 없이 시작하여
  Tab/Shift+Tab, 방향키와 정의된 shortcut으로 toolbar/address/list/양 pane/tab에 도달하고 복귀한다.
- 관련 파일: `tests/winui/test_owned_accessibility_layout_gui.py`,
  `tests/winui/test_v7_window_tabs_gui.py` 등 기존 탭 fixture, `MainWindow.xaml[.cpp]`.
- 기대 동작·완료 조건: 입력마다 실제 focused element의 이름/역할·소유 PID·가시 영역을 기록하고
  목표 영역 도달·함정 없음·복귀를 assert한다. 실제 focus 픽셀과 기능 assertion은 별도 판정한다.
  정해진 이동이 막힌 경우에만 제품 결함으로 분류한다. 테스트 보완부터 판단한다.

추가 공백: KEY-05의 주소/검색/이름 변경 IME 조합, 실제 고배율·HC·Narrator,
승인된 정상 SMB provider, 대량 폴더/전체 view 조합. 현재 제외된 전역 상태를 바꾸거나
이들을 새 기능 개발로 자동 승격하지 않는다. 준비된 별도 환경에서
`manual_accessibility_matrix.py`를 사용하는 후속 작업이 필요하다.

## 실행 이력·실패 분류

- [39182117625](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182117625)
  FAILED: SYSTEM과 제어 checkout 소유자 차이로 `git rev-parse`가 dubious ownership을 거부했다.
  제품 실행 이전의 제어 환경/preflight 실패다. 전역 safe.directory나 ACL을 변경하지 않았다.
- [39182217485](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182217485)
  SUCCESS: 확인한 정확한 경로에만 `git -c safe.directory=<path>`를 적용해 inventory 완료.
  대화형 Explorer session 1개, Narrator 프로세스 0개. SYSTEM 하드웨어 inventory만으로
  실제 DPI/HC/audio endpoint를 판정하지 않았다.
- [39182437118](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182437118)
  FAILED: 새 관찰 harness가 UIAWrapper에 `child_window`를 호출한 AttributeError.
  현재 binary의 UI 결함 증거가 아니다. actual input/screenshot 전 중단했으며,
  테스트 fixture 제거, 실제 설정 hash/HC 불변, task/process 잔류 0을 확인했다.
  기존 테스트 방식인 `Desktop.window(handle=...)` WindowSpecification으로 수정한 후속 run만 허용했다.
- [39182554102](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182554102)
  FAILED: 키보드 부분 관찰 후 UIA backend가 지원하지 않는 `move_window` 호출로 중단됐다.
  제품 실패가 아니다. 실제 keyboard 결과를 보존하고 반복하지 않았다.
  기존 checked-in fixture가 사용하는 Win32 `SetWindowPos`로 크기 조절 경계만 수정하여
  화면·정렬 메뉴 관찰을 분리했다.
- [39182719028](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39182719028)
  SUCCESS: 새 build 없이 96-DPI 화면 두 장과 정렬 메뉴 UIA를 관찰하고 정상 종료·설정 보존·정리를
  확인했다. 앞의 실패 run들을 소급하여 PASS로 바꾸지 않는다.

## 최초 점검의 변경·검증·종료 범위

- 영속 문서 변경은 이 파일뿐이다. 원격 관찰용 Python/PowerShell 및 로그·캡처는
  ignored `logs/ui-ux-audit/`와 VM의 고유 test-owned evidence 아래에 둔다.
- 제품 C++/XAML, 프로젝트 템플릿, 사용자 `build.bat`, `.agent-policy`는 수정하지 않는다.
- 새 전체 빌드·중앙 source/Release/gui·E2E·패키징은 실행하지 않는다.
  문서 diff 검토와 `git diff --check`만 문서 검증으로 수행한다.
- 후속 구현 추천 순서: **R1 정렬 상태 표시 → R3 키보드 증거 완결 → R2 탭 범위 안내**.
  재현된 파일 안전 결함이 새로 확인되면 그 결함을 먼저 처리한다.
- 미검증 환경은 이 문서에 인계한다. 별도의 중복 HANDOFF나 자동 후속 실행은 만들지 않는다.

## 관련 현재 문서

`CURRENT_STATUS.md`, `ARCHITECTURE.md`, `AGENT_EFFICIENCY.md`, `ERROR_HISTORY.md`,
`UI_UX_DESIGN_GUIDE.md`, `WIN11_EXPLORER_UI_REFERENCE.md`, `UI_VISUAL_RETEST.md`,
`F04_NAVIGATION_TREE.md`, `F05_GROUP_BY.md`.
`WIN11_EXPLORER_FEATURE_BENCHMARK_20261012.md`는 당시 로드맵이다.
그 문서의 F01~F06 “미구현” 비교는 이후 수용 기록으로 대체되었으며 새 결함이 아니다.

## R1 후속 구현 — 현재 정렬 모드의 메뉴 표시

사용자 승인 범위는 R1 구현과 필요한 검증 후 main 푸시다. R2/R3 구현은 포함하지 않는다.

- `FileToolbar.xaml`: 기존 8개 정렬 명령을 이름 있는 ToggleMenuFlyoutItem으로 바꾸고
  초기 이름 오름차순을 체크한다. 명령·레이블·정렬 엔진은 유지한다.
- `FileToolbar.xaml.cpp`: 기존 `SetSortIndex`에서 메뉴 체크 상태를 투영한다.
  `ChooseSort`와 숨긴 ComboBox의 기존 이벤트 경로도 같은 함수를 거치며,
  XAML 초기화 중 callback이 없는 경우의 기존 보호 조건을 유지한다.
- 기존 패널·탭 활성화가 호출하는 `SetSortIndex`를 사용한다. MainWindow에 새 상태나
  controller를 추가하지 않는다.
- `test_sort_menu_gui.py`: 실제 Space/Home/Down/Enter 입력, 8개 메뉴의 상호 배타적인
  Toggle 상태, 이름 정렬의 실제 파일 순서, 좌우 pane·WindowTab의 독립 상태를 검증한다.
  PaneTab 전환은 현재 실제 목록과 메뉴 표시가 일치하는지 확인한다.
  읽을 수 없는 숨김 ComboBox의 UIA selected_index 값은 판정 근거로 사용하지 않는다.
  테스트는 private 환경과 합성 파일을 사용하며, app/legacy 사용자 설정을 전후 검증한다.
- BEFORE: [39183800467](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39183800467)
  SUCCESS, 기존 EXE `300eeb16…`, 96 DPI, Light/Dark, 960/800×634, 이름 내림차순 메뉴.
  네 PNG와 geometry/hash metadata는 ignored `logs/r1-sort/`에 보존했다.
- 최종 제품 후보: main `3dd17f61` 위의 두 제품 파일 변경. XAML SHA-256
  `dc1a6671b3424640fdbd934e9219a6d893ce3a6c763a85a56ab808b66bed2f69`, C++ SHA-256
  `86fc054bbc7827e01a5d571ac5874092c6f0171537c3e66b99313fcebce79bf0`.
  새 test-owned checkout `s-8bd610da`에서 구조 4/4, core 60/60, canonical
  `build.bat Release` PASS. EXE SHA-256
  `5a90c5deaa76f4e93f6a6a870a1defc20beb11456d2bcdf75537b76fc2cab751`.
  이후 수정은 GUI harness뿐이며 이 제품 binary를 재사용한다.
- **기능 GUI: PASS (R1 범위).**
  [39188197976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39188197976)
  SUCCESS에서 최종 source manifest와 EXE hash를 대조하고 Light/Dark 각 실행 exit 0,
  `SORT_MENU_FUNCTIONAL_PASS`, 사용자 설정 불변, task/product 잔류 0을 확인했다.
  최종 GUI fixture SHA-256은 `bba0695a4a0a49a7091b29fa98adf9fe06561b2b0e91cf59227a68f66d927e1b`다.
  8개 모드의 상호 배타적인 체크, 실제 이름 순서, 좌우 pane과 WindowTab 상태 복원,
  기존 PaneTab 공유 동작에서 메뉴/목록 일치를 수용한다. 전체 GUI/E2E나 Debug는 재실행하지 않았다.
- **VISUAL ACCEPTANCE: PASS (96 DPI, Light/Dark, 960/800×634의 정렬 메뉴).**
  BEFORE/AFTER 네 쌍의 실제 원본 PNG를 각각 검토했다. 이름 내림차순의 체크 표시와
  이름 오름차순의 키보드 포커스 테두리가 구분되고, 모든 메뉴 문구와 체크가 읽힌다.
  체크 여백 때문에 popup 폭이 늘어난 것은 의도한 변화이며 800px에서도 잘리지 않는다.
  두 pane·명령 영역·파일 목록·열 머리글에서 새로운 material overlap/clipping은 없었다.
  synthetic breadcrumb 경로와 마지막 F6 상태 문구 차이는 fixture/입력 이력 차이로 분류한다.
  메뉴 외의 전체 상태, 실제 고배율·HC·Narrator 음성은 이번 수용에 포함하지 않는다.

| AFTER 원본 PNG (ignored `logs/r1-sort/`) | SHA-256 |
| --- | --- |
| `after-light-960.png` | `a6cc0a682595802cd8f985a0303d6350de731b06b03237189eb6ef238ed98252` |
| `after-light-800.png` | `e9067bac14fdcba9c0f5afb5834ce97e3785ab72d25948c01191538ad4f21f78` |
| `after-dark-960.png` | `5ad684ef83619586ac17e3102b010eee3ee5c845a2291a948fb398ee6ac8a5bd` |
| `after-dark-800.png` | `7a8fc4db28ebd55fb234e67027571a9b2f75db66516557ff2e94ae8a409efd26` |

정확한 matched crop은 960px에서 `[47,43,983,661]`, 800px에서 `[47,43,823,661]`다.
VM의 검토된 후보 source/runtime/evidence는 owner marker가 있는 test-owned `s-8bd610da`에
보존한다. 이것은 registered central GUI의 exact-main status나 설치·배포 수용을 뜻하지 않는다.

진단 중 실패한 준비/fixture 작업은 제품 실패와 구분한다. 첫 dependency 경로 오류,
SYSTEM 생성 checkout의 사용자 Git 소유권 경계, root 명령 종료 후 `Start-Process -Wait`
대기, 필수 polling interval 누락, 숨긴 ComboBox의 `selected_index() == None`을 순서대로
확인했다. 입력 포커스/체크/실제 파일 순서를 추적한
[39186572498](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39186572498)는
정상 종료 0으로 마지막 항목이 잘못된 테스트 oracle임을 확인했다.
통과한 제품 빌드를 재실행하지 않고 무효화된 GUI 판정 경계만 수정했다.
실패/취소/대기 기록을 최종 PASS로 소급 변경하지 않는다.

### 추가 확인: 폴더 탭의 정렬 소유 범위 차이 (P1, 기존 동작)

[39187495613](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39187495613)
SUCCESS의 같은 입력 비교에서 기존 `300eeb16…`와 R1 `5a90c5de…` 모두 다음을 보였다:
기존 폴더 탭 이름 내림차순 → 새 폴더 탭 이름 오름차순 → 새 탭 닫기 후 기존 탭도
오름차순. 두 app 정상 종료 0, 실제 파일 순서와 legacy 설정 보존을 확인했다.
R1이 새로 만든 회귀는 아니지만, ARCHITECTURE의 PaneTab별 sort 설명과 현재 구현 사이의
차이다. `WindowTabState.fileLists[side].sortMode`가 현재 pane 단위로 공유되고,
`explorerui::Pane.tabs`의 navigation Session에는 별도 sort 값이 없다.

후속 요구사항: PaneTab별 정렬을 실제로 독립시킬지 결정하고, 선택한다면 현재 sort의
capture/restore, 새 탭 초기값, close/switch/restart 및 session schema 호환성을 함께 검증한다.
관련 파일은 `file_list_state.h`, `window_tab_state.h`, `WindowWorkspaceController`,
`SessionCoordinator`, `src/base/ui_session.*`, pane tab event/presentation 경계다.
이 작업은 R1 체크 표시 개선에 섞지 않는다. R1 수용은 현재 데이터의 정렬과 메뉴 표시가
일치하고 기존 동작을 보존하는 범위이며, PaneTab별 정렬 독립성을 인증하지 않는다.
