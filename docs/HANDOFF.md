# flyExplorer 작업 인계 — 2026-10-19 L08 커서 OPEN, G01 코드·빌드 PASS

## 2026-10-21 EP10/F08 — 2~8개 ZIP Store/Deflate 혼합 해제 (코드 반영, 미검증)

- 기준 main `473827e0`. 기존 `zip_store_batch_extractor.h`를
  **2~8개 평면 일반 파일 ZIP의 Store(0)·raw Deflate(8) 혼합**
  해제로 확장했다. 로컬/중앙 헤더 method·flags·시각·크기·CRC·
  파일명·오프셋을 상호 검증하며 Deflate versionNeeded는 20이다.
  ZIP64, data descriptor, 암호화, extra/comment, 중첩 경로,
  링크, 비ASCII 레거시 인코딩 및 다른 메서드는 거부한다.
- 입력 최대 16MiB, 항목/전체 출력 최대 8MiB, Deflate 확장률
  최대 100:1을 적용한다. Deflate는 기존 miniz 3.1.2의
  `ziprawdeflate::inflateExact`로 정확한 소비/출력 바이트를
  확인한 뒤 실제 CRC32를 계산한다. Store는 packed==unpacked를
  계속 강제한다. 총량은 **압축 전 크기 합계**로 제한한다.
  **모든 항목**의 CRC를 검증한 다음에야 임시 파일을 만든다.
- 기존 `flyExplorer-selection-unpacked` 임시 디렉터리·완료 후
  전체 비대체(rename) 공개·원본 및 기존 대상 보존·RAII 실패
  정리·취소·WindowTab/PaneTab/route 확인을 유지했다.
  각 Deflate 호출 앞뒤에는 취소 검사하지만 단일 저수준
  inflate 호출 *진행 중* 선점 취소는 아직 구현하지 않았다.
  공개 rename이 이미 성공하면 취소 요청으로 롤백하지 않는다.
- WinUI 다중 해제 메뉴/완료·지원 형식 안내 문구와 소스 계약을
  갱신했다. 기존 ZIP Store **생성**은 무압축 방식 그대로다.
- **NOT TESTED:** 빌드, 네이티브/소스 테스트, 정상·손상 ZIP,
  CRC·zip bomb·경합·취소, GUI·시각 검증 전부 미실행.
  신규 miniz 통합의 C/C++ 링크도 아직 미검증 상태다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — raw Deflate 단일 ZIP 항목 해제 (코드 반영, 미검증)

- 기준 main `f0824a32`. miniz v3.1.2의 low-level `tinfl`만
  라이선스와 함께 `src/base/third_party/miniz_3_1_2/`에 도입했다.
  원본 3개 파일 중 `miniz_tinfl.c`의 `miniz.h` include만
  독립적인 `miniz_tinfl.h`로 치환했고, `miniz_export.h`
  정적 shim을 별도 만들었다. 라이선스 조건·출처·수정 사항은
  `UPSTREAM.md`에 기록했다. 생성 프로젝트가
  `src/base/zip_raw_deflate.cpp`는 NotUsing PCH C++로,
  `miniz_tinfl.c`는 별도 CompileAsC/NotUsing PCH로 컴파일하도록
  템플릿을 갱신했다(각 번역 단위 no-malloc/stdio/time).
- `zip_raw_deflate.h/.cpp`는 raw RFC1951만 처리한다.
  출력 최대 8MiB, 입력 최대 16MiB, 최대 확장률 100:1,
  고정 크기 출력 buffer에서 `TINFL_STATUS_DONE`·**정확한
  소비 바이트/출력 바이트 일치**가 모두 성립한 경우만 통과한다.
  zlib/gzip wrapper를 받지 않고 암호화·ZIP64/descriptor를
  지원하지 않는다. 단일 ZIP Store 해제의 기존 헤더·경로·
  CRC32 확인 경로에서 **method 8**을 분기해 사용한다.
  기존 no-overwrite 스테이징 및 최종 rename은 유지한다.
- 작업 범위는 **평면 파일 하나가 있는 ZIP Deflate 해제**에
  한정된다. 다중 Deflate, Deflate 압축 *생성*, nested
  directory, Unix creator/extra/comment와 일반 ZIP
  호환성은 지원하지 않는다. Deflate 단일 작업은 아직
  취소 버튼을 제공하지 않으며, 디코딩 중 취소도 미지원이다.
- 신규 vendor 소스는 미빌드·미실행이고 실제 손상/정상 raw
  stream fixture 검증은 하지 않았다. 신규 소스 계약
  작성 및 기존 계약 문구 갱신만 했다. **NOT TESTED**:
  Windows Release/Debug 빌드, native 테스트, GUI,
  시각 검증 모두 미실행. 라이선스는 릴리스 패키징에
  포함해야 하며 GPLv3 배포와 별도 확인이 필요하다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — 표준 DOS 수정시각·ASCII ZIP Store 호환 (코드 반영, 미검증)

- 기준 main `87a968c5`. ZIP 엔진·외부 zlib/miniz 의존성이
  저장소 런타임에 없음을 확인했다. Windows MSZIP는 RFC 1951과
  유사한 Windows 고유 포맷이므로 **ZIP Deflate(method 8)과
  동일하다고 간주해 연결하지 않았다**. 외부 엔진 추가 및
  Windows 앱 패키징/라이선스는 별도 채택과 검증이 필요하다.
- `src/base/zip_store_compat.h`에 **Store(method 0) 전용**
  중앙·로컬 헤더 호환 정책을 분리했다. 일반적인 비제로 DOS
  수정 시간·날짜를 허용하되 두 헤더 값이 같아야 한다.
  ZIP 버전은 DOS 생성자/필요 버전 1.0 또는 2.0만 지원한다.
  GPBF bit 11(UTF-8)만 허용하되 bit11 없는 ZIP은 **7비트
  ASCII 이름만** 허용하고 비ASCII 레거시 코드를 추측하지 않는다.
  단일/다중(Store, 2~8개) 해제 양쪽에 같은 계약을 적용했다.
- **보존한 제약:** ZIP64, Deflate, 암호화, data descriptor,
  비ASCII 레거시 코드 페이지, extra field, 파일·ZIP 주석,
  링크·중첩 경로, 기존 파일 덮어쓰기 금지. 모든 경로·크기
  검증, 실제 CRC, 임시 출력/최종 non-replace publish,
  다중 해제 취소 정책은 그대로 유지한다.
- 기존 추출 계약 둘을 수정하고 신규 소스 계약을 작성했다.
  기존 다중 추출 계약에 남아 있던 옛 시그니처 문자열
  (`extractMany(source)`)도 현행 취소 토큰 호출로 정리했다.
  **빌드·실행 테스트·GUI·시각 검증은 전부 NOT TESTED**.
  향후 raw Deflate는 라이브러리 버전/라이선스 고정 후
  `inflateInit2(-MAX_WBITS)` 기반의 별도 제한적 디코딩,
  입력 소비/출력 상한/CRC/취소 검증이 필요하다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — 다중 ZIP Store 생성·해제 협력적 취소 (코드 반영, 미검증)

- 기준 main `3a99a309`. 기존 FileToolbar 취소 버튼으로
  다중 ZIP Store 생성(2~8개)과 해제(2~8개)에 각 작업이 소유한
  `shared_ptr<atomic_bool>` 취소 토큰을 전달하도록 연결했다.
  Shell 파일 작업 취소 경로는 유지한다. 단일 ZIP 생성·해제와
  읽기 전용 ZIP 항목 검사에 취소 기능을 확장하지 않았다.
- `zip_store_batch_writer.h`는 원본 읽기·아카이브 생성
  작업 중, `zip_store_batch_extractor.h`는 ZIP 검증·임시
  폴더 출력 중 취소를 확인한다. 공용
  `zip_store_writer.h::detail::writeAll`은 선택적 atomic
  토큰으로 64KiB 기록 청크마다 중단한다.
  취소를 최종 non-replace rename 이전에 확인하면
  `Status::Cancelled`로 종료하고 임시 출력만 RAII 정리한다.
  마지막 확인과 실제 rename 사이의 경합으로 이미 성공한
  작업은 취소되지 않는다. 결과 메시지는 이 차이를 구별한다.
- ZIP 작업 시작/완료에 취소 버튼을 활성화·복귀시키며,
  UI 완료 피드백은 기존 정확한 WindowTab/PaneTab/route에만
  반영한다. OS I/O 선점형 중단, 단일 ZIP 작업 취소,
  DispatcherQueue enqueue 실패 복구, 비정상 종료 시
  임시 출력 잔여물, 경로 치환 공격은 미해결·미검증이다.
- 신규/수정 계약은 작성만 했다. **빌드·테스트·GUI·시각
  검증 미실행 / NOT TESTED**. G01 OPEN, G07 사용자
  중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — 다중 ZIP Store 평면 파일 해제 (코드 반영, 미검증)

- 기준 main f8d4c193. 기존 다중 파일 Store 생성기에 대응하는
  **일반 파일 2~8개, 평면 경로, UTF-8/Store 메서드만** 해제하는
  `src/base/zip_store_batch_extractor.h`를 도입했다.
  입력 ZIP은 최대 16MiB, 전체 해제 크기는 8MiB 이하다.
  ZIP64, Deflate, 중첩 디렉터리, 항목별 extra/comment, 암호화,
  symlink, 임의 prefix/trailer, 유사하지만 다른 ZIP은 거부한다.
- 단일 열린 ZIP 핸들에서 읽은 bounded snapshot의 모든 로컬/중앙
  헤더, 파일명, 길이/CRC, 위치·offset, EOCD/중복 이름/안전한
  Windows leaf 이름을 검사한다. **모든 항목의 실제 CRC를
  확인한 뒤에만 첫 출력 파일을 생성한다.**
- 대상은 ZIP과 동일 폴더의 `flyExplorer-selection-unpacked`이다.
  기존 대상이 있으면 작업 자체를 거부한다. 임시 파일 예약에서
  파생된 별도 임시 **디렉터리**를 원자적 CreateDirectory로
  독점 생성하고 그 내부에 각 파일을 CREATE_NEW·flush한다.
  파일 여러 개를 최종 위치에 개별 공개하지 않고, 전부 완성되면
  디렉터리 전체를 non-replace rename한다.
  일반 실패/예외 때 RAII로 알려진 임시 파일과 임시 디렉터리만
  정리한다. cleanup 실패·갑작스러운 종료 시 *최종 위치가 아닌*
  임시 잔여 디렉터리가 남을 수 있으며, 외부 동시 경로/접합점
  바꿔치기 공격을 실제 Windows에서 입증해 차단한 것은 아니다.
- WinUI 우클릭 메뉴에 **ZIP 여러 파일 해제 (Store, 2~8개)**
  명령을 연결해 이전 단일/다중 ZIP 작업 시작과 상호 배제한다.
  성공/실패 UI 및 폴더 refresh는 정확한 WindowTab/PaneTab/
  route/원본 폴더가 유지됐을 때만 적용한다. 작업자가 시작한 뒤
  다른 탭으로 이동해도 OS 파일 I/O 자체가 취소되지는 않는다.
