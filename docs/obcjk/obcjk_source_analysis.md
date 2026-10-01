# obCJK 소스 및 동작 분석

## 근거 버전

- [사용자가 지정한 Nexus 페이지](https://www.nexusmods.com/oblivion/mods/56434): 표시 버전 20260807, xOBSE 22.13 요구.
- [공식 GitHub](https://github.com/AophMiSaki/obCJK): 조사한 main 커밋 `4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6`, 2026-08-08. 조회한 원격 브랜치는 main 하나다.
- 로컬 소스 사본: `_build/research/obCJK/`.
- 설치된 DLL은 MO2의 ObCJK 모드에 있으며 83,456 bytes다. 배포 메타데이터의 archive 이름은 20260807을 가리킨다. 공개 소스를 이 DLL의 재현 빌드로 인증한 것은 아니다.

소스 링크는 위 커밋에 고정한다. 소스 주석의 테스트 주장은 저자의 기록이며 이 프로젝트의 실행 검증 결과가 아니다.

## ESP/ESM 바이트와 전역 인코딩

[obCJK_Encoding.h](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_Encoding.h)에서 한국어 codepage는 **949**, UTF-8은 **65001**이다. 한국어 모드의 Python 이름도 `cp949`다. Nexus 설명의 EUC-KR 표기는 엄밀한 codec 선택 기준으로 삼으면 안 된다.

CP949 모드는 선행 바이트 `0x81..0xFE`와 후행 바이트 범위를 처리하며 Windows codepage 949로 글리프를 변환한다. CP949 확장 한글을 대상으로 하는 설계다. 모든 확장 조합의 게임 내 표시를 검증한 것은 아니다.

설정 parser가 받는 한국어 별칭은 `cp949`, `949`이고, UTF-8 별칭은 `utf8`, `utf-8`, `65001`이다. **`ActiveCodePage=KOREAN` 또는 `EUC-KR`은 이 C++ parser에서 한국어 모드로 인식되지 않고 기본 BIG5로 돌아간다.** `KOREAN`은 내부 표시명/폰트 INI section 이름이다. 한국어 모드를 시험할 때는 `ActiveCodePage=cp949`로 지정해야 한다.

[main.cpp](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/main.cpp)는 시작 시 INI의 `ActiveCodePage`를 읽어 전역 `g_activeCodePage`를 설정한다. UTF-8 또는 DBCS 훅 중 하나를 설치한다. 확인한 코드에서 플러그인별 인코딩 선택이나 legacy 한국어 자동 감지는 없다.

이 DLL이 ESP 파일을 열어 한글 패치 전체를 UTF-8로 변환하는 구조가 아니다. 엔진이 읽은 문자열의 측정·줄바꿈·글리프 렌더링 경로를 후킹한다. UTF-8 훅은 2/3/4-byte sequence를 해석한다. 따라서 빌더가 쓰는 실제 문자열 바이트가 선택 모드와 일치해야 한다.

영문 ASCII는 두 모드에 공통이다. 원본 Windows-1252의 스마트 따옴표·악센트 등 비ASCII를 그대로 두면 UTF-8의 유효 바이트가 되지 않는다. 기존 한국어 번역 외에 플레이어에게 보이는 미번역 비ASCII 문자열도 인벤토리/변환 정책이 필요하다. EditorID·파일명·음성 경로·바이너리까지 일괄 변환하면 안 된다.

## 폰트와 UI

[obCJK_GlyphAtlas.h](https://github.com/AophMiSaki/obCJK/blob/4cbdacc0c4970cbfb46650c92ba2b0dcb7bff6a6/obse_plugin_example/include/obCJK_GlyphAtlas.h)는 UTF-8로 저장한 폰트 이름을 `MultiByteToWideChar(CP_UTF8)`로 읽고 `LOGFONTW`/GDI 폰트 생성 경로를 사용한다. 게임 기본 font texture를 확장하고 새 글리프를 atlas에 넣어 엔진의 glyph 경로에 연결한다. Scaleform을 요구하는 방식은 확인하지 못했다.

시스템에 설치된 글꼴 이름을 지정하는 구조다. `.otf/.ttf` 파일을 MO2의 `Fonts/Korean`에 복사한 것만으로 이 이름 기반 로딩이 충족된다고 판단하면 안 된다. 이번 PC에는 맑은 고딕 파일이 존재한다. 첫 테스트는 설치 확인이 쉬운 `Malgun Gothic` 등 한글 지원 폰트로 제한한다.

기본 slot 1/2/3/5, MenuQue/Loot Menu slot 7/8, NorthernUI 별도 역할을 지원하며 slot 4 Daedric은 제외한다. UTF-8에서도 기본 `.fnt/.tex` 기반 font manager와 연결하므로 obCJK판에서 TheGreatestKorean을 빼더라도 **원본 기본 폰트 자원까지 제거하면 안 된다**.

MenuQue delimiter 훅은 DBCS 모드에서 GameInitialized 시점에 설치하며 UTF-8에서는 건너뛴다. NorthernUI는 datastore.xml과 DLL/font 역할 매핑을 별도로 처리한다. 지원 코드 존재는 특정 모드 버전 조합의 호환성 통과를 의미하지 않는다. 현재 조사한 모드 DLL 목록에는 MenuQue/NorthernUI/Loot Menu가 없고 obCJK와 UOP의 jail/training fix DLL만 있다.

`menus/strings.xml` 등 엔진에 전달되는 UI 텍스트는 동일한 인코딩 모드의 영향을 받는다. XML declaration, literal 텍스트, 엔진 파싱을 함께 확인해야 한다. 게임 EXE의 기존 ASCII 문자열은 공통이며 일부 메뉴 문자열은 기존 GMST 오버레이로 계속 공급할 수 있다.

## 초기화 및 종료 후보

`OBSEPlugin_Query`는 xOBSE 버전이 기준보다 낮으면 false를 반환한다. Oblivion 버전이 빌드의 `OBLIVION_VERSION`과 다르면 오류를 기록하지만 **그 분기에서 false를 반환하지 않는다**. 프로젝트 설정은 `OBLIVION_VERSION=0x010201A0`으로 고정되어 있다. 로컬 EXE의 버전은 1.2.0.416, loader 로그는 Steam 빌드를 기록한다.

훅들은 고정 VA를 사용한다. `obCJK_HookUtil.h`의 일반 trampoline 설치는 대상 명령어 길이를 계산하여 덮어쓰며, 일부 call-site 훅에는 opcode 확인이 있으나 전체 실행파일의 fingerprint를 검사하는 구조는 아니다. 버전 차이·동일 주소 선행 훅·명령 해석 문제를 후보로 남겨야 한다. 여러 Install 호출 결과가 main의 전체 로딩 실패로 집계되지 않으므로 단순 Load 성공만으로 모든 경로를 인증할 수 없다.

설정 파일은 작업 디렉터리 기준 `Data/OBSE/Plugins/obCJK/obCJK.ini`다. MO2 VFS와 올바른 게임 working directory를 사용해야 한다. INI가 없거나 인코딩 값이 잘못되면 기본 BIG5 설정을 사용할 수 있다.

이번에 보존한 13:57 로그에는 UTF8 선택, 주요 훅 ok, D3D renderer/device 확보, 첫 frame task 실행이 있다. DLL 자체 미로드 가설을 그 실행에 적용할 수 없다. 상세한 종료 증거와 한계는 [startup_diagnosis.md](startup_diagnosis.md)를 따른다.

## 저장 및 입력

CreateFileW/DeleteFileW, 저장 목록의 FindFirstFileW/FindNextFileW shim, 파일명 절단과 반환값 수정이 있다. 파일명은 active codepage와 Windows UTF-16 사이를 변환한다. IME는 입력 문자열을 선택 codepage로 만들며 UTF-8에서는 `WideCharToMultiByte(CP_UTF8)`를 사용한다.

이것은 과거 TheGreatestKorean 문자열이 들어 있는 세이브 내용 전체를 자동 마이그레이션한다는 뜻이 아니다. ASCII 이름의 기존 세이브와 비ASCII 이름/사용자 지정 아이템이 있는 세이브를 따로 테스트하고 원본 사본을 보존해야 한다. 저장 성공 UI뿐 아니라 실제 파일 생성과 재로드를 확인한다. 기존 CELL/WRLD 및 저장 안정성 정책은 유지한다.

## 동영상 자막

공식 소스의 게임 플러그인과 설정 UI/문서에서 subtitle/SRT/Bink/movie/video를 검색했다. 발견한 것은 slot 2의 **HUD/dialogue subtitles** 설명과 글리프 배경에 대한 subtitle-style 설명이다. SRT cue reader, Bink 재생 시간 연동, 동영상 자막 렌더러는 발견하지 못했다. Nexus 20260807 설명도 이 기능을 명시하지 않는다.

따라서 기존 `build_video_subtitles.py`와 `video_subtitles/OblivionIntro.srt`, `OblivionOutro.srt`는 보존한다. 나중에 별도 배포본에서 외부 자막 기능이 확인되면 형식·경로·타이밍을 검증해 같은 확정 번역을 재사용한다. 자막이 이미 입혀진 BIK와 외부 자막을 동시에 켜면 중복 표시될 수 있으므로 모드는 상호 배타적으로 설계한다.

## 인코딩 결정

**권고: UTF-8, BOM 없는 문자열 바이트 + 종단 NUL 한 개, INI `ActiveCodePage=UTF8`.**

근거는 실제 UTF-8 전용 훅의 존재, 모든 현대 한글 음절 표현, 사람이 읽는 Unicode 번역 데이터와의 직접 연결, CP949의 바이트 경계/레거시 문장부호 처리 복잡도 감소다. 한국어를 다시 번역하지 않고 표현 방식을 바꾸는 방향이다.

CP949는 비교 실험용 대안으로 남긴다. EUC-KR은 CP949와 다르고 표현 범위가 좁으므로 별도 검증 없이 backend codec으로 선택하지 않는다. 현재 권고는 소스 분석 결과이지 게임 실행 합격 판정이 아니다.

## 라이선스와 설치기

현재 GitHub `LICENSE`는 2-byte 빈 내용이며 마지막 커밋 메시지는 MIT 제거다. 예전 MIT였다는 이유로 재배포 허가를 추정하면 안 된다. Nexus 페이지는 재업로드를 금지하고 수정/자산 사용에 허가를 요구한다.

계획상 설치기에는 obCJK DLL·설정 도구 EXE를 포함하지 않고 사용자 별도 설치를 안내한다. 우리 번역 데이터와 새로 작성한 설정 템플릿을 분리한다. 설치기 변경은 실제 게임 테스트 통과 후에 진행한다.
