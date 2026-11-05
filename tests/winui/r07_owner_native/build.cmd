@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\..\"
set "MSBUILD="
for /f "usebackq delims=" %%I in (`python -X utf8 "%ROOT%tools\winui\resolve_msbuild.py"`) do set "MSBUILD=%%I"
if not defined MSBUILD exit /b 3
if not exist "%MSBUILD%" exit /b 3
copy /y "%HERE%FlyR07OwnerNative.project-template.xml" "%HERE%FlyR07OwnerNative.vcxproj" >nul || exit /b 4
"%MSBUILD%" "%HERE%FlyR07OwnerNative.vcxproj" /nologo /t:Build /p:Configuration=Release /p:Platform=x64 /v:minimal /m:2
if errorlevel 1 exit /b 5
exit /b 0
