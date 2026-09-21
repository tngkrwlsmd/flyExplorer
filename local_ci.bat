@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1

set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=x64"
set "LOG_DIR=%TEMP%\flyExplorer-local-ci"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

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
exit /b 1

:python_found
echo [local-ci] Python = "%PYTHON_EXE%" %PYTHON_ARGS%
exit /b 0

:locate_msbuild
if defined MSBUILD_EXE exit /b 0

set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    echo ERROR: vswhere.exe was not found at "%VSWHERE%".
    echo Install Visual Studio 2026 with Desktop development with C++ and MFC.
    exit /b 1
)

set "VS_INSTALL="
for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath`) do set "VS_INSTALL=%%I"

if not defined VS_INSTALL (
    echo ERROR: Visual Studio installation with MSBuild was not found.
    exit /b 1
)

set "MSBUILD_EXE=%VS_INSTALL%\MSBuild\Current\Bin\MSBuild.exe"
if not exist "%MSBUILD_EXE%" (
    echo ERROR: MSBuild.exe was not found at "%MSBUILD_EXE%".
    exit /b 1
)

echo [local-ci] MSBuild = "%MSBUILD_EXE%"
exit /b 0

:run_source_preflight
echo.
echo ==== Source invariant preflight ====
"%PYTHON_EXE%" %PYTHON_ARGS% "build\validate_source_invariants.py"
exit /b %errorlevel%

:run_policy_validation
echo.
echo ==== Full local policy validation ====
set "POLICY_VENV=%TEMP%\flyExplorer-policy-venv"

if not exist "%POLICY_VENV%\Scripts\python.exe" (
    echo [local-ci] Creating reusable policy venv at "%POLICY_VENV%"...
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%POLICY_VENV%"
    if errorlevel 1 exit /b 1
)

"%POLICY_VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --require-hashes --requirement ".agent-policy\requirements.lock"
if errorlevel 1 exit /b 1

"%POLICY_VENV%\Scripts\python.exe" ".agent-policy\scripts\validate.py"
if errorlevel 1 exit /b 1

"%POLICY_VENV%\Scripts\python.exe" ".agent-policy\scripts\validate.py" --project-root . --readiness development
if errorlevel 1 exit /b 1

pushd ".agent-policy"
"%POLICY_VENV%\Scripts\python.exe" "scripts\conformance.py"
set "POLICY_RESULT=%errorlevel%"
popd
if not "%POLICY_RESULT%"=="0" exit /b %POLICY_RESULT%

call :run_source_preflight
exit /b %errorlevel%

:run_x64_release
echo.
echo ==== Release x64 local CI ====
call "build.bat" 2026 x64
if errorlevel 1 exit /b 1

call :build_configuration "Release-x64-Unicode" "x64" "release-x64"
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

powershell -NoProfile -ExecutionPolicy Bypass -File "build\runtime_smoke.ps1" -SourceDir "bin\x64" -Configuration "Release-x64-Unicode"
exit /b %errorlevel%

:run_x64_debug
echo.
echo ==== Debug x64 regression ====
call :build_configuration "Debug-x64-Unicode" "x64" "debug-x64"
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
echo.
echo ==== x86 compatibility local CI ====
call "build.bat" 2026 x86
if errorlevel 1 exit /b 1

call :build_configuration "Release-x86-Unicode" "Win32" "release-x86-unicode"
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

powershell -NoProfile -ExecutionPolicy Bypass -File "build\runtime_smoke.ps1" -SourceDir "bin\x86-unicode" -Configuration "Release-x86-Unicode"
if errorlevel 1 exit /b 1

call :build_configuration "Release-x86-Multibyte" "Win32" "release-x86-multibyte"
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

powershell -NoProfile -ExecutionPolicy Bypass -File "build\runtime_smoke.ps1" -SourceDir "bin\x86-multibyte" -Configuration "Release-x86-Multibyte"
exit /b %errorlevel%

:run_package_validation
echo.
echo ==== Release package validation ====
call :require_file "bin\x64\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-unicode\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x86-multibyte\fxfile.exe"
if errorlevel 1 exit /b 1
call :require_file "bin\x64\upchecker\fxfile-upchecker.exe"
if errorlevel 1 exit /b 1

call "dist\package.bat"
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -File "build\validate_package.ps1" -DistDir "dist"
exit /b %errorlevel%

:build_configuration
set "CI_CONFIGURATION=%~1"
set "CI_PLATFORM=%~2"
set "CI_TAG=%~3"
set "FXFILE_CI_LOG=%LOG_DIR%\%CI_TAG%.log"

echo.
echo [local-ci] Building %CI_CONFIGURATION% ^| %CI_PLATFORM%
echo [local-ci] Log: "%FXFILE_CI_LOG%"

"%MSBUILD_EXE%" "fxfile.sln" /m /nologo /verbosity:minimal /fl "/flp:logfile=%FXFILE_CI_LOG%;verbosity=normal" "/p:Configuration=%CI_CONFIGURATION%" "/p:Platform=%CI_PLATFORM%"
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$warnings = @(Select-String -LiteralPath $env:FXFILE_CI_LOG -Pattern '\bwarning (?:C\d+|LNK\d+|MSB\d+):'); if ($warnings.Count -gt 0) { Write-Host 'Unexpected compiler/linker/MSBuild warnings:'; foreach ($w in $warnings) { Write-Host $w.Line }; exit 1 }"
if errorlevel 1 exit /b 1

echo [local-ci] Warning check PASS: %CI_CONFIGURATION%
exit /b 0

:require_file
if not exist "%~1" (
    echo ERROR: Required local CI artifact is missing: %~1
    exit /b 1
)
echo [local-ci] Verified: %~1
exit /b 0

:passed
echo.
echo ============================================================
echo Local CI PASS: %PROFILE%
echo ============================================================
popd
exit /b 0

:failed
set "RESULT=%errorlevel%"
if "%RESULT%"=="0" set "RESULT=1"
echo.
echo ============================================================
echo Local CI FAIL: %PROFILE% ^(exit %RESULT%^)
echo Logs: "%LOG_DIR%"
echo ============================================================
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
popd
exit /b 0

:usage_error
echo Usage: local_ci.bat [quick^|policy^|x64^|x86^|release^|full]
popd
exit /b 2
