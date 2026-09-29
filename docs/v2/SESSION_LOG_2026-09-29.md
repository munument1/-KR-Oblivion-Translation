# Session Log — 2026-09-29

## v1 / Git 기반 전환

- v1.0.2 릴리즈 완료 및 동결.
- 기준 커밋 `97e4679330fda6bf277780e3cb05fa866c5f1cb6`.
- v2 개발 브랜치 `v2-development`.
- Git 기반 PROJECT_STATE / DECISIONS / NEXT_SESSION / SESSION_LOG 체계 도입.

## Steam Deck 이전

- Windows 설치 Steam Deck `Deck_Seung`에서 작업 시작.
- 작업 루트를 `C:\오블리비언`으로 변경.
- v2_work, SST, Gemini 키 파일, 기존 결과가 정상 복사된 것을 확인.
- 본컴은 오프라인이어도 v2 작업 가능.

## SST

- 79개 SSU8 전수 파싱.
- 98,568행.
- 파싱 실패 0.
- 초기 SST 충돌 945.
- Oblivion exact-match 관련 충돌 157.
- 비대사 충돌을 Sol/문맥 기준으로 정리하고 대사형 130건은 전역 강제에서 제외.

## Oblivion 원문 추출

- 공식 플러그인 11개에서 50,414개 문자열 추출.
- 메뉴 GMST master 926.
- EXE UI 후보 923.
- 전체 추출 52,263.

주요 안전 분류:
- TRANSLATE 44,216
- TOPIC_STRUCTURE_CHECK 4,122
- REVIEW_LOCATION_UNSAFE 1,953
- KEEP_ENGLISH_RACE_FULL 14

## 용어집 재구축

초기 문제:
- `Vitharn`을 v1 QA만 보고 `비타른`으로 성급하게 올린 오류 발견.
- 사용자 결정으로 `Vitharn → 비탄` 확정.
- Skyrim BOOK 본문이 시리즈 고유명사 근거로 유용함을 확인.
- 나무위키/현재 커뮤니티 표기는 Skyrim에 없는 Oblivion 전용 고유명사의 교차검증 자료로 사용.

용어 우선순위 확정:
사용자 결정 > Skyrim SST exact > Skyrim BOOK/DESC > 현재 커뮤니티 > Remastered > v1 QA.

현재:
- core terminology 181
- conflicts 16
- active glossary 1,226
- EXACT_ONLY 1,045
- PHRASE_CONTEXT 181

대표 확정:
- Vitharn 비탄
- Jyggalag 지갈렉
- Pelinal 펠리날
- Shivering Isles 쉬버링 아일즈
- Golden Saint 골든 세인트
- Dark Seducer 다크 세듀서
- Blackwood Company 블랙우드 컴퍼니
- Order of the Virtuous Blood 고귀한 피의 결사
- Raminus Polus 라미누스 폴루스
- Tar-Meena 타르-미나
- Nord Winds 노드의 바람

## GMST

사용자 결정으로 메뉴 GMST는 새 번역하지 않고 v1.0.2 번역 재사용.

생성:
`v2_work\06_build_inputs\GMST_REUSE_V1_926.csv`

검증:
- 926행
- 924 unique EDID
- blank Korean 1건: `sPlural` / `(s)`
- 한국어에는 영어식 복수 접미사가 필요 없으므로 의도된 빈 값.

## Gemini 프로토콜 시행착오

초기 42K-char 배치:
- 1,224요청으로 지나치게 잘게 분할됨.

420K-char 대형 배치:
- 약 600여 항목.
- 일부 응답에서 항목 누락 발생.
- ID를 모델이 직접 재출력할 때 미세한 ID 변형 발생.
- 단순 배열 위치 결합은 중간 밀림을 잡지 못함.

최종 방식:
- 약 210K chars
- 대략 300여 항목
- 정수 n 반환
- n/개수 완전 일치 검증
- 호출 간격 18초

유효 키 슬롯:
- 로컬 파일의 키 값은 출력하지 않음.
- 실제 models API 조회 성공 슬롯 2개 확인.

## 파일럿 QA

core 180 기준 5배치:
- 1,550건
- placeholder mismatch 0
- tag mismatch 0
- newline mismatch 0
- sequence/structure error 0
- glossary miss 1

glossary miss:
- `Nord Winds in Bruma`
- 일반 종족명 `Nord`와 상점 고유명사 `Nord Winds` 충돌.
- 프로젝트 검수본에서 `Nord Winds → 노드의 바람` 확인.
- core term에 추가하여 core 181로 증가.
- 파일럿 결과는 로그 보관 후 본 번역에서 제외.

## 최종 manifest

core 181 / active 1,226 기준:
- 48,338 작업
- 233배치
- max 약 211K chars
- menu items 0
- INFO 25,119
- DIAL 4,122
- QUST/CNAM 2,475
- BOOK/DESC 941

구 manifest의 stale batch JSON 991개는 로그로 이동.
현재 03_translation_json에는 manifest 대상 233개만 남김.

## 다음

- core 181 기준 최종 Gemini 본 번역.
- 주기적 range QA.
- 전체 Gemini 완료 후 Sol 영어 원문 대조 검수.
- 전역 QA 후 빌드 입력/테스트 빌드.


## core 181 최종 파일럿 / 본 번역 시작

최종 core 181 / active 1,226 기준 manifest로 batch 0001~0005를 다시 생성/번역했다.

결과:
- 5배치
- 1,550건
- 모든 배치 1차 시도 성공
- n/개수 구조 오류 0
- placeholder mismatch 0
- tag mismatch 0
- newline mismatch 0
- glossary miss 0
- unchanged 4건: 내부 Faction 식별자형 문자열

대표 적용:
- Vitharn Smith → 비탄 대장장이
- Order of the Virtuous Blood → 고귀한 피의 결사
- Blackwood Company → 블랙우드 컴퍼니
- Jyggalag 계열 → 지갈렉 일관 적용

다음 시작점: batch 0006.
