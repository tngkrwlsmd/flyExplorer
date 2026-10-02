@echo off
setlocal EnableExtensions
rem M2.0: native UI state/command contract; NO MFC user config access.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\..\"
set "MSBUILD="
for /f "usebackq delims=" %%I in (`python -X utf8 "%ROOT%tools\winui\resolve_msbuild.py"`) do set "MSBUILD=%%I"
if not defined MSBUILD exit /b 3
if not exist "%MSBUILD%" exit /b 3
copy /y "%HERE%FlyM22ShellTransferContracts.project-template.xml" "%HERE%FlyM22ShellTransferContracts.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyM22ShellTransferContracts.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 /v:minimal /m:2
if errorlevel 1 exit /b 5
exit /b 0
