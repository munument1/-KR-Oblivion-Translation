# obCJK 글꼴 사용 위치와 교체 방법

2026-10-01 현재 `obcjk-save-test`의 기본 게임 UI 기준이다. 설치본 obCJK의 `obcjk_iniedit_readme(EN).md`에 명시된 SLOT 역할과 실제 시험판 INI를 대조했다. UI 모드가 다른 슬롯을 지정하면 화면별 대응도 달라질 수 있다.

## 현재 글꼴과 사용 위치

| 슬롯 | 게임에서 쓰이는 곳 | 현재 글꼴 | `[UTF8]` 설정 키 | 현재 크기(ASCII / 한글) |
|---|---|---|---|---|
| 1 | 제목, 대부분의 메뉴/UI, 일반 책 | Malgun Gothic(맑은 고딕), 굵기 400 | `FontParam1_1`, `FontParam1_2` | 38 / 39 |
| 2 | NPC 대사 자막, HUD | **Noto Serif KR, 굵기 500** | `FontParam2_1`, `FontParam2_2` | 40 / 40 |
| 3 | 지도 위치명, 팝업, 나머지 UI | Malgun Gothic, 굵기 400 | `FontParam3_1`, `FontParam3_2` | 26 / 26 |
| 4 | 데이드릭 문자 | 원본 Daedric_Font | obCJK 치환 대상 아님 | 원본 자원 사용 |
| 5 | 손글씨 스타일 책, 편지 | Malgun Gothic, 굵기 400 | `FontParam5_1`, `FontParam5_2` | 34 / 34 |

**대사만 고르면 슬롯 2부터 바꾸면 된다.** 같은 슬롯을 쓰는 HUD도 함께 바뀐다. 제목과 책도 슬롯 1을 공유하므로 서로 완전히 독립된 글꼴 설정은 아니다. 크기 값은 obCJK의 설정값이며 실제 화면의 최종 픽셀 크기는 게임 해상도/렌더링 배율에도 영향을 받는다.

추가 UI 모드를 사용할 때의 슬롯은 다음과 같다. 현재 시험 구성에는 MenuQue/NorthernUI가 없어 아래 설정을 바꿔도 해당 화면은 생기지 않는다.

| 슬롯 | 용도 | 키 |
|---|---|---|
| 7 / 8 | MenuQue 추가 글꼴 1 / 2 | `FontParam7_1/2`, `FontParam8_1/2` |
| 33 | NorthernUI Normal | `FontParam33_1/2` |
| 34 | NorthernUI Large | `FontParam34_1/2` |
| 35 | NorthernUI MediumLargeUpper | `FontParam35_1/2` |
| 36 | NorthernUI Shadowed | `FontParam36_1/2` |
| 37 | NorthernUI Small | `FontParam37_1/2` |

NorthernUI의 다섯 역할은 크기/스타일 역할 이름이다. 실제 어느 화면이 그 역할을 쓰는지는 NorthernUI XML 설정에 따라 달라진다.

## 눈누에서 고른 글꼴 넣기

1. 원하는 글꼴의 TTF/OTF를 내려받아 Windows에 설치한다. MO2의 Fonts 폴더에 파일만 복사하는 것으로는 obCJK의 이름 기반 글꼴 선택이 충족되지 않는다.
2. Windows 글꼴 정보 또는 obCJK 설정 편집기의 글꼴 목록에서 **설치된 글꼴 이름**을 확인한다. 눈누 표시명이나 파일명과 Windows 등록명이 다를 수 있다.
3. 아래 시험판 파일의 **`[UTF8]` 구역**에서 원하는 슬롯의 글꼴 이름을 바꾼다. 같은 키가 `[BIG5]`에도 있으므로 구역을 확인한다.

```text
D:\Oblivion MO2\mods\Oblivion_KR_obCJK_UTF8_Test\OBSE\plugins\obCJK\obCJK.ini
```

현재 자막 설정:

```ini
[UTF8]
FontParam2_1 = Noto Serif KR,0,40,0,0,34,500,0,0
FontParam2_2 = Noto Serif KR,0,40,0,0,34,500,0,0
FontParam2_1_Native = 0
```

`_1`은 반각 영문/숫자, `_2`는 한글 등 CJK용이다. 처음에는 두 줄에 같은 글꼴을 쓰면 혼합 문장에서 스타일 차이를 줄일 수 있다. 위 값 중 첫 번째 항목이 글꼴 이름, 세 번째 `40`이 높이, 일곱 번째 `500`이 굵기다. 글꼴만 비교할 때는 이름만 바꾸고 나머지 숫자는 유지한다. INI는 UTF-8로 저장하고 게임을 다시 실행한다.

다른 사람이 같은 설정을 사용하려면 그 PC에도 해당 글꼴이 설치돼 있어야 한다. Windows/GDI가 다른 글꼴로 대체한 상태와 선택한 글꼴의 실제 적용은 구분한다.

## 고를 때 비교할 문장

```text
이곳에 오래 머물지 마십시오. 문 너머에서 무슨 일이 벌어질지 모릅니다.
값·꽃·읽음·닭·뷁  제국 감옥  체력 125/200  “기록” (ABC 123)-A
```

자막에는 긴 문장의 가독성, 지도에는 작은 크기의 받침과 긴 위치명, 책에는 여러 줄에서의 피로도를 살펴보면 된다. 같은 한글 글꼴이라도 지원 글자 범위와 영문 모양이 다르므로 위 문장과 실제 대사를 함께 비교한다.

## 이번 적용과 검증

슬롯 2의 ASCII/CJK 두 줄만 Malgun Gothic 400에서 Noto Serif KR 500으로 변경했다. 크기·간격·위치·나머지 설정은 동일하다. Windows GDI가 Noto Serif KR을 실제 선택했고 완성형 한글 11,172자 누락 0개를 확인했다. 폰트 변경 후 실제 대사 화면의 줄바꿈/잘림 비교는 아직 하지 않았다. 게임은 변경 시점에 종료돼 있었으며 다음 실행에 적용된다.

변경 전 INI와 해시/적용 기록은 `_build/obcjk/font-preview/subtitle-serif/`에 보관했다. 원본 obCJK 모드 및 기본 빌더의 글꼴 기본값은 바꾸지 않았다.
