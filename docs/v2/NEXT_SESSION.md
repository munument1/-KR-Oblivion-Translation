# Next Session

최종 갱신: 2026-09-29

## 현재 시작점

Steam Deck Windows 작업 루트:
`C:\오블리비언`

현재 기준:
- core terminology: 181
- active glossary: 1,226
- terminology conflicts documented: 16
- GMST: 926개 v1.0.2 재사용
- Gemini 번역 대상: 48,338건
- manifest: 233배치
- `03_translation_json`에는 현재 manifest 233개만 존재
- 최종 181개 용어집 기준 `04_gemini_raw`은 새로 채우면 됨

## 바로 할 일

1. `v2_work\01_glossary\OBLIVION_CORE_TERMINOLOGY_V2.csv`와
   `OBLIVION_GLOSSARY_V2_ACTIVE.csv`를 기준 용어집으로 고정한다.
2. `v2_work\03_translation_json\manifest.json` 기준으로 Gemini 번역을 진행한다.
3. 기본 runner:
   `v2_tools\run_gemini_translation.py`
4. 기본 모델:
   `gemini-3.5-flash-lite`
5. 기본 호출 간격:
   18초
6. 배치 결과 저장 전 n 순번/개수 검증이 반드시 통과해야 한다.
7. 번역 중 429/5xx가 나면 runner의 백오프/키 전환을 사용한다.
8. 일정 구간마다 `qa_gemini_range.py`로 자동 QA한다.
9. glossary miss가 나오면 무조건 Gemini를 탓하지 말고
   일반어/고유명사 중첩 여부를 먼저 확인한다.
10. 전체 Gemini 완료 후 `05_sol_review`용 병합 큐를 만든다.

## 품질 게이트

Gemini 배치마다:
- n 순번 일치
- 결과 개수 일치
- placeholder 보존
- 태그 보존
- 줄바꿈 보존
- glossary target 적용 여부
- 내부 식별자 unchanged 허용 여부

전체 번역 후:
- 동일 원문 상이 번역
- 핵심 고유명사 181개 일관성
- BOOK 전체 문서 문체/연결성
- INFO 대사 문맥
- DIAL 토픽 구조
- 불필요한 영어 괄호
- ??? / 빈 번역
- RACE/FULL 변경 0
- CELL/WRLD 안전 제외 유지

## GMST

`v2_work\06_build_inputs\GMST_REUSE_V1_926.csv` 사용.
Gemini 입력에 GMST를 다시 넣지 않는다.
`sPlural=(s)`의 한국어 빈 값은 의도된 값이다.

## 참고: 최근 파일럿에서 잡힌 시행착오

- 600여 항목 장배치에서 모델이 일부 항목을 누락한 사례가 있었음.
- 단순 배열 위치 결합은 개수가 같아도 중간 밀림을 잡지 못했음.
- 해결: 약 300개/배치 + 정수 n 검증.
- 일반 SST 부분일치 강제는 `Anvil→모루` 같은 사고를 일으킴.
- 해결: 일반 SST exact-only, core proper noun만 case-sensitive phrase-context.
- 구 manifest의 stale batch JSON 991개는 로그로 이동 완료.

## 세션 종료 시

- PROJECT_STATE 갱신
- 새 장기 결정은 DECISIONS에 추가
- NEXT_SESSION은 다음 실제 실행 단계만 남김
- 중요한 숫자/시행착오는 SESSION_LOG에 기록
- API 키 값은 절대 기록 금지
