# UTF-8 플러그인 시험판 — 2026-10-01

사용자가 기존 프로젝트 빌더의 사용 예외를 허용한 뒤 진행했다. Windows 본PC만 대상이며, `obcjk-unicode` 브랜치와 별도 MO2 테스트 프로필을 사용한다. xEdit MCP의 Oblivion 미지원은 그대로이며 xEdit 검증을 통과했다고 주장하지 않는다.

## 구현

`build_vanilla_overlay.py`에 `--text-backend legacy|obcjk`를 추가했다. 기본값은 `legacy`다. obCJK 모드는 기존 빌더를 별도 임시 폴더에서 실행하고, 그 결과의 번역 문자열만 UTF-8로 변환한다. 기존 원문 매칭·번역 우선순위·821개 GMST 추가 동작을 재사용한다.

UTF-8 출력에는 메뉴 XML, obCJK UTF8 설정, 원본 `.fnt` 경로 안내, 변환 및 빌드 감사 JSON이 들어간다. TheGreatestKorean 폰트 자산은 이 출력에 복사하지 않는다. obCJK DLL은 사용자가 설치한 원본 모드를 사용한다. `--obcjk-ini`로 별도 설정을 제공하거나 기본 Malgun Gothic 설정을 생성할 수 있다. 기존 게임 INI에 쓰는 `--ini` 옵션은 obCJK 모드에서 거부하고 프로필별 원본 폰트 설정을 사용하도록 한다.

```powershell
python build_vanilla_overlay.py --text-backend obcjk --data-dir "<원본 게임 Data>" --output _build/obcjk/utf8-output --video-subtitles off
```

출력 폴더는 비어 있어야 한다. 기존 릴리즈 EXE·설치기는 교체하지 않았다. PyInstaller spec에 필요한 JSON/CSV 자원을 추가했지만 새 EXE의 패키징 및 실행은 아직 검증하지 않았다.

비공식 패치는 설치된 기존 KR 파일을 원본 패치와 대조하여 별도 `build_obcjk_overlay.py`로 변환했다. `build_unofficial_release.py`의 기존 기본 빌드 동작은 유지한다. 향후 비공식 패치 재빌드용 CLI의 직접 backend 연결은 별도 작업이다.

## 기존 번역 기준

공식 본편·DLC의 legacy 재빌드 10개 파일을 설치된 v1.0.4와 비교했다. raw 파일 해시는 달랐지만 압축 해제 후 모든 레코드 헤더·그룹 경로·서브레코드 bytes가 일치했다. 번역 및 게임플레이 데이터 차이는 0개였다. 비교 JSON은 `_build/obcjk/legacy-reference/semantic_comparison.json`에 보관한다.

23개 CSV의 84,349행은 전부 텍스트 복원 검사를 통과했다. 이 수치는 중복 자료를 포함하며 적용 레코드 수가 아니다. 서양 알파벳 시험용 BOOK 2개는 cp1252로, 나머지 4개 문자열의 섞인 CP949 조각은 전체 문자열 해시와 바이트 위치가 맞을 때만 복원한다. [예외 목록](legacy_text_exceptions.json)에 원본 행·레코드·해시·위치와 Unicode 값을 기록했다.

BOOK `0000A2B3`의 `8F B3`는 CP949로 `뤂`에 해당한다. 주변 문장의 기존 오타로 보이지만 이는 문맥에 따른 추론이며, 번역을 다시 쓰지 않도록 그 값을 그대로 유지했다. 인코딩 왕복 성공은 번역 품질 검수를 뜻하지 않는다.

## 파일 검증

최종 결과는 `_build/obcjk/cli-final`, `full-uop`, `full-usip`, `full-uodp`의 `obcjk_validation.json`이다. 초기 중간 출력보다 이 최종 감사 파일을 기준으로 삼는다.

| 범위 | 플러그인 수 | 레코드 수 | UTF-8로 bytes가 바뀐 문자열 필드 | 그대로인 서브레코드 |
|---|---:|---:|---:|---:|
| 본편·공식 DLC | 10 | 1,191,672 | 47,966 | 4,635,558 |
| UOP 및 동봉 ESP | 3 | 86,483 | 6,711 | 364,682 |
| USIP | 1 | 12,901 | 1,491 | 61,032 |
| 비공식 DLC 패치 | 10 | 1,948 | 616 | 19,878 |

`DLCShiveringIsles.esp`는 legacy 빌더가 번역할 필드가 없는 파일이므로 원본을 사용하며 위 10개 출력에 포함되지 않는다. ASCII만 있는 번역은 UTF-8에서 bytes가 바뀌지 않으므로 표의 변경 수와 기존 applied_strings 수는 다르다.

legacy→UTF-8 사이에서 아래 항목을 검사했다.

