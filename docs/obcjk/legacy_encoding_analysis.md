# 기존 한국어 패치 인코딩 분석

기준: v1.0.4 `be9140e`, 2026-10-01 실제 CSV 조사. 번역문 수정이나 재번역은 수행하지 않았다.

## 실제 흐름

`한국어 Unicode → 준비 단계에서 custom encoder → CSV의 legacy hex → 빌더 bytes.fromhex → ESP/ESM 문자열 → TheGreatestKorean .fnt/.tex → 게임 표시`

`oblivion_korean_codec.py`의 `encode_hangul`은 현대 한글 11,172음절을 초성/중성/종성으로 나누고 커스텀 2/3-byte 글리프 조합을 생성한다. 이것은 UTF-8/CP949/EUC-KR이 아니다. 현재 모듈에는 전체 문자열 decoder가 없다.

현재 공식/언오피셜 빌더는 `encode_hangul`을 호출하지 않는다. 이미 만들어진 hex를 읽고 적용한다. `Translation.korean`의 타입도 Unicode 문자열이 아닌 `bytes`다. CLI에 backend 옵션만 추가해서는 인코딩이 바뀌지 않는다.

## 데이터 종류와 조사 결과

PyInstaller spec에 포함된 CSV 22개와 언오피셜 빌더의 `patch_completion.csv` 1개, 합계 84,349행을 읽었다. 전체 컬럼·행 수·Unicode/hex 칼럼·비어 있는 텍스트·제한적 왕복 비교 결과는 [csv_inventory.json](csv_inventory.json)에 있다. 이것은 최종 적용 문자열 수가 아니라 여러 중복 memory를 합친 입력 행 수다.

| 입력 종류 | Unicode | legacy byte source | 주의점 |
|---|---|---|---|
| applied/remaster/manual/final-review memory | 대부분 `new_korean` | `new_bytes_hex` | 다수는 Unicode와 hex가 함께 있다 |
| 기존 메뉴 105개 | `new_korean` | `new_bytes_hex` | EditorID/occurrence 유지 |
| 새 메뉴 821개 | `korean` | `encoded_hex` | 빈 문자열 한 행은 정상 NUL-only인지 구분 |
| EXE GMST translation/extra | `korean` | `encoded_hex` | v1.0.4 UI 조합 표현 유지 |
| QUST/LSCR 424개 | 한국어 칼럼 없음 | `encoded_hex` | stage/occurrence별 복원 필요 |
| patch completion 1개 | 한국어 칼럼 없음 | `target_hex` | source_hex는 영어 원문 확인용 |
| prior KR ESP 기반 memory | 파일 내 바이트 | 기존 KR 문자열 | Unicode가 있다고 가정할 수 없음 |

Unicode 칸이 비어 있고 legacy hex에 번역이 있는 행:

- `vanilla_completion.csv`: 349/355.
- `patch_translation_memory.csv`: 7,275/7,275.
- `legacy_carrier_completion.csv`: 118/118.
- `legacy_full_recovery.csv`: 31,497/31,497.
- 합계 **39,239행**. `new_korean.encode('utf-8')`로만 처리하면 이 번역들이 빈 문자열이 된다.

ASCII+현대 한글만 있는 비어 있지 않은 Unicode 문자열을 `encode_hangul`과 ASCII로 인코딩해 legacy hex와 비교했을 때 차이는 발견하지 못했다. 다른 문자(스마트 따옴표, Unicode 문장부호 등)가 있는 159행은 이 제한적 비교 대상에서 제외했다. 완전한 decoder 검증을 통과한 것은 아니다. 39,239건의 비교 차이는 빈 Unicode 칸 때문에 발생하며 번역 오류 39,239건을 뜻하지 않는다.

`final_review_override.csv`는 현재 **19,871행**이다. 과거 문서의 12,122행은 현재 기준으로 쓰지 않는다. 최종 override의 우선순위와 v1.0.4의 `sTo`, `for/in/on`, 효과 용어 변경을 모두 보존해야 한다.

## 빌더 소비 지점

- `build_vanilla_overlay.py::load_translations`: `new_bytes_hex`, source/record/FormID/field/EDID/occurrence 매칭.
- `load_menu_gmsts`: 기존 105개는 일반 table에 추가, 새 821개는 `encoded_hex`를 별도 삽입.
- `load_quest_loading_translations`: 424개 `encoded_hex`, 원문 `source_hex`, quest stage/occurrence 확인.
- main의 final menu override: `new_bytes_hex`를 다시 읽는다. 여기까지 backend가 전파되어야 한다.
- `BASE_MENU_GMSTS`: 코드 내부에 legacy hex 상수가 존재한다. 실제 사용 여부와 관계없이 backend 분리 때 검토 대상이다.
- `build_unofficial_release.py`: 기존 KR ESP를 fallback으로 사용하고 공식 audit/translation table/final override/quest-loading/manual completion/선택적 `_build/nexus_patch_completion.csv`로 덮는다. 이 모든 입력을 동일 backend에 맞춰야 한다.
- `assets/menus/strings.xml`: bytes 자산이다. 그대로 복사하는 방식이므로 Unicode 선언만 바꾸어 해결되지 않는다.
- `OblivionKRBuilder.spec`: legacy 폰트와 메뉴 assets를 통째로 포함한다. obCJK 빌드에서는 자산 선택이 필요하다.
- `install.bat`: legacy 폰트 INI 변경과 동영상 burn-in auto가 기본이다. obCJK 설치기와 분리해야 한다.

`exe_gmst_translations.csv`와 `exe_gmst_extra.csv`는 spec에 포함되지만 현재 vanilla main의 직접 table 목록에는 없다. 기존/새 메뉴 CSV로 이미 반영된 자료와 보조 자료를 구분하여, 전환 시 중복 적용이나 v1.0.4 되돌림을 방지한다.

## 현재 검증기의 한계

기존 `structure_signature`는 record/group bounds, 레코드 헤더 기반 identity, SCPT 전체 및 QUST/INFO의 script subrecord hash를 확인한다. **모든 레코드의 EditorID·서브레코드 순서·모든 비문자열 값 동일성을 완전히 검증하지는 않는다.**

현재 원본→한국어 빌드에서는 메뉴 GMST 821개를 추가하고 TES4 count/GRUP size를 수정한다. 원본과 변환본의 레코드 수가 무조건 같아야 한다는 규칙을 적용하면 정상 삽입도 실패한다. backend 비교는 동일한 legacy v1.0.4 결과를 기준으로 레코드 수 동일성을 검사하고, 원본과 비교할 때는 명시한 추가 GMST만 예외로 둔다.

이번 조사에서는 ESP/ESM을 자체 parser로 열거나 기존 빌더를 실행하지 않았다. 플러그인 레코드 readback과 이후 제작·검증은 xEdit MCP 경로로 진행한다.
