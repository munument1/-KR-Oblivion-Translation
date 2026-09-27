# 실행 파일 기본 문구 조사 (2026-09-27)

`Oblivion.exe`의 문자열 게임 설정 기본값을 원본 `Oblivion.esm`의 GMST 키와 비교했다. 실행 파일 안에서 `s...` 설정 이름과 인접한 ASCII 기본값이 확인되고 ESM에 같은 키가 없는 경우만 후보로 기록했다. 리마스터 한국어 자료는 **설정 키로만** 연결했다. 문자열 원문이나 Source String Hash가 동일하다고 검증한 결과는 아니다.

기준 파일 SHA-256:

- `Oblivion.exe`: `A8F313845C1545E9A60E1E995961EEF4C033115DA9443F6D756341DF3C2B7DC6`
- `Oblivion.esm`: `A26E21EA8C3041F8737FFB3A266129DEDB7F8A88590625ECFECD5EB7F66B4A70`

| 조사 결과 | 개수 |
| --- | ---: |
| 원본 ESM의 문자열 GMST 키 | 108 |
| ESM에 없는 실행 파일 기본값 후보 | 756 |
| 경로·자산명처럼 보이는 값을 제외한 텍스트 후보 | 605 |
| 텍스트 후보 중 리마스터 한국어와 키가 일치한 항목 | 343 |

후보에는 메뉴, 상태 알림, 캐릭터 생성, 버튼 이름 등이 섞여 있다. 현재 설치기에 반영하고 게임에서 확인한 것은 종료 확인창의 `sExitGameAffirm`, `sExitGameQuestion`, `sCancel` 세 항목이다. 추가 검토 우선 항목은 `sContinueLastSave`, `sLoadFromMainMenu`, `sSaveOverSaveGame`, `sDeleteSaveGame`, `sMenuDisplayNoSaves` 등 저장·불러오기 관련 문구다.

이 수치는 실제로 화면에 영어로 나타나는 항목 수가 아니다. 메뉴 XML의 기존 번역, 게임 상태, 플랫폼별 기능, 설정이 사용되는 맥락을 확인해야 한다. 리마스터 문구는 원작의 자리표시자와 문맥이 다를 수 있어 키 일치만으로 일괄 이식하지 않는다. 설치기에는 화면에서 확인하고 원문·인코딩을 검증한 문구만 추가한다.

재현: `python audit_menu_gmst.py --exe <Oblivion.exe> --esm <Oblivion.esm> --locres-csv <remastered_korean_locres.csv> --output <audit.csv>`. 리마스터 CSV는 선택 사항이며 저장소·릴리스에는 포함하지 않는다.
