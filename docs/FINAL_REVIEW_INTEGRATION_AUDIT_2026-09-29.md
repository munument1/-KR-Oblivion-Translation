# Oblivion Original 한국어 번역 - 최종 검수 통합 감사

기준일: 2026-09-29

## 1. GitHub 상태
- 감사 시작 시 로컬 main과 GitHub origin/main은 동일한 커밋 8f73080이었다.
- 즉 이전 채팅에서 이미 커밋한 작업 중 로컬에만 남아 있던 숨은 커밋은 없었다.
- v1.0.1 태그 이후의 인트로/아웃트로 수정은 GitHub main에는 올라가 있으나 기존 v1.0.1 Release ZIP에는 포함되지 않는다.
- GitHub push와 Release asset 업로드는 별개이며 자동 Release workflow는 없다.

## 2. 최종 검수 작업의 통합 방식
- 최종 Source of Truth: _build/final_review_export/GLOBAL_EFFECTIVE_POST_REVIEW_GEMINI_HIGH_WORKING.csv
- 총 47,841 레코드.
- v1.0.1 기준본과 구조 키로 비교한 현재 최종 변경분: 12,417건.
- 일반 빌더 override: 12,122건 -> final_review_override.csv
- QUST/LSCR 특수 경로 변경: 295건 -> quest_loading_translations.csv
- 따라서 중간 HIGH/MEDIUM/CONFLICT/BOOK/TOPIC 파일이 Git에 직접 올라가지 않아도 최종 효과는 위 두 입력으로 재현된다.

## 3. 검수 완료 상태
- CONFLICT 288/288 완료.
- REVIEW 38/38 완료: FIX 35 / KEEP 3.
- TOPIC_CHECK 2,924/2,924 완료.
- BOOK/DESC 939건: 본문 빈 레코드 0, 비정상 단문 0.
- ??/??? 깨짐 0, Unicode replacement character 0.
- DIAL/FULL 영문 잔재 0.
- 매드니스 -> 광기 전역 통일 완료.
- 2026-09-29 추가 용어 정규화:
  - Jyggalag: 지갈렉
  - Skyrim: 스카이림
  - Boethiah: 보에시아
- Source of Truth의 잘못된 변형 지갈락 / 스키림 / 보에디아는 번역문 기준 각각 0건.

## 4. 빌드 재현 검증
- 정식 build_vanilla_overlay.py에 final_review_override.csv 및 최종 quest_loading_translations.csv를 연결했다.
- Steam 원본 Data에서 현재 입력으로 테스트 빌드 성공.
- 재추출 가능한 47,780건을 최종 Working과 비교: 번역 불일치 0.
- 61건은 TEST/NQD/내부 레코드 또는 원문과 최종 문자열이 동일해 패치 문자열로 추출되지 않는 항목.
- 현재 delta는 12,417건(일반 override 12,122 + QUST/LSCR 특수 경로 295)이며, 재추출 가능한 전체 47,780건은 현재 Working과 번역 불일치 0.
- Python 빌더와 현재 PyInstaller EXE 출력 파일 21개를 SHA-256 비교: 차이 0.

## 5. EXE 포함 데이터 검증
PyInstaller spec에는 다음 최종 입력/자산이 포함된다.
- final_review_override.csv
- quest_loading_translations.csv
- video_subtitles/OblivionIntro.srt
- video_subtitles/OblivionOutro.srt
- 한국어 Fonts / menus assets
- 기존 translation memory/completion CSV 일체

2026-09-29 엘더7 고유명사 정규화 후 PyInstaller EXE를 다시 빌드했으며, 같은 원본 Data를 대상으로 Python 빌더와 EXE 빌더의 21개 출력 SHA-256은 모두 동일했다.

## 6. Git에 반드시 포함되어야 하는 현재 변경
- .gitignore
- OblivionKRBuilder.spec
- build_vanilla_overlay.py
- quest_loading_translations.csv
- final_review_override.csv
- docs/FINAL_REVIEW_INTEGRATION_AUDIT_2026-09-29.md

현재는 아직 commit/push/release 하지 않았다.

## 7. 주의
- 기존 v1.0.1 Release ZIP은 v1.0.1 태그 시점 산출물이므로 이후 자막 수정과 이번 최종 검수는 포함하지 않는다.
- 다음 Release에서는 반드시 현재 소스에서 OblivionKRBuilder.exe와 ZIP을 새로 만들어야 한다.
- 이번 감사 중 생성한 dist/OblivionKRBuilder.exe는 로컬 검증용이며 GitHub Release에는 업로드하지 않았다.

