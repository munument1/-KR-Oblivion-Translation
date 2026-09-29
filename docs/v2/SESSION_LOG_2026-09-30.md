# Session Log — 2026-09-30

## 작업 환경

- 주 작업 머신: Windows Steam Deck `Deck_Seung`
- 작업 루트: `C:\오블리비언`
- 게임 Data: `C:\Program Files (x86)\Steam\steamapps\common\Oblivion\Data`
- API 키/비밀값은 Git에 기록하지 않는다.
- Gemini 키 4개는 **서로 다른 Google Cloud 프로젝트**다.

## 번역 진행 스냅샷

이 문서 작성 시점 기준:

- 일반 Gemini raw: **218/218 배치 완료**
- BOOK: **156/156 배치 완료**
- 143 이전 INFO/NAM1 대사 말투 backfill:
  - 대상 17,233개
  - 총 144배치
  - **49/144 완료**
  - 현재 backfill runner가 계속 실행 중인 상태에서 인수인계
- QUST/CNAM journal backfill:
  - 2,475개
  - 25배치
  - 아직 본 실행 전
- 문장형 DIAL/FULL player-choice backfill:
  - 2,184개
  - 22배치
  - 아직 본 실행 전

## 일반 번역 구조

일반 번역 대상은 최신 기준으로 218배치까지 모두 생성/번역되었다.
초기의 오래된 233배치 수치는 더 이상 현재 상태가 아니다.

일반 runner:
- `v2_tools\run_gemini_translation.py`
- 기본: `gemini-3.5-flash-lite`
- 프로젝트 슬롯: 2, 3
- 기본 간격: 18초
- 고유명사 잠금 + 포맷 잠금 + 조사 로컬 복원 + 화자/대화 문맥 메타데이터 사용

## Gemini quota

키 1~4는 각각 다른 Cloud project다.

따라서 안전선은 전역 합산이 아니라 **project × model 별도**로 계산한다.

`v2_tools\gemini_quota.py`는:
- project별 호출량
- model별 호출량
을 따로 계산하도록 수정됨.

대사 backfill runner는:
- 3.5 Flash-Lite 우선
- 해당 project/model이 429 또는 안전선에 도달하면
- 3.1 Flash-Lite로 폴백
하도록 구현됨.

## 고유명사 잠금 / 조사 복원

핵심 모듈:
- `v2_tools\locked_terms.py`

현재 지원:
- `{OBJ}` 을/를
- `{SUBJ}` 이/가
- `{TOPIC}` 은/는
- `{WITH}` 과/와
- `{DIR}` 으로/로
- `{VOC}` 아/야
- `{GEN}` 의
- `{FROM}` 으로부터/로부터

복원기는 아래 찌꺼기도 처리하도록 확장됨:
- `이(가)`, `(이)가`
- `을(를)`, `(을)를`
- `은(는)`, `(은)는`
- `과(와)`, `(과)와`
- `으(로)`, `로(으)`
- `의(의)`
- `에(에)`
- slash형/중복 조사

추가 함수:
- `normalize_josa_artifacts()`
- `UNRESOLVED_JOSA_RE`

### PN 숫자 누출

Gemini가 `__PN001__`을 직접 한국어로 치환하면서
`쉐오고라스1`, `타이버 셉팀1 탈로스2`처럼
토큰 번호를 이름 뒤에 남기는 현상이 확인됨.

조치:
- 확정 고유명사 + 해당 PN token index가 붙은 경우
- 숫자를 제거한 뒤
- 실제 한국어 이름의 받침 기준으로 조사까지 재선택

기존 일반 raw 교정:
- 35개 배치
- 272문장
- 288개 locked/josa artifact 수정
- 추가 잔여 numeric leak 17문장 / 22건 수정

## 불필요한 '의'

대사와 서적 모두 영어의 possessive/'s/of/noun-chain을
한국어 `의`로 기계적으로 옮기는 직역체가 확인됨.

일반/BOOK prompt에 다음 원칙 추가:
- 영어에 's/of가 있다고 `의`를 자동 사용하지 않는다.
- 한국어에서 실제 소유/속격이 자연스럽고 필요할 때만 `의` 사용.
- 복합명사, 관형형, 동격, 다른 조사, 생략이 자연스러우면 그 방식을 우선.
- 연속/과잉 `의`를 피한다.

LOCK_INSTRUCTION의 `{GEN}`도:
- 영어 소유격 때문에 자동 선택 금지
- 한국어 최종 문장에서 정말 필요할 때만 선택