- 신규 소스 계약 추가. **빌드·테스트 실행·native/GUI/시각
  검증 전부 미실행 / NOT TESTED**. 다음 범위는 직접 승인된
  테스트에서 스테이징/재파싱·CRC 손상·충돌·종료 잔여물을
  검증하고 Deflate/일반 ZIP 호환 및 명시적 취소를 별도 설계한다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — 다중 일반 파일 ZIP Store 생성 (코드 반영, 미검증)

- 기준 main 94dacf9a. 앱 우클릭에 "선택한 파일 ZIP으로 묶기
  (2~8개, 무압축)"를 추가했다. **현재 동일 로컬 고정 드라이브 폴더의
  일반 파일 2~8개, 합계 8MiB 이하**만 Store 메서드로 묶는다.
  결과는 해당 폴더의 `flyExplorer-selection.zip`이라는 고정 이름이다.
  기존 ZIP과 원본 파일을 덮어쓰거나 삭제하지 않는다.
- `src/base/zip_store_batch_writer.h`는 모든 원본을 ZIP 공개 전에
  read-only 핸들로 읽고, 크기/수정시각/재분석 속성 검사를 수행한다.
  정규화 경로, Windows 예약 이름, 대소문자 무시한 중복 파일명과
  다른 원본 폴더를 거부한다. ZIP 각 로컬 헤더·중앙 디렉터리
  UTF-8 이름/CRC32/실제 오프셋과 EOCD를 작성한다.
  같은 폴더에 예약한 임시 파일을 flush 후, 덮어쓰기 옵션 없이
  rename한다. 기존 F08 단일 생성/해제 임시 출력과 함께
  링크 수가 1인지 확인해 타 파일의 hardlink로 바뀐 임시 경로를
  통한 변경을 거부한다. 실패/예외는 소유 임시 파일만 RAII 정리한다.
- 기존 `MainWindow::ShowAppFileContextMenu`의 원본 선택 논리 ID,
  WindowTab/PaneTab/route 검사 위에 새 항목을 연결했다.
  `CreateSelectedBatchZip`는 실제 작업 전 다중 선택을 재검증하고
  비동기 작업 후 원래 화면이 같을 때만 상태 및 새로고침을 표시한다.
  기존 단일 ZIP 생성/검사/단일 Store 해제와 동시 진행은 UI 시작
  시점에서 차단하며, 이미 시작한 작업은 화면 전환으로 취소하지 않는다.
- **범위 제한:** 실질적인 압축률 감소(Deflate), 중첩 폴더,
  파일 여러 개 해제, 취소 및 광범위 ZIP 호환은 미구현이다.
  기존 단일 파일 Store 추출기는 다중 ZIP을 해제하지 않는다.
  프로세스 비정상 종료 시 임시 예약 파일 잔류와 디렉터리
  치환/경합 등은 실행 검증·후속 방어가 남았다.
- 테스트 파일은 작성만 했고 실행하지 않았다. 새 기능은
  **빌드·네이티브/소스 테스트·GUI·시각 검증 미수행: NOT TESTED**.
  G01 OPEN, G07 사용자 중단, G03~G05 사용자 제외 유지.

## 2026-10-21 EP10/F08 — 단일 ZIP Store 파일 안전 해제 (코드 반영, 미검증)

- 기준 main 33e960e9. ZIP 생성·읽기 전용 검사 뒤 첫 실제 해제 단위로
  `src/base/zip_store_extractor.h`를 추가했다. 범위는 **ZIP 중앙
  디렉터리 1개, Store(메서드 0), UTF-8, DOS regular file,
  하위 폴더 없는 평면 파일 한 개**이다. 허용 입력 16MiB,
  내부 출력 파일 최대 8MiB. Deflate·다중 파일·디렉터리·ZIP64·
  타 ZIP 구현의 extra/comment·파일명 인코딩 차이는 미지원으로 거부한다.
- 동일한 열린 소스 핸들에서 파일 전체를 읽은 뒤 로컬/중앙 헤더,
  EOCD, 항목 수, 경계/offset, 이름, 크기를 상호 대조한다.
  원본 ZIP 경로와 멤버 leaf를 엄격 검증해 `../`, 절대/드라이브,
  하위 디렉터리, 예약 이름과 링크/재분석 지점을 차단한다.
  실제 데이터로 계산한 CRC32와 헤더를 대조하기 전에는 출력을
  시작하지 않는다. 파일/폴더 충돌이면 무조건 거부한다.
- 대상은 ZIP과 같은 폴더의 실제 멤버 파일명이다. CRC 통과 뒤
  같은 폴더에 독점 예약한 임시 파일을 작성·flush하고
  `MOVEFILE_REPLACE_EXISTING` 없이 최종 rename한다. RAII로
  실패/예외 시 예약한 임시 파일만 정리한다. 기존 원본 ZIP과
  기존 파일은 덮어쓰거나 삭제하지 않는다. 정전/프로세스 종료로
  남을 수 있는 임시 파일 정리, 동시 디렉터리 변경, IO 경합은
  실제 네이티브 실행 검증 전이라 미수용.
- 기존 앱 우클릭에 **ZIP 해제 (Store, 한 파일만)** 명령을 추가하고
  mZipExtractionBusy로 동시 ZIP 작업 재요청을 막았다.
  비동기 완료 피드백은 정확한 WindowTab/PaneTab/route/폴더에만
  반영한다. 다른 탭으로 이동해도 일단 시작한 파일 작업이
  자동 취소되지는 않으며, 화면 복귀 시 성공을 허위 표시하지 않는다.
- 신규 소스 계약 작성 완료, 실행하지 않음. **빌드·원본 코드
  테스트·native fixture·GUI·시각 검증 모두 미실행(NOT TESTED).**
  모든 ZIP/Deflate 해제 호환성 또는 F08 완성을 주장하지 않는다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — 일반 파일 하나를 ZIP Store로 묶기 (코드 반영, 미검증)

- 기준 main 0fdbab04. 기존 읽기 전용 ZIP 검사 다음 개발 단위로
  **일반 로컬 파일 한 개 → 같은 폴더의 <원본파일명>.zip** 생성을 구현했다.
  우클릭 앱 메뉴에 "ZIP으로 묶기 (무압축, 한 파일)" 명령을 추가했다.
  이름과 상한이 고정된 첫 단위이므로 폴더/복수 파일, 실제 Deflate
  압축, 실제 해제 기능은 **아직 제공하지 않는다**.
- src/base/zip_store_writer.h는 디스크 고정 드라이브·정규화 경로,
  재분석 지점 없는 부모/일반 원본, ZIP 안전 leaf 이름을 확인하고
  8 MiB 입력 제한 및 UTF-8 이름 최대 512바이트를 적용한다.
  단일 ZIP Store 엔트리와 CRC32, 중앙 디렉터리, EOCD를 작성한다.
- 원본은 읽기 전용/쓰기 공유 불허 핸들로 읽는다. 출력을 바로
  공개하지 않고 같은 폴더의 예약된 임시 파일에 기록·flush 후,
  MOVEFILE_REPLACE_EXISTING 없이 rename한다. 대상이 존재하면
  **덮어쓰지 않고 실패**한다. 정상 실패 시 생성 임시 파일만
  정리하고 원본은 변경하지 않는다. 예외 발생 시에도 임시 파일
  RAII 정리 경계를 유지한다. 갑작스러운 프로세스 종료 시
  남을 수 있는 임시 파일 정리, 동시 경로 변경과 AV 잠금 등은
  별도 Windows 검증 전이다.
- 기존 WindowTab/PaneTab/route/원본 폴더를 캡처해 완료 피드백과
  폴더 새로고침을 정확한 화면에만 반영한다. 파일시스템 작업
  성공과 표시 컨텍스트 유효성을 구별한다. 복수·폴더 선택과
  UI에서 진행 중 중복 요청은 막는다.
- 신규 소스 계약은 작성만 했다. **빌드, 네이티브/소스 테스트,
  GUI/시각 검증은 요청되지 않아 미실행: NOT TESTED**.
  CRC가 출력 내용과 실제로 일치하는지, 정상 종료·충돌 시 정리
  등은 아직 수용되지 않았다. 다음은 본 기능의 실행 검증이
  허용될 때 한정된 fixture로 확인하고, 별도 F08 안전 추출 정책·
  임시 출력 커밋 방식과 CRC 검증 구현을 이어 간다.
  G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP10/F08 — ZIP 읽기 전용 안전성 사전 검사 (코드 반영, 미검증)

- 기준 main baf87daf. 제품에 ZIP 런타임 엔진이 없으므로 지원
  범위를 확대해 주장하지 않고, 안전한 실제 압축/해제 구현에 앞선
  **읽기 전용 ZIP 내부 항목/메타데이터 검사**를 우선 도입했다.
  단일 로컬 고정 드라이브의 *.zip 항목 우클릭 메뉴에서만 명시적으로
  실행한다. 워커 스레드에서 구조를 분석하고 원래 WindowTab/
  PaneTab/route와 선택 파일 논리 ID/경로가 일치하는 경우에만
  별도 UI 패널에 목록을 표시한다.
- src/base/zip_inspection.h: 16 MiB 입력 상한, 최대 128개 항목,
  개별 해제 예상량 32 MiB/전체 64 MiB, 압축률 100:1 상한.
  ZIP 중앙 디렉터리와 각 로컬 헤더·데이터 범위 및 서로 겹침 검증.
  ../, 절대/드라이브 경로, Windows 예약 이름, 중복/대소문자 충돌,
  파일-자식 경로 충돌, 링크/비정규화·재분석 경로를 거부한다.
  ZIP64, 다중 볼륨, 암호화, data descriptor, 레거시 비ASCII 이름,
  미지원 메서드는 fail closed. 단순 Store/Deflate 메서드의
  메타데이터 검사만 해당한다.
- **파일 콘텐츠/CRC, 실제 압축/해제는 전혀 수행하지 않으며**
  메타데이터 통과를 ZIP 전체 안전성·내용 무결성 PASS로 간주하지
  않는다. 읽기 전용 핸들로 ZIP을 검사할 뿐 실제 파일/폴더
  생성·삭제·기존 항목 덮어쓰기는 없다. 워커 파일 I/O의 강제
  마감/취소는 미구현이며 16MiB 상한과 읽기 전용 경계만 제공한다.
- 새 소스 계약을 추가했지만 실행하지 않았다. **빌드·테스트·GUI·
  시각 검증 모두 미실행 / NOT TESTED**. Windows ZIP/메뉴/파일
  사용 중 경쟁·경계 처리 검증 전이므로 F08 압축·해제 완료로
  보고하지 않는다. G01 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP09/F14 — 폴더별 보기 모드 명시적 기억 (코드 반영, 미검증)

