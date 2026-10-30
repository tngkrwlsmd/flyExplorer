# 2026-10-30 파일 목록 Backspace 뒤로 가기

Windows 탐색기 기본 조작과 현재 구현을 대조해, 파일 목록의 일반 Backspace를
기존 뒤로 가기 명령에 연결했다. 상위 폴더 이동이 아니라 현재 폴더 탭의
방문 이력을 사용한다. Ctrl/Shift/Alt 조합과 텍스트 편집 입력은 대상이 아니다.
파일 확인창 또는 종료 중에는 새 명령을 실행하지 않는다. 탐색 중 요청 거부,
이력 없음, 늦은 결과 처리와 패널 소유권은 기존 OnBackClicked 경로를 재사용한다.

기준 PR head는 `e5e6f2aa939a3ad965bf6ab7c30c8ff53c9e5b3b`다.
Microsoft 공식 [Windows 단축키](https://support.microsoft.com/en-us/accessibility/windows/keyboard-shortcuts-in-windows)의
File Explorer Backspace 동작을 2026-10-30 확인했다. 새 제어 요소나 저장 형식,
파일 조작·클립보드 동작은 추가하지 않는다.

## 현재 검사

- 관련 단축키/탐색/명령 가용성 소스 계약 **34/34 PASS**.
- `git diff --check` PASS, 준비한 소유 GUI 스크립트 Python AST 검사 PASS.
- 이 커밋 시점의 Windows 증분 Release·실제 키 입력은 **검증 대기**다.
  아침의 이전 성공 바이너리를 새 C++ 변경의 증거로 사용하지 않는다.
- 최소 실제 검사는 양쪽 패널에서 서로 이웃인 두 폴더 사이의 이력 복귀,
  반대 패널 보존, 주소·검색·이름 편집에서 글자 삭제 유지와 원본/정상 종료다.
  새 전체 GUI·클린 빌드·포장 검사를 실행하지 않는다.

## 직전 빈 배경 메뉴의 화면 검토 완료

이 기능을 시작하기 전 기존 제품 a4333748의 보존된 전후 PNG를
[41008296066](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41008296066)에서 읽어 직접 검토했다.
Light/96 DPI/1160x640 조건에서 수정 후 이름 줄기의 파란 선택 강조와 포커스
밑줄을 확인했고 도구 모음·양쪽 목록의 새 겹침은 없었다. 긴 이름의 일부는
고정 폭 입력란 내부 스크롤로 처리된다. 이 이름 입력 포커스 범위만 시각 수용한다.

- 이전 PNG SHA256: `0fe3b2f877efa9ea065b398edcb230b37776601c6d078d487b70e0f7c89061dc`.
- 이후 PNG SHA256: `d2b9ca4b0088bd602a0a705b143997d65a313d1ae4d29afe9c53e063bd37a888`.
- 생성 직후 PNG `bd6193b29021628b7b17eb432c7da091566b4a2631d5d04f59469c54dbc3e1ba`는
  불러오는 중인 이전 목록 프레임이므로 생성 행의 최종 픽셀 수용으로 사용하지 않는다.
- 기존 실제 파일 생성·선택·정상 종료/보존·정리는 #41007167335의 한정 증거를 재사용한다.

## Windows 후속 결과와 한정 수용

- 제품 소스: `a6174aee2fd45cd56d27aaa83a3e278f344cd881`.
- [41008802577](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41008802577):
  기존 캐시로 증분 Release 성공, m22_transfers.cpp 컴파일을 확인했다.
  EXE SHA256 `a1fd4ccd44191a9d0acdb6cf2b66739b8fa8326e9ed0a12a034bf4d4247714a1`.
  왼쪽 Second→Backspace→First와 반대 패널 보존은 PASS다.
  오른쪽 준비를 기존 왼쪽 전용 benchmark navigate 함수로 검사해 전체 실행은 FAIL했다.
  정상 종료/원본 설정 보존은 확인했으며 실패 자료를 보존한다. 제품 결함으로 분류하지 않는다.
- 테스트만 수정한 `86141a2e`/`282ef2e23b5df2afd2f44f85966328082145e1e3`에서
  명시한 패널의 경로·행·명령 준비를 확인하도록 바꾸고, 왼쪽 성공을 재사용하는 후속 범위를 제공했다.
- [41009193684](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41009193684):
  C++ 변경이 없고 위 EXE 해시가 같음을 확인해 재빌드 없이 오른쪽·편집 검사만 실행했다.
  오른쪽 Second→Backspace→First, 왼쪽 위치 보존, 주소/검색/이름 편집의 실제 글자 삭제와
  이름 편집 Esc 취소가 PASS다. 정상 종료, 원본 설정/소유 파일 이름·바이트 보존,
  성공 fixture/profile 제거도 PASS다. 이전 왼쪽 검사를 다시 실행하지 않았다.
- [41009358308](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/41009358308):
  실제 Light/96 DPI/1160x640 PNG 네 장을 직접 검토했다. 활성 왼쪽/오른쪽의
  Second→First 주소·탭·파일 행 변화와 반대 패널 보존을 확인했고 목록·명령 영역의
  새 겹침/잘림은 없었다. 일부 이동 전 footer는 불러오는 중인 프레임이므로
  전체 정지 상태나 모든 비동기 상태 화면의 수용으로 확대하지 않는다.
  source282ef2e clean, 실행 앱 0개와 두 소유 worker task의 제거도 확인했다.

| 실제 PNG | SHA256 |
| --- | --- |
| 왼쪽 이동 전 | dfd8cc027591f9e173d8bdd0af5f9475778565932a9dd163e03315c08a671a5e |
| 왼쪽 이동 후 | 6a07f6d3b7cb09004ff520d5d447f20e8d25d4cceeb0f79bc312283efbeac060 |
| 오른쪽 이동 전 | 24cf2cf9994fa25cc12e22f193b23950bdf692e68ec4c92975f20dc287d69b5d |
| 오른쪽 이동 후 | 3c0b2ee2af35e8acd29caa59b9e29863ec7c0c4f31a0fc263b649bd322bb775c |

이번 파일 목록 Backspace의 로컬 이력/편집 보존은 위 조건에서 기능 수용한다.
Dark/가상 제공자/모든 키 조합/실제 Explorer 동시 대조/실제 충돌창에서의 키 입력은
이번 runtime 검사 밖이다. 기존 guard 소스 증거와 runtime 증거를 구분한다.
세션/패널 소유 정책과 실제 클립보드·휴지통은 변경하지 않았으며 PR #70은 미병합이다.
