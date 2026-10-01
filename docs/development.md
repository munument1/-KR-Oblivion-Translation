# 빌드와 저장소 구성

현재 main은 v1.0.5 UTF-8 설치기를 기준으로 합니다. 사용자 안내는 루트 README.md 한 곳에서 관리합니다.

## Windows 설치기 빌드

```powershell
python -m unittest discover -s tests -v
pyinstaller --noconfirm --clean OblivionKRBuilder.spec
python package_obcjk_installer.py --exe dist/OblivionKRBuilder.exe --output dist/Oblivion_Original_KR_Installer_v1.0.5.zip
```

설치기 ZIP에는 EXE, 한국어 BAT, 사용자 안내, 글꼴 출처와 OFL 라이선스만 넣습니다. 게임의 원본 ESM/ESP, 외부 DLL, MO2 프로필, 세이브는 포함하지 않습니다. 설치기를 MO2에서 실행할 필요는 없습니다.

## 코드와 자료

- `install_obcjk.py`: 기존 INI 자동 검색·글꼴 경로 복원, 기존 번역 빌더 호출, 글꼴 등록.
- `build_vanilla_overlay.py`, `build_unofficial_release.py`: 기존 번역과 원본을 대조하는 변환 기반. UTF-8 생성 과정에서 필요하므로 유지합니다.
- `build_obcjk_*.py`, `obcjk_text_backend.py`, `oblivion_korean_codec.py`: UTF-8 변환, UI와 한글 위치명 적용·검증.
- 루트 CSV 23개: 설치기의 실제 번역 입력. 이름에 legacy/remaster가 있어도 사용 중이므로 삭제하지 않습니다.
- `assets/obcjk_fonts`: 원본 글꼴 3개, obCJK.ini, 라이선스와 SHA-256 목록.
- `assets/Fonts`, `assets/menus`: 기존 인코딩 변환과 UI 입력 자료.
- `build_video_subtitles.py`, `video_subtitles`: 사용자 원본 인트로·엔딩에 한국어 자막을 입혀 Bink 1 영상 2개를 생성합니다. PATH/기본 설치 위치의 FFmpeg·ffprobe·RAD를 먼저 사용하고, 없으면 검증된 공식 배포본을 `%LOCALAPPDATA%\\OblivionKRInstaller\\video-tools`에 자동 준비합니다. 다운로드는 고정 해시를 검증합니다. 필수 생성 검증에는 `--video-subtitles required`를 사용합니다.
- `tests`: 문자열·바이너리 보존, 위치명, INI 및 글꼴 검증.
- `docs/obcjk`: 조사 이력, 설정 설명과 실행 검증 기록.
- `docs/v2_review`, `v2_tools`, 루트 audit/extract 도구: 번역 검수 이력과 보강 도구. 설치기에는 포함하지 않습니다.
- `docs/legacy`: 과거 사용자 안내. 과거 배포의 재현은 해당 버전 태그를 사용합니다.
- `_build`, `build`, `dist`, `output`, `release`, `v2_work`: 로컬 작업·출력이며 Git에서 제외합니다.

## Nexus ZIP 분리

```powershell
python package_obcjk_unofficial.py --patch UOP --input-dir _build/obcjk/full-uop --locations _build/obcjk/korean-locations-final --output dist/UOP_KR_UTF8_obCJK_v1.0.5.zip
python package_obcjk_unofficial.py --patch USIP --input-dir _build/obcjk/full-usip --locations _build/obcjk/korean-locations-final --output dist/USIP_KR_UTF8_obCJK_v1.0.5.zip
python package_obcjk_unofficial.py --patch UODP --input-dir _build/obcjk/full-uodp --locations _build/obcjk/korean-locations-final --output dist/UODP_KR_UTF8_obCJK_v1.0.5.zip
```

선택 ESP는 해당 ZIP의 Optional에 둡니다. 패키징은 UTF-8 변환 보고서와 한글 위치명 보고서의 전후 SHA-256을 확인하며, 각 ZIP에 해당 모드의 ESP만 포함합니다.

## main 정리

중복 설치 BAT/README/spec, 구형 통합 언오피셜 패키저와 사용이 끝난 v1.0.4 전용 자동 배포 워크플로를 제거했습니다. 과거 릴리스·태그와 검수 원자료는 유지합니다. 코드 정리만으로 새 프로필을 만들거나 실사용 세이브를 변경하지 않습니다.
