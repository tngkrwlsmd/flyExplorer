@echo off
setlocal EnableExtensions
rem M1.6 independent read-only native helper. No MFC/WinUI product deployment.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\..\"
set "OUT=%ROOT%out\helper\%CONFIG%"
set "OBJ=%ROOT%out\obj\helper\%CONFIG%"
set "MSBUILD=C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe"
if not exist "%MSBUILD%" exit /b 3
rem Do not edit generated .vcxproj: the tracked template is canonical.
copy /y "%HERE%FlyShellIsolationHelper.project-template.xml" "%HERE%FlyShellIsolationHelper.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyShellIsolationHelper.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 "/p:OutDir=%OUT%/" "/p:IntDir=%OBJ%/" /v:minimal /m:2
if errorlevel 1 exit /b 5
exit /b 0
