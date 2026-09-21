@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "makensis=%CD%\nsis\makensis.exe"
set "output=fxfile_v2.0.4-dev.exe"

if not exist "%makensis%" (
    echo ERROR: Vendored NSIS compiler is missing: %makensis%
    popd
    exit /b 1
)

if exist "%output%" del /q "%output%"

"%makensis%" /V2 "setup.nsi"
set "result=%errorlevel%"
if not "%result%"=="0" (
    echo ERROR: makensis failed with exit code %result%.
    popd
    exit /b %result%
)

if not exist "%output%" (
    echo ERROR: NSIS completed without creating %output%.
    popd
    exit /b 1
)

popd
exit /b 0