- 기준 main 1f3a993e. 기존 PaneTab 정렬 및 세션 v4 보기 상태를 건드리지
  않기 위해 **명시적으로 기억한 로컬 폴더**에만 뷰 모드 override를
  적용하는 작은 F14 첫 개발 단위를 채택했다. 보기(View) 메뉴에
  "현재 폴더의 보기 기억 (이 세션만)" / "현재 폴더의 기억된 보기 해제"
  2개 명령을 추가했다. 별도 파일 읽기/쓰기 및 숨은 자동 수집이 없다.
- FolderViewController는 WinUI·COM 의존이 없는 인메모리 값 소유자다.
  정규화된 로컬 드라이브 절대 경로/보기 모드 0~4만 받고 최대 64개를
  저장한다. 동일 경로의 명시적 변경은 갱신하며 오래된 override는
  가장 뒤에서 제거한다. 네트워크·가상 경로는 기억하지 않는다.
- 기억된 보기는 해당 폴더에 **실제로 성공한 비동기 Shell 탐색** 후
  대상 패널에만 적용한다. refresh/continuation, 실패/늦은 결과,
  private workspace restore 활성 요청에는 적용하지 않으며, 세션
  파일 schema와 앱 기본 보기 선호도는 변경하지 않는다. 다른
  WindowTab·PaneTab 상태를 직접 갱신하지 않는다.
- Forget은 저장된 override만 제거하고 지금 표시된 모드는 그대로 둔다.
  실행 중 앱을 종료하면 저장한 폴더별 override도 사라진다.
  재시작 후 위치별 보기 자동 복원·모든 보기 옵션/열 크기·정렬까지
  포함하는 완전한 F14/Explorer 위치별 설정 지원은 **미구현**이다.
- 관련 소스 계약 추가. 이번 범위는 사용자 지시로
  **빌드·시험 실행·GUI·시각 검증 미실행( NOT TESTED )**.
  뷰 메뉴·탭 전환·복원·탐색 결과는 실제 Windows 수용 보류.
  G01 종료 OPEN, G07 사용자 중단, G03~G05 제외 정책 유지.

## 2026-10-21 EP09/F07 — 최근 항목 개별 기록 제거 (코드 반영, 미검증)

- 기준 main ca4391bf. 옵트인 세션 내 최근 연 파일과 자주 방문한
  폴더 패널에 각각 '기록에서 제거' 버튼을 추가했다. 기존 전체 지우기,
  기록 OFF 및 창 종료 자동 삭제 동작은 유지한다.
- 기존 RecentActivityController만 개별 항목을 소유하며
  removeFile(path), removeFolder(path)는 정규화된 로컬 경로와 기록
  존재를 검사해 벡터에서 한 건만 지운다. 파일시스템 호출, 실제
  파일/폴더 삭제, Recycle Bin, 디스크 저장, Explorer 최근 기록
  변경은 하지 않는다. 폴더 방문 횟수도 그 항목과 함께 사라진다.
- WinUI는 개별 목록에서 항목 선택 시에만 해당 제거 버튼을 활성화한다.
  실행 전 활성 기록/패널, 선택 인덱스, 표시 문자열과 원본 경로를 다시
  대조한다. 삭제 직후 목록을 재구성하면서 모든 선택/작업 버튼을
  비활성화해 오래된 선택에 의한 다른 기록 삭제를 방지한다.
- F07 관련 미실행 소스 계약에 버튼, 메서드, 원본 경로 대조,
  비파일변경 조건을 추가했다. **빌드·테스트 실행·GUI·시각 검증을
  수행하지 않았다. NOT TESTED.** 실제 WinUI 선택 변경, 좁은
  화면·키보드, 빈 목록 재선택/기록 재활성화 동작은 검증 보류다.
  기존 F07 옵트인 인메모리/비영속 한계를 유지하고 F14 폴더별
  설정이나 F08 ZIP을 구현 완료로 주장하지 않는다.
  G01 OPEN, G07 사용자 중단, G03~G05 제외 유지.

## 2026-10-21 EP09/F07 — 옵트인 세션 최근 파일·자주 방문한 폴더 (코드 반영, 미검증)

- 작업 기준 main 6f79a774. 기존 즐겨찾기·최근 검색과 구분해
  RecentActivityController(인메모리 UI 독립 값 소유자)를 추가했다.
  기본 기록 OFF, 사용자가 체크박스로 ON한 이후에만 이벤트를 모은다.
  OFF·전체 지우기·창 종료는 항목과 빈도를 모두 지운다. 설정·레지스트리·
  Explorer 최근 항목이나 파일 자체를 읽거나 디스크에 저장하지 않는다.
- 실제 비동기 Shell 탐색에서 활성 탭에 성공적으로 적용된 Open/Back/
  Forward/Up 등 Refresh·Continue가 아닌 로컬 폴더만 방문 횟수를
  계산한다. 기본 앱 열기 또는 연결 프로그램 선택이 성공했다고
  반환된 파일만 최근 파일에 기록한다. 실패·시간 초과·취소는 기록 안 함.
  목록은 각각 최대 16개, 1,024 UTF-16 단위 이내의 정규화된
  로컬 드라이브 경로만 허용한다. 자주 방문한 폴더는 방문 횟수 우선,
  동일 빈도일 때 마지막 사용 시각 순서로 정렬한다.
- 명시적 선택으로 최근 파일 기본 앱 열기 / 자주 방문한 폴더 탐색을
  다시 실행할 수 있다. 파일 열기는 기존 FileOpenController,
  폴더는 기존 QueuePath를 호출한다. 다른 WindowTab/PaneTab의
  비동기 결과를 덮어쓰지 않도록 기존 작업 컨텍스트를 재확인한다.
  UI는 상단 최근 항목 버튼과 별도의 Grid.Row=4 패널을 사용하고
  최근 파일과 폴더 목록을 별도 행으로 표시한다. 다른 관리 패널을 열면 닫힌다.
  기본 파일 열기 역시 원본 WindowTab identity를 검사해
  다른 작업공간에 성공 피드백이나 기록을 전가하지 않는다.
- 신규 기능의 빌드, 네이티브/소스 시험 실행, GUI/픽셀·시각 검증은
  **요청되지 않아 수행하지 않았다. NOT TESTED**. 경로 표시 길이,
  작은 화면, 실제 WinUI 이벤트 연결, 세션 기록과 재탐색은 검증 보류.
  다음 개발 단위로 영속 기록 여부와 명시적 동의 범위를 먼저 결정하고
  빈 경로/존재하지 않는 파일 대응을 강화할 수 있다. 현재 F07 전체
  또는 Explorer Home 호환을 주장하지 않는다.
  G01 OPEN, G07 중단, G03~G05 사용자 제외 유지.

## 2026-10-21 EP11/F09 — Windows 연결 프로그램으로 열기 (코드 반영, 실행 미검증)

- 기준 main c9cd4944. 로컬 일반 파일 단일 선택에만 앱 우클릭
  '연결 프로그램으로 열기'를 제공한다. 기존 WindowTab·PaneTab·route·
  선택 논리 ID 보호를 유지하고 폴더·가상 Shell 항목·복수 선택에서는 비활성화한다.
- 기존 FileOpenController의 ChooseApp 모드가 Windows 비동기
  LauncherOptions.DisplayApplicationPicker(true)를 사용해 앱 선택 UI를
  요청한다. 사용자 앱 선택에는 120초 대기 상한과 기존 닫기·오래된 결과 무시가
  적용된다. 기존 기본 앱 열기의 조회 및 15초 경로는 변경하지 않는다.
  앱 선택은 기본 연결이 없어도 진입하므로 사전 QueryFileSupport를 건너뛴다.
- 실행 직전과 완료 피드백은 원래 WindowTab identity, PaneTab, route,
  네이티브/표시 폴더를 확인한다. 취소·실패 시 기본 앱 자동 실행으로
  전환하지 않는다. 파일 변경·레지스트리/연결 프로그램 등록 코드는 없다.
  OS 앱 선택 창에서 사용자가 설정하는 기본 연결은 Windows가 관리한다.
- 소스 계약 추가. 빌드·테스트 실행·GUI·시각 검증 모두 미실행,
  NOT TESTED. 실제 Windows 앱 선택·거부·취소·탭 전환 동작은 수용 보류.
  G01 OPEN, G07 중단, G03~G05 제외 상태 유지.

## 2026-10-21 EP08/F11 — 검색 결과가 있는 폴더로 이동 (코드 반영, 실행 미검증)

- 직전 F13 커밋 96e62435 위에서 소규모 검색 UX 개선을 구현했다.
  기존 결과 목록의 선택 변경과 "선택한 결과의 폴더로 이동" 버튼을 연결하고
  검색 결과의 실제 절대 경로에서 상위 폴더를 도출한다. 검색 결과가 파일이든
  폴더든 "해당 항목을 포함하는 폴더"로 이동하며 파일 실행은 하지 않는다.
- MainWindow는 **직전 성공적으로 수용된 검색의 컨텍스트와 최대 1,000개 결과
  경로만 UI 수명 동안 보유**한다. 결과 항목 선택과 버튼 명령에서
  SearchController::sameContext의 WindowTab, PaneTab, route, 폴더, scope,
  쿼리 계약을 재사용한다. 화면 행 문자열과 해당 인덱스의 원본 결과도 대조한다.
  쿼리·탭·경로가 바뀌거나 검색을 다시 시작/닫은 상태에서는 경로 이동을 거부한다.
- 경로는 파일을 열거나 UI 스레드에서 디스크 속성을 검사하지 않고 기존 비동기
  QueuePath와 Shell navigation의 취소·늦은 결과 거부를 사용한다. 새 탐색 요청을
  제출한 경우에만 검색 패널을 닫는다. 선택된 항목 자체의 자동 하이라이트,
  별도 파일 실행, 자동 검색 모드 변경은 추가하지 않았다.
- 관련 소스 계약을 추가했으며 **빌드, 테스트 실행, GUI 및 시각 검증은 하지 않았다.**
  구현/코드 반영만 확인한 단계이므로 실제 WinUI 동작 및 배치는 NOT TESTED다.
  이전 F01~F06/G02/G06 수용과 F13 미검증 상태는 유지한다.
  G01 종료 위험 OPEN, G07 사용자 중단, G03~G05 사용자 제외.

## 2026-10-21 F13 / EP11 — 빈 텍스트 문서 생성 추가 (실행 검증 보류)

- 사용자 요청의 추가 기능 후보 중 F13의 빈 텍스트 문서(.txt) 생성을 우선
  소규모 단위로 채택했다. 빈 파일 목록 영역의 앱 우클릭 메뉴
  "새로 만들기 > 텍스트 문서 (.txt)"에 추가했다. 기존 WindowTab,
  PaneTab, route 및 비동기 명령 busy 검사를 재사용한다.
- FileToolbar 이름 편집기의 세 번째 상태를 사용한다. "새 텍스트 문서.txt"의
  확장자 앞 이름을 선택하고 Enter는 기존 FileOperationController worker,
  Esc는 편집만 취소한다. 다른 폴더/탭 완료 결과는 기존 수용 경계가 거부한다.
