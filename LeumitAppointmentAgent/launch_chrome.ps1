# Launch Chrome with remote debugging enabled
# This allows the agent to connect to an existing Chrome window
# IMPORTANT: Keep this terminal open while the agent runs!

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$userDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"

Write-Host "╔════════════════════════════════════════════════════════════╗"
Write-Host "║  Chrome Remote Debugging Launch                           ║"
Write-Host "╚════════════════════════════════════════════════════════════╝"
Write-Host ""
Write-Host "Starting Chrome with remote debugging on port 9222..."
Write-Host "User profile: $userDataDir"
Write-Host ""
Write-Host "IMPORTANT: Keep this terminal open while running the agent!"
Write-Host "The agent will connect through port 9222"
Write-Host ""

# Launch Chrome with:
# - Remote debugging port 9222
# - Default user data directory (your real profile with saved sessions)
# - Start URL to leumit
$arguments = @(
    "--remote-debugging-port=9222",
    "--user-data-dir=`"$userDataDir`"",
    "https://online2.leumit.co.il"
)

# Start Chrome and wait for it
& $chromePath @arguments

Write-Host ""
Write-Host "Chrome has closed. The agent can no longer connect."

