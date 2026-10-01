# v1.0.5 배포 검증

2026-10-02, Windows / Steam Oblivion / MO2 시험 구성 기준.

- `test_obcjk_overlay`, `test_obcjk_locations`, `test_obcjk_installer`, `test_legacy_text_codec`: 총 13개 검사 통과.
- PyInstaller로 만든 Windows EXE를 원본 게임 Data에 직접 실행해 종료 코드 0을 확인했다. 설치기를 MO2 안에서 실행한 것이 아니다.
- EXE는 기존 번역을 엄격하게 복구·UTF-8 변환하고 한글 위치명을 적용한다. C드라이브의 임시 작업 폴더와 D드라이브 출력 폴더를 사용하는 환경에서 전체 빌드를 검증했다.
- CSV 84,349행 변환 실패 0. 이 행 수는 중복을 포함하므로 게임에 적용한 독립 문자열 수가 아니다.
- 공식 출력 ESM/ESP 10개는 `_build/obcjk/korean-locations-final` 및 `cli-final`의 게임 시험판과 SHA-256이 같다. 한글 위치명 변경 1,927필드. Shivering Isles의 작은 로더 ESP에는 번역 필드가 없어 원본을 사용하며 본문은 Oblivion.esm에 있다.
- 출력의 UTF-8 변환 보고서와 위치명 보고서를 함께 검증했다. 위치명 치환 후에도 레코드/그룹 식별자·스크립트 해시를 보존한다. 두 단계의 전후 SHA-256은 각각 보고서에 연결한다.
- EXE의 글꼴 설치와 ZIP에서 추출한 EXE의 재실행을 확인했다. 본명조 Regular/Medium, 이롭게바탕체는 GDI에서 실제 선택되고 각각 한글 11,172자 누락 0이다. 동일 글꼴의 재설치는 기존 파일을 재사용했다.
- 임시 MO2 프로필 INI에서 BOM/CRLF·다른 설정을 보존하고 글꼴 다섯 경로만 변경하는 검사, 원본 백업 보존 및 불완전 INI 사전 거부 검사를 통과했다. 실사용 프로필 INI는 릴리스 검증 중 수정하지 않았다.
- 배포 전후 원본·프로필·기존 v1.0.4 EXE·시험 세이브를 포함한 파일 105개의 SHA-256 변화 0.
- Nexus용 ZIP은 기본 ESP 11개와 Optional ESP 2개로 구성했다. 한글 위치명 변경 1,361필드. 각 파일의 UTF-8/위치명 보고서와 ZIP 안 SHA-256, ZIP CRC를 확인했다. 번역 없는 Vampire Aging & Face Fix는 포함하지 않는다.
- GitHub ZIP에는 본편/언오피셜 ESM·ESP 또는 외부 xOBSE/obCJK DLL이 들어 있지 않다. Windows EXE 내부에는 번역 빌더·번역 자료·폰트가 포함되며 출력 폴더에 obCJK 설정 파일을 생성한다.

실행 로그와 상세 로컬 검증 결과는 `_build/obcjk/release-v1.0.5/`에 보관했다. 사용자는 본명조 적용 후 종족 설명·이름 입력 커서의 정상 표시를 확인했다. 한글 위치명 저장 파일 생성도 이전 시험에서 확인했다. 모든 기존 세이브 재로딩·장시간 플레이·퀘스트/책 UI 전수 검증을 완료했다는 뜻은 아니다.
