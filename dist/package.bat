@echo off
setlocal
pushd "%~dp0" || exit /b 1

rem Remove previously generated outputs before attempting release packaging.
for %%F in (
    "fxfile_v2.0.4-dev.exe"
    "fxfile_v2.0.4-dev_x64_portable.zip"
    "fxfile_v2.0.4-dev_x86_unicode_portable.zip"
    "fxfile_v2.0.4-dev_x86_multibyte_portable.zip"
) do (
    if exist "%%~F" del /q "%%~F"
    if exist "%%~F" goto :error
)

rem copy.bat checks required inputs and stages transactionally; do not
rem destroy the old generated bin tree before its checks have passed.
call copy.bat
if errorlevel 1 goto :error

rem Assemble installer before portable-specific documentation is staged into
rem each architecture's bin tree; avoids duplicate nested CHM/notices.
call make_installer.bat
if errorlevel 1 goto :error

call make_portable.bat
if errorlevel 1 goto :error

popd
exit /b 0

:error
set "result=%errorlevel%"
rem Delete generated outputs if any platform, archive or installer fails.
for %%F in (
    "fxfile_v2.0.4-dev.exe"
    "fxfile_v2.0.4-dev_x64_portable.zip"
    "fxfile_v2.0.4-dev_x86_unicode_portable.zip"
    "fxfile_v2.0.4-dev_x86_multibyte_portable.zip"
) do if exist "%%~F" del /q "%%~F"
if "%result%"=="0" set "result=1"
echo ERROR: Packaging failed with exit code %result%.
popd
exit /b %result%
