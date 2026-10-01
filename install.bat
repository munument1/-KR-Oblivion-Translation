@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "DATA_DIR=%~1"
if not defined DATA_DIR (
  echo 오리지널 오블리비언의 Data 폴더 경로를 입력하세요.
  echo 예: C:\Games\Steam\steamapps\common\Oblivion\Data
  set /p "DATA_DIR=Data 폴더: "
)
if not exist "%DATA_DIR%\Oblivion.esm" (
  echo 지정한 폴더에서 Oblivion.esm을 찾을 수 없습니다.
  echo 아무 키나 누르면 종료합니다.
  pause >nul
  exit /b 1
)
set "OUT_DIR=%~dp0output\Oblivion_KR_Mod"
echo FFmpeg와 RAD Video Tools가 있으면 인트로와 엔딩 한국어 자막 영상도 자동 생성합니다.
set "INI_PATH=%~2"
if not defined INI_PATH (
  for /f "delims=" %%I in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')"') do set "INI_PATH=%%I\My Games\Oblivion\Oblivion.ini"
)
if not exist "%~dp0OblivionKRBuilder.exe" (
  echo OblivionKRBuilder.exe가 없습니다. 설치기 ZIP을 모두 압축 해제하세요.
  echo 아무 키나 누르면 종료합니다.
  pause >nul
  exit /b 1
)
if exist "%INI_PATH%" (
  echo 기존 Oblivion.ini를 찾았습니다: "%INI_PATH%"
  "%~dp0OblivionKRBuilder.exe" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%"
) else (
  "%~dp0OblivionKRBuilder.exe" --data-dir "%DATA_DIR%" --output "%OUT_DIR%"
)
if errorlevel 1 (
  echo 생성에 실패했습니다. 위 오류 내용을 확인하세요.
  echo 아무 키나 누르면 종료합니다.
  pause >nul
  exit /b 1
)
echo.
echo 번역 데이터와 obCJK.ini 생성, 글꼴 설치가 완료되었습니다.
echo 생성된 폴더: "%OUT_DIR%"
if exist "%OUT_DIR%\Video\OblivionIntro.bik" if exist "%OUT_DIR%\Video\OblivionOutro.bik" echo 인트로와 엔딩 한국어 자막 영상이 Video 폴더에 포함되었습니다.
if not exist "%OUT_DIR%\Video\OblivionIntro.bik" echo 주의: 동영상 자막이 포함되지 않았습니다. README의 영상 도구 준비 방법을 확인하세요.
if not exist "%OUT_DIR%\Video\OblivionOutro.bik" if exist "%OUT_DIR%\Video\OblivionIntro.bik" echo 주의: 엔딩 자막 영상이 없습니다. 위 오류 내용을 확인하세요.
echo 이 폴더를 MO2에 모드로 넣고 활성화하세요.
echo MO2 왼쪽 목록에서 obCJK와 영문 패치보다 아래에 두세요.
echo xOBSE와 obCJK는 별도로 설치해야 합니다.
echo 기존 바이트 방식 한글 패치와 시험판 번역 모드는 꺼주세요.
echo MO2에서 Oblivion을 선택해 실행하세요.
echo 아무 키나 누르면 종료합니다.
pause >nul
exit /b 0
