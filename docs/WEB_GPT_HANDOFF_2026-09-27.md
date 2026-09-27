# 웹 GPT 인계 보고서 — Oblivion Original 한국어화

작성일: 2026-09-27. 작업 루트: `D:\Codex_Trans\오블리비언`.

## 이번 작업의 산출물

- GitHub 저장소: <https://github.com/munument1/-KR-Oblivion-Translation>. 본편 설치기 v0.1.5 릴리스: <https://github.com/munument1/-KR-Oblivion-Translation/releases/tag/v0.1.5>. 원본 게임의 `Oblivion.esm` 및 공식 DLC ESP에서 검증된 문자열만 바꾸어 MO2 모드 폴더를 만드는 `install.bat` + `OblivionKRBuilder.exe` 패키지다. 본편 원본이나 번역 적용 ESM/ESP는 GitHub 압축파일에 넣지 않는다.
- 별도 넥서스 업로드용 ZIP: `dist\Unofficial_Oblivion_Patches_KR_3.5.9a_1.6.2_v27.zip`. 사용자가 넥서스에는 **이 언오피셜 패치 한국어 ESP만** 올린다. ZIP에는 기본 ESP 11개, 선택 ESP 2개, 한국어 README, 검증 JSON만 들어 있다. 최신 영문 원본 패치 3종 자체나 본편 번역 ESM은 포함되지 않는다. 제작자 허락은 사용자가 받았다고 명시했다.
- 인트로와 아웃트로만 자막 대상: `OblivionIntro.bik`, `OblivionOutro.bik`. 설치기가 FFmpeg 및 RAD Video Tools를 찾으면 원본 영상 해시를 확인하고 한국어 자막 BIK1을 출력 모드에 생성한다. 다른 영상은 처리하지 않는다.

## 사용한 원본과 번역 기억

- 바닐라 원본: `C:\Games\Steam\steamapps\common\Oblivion\data\Oblivion.esm` 및 같은 Data 폴더의 공식 DLC ESP.
- 최신 언오피셜 패치 원본: 사용자가 제공한 데스크톱 7z 세 개에서 `_build\latest_patch_source\UOP`, `USIP`, `UODP`에 추출. UOP 3.5.9a, USIP 1.6.2, UODP v27.
- `applied_translations_v2.csv`, `patch_translation_memory.csv`, `legacy_carrier_completion.csv`, `vanilla_completion.csv`, `quest_loading_translations.csv`, `exe_gmst_*.csv`는 기존 한글패치에서 회수하거나 원문 대조로 보강한 문자열 자료다. 구버전 패치의 기능 레코드는 최신 패치로 복사하지 않는다.
- 리마스터 CSV는 이번 Original 출력에 사용하지 않았다. 단순 문자열 순서 매칭 금지. 향후 사용 시 FormID/EditorID/필드/발생 순서/INFO 응답/QUST 단계/원문 해시를 검증해야 한다.

## 검증된 결과와 한계

- 본편 설치기: 기존 필드 번역 17,891건(그중 `Oblivion.esm` 16,915건), 새 GMST 설정 396건. Python 빌더와 EXE 빌더의 출력 플러그인 SHA-256이 모두 같았다. 원본과 출력의 레코드·그룹 식별자 및 컴파일된 스크립트 해시도 같았다.
- 본편 `INFO/NAM1`는 전체 23,877건 중 2,046건만 번역되어 **21,831건(약 91.4%)이 남아 있다**. `DIAL/FULL`은 3,813건 중 1,333건 번역. `LSCR/DESC` 로딩 문구는 337건 전부 번역. 따라서 완역이라고 표기하거나 일반 대화가 모두 한글이라고 주장하면 안 된다.
- 언오피셜 패치 ZIP은 최신 영문 ESP 14개를 재구성했고, 번역이 없는 선택 ESP 1개를 제외한 13개를 포함한다. 번역 문자열은 7,276건이며 모든 ESP의 레코드·그룹 식별자/컴파일 스크립트 해시가 영문 원본과 같다. 장소명 `CELL/FULL`, `WRLD/FULL` 1,410건은 영어로 유지했다.
- 언오피셜 패치가 직접 가진 `INFO/NAM1` 3,126건 중 2,365건, `DIAL/FULL` 533건 중 466건에 한국어를 적용했다. 남은 해당 패치 대사 761건과 선택지 67건은 영어다. 이는 본편 전체 대사 수와 다른 분모다.
- 초기 레코드 단위 검사는 본편 한글을 UOP가 영어로 되돌릴 수 있는 `INFO` 후보 171건을 보였지만, **같은 레코드 내부의 개별 문장 순서로 다시 비교하자 INFO 회귀는 확인되지 않았다**. 따라서 171건을 확정 결함으로 취급하지 말 것. 퀘스트 `QUST/CNAM`은 단계와 같은 단계 안의 발생 순서를 함께 대조해야 한다.
- 인트로/아웃트로 자막 BIK는 각각 1280×720, 약 115.48초/58.02초이며 음성 트랙 유지와 자막 프레임 시각 검사를 통과했다. 새 일반 대사, 선택지, 새 UOP ESP 조합의 게임 안 작동은 아직 사용자 플레이 검사 전이다.
- 일반 저장 실패 재현 때문에 장소명은 영어로 유지한다. 이전 저장 안전판은 MO2에서 일반 저장 생성과 불러오기가 확인됐다. 자동 저장이나 콘솔 `save TestSave` 성공만으로 일반 저장 성공을 판단하지 말 것.

## 재현과 이어서 할 일

1. 본편 빌드: `python build_vanilla_overlay.py --data-dir "C:\Games\Steam\steamapps\common\Oblivion\data" --output ".\output\Oblivion_KR_Mod"`. 자막까지 강제 검사할 때 `--video-subtitles required`를 붙인다. 기본 BAT는 `auto`로 도구가 없으면 영상만 건너뛴다.
2. 언오피셜 빌드: `python build_unofficial_release.py --source ".\_build\latest_patch_source" --prior-kr "D:\Oblivion MO2\mods" --output ".\_build\uop_release_stage_v016" --vanilla-audit ".\_build\vanilla_v016_compact_test\translation_audit.json"`, 이어 `python package_unofficial_release.py --stage ".\_build\uop_release_stage_v016" --output ".\dist\Unofficial_Oblivion_Patches_KR_3.5.9a_1.6.2_v27.zip"`.
3. 다음 핵심 과제는 남은 `INFO/NAM1` 21,831건과 `DIAL/FULL` 2,480건의 번역 원천 확보 및 신뢰도 높은 레코드별 매칭이다. 현재 자료만으로 완역이라고 볼 수 없다. 대화 응답, 선택지, 저널, 책 본문은 각각 별도 누락 감사를 유지한다.
4. MO2 게임 검사: 기존 `-KR` 언오피셜 모드는 끄고 새 ZIP 하나만 영문 원본보다 높은 모드 우선순위에 설치한다. 새 게임과 기존 저장에서 대사·선택지·저널·로딩 화면, 인트로/아웃트로, 수동 **새 저장 파일 생성 및 불러오기**를 검사한다. 실제 메뉴 문구는 화면 기록과 FormID를 묶어 보고한다.
5. 넥서스 업로드는 사용자가 직접 수행한다. 업로드 설명에는 대상 원본 버전 3종, 원본 모드 선행 설치, 번역 범위, 일반 저장을 위한 장소명 영어 유지, 미완역 상태, 게임 안 검증 상태를 적는다.
