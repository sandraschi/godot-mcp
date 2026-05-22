#!/usr/bin/env pwsh
# Patch official 2D platformer AnimationPlayer libraries for Godot 4.4 (4.6 uses libraries/ = syntax).
$ErrorActionPreference = "Stop"
$root = Join-Path (Split-Path -Parent $PSScriptRoot) "samples\godot-demo-projects\2d\platformer"
if (-not (Test-Path $root)) {
    Write-Host "Clone samples first (see samples/README.md)" -ForegroundColor Red
    exit 1
}
$count = 0
Get-ChildItem $root -Filter *.tscn -Recurse -File | ForEach-Object {
    $text = [IO.File]::ReadAllText($_.FullName)
    $new = [regex]::Replace($text, 'libraries/ = SubResource\("([^"]+)"\)', "libraries = {`r`n`"`"`": SubResource(`"`$1`"")`r`n}")
    if ($new -ne $text) {
        [IO.File]::WriteAllText($_.FullName, $new)
        Write-Host "Patched $($_.FullName)" -ForegroundColor Green
        $count++
    }
}
Write-Host "Done. $count file(s) updated." -ForegroundColor Cyan
