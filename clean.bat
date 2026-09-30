@echo off
setlocal EnableExtensions
set "MODE=%~1"
if "%MODE%"=="" set "MODE=build"
if /I "%MODE%"=="build" goto :build
if /I "%MODE%"=="cache" goto :cache
if /I "%MODE%"=="all" goto :all
echo Usage: clean.bat [build^|cache^|all]
exit /b 2

:all
call :remove_build
call :remove_cache
exit /b 0

:build
call :remove_build
exit /b 0

:cache
call :remove_cache
exit /b 0

:remove_build
if exist "%~dp0out" (
  echo Removing generated build output: %~dp0out
  rmdir /s /q "%~dp0out"
)
exit /b 0

:remove_cache
if exist "%~dp0.cache" (
  echo Removing local package cache: %~dp0.cache
  rmdir /s /q "%~dp0.cache"
)
exit /b 0
