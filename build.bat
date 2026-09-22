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

if /I not "%msvs_version%"=="2026" (
    echo WARNING: The supported default build target is Visual Studio 2026.
    echo Requested msvs_version = %msvs_version%
)

set "PYTHON_EXE="
set "PYTHON_ARGS="
set "PYTHON_CANDIDATES=%TEMP%\flyexplorer-python-%RANDOM%-%RANDOM%.txt"

where python >"%PYTHON_CANDIDATES%" 2>nul
if errorlevel 1 goto python_try_launcher

for /f "usebackq delims=" %%P in ("%PYTHON_CANDIDATES%") do (
    "%%P" "build\check_python.py" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%%P"
        goto python_ready
    )
)

:python_try_launcher
where py >"%PYTHON_CANDIDATES%" 2>nul
if errorlevel 1 goto python_missing

for /f "usebackq delims=" %%P in ("%PYTHON_CANDIDATES%") do (
    "%%P" -3 "build\check_python.py" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%%P"
        set "PYTHON_ARGS=-3"
        goto python_ready
    )
)
goto python_missing

:python_missing
if exist "%PYTHON_CANDIDATES%" del /q "%PYTHON_CANDIDATES%" >nul 2>&1
echo ERROR: Python 3.9 or newer is required.
echo Install Python 3 and make either "python" or "py -3" available on PATH.
popd
exit /b 1

:python_ready
if exist "%PYTHON_CANDIDATES%" del /q "%PYTHON_CANDIDATES%" >nul 2>&1
echo Python command = "%PYTHON_EXE%" %PYTHON_ARGS%
"%PYTHON_EXE%" %PYTHON_ARGS% "build\check_python.py"
if errorlevel 1 (
    echo ERROR: Python was detected but failed the bootstrap check.
    popd
    exit /b 1
)

echo Running source invariant and regression preflight...
rem Includes ModernUI wiring, direct-CDialog migration, and known compiler regression guards.
"%PYTHON_EXE%" %PYTHON_ARGS% "build\validate_source_invariants.py"
if errorlevel 1 (
    echo ERROR: Source invariant/regression preflight failed.
    echo Fix the reported source dependency/integration issue before generating projects.
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

echo Removing stale Visual Studio project files...
if exist "fxfile.sln" del /q "fxfile.sln"
for %%F in (*.vcxproj *.vcxproj.filters *.vcxproj.user) do if exist "%%F" del /q "%%F" >nul 2>&1
for /r "%~dp0src" %%F in (*.vcxproj *.vcxproj.filters *.vcxproj.user) do del /q "%%F" >nul 2>&1

set "GYP_MSVS_VERSION=%msvs_version%"

echo msvs_version = %msvs_version%
echo target_arch = %target_arch%
echo gyp-next = %GYP_VERSION%
echo ----------

"%PYTHON_EXE%" %PYTHON_ARGS% "%GYP_DIR%\gyp_main.py" fxfile.gyp --depth=. -G msvs_version=%msvs_version% -D target_arch=%target_arch% -D msvs_version=%msvs_version%
if errorlevel 1 (
    echo ERROR: Failed to generate Visual Studio projects.
    popd
    exit /b 1
)

if not exist "fxfile.sln" (
    echo ERROR: fxfile.sln was not generated.
    popd
    exit /b 1
)

if not exist "fxfile.vcxproj" (
    echo ERROR: The root aggregate fxfile.vcxproj was not generated.
    popd
    exit /b 1
)

if /I "%target_arch%"=="x64" (
    findstr /c:"Release-x64-Unicode|x64" "fxfile.vcxproj" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Root fxfile.vcxproj is missing Release-x64-Unicode^|x64.
        echo The generated aggregate project is inconsistent with the x64 solution.
        popd
        exit /b 1
    )
)

echo Fixing mixed x64/x86 solution configuration mappings...
"%PYTHON_EXE%" %PYTHON_ARGS% "build\fix_solution_configs.py" "fxfile.sln"
if errorlevel 1 (
    echo ERROR: Failed to fix helper project configuration mappings.
    popd
    exit /b 1
)

if /I "%msvs_version%"=="2026" (
    findstr /s /m /c:"<PlatformToolset>v140</PlatformToolset>" src\*.vcxproj >nul 2>&1
    if not errorlevel 1 (
        echo ERROR: A generated project still targets the legacy v140 toolset.
        echo Delete generated project files and run build.bat again.
        popd
        exit /b 1
    )

    findstr /s /m /c:"<PlatformToolset>v145</PlatformToolset>" src\*.vcxproj >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Generated projects do not contain the Visual Studio 2026 v145 toolset.
        popd
        exit /b 1
    )
)

echo Preparing bundled runtime files and language resources...
call copy_lib.bat >nul
if errorlevel 1 (
    echo ERROR: Failed to prepare bundled runtime libraries.
    popd
    exit /b 1
)
call copy_languages.bat >nul
if errorlevel 1 (
    echo ERROR: Failed to prepare language resources.
    popd
    exit /b 1
)

echo ----------
echo Generated fxfile.sln for Visual Studio %msvs_version%.
if /I "%msvs_version%"=="2026" echo Verified platform toolset: v145
if /I "%target_arch%"=="x64" echo Win32 helpers are mapped to x86; updater is deferred to an x86-multibyte build.
echo For a 64-bit release build, use configuration Release-x64-Unicode.

popd
exit /b 0
