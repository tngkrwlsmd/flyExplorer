@echo off
setlocal EnableExtensions

call :ensure_dir "bin" || exit /b 1
call :ensure_dir "bin\x86-multibyte" || exit /b 1
call :ensure_dir "bin\x86-unicode" || exit /b 1
call :ensure_dir "bin\x64" || exit /b 1

call :copy_newer "lib\gfl\lib\libgfl340.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\gfl\lib\libgfle340.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\gfl\libW\libgfl340.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\gfl\libW\libgfle340.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\gfl\lib64W\libgfl340.dll" "bin\x64" || exit /b 1
call :copy_newer "lib\gfl\lib64W\libgfle340.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\mingwrt\bin\libgcc_s_sjlj-1.dll" "bin" || exit /b 1
call :copy_newer "lib\mingwrt\bin\libgcc_s_sjlj-1.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\mingwrt\bin\libgcc_s_sjlj-1.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\mingwrt\bin64\libgcc_s_sjlj-1.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\mingwrt\bin\libwinpthread-1.dll" "bin" || exit /b 1
call :copy_newer "lib\mingwrt\bin\libwinpthread-1.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\mingwrt\bin\libwinpthread-1.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\mingwrt\bin64\libwinpthread-1.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\iconv\bin\libiconv-2.dll" "bin" || exit /b 1
call :copy_newer "lib\iconv\bin\libiconv-2.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\iconv\bin\libiconv-2.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\iconv\bin64\libiconv-2.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\iconv\bin\libcharset-1.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\iconv\bin\libcharset-1.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\iconv\bin64\libcharset-1.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\libxml2\bin\libxml2-2.dll" "bin" || exit /b 1
call :copy_newer "lib\libxml2\bin\libxml2-2.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\libxml2\bin\libxml2-2.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\libxml2\bin64\libxml2-2.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\libxml2\bin\zlib1.dll" "bin" || exit /b 1
call :copy_newer "lib\libxml2\bin\zlib1.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\libxml2\bin\zlib1.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\libxml2\bin64\zlib1.dll" "bin\x64" || exit /b 1

call :copy_newer "lib\libcurl\bin\libcurl.dll" "bin" || exit /b 1

call :copy_newer "lib\vld\bin\Win32\vld_x86.dll" "bin" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\dbghelp.dll" "bin" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\Microsoft.DTfW.DHL.manifest" "bin" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\vld_x86.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\dbghelp.dll" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\Microsoft.DTfW.DHL.manifest" "bin\x86-multibyte" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\vld_x86.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\dbghelp.dll" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\vld\bin\Win32\Microsoft.DTfW.DHL.manifest" "bin\x86-unicode" || exit /b 1
call :copy_newer "lib\vld\bin\Win64\vld_x64.dll" "bin\x64" || exit /b 1
call :copy_newer "lib\vld\bin\Win64\dbghelp.dll" "bin\x64" || exit /b 1
call :copy_newer "lib\vld\bin\Win64\Microsoft.DTfW.DHL.manifest" "bin\x64" || exit /b 1

exit /b 0

:ensure_dir
if not exist "%~1" mkdir "%~1"
if errorlevel 1 (
    >&2 echo ERROR: Failed to create directory "%~1".
    exit /b 1
)
exit /b 0

:copy_newer
xcopy "%~1" "%~2" /d /e /r /y /i >nul
if errorlevel 1 (
    >&2 echo ERROR: Failed to copy "%~1" to "%~2".
    exit /b 1
)
exit /b 0
