# Oblivion Original 한국어 번역 v1.0.7

오리지널 Oblivion (2006) 본편과 공식 확장팩/DLC용 한국어 번역입니다. obCJK UTF-8 방식과 한글 위치명을 적용하며, 본명조·이롭게바탕체를 자동 설치합니다.

## 설치

1. MO2를 준비하고 [xOBSE](https://www.nexusmods.com/oblivion/mods/37952)와 [obCJK](https://www.nexusmods.com/oblivion/mods/56434)를 별도로 설치합니다.
2. [v1.0.7 설치기 ZIP](https://github.com/munument1/-KR-Oblivion-Translation/releases/tag/v1.0.7)을 내려받아 전체 압축을 풉니다.
3. `install.bat`을 실행하고 원본 게임의 **Data 폴더**를 지정합니다. Python은 필요하지 않습니다.
4. 생성된 `output\Oblivion_KR_Mod` 폴더를 MO2에 모드로 넣고 활성화합니다.
5. MO2 왼쪽 목록에서 obCJK보다 아래에 두고, 기존 바이트 방식 한글 패치와 시험판 번역 모드는 끕니다.
6. MO2 실행 대상에서 **Oblivion**을 선택합니다. 필요한 경우 [MO2의 xOBSE 강제 로드 안내](https://github.com/ModOrganizer2/modorganizer/wiki/Running-Oblivion-OBSE-with-MO2)를 확인합니다.

설치기는 원본 게임 Data를 읽고 별도 번역 모드 폴더를 만듭니다. 여기에 ESM/ESP, 메뉴 문자열과 `OBSE\plugins\obCJK\obCJK.ini`가 들어갑니다. 인트로·엔딩 한국어 자막 영상은 설치기와 분리해 Nexus에서 별도 배포합니다. 프로필과 세이브는 생성하거나 포함하지 않습니다.

기존 설치기와 같이 문서 폴더의 `My Games\Oblivion\Oblivion.ini`를 자동으로 찾습니다. 찾은 기존 파일에서 글꼴 경로만 복원하고 최초 변경 전 파일을 백업합니다. INI 주소 입력 단계는 없습니다. INI가 없으면 새 파일을 만들지 않습니다.

MO2에서 프로필별 INI를 사용하는 경우, 해당 기존 INI의 `[Fonts]`가 아래 원본 경로인지 확인하세요. 이전 한글 패치 설정이 남아 있으면 다음 값으로 복원합니다.

```ini
[Fonts]
SFontFile_1=Data\Fonts\Kingthings_Regular.fnt
SFontFile_2=Data\Fonts\Kingthings_Shadowed.fnt
SFontFile_3=Data\Fonts\Tahoma_Bold_Small.fnt
SFontFile_4=Data\Fonts\Daedric_Font.fnt
SFontFile_5=Data\Fonts\Handwritten.fnt
```

기존과 같은 명령 실행도 지원합니다. 두 번째 인수는 기존 INI를 직접 지정할 때만 사용합니다.

```bat
install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data"
```

출력 폴더가 이미 사용 중이면 덮어쓰지 않습니다. 업데이트할 때는 새 폴더에 설치기 ZIP을 풀어 실행하세요.

v1.0.7은 v1.0.6의 지형 로딩 수정에 더해, 오리지널 기준 canonical 번역 47,227건과 언오피셜 패치 번역 8,818건을 고정하고 지도 마커·지역명 및 퀘스트 일지 교정을 반영한 버전입니다. 새 ZIP으로 모드를 다시 생성하고 MO2의 기존 번역 모드를 교체하세요.

## 인트로·엔딩 동영상 자막

한국어 자막을 입힌 `OblivionIntro.bik`와 `OblivionOutro.bik`는 GitHub 설치기와 분리해 **Nexus에서 별도 영상 파일로 배포**합니다. 일반 설치 과정에서는 FFmpeg나 RAD Video Tools를 설치하거나 내려받지 않으며, 원본 게임 영상도 GitHub 설치기 ZIP에 포함하지 않습니다.

저장소의 `video_subtitles` 자막 소스와 `build_video_subtitles.py`는 유지합니다. 개발자가 영상을 다시 만들 때는 FFmpeg·ffprobe와 RAD Video Tools를 직접 준비한 뒤 `--video-subtitles auto` 또는 `required`를 사용할 수 있습니다. 빌더는 외부 영상 도구를 자동으로 내려받지 않습니다.

## 글꼴

- 메뉴·일반 책·대사/HUD·지도/팝업: **본명조 KR Medium**.
- 편지·손글씨 책: **이롭게바탕체 Medium**.
- MenuQue 7/8, NorthernUI 33–37: 본명조 KR Regular.
- 영문·숫자·제어문자는 원래 게임 렌더링을 사용합니다.

본명조 Regular/Medium과 이롭게바탕체를 현재 Windows 사용자에게 등록합니다. 관리자 권한은 필요하지 않습니다. OFL 원문은 설치기 ZIP의 `licenses`, 출처와 해시는 `font_sources.json`에 있습니다. [슬롯별 글꼴 안내](https://github.com/munument1/-KR-Oblivion-Translation/blob/main/docs/obcjk/font_slots_guide.md)를 참고하세요.

## 언오피셜 패치

GitHub 설치기는 본편·공식 DLC용입니다. Nexus용 언오피셜 번역은 세 ZIP으로 따로 제공합니다.

| 번역 | 대상 원본 | 안내 |
|---|---|---|
| UOP | 3.5.9a | [UOP](docs/unofficial/UOP.md) |
| USIP | 1.6.2 | [USIP](docs/unofficial/USIP.md) |
| UODP | v27 | [UODP](docs/unofficial/UODP.md) |

각 번역은 해당 영문 패치 위에 적용하는 ESP 오버레이입니다. 원본 패치의 메시·텍스처·음성은 별도로 설치합니다.

## 검증과 개발

원본 게임 파일, FormID, 레코드 구조와 컴파일된 스크립트를 보존합니다. 종족 이름은 음성 경로를 위해 영어로 유지합니다. 검증 보고서는 모드 폴더 옆 `Oblivion_KR_Mod.validation.json`에 저장합니다.

MO2에서 한국어 메뉴 표시, 한글 위치명이 들어간 세이브 생성, 본명조 및 줄바꿈·입력 커서 표시를 확인했습니다. 모든 기존 세이브 재로딩과 장시간 플레이의 전수 검증을 완료한 것은 아닙니다.

[빌드와 저장소 구성](docs/development.md), [v1.0.7 canonical 검증 기록](docs/obcjk/canonical_release_audit_v1.0.7.json), [변경 이력](docs/release-changelog.md)을 참고하세요. [v1.0.6](https://github.com/munument1/-KR-Oblivion-Translation/releases/tag/v1.0.6)은 이전 버전으로 기존 릴리스에서 받을 수 있습니다.
