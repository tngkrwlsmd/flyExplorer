# UI-09 — 북마크 도구 모음 잔상 실행 진단 (2026-09-26)

## 재현 조건과 원인

기준 소스는 `dca62afa7ef4abbed5aa4745c68a81e8c07f6524`이며 작업 재개 시
fetch한 `origin/main`과 일치했다. 그 위에 제한된 임시 좌표/paint 진단을
추가하고 실제 Windows의 `Release-x64-Unicode | x64` 실행으로 확인했다.
이 문서는 이전 UI-09 원인 후보를 확정 사실로 승격하지 않는다.

**Acceptance:** 기본 8개 북마크가 있는 내 문서 화면에서 설정의 앱 테마를
Light ↔ Dark/System으로 적용한다. 아이콘과 레이블은 한 번만 표시되고,
아래에 잘린 색상 조각이 남지 않아야 한다. 창을 닫거나 다시 열어 없애는
것은 성공 조건이 아니다.

**Observed:** 시작 직후에는 깨끗했으나 테마 적용 후 Light와 System(Dark)
양쪽에서 사용자 스크린샷과 같은 잔상을 직접 재현했다. 버튼은 8개, native
row는 1개였고 `TBSTATE_WRAP`은 없었다. client/band 높이는 40px였다.

최초 실패를 설명하는 실제 순서는 다음과 같다. 좌표는 toolbar client 기준이다.

| 순서 | 수정 전 실행 기록 | 의미 |
| --- | --- | --- |
| 1 | `TB_SETBUTTONSIZE`: 첫 항목 `(0,0,83,22)` → `(0,0,83,36)` | 테마 갱신의 `ApplyModernMetrics`가 36px 버튼 높이를 적용 |
| 2 | tick 36623343: owned paint, item bottom=36, DC clip=`(0,0,1313,40)` | 아이콘과 글자를 36px 기준으로 배치해 실제 출력 |
| 3 | tick 36623453: owned paint, item bottom=22, DC clip=`(0,0,572,22)` | native 버튼 좌표는 줄었지만 이전 위치의 하단 픽셀이 update region에서 제외 |
| 4 | 화면의 각 아이콘/문자 아래 짧은 색상 조각 | 이전 아이콘은 y=10..25, 새 아이콘은 y=3..18에 해당하며, y=22..25는 다음 paint의 clip 밖 |

**확정한 책임 경로:** 설정 적용 → 북마크 재구성/modern metrics → 36px paint →
MFC 명령 UI 갱신 → `MainFrame::canExecute`의 `CCmdUI::SetCheck(FALSE)` →
`CToolCmdUI::SetCheck` → `CToolBar::SetButtonStyle` → `_SetButton`.
설치된 VS 2026 MFC `bartool.cpp`에서 `_SetButton`은 상태/style 변경에도
버튼을 delete/reinsert하고, **변경 후** `TB_GETITEMRECT`만 invalidate한다.
comctl32가 이때 버튼 높이를 다시 계산하면 변경 전 그려진 픽셀이 빠진다.
버튼 style도 `0x50`에서 `0x52`로 변한다. UI-09는 버튼 중복 생성이나
두 번째 행을 단정해야 설명되는 문제가 아니라, **축소 전 영역을 빠뜨린
명령 상태 갱신의 invalidation 오류**다.

이 경로는 수정 빌드의 `CToolBar::OnUpdateCmdUI` 직전/직후 계측으로도
직접 확인했다. 단순한 타이밍 추정이 아니다.

```text
tick=6128406 owned: item=(0,0,83,36), clip=(0,0,1315,40)
tick=6128515 command-update-before: item=(0,0,83,36)
tick=6128515 command-update-after:  item=(0,0,83,22)
tick=6128515 command-update-damage: rect=(0,0,572,36)
tick=6128531 owned: item=(0,0,83,22), clip=(0,0,572,36)
```

해당 수정 빌드에서 Light → Dark 적용 직후, 재열기 없이 잔상이 사라졌다.
원인 진단에 사용한 임시 trace는 최종 제품에서 제거한다.

## 조사 항목별 결론

