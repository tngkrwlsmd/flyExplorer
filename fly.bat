@echo off
setlocal EnableExtensions DisableDelayedExpansion
rem User-facing developer dispatcher. Internal build/test implementations stay separate.
set "ROOT=%~dp0"
set "ACTION=%~1"
if "%ACTION%"=="" goto :help
if /I "%ACTION%"=="help" goto :help
if /I "%ACTION%"=="-h" goto :help
if /I "%ACTION%"=="--help" goto :help
if /I "%ACTION%"=="build" goto :build
if /I "%ACTION%"=="run" goto :run
if /I "%ACTION%"=="check" goto :check
if /I "%ACTION%"=="test" goto :test
if /I "%ACTION%"=="package" goto :package
if /I "%ACTION%"=="clean" goto :clean
echo [fly] Unknown command: %ACTION%
goto :usage_error

:build
if not "%~3"=="" goto :usage_error
call "%ROOT%build.bat" "%~2"
exit /b %ERRORLEVEL%

:run
if not "%~4"=="" goto :usage_error
if "%~2"=="" (
  if not "%~3"=="" goto :usage_error
  call "%ROOT%run.bat" Release
  exit /b %ERRORLEVEL%
)
if /I "%~2"=="Debug" goto :run_config
if /I "%~2"=="Release" goto :run_config
if not "%~3"=="" goto :usage_error
call "%ROOT%run.bat" Release "%~2"
exit /b %ERRORLEVEL%

:run_config
call "%ROOT%run.bat" "%~2" "%~3"
exit /b %ERRORLEVEL%

:check
if not "%~2"=="" goto :usage_error
call "%ROOT%test.bat" source
exit /b %ERRORLEVEL%

:test
if not "%~4"=="" goto :usage_error
if "%~2"=="" (
  if not "%~3"=="" goto :usage_error
  call "%ROOT%test.bat" source
  exit /b %ERRORLEVEL%
)
if /I "%~2"=="source" goto :test_valid
if /I "%~2"=="product-source" goto :test_valid
if /I "%~2"=="harness" goto :test_valid
if /I "%~2"=="infra" goto :test_valid
if /I "%~2"=="build" goto :test_valid
if /I "%~2"=="gui" goto :test_valid
if /I "%~2"=="full" goto :test_valid
if /I "%~2"=="policy" goto :test_valid
goto :usage_error

:test_valid
if /I "%~2"=="policy" if not "%~3"=="" goto :usage_error
rem The full stage uses Release by default; run_checks.py ignores --configuration
rem for full. Reject an apparently selectable configuration to avoid confusion.
if /I "%~2"=="full" if not "%~3"=="" goto :usage_error
call "%ROOT%test.bat" "%~2" "%~3"
exit /b %ERRORLEVEL%

:clean
if not "%~3"=="" goto :usage_error
call "%ROOT%clean.bat" "%~2"
exit /b %ERRORLEVEL%

:package
if not "%~2"=="" goto :usage_error
rem Destructive cleanup is explicit: package always rebuilds one exact Release set.
echo [fly] Packaging: clean build output, build Release, provenance, setup.
set "FAILED_STEP=clean build output"
call "%ROOT%clean.bat" build
if errorlevel 1 goto :package_failed
set "FAILED_STEP=build Release"
call "%ROOT%build.bat" Release
if errorlevel 1 goto :package_failed
set "FAILED_STEP=write runtime provenance"
python -X utf8 "%ROOT%packaging\provenance.py" --write
if errorlevel 1 goto :package_failed
set "FAILED_STEP=verify runtime provenance"
python -X utf8 "%ROOT%packaging\provenance.py" --check
if errorlevel 1 goto :package_failed
set "FAILED_STEP=build setup"
call "%ROOT%package.bat" Release
if errorlevel 1 goto :package_failed
echo [fly] Packaging completed: out\package\flyExplorer-Setup-x64.exe
exit /b 0

:package_failed
set "RC=%ERRORLEVEL%"
echo [fly] Packaging failed at: %FAILED_STEP% (exit %RC%).
exit /b %RC%

:usage_error
echo [fly] Invalid arguments. Use: fly.bat help
exit /b 2

:help
echo flyExplorer developer commands
echo.
echo   fly.bat check                       Source, harness and infra contracts
echo   fly.bat build [Debug^|Release]      Build program and Shell helper
echo   fly.bat run [Debug^|Release] [dir]  Start an already-built program
echo   fly.bat run "C:\My Files"          Start Release at a folder
echo   fly.bat test [stage] [config]       Stage: source, product-source,
echo                                       harness, infra, build, gui, full, policy
echo   fly.bat package                     Clean, Release build, provenance, setup
echo   fly.bat clean [build^|cache^|all]    Remove generated output or cache
echo.
echo Double-click run.bat for a normal Release launch without a terminal.
echo Package recreates out\ and updates tracked provenance metadata.
echo Full defaults to Release build + complete GUI (not visual or Debug).
exit /b 0
