@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1

rem Python switches to the Windows ANSI code page when stdout is redirected.
rem Force UTF-8 so policy/readiness logs can contain Unicode punctuation safely.
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
chcp 65001 >nul

set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=x64"

set "LOG_DIR=%~dp0logs\local-ci"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

rem Keep one persistent log only. Temporary capture files are deleted on exit.
del /q "%LOG_DIR%\*.log" "%LOG_DIR%\*.tmp" >nul 2>&1
set "LOCAL_CI_LOG=%LOG_DIR%\local-ci.log"
set "STEP_LOG=%LOG_DIR%\step.tmp"
set "MSBUILD_RAW_LOG=%LOG_DIR%\msbuild-raw.tmp"

> "%LOCAL_CI_LOG%" echo ============================================================
>>"%LOCAL_CI_LOG%" echo flyExplorer Local CI
>>"%LOCAL_CI_LOG%" echo Profile: %PROFILE%
>>"%LOCAL_CI_LOG%" echo Started: %DATE% %TIME%
>>"%LOCAL_CI_LOG%" echo Repository: %~dp0
>>"%LOCAL_CI_LOG%" echo ============================================================

echo [local-ci] Log = "%LOCAL_CI_LOG%"

if /I "%PROFILE%"=="help" goto :usage
if /I "%PROFILE%"=="--help" goto :usage
if /I "%PROFILE%"=="/?" goto :usage
if /I "%PROFILE%"=="quick" goto :profile_quick
if /I "%PROFILE%"=="policy" goto :profile_policy
if /I "%PROFILE%"=="x64" goto :profile_x64
if /I "%PROFILE%"=="x86" goto :profile_x86
if /I "%PROFILE%"=="release" goto :profile_release
if /I "%PROFILE%"=="full" goto :profile_full

echo ERROR: Unknown local CI profile "%PROFILE%".
>>"%LOCAL_CI_LOG%" echo ERROR: Unknown local CI profile "%PROFILE%".
goto :usage_error

:profile_quick
call :find_python
if errorlevel 1 goto :failed
call :run_source_preflight
if errorlevel 1 goto :failed
goto :passed

:profile_policy
call :find_python
if errorlevel 1 goto :failed
call :run_policy_validation
if errorlevel 1 goto :failed
goto :passed

:profile_x64
call :locate_msbuild
if errorlevel 1 goto :failed
call :run_x64_release
if errorlevel 1 goto :failed
goto :passed

:profile_x86
call :locate_msbuild
if errorlevel 1 goto :failed
call :run_x86_release
if errorlevel 1 goto :failed
goto :passed

:profile_release
call :locate_msbuild
if errorlevel 1 goto :failed
call :run_x64_release
if errorlevel 1 goto :failed
call :run_x86_release
if errorlevel 1 goto :failed
call :run_package_validation
if errorlevel 1 goto :failed
goto :passed

:profile_full
call :find_python
if errorlevel 1 goto :failed
call :run_policy_validation
if errorlevel 1 goto :failed
call :locate_msbuild
if errorlevel 1 goto :failed
call :run_x64_release
if errorlevel 1 goto :failed
call :run_x64_debug
if errorlevel 1 goto :failed
call :run_x86_release
if errorlevel 1 goto :failed
call :run_package_validation
if errorlevel 1 goto :failed
goto :passed

:find_python
if defined PYTHON_EXE exit /b 0

where python >nul 2>&1
if not errorlevel 1 (
    python "build\check_python.py" >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%P in ('where python') do (
            set "PYTHON_EXE=%%P"
            set "PYTHON_ARGS="
            goto :python_found
        )
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "build\check_python.py" >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%P in ('where py') do (
            set "PYTHON_EXE=%%P"
            set "PYTHON_ARGS=-3"
            goto :python_found
        )
    )
)

echo ERROR: Python 3.9 or newer was not found.
>>"%LOCAL_CI_LOG%" echo ERROR: Python 3.9 or newer was not found.
exit /b 1

:python_found
echo [local-ci] Python = "%PYTHON_EXE%" %PYTHON_ARGS%
>>"%LOCAL_CI_LOG%" echo Python = "%PYTHON_EXE%" %PYTHON_ARGS%
exit /b 0

:locate_msbuild
if defined MSBUILD_EXE exit /b 0

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo ERROR: vswhere.exe was not found at "%VSWHERE%".
    echo Install Visual Studio 2026 with Desktop development with C++ and MFC.
    >>"%LOCAL_CI_LOG%" echo ERROR: vswhere.exe was not found at "%VSWHERE%".
    exit /b 1
)

set "VS_INSTALL="
for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do set "VS_INSTALL=%%I"

