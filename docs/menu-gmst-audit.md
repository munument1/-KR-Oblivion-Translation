# 실행 파일 기본 문구 조사 (2026-09-27)

원본 `Oblivion.exe`에서 `s...` 설정 이름과 인접한 ASCII 기본값을 추출했다. ESM이나 리마스터 CSV와 대조하지 않은 **실행 파일 자체의 목록**이다.

기준 파일 SHA-256:

- `Oblivion.exe`: `A8F313845C1545E9A60E1E995961EEF4C033115DA9443F6D756341DF3C2B7DC6`

| 조사 결과 | 개수 |
| --- | ---: |
| 실행 파일 문자열 설정 후보 | 823 |
| 경로·자산명처럼 보이는 값을 제외한 텍스트 후보 | 670 |

후보에는 메뉴, 상태 알림, 캐릭터 생성, 버튼 이름 등이 섞여 있다. 현재 설치기에 반영하고 게임에서 확인한 것은 종료 확인창의 `sExitGameAffirm`, `sExitGameQuestion`, `sCancel` 세 항목이다. 추가 검토 우선 항목은 `sContinueLastSave`, `sLoadFromMainMenu`, `sSaveOverSaveGame`, `sDeleteSaveGame`, `sMenuDisplayNoSaves` 등 저장·불러오기 관련 문구다.

이 수치는 미번역 항목 수가 아니다. 메뉴 XML이나 다른 게임 파일에서 이미 번역했을 수 있고, 게임 상태나 플랫폼에 따라 쓰이지 않을 수도 있다. 설치기에 추가할 때는 오리지널 번역 자료의 대응 문구와 실제 화면 표시·원문·인코딩을 확인한다.

재현: `python audit_menu_gmst.py --exe <Oblivion.exe> --output <audit.csv>`.
