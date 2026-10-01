# Oblivion Original 한국어 번역 v1.0.5

오리지널 Oblivion (2006) 본편과 공식 확장팩/DLC용 한국어 번역 설치기입니다. **v1.0.5부터 obCJK UTF-8 방식**을 사용합니다. Python 설치 없이 실행할 수 있습니다.

GitHub 설치기에는 본편·공식 DLC 번역과 OFL 글꼴만 포함합니다. 언오피셜 패치 번역은 별도 Nexus 배포용 파일입니다. xOBSE와 obCJK 본체는 포함하지 않습니다. Steam Deck 작업은 대상에 포함하지 않습니다.

## 설치

1. 오리지널 Oblivion을 준비하고 MO2를 설치합니다. 게임을 한 번 실행해 INI를 생성합니다.
2. Nexus에서 **xOBSE**와 **obCJK**를 각각 내려받아 해당 모드의 안내에 따라 설치합니다. 이번 테스트 환경은 xOBSE 22.13과 obCJK 20260807입니다.
   - [xOBSE](https://www.nexusmods.com/oblivion/mods/37952)
   - [obCJK](https://www.nexusmods.com/oblivion/mods/56434)
3. [GitHub Releases](https://github.com/munument1/-KR-Oblivion-Translation/releases)에서 `Oblivion_Original_KR_Installer_v1.0.5.zip`을 내려받아 **전체 압축을 푼 뒤** `install.bat`을 실행합니다.
4. 원본 게임의 `Data` 폴더를 지정합니다. 설치기는 원본 파일을 읽고 별도 `output\Oblivion_KR_obCJK` 폴더에 번역본을 생성합니다.
5. 기존 한글 패치의 글꼴 설정을 쓰던 경우, MO2를 종료하고 사용할 프로필의 `Oblivion.ini` 경로도 지정합니다. 설치기는 `[Fonts]`의 다섯 원본 글꼴 경로만 복원하고 변경 전 INI를 백업합니다. 빈 입력으로 건너뛴 경우 출력 폴더의 `FONT_SETTINGS.txt`를 사용할 프로필 INI에 반영합니다.
6. 생성된 `output\Oblivion_KR_obCJK` 폴더를 MO2 모드로 추가합니다. 폴더 안의 `Oblivion.esm` 및 ESP가 모드 최상위에 있어야 합니다.
7. MO2 왼쪽 목록에서 **obCJK보다 번역 모드를 아래에** 두어 번역 모드의 `OBSE\plugins\obCJK\obCJK.ini`가 적용되게 합니다. 기존 TheGreatestKorean 방식 한글 모드와 시험판 번역 모드는 끕니다. 설치한 공식 DLC만 활성화하고 기존 플러그인 로드 순서를 유지합니다.
8. MO2 실행 대상에서 **Oblivion**을 선택해 실행합니다. 구형 MO2 인스턴스는 [MO2 공식 xOBSE 실행 안내](https://github.com/ModOrganizer2/modorganizer/wiki/Running-Oblivion-OBSE-with-MO2)에 따라 `Force Load Libraries` 설정을 확인합니다.

명령 예:

```bat
install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data" "D:\Oblivion MO2\profiles\한국어\Oblivion.ini"
```

기존 `output\Oblivion_KR_obCJK`가 비어 있지 않으면 덮어쓰지 않고 중단합니다. 업데이트할 때 새 폴더에 설치기 ZIP을 풀어 실행하세요. Windows 사용자 글꼴에 동일 이름의 다른 파일이 이미 있으면 그 파일을 보존하고 설치를 중단합니다.

## 글꼴과 표시

- 메뉴·제목·일반 책, 대사/HUD, 지도/팝업의 한글: **본명조 KR Medium**.
- 편지·손글씨 책의 한글: **이롭게바탕체 Medium**.
- MenuQue 7/8 및 NorthernUI 33–37의 한글: 본명조 KR Regular. 해당 UI 모드를 설치한 경우에만 사용합니다.
- 영문·숫자·제어문자: 원래 게임의 글꼴과 렌더링. 종족 설명의 줄바꿈과 이름 입력 커서에서 생기는 네모 표시를 피하기 위해 `AsciiRenderEnable = 0`을 사용합니다.

설치기는 본명조 Regular/Medium과 이롭게바탕체를 **현재 Windows 사용자에게 자동 등록**합니다. 관리자 권한은 필요하지 않습니다. 글꼴이 이미 동일하게 설치돼 있으면 재사용합니다. 폰트를 MO2 폴더에 복사하는 것만으로는 Windows 등록이 되지 않습니다.

글꼴 원본은 변경하지 않았으며 OFL 1.1 저작권·라이선스를 함께 제공합니다. 출처와 SHA-256은 `font_sources.json`, 원문 라이선스는 `licenses`에 있습니다. 상세 설정은 저장소의 [글꼴 안내](https://github.com/munument1/-KR-Oblivion-Translation/blob/obcjk-unicode/docs/obcjk/font_slots_guide.md)를 참고하세요.

## 지원 범위와 검증

본편, Shivering Isles, Knights of the Nine, DLCBattlehornCastle, DLCFrostcrag, DLCHorseArmor, DLCMehrunesRazor, DLCOrrery, DLCSpellTomes, DLCThievesDen, DLCVileLair를 지원합니다. 설치되지 않은 DLC는 만들지 않습니다. 종족 이름은 음성 경로 호환성을 위해 영어로 유지합니다. 일부 개발/디버그 문자열과 원문 대조가 확정되지 않은 위치명은 영어가 남을 수 있습니다.

v1.0.5는 기존 번역을 UTF-8로 변환하고 검증된 CELL/WRLD 한글 위치명을 적용합니다. 원본 게임 Data와 실행 파일을 수정하지 않습니다. FormID, 레코드 구조와 컴파일된 스크립트를 보존하며 출력 폴더에 검증 보고서를 생성합니다. 기존 방식의 동영상 재인코딩은 실행하지 않습니다.

MO2 시험 환경에서 UTF-8 메뉴, 한글 위치명을 포함한 저장 파일 생성, 본명조 적용과 줄바꿈·입력 커서 네모 표시 수정은 확인했습니다. 저장 생성 확인을 모든 기존 세이브의 재로딩·장시간 플레이 검증으로 확대해 해석하지 않습니다.

v1.0.4와 이전 릴리스는 [기존 Releases](https://github.com/munument1/-KR-Oblivion-Translation/releases/tag/v1.0.4)에 그대로 유지합니다. 기존 바이트 방식의 한글 패치와 UTF-8 번역 모드를 함께 활성화하지 마세요.
