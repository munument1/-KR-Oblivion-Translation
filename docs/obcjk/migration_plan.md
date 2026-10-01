# obCJK backend 설계 및 최소 빌드 계획

## 실행 순서와 완료 조건

1. 별도 프로필의 원본+xOBSE+obCJK 실행으로 메인 메뉴 전 종료를 분리한다.
2. legacy 문자열 복원기를 설계하고 데이터만 대상으로 왕복 검증한다.
3. 작은 UTF-8 ESP를 xEdit MCP로 제작하고 게임에서 표시/저장/재로드를 검증한다.
4. backend를 빌더에 연결하여 별도 output을 만들고 무결성 비교를 통과시킨다.
5. 본편/공식 DLC를 검증한 뒤 UOP/USIP/UODP를 동일 모드로 전환한다.
6. 실제 실행 체크리스트가 모두 통과한 뒤 설치기를 분리한다.

기존 번역/legacy backend를 보존한다. main 병합·릴리즈·Nexus 수정은 실제 게임 테스트 전에는 하지 않는다.

## backend 구조

목표 API는 Unicode 텍스트와 legacy 바이트를 구분하는 명시적 모델이다.

- `--text-backend legacy`: 기본값. 기존 hex를 그대로 사용해 v1.0.4 결과를 재현한다.
- `--text-backend obcjk`: 검증된 Unicode 문자열을 UTF-8로 만들고 종단 NUL 한 개를 붙인다.
- CP949는 비교 실험용 옵션으로만 추가 여부를 결정한다. `obcjk`의 기본 codec과 INI는 하나로 고정한다.
- report에 backend, codec, source CSV hash, effective translation key, codepage 설정, 보존 정책을 남긴다.

빈 Unicode 칼럼을 빈 번역으로 간주하지 않는다. 텍스트 없는 항목은 legacy decoder로 복구하여 **decode → legacy encode가 기존 바이트와 동일한 경우에만** 채택한다. 알 수 없는 글리프/문장부호/잘못된 NUL은 예외와 위치를 보고하고 중단한다. replace/ignore codec이나 임의 ASCII 대체로 통과시키지 않는다.

문장부호나 byte sequence 해석이 모호하면 폰트의 실제 mapping/기존 확정 Unicode 자료와 대조한다. 번역을 다시 생성해서 해결하지 않는다. 특히 424개 QUST/LSCR과 patch completion, prior KR fallback은 Unicode source를 먼저 확보한다.

일반 table의 원문·FormID·EDID·occurrence 매칭, quest stage, final override 순서는 그대로 둔다. 전체 memory의 빈 칼럼을 기계적으로 채우기보다 최종 적용되는 문자열과 provenance를 먼저 확정한다.

## 필요한 코드 변경

| 파일/영역 | 필요한 변경 | legacy 보존 검사 |
|---|---|---|
| `oblivion_korean_codec.py` | 전체 문자열 encode/decode와 모호성/미지원 문자 처리, 현대 한글 전범위 왕복 | 기존 encode_hangul 결과 유지 |
| 새 backend 모듈 | Unicode → target bytes, codec/NUL 정책, source provenance | default legacy bytes 동일 |
| `build_vanilla_overlay.py` | load_translations/menu/quest-loading/final-menu 경로 전부 backend 전달 | v1.0.4와 출력 hash 또는 의미 구조 동일 |
| 코드 내 GMST hex | 사용 중인 항목은 Unicode source와 연결 | 기존 FormID/EDID/값 유지 |
| `build_unofficial_release.py` | prior KR fallback·completion·공식 복원 데이터의 codec 통일 | 원본 패치의 게임플레이 값/스크립트 유지 |
| `assets/menus/strings.xml` | legacy와 Unicode 자산 분리, 선언과 실제 bytes 확인 | 원래 자산 보존 |
| assets/폰트 설정 | obCJK판에 legacy custom fnt/tex를 복사하지 않음, 원본 폰트 경로+시스템 한글 폰트 사용 | legacy 설치 폰트 유지 |
| `OblivionKRBuilder.spec` | 새 모듈/Unicode 자산 포함, backend별 packaging | 기존 EXE 모드 재현 |
| `install.bat`/새 설치기 | obCJK 모드 분리, version/config 검사, DLL 별도 설치 안내 | 기존 설치기 유지 |
| video subtitles | 현재 burn-in 유지, 확인된 별도 runtime 기능이 생기면 별도 옵션 | 확정 SRT 문구/타이밍 유지 |
| 경로 처리 | repo root 탐지, CLI/local config, frozen _MEIPASS 자원 처리 유지 | Windows 사용자 경로 지원 |

프로젝트 내부 경로는 repo 기준 상대경로로 두고 `--data-dir`, `--mo2-dir`, `--obcjk-dir`, `--output` 및 ignored local config를 사용한다. 이번 조사 설정은 `_build/obcjk/research/local_environment.json`에 기록했다. 신규 output은 `output_obcjk/` 또는 `release_obcjk/`이며 구현 시 .gitignore에 추가한다.

