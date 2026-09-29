@echo off
setlocal EnableExtensions
rem M2.0: native UI state/command contract; NO MFC user config access.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "MSBUILD=C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe"
if not exist "%MSBUILD%" exit /b 3
copy /y "%HERE%FlyM21NativeContracts.project-template.xml" "%HERE%FlyM21NativeContracts.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyM21NativeContracts.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 /v:minimal /m:2
if errorlevel 1 exit /b 5
exit /b 0
