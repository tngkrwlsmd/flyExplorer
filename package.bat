@echo off
setlocal EnableExtensions
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"
if /I not "%CONFIG%"=="Release" (
  echo Usage: package.bat Release
  exit /b 2
)
python -X utf8 "%~dp0packaging\package.py" "%CONFIG%"
exit /b %ERRORLEVEL%
