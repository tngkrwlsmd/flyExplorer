@echo off
setlocal EnableExtensions
rem G01: deterministic owned pipe/child-exit race; no product profiles.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\..\"
set "MSBUILD="
for /f "usebackq delims=" %%I in (`python -X utf8 "%ROOT%tools\winui\resolve_msbuild.py"`) do set "MSBUILD=%%I"
if not defined MSBUILD exit /b 3
if not exist "%MSBUILD%" exit /b 3
copy /y "%HERE%FlyG01PipeExitRace.project-template.xml" "%HERE%FlyG01PipeExitRace.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyG01PipeExitRace.vcxproj" /nologo /t:Rebuild "/p:Configuration=%CONFIG%" /p:Platform=x64 /v:normal /m:2
if errorlevel 1 exit /b 5
exit /b 0
