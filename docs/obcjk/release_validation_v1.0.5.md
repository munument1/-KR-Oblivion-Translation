# v1.0.5 배포 검증

2026-10-02, Windows / Steam Oblivion / MO2 시험 구성 기준.

## 동영상 자막 복구 검증

- 새 EXE가 든 ZIP을 풀고 `install.bat` 기본 실행으로 인트로·엔딩 자막을 자동 생성했다. 종료 코드 0, 출력 게임 파일 14개: 기존 번역/설정 12개와 `Video`의 BIK 2개.
- 인트로 115.482149초, 엔딩 58.024691초. 두 영상 모두 Bink 1 `BIKi`, 1280×720, 음성 트랙을 유지하며 FFmpeg로 전체 영상·음성을 오류 없이 디코딩했다. 자막 구간의 프레임을 추출해 한글 표시를 확인했다. 이번 확인은 파일 생성·디코딩 검증이며 새 게임 내 재생 시험과는 구분한다.
- 인트로 SHA-256: `1b3e3014d56484c255a61e21ec086dcced553516762c9ed2435c7153c4eb58e8`.
- 엔딩 SHA-256: `be61654728658220f41bba241f756a710748ecebd55e5ef663455821d0fdd29a`.
- 두 생성 영상은 MO2에 보존된 기존 자막 영상과 해시가 같다. 원본 영상 두 개도 원본 해시를 유지한다. 공식 번역 플러그인 10개와 메뉴, obCJK 설정은 이전 검증본과 동일하다.
- 검사 17개 통과. 기본 자동 영상 생성, 도구 누락 시 한국어 경고/필수 모드 실패, 수정된 원본 영상의 인코딩 전 거부를 확인했다.
- ZIP CRC와 내부 SHA-256, EXE 안의 SRT 2개를 확인했다. ZIP/EXE에 프로필·세이브는 없고 검증 보고서는 모드 폴더 옆에 저장한다. 보호 파일 94개와 프로필 목록이 변하지 않았다.
- 실행 로그·영상 프레임·상세 검증 결과는 `_build/obcjk/release-v1.0.5/video-fix/`에 보관한다.

## 설치기 단순화 및 ZIP 분리 검증 (동영상 복구 전)

- 기존 `install.bat` / `OblivionKRBuilder.exe` 이름과 `output/Oblivion_KR_Mod` 경로를 복원하고 BAT 안내를 한국어로 바꿨다. 별도 프로필 주소 입력은 없으며 기존 문서 폴더의 Oblivion.ini를 자동 검색한다.
- 검사 15개 통과. 자동 검색되는 기존 INI만 변경하고, INI가 없으면 파일이나 프로필을 만들지 않는 경로를 검증했다. UTF-8 BOM/CRLF, 비 UTF-8 바이트, 대소문자가 다른 Fonts 키, 최초 백업을 보존한다.
- 새 EXE가 들어간 ZIP을 풀어 한국어 BAT로 원본 게임 Data에 직접 실행했다. 기존 INI 적용 검증에는 작업 폴더의 단독 INI 파일을 사용했으며 MO2 프로필을 생성하지 않았다.
- 생성된 MO2 모드 파일은 플러그인 10개, menus/strings.xml, OBSE/plugins/obCJK/obCJK.ini의 12개뿐이다. 플러그인과 메뉴는 기존 시험판/배포 검증본과 SHA-256이 같고 설정은 확인된 글꼴 프리셋과 같다.
- 글꼴 3종의 GDI 선택·한글 누락 0을 확인했다. 글꼴 사본과 검증 보고서는 모드 폴더에 넣지 않는다. 보고서는 모드 폴더 옆 `Oblivion_KR_Mod.validation.json`으로 저장한다.
- 게임·MO2·세이브·기존 설치기·사용자 미추적 스크립트 등 파일 118개의 변화 0. MO2 프로필 디렉터리 목록도 변하지 않았다. ZIP과 EXE 내 자료에서 프로필 및 .ess/.obse 세이브 파일 부재를 검사했다.
- UOP ZIP: 기본 ESP 1개와 Citadel Door Fix 선택 ESP 1개, USIP ZIP: 기본 ESP 1개, UODP ZIP: 기본 ESP 9개와 SSSB 선택 ESP 1개. 합계 13개가 기존 검증된 ESP와 바이트 단위로 동일하며 각 ZIP의 목록·SHA-256·CRC를 확인했다.
- 기존 릴리스와 태그는 보존하며 1.0.5 설치기 자산과 main 소스를 정정한다. 상세 결과는 `_build/obcjk/release-v1.0.5/corrected/validation.json`과 `split_package_validation.json`에 있다.

## 최초 배포 구성 검증 (정정 전)

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
