# obCJK 폰트 후보와 검증 범위 — 2026-10-01

직접 고를 때는 [슬롯별 사용 위치와 교체 방법](font_slots_guide.md)을 따른다. 사용자의 자막 스타일 요청으로 시험판 **슬롯 2만 Noto Serif KR, 굵기 500**으로 바꿨다. 아래 고딕 자막 추천은 기존 가독성 우선 비교안이며, 현재 적용값과는 구분한다. 새 명조 자막의 GDI 한글 지원은 확인했고 실제 대사 화면 비교는 남아 있다.

Unicode 메뉴는 현재도 정상 표시된다. 본문·비공식 패치 UTF-8와 한글 위치명의 파일 검사 및 메인 메뉴 진입은 [후속 시험](unofficial_locations_test_results.md)에서 확인했다. 실제 본문 화면은 남아 있으므로 아래는 **폰트 비교에 근거한 추천안**이다. 런타임으로 확인한 폰트 범위는 현재 Malgun Gothic의 기본 메뉴뿐이다.

## 실제 비교 결과

설치된 폰트 파일 7개로 같은 한국어/ASCII/숫자/받침/문장부호/긴 문장을 렌더링했다. 이미지와 파일 해시, GDI가 실제 선택한 face, 지원 범위는 Git에서 제외되는 `_build/obcjk/font-preview/`에 보관한다. 미리보기는 Pillow 파일 렌더링이며 게임 화면이 아니다. Windows GDI의 glyph 검사도 실제 게임의 줄바꿈/정렬/클리핑 검증을 대신하지 않는다.

| 글꼴 후보 | Windows GDI의 완성형 한글 검사 | 판단 |
|---|---|---|
| Malgun Gothic Regular | 11,172자 중 누락 0 | 현재 게임 메뉴에서 표시 확인한 기준 글꼴 |
| Noto Sans KR Regular/Bold | 각각 누락 0 | 대사/HUD/작은 UI의 우선 후보 |
| Noto Serif KR Regular | 누락 0 | 양피지 배경의 제목/책에 우선 추천 |
| KoPub바탕체 Medium | 누락 0 | 책 본문 대안, 작은 크기에서는 실제 페이지 비교 필요 |
| Nanum Brush Script | 누락 0 | 손글씨 분위기; 짧은 편지 후보, 긴 본문의 기본값은 피함 |
| 설치된 Pretendard-subset3 | 6,937자 누락 | 그대로 기본값에 사용하지 않음. 완전판 Pretendard와는 별도 파일 |

Noto의 KR는 한국어 변형이며, TC는 번체 중국어 변형이다. [공식 Noto CJK 문서](https://github.com/notofonts/noto-cjk)에서 지역별 변형을 확인했다. [Noto Serif KR 설명](https://github.com/google/fonts/blob/main/ofl/notoserifkr/DESCRIPTION.en_us.html)은 한글/한자 및 여러 문자 지원을 명시한다.

Pretendard 자체는 전체 글꼴과 여러 굵기를 제공하지만, 현재 PC에 등록된 `Pretendard-subset3`는 일부 글자 파일이다. 향후 완전판을 쓰려면 별도로 파일·GDI 지원·게임 렌더링을 검증한다. [Pretendard 공식 문서](https://github.com/orioncactus/pretendard/blob/main/packages/pretendard/README.md).

## 용도별 추천

확인한 설치본 `obcjk_iniedit_readme(EN).md`의 SLOT 설명을 기준으로 했다. 같은 SLOT을 쓰는 화면은 글꼴을 공유한다. 이름만 보고 메뉴/책/대사를 각각 독립적으로 바꿀 수 있다고 가정하지 않는다.

| 문항/용도 | 대응 SLOT | 우선 후보 | 추천 이유와 적용 조건 |
|---|---|---|---|
| 제목·대부분의 UI·일반 책 | 1 | Noto Serif KR Medium | 양피지 분위기와 제목의 선명함. 이 슬롯이 책에도 사용되므로 전체 Bold는 피한다. 가독성 우선 대안은 Noto Sans KR Regular |
| HUD·대사 자막 | 2 | Noto Sans KR Regular 또는 Medium | 빠르게 읽는 긴 문장에 고딕이 유리. 줄바꿈과 음성 중 자막 유지시간은 실제 대화에서 검사 |
| 지도 위치명·팝업·나머지 UI | 3 | Noto Sans KR Medium | 작은 글자와 복잡한 받침을 읽기 쉽게. 긴 한글 위치명의 잘림을 실제 화면에서 확인 |
| 편지·손글씨 스타일 책 | 5 | Noto Serif KR Regular | 긴 편지도 읽을 수 있는 기본안. 손글씨를 선호하면 Nanum Brush Script를 비교하되 해당 슬롯의 긴 책까지 함께 확인 |
| 데이드릭 문자 | 4 | 기존 Daedric_Font 유지 | obCJK 소스에서 치환 제외된 특수 문자 슬롯 |
| MenuQue 추가 글꼴 | 7/8 | Noto Sans KR, 해당 UI 확인 후 적용 | 현재 검증 구성에 MenuQue가 없다. 기본 게임의 대사 슬롯으로 혼동하지 않음 |

권장 조합은 **SLOT1 Noto Serif KR / SLOT2·3 Noto Sans KR / SLOT5 Noto Serif KR**이다. 변경 전에 전체 번역 실행을 Malgun Gothic으로 먼저 통과시켜 인코딩 문제와 폰트 변경 영향을 구분한다.

`FontParamN_1`은 ASCII, `_2`는 CJK 설정이다. 한국어와 영어의 크기·baseline이 어긋나면 혼합 문장에서 눈에 띄므로 첫 후보는 두 영역에 같은 패밀리를 사용한다. 글꼴 이름과 weight만 먼저 변경하고, 기존 크기·줄 높이·spacing을 고정해 비교한다. 크기 숫자는 아직 추천값으로 인증하지 않았다.

## 재현 도구

`tools/preview_obcjk_fonts.py --manifest <Git 제외 로컬 JSON> --output <비교 디렉터리>`.

manifest는 label/path/face/weight 및 필요하면 variation을 지정한다. GDI 검사에서는 요청 face뿐 아니라 실제 선택된 이름도 기록한다. 이 도구는 폰트를 설치하거나 MO2/게임 INI를 변경하지 않는다.

## 남은 요구사항

- 전체 한글패치 UTF-8 파일 생성 및 구조/값 보존 검증은 완료했다. 실제 본문 화면 표시를 이어서 확인한다.
- 실제 게임에서 UI·대사·아이템·효과·책·퀘스트를 확인.
- 위 기준 실행 통과 후 추천 폰트 조합으로 실제 화면 재검증.
- 한글 위치명 저장/목록/재로드는 별도 검증.

현재 xEdit MCP 및 확인한 공식 main의 client는 Oblivion 모드를 지원하지 않는다. [공식 client 소스](https://github.com/BB-84C/bgs-modding-superpowers/blob/main/tools/mo2-vfs-launcher/lib/xedit-client.common.ps1)의 지원 map도 Fallout4/Skyrim/SkyrimSE/Starfield만 포함한다. 이후 사용자가 기존 프로젝트 빌더의 사용 예외를 허용하여 UTF-8 본문 시험판을 만들었다. 이 폰트 변경은 ESP/ESM을 수정하지 않는다.