if not defined VS_INSTALL (
    echo ERROR: Visual Studio installation with MSBuild was not found.
    >>"%LOCAL_CI_LOG%" echo ERROR: Visual Studio installation with MSBuild was not found.
    exit /b 1
)

set "MSBUILD_EXE=%VS_INSTALL%\MSBuild\Current\Bin\MSBuild.exe"
if not exist "%MSBUILD_EXE%" (
    echo ERROR: MSBuild.exe was not found at "%MSBUILD_EXE%".
    >>"%LOCAL_CI_LOG%" echo ERROR: MSBuild.exe was not found at "%MSBUILD_EXE%".
    exit /b 1
)

echo [local-ci] MSBuild = "%MSBUILD_EXE%"
>>"%LOCAL_CI_LOG%" echo MSBuild = "%MSBUILD_EXE%"
exit /b 0

:append_file
set "LOG_TITLE=%~1"
set "LOG_FILE=%~2"
echo.
echo ==== %LOG_TITLE% ====
>>"%LOCAL_CI_LOG%" echo.
>>"%LOCAL_CI_LOG%" echo ==== %LOG_TITLE% ====
if exist "%LOG_FILE%" (
    type "%LOG_FILE%"
    type "%LOG_FILE%" >>"%LOCAL_CI_LOG%"
) else (
    echo [local-ci] No captured output.
    >>"%LOCAL_CI_LOG%" echo [local-ci] No captured output.
)
exit /b 0

:run_source_preflight
"%PYTHON_EXE%" %PYTHON_ARGS% "build\validate_source_invariants.py" >"%STEP_LOG%" 2>&1
set "SOURCE_RESULT=%errorlevel%"
call :append_file "Source invariant preflight" "%STEP_LOG%"
exit /b %SOURCE_RESULT%

:run_policy_validation
set "POLICY_VENV=%TEMP%\flyExplorer-policy-venv"

if not exist "%POLICY_VENV%\Scripts\python.exe" (
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%POLICY_VENV%" >"%STEP_LOG%" 2>&1
    set "POLICY_RESULT=%errorlevel%"
    call :append_file "Create policy virtual environment" "%STEP_LOG%"
    if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%
)

"%POLICY_VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --require-hashes --requirement ".agent-policy\requirements.lock" >"%STEP_LOG%" 2>&1
set "POLICY_RESULT=%errorlevel%"
call :append_file "Policy dependencies" "%STEP_LOG%"
if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%

"%POLICY_VENV%\Scripts\python.exe" ".agent-policy\scripts\validate.py" >"%STEP_LOG%" 2>&1
set "POLICY_RESULT=%errorlevel%"
call :append_file "Policy bundle validation" "%STEP_LOG%"
if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%

"%POLICY_VENV%\Scripts\python.exe" ".agent-policy\scripts\validate.py" --project-root . --readiness development >"%STEP_LOG%" 2>&1
set "POLICY_RESULT=%errorlevel%"
call :append_file "Development readiness" "%STEP_LOG%"
if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%

pushd ".agent-policy"
rem The invalid-distribution corpus intentionally creates a duplicate ZIP entry.
rem Suppress only zipfile's expected duplicate-name UserWarning; test semantics remain unchanged.
"%POLICY_VENV%\Scripts\python.exe" -W "ignore:Duplicate name:UserWarning:zipfile" "scripts\conformance.py" >"%STEP_LOG%" 2>&1
set "POLICY_RESULT=%errorlevel%"
popd
call :append_file "Policy conformance" "%STEP_LOG%"
if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%

call :run_source_preflight
exit /b %errorlevel%

:run_x64_release
call "build.bat" 2026 x64 >"%STEP_LOG%" 2>&1
set "BOOTSTRAP_RESULT=%errorlevel%"
call :append_file "Generate Visual Studio 2026 x64 solution" "%STEP_LOG%"
if not "%BOOTSTRAP_RESULT%"=="0" exit /b %BOOTSTRAP_RESULT%

call :build_configuration "Release-x64-Unicode" "x64" "Release x64"
if errorlevel 1 exit /b 1

call :require_file "bin\x64\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\libxprw.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-crash.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-launcher.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-keyhook.dll"
if errorlevel 1 exit /b 1

call :run_runtime_smoke "bin\x64" "Release-x64-Unicode" "Release x64 runtime smoke"
exit /b %errorlevel%

:run_x64_debug
call :build_configuration "Debug-x64-Unicode" "x64" "Debug x64"
if errorlevel 1 exit /b 1

call :require_file "bin\x64\fxfile_dbg.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\libxprw_dbg.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-crash_dbg.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-launcher_dbg.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\fxfile-keyhook_dbg.dll"
exit /b %errorlevel%

