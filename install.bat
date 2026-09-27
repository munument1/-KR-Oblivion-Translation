@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "DATA_DIR=%~1"
if not defined DATA_DIR (
  echo Enter the original Oblivion Data folder path.
  set /p "DATA_DIR=Data folder: "
)
if not exist "%DATA_DIR%\Oblivion.esm" (
  echo Oblivion.esm was not found in: "%DATA_DIR%"
  exit /b 1
)
set "OUT_DIR=%~dp0output\Oblivion_KR_Mod"
set "INI_PATH=%~2"
if not defined INI_PATH (
  for /f "delims=" %%I in ('powershell -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')"') do set "INI_PATH=%%I\My Games\Oblivion\Oblivion.ini"
)
echo Active INI: "%INI_PATH%"
if defined INI_PATH if not exist "%INI_PATH%" if exist "%DATA_DIR%\..\Oblivion_default.ini" (
  for %%I in ("%INI_PATH%") do if not exist "%%~dpI" mkdir "%%~dpI"
  copy /Y "%DATA_DIR%\..\Oblivion_default.ini" "%INI_PATH%" >nul
)
if exist "%~dp0OblivionKRBuilder.exe" (
  set "RUNNER=%~dp0OblivionKRBuilder.exe"
  goto run_exe
)
where py >nul 2>nul
if not errorlevel 1 goto run_py
where python >nul 2>nul
if not errorlevel 1 goto run_python
echo Python 3 or OblivionKRBuilder.exe is required.
exit /b 1
:run_exe
if exist "%INI_PATH%" (
  "%RUNNER%" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%" --video-subtitles auto
) else (
  "%RUNNER%" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --video-subtitles auto
)
goto finish
:run_py
if exist "%INI_PATH%" (
  py -3 "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%" --video-subtitles auto
) else (
  py -3 "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --video-subtitles auto
)
goto finish
:run_python
if exist "%INI_PATH%" (
  python "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%" --video-subtitles auto
) else (
  python "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --video-subtitles auto
)
:finish
if errorlevel 1 exit /b 1
echo.
echo Overlay ready: "%OUT_DIR%"
if not exist "%INI_PATH%" echo Oblivion.ini was not found. Apply FONT_SETTINGS.txt to the active INI.
echo Save-safe mode: CELL and WRLD location names stay in English so menu saves can create files.
echo If you use UOP/USIP/UODP, use the updated Korean ESP overlay that keeps location names in English.
echo Install the output folder as an MO2 mod, or copy its contents into a separate mod overlay.
exit /b 0
