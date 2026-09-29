# v2 Project State

최종 갱신: 2026-09-29

## 1. 동결 기준본

- 정식 릴리즈: `v1.0.2`
- 기준 커밋: `97e4679330fda6bf277780e3cb05fa866c5f1cb6`
- 릴리즈 ZIP: `Oblivion_Original_KR_Installer_v1.0.2.zip`
- SHA-256: `823128bdc19af509bde91d7ba8f84a3c44887bbdc4fe8e12f85b74e95ea96ab4`
- v1.0.2는 수정하지 않는다. v2의 번역 원본으로 사용하지 않고 비교/폴백/QA 참고용으로만 사용한다.

## 2. v1.0.2 검증 핵심

- Python 빌드와 최종 PyInstaller EXE 출력: 21개 파일 / diff 0.
- RACE/FULL 변경 0건. VoiceFix 호환 유지.
- 메뉴 GMST 참고 ESP 926레코드 / 924 고유 EDID 전수 대조.
- 기존 Oblivion.esm GMST 105개는 DATA 교체.
- EXE 전용 GMST 821개는 참고 ESP FormID로 Oblivion.esm에 신규 통합.
- 별도 메뉴 ESP는 배포하지 않는다.
- `sLevelPopUpText`는 실제 FormID `00099F12`로 통합.

## 3. v2 로컬 작업 구조

로컬 루트: `D:\Codex_Trans\오블리비언\v2_work`

- `00_incoming_sst` — 최신 Skyrim SST 입력
- `01_glossary` — 새 Oblivion 전용 용어집
- `02_source_extract` — 정품 영문 원본 신규 추출
- `03_translation_json` — 문맥 포함 Gemini 입력
- `04_gemini_raw` — Gemini 원시 결과
- `05_sol_review` — GPT-5.6 Sol 검수/확정
- `06_build_inputs` — 실제 빌더 입력
- `07_test_build` — 테스트 빌드
- `logs` — 배치/API/검수 로그

`v2_work`는 Git 추적 대상이 아니다.

## 4. 원문 소스

영문 원문은 기존 한국어 패치가 아니라 설치된 정품 파일에서 새로 추출한다.

- 게임 Data: `C:\Games\Steam\steamapps\common\Oblivion\Data`
- 실행 파일: `C:\Games\Steam\steamapps\common\Oblivion\Oblivion.exe`
- 대상: `Oblivion.esm` + 모든 공식 DLC/확장 ESP + EXE 메뉴/GMST

## 5. SST 기준

- v2 용어 기준은 사용자가 확보한 **최신 Skyrim SST**를 최우선으로 한다.
- Elder7 SST는 v1 참고자료일 뿐 v2 기준으로 고정하지 않는다.
- SST 전체를 파싱한 뒤 Oblivion에 실제 등장하는 항목만 추려 전용 용어집을 만든다.
- 동일 영어 원문에 여러 번역이 있으면 자동 확정하지 않는다.
- 충돌 목록을 만들고 Sol이 문맥/빈도/시리즈 용례를 보고 확정한다.
- 프로젝트 고유 예외는 별도 override 테이블로 관리한다.

## 6. 기술적 번역 금지 / 안전 규칙

- RACE/FULL은 영어 원문 유지.
- 일반 대사/설명 속 종족명은 한국어 번역 가능.
- CELL/FULL, WRLD/FULL 등 저장 안정성에 영향 가능한 위치명은 v1 안전 규칙을 검토한 뒤 처리.
- EDID, 스크립트, 파일 경로, 내부 식별자, 바이너리/포맷 제어값은 번역하지 않는다.
- `%s`, `%d` 등 placeholder, 줄바꿈, 마크업/태그는 반드시 보존.
- 메뉴 GMST 926개는 플레이어 노출 마스터 목록으로 취급하며 임의 제외하지 않는다.

## 7. 번역 파이프라인

1. 최신 SST 전수 파싱 및 정규화
2. Oblivion 정품 원문 전수 추출
3. SST와 Oblivion 원문 교차 → 전용 용어집 생성
4. 기술적 번역 금지 규칙 적용
5. 문맥 포함 JSON 생성
6. Gemini Flash Lite 번역
7. Sol이 영어 원문과 직접 대조 검수
8. 전역 QA
9. 빌드 입력 확정
10. 테스트 빌드 및 diff 검증

## 8. Gemini 운영

사용 가능한 모델 계열:
- Gemini 3.5 Flash Lite
- Gemini 3.1 Flash Lite

실제 API 모델 ID는 작업 시점에 공식 모델 목록으로 확인한다.

제한 기준:
- RPM 15
- TPM 250,000
- RPD 500

API 키는 로컬 비밀 파일에서만 읽고 Git/채팅/로그에 값 자체를 출력하지 않는다.
4개 키가 동일 프로젝트 쿼터를 공유할 가능성을 고려하며 4배 쿼터로 가정하지 않는다.
`429 / RESOURCE_EXHAUSTED`는 기록하고 백오프/재시도/키 전환 로직을 사용한다.

## 9. 번역 JSON 핵심 필드

`source_file`, `record_type`, `formid`, `editor_id`, `field`, `occurrence`,
`quest_stage`, `speaker`, `quest/topic context`, `source_english`,
`glossary_hits`, `constraints`

- INFO: 화자/퀘스트/앞뒤 대화 문맥 포함
- BOOK/NOTE: 줄 단위가 아니라 문서 전체 단위
- QUST/LSCR: stage/연속 문맥 유지
- DIAL/FULL: 토픽 구조 별도 검증
- v1 번역을 Gemini의 정답 예시로 넣지 않는다.

## 10. Sol 검수 기준

Gemini 결과는 자동 확정하지 않는다.

우선순위:
1. 새 Gemini 번역 채택
2. v1이 더 좋으면 참고하여 채택
3. 둘 다 부족하면 Sol이 새로 번역

전역 검사:
- 동일 원문 상이 번역
- 용어 불일치
- 불필요한 영어 잔존
- `???`
- placeholder 손실
- 줄바꿈/태그/마크업 파손

## 11. 현재 단계

v1.0.2 릴리즈는 완료 및 동결.
다음 단계는 **최신 Skyrim SST를 입력받아 v2 용어집과 신규 원문 추출 파이프라인을 시작하는 것**이다.