- 네이티브 CreateTextFile은 올바른 단일 이름과 대소문자 비구분 .txt를 요구한다.
  로컬 고정/이동식 드라이브 일반 폴더만 허용하고 상위 경로의 재분석 지점을 거부한다.
  CreateFileW(CREATE_NEW)로 기존 항목 덮어쓰기·삭제 없이 0바이트 파일을 만든다.
  성공 결과는 기존 Shell Refresh 및 1회 선택/표시 흐름을 재사용한다.
- 소유된 M21 네이티브 fixture의 7개 검증 시나리오와 관련 소스 계약을 추가하고
  예상 23개에서 30개로 갱신했다. **빌드·GUI·시각 검증·테스트 실행은 하지 않았다.**
  코드만 추가한 단계로 실제 Windows 기능 수용은 NOT TESTED다.
- F13의 나머지 템플릿/파일 유형, F08 압축, F09 연결 프로그램, F07 최근 항목,
  F12 갤러리는 구현/완료로 주장하지 않는다. G01 종료 위험은 OPEN,
  G07은 중단, G03~G05는 제외 상태를 유지한다.


## 2026-10-21 EP06 새 폴더·이름 변경 완료 후 대상 행 표시 (검증 보류)

- 시작 기준 main `cf8a3a09`. 이름 변경/새 폴더 생성의 네이티브 작업
  결과에는 실제 `Result.target`가 있으나, 기존 UI는 해당 경로를
  새로 고친 목록에서 선택하지 않아 사용자가 수동으로 다시 찾아야
  했다.
- `app/winui/file_list_state.h`에 WindowTab/Pane 소유의
  **비영속 일회성 표시 요청**(`FileCommandReveal`)을 추가했다.
  `m21_commands.cpp`는 파일 명령이 `Succeeded`이고 동일한
  WindowTab·PaneTab·route인 경우만 성공 결과의 실제 대상 경로,
  원본 폴더와 route를 저장한다. 사용자 입력 이름을 다시 조합하거나
  작업을 재실행하지 않는다.
- `MainWindow.xaml.cpp`에서 성공한 정확한 Shell
  `NavigationAction::Refresh` 결과(원래 tab/route/folder)가
  들어왔을 때만 일회성 표시를 활성화한다. Refresh 실패/NoChange,
  다른 탐색 이동에서는 요청을 취소한다. `FillFiles`는 이 표시
  요청을 **한 번만** 적용해 새 경로를 대소문자 비구분으로 찾고,
  실제 목록에 있는 경우 이전 이름의 선택을 지우고 대상 행만
  선택한다. 원래 활성 패널에 해당 행이 있으면 키보드 포커스와
  `ScrollIntoView`도 시도한다.
- 필터, 그룹 접힘, 현재 렌더링 페이지 또는 기존 안전 상한 때문에
  새 항목이 표시되지 않으면 임의 행을 선택하거나 다른 페이지를
  자동 탐색하지 않는다. 이 동작은 기존 bounded rendering 정책을
  보존하기 위해 의도한 제한이다. 별도 비동기 상태 머신, I/O,
  세션 저장 스키마 변경은 없다.
- `tests/winui/test_file_command_feedback_contract.py`에
  일회성 표시 요청·WindowTab/route 보호·성공 refresh·대상 경로
  비교에 관한 **미실행 소스 계약**을 추가했다.
- 변경 커밋: `e89c6467`, `fc082632`, `5d61b09d`,
  `7edff74c`, `1dfb3938`, `7e2ceb84`.
  **사용자 지시대로 빌드·GUI·시각 검증 및 테스트를 실행하지
  않았다.** 파일 생성·이름 변경 후 실제 표시, 필터/정렬/그룹/탭
  조합, 키보드 포커스·스크롤은 NOT TESTED다. 신규 제품 PASS나
  배포 적합성은 주장하지 않는다.
- G01 종료 잔류 OPEN, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP04 파일 목록 선택·포커스 복원 제한 (검증 보류)

- 시작 기준 main `f4093c11`. 기존 `FillFiles`는 같은 PaneTab의
  새로 고침뿐 아니라 **폴더 변경에도** 구 렌더 행의 parsing path로
  선택을 넘길 수 있었다. WindowTab을 바꿔도 화면 ListView는
  재사용하므로 구 UI의 선택이 다른 WindowTab에 혼입될 위험도
  있었다.
- `aec9303e`에서 PaneState에 런타임 렌더 폴더 식별자
  `renderedFolder`를 추가했다. `603ab909`에서 렌더 폴더·route·
  PaneTab이 같은 경우에만 이전 native path 선택을 복원하고,
  화면에 실제로 키보드 포커스가 있던 파일 행의 path가 새 목록에
  있으면 포커스도 복원하도록 했다.
- `7d09bcbf`에서 화면 ListView의 `Tag`로 **마지막 렌더 WindowTab
  identity**를 확인하도록 추가했다. 다른 WindowTab에서 재사용한
  컨트롤의 선택·포커스는 같은 폴더더라도 가져오지 않는다.
  파일시스템 호출·세션 저장 형식·Shell identity나 사용자 파일은
  변경하지 않았다. `19df2ee4`는 해당 소스 계약만 추가했다.
- 사용자 지시로 빌드·GUI·시각 검증 및 테스트 실행은 **전부 하지
  않았다**. 코드 반영만 확인했고 키보드 포커스의 실제 WinUI
  복귀, 스크롤 위치, 접근성, 탭 이동·파일 작업 조합은 NOT TESTED다.
  행이 없어졌을 때 임의 첫 항목을 선택·집중시키지 않는다.
  G01 원인 미확정, G07 중단, G03~G05 제외 유지.

## 2026-10-21 EP06 파일 작업 안내 WindowTab 소유 변경 (검증 보류)

- 작업 시작 main `c981c07a`. 전송 실패 안내가 MainWindow 전역
  `mTransferFailureNotice`로 저장되어 다른 WindowTab의 Refresh
  상태 표시줄에 재노출될 수 있는 소유 범위 문제를 수정했다.
  `WindowTabState::fileOperationNotice`는 런타임에만 존재하며
  저장/세션 마이그레이션 형식에는 포함하지 않는다.
- `MainWindow.xaml.cpp`에서 일반 탐색 시작 시 **현재 WindowTab**
  안내만 초기화하고, Refresh 완료/WindowTab 활성화 시 해당 탭의
  안내만 복원한다. `m22_transfers.cpp`는 전송 완료의 원본
  `windowTabIdentity`를 사용해 해당 작업공간의 안내를 기억하며,
  현재 표시 중인 다른 탭에는 전송 성공/실패/지연 상태를 덮어쓰지 않는다.
  과거 WindowTab이 이미 닫혔다면 다른 탭에 결과를 전가하지 않는다.
- `m21_commands.cpp`에서 새 폴더 생성·이름 변경 결과도 원본
  WindowTab에 한정하며 실패/화면 변경 안내를 원래 탭에 보존한다.
  새 파일 명령이 실제 `Started`인 경우에만 이전 안내를 비운다.
  비동기 컨트롤러 수명과 사용자 파일 처리·취소·충돌 로직은 그대로 둔다.
- 업데이트 파일: `app/winui/window_tab_state.h`,
  `app/winui/MainWindow.xaml.h/.cpp`,
  `app/winui/m22_transfers.cpp`, `app/winui/m21_commands.cpp`,
  `tests/winui/test_file_operation_controller_contract.py`,
  `tests/winui/test_file_command_feedback_contract.py`.
- **검증 상태:** GitHub에 기록된 원본 소스를 읽어 코드 참조를
  정리했을 뿐 사용자 지시로 빌드·GUI·시각 검증과 계약 테스트는
  수행하지 않았다. 신규 기능 Windows 수용은 NOT TESTED다.
  원래 탭으로 돌아온 뒤 실제 안내, 화면 갱신 타이밍, 접근성은
  실행 근거가 없어 미검증으로 남긴다.
- G01 종료 잔류는 OPEN, G07은 사용자 중단, G03~G05는 제외 유지.

## 2026-10-21 EP06/L10 후속 수정 — 다른 WindowTab 새로 고침 차단

- 기준 `ca023a68`. 파일 작업 완료 후 선택 복원은 기존 `FillFiles`의
  Shell parsing path 기반 구현을 유지한다. 파일 작업으로 닿은 폴더를
  새로 고치는 `OnTransferCompleted` 경로에서 완료 당시 WindowTab
  identity와 현재 WindowTab identity가 같을 때에만 `QueuePidl`을
  호출하도록 `2fce9cbb`에서 수정했다. 이름이나 표시 폴더가 같다는
  이유만으로 다른 작업공간의 탐색 상태를 변경하지 않는다.
  StaleContext는 기존 비성공 상태와 안내를 유지한다.
- `0160d728`에서 L10 파일 메뉴의 provider Copy-out을 실제 로컬
  경로가 없는 가상 원본 폴더에서만 활성화하도록 조건을 좁혔다.
  로컬 폴더 내 선택으로 provider 복사를 우회하지 못하게 한다.
- 관련 소스 계약 `9f6f0a2e`, `6f8d7b89`를 갱신했다.
  **사용자 지시에 따라 빌드·GUI·시각 검증과 테스트 실행 없음.**
  코드만 반영했으며 실행 수용은 NOT TESTED다.
  G01 미해결, G07 중단, G03~G05 제외 상태 유지.

## 2026-10-21 EP05/L10 도구 모음과 메뉴 활성화 정책 통일

- 기준 main `affb8e9c`. `74f21ccf`에서
  `MainWindow::UpdateCommandAvailability`가 활성 WindowTab/PaneTab의
  표시 route, 현재 선택 항목의 Tag/indexed identity, 파일시스템 여부,
  최대 항목 수(1,024개)·총 경로 길이와 반대쪽 패널의 대상 로딩·지원 범위를
  읽기 전용으로 판정한다. 로컬 클립보드·휴지통·이름 변경과 반대쪽
  Copy/Move는 실제 지원 조건에 따라 독립적으로 활성화한다.
  새 폴더·붙여넣기도 실제 폴더 준비 여부를 반영한다.
- `0e988e0d`에서 앱 파일 우클릭 메뉴가 같은 로컬 원본, 공급자 Copy,
  대상 폴더/공급자 제한을 따르게 하며, 선택 항목 전체 경로 길이를
  파일 작업 상한 이내로 제한한다. 실제 파일 동작과 비동기 Shell/helper,
  취소/충돌 정책, WindowTab/route 안정성은 유지했다.
- `2c7991b9`, `abb362ba`, `48ee54c4`는 관련 소스 계약만 현재
  구조에 맞춰 기록했다. 기존 EP06 AllSkipped 계약에 남았던 이전
  표현도 실제 누적 skip 처리 코드에 맞게 정리했다.
