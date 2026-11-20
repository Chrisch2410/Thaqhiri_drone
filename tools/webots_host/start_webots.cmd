@echo off
rem Start Webots natively on Windows for HOST_PLATFORM=windows: ROS 2 runs in
rem Docker and its controllers connect to this Webots over TCP (port 1234).
rem
rem Usage: tools\webots_host\start_webots.cmd [world.wbt] [extra webots args]
rem   world defaults to mine_test_arena.wbt (src\thaqhiri_sim_webots\worlds).
rem Webots is found through WEBOTS_HOME or the installer's registry entry.
setlocal

set "WORLD=%~1"
if "%WORLD%"=="" set "WORLD=mine_test_arena.wbt"
set "WORLD_PATH=%~dp0..\..\src\thaqhiri_sim_webots\worlds\%WORLD%"
if not exist "%WORLD_PATH%" (
  echo World not found: %WORLD_PATH%
  exit /b 1
)

if not defined WEBOTS_HOME call :find_webots HKLM
if not defined WEBOTS_HOME call :find_webots HKCU
set "WEBOTS_EXE=%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe"
if not exist "%WEBOTS_EXE%" (
  echo Webots not found. Install Webots R2025a or set WEBOTS_HOME.
  exit /b 1
)

rem The container ships Webots R2025a; extern controllers need the same release.
set "VERSION="
if exist "%WEBOTS_HOME%\resources\version.txt" set /p VERSION=<"%WEBOTS_HOME%\resources\version.txt"
if not "%VERSION%"=="R2025a" echo WARNING: Webots %VERSION% found; the container uses R2025a.

rem Forward the raw text after the world (e.g. --mode=fast): shift/%%1 would
rem split "--mode=fast" at "=", so strip the first argument from %%* instead.
set "EXTRA="
if not "%~1"=="" (
  set "ARGS=%*"
  call set "EXTRA=%%ARGS:*%1=%%"
)

echo Starting %WEBOTS_EXE% with %WORLD%%EXTRA% on port 1234
"%WEBOTS_EXE%" --port=1234%EXTRA% "%WORLD_PATH%"
exit /b %ERRORLEVEL%

:find_webots
for /f "tokens=2,*" %%A in ('reg query "%1\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Webots" 2^>nul ^| findstr /r /c:"InstallLocation"') do set "WEBOTS_HOME=%%B"
if defined WEBOTS_HOME if "%WEBOTS_HOME:~-1%"=="\" set "WEBOTS_HOME=%WEBOTS_HOME:~0,-1%"
exit /b 0
