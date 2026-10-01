# The Elder Scrolls IV: Oblivion Original 한국어 번역

오리지널 The Elder Scrolls IV: Oblivion (2006) 본편과 공식 확장팩/DLC를 대상으로 하는 한국어 번역 빌더입니다.

이 저장소의 GitHub Release는 본편 + 공식 DLC 전용입니다. Unofficial Oblivion Patch / Unofficial Shivering Isles Patch / Unofficial Oblivion DLC Patches용 한국어 ESP는 이 저장소의 릴리즈에 포함하지 않습니다.

## v1.0.4 지원 범위

- Oblivion.esm
- Knights of the Nine
- Shivering Isles
- DLCBattlehornCastle / DLCFrostcrag / DLCHorseArmor / DLCMehrunesRazor
- DLCOrrery / DLCSpellTomes / DLCThievesDen / DLCVileLair
- 한국어 폰트 및 메뉴 문자열
- 일부 Oblivion.exe 기본 UI 문자열의 GMST 오버레이
- 인트로/아웃트로 자막 소스

플레이어용 일반 대사, 퀘스트 저널, 실제 책 본문을 우선하여 번역했습니다. TEST, DEBUG, TEMP, Script Effect 같은 개발/엔진 내부 문자열은 의도적으로 영어로 남을 수 있습니다.

## 설치

1. Releases에서 Oblivion_Original_KR_Installer_v1.0.4.zip을 내려받아 압축을 풉니다.
2. install.bat을 실행합니다.
3. 설치된 오리지널 Oblivion의 Data 폴더를 지정합니다.
4. 생성된 output\Oblivion_KR_Mod를 MO2에 별도 모드로 등록합니다.
5. MO2 프로필별 INI를 사용하는 경우 두 번째 인수로 해당 oblivion.ini를 지정할 수 있습니다.

예: install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data"

MO2 프로필 INI 예: install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data" "D:\Oblivion MO2\profiles\Default\oblivion.ini"

릴리즈에는 Python 없이 실행할 수 있는 OblivionKRBuilder.exe가 포함되어 있습니다.

## 저장 안정성

원본 게임 파일을 직접 덮어쓰지 않고 별도의 한국어 오버레이를 생성합니다.

특히 저장 파일 생성/불러오기 문제를 피하기 위해 CELL/FULL, WRLD/FULL 및 저장 안정성에 영향을 줄 수 있는 위치/참조 이름은 의도적으로 영어로 유지합니다. FormID, 레코드 구조, 컴파일된 스크립트는 변경하지 않습니다.

Oblivion.exe도 직접 수정하지 않습니다. 실행 파일의 일부 사용자 인터페이스 기본 문자열은 ESM의 GMST 오버레이 방식으로 번역합니다.

## 빌더 검증

v1.0.3 릴리즈용 OblivionKRBuilder.exe는 Steam 오리지널 Data에 직접 실행하여 Oblivion.esm, Knights.esp 및 모든 공식 DLC 출력이 정상 생성되는 것을 검증했습니다. v1.0.4는 동일한 빌더 코드에서 GMST 번역 데이터만 보정한 패치 릴리즈이며, 릴리즈 설치기는 현재 main 소스에서 새로 빌드합니다.

빌더는 번역 대상의 원문과 레코드 구조를 검증한 뒤 문자열 필드만 교체합니다.

## 번역 자료

기존 오리지널 한국어 패치 자료와 공식 한국어판에서 대응 가능한 번역을 회수하고, 레코드/EditorID/원문/퀘스트 stage/대사 문맥을 검증해 보강하는 방식으로 제작했습니다. 위치명처럼 저장 안정성에 영향을 줄 수 있는 필드는 자동 적용 대상에서 제외했습니다.

## v1.0.4

문/출입구의 목적지 표시와 주문·아이템 효과 설명에 남아 있던 영어식 조합 문구를 교정한 패치 릴리즈입니다. `sTo`의 `~에게`를 `->`로 바꾸고, 마법 효과 조합용 GMST를 `범위:`, `지속:`, `적용:` 중심의 정보형 표기로 정리했습니다. Damage는 `피해`, Self는 `자신`, Touch는 `접촉`, Strike는 `공격 적중`, up to level은 `최대 레벨`로 교정했습니다.

## v1.0.3

v2 전면 검수 결과를 실제 빌드 데이터에 반영한 릴리즈입니다. MASTER 8,553건과 BOOK 본문 496건을 영어 원문과 대조해 GPT-5.6 Sol이 최종 확정했으며, ACTIVE 용어집과 고유명사 아포스트로피/하이픈 정책을 적용했습니다. Madness→광기, Vitharn→비탄, Grummite→그루마이트, Drain/Absorb 구분 등 확정 용어를 전역 반영하고 BOOK 마크업 및 커스텀 한글 폰트 인코딩 호환성도 최종 점검했습니다.

## v1.0.2

최종 검수 통합 릴리즈. 본편/DLC 번역 검수본과 최신 용어 기준을 반영하고, RACE 이름은 음성 경로 호환성을 위해 영어 원문으로 유지합니다. 메뉴 GMST 추출 자료 926개를 기준으로 플레이어 노출 메뉴 문자열을 Oblivion.esm에 직접 통합했으며, 별도 메뉴 ESP 없이 캐릭터 생성, 스킬/레벨, 저장/불러오기, 옵션/컨트롤 등 UI 번역을 보강했습니다.

## v1.0.1

메뉴 번역 보완 릴리즈. 캐릭터 생성창의 Face/Hair/Eyes, Yes/No, On/Off, Main Menu 및 관련 메뉴 라벨을 보완하고, 스킬 창의 21개 개별 스킬명과 관련 능력치(힘/지능/의지력/민첩성/속도/지구력/매력/행운), 전문분야(전투/마법/은신)를 모두 한국어화했습니다.

## v1.0.0

첫 정식 릴리즈. 오리지널 Oblivion 본편과 공식 확장팩/DLC의 한국어 번역, 폰트, 메뉴 및 안전한 UI 오버레이를 제공합니다.