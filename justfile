set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

export NAME := "Godot MCP"
export DESC := "Godot 4.0 engine control via WebSocket + MCP tools"
export VER  := "0.1.0"
export PORT := "10993"
export WEB_PORT := "10992"
export HOST := "0.0.0.0"

# Display the industrial dashboard
default:
    @$lines = Get-Content '{{justfile()}}'; \
    Write-Host " [{{NAME}}] {{DESC}} v{{VER}}" -ForegroundColor White -BackgroundColor Cyan; \
    Write-Host '' ; \
    $currentCategory = ''; \
    foreach ($line in $lines) { \
        if ($line -match '^# ── ([^─]+) ─') { \
            $currentCategory = $matches[1].Trim(); \
            Write-Host "`n  $currentCategory" -ForegroundColor Cyan; \
            Write-Host ('  ' + ('─' * 45)) -ForegroundColor Gray; \
        } elseif ($line -match '^# ([^─].+)') { \
            $desc = $matches[1].Trim(); \
            $idx = [array]::IndexOf($lines, $line); \
            if ($idx -lt $lines.Count - 1) { \
                $nextLine = $lines[$idx + 1]; \
                if ($nextLine -match '^([a-z0-9-]+):') { \
                    $recipe = $matches[1]; \
                    $pad = ' ' * [math]::Max(2, (20 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host "`n  [Mode: DUAL | Port: {{PORT}}]" -ForegroundColor DarkGray; \
    Write-Host ''

# ── Lifecycle ─────────────────────────────────────────────────────────────────

# Install Godot 4.x engine if not present (headless + editor)
install-godot version=4.4:
    $dest = "$env:USERPROFILE\.local\bin\godot.exe"; \
    if (Get-Command godot.exe -ErrorAction SilentlyContinue) { Write-Host "Godot already installed: $(godot --version)" -ForegroundColor Green; exit 0 }; \
    Write-Host "Downloading Godot {{version}}..." -ForegroundColor Cyan; \
    $url = "https://github.com/godotengine/godot/releases/download/{{version}}-stable/Godot_v{{version}}-stable_win64.exe.zip"; \
    $tmp = "$env:TEMP\godot.zip"; \
    Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing; \
    Expand-Archive -Path $tmp -DestinationPath "$env:TEMP\godot-tmp" -Force; \
    $exe = Get-ChildItem "$env:TEMP\godot-tmp" -Filter "Godot_v{{version}}-stable_win64.exe" | Select-Object -First 1; \
    if (-not $exe) { Write-Host "Download failed" -ForegroundColor Red; exit 1 }; \
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.local\bin" -Force | Out-Null; \
    Move-Item -Path $exe.FullName -Destination $dest -Force; \
    Remove-Item "$env:TEMP\godot-tmp" -Recurse -Force; \
    Remove-Item $tmp -Force; \
    Write-Host "Godot {{version}} installed to $dest" -ForegroundColor Green

# Synchronise all dependencies and dev extras (auto-installs Godot)
bootstrap: install-godot
    uv sync --all-extras
    Set-Location '{{justfile_directory()}}\webapp'
    cmd /c npm install

# Workspace sanitisation
clean:
    if (Test-Path -Path "**/__pycache__") { Get-ChildItem -Path "." -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force }; \
    if (Test-Path -Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }; \
    if (Test-Path -Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }

# Complete project re-initialisation
setup: clean bootstrap
    Write-Host "Godot MCP ready." -ForegroundColor Green

# ── Operation ─────────────────────────────────────────────────────────────────

# Start the Godot MCP server (Unified Gateway, dual mode)
serve mode=dual port=PORT:
    uv run python -m godot_mcp.server --mode {{mode}} --port {{port}}

# Start in stdio mode (for MCP clients)
stdio:
    uv run python -m godot_mcp.server --mode stdio

# Start the Vite dashboard
web:
    Set-Location '{{justfile_directory()}}\webapp'
    cmd /c npm run dev

# ── Development ───────────────────────────────────────────────────────────────

# Start server with auto-reload
dev port=PORT:
    uv run uvicorn godot_mcp.server:app --reload --port {{port}} --host {{HOST}}

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute linting (ruff + biome)
lint:
    uv run ruff check src/ tests/
    -cmd /c npx biome lint webapp/src/

# Execute auto-fixes and formatting
fix:
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
    -cmd /c npx biome check --write webapp/src/

# Fast quality check (lint + tests)
check: lint test

# ── Testing ───────────────────────────────────────────────────────────────────

# Run the complete test suite
test:
    uv run pytest

# ── Diagnostics ───────────────────────────────────────────────────────────────

# Check Godot MCP status
health:
    curl http://localhost:10993/api/v1/status
