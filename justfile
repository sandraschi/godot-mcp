set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

export NAME := "Godot MCP"
export DESC := "Godot 4.0 engine control via WebSocket + MCP tools"
export VER  := "0.5.0-beta.1"
export PORT := "10993"
export WEB_PORT := "10992"
export BRIDGE_PORT := "9080"
export HOST := "0.0.0.0"

# Open the interactive recipe dashboard in the browser
default:
    @just --list

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

# Download Godot export templates (required for little-game-export)
install-export-templates version="4.4":
    pwsh -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\install-godot-export-templates.ps1' -Version '{{version}}'

# Synchronise all dependencies and dev extras (auto-installs Godot)
bootstrap: install-godot
    uv sync --all-extras
    Set-Location '{{justfile_directory()}}\webapp'
    bun install

# Pin all deps to exact versions and freeze lockfiles
freeze:
    uv sync --all-extras
    uv lock --upgrade
    Set-Location '{{justfile_directory()}}\webapp'
    bun install --frozen-lockfile

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
    Write-Host "=== Bun ===" -ForegroundColor Cyan; \
    bun --version; \
    Write-Host "=== Node ===" -ForegroundColor Cyan; \
    node --version; \
    Write-Host "=== Ports ===" -ForegroundColor Cyan; \
    $ports = @({{PORT}}, {{WEB_PORT}}, {{BRIDGE_PORT}}); \
    foreach ($p in $ports) { $tcp = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; if ($tcp) { Write-Host "  Port ${p}: $($tcp.State) PID=$($tcp.OwningProcess)" -ForegroundColor Green } else { Write-Host "  Port ${p}: free" -ForegroundColor Gray } }; \
    Write-Host "=== Ruff ===" -ForegroundColor Cyan; \
    uv run ruff --version; \
    Write-Host "=== Biome ===" -ForegroundColor Cyan; \
    bunx biome --version 2>$null

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
    if (Test-Path -Path "webapp\node_modules") { Remove-Item -Recurse -Force "webapp\node_modules" }; \
    if (Test-Path -Path "native\target") { Remove-Item -Recurse -Force "native\target" }; \
    Write-Host "Cleaned. Run 'just bootstrap' to rebuild." -ForegroundColor Yellow

# Complete project re-initialisation
setup: clean bootstrap
    Write-Host "Godot MCP ready." -ForegroundColor Green

# ── Server ────────────────────────────────────────────────────────────────────

# Start the Godot MCP server (Unified Gateway, dual mode)
serve mode="dual" port=PORT:
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
    Set-Location '{{justfile_directory()}}\webapp'
    bun run dev

# Start everything (backed + webapp) via start script
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

# Install the MCP bridge addon into a Godot project (copies mcp_bridge.gd + plugin.cfg)
install-addon project_path:
    $body = @{project_path="{{project_path}}"} | ConvertTo-Json -Compress; \
    try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/addon/install" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 15; ($r.Content | ConvertFrom-Json) | ConvertTo-Json } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

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

# List downloaded sample games under samples/
demo-list:
    Write-Host "Sample games (just demo-run <name>):" -ForegroundColor Cyan; \
    Write-Host "  heart       Heart-Platformer-Godot-4 (2D, Godot 4.0)" -ForegroundColor White; \
    Write-Host "  platformer  Official 2D platformer (physics, shooting)" -ForegroundColor White; \
    Write-Host "  dodge       Dodge the Creeps (first-game tutorial)" -ForegroundColor White; \
    Write-Host "  pong        Classic Pong" -ForegroundColor White; \
    Write-Host "  procedural  GDQuest procedural generation demos" -ForegroundColor White; \
    Write-Host "  skelerealms Open-world RPG framework (3D)" -ForegroundColor White; \
    Write-Host "  vibecode    VibeCode Runner — jump IDEs, dodge agent loops (2D)" -ForegroundColor Magenta; \
    Write-Host "  demos       Open godot-demo-projects folder (50+ mini-demos)" -ForegroundColor Gray