- **명시적 사용자 지시대로 빌드·GUI·시각 검증 및 테스트 실행은
  수행하지 않았다.** 코드 반영만 확인했고 이 변경의 실행 수용은
  NOT TESTED다. 선택/정렬 후 기존 선택 복원 로직은 그대로 보존한다.
  G01 종료 진단은 OPEN, G07은 중단, G03~G05는 제외 상태를 유지한다.

## 2026-10-21 EP06 후속 수정 — WindowTab 소유·재확인 안전 조건 (검증 보류)

- 기준 main `5e84b12c`. `f08ff579`, `aaaf01e4`, `0c83dd34`에서
  `FileOperationController::Context`에 WindowTab identity를 추가하고
  `sameContext`에서 PaneTab·route·폴더뿐 아니라 WindowTab 자체를
  일치시킨다. 파일 작업 UI는 `FileOperationContext`에서
  `ActiveWindowTab().identity`를 캡처한다. 이 조건은 복사·이동·휴지통
  및 이름 변경의 늦은 완료/확인 결과 모두에 적용된다.
- `02e81a0b`에서 재차 충돌하여 모든 잔여 항목을 건너뛰는 경우,
  `StartStatus::AllSkipped`의 출력 개수를 마지막 단계가 아닌
  이전 확인까지 합친 누적 skip 개수로 바꿨다. 일반 Started 경로의
  건너뛴 개수 안내는 이번 단계 수 그대로다.
- `e662198b`에서 새 충돌 확인창은 `Collision::Reject`로
  거부된 사전 검사이면서 중단 상태가 아닌 경우에만 표시한다.
  `KeepBoth`로 이미 실행한 Shell 작업에서 충돌 오류가 발생하면
  완료 결과를 실패로 남기며 다시 확인창을 띄우지 않는다.
- 관련 소스 계약 기록: `fa55a112`, `62ee89c8`.
  **사용자의 검증 보류 지시에 따라 빌드·GUI·시각 검증과 계약 테스트를
  실행하지 않았다.** 변경 코드 자체를 조회했을 뿐, 기능 수용은
  NOT TESTED이며 부분 작업 복구/실제 완료 수를 보장하지 않는다.
- 기존 실행 증거와 관계없는 G01 종료 진단은 미해결로 유지한다.
  G07은 사용자 중단, G03~G05는 사용자 제외를 유지한다.

## 2026-10-21 EP06/L10 후속 개발 — 누적 건너뛰기·명령 활성 상태

- 기준 `2fe478b9`; `01a42a68`에서 EP06의 이전 충돌 사전 검사에서
  건너뛴 수를 `PendingTransfer`에 보존한다. 남은 항목에서 다음
  충돌이 발견되어 2회 이상 확인하게 되면 이전 건너뛰기 수를 새
  `TransferCompletion`에 이어 전달하며, 이후 KeepBoth/Skip 중
  어느 선택을 해도 누적 상태를 잃지 않는다. 건너뛰기 수는
  `kMaxItems`를 넘지 못하게 하며, 기존 비동기 재검증과 덮어쓰기
  방지 경계를 변경하지 않는다.
- `331b5b43`, `b799b4c1`에서 UI 충돌 확인 대화상자에
  이번 요청에서 남은 항목·이번 충돌 수 및 이전에 건너뛴 수를
  구분해 표시한다. 전송 성공 수는 여전히 Shell 집계 결과만을
  신뢰하며 일부 완료 개수를 추정하지 않는다.
- `ffed004e`에서 L10 파일 우클릭 메뉴의 메뉴 상태를 원본
  폴더 경로와 반대쪽 PaneTab의 로딩 여부·실제 파일시스템/
  지원 provider 대상에 맞춰 활성화하도록 바꿨다. 이동은
  파일시스템에서 파일시스템으로만 활성화하고, virtual provider
  항목의 외부 메뉴·이름 변경은 제한한다. 실제 실행에서의
  추가 가드와 실패 안내는 기존 컨트롤러가 유지한다.
- `81d5c686` 및 `0d54b2c8`에서 관련 소스 계약만 갱신했다.
  **사용자 지시에 따라 빌드·GUI·시각 검증·테스트 실행 없음.**
  코드는 main에 반영됐지만 신규 메뉴 활성·전송 경합·부분 실패
  결과는 NOT TESTED이며 수용 PASS로 승격하지 않는다.
  G01 미해결, G07 중단, G03~G05 제외는 그대로 유지한다.

## 2026-10-21 EP06 선택적 충돌 건너뛰기 — 신규 코드, 미검증

- 작업 시작 기준 `cce132ca`; 파일시스템→파일시스템 **복사/이동**
  사전 확인에서 이름 충돌이 발생한 경우, 기존 **이름 바꿔 둘 다 유지**,
  **취소** 외에 **충돌 항목 건너뛰기** 선택지를 추가했다.
  공급자 Copy, 가상 대상 및 휴지통 요청에는 건너뛰기를 열지 않는다.
- `file_operation_controller.h/.cpp`에서 확인된 대상 충돌 경로와
  정확히 일치하는 이름만 소스 목록에서 제거한다. 충돌 경로 대응이
  모호하거나 탭/경로 컨텍스트가 바뀌었다면 실행을 거부하며,
  모두 충돌하면 새 작업을 시작하지 않는다.
  UI 스레드에서는 파일 상태를 조회하지 않는다. 남은 요청은 기존
  비동기 Shell/격리 helper의 **새 사전 검사**와 안전 상한을 다시 거친다.
  기존 항목 덮어쓰기나 임의 소스 삭제는 허용하지 않는다.
- `m22_transfers.cpp`의 충돌 대화 상자에는 요청 수·충돌 수와
  3가지 선택을 표시한다. 사전 충돌 단계에서는 아직 변경하지 않았다는
  사실을 안내하고 확인 취소와 작업 중 취소를 구분한다.
  `TransferCompletion.skippedCollisions`로 **건너뛴 개수**만 결과에
  전달한다. 나머지 성공 여부는 기존 Shell 집계 결과로만 판정하며
  실패 시 실제 성공 개수를 추정하지 않는다. 작업 중 부분 실패는
  원본/대상 확인과 기존 닿은 폴더 새로 고침/상태 안내를 유지한다.
- 변경 파일: `app/winui/file_operation_controller.h/.cpp`,
  `app/winui/MainWindow.xaml.h`, `app/winui/m22_transfers.cpp`.
  소스 계약은 `tests/winui/test_file_command_feedback_contract.py`에
  추가했다(신규 로직 실행 증거는 아님).
- 사용자 명시 지시에 따라 **빌드·GUI·시각 검증 및 계약 테스트 실행
  전부 생략**했다. 코드 반영만 확인했으며 Windows 실행·충돌 경합
  수용은 NOT TESTED다. Release/GUI PASS, 부분 전송 성공 수 또는
  배포 준비 완료로 해석하지 않는다.
- 종료 잔류 G01 진단 대기, 사용자 중단 G07 및 제외 G03~G05는
  그대로다. 다음 개발은 사용자가 지시한 범위에서 독립적으로 진행한다.



## 2026-10-21 L10 빈 공간 메뉴 보기·정렬 확장 (검증 보류)

- 기준 main `b8541261`. `e8781489`에서 `m22_transfers.cpp`의
  빈 폴더 영역 우클릭 메뉴를 도구 모음의 보기 5종(자세히·목록·작은/
  중간/큰 아이콘), 정렬 8종(이름·유형·크기·수정일 각각 오름차순/
  내림차순)으로 확장하고 현재 모드에 `ToggleMenuFlyoutItem.IsChecked`
  표시를 추가했다. 기존 `UpdateView`/`UpdateSort`를 재사용하고,
  WindowTab identity·패널·PaneTab·탐색 route 검증을 일반 메뉴 항목과
  체크 메뉴 항목이 공유하도록 했다. `filesystemPaths` 인덱스 범위
  방어도 추가했다.
- `3977370b`에서는 선택 항목이 없는 Shift+F10이 파일을 먼저
  선택하라는 안내 대신 동일한 빈 영역 메뉴를 연다. 선택된 파일이
  있으면 기존 파일 컨텍스트 메뉴를 유지한다.
- `90465fbb`에서는 `test_external_context_contract.py`의 기존
  위치 인자 없는 우클릭 함수 문자열을 실제 새 코드에 맞게 수정하고
  체크 상태·5/8모드·Shift+F10 소스 계약을 추가했다.
- **사용자 지시에 따라 테스트 실행, 빌드, GUI 및 시각 검증은 하지
  않았다.** 소스 변경이 main에 반영된 사실 외 기능·픽셀 수용
  증거는 없으며 NOT TESTED로 유지한다. 기존 정렬 저장 범위와
  Shell/파일 작업 로직, 사용자 제외 G03~G05 및 중단 G07은 보존한다.

## 2026-10-21 L10 우클릭 메뉴 이미지 참고 구현 (검증은 사용자 지시 시)

- 최신 작업 시작 기준: `72358016`; 2026-10-21 사용자가 제공한 두 메뉴
  이미지를 새 L10 표시 구조의 참고로 받아 진행했다.
- 제품 경로: `MainWindow.xaml.h`, `m22_transfers.cpp`에서
  앱 파일 우클릭 메뉴와 빈 공간 우클릭 메뉴를 구분한다. 파일/폴더 메뉴에는
  열기, 폴더만 새 탭에서 열기, 잘라내기·복사·이름 바꾸기·휴지통 이동,
  반대쪽 패널 보내기 하위 메뉴와 끝의 '추가 옵션 표시'를 둔다.
  빈 공간에는 보기·정렬 기준 하위 메뉴, 새로 고침, 붙여넣기,
  새 폴더를 제공한다. 아이콘은 기존 WinUI FontIcon, 구분선과
  WinUI 테마 메뉴를 사용한다.
- 우클릭과 Shift+F10은 앱 메뉴를 열며, 사용자가 **추가 옵션 표시**
  를 선택한 경우에만 기존의 격리된 Windows Shell 확장 메뉴를 연다.
  기존 단일/다중 선택 유지, 경로/가상 공급자/확장 메뉴 제한과
  파일 작업 컨트롤러는 변경하지 않는다.
- 지연 메뉴 명령은 WindowTab identity, 좌우 패널, PaneTab, 탐색 route,
  논리 항목 선택 또는 빈 배경 컨텍스트가 동일한 경우에만 실행한다.
  스크린 좌표를 하드코딩하지 않고 `RightTapped.GetPosition`과
  `FlyoutShowOptions.Position`으로 실제 클릭 지점을 전달한다.
- 변경 커밋: `27ae9122`, `1a14c9e0`, `39977f37`, `746a1fc5`,
  `99186d01`, `a68cae81`, `737b1f2c`, `29574965`.
  이전 즉시 Shell Helper 실행을 전제로 했던 검사 소스는
  `6b271223`, `777d8714`, `d876034d`에서 새 진입 경로로 갱신했다.
