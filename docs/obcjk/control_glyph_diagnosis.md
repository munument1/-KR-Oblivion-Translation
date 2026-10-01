# 본명조의 줄바꿈·입력 커서 네모 비교 시험

2026-10-01 사용자가 종족 설명의 `임페리얼 (imperial)` 뒤와 빈 줄, 캐릭터 이름 입력란의 깜빡이는 커서에서 X자 네모를 보고했다.

## 확인한 근거

- Windows GDI의 `GetGlyphOutlineW`를 obCJK와 같은 `GGO_GRAY8_BITMAP`으로 호출했다. 본명조 KR Medium은 CR(U+000D), LF(U+000A), TAB(U+0009)를 같은 32×40 비트맵으로 돌려준다. 맑은 고딕의 CR은 비어 있다. 한글 11,172자 지원과 제어문자 렌더링은 별개 문제다.
- 조사용 obCJK 소스의 `ObCJKGlyphAtlas_GetGlyph`는 LF에 대해서만 사용자 글꼴 대신 원래 처리를 강제한다. UTF8 ASCII 후보에는 CR과 DEL도 들어간다. 이 소스만으로 현재 Nexus DLL의 모든 분기 동작이 입증되는 것은 아니다.
- Oblivion Font Editor 저자의 분석에 따르면 입력 커서는 `|`와 `0x7F`를 번갈아 쓴다. 해당 문자는 원래 글꼴에서 비워 둬야 한다. [저자 설명](https://www.nexusmods.com/oblivion/mods/48029?tab=posts)
- 현재 최종 위치명 시험판의 Imperial RACE DESC 자체에는 CR/LF가 없다. 본문은 정상 UTF-8이다. 제목과 빈 줄은 그 문자열 바깥에서 구성될 가능성이 있으므로, 번역 CSV의 줄바꿈만 일괄 수정해 해결됐다고 주장하지 않는다.

GDI 측정 원본은 `_build/obcjk/font-preview/control-glyphs.json`에 있다.

## 임시 비교 설정

`Oblivion_KR_obCJK_UTF8_Test/OBSE/plugins/obCJK/obCJK.ini`에서 `[obCJK] AsciiRenderEnable`만 1에서 0으로 바꿨다. 모든 CJK FontParam 값, 크기, 간격은 그대로다. 한글은 본명조 Medium/이롭게바탕체 설정을 쓰고 영문·숫자·제어문자는 원래 게임의 글꼴/렌더링을 쓴다.

비교 당시 변경 전 INI와 해시 보고서는 `_build/obcjk/font-preview/control-rendering/`에 보관했다. 원본 obCJK 모드, 게임 Data 및 번역 플러그인은 수정하지 않았다.

설정 변경 후 사용자가 "음 이제 제대로 나온다"라고 정상 표시를 확인했고 v1.0.5 배포를 요청했다. 이 설정을 설치기용 프리셋에도 반영한다. 영어·숫자는 원래 글꼴을 쓰며, 전체 게임의 UI·줄바꿈을 전수 검증했다고 주장하지 않는다.