## 8. 커밋 예정 diff 재검증
- build_vanilla_overlay.py의 중복 GMST override 블록 1개를 제거했다. 최종 구현은 main()의 단일 경로만 사용한다.
- quest_loading_translations.csv는 레코드 수 424건, 키 중복 0건을 유지한다.
- HEAD 대비 의미 변경은 encoded_hex 295건뿐이다: LSCR 284건 / QUST 11건.
- original_english, source_hex, source 메타데이터 변경은 0건이다.
- final_review_override.csv는 12,122건이며 구조 키 중복 0건이다.
- final_review_override.csv와 현재 Source of Truth의 일반 delta를 재대조: left_only 0 / right_only 0 / 번역 불일치 0 / 인코딩 불일치 0.
- 현재 정식 Python 빌더 출력 21개와 현재 PyInstaller EXE 출력 21개 SHA-256 비교 결과: 차이 0.
- quest_loading_translations.csv는 저장소에서 CSV를 -text로 관리하고 기존 blob이 CRLF라, 변경 행에 대해 git diff --check가 CR을 trailing whitespace로 표시할 수 있다. 의미 데이터 이상은 아니며 구조/컬럼 비교로 별도 검증했다.

## 9. 이전 약 1.3만 건 검수의 현재 Source of Truth 반영 감사
이전 단계의 확정 검수 파일은 다음 세 묶음이며 합계는 정확히 13,047건이다.
- HIGH_4473_FINAL_REVIEWED.csv: 4,473건
- MEDIUM_5650_FINAL_REVIEWED.csv: 5,650건
- TOPIC_CHECK_2924_FINAL.csv: 2,924건

현재 Source of Truth와 구조 키를 비교할 때, 예전 QUST 단계 값의 30.0 형식과 현재 30 형식 차이를 숫자형으로 정규화해서 대조했다.
- 구조적으로 누락된 레코드: 0건.
- HIGH: 현재 값과 동일/줄바꿈만 동등 3,838건, 이후 검수로 더 변경 635건.
- MEDIUM: 현재 값과 동일 3,645건, 이후 검수로 더 변경 2,005건.
- TOPIC_CHECK: 현재 값과 동일 2,914건, 이후 검수로 더 변경 10건.
- 합계: 동일 또는 형식 동등 10,397건 + 후속 검수로 갱신 2,650건 = 13,047건.

즉 이전 약 1.3만 건 작업은 빠진 것이 아니라 현재 47,841건 Source of Truth 안에 전부 존재하며, 일부는 이후 BOOK 복구, 대사/토픽 재검수, 용어 정규화 등 더 최신 결과로 덮어쓴 상태다.

## 10. 2026-09-29 용어 수정 감사
Source of Truth의 translation_korean 필드만 대상으로 다음 오표기를 전역 교정했다.
- 지갈락 -> 지갈렉: 130회
- 스키림 -> 스카이림: 11회
- 보에디아 -> 보에시아: 43회
- 총 184회, 174개 레코드 영향.

수정 후 번역문 기준:
- 지갈락 0건
- 스키림 0건
- 보에디아 0건

최종 표기 누적 출현 수:
- 지갈렉 135회
- 스카이림 114회
- 보에시아 45회

이 변경을 Source of Truth -> FINAL_REVIEW_OVERRIDE / quest_loading_translations_FINAL -> 저장소 루트 입력 -> 정식 Python 빌드 -> PyInstaller EXE 빌드 순으로 다시 반영하고 검증했다.
## 11. Skyrim 엘더7 고유명사 기준 통일
- Skyrim 엘더7 TesVTranslator 사용자사전(본편 + Update + Dawnguard + Hearthfire + Dragonborn)을 참고용 고유명사 기준으로 사용했다. 말미르판은 사용하지 않았다.
- 리마스터 한국어 번역은 고유명사 기준으로 사용하지 않는다.
- 고유 인명, 신격명, 지명, 조직명, 종족/설정 고유명, 고유 유물명은 엘더7 표기를 우선한다. 일반 명사와 일반 문장 번역은 이 규칙으로 일괄 변경하지 않는다.
- 사용자 지정 예외: Argonian은 엘더7의 `아고니언`을 따르지 않고 `아르고니안`을 유지한다. 현재 Argonian 원문 포함 191행 중 `아고니언` 0행.
- 엘더7 기준 적용 전 백업 대비 translation_korean 변경 레코드: 801건. 번역문 외 구조/메타데이터 변경: 0건.
- 주요 변경 예: Ayleid `에일리드 -> 아일레이드`, Molag Bal `몰라그 발 -> 몰락 발`, M'aiq `므'아이크/마이크 -> 마'이크`, Shadowmere `섀도미어 -> 셰도우미어`, Mannimarco `매니마코/마니마르코/만니마르코 -> 매니마르코`, Sancre Tor `생커/셍커 토르 -> 생크 토르`, Mythic Dawn `신화 여명회 -> 미씩 던`, Hermaeus Mora `헤르메스 모라 -> 헤르메우스 모라`, Mehrunes Dagon `메르네스 데이건 -> 메이룬스 데이건`.
- 드레모라 계급명도 엘더7 기준으로 통일: Markynaz `마키나스`, Caitiff `카이티프`, Churl `커르`, Valkynaz `발키나스`.
- 고유 유물/고유 명칭 예: Mysterium Xarxes `자서스의 신비`, Blade of Woe `통곡의 단검`, Skull of Corruption `타락의 해골`, Skein of Magnus `매그누스의 실타래`, Mehrunes Razor `메이룬스의 면도칼`.
- 기존 보조 스크립트에 남아 있던 `에일리드`, `신화 여명회`, `작시스의 신비` 하드코딩도 새 기준으로 수정해 재실행 시 역행하지 않도록 했다.
- 새 Source of Truth에서 빌드 입력을 재생성한 결과: delta 12,417 / 일반 override 12,122 / 특수 QUST·LSCR 295. override exactness: left_only 0 / right_only 0 / translation_mismatch 0 / encoded_mismatch 0.
- 실제 Steam Data 빌드 후 재추출 47,780건은 Working과 mismatch 0. 빌드 결과에서 감사 대상 구표기와 `아고니언`은 0건이며 `아르고니안`은 유지된다.
- 새 PyInstaller EXE를 로컬 재빌드했으며 Python 빌더와 EXE의 출력 21개 SHA-256 차이 0.
- commit / push / tag / GitHub Release / Release ZIP 업로드는 하지 않았다.


