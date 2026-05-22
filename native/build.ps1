#!/usr/bin/env pwsh
param(
    [ValidateSet("release", "dev")]
    [string]$Mode = "release"
)
<#
.SYNOPSIS
    Build godot-mcp Tauri app. release = installer; dev = tauri dev (backend via uv).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if ($Mode -eq "dev") {
    Write-Host "=== godot-mcp Tauri dev ===" -ForegroundColor Cyan
    Push-Location $PSScriptRoot
    try {
        $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
        if (-not (Test-Path "node_modules")) { npm install }
        npx @tauri-apps/cli dev
    } finally { Pop-Location }
    exit $LASTEXITCODE
}

Write-Host "=== godot-mcp Tauri release build ===" -ForegroundColor Cyan

Write-Host "-> [1/4] web_sota..." -ForegroundColor Yellow
Push-Location "$Root\web_sota"
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "vite build failed" }
} finally {
    Pop-Location
}

Write-Host "-> [2/4] Tauri icons..." -ForegroundColor Yellow
pwsh -NoLogo -File "$Root\scripts\generate-tauri-icon.ps1"
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path "icons\icon.ico")) {
        npx --yes @tauri-apps/cli icon icons/icon.png
    }
} finally {
    Pop-Location
}

Write-Host "-> [3/4] PyInstaller sidecar..." -ForegroundColor Yellow
pwsh -NoLogo -File "$PSScriptRoot\build-sidecar.ps1"

Write-Host "-> [4/4] Tauri bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
try {
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install in native/ failed" }
    npx @tauri-apps/cli build
    if ($LASTEXITCODE -ne 0) { throw "tauri build failed" }
} finally {
    Pop-Location
}

$nsis = Get-ChildItem "$PSScriptRoot\target\release\bundle\nsis\*-setup.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
Write-Host "=== Build complete ===" -ForegroundColor Green
if ($nsis) {
    Write-Host "Installer: $($nsis.FullName)" -ForegroundColor Cyan
}
