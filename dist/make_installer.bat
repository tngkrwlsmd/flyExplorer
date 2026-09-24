@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "makensis=%CD%\nsis\makensis.exe"
set "output=fxfile_v2.0.4-dev.exe"

rem Fail closed: a failed build must never leave an older installer to publish.
if exist "%output%" del /q "%output%"

rem Every invocation (including direct make_installer.bat) requires fresh help.
rem PYTHON, when set, must point to the Python 3 executable path.
if defined PYTHON (
    "%PYTHON%" "..\build\rebuild_htmlhelp.py" --build
) else (
    python "..\build\rebuild_htmlhelp.py" --build
)
if errorlevel 1 (
    echo ERROR: Fresh fxfile.chm regeneration failed; refusing stale installer.
    popd
    exit /b 1
)
if not exist "fxfile.chm" (
    echo ERROR: HTML Help compiler did not create fxfile.chm.
    popd
    exit /b 1
)

if not exist "%makensis%" (
    echo ERROR: Vendored NSIS compiler is missing: %makensis%
    popd
    exit /b 1
)

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
