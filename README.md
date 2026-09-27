# Oblivion Original 한국어 번역 설치기

원본 **Oblivion.esm과 공식 DLC**를 사용자의 게임 설치에서 읽어 한국어 MO2 모드 폴더를 만듭니다. 최신 UOP/USIP/UODP는 입력, 수정, 출력에 포함하지 않습니다.

## 사용 방법

1. [Releases](https://github.com/munument1/-KR-Oblivion-Translation/releases)에서 설치기 압축파일을 받아 압축을 풉니다.
2. `install.bat`을 실행하고 원본 게임의 `Data` 폴더 경로를 입력합니다. 명령줄에서 `install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data"`처럼 지정해도 됩니다.
3. 생성된 `output\Oblivion_KR_Mod` 폴더를 MO2에 모드로 추가합니다. 원본 게임 파일은 건드리지 않습니다.
4. 설치기는 Windows가 지정한 실제 **문서** 폴더(OneDrive로 이동된 경우 포함)의 `My Games\Oblivion\Oblivion.ini`에 한글 폰트 1–3을 설정합니다. 파일이 없으면 게임의 `Oblivion_default.ini`에서 생성합니다. 기존 INI는 수정 전에 백업합니다.
5. MO2에서 **프로필별 게임 INI**를 사용하는 경우에는 두 번째 인수에 해당 프로필 INI를 지정합니다. 예: `install.bat "C:\Games\Steam\steamapps\common\Oblivion\Data" "D:\Oblivion MO2\profiles\Default\oblivion.ini"`. MO2 설치 폴더 바로 아래의 `oblivion.ini`에 설정을 추가하는 것만으로는 활성 게임 INI가 바뀌지 않을 수 있습니다.
6. 공식 DLC가 활성화되어 있다면 MO2에서 기존 플러그인 로드 순서를 유지합니다. 출력 폴더에는 바뀐 플러그인만 들어갑니다.

Python 3.10 이상이 있으면 저장소의 `install.bat`을 그대로 실행할 수 있습니다. 릴리스에는 Python 없이 실행하는 `OblivionKRBuilder.exe`도 포함됩니다.

## 적용 원칙

- 이전 작업의 `applied_translations_v2.csv`와 기존 한글 폰트·메뉴 자산을 재사용합니다.
- FormID, 레코드 종류, 필드, **원본 영어 문자열의 정확한 일치**를 모두 확인한 뒤 기존 문자열 서브레코드만 바꿉니다. 문자열 순서로 매칭하지 않습니다.
- UOP/USIP 번역 행은 바닐라 원본에 **동일한 레코드와 영어 문자열이 있는 경우에만** 번역 메모리로 활용합니다. Unofficial Patch의 기능 레코드나 ESP를 복사하지 않습니다.
- 실행 파일 기본값 중 기존 오리지널 한글패치에 번역이 있는 문자열 378건을 `exe_gmst_translations.csv`에서 가져옵니다. 실행 파일의 설정 이름과 **영어 기본값이 정확히 일치할 때만** 적용합니다. 종료 확인창 3건을 합쳐 문자열 게임 설정 381건을 ESM에 추가합니다. `install.bat`이 실행하는 빌더에 포함되며 게임 실행 파일은 수정하지 않습니다.
- 튜토리얼 `MQ01` 저널 단계 문구 43건(`QUST/CNAM`)과 로딩 화면 문구 337건(`LSCR/DESC`)을 기존 오리지널 한글패치에서 가져옵니다. FormID, EditorID, 퀘스트 단계와 동일 단계 내 순서, 원본 영어 바이트를 확인하고 문자열 필드만 교체합니다. 다른 퀘스트 저널은 구버전 패치와 오리지널의 단계 문구가 어긋나는 사례가 있어 추가 검토 전까지 제외합니다.
- **일반 저장 보호:** `CELL/FULL`과 `WRLD/FULL` 장소명은 원본 영어를 유지합니다. 기존 한글패치의 특수 한글 바이트가 현재 장소명에 들어가면 일반 저장은 성공 메시지가 나와도 파일이 생기지 않을 수 있습니다. 자동 저장과 콘솔 저장은 별도로 동작합니다. 출력 ESM의 장소명 1,825건이 원본과 동일한지 검사했습니다. 참고: [Bethesda 저장 문제 안내](https://help.bethesda.net/app/answers/detail/a_id/17980/~/what-can-i-do-if-i-cannot-get-oblivion-to-save), [obCJK 제작자의 현상 설명](https://www.nexusmods.com/oblivion/mods/56434).
- 출력 검사는 기존 레코드·그룹 식별자와 SCPT, QUST, INFO 내부 스크립트 바이트의 원본 일치 여부, 새 문자열 설정 381건의 추가를 확인합니다. `translation_audit.json`에는 파일별 SHA-256과 각 문자열의 원문 SHA-256을 기록합니다.
- `DLCShiveringIsles.esp`가 85바이트인 설치본에서는 그 ESP에 적용할 문자열이 없습니다. 해당 콘텐츠에서 본편 ESM에 들어 있는 번역 대상은 ESM에서 처리합니다.

## 현재 기준 시험 결과

2026-09-27, Steam 원본 `Oblivion.esm` 및 공식 DLC 복사본으로 검증했습니다.

| 대상 | 적용 문자열 |
| --- | ---: |
| Oblivion.esm | 12,139 |
| Knights.esp | 118 |
| DLCSpellTomes.esp | 632 |
| 그 외 공식 DLC | 37 |
| 합계 | **12,926** |

매칭되지 않은 CSV 행은 적용하지 않습니다. 시험에서 레코드·그룹 식별자와 SCPT, QUST, INFO 스크립트 바이트 비교는 모두 통과했습니다. MO2에서 별도 UOP 한글 번역 모드를 끈 상태로 일반 저장 파일 생성·불러오기, 튜토리얼 저널, 로딩 화면과 일부 메뉴의 한글 표시를 확인했습니다. 다른 화면은 게임에서 계속 확인해야 합니다. 다른 모드가 나중에 같은 레코드를 덮으면 해당 문자열은 바뀔 수 있습니다.

MO2에서 기존 `Unofficial Oblivion Patch-KR`, `Unofficial Shivering Isles Patch-KR`, `Unofficial Oblivion DLC Patches-KR` 같은 **별도 한글 ESP**를 켜 두면 ESM 뒤에서 장소명을 다시 한글로 덮을 수 있습니다. 일반 저장을 시험할 때는 이 번역 모드를 끄고 최신 영문 패치만 유지하세요. 이 설치기는 해당 패치를 설치하거나 수정하지 않습니다.

## 출처

- 원본 게임과 공식 DLC: 사용자가 소유한 Oblivion 설치에서 읽음. 게임 플러그인 원본이나 번역 적용본은 저장소·릴리스에 포함하지 않습니다.
- 기본 번역 CSV: 프로젝트 [번역 결과물](https://drive.google.com/drive/folders/1Q9jgIRLbAxJRju7dQ3Q1pyVrE-xfBzg3)의 `applied_translations_v2.csv`.
- 저널·로딩 화면·실행 파일 기본값 번역: 프로젝트 [오리지널 번역 자료](https://drive.google.com/drive/folders/1PipuKlwez2ECvncPlGDCzCI6A4YZWKKy)의 `오블 엘갤럼 한글패치 합친버전v2`에서 문자열 값만 추출. 구버전 Unofficial Patch의 기능 레코드는 사용하지 않습니다.
- 폰트·메뉴 자산: 프로젝트 [오리지널 번역 자료](https://drive.google.com/drive/folders/1PipuKlwez2ECvncPlGDCzCI6A4YZWKKy)의 `오블 엘갤럼 한글패치 합친버전v2`.

## 개발

```powershell
python build_vanilla_overlay.py --data-dir "C:\Games\Steam\steamapps\common\Oblivion\Data" --output ".\output\Oblivion_KR_Mod"
```

빌더는 출력 위치가 원본 `Data` 폴더 안팎으로 겹치면 중단합니다.

추가 문자열 검증을 위해 원본 `Data` 폴더의 상위 경로에 `Oblivion.exe`가 있어야 합니다. 다른 실행 파일 버전에서 영어 기본값이 다르면 해당 항목을 적용하지 않고 중단합니다.

실행 파일에 들어 있는 다른 문자열 게임 설정 후보는 `audit_menu_gmst.py`로 조사할 수 있습니다. 이 도구는 EXE만 읽으며, 출력은 미번역 목록이 아닙니다. 실제 게임 화면에서 확인하기 전에는 번역 설정으로 자동 추가하지 않습니다.
