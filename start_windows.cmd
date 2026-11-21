@echo off
rem Windows host, Webots running natively (the fastest mode). Double-click it, or:
rem   start_windows.cmd [world.wbt]      (default: WORLD in .env, else mine_test_arena.wbt)
rem Starts Docker Desktop if needed, opens Webots, then runs the ROS 2 stack with
rem docker compose. Ctrl+C stops the stack and closes Webots.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\webots_host\start_windows.ps1" %*
if errorlevel 1 pause
