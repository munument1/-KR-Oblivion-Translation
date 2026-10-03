# 원본 폰트 검정 효과와 obCJK 윤곽선 조사

2026-10-02. 적용 가능성 조사이며 게임 설정·DLL·설치기·릴리스는 변경하지 않았다.

## 확인 결과

- Steam 원본 `Oblivion - Misc.bsa`(BSA v103)의 폰트 자원 10개를 작업 폴더에만 추출했다. 사용한 bgs-archive 0.1.0 Windows 도구는 릴리스 SHA-256 검증 후 capabilities/info/list/extract 순서로 사용했다.
- 원본 `kingthings_shadowed_0_lod_a.tex`는 512×512 RGBA이며 투명하지 않은 검정 픽셀 58,655개가 있다. `kingthings_regular_0_lod_a.tex`의 같은 조건 검정 픽셀은 0개다. 원본 대사/HUD용 슬롯 2에는 검정 효과가 텍스처 자체에 저장되어 있다.
- 우리 슬롯 2의 원본 경로도 `Kingthings_Shadowed.fnt`이다. `AsciiRenderEnable=0`이라 영문은 원본 자원을 사용하고, 한글은 obCJK가 본명조 Medium에서 새 글리프를 만든다. 새 한글 글리프에 원본 영어 글리프의 그림자가 자동 복사되지는 않는다.
- 공식 main은 현재 `4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6`이다. [TexUpload의 실제 업로드 경로](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_TexUpload.h#L126-L140)는 글리프 픽셀을 [CompositeGlyphPixel](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_GlyphAtlas.h#L385-L432)로 처리한다. 배경 불투명도 0이면 RGB는 흰색, 알파는 글자 모양이며 검정 테두리를 추가하지 않는다.
- `BackgroundOpacity`는 글리프의 직사각형 영역 전체에 검정 배경을 합성하는 전역 설정이다. 글자 윤곽선 또는 슬롯 2만의 그림자 설정이 아니다. 현재 설치 DLL에도 이 설정 이름이 존재하며 우리 INI에는 없어 기본값 0을 쓴다.
- 글꼴 이름·굵기·밀도·대비와 NorthernUI `Shadowed` 역할은 새 한글 글리프에 윤곽선을 추가하는 옵션이 아니다. 조사한 소스 및 설정 도구에는 별도 윤곽선 두께·그림자 오프셋 옵션이 없다.

## 적용 방향

얇은 검정 윤곽선은 흰색 대사/HUD가 밝은 배경에서도 읽히게 하는 데 도움이 된다. 우선 슬롯 2의 한글만 1px/2px 효과를 비교하고, 메뉴·책에 일괄 적용하는 것은 피하는 것이 적절하다.

기술적으로 RGBA 글리프 주변에 검정 알파 마스크를 합성할 수 있다. 다만 현재 INI만으로는 구현되지 않으며 obCJK의 글리프 렌더링 지원을 확장해야 한다. 윤곽선 패딩만큼 atlas 사각형·UV·글리프 위치/크기를 조정하되 문자 전진 폭과 줄 간격은 보존하고, 대사 줄바꿈·클리핑·혼합 영문/한글·ASCII 제어문자 처리의 실제 게임 시험이 필요하다. 이번 조사에서는 DLL을 수정하거나 게임 시험을 하지 않았다.

동영상 인트로/엔딩 자막은 별도 FFmpeg 경로이며, 이미 검정 `Outline=2`를 사용한다.

원본 픽셀 분석·오프라인 본명조 효과 비교는 `_build/research/font-outline/`에 있다. 비교 이미지는 Pillow 렌더링이므로 실제 obCJK 게임 출력과 구분한다.
