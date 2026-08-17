param(
    [string]$BuildDir = "",
    [int]$Port = 10994
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

# Find the latest HTML5 export
if (-not $BuildDir) {
    $candidates = @(
        Join-Path $Root "build\little-game"
        Join-Path $Root "build"
    )
    foreach ($dir in $candidates) {
        if (Test-Path $dir) {
            $html5Dirs = Get-ChildItem -Path $dir -Recurse -Directory -Filter "web" -ErrorAction SilentlyContinue
            if ($html5Dirs) {
                $BuildDir = $html5Dirs[-1].FullName
                break
            }
        }
    }
}

if (-not $BuildDir -or -not (Test-Path $BuildDir)) {
    Write-Host "No HTML5 export found. Run 'just gb-smoke' or 'just little-game-export web dodge' first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $BuildDir "index.html"))) {
    Write-Host "No index.html found in $BuildDir — not a valid web export." -ForegroundColor Red
    exit 1
}

Write-Host "Serving: $BuildDir" -ForegroundColor Cyan
Write-Host "URL:     http://localhost:$Port" -ForegroundColor Green

# Kill any existing server on this port
Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# Start Python HTTP server
$serverJob = Start-Job -Name "gb-preview" -ScriptBlock {
    param($Dir, $Port)
    Set-Location $Dir
    python -m http.server $Port --bind 127.0.0.1
} -ArgumentList $BuildDir, $Port

Start-Sleep -Seconds 1
Start-Process "http://localhost:$Port"

Write-Host "Press Ctrl+C to stop the preview server." -ForegroundColor Yellow

# Keep running until Ctrl+C
try {
    while ($true) {
        if ($serverJob.State -eq "Failed") {
            Receive-Job $serverJob
            break
        }
        Start-Sleep 2
    }
} finally {
    Stop-Job $serverJob -ErrorAction SilentlyContinue
    Remove-Job $serverJob -ErrorAction SilentlyContinue
}
