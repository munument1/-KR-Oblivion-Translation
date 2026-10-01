# UTF-8 기본 메뉴 검증 — 2026-10-01

사용자 요청에 따라 **기본 번역 표시 → 본문 번역 → 한글 위치명 저장** 순서로 진행한다. Steam Deck은 제외한다. 아래 결과는 메뉴 XML 범위의 성공이며 전체 ESP/ESM 전환 완료를 뜻하지 않는다.

## 실제 실행

본PC Windows, Oblivion Original Steam 1.2.0.416, xOBSE 22.13, 설치된 obCJK 20260807을 사용했다. `Default`를 세이브 없이 복제한 `obcjk-save-test`에서만 실행했다. LocalSettings/LocalSaves를 켜고 기존 Documents INI를 테스트 프로필로 복사했다.

기존 KR 및 UOP/USIP/UODP 모드는 테스트 프로필에서 껐다. 테스트 프로필의 기본 `.fnt`는 원본 Kingthings/Tahoma/Handwritten을 사용하고, obCJK UTF8의 GDI 글꼴은 시스템에 설치된 Malgun Gothic으로 지정했다. 기존 obCJK DLL/INI는 수정하지 않고 별도 `Oblivion_KR_obCJK_UTF8_UI_Test` 모드의 INI가 우선하도록 했다. DLL을 복제하거나 배포 패키지에 포함하지 않았다.

| 실행 | 시작 시각(KST) | 구성 | 확인 결과 |
|---|---|---|---|
| A | 20:14:31 | 영문 원본+xOBSE | 메인 메뉴 도달, 30초 이상 유지 |
| B | 20:16:39 | A+obCJK UTF8+Malgun Gothic | 영문 메인 메뉴 도달, GDI 글꼴 적용, 30초 이상 유지 |
| C | 20:17:56 | B+UTF-8 strings.xml | 한글 메뉴 표시; legacy DEL 문자가 네모로 표시됨 |
| D | 20:19:13 | C에서 DEL 제거 | 새로하기/불러오기/환경설정/제작진/종료가 네모 없이 표시됨, 수분 유지 |

각 실행의 화면을 Computer Use로 직접 관찰했다. 동일 실행의 OBSE/obCJK 로그를 `_build/obcjk/utf8-test/run-*.log`에 보관했다. A-C는 메뉴 상태에서 비교 실행을 종료하기 위해 테스트 게임 프로세스만 종료했다. 새 게임 또는 저장은 시작하지 않았다.

현재 최소 구성에서는 기존의 메인 메뉴 전 종료가 재현되지 않았다. 이것은 과거 종료의 원인 확정이나 전체 구성의 안정성 증명은 아니다.

설정 항목 선택은 자동 입력으로 전환되지 않아 **설정 화면 내부 동작은 미검증**이다. 메뉴 표시 성공과 메뉴 클릭 동작을 구분한다. NPC 대사/아이템/주문/BOOK/퀘스트/세이브도 아직 미검증이다.

## 구현과 정적 검사

- `oblivion_korean_codec.py`에 텍스트 전용 strict decoder/encoder를 추가했다. 기존 `encode_hangul` 동작을 보존한다. ESP/ESM을 열지 않는다.
- 완성형 한글 11,172개 모두 일대일 왕복 변환, 받침/ASCII/숫자/문장부호/줄바꿈 혼합, 잘린 바이트 거부 검사 3개가 통과했다.
- `build_obcjk_ui.py`는 원본 메뉴 자산을 읽어 정확한 legacy 왕복을 검사한 후 UTF-8, BOM 없음으로 별도 출력한다. 동일 입력 경로에 덮어쓰기를 거부한다.
- 원본 메뉴의 한글 780자와 XML 요소 269개를 유지했다. GDI에서 네모로 보인 DEL(0x7F) 350개만 제거했다. 번역문은 재번역하지 않았다.
- 원본 XML SHA256: `3d65cef1569a7b1045b8598b77655e4579c4bd0c6b9b92adf1fc3f7f0bde256a`.
- 최종 UTF-8 XML SHA256: `8fb0f615fcd045473906ef5e9912e080330b06d8a772ed280c47f18567db2b17`.

```powershell
python -m unittest discover -s tests -p test_legacy_text_codec.py
python build_obcjk_ui.py --output _build/obcjk/utf8-test/ui/menus/strings.xml --report _build/obcjk/utf8-test/ui-report.json
python audit_obcjk_texts.py --output _build/obcjk/utf8-test/tables
```

`audit_obcjk_texts.py`는 원본 CSV를 보존하면서 별도 사본에 Unicode/UTF-8 hex/변환 상태를 추가한다. 기존 Unicode 문자열이 있으면 정확한 legacy bytes 비교를 요구한다. 기존 폰트용으로 정규화된 따옴표/대시/말줄임표/NBSP도 문서화된 치환 후 **전체 문자열 bytes 일치**를 확인하고 원래 Unicode 문장부호를 출력에 유지한다.

84,349행 중 84,343행의 텍스트 변환을 검증했고, 그중 39,659행은 Unicode 칸 없이 legacy hex에서 복원했다. 이 수치는 중복·보조 자료를 포함한 CSV 행 수이며 적용되는 고유 레코드 수가 아니다. 남은 `legacy_full_recovery.csv` 6행은 서양 글꼴 시험 문자/옛 특수문자 또는 다른 legacy bytes 문제로 변환을 차단한다. 해당 행을 빈 번역으로 적용하지 않는다. 감사 명령은 미해결 행이 있으면 exit 1이며 전체 변환 합격으로 판단하지 않는다.

## 본문 변환을 막는 도구 제한

`xedit_start`를 Oblivion 모드로 요청했고, 실제 결과는 다음과 같다.

```text
xedit-client exited 1.
Unsupported game mode: Oblivion. Supported game modes: Fallout4, Skyrim, SkyrimSE, Starfield
```

현재 BGS 스킬은 자체 ESP/ESM parser 사용을 금지한다. 사용자에게 이번 전환에서 기존 프로젝트 빌더를 사용하는 예외를 요청했고, 답변 전에는 본문 ESP를 읽거나 쓰지 않았다. 도구의 모드를 속이거나 직접 xEdit을 띄우는 방식으로 우회하지 않았다.

## 보존과 MO2 변경

승인된 동안만 `.mo2-mcp.json`으로 full-control을 적용했다. 테스트 프로필 복제/모드 생성/INI 변경 후 임시 파일을 제거하고 재bind하여 `permission_ceiling=metadata-editable`로 돌아온 것을 확인했다.

추가된 관리 환경 파일은 MO2의 번들 제어 플러그인과 지원 디렉터리이며, 설치기가 `ModOrganizer.ini`의 `lock_gui=false`를 설정했다. 설치 전 ModOrganizer.ini 및 실제 Documents 게임 INI는 `_build/obcjk/utf8-test/`에 사본을 보존했다.

기존 보존 목록 99개를 재해시한 결과 변경 0개였다. 실제 Documents Oblivion.ini도 검사 전 사본과 동일했다. Default 프로필, 기존 KR/obCJK 모드와 v1.0.4 배포 파일을 보존했다. 테스트 프로필과 모드는 별도로 남겨 후속 검증에 사용한다.

다음 단계는 도구 제한 해결 후 작은 UTF-8 ESP의 UI/대사/아이템/효과/BOOK 표시 검사다. 그다음 한글 CELL 위치명을 포함한 저장/목록/완전 재실행 후 재로드를 검사한다. 세이브 Unicode 성공은 아직 주장하지 않는다.
