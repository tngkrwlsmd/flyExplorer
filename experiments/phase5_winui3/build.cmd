@echo off
setlocal
rem Preserve reproducible, tracked project templates: root repository ignores generated vcxproj files.
if not exist "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" copy /y "%~dp0FlyExplorerWinUI3NavPoC.project-template.xml" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" >nul || exit /b 6
if not exist "%~dp0FlyExplorerWinUI3NavPoC.vcxproj.filters" copy /y "%~dp0FlyExplorerWinUI3NavPoC.filters-template.xml" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj.filters" >nul || exit /b 7
set "ROOT=%~dp0..\..\"
set "VS=C:\Program Files\Microsoft Visual Studio\18\Community"
if not exist "%VS%\MSBuild\Current\Bin\MSBuild.exe" exit /b 3
if not exist "%ROOT%\logs\phase5" mkdir "%ROOT%\logs\phase5"
set "NUGET_PACKAGES=%ROOT%\logs\phase5\nuget-packages"
set "NUGET_HTTP_CACHE_PATH=%ROOT%\logs\phase5\nuget-http"
set "NUGET_PLUGINS_CACHE_PATH=%ROOT%\logs\phase5\nuget-plugin"
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" /nologo /t:Restore /p:Configuration=Debug /p:Platform=x64 "/p:RestoreConfigFile=%~dp0NuGet.Config" "/p:RestorePackagesPath=%NUGET_PACKAGES%" /v:minimal
if errorlevel 1 exit /b 4
rem VS18 VC++ selects a UAP fallback target that is absent from the native PackageReference asset graph.
rem Resolve the actual native v0.0 graph explicitly and suppress the mismatched fallback and .NET-style runtime ID.
rem Double percent is required inside CMD to pass MSBuild the NuGet escaped comma (%2C) in the moniker.
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%~dp0FlyExplorerWinUI3NavPoC.vcxproj" /nologo /t:Build /p:Configuration=Debug /p:Platform=x64 "/p:NuGetTargetMoniker=native%%2CVersion=v0.0" "/p:_NuGetTargetFallbackMoniker=" "/p:NuGetRuntimeIdentifier=" /m:2 /v:minimal
if errorlevel 1 exit /b 5