## 바이너리 무결성 계약

검증 기준을 두 개로 분리한다.

- 원본→각 backend: 현재 의도된 번역 문자열 변경 및 **821개 메뉴 GMST 추가**를 명시적으로 허용한다. TES4 record count/GRUP size 등 필수 container 갱신은 허용 목록에 기록한다.
- legacy v1.0.4 결과→obCJK 결과: 같은 record/FormID/EditorID 집합을 사용하고 target text bytes만 바뀌어야 한다. record count 동일성을 여기서 요구한다.

검사는 xEdit MCP를 우선 확인했지만 현재 Oblivion은 지원하지 않는다. 이후 사용자가 이번 전환에서 기존 프로젝트 빌더 사용 예외를 허용했다. 해당 경로의 별도 UTF-8 출력과 엄격한 bytes 비교를 사용하며, xEdit 검증과 구분한다. 최신 구현·검증 범위는 [플러그인 시험판 결과](utf8_plugin_test_results.md)에 기록한다.

필수 acceptance 항목:

- 레코드 수/유형/FormID/EditorID, master 목록, 레코드 flags와 비문자열 헤더 동일.
- 모든 서브레코드 순서·종류·개수와 비문자열 값 동일. 예외는 사전에 허용한 container 변경뿐.
- SCPT와 INFO/QUST의 컴파일된 script 및 참조 데이터 동일. 게임별 script 구조를 사용하고 Oblivion에 VMAD가 있다고 가정하지 않음.
- 변경 target은 `(file, record type, FormID, field, occurrence, stage)`로 식별한 문자열 allowlist 내부.
- UTF-8 strict decoding, 문자열 내부 NUL 금지, 종단 NUL 한 개, byte 길이 및 XXXX 확장 길이 처리 정상.
- 압축 레코드의 uncompressed length 정상, 압축 해제 후 비문자열 payload 동일, GRUP bounds/parent 구조 정상.
- BOOK markup, 줄바꿈, `%` 등의 formatting placeholder 및 영어/ASCII 보존.
- CELL/WRLD, 기존 저장 안정성 제외 위치/참조 이름, RACE 음성 경로 정책 유지.

현재 `structure_signature`만으로 위 검사를 통과했다고 보고하지 않는다. report는 수행한 항목/미수행 항목을 구분하고 JSON+Markdown으로 저장한다.

## 최소 테스트 ESP

별도 프로필 `obcjk-isolation`, 원본 영문 master와 원본 기본 폰트, xOBSE 22.13, obCJK UTF8을 사용한다. legacy KR/UOP KR을 섞지 않는다. 프로필/INI/save를 분리하며 기존 세이브는 원본 대신 사본으로만 테스트한다.

ESP는 `ObCJK_KR_Smoke.esp`로 계획한다. 기존 게임플레이 레코드 override를 최소화하고, 테스트별 locator와 원본 값을 manifest에 남긴다. 제작은 xEdit MCP가 해당 Oblivion 모드와 UTF-8 입력/저장 경로를 지원함을 확인한 뒤 진행한다.

| 영역 | 문자열/검사 | 접근 계획 |
|---|---|---|
| GMST UI | `한글 메뉴 확인 (ABC 123) - O'Brien` | 사전 확인한 메뉴 GMST 한 항목을 override |
| 아이템 이름 | `받침 검사: 값·꽃·읽음 (123)` | 테스트 아이템 한 개, locator 기록 |
| NPC 대사 | 일반/긴 문장/두 줄 | DIAL/INFO 최소 구성, voice 부재와 글리프 문제 구분 |
| 주문 효과 | `피해 10 / 지속: 5초 / 적용: 자신` | 표시 대상 텍스트 확인, gameplay 값 불변 |
| 문 목적지 | `-> 목적지`의 조합 표시 | 실제 CELL/WRLD 이름은 영어 유지하고 GMST 조합을 확인 |
| 책 | 한글+영문+괄호+apostrophe+hyphen+긴 문장/줄바꿈 | BOOK markup 유지, UI 경로별 wrap 확인 |

신규 테스트 plugin에서 ASCII/숫자/일반 한글/받침/확장 한글/문장부호/빈 문자열/긴 문장/줄바꿈을 포함한다. 메뉴 한 개부터 시작하여 기능별로 확대한다. 실패하면 직전 성공 조합으로 돌아가 원인을 분리한다.

**현재는 ESP 제작 전 계획이다.** 종료 원인 분리와 xEdit 연결이 아직 완료되지 않아 바이너리나 실행 성공 결과는 없다. 실제 검증 기록은 [obcjk_smoke_test.md](obcjk_smoke_test.md)에 쌓는다.
