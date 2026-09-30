@echo off
setlocal EnableExtensions
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" (
  echo Usage: build.bat [Debug^|Release]
  exit /b 2
)
call "%~dp0app\winui\build.cmd" "%CONFIG%"
exit /b %ERRORLEVEL%
