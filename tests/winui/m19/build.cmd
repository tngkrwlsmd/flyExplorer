@echo off
setlocal EnableExtensions
rem Isolated M1.9 native contracts only; never touches legacy configuration.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\..\"
set "MSBUILD="
for /f "usebackq delims=" %%I in (`python -X utf8 "%ROOT%tools\winui\resolve_msbuild.py"`) do set "MSBUILD=%%I"
if not defined MSBUILD exit /b 3
if not exist "%MSBUILD%" exit /b 3
copy /y "%HERE%FlyM19NativeContracts.project-template.xml" "%HERE%FlyM19NativeContracts.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyM19NativeContracts.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 /v:minimal /m:2
if errorlevel 1 exit /b 5
exit /b 0
