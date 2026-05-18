# build.ps1 — Godot MCP Tauri native build
param(
    [string]$Mode = "dev"
)

$Root = Split-Path -Parent $PSScriptRoot
$WebApp = Join-Path $Root "webapp"

Write-Host "Building webapp..." -ForegroundColor Cyan
Push-Location $WebApp
npm run build
if ($LASTEXITCODE -ne 0) { Write-Host "Webapp build failed" -ForegroundColor Red; exit 1 }
Pop-Location

Write-Host "Building Tauri native ($Mode)..." -ForegroundColor Cyan
Push-Location $PSScriptRoot
if ($Mode -eq "dev") {
    cargo tauri dev
} else {
    cargo tauri build
}
Pop-Location
