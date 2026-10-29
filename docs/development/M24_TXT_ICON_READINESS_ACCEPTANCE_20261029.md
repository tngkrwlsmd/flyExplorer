# 2026-10-29 — M24 등록 .txt 아이콘 준비 및 실제 표시: 한정 Windows 검증

## 변경과 실행 기준

- 제품 수정: [`ef3588db`](https://github.com/tngkrwlsmd/flyExplorer/commit/ef3588db355e6c3f00f7e6de8050346e5e076a30)의 `file_detail_controller.cpp`. 기존 일괄 Windows 유형 조회에서 `.txt` 유형명은 있지만 BGRA 아이콘 픽셀이 비어 있으면 이미 있던 1회 제한 개별 재조회를 사용한다. 재조회가 부분 응답이면 기존 정상 유형명/이미지는 유지. 새 OS Shell 접근·이미지 위조·파일 변경·재시도 제한 증가는 없다.
- 전용 GUI 검사 [`ddd34069`](https://github.com/tngkrwlsmd/flyExplorer/commit/ddd340694fa98442ea8e2bfcde6139901aac94c9): 정확한 테스트 소유 `readme.txt` 행의 자식 `Image`에 `AutomationProperties.Name=` `Windows system registered file icon`이 존재하고 행 안의 16×16 사각형을 갖는지 확인한다. 350ms 후 다시 확인하고 **그 준비 상태에서** 소유된 HWND를 캡처한다. 유형 글자만 나타나는 것은 PASS 조건이 아니다. `.env.local`과 `.gitignore`는 일괄 조회 구성용 테스트 소유 파일일 뿐, 기존 L03 유형 시험을 재개하지 않는다.

## 정확한 증거

| 항목 | 검증 결과 |
| --- | --- |
| 이전 Windows x64 Release EXE SHA-256 | `c2f4251291327083353acc6ca1afd81d8a758d83edc5eaee548e96b392232051` |
| 변경된 Windows x64 Release EXE SHA-256 | `5fef82d04f58a9640a4bab2db4b64cd496e2675d64ffe3ce5315c6353e0f4fb4` |
| 소스·테스트 정확한 HEAD | `ddd340694fa98442ea8e2bfcde6139901aac94c9` |
| 이전 관련 소스 계약 | [중앙 #40839047125](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40839047125) **8/8 PASS** — 이미 수용, 이번에 재실행 안 함 |
| 변경 소스 Release | [중앙 #40840990001](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40840990001) `M24_BUILD_RELEASE_EXIT=0`, `flyExplorer.exe` 해시 갱신 |
| Light 테마 소유 `.txt` 아이콘 | 같은 실행, GUI exit 0, `icon_ready=true`, 아이콘 좌표 `[231,306,247,322]`, 유형 `텍스트 문서` |
| Dark 테마 소유 `.txt` 아이콘 | 같은 실행, GUI exit 0, `icon_ready=true`, 동일 크기·좌표, 유형 `텍스트 문서` |
| 이미지 수집·수동 검토 | [중앙 #40841368812](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40841368812) 두 원본 PNG 해시 대조 완료, 실제 Light/Dark 화면 검토 |
| 안전한 정상 종료와 데이터 보존 | 두 테마 모두 종료 0, 기존 fxfile 레거시 설정·시험 파일 해시 불변, 개별 격리 프로필 삭제. 별도 VM 판독에서 소유 폴더/프로필 잔존 0 |

- 환경은 중앙 승인 Windows VM, Windows 11 API `10.0.26300`, 96 DPI, 테스트 소유 로컬 파일 3개, 앱 창 1160×640. 개인 PC·실제 사용자 파일·OS 전역 설정은 사용하지 않았다.
- Light 원본 `capture-ready-light.png` SHA-256: `373b6d5f53297f9e06d871112b1040cc8cf5239bf44ab38386f851f46871e71a`.
- Dark 원본 `capture-ready-dark.png` SHA-256: `48b3d248ec4d3b32ba339c80565a5d39ad3d45d070436d86019a732d82fc0078`.
- UIA에서 두 테마 모두 해당 행의 **Windows 등록 파일 `Image` 요소가 실제로 준비되어 표시**됨을 확인했다. 실제 스크린샷에서도 아이콘이 파일명 왼쪽에 나타나고 텍스트와 양쪽 패널이 읽힌다. **아이콘 그림 자체는 단순한 문서 모양**으로 보이므로, 과거 캡처의 세부 문양과 동일하거나 모든 Windows 파일 연결의 그림 품질이 완전하다는 결론을 내리지 않는다. 이전 바이너리의 icon-ready UIA 상태를 같은 조건으로 측정하지 않았으므로 이 전후 결과만으로 변경 코드가 일정 비율만큼 개선했다고 정량 주장하지 않는다.
- [별도 VM 빌드/화면 판독 #40841368812](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/40841368812): `file_detail_controller.cpp`와 WinUI 프로젝트 링크 확인. `fly.bat build Release`는 기존 출력을 사용해 시작했지만 `Previous IPDB and IOBJ mismatch`로 **25,356 함수 전체 재컴파일**로 전환됐다. Clean/package나 다른 기능 GUI는 실행하지 않았다. 컴파일러 C4456 지역 변수 가리기 경고는 기록만 남기고 관련 없는 코드까지 확장하지 않았다.

## 수용/미수용 경계

**완료:** 정확한 새 Release 컴파일, 해당 `.txt` 파일에서 등록 이미지 요소 준비 확인, 같은 상태의 Light/Dark 화면 확인, 정상 종료와 소유 데이터 보존/정리. **미수용:** 모든 아이콘 세부 문양의 과거 대비 완전 동등성, 모든 확장자·Shell 제공자·반복적인 캐시 부하·색인·전체 UI 시험, 제외된 G03–G05와 중단된 G07. 종전 L03 유형 글자·검색·홈·미리보기·복사 수용을 다시 검사하지 않았다. 추가 재검증은 동일한 증거를 반복하기보다 새로운 구체적 사용자 관찰이 있을 때만 해당 범위를 선정한다.
