@echo off
REM Launch the Leumit Appointment Agent
REM The Python process may exit but Chrome will stay alive

setlocal enabledelayedexpansion

echo ============================================================
echo Leumit Appointment Agent Launcher
echo ============================================================
echo.

cd /d C:\MyData\Git\AI Projects\LeumitAppointmentAgent

echo Starting agent...
python src/main.py

echo.
echo ============================================================
echo Agent has finished, but Chrome window should still be open.
echo Close this window when you're done using Chrome.
echo ============================================================
pause
