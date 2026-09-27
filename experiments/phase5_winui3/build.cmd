@echo off
setlocal
set "ROOT=%~dp0..\..\"
set "VS=C:\Program Files\Microsoft Visual Studio\18\Community"
if not exist "%VS%\MSBuild\Current\Bin\MSBuild.exe" exit /b 3
if not exist "%ROOT%\logs\phase5" mkdir "%ROOT%\logs\phase5"
set "NUGET_PACKAGES=%ROOT%\logs\phase5\nuget-packages"
set "NUGET_HTTP_CACHE_PATH=%ROOT%\logs\phase5\nuget-http"
set "NUGET_PLUGINS_CACHE_PATH=%ROOT%\logs\phase5\nuget-plugin"
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" /nologo /t:Restore /p:Configuration=Debug /p:Platform=x64 "/p:RestoreConfigFile=%~dp0NuGet.Config" "/p:RestorePackagesPath=%NUGET_PACKAGES%" /v:minimal
if errorlevel 1 exit /b 4
rem Experimental temporary workaround ONLY for VS18 native/UAP NuGet asset selection.
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" /nologo /t:Build /p:Configuration=Debug /p:Platform=x64 /p:ResolveNuGetPackages=false /m:2 /v:minimal
if errorlevel 1 exit /b 5
