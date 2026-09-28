@echo off
setlocal
set "HERE=%~dp0"
set "ROOT=%~dp0..\..\"
set "VS=C:\Program Files\Microsoft Visual Studio\18\Community"
if not exist "%VS%\MSBuild\Current\Bin\MSBuild.exe" exit /b 3
if not exist "%HERE%FlyExplorerIslandBridge.vcxproj" copy /y "%HERE%FlyExplorerIslandBridge.project-template.xml" "%HERE%FlyExplorerIslandBridge.vcxproj" >nul || exit /b 6
if not exist "%ROOT%logs\phase5" mkdir "%ROOT%logs\phase5"
set "NUGET_PACKAGES=%ROOT%logs\phase5\nuget-packages"
set "NUGET_HTTP_CACHE_PATH=%ROOT%logs\phase5\nuget-http"
set "NUGET_PLUGINS_CACHE_PATH=%ROOT%logs\phase5\nuget-plugin"
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%HERE%FlyExplorerIslandBridge.vcxproj" /nologo /t:Restore /p:Configuration=Debug /p:Platform=x64 /p:WindowsAppContainer=false "/p:RestoreConfigFile=%HERE%NuGet.Config" "/p:RestorePackagesPath=%NUGET_PACKAGES%" /v:minimal
if errorlevel 1 exit /b 4
"%VS%\MSBuild\Current\Bin\MSBuild.exe" "%HERE%FlyExplorerIslandBridge.vcxproj" /nologo /t:Build /p:Configuration=Debug /p:Platform=x64 /p:WindowsAppContainer=false "/p:NuGetTargetMoniker=native%%2CVersion=v0.0" "/p:_NuGetTargetFallbackMoniker=" "/p:NuGetRuntimeIdentifier=" /p:WindowsAppContainer=false /m:2 /v:minimal
if errorlevel 1 exit /b 5
