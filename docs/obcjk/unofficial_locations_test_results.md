# 비공식 패치 UTF-8 및 한글 위치명 적용 — 2026-10-01

사용자가 비공식 패치 번역의 UTF-8 적용과 한글 위치명 추가를 요청하여 `obcjk-save-test`에 적용했다. Default, 기존 KR 모드, 기존 세이브 및 legacy 빌드의 위치명 정책은 보존한다.

## 적용 구성

| 모드 | 역할 |
|---|---|
| `Oblivion_KR_obCJK_UTF8_Test` | 본편·공식 DLC UTF-8 번역과 메뉴/obCJK 설정 |
| `UOP_KR_obCJK_UTF8_Test` | UOP 및 동봉 ESP의 기존 번역을 UTF-8로 변환 |
| `USIP_KR_obCJK_UTF8_Test` | USIP 번역의 UTF-8 변환 |
| `UODP_KR_obCJK_UTF8_Test` | 비공식 DLC 패치 10개 ESP의 UTF-8 변환 |
| `Oblivion_KR_obCJK_Locations_Test` | 위 파일 중 21개에 한글 CELL/WRLD FULL을 추가한 선택 가능한 시험용 변형 |

원본 비공식 패치 모드 3개도 켜서 메시·텍스처 등 자산을 제공한다. 기존 커스텀 인코딩 KR 모드는 끈다. obCJK 원본 DLL을 사용하고 시험판 INI는 `ActiveCodePage=UTF8`, Malgun Gothic, `SaveDiagEnable=1`이다.

플러그인 25개의 활성 상태와 로드 순서는 **Default의 plugins.txt와 동일**하게 맞췄다. MO2 GUI, 저장된 파일, 실제 플러그인 origin을 확인했다. missing-master 경고는 0개였다. 한글 위치명 모드는 가장 높은 우선순위에서 같은 플러그인 파일을 제공하므로, 해당 모드만 끄면 기본 UTF-8 번역의 영어 위치명으로 돌아간다.

## 위치명 변환과 보존 검사

`build_obcjk_locations.py`는 이미 검증된 UTF-8 출력 파일을 읽어 별도 폴더에 쓴다. CELL/WRLD FULL 외에는 바꾸지 않으며, 결과 파일을 기존 validator로 다시 읽어 모든 나머지 서브레코드 bytes·헤더·그룹 구조·스크립트 signature를 비교한다.

우선 기존 번역 CSV의 파일·FormID·원문·가능한 EDID를 매칭한다. 직접 매칭이 없으면 **영문 전체 문자열이 정확히 같고 기존 번역이 하나로만 확정되는 경우**에 한해 번역 메모리를 재사용한다. 유사 문자열 추정이나 새 기계 번역은 사용하지 않았다. 각 결과에 `match_kind`와 CSV 행 provenance를 기록한다.

- 파일별 적용: CELL 3,169개 + WRLD 119개 = **3,288개 FULL 필드**, 21개 파일. 같은 장소의 master/patch override가 중복된다.
- 실제 활성 로드 순서와 각 파일의 master 인덱스를 해석하여 마지막 override를 계산한 결과: **한글 CELL 1,681개, WRLD 65개**. 이 숫자는 파일 분석 결과이며 게임 화면에서 전부 방문한 수치가 아니다.
- 현재 제공되는 CELL/WRLD FULL 전체에서 잘못된 UTF-8 문자열은 0개였다.
- 원문 변경/모호성 때문에 매칭하지 못한 기존 레코드 후보 132개는 영어를 유지했다. 번역 자료가 없는 다른 이름도 이 적용 완료 수치에 포함하지 않는다.
- 초기 감옥 CELL `0001FBB9`의 최종 FULL은 UOP의 **제국 감옥**이다. 해당 위치에서 저장하는 실제 시험은 남아 있다.

감사 파일은 `_build/obcjk/korean-locations-final/location_validation.json`이다. 실제 사용 파일/로드 순서는 `_build/obcjk/utf8-test/location-active-files.json`, 최종 위치명 계산은 `location-effective.json`에 있다. 전체 비공식 UTF-8 변환 검사 범위는 [기본 플러그인 결과](utf8_plugin_test_results.md)를 따른다.

```powershell
python build_obcjk_locations.py --input-dir _build/obcjk/cli-final --input-dir _build/obcjk/full-uop --input-dir _build/obcjk/full-usip --input-dir _build/obcjk/full-uodp --tables-dir _build/obcjk/utf8-test/tables --output _build/obcjk/locations-output
```

추가 단위 검사에서 정확한 원문 매칭, upstream에서 이름이 달라진 경우의 미적용, 번역이 충돌하는 경우의 미적용, CELL의 비문자열 DATA 보존을 확인했다. 기본 인코딩/플러그인 검사와 합쳐 10개 검사다.

## 실행 결과

21:34:15(KST)에 위 구성 전체로 실행했다. UTF-8 비공식 패치와 한글 위치명을 함께 켠 상태에서 메인 메뉴에 진입했고, 수분 후에도 종료 없이 한글 메뉴가 표시되는 것을 직접 확인했다. 같은 실행의 obCJK 로그에서 UTF8 활성화, SavePathFix/CreateFileW/SaveList 훅 초기화를 확인했다. 실행 I의 로그는 `_build/obcjk/utf8-test/run-I-unofficial-locations-*.log`에 보관한다.

훅 초기화 성공은 .ess 생성/목록/재로드 성공을 뜻하지 않는다. 자동 입력이 게임 메뉴 선택으로 안정적으로 이어지지 않고 사용자가 외출 중이므로 **새 게임, 실제 위치명 표시, 저장 및 재로드는 아직 미검증**이다. 기존 저장 파일에 쓰는 작업은 하지 않았다.

검사 후 메뉴 대기 상태에서 시험 프로세스를 종료하고 시험 프로필의 구성은 그대로 남겼다. 기존 보존 목록 99개와 Documents INI는 해시 변경이 없었다. 설치된 위치명 변형 21개는 검증된 출력과 해시가 모두 같고, 시험 프로필의 plugins.txt는 Default와 동일했다. 시험 프로필에 생성된 .ess는 없다. 임시 MO2 full-control 설정을 제거하고 MCP 권한이 metadata-editable로 돌아온 것을 확인했다. 보존 검사 결과는 `_build/obcjk/utf8-test/unofficial_locations_preservation.json`이다. 후속 저장 검사는 [한글 위치명 저장 계획](korean_location_save_test.md)에 따라 테스트 프로필의 새 슬롯만 사용한다.
