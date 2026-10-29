# EP04/L03 점파일 유형 표시 — 2026-10-29 한정 Windows 검증 수용

## 대상 및 변경

- **제품 변경:** [dfdd2671](https://github.com/tngkrwlsmd/flyExplorer/commit/dfdd26716cc6d608500cee7206e6845f8d68d292)의 `app/winui/file_detail_controller.cpp`만 수정했다. 비동기 시각 유형의 확장자 수집과 대체 유형 문구가 정렬 메타데이터와 동일하게 `std::filesystem::path(path).extension()`을 사용한다. 확장자가 없는 `.gitignore`/`.env`는 무리하게 확장자로 해석하지 않는다. 등록된 실제 확장자(.local, .txt 등)의 Windows 유형명 우선 적용, Shell 항목 별도 위임, 로컬 데이터·세션/정렬 소유권과 명령 동작은 유지한다.
- 테스트 전용 수정: [e19c2a2a](https://github.com/tngkrwlsmd/flyExplorer/commit/e19c2a2aed3513fdb88bc45105356539ed332e4e)의 파일 상세/Windows 유형 소스 계약, [최종 전·후 GUI 테스트 0dbea866](https://github.com/tngkrwlsmd/flyExplorer/commit/0dbea8660ceeb0548a095a2fe304f903dabf0d3b). 테스트용 `archive.tar.gz`는 실제 Windows Shell에서 **압축 폴더**로 분류되므로 일반 파일의 유형 판정 조건으로 사용하지 않았다.

## 정확한 Windows 결과

- 환경: 승인된 중앙 Windows VM, Windows 11 build 26300 (API 버전 `10.0.26300`), x64 Release, 96 DPI, 1160×640 앱 창, 격리된 테스트용 로컬 폴더, 설정·개인 파일/OS 전역 설정 변경 없음.
- 소스 계약: [Windows #40834824156](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40834824156)의 파일 상세 7/7 + Windows 등록 유형 4/4 **PASS**. 이 소스 계약은 `e19c2a2a`에서 실행했으며 그 이후 제품 C++는 변하지 않고 테스트/문서만 추가됐다.
- [최종 Windows #40837682596](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40837682596): 정확한 제품/GUI 테스트 소스 `0dbea8660ceeb0548a095a2fe304f903dabf0d3b`에서 변경 전 Dark GUI, Release 빌드, 변경 후 Dark·Light GUI 모두 **exit 0**.
- 이전 실행 파일 SHA-256: `ab3109a78d9cba63c3f24f29c75b9ad83be2b38466b014f02c0e167fe67a79e3`.
- 변경 후 실행 파일 SHA-256: `c2f4251291327083353acc6ca1afd81d8a758d83edc5eaee548e96b392232051`. 이전과 다르며 [빌드 로그·보존 검증 #40838189060](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40838189060)에서 현재 EXE 해시 재확인.
- 정확한 빌드 로그: `file_detail_controller.cpp` 컴파일과 `flyExplorer.vcxproj` 링크 성공을 확인. 통상 `fly.bat build Release` 증분 경로로 실행했지만 **IPDB/IOBJ mismatch** 때문에 컴파일러가 **25,356개 함수를 전체 재컴파일**했다고 기록했다. Clean/package나 전체 기능 GUI는 실행하지 않았다. 인접 소스의 C4456 shadowing 경고가 있었으나 빌드는 성공했고 이를 별도 결함 수정으로 확장하지 않았다.

| 시험 파일 | 변경 전 Dark 유형 | 변경 후 Dark/Light 유형 |
| --- | --- | --- |
| `.env` | `ENV 파일` | `파일` |
| `.gitignore` | `txtfile` | `파일` |
| `.env.local` | `LOCAL 파일` | `LOCAL 파일` |
| `readme.txt` | `텍스트 문서` | `텍스트 문서` |

- UIA 행의 실제 `[파일] 파일명 | 유형 | 크기 | 날짜` 텍스트로 확인했다. 기존 Windows 등록 `.txt` 유형과 실제 확장자 `.local`은 유지됐고, 변경 대상 점파일 두 개만 올바른 대체 문구로 바뀌었다.
- 세 GUI 모두 **정상 종료 0**, 실제 사용자 레거시 설정 스냅샷 및 테스트 소유 5개 원본 파일 바이트 해시 불변. 격리 프로필과 테스트용 파일은 실행 종료 시 제거됐다. [독립 정리 검증 #40838189060](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40838189060)의 `L03_LEFTOVER_OWNED_FIXTURE_AND_PROFILES=0` 기록.
- 실제 테스트 소유 HWND PNG 3장을 해시 대조하고 [독립 이미지 수집 #40837979417](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40837979417) 후 직접 확인했다. 같은 창 크기에서 변경 전 Dark와 변경 후 Dark, 추가 Light의 유형 글자가 모두 읽히고 양쪽 파일 목록 및 열 배치가 유지됐다. **유형 텍스트·이 화면의 가독성/겹침만 한정 시각 수용**. 파일 아이콘 형태는 캡처 간 차이가 보이므로, 아이콘 자산/로딩/Windows 연결 전체가 변경 전과 동일하다고 주장하지 않는다. 특히 변경 전후 `.txt`의 작은 아이콘 형태 차이는 아직 원인을 입증하지 않은 별도 관찰로 남긴다.

### 원본 화면 PNG SHA-256

| 캡처 | SHA-256 |
| --- | --- |
| 변경 전 Dark `capture-before-dark.png` | `2297be2456f0e5488b6877b54f9540d0f34eeb6f0c3cbb5a7dc9b45ac4e941c5` |
| 변경 후 Dark `capture-after-dark.png` | `30881e422970f1f11a0024f085847d079d6403db72a44ab384d06de212aa1b64` |
| 변경 후 Light `capture-after-light.png` | `dc88323cbef211ee53f70e35b1c05e6532011e4fd69ca988b09f71baa1eb3457` |

## 기존 실패를 소급 수정하지 않음

- [Windows #40836514832](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40836514832): 테스트가 변경 전 전체 파일 유형의 비동기 준비를 지나치게 엄격하게 기다려 GUI 검사 전 실패. 빌드·변경 후 검증 미도달.
- [Windows #40836936586](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40836936586): 테스트용 `archive.tar.gz`를 일반 파일로 가정했으나 OS Shell은 압축 폴더로 표시했다. [증거 #40837109099](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40837109099)에서 양쪽 파일 목록의 실제 UIA 타입 문자열을 확인했다. 제품 유형 수정 자체의 실패가 아니다.
- [Windows #40837304909](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40837304909): 변경 전 GUI 유형 확인·원본 보존은 성공했지만 캡처 준비 중 Python `TypeError: 'RECT' object is not iterable`로 종료. [증거 #40837478633](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40837478633)에서 정확한 예외 확인 후 좌표 필드별 접근으로 수정했다. 세 실패는 그대로 FAIL로 보존하고 최종 성공과 구분한다.

## 수용 경계 / 다음 작업

이 범위는 **로컬 일반 파일 이름 두 개의 점파일 유형 대체 문구**, 기존 실제 확장자 유형 보존, 양쪽 파일 패널 표시, Dark 전후·Light 변경 후 화면 가독성, 정상 종료 및 테스트 격리다. ZIP/TAR를 내부 파일로 인식시키는 변경, 모든 Windows Shell 제공자/연결 유형, 아이콘 완전 동등성, 전체 PX15/EP04, 전체 파일작업/탭/검색 회귀는 수행하지 않았고 완료로 표시하지 않는다. G03~G05는 사용자 제외, G07 실제 IME는 중단 상태를 유지한다. 아이콘 차이가 실제 사용에서 재현되면 해당 **정확한 파일과 icon-ready 상태**만 별도로 검사하고, 동일 유형 텍스트 사례를 자동 반복하지 않는다.
