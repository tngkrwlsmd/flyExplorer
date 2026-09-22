@echo off
setlocal EnableExtensions

call :ensure_dir "bin" || exit /b 1
call :ensure_dir "bin\x86-multibyte" || exit /b 1
call :ensure_dir "bin\x86-multibyte\Languages" || exit /b 1
call :ensure_dir "bin\x86-unicode" || exit /b 1
call :ensure_dir "bin\x86-unicode\Languages" || exit /b 1
call :ensure_dir "bin\x64" || exit /b 1
call :ensure_dir "bin\x64\Languages" || exit /b 1

call :copy_newer "src\fxfile\Languages\*.*" "bin\x86-multibyte\Languages" || exit /b 1
call :copy_newer "src\fxfile\Languages\*.*" "bin\x86-unicode\Languages" || exit /b 1
call :copy_newer "src\fxfile\Languages\*.*" "bin\x64\Languages" || exit /b 1

exit /b 0

:ensure_dir
if not exist "%~1" mkdir "%~1"
if errorlevel 1 (
    >&2 echo ERROR: Failed to create directory "%~1".
    exit /b 1
)
exit /b 0

:copy_newer
if not exist "%~1" (
    >&2 echo ERROR: Required staging source is missing: "%~1".
    exit /b 1
)
xcopy "%~1" "%~2" /d /e /r /y /i >nul
if errorlevel 2 (
    >&2 echo ERROR: Failed to copy "%~1" to "%~2".
    exit /b 1
)
exit /b 0
