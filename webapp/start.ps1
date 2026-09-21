# start.ps1 ÔÇö Godot MCP webapp frontend
$WebPort = 10992
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath


# Kill any existing processes on this port
# HARDENED 2026-09-17 (TRAPS_AND_PITFALLS.md #36): both waits below used to be
# blind Start-Sleep with no verification - kill+sleep1 never checked the port
# actually freed, and start+sleep5 opened the browser regardless of whether the
# dev server had actually come up. Poll both instead.
Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
$portFreeWaitSec = 10
$portFreeElapsed = 0
while ($portFreeElapsed -lt $portFreeWaitSec -and (Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue)) {
    Start-Sleep -Milliseconds 500
    $portFreeElapsed += 0.5
}

# Start webapp
Push-Location "$PSScriptRoot"
Start-Process cmd -ArgumentList "/c", "bun", "run", "dev"
Pop-Location

$devReady = $false
$devWaitSec = 20
$devElapsed = 0
while ($devElapsed -lt $devWaitSec -and -not $devReady) {
    Start-Sleep -Milliseconds 500
    $devElapsed += 0.5
    $devReady = [bool](Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' })
}
if (-not $devReady) {
    Write-Host "WARNING: dev server not listening on $WebPort after ${devWaitSec}s - opening browser anyway" -ForegroundColor Yellow
}
Write-Host "Godot MCP Webapp: http://localhost:$WebPort" -ForegroundColor Green
Write-Host "Opening in default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$WebPort"