QA:
- `v2_tools\audit_genitive_calques.py`
- 현재 우선 검수 후보 약 1,288문장
- 후보는 오류 확정이 아니라 Sol 검수 우선순위다.
- 절대 `의`를 기계적으로 일괄 삭제하지 않는다.

## BOOK

BOOK:
- 931권
- 156배치
- **156/156 완료**

입력:
- `03_translation_json_books`

raw:
- `04_gemini_raw_books`

재구성:
- `05_sol_review\books_reconstructed`

모델:
- `gemini-3.1-flash-lite`
- project 1,4

### BOOK 잠금 버그와 해결

116번에서 반복 실패가 있었음.

원인 1:
- 같은 책 안 여러 segment에서 `__PN001__` 번호가 재사용되어
  모델이 segment 사이 토큰을 혼동할 수 있었음.

해결:
- 한 책 전체에서 PN token namespace를 유일하게 만든다.

원인 2:
- 제목 segment의 exact glossary term
  예: `Bound Sword → 마법 검`
  이 본문의
  `Bound Sword, 15 seconds on Self`
  에는 잠기지 않았음.
- 모델은 책 전체 문맥을 보고 제목 token을 본문에도 복사하여
  unresolved token 오류 발생.

해결:
- 한 책에서 확인된 용어는 book-local memory로 유지
- 동일 영어 구문이 다른 segment에 다시 나타나면 해당 segment에도 잠금 전파
- 각 occurrence는 책 전체에서 고유한 PN 번호를 사용

원인 3:
- 전파된 glossary를 실제 원문에 없는 segment까지 glossary-miss 검증함.

해결:
- 검증은 **그 segment에 실제 mapping이 생성된 용어만** 검사.

이 수정 후 BOOK 116번이 통과했고 최종 156번까지 완료.

## INFO 화자 resolver / 캐릭터 말투

원본 Oblivion.esm INFO의 CTDA를 분석해 화자를 추출.

확인된 CTDA 구조:
- GetIsID function number: 72
- CTDA raw offset 12: NPC FormID

스크립트:
- `v2_tools\build_info_speaker_map.py`

출력:
- `02_source_extract\INFO_SPEAKER_MAP.csv`

초기 결과:
- INFO with GetIsID: 15,736
- EXACT_SINGLE: 13,797
- EXACT_SET: 1,938
- unresolved: 1

주의:
- 현재 speaker map은 기본적으로 Oblivion.esm 중심 구현.
- 공식 DLC plugin 전체 resolver 일반화는 추후 점검 가능.

## DIAL context

스크립트:
- `v2_tools\build_dial_context_map.py`

DIAL 유형:
- TOPIC
- CONVERSATION
- PERSUASION
- COMBAT
- DETECTION
- SERVICE
- MISC

addressee hint:
- TOPIC/PERSUASION/SERVICE → PLAYER_LIKELY
- CONVERSATION → NPC_CONVERSATION_OR_SCRIPTED 또는 special bark
- COMBAT/DETECTION/MISC → SITUATIONAL_TARGET

이는 정확한 상대 FormID가 아니라 heuristic이다.

## 캐릭터 말투

모듈:
- `v2_tools\dialogue_style.py`

원칙:
- 캐릭터마다 하나의 존댓말/반말을 기계적으로 고정하지 않는다.
- speaker + addressee + 관계 + 계급 + 적대/친밀 + 상황을 함께 본다.
- 같은 캐릭터라도 상대/상황에 따라 어투가 달라질 수 있다.

주요 style profile:
- Sheogorath
- Martin Septim
- Jauffre
- Lucien Lachance
- Haskill은 반드시 추가/확인 대상

Haskill 권장:
- 건조하고 절제된 존댓말
- 냉소/빈정거림
- Sheogorath에게 격식
- 감정 과장 금지

alias:
- Brother Martin → Martin Septim
- DASheogorathVoice → Sheogorath

## 143 이전 INFO backfill

새 화자/상대/말투 규칙 도입 전 번역된 대사를 재교정한다.

대상:
- batch 1~142의 INFO/NAM1
- 17,233개
- 144개 backfill batch

입력:
- `03_translation_json_dialogue_backfill`

출력:
- `04_gemini_raw_dialogue_backfill`

runner:
- `v2_tools\run_dialogue_backfill.py`

현재 스냅샷:
- **49/144 완료**
- 새 runner는 3.5 → 3.1 자동 폴백 지원

완료 후 검증된 backfill 결과가 기존 general raw보다 우선되도록 최종 병합할 것.

## QUST/CNAM

