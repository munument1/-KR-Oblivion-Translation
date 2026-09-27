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
set "INI_PATH=%USERPROFILE%\Documents\My Games\Oblivion\Oblivion.ini"
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
  "%RUNNER%" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%"
) else (
  "%RUNNER%" --data-dir "%DATA_DIR%" --output "%OUT_DIR%"
)
goto finish
:run_py
if exist "%INI_PATH%" (
  py -3 "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%"
) else (
  py -3 "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%"
)
goto finish
:run_python
if exist "%INI_PATH%" (
  python "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --ini "%INI_PATH%"
) else (
  python "%~dp0build_vanilla_overlay.py" --data-dir "%DATA_DIR%" --output "%OUT_DIR%"
)
:finish
if errorlevel 1 exit /b 1
echo.
echo Overlay ready: "%OUT_DIR%"
if not exist "%INI_PATH%" echo Oblivion.ini was not found. Apply FONT_SETTINGS.txt after the game creates it.
echo Install the output folder as an MO2 mod, or copy its contents into a separate mod overlay.
exit /b 0
