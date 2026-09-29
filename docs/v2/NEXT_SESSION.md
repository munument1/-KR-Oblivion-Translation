# Next Session

최종 갱신: 2026-09-30

## 시작 즉시 확인

작업 머신:
- Deck_Seung
- `C:\오블리비언`

최신 인수인계:
- `docs/v2/SESSION_LOG_2026-09-30.md`

현재 기준:
- 일반 Gemini raw: **218/218 완료**
- BOOK: **156/156 완료**
- INFO/NAM1 pre-143 dialogue backfill: **49/144 완료** (문서 작성 시점)
- QUST/CNAM journal backfill: 2,475개 / 25배치, 대기
- 문장형 DIAL/FULL backfill: 2,184개 / 22배치, 대기

새 채팅에서는 숫자를 믿고 추정하지 말고
먼저 실제 프로세스와 출력 파일 수/mtime을 확인한다.

## 1순위 — INFO dialogue backfill 계속

runner:
`v2_tools\run_dialogue_backfill.py`

입력:
`v2_work\03_translation_json_dialogue_backfill`

출력:
`v2_work\04_gemini_raw_dialogue_backfill`

모델:
- 3.5 Flash-Lite 우선
- 3.1 Flash-Lite 자동 폴백

프로젝트:
- 2, 3

쿼터는 project × model 별도 계산.
전역 합산 450으로 되돌리지 않는다.

## 2순위 — QUST journal backfill

INFO backfill 완료 후:

- 2,475개
- 25배치
- `03_translation_json_quest_backfill`

QUST/CNAM은 플레이어 일지/독백:
- `-했다`
- `-해야 한다`
- `-인 것 같다`

이유 없는 존댓말 금지.

## 3순위 — DIAL/FULL player-choice backfill

- 문장형 2,184개
- 22배치
- `03_translation_json_dial_backfill`

DIAL/FULL 문장형은 NPC 대사가 아니라
플레이어 선택문/토픽일 수 있다.

중립적 자연 구어체.
근거 없는 `-묻는가/-하는가/-하오/-하네` 등을 만들지 않는다.

## BOOK

BOOK 번역 자체는 **156/156 완료**.

116번에서 수정한 핵심:
- book-wide unique PN token namespace
- 책 안에서 확인된 exact term을 동일 영어 occurrence에 전파
- 검증은 실제 segment mapping이 있는 용어만 확인

다시 BOOK을 처음부터 돌리지 않는다.
최종 QA와 Sol review에서 검수한다.

## 조사/잠금 주의

`locked_terms.py`에서 이미 보강됨:

- `(이)가`, `이(가)`
- `(을)를`, `을(를)`
- `(은)는`, `은(는)`
- `(과)와`
- `으(로)`, `로(으)`
- `의(의)`, `에(에)`
- PN 숫자 누출

기존 일반 raw에서 이미:
- 272문장 / 288 artifact 수정
- 추가 17문장 / PN 숫자 22건 수정

backfill 이후 반드시 동일 감사를 다시 한다.

## 불필요한 '의'

영어 possessive/of/noun-chain을
기계적으로 `의`로 만들지 않는다.

`{GEN}`도 한국어에서 실제로 필요할 때만 선택.

`audit_genitive_calques.py` 후보는
자동 삭제 대상이 아니라 Sol 검수 우선순위다.

## 최종 QA 순서

모든 backfill 완료 후:

1. `audit_translation_coverage.py`
2. `audit_book_coverage.py`
3. `audit_locked_artifacts.py`
4. `audit_genitive_calques.py`
5. `audit_quest_journal_style.py`
6. `audit_dialogue_tone.py`
7. `summarize_speaker_tone.py`
8. WORDPLAY_REVIEW
9. CHARACTER_VOICE_REVIEW

확인 항목:
- 미번역
- 영어 잔존
- 원문 그대로
- ??? / placeholder
- PN 숫자
- 조사 선택형
- 불필요한 의
- BOOK 누락
- QUST 존댓말
- DIAL player-choice 어투
- 의미 축약
- 캐릭터 말투

## v1 비교

최종 backfill/QA 뒤
v1.0.2와 v2를 영어 원문 기준으로 전수 비교.

v1은 정답/덮어쓰기 원본이 아니다.
회귀 탐지와 좋은 표현 참고용이다.

## 비밀값

API 키는 절대 Git/채팅/로그에 기록하지 않는다.
키 슬롯/프로젝트 번호/모델/호출량만 기록한다.
