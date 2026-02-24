@echo off
REM This batch file launches the agent in a completely detached process
REM The Python process will continue running even if this batch file exits

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ========================================================
echo   Leumit Appointment Agent - Detached Mode
echo ========================================================
echo.
echo The Python process is starting independently.
echo You can close this window or the terminal without affecting the agent.
echo.

REM Launch Python in a new command prompt window that won't be terminated with parent
start "Leumit Appointment Agent" python src\main.py

REM Give it a moment to start
timeout /t 2 /nobreak

echo Agent process started!
echo You can now close this window if you want.
echo.