- **범위 한계:** 코드를 GitHub main에서 읽어 반영 여부만 확인했다.
  빌드·GUI·시각 검증 및 계약 테스트 실행은 사용자가 명시 요청하지 않아
  **모두 NOT TESTED**다. 따라서 첨부 이미지와의 픽셀 일치,
  열림 위치·보조 메뉴/키보드 초점·테마 화면 수용을 주장하지 않는다.
  이미지와 다를 경우 사용자 요청 범위에서 후속 수정한다.
- 후속 개발은 EP06 부분 완료/건너뛰기 결과 계약 또는 필요한 L10 메뉴
  명령 지원 범위를 좁혀 진행한다. G01 종료 원인은 미확정이고
  G07 중단 및 G03/G04/G05 제외는 유지한다.



## 2026-10-21 EP11 기본 앱 열기 — 연결 상태·오래된 요청 처리 보강

- 기준 `15563803`에서 EP11 단위 코드 수정. `67f094c4`에서
  `FileOpenController`가 Windows `Launcher::QueryFileSupportAsync` 결과의
  `AppNotInstalled`/`NotSupported` 및 `AppUnavailable`를 구분한다.
  `Unknown` 또는 지원 조회가 예외로 실패하면 기존
  `LaunchFileAsync` 결과로 판단한다. 자동 기본 연결 설정 변경이나
  새로운 실행 파일/가상 Shell 항목 활성화는 추가하지 않았다.
- `c84ba31b`에서 메인 창에 기본 앱 없음·앱 사용 불가·시간 초과 및
  일반 실패의 안내를 구분했다. `585b1cf3`에서 현재 pane/tab/route가
  이미 달라진 열기 작업의 ticket을 무효화하고 pending 요청을 취소한 뒤
  새 요청을 허용한다. 같은 컨텍스트의 중복 요청은 Busy로 막는다.
  이는 이미 OS로 넘어간 외부 앱 실행을 소급 취소한다는 뜻이 아니다.
- `6e0c9af6`에서 비동기 호출 순서, 15초 제한, 오래된 콜백 차단 및
  명시적인 연결 상태 피드백에 대한 **소스 계약**을 추가했다.
  **사용자 지시대로 계약 테스트 실행, Release 빌드, 실제 GUI, 전후
  화면 검증은 수행하지 않았다.** 모두 NOT TESTED이며 새 제품 동작의
  수용 또는 배포 적합성을 주장하지 않는다.
- 다음 코드 개발 후보는 L10 앱 자체 명령 메뉴 또는 EP06 일부 작업
  건너뛰기/결과 요약으로, 별도 논리 단위에서 다룬다. 간헐 종료 위험
  G01은 원인 미확정, G07은 사용자 중단, G03~G05는 사용자 제외를 유지한다.



## 2026-10-21 EP06/L10 구현 — 빌드·GUI·시각 검증 보류 (사용자 지시)

- 기준 main은 직전 `5ba90042`. 제품 코드 변경 `612e2fdc`(EP06),
  `05175d29`(L10) 및 회귀 계약 추가 `9ff69c2f`, `88f4a446`을
  순차적으로 main에 반영했다. 기존 비동기 파일 작업, Windows
  Shell 보조 프로세스, 복사·이동·휴지통 안전 정책은 그대로다.
- EP06: 휴지통·동명 파일 확인 단계에서 사용자가 취소할 때
  `StartStatus::Cancelled` 안내를 표시한다. 실제 전송 도중 취소
  (`report.aborted`/`ERROR_CANCELLED`)와 다른 오류를 구분하며,
  일괄 전송은 트랜잭션이 아니므로 이전 항목이 이미 처리됐을 수 있다는
  경고와 닿은 폴더의 갱신 로직을 보존한다.
- L10: 기존의 격리된 외부 Windows 메뉴와 다중 선택 시 속성만 허용하는
  정책을 유지하면서, 메뉴 시작 안내와 금지 명령 결과(`code==65`),
  속성 창 종료 미확인(`code==69`)을 구별해 안내한다.
  앱 자체 우클릭 메뉴의 시각·레이아웃 전면 교체는 수행하지 않았다.
- **2026-10-21 명시적 사용자 지시:** 빌드, GUI 및 시각 검증은
  사용자가 따로 지시할 때만 수행한다. 프로젝트별 `AGENTS.md`
  지침 `fca36be8`에 기록했다. 수정 내용을 읽어 보존 범위를 점검했으나,
  회귀 계약의 실행, Release 빌드, 실제 GUI·화면 비교는
  **전부 NOT TESTED**이며 신규 제품 기능 수용 PASS를 주장하지 않는다.
- 다음 개발 후보: 요구된 L10 앱 자체 공통 명령과 외부 메뉴의 사용성
  구분, EP06 건너뛰기·부분 작업 정책, EP11 기본 앱 연결 실패·중복 요청.
  사용자 제외 G03~G05, 중단 G07 및 원인 미확정인 G01 종료 잔류는 보존한다.



## 2026-10-21 EP01/L01·L03·L09 기본 사용성 개발 (검증 최소화)

- 기준: 제품 `main` `8402d318`, 변경 순서 `8f86f587` → `1ce0daba` → `25cb91ce`.
  G01 종료 잔류는 별도 OPEN이며 2026-10-21 덤프 수집 준비 결과를 보존한다.
- EP04/L03: `file_detail_controller.cpp`에서 등록된 Windows 파일 유형 이름을
  확장자 설명 뒤에 다시 붙이지 않고, 유형 열에 등록 이름만 표시한다.
  등록 유형이 없으면 기존 확장자 대체 문구를 유지하고 Shell 항목의
  제공자 유형·아이콘·미리보기 처리 경로는 변경하지 않았다.
- EP01/L01: `MainWindow.xaml.cpp`의 기존 PreviewKeyDown 경로에
  Alt+Left/Right/Up을 추가했다. 현재 활성 패널의 기존 뒤로/앞으로/
  상위 이동 핸들러를 재사용한다. 편집기·메뉴·대화 상자의 키 입력 경로,
  Ctrl/Shift 조합은 건드리지 않는다.
- EP06/L09: `m21_commands.cpp`에서 이름 변경 시작 및 확정 시
  파일 또는 폴더 하나만 선택하도록 검사하고, 상태 표시줄에 편집
  대상 이름과 Enter/Esc 안내를 표시한다. 기존 F2 확장자 제외
  선택·비동기 파일 작업·사용자 데이터 보호 처리는 변경하지 않았다.
- **검증 상태:** 해당 파일의 수정 코드와 `main` 반영은 읽기 전용으로
  대조했다. 사용자 요청에 따라 Windows Release/GUI/픽셀 비교 및
  전체 테스트는 **실행하지 않았다**. 따라서 기능·시각 수용은 NOT TESTED이고
  마지막으로 수용된 이전 바이너리의 결과를 신규 변경의 PASS로 확대하지 않는다.
  다음 추가 작업은 이 세 항목을 다시 설계하기보다 사용 중 재현되는 문제를
  기준으로 최소 수정한다.
- 사용자 제외 G03/G04/G05, 사용자 중단 G07은 재개하지 않는다.
  L08의 사용자 수동 커서 정상 보고와 자동화 실패도 각각 보존한다.


## 2026-10-21 최신 인계 — G01 소유 덤프 수집 경로 준비

- tests/winui/owned_process_dump.py를 추가하고 shortcut GUI 종료 타임아웃에
  연결했다. 원래 Popen 핸들/PID/실행 파일을 검증하고 읽기 전용에 가까운 제한된
  핸들만 별도 수집기에 상속한다. 수집 제한 10초; 원래 종료 실패를 PASS로 바꾸지 않는다.
- 실제 합성 helper 정지 시험에서 4개 thread/context/stack 수집, 대상 생존,
  기존 소유 복구·정리·설정 보존을 확인했다. 최초 unused-slot 파서 오류를 수정했고
  표준 하네스 51개·관련 소스 16개·정적 검사 PASS. 제품 구현/빌드/UI 변경 없음.
- 실제 WinUI 종료 실패 훅 실행·심볼 스택 분석은 아직 없다. G01 원인/해결을
  주장하지 않는다. 다른 소유 프로브는 다음 필요한 신규 실행 전에 같은 수집기를
  연결할 수 있다. 이미 수용한 GUI를 동일 조건으로 재실행하지 않는다.
- 원시 덤프는 ignored logs/의 소유 증거에만 보존하고 commit/upload하지 않는다.
  합성 시험 덤프는 정리했다. 전역 WER·보안 설정·디버거 설치를 바꾸지 않았다.
- 전체 해시·증거·한계는 CURRENT_STATUS.md 최신 G01 절과 tools/winui/README.md.
  G07 사용자 중단과 G03~G05 제외, G02/G06·세션·G08 수용을 보존한다.
- 사용자가 요청한 대로 이 완료 단위도 검토 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G08 helper 계측 도구·표준 검증 복구

- 로컬 합성 폴더의 native helper 페이지 계측 도구를 추가했다. 200개 사전 시험 후
  8,000개/8페이지를 읽어 항목·내용·설정 보존과 정리 PASS. 첫 페이지 169.320 ms,
  페이지 합계 1,458.497 ms. GUI/정렬/색인/20k·25k 성능으로 확대하지 않는다.
- 설치된 tests 패키지 때문에 표준 unittest 경로가 실패하는 문제를 명시 파일
  로더로 복구했다. 표준 하네스 43개·관련 Shell/streaming 19개·실제 helper 복구/
  정리 회귀 및 정적 검사 PASS. 제품 구현/바이너리는 바꾸거나 다시 빌드하지 않았다.
- 재현 명령과 전체 SHA/측정 범위는 tools/winui/README.md 및 CURRENT_STATUS.md.
  동일한 측정을 성공 확인 목적으로 반복하거나 지원 상한을 임의로 높이지 않는다.
- 사용자는 G07 실제 IME 시험을 중단했다. 자동 재개하지 않는다. 중단 정리 당시
  PID 15472 창 없는 프로세스 잔류와 소유-only 종료를 기록했다. 스택 미확보,
  원인 미확정이며 G01 종료 위험은 여전히 열려 있다. 실제 재발 시 스택을 확보한다.
- G02/G06·구형 세션 수용과 G03~G05 제외를 보존한다. 새 GUI/시각 수용 없음.
  완료 단위마다 바로 push하라는 사용자 지시를 유지한다.

## 2026-10-21 최신 인계 — G01 구형 세션 호환 확인

- ebe26cf9로 v4 저장기를 v3으로 오판하던 회귀 검사를 복구·push했다.
  실제 Release 네이티브 41개와 관련 소스 15개 PASS. 제품 구현 변경 없음.
- 같은 EXE 78fb331f...로 실제 구형 v1/v2/v3 기본 실행 복원과 작업 공간의 명시
  v4 저장을 확인했다. 좌우 탭·선택·정렬, 버전별 표시 옵션과 Back 히스토리를
  저장 결과의 독립 디코딩으로 확인했고 세 실행 모두 정상 종료 0·원본 불변이었다.
- 구형 세션 실측 공백은 위 범위에서 닫는다. 이전의 구형 세션 미검증 문구는
  이 수용 전 기록이다. 정확한 전체 해시·범위는 CURRENT_STATUS.md 최신 G01 절.