| 후보 | 확인 결과 / 한계 |
| --- | --- |
| 중복 버튼, 초기화 실패 | 실패 상태에도 count=8. `setBookmark`는 삭제 후 재구성. 이번 재현 원인에서 배제 |
| WRAP 상태 불일치 | 1 row, 모든 item y=0, WRAP 없음. 이번 단일 행 잔상의 원인에서 배제 |
| item 좌표와 Rebar 크기 차이 | item 36→22, client/band=40. 차이 자체보다 **36px paint 이후 22px 부분 무효화**가 실패를 직접 설명 |
| Rebar 높이/행 계산 | `setWrapable`/size observer/Rebar 연결을 확인. 밴드 높이가 바뀌지 않아도 재현되며 이번 수정은 Rebar 크기/배치 규칙을 변경하지 않음 |
| 중복 paint/print/custom-draw | 실패 trace의 bookmark는 owned paint였고 native custom-draw 호출은 기록되지 않음. 같은 항목을 두 renderer가 중복 출력해야 발생하는 현상이 아님. 다른 모든 OS/print 경로까지 배제했다는 뜻은 아님 |
| control 밖의 출력 | 잔상은 40px client 안, 새 item 22px 밖. Windows가 정상적으로 paint DC를 update region에 clip하기 때문에 남음 |
| 오래된 레이아웃 | 테마 적용 후 최초 command update가 native geometry를 변경함을 계측. 다른 DPI/배치 상황은 아래 검증 범위대로만 판단 |

이전 wrap 초기화/REBARBANDINFO 초기화/first-row clip은 이미 반영돼 있었다.
이번 실패는 한 행에서도 생기고, `FillRect` 역시 paint DC clip 밖의 픽셀은
지울 수 없으므로 첫 행 clipping이나 renderer 통일만으로는 해결되지 않았다.
그 변경들의 다른 목적까지 부정하거나 근거 없이 되돌리지는 않는다.

## 수정과 호환성

- `CToolBarEx::OnUpdateCmdUI`: 북마크에 한해 native item 좌표를 inherited
  update 전후로 수집하고, 좌표가 달라진 항목의 이전/새 영역을 invalidate한다.
  기존 MFC command routing은 그대로 한 번 실행한다.
- `ToolbarLayoutDamage.h`: 변경 항목의 damage 계산을 제품과 native test가
  공유한다. 변경 없는 idle update는 추가 invalidate를 하지 않는다.
- 기존 paint/print/custom-draw 구현, hit test, command ID, text/image list,
  bookmark 데이터, WRAP 옵션, tooltip/drag/drop/overflow 처리는 변경하지 않는다.
- 별도 덮어 그리기, 높이 강제 증가, 임의 설정 초기화, 전체 toolbar invalidation을
  추가하지 않는다. `InvalidateRect(..., TRUE)`는 기존 native High Contrast
  경로의 background erase 계약도 유지한다.
- 최종 소스에서 opt-in 진단 writer와 계측 호출을 제거한다. 개인 북마크 경로/이름은
  진단 파일에 수집하지 않았다.

## 재발 방지

`toolbar_layout_tests.cpp`는 실제 36→22 축소, 확장, 이동, 줄바꿈 형태의 위치 변경,
추가/삭제에 대해 모든 변경 전/후 영역이 damage에 포함되는지 검사한다.
변경 없는 항목과 멀리 있는 변경 없는 항목은 영역을 불필요하게 넓히지 않아야 한다.
96/120/144/192 DPI에 해당하는 좌표로도 검사한다. 이는 DPI 화면 검증을 대신하지 않는다.
기존 native functional suite에 등록했으며 진단 빌드에서 **17 passed / 0 failed**였다.

정적 검사는 상속된 command update 전후의 수집/무효화 연결, 직접 header include,
native test의 실행 연결을 확인한다. 이 경계에 전체 repaint/강제 resize를 넣거나
임시 진단 코드를 다시 남기면 실패한다. 행/팔레트 문자열의 존재를 visual PASS로
판정하지 않는다.

## 최종 검증 상태

최종 진단 제거 빌드와 추가 조작 검증 진행 중. 아래 상태는 작업 종료 시 갱신한다.
GitHub Actions, Debug/x86, Release 게시/배포는 실행하지 않는다.