## 12. 언오피셜 패치 3종 재동기화
- 대상: Unofficial Oblivion Patch, Unofficial Shivering Isles Patch, Unofficial Oblivion DLC Patches의 기존 KR 오버레이.
- 기존 KR은 과거 번역을 기준으로 만들어져 있어 최종 검수본이 동일 본편/DLC 레코드에 반영되지 않는 문제가 있었다.
- build_unofficial_release.py 우선순위를 `최종 검수 final_review_override / QUST·LSCR 특수값 > 기존 KR > 미번역`으로 변경했다.
- 패치 전용 문장은 기존 KR을 fallback으로 유지하며, 원본 FormID/필드/영문 원문이 최종 검수본과 정확히 일치할 때만 최종 검수 번역을 덮어쓴다.
- CELL/WRLD 저장 안전 정책과 패치별 수동/nexus completion 우선순위는 유지한다.
- 최신 원본 14개 ESP를 기준으로 재빌드했고 모든 출력은 원본과 structure_signature가 동일해 레코드 구조/스크립트 변경이 없다.
- 전체 번역 필드 8,821건 중 최종 검수본과 직접 매칭된 필드는 3,295건이며, 기존 KR 문구를 실제로 교체한 필드는 84건이다.
- 기존 KR 대비 총 바이트 변경 텍스트 필드는 86건이다. 추가 2건은 내부용 `NQD Cheydinhal` QUST와 `SE 09 Battling Creature Faction` FACT가 최종 정책에 따라 원문으로 복귀한 경우다.
- UOP Vampire Aging & Face Fix.esp는 한국어 번역 필드가 0건이며 테스트 편의를 위해 MO2형 테스트 묶음에는 원본 동일 파일을 포함할 수 있으나 정식 별도 배포 패키지에서는 제외한다.
- 기존 MO2의 KR 3개 폴더는 테스트 빌드 과정에서 수정하지 않았다.

## 13. 음성 출력 호환성 수정
- 실게임 테스트에서 번역은 정상이나 NPC 음성이 출력되지 않고 일부 자막이 너무 빨리 사라지는 문제가 확인되었다.
- 원인은 RACE/FULL 표시 이름을 한국어로 번역하면 Oblivion의 `Sound\\Voice\\<plugin>\\<Race Name>\\...` 음성 폴더 탐색과 충돌하는 것이었다.
- 본편 최종 Source of Truth에서 RACE/FULL 14건(Sheogorath, Golden Saint, Dark Seducer, Dremora, Argonian, Nord, Breton, Wood Elf, Khajiit, Dark Elf, Orc, High Elf, Redguard, Imperial)을 영어 원문 유지로 변경했다.
- 일반 대사/설명 속 종족명 번역은 그대로 유지하며, `Argonian -> 아르고니안` 사용자 예외도 RACE/FULL 외 텍스트에는 그대로 적용된다.
- 언오피셜 재빌더에도 RACE/FULL을 항상 원문 유지하는 voice-safe 규칙을 추가했다.
- 새 본편 빌드에서 RACE/FULL 변경 0건을 확인했고, 새 PyInstaller EXE와 Python 빌드 출력 21개 SHA 비교 결과 차이 0이었다.
- 사용자 실게임 재검증 결과 NPC 음성과 자막 표시 시간이 정상으로 복구되었다.