- G01 간헐 종료 위험은 여전히 원인 미확정이다. 실제 재발 때 네이티브 스택을
  확보한다. 정상 실행을 반복하거나 추측한 종료 코드를 추가하지 않는다.
- G02/G06 완료 기준선과 G03~G05 제외는 유지한다. 제품 픽셀 변경 없이 Dark
  복원 화면만 검토했으며 전체 시각 PASS를 주장하지 않는다. 소유 앱 잔류 없음.
- 이번 결과 문서도 사용자 지시에 따라 완료 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G02 남은 로컬 검증 완료

- main `44d770ee`와 origin/main 일치를 확인했고 중앙 최신 CI는 이전 `7ac35a06`의
  source PASS임을 구분했다. 현재 수용은 실제 로컬 Computer Use 결과다.
- 제품 변경·재빌드 없이 EXE `78fb331f...`로 새 격리 PID 20760을 실행했다.
  시작 포커스부터 Tab 39회 순환, 역순 이동·F6·주소/검색·정렬 메뉴 복귀 및 재열기,
  정상 Alt+F4 exit 0·사용자 설정과 합성 파일 12개 불변을 확인했다.
- G02 시작/메뉴의 미완료 게이트를 해당 로컬 범위에서 완료했다. 아래 G02 순회 대기
  내용은 과거 기록이며 다시 실행할 지시가 아니다. G06 완료 증거도 그대로 보존한다.
- 현재 상태·시각 범위·전체 해시는 CURRENT_STATUS.md와 UI_UX_AUDIT.md 최신 절.
  문서만 갱신하며 추가 소스 검사·빌드나 새 기능을 자동 시작하지 않는다.
- G01 간헐 종료 위험은 해결 주장 없이 유지한다. 실제 재발 때만 네이티브 스택을
  확보하고 동일 조건 반복/추측 수정은 피한다. G03~G05 제외는 유지. 소유 앱 잔류 없음.
- 사용자 지시에 따라 이 완료 기록도 검토 후 바로 커밋·push한다.

## 2026-10-21 최신 인계 — G06 포커스 회귀 검증 완료

- 빌드 사전 점검은 `b02c51a6`으로 main에 push 완료. 사용자는 이후에도 검증된
  논리 작업 단위가 끝나면 바로 커밋·push하도록 승인했다.
- G06: `RefreshTabs()`의 Clear/recreate를 기존 TabViewItem 재사용으로 수정했다.
  제품 blob `f5ae9266...`, EXE `78fb331f...`; Release·관련 소스 25개와
  실제 두 작업 공간×좌우×두 탭 방향키+Enter·Dark 전후 검토·exit 0 확인.
  사용자 설정과 12개 합성 파일 불변. 자동 GUI 회귀 확장은 정적 검사만 완료했다.
- 다음 미완료 범위는 G02의 시작부터 연속 순회·메뉴 복귀를 정상 종료까지 확인하는
  좁은 검증이다. 이미 수용한 G06 네 영역이나 빌드를 이유 없이 반복하지 않는다.
- G01: 기준 바이너리 첫 종료의 0xC0000005와 후속 정상 종료를 모두 보존한다.
  이번 탭 수정이 종료 위험을 해결했다고 주장하지 않는다. 새 제품 기능을 섞지 않는다.
- 캡처가 검게 나왔던 도구 문제는 사용자 바탕 화면 복귀 및 JS 캡처 세션 재연결로
  복구했다. 검은 화면 구간은 기능/시각 판정에서 제외했다. 남은 소유 앱은 없다.

## 2026-10-20 G02/G06 후속 — 확인된 GUI 범위 보존

- main `db10ef42`, 동일 기존 EXE `eb89f47d...`로 소유 실행 1회, exit 0.
  두 작업 공간×좌우×두 폴더 탭 이름과 추가 대상, B의 닫기 대상 및 A 보존을 확인했다.
  F6/실제 파일 선택, 목록 Tab·Shift+Tab, 주소→검색, 정렬 메뉴 Escape 후 복귀·
  Enter 재열기, A 왼쪽 폴더 탭 방향키+Enter 왕복도 정상이다. 사용자 설정·파일 불변.
- 전체 G02/G06 PASS는 아니다. 다음에는 초기부터 연속 키보드 순회와 네 영역 전체의
  포커스만 확인한다. 도구 focused_element 값은 화면과 불일치하므로 단독 판정 금지.
  입력 간섭·가림이 있던 시도는 제외했다. 이미 확인한 행렬이나 빌드는 반복하지 않는다.
- 제품 코드·새 빌드 없음. 전체 시각 수용과 기존 간헐적 종료 위험은 별도 보존한다.

## 2026-10-20 G01 후속 진단 — 종료 잔류 재현 안 됨

- 최신 main `08e066a1`, 기존 EXE `eb89f47d...`와 같은 소유 v4 세션을 재사용했다.
  UIA 텍스트만 확인한 복원 실행과 화면 캡처·두 번째 탭 전환을 추가한 실행이
  모두 exit 0, 원본 사용자 설정 불변이었다. 새 빌드·제품 수정·전체 GUI 실행 없음.
- 이전 종료 잔류 원인은 미확정이다. 해결 완료나 G01 전체 PASS로 바꾸지 않는다.
  동일 조건 반복 대신 실제 재발 시 소유 PID의 네이티브 호출 스택을 확보한다.
  현재 남은 테스트 앱은 없다. 추측한 강제 종료 코드를 추가하지 않는다.
- 다음 별도 기능 과제는 G02/G06의 좁은 키보드·UIA 점검이다.

## 2026-10-20 G01 최신 재개 결과 — 정상 종료 게이트 보류

- `4bdde290` 로컬 Release 한 번 빌드 후 실제 소유 GUI에서 폴더 탭 추가·전환·
  닫기, 좌우/WindowTab 독립 정렬, v4 저장·재시작 후 두 탭 정렬 복원을 확인했다.
- 최초 실행 exit 0. 복원 실행은 창이 닫힌 뒤에도 60초 이상 프로세스가 남았다.
  대기 체인은 `csrss.exe` 방향 ALPC wait이며 cycle은 보고되지 않았다.
  소유 PID만 정리한 최종 exit는 -1. 사용자 설정·합성 파일은 불변이다.
- G01 최종 GUI PASS로 승격하지 않는다. 다음 작업은 저장 세션 복원 후 종료의
  OS/앱 생명주기 경계를 좁히는 것이다. 이미 확인한 정렬 시나리오와 전체 GUI를
  반복하거나 근거 없이 Application.Exit/강제 종료를 제품 해결책으로 넣지 않는다.
- 제품 변경 없음. 정확한 EXE/범위/한계는 CURRENT_STATUS.md 최신 G01 절 및
  ignored `logs/g01-local-20261020/result.json`에 기록했다. 구버전 세션 실측은 별도 미검증.

## 2026-10-20 최신 사용자 관찰 — 이후 재개 시 우선 적용

- 사용자가 직접 열 경계에 마우스를 올렸을 때 조절 커서가 정상 표시됨을
  보고했다. 아래 자동 입력 실패를 제품 전체의 커서 미동작으로 일반화하지 않는다.
- 사용자 관찰의 정확한 바이너리·열/패널·환경은 기록되지 않았다. 사용자 실측
  근거와 기존 exact-SHA 자동 실패를 함께 보존하며 전체 L08 PASS로 확대하지 않는다.
- 커서 제품 수정은 중단한다. 자동 입력과 실제 입력의 차이를 먼저 분류하고,
  이미 실패한 후보를 다시 빌드하거나 엄격한 커서 assertion을 약화하지 않는다.
- 이번 로컬 재개에서 추가했던 이벤트 대상 임시 진단은 소스에서 제거했다.
  그 진단을 위한 로컬 빌드 출력은 제품 수용/배포 증거로 사용하지 않는다.
- 다음 제품 작업은 이미 구현된 G01 및 G02/G06의 남은 GUI 수용을 마무리하는
  순서다. 아래 원격 요청 슬롯의 복원/승인 경계와 사용자 제외 조건을 유지한다.

## 기준과 사용자 범위

- G01 제품 변경은 [`5c5298a3`](https://github.com/tngkrwlsmd/flyExplorer/commit/5c5298a3e126542b0118c5a670ac982cd5ed1718)에 반영됐다.
  L08 커서 검증의 당시 제품 코드는 `099cfb7125f9`였다. 재개할 때 최신 `main`,
  최근 10개 커밋, 중앙 CI 및 `CURRENT_STATUS.md`를 다시 확인한다.
- 작업 순서: **1) L08 커서/드래그 검증 → 2) G01 정렬 상태 독립화
  → 3) 일상 파일 사용성 개선**. 완료되지 않은 앞 단계를 PASS로 처리하거나
  다음 단계의 코드를 섞지 않는다.
- 실 OS 125/150/200% DPI, F04/F05 High Contrast/Narrator 음성,
  실제 USB/SMB/UNC 시험은 **USER-EXCLUDED**. 실행·권유·출시 차단 금지.
  사용자의 기존 앱·설정·파일을 건드리지 않는다. PR 생성 금지.

## 1. L08 진행: Build PASS, GUI/커서 FAIL

