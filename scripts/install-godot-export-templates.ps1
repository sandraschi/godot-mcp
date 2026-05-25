# Download Godot export templates for the installed engine version.
# Usage: pwsh -File scripts/install-godot-export-templates.ps1 -Version 4.4

param(
    [string]$Version = '4.4'
)

$ErrorActionPreference = 'Stop'

$destRoot = Join-Path $env:APPDATA 'Godot\export_templates'
$destDir = Join-Path $destRoot "$Version.stable"
$marker = Join-Path $destDir 'version.txt'

if (Test-Path (Join-Path $destDir 'web_nothreads_release.zip')) {
    Write-Host "Export templates already present: $destDir" -ForegroundColor Green
    exit 0
}

$url = "https://github.com/godotengine/godot/releases/download/$Version-stable/Godot_v$Version-stable_export_templates.tpz"
$tmp = Join-Path $env:TEMP "godot-export-templates-$Version.tpz"
$extract = Join-Path $env:TEMP "godot-export-templates-$Version"

Write-Host "Downloading export templates $Version..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing

if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
New-Item -ItemType Directory -Path $extract -Force | Out-Null
Expand-Archive -Path $tmp -DestinationPath $extract -Force

$inner = Get-ChildItem $extract -Directory | Select-Object -First 1
if (-not $inner) { throw "Unexpected template archive layout" }

New-Item -ItemType Directory -Path $destDir -Force | Out-Null
Copy-Item -Path (Join-Path $inner.FullName '*') -Destination $destDir -Recurse -Force

Remove-Item $tmp -Force
Remove-Item $extract -Recurse -Force

Write-Host "Installed export templates -> $destDir" -ForegroundColor Green
