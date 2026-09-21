@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "version=2.0.4-dev"
set "sevenzip=%CD%\7zip\7za.exe"

if not exist "%sevenzip%" (
    echo ERROR: 7-Zip command line tool is missing: %sevenzip%
    popd
    exit /b 1
)

for %%F in (
    "fxfile_v%version%_x64_portable.zip"
    "fxfile_v%version%_x86_unicode_portable.zip"
    "fxfile_v%version%_x86_multibyte_portable.zip"
) do (
    if exist "%%~F" del /q "%%~F"
)

call :archive "bin\x64" "fxfile_v%version%_x64_portable.zip"
if errorlevel 1 goto :error

call :archive "bin\x86-unicode" "fxfile_v%version%_x86_unicode_portable.zip"
if errorlevel 1 goto :error

call :archive "bin\x86-multibyte" "fxfile_v%version%_x86_multibyte_portable.zip"
if errorlevel 1 goto :error

popd
exit /b 0

:archive
set "source=%~1"
set "output=%~2"
if not exist "%source%\fxfile.exe" (
    echo ERROR: Package source is incomplete: %source%
    exit /b 1
)
pushd "%source%" || exit /b 1
"%sevenzip%" a -tzip -mx=9 "..\..\%output%" *
set "result=%errorlevel%"
popd
if not "%result%"=="0" (
    echo ERROR: Failed to create %output%.
    exit /b %result%
)
exit /b 0

:error
set "result=%errorlevel%"
if "%result%"=="0" set "result=1"
popd
exit /b %result%
