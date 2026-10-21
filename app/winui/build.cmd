@echo off
setlocal EnableExtensions
rem Canonical flyExplorer WinUI 3 product build.
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Debug"
if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" exit /b 2
set "HERE=%~dp0"
set "ROOT=%HERE%..\..\"
set "MSBUILD="
for /f "usebackq delims=" %%I in (`python -X utf8 "%ROOT%tools\winui\resolve_msbuild.py" --winui`) do set "MSBUILD=%%I"
if not defined MSBUILD exit /b 3
if not exist "%MSBUILD%" exit /b 3
rem Build the matching isolated Shell helper, then stage it beside the app.
call "%HERE%helper\build.cmd" "%CONFIG%"
if errorlevel 1 exit /b 8
rem Canonical tracked templates own the generated project after any source edit.
copy /y "%HERE%flyExplorer.project-template.xml" "%HERE%flyExplorer.vcxproj" >nul || exit /b 4
copy /y "%HERE%flyExplorer.filters-template.xml" "%HERE%flyExplorer.vcxproj.filters" >nul || exit /b 5
set "OUT=%ROOT%out"
set "APP_OUT=%OUT%\winui\%CONFIG%"
set "APP_OBJ=%OUT%\obj\winui\%CONFIG%"
set "CACHE=%ROOT%.cache\nuget"
if not exist "%APP_OUT%" mkdir "%APP_OUT%"
if not exist "%APP_OBJ%" mkdir "%APP_OBJ%"
if not exist "%CACHE%" mkdir "%CACHE%"
rem Generated binaries/intermediates/cache live outside app/winui source.
set "NUGET_PACKAGES=%CACHE%\packages"
set "NUGET_HTTP_CACHE_PATH=%CACHE%\http"
set "NUGET_PLUGINS_CACHE_PATH=%CACHE%\plugins"
"%MSBUILD%" "%HERE%flyExplorer.vcxproj" /nologo /t:Restore "/p:Configuration=%CONFIG%" /p:Platform=x64 "/p:BaseIntermediateOutputPath=%APP_OBJ%/" "/p:RestoreConfigFile=%HERE%NuGet.Config" "/p:RestorePackagesPath=%NUGET_PACKAGES%" /v:minimal
if errorlevel 1 exit /b 6
python -X utf8 "%ROOT%tools\winui\verify_restore.py" "%APP_OBJ%\project.assets.json" "%NUGET_PACKAGES%"
if errorlevel 1 exit /b 15
"%MSBUILD%" "%HERE%flyExplorer.vcxproj" /nologo /t:Build "/p:Configuration=%CONFIG%" /p:Platform=x64 "/p:BaseIntermediateOutputPath=%APP_OBJ%/" "/p:OutDir=%APP_OUT%/" "/p:IntDir=%APP_OBJ%/" "/p:GeneratedFilesDir=%APP_OBJ%/Generated Files/" "/p:NuGetTargetMoniker=native%%2CVersion=v0.0" "/p:_NuGetTargetFallbackMoniker=" "/p:NuGetRuntimeIdentifier=" /m:2 /v:minimal
if errorlevel 1 exit /b 7
set "HELPER=%OUT%\helper\%CONFIG%\FlyShellIsolationHelper.exe"
set "DEST=%APP_OUT%"
if not exist "%HELPER%" exit /b 9
if not exist "%DEST%" exit /b 10
copy /y "%HELPER%" "%DEST%\FlyShellIsolationHelper.exe" >nul || exit /b 11
if /I "%CONFIG%"=="Release" (
  if not exist "%OUT%\symbols\winui\Release" mkdir "%OUT%\symbols\winui\Release"
  if exist "%DEST%\flyExplorer.pdb" move /y "%DEST%\flyExplorer.pdb" "%OUT%\symbols\winui\Release\flyExplorer.pdb" >nul || exit /b 12
  if exist "%DEST%\flyExplorer.lib" del /q "%DEST%\flyExplorer.lib" || exit /b 13
  if exist "%DEST%\flyExplorer.exp" del /q "%DEST%\flyExplorer.exp" || exit /b 14
)
exit /b 0
