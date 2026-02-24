# Leumit Appointment Agent - Running Instructions

## Problem: Browser Closes When Stopping the Agent

When running the agent from VS Code chat and stopping it, the browser window closes because the Python process gets terminated.

## Solution: Use the Detached Launcher

### Option 1: Run in Detached Mode (RECOMMENDED)
This launches the agent in a completely independent process:

```powershell
cd c:\MyData\Git\AI Projects\LeumitAppointmentAgent
.\run_detached.bat
```

**This ensures:**
- The browser window stays open even if you close the terminal
- The Python process continues running independently
- You can examine the page and manually interact with the browser
- You can close the launcher window without affecting the agent

### Option 2: Run Directly (Not Recommended)
```powershell
python src/main.py
```

**Issues:**
- If you stop the agent in VS Code chat, the browser closes
- The only way to keep it open is to NOT stop the script

## What to Expect

1. **Browser launches** - Chromium opens and navigates to Leumit
2. **You enter OTP** - After credentials, you'll manually enter the SMS code in the browser
3. **Agent continues** - Once logged in, agent navigates to appointments section
4. **Form appears** - The search form loads
5. **Browser stays open** - You can then examine what form fields are available

## Stopping the Agent

- If running with `run_detached.bat`: Just close the window or launcher
- If running with `python src/main.py` directly: Press `Ctrl+C` in the terminal
- Either way: Close the browser window to end the agent session
