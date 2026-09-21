@echo off
setlocal
pushd "%~dp0" || exit /b 1

call cleanup.bat
if errorlevel 1 goto :error

call copy.bat
if errorlevel 1 goto :error

call make_portable.bat
if errorlevel 1 goto :error

call make_installer.bat
if errorlevel 1 goto :error

popd
exit /b 0

:error
set "result=%errorlevel%"
if "%result%"=="0" set "result=1"
echo ERROR: Packaging failed with exit code %result%.
popd
exit /b %result%