# Import sample assets once (required before first run if .godot/ is missing)
demo-import game="heart":
    $root = '{{justfile_directory()}}'; \
    $proj = switch ('{{game}}') { \
        'heart' { Join-Path $root 'samples\Heart-Platformer-Godot-4' } \
        'platformer' { Join-Path $root 'samples\godot-demo-projects\2d\platformer' } \
        'dodge' { Join-Path $root 'samples\godot-demo-projects\2d\dodge_the_creeps' } \
        'pong' { Join-Path $root 'samples\godot-demo-projects\2d\pong' } \
        'procedural' { Join-Path $root 'samples\godot-4-procedural-generation' } \
        'skelerealms' { Join-Path $root 'samples\skelerealms' } \
        'vibecode' { Join-Path $root 'samples\vibecode-runner' } \
        'demos' { Join-Path $root 'samples\godot-demo-projects' } \
        default { Write-Host "Unknown demo: {{game}}. Run: just demo-list" -ForegroundColor Red; exit 1 } \
    }; \
    if (-not (Test-Path (Join-Path $proj 'project.godot'))) { Write-Host "Missing project: $proj" -ForegroundColor Red; exit 1 }; \
    Write-Host "Importing {{game}} -> $proj" -ForegroundColor Cyan; \
    & (Get-Command godot.exe).Source --path $proj --import; \
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; \
    Write-Host "Import done." -ForegroundColor Green

# Run a sample game (separate Godot window; MCP bridge can stay on godot-mcp root)
demo-run game="heart":
    $root = '{{justfile_directory()}}'; \
    $proj = switch ('{{game}}') { \
        'heart' { Join-Path $root 'samples\Heart-Platformer-Godot-4' } \
        'platformer' { Join-Path $root 'samples\godot-demo-projects\2d\platformer' } \
        'dodge' { Join-Path $root 'samples\godot-demo-projects\2d\dodge_the_creeps' } \
        'pong' { Join-Path $root 'samples\godot-demo-projects\2d\pong' } \
        'procedural' { Join-Path $root 'samples\godot-4-procedural-generation' } \
        'skelerealms' { Join-Path $root 'samples\skelerealms' } \
        'vibecode' { Join-Path $root 'samples\vibecode-runner' } \
        'demos' { Join-Path $root 'samples\godot-demo-projects' } \
        default { Write-Host "Unknown demo: {{game}}. Run: just demo-list" -ForegroundColor Red; exit 1 } \
    }; \
    if (-not (Test-Path (Join-Path $proj 'project.godot'))) { Write-Host "Missing project: $proj" -ForegroundColor Red; exit 1 }; \
    if (-not (Test-Path (Join-Path $proj '.godot\imported'))) { Write-Host "First run: importing assets for {{game}}..." -ForegroundColor Yellow; & (Get-Command godot.exe).Source --path $proj --import; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }; \
    Write-Host "Launching {{game}} -> $proj" -ForegroundColor Cyan; \
    Start-Process -FilePath (Get-Command godot.exe).Source -ArgumentList '--path', $proj

# ── Little game export (itch.io / desktop) ───────────────────────────────────

# Export sample game: web (HTML5) or windows (.exe). Usage: just little-game-export web dodge
little-game-export target game="dodge" output="" pack="false":
    $packSwitch = if ('{{pack}}' -eq 'true') { '-Pack' } else { '' }; \
    $outArg = if ('{{output}}') { "-Output '{{output}}'" } else { '' }; \
    pwsh -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\little-game-export.ps1' -Target '{{target}}' -Game '{{game}}' $outArg $packSwitch

# Zip last export for itch.io upload (runs export with -Pack)
little-game-pack target game="dodge" output="":
    $outArg = if ('{{output}}') { "-Output '{{output}}'" } else { '' }; \
    pwsh -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\scripts\little-game-export.ps1' -Target '{{target}}' -Game '{{game}}' $outArg -Pack

