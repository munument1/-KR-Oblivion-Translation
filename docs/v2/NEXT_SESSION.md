# Next Session

최종 갱신: 2026-09-29

## 시작 직후 확인

1. `D:\Codex_Trans\오블리비언\v2_work\00_incoming_sst`에 최신 Skyrim SST가 들어왔는지 확인.
2. SST 파일 목록, 크기, 수정 시각, 포맷/버전을 기록.
3. 파일을 전수 파싱해 원문-번역 쌍을 정규화.
4. 중복/충돌 통계 생성.
5. 정품 Oblivion ESM/ESP/EXE에서 신규 영문 문자열 전수 추출.
6. SST와 Oblivion 원문을 교차해 `01_glossary`에 전용 용어집 생성.
7. 충돌 후보는 자동 확정하지 않고 별도 목록 생성.
8. 기술적 번역 금지 규칙을 적용.
9. `03_translation_json`에 문맥 포함 배치 생성.
10. Gemini 실제 모델 ID와 쿼터 동작을 확인한 뒤 소규모 샘플부터 번역 검증.

## 첫 번째 품질 게이트

대량 번역 전에 최소 다음을 확인한다.

- placeholder 보존
- 줄바꿈/태그 보존
- 용어집 강제 적용
- JSON 스키마 외 출력 없음
- INFO 문맥 전달 정상
- BOOK/NOTE 전체 문서 단위 유지
- RACE/FULL 제외
- 메뉴 GMST 범위 누락 없음

## 세션 종료 시

- 완료된 단계와 생성 파일을 `PROJECT_STATE.md`에 반영.
- 새 장기 규칙이 생겼으면 `DECISIONS.md`에 새 ID 추가.
- 다음 작업 3~10개만 `NEXT_SESSION.md`에 남김.
- 중요한 시행착오/수치/비교 결과는 날짜별 `SESSION_LOG`에 기록.
- API 키/토큰은 절대 기록하지 않음.
