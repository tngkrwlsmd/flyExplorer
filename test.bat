@echo off
setlocal EnableExtensions
set "STAGE=%~1"
if "%STAGE%"=="" set "STAGE=source"
set "CONFIG=%~2"
if "%CONFIG%"=="" set "CONFIG=Release"
if /I "%STAGE%"=="policy" goto :policy
python -X utf8 "%~dp0tools\winui\run_checks.py" "%STAGE%" --configuration "%CONFIG%"
exit /b %ERRORLEVEL%

:policy
python -X utf8 "%~dp0tools\policy\run_policy_checks.py"
exit /b %ERRORLEVEL%
