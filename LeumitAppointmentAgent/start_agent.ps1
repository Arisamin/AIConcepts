# Start Leumit Appointment Agent in a detached process
# This ensures the Chrome browser stays open even if this terminal closes

$agentPath = Join-Path $PSScriptRoot "src\main.py"
$logPath = Join-Path $PSScriptRoot "logs\agent.log"

Write-Host "Starting Leumit Appointment Agent..."
Write-Host "Log file: $logPath"
Write-Host ""
Write-Host "IMPORTANT: The browser window will stay open independently."
Write-Host "You can close this terminal without closing the browser."
Write-Host ""

# Create a new PowerShell process that is completely independent
# The -NoExit keeps the window open, but the key is using CreateNoWindow to detach from parent
$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName = "python"
$pinfo.Arguments = $agentPath
$pinfo.WorkingDirectory = $PSScriptRoot
$pinfo.UseShellExecute = $true
$pinfo.CreateNoWindow = $false
# Don't redirect output - let it show in its own window

$proc = [System.Diagnostics.Process]::Start($pinfo)

Write-Host "Agent process started (PID: $($proc.Id))"
Write-Host ""
Write-Host "The browser will stay open independently."
Write-Host "You can:"
Write-Host "  - Close this terminal window immediately"
Write-Host "  - Leave it open to see real-time logs"
Write-Host "  - Close the Chrome window to end the agent"
Write-Host ""
Write-Host "NOTE: When you close this terminal, the agent keeps running."
Write-Host ""
