@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "version=2.0.4-dev"
set "sevenzip=%CD%\7zip\7za.exe"


for %%F in (
    "fxfile_v%version%_x64_portable.zip"
    "fxfile_v%version%_x86_unicode_portable.zip"
    "fxfile_v%version%_x86_multibyte_portable.zip"
) do (
    if exist "%%~F" del /q "%%~F"
    if exist "%%~F" (
        echo ERROR: Could not remove stale portable output %%~F.
        goto :error
    )
)
if not exist "%sevenzip%" (
    echo ERROR: 7-Zip command line tool is missing: %sevenzip%
    goto :error
)

rem A portable archive must never ship without the help that the Help command opens.
rem Rebuild it for direct invocation as well as for package.bat (no stale CHM).
if defined PYTHON (
    "%PYTHON%" "..\build\rebuild_htmlhelp.py" --build
) else (
    python "..\build\rebuild_htmlhelp.py" --build
)
if errorlevel 1 (
    echo ERROR: Unable to create fresh portable help; refusing incomplete ZIPs.
    goto :error
)
if not exist "fxfile.chm" (
    echo ERROR: Missing freshly compiled portable help.
    goto :error
)


rem Keep portable documentation and file-list icon assets next to fxfile.exe.
for %%D in ("bin\x64" "bin\x86-unicode" "bin\x86-multibyte") do (
    call :stage_portable_assets "%%~D"
    if errorlevel 1 goto :error
)

call :archive "bin\x64" "fxfile_v%version%_x64_portable.zip"
if errorlevel 1 goto :error

call :archive "bin\x86-unicode" "fxfile_v%version%_x86_unicode_portable.zip"
if errorlevel 1 goto :error

call :archive "bin\x86-multibyte" "fxfile_v%version%_x86_multibyte_portable.zip"
if errorlevel 1 goto :error

popd
exit /b 0

:stage_portable_assets
set "source=%~1"
if not exist "%source%\fxfile.exe" (
    echo ERROR: Missing portable application before staging: %source%
    exit /b 1
)
for %%F in (
    "fxfile.chm"
    "custom_image_list_16.bmp"
    "custom_image_list_32.bmp"
    "license.txt"
    "readme.txt"
    "history.txt"
) do (
    if not exist "%%~F" (
        echo ERROR: Missing portable distribution asset: %%~F
        exit /b 1
    )
    copy /b /y "%%~F" "%source%\%%~nxF" >nul
    if errorlevel 1 (
        echo ERROR: Could not stage %%~F into %source%.
        exit /b 1
    )
)
if not exist "..\CREDITS" (
    echo ERROR: Third-party license notices are missing.
    exit /b 1
)
copy /b /y "..\CREDITS" "%source%\third_party_notices.txt" >nul
if errorlevel 1 (
    echo ERROR: Third-party notices could not be staged.
    exit /b 1
)
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
rem A partially created archive must never survive a failed run.
for %%F in (
    "fxfile_v%version%_x64_portable.zip"
    "fxfile_v%version%_x86_unicode_portable.zip"
    "fxfile_v%version%_x86_multibyte_portable.zip"
) do if exist "%%~F" del /q "%%~F"
if "%result%"=="0" set "result=1"
popd
exit /b %result%
