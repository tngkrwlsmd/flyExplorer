@echo off
setlocal EnableExtensions
set "STAGE=%~1"
if "%STAGE%"=="" set "STAGE=source"
set "CONFIG=%~2"
if "%CONFIG%"=="" set "CONFIG=Release"
python -X utf8 "%~dp0tools\winui\run_checks.py" "%STAGE%" --configuration "%CONFIG%"
exit /b %ERRORLEVEL%
