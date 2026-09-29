# v2 Project State

최종 갱신: 2026-09-29

## 1. 동결 기준본

- 정식 릴리즈: `v1.0.2`
- 기준 커밋: `97e4679330fda6bf277780e3cb05fa866c5f1cb6`
- 릴리즈 ZIP: `Oblivion_Original_KR_Installer_v1.0.2.zip`
- SHA-256: `823128bdc19af509bde91d7ba8f84a3c44887bbdc4fe8e12f85b74e95ea96ab4`
- v1.0.2는 수정하지 않는다.
- v1 번역은 v2의 신규 번역 원본으로 사용하지 않고 비교/폴백/QA 참고용으로만 사용한다.
- 예외: 메뉴 GMST 926개는 실제 게임에서 검증된 v1.0.2 번역을 그대로 재사용한다.

## 2. 현재 작업 환경

현재 v2 주 작업 머신: Windows 설치 Steam Deck
로컬 저장소/작업 루트: `C:\오블리비언`

작업 디렉터리:
- `v2_work\00_incoming_sst` — 최신 Skyrim SST 입력
- `v2_work\01_glossary` — Oblivion 전용 용어집/증거표
- `v2_work\02_source_extract` — 정품 영문 원본 신규 추출
- `v2_work\03_translation_json` — Gemini 입력 배치
- `v2_work\04_gemini_raw` — Gemini 확정 원시 결과
- `v2_work\05_sol_review` — GPT-5.6 Sol 검수/확정
- `v2_work\06_build_inputs` — 빌더 입력
- `v2_work\07_test_build` — 테스트 빌드
- `v2_work\logs` — 배치/API/검수 로그 및 폐기/파일럿 보관
- `v2_tools` — 재현 가능한 v2 파이프라인 스크립트

`v2_work`와 API 키 파일은 Git 추적 대상이 아니다.

## 3. SST 파싱 현황

입력:
- SST 파일 79개
- 포맷: SSU8
- 총 행: 98,568
- SST 고유 원문(초기 정규화): 77,675
- SST 충돌 원문: 945
- 정확 고유 원문-번역 쌍: 78,861
- 실패 파일: 0

Oblivion과 교차 후:
- 번역 가능한 SST 원문: 73,267
- Oblivion 고유 원문: 42,254
- 정확히 겹치는 원문: 1,451
- 겹치는 Oblivion 발생 건수: 4,585
- 관련 SST 충돌: 157
- 무충돌 exact 후보: 1,294
- 초기 term-like seed: 1,071

## 4. Oblivion 영문 원문 신규 추출

정품 영문 게임에서 새로 추출한다. v1 한국어 패치에서 역추출하지 않는다.

공식 플러그인 11개:
- Oblivion.esm
- Knights.esp
- DLCBattlehornCastle.esp
- DLCFrostcrag.esp
- DLCThievesDen.esp
- DLCSpellTomes.esp
- DLCMehrunesRazor.esp
- DLCVileLair.esp
- DLCOrrery.esp
- DLCHorseArmor.esp
- DLCShiveringIsles.esp (stub)

추출 결과:
- 공식 플러그인 문자열: 50,414
- 메뉴 GMST 마스터: 926
- Oblivion.exe UI 후보: 923
- 전체 추출 행: 52,263

안전 분류:
- TRANSLATE: 44,216
- TOPIC_STRUCTURE_CHECK: 4,122
- REVIEW_LOCATION_UNSAFE: 1,953
- KEEP_ENGLISH_RACE_FULL: 14
- REVIEW_INTERNAL: 1
- MENU_GMST: 1,034
- EXE_UI_CANDIDATE: 923

## 5. 용어집 정책 및 현재 상태

우선순위:
1. 사용자/프로젝트 확정 용어
2. 최신 Skyrim SST exact
3. 최신 Skyrim BOOK/DESC 본문 및 반복 문맥
4. 현재 한국어 TES 커뮤니티/나무위키 표기 교차검증
5. Oblivion Remastered 반복 메모리
6. v1 번역은 마지막 QA/비교용

현재 파일:
- `01_glossary\OBLIVION_CORE_TERMINOLOGY_V2.csv`
- `01_glossary\OBLIVION_TERMINOLOGY_CONFLICTS_V2.csv`
- `01_glossary\OBLIVION_GLOSSARY_V2_ACTIVE.csv`
- `01_glossary\TERMINOLOGY_EVIDENCE_ALL.csv`
- `01_glossary\TERMINOLOGY_EVIDENCE_CORE.csv`

현재 수치:
- 핵심 고유명사/시리즈 용어 확정: 181
- 문서화된 충돌: 16
- 활성 용어집: 1,226
- EXACT_ONLY: 1,045
- PHRASE_CONTEXT: 181

적용 규칙:
- SST 일반 용어는 영어 원문 전체가 정확히 일치할 때만 강제.
- 사람이/근거로 확정한 핵심 고유명사만 문장 내부에서도 강제.
- PHRASE_CONTEXT는 대소문자를 구분하여 `Anvil`, `Bliss`, `Split` 같은 일반 영어 단어 오적용을 막는다.
- `Order` 같은 일반어는 단독 강제하지 않고 `Knights of Order`, `Priests of Order` 같은 완전 고유 구문만 사용한다.