:run_x86_release
call "build.bat" 2026 x86 >"%STEP_LOG%" 2>&1
set "BOOTSTRAP_RESULT=%errorlevel%"
call :append_file "Generate Visual Studio 2026 x86 solution" "%STEP_LOG%"
if not "%BOOTSTRAP_RESULT%"=="0" exit /b %BOOTSTRAP_RESULT%

call :build_configuration "Release-x86-Unicode" "Win32" "Release x86 Unicode"
if errorlevel 1 exit /b 1

call :require_file "bin\x86-unicode\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\libxprw.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\fxfile-crash.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\fxfile-launcher.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\fxfile-keyhook.dll"
if errorlevel 1 exit /b 1

call :run_runtime_smoke "bin\x86-unicode" "Release-x86-Unicode" "Release x86 Unicode runtime smoke"
if errorlevel 1 exit /b 1

call :build_configuration "Release-x86-Multibyte" "Win32" "Release x86 Multibyte"
if errorlevel 1 exit /b 1

call :require_file "bin\x86-multibyte\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\libxpr.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\fxfile-crash.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\fxfile-launcher.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\fxfile-keyhook.dll"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\upchecker\fxfile-upchecker.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\upchecker\fxfile-upchecker.exe"
if errorlevel 1 exit /b 1

call :run_runtime_smoke "bin\x86-multibyte" "Release-x86-Multibyte" "Release x86 Multibyte runtime smoke"
exit /b %errorlevel%

:run_package_validation
call :require_file "bin\x64\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\upchecker\fxfile-upchecker.exe"
if errorlevel 1 exit /b 1

call "dist\package.bat" >"%STEP_LOG%" 2>&1
set "PACKAGE_RESULT=%errorlevel%"
call :append_file "Build release packages" "%STEP_LOG%"
if not "%PACKAGE_RESULT%"=="0" exit /b %PACKAGE_RESULT%

powershell -NoProfile -ExecutionPolicy Bypass -File "build\validate_package.ps1" -DistDir "dist" >"%STEP_LOG%" 2>&1
set "PACKAGE_RESULT=%errorlevel%"
call :append_file "Validate release packages" "%STEP_LOG%"
exit /b %PACKAGE_RESULT%

:run_runtime_smoke
set "SMOKE_SOURCE=%~1"
set "SMOKE_CONFIGURATION=%~2"
set "SMOKE_TITLE=%~3"

powershell -NoProfile -ExecutionPolicy Bypass -File "build\runtime_smoke.ps1" -SourceDir "%SMOKE_SOURCE%" -Configuration "%SMOKE_CONFIGURATION%" -SkipIfUserStateExists >"%STEP_LOG%" 2>&1
set "SMOKE_RESULT=%errorlevel%"
call :append_file "%SMOKE_TITLE%" "%STEP_LOG%"

if "%SMOKE_RESULT%"=="3" (
    echo [local-ci] Runtime smoke SKIPPED: %SMOKE_CONFIGURATION%
    >>"%LOCAL_CI_LOG%" echo [local-ci] Runtime smoke SKIPPED: %SMOKE_CONFIGURATION% due to existing user state.
    set "LOCAL_CI_SKIPPED=1"
    exit /b 0
)

exit /b %SMOKE_RESULT%

:build_configuration
set "CI_CONFIGURATION=%~1"
set "CI_PLATFORM=%~2"
set "CI_TITLE=%~3"

del /q "%STEP_LOG%" "%MSBUILD_RAW_LOG%" >nul 2>&1
echo.
echo [local-ci] Rebuilding %CI_CONFIGURATION% ^| %CI_PLATFORM%...
>>"%LOCAL_CI_LOG%" echo.
>>"%LOCAL_CI_LOG%" echo [local-ci] Rebuilding %CI_CONFIGURATION% ^| %CI_PLATFORM%...

rem Rebuild is intentional: local CI must not reuse stale object files from a
rem previous CRT/configuration state. The normal file logger also records every
rem source file actually compiled.
"%MSBUILD_EXE%" "fxfile.sln" /m /nologo /verbosity:quiet /t:Rebuild /fl "/flp:logfile=%MSBUILD_RAW_LOG%;verbosity=normal" "/p:Configuration=%CI_CONFIGURATION%" "/p:Platform=%CI_PLATFORM%" >nul 2>&1
set "BUILD_RESULT=%errorlevel%"