- **2026-10-19 후속 실제 GUI 결과:** 중앙 Windows
  [#39247119043](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39247119043)에서
  소유 앱의 UIA hit 대상은 `LeftNameColumnResizeThumb` (`Group`)였지만
  실제 커서 `65539`는 기본 arrow `65539`였으며 좌우 조절용 커서 `65553`와 달랐다.
  GUI assertion은 **FAIL**이다. 실행 래퍼가 `gui-pass/exit_code=0`을
  잘못 기록했지만 Python traceback과 필수 마커 누락으로 이를 거부했다.
- **후속 격리 후보:** 기존 앱을 중단하거나 소스 `main`을 수정하지 않고
  `MainWindow.xaml.cpp/.h` 두 파일의 `WM_SETCURSOR` 보정 후보를 별도
  Windows 테스트 작업공간에 적용했다. 중앙
  [#39248666199](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39248666199)에서
  source-contract와 Release 빌드는 **PASS**, GUI는 동일한 기본 arrow 커서로
  **FAIL**이었다. 이 후보를 제품 코드에 도입하지 않는다.
- **검증 도구 정비:** `ffd9027c`에서 L08 Python GUI 예외를 명시적으로
  `OWNED_DETAIL_COLUMN_RESULT FAIL`로 출력하도록 변경했다.
  `3b308357`에서 `python tools/winui/run_checks.py gui --area column-resize
  --configuration Release` 집중 경로를 추가했고, `81cab8b6`에서 관련
  소스 계약을 보강했다. 이후 `ed68a40a`와 `1f7ad3ca`에서는
  전용 실행 결과에 정상 종료 코드가 있더라도 명시적 PASS, 세 열의
  실제 변경 마커, 원본 설정 불변 마커가 모두 존재하고 traceback/FAIL이
  없어야만 통과시키도록 강화했다. 이 변경은 테스트 실행기의 안전 판정
  개선이지 커서 문제 해결은 아니다. 기존 엄격한 커서 assertion과 세 열 드래그,
  기존 사용자 설정 불변 조건은 그대로다. **이 새 경로의 실제 Windows 실행은
  아직 NOT TESTED**다. 전체 GUI 통과로 승격하지 않는다.
- **제어 상태:** 마지막 조회 시 `personal-control-plane`의
  `requests/remote-shell/windows-vm.json`에 완료된 과거 후보 요청이 남아 있었다.
  실행은 모두 종료됐지만 해당 슬롯의 idle 복원 GitHub 쓰기는 안전 검사에서
  차단됐다. 다른 수단으로 우회하거나 그 슬롯을 덮어쓰지 않는다.
  승인된 정상 복원 가능 상태가 확인된 뒤에만 Windows 작업을 재개한다.
  이후의 cursor 수정은 실제 XAML 입력 전달·네이티브 창 경계의 증거가 있을 때만 선택한다.


- **2026-10-19 후속 진단 준비:** [`552fe9c5`](https://github.com/tngkrwlsmd/flyExplorer/commit/552fe9c58787a64aebf3f126a11f933acb50b07d)에서
  `tests/winui/test_owned_column_resize_gui.py`의 엄격한 커서 assertion 직전에
  소유 앱 위치의 UIA hit 정보와 native active/arrow/sizewe 커서 핸들을
  `COLUMN_RESIZE_HOVER_PROBE`로 출력하게 했다. 실패를 성공으로 바꾸거나
  기존 커서 assertion/드래그 조건을 우회하지 않는다.
- 독립 중앙 Windows [#39244437409](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39244437409)는
  정확한 위 `main` SHA의 신선한 clone에서 **Python `py_compile` PASS**
  (`L08_PRECHECK_PYTHON_SYNTAX_PASS`)를 기록했다. GUI를 실행하지 않았고
  **제품 커서 동작/기능 GUI/시각 수용은 여전히 FAIL/NOT TESTED 범위 그대로**다.
  단일 Remote Shell 요청 슬롯은 완료 후 idle로 복원했다.
- [`0d3f5f4`](https://github.com/tngkrwlsmd/flyExplorer/commit/0d3f5f455af7342349f9dca8bda3142af1aef607)는
  hover 대상이 소유 앱 프로세스와 다를 경우 외부 창 제목을 수집하지 않도록
  로그를 제한한다. 이 **최신 테스트 Blob**의 정확한 Windows Python 구문 검사는
  [#39245014398](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39245014398)에서
  `L08_CURRENT_SYNTAX_PASS`를 확인했다. GUI 및 제품 변경은 없음.
  Remote Shell 요청 슬롯은 검증 후 다시 idle로 복원했다.
- 다음 단계는 **허용된 실제 로그인 GUI 경로**에서 새 probe의 UIA hit target과
  실제 cursor 핸들 출력을 확인해, WinUI `ProtectedCursor`가 수평 핸들에
  적용되지 않는 원인이 hit-test 또는 메시지 전달 중 어디에 있는지 먼저
  분류하는 것이다. 승인 차단이 지속되면 우회하지 않는다. 기존 드래그
  경계·실패 검증을 유지하고 원인 확인 전 HWND subclass 등의 변경은 금지한다.

- 새 `main`의 `DetailColumnHandle`과 드래그 코드 자체는 이미 구현됐다.
  정식 테스트 소유 Release 빌드 [#39221721375](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39221721375)
  PASS; EXE `9a9056d94c18d6f662a7b8991f2704d877ae0bee746b9ece6b4e037bbdb9eaf6`.
- 첫 실제 GUI [#39222335628](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39222335628):
  `test_owned_column_resize_gui.py`의 첫 hover 수평 커서 assertion에서
  Python Traceback이 발생했다. 외부 Actions SUCCESS/worker exit=0만 보고
  PASS라고 판단하면 안 된다. 필수 GUI 통과 마커는 없었다.
- [#39223067075](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223067075)
  진단에서 **커서 assertion을 의도적으로 우회한 경우에만** 세 개 열 경계의
  실제 물리 마우스 이동과 너비 증가, `RESIZE_MOVE`를 관찰했다.
  이 실행은 수용 근거가 아니다.
- [#39223454976](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39223454976):
  호버 위치가 `LeftNameColumnResizeThumb`인 상황에서 커서 `65539`는
  stock IDC_ARROW와 같고 IDC_SIZEWE `65553`와 달랐다.
  **현행 L08 cursor 동작은 수용 실패.**
- 임시 `DetailColumnHandle.cpp` PointerEntered/Moved+Win32 SetCursor 후보는
  헤더 수정 후 격리 Release [#39224349062](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224349062)
  PASS (EXE `df5e964b8e60a064843f9251642711c5c067ca232e5c688b406ec7bcb52b076c`)
  였으나 엄격한 실제 GUI [#39224659050](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39224659050)
  에서 같은 cursor assertion **FAIL**. 본 후보는 `flyExplorer/main`에
  푸시하지 않았다. 반복만 하는 빌드·테스트는 금지.
- 표준 WinUI `ProtectedCursor`가 포인터 over 상태에서 적용되는지,
  실제 이벤트 전달·캡처 경계 및 native WM_SETCURSOR 경계를 추가로
  분석하고 최소 수정 후보를 결정한다. 프로세스·시스템 전역 커서나
  복잡한 HWND subclass를 검증 없이 추가하지 않는다.
- 수용 기준: 테스트 소유 앱에서 실제 3개 열의 hover 수평 커서,
  드래그→최종 너비, release, body 이동 시 기본 커서 복귀, 좌우 패널
  영향 범위, 정상 종료·사용자 설정 불변을 기록한다. GUI 판정은
  명시적 통과 마커+오류 출력 부재로 한다. 픽셀 시각 검토는 별도.

## 2. G01 진행: 코드 및 Release PASS, 실제 GUI 수용 대기

- [`5c5298a3`](https://github.com/tngkrwlsmd/flyExplorer/commit/5c5298a3e126542b0118c5a670ac982cd5ed1718)
  에서 WindowTab당 좌우 각 PaneTab의 정렬 스냅샷을 도입했다.
  새 PaneTab 기본 이름 오름차순, 탭 선택/닫기 시 정렬 복원,
  private session schema v4 기록 및 v1~v3 읽기 호환을 구현했다.
  R1 정렬 체크와 기존 F05 그룹 상태를 변경하지 않았다.
- 7개 패치 Git Blob의 동일성을 격리 Windows 소스에서 확인한 뒤,
  `test_session_coordinator_contract.py`와 GUI 스크립트 문법 검사,
  정식 Release 빌드를 [#39230031402](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39230031402)
  에서 PASS했다. 바이너리 해시
  `368cc3c2b74f17845ec06e4db3cfc31687040eef78f878c8faba6b7b32df6fa1`.
- GUI 시험의 Windows 실행 승인 단계가 안전 제어로 **차단됐다**.
  다른 경로로 우회하지 않았고, **실제 GUI·시각·세션 복원은 NOT TESTED**다.
  승인 가능한 정식 수용 경로가 명확해지기 전까지 PASS로 승격하지 않는다.
- 해당 변경의 상세 원인·테스트 범위는 최신 `CURRENT_STATUS.md`,
  `NEXT_DEVELOPMENT_GOALS.md`를 따른다.

## 3. 일상 파일 사용성 — G02/G06 소스 개선 반영, GUI 미검증

- 최근 `main`의 F2 파일명 기본 이름 선택(`b1cddbbb`), 선택별 명령
  활성 정책(`81b8bc26`), stale-context 파일 작업 결과 안내
  (`0dfbd31a`)는 **이미 코드에 반영**되어 있다. 이번 재개에서 중복
  변경하지 않았으며 실제 GUI 수용은 별도로 필요하다.
- G02 F6 포커스 결과 분기 `1c768b3` 및 소스 계약 `05266a4` 반영:
  반대 패널 파일 목록의 `Focus()` 실패 시 성공한 것처럼 알리지 않는다.
- G06 접근성 이름 `8480403`, `c290ff6`, 소스 계약 `de2c687`
  반영: 제목 표시줄 작업 공간(WindowTab)과 활성 패널의 폴더 탭
  생성·닫기(PaneTab)를 사용자에게 구별한다. 레이아웃과 단축키 불변.
- 이어서 `1a024da`에서 좌우 PaneTab **항목별** UIA 이름,
  `d19c359`에서 활성 패널별 생성·닫기 버튼 이름을 적용했다.
  `e34b95b`, `ea2d08b`에 해당 계약을 추가했다.
- 정확한 소스 `11915f42bd6d85d2001653dba0a2aa30e0141532`로
  새로운 test-owned Windows checkout의 단축키 소스 계약·탭 소스 계약
  및 실제 Release 빌드 [#39239758606](https://github.com/tngkrwlsmd/personal-control-plane/actions/runs/39239758606)
  **모두 PASS** (`exit=0/0/0`). EXE SHA-256
  `967db8f70dce972274786c177753de1030d10c2908fb1fe6758fcd5f0292943b`.
  범위는 **컴파일과 source 계약**이며 실제 GUI/UIA·시각 픽셀 수용 아님.
  Remote Shell 요청 파일은 검사 후 idle로 복원했다.
- 현재 Desktop Commander 호스트는 offline. 기존 GUI 실행 승인
  차단의 우회는 하지 않았으므로 G02/G06 기능 GUI는 미검증으로 유지한다.
- 추가 키보드 처음-끝 왕복(G02), F2 실제 선택 범위 및 명령 활성·파일
  작업 결과 GUI 검증, L08 커서와 G01 실제 수용은 계속 열린 상태다.
  이전 사용자 제외 항목 3종은 이 작업의 하위 시험으로 다시 등록 금지.



## 통제/증거 정리

- Windows 검사는 중앙 `personal-control-plane`의
  `windows-vm` 전용 Remote Shell을 이용했다. 해당 요청 파일은
  검사 뒤 idle 명령으로 복원했다.
- SYSTEM 전용 테스트 소유 작업 폴더
  `C:\ProgramData\personal-control-plane\central-ci\f67e51c3f71a47e39f02390c3a395013`
  에 후보 바이너리/로그/일부 실패 fixture가 증거로 남아 있을 수 있다.
  이것은 `main` 기준 소스·실행 파일이 아니다. 임의 전체 정리 금지.
  필요 시 소유 마커·정확한 경로·내용을 확인한 뒤 별도 정리한다.
- 이번 재개에서 G01 제품 변경 7개 파일을 `main`에 반영했다. L08 제품
  코드는 변경하지 않았고, 사용자 제외 시험과 신규 PR을 수행하지 않았다.
  중앙 `windows-vm` 요청 파일은 idle 명령으로 복원했다. 성공한 Actions
  run도 내부 Traceback 또는 PASS 마커 누락을 덮어쓰지 못한다.
