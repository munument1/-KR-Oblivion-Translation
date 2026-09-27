# CODEX 긴급 감사 인계 — 번역 대량 누락 원인 재조사

작성일: 2026-09-27

## 결론부터

현재 `Oblivion.esm INFO/NAM1 23,877건 중 2,046건`만 적용된 상태를 "번역 원천 부족"으로 단정하면 안 된다. Google Drive 원천과 현재 코드를 재감사한 결과, **기존 번역을 추출/매칭 단계에서 대량 탈락시켰을 가능성이 높다. 새 AI 번역을 시작하기 전에 반드시 원천 회수 감사를 먼저 수행한다.**

## 확인된 원천

Google Drive 폴더:
`https://drive.google.com/drive/folders/1d-fT-l49QHwUwkXQtT78SvbtWzCs83WE`

구조:
- 1. 오리지널 ESM
- 2. 오리지널 번역 자료
  - `오블 엘갤럼 한글패치 합친버전v2`
  - `Unofficial Oblivion Patch.esp` 약 20.3 MB
  - `Unofficial Shivering Isles Patch.esp` 약 12.4 MB
- 3. 리마스터 번역 자료
  - `zzzKorean260805_P.pak`
- 4. 번역 결과물
- 4/90 중간 분석자료에는 `remastered_korean_locres.csv`가 존재

`remastered_korean_locres.csv` 실측:
- 56,527 rows
- 그중 Unicode Hangul 포함 rows: 55,819
- 즉 리마스터 쪽 한국어 원천 자체는 매우 크다.

## 구형 Oblivion 한글 ESP 인코딩 주의

구형 UOP의 실제 INFO/NAM1 바이트를 직접 검사했다. 예:
`DD A2 07 C6 84 B3 89 20 BD 80 B8 89 B4 80 2E 00`

이 문자열은 UTF-8 / CP949 / EUC-KR로 정상 디코딩되지 않는다. 기존 패치는 `TheGreatestKorean*.fnt/.tex`와 결합된 **Oblivion용 커스텀 한글 바이트 매핑**을 사용한다.

따라서 다음은 금지:
- Unicode Hangul regex로 구형 ESP의 번역 여부 판정
- CP949/EUC-KR 디코딩 성공 여부로 번역 여부 판정
- `new_korean` Unicode 컬럼이 비어 있다는 이유로 미번역 판정

구형 번역의 신뢰 가능한 실체는 현재 CSV에서도 사용 중인 `new_bytes_hex` 같은 raw encoded bytes다.

## 확인된 코드상 대량 탈락 위험

### 1. extract_legacy_carrier_memory.py

현재 코드:

```python
legacy=read_records(args.legacy_uop)
latest_keys=read_records(args.latest_uop).keys()
carriers={key:legacy[key] for key in legacy.keys()-latest_keys if key[1]>>24==0}
```

즉 **구형 UOP와 최신 UOP에 동시에 존재하는 레코드는 legacy carrier 회수 대상에서 전부 제외**한다.

이 스크립트는 이름 그대로 "latest에서 사라진 carrier"만 복구하는 보조 경로일 뿐, 구형 한글패치 전체 번역을 회수하는 전수 추출기가 아니다. 이 결과를 전체 legacy 번역 회수량으로 간주하면 안 된다.

또 다음 조건도 있다:

```python
if len(source_values)!=1 or len(targets)!=1:
    continue
```

동일 subrecord field가 반복되는 레코드는 통째로 탈락한다. INFO/QUST 등 반복/순서 문맥이 필요한 레코드에서는 occurrence-aware 매칭이 필요하다.

### 2. build_vanilla_overlay.py

적용 키는 기본적으로:
`(target, record_type, formid, field)`

그리고 실제 적용 시:
- 현재 영어 문자열과 `old_english` exact match
- optional EditorID exact match
- 같은 키 후보의 replacement가 하나로 합의되어야 함

이 안전장치 자체는 유지해야 한다. 문제는 **그 전에 translation CSV를 만드는 단계에서 legacy/remaster 원천이 얼마나 탈락했는지 감사하지 않았다는 것**이다.

## Codex가 지금 해야 할 일

새 AI 번역 금지. 먼저 아래 audit를 구현하고 실행한다.

1. **legacy UOP/USIP full text extraction**
   - 최신 UOP와 겹치는 레코드도 제외하지 말 것.
   - `TEXT_FIELDS` 전체에 대해 raw bytes를 추출.
   - original Oblivion.esm/official DLC의 동일 FormID 레코드와 비교.
   - EditorID, record type, FormID, field, field occurrence index를 보존.
   - 반복 field는 occurrence index를 사용하고 무조건 skip하지 말 것.
   - legacy raw target bytes가 original English bytes와 다르고 NUL-safe이면 번역 후보로 기록.
   - CELL/FULL, WRLD/FULL은 저장 문제 때문에 **감사에는 포함하되 자동 적용은 금지**.

2. **remaster locres full audit**
   - `remastered_korean_locres.csv` 56,527 rows를 현재 사용된 remaster match CSV와 비교.
   - used / unmatched / ambiguous / remaster-only UI로 분류.
   - 단순 순서 매칭 금지.
   - 가능한 경우 original English source + FormID/EditorID/record/field/occurrence/quest stage/INFO context로 검증.

3. **coverage matrix 생성**
   최소 컬럼:
   - record_type
   - field
   - total_original_strings
   - legacy_candidates
   - remaster_candidates
   - currently_applied
   - recoverable_not_applied
   - ambiguous
   - truly_no_translation_source

   특히:
   - INFO/NAM1
   - DIAL/FULL
   - QUST/CNAM
   - BOOK/DESC 또는 본문 필드
   - LSCR/DESC
   - GMST/DATA
   - NPC_/FULL
   - CREA/FULL
   - WEAP/FULL
   - ARMO/FULL
   - ALCH/FULL
   - SPEL/FULL
   - MISC/FULL
   - CELL/FULL, WRLD/FULL (audit only)

4. **누락 이유별 CSV 생성**
   - legacy_overlap_excluded
   - repeated_field_excluded
   - english_exact_mismatch
   - editorid_mismatch
   - ambiguous_replacement
   - remaster_unmatched
   - no_source

5. recoverable 후보를 적용한 뒤 다시 전체 coverage를 계산한다.

## 완료 조건

`INFO/NAM1 2,046/23,877` 숫자를 단순히 AI 번역으로 메우지 않는다.

먼저 보고할 것:
- 구형 한글패치에 실제 존재하는 INFO/NAM1 raw translation candidate 수
- 그중 현재 CSV/ESM에 적용된 수
- 현재 미적용이지만 안전하게 회수 가능한 수
- 진짜 번역 원천이 없는 수
- DIAL/QUST/BOOK 및 나머지 TEXT_FIELDS에 대한 동일 통계

그 다음에만 "진짜 미번역"을 AI 번역 대상으로 넘긴다.

## 유지해야 할 안전 조건

- gameplay record 생성/복사 금지
- compiled scripts 변경 금지
- FormID/record identity 유지
- raw source validation 유지
- CELL/FULL, WRLD/FULL 자동 적용 금지
- 순서만으로 remaster 매칭 금지
- 출력 후 structure_signature 및 save/load 검증 유지
