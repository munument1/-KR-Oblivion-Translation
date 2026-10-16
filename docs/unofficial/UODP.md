# Unofficial Oblivion DLC Patches 한국어 UTF-8 번역 v1.1.0

대상 원본: **UODP v27**. 다른 버전의 ESP에 적용하지 마세요.

## 2026-10-16 책 본문 복구

기본 ESP 9개와 선택 SSSB ESP의 모든 BOOK 15개를 원본과 대조했습니다. 본문이 제목 한 줄로 축약된 다음 4개를 기존 `canonical_unofficial_translation_v2.csv`에서 복구했습니다. 새 보정 CSV는 추가하지 않았습니다.

| 플러그인 | FormID | 책 | 이전 본문 → 복구 본문 |
|---|---|---|---|
| DLCSpellTomes - Unofficial Patch.esp | 02001281 | Fenrik's Welcome Tome | 21자 → 502자 |
| Knights - Unofficial Patch.esp | 02000ED2 | The Knights of the Nine | 10자 → 1,987자 |
| Knights - Unofficial Patch.esp | 02000ED4 | Shezarr and the Divines | 9자 → 1,901자 |
| Knights - Unofficial Patch.esp | 02000ED8 | The Song of Pelinal, v 5 | 13자 → 1,236자 |

공식 DLC의 전체 한국어 본문을 기반으로 복구하고, UODP의 주문 잠금 난이도 변경(상급 → 중급)을 반영했습니다. 복구 대상의 연도·거지 살해 사건 등 원문과 어긋난 일부 표현도 바로잡았습니다. 책 제목 FULL과 다른 레코드, 나머지 정상 본문 11개는 유지합니다.

언오피셜 전체 14개 ESP 빌드와 단위 테스트 74개가 통과했습니다. 생성된 ESP에서 15개 본문을 다시 읽어 CSV·UTF-8 일치를 확인했고, 이번 수정 대상 ESP 2개를 제외한 12개 출력은 이전과 바이트 단위로 동일합니다. UOP의 기존 112개 책 본문 복구도 유지했습니다. 원문·출력 해시와 전체 목록은 [전수 검증 기록](https://github.com/munument1/Oblivion-KR-Translation/blob/main/docs/unofficial/uodp_book_body_audit_20261016.json)에 있습니다. 실제 게임 화면에서의 페이지 표시 검증은 별도입니다.

넥서스 업로드용 파일: `UODP_KR_UTF8_obCJK_v27_BOOKFIX_20261016.zip`. **UODP 전체 교체용 ZIP**이며 기존 영문 UODP v27 위에 설치합니다. UOP·USIP 파일과 DLL은 들어 있지 않습니다. 본편 설치기만 다시 실행해도 기존 UODP 한국어 ESP는 바뀌지 않으므로, 이 ZIP으로 UODP 한국어 모드를 교체하세요.

## 구성

기본 ESP 9개:

- `DLCBattlehornCastle - Unofficial Patch.esp`
- `DLCFrostcrag - Unofficial Patch.esp`
- `DLCHorseArmor - Unofficial Patch.esp`
- `DLCMehrunesRazor - Unofficial Patch.esp`
- `DLCOrrery - Unofficial Patch.esp`
- `DLCSpellTomes - Unofficial Patch.esp`
- `DLCThievesDen - Unofficial Patch.esp`
- `DLCVileLair - Unofficial Patch.esp`
- `Knights - Unofficial Patch.esp`

선택: `Optional/DLCThievesDen - Unofficial Patch - SSSB.esp`.

## MO2 설치

1. 해당 공식 DLC, xOBSE, obCJK, 영문 UODP v27을 먼저 설치합니다.
2. 본편·공식 DLC용 `Oblivion_KR_obCJK`를 활성화합니다. 글꼴과 프로필 INI는 본편 v1.1.0 설치기 안내를 따릅니다.
3. 이 ZIP을 별도 모드로 설치하고, MO2 왼쪽 목록에서 영문 UODP 및 본편 번역 모드보다 아래에 둡니다.
4. SSSB 선택 패치를 사용하던 경우에만 `Optional` 안 ESP를 모드 최상위로 옮깁니다. 설치한 DLC에 해당하는 ESP만 활성화합니다.
5. 플러그인 이름과 기존 로드 순서를 유지합니다. 이전 바이트 방식 UODP 한글 모드와 UTF-8 시험판을 끄고 MO2의 Oblivion 항목으로 실행합니다.

검증된 번역을 UTF-8로 변환하고 CELL/WRLD 한글 위치명을 적용했습니다. 종족 이름은 영어로 유지합니다. 원문 대조가 확정되지 않은 문자열은 영어로 남을 수 있습니다.

원본 대비 레코드·그룹 식별자, FormID, 필드 순서와 컴파일된 스크립트 보존을 검사했습니다. `validation.json`과 `SHA256SUMS.txt`에 파일별 검증 결과와 해시가 있습니다. 모든 퀘스트·대화·장시간 플레이의 개별 검증을 완료했다는 뜻은 아닙니다.

이 파일은 번역 ESP만 제공합니다. 원본 패치의 메시·텍스처·음성, xOBSE/obCJK DLL, 글꼴은 포함하지 않습니다. 원본 제작 크레딧은 Unofficial Patch Project Team / Arthmoor 및 원본 패치의 기여자에게 있습니다.
