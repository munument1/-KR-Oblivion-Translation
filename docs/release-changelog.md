# Oblivion Original Korean Translation Release Changelog

Player-facing release notes. Newest releases are listed first.

## Releases

## v1.0.5 (2026-10-02)

### Added

- obCJK용 UTF-8 번역과 검증된 한글 위치명.
- 본명조 Regular/Medium, 이롭게바탕체 및 OFL 라이선스. 설치기가 현재 Windows 사용자에게 글꼴을 자동 등록합니다.

### Changed

- 메뉴·일반 책·대사·지도 한글을 본명조 Medium으로, 편지·손글씨 책 한글을 이롭게바탕체로 표시합니다.
- 본편·공식 DLC 설치기와 Nexus 업로드용 언오피셜 패치 번역 ZIP을 분리합니다.
- UOP / USIP / UODP 번역을 각 원본 모드에 대응하는 세 ZIP으로 배포합니다.
- 설치기 인터페이스를 기존 `install.bat` / `OblivionKRBuilder.exe`로 통일하고 BAT 안내를 한국어로 표시합니다.
- 문서 폴더의 기존 Oblivion.ini를 자동 검색합니다. 별도 프로필 주소를 묻거나 새 프로필·INI·세이브를 만들지 않습니다.
- MO2에 넣는 모드 폴더에는 게임용 번역 데이터, 생성된 자막 영상과 obCJK.ini를 두고 검증 보고서는 폴더 옆에 저장합니다.

### Fixed

- 새 설치기에서 누락된 인트로·엔딩 한국어 자막 영상 자동 생성을 복구했습니다. FFmpeg·ffprobe 및 RAD Video Tools가 없으면 한국어로 누락을 안내합니다.
- 종족 설명의 줄바꿈과 이름 입력 커서 네모 표시를 피하도록 영문·숫자·제어문자에 원래 게임 렌더링을 사용합니다.

### Compatibility

- MO2, 별도 설치한 xOBSE 및 obCJK가 필요합니다. 시험 환경은 xOBSE 22.13 / obCJK 20260807입니다.
- 기존 바이트 방식의 한글 모드 및 UTF-8 시험판 모드는 끄고 새 번역 모드를 사용합니다. v1.0.4는 기존 릴리스에서 유지합니다.
- 저장 파일 생성 확인과 모든 기존 세이브의 재로딩·장시간 플레이 검증은 별개입니다.
