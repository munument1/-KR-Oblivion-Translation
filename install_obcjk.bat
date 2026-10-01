@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
set "DATA_DIR=%~1"
if not defined DATA_DIR (
  echo Original Oblivion Data folder:
  set /p "DATA_DIR=Data folder: "
)
if not exist "%DATA_DIR%\Oblivion.esm" (
  echo Oblivion.esm was not found.
  exit /b 1
)
set "PROFILE_INI=%~2"
if not defined PROFILE_INI (
  echo Close MO2. Enter the obCJK profile's Oblivion.ini path.
  echo Leave empty to keep your profile INI unchanged.
  set /p "PROFILE_INI=Profile INI: "
)
set "OUT_DIR=%~dp0output\Oblivion_KR_obCJK"
if exist "%~dp0OblivionKRObCJKInstaller.exe" (
  if defined PROFILE_INI (
    "%~dp0OblivionKRObCJKInstaller.exe" --data-dir "%DATA_DIR%" --output "%OUT_DIR%" --profile-ini "%PROFILE_INI%"
  ) else (
    "%~dp0OblivionKRObCJKInstaller.exe" --data-dir "%DATA_DIR%" --output "%OUT_DIR%"
  )
) else (
  echo OblivionKRObCJKInstaller.exe is missing. Extract the complete installer package.
  exit /b 1
)
if errorlevel 1 exit /b 1
echo.
echo Fonts and UTF-8 overlay ready: "%OUT_DIR%"
echo Install this output folder as an MO2 mod; enable xOBSE and obCJK separately.
echo Run Oblivion from MO2 with Force Load Libraries enabled.
pause
exit /b 0
