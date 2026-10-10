@echo off
setlocal EnableExtensions
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" (
  echo Usage: run.bat [Debug^|Release] [folder]
  exit /b 2
)
set "EXE=%~dp0out\winui\%CONFIG%\flyExplorer.exe"
set "HELPER=%~dp0out\winui\%CONFIG%\FlyShellIsolationHelper.exe"
if not exist "%EXE%" (
  echo [flyExplorer] Build missing. Run: fly.bat build %CONFIG%
  if "%~1"=="" pause
  exit /b 3
)
if not exist "%HELPER%" (
  echo [flyExplorer] Incomplete build: FlyShellIsolationHelper.exe is missing.
  echo [flyExplorer] Rebuild with: fly.bat build %CONFIG%
  if "%~1"=="" pause
  exit /b 4
)
if "%~2"=="" (
  start "" "%EXE%"
) else (
  start "" "%EXE%" "%~2"
)
exit /b 0
