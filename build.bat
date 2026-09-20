::
:: Copyright (c) 2001-2013 Leon Lee author. All rights reserved.
::
::   homepage: http://www.flychk.com
::   e-mail:   mailto:flychk@flychk.com
::
:: Use of this source code is governed by a GPLv3 license that can be
:: found in the LICENSE file.
@echo off

set PATH=%~dp0tools\python_274;%PATH%

set msvs_version=2015
set target_arch=x64
set platform_toolset=

if not %1/==/ set msvs_version=%1
if not %2/==/ set target_arch=%2
if not %3/==/ set platform_toolset=%3

@echo msvs_version = %msvs_version%
@echo target_arch = %target_arch%
if not "%platform_toolset%"=="" @echo platform_toolset = %platform_toolset%
@echo ----------

call tools\gyp\gyp.bat fxfile.gyp --depth=. -G msvs_version=%msvs_version% -D target_arch=%target_arch% -D msvs_version=%msvs_version%
if errorlevel 1 exit /b %errorlevel%

if not "%platform_toolset%"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$toolset='%platform_toolset%'; Get-ChildItem -Path '%~dp0' -Recurse -Filter *.vcxproj | ForEach-Object { $path=$_.FullName; $text=[System.IO.File]::ReadAllText($path); $text=[regex]::Replace($text, '<PlatformToolset>[^<]+</PlatformToolset>', '<PlatformToolset>'+$toolset+'</PlatformToolset>'); [System.IO.File]::WriteAllText($path, $text) }"
    if errorlevel 1 exit /b %errorlevel%
)
