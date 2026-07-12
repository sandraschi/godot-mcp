# start.ps1 - Godot MCP + Webapp
$WebPort = 10992
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath

$ApiPort = 10993

# Kill any existing processes on these ports
Get-NetTCPConnection -LocalPort $ApiPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# Start backend (dual mode: REST + MCP SSE)
$job = Start-Job -Name "godot-mcp" -ScriptBlock {
    Set-Location "$using:PWD"
    uv run python -m godot_mcp.server --mode dual --port $using:ApiPort
}
Start-Sleep -Seconds 3

# Start webapp
Push-Location webapp
Start-Process cmd -ArgumentList "/c", "bun", "run", "dev"
Pop-Location

Start-Sleep -Seconds 5
Write-Host "Godot MCP:   http://localhost:$ApiPort/api/v1/status" -ForegroundColor Green
Write-Host "Webapp:      http://localhost:$WebPort" -ForegroundColor Green
Write-Host "MCP SSE:     http://localhost:$ApiPort/sse" -ForegroundColor Green
Write-Host ""
Write-Host "Opening webapp in default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$WebPort"
