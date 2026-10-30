# 2026-10-30 Ctrl+번호 작업공간 탭 선택

상단 숫자키 Ctrl+1~9로 같은 번호의 상단 WindowTab 작업공간을 선택한다.
기존 Ctrl+T/Ctrl+Tab과 같은 계층이며 좌우 패널 안의 폴더 탭은 변경하지 않는다.
없는 번호와 이미 활성인 번호는 탭을 만들거나 탐색을 다시 시작하지 않는다.
주소/검색/파일명 등 텍스트 편집과 메뉴/대화상자, 종료/파일 확인 상태를 보호한다.
Ctrl+Shift+숫자의 기존 보기 전환과 Ctrl+Alt 조합은 이 명령의 대상이 아니다.

기준 PR head: `56355efa28b9ea842e70294a965c235891701b59`.
Microsoft 공식 [Windows 바로 가기](https://support.microsoft.com/en-gb/accessibility/windows/keyboard-shortcuts-in-windows)의
파일 탐색기 Ctrl+Number (1-9) 안내를 2026-10-30 확인했다. Ctrl+9를 마지막
탭으로 별도 해석하지 않고 아홉 번째 탭으로 취급한다. 세션 형식과 탭 상태
소유권, 파일 작업 엔진과 UI 구성은 변경하지 않는다.

## 소스 검사와 현재 경계

- 단축키/탐색/명령/파일명 명령의 관련 소스 계약 **53/53 PASS**, diff 검사 PASS.
- 새 내부 RefreshWindowTabs 호출 때문에 기존 검사 셋이 이벤트 본문을 너무
  일찍 잘랐다. 실제 이벤트 종료 경계를 사용하도록 검사 코드만 수정했다.
- 별도 새 폴더 검사도 기존 F11 지원을 부정하는 오래된 단언을 갖고 있었다.
  기준56355efa에서도 FAIL을 재현한 뒤 새 폴더 명령 자체만 추출하도록 고쳤다.
  이 검사 문제들을 제품 실패로 분류하지 않는다.
- 소유 GUI는 두 작업공간의 양쪽 경로 복원, 반복/없는 번호, 주소 편집 보호,
  원본 설정/파일 보존·정상 종료·성공 소유 정리를 확인하도록 준비했다.
- 이 초기 구현 커밋에서 Windows 증분 Release와 실제 키 입력·픽셀은 검증 대기다.
  이미 수용한 Ctrl+D/Ctrl+휠/Backspace 및 다른 기능 전체를 다시 검사하지 않는다.

## Windows 후속 결과

- 정확한 제품/검사 소스 `a3ab6ce68b2c33744d8cc97043fa82f2890e2b35`.
- [41040999662](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41040999662):
  Release 빌드와 실제 소유 GUI 모두 PASS. MainWindow.xaml.cpp가 컴파일됐다.
  증분 명령으로 시작했지만 IPDB/IOBJ 캐시가 맞지 않아 25,600개 함수의 전체
  코드 생성으로 전환됐다. 최소 코드 생성 또는 완전한 캐시 재사용이라고 표현하지 않는다.
- EXE SHA256 `29b9e2dbd4717f690efb7e15f7f9b0698d7514838df87bc2e8ee476f147c7cac`.
- 두 작업공간을 각각 First/Second 소유 폴더로 준비하고 Ctrl+1/Ctrl+2의 상단
  선택 상태, 양쪽 패널 경로/파일 복원을 확인했다. 같은 번호와 없는 Ctrl+9는
  상태를 바꾸지 않았고 주소 편집의 Ctrl+1은 입력·포커스/작업공간을 보존했다.
- 정상 종료, 원래 설정과 소유 파일 이름/바이트 보존, 성공 fixture/profile
  제거 PASS. 대화상자·메뉴와 다른 텍스트 편집의 모든 조합까지 runtime 수용한 것은 아니다.
- [41041344251](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41041344251):
  같은 Light/96 DPI/1160x640 실제 PNG 세 장을 직접 검토했다. 두 번째→첫 번째→
  두 번째 상단 탭 강조·주소·양쪽 목록의 일치와 새 겹침/잘림 없음을 확인했다.
  일부 유형/아이콘은 비동기 준비 중인 프레임이므로 아이콘 전체 동등성으로 확대하지 않는다.
  소스 clean, 앱 프로세스0과 소유 worker task 제거도 확인했다.

| 화면 | PNG SHA256 |
| --- | --- |
| 두 번째 작업공간, 이동 전 | 4a86effa7afe2f840800e66bd6d23a19b2eb4aeebeda539fc54defc7656ed520 |
| Ctrl+1 후 첫 번째 | 027ad50635adc96bdd6b6b9b9cec9a509ef5a090106db8878d695d676920ea6d |
| Ctrl+2 후 두 번째 복원 | a997d3269a30d749185979c5b61b976a72ec9629ce3a34e029523f7749f474cc |

이 조건의 번호 선택은 기능·시각 한정 수용이다. 3~9개 실제 탭, 다른 테마/
창 크기·제공자와 실제 Explorer 병렬 대조는 별도 미검증이다. 기존 Ctrl+D/
휠/Backspace, 제외 G03~G05/중단 G07과 실제 클립보드·휴지통을 다시 실행하지 않았다.
PR #70은 draft/미병합이며 main c563a0e0는 변경하지 않는다.