QUST/CNAM은 NPC 대사가 아니다.
플레이어의 퀘스트 일지/내적 독백이다.

확정 문체:
- `-했다`
- `-해야 한다`
- `-인 것 같다`
- `-알아봐야 한다`

금지:
- 이유 없는 `-습니다/-ㅂ니다`
- `-해요/-세요`

현재 2,475개 전체를 재교정하기 위한 queue 생성:
- `03_translation_json_quest_backfill`
- 25배치

기존 스냅샷에서 번역된 QUST 1,570건 중
존댓말 종결 후보 465건이 확인되었으므로
일부만 고치지 말고 **2,475건 전체를 동일 규칙으로 재검수**한다.

QA:
- `v2_tools\audit_quest_journal_style.py`

## DIAL/FULL

`DIAL/FULL`은 NPC의 실제 응답(INFO)이 아니라
플레이어가 보는 토픽/선택문인 경우가 많다.

실제 사례:
- Knights.esp
- `NDRodericGreetC`
- `No. Why do you ask?`
- 잘못된 초안: `아니오. 왜 묻는가?`

이 문장은 NPC 화자 말투가 아니라 플레이어 선택문인데,
기존 Gemini가 문맥 없이 임의의 하게체/문어체를 부여한 것.

새 원칙:
- 명사형 토픽 → 간결한 UI label
- 문장형 선택지 → 중립적이고 자연스러운 플레이어 발화
- 플레이어의 나이/성별/신분/고풍스러운 persona를 임의로 만들지 않는다.
- 영어가 직접 나타내지 않는 `-하오/-하게/-하는가/-묻는가/-하네` 등의 스타일 금지
- 원문에 분명한 무례함/정중함/감정은 보존

문장형 DIAL/FULL:
- 2,184개
- 22배치
- `03_translation_json_dial_backfill`

이 backfill은 INFO backfill, QUST backfill 이후 진행.

## 말장난 / 관용 표현

고유명사는 기술적으로 잠그되,
농담/말장난/관용구/비꼼/반복어는 직역보다 **기능과 효과 보존**을 우선한다.

최종 Sol review에:
- WORDPLAY_REVIEW
- sarcasm
- idiom
- name joke
- repetition joke
- Sheogorath/Shivering Isles 특유 말장난
을 포함한다.

필요 시 `LOCKED_NAME`과 `WORDPLAY_NAME`을 구분한다.

## 전역 QA

스크립트:
- `v2_tools\audit_translation_coverage.py`
- `v2_tools\audit_book_coverage.py`
- `v2_tools\audit_locked_artifacts.py`
- `v2_tools\audit_genitive_calques.py`
- `v2_tools\audit_dialogue_tone.py`
- `v2_tools\summarize_speaker_tone.py`
- `v2_tools\audit_quest_journal_style.py`

최종 backfill 완료 후 반드시 다시 전역 스캔:
- MISSING_OUTPUT
- 원문 그대로
- 한글 없음
- 영어 잔존
- 원문 단어 3개 이상 생존
- ??? / placeholder / TODO
- PN 숫자 누출
- unresolved 조사 선택형
- `으(로)`, `(이)가`, `의(의)` 등
- 불필요한 `의`
- BOOK segment 누락
- 구조/태그/줄바꿈/printf 파손
- 의미 과도 축약
- 캐릭터 말투 불일치
- QUST 존댓말
- DIAL 플레이어 선택문 어투

## v1 비교

모든 backfill + 전역 QA 후
v1.0.2 번역과 최종 v2를 전수 비교한다.

v1은 source of truth가 아니다.
용도:
- v1은 정상인데 v2에서 회귀한 곳 탐지
- 빠진 의미/미번역 탐지
- 좋은 기존 표현 참고

권장 비교표:
- source English
- v1 Korean
- v2 Korean
- record type / FormID
- difference reason
- review result

v1의 구용어/기계번역 흔적은 따라가지 않는다.

## 다음 순서

1. 현재 INFO dialogue backfill 49/144부터 계속
2. dialogue backfill 완료/검증
3. QUST/CNAM 2,475건 / 25배치 backfill
4. 문장형 DIAL/FULL 2,184건 / 22배치 backfill
5. backfill을 final working result에 우선 병합
6. 일반+BOOK 전역 QA 재실행
7. WORDPLAY_REVIEW / CHARACTER_VOICE_REVIEW
8. v1.0.2 전수 비교
9. Sol 영어 원문 대조 최종 검수
10. build input 생성
11. Oblivion.esm + official DLC test build
12. 게임 내 테스트 후 v2 릴리즈 준비
