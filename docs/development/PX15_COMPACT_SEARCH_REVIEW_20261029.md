# PX15 작은 창 검색 패널 가림 수정 — 2026-10-29

## 문제와 변경

`main@3c22b4240c8d943c4f34cc2c05c7508ce2d63a97`의 실제 Release에서 검색을
연 뒤 960×519로 복원하면 높이 제한 없는 검색 패널이 양쪽 파일 목록을
가리고 결과 폴더 이동 버튼을 창 아래로 밀어냈다. 1220×700에서도 파일
목록의 표시 높이는 57px였다. 3개 소유 파일 중 한 결과를 검색한 Light
화면으로 변경 전 현상을 확인했다. Home의 과거 축소 문제와 별개다.

검색 패널만 세로 ScrollViewer로 감싸고, 열기·패널 크기 변화·창 크기 변화에
사용 가능한 높이를 다시 계산한다. 다른 chrome 행을 제외하고 파일 패널에
160 XAML 단위를 남기며 검색 높이는 0~400으로 제한한다. 넘치는 조건·결과·
이동 버튼에는 세로 스크롤로 접근한다. 검색 Controller, 취소/결과 유효성,
파일 작업, 탭 소유·세션 정책과 Home의 높이 계산은 바꾸지 않았다.

## 실행 환경과 소스 식별

- 중앙 관리 Windows VM, Windows 11 build 26300, x64 Release, 96 DPI.
- 창 rect: 넓은 창 `(20,20,1240,720)`, 작은 창 `(20,20,980,539)`.
- 변경 전 EXE SHA256:
  `ea1bd812d8417cd5b10b745a38ae2d31bac155d0e9ab047ff4f76f37193ba8f2`.
- 변경 후 EXE SHA256:
  `ccc88f0fc24981b44cab6712da21823228f85c18bd0991859f42e2b8086bc431`.
- 빌드는 기준 main에 아래 검토된 변경을 적용한 후보에서 수행했다. 최종 문서
  커밋의 clean HEAD를 빌드한 것으로 표현하지 않는다. 기존 산출물/캐시를
  재사용했으나 헤더/XAML 의존 파일 재컴파일과 LTCG IPDB/IOBJ 불일치에 따른
  full-function fallback이 있었으므로 순수 증분 링크라고 표현하지 않는다.

| 후보 파일 | 검증한 Git blob |
| --- | --- |
| `app/winui/MainWindow.xaml` | `877931f71533b0f1aa756dfbbc0e75e84568559e` |
| `app/winui/MainWindow.xaml.cpp` | `1245b1b2917dc69f1ac69a0b2897b9258eacff73` |
| `app/winui/MainWindow.xaml.h` | `a71d90a116572a4e2a11bd5aa8384ca7173a4e58` |
| `app/winui/m19_features.cpp` | `77159802bf481ad594ac25690b862f47c495a2e1` |
| `tests/winui/test_search_controller_contract.py` | `2f361dcee4a72e100e123f57cf14bedf24e93b85` |
| `tests/winui/test_px15_search_layout_gui.py` | `bd1a5fdcbed5bc895db34074eb1fa3022727bfb1` |

## 집중 검증과 실패 경계

- 클라우드 소스 검사: 검색·공유 resize 의존 Home 계약 **18/18 PASS**;
  XAML XML 파싱, GUI Python 구문, `git diff --check` PASS.
- 중앙 [#40823034339](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40823034339):
  공식 `fly.bat build Release` exit 0. 첫 GUI는 결과 이동 후 접힌 검색 노드가
  UIA 트리에서 사라진 상태를 harness가 예외로 재시도해 FAIL했다. 빌드 PASS와
  Light 화면 증거는 유효하지만 이 실행의 전체 GUI는 PASS가 아니다. 제품은
  정상 종료했고 원래 설정·소유 파일은 보존됐다. UIA 노드 부재를 올바르게
  처리하도록 검사만 수정하고 동일 EXE를 재사용한다.
- 중앙 [#40823403517](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40823403517):
  동일 EXE로 집중 GUI **PASS**. Light/Dark 각 넓은→작은 창에서 양쪽 실제
  파일 목록 높이 93px를 확인했다. 작은 창에서는 세 파일 행이 표시되고,
  검색 패널 스크롤 후 한 결과 선택·이동 버튼 접근·결과 폴더 이동 PASS.
  정상 종료 코드 0, 원래 설정/소유 파일 불변, 성공 fixture/프로필 제거 PASS.
- 실제 픽셀 **PASS(한정 범위)**: Light 넓은/작은 창 전후 및 추가 Dark
  변경 후 화면을 검토했다. 검색 조건 상단과 스크롤된 결과/선택/이동 버튼,
  양쪽 파일 목록, 상태줄을 포함한 변경 후 PNG 6장을 직접 확인했다. 기존의
  가려진 파일 영역이 복구됐고 테마별 대비·선택 표시의 새 결함은 관찰하지
  못했다. 넓은 창에서도 결과 이동 버튼은 필요시 스크롤한다.
- 중앙 [#40823683860](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40823683860):
  남은 실패 시도의 소유 fixture/격리 프로필 3세트를 파일명·원래 내용·부모 경로·
  reparse 부재 확인 후 제거 PASS. 빈 최초 작업 폴더 제거, 테스트 앱/작업 0개,
  검증한 EXE/빌드 캐시/별도 PNG·실패 로그 보존. 임의 폴더 정리는 하지 않았다.

원격 준비/변경 전 기록도 실패 그대로 보존한다.
[#40822374054](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40822374054)는
숫자 SID ACL 구문 오류로 앱 실행 전 FAIL했다. `*SID` 구문으로 수정했다.
[#40822458468](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40822458468)와
[#40822635769](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40822635769)는
가려진 파일 목록의 UIA geometry 조회가 중단된 harness FAIL이다. 후자의 실제
Light 넓은/작은 창 PNG와 정상 종료·보존 결과는 현상 확인에 사용했다. 변경 전
Dark는 캡처하지 못했다. 캡처를 다시 늘리지 않고 유효한 Light 전후와 추가
Dark 변경 후 화면으로 범위를 한정한다.

## 재현과 남는 범위

Windows의 검토된 정확한 Release와 격리 환경에서 다음 집중 harness를 사용한다.
원래 설정 6종의 존재/해시를 읽기 전용으로 비교하고, 별도의 APPDATA·LOCALAPPDATA·
USERPROFILE·TEMP·TMP 및 소유 파일 3개만 사용한다. 화면은 소유 foreground HWND와
실제 디스플레이 경계를 확인한 뒤 캡처한다. clipboard·휴지통·개인 PC는 사용하지 않는다.

```powershell
python tests/winui/test_px15_search_layout_gui.py --phase after
```

이 결과는 PX15 검색 패널의 명시한 창 크기·검색 결과 한 개·테마 범위다.
전체 PX15, 모든 창 크기/긴 경로/조건 조합, PX06 취소 재수용, OS DPI/고대비/
Narrator/실제 IME/외부 드라이브 수용이 아니다. 많은 고급 조건은 스크롤해야
하며 좁은 창의 일부 긴 설명 문구는 기존처럼 잘릴 수 있다. PX11 정책은
변경하지 않았다. 미리보기 등 별도 미검토 화면은 계속 별개 과제다.
