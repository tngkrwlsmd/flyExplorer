@echo off
setlocal EnableExtensions
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" (
  echo Usage: run.bat [Debug^|Release] [folder]
  exit /b 2
)
set "EXE=%~dp0app\winui\x64\%CONFIG%\FlyExplorerWinUIShell\FlyExplorerWinUIShell.exe"
if not exist "%EXE%" (
  echo Build missing. Run: build.bat %CONFIG%
  exit /b 3
)
if "%~2"=="" (
  start "" "%EXE%"
) else (
  start "" "%EXE%" "%~2"
)
exit /b 0