- 레코드 수·순서·종류·FormID·flags·비크기 헤더, 전체 그룹 경로 및 그룹 수 동일. 빈 GRUP도 유지한다.
- EDID, master 목록, 서브레코드 순서·개수, 허용 목록 밖의 서브레코드 raw bytes 동일.
- 변경 대상은 문자열 allowlist와 정확히 일치하며 UTF-8 strict decode, 내부 NUL 없음, 종단 NUL 한 개를 검사한다.
- 압축 해제 크기, GRUP/레코드 경계, 긴 문자열의 XXXX 확장 길이를 검사한다.
- 기존 구조/스크립트 signature도 비교하며 SCPT와 INFO/QUST script 데이터가 유지된다.
- CELL/WRLD FULL과 RACE FULL은 그대로 유지한다. 한글 위치명은 이번 기본 번역 시험에 넣지 않았다.

최소 ESP는 원본 레코드 override 7개, 변환 문자열 8개로 구성했다. GMST·MGEF·SPEL·BOOK·WEAP·INFO와 INFO의 부모 DIAL을 포함한다. 실제 번역을 사용하며 게임플레이 값은 해당 원본 레코드와 같다. 최종 FULL 파일은 821개 메뉴 GMST를 포함한 기존 legacy 결과와 같은 레코드 집합을 유지한다. 최소 ESP의 새 TES4/잘라낸 그룹 구조는 이 FULL 비교와 다른 의도된 시험 구성이다.

단위 검사 9개가 통과했다. 완성형 한글 11,172개 왕복, 잘린 legacy bytes 거부, 압축 BOOK의 긴 UTF-8/XXXX, 임의 script 변경 거부, 헤더·경계 손상 거부, NUL 거부, 빈 그룹 보존, 해시로 제한한 예외 복원을 포함한다.

## 실행과 미확인 범위

`obcjk-save-test`에서 기본 원본 폰트와 obCJK UTF8/Malgun Gothic을 사용한다. 기존 KR 모드와 원본 비공식 패치는 끄고, 본편·공식 DLC만 먼저 시험한다. MO2의 실제 플러그인 origin도 새 시험판 모드를 가리키는지 확인했다.

최소 ESP의 첫 실행은 MO2 도구가 활성화를 응답한 직후 다시 읽으면서 체크가 풀리는 문제가 있었다. 해당 실행을 ESP 성공으로 세지 않는다. 화면에서 체크한 뒤 `plugins.txt`에 실제로 기록된 것을 확인하고 재실행한 구성에서는 메인 메뉴에 진입했다. 이 동작 차이는 기존 게임 CTD와 구분한다.

그룹 보존 검사를 통과한 최종 파일로 21:14:07(KST)에 다시 실행했고, 종료 없이 한글 메인 메뉴가 표시되는 것을 수분 후에도 직접 관찰했다. 같은 실행의 OBSE 로그에서 obCJK DLL 로드 성공, obCJK 로그에서 `ActiveCodePage=UTF8`와 훅 초기화를 확인했다. 실행 H의 로그는 로컬 `_build/obcjk/utf8-test/run-H-final-full-*.log`에 보관한다. 본편 master SHA256은 `c5ee34660fba087b2edaed96eccfd110b834e6d8a66368b970a15249f64216b4`이며 MO2 시험판과 검증 산출물이 일치한다.

자동 마우스·키 입력이 Oblivion의 메뉴 선택으로 안정적으로 이어지지 않았고 사용자가 외출 중이므로 새 게임·인벤토리·책·대사·주문 화면·저장/재로드는 보류했다. 메인 메뉴 진입을 실제 플레이 또는 저장 성공으로 확대하지 않는다. 이후 사용자 요청으로 UOP/USIP/UODP와 한글 위치명도 함께 켰다. [후속 적용·실행 결과](unofficial_locations_test_results.md)를 따른다.

## 이어서 확인할 항목

현재 본편·공식 DLC 시험판은 MO2의 `Oblivion_KR_obCJK_UTF8_Test` 모드로 준비했다. `Default`와 기존 KR 모드는 보존한다. 최소 ESP는 `Oblivion_KR_obCJK_UTF8_UI_Test`에 별도로 남겼으며 FULL 시험 중에는 끈다.

최종 확인 후 테스트 게임은 메뉴에서 종료했다. 임시 MO2 full-control 설정은 원본 해시를 확인한 뒤 제거하고 다시 연결했다. 보존 목록 99개를 다시 검사하여 변경 0개였으며 실제 Documents Oblivion.ini도 검사 전 사본과 같았다. 결과는 `_build/obcjk/utf8-test/final_preservation.json`에 있다.

한글 위치명 변형은 후속 작업에서 이미 별도 모드로 적용했다. 새 게임 진입 후 한글 GMST·대사·아이템·BOOK·주문 및 실제 장소 이름의 표시를 확인하고, 프로필 내부의 새 저장/완전 재실행 후 재로드를 진행한다. 이전 세이브에는 쓰지 않는다. 폰트 선택은 [SLOT별 추천](font_recommendations.md)을 기준으로 실제 본문 화면에서 비교한다.
