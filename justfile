set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

export NAME := "Godot MCP"
export DESC := "Godot 4.0 engine control via WebSocket + MCP tools"
export VER  := "0.1.0"
export PORT := "10993"
export WEB_PORT := "10992"
export BRIDGE_PORT := "9080"
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
                    $pad = ' ' * [math]::Max(2, (22 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host "`n  [Mode: DUAL | Port: {{PORT}} | Web: {{WEB_PORT}} | Bridge: {{BRIDGE_PORT}}]" -ForegroundColor DarkGray; \
    Write-Host ''

# ── Lifecycle ─────────────────────────────────────────────────────────────────

# Install Godot 4.x engine if not present (headless + editor)
install-godot version="4.4":
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
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm install

# Pin all deps to exact versions and freeze lockfiles
freeze:
    uv sync --all-extras && uv lock --upgrade
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm install --package-lock-only

# Upgrade all Python deps to latest compatible
upgrade:
    uv sync --all-extras --upgrade
    uv lock --upgrade

# Show current dependency tree
tree:
    uv tree

# Doctor: check all tools, ports, config are healthy
doctor:
    Write-Host "=== Godot ===" -ForegroundColor Cyan; \
    if (Get-Command godot.exe -ErrorAction SilentlyContinue) { Write-Host "  $(godot --version)" -ForegroundColor Green } else { Write-Host "  NOT INSTALLED" -ForegroundColor Red }; \
    Write-Host "=== Python ===" -ForegroundColor Cyan; \
    uv run python --version; \
    Write-Host "=== Node ===" -ForegroundColor Cyan; \
    node --version; \
    Write-Host "=== npm ===" -ForegroundColor Cyan; \
    npm --version; \
    Write-Host "=== Ports ===" -ForegroundColor Cyan; \
    $ports = @({{PORT}}, {{WEB_PORT}}, {{BRIDGE_PORT}}); \
    foreach ($p in $ports) { $tcp = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; if ($tcp) { Write-Host "  Port $p: $($tcp.State) PID=$($tcp.OwningProcess)" -ForegroundColor Green } else { Write-Host "  Port $p: free" -ForegroundColor Gray } }; \
    Write-Host "=== Ruff ===" -ForegroundColor Cyan; \
    uv run ruff --version; \
    Write-Host "=== Biome ===" -ForegroundColor Cyan; \
    cmd /c npx biome --version 2>$null

# Print version info
info:
    Write-Host "{{NAME}} v{{VER}}" -ForegroundColor White -BackgroundColor Cyan; \
    Write-Host "Backend:  http://localhost:{{PORT}}" -ForegroundColor Cyan; \
    Write-Host "Webapp:   http://localhost:{{WEB_PORT}}" -ForegroundColor Cyan; \
    Write-Host "Bridge:   tcp://127.0.0.1:{{BRIDGE_PORT}}" -ForegroundColor Cyan; \
    Write-Host "MCP SSE:  http://localhost:{{PORT}}/sse" -ForegroundColor Cyan; \
    Write-Host "Swagger:  http://localhost:{{PORT}}/docs" -ForegroundColor Cyan

# Workspace sanitisation
clean:
    if (Test-Path -Path "**/__pycache__") { Get-ChildItem -Path "." -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force }; \
    if (Test-Path -Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }; \
    if (Test-Path -Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }; \
    if (Test-Path -Path ".ruff_cache") { Remove-Item -Recurse -Force ".ruff_cache" }

# Nuke and reinstall everything from scratch
reset: clean
    if (Test-Path -Path ".venv") { Remove-Item -Recurse -Force ".venv" }; \
    if (Test-Path -Path "web_sota\node_modules") { Remove-Item -Recurse -Force "web_sota\node_modules" }; \
    if (Test-Path -Path "native\target") { Remove-Item -Recurse -Force "native\target" }; \
    Write-Host "Cleaned. Run 'just bootstrap' to rebuild." -ForegroundColor Yellow

# Complete project re-initialisation
setup: clean bootstrap
    Write-Host "Godot MCP ready." -ForegroundColor Green

# ── Server ────────────────────────────────────────────────────────────────────

# Start the Godot MCP server (Unified Gateway, dual mode)
serve mode=dual port=PORT:
    uv run python -m godot_mcp.server --mode {{mode}} --port {{port}}

# Start in stdio mode (for MCP clients)
stdio:
    uv run python -m godot_mcp.server --mode stdio

# Start in agentic mode (CodeMode BM25 discovery)
agentic port=PORT:
    uv run python -m godot_mcp.server --mode dual --port {{port}} --agentic

# Start server with auto-reload
dev port=PORT:
    uv run uvicorn godot_mcp.server:app --reload --port {{port}} --host {{HOST}}

# Start the Vite dashboard
web:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm run dev

# Start everything (backed + web_sota) via start script
start:
    & '{{justfile_directory()}}\start.ps1'

# Kill all godot-mcp processes
stop:
    $ports = @({{PORT}}, {{WEB_PORT}}, {{BRIDGE_PORT}}); \
    foreach ($p in $ports) { Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }; \
    Get-Process -Name godot -ErrorAction SilentlyContinue | Stop-Process -Force; \
    Write-Host "Stopped" -ForegroundColor Yellow

# Restart everything
restart: stop start

# ── Godot Bridge ──────────────────────────────────────────────────────────────

# Launch Godot editor with bridge project
godot-editor:
    Start-Process -FilePath (Get-Command godot.exe).Source -ArgumentList "--path {{justfile_directory()}}"

# Launch Godot headless with bridge project
godot-headless:
    Start-Process -FilePath (Get-Command godot.exe).Source -ArgumentList "--path {{justfile_directory()}} --headless" -WindowStyle Hidden

# Run bridge standalone with Godot
godot-bridge:
    Start-Process -FilePath (Get-Command godot.exe).Source -ArgumentList "--path {{justfile_directory()}} --headless --verbose" -WindowStyle Hidden -RedirectStandardError "$env:TEMP\godot-bridge.log"; \
    Write-Host "Bridge launching..." -ForegroundColor Cyan

# Check Godot bridge connection
bridge-status:
    try { \
        $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/status" -UseBasicParsing -TimeoutSec 5; \
        ($r.Content | ConvertFrom-Json).godot | Format-Table; \
    } catch { Write-Host "Backend not reachable: $_" -ForegroundColor Red }

# Export Godot scene to HTML5/WebAssembly via MCP tool
godot-export path="user://export/web/index.html":
    $body = @{tool="godot_export_web"; arguments=@{output_path="{{path}}""}} | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 } catch { Write-Host "Export failed: $_" }

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute linting (ruff + biome)
lint:
    uv run ruff check src/ tests/
    -cmd /c npx biome lint web_sota/src/

# Execute auto-fixes and formatting
fix:
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
    cmd /c npx biome check --write web_sota/src/

# TypeScript type checking (biome check already covers, add explicit tsc)
typecheck:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npx tsc --noEmit

# Full format check (CI style)
format-check:
    uv run ruff format src/ tests/ --check
    cmd /c npx biome format web_sota/src/ --check

# Security scan (Python)
security:
    uv run ruff check src/ --select S

# Check docstrings follow SOTA standard
docstrings:
    uv run ruff check src/ --select D

# Fast quality check (lint + typecheck + tests)
check: lint typecheck test

# Full CI check (all quality gates)
ci-check: lint typecheck format-check test

# ── Testing ───────────────────────────────────────────────────────────────────

# Run the complete test suite
test:
    uv run pytest -v --tb=short

# Run tests with coverage report
test-cov:
    uv run pytest --cov=godot_mcp --cov-report=term-missing --cov-report=html

# Run tests matching a keyword (e.g. just test-match bridge)
test-match pattern:
    uv run pytest -v -k {{pattern}}

# Run tests in watch mode (re-run on changes)
test-watch:
    uv run pytest-watch -- --tb=short

# Run integration tests only
test-integration:
    uv run pytest -v -m integration --tb=short

# Run unit tests only (fast)
test-unit:
    uv run pytest -v -m "not integration" --tb=short -x

# Run tests and open coverage HTML
test-html: test-cov
    Start-Process (Join-Path {{justfile_directory()}} "htmlcov\index.html")

# Run tests sequentially (avoid asyncio conflicts)
test-seq:
    uv run pytest -v -p no:anyio --tb=short -x

# ── Webapp ────────────────────────────────────────────────────────────────────

# Build web_sota for production
web-build:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm run build

# Preview production build
web-preview:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm run preview

# Install web_sota deps only
web-install:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm install

# Add a web_sota dependency (usage: just web-add <package>)
web-add package:
    Set-Location '{{justfile_directory()}}\web_sota'
    cmd /c npm install {{package}}

# ── Tauri Native ──────────────────────────────────────────────────────────────

# Build Tauri native desktop app (dev mode)
tauri-dev:
    Set-Location '{{justfile_directory()}}\native'
    cargo tauri dev

# Build Tauri native desktop app (release)
tauri-build:
    Set-Location '{{justfile_directory()}}\native'
    cargo tauri build

# ── Docker ────────────────────────────────────────────────────────────────────

# Build Docker image
docker-build:
    docker build -t godot-mcp:{{VER}} .

# Run Docker container
docker-run port=PORT:
    docker run -p {{port}}:{{port}} -e GODOT_HOST=host.docker.internal godot-mcp:{{VER}}

# ── Diagnostics ───────────────────────────────────────────────────────────────

# Check Godot MCP health endpoint
health:
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/status" -UseBasicParsing -TimeoutSec 5 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Test a tool via REST bridge (usage: just tool godot_status)
tool name="godot_status" args='{}':
    $body = @{tool="{{name}}"; arguments=(${{args}} | ConvertFrom-Json)} | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 15 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Stream live logs from backend
logs:
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/logs/stream" -UseBasicParsing -TimeoutSec 30 | ForEach-Object { $_.Content } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Quick live FPS check
fps:
    $body = '{"tool":"godot_status","arguments":{}}'; \
    try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10; ($r.Content | ConvertFrom-Json).data | Select-Object fps, godot_version, node_count | Format-Table } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Verify bridge is connected
bridge-test:
    $body = '{"tool":"godot_status","arguments":{}}'; \
    try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10; $d = ($r.Content | ConvertFrom-Json); if ($d.success) { Write-Host "Bridge OK - Godot $($d.data.godot_version) @ $($d.data.fps) FPS" -ForegroundColor Green } else { Write-Host "Bridge error: $($d.message)" -ForegroundColor Red } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# List all registered MCP tools
tools:
    uv run python -c "from godot_mcp.tools import register_all; print('12 tools registered')"

# ── Git ───────────────────────────────────────────────────────────────────────

# Show pending changes summary
git-status:
    git status --short

# Show diff of unstaged changes
git-diff:
    git diff --stat

# Show recent commits
git-log count=10:
    git log --oneline -{{count}}
