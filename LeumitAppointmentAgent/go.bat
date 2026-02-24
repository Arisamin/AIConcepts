@echo off
REM Main launcher - decides which script to run

setlocal enabledelayedexpansion

cd /d "%~dp0"

REM Check if browser is already running
if exist ".leumit_state.json" (
    echo.
    echo ========================================================
    echo   RECOVERY RUN - Connecting to Existing Browser
    echo ========================================================
    echo.
    python fill_form.py
) else (
    echo.
    echo ========================================================
    echo   NEW RUN - Starting Fresh Browser
    echo ========================================================
    echo.
    python start_browser.py
)

echo.
pause