# Butler / itch.io status (requires server running for REST, or uses uv inline)
itch-status:
    try { \
        $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/itch/status" -UseBasicParsing -TimeoutSec 10; \
        ($r.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 5; \
    } catch { \
        uv run python -c "from godot_mcp.itch.service import itch_status; import json; print(json.dumps(itch_status(), indent=2))"; \
    }

# Preview Butler push diff
itch-push-preview upload_dir itch_target="" channel="html":
    $body = @{upload_dir="{{upload_dir}}"}; \
    if ('{{itch_target}}') { $body.itch_target = '{{itch_target}}' }; \
    if ('{{channel}}') { $body.channel = '{{channel}}' }; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/itch/push-preview" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 300 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 5 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Push build directory to itch.io
itch-push upload_dir itch_target="" channel="html" hidden="false":
    $body = @{upload_dir="{{upload_dir}}"; hidden=('{{hidden}}' -eq 'true')}; \
    if ('{{itch_target}}') { $body.itch_target = '{{itch_target}}' }; \
    if ('{{channel}}') { $body.channel = '{{channel}}' }; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/itch/push" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 900 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 5 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Export + preview + push in one step (set BUTLER_API_KEY and ITCH_TARGET first)
ship target="web" game="dodge" itch_target="" channel="" preview="true" push="true":
    $body = @{target='{{target}}'; game='{{game}}'; preview=('{{preview}}' -eq 'true'); push=('{{push}}' -eq 'true')}; \
    if ('{{itch_target}}') { $body.itch_target = '{{itch_target}}' }; \
    if ('{{channel}}') { $body.channel = '{{channel}}' }; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/itch/ship" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 900 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 6 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Steam / steam-mcp status (requires steam-mcp on :11020 for full publish block)
steam-status:
    try { \
        $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/steam/status" -UseBasicParsing -TimeoutSec 15; \
        ($r.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 6; \
    } catch { \
        uv run python -c "from godot_mcp.steam.service import steam_status; import json; print(json.dumps(steam_status(), indent=2))"; \
    }

# Export Windows + stage to _exchange/steam-builds/<app_id>/content
steam-stage game="dodge" app_id="":
    $body = @{game='{{game}}'}; \
    if ('{{app_id}}') { $body.app_id = [int]'{{app_id}}' }; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/steam/stage" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 900 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 6 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Full pipeline: export + stage + beta upload (dry_run default true)
steam-ship-beta game="dodge" dry_run="true":
    $body = @{game='{{game}}'; phase='prerelease'; dry_run=('{{dry_run}}' -eq 'true')}; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/steam/ship" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 900 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 6 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Full pipeline: export + stage + default branch upload (dry_run default true)
steam-ship-release game="dodge" dry_run="true":
    $body = @{game='{{game}}'; phase='release'; dry_run=('{{dry_run}}' -eq 'true')}; \
    $json = $body | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/steam/ship" -Method POST -Body $json -ContentType "application/json" -UseBasicParsing -TimeoutSec 900 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 6 } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Export Godot scene to HTML5/WebAssembly via MCP tool
godot-export path="user://export/web/index.html":
    $body = @{tool="godot_export_web"; arguments=@{output_path="{{path}}"}} | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 } catch { Write-Host "Export failed: $_" }

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute linting (ruff + biome)
lint:
    uv run ruff check src/ tests/
    -bunx biome lint webapp/src/

# Execute auto-fixes and formatting
fix:
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
    bunx biome check --write webapp/src/

# TypeScript type checking (biome check already covers, add explicit tsc)
typecheck:
    Set-Location '{{justfile_directory()}}\webapp'
    bunx tsc --noEmit

# Full format check (CI style)
format-check:
    uv run ruff format src/ tests/ --check
    bunx biome format webapp/src/ --check

# Security scan (Python)
security:
    uv run ruff check src/ --select S

# Check docstrings follow SOTA standard
docstrings:
    uv run ruff check src/ --select D

# Fast quality check (lint + typecheck + tests)
check: lint typecheck test

# Lint GDScript files with gdlint
gdscript-lint:
    Get-ChildItem -Path '{{justfile_directory()}}' -Recurse -Filter '*.gd' | ForEach-Object { & "$env:USERPROFILE\.local\bin\gdlint.exe" $_.FullName }

# Format GDScript files with gdformat (check mode)
gdscript-format-check:
    Get-ChildItem -Path '{{justfile_directory()}}' -Recurse -Filter '*.gd' | ForEach-Object { & "$env:USERPROFILE\.local\bin\gdformat.exe" --check $_.FullName 2>&1 }

# Full CI check (all quality gates)
ci-check: lint typecheck format-check test

# ── Testing ───────────────────────────────────────────────────────────────────

# Run the complete test suite
test:
    uv run pytest -v --tb=short

# Run tests with coverage report
test-cov:
    uv run pytest --cov=godot_mcp --cov-report=term-missing --cov-report=html

# Game Builder E2E smoke test (design → logic → validate; needs Ollama/LLM)
gb-smoke:
    uv run python scripts/gb-smoke.py

# Run the full Game Builder demo (design -> GDScript -> validate)
gb-demo concept="A 2D runner where you collect stars and avoid spikes.":
    pwsh -NoProfile -File '{{justfile_directory()}}\scripts\gb-demo.ps1' -Concept '{{concept}}'

# Run the Game Builder smoke test (design -> logic -> validate)
gb-test game_plan_json="" project_path="":
    uv run python -c "import asyncio, json; from godot_mcp.game_builder.tools import generate_game_tests; from godot_mcp.game_builder.plan import GamePlan; plan = GamePlan.from_json(open('{{game_plan_json}}').read() if '{{game_plan_json}}' else '{\"title\":\"Test\",\"viewport\":\"2d\",\"scenes\":[{\"name\":\"Main\",\"type\":\"Node2D\"}],\"scripts\":[{\"name\":\"player.gd\",\"description\":\"Player controller\"}]}'); r = asyncio.run(generate_game_tests(plan.to_json(), '{{project_path}}' if '{{project_path}}' else '.', None)); print(json.dumps(r, indent=2))"

# Serve the latest HTML5 export and preview in browser
gb-preview build_dir="" port="10994":
    pwsh -NoProfile -File '{{justfile_directory()}}\scripts\gb-preview.ps1' -BuildDir '{{build_dir}}' -Port {{port}}

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

# Build webapp for production
web-build:
    Set-Location '{{justfile_directory()}}\webapp'
    bun run build

# Preview production build
web-preview:
    Set-Location '{{justfile_directory()}}\webapp'
    bun run preview

# Install webapp deps only
web-install:
    Set-Location '{{justfile_directory()}}\webapp'
    bun install

# Add a webapp dependency (usage: just web-add <package>)
web-add package:
    Set-Location '{{justfile_directory()}}\webapp'
    bun add {{package}}

# ── Tauri Native ──────────────────────────────────────────────────────────────

# Build Tauri native desktop app (dev mode — expects webapp dev server on 10992)
tauri-dev:
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1' -Mode dev

# Full release: webapp + PyInstaller sidecar + NSIS installer
tauri-build:
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'

# PyInstaller backend only (for Tauri sidecar)
tauri-sidecar:
    pwsh -NoProfile -File '{{justfile_directory()}}\native\build-sidecar.ps1'

# ── Docker ────────────────────────────────────────────────────────────────────

# Build Docker image
docker-build:
    docker build -t godot-mcp:{{VER}} .

# Run Docker container
docker-run port=PORT:
    docker run -p {{port}}:{{port}} -e GODOT_HOST=host.docker.internal godot-mcp:{{VER}}

# ── MCPB Pack ──────────────────────────────────────────────────────────────────

# MCPB packing: use the fleet-standard recipe `just mcpb-pack` (scripts/just/fleet.just).
# It packs the REPO ROOT (real godot_mcp package + root manifest.json) via the mcpb CLI.

# ── Diagnostics ───────────────────────────────────────────────────────────────

# Check Godot MCP health endpoint
health:
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/status" -UseBasicParsing -TimeoutSec 5 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Test a tool via REST bridge (usage: just tool godot_status)
tool name="godot_status" args="{}":
    $body = @{tool="{{name}}"; arguments=('{{args}}' | ConvertFrom-Json)} | ConvertTo-Json -Compress; \
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

# List all registered MCP tools (actually enumerates - no hardcoded counts)
tools:
    uv run python -c "import asyncio; from godot_mcp.server import mcp; tools = asyncio.run(mcp.list_tools()); names = sorted(t.name for t in tools); print(str(len(names)) + ' MCP tools registered:'); [print('  ' + n) for n in names]"

# Import a GLB/STL/OBJ from the fleet exchange depot into Godot (usage: just depot-import path/to/model.glb)
depot-import file name="DepotImport":
    Set-Location '{{justfile_directory()}}'
    $body = @{tool="godot_import_glb"; arguments=@{path="{{file}}"; name="{{name}}"}} | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Export current scene to HTML5 via godot CLI
depot-export output="D:/Dev/repos/_exchange/models/godot_export":
    Set-Location '{{justfile_directory()}}'
    $body = @{tool="godot_export_web"; arguments=@{output_path="{{output}}"}} | ConvertTo-Json -Compress; \
    try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 300 | ForEach-Object { ($_.Content | ConvertFrom-Json) | ConvertTo-Json } } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# ── Fleet Exchange ─────────────────────────────────────────────────────────────