주요 확정 예:
- Vitharn → 비탄 (프로젝트 결정)
- Jyggalag → 지갈렉
- Sheogorath → 쉐오고라스
- Golden Saint → 골든 세인트
- Dark Seducer → 다크 세듀서
- Shivering Isles → 쉬버링 아일즈
- Mankar Camoran → 맨카 캐모런
- Raven Camoran → 레이븐 캐모런
- Ruma Camoran → 루마 캐모런
- Blackwood Company → 블랙우드 컴퍼니
- Order of the Virtuous Blood → 고귀한 피의 결사
- Raminus Polus → 라미누스 폴루스
- Tar-Meena → 타르-미나
- Nord Winds → 노드의 바람

## 6. 메뉴 GMST 정책

메뉴 GMST는 Gemini에 보내지 않는다.
v1.0.2에서 게임 검증이 끝난 926개 번역을 v2에서도 그대로 재사용한다.

생성 파일:
- `06_build_inputs\GMST_REUSE_V1_926.csv`
- `06_build_inputs\GMST_REUSE_V1_926_REPORT.json`

검증:
- 926행
- 924 고유 EDID
- 한국어 빈 값 1건: `sPlural` / 원문 `(s)`
- `sPlural`의 빈 한국어는 한국어 복수 접미사가 필요 없으므로 의도적으로 보존한다.

최종 배포 방식은 별도 메뉴 ESP가 아니라 Oblivion.esm 직접 통합을 유지한다.

## 7. 기술적 번역 금지 / 안전 규칙

- RACE/FULL은 영어 원문 유지.
- 일반 대사/설명 속 종족명은 한국어 번역 가능.
- CELL/FULL, WRLD/FULL 등 저장 안정성 영향 가능 위치명은 번역 배치에서 제외/보류.
- EDID, 스크립트, 파일 경로, 내부 식별자, 바이너리/포맷 제어값은 번역하지 않는다.
- `%s`, `%d` 등 placeholder, 줄바꿈, 마크업/태그를 반드시 보존.
- DIAL/FULL은 토픽 구조 검증 대상.
- 내부용 FULL처럼 보이는 문자열은 unchanged가 정상일 수 있다.

## 8. Gemini 번역 프로토콜

기본 모델: `gemini-3.5-flash-lite`
대체 가능 계열: `gemini-3.1-flash-lite`

사용자 제공 제한 기준:
- RPM 15
- TPM 250,000
- RPD 500

현재 로컬 키 파일에서 실제 API 조회에 성공하는 유효 키 슬롯은 2개였다.
키 값 자체는 Git/채팅/로그에 절대 기록하지 않는다.

구조 안전:
- 모델에게 FormID/복합 ID 문자열을 재출력시키지 않는다.
- 각 요청 항목에 단순 정수 `n=1..N`을 부여.
- 모델은 `{translations:[{n,korean},...]}`만 반환.
- 로컬에서 n의 누락/중복/재정렬을 검증하고 원래 ID와 결합.
- 검증 실패 결과는 확정 파일로 저장하지 않는다.

배치 크기:
- 약 210,000 chars/request
- 대략 300여 항목/request
- 기본 호출 간격 18초

## 9. 최신 번역 배치

핵심 용어 181개/활성 1,226개 기준으로 생성:
- 번역 작업: 48,338건
- 배치: 233개
- 최대 배치 크기: 약 211K chars
- 메뉴 GMST 항목: 0
- INFO 대사: 25,119
- DIAL 토픽: 4,122
- QUST/CNAM: 2,475
- BOOK/DESC: 941

오래된 manifest에서 남은 stale `batch_*.json` 991개는 로그 보관 폴더로 이동했고,
현재 `03_translation_json`에는 manifest에 등록된 233개만 남아 있다.

최종 181개 용어집 직전 파일럿:
- 5배치 / 1,550건
- placeholder 손실 0
- 태그 손실 0
- 줄바꿈 손실 0
- 구조/순번 오류 0
- glossary miss 1: `Nord Winds in Bruma`
- 원인: 종족명 Nord와 상점명 Nord Winds의 중첩
- 조치: `Nord Winds → 노드의 바람`을 core term으로 추가
- 해당 파일럿 결과는 로그로 보관하고 본 번역 결과에서 제외

현재 최종 manifest는 용어 181개 기준으로 다시 생성된 상태다.

최종 181개 용어집 기준 본 번역 검증:
- batch 0001~0005 완료
- 1,550건
- n/개수 구조 오류 0
- placeholder 손실 0
- 태그 손실 0
- 줄바꿈 손실 0
- glossary miss 0
- unchanged 4건은 내부 Faction 식별자형 문자열로 보존

## 10. Sol 검수 기준

Gemini 결과는 자동 확정하지 않는다.

우선순위:
1. 영어 원문 기준으로 Gemini 번역이 좋으면 채택
2. v1이 더 좋으면 비교 참고
3. 둘 다 부족하면 Sol이 직접 새 번역 작성

전역 QA:
- 동일 원문 상이 번역
- 용어 불일치
- 불필요한 영어 잔존
- `???`
- placeholder 손실
- 줄바꿈/태그/마크업 파손
- 문맥상 잘못된 고유명사 해석
- 내부 식별자 오번역

## 11. 현재 단계

용어집 1차 구축 및 Gemini 프로토콜 검증 완료.
GMST 926개는 v1 재사용으로 분리 완료.
최종 용어집 기준 신규 manifest 233개 생성 완료.

다음 단계:
1. batch 0006부터 최종 manifest Gemini 번역 계속
2. 각 배치 구조/포맷 자동 QA
3. Gemini 전체 결과를 Sol 검수 큐로 병합
4. Sol 영어 원문 대조 검수
5. 전역 일관성 QA
6. 빌드 입력 생성 및 테스트 빌드
