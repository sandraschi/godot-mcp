#!/usr/bin/env pwsh
# gb-demo.ps1 — Game Builder demo: runs the full pipeline and reports.
param(
    [string]$Concept = "A 2D runner where you collect stars and avoid spikes. Arrow keys to move, space to jump.",
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Start = Get-Date

if (-not $OutDir) { $OutDir = Join-Path $Root "build\gb-demo" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "=== Game Builder Demo ===" -ForegroundColor Cyan
Write-Host "Concept: $Concept" -ForegroundColor White
Write-Host "Output:  $OutDir" -ForegroundColor White
Write-Host ""

$planFile = Join-Path $OutDir "game_plan.json"

# Step 1: Design
Write-Host "[1/4] Designing game..." -ForegroundColor Yellow
uv run python -c @"
import asyncio, json, sys
sys.path.insert(0, '$Root/src')
from godot_mcp.game_builder.pipeline import design_game
plan = asyncio.run(design_game('$Concept'))
with open('$planFile', 'w') as f:
    f.write(plan.to_json())
print(f'Title: {plan.title} ({plan.genre})')
print(f'Scenes: {len(plan.scenes)}, Scripts: {len(plan.scripts)}, Worlds: {len(plan.worlds)}')
"@ 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

# Step 2: Generate logic
Write-Host "[2/4] Generating GDScript..." -ForegroundColor Yellow
$scriptsOut = Join-Path $OutDir "scripts"
New-Item -ItemType Directory -Force -Path $scriptsOut | Out-Null

uv run python -c @"
import asyncio, json, sys
sys.path.insert(0, '$Root/src')
from godot_mcp.game_builder.plan import GamePlan
from godot_mcp.game_builder.pipeline import generate_game_logic
plan = GamePlan.from_json(open('$planFile').read())
result = asyncio.run(generate_game_logic(plan))
for name, data in result.get('scripts', {}).items():
    if data.get('generated'):
        path = '$scriptsOut\\' + name
        with open(path, 'w') as f:
            f.write(data['code'])
        print(f'OK: {name} ({data[\"size_bytes\"]} bytes)')
    else:
        print(f'FAIL: {name}: {data.get(\"error\", \"unknown\")}')
"@ 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "FAILED" -ForegroundColor Red; exit 1 }

# Step 3: Validate
Write-Host "[3/4] Validating scripts..." -ForegroundColor Yellow
$allPass = $true
Get-ChildItem $scriptsOut -Filter "*.gd" | ForEach-Object {
    $r = & "$env:USERPROFILE\.local\bin\gdlint.exe" $_.FullName 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  PASS: $($_.Name)" -ForegroundColor Green
    } else {
        Write-Host "  FAIL: $($_.Name)" -ForegroundColor Red
        $allPass = $false
    }
}

# Step 4: Summary
$Elapsed = [math]::Round(((Get-Date) - $Start).TotalSeconds, 1)
Write-Host ""
Write-Host "=== Demo Complete ($Elapsed seconds) ===" -ForegroundColor Cyan
Write-Host "Plan:     $planFile" -ForegroundColor Green
Write-Host "Scripts:  $scriptsOut\" -ForegroundColor Green
Write-Host "Valid:    $(if ($allPass) {'All passed'} else {'Some failed'})" -ForegroundColor $(if ($allPass) {'Green'} else {'Yellow'})
Write-Host ""
Write-Host "Next: just gb-preview (after export)" -ForegroundColor Cyan
