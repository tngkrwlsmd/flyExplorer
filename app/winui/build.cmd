@echo off
setlocal EnableExtensions
rem Canonical flyExplorer WinUI 3 product build.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\"
set "MSBUILD=C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe"
if not exist "%MSBUILD%" exit /b 3
rem Build the matching isolated Shell helper, then stage it beside the app.
call "%HERE%helper\build.cmd" "%CONFIG%"
if errorlevel 1 exit /b 8
rem Canonical tracked templates own the generated project after any source edit.
copy /y "%HERE%FlyExplorerWinUIShell.project-template.xml" "%HERE%FlyExplorerWinUIShell.vcxproj" >nul || exit /b 4
copy /y "%HERE%FlyExplorerWinUIShell.filters-template.xml" "%HERE%FlyExplorerWinUIShell.vcxproj.filters" >nul || exit /b 5
if not exist "%ROOT%logs\phase6-winui" mkdir "%ROOT%logs\phase6-winui"
rem Keep the package cache inside this repository's ignored logs tree.
set "NUGET_PACKAGES=%ROOT%logs\phase6-winui\nuget-packages"
set "NUGET_HTTP_CACHE_PATH=%ROOT%logs\phase6-winui\nuget-http"
set "NUGET_PLUGINS_CACHE_PATH=%ROOT%logs\phase6-winui\nuget-plugin"
"%MSBUILD%" "%HERE%FlyExplorerWinUIShell.vcxproj" /nologo /t:Restore "/p:Configuration=%CONFIG%" /p:Platform=x64 "/p:RestoreConfigFile=%HERE%NuGet.Config" "/p:RestorePackagesPath=%NUGET_PACKAGES%" /v:minimal
if errorlevel 1 exit /b 6
"%MSBUILD%" "%HERE%FlyExplorerWinUIShell.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 "/p:NuGetTargetMoniker=native%%2CVersion=v0.0" "/p:_NuGetTargetFallbackMoniker=" "/p:NuGetRuntimeIdentifier=" /m:2 /v:minimal
if errorlevel 1 exit /b 7
set "HELPER=%HERE%helper\bin\x64\%CONFIG%\FlyShellIsolationHelper.exe"
set "DEST=%HERE%x64\%CONFIG%\FlyExplorerWinUIShell"
if not exist "%HELPER%" exit /b 9
if not exist "%DEST%" exit /b 10
copy /y "%HELPER%" "%DEST%\FlyShellIsolationHelper.exe" >nul || exit /b 11
exit /b 0