# Show available files in the fleet exchange depot for godot import
depot-ls:
    Set-Location '{{justfile_directory()}}'
    @Get-ChildItem "D:\Dev\repos\_exchange" -Recurse -File | Where-Object { $_.Extension -match '\.(stl|glb|gltf|obj|csv)$' } | Format-Table Name, Length, LastWriteTime -AutoSize

# Fleet exchange status (MCP REST)
fleet-status:
    Set-Location '{{justfile_directory()}}'
    try { Invoke-RestMethod -Uri "http://localhost:{{PORT}}/api/v1/fleet/status" -TimeoutSec 15 | ConvertTo-Json -Depth 6 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Import GLB/OBJ/STL from fleet exchange via godot bridge
fleet-import path name="FleetImport":
    Set-Location '{{justfile_directory()}}'
    $body = @{path="{{path}}"; name="{{name}}"} | ConvertTo-Json -Compress
    try { Invoke-RestMethod -Uri "http://localhost:{{PORT}}/api/v1/fleet/exchange/import" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120 | ConvertTo-Json -Depth 6 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Fetch World Labs asset URLs (requires worldlabs bridge on 10865)
fleet-worldlabs-info world_id:
    Set-Location '{{justfile_directory()}}'
    try { Invoke-RestMethod -Uri "http://localhost:{{PORT}}/api/v1/fleet/worldlabs/{{world_id}}" -TimeoutSec 60 | ConvertTo-Json -Depth 6 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Download World Labs collider GLB to _exchange (no Godot import)
fleet-worldlabs-stage-mesh world_id:
    Set-Location '{{justfile_directory()}}'
    $body = @{world_id="{{world_id}}"} | ConvertTo-Json -Compress
    try { Invoke-RestMethod -Uri "http://localhost:{{PORT}}/api/v1/fleet/worldlabs/stage-mesh" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 180 | ConvertTo-Json -Depth 6 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Download World Labs collider GLB and import into Godot (requires godot-bridge)
fleet-worldlabs-import world_id name="":
    Set-Location '{{justfile_directory()}}'
    $body = @{world_id="{{world_id}}"; node_name="{{name}}"} | ConvertTo-Json -Compress
    try { Invoke-RestMethod -Uri "http://localhost:{{PORT}}/api/v1/fleet/worldlabs/import-mesh" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 180 | ConvertTo-Json -Depth 6 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Show pending changes summary
git-status:
    git status --short

# Show diff of unstaged changes
git-diff:
    git diff --stat

# Show recent commits
git-log count="10":
    git log --oneline -{{count}}
# ── Playwright E2E ─────────────────────────────────────────────────────

# Install Playwright browsers (one-time)
e2e-install:
    Set-Location '{{justfile_directory()}}\webapp'
    bunx playwright install chromium

# Run Playwright E2E smoke tests (start backend first: just serve)
e2e:
	Set-Location '{{justfile_directory()}}\webapp'
	bunx playwright test

# ── Profiling ───────────────────────────────────────────────────────

# Snapshot Godot performance metrics
profile-snapshot:
	$body = '{"tool":"godot_profile","arguments":{"operation":"snapshot"}}'; \
	try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10; ($r.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 10 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Enable auto-profiling (300-frame rolling window)
profile-enable:
	$body = '{"tool":"godot_profile","arguments":{"operation":"enable","enabled":true}}'; \
	try { Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 | Out-Null; Write-Host "Profiling enabled" -ForegroundColor Green } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# Show profiling history with spike detection
profile-history:
	$body = '{"tool":"godot_profile","arguments":{"operation":"history"}}'; \
	try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10; ($r.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 10 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# ── Animation ───────────────────────────────────────────────────────

# List animations on an AnimationPlayer node
anim-list node="AnimationPlayer":
	$body = (@{tool="godot_animation"; arguments=@{operation="list_animations"; node="{{node}}"}} | ConvertTo-Json -Compress); \
	try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 10; ($r.Content | ConvertFrom-Json).data | ConvertTo-Json -Depth 10 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# ── Mesh Validation ─────────────────────────────────────────────────

# Validate all meshes in the scene for geometric corruption
mesh-validate:
	$body = '{"tool":"godot_validate_meshes","arguments":{}}'; \
	try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 30; ($r.Content | ConvertFrom-Json) | ConvertTo-Json -Depth 10 } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# ── Documentation ───────────────────────────────────────────────────

# Import a 3D Gaussian splat file into Godot (usage: just splat-import path/to/scene.ply)
splat-import path max_splats="200000":
	Set-Location '{{justfile_directory()}}'
	uv run python demos/splat_import.py {{path}} --max-splats {{max_splats}}

# Fetch Godot class reference docs (usage: just godot-docs Node3D)
godot-docs class="Node3D":
	$body = (@{tool="godot_docs"; arguments=@{query="{{class}}"}} | ConvertTo-Json -Compress); \
	try { $r = Invoke-WebRequest -Uri "http://localhost:{{PORT}}/api/v1/control/tool" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 20; ($r.Content | ConvertFrom-Json).data | Select-Object -ExpandProperty content | Write-Host } catch { Write-Host "FAIL: $_" -ForegroundColor Red }

# ── Demo Scripts ────────────────────────────────────────────────────

# List available demo scripts
demos:
	Get-ChildItem '{{justfile_directory()}}\demos\*.py' | ForEach-Object { Write-Host "  $($_.Name): $($_.BaseName)" }

# Run a demo script (usage: just demo <name>)
demo name="playtesting":
	Set-Location '{{justfile_directory()}}'
	uv run python demos/{{name}}.py

