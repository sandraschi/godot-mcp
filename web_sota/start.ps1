
# Fast port helpers (scripts/PortHelpers.ps1)
$__RepoRootForPorts = Split-Path -Parent $PSScriptRoot
$__PortHelpers = Join-Path $__RepoRootForPorts 'scripts\PortHelpers.ps1'
if (Test-Path -LiteralPath $__PortHelpers) { . $__PortHelpers }
# start.ps1 - Godot MCP web_sota frontend
$WebPort = 10992

# Kill any existing processes on this port
Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# Start webapp
Push-Location "$PSScriptRoot"
Start-Process cmd -ArgumentList "/c", "npm", "run", "dev"
Pop-Location

Start-Sleep -Seconds 5
Write-Host "Godot MCP Webapp: http://localhost:$WebPort" -ForegroundColor Green
Write-Host "Opening in default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$WebPort"

