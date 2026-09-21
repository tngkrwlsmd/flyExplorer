::
:: Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
::
:: Modernized build bootstrap for Visual Studio 2026.
::
@echo off
setlocal EnableExtensions
pushd "%~dp0"

set "GYP_VERSION=v0.22.2"
set "GYP_DIR=%~dp0tools\gyp-next"
set "msvs_version=2026"
set "target_arch=x64"

if not "%~1"=="" set "msvs_version=%~1"
if not "%~2"=="" set "target_arch=%~2"

if /I not "%target_arch%"=="x64" if /I not "%target_arch%"=="x86" (
    echo ERROR: target_arch must be x64 or x86.
    popd
    exit /b 1
)

set "PYTHON_CMD="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo ERROR: Python 3.9 or newer is required.
    echo Install Python 3 and make either "py -3" or "python" available on PATH.
    popd
    exit /b 1
)

if not exist "%GYP_DIR%\gyp_main.py" (
    where git >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Git is required to download gyp-next.
        popd
        exit /b 1
    )

    if not exist "%~dp0tools" mkdir "%~dp0tools"

    echo Installing gyp-next %GYP_VERSION%...
    git clone --depth 1 --branch %GYP_VERSION% https://github.com/nodejs/gyp-next.git "%GYP_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to clone gyp-next.
        popd
        exit /b 1
    )
)

findstr /C:"\"2026\"" "%GYP_DIR%\pylib\gyp\MSVSVersion.py" >nul 2>&1
if errorlevel 1 (
    echo ERROR: The installed gyp-next does not support Visual Studio 2026.
    echo Delete tools\gyp-next and run build.bat again.
    popd
    exit /b 1
)

set "GYP_MSVS_VERSION=%msvs_version%"

echo msvs_version = %msvs_version%
echo target_arch = %target_arch%
echo gyp-next = %GYP_VERSION%
echo ----------

%PYTHON_CMD% "%GYP_DIR%\gyp_main.py" fxfile.gyp --depth=. -G msvs_version=%msvs_version% -D target_arch=%target_arch% -D msvs_version=%msvs_version%
if errorlevel 1 (
    echo ERROR: Failed to generate Visual Studio projects.
    popd
    exit /b 1
)

echo ----------
echo Generated fxfile.sln for Visual Studio %msvs_version%.
echo For a 64-bit release build, use configuration Release-x64-Unicode.

popd
exit /b 0