rem MSBuild's file logger uses the Windows ANSI code page on localized systems.
rem Convert it to BOM-less UTF-8 before displaying/appending to the unified log.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$r = New-Object System.IO.StreamReader($env:MSBUILD_RAW_LOG, [System.Text.Encoding]::Default, $true); try { $text = $r.ReadToEnd() } finally { $r.Dispose() }; $utf8 = New-Object System.Text.UTF8Encoding($false); [System.IO.File]::WriteAllText($env:STEP_LOG, $text, $utf8)"
if errorlevel 1 (
    echo ERROR: Failed to convert MSBuild log to UTF-8.
    >>"%LOCAL_CI_LOG%" echo ERROR: Failed to convert MSBuild log to UTF-8.
    exit /b 1
)

call :append_file "%CI_TITLE% rebuild" "%STEP_LOG%"
if not "%BUILD_RESULT%"=="0" exit /b %BUILD_RESULT%

rem Scan the UTF-8 normalized log. The full warning line is already visible
rem above, so do not duplicate it through another code-page conversion path.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$text = [System.IO.File]::ReadAllText($env:STEP_LOG, [System.Text.Encoding]::UTF8); if ([regex]::IsMatch($text, '\bwarning (?:C\d+|LNK\d+|MSB\d+):')) { exit 1 }; exit 0"
set "WARNING_RESULT=%errorlevel%"
if not "%WARNING_RESULT%"=="0" (
    echo ERROR: Unexpected compiler/linker/MSBuild warning detected in %CI_CONFIGURATION%.
    >>"%LOCAL_CI_LOG%" echo ERROR: Unexpected compiler/linker/MSBuild warning detected in %CI_CONFIGURATION%.
    exit /b %WARNING_RESULT%
)

echo [local-ci] Warning check PASS: %CI_CONFIGURATION%
>>"%LOCAL_CI_LOG%" echo [local-ci] Warning check PASS: %CI_CONFIGURATION%
exit /b 0

:require_file
if not exist "%~1" (
    echo ERROR: Required local CI artifact is missing: %~1
    >>"%LOCAL_CI_LOG%" echo ERROR: Required local CI artifact is missing: %~1
    exit /b 1
)
echo [local-ci] Verified: %~1
>>"%LOCAL_CI_LOG%" echo [local-ci] Verified: %~1
exit /b 0

:passed
echo.
echo ============================================================
if defined LOCAL_CI_SKIPPED (
    echo Local CI PASS WITH SKIPS: %PROFILE%
    echo Runtime smoke checks marked SKIPPED are NOT TESTED.
    >>"%LOCAL_CI_LOG%" echo.
    >>"%LOCAL_CI_LOG%" echo Result: PASS_WITH_SKIPS
) else (
    echo Local CI PASS: %PROFILE%
    >>"%LOCAL_CI_LOG%" echo.
    >>"%LOCAL_CI_LOG%" echo Result: PASS
)
echo Log: "%LOCAL_CI_LOG%"
echo ============================================================
>>"%LOCAL_CI_LOG%" echo Finished: %DATE% %TIME%
del /q "%STEP_LOG%" "%MSBUILD_RAW_LOG%" >nul 2>&1
popd
exit /b 0

:failed
set "RESULT=%errorlevel%"
if "%RESULT%"=="0" set "RESULT=1"
echo.
echo ============================================================
echo Local CI FAIL: %PROFILE% ^(exit %RESULT%^)
echo Log: "%LOCAL_CI_LOG%"
echo ============================================================
>>"%LOCAL_CI_LOG%" echo.
>>"%LOCAL_CI_LOG%" echo Result: FAIL ^(exit %RESULT%^)
>>"%LOCAL_CI_LOG%" echo Finished: %DATE% %TIME%
del /q "%STEP_LOG%" "%MSBUILD_RAW_LOG%" >nul 2>&1
popd
exit /b %RESULT%

:usage
echo Usage: local_ci.bat [quick^|policy^|x64^|x86^|release^|full]
echo.
echo   quick    Source invariant preflight only.
echo   policy   Full vendored policy/readiness/conformance validation.
echo   x64      Default. Release x64 build, warning check, artifacts, launch smoke.
echo   x86      x86 Unicode + Multibyte builds, warning checks, artifacts, smokes.
echo   release  x64 + x86 + package build/payload validation.
echo   full     policy + x64 Release/Debug + x86 + package validation.
echo.
echo See LOCAL_CI_MANUAL.txt for the short usage guide.
del /q "%STEP_LOG%" "%MSBUILD_RAW_LOG%" >nul 2>&1
popd
exit /b 0

:usage_error
echo Usage: local_ci.bat [quick^|policy^|x64^|x86^|release^|full]
del /q "%STEP_LOG%" "%MSBUILD_RAW_LOG%" >nul 2>&1
popd
exit /b 2
