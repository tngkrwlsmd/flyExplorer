@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1

rem Preflight every required release asset before touching the generated bin tree.
rem No /c: required files must fail packaging rather than being ignored.
call :require_input "..\bin\x86-multibyte\fxfile.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\fxfile-crash.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libcharset-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libgfl340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libgfle340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libiconv-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libxml2-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\libxpr.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-multibyte\zlib1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\fxfile.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\fxfile-crash.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libcharset-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libgfl340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libgfle340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libiconv-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libxml2-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\libxprw.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x86-unicode\zlib1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\fxfile.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\fxfile-crash.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libcharset-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libgfl340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libgfle340.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libiconv-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libxml2-2.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\libxprw.dll"
if errorlevel 1 goto :error
call :require_input "..\bin\x64\zlib1.dll"
if errorlevel 1 goto :error
call :require_input "..\src\fxfile\Languages\Korean.xml"
if errorlevel 1 goto :error

if exist ".package-stage" rmdir /s /q ".package-stage"
if exist ".package-stage" goto :error
mkdir ".package-stage\x86-multibyte\Languages" || goto :error
mkdir ".package-stage\x86-unicode\Languages" || goto :error
mkdir ".package-stage\x64\Languages" || goto :error
call :copy_required "..\bin\x86-multibyte\fxfile.exe" ".package-stage\x86-multibyte\fxfile.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\fxfile-crash.dll" ".package-stage\x86-multibyte\fxfile-crash.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\fxfile-keyhook.dll" ".package-stage\x86-multibyte\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\fxfile-launcher.exe" ".package-stage\x86-multibyte\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libcharset-1.dll" ".package-stage\x86-multibyte\libcharset-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libgcc_s_sjlj-1.dll" ".package-stage\x86-multibyte\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libgfl340.dll" ".package-stage\x86-multibyte\libgfl340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libgfle340.dll" ".package-stage\x86-multibyte\libgfle340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libiconv-2.dll" ".package-stage\x86-multibyte\libiconv-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libwinpthread-1.dll" ".package-stage\x86-multibyte\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libxml2-2.dll" ".package-stage\x86-multibyte\libxml2-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\libxpr.dll" ".package-stage\x86-multibyte\libxpr.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-multibyte\zlib1.dll" ".package-stage\x86-multibyte\zlib1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\fxfile.exe" ".package-stage\x86-unicode\fxfile.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\fxfile-crash.dll" ".package-stage\x86-unicode\fxfile-crash.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\fxfile-keyhook.dll" ".package-stage\x86-unicode\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\fxfile-launcher.exe" ".package-stage\x86-unicode\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libcharset-1.dll" ".package-stage\x86-unicode\libcharset-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libgcc_s_sjlj-1.dll" ".package-stage\x86-unicode\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libgfl340.dll" ".package-stage\x86-unicode\libgfl340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libgfle340.dll" ".package-stage\x86-unicode\libgfle340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libiconv-2.dll" ".package-stage\x86-unicode\libiconv-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libwinpthread-1.dll" ".package-stage\x86-unicode\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libxml2-2.dll" ".package-stage\x86-unicode\libxml2-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\libxprw.dll" ".package-stage\x86-unicode\libxprw.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x86-unicode\zlib1.dll" ".package-stage\x86-unicode\zlib1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\fxfile.exe" ".package-stage\x64\fxfile.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\fxfile-crash.dll" ".package-stage\x64\fxfile-crash.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\fxfile-keyhook.dll" ".package-stage\x64\fxfile-keyhook.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\fxfile-launcher.exe" ".package-stage\x64\fxfile-launcher.exe"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libcharset-1.dll" ".package-stage\x64\libcharset-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libgcc_s_sjlj-1.dll" ".package-stage\x64\libgcc_s_sjlj-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libgfl340.dll" ".package-stage\x64\libgfl340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libgfle340.dll" ".package-stage\x64\libgfle340.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libiconv-2.dll" ".package-stage\x64\libiconv-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libwinpthread-1.dll" ".package-stage\x64\libwinpthread-1.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libxml2-2.dll" ".package-stage\x64\libxml2-2.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\libxprw.dll" ".package-stage\x64\libxprw.dll"
if errorlevel 1 goto :error
call :copy_required "..\bin\x64\zlib1.dll" ".package-stage\x64\zlib1.dll"
if errorlevel 1 goto :error
xcopy "..\src\fxfile\Languages\*.xml" ".package-stage\x86-multibyte\Languages\" /e /r /y /i >nul
if errorlevel 1 goto :error
xcopy "..\src\fxfile\Languages\*.xml" ".package-stage\x86-unicode\Languages\" /e /r /y /i >nul
if errorlevel 1 goto :error
xcopy "..\src\fxfile\Languages\*.xml" ".package-stage\x64\Languages\" /e /r /y /i >nul
if errorlevel 1 goto :error
if exist "bin" rmdir /s /q "bin"
if exist "bin" goto :error
move ".package-stage" "bin" >nul
if errorlevel 1 goto :error
popd
exit /b 0

:require_input
if not exist "%~1" (
    echo ERROR: Required release file is missing: %~1
    exit /b 1
)
exit /b 0

:copy_required
copy /b /y "%~1" "%~2" >nul
if errorlevel 1 (
    echo ERROR: Failed to stage required file: %~1
    exit /b 1
)
exit /b 0

:error
set "result=%errorlevel%"
if "%result%"=="0" set "result=1"
if exist ".package-stage" rmdir /s /q ".package-stage"
echo ERROR: Release staging failed. Existing bin tree was not replaced.
popd
exit /b %result%
