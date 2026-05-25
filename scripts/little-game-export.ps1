# Export a godot-mcp sample (or custom project) for itch.io / desktop sharing.
# Usage: pwsh -File scripts/little-game-export.ps1 -Target web -Game dodge
#        pwsh -File scripts/little-game-export.ps1 -Target windows -Game dodge -Pack

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('web', 'windows')]
    [string]$Target,

    [string]$Game = 'dodge',
    [string]$Project = '',
    [string]$Output = '',
    [switch]$Pack
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

function Resolve-LittleGameProject {
    param([string]$Name, [string]$CustomPath)

    if ($CustomPath) {
        if (-not (Test-Path (Join-Path $CustomPath 'project.godot'))) {
            throw "No project.godot in: $CustomPath"
        }
        return (Resolve-Path $CustomPath).Path
    }

    $map = @{
        heart       = Join-Path $root 'samples\Heart-Platformer-Godot-4'
        platformer  = Join-Path $root 'samples\godot-demo-projects\2d\platformer'
        dodge       = Join-Path $root 'samples\godot-demo-projects\2d\dodge_the_creeps'
        pong        = Join-Path $root 'samples\godot-demo-projects\2d\pong'
        procedural  = Join-Path $root 'samples\godot-4-procedural-generation'
        skelerealms = Join-Path $root 'samples\skelerealms'
        vibecode  = Join-Path $root 'samples\vibecode-runner'
    }

    if (-not $map.ContainsKey($Name)) {
        throw "Unknown game '$Name'. Use: heart, platformer, dodge, pong, procedural, skelerealms, vibecode — or pass -Project path."
    }

    $proj = $map[$Name]
    if (-not (Test-Path (Join-Path $proj 'project.godot'))) {
        throw "Missing sample project: $proj`nClone samples first (see samples/README.md)."
    }
    return $proj
}

function Ensure-ExportPresets {
    param([string]$Proj)

    $dest = Join-Path $Proj 'export_presets.cfg'
    $template = Join-Path $root 'templates\little-game-export_presets.cfg'
    if (-not (Test-Path $template)) {
        throw "Missing template: $template"
    }

    $needsCopy = -not (Test-Path $dest)
    if (-not $needsCopy -and (Test-Path $dest)) {
        $existing = Get-Content $dest -Raw
        # Refresh presets copied from an older template (invalid on Godot 4.4 web export)
        if ($existing -match 'variant/thread_support|ensure_cross_origin_isolation_headers|export_d3d12') {
            $needsCopy = $true
            Write-Host "Refreshing outdated export_presets.cfg..." -ForegroundColor Yellow
        }
    }

    if ($needsCopy) {
        Copy-Item -Path $template -Destination $dest -Force
        Write-Host "Applied export_presets.cfg (Web + Windows Desktop)." -ForegroundColor Yellow
    }
}

function Ensure-Imported {
    param([string]$Proj)

    if (Test-Path (Join-Path $Proj '.godot\imported')) { return }

    Write-Host "First run: importing assets..." -ForegroundColor Yellow
    & (Get-Command godot.exe).Source --path $Proj --import
    if (-not (Test-Path (Join-Path $Proj '.godot\imported'))) {
        throw "Godot import failed — .godot/imported not created (exit $LASTEXITCODE)"
    }
}

$proj = Resolve-LittleGameProject -Name $Game -CustomPath $Project
$godot = (Get-Command godot.exe -ErrorAction Stop).Source

Ensure-ExportPresets -Proj $proj
Ensure-Imported -Proj $proj

$buildRoot = Join-Path $root "build\little-game\$Game"
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null

if ($Target -eq 'web') {
    $preset = 'Web'
    if (-not $Output) {
        $outDir = Join-Path $buildRoot 'web'
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
        $Output = Join-Path $outDir 'index.html'
    } else {
        $outDir = Split-Path -Parent $Output
        if ($outDir) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    }
} else {
    $preset = 'Windows Desktop'
    if (-not $Output) {
        $outDir = Join-Path $buildRoot 'windows'
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
        $Output = Join-Path $outDir "$Game.exe"
    } else {
        $outDir = Split-Path -Parent $Output
        if ($outDir) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    }
}

Write-Host "Exporting $preset -> $Output" -ForegroundColor Cyan
Write-Host "Project: $proj" -ForegroundColor Gray

& $godot --headless --path $proj --export-release $preset $Output

if (-not (Test-Path $Output)) {
    Write-Host ""
    Write-Host "Export failed (output missing): $Output" -ForegroundColor Red
    Write-Host "Run: just install-export-templates" -ForegroundColor Yellow
    exit 1
}

Write-Host "Export OK: $Output" -ForegroundColor Green

if ($Target -eq 'web') {
    $webDir = if ($outDir) { $outDir } else { Split-Path -Parent $Output }
    Write-Host "Upload folder to itch.io (HTML game): $webDir" -ForegroundColor Cyan
    Write-Host "MCD guide: mcp-central-docs/docs/gamedev/ITCH_IO_GUIDE.md" -ForegroundColor Gray
} else {
    Write-Host "Zip folder for itch.io (Windows download): $outDir" -ForegroundColor Cyan
}

if ($Pack) {
    $zipDir = if ($outDir) { $outDir } else { Split-Path -Parent $Output }
    $zipPath = Join-Path $buildRoot "$Target-$Game.zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    Compress-Archive -Path (Join-Path $zipDir '*') -DestinationPath $zipPath -Force
    Write-Host "Pack OK (itch.io upload): $zipPath" -ForegroundColor Green
}
