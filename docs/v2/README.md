# Oblivion Korean Translation v2 — Context Index

이 디렉터리는 v2 작업의 **정본 문맥(canonical context)** 을 보존한다.

## 새 작업 세션에서 읽는 순서

1. `PROJECT_STATE.md` — 현재 기준 상태와 기술적 전제
2. `DECISIONS.md` — 이미 확정된 의사결정과 금지사항
3. `NEXT_SESSION.md` — 바로 다음에 할 일
4. `SESSION_LOG_YYYY-MM-DD.md` — 필요할 때만 과거 작업 경위 확인

## 운영 원칙

- `main`의 v1.0.2 릴리즈 기준은 동결한다.
- v2 개발 문맥과 변경은 `v2-development`에서 관리한다.
- 대화 내용을 그대로 덤프하지 않는다. 작업 결과, 결정, 이유, 보류사항만 요약한다.
- 작업이 끝날 때 `PROJECT_STATE.md`와 `NEXT_SESSION.md`를 반드시 갱신한다.
- 새로운 장기 규칙이 생기면 `DECISIONS.md`에 ID를 부여해 추가한다.
- API 키, 토큰, 계정정보 등 비밀값은 Git에 기록하지 않는다.
- 로그에는 키 값이 아니라 키 슬롯 번호/오류 코드/요청 배치 ID만 남긴다.

## 브랜치 기준

- v1.0.2 기준 커밋: `97e4679330fda6bf277780e3cb05fa866c5f1cb6`
- v2 개발 브랜치: `v2-development`

이 문서 구조가 앞으로 ChatGPT/Codex/사람 작업자 사이의 공통 인수인계 기준이다.
