# v2_tools

Oblivion Original Korean v2 번역 파이프라인 도구.

현재 기본 작업 루트는 Windows Steam Deck의 `C:\오블리비언`이다.
민감한 API 키 및 `v2_work` 생성물은 Git에 포함하지 않는다.

주요 순서:

1. `parse_sst.py` — 최신 Skyrim SST 파싱/정규화
2. `extract_oblivion_source.py` — 정품 Oblivion ESM/ESP 원문 추출
3. `build_sst_glossary.py` — SST↔Oblivion exact 교차
4. `prepare_conflict_review.py` / `finalize_glossary_conflicts.py` — 충돌 정리
5. `build_terminology_evidence.py` — SST BOOK/Remaster/v1 근거표 생성
6. `build_core_terminology.py` — 검증된 핵심 고유명사 용어집 생성
7. `build_active_glossary.py` — exact-only + phrase-context 활성 용어집 생성
8. `build_gmst_reuse.py` — v1.0.2 GMST 926개 재사용 입력 생성
9. `build_translation_batches.py` — 문맥 포함 Gemini JSON 배치 생성
10. `run_gemini_translation.py` — 순번 n 검증형 Gemini runner
11. `qa_gemini_batch.py` / `qa_gemini_range.py` — 포맷/용어집 자동 QA

상세 상태와 결정은 `docs/v2/PROJECT_STATE.md`, `DECISIONS.md`, `NEXT_SESSION.md`를 먼저 읽는다.
